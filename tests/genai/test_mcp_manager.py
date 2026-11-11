"""MCP manager unit tests: role scoping, unknown tools, async executors."""

import asyncio

from app.mcp.client.manager import build_user_context
from app.mcp.client.normalize import normalize_tool_result


def test_unknown_tool_returns_error(fresh_manager):
    result = asyncio.run(
        fresh_manager.call_tool(
            "does_not_exist", {}, build_user_context("u1", "owner")
        )
    )
    assert result["ok"] is False
    assert "Unknown or unavailable tool" in result["error"]


def test_role_mismatch_is_blocked_in_manager(fresh_manager):
    def executor(arguments, user_context):
        raise AssertionError("must not run")

    fresh_manager.register_executor(
        name="update_charging_price",
        role="owner",
        description="owner-only",
        parameters_schema={"type": "object", "properties": {}, "required": []},
        executor=executor,
    )

    result = asyncio.run(
        fresh_manager.call_tool(
            "update_charging_price", {}, build_user_context("d1", "driver")
        )
    )
    assert result["ok"] is False
    assert "not available for your role" in result["error"]


def test_async_executor_supported(fresh_manager):
    async def executor(arguments, user_context):
        return {"async": True}  # raw payload; manager normalizes it

    fresh_manager.register_executor(
        name="search_stations",
        role="driver",
        description="search",
        parameters_schema={"type": "object", "properties": {}, "required": []},
        executor=executor,
    )

    result = asyncio.run(
        fresh_manager.call_tool("search_stations", {}, build_user_context("d1", "driver"))
    )
    assert result["ok"] is True
    assert result["data"] == {"async": True}


def test_permission_error_becomes_tool_error(fresh_manager):
    def executor(arguments, user_context):
        raise PermissionError("Not your station.")

    fresh_manager.register_executor(
        name="update_station",
        role="owner",
        description="update",
        parameters_schema={"type": "object", "properties": {}, "required": []},
        executor=executor,
    )

    result = asyncio.run(
        fresh_manager.call_tool("update_station", {}, build_user_context("o1", "owner"))
    )
    assert result["ok"] is False
    assert "Not your station." in result["error"]


def test_tools_for_role_are_isolated(fresh_manager):
    for role in ("owner", "driver"):
        fresh_manager.register_executor(
            name=f"tool_{role}",
            role=role,
            description="x",
            parameters_schema={},
            executor=lambda a, u: normalize_tool_result(f"tool_{role}", None),
        )
    assert [t.name for t in fresh_manager.tools_for_role("owner")] == ["tool_owner"]
    assert [t.name for t in fresh_manager.tools_for_role("driver")] == ["tool_driver"]
