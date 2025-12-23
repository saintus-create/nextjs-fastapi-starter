from __future__ import annotations

import httpx
import structlog
from typing import Any, List, Dict

log = structlog.get_logger(__name__)


class MCPClient:
    """Thin HTTP client for external MCP servers (e.g. shadcn/ui)."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=10.0)
        log.debug("MCPClient init", base_url=self.base_url)

    def discover(self) -> List[Dict[str, Any]]:
        resp = self.client.get("/mcp/discover")
        resp.raise_for_status()
        return resp.json()

    def invoke(self, tool: str, action: str, args: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"tool": tool, "action": action, "args": args}
        resp = self.client.post("/mcp/invoke", json=payload)
        resp.raise_for_status()
        return resp.json()
