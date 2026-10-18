# layering-gate

**中文** | [English](#english)

**AST 分层闸门**：把包的依赖方向变成一个单元测试，违反即红。

```bash
pip install layering-gate
```

```python
from layering_gate import LayeringGate

ALLOWED = {
    "core":       {"core", "config"},
    "store":      {"core", "store", "config"},
    "services":   {"core", "store", "services", "config"},
    "interfaces": {"core", "store", "services", "interfaces", "config"},
}

def test_layering():
    LayeringGate("src/mypkg", ALLOWED).assert_clean()  # 违规时列出全部边
```

## 它查什么

AST 扫描包内**每一个** import——模块级、函数体内的惰性导入、相对导入（`from ..store import x`）、绝对导入（`from mypkg.store import x`）全部解析成包内绝对路径，再对照你的分层规则。`core` 一旦 import 了 `services`，测试当场红给你看：

```
AssertionError: 1 layering violation(s):
  core/mod.py imports mypkg.services.mod (layer 'core' may only reach ['config', 'core'])
```

## 为什么

"分层"写在 README 里靠自觉，写进 CI 里才作数。相比 import-linter：不用配置文件、不用额外依赖、一个测试文件内联在测试套件里，相对导入的解析经过生产代码验证（含包深二层的 `..` 边界——这里最容易解析错）。抽取自 Trace 的 `tests/test_layering.py`，守护其四层架构。

## 测试

```bash
python -m unittest discover tests
```

MIT — Brook Zeng

---

<a name="english"></a>

# layering-gate (English)

**AST layering gate**: turn your package's dependency direction into a unit test that goes red on violation.

```bash
pip install layering-gate
```

```python
from layering_gate import LayeringGate

ALLOWED = {
    "core":       {"core", "config"},
    "store":      {"core", "store", "config"},
    "services":   {"core", "store", "services", "config"},
    "interfaces": {"core", "store", "services", "interfaces", "config"},
}

def test_layering():
    LayeringGate("src/mypkg", ALLOWED).assert_clean()  # lists every bad edge on failure
```

## What it checks

An AST scan of **every** import in the package — module-level, lazy imports inside function bodies, relative (`from ..store import x`) and absolute (`from mypkg.store import x`) — resolved to package-absolute paths, then checked against your rules. The moment `core` imports `services`, the test goes red:

```
AssertionError: 1 layering violation(s):
  core/mod.py imports mypkg.services.mod (layer 'core' may only reach ['config', 'core'])
```

## Why

Layering written in a README is a hope; layering written into CI is a law. Versus import-linter: no config file, no extra dependency, one inline test in your suite — and relative-import resolution is battle-tested in production (including the depth-2 `..` boundary, where naive parsers go wrong). Extracted from Trace's `tests/test_layering.py`, which guards its four-layer architecture.

## Test

```bash
python -m unittest discover tests
```

MIT — Brook Zeng
