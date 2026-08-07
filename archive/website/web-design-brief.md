# Zephyr — Website Design Brief

**Handoff document. Self-contained: everything needed to design and build
zephyr-lang.org is in this file.**

- **Deliverable:** a single-page marketing site (+ a docs shell), static, no framework required.
- **Audience:** systems programmers, compiler people, HN/lobste.rs. Skeptical. They will check your claims.
- **Success:** a reader thinks *"this person knows what they're doing"* within 5 seconds, and can verify the headline claim within 30.

---

## 1. What Zephyr is (product context)

Zephyr is a small, statically-typed, memory-safe programming language that compiles
directly to native x86-64 machine code.

The two things that matter:

1. **It is self-hosted with no external toolchain.** The compiler (`zc`) is ~10,000
   lines *written in Zephyr itself* and contains its own lexer, parser, type checker,
   x86-64 code generator, **assembler, and PE linker**. No LLVM. No gcc. No C anywhere
   in the build loop. It rebuilds itself by running on itself and reproduces itself
   byte-for-byte. Emitted programs import exactly one library: `kernel32.dll`.
2. **It beats C and Rust on its benchmarks.** Identical algorithms, byte-identical
   output. It wins by emitting better AVX2 than LLVM does for specific loop shapes.

Supporting facts (all true, all usable):

- Language: `int`, `float`, `bool`, `str`, lists `[T]`, hash maps `[K: V]`, `struct`,
  `enum`, optionals `T?`, first-class functions `fn(int) -> int`, `import` for
  multi-file programs, string interpolation.
- Memory-safe by construction: no pointers, no manual memory, no null,
  bounds-checked indexing, everything initialized.
- The **runtime is also written in Zephyr** — allocation, strings, maps, formatting,
  file I/O, Win32 FFI, and a conservative mark-sweep **garbage collector**.
- The compiler frontend does **10,000 lines in ~18 ms**; `zc` rebuilds itself in **~0.12 s**.
- The FFI reaches `user32`/`gdi32`: `examples/cube3d.zeph` opens a real Win32 window
  and draws a spinning wireframe cube with GDI vector lines, in pure Zephyr.
- Current version: **0.2**. Platform: **Windows / x86-64 only**.

### Honest gaps — do not hide these; put them below the fold

- Function values are code pointers — **closures do not capture**.
- **No generics or overloading.**
- Windows / x86-64 only.

A technical audience respects a project that names its gaps before they do. There
should be a short, plainly-worded "Not yet" section near the bottom.

---

## 2. Verified claims (the only numbers you may print)

**Do not invent, round up, or embellish any number.** These are measured and
reproducible. If a number isn't here, don't print it.

**Fig. 1 — Integer matmul, 768×768** (identical algorithm, byte-identical checksums)

| Language | Time |
|---|---|
| **Zephyr** | **59 ms** |
| Rust (`rustc -O`) | 113 ms |
| C (`gcc -O2`) | 118 ms |

**Fig. 2 — Wireframe cube render, 12,000 frames**

| Language | Time |
|---|---|
| **Zephyr** | **42 ms** |
| C (`gcc -O2`) | 44 ms |
| Rust (`rustc -O`) | 47 ms |

Reproduce: `bench\run_matmul.ps1` · `bench\run_cube.ps1`

### The mandatory qualifier

Any speed claim must remain attached to **"on these benchmarks."** Zephyr wins because
it out-vectorizes LLVM on *recognized loop shapes* — not universally. The qualified
claim is verifiable and impressive; the unqualified one is disproved by the first
skeptic and costs more credibility than the adjective buys.

**Banned words:** "blazingly fast", "simply beautiful", "developer experience",
"revolutionary", "magical".

---

## 3. Design thesis

> **Evidence, not enthusiasm.**

Do not design a SaaS landing page. Design a **precision instrument's datasheet**.
Every element either states a fact or shows one. The benchmark figure *is* the hero
graphic. Code *is* the imagery. No illustration, no mascot, no abstract 3D render.

Tone: exacting, airy, unhurried. *Zephyr* means a light wind — design against the
tension of **air + precision**: generous whitespace, hairline rules, no visual noise.
Confidence is shown by restraint.

---

## 4. The anti-slop contract (hard bans)

The client's explicit brief is *"it must not look vibe-coded."* These are the tells:

- ❌ **Purple/indigo** (`#6366f1` and relatives). Instantly reads "generated".
- ❌ **Gradient text**, gradient buttons, gradient anything.
- ❌ **Glassmorphism** — no `backdrop-filter`, no frosted nav, no blurred blobs.
- ❌ **Emoji in headings.** No ⚡ 🚀 ✨.
- ❌ **Three symmetric feature cards** with icon circles / `rounded-2xl` / `shadow-lg`.
- ❌ **Scroll-triggered fade-in / slide-up** on sections. No parallax. No counting-up
  numbers. No typewriter hero.
- ❌ **Inter.** Overexposed. So is Poppins.
- ❌ Border-radius above **6px**.
- ❌ Drop shadows for separation — use **1px rules**.
- ❌ Centred hero.
- ❌ Floating browser/laptop mockups.

**Positive constraints:** left-aligned hero · asymmetric grid · monospace as a
*structural* element (this is a compiler — mono is native, not decoration) · exactly
one accent colour · real data.

---

## 5. Tokens

One accent, used sparingly. Everything else is ink and paper. **Colour is reserved for
code and data** — that discipline is what makes it look designed.

Accent is **cyan-teal**: evokes air/speed, and it's an open lane (Go owns blue, Rust
orange, Zig amber, Gleam pink, Nim yellow).

```css
:root {
  /* paper — warm off-white, never #fff */
  --paper:      #FBFAF8;
  --paper-sunk: #F3F1ED;   /* code wells, table zebra */
  --rule:       #E4E1DB;   /* all 1px hairlines */
  --rule-firm:  #CFCBC3;

  /* ink */
  --ink:        #14161A;   /* headings */
  --ink-body:   #33383F;   /* prose */
  --ink-mute:   #6E747E;   /* captions, secondary */

  /* accent — the only chroma in the chrome */
  --accent:       #0A6E7A;  /* links, CTA */
  --accent-hover: #085A64;
  --accent-tint:  #E7F2F3;  /* winning bar fill, callout bg */
  --focus:        #0A6E7A;
}

:root[data-theme="dark"] {
  --paper:      #0E1012;
  --paper-sunk: #15181B;
  --rule:       #24282C;
  --rule-firm:  #343A40;

  --ink:        #ECEAE6;
  --ink-body:   #B9BEC5;
  --ink-mute:   #7C848E;

  --accent:       #3FC5D6;
  --accent-hover: #63D6E4;
  --accent-tint:  #0E2A2F;
  --focus:        #3FC5D6;
}
```

**Rule:** the accent may appear at most ~5 times per viewport. If it's everywhere,
it's wallpaper.

---

## 6. Typography

**IBM Plex** — sans, mono *and* serif from one family. Engineering heritage, free,
coherent, conspicuously not Inter.

| Role | Face |
|---|---|
| Headings / UI | **IBM Plex Sans** — 600 max, never 800 |
| Long-form prose (docs) | **IBM Plex Serif** — the "technical paper" signal; optional on the landing page |
| Code, data, labels | **IBM Plex Mono** — load 400/500 only |

```css
--font-sans:  "IBM Plex Sans", system-ui, sans-serif;
--font-serif: "IBM Plex Serif", Georgia, serif;
--font-mono:  "IBM Plex Mono", ui-monospace, monospace;
```

### Scale (desktop → mobile)

| Token | Size / line | Weight | Tracking |
|---|---|---|---|
| `display` | 56/1.05 → 34 | 600 | −0.022em |
| `h2` | 28/1.25 → 24 | 600 | −0.01em |
| `h3` | 19/1.35 | 600 | 0 |
| `body` | 17/1.65 → 16 | 400 | 0 |
| `small` | 14/1.5 | 400 | 0 |
| `label` | 12/1 mono **UPPERCASE** | 500 | +0.09em |
| `code` | 14/1.55 mono | 400 | 0 |

`label` (mono, uppercase, tracked) is the workhorse — section eyebrows, table headers,
figure numbers. It does an icon's job with more credibility. **Use it instead of icons.**

**Measure:** prose capped at **68ch**. Never full-bleed text.
**Numbers:** `font-variant-numeric: tabular-nums` on every figure in a table.

---

## 7. Layout

- Content max-width **1120px**; prose column **680px**. Gutters 24px mobile / 48px desktop.
- 4px spacing base. Section rhythm **112px** desktop / 64px mobile.
- **Asymmetry:** hero text occupies columns 1–7 of 12; Fig. 1 sits 8–12, optically
  heavier. Do not centre.
- Separation is `1px solid var(--rule)`. Not shadows.
- Radius: `3px` (code wells, inputs, buttons); `0` for tables and rules; never > 6px.
- Breakpoints: 640 / 900 / 1200.

---

## 8. Page structure with final copy

Use this copy as written. It is approved and factual.

### 8.1 Nav
56px, `border-bottom: 1px solid var(--rule)`, opaque `--paper` (no blur, no sticky
glass). Wordmark `zephyr` — mono, lowercase, 500. Right: `v0.2` chip, Docs, Source.
**No CTA button in the nav.**

### 8.2 Hero (left-aligned, cols 1–7)

```
LABEL     SYSTEMS LANGUAGE · SELF-HOSTED

DISPLAY   The language that compiles itself —
          and outruns C.

BODY      No LLVM. No gcc. No C. zc carries its own assembler
          and PE linker, rebuilds itself in 0.12 seconds, and
          emits binaries that import exactly one DLL.

INSTALL   $ zc --rt hello.zeph hello.exe          ⧉
```

### 8.3 Fig. 1 — the hero visual (cols 8–12)

The benchmark is the graphic. Not an illustration.

- Header: `label` style → `FIG. 1 — INTEGER MATMUL, 768×768`
- Horizontal bars. **Zephyr:** `--accent-tint` fill + 2px `--accent` left edge.
  **C / Rust:** `--paper-sunk` fill + `--rule-firm` edge.
- Values right-aligned, mono, tabular figures.
- Caption, `--ink-mute` 13px:
  > *Identical algorithm, byte-identical checksums. Reproduce: `bench\run_matmul.ps1`*

**The caption is the credibility. Never show a benchmark without one.**

### 8.4 Code sample

Real, working Zephyr. Use exactly this:

```zephyr
enum Color { Red, Green, Blue }

fn map_list(xs: [int], f: fn(int) -> int) -> [int] {
    var out: [int] = []
    for x in xs { out.push(f(x)) }
    return out
}

var ages: [str: int] = ["alice": 30]
print(ages.get("bob").or(0))            // 0 — absence without a panic
print("distance is {sqrt(9.0 + 16.0)}") // distance is 5
```

Presentation: `--paper-sunk`, 1px rule, 3px radius, filename tab in `label` style flush
left in the top rule. **No traffic-light dots.** No line numbers on the landing page.

### 8.5 "Why" — definition list, NOT cards

Two columns, hairline between rows, term in `--ink` 600, definition in `--ink-body`.
**Zero icons.**

```
Memory safe        No pointers, no null, bounds-checked indexing,
                   everything initialized — and a garbage collector
                   written in Zephyr itself.

Self-hosted        10,000 lines of Zephyr. Its own assembler and PE
                   linker. Rebuilds itself byte-for-byte.

Zero dependencies  One executable. One DLL import. Ship it anywhere.

Instant builds     The whole frontend does 10,000 lines in ~18 ms.

Reads like you'd   and / or / not, string interpolation, no semicolons,
write it           let vs var. Lists, maps, structs, enums, optionals,
                   first-class functions, modules.
```

### 8.6 "How it beats C" — the technical proof section

```
H2    How it beats C

BODY  Zephyr hunts for loops LLVM leaves on the table. Matmul's inner
      loop gets a hand-written 4-wide AVX2 kernel where LLVM settles
      for 2-wide SSE2. The cube's checksum reduction gets vectorized
      where gcc emits plain scalar code.

      It turns out "the C compiler is optimal" isn't a law of physics —
      it's just a very good default.
```

Then Fig. 2 (cube benchmark), same treatment as Fig. 1.

### 8.7 "Not yet" — below the fold, plainly worded

```
H2    Not yet

BODY  Zephyr is v0.2 and honest about it:

      · Function values are code pointers — closures don't capture.
      · No generics or overloading.
      · Windows / x86-64 only.
```

### 8.8 Footer
Dense, mono 13px, `--ink-mute`, hairline top. Columns: Docs · Source · Spec · Benchmarks.

---

## 9. Syntax highlighting

Restrained. Keywords carry weight, not rainbow. Comments must be legible — they're prose.

```css
--syn-plain:   var(--ink);
--syn-keyword: #A03E88;  /* fn let var if for enum — magenta-ink */
--syn-type:    #0A6E7A;  /* int str [T] — accent */
--syn-string:  #3F7A34;  /* muted green */
--syn-number:  #B0561A;  /* burnt orange */
--syn-comment: #8A9099;  /* italic */
--syn-fn:      #14161A;  /* names stay ink, weight 500 — no colour */
```

Dark mode: `#D98BC4` / `#3FC5D6` / `#86C46F` / `#E0975A` / `#6E767F`.

---

## 10. Motion

- Duration **150ms**, `cubic-bezier(0.2, 0, 0, 1)`. **Hover and focus only.**
- **No scroll-triggered animation.**
- One permitted flourish: Fig. 1/2 bars may grow from zero once on first view — 400ms,
  60ms stagger — and only under `prefers-reduced-motion: no-preference`.

---

## 11. Accessibility

- Body text ≥ **4.5:1**, large text ≥ 3:1. Verify `--accent` on `--paper` before shipping.
- Focus: `outline: 2px solid var(--focus); outline-offset: 2px`. Never `outline: none`.
- Never colour-only: the winning bar also carries a bold value and a `label`.
- Respect `prefers-reduced-motion` and `prefers-color-scheme`; a manual theme toggle
  must override both.
- Semantic HTML. The benchmark is a real `<table>` (or a `<figure>` wrapping one),
  not a stack of divs.

---

## 12. Deliverables

1. `index.html` — single page, self-contained CSS, no framework, no build step.
2. Light + dark, with a manual toggle.
3. Responsive at 640 / 900 / 1200.
4. A docs shell reusing the same tokens (nav + prose column at 68ch + sidebar).

## 13. Acceptance checklist

Self-check before returning:

- [ ] No purple. No gradients. No glassmorphism. No emoji in headings. No Inter.
- [ ] Hero is left-aligned and asymmetric; the benchmark is the hero visual.
- [ ] Accent appears ≤ ~5 times per viewport; all other chroma is in code/data only.
- [ ] Every radius ≤ 6px. Every separation is a 1px rule, not a shadow.
- [ ] Zero icon circles; the "why" section is a definition list.
- [ ] Every benchmark has a reproduce caption; every speed claim says "on these benchmarks".
- [ ] Every printed number appears in §2 of this brief.
- [ ] No scroll-triggered animation.
- [ ] Contrast checked; focus rings visible; `tabular-nums` on all figures.
- [ ] The "Not yet" section is present and unhedged.
