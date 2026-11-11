"""MCP client manager and trusted-context propagation (Member 4).

Owns connections to the Owner MCP server (Member 2) and Driver MCP server
(Member 3) and exposes a role-filtered tool registry.

Security contract (agreed with the team):

- Identity/role of the acting user travel ONLY in the trusted context dict
  attached here at call time, derived from verified JWT claims by the API
  layer. The LLM never supplies or overrides them.
- Each role sees only its own server's tools. Owner tools are never
  registered in the driver registry and vice versa.
- MCP servers must resolve the acting user from the trusted context and
  enforce ownership in the domain services they call.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from app.mcp.client.normalize import (
    normalize_mcp_call_result,
    normalize_tool_error,
    normalize_tool_result,
)

logger = logging.getLogger(__name__)

# Type for the trusted user context propagated to MCP execution.
# {"user_id": str, "role": "owner"|"driver"} — built from JWT claims only.
UserContext = dict[str, str]

# A registered tool executor: (tool_name, arguments, user_context) -> dict
ToolExecutor = Callable[[str, dict, UserContext], Any]


@dataclass
class RegisteredTool:
    """A tool available to exactly one role."""

    name: str
    role: str
    description: str
    parameters_schema: dict
    executor: ToolExecutor
    # Tools that must never run without an explicit in-app user action.
    requires_confirmation: bool = False
    # Human-readable summary of what confirmation will present to the user.
    confirmation_summary_fields: tuple[str, ...] = ()


@dataclass
class MCPServerConfig:
    """Connection descriptor for one MCP server.

    The MVP wires the servers in-process (they import the same domain
    services); `url` supports a remote streamable-HTTP server later.
    """

    name: str
    role: str
    url: str = ""  # empty => not deployed yet
    metadata: dict = field(default_factory=dict)


class MCPClientManager:
    """Registry + execution façade for role-scoped MCP tools.

    Until Members 2 and 3 ship their servers, `register_executor` lets the
    team attach thin adapters to existing domain services; the exact same
    interface is used once real MCP servers are connected.
    """

    def __init__(self) -> None:
        self._servers: dict[str, MCPServerConfig] = {}
        self._tools: dict[str, RegisteredTool] = {}

    # ---- server registration -------------------------------------------------

    def register_server(self, config: MCPServerConfig) -> None:
        self._servers[config.name] = config
        logger.info("Registered MCP server %s for role %s", config.name, config.role)

    def server_status(self) -> dict[str, dict]:
        return {
            name: {"role": cfg.role, "url": cfg.url or None, "connected": bool(cfg.url)}
            for name, cfg in self._servers.items()
        }

    # ---- tool registration ---------------------------------------------------

    def register_executor(
        self,
        *,
        name: str,
        role: str,
        description: str,
        parameters_schema: dict,
        executor: ToolExecutor,
        requires_confirmation: bool = False,
        confirmation_summary_fields: tuple[str, ...] = (),
    ) -> None:
        """Register one tool under a role.

        `executor` must ultimately delegate to the domain services owned by
        Members 2/3 — tool functions are thin adapters, never copies of the
        business rules.
        """
        self._tools[name] = RegisteredTool(
            name=name,
            role=role,
            description=description,
            parameters_schema=parameters_schema,
            executor=executor,
            requires_confirmation=requires_confirmation,
            confirmation_summary_fields=confirmation_summary_fields,
        )

    # ---- role-scoped access --------------------------------------------------

    def tools_for_role(self, role: str) -> list[RegisteredTool]:
        return [t for t in self._tools.values() if t.role == role]

    def get_tool(self, name: str) -> RegisteredTool | None:
        return self._tools.get(name)

    # ---- execution -----------------------------------------------------------

    async def call_tool(
        self, name: str, arguments: dict, user_context: UserContext
    ) -> dict:
        """Execute a tool with trusted context injection.

        Returns the normalized result dict; never raises into the graph.
        """
        tool = self._tools.get(name)
        if tool is None:
            return normalize_tool_error(name, f"Unknown or unavailable tool '{name}'.")

        if tool.role != user_context.get("role"):
            # Role-confusion defence: a driver-context call can never invoke
            # an owner tool, regardless of what the model produced.
            return normalize_tool_error(
                name, "This tool is not available for your role."
            )

        try:
            payload = tool.executor(arguments, user_context)
            if isinstance(payload, Awaitable):
                payload = await payload
            # If a real MCP server produced this result, normalize its shape.
            if hasattr(payload, "content"):
                return normalize_mcp_call_result(name, payload)
            return normalize_tool_result(name, payload)
        except PermissionError as exc:
            return normalize_tool_error(name, str(exc) or "Not authorized.")
        except Exception:
            logger.exception("Tool %s failed", name)
            return normalize_tool_error(
                name, "The operation failed while contacting application services."
            )


manager = MCPClientManager()


def build_user_context(user_id: str, role: str) -> UserContext:
    """Build the trusted context dict from verified identity (API layer only)."""
    return {"user_id": str(user_id), "role": role}
