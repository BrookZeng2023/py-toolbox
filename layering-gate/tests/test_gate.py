import os
import tempfile
import textwrap
import unittest

from layering_gate import LayeringGate

ALLOWED = {
    "core": {"core", "config"},
    "store": {"core", "store", "config"},
    "services": {"core", "store", "services", "config"},
    "interfaces": {"core", "store", "services", "interfaces", "config"},
}


def _build_pkg(tmp: str, *, bad_edge: bool, lazy: bool = False) -> str:
    pkg = os.path.join(tmp, "mypkg")
    for sub in ("config", "core", "store", "services", "interfaces"):
        os.makedirs(os.path.join(pkg, sub), exist_ok=True)
        with open(os.path.join(pkg, sub, "__init__.py"), "w"):
            pass
    with open(os.path.join(pkg, "__init__.py"), "w"):
        pass

    def put(rel: str, code: str) -> None:
        with open(os.path.join(pkg, rel), "w") as f:
            f.write(textwrap.dedent(code))

    put("core/mod.py", "X = 1\n")
    put("store/mod.py", "from ..core.mod import X\nY = X\n")
    if lazy:
        put("services/mod.py", "def f():\n    from ..store.mod import Y\n    return Y\n")
    else:
        put("services/mod.py", "from ..store.mod import Y\n")
    if bad_edge:
        # core reaching upward into services — the violation
        put("core/mod.py", "def g():\n    from ..services.mod import f\n    return f\n")
    put("interfaces/mod.py", "from ..services.mod import f\nfrom mypkg.store.mod import Y\n")
    return pkg


class TestGate(unittest.TestCase):
    def test_clean_package_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = _build_pkg(tmp, bad_edge=False, lazy=True)
            LayeringGate(pkg, ALLOWED).assert_clean()  # no raise

    def test_upward_edge_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = _build_pkg(tmp, bad_edge=True)
            with self.assertRaises(AssertionError) as ctx:
                LayeringGate(pkg, ALLOWED).assert_clean()
            self.assertIn("core/mod.py imports", str(ctx.exception))

    def test_lazy_imports_are_seen(self):
        # the lazy upward edge lives inside a function body — AST still finds it
        with tempfile.TemporaryDirectory() as tmp:
            pkg = _build_pkg(tmp, bad_edge=True, lazy=False)
            gate = LayeringGate(pkg, ALLOWED)
            self.assertTrue(any("services" in v for v in gate.violations()))


if __name__ == "__main__":
    unittest.main()
