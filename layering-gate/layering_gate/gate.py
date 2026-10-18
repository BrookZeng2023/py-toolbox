"""AST layering gate — enforce dependency direction as a test, not a hope.

**中文** · **English**

定义分层（如 interfaces → services → store → core），本模块扫描包内
所有 import（含相对导入与惰性导入），任何一层引用了不允许的方向即
返回违规。当作一个单元测试跑：`LayeringGate(...).assert_clean()`。

Define your layers (e.g. interfaces → services → store → core); this
module resolves every import in the package (relative, absolute, and
lazy in-function imports) via AST and reports any edge that reaches an
unallowed layer. Run it as a unit test: `LayeringGate(...).assert_clean()`.

    from layering_gate import LayeringGate

    gate = LayeringGate(
        pkg_dir="src/mypkg",
        allowed={
            "core": {"core", "config"},
            "store": {"core", "store", "config"},
            "services": {"core", "store", "services", "config"},
            "interfaces": {"core", "store", "services", "interfaces", "config"},
        },
        # modules living at the package top level may import anything:
        top_level_unrestricted=True,
    )
    gate.assert_clean()   # raises AssertionError listing violations
"""

from __future__ import annotations

import ast
import os


def _resolve_imports(path: str, pkg_root: str) -> set[str]:
    """Dotted, package-absolute targets of every import in one module."""
    with open(path, encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=path)
    rel = os.path.relpath(path, pkg_root)
    parts = rel.split(os.sep)
    here = ".".join(parts[:-1])  # dotted package of this module ('' at top)
    pkg_name = os.path.basename(pkg_root)
    targets: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module or ""
                if base == pkg_name or base.startswith(pkg_name + "."):
                    if base == pkg_name:  # from pkg import a, b
                        for a in node.names:
                            if a.name != "*":
                                targets.add(f"{pkg_name}.{a.name}")
                    else:
                        targets.add(base)
                continue
            # relative: level 1 = this package, each extra level pops one
            base = here
            for _ in range(node.level - 1):
                base = base.rsplit(".", 1)[0] if "." in base else ""
            if node.module:
                target = f"{base}.{node.module}" if base else node.module
                targets.add(f"{pkg_name}.{target}")
            else:
                for a in node.names:
                    if a.name == "*":
                        continue
                    target = f"{base}.{a.name}" if base else a.name
                    targets.add(f"{pkg_name}.{target}")
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.name == pkg_name or a.name.startswith(pkg_name + "."):
                    targets.add(a.name)
    return targets


class LayeringGate:
    """Scan ``pkg_dir`` and check every module's imports against ``allowed``."""

    def __init__(
        self,
        pkg_dir: str,
        allowed: dict[str, set[str]],
        skip_dirs: tuple[str, ...] = ("__pycache__",),
        top_level_unrestricted: bool = True,
    ) -> None:
        self.pkg_dir = os.path.abspath(pkg_dir)
        self.allowed = allowed
        self.skip_dirs = skip_dirs
        self.top_level_unrestricted = top_level_unrestricted

    def violations(self) -> list[str]:
        found: list[str] = []
        for root, dirs, files in os.walk(self.pkg_dir):
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]
            rel_root = os.path.relpath(root, self.pkg_dir)
            layer = "" if rel_root == "." else rel_root.split(os.sep)[0]
            if layer not in self.allowed:  # unmapped dirs are unrestricted
                continue
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                for target in _resolve_imports(path, self.pkg_dir):
                    segs = target.split(".")
                    if len(segs) < 2:
                        continue
                    dest = segs[1]
                    if dest not in self.allowed[layer]:
                        found.append(
                            f"{os.path.relpath(path, self.pkg_dir)} imports {target} "
                            f"(layer '{layer}' may only reach {sorted(self.allowed[layer])})"
                        )
        return found

    def assert_clean(self) -> None:
        bad = self.violations()
        if bad:
            raise AssertionError(
                f"{len(bad)} layering violation(s):\n  " + "\n  ".join(bad)
            )
