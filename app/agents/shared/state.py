"""Common LangGraph state shared by all role workflows (Member 4).

Trusted-context fields (user_id, role, conversation_id) are populated by the
backend API layer from verified identity — never from prompt text or LLM
output. Graph nodes treat them as read-only.
"""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage


def _merge_history(
    left: list[AnyMessage] | None, right: list[AnyMessage] | None
) -> list[AnyMessage]:
    """Reducer for the running message history within one graph invocation."""
    merged = list(left or [])
    for message in right or []:
        if not merged or message != merged[-1]:
            merged.append(message)
    return merged


def _replace(left: Any, right: Any) -> Any:
    return right


class ChatGraphState(TypedDict, total=False):
    # --- trusted backend context (set once by the API layer) ---
    user_id: Annotated[str, _replace]
    role: Annotated[str, _replace]
    conversation_id: Annotated[str, _replace]

    # --- conversation ---
    user_message: Annotated[str, _replace]
    history: Annotated[list[AnyMessage], _merge_history]

    # --- routing ---
    # One of: "general" | "tools" | "rag" | "refuse"
    route: Annotated[str, _replace]

    # --- tool execution ---
    available_tools: Annotated[list[Any], _replace]
    tool_results: Annotated[list[dict], _replace]
    tool_rounds: Annotated[int, _replace]

    # --- confirmation workflow ---
    # {"proposal_id", "tool_name", "arguments", "summary"}; the graph sets it
    # but only the trusted API layer may execute the confirmed action.
    pending_confirmation: Annotated[dict | None, _replace]
    awaiting_confirmation: Annotated[bool, _replace]

    # --- RAG ---
    rag_context: Annotated[str, _replace]
    rag_sources: Annotated[list[dict], _replace]

    # --- response / errors ---
    response: Annotated[str, _replace]
    error: Annotated[str | None, _replace]


def new_graph_state(
    *,
    user_id: str,
    role: str,
    conversation_id: str,
    user_message: str,
    tools: list[Any] | None = None,
) -> ChatGraphState:
    """Build the initial state for one user turn from trusted context."""
    return ChatGraphState(
        user_id=user_id,
        role=role,
        conversation_id=conversation_id,
        user_message=user_message,
        history=[],
        available_tools=list(tools or []),
        tool_results=[],
        tool_rounds=0,
        pending_confirmation=None,
        awaiting_confirmation=False,
        rag_context="",
        rag_sources=[],
        response="",
        error=None,
    )
