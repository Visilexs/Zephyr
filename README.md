# Zephyr

A statically typed, self-hosted language with a reference-counted runtime.
The compiler is written in Zephyr and produces native code with its own
assembler and linker for these targets:

- Windows x86-64 (PE)
- Linux x86-64 (static ELF, no libc)
- WebAssembly
- Apple Silicon macOS (ARM64 Mach-O, with an in-memory JIT)

```zephyr
struct Point { x: float, y: float }

fn length(p: Point) -> float { return sqrt(p.x * p.x + p.y * p.y) }

let points = [Point { x: 3.0, y: 4.0 }, Point { x: 6.0, y: 8.0 }]
var total = 0.0
for p in points { total += length(p) }
print("total {total}")
```

## Documentation

| document | covers |
|---|---|
| [docs/spec.md](docs/spec.md) | language rules, types, memory model, targets, command-line flags |
| [docs/std.md](docs/std.md) | standard library |
| [docs/optimizer.md](docs/optimizer.md) | the `-O2` tier: inlining, specialization, partial inlining, recursion passes, profile-guided builds, reports, known gaps |
| [docs/jit.md](docs/jit.md) | the Apple Silicon JIT |
| [tests/README.md](tests/README.md) | test suites |

## Windows, Linux and WebAssembly

Run these from the repository root in PowerShell. `zc.exe` is the checked-in
compiler seed.

```powershell
.\zc.exe --rt program.zeph program.exe          # baseline build
.\zc.exe -O2 --rt program.zeph program.exe      # optimized build
.\zc.exe run program.zeph arg1 arg2             # compile in memory and run
.\zc.exe --test program.zeph program-tests.exe  # build the file's test blocks
.\zc.exe --linux --rt program.zeph program      # static Linux ELF
.\zc.exe --wasm --rt program.zeph program.wasm  # run with: node scripts\wasm-run.js program.wasm
```

### Profile-guided builds

```powershell
.\zc.exe -O2 --rt --profile-generate app.zprof app.zeph train.exe
.\train.exe
.\zc.exe -O2 --rt --profile-use app.zprof app.zeph app.exe
```

To see what the optimizer did, use these flags (all described in
[docs/optimizer.md](docs/optimizer.md)):

- `--opt-report`: decisions per function
- `-O2 --callgraph-report`: the call graph
- `--map`: a symbol map for profilers

### Rebuilding the compiler

```powershell
.\scripts\selfbuild.ps1
```

This does three things:

1. Regenerates the embedded runtime and standard-library sources.
2. Builds the compiler three times (seed → s1 → s2 → s3) and requires s2 and
   s3 to be byte-identical.
3. Replaces `zc.exe`.

Every code-generation change must pass this fixpoint. The `>>>EMBED`
section of `zc.zeph` is generated from `compiler/runtime.zeph` and
`lib/std/*.zeph`; never edit it by hand.

### Checks

After a self-build, run:

```powershell
powershell -File tests\pgo_roundtrip.ps1
powershell -File tests\run_tests.ps1
powershell -File tests\std_tests.ps1
powershell -File tests\optimizer_parity.ps1
powershell -File tests\run_parity.ps1
powershell -File tests\crosscheck-linux.ps1   # needs x86-64 WSL
powershell -File tests\crosscheck-wasm.ps1    # needs Node.js
```

## Apple Silicon macOS

Requirements:

- an Apple Silicon Mac
- native ARM64 Python 3
- Apple Command Line Tools (`xcode-select --install`)

The deployment target is macOS 13.

```sh
./zc tests/fixtures/basics/hello.zeph /tmp/hello && /tmp/hello
./zc run program.zeph "argument with spaces"
./zc run --jit-threshold 1000 --jit-report /tmp/profile.json program.zeph
./zc --test program.zeph /tmp/program-tests
./zc selfbuild
python3 tests/macos_tests.py
python3 tests/macos_jit.py
```

`zc run` uses the native JIT. Code starts at the baseline tier. Call counters
then trigger `-O2` recompilation of hot functions, and later calls reach the
new code through stable entries. See [docs/jit.md](docs/jit.md).

Builds with an explicit output path use the AOT path: the IR goes through
`scripts/macos/arm64.py` and Apple Clang, and links against the Darwin runtime
in `bootstrap/macos/`. On macOS:

- `--rt` is always on.
- `selfbuild` verifies an assembly fixpoint before it replaces `zc-macos`.
- Threads, Windows DLL interop, raw machine-code calls and general SIMD loop
  vectorization are not supported.

## Layout

| path | contents |
|---|---|
| `compiler/zc.zeph` | front end, AST passes, x86-64 and WebAssembly back ends, assembler, linker, driver |
| `compiler/optimizer.zeph` | the `-O2` SSA tier |
| `compiler/runtime.zeph` | memory management, strings, collections, maps, sorting, threads |
| `lib/std/`, `lib/os/` | standard library; Linux and WebAssembly OS layers |
| `bootstrap/` | historical C seed and the native Darwin runtime |
| `scripts/` | self-build, embedding, macOS back end, WebAssembly runner |
| `tests/` | test runners, regressions, fixtures, macOS benchmarks |
