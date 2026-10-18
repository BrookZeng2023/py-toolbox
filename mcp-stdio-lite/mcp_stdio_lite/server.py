"""Minimal MCP (Model Context Protocol) stdio server — pure stdlib.

Newline-delimited JSON-RPC 2.0 on stdin/stdout, exactly as MCP stdio
transport specifies. No SDK dependency: the whole protocol surface an
MCP host needs from a tool server is initialize / tools/list /
tools/call / ping, and that is all this implements — correctly.

Diagnostics go to stderr only; stdout carries protocol messages
exclusively. Tool exceptions become ``isError: true`` results, never a
crashed loop. Malformed lines are logged and skipped; EOF exits 0.

    from mcp_stdio_lite import McpServer

    server = McpServer("my-tools", "1.0.0")

    @server.tool("add", "Add two integers", {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    })
    def add(a: int, b: int) -> dict:
        return {"sum": a + b}

    server.serve()  # or serve(stdin=..., stdout=...) in tests
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any, Callable, IO, TextIO

logger = logging.getLogger("mcp_stdio_lite")

PROTOCOL_VERSION = "2024-11-05"
METHOD_NOT_FOUND = -32601


class McpServer:
    """A read-only MCP tool server over stdio. Tools return JSON-serializable
    values; kwargs arrive straight from the host's ``arguments`` dict."""

    def __init__(self, name: str, version: str = "1.0.0") -> None:
        self.name = name
        self.version = version
        self._tools: dict[str, dict[str, Any]] = {}  # name → {description, schema, fn}
        self._initialized = False

    # ── registration ────────────────────────────────────────────────

    def tool(
        self, name: str, description: str = "", input_schema: dict | None = None
    ) -> Callable:
        """Decorator: register a function as an MCP tool."""

        def deco(fn: Callable) -> Callable:
            self._tools[name] = {
                "description": description,
                "schema": input_schema or {"type": "object", "properties": {}},
                "fn": fn,
            }
            return fn

        return deco

    # ── request handling ────────────────────────────────────────────

    def handle_line(self, line: str) -> dict | None:
        """Parse and dispatch one input line → one response dict (or None
        for notifications/malformed input, which must stay silent)."""
        line = line.strip()
        if not line:
            return None
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("malformed line skipped: %.80s", line)
            return None
        if not isinstance(msg, dict):
            return None
        method = msg.get("method")
        msg_id = msg.get("id")
        if method is None:  # a response we never asked for — ignore
            return None
        if msg_id is None:  # notification → no reply, ever
            if method == "notifications/initialized":
                self._initialized = True
            return None
        return self._dispatch(method, msg_id, msg.get("params") or {})

    def _dispatch(self, method: str, msg_id: Any, params: dict) -> dict:
        if method == "initialize":
            return self._reply(msg_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": self.name, "version": self.version},
            })
        if method == "ping":
            return self._reply(msg_id, {})
        if method == "tools/list":
            return self._reply(msg_id, {"tools": [
                {
                    "name": name,
                    "description": spec["description"],
                    "inputSchema": spec["schema"],
                }
                for name, spec in self._tools.items()
            ]})
        if method == "tools/call":
            name = params.get("name")
            spec = self._tools.get(name) if isinstance(name, str) else None
            if spec is None:
                return self._reply(msg_id, {
                    "content": [{"type": "text", "text": f"unknown tool: {name!r}"}],
                    "isError": True,
                })
            try:
                result = spec["fn"](**(params.get("arguments") or {}))
                return self._reply(msg_id, {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, default=str),
                    }],
                    "isError": False,
                })
            except Exception as e:  # tool failure is data, not a crash
                logger.warning("tool %s failed: %s", name, e)
                return self._reply(msg_id, {
                    "content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}],
                    "isError": True,
                })
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": METHOD_NOT_FOUND, "message": f"unknown method: {method}"},
        }

    @staticmethod
    def _reply(msg_id: Any, result: Any) -> dict:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    # ── main loop ───────────────────────────────────────────────────

    def serve(
        self, stdin: TextIO = sys.stdin, stdout: IO[str] = sys.stdout
    ) -> None:
        """Read lines until EOF; write one JSON reply per request line."""
        for line in stdin:
            reply = self.handle_line(line)
            if reply is not None:
                stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
                stdout.flush()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    print("define tools and call serve(); see module docstring", file=sys.stderr)
