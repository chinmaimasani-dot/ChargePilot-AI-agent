"""Normalization of MCP tool outputs and errors (Member 4).

Every tool result entering LangGraph is a dict:

    {"tool": <name>, "ok": true|false, "data": <payload>, "error": <str|None>}

so graph nodes never depend on raw MCP types or exception shapes.
"""

from typing import Any


def normalize_tool_result(tool_name: str, payload: Any) -> dict:
    """Wrap a successful tool payload."""
    return {"tool": tool_name, "ok": True, "data": payload, "error": None}


def normalize_tool_error(tool_name: str, message: str) -> dict:
    """Wrap a controlled, LLM-safe tool error."""
    return {"tool": tool_name, "ok": False, "data": None, "error": message}


def normalize_mcp_call_result(tool_name: str, call_result: Any) -> dict:
    """Convert an MCP `CallToolResult` into the normalized shape.

    The MCP Python SDK returns objects with `.content` (a list of content
    blocks) and `.isError`. We flatten text blocks; structured payloads are
    passed through when present.
    """
    if getattr(call_result, "isError", False):
        return normalize_tool_error(
            tool_name, "The tool reported an error while executing."
        )

    data: Any = None
    structured = getattr(call_result, "structuredContent", None)
    if structured is not None:
        data = structured
    else:
        texts = []
        for block in getattr(call_result, "content", None) or []:
            text = getattr(block, "text", None)
            if text is not None:
                texts.append(text)
        if texts:
            data = "\n".join(texts)

    return normalize_tool_result(tool_name, data)


def summarize_tool_results(tool_results: list[dict]) -> str:
    """Render tool results compactly for the response-generation prompt."""
    if not tool_results:
        return "No tool results."
    lines = []
    for result in tool_results:
        if result.get("ok"):
            lines.append(f"[{result['tool']}] OK: {result.get('data')}")
        else:
            lines.append(f"[{result['tool']}] ERROR: {result.get('error')}")
    return "\n".join(lines)
