# py-hotkey-carbon

**中文** | [English](#english)

macOS 上**免权限的全局快捷键**——纯 `ctypes` 直调 `Carbon.framework` 的 `RegisterEventHotKey`，零依赖。

```bash
pip install py-hotkey-carbon
```

```python
from py_hotkey_carbon import register

register(lambda: print("⌘⌥T 触发!"), key="t", modifiers=("cmd", "option"))
# 保持 runloop 存活（任何 GUI 程序 / rumps 菜单栏应用自带）
```

## 为什么需要它

- **不要辅助功能权限**：`RegisterEventHotKey` 是经典的 Carbon 快捷键 API——系统级生效、任何 App 在前台都能触发、在你的 runloop 上投递。
- **pyobjc 不带它**：HIToolbox 热键 API 没有 pyobjc 绑定（`pyobjc-framework-Carbon` 近期版本甚至没发布），ctypes 是最轻的路径。
- **优雅降级**：Carbon 缺失或无 runloop 时 `register()` 返回 `False`，当作"今天没有快捷键"，绝不是错误。

支持的键：单字符、`"space"` / `"return"` / `"tab"` / `"escape"`、方向键、数字。修饰键：`"cmd"` / `"shift"` / `"option"` / `"ctrl"`。

## 本库固化过的坑

Carbon 的 `EventModifiers` 是**低位**掩码（`cmdKey = 1 << 8`）。如果传成 NSEvent 风格的高位值，低位全零，你会静默注册出**裸键**快捷键——按一下普通 `T` 就触发。本库的掩码对齐头文件，且有测试钉死。

抽取自生产级 macOS 菜单栏应用（Trace），驱动其 ⌘⌥T 面板开关。

## 测试

```bash
python -m unittest discover tests   # macOS 上
```

MIT — Brook Zeng

---

<a name="english"></a>

# py-hotkey-carbon (English)

Permission-free **global hotkeys on macOS** from Python — pure `ctypes` against `Carbon.framework`'s `RegisterEventHotKey`. Zero dependencies.

```bash
pip install py-hotkey-carbon
```

```python
from py_hotkey_carbon import register

register(lambda: print("⌘⌥T hit!"), key="t", modifiers=("cmd", "option"))
# keep a runloop alive (any GUI app / rumps already has one)
```

## Why

- **No Accessibility permission.** `RegisterEventHotKey` is the classic Carbon API for app-owned shortcuts: system-wide, fires while any app is frontmost, delivered on your runloop.
- **pyobjc doesn't ship it.** The HIToolbox hotkey API has no pyobjc bindings (`pyobjc-framework-Carbon` is not even published for recent series), so ctypes is the lightest path.
- **Graceful degradation.** Missing Carbon or no runloop → `register()` returns `False`; treat it as "no shortcut today", never an error.

Keys: single chars, `"space"`, `"return"`, `"tab"`, `"escape"`, arrows, digits. Modifiers: `"cmd"`, `"shift"`, `"option"`, `"ctrl"`.

## The gotcha this library encodes

Carbon `EventModifiers` are **low-bit** masks (`cmdKey = 1 << 8`). Pass NSEvent-style high-bit values and the low bits are all zero — you silently register a *bare key*, so pressing plain `T` starts triggering your app. The masks here match the headers, and a test pins them.

Extracted from a production macOS menu-bar app (Trace), where it powers the ⌘⌥T panel toggle.

## Test

```bash
python -m unittest discover tests   # on macOS
```

MIT — Brook Zeng
