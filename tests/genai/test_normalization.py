"""Unit tests for MCP output normalization and argument validation."""

from types import SimpleNamespace

from app.mcp.client.adapters import validate_against_schema
from app.mcp.client.normalize import (
    normalize_mcp_call_result,
    normalize_tool_error,
    normalize_tool_result,
    summarize_tool_results,
)


def test_normalize_success_result():
    result = normalize_tool_result("get_owner_stations", {"stations": [1, 2]})
    assert result == {
        "tool": "get_owner_stations",
        "ok": True,
        "data": {"stations": [1, 2]},
        "error": None,
    }


def test_normalize_error_result():
    result = normalize_tool_error("get_owner_stations", "Not authorized.")
    assert result["ok"] is False
    assert result["error"] == "Not authorized."
    assert result["data"] is None


def test_normalize_mcp_call_result_flattens_text():
    call_result = SimpleNamespace(
        isError=False,
        structuredContent=None,
        content=[SimpleNamespace(text="station-a"), SimpleNamespace(text="station-b")],
    )
    normalized = normalize_mcp_call_result("t", call_result)
    assert normalized["ok"] is True
    assert normalized["data"] == "station-a\nstation-b"


def test_normalize_mcp_call_result_prefers_structured():
    call_result = SimpleNamespace(
        isError=False,
        structuredContent={"revenue": 5000},
        content=[SimpleNamespace(text="ignored")],
    )
    normalized = normalize_mcp_call_result("t", call_result)
    assert normalized["data"] == {"revenue": 5000}


def test_normalize_mcp_call_result_error_flag():
    call_result = SimpleNamespace(isError=True, content=[], structuredContent=None)
    normalized = normalize_mcp_call_result("t", call_result)
    assert normalized["ok"] is False


def test_validate_against_schema_missing_required():
    tool = SimpleNamespace(
        name="t",
        parameters_schema={
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
    )
    assert validate_against_schema({}, tool) == "Missing required argument 'station_id'."


def test_validate_against_schema_unexpected_argument():
    tool = SimpleNamespace(
        name="t",
        parameters_schema={
            "properties": {"station_id": {"type": "string"}},
            "required": [],
        },
    )
    assert "Unexpected argument" in validate_against_schema({"hack": "1"}, tool)


def test_validate_against_schema_ok():
    tool = SimpleNamespace(
        name="t",
        parameters_schema={
            "properties": {"station_id": {"type": "string"}},
            "required": ["station_id"],
        },
    )
    assert validate_against_schema({"station_id": "s1"}, tool) is None


def test_summarize_tool_results():
    summary = summarize_tool_results(
        [
            {"tool": "a", "ok": True, "data": {"x": 1}, "error": None},
            {"tool": "b", "ok": False, "data": None, "error": "bad args"},
        ]
    )
    assert "[a] OK" in summary
    assert "[b] ERROR: bad args" in summary
