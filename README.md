# Zephyr

A small, statically typed, memory-safe language that compiles to native code —
Windows x86-64, Linux x86-64 (static ELF), and WebAssembly — from one
self-hosted toolchain. No external assembler, linker, or C compiler in the loop.

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

**Memory safe, without collector pauses.** No pointers, no manual memory, no
null. Memory is reclaimed by reference counting the compiler inserts; every
index is bounds-checked and every variable is initialized at creation. Nothing
stops for a collection: the worst frame under heavy churn is under 65 µs, against
~4 ms for the tracing collector it replaced. See
[reference counting](#reference-counting).

**Statically typed, lightly annotated.** Locals infer (`let x = 3`); signatures
and struct fields are declared. `int` widens to `float` implicitly. Every other
conversion is written out: `n as str`, `"3.14" as float`.

**Native performance.** `bench\run_suite.ps1` runs each workload as the same
algorithm in Zephyr, C (`gcc -O2`) and Rust (`rustc -O`), and checks the output
checksums match across all three before reporting a number. Best of at least 7 runs on a
Ryzen 7 9800X3D, Windows x86-64, gcc 16.1, rustc 1.98.1:

| Area | Zephyr | C `-O2` | Rust `-O` | |
|------|-------:|--------:|----------:|---|
| integer SIMD (matmul) | **43 ms** | 73 | 70 | wins both |
| rasterization (cube) | **7 ms** | 9 | 11 | wins both |
| bignum (pi) | **56 ms** | 85 | 94 | wins both |
| allocation churn (strings) | **154 ms** | 175 | 166 | wins both |
| sorting | **89 ms** | 299 | 45 | 3.4× faster than C |
| hash map | **47 ms** | 29 | 71 | 1.5× faster than Rust |
| recursion (fib) | 21 ms | 10 | 20 | ties Rust |
| float compute (mandel) | 98 ms | 91 | 92 | 1.07× |
| fluid / neighbours (liquid) | 2,906 ms | 2,249 | 2,557 | 1.3× |

The sorting win is a branchless-partition introsort (the pdqsort technique)
against C's `qsort`. The allocation win is a single-allocation string builder
against per-format heap strings. Peak memory is the lowest of the three on every
row but the hash map, and every row compiles faster than with gcc or rustc:
124–153 ms, against 157–212 ms for gcc and 212–706 ms for rustc. Measured
2026-09-29.

**The optimizer.** Function inliner, register promotion of loop-hot locals into
callee-saved registers (integers into GPRs, floats into `xmm6`–`xmm11`), an
xmm-native float expression evaluator, compare-and-branch fusion (integer and
float, threaded through `and`/`or` short-circuits), immediate-operand folding,
push/pop-free leaf operands and array indexing, a peephole pass, and AVX2
auto-vectorization of the AXPY, fill, and index-weighted-reduction idioms, where
gcc and LLVM emit 2-wide SSE2 or leave the loop scalar.

**Runtime-reciprocal division.** Mainstream compilers turn division into
multiply-by-reciprocal only when the divisor is a compile-time constant. Zephyr
also does it when the divisor is merely loop-invariant at runtime — a
`%1000000007`, or a variable not reassigned in the loop. At loop entry it
computes the magic reciprocal `M = (2⁶⁴−1)/d` with one hardware divide, then
each div/mod site runs `mulhi` plus a conditional fixup, about 2× faster than
`idiv`. Negative operands fall back to exact `idiv`, so results are bit-for-bit
identical. This is what `libdivide` does by hand. It alone flipped the pi
benchmark from losing to C (93 ms) to winning (68 ms).

**Fast compiler.** `zc` compiles itself — `compiler/zc.zeph`, 18,000 lines with
the embedded runtime and standard library — to a 5 MB executable in about 1.1 s.

**Readable.** `and`/`or`/`not` rather than symbol soup, string interpolation
(`"hello {name}"`), no semicolons, `let` versus `var`.

**Batteries included.** Lists `[T]`, hash maps `[K: V]`, structs, enums (which
print their member name), optionals `T?`, closures, generics, structural
interfaces with dynamic dispatch, and `import "other.zeph"`.

**Three targets, one source.** A Windows PE (kernel32 only), a static Linux ELF
(`--linux`, raw syscalls, no libc), or a WebAssembly module (`--wasm`, the one
target still reclaiming by collection rather than counting). The `crosscheck`
scripts compile both native targets from the same sources and require identical
output.

**Talks to the machine.** A native-interop layer — `win("user32!GetDC", …)`, the
`callptr` intrinsic, `extern fn … from "x.dll"`, and raw-memory builtins — lets
pure Zephyr call the OS and the GPU. On top of it the repo ships a Vulkan
wrapper (`lib/vk`, with a Zephyr→SPIR-V shader compiler in `tools/zspv.zeph`),
an immediate-mode GUI toolkit (`lib/ui`), and threads (`lib/std/thread.zeph`,
`parallel_for`). `examples/graphics` drives all of it, from a software particle
rasterizer to a real-time geodesic-ray-traced black hole. See
[docs/graphics.md](docs/graphics.md).

**A standard library in Zephyr, not welded into the compiler.** `contains`,
`map`, `filter`, `fold`, `sort_by` and the rest live in `lib/std/list.zeph` as
ordinary generic code:

```zephyr
fn contains[T](xs: [T], x: T) -> bool {
    for v in xs { if v == x { return true } }
    return false
}
```

Type parameters are inferred from the arguments, and each instantiation is
type-checked with `T` bound, so `contains` gets the right `==` for `int`, `str`
or an enum without a trait system.

## Build

`zc.exe` is the compiler, written in Zephyr. It carries its own x86-64 assembler
and PE linker and depends on nothing but `kernel32.dll`. Rebuilding it means
compiling it with itself:

```powershell
.\scripts\selfbuild.ps1          # recompiles compiler\zc.zeph into a new zc.exe
.\zc.exe --rt app.zeph app.exe   # compile a program
```

`selfbuild.ps1` checks the bootstrap invariant: the new compiler must reproduce
itself byte-for-byte. Editing the compiler is editing `compiler\zc.zeph` and
running it again.

## Use

```powershell
.\zc.exe --rt app.zeph app.exe   # kernel32-only exe
.\app.exe
.\zc.exe --rt app.zeph app.s     # generated assembly instead
```

`zc.exe` is single-file: `runtime.zeph` and `std/` are embedded in the binary,
regenerated by `scripts\embed-gen.ps1`, which `selfbuild.ps1` runs for you. A
`runtime.zeph` or `std\` next to the exe, or in the current directory, overrides
the embedded copy — so the dev loop in this repo works against the on-disk
sources while a copied-out `zc.exe` still works alone.

### Packaging

`.\scripts\package.ps1` assembles `dist\zephyr-<version>\` and a `.zip`: the
single-file `zc.exe` plus docs and examples, no bootstrap sources, tests or
benchmarks. It self-checks by copying `zc.exe` into a bare directory and
compiling a std-importing program there before zipping.

## Documentation

- [Language tour](docs/tour.md) — Zephyr in ten minutes.
- [Language specification](docs/spec.md) — grammar, type rules, conversions,
  runtime semantics, native interop, targets, concurrency.
- [Graphics & GPU](docs/graphics.md) — the FFI, the Vulkan wrapper, the
  Zephyr→SPIR-V shader compiler, and the `examples/graphics` walkthrough.

## Self-hosting

The compiler exists twice: a bootstrap compiler in C (`bootstrap/zephyr.c`) and
the self-hosted one in Zephyr (`compiler/zc.zeph`, ~14,000 lines — lexer,
parser, type checker, optimizer, x86-64 code generator, assembler, PE linker).

A self-hosted compiler needs a starting binary, like rustc or the Go toolchain.
Everything C lives in `bootstrap\`, isolated from the live source, and produced
the first `zc.exe` once:

```powershell
.\bootstrap\build.ps1        # gcc builds the C seed, which emits the first zc.exe
```

After that gcc and the C sources are out of the toolchain, kept only so the
compiler can be reconstructed from nothing if the binary is lost.

```powershell
powershell -File bootstrap\bootstrap.ps1   # verifies both fixpoints
powershell -File bootstrap\nocc.ps1        # verifies the loop with no gcc and no C
```

`bootstrap.ps1` proves the fixpoint two ways: gcc assembling and linking `zc`'s
assembly output, and `zc` assembling and PE-linking its own `.exe` with no
external tools, twice, byte-identical. `nocc.ps1` goes further — the C seed
builds a kernel32-only `zc`, that `zc` compiles `zc.zeph` with `--rt` into
another kernel32-only `zc`, byte-identical on the second round, and the
C-free-built compiler then compiles and runs ordinary programs. After the seed,
gcc and the C runtime can be discarded.

Any change to code generation is promoted through a three-stage bootstrap: the
old compiler builds one carrying the new codegen, which rebuilds itself to a
byte-identical fixpoint. The compiler that ships always reproduces itself.

## The runtime, written in Zephyr

The runtime exists in two forms. The default is C (`bootstrap/runtime.c`,
`zephyr_rt.dll`), which has the tracing collector and full float support. The
second is written in Zephyr (`runtime.zeph`): allocation, strings, lists,
struct/list formatting, interpolation, panics, command-line args — all built
from Zephyr's low-level primitives, namely bitwise ops, raw memory access
(`load64`/`store8`/`addr`), and Win64 FFI to kernel32 (`win("WriteFile", …)`).

```powershell
.\zc.exe --rt app.zeph app.exe   # link the Zephyr runtime
.\app.exe                        # imports kernel32.dll only
```

The Zephyr runtime is feature-complete: every type including maps, enums,
optionals and function values; string/int/float parsing and float formatting
matching C's `%.15g`; file I/O; command-line args; and reference counting.
`examples/basics/ffi_runtime.zeph` is a smaller standalone demonstration —
stdout I/O and integer formatting in pure Zephyr, calling only kernel32.

### Reference counting

Every object carries a 24-byte header: a count, a pointer to a static shape
descriptor the compiler emits, and its size. The compiler holds an ownership
contract — an expression leaves an owned value in `rax`, every slot storing one
owns a count, and a function releases its locals on the way out — so retain and
release never appear in source. Nothing is deferred, so freeing spreads through
the program instead of pooling into a pause.

- 26–63 µs worst frame over 3,000 frames (three runs; p99 18 µs), 50 MB live,
  585 MB churned (`bench/gc_pause.zeph`), no frame over 1 ms. The allocation-free
  control loop in the same program peaks as high as 167 µs, so the worst frame is
  at the machine's own jitter. The tracing collector spiked to
  ~4 ms on the same workload, which drops frames.
- A 300k-iteration churn loop with a four-object live set peaks at 4 MB, and at
  4 MB again with the collector stubbed out. Counting does all the reclaiming.
- Compiling `zc.zeph`, about four million objects, leaves one unreachable object
  unfreed. The collector-era build left 3,996,212.

Counting cannot reclaim a cycle, so the conservative mark-sweep collector stays
linked underneath: a contiguous reserved heap with an object-start bitmap for
O(1) pointer identification, free lists for O(1) allocation, and roots scanned
from the machine stack and the globals array. It fires only when the free lists
come up empty past a growth target, which counting makes rare. Declaring a
back-edge weak, so cycles never form, is planned and not implemented.

## How it works

Both compilers share a pipeline: lexer → recursive-descent parser → type checker
→ inliner → optimizer passes → x86-64 code generator (Intel syntax) → peephole →
built-in assembler and PE linker. The assembler encodes exactly the instruction
vocabulary the code generator emits, and the linker writes a PE64 executable
directly, imports and sections and entry stub included. Every Zephyr value is 64
bits; composites live on a reference-counted heap.

The self-hosted `zc.exe` links the Zephyr runtime (`--rt`) and imports only
`kernel32.dll`. The C seed instead links `zephyr_rt.dll`, a small C runtime with
the same semantics, and carries an older subset of the optimizer. It exists only
to reconstruct the first `zc.exe` from source; the numbers above come from
`zc.exe`.

## Tests

```powershell
powershell -File tests\run_tests.ps1
powershell -File scripts\crosscheck-linux.ps1
powershell -File scripts\crosscheck-wasm.ps1
```

`run_tests.ps1` covers the examples, language features, allocation stress (200k
objects), compile-time errors, and runtime panics. The crosscheck scripts are
the only cover the non-Windows backends get, and the Linux one includes a
self-build fixpoint.

## Roadmap

Landed: maps, enums, modules, optionals, closures, generics, interfaces, float
formatting, reference counting, the inliner, register promotion (integer and
float), runtime-reciprocal division, a register-based calling convention for
user functions, and the Linux/ELF and WebAssembly backends. Then the language
round: `match`, if-expressions, `if let`, labeled loops, `defer`, `const`,
richer literals, tuples, structural `==`, generic structs, enums with values
(`Result[T, E]`), packed `[u8]`/`[f32]`, default parameters, `import ... as`,
`private`, `fn main()`, test blocks, and Linux threads with sync primitives.

Open, roughly in the order that would move the benchmarks:

- **Reference-counting overhead.** The cost is the number of retains executed,
  not the price of each, so the levers are all fewer owned reads: escape
  analysis to stack-allocate non-escaping temporaries, reuse analysis to write
  in place when a count is known to be one, and weak back-edges so cycles stop
  needing the collector. Counts are also non-atomic, so sharing an object across
  threads is unsound until they become interlocked.
- **Counting on WebAssembly.** That backend emits none and relies on the
  collector.
- **Feature parity across targets.** WebAssembly lacks files, closures,
  interfaces and threads; native interop (`extern fn … from`) is Windows-only.
- **Generic structs and interfaces.** An instance of a generic struct cannot
  yet satisfy an interface.
- **Overloading.** One name, one function. Generics covered the cases that
  mattered; overloading is a convenience.
- **More vectorizer idioms.** The AVX2 wins cover AXPY, fill and reduction
  shapes. Generalizing needs a real cost model.
