import json
import unittest
from io import StringIO

from mcp_stdio_lite import McpServer


def _make_server() -> McpServer:
    server = McpServer("demo", "0.1.0")

    @server.tool("add", "Add two integers", {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    })
    def add(a: int, b: int) -> dict:
        return {"sum": a + b}

    @server.tool("boom", "Always raises")
    def boom() -> dict:
        raise RuntimeError("kapow")

    return server


def _run(server: McpServer, lines: list[str]) -> list[dict]:
    out = StringIO()
    server.serve(stdin=StringIO("\n".join(lines) + "\n"), stdout=out)
    return [json.loads(l) for l in out.getvalue().splitlines()]


class TestProtocol(unittest.TestCase):
    def test_full_session_replies_once_per_request(self):
        server = _make_server()
        replies = _run(server, [
            '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}',
            '{"jsonrpc":"2.0","method":"notifications/initialized"}',
            '{"jsonrpc":"2.0","id":2,"method":"tools/list"}',
            '{"jsonrpc":"2.0","id":3,"method":"ping"}',
        ])
        self.assertEqual([r["id"] for r in replies], [1, 2, 3])  # notification got none
        self.assertEqual(replies[0]["result"]["serverInfo"]["name"], "demo")
        self.assertEqual(
            [t["name"] for t in replies[1]["result"]["tools"]], ["add", "boom"]
        )
        self.assertEqual(replies[2]["result"], {})

    def test_tool_call_success_and_arguments_passthrough(self):
        replies = _run(_make_server(), [
            '{"jsonrpc":"2.0","id":1,"method":"tools/call",'
            '"params":{"name":"add","arguments":{"a":2,"b":40}}}',
        ])
        body = replies[0]["result"]
        self.assertFalse(body["isError"])
        self.assertEqual(json.loads(body["content"][0]["text"]), {"sum": 42})

    def test_tool_exception_is_error_not_crash(self):
        replies = _run(_make_server(), [
            '{"jsonrpc":"2.0","id":9,"method":"tools/call",'
            '"params":{"name":"boom","arguments":{}}}',
        ])
        body = replies[0]["result"]
        self.assertTrue(body["isError"])
        self.assertIn("kapow", body["content"][0]["text"])

    def test_unknown_method_and_tool(self):
        replies = _run(_make_server(), [
            '{"jsonrpc":"2.0","id":1,"method":"nope"}',
            '{"jsonrpc":"2.0","id":2,"method":"tools/call",'
            '"params":{"name":"nope","arguments":{}}}',
        ])
        self.assertEqual(replies[0]["error"]["code"], -32601)
        self.assertTrue(replies[1]["result"]["isError"])

    def test_malformed_and_blank_lines_are_silent(self):
        replies = _run(_make_server(), ["not json", "", "   "])
        self.assertEqual(replies, [])


if __name__ == "__main__":
    unittest.main()
