"""mcp-stdio-lite: minimal MCP stdio server, pure stdlib."""

from .server import McpServer, PROTOCOL_VERSION

__version__ = "0.1.0"
__all__ = ["McpServer", "PROTOCOL_VERSION"]
