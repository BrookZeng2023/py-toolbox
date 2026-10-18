"""py-hotkey-carbon: permission-free global hotkeys on macOS, pure ctypes.

Re-exports :func:`register` and :func:`unregister`.
"""

from .hotkey import register, unregister

__version__ = "0.1.0"
__all__ = ["register", "unregister"]
