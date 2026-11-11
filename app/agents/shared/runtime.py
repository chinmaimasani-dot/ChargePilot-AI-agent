"""Shared LangGraph runtime (Member 4).

Role-based workflow selection, invocation, conversation memory, and the
trusted confirmation workflow. The API layer is the only caller.

Security invariants enforced here:

- Role comes from verified backend identity (`user_context`), never from
  prompt text — the wrong graph cannot be reached by asking nicely.
- A pending confirmation is executed ONLY by `confirm_pending`, which the
  API exposes as an explicit user action. The model cannot trigger it.
- Provider failures surface as controlled response payloads, not 500s with
  internal details.
"""

import logging
import uuid

from langchain_core.messages import AIMessage, HumanMessage

from app.agents.shared.context import ConversationStore, get_conversation_store
from app.agents.shared.graph_factory import build_role_graph
from app.agents.shared.state import ChatGraphState, new_graph_state
from app.llm.client import get_chat_model_for_role
from app.mcp.client.adapters import build_langchain_tools
from app.mcp.client.adapters import dumps_safe
from app.mcp.client.manager import MCPClientManager, build_user_context, manager

logger = logging.getLogger(__name__)

ROLES = ("owner", "driver")


class ChatTurnResult(dict):
    """Structured result of one conversational turn."""


def _turn_result(
    reply: str,
    *,
    conversation_id: str,
    sources: list | None = None,
    tool_results: list | None = None,
    pending_confirmation: dict | None = None,
    route: str | None = None,
) -> ChatTurnResult:
    return ChatTurnResult(
        reply=reply,
        conversation_id=conversation_id,
        sources=sources or [],
        tool_results=tool_results or [],
        pending_confirmation=pending_confirmation,
        route=route,
    )


class ChatRuntime:
    """Entry point the chat API uses for both roles."""

    def __init__(
        self,
        mcp_manager: MCPClientManager,
        retriever=None,
        store: ConversationStore | None = None,
    ) -> None:
        self.mcp_manager = mcp_manager
        self.retriever = retriever
        self.store = store or get_conversation_store()
        self._graphs = {
            role: build_role_graph(mcp_manager, self.retriever).compile()
            for role in ROLES
        }

    # ---- conversation lifecycle ---------------------------------------------

    def start_conversation(self, user_context: dict) -> str:
        """Create a conversation for the verified user (owner-side id)."""
        conversation_id = str(uuid.uuid4())
        return conversation_id

    # ---- main turn ------------------------------------------------------------

    async def run_turn(self, user_context: dict, conversation_id: str, message: str) -> ChatTurnResult:
        """Process one user message through the role-appropriate graph."""
        user_id = user_context["user_id"]
        role = user_context["role"]

        if role not in ROLES:
            return _turn_result(
                "Your account role is not supported by the assistant.",
                conversation_id=conversation_id,
            )

        history = self.store.load_history(conversation_id, user_id)
        messages = [
            HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
            for m in history
        ]
        messages.append(HumanMessage(content=message))

        tools = build_langchain_tools(self.mcp_manager, role, user_context)
        state = new_graph_state(
            user_id=user_id,
            role=role,
            conversation_id=conversation_id,
            user_message=message,
            tools=tools,
        )
        state["history"] = messages

        try:
            graph = self._graphs[role]
            final: ChatGraphState = await graph.ainvoke(state)
        except Exception:
            logger.exception("Graph invocation failed")
            return _turn_result(
                "The AI service is temporarily unavailable. Please try again later.",
                conversation_id=conversation_id,
            )

        reply = final.get("response") or "I could not process that request."

        # Persist the exchange so follow-up turns keep context (Member 1's
        # tables back this store once integrated).
        self.store.append_message(conversation_id, user_id, "user", message)
        self.store.append_message(conversation_id, user_id, "assistant", reply)

        pending = final.get("pending_confirmation")
        self.store.set_pending_confirmation(
            conversation_id, user_id, pending
        )

        return _turn_result(
            reply,
            conversation_id=conversation_id,
            sources=final.get("rag_sources", []),
            tool_results=final.get("tool_results", []),
            pending_confirmation=pending,
            route=final.get("route"),
        )

    # ---- explicit confirmation workflow ---------------------------------------

    async def confirm_pending(self, user_context: dict, conversation_id: str, proposal_id: str) -> ChatTurnResult:
        """Execute a pending action after an explicit in-app user action.

        This is a trusted application transition tied to the exact proposal
        recorded for this conversation; the LLM is not involved in approving.
        """
        user_id = user_context["user_id"]
        pending = self.store.get_pending_confirmation(conversation_id, user_id)

        if not pending or pending.get("proposal_id") != proposal_id:
            return _turn_result(
                "There is no matching action awaiting your confirmation.",
                conversation_id=conversation_id,
            )

        result = await self.mcp_manager.call_tool(
            pending["tool_name"],
            pending.get("arguments", {}),
            build_user_context(user_id, user_context["role"]),
        )

        self.store.set_pending_confirmation(conversation_id, user_id, None)

        if result.get("ok"):
            data_summary = dumps_safe(result.get("data"))
            reply = (
                f"Confirmed. {pending['tool_name']} completed.\nResult: {data_summary}"
            )
        else:
            reply = f"Confirmation failed: {result.get('error')}"
        self.store.append_message(conversation_id, user_id, "assistant", reply)
        return _turn_result(
            reply,
            conversation_id=conversation_id,
            tool_results=[result],
        )

    async def reject_pending(self, user_context: dict, conversation_id: str, proposal_id: str) -> ChatTurnResult:
        user_id = user_context["user_id"]
        pending = self.store.get_pending_confirmation(conversation_id, user_id)
        if pending and pending.get("proposal_id") != proposal_id:
            return _turn_result(
                "There is no matching action awaiting your confirmation.",
                conversation_id=conversation_id,
            )
        self.store.set_pending_confirmation(conversation_id, user_id, None)
        reply = "The action was cancelled. Nothing was executed."
        self.store.append_message(conversation_id, user_id, "assistant", reply)
        return _turn_result(reply, conversation_id=conversation_id)


# ---- process-wide runtime ----------------------------------------------------

# Retriever is injected at app startup once RAG config is available; until
# then the graphs run with general+tools routes only.
_runtime: ChatRuntime | None = None


def get_runtime() -> ChatRuntime:
    global _runtime
    if _runtime is None:
        from app.rag.retriever import KnowledgeRetriever, get_retriever

        retriever = get_retriever()
        _runtime = ChatRuntime(mcp_manager=manager, retriever=retriever)
    return _runtime


def set_runtime(runtime: ChatRuntime | None) -> None:
    """Test/integration seam: replace the process-wide runtime."""
    global _runtime
    _runtime = runtime
