"""Owner graph composition.

The graph body comes from the shared framework (Member 4). Members 2/3 add
domain-specific nodes or prompt tweaks here during workflow integration —
orchestration itself must stay in `app.agents.shared`.
"""

from app.agents.shared.graph_factory import build_role_graph
from app.llm.config import get_genai_settings
from app.mcp.client.manager import manager as mcp_manager


def build_owner_graph():
    """Compile the owner workflow. RAG retriever wired in by the runtime."""
    return build_role_graph(mcp_manager, retriever=None, settings=get_genai_settings())
