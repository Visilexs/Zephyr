# Zephyr

A small, statically-typed, memory-safe programming language that compiles to
native machine code — Windows x86-64, Linux x86-64 (static ELF), and
WebAssembly — from one self-hosted toolchain with no external assembler,
linker, or C compiler in the loop.

```zephyr
struct Point { x: float, y: float }

fn dist(a: Point, b: Point) -> float {
    let dx = a.x - b.x
    let dy = a.y - b.y
    return sqrt(dx * dx + dy * dy)
}

let a = Point{x: 0.0, y: 0.0}
let b = Point{x: 3.0, y: 4.0}
print("distance is {dist(a, b)}")   // distance is 5
print(b.dist(a))                    // same call, method syntax
```

## Why

- **Memory safe.** No pointers, no manual memory, no null. A garbage collector
  reclaims memory, every list access is bounds-checked, and every variable must
  be initialized. There is no way to write a use-after-free, double-free,
  buffer overrun, or null dereference.
- **Statically typed, but concise.** Types are inferred for locals
  (`let x = 3`), required only on function signatures and struct fields.
  `int` widens to `float` implicitly; every other conversion is explicit
  and visible: `n as str`, `"3.14" as float`.
- **Native performance, measured honestly.** Programs compile to x86-64
  assembly and link into a standalone `.exe`. `bench\run_suite.ps1` runs eight
  workload areas as the *same algorithm* in Zephyr, C (`gcc -O2`) and Rust
  (`rustc -O`), and verifies the output checksum is byte-identical across all
  three before trusting a single number. Current standing (best-of-7, Windows
  x86-64, a Zen5 desktop):

  | Area | Zephyr | C `-O2` | Rust `-O` | |
  |------|-------:|--------:|----------:|---|
  | integer SIMD (matmul) | **42 ms** | 72 | 70 | wins both |
  | rasterization (cube) | **8 ms** | 10 | 11 | wins both |
  | bignum (pi) | **66 ms** | 84 | 91 | wins both |
  | alloc / GC (strings) | **132 ms** | 172 | 148 | wins both |
  | sorting | **139 ms** | 276 | 43 | 2× faster than C |
  | recursion (fib) | 21 ms | 12 | 21 | ties Rust |
  | hash map | 83 ms | 32 | 69 | ties Rust |
  | float compute (mandel) | 109 ms | 88 | 90 | 1.2× |

  Zephyr beats **both** compilers outright on integer SIMD, rasterization,
  bignum, and allocation churn (a single-allocation string builder vs C's and
  Rust's per-format heap strings), beats C by 2× on sorting (a
  branchless-partition introsort — the pdqsort technique — against C's
  `qsort`), ties Rust on recursion and hash maps, and is within ~1.2× on
  float. **Peak memory is the lowest of the three on most rows** (alloc/GC:
  12 MB vs its own earlier 138 MB, thanks to a Go-style live-proportional GC
  trigger and the string builder). Every row also *compiles* ~10× faster than
  gcc or rustc on the same program.

- **A real optimizer — including things gcc and LLVM don't do.** The
  self-hosted compiler carries: a function **inliner**, **register promotion**
  of loop-hot locals into callee-saved registers (integers into GPRs, floats
  into callee-saved `xmm6`–`xmm11`), an **xmm-native float expression
  evaluator**, compare-and-branch fusion (integer *and* float, threaded through
  `and`/`or` short-circuits), immediate-operand folding, push/pop-free leaf
  operands and array indexing, a peephole pass, and **AVX2 auto-vectorization**
  of the AXPY, fill, and index-weighted-reduction idioms (where gcc/LLVM emit
  2-wide SSE2 or leave the loop scalar entirely).

- **Runtime-reciprocal division.** Mainstream compilers turn division into
  multiply-by-reciprocal *only* when the divisor is a compile-time constant.
  Zephyr also does it when the divisor is merely **loop-invariant at runtime**
  (a `%1000000007`, a variable that isn't reassigned in the loop): at loop
  entry it computes the magic reciprocal `M = (2⁶⁴−1)/d` with one hardware
  divide, then each div/mod site runs `mulhi` + one conditional fixup — ~2×
  faster than `idiv` — and falls back to exact `idiv` for negative operands, so
  results are bit-for-bit identical. This is what programmers reach for
  `libdivide` to do by hand; Zephyr does it automatically, and it alone flipped
  the pi benchmark from losing to C (93 ms) to winning (68 ms).

- **Fast compiler.** The whole frontend (lex, parse, typecheck) does
  **10,000 lines in ~18 ms**; total build time is dominated by the ~0.2 s
  assemble/link step.
- **Readable.** `and`/`or`/`not` instead of symbol soup, string interpolation
  (`"hello {name}"`), no semicolons, `let` vs `var` for immutability.
- **Batteries included.** Lists `[T]`, hash maps `[K: V]`, `struct`s, `enum`s
  (which print their member name), optionals `T?`, closures, generics,
  interfaces (structural, dynamic dispatch), and `import "other.zeph"` for
  multi-file programs.
- **Three targets, one source.** The same program compiles to a Windows PE
  (`.exe`, kernel32 only), a static Linux ELF (`--linux`, raw syscalls, no
  libc), or a WebAssembly module (`--wasm`, runtime and GC included).
  `crosscheck` scripts compile both native targets from the same sources and
  require byte-identical output.
- **Talks to the machine when it needs to.** A native-interop layer —
  `win("user32!GetDC", …)`, the `callptr` intrinsic, `extern fn … from "x.dll"`,
  and raw-memory builtins — lets pure Zephyr call the OS and the GPU directly.
  On top of it the repo ships a **Vulkan wrapper** (`lib/vk`, with a
  Zephyr→SPIR-V shader compiler in `tools/zspv.zeph`), an immediate-mode **GUI
  toolkit** (`lib/ui`), and **threads** (`lib/std/thread.zeph`,
  `parallel_for`). The `examples/graphics` directory drives all of it — from a
  software particle rasterizer to a real-time, geodesic-ray-traced black hole.
  See [docs/graphics.md](docs/graphics.md).
- **A standard library written in Zephyr, not welded into the compiler.**
  `contains`, `map`, `filter`, `fold`, `sort_by` and friends live in
  `lib/std/list.zeph` as ordinary generic code:

  ```zephyr
  fn contains[T](xs: [T], x: T) -> bool {
      for v in xs { if v == x { return true } }
      return false
  }
  ```

  Type parameters are inferred from the arguments, and each instantiation is
  type-checked with `T` bound — so `contains` gets the right `==` for `int`,
  `str` or an enum, with no trait system anywhere.

## Install & self-build

The live compiler is `zc.exe` — the Zephyr compiler, **written in Zephyr**. It
contains its own x86-64 assembler and PE linker and depends on nothing but
`kernel32.dll`. To rebuild it from source you use it to compile itself — no
gcc, no C:

```powershell
.\scripts\selfbuild.ps1     # zc.exe recompiles compiler\zc.zeph into a new zc.exe
.\zc.exe --rt app.zeph app.exe   # compile a program (kernel32-only output)
```

`scripts\selfbuild.ps1` also checks the classic bootstrap invariant: the new compiler
must reproduce itself byte-for-byte. Editing the compiler is just editing
`compiler\zc.zeph` and running `scripts\selfbuild.ps1` again — Zephyr compiling Zephyr.

### The one-time seed (historical)

A self-hosted compiler is a binary that builds itself, so it needs a starting
binary — exactly like `rustc` or the Go toolchain. Everything C lives in
`bootstrap\`, isolated from the live source. Zephyr's first `zc.exe` was
produced **once** from that C seed:

```powershell
.\bootstrap\build.ps1     # gcc builds the C seed and emits the first zc.exe
```

After that, gcc and the C sources (`bootstrap\zephyr.c`, `bootstrap\runtime.c`)
are no longer part of the toolchain — they're the fossil seed, kept only so
the compiler can be reconstructed from nothing if the binary is ever lost.
`bootstrap\nocc.ps1` proves the loop needs neither.

## Use

```powershell
.\zc.exe --rt app.zeph app.exe     # compile app.zeph to a kernel32-only exe
.\app.exe                             # run it
```

`zc.exe` is **single-file**: `runtime.zeph` and the `std/` library are embedded
in the binary (regenerated by `tools\embed-gen.ps1`, which `scripts\selfbuild.ps1` runs
automatically). A `runtime.zeph` or `std\` found next to the exe — or in the
current directory — overrides the embedded copy, so the edit-and-rebuild dev
workflow in this repo is unchanged, while a copied-out `zc.exe` works alone.

### Packaging

`.\package.ps1` assembles the end-user distribution in `dist\zephyr-<version>\`
(and a `.zip`): the single-file `zc.exe` plus docs and examples — no bootstrap
sources, tests, or benchmarks. It self-checks by copying `zc.exe` into a bare
directory and compiling a std-importing program there before zipping.

`zc.exe` is the self-hosted compiler; its output ends in `.s` instead of
`.exe` if you want to read the generated assembly. It carries the full
optimizer described above — inliner, register promotion, runtime-reciprocal
division, the AVX2 auto-vectorizers, and the rest — so it, not the historical C
seed, produces the benchmark numbers. The C seed (`bootstrap\zephyr.exe`)
additionally offers `run` / `check` conveniences during development.

## Documentation

- [Language tour](docs/tour.md) — learn Zephyr in ten minutes.
- [Language specification](docs/spec.md) — grammar, type rules, conversion
  table, runtime semantics, native interop, targets, concurrency.
- [Graphics & GPU](docs/graphics.md) — the FFI, the Vulkan wrapper, the
  Zephyr→SPIR-V shader compiler, and the `examples/graphics` walkthrough.

## Self-hosting

The compiler exists twice: the bootstrap compiler in C (`bootstrap/zephyr.c`)
and the **self-hosted compiler written in Zephyr itself** (`compiler/zc.zeph`,
~6,200 lines of Zephyr — a complete lexer, parser, type checker, optimizer,
x86-64 code generator, **assembler, and PE linker**). `bootstrap\bootstrap.ps1`
proves the fixpoint two ways:

- **gcc path**: `zc` emits assembly, gcc assembles/links it.
- **native path**: `zc` assembles and PE-links its own `.exe` with no
  external tools, then does it again — byte-identical output.

Any change to code generation is promoted through a three-stage bootstrap (the
old compiler builds one with the new codegen, which then rebuilds itself to a
byte-identical fixpoint), so the compiler that ships is always one that
reproduces itself exactly.

```powershell
powershell -File bootstrap\bootstrap.ps1       # verifies both fixpoints
.\zc.exe --rt app.zeph app.exe              # Zephyr compiling Zephyr to a native exe, zero C tools
```

## The runtime, written in Zephyr

Zephyr's runtime exists in two forms. The default is C (`bootstrap/runtime.c`,
`zephyr_rt.dll`) — it has the optimized GC and full float support. The second is
**written in Zephyr itself** (`runtime.zeph`): allocation, strings, lists,
struct/list formatting, interpolation, panics, and command-line args, all
implemented with Zephyr's low-level primitives — bitwise ops, raw memory access
(`load64`/`store8`/`addr`), and Win64 FFI to kernel32 (`win("WriteFile", …)`).

```powershell
.\zc.exe --rt app.zeph app.exe   # link the Zephyr runtime
.\app.exe                            # depends on kernel32.dll ONLY — no zephyr_rt.dll, no C
```

An executable built with `--rt` imports nothing but `kernel32.dll`. The Zephyr
runtime is now feature-complete: every type (including maps, enums, optionals
and function values), string/int/float parsing **and float formatting**
(matching C's `%.15g`), file I/O, command-line args, and a **conservative
mark-sweep garbage collector** — a contiguous reserved heap with an
object-start bitmap for O(1) pointer identification, size-segregated free
lists for O(1) allocation, and roots scanned from the machine stack and the
globals array. It halves peak memory on an allocation-heavy benchmark (2M
short-lived strings: 56.9 MB collected vs 114.3 MB uncollected) and costs the
compiler ~25% on compile time.

`examples/ffi_runtime.zeph` is a smaller standalone demonstration — stdout I/O
and integer formatting in pure Zephyr, calling only kernel32.

### A self-sustaining toolchain with no gcc and no C

The self-hosted compiler `zc` can be built *with* the Zephyr runtime, and it
can *emit* `--rt` output — so the whole toolchain closes on itself with no C
anywhere in the loop. `bootstrap\nocc.ps1` proves it:

1. **One-time C seed**: the C `zephyr.exe` builds a kernel32-only `zc` (this
   is the unavoidable bootstrap seed every self-hosted language has).
2. That kernel32-only `zc` compiles `zc.zeph` (with `--rt`) into another
   kernel32-only `zc` — **no gcc, no C runtime** — and does it again to a
   **byte-identical fixpoint**.
3. The C-free-built compiler then compiles and runs ordinary programs, all
   depending on nothing but `kernel32.dll`.

After the seed, gcc and the C runtime can be discarded: a Zephyr compiler,
assembler, and linker — all written in Zephyr, all in one standalone
executable — reproduce themselves and compile standalone programs.

## How it works

Both compilers share the same pipeline: lexer → recursive-descent parser →
type checker → inliner → optimizer passes → x86-64 code generator (Intel-syntax
assembly) → peephole → **built-in assembler and PE linker**. The assembler
encodes exactly the instruction vocabulary the code generator emits, and the
linker writes a Windows PE64 executable directly — imports, sections, entry
stub and all — with no external tools. Every Zephyr value is 64 bits; composite
values live on the GC heap.

The self-hosted `zc.exe` links the Zephyr-written runtime (`--rt`) and imports
only `kernel32.dll`. The historical C seed instead links `zephyr_rt.dll`, a
small C runtime with the same semantics. The optimizer — inliner, register
promotion, runtime-reciprocal division, compare-and-branch fusion, the AVX2
vectorizers — lives in `compiler/zc.zeph`; the C seed carries an older subset
and exists only to reconstruct the first `zc.exe` from source.

## Tests

```powershell
powershell -File tests\run_tests.ps1
```

Covers the examples, language features, GC stress (200k allocations),
compile-time errors, and runtime panics.

## Roadmap

Maps, enums, modules, optionals, closures, generics, interfaces, float
formatting, the garbage collector, the inliner, register promotion (integer
*and* float), runtime-reciprocal division, a **register-based calling
convention** for user functions, and two further backends — **Linux/ELF**
(`--linux`) and **WebAssembly** (`--wasm`) — have all landed. Still open,
roughly in the order that would move the benchmarks:

- **Allocation / GC pressure** — the alloc and hash-map benchmarks are
  allocation-bound. Escape analysis to stack-allocate non-escaping temporaries,
  and inlining the map probe fast-path at call sites, are the open levers.
- **Feature parity across targets** — WebAssembly still lacks files, closures,
  interfaces and threads; native interop (`extern fn … from`) is Windows-only.
- **Overloading** — one name, one function. Generics covered the cases that
  actually mattered; overloading is a convenience, not a gap.
- **More vectorizer idioms** — the AVX2 wins cover the AXPY, fill and reduction
  shapes. A real cost model would generalise it.
