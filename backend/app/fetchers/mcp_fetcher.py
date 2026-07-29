"""
Fetches tool definitions from an MCP server via `tools/list`.

Supports HTTP transport directly (JSON-RPC over POST). SSE transport is
stubbed with a clear error for now — full SSE session handling is real
scope and shouldn't block the MVP; ship HTTP first, add SSE when a
customer actually needs it.
"""
import httpx

from app.fetchers.rest_fetcher import _reject_private_targets, FetchError
from app.fetchers.retry import with_transient_retry


def fetch_mcp_tools(server_url: str, transport: str = "http", timeout: float = 15.0) -> dict:
    """Returns a raw `{"tools": [...]}` dict from an MCP server's tools/list call."""
    if transport == "sse":
        raise FetchError(
            "SSE transport isn't supported yet — use an HTTP-transport MCP endpoint for now."
        )

    _reject_private_targets(server_url)

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {},
    }

    @with_transient_retry
    def _post() -> httpx.Response:
        resp = httpx.post(server_url, json=payload, timeout=timeout,
                           headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        return resp

    try:
        resp = _post()
        body = resp.json()
    except httpx.HTTPError as e:
        raise FetchError(f"Failed to reach MCP server: {e}") from e
    except ValueError as e:
        raise FetchError(f"MCP server returned invalid JSON: {e}") from e

    if "error" in body:
        raise FetchError(f"MCP server returned an error: {body['error']}")

    result = body.get("result", {})
    return {"tools": result.get("tools", [])}
