# Zephyr

Small, statically-typed, memory-safe language that compiles to native Windows
x86-64. Self-hosted: `zc.exe` (the compiler) is **written in Zephyr**, carries its
own assembler + PE linker, and depends only on `kernel32.dll`. `.zeph` sources.

## Source of truth — read these before guessing semantics

- `docs/spec.md` — grammar, type rules, conversion table, runtime semantics. **Authoritative.**
- `docs/tour.md` — the language in ten minutes.
- `lib/std/list.zeph` — the standard library, written in ordinary Zephyr (not compiler builtins).
- `compiler/zc.zeph` — the compiler itself (~14,000 hand-written lines plus a generated `>>>EMBED` section holding runtime.zeph and lib/std): lexer, parser, typechecker, optimizer, x86-64 and wasm codegen, assembler, PE/ELF linkers. Never hand-edit the EMBED section; `scripts/embed-gen.ps1` rewrites it.

Zephyr *looks* like Rust/Swift but is its own language. When behavior isn't
obvious from a `.zeph` file, check `docs/spec.md` — don't assume Rust semantics.

## Build / run / test (PowerShell, Windows only)

```powershell
.\zc.exe --rt app.zeph app.exe   # compile to a kernel32-only exe
.\app.exe                        # run it
.\zc.exe --rt app.zeph app.s     # emit x86-64 assembly instead (read the codegen)
.\scripts\selfbuild.ps1                  # rebuild zc.exe from compiler\zc.zeph (byte-identical fixpoint)
powershell -File tests\run_tests.ps1
.\zc.exe --linux --rt app.zeph app  # static ELF64: no libc, no interpreter, syscalls only
wsl ./app
.\zc.exe --wasm --rt app.zeph app.wasm   # WebAssembly (the one target reclaiming by collection)
node scripts\wasm-run.js app.wasm
.\scripts\build-wasm-demo.ps1       # same module inlined into one HTML page
.\scripts\crosscheck-linux.ps1      # same sources both targets, output must match
.\scripts\crosscheck-wasm.ps1
```

`--rt` links the Zephyr-written runtime; output imports `kernel32.dll` only.
Editing the compiler = editing `compiler\zc.zeph` then `.\scripts\selfbuild.ps1`. A change to the
code the compiler generates needs one more stage (build with the new compiler, then require
the next two stages to match). New syntax cannot be used inside `zc.zeph` or `runtime.zeph`
until an installed `zc.exe` understands it — stage 1 is always built by the old compiler.

## Language facts that differ from the Rust/Swift default assumption

- **No semicolons.** Statements end at newline.
- **Logical operators are words:** `and` / `or` / `not` — not `&&`/`||`/`!`.
- **`let` immutable, `var` mutable.** Locals infer types; function params, return
  types, and struct fields require annotations.
- **`int` widens to `float` implicitly.** Every other conversion is explicit and
  visible: `n as str`, `"3.14" as float`, `Color.Blue as int`.
- **Ranges are half-open:** `for i in 1..101` iterates 1..100. (`0..xs.len()` is the idiom.)
- **No null.** Absence is the optional type `T?` with `none`; use `.or(default)`,
  `.has()`, `.get(key)`. `let zero: int? = 0` is a value, not none.
- **Every value is 64 bits;** composites live on a reference-counted, non-moving
  heap — the compiler inserts the counting, and a mark-sweep collector stays
  linked underneath only to catch cycles. Lists are bounds-checked. No pointers,
  no manual memory, no use-after-free.
- **Method-call sugar:** `b.dist(a)` == `dist(b, a)`. `impl` blocks add methods;
  `fn new(...)` (no `self`) is an associated constructor called `Point.new(...)`.
- **Enums print their member name** and compare by identity: `print(Color.Green)` → `Green`.
- **Generics:** type params in brackets — `fn contains[T](xs: [T], x: T) -> bool`.
  Inferred from arguments, monomorphized per instantiation. No trait system.
- **Interfaces** give dynamic dispatch: `fn describe(s: Shape)` accepts any impl.
- **Collections:** lists `[T]`, maps `[K: V]` (`["alice": 30]`, `.has`, `.keys`, `.remove`).
- **Strings** interpolate with braces: `"len = {p.len()}"`. Methods: `.upper`,
  `.split`, `.replace`, `.contains`, `.trim`, `.repeat`, `.startsWith`, `.indexOf`.
- **Multi-file:** `import "std/list.zeph"` — library paths resolve relative to zc.exe (it looks in `lib/`), so they work from any directory.
- **`assert(cond)` / `assert(cond, msg)`** is built in.
- **Literals:** `0xFF`, `0b1010`, `1_000`, `6.02e23`, `'a'` (an int byte), raw `r"C:\dir"`,
  multi-line `"""..."""` (indentation stripped). Comments: `//` and nesting `/* */`.
- **`const`** is a compile-time constant, usable from any function regardless of order.
- **Comparisons chain:** `0 <= i < n`. `x == none` tests an optional. `==` on lists,
  structs, tuples, optionals and maps compares by value.
- **Control flow:** `match x { A { } B, C { } else { } }` (no `=>`, also an expression),
  `if c { a } else { b }` as an expression (no `?:`), `if let v = opt { }`, `for i, x in xs`,
  `for i in a..b step s`, `label: for`/`break label`, `defer`.
- **Types:** tuples `(int, str)` / `t.0` / `let (a, b) = t`, `type Alias = T`, struct field
  defaults, default parameters, `struct Box[T]`, enums with values `Circle(float)` matched as
  `Circle(r)`, `x is Member`, packed `[u8]`/`[f32]` (convert with `as`).
- **Modules:** `import "m.zeph" as m` (qualified `m.name`), `private` declarations,
  `fn main()` auto-called, `test "name" { }` run by `zc --test`.

## Layout

Roughly the order you meet things in:

| path | what |
|------|------|
| `zc.exe` | the compiler. Must stay at the root: it resolves `lib/` and `compiler/runtime.zeph` relative to itself |
| `examples/` | `basics/` `graphics/` `vulkan/` `threads/`, plus `shaders/` (GLSL + `.zsh` + compiled `.spv`) |
| `lib/` | libraries importable as `std/…`, `vk/…`, `ui/…`; `os/linux.zeph` is the syscall shim `--linux` links in |
| `compiler/` | `zc.zeph` (the compiler, in Zephyr) and `runtime.zeph` (allocation + counting, strings, threads) |
| `scripts/` | `selfbuild` `package` `clean` `embed-gen` `build-shaders` |
| `tools/` | `vkgen.c` (Vulkan bindings from the SDK headers), `zspv.zeph` (Zephyr → SPIR-V) |
| `tests/` `bench/` `docs/` | suite, benchmarks vs C/Rust (`python bench/bench.py`, see AGENTS.md), spec and tour |
| `bootstrap/` | the C seed. Rebuilds `zc.exe` from nothing; not part of the normal loop |
| `dist/` | packaging output |

Imports are written library-relative (`import "vk/gfx.zeph"`) and resolve
against `zc.exe`'s directory, so nesting an example deeper does not change them.

## Constraints

- **Three targets.** Windows x86-64 (PE, kernel32), Linux x86-64 (static ELF, raw
  syscalls), and WebAssembly (`--wasm`, runtime included; no counting emitted). Threads run on
  Windows and Linux. Not on wasm: files, closures, interfaces and threads.
  wasm frames live in a shadow stack in linear memory so the conservative GC can
  scan them — see the memory-map comment above `writeWasm` in `zc.zeph`.
- One name, one function — **no overloading** (generics cover the real cases).
- Editor tooling lives outside this repo: an IntelliJ plugin (`../zephyr-idea-plugin`)
  and a VS Code extension + LSP (`../zephyr-vscode`).

## Frontend aesthetics

<frontend_aesthetics>
You tend to converge toward generic, "on distribution" outputs. In frontend design, this creates what users call the "AI slop" aesthetic. Avoid this: make creative, distinctive frontends that surprise and delight. Focus on:

Typography: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics.

Color & Theme: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes. Draw from IDE themes and cultural aesthetics for inspiration.

Motion: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions.

Backgrounds: Create atmosphere and depth rather than defaulting to solid colors. Layer CSS gradients, use geometric patterns, or add contextual effects that match the overall aesthetic.

Avoid generic AI-generated aesthetics:
- Overused font families (Inter, Roboto, Arial, system fonts)
- Clichéd color schemes (particularly purple gradients on white backgrounds)
- Predictable layouts and component patterns
- Cookie-cutter design that lacks context-specific character

Interpret creatively and make unexpected choices that feel genuinely designed for the context. Vary between light and dark themes, different fonts, different aesthetics. You still tend to converge on common choices (Space Grotesk, for example) across generations. Avoid this: it is critical that you think outside the box!
</frontend_aesthetics>
