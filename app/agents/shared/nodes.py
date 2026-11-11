"""Common graph nodes and utilities (Member 4).

Reusable nodes used by both role workflows: request normalization, role-aware
routing, RAG retrieval, bounded tool execution, confirmation gating, and
response generation. Business rules are NOT implemented here — tool calls
delegate to MCP/domain services owned by Members 2 and 3.
"""

import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.shared.prompts import (
    RAG_SYSTEM_PROMPT,
    ROUTER_SYSTEM_PROMPT,
    SYSTEM_PROMPTS,
)
from app.agents.shared.state import ChatGraphState
from app.llm.client import get_chat_model_for_role
from app.mcp.client.adapters import (
    build_confirmation_proposal,
    dumps_safe,
    validate_against_schema,
)
from app.mcp.client.manager import MCPClientManager
from app.mcp.client.normalize import (
    normalize_tool_error,
    summarize_tool_results,
)

logger = logging.getLogger(__name__)

# Heuristic keyword buckets used as routing fallback when the LLM router is
# unavailable. They intentionally mirror the capability tables of the brief.
TOOL_KEYWORDS = (
    "my station", "my stations", "revenue", "sessions", "analytics", "utilization",
    "price", "pricing", "mark charger", "update charger", "update station",
    "add station", "create station", "available", "availability", "find station",
    "search station", "compatible", "favourite", "favorite", "preference",
    "book", "booking", "slot", "cancel",
)
RAG_KEYWORDS = (
    "what is", "explain", "difference", "how does", "maintenance", "safety",
    "connector type", "ac charging", "dc charging", "charging basics", "faq",
    "guideline", "specification",
)


def _with_system_prompt(role: str, messages: list) -> list:
    """Prepend the role's versioned system prompt to the message list."""
    system = SYSTEM_PROMPTS.get(role)
    if system:
        return [SystemMessage(content=system)] + list(messages)
    return list(messages)


def route_request(state: ChatGraphState) -> dict:
    """Role-aware routing between tools, RAG and general conversation.

    The router only sees capabilities registered for the caller's role;
    routing cannot promote a driver request into owner capabilities.
    """
    role = state["role"]
    tool_names = [t.name for t in state.get("available_tools", [])]
    message = (state.get("user_message") or "").strip().lower()

    if not message:
        return {"route": "general"}

    has_tool_intent = any(k in message for k in TOOL_KEYWORDS)
    has_rag_intent = any(k in message for k in RAG_KEYWORDS)

    decided: str | None = None
    try:
        model = get_chat_model_for_role(role)
        answer = model.invoke(
            [
                HumanMessage(
                    content=ROUTER_SYSTEM_PROMPT.format(
                        capabilities=", ".join(tool_names) or "none"
                    )
                ),
                HumanMessage(content=message),
            ]
        )
        text = (answer.content or "").strip().lower()
        if text in {"tools", "rag", "general"}:
            decided = text
    except Exception:
        logger.warning("LLM routing unavailable; using heuristic router")

    if decided is None:
        if has_tool_intent and tool_names:
            decided = "tools"
        elif has_rag_intent:
            decided = "rag"
        else:
            decided = "general"

    # Guard: "tools" is only valid when the role actually has tools.
    if decided == "tools" and not tool_names:
        decided = "general"
    return {"route": decided}


def retrieve_knowledge(state: ChatGraphState, retriever) -> dict:
    """RAG node: retrieve role-filtered knowledge for the current question.

    Retrieval failures (e.g. knowledge tables not yet migrated, vector
    store unavailable) degrade to "no evidence" so the assistant answers
    that it does not know instead of failing the whole turn.
    """
    if retriever is None:
        return {"rag_context": "", "rag_sources": []}
    try:
        results = retriever.retrieve(state["user_message"], audience=state["role"])
    except Exception:
        logger.exception("Knowledge retrieval failed; continuing without evidence")
        return {"rag_context": "", "rag_sources": []}
    if not results:
        return {"rag_context": "", "rag_sources": []}
    context = "\n\n".join(f"[source: {r['title']}] {r['content']}" for r in results)
    sources = [{"title": r["title"], "score": r.get("score")} for r in results]
    return {"rag_context": context, "rag_sources": sources}


def agent_step(state: ChatGraphState) -> dict:
    """Tool-loop reasoning step: bind the role's tools and let the model act.

    The runtime guarantees `state["history"]` ends with the current user
    message, followed by this turn's assistant tool-call messages and their
    tool-result messages.
    """
    role = state["role"]
    tools = state.get("available_tools", [])
    model = get_chat_model_for_role(role)
    bound = model.bind_tools(tools) if tools else model

    try:
        answer = bound.invoke(
            _with_system_prompt(role, list(state.get("history") or []))
        )
    except Exception:
        logger.exception("Provider failure in agent_step")
        return {
            "error": "The AI service is temporarily unavailable. Please try again later."
        }

    proposed = list(getattr(answer, "tool_calls", None) or [])
    if not proposed:
        content = (
            answer.content
            if isinstance(answer.content, str)
            else dumps_safe(answer.content)
        )
        return {"response": content or "I could not generate a response."}

    # Persist the assistant's tool-call message for the next round.
    return {"history": [answer], "response": ""}


async def execute_tools(state: ChatGraphState, mcp_manager: MCPClientManager) -> dict:
    """Execute the model's proposed tool calls with confirmation gating.

    Sensitive tools (e.g. booking confirmation, once registered by Member 3)
    are never executed here on first proposal: the node records a pending
    proposal and ends the turn. Only the trusted API layer executes it after
    an explicit in-app user action.
    """
    last_ai = next(
        (
            m
            for m in reversed(state.get("history", []))
            if getattr(m, "tool_calls", None)
        ),
        None,
    )
    proposed_calls = list(getattr(last_ai, "tool_calls", None) or [])
    if not proposed_calls:
        return {}

    results = list(state.get("tool_results", []))
    executed_call_ids = {r.get("call_id") for r in results if r.get("call_id")}
    rounds = int(state.get("tool_rounds", 0)) + 1
    history_appends = []

    for call in proposed_calls:
        call_id = call.get("id")
        if call_id and call_id in executed_call_ids:
            continue  # already executed in an earlier round of this turn
        name = call.get("name", "")
        arguments = call.get("args") or {}
        tool = mcp_manager.get_tool(name)

        if tool is None or tool.role != state["role"]:
            results.append(
                {
                    **normalize_tool_error(
                        name, "This tool is not available for your role."
                    ),
                    "call_id": call_id,
                }
            )
            continue

        schema_error = validate_against_schema(arguments, tool)
        if schema_error:
            results.append(
                {**normalize_tool_error(name, schema_error), "call_id": call_id}
            )
            continue

        if tool.requires_confirmation and not state.get("awaiting_confirmation"):
            proposal = build_confirmation_proposal(mcp_manager, name, arguments)
            return {
                "pending_confirmation": proposal,
                "awaiting_confirmation": True,
                "tool_results": results,
                "tool_rounds": rounds,
            }

        result = await mcp_manager.call_tool(
            name,
            arguments,
            {"user_id": state["user_id"], "role": state["role"]},
        )
        results.append({**result, "call_id": call_id})

    # Feed executed results back to the model for the next reasoning round.
    for result in results:
        history_appends.append(AIMessage(content=dumps_safe(result)))

    return {"tool_results": results, "tool_rounds": rounds, "history": history_appends}


def generate_response(state: ChatGraphState) -> dict:
    """Final response generation for the chosen route."""
    if state.get("awaiting_confirmation") and state.get("pending_confirmation"):
        proposal = state["pending_confirmation"]
        reply = (
            "Please review and confirm this action in the app:\n"
            f"- action: {proposal['tool_name']}\n{proposal['summary']}\n\n"
            "Nothing has been executed yet."
        )
        return {"response": reply}

    if state.get("error"):
        return {"response": state["error"]}

    route = state.get("route", "general")

    if route == "rag":
        if not state.get("rag_context"):
            return {
                "response": (
                    "I could not find relevant information in the knowledge base "
                    "for that question."
                )
            }
        prompt = RAG_SYSTEM_PROMPT.format(context=state["rag_context"])
        try:
            model = get_chat_model_for_role(state["role"])
            answer = model.invoke(
                _with_system_prompt(
                    state["role"],
                    [
                        HumanMessage(content=prompt),
                        HumanMessage(content=state["user_message"]),
                    ],
                )
            )
            content = (
                answer.content
                if isinstance(answer.content, str)
                else dumps_safe(answer.content)
            )
            return {"response": content}
        except Exception:
            logger.exception("Provider failure generating RAG response")
            return {
                "response": "The AI service is temporarily unavailable. Please try again later."
            }

    if route == "tools":
        if state.get("response"):
            return {}
        summary = summarize_tool_results(state.get("tool_results", []))
        try:
            model = get_chat_model_for_role(state["role"])
            answer = model.invoke(
                _with_system_prompt(
                    state["role"],
                    [
                        HumanMessage(
                            content=(
                                "Summarize these tool results for the user in one or two "
                                "clear sentences. If a result is an error, explain it and "
                                "suggest a fix.\n" + summary
                            )
                        )
                    ],
                )
            )
            content = (
                answer.content
                if isinstance(answer.content, str)
                else dumps_safe(answer.content)
            )
            return {"response": content}
        except Exception:
            return {"response": summary}

    # general route: plain conversational reply over persisted history
    try:
        model = get_chat_model_for_role(state["role"])
        answer = model.invoke(
            _with_system_prompt(state["role"], list(state.get("history") or []))
        )
        content = (
            answer.content
            if isinstance(answer.content, str)
            else dumps_safe(answer.content)
        )
        return {"response": content or "I could not generate a response."}
    except Exception:
        logger.exception("Provider failure generating general response")
        return {
            "response": "The AI service is temporarily unavailable. Please try again later."
        }
