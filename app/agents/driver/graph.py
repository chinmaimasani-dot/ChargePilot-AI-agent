"""Driver graph composition.

The graph body comes from the shared framework (Member 4). The booking
confirmation pause/resume is part of that framework; Member 3 validates the
domain behaviour during workflow integration.
"""

from app.agents.shared.graph_factory import build_role_graph
from app.llm.config import get_genai_settings
from app.mcp.client.manager import manager as mcp_manager


def build_driver_graph():
    """Compile the driver workflow. RAG retriever wired in by the runtime."""
    return build_role_graph(mcp_manager, retriever=None, settings=get_genai_settings())
