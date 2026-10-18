# mcp-stdio-lite

**中文** | [English](#english)

极简 **MCP (Model Context Protocol) stdio 服务器**——纯标准库，零 SDK 依赖。

```bash
pip install mcp-stdio-lite
```

```python
from mcp_stdio_lite import McpServer

server = McpServer("my-tools", "1.0.0")

@server.tool("add", "两个整数相加", {
    "type": "object",
    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    "required": ["a", "b"],
})
def add(a: int, b: int) -> dict:
    return {"sum": a + b}

server.serve()   # stdin/stdout 循环，EOF 退出
```

接入 Claude Code：

```bash
claude mcp add mytools -- python3 your_server.py
```

## 协议面

实现 MCP stdio 传输需要的全部：`initialize`（协议版本 2024-11-05）、`tools/list`、`tools/call`、`ping`。讲究的地方都在细节里：

- **stdout 只走协议消息**，诊断一律 stderr
- 工具抛异常 → `isError: true` 的正常应答，**循环永不崩**
- 通知（`notifications/*`）不回包；坏行记日志跳过；EOF 干净退出
- `serve(stdin=..., stdout=...)` 可注入流，测试就是喂 `StringIO`

## 为什么

官方 MCP Python SDK 拉起一整棵依赖树，而"把几个函数暴露给 Claude"只需要一个正确的 JSON-RPC 循环。抽取自生产级应用（Trace 的聊天记录 MCP 服务，5 个工具、真机 60 万条数据验证）。

## 测试

```bash
python -m unittest discover tests
```

MIT — Brook Zeng

---

<a name="english"></a>

# mcp-stdio-lite (English)

Minimal **MCP (Model Context Protocol) stdio server** — pure stdlib, no SDK.

```bash
pip install mcp-stdio-lite
```

```python
from mcp_stdio_lite import McpServer

server = McpServer("my-tools", "1.0.0")

@server.tool("add", "Add two integers", {
    "type": "object",
    "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    "required": ["a", "b"],
})
def add(a: int, b: int) -> dict:
    return {"sum": a + b}

server.serve()   # stdin/stdout loop, exits on EOF
```

Wire into Claude Code:

```bash
claude mcp add mytools -- python3 your_server.py
```

## Protocol surface

Everything an MCP stdio transport needs: `initialize` (protocol 2024-11-05), `tools/list`, `tools/call`, `ping`. The details are where the care is:

- **stdout carries protocol messages exclusively**; diagnostics go to stderr
- A raising tool → an `isError: true` reply — **the loop never crashes**
- Notifications (`notifications/*`) get no reply; malformed lines are logged and skipped; EOF exits cleanly
- `serve(stdin=..., stdout=...)` takes injectable streams — tests just feed `StringIO`

## Why

The official MCP Python SDK pulls in a dependency tree, while "expose a few functions to Claude" needs one correct JSON-RPC loop. Extracted from a production app (Trace's chat-records MCP server: 5 tools, verified against 600k real rows).

## Test

```bash
python -m unittest discover tests
```

MIT — Brook Zeng
