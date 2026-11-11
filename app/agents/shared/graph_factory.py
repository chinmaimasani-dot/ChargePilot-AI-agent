"""Shared LangGraph factory (Member 4).

Builds a role workflow from reusable blocks. Role graphs (owner/driver) call
`build_role_graph` with their retriever and the MCP manager; they must not
redefine orchestration.
"""

from functools import partial

from langgraph.graph import END, StateGraph

from app.agents.shared import nodes
from app.agents.shared.state import ChatGraphState
from app.llm.config import get_genai_settings
from app.mcp.client.manager import MCPClientManager

ROUTE_EDGE_LIMIT = 10  # safety net against accidental infinite loops


def build_role_graph(
    mcp_manager: MCPClientManager,
    retriever=None,
    settings=None,
) -> StateGraph:
    """Compile a role workflow graph.

    Flow:
        route → (rag | tools | general)
        rag:    retrieve → respond → END
        tools:  reason ⇄ execute (bounded) → respond → END
        general: respond → END

    `execute_tools` may pause the graph with a pending confirmation; the
    runtime resolves it through the trusted API layer, never through the
    model.
    """
    settings = settings or get_genai_settings()
    graph = StateGraph(ChatGraphState)

    graph.add_node("route_request", nodes.route_request)
    graph.add_node("retrieve_knowledge", partial(nodes.retrieve_knowledge, retriever=retriever))
    graph.add_node("agent_step", nodes.agent_step)
    graph.add_node(
        "execute_tools", partial(nodes.execute_tools, mcp_manager=mcp_manager)
    )
    graph.add_node("generate_response", nodes.generate_response)

    graph.set_entry_point("route_request")

    def route_after_classification(state: ChatGraphState) -> str:
        return state.get("route", "general")

    def route_after_agent_step(state: ChatGraphState) -> str:
        # The model produced tool calls when no final response was set.
        if state.get("error"):
            return "respond"
        if state.get("response"):
            return "respond"
        return "execute"

    def route_after_execute(state: ChatGraphState) -> str:
        if state.get("awaiting_confirmation"):
            return "respond"
        if int(state.get("tool_rounds", 0)) >= settings.max_tool_call_rounds:
            return "respond"
        # Let the model react to fresh tool results.
        return "reason"

    def route_after_response(state: ChatGraphState) -> str:
        return END

    graph.add_conditional_edges(
        "route_request",
        route_after_classification,
        {"tools": "agent_step", "rag": "retrieve_knowledge", "general": "generate_response"},
    )
    graph.add_conditional_edges(
        "agent_step",
        route_after_agent_step,
        {"execute": "execute_tools", "respond": "generate_response"},
    )
    graph.add_conditional_edges(
        "execute_tools",
        route_after_execute,
        {"reason": "agent_step", "respond": "generate_response"},
    )
    graph.add_edge("retrieve_knowledge", "generate_response")
    graph.add_edge("generate_response", END)

    return graph
