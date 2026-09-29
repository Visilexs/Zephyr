# Zephyr UI

An immediate-mode GUI toolkit for Zephyr — a native Win32 window drawn through
GDI (real TrueType text, crisp filled rects), double-buffered so it never
flickers, with mouse and keyboard input polled each frame. Pure Zephyr on top of
the `win()` FFI; a compiled program imports only `kernel32.dll`, `user32.dll`,
and `gdi32.dll`. No C, no external UI framework.

```zephyr
import "ui/ui.zeph"

var count = 0
var on = true
var volume = 0.5

uiInitialize("Hello", 480, 320)
while uiRunning() {
    uiBeginFrame()
    uiPanel(24, 24, 300, 260, "Demo")
    if uiButton(1, "Click me") { count += 1 }
    uiLabel("clicked " + (count as str) + " times")
    on = uiCheckbox(2, "Enabled", on)
    volume = uiSlider(3, "Volume", volume, 0.0, 1.0)
    uiEndFrame()
    let s = win("Sleep", 12)
}
```

```
zc.exe --rt examples\ui_demo.zeph ui_demo.exe && .\ui_demo.exe
```

## Concepts

**Immediate mode.** There is no widget tree and no retained object state. You
call widget functions every frame; each one draws itself *and* returns what
happened. This makes UIs a plain function of your program's variables.

**Functional widgets.** Zephyr has no pointers, so widgets that hold a value
take the current value and **return the new one** — you store it yourself:

```zephyr
on     = uiCheckbox(id, "On", on)        // returns the toggled value
volume = uiSlider(id, "Vol", volume, 0.0, 1.0)   // returns the dragged value
quality = uiRadio(id, "High", quality, 2)         // returns the selected value
name   = uiTextBox(id, name)             // returns the edited string
```

Action widgets return a `bool` that is true only on the frame they fire:

```zephyr
if uiButton(id, "Save") { save() }
```

**IDs.** Every interactive widget takes a unique integer `id` so the toolkit can
track hover/active/focus across frames. Give each widget a distinct constant.

## Lifecycle

| Call | Purpose |
|------|---------|
| `uiInitialize(title, width, height)` | create the window and fonts (once, before the loop) |
| `uiRunning() -> bool` | pump messages; false once the window is closed |
| `uiBeginFrame()` | start a frame: poll input, clear, reset layout |
| `uiEndFrame()` | present the back buffer to the window |

The window is resizable; the back buffer follows the client size automatically.

## Layout

Widgets stack vertically inside the current panel. Use these to arrange them:

| Call | Effect |
|------|--------|
| `uiPanel(x, y, width, height, title)` | draw a titled container; following widgets flow inside it |
| `uiSameLine()` | place the next widget to the right of the previous one |
| `uiSpacing()` | add a little vertical gap |
| `uiSeparator()` | a horizontal divider line |

## Widgets

| Call | Returns | Notes |
|------|---------|-------|
| `uiLabel(text)` | — | normal text |
| `uiDimText(text)` | — | secondary/greyed text |
| `uiHeading(text)` | — | bold section heading |
| `uiKeyValue(label, value)` | — | `label ……… value` read-out row |
| `uiButton(id, label)` | `bool` | auto-width; true on click |
| `uiButtonWide(id, label)` | `bool` | full-width button |
| `uiCheckbox(id, label, value)` | `bool` | new checked state |
| `uiRadio(id, label, current, optionValue)` | `int` | `optionValue` if clicked, else `current` |
| `uiSlider(id, label, value, minimum, maximum)` | `float` | draggable; shows value |
| `uiSliderInt(id, label, value, minimum, maximum)` | `int` | integer slider |
| `uiProgressBar(fraction, label)` | — | 0..1 bar with optional caption |
| `uiTextBox(id, value)` | `str` | click to focus, then type; new string |
| `uiTab(id, label, current, index)` | `int` | tab in a tab bar (use `uiSameLine`) |
| `uiCollapsingHeader(id, label, open)` | `bool` | section header; guard body with `if` |

### Radio group

```zephyr
quality = uiRadio(20, "Low",    quality, 0)
quality = uiRadio(21, "Medium", quality, 1)
quality = uiRadio(22, "High",   quality, 2)
```

### Tab bar

```zephyr
tab = uiTab(1, "General",  tab, 0)  uiSameLine()
tab = uiTab(2, "Graphics", tab, 1)  uiSameLine()
tab = uiTab(3, "Audio",    tab, 2)
if tab == 0 { ... }
```

### Collapsing section

```zephyr
advanced = uiCollapsingHeader(5, "Advanced", advanced)
if advanced {
    fov = uiSlider(6, "FOV", fov, 60.0, 120.0)
}
```

### Text input

Click a text field to focus it (a blinking caret appears), then type. Supports
letters, digits, space, common punctuation, Shift, and Backspace. Clicking
elsewhere drops focus.

```zephyr
name = uiTextBox(40, name)
uiLabel("Hello, " + name)
```

## IDE-scale primitives

Beyond the basic widgets, the toolkit has the building blocks for full
application chrome — `examples/ide.zeph` uses them to recreate a JetBrains-style
IDE (toolbar, split panes, tree views, a syntax-coloured code editor, dockable
tool windows, status bar).

| Call | Purpose |
|------|---------|
| `uiVerticalSplit(id, x, y, height, minimum, maximum)` | draggable vertical split bar; returns new x |
| `uiHorizontalSplit(id, y, x, width, minimum, maximum)` | draggable horizontal split bar; returns new y |
| `uiScrollBegin(id, x, y, width, height, contentHeight, offset)` | begin a clipped, scrollable region (mouse-wheel + scrollbar); returns clamped offset |
| `uiScrollEnd()` | end it; **returns the measured content height** to feed back next frame |
| `uiTreeRow(id, depth, label, hasChildren, icon)` | one tree row (indent, chevron expander, icon, rounded full-width selection); returns whether open — draw children when true |
| `uiIcon(kind, color)` | pack an icon for `uiTreeRow`: 1 folder, 2 file, 3 database, 4 table, 5 status dot, 0 plain swatch |
| `fillRoundRect(x, y, width, height, cornerDiameter, color)` / `frameRoundRect(...)` | rounded fill / outline (r ≈ 8-10 for the JetBrains look) |
| `drawChevronDown(x, y, color)` / `drawChevronRight(x, y, color)` | small chevron glyphs (dropdowns, expanders) |
| `uiTreeSelected()` | id of the selected tree row |
| `uiTextRun(x, y, text, color)` | draw a text run, return its width (build colour-coded lines) |
| `uiUseMonospaceFont()` / `uiUseNormalFont()` | switch to the monospace / UI font |
| `uiClip(x, y, width, height)` / `uiClipOff()` | set / clear a clip rect |
| `uiAbsoluteButton(id, x, y, width, height, label)` | absolutely-positioned button (toolbars, chrome) |
| `uiFlatButton(id, x, y, width, height, glyph, hotColor)` | flat clickable region (icon buttons) |
| `uiFlatTab(id, x, y, width, height, label, active)` | flat document/tool tab |
| `uiWidth()` / `uiHeight()` | client width / height |

**Trees are retained.** `uiTreeRow` keeps each node's expand and selection
state internally (keyed by `id`), so you just call it for every node every frame
and it remembers what's open. Wrap children in `if uiTreeRow(...) { ... }`.

**Scroll regions self-size.** Pass last frame's content height in and store what
`uiScrollEnd()` returns, so the scrollbar thumb is correct after one frame:

```zephyr
off = uiScrollBegin(id, x, y, w, h, contentH, off)
drawRows()
contentH = uiScrollEnd()
```

**Mouse wheel** is captured in the message pump, so scrolling works with no
window procedure.

> One gotcha when you copy the IDE example: any global whose *initialiser* must
> run (e.g. `let SEP = chr(1)`) has to be declared **before** the `while
> uiRunning()` loop — the loop never returns, so top-level statements after it
> never execute. Function *definitions* can live anywhere (they're hoisted); only
> global initialisers are order-sensitive.

## Theme

The default theme matches the JetBrains "New UI" dark palette: one flat surface
colour (`colorPanel`, #2B2D30) everywhere, regions separated by 1px seams that
are *darker* than the surface (`colorBorder`, #1E1F22 — never lighter), rounded
rects for every hover/selection state, `colorActive` (#2E436E) selection blue and
`colorAccent` (#3574F0) accent. Colours live as `COL_*` constants near the top of
`ui.zeph`; change them there to restyle every widget at once.

## How it works

`uiInitialize` registers a window class (with `DefWindowProc` — no callback needed)
and creates two GDI fonts. Each frame, `uiBeginFrame` reads the mouse via
`GetCursorPos`/`ScreenToClient` and buttons/keys via `GetAsyncKeyState`, so input
needs no window procedure. Drawing goes into an off-screen bitmap
(`CreateCompatibleDC` + `CreateCompatibleBitmap`) using `FillRect` and `TextOutA`;
`uiEndFrame` blits it to the window in one `BitBlt`, so there is never any flicker.
All scratch memory (the message struct, RECT/POINT, C-string buffers) is
`VirtualAlloc`ed once so the garbage collector never touches it.
