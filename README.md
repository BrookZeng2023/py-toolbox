# py-toolbox

**中文** | [English](#english)

从生产应用中抽出的小型 Python 工具集——每个组件独立可装、独立测试、零依赖（纯标准库）。

| 组件 | 干什么 | 装 |
|------|--------|-----|
| [`hotkey-carbon/`](hotkey-carbon/) | macOS 免权限全局快捷键（ctypes→Carbon） | `pip install "git+https://github.com/BrookZeng2023/py-toolbox.git#subdirectory=hotkey-carbon"` |
| [`mcp-stdio-lite/`](mcp-stdio-lite/) | 极简 MCP stdio 服务器（纯 stdlib JSON-RPC） | `…#subdirectory=mcp-stdio-lite` |
| [`citation-gate/`](citation-gate/) | LLM 引用闸：引用对不上就丢弃 | `…#subdirectory=citation-gate` |
| [`layering-gate/`](layering-gate/) | AST 分层闸门：依赖方向即测试 | `…#subdirectory=layering-gate` |

每个组件目录有自己的 README（中英双语）和测试。统一约定：

- 纯标准库，无第三方依赖
- 逐字从生产代码抽取（出处见各组件 README），不是玩具
- `python -m unittest discover tests` 一条命令验证

将来某 个组件有真实用户了，再单独拆出上 PyPI，互不影响。

MIT — Brook Zeng

---

<a name="english"></a>

# py-toolbox (English)

Small Python utilities extracted from production apps — each component installs and tests independently, zero dependencies (pure stdlib).

| Component | What it does | Install |
|-----------|--------------|---------|
| [`hotkey-carbon/`](hotkey-carbon/) | Permission-free global hotkeys on macOS (ctypes→Carbon) | `pip install "git+https://github.com/BrookZeng2023/py-toolbox.git#subdirectory=hotkey-carbon"` |
| [`mcp-stdio-lite/`](mcp-stdio-lite/) | Minimal MCP stdio server (pure-stdlib JSON-RPC) | `…#subdirectory=mcp-stdio-lite` |
| [`citation-gate/`](citation-gate/) | LLM citation gate: drop claims that don't resolve | `…#subdirectory=citation-gate` |
| [`layering-gate/`](layering-gate/) | AST layering gate: dependency direction as a test | `…#subdirectory=layering-gate` |

Each component directory carries its own README (bilingual) and tests. House rules:

- Pure stdlib, no third-party dependencies
- Extracted verbatim from production code (see each component's README), not toys
- `python -m unittest discover tests` verifies everything

When a component gains real users, it can split out and go to PyPI independently.

MIT — Brook Zeng
