import unittest

from py_hotkey_carbon.hotkey import _KEYCODES, _MODIFIERS, register

IS_MAC = __import__("platform").system() == "Darwin"


class TestMasks(unittest.TestCase):
    """Carbon EventModifiers are low-bit masks (Events.h) — getting these
    wrong silently registers a *bare key* hotkey (the classic bug)."""

    def test_modifier_masks_match_carbon_headers(self):
        self.assertEqual(_MODIFIERS["cmd"], 0x0100)  # cmdKey
        self.assertEqual(_MODIFIERS["shift"], 0x0200)  # shiftKey
        self.assertEqual(_MODIFIERS["option"], 0x0800)  # optionKey
        self.assertEqual(_MODIFIERS["ctrl"], 0x1000)  # controlKey

    def test_keycodes_cover_common_keys(self):
        for key in ("t", "space", "return", "up", "a", "z", "0", "9"):
            self.assertIn(key, _KEYCODES)


@unittest.skipUnless(IS_MAC, "Carbon only exists on macOS")
class TestRegistration(unittest.TestCase):
    def test_unknown_key_returns_false(self):
        self.assertFalse(register(lambda: None, key="not-a-key"))

    def test_double_register_is_idempotent(self):
        first = register(lambda: None, key="t", modifiers=("cmd", "option"))
        self.assertTrue(register(lambda: None, key="t", modifiers=("cmd", "option")))
        self.assertTrue(first)  # both calls agree on success


if __name__ == "__main__":
    unittest.main()
