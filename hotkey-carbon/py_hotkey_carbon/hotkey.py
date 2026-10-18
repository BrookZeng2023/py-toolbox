#!/usr/bin/env python3
"""Global hotkeys for macOS apps via ctypes -> Carbon RegisterEventHotKey.

The permission-free way for any running app (menu-bar helpers, Python
daemons with a runloop) to own a system-wide shortcut: no Accessibility
approval, fires while any application is frontmost, delivered on the
app's main runloop.

Pure ctypes against Carbon.framework -- zero dependencies. Notably
pyobjc does not ship Carbon bindings (HIToolbox hotkey API), so this is
the lightest path from Python. Degrades to False when Carbon is missing
or the caller has no runloop; treat that as "no shortcut today", never
an error.

Usage:
    from py_hotkey_carbon import register
    register(lambda: print("hit"), key="t", modifiers=("cmd", "option"))
"""

from __future__ import annotations

import ctypes
import ctypes.util
import logging
import threading

logger = logging.getLogger(__name__)

_carbon_path = "/System/Library/Frameworks/Carbon.framework/Carbon"
_carbon = None
try:
    _carbon = ctypes.CDLL(_carbon_path)
except OSError:
    logger.info("Carbon framework unavailable — global hotkey disabled")

# modifier name → Carbon EventModifiers mask (cmdKey=1<<8) (from Events.h)
_MODIFIERS = {
    "cmd": 0x0100,  # cmdKey
    "option": 0x0800,  # optionKey
    "ctrl": 0x1000,  # controlKey
    "shift": 0x0200,  # shiftKey
}

# key name → virtual keycode (Events.h kVK_ANSI_*)
_KEYCODES = {
    "a": 0x00,
    "s": 0x01,
    "d": 0x02,
    "f": 0x03,
    "h": 0x04,
    "g": 0x05,
    "z": 0x06,
    "x": 0x07,
    "c": 0x08,
    "v": 0x09,
    "b": 0x0B,
    "q": 0x0C,
    "w": 0x0D,
    "e": 0x0E,
    "r": 0x0F,
    "y": 0x10,
    "t": 0x11,
    "u": 0x20,
    "i": 0x22,
    "o": 0x1F,
    "p": 0x23,
    "l": 0x25,
    "j": 0x26,
    "k": 0x28,
    "n": 0x2D,
    "m": 0x2E,
    "0": 0x1D,
    "1": 0x12,
    "2": 0x13,
    "3": 0x14,
    "4": 0x15,
    "6": 0x16,
    "5": 0x17,
    "=": 0x18,
    "9": 0x19,
    "7": 0x1A,
    "-": 0x1B,
    "8": 0x1C,
    "/": 0x1C,
    "space": 0x31,
    "return": 0x24,
    "tab": 0x30,
    "escape": 0x35,
    "left": 0x7B,
    "right": 0x7C,
    "down": 0x7D,
    "up": 0x7E,
    ",": 0x2B,
    ".": 0x2F,
    ";": 0x29,
    "'": 0x27,
    "[": 0x21,
    "]": 0x1E,
}

_HotKeyID = ctypes.c_uint32(0x54524345)  # 'TRCE'
_ref: dict = {"hotkey": None, "handler": None, "cb": None}
_lock = threading.Lock()


def _mask_from(names) -> int:
    mask = 0
    for n in names:
        mask |= _MODIFIERS.get(str(n).lower(), 0)
    return mask


def register(callback, key: str = "t", modifiers=("cmd", "option")) -> bool:
    """Register the system-wide hotkey; ``callback`` fires on the main thread.

    Returns False when Carbon is unavailable or registration fails — callers
    treat that as "no shortcut today", never as an error.
    """
    if _carbon is None:
        return False
    key = str(key).lower()
    keycode = _KEYCODES.get(key)
    if keycode is None:
        logger.warning("unknown hotkey key %r — disabled", key)
        return False
    with _lock:
        if _ref["hotkey"] is not None:
            return True  # already registered

        handler_t = ctypes.CFUNCTYPE(
            ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
        )

        def _on_hotkey(_call_ref, _event, _user):
            try:
                callback()
            except Exception:
                logger.warning("hotkey callback failed", exc_info=True)
            return 0

        handler = handler_t(_on_hotkey)

        carbon = _carbon
        carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
        target = carbon.GetApplicationEventTarget()

        # EventTypeSpec {u32 class, u32 kind}; kEventClassKeyboard='keyb', kEventHotKeyPressed=6
        class EventTypeSpec(ctypes.Structure):
            _fields_ = [("eventClass", ctypes.c_uint32), ("eventKind", ctypes.c_uint32)]

        spec = EventTypeSpec(int.from_bytes(b"keyb", "big"), 6)
        handler_ref = ctypes.c_void_p()
        carbon.InstallEventHandler(
            ctypes.c_void_p(target),
            handler,
            1,
            ctypes.byref(spec),
            None,
            ctypes.byref(handler_ref),
        )
        if not handler_ref.value:
            logger.warning("InstallEventHandler failed — hotkey disabled")
            return False

        # EventHotKeyID {u32 signature, u32 id}
        class HotKeyID(ctypes.Structure):
            _fields_ = [("signature", ctypes.c_uint32), ("id", ctypes.c_uint32)]

        hotkey_id = HotKeyID(int.from_bytes(b"TRCE", "big"), 1)
        hotkey_ref = ctypes.c_void_p()
        carbon.RegisterEventHotKey(
            ctypes.c_uint32(keycode),
            ctypes.c_uint32(_mask_from(modifiers)),
            hotkey_id,
            ctypes.c_void_p(target),
            ctypes.c_uint32(0),
            ctypes.byref(hotkey_ref),
        )
        status_ok = bool(hotkey_ref.value)
        if not status_ok:
            logger.warning("RegisterEventHotKey failed — hotkey disabled")
            return False

        _ref.update(hotkey=hotkey_ref, handler=handler, cb=callback)
        logger.info("global hotkey registered: %s", _pretty(key, modifiers))
        return True


def unregister() -> None:
    """Best-effort unregistration (not needed for a process-lifetime shortcut)."""
    with _lock:
        hk = _ref.get("hotkey")
        if hk and _carbon is not None:
            try:
                _carbon.UnregisterEventHotKey(
                    ctypes.c_void_p(hk.value if hasattr(hk, "value") else hk)
                )
            except Exception:
                logger.debug("unregister failed", exc_info=True)
        _ref.update(hotkey=None, handler=None, cb=None)


def _pretty(key: str, modifiers) -> str:
    sym = {"cmd": "⌘", "option": "⌥", "ctrl": "⌃", "shift": "⇧"}
    mods = "".join(sym.get(m, m + "+") for m in modifiers)
    return f"{mods}{key.upper()}"
