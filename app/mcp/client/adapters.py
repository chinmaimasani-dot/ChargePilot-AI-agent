"""Adapters exposing registered MCP tools as LangChain tools (Member 4).

LangGraph models call these adapters; each adapter:

1. Validates arguments against the tool's registered JSON schema.
2. Invokes the MCP executor with the trusted user context captured at
   graph-build time (never taken from model output).
3. Returns the normalized result dict so tool errors are data, not crashes.
"""

import json
import uuid
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model

from app.mcp.client.manager import MCPClientManager, UserContext
from app.mcp.client.normalize import normalize_tool_error


def _model_from_schema(tool) -> type[BaseModel]:
    """Build a Pydantic model from the tool's JSON-schema properties."""
    schema = tool.parameters_schema or {}
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    fields: dict[str, tuple[type, Any]] = {}
    type_map = {"string": str, "integer": int, "number": float, "boolean": bool}
    for prop_name, prop in props.items():
        py_type = type_map.get(prop.get("type"), Any)
        field_info = Field(
            description=prop.get("description", ""),
            default=... if prop_name in required else prop.get("default"),
        )
        fields[prop_name] = (py_type | None, field_info)
    return create_model(f"{tool.name}_args", **fields)


def validate_against_schema(arguments: dict, tool) -> str | None:
    """Return an error message for invalid arguments, else None."""
    schema = tool.parameters_schema or {}
    for required_key in schema.get("required", []):
        if required_key not in arguments or arguments[required_key] is None:
            return f"Missing required argument '{required_key}'."
    allowed = set((schema.get("properties") or {}).keys())
    for key in arguments:
        if allowed and key not in allowed:
            return f"Unexpected argument '{key}'."
    return None


def _build_confirmation_summary(tool, arguments: dict) -> str:
    """Human-readable summary shown to the user before they confirm."""
    if tool.confirmation_summary_fields:
        parts = [
            f"{field_name}: {arguments.get(field_name, 'n/a')}"
            for field_name in tool.confirmation_summary_fields
        ]
        return "\n".join(f"- {part}" for part in parts)
    return "\n".join(f"- {k}: {v}" for k, v in (arguments or {}).items())


def build_confirmation_proposal(
    mcp_manager: MCPClientManager, name: str, arguments: dict
) -> dict:
    """Build the pending-confirmation record for a sensitive tool call."""
    tool = mcp_manager.get_tool(name)
    if tool is None:
        raise ValueError(f"Unknown tool '{name}'")
    return {
        "proposal_id": str(uuid.uuid4()),
        "tool_name": name,
        "arguments": arguments or {},
        "summary": _build_confirmation_summary(tool, arguments or {}),
    }


def build_langchain_tools(
    mcp_manager: MCPClientManager,
    role: str,
    user_context: UserContext,
) -> list[StructuredTool]:
    """Create the LangChain tool set for one role and one verified user.

    The returned tools capture `user_context` in their closure so the model
    cannot pass identity arguments; executors receive it from here.
    """
    tools: list[StructuredTool] = []

    for registered in mcp_manager.tools_for_role(role):

        def _validate(
            arguments: dict, _tool=registered
        ) -> tuple[dict, str | None]:
            arguments = arguments if isinstance(arguments, dict) else {}
            return arguments, validate_against_schema(arguments, _tool)

        async def _runner(arguments: dict, _tool=registered) -> dict:
            arguments, validation_error = _validate(arguments, _tool)
            if validation_error:
                return normalize_tool_error(_tool.name, validation_error)
            return await mcp_manager.call_tool(
                _tool.name, arguments, user_context
            )

        def _run_sync(arguments: dict, _tool=registered) -> dict:
            import asyncio

            arguments, validation_error = _validate(arguments, _tool)
            if validation_error:
                return normalize_tool_error(_tool.name, validation_error)
            result = mcp_manager.call_tool(_tool.name, arguments, user_context)
            if hasattr(result, "__await__"):
                result = asyncio.run(result)
            return result

        args_model = _model_from_schema(registered)
        tool = StructuredTool.from_function(
            func=_run_sync,
            coroutine=_runner,
            name=registered.name,
            description=registered.description,
            args_schema=args_model,
        )
        tools.append(tool)

    return tools


def dumps_safe(value: Any) -> str:
    """JSON-dump helper that never raises into the graph."""
    try:
        return json.dumps(value, default=str)
    except Exception:
        return str(value)
