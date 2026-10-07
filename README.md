# Zephyr

A statically typed, self-hosted language with a reference-counted runtime.
The compiler is written in Zephyr and produces native code with its own
assembler and linker for these targets:

- Windows x86-64 (PE)
- Linux x86-64 (static ELF, no libc; `extern fn … from "libX.so.N"` loads
  shared libraries at run time, making the ELF dynamic)
- WebAssembly
- Apple Silicon macOS (ARM64 Mach-O, assembled and linked by Apple Clang)

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
.\zc.exe --linux --rt program.zeph program.o    # ELF object to link with C (zephyrMain)
.\zc.exe --wasm --rt program.zeph program.wasm  # run with: node scripts\wasm-run.js program.wasm
```

### On Linux

The `./zc` driver runs the native `zc-linux`, bootstrapping it once via wine
if it is missing:

```sh
./zc --linux --rt program.zeph program && chmod +x program   # static ELF
./zc --linux --rt program.zeph program.o                     # link with C: gcc -no-pie program.o main.c
```

With `extern fn … from "libX.so.N"` the ELF becomes dynamic (dlopen/dlsym,
spec §3.6); without it the output stays fully static. `zc-linux` is a build
product, kept at the self-build fixpoint by `scripts/linux-selfbuild.sh`.

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

On Linux the native `./zc-linux` is kept at the same fixpoint without wine
after one bootstrap (`wine zc.exe --linux --rt compiler/zc.zeph zc-linux`):

```sh
./scripts/linux-selfbuild.sh        # -O2 by default; OPT= for unoptimized
```

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

On Linux, `extern fn … from "libX.so.N"` (shared libraries via dlopen/dlsym,
described in [docs/spec.md](docs/spec.md) §3.6) is covered by:

```sh
./tests/linux_extern.sh            # needs ./zc-linux and gcc
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
./zc --test program.zeph /tmp/program-tests
./zc selfbuild
python3 tests/macos_tests.py
```

The compiler's IR goes through `scripts/macos/arm64.py` and Apple Clang, and
links against the Darwin runtime in `bootstrap/macos/`. `zc run` builds to a
temporary executable and runs it. On macOS:

- `--rt` is always on.
- `selfbuild` verifies an assembly fixpoint before it replaces `zc-macos`.
- Threads, Windows DLL interop, raw machine-code calls and general SIMD loop
  vectorization are not supported.

GitHub Actions runs this suite on an Apple Silicon runner for every push and
pull request (`.github/workflows/macos.yml`).

## Projects

Things built with Zephyr:

| project | what |
|---|---|
| [zui](https://github.com/Visilexs/zui) | a small React-style UI library; **pi-desk**, a native desktop window for the [pi](https://github.com/earendil-works/pi) coding agent, is built with it. Loads SDL3, FreeType and fontconfig at run time through `extern fn`, which needs the Linux dynamic-linking support above (`zc --version` lists `linux-extern`) |
| `zephyr-mc` | a system-by-system port of Minecraft Java Edition, rendering with Vulkan |
| `zephyr-wm` | an early Wayland tiling compositor for Linux |

## Layout

| path | contents |
|---|---|
| `compiler/zc.zeph` | front end, AST passes, x86-64 and WebAssembly back ends, assembler, linker, driver |
| `compiler/optimizer.zeph` | the `-O2` SSA tier |
| `compiler/runtime.zeph` | memory management, strings, collections, maps, sorting, threads |
| `lib/std/`, `lib/os/` | standard library; Linux and WebAssembly OS layers |
| `bootstrap/` | historical C seed and the native Darwin runtime |
| `scripts/` | self-build (Windows and Linux), embedding, macOS back end, WebAssembly runner |
| `tests/` | test runners, regressions, fixtures, macOS benchmarks |
| `editors/` | syntax highlighting for vim, micro, nano, bat, Sublime Text, highlight.js (`editors/install.sh`) |
