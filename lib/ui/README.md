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

ui_init("Hello", 480, 320)
while ui_running() {
    ui_begin()
    ui_panel(24, 24, 300, 260, "Demo")
    if ui_button(1, "Click me") { count += 1 }
    ui_label("clicked " + (count as str) + " times")
    on = ui_checkbox(2, "Enabled", on)
    volume = ui_slider(3, "Volume", volume, 0.0, 1.0)
    ui_end()
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
on     = ui_checkbox(id, "On", on)        // returns the toggled value
volume = ui_slider(id, "Vol", volume, 0.0, 1.0)   // returns the dragged value
quality = ui_radio(id, "High", quality, 2)         // returns the selected value
name   = ui_textbox(id, name)             // returns the edited string
```

Action widgets return a `bool` that is true only on the frame they fire:

```zephyr
if ui_button(id, "Save") { save() }
```

**IDs.** Every interactive widget takes a unique integer `id` so the toolkit can
track hover/active/focus across frames. Give each widget a distinct constant.

## Lifecycle

| Call | Purpose |
|------|---------|
| `ui_init(title, w, h)` | create the window and fonts (once, before the loop) |
| `ui_running() -> bool` | pump messages; false once the window is closed |
| `ui_begin()` | start a frame: poll input, clear, reset layout |
| `ui_end()` | present the back buffer to the window |

The window is resizable; the back buffer follows the client size automatically.

## Layout

Widgets stack vertically inside the current panel. Use these to arrange them:

| Call | Effect |
|------|--------|
| `ui_panel(x, y, w, h, title)` | draw a titled container; following widgets flow inside it |
| `ui_same_line()` | place the next widget to the right of the previous one |
| `ui_spacing()` | add a little vertical gap |
| `ui_separator()` | a horizontal divider line |

## Widgets

| Call | Returns | Notes |
|------|---------|-------|
| `ui_label(s)` | — | normal text |
| `ui_text_dim(s)` | — | secondary/greyed text |
| `ui_heading(s)` | — | bold section heading |
| `ui_kv(label, value)` | — | `label ……… value` read-out row |
| `ui_button(id, label)` | `bool` | auto-width; true on click |
| `ui_button_wide(id, label)` | `bool` | full-width button |
| `ui_checkbox(id, label, value)` | `bool` | new checked state |
| `ui_radio(id, label, current, val)` | `int` | `val` if clicked, else `current` |
| `ui_slider(id, label, value, lo, hi)` | `float` | draggable; shows value |
| `ui_slideri(id, label, value, lo, hi)` | `int` | integer slider |
| `ui_progress(frac, label)` | — | 0..1 bar with optional caption |
| `ui_textbox(id, value)` | `str` | click to focus, then type; new string |
| `ui_tab(id, label, current, index)` | `int` | tab in a tab bar (use `ui_same_line`) |
| `ui_collapsing(id, label, open)` | `bool` | section header; guard body with `if` |

### Radio group

```zephyr
quality = ui_radio(20, "Low",    quality, 0)
quality = ui_radio(21, "Medium", quality, 1)
quality = ui_radio(22, "High",   quality, 2)
```

### Tab bar

```zephyr
tab = ui_tab(1, "General",  tab, 0)  ui_same_line()
tab = ui_tab(2, "Graphics", tab, 1)  ui_same_line()
tab = ui_tab(3, "Audio",    tab, 2)
if tab == 0 { ... }
```

### Collapsing section

```zephyr
advanced = ui_collapsing(5, "Advanced", advanced)
if advanced {
    fov = ui_slider(6, "FOV", fov, 60.0, 120.0)
}
```

### Text input

Click a text field to focus it (a blinking caret appears), then type. Supports
letters, digits, space, common punctuation, Shift, and Backspace. Clicking
elsewhere drops focus.

```zephyr
name = ui_textbox(40, name)
ui_label("Hello, " + name)
```

## IDE-scale primitives

Beyond the basic widgets, the toolkit has the building blocks for full
application chrome — `examples/ide.zeph` uses them to recreate a JetBrains-style
IDE (toolbar, split panes, tree views, a syntax-coloured code editor, dockable
tool windows, status bar).

| Call | Purpose |
|------|---------|
| `ui_vsplit(id, x, y, h, lo, hi)` | draggable vertical split bar; returns new x |
| `ui_hsplit(id, y, x, w, lo, hi)` | draggable horizontal split bar; returns new y |
| `ui_scroll_begin(id, x, y, w, h, contentH, off)` | begin a clipped, scrollable region (mouse-wheel + scrollbar); returns clamped offset |
| `ui_scroll_end()` | end it; **returns the measured content height** to feed back next frame |
| `ui_tree_row(id, depth, label, hasKids, icon)` | one tree row (indent, chevron expander, icon, rounded full-width selection); returns whether open — draw children when true |
| `ui_icon(kind, colour)` | pack an icon for `ui_tree_row`: 1 folder, 2 file, 3 database, 4 table, 5 status dot, 0 plain swatch |
| `fill_rr(x,y,w,h,r,col)` / `frame_rr(...)` | rounded fill / outline (r ≈ 8-10 for the JetBrains look) |
| `chev_down(x,y,col)` / `chev_right(x,y,col)` | small chevron glyphs (dropdowns, expanders) |
| `ui_tree_selected()` | id of the selected tree row |
| `ui_run(x, y, s, col)` | draw a text run, return its width (build colour-coded lines) |
| `ui_mono()` / `ui_ui()` | switch to the monospace / UI font |
| `ui_clip(x,y,w,h)` / `ui_clip_off()` | set / clear a clip rect |
| `ui_abtn(id,x,y,w,h,label)` | absolutely-positioned button (toolbars, chrome) |
| `ui_flat(id,x,y,w,h,glyph,hotCol)` | flat clickable region (icon buttons) |
| `ui_abtn_flat(id,x,y,w,h,label,active)` | flat document/tool tab |
| `ui_w()` / `ui_h()` | client width / height |

**Trees are retained.** `ui_tree_row` keeps each node's expand and selection
state internally (keyed by `id`), so you just call it for every node every frame
and it remembers what's open. Wrap children in `if ui_tree_row(...) { ... }`.

**Scroll regions self-size.** Pass last frame's content height in and store what
`ui_scroll_end()` returns, so the scrollbar thumb is correct after one frame:

```zephyr
off = ui_scroll_begin(id, x, y, w, h, contentH, off)
draw_rows()
contentH = ui_scroll_end()
```

**Mouse wheel** is captured in the message pump, so scrolling works with no
window procedure.

> One gotcha when you copy the IDE example: any global whose *initialiser* must
> run (e.g. `let SEP = chr(1)`) has to be declared **before** the `while
> ui_running()` loop — the loop never returns, so top-level statements after it
> never execute. Function *definitions* can live anywhere (they're hoisted); only
> global initialisers are order-sensitive.

## Theme

The default theme matches the JetBrains "New UI" dark palette: one flat surface
colour (`COL_PANEL`, #2B2D30) everywhere, regions separated by 1px seams that
are *darker* than the surface (`COL_BORDER`, #1E1F22 — never lighter), rounded
rects for every hover/selection state, `COL_ACTIVE` (#2E436E) selection blue and
`COL_ACCENT` (#3574F0) accent. Colours live as `COL_*` constants near the top of
`ui.zeph`; change them there to restyle every widget at once.

## How it works

`ui_init` registers a window class (with `DefWindowProc` — no callback needed)
and creates two GDI fonts. Each frame, `ui_begin` reads the mouse via
`GetCursorPos`/`ScreenToClient` and buttons/keys via `GetAsyncKeyState`, so input
needs no window procedure. Drawing goes into an off-screen bitmap
(`CreateCompatibleDC` + `CreateCompatibleBitmap`) using `FillRect` and `TextOutA`;
`ui_end` blits it to the window in one `BitBlt`, so there is never any flicker.
All scratch memory (the message struct, RECT/POINT, C-string buffers) is
`VirtualAlloc`ed once so the garbage collector never touches it.
