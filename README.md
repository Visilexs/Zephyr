# Zephyr

A statically typed, self-hosted language compiler and reference-counted runtime.
This checkout contains the compiler, runtime, standard library, build support,
and tests. Language rules are in [docs/spec.md](docs/spec.md), and standard
library APIs are in [docs/std.md](docs/std.md).

## Apple Silicon macOS

Requires an Apple Silicon Mac, native ARM64 Python 3, and Apple Command Line
Tools (`xcode-select --install`). The deployment target is macOS 13. Both the
compiler seed and generated executables run native ARM64 instructions.

```sh
./zc --version
./zc tests/fixtures/basics/hello.zeph /tmp/hello
/tmp/hello
./zc run tests/fixtures/basics/hello.zeph
./zc run program.zeph "argument with spaces"
./zc run --jit-threshold 1000 --jit-report /tmp/profile.json program.zeph
./zc --test program.zeph /tmp/program-tests
python3 tests/macos_tests.py
python3 tests/macos_jit.py
./zc selfbuild
```

`--rt` is always enabled on macOS. Output ending in `.s` emits ARM64 assembly.
`selfbuild` builds two native compiler generations and verifies their assembly
fixpoint before replacing `zc-macos`. Keep the seed beside `compiler/` and `lib/`.
Generated programs require only macOS system libraries to run.

`zc run` is the native ARM64 JIT execution path. It assembles baseline code,
relocates it into executable memory, and runs it in the driver's process.
Runtime call counters trigger selective `-O2` recompilation of hot functions;
future calls switch tiers through stable entries. Closures and interface method
pointers retain their identity, globals stay shared, and active frames finish
in their original code. Failed optimization keeps baseline execution working.
`--jit-baseline` disables adaptive compilation; `run -O2` starts optimized and
does not collect hotness feedback. See [docs/jit.md](docs/jit.md) for scope,
profiling, and timing details.

Builds with an explicit output path retain the AOT path for compiler bootstrapping,
standalone artifacts, and comparison tests. The frontend's IR passes through
`scripts/macos/arm64.py` and Apple Clang to produce ARM64 Mach-O.
`bootstrap/macos/` supplies native OS services for
memory, files, directories, clocks, environment variables, and subprocesses.
Closures, interfaces, collections, scalar math, and `-O2` are supported.
Native threads, Windows DLL interop, raw machine-code calls, and general SIMD
loop vectorization remain unsupported. Integer array
updates of the form `output[a + j] += factor * input[b + j]` have a native
two-lane NEON fast path with range and alias guards.
Integer array fills use wide native stores; weighted sums
`sum += values[i] * i` have a guarded NEON kernel and scalar tails.
Literal double quotes inside command-line arguments are rejected;
the inherited file-size and directory-name limits still apply.

## Windows, Linux, and WebAssembly

The existing Windows seed retains its x86-64 Windows/Linux and WebAssembly
backends. Run these commands in PowerShell on Windows:

```powershell
.\zc.exe --rt program.zeph program.exe
.\scripts\selfbuild.ps1
powershell -File tests\run_tests.ps1
powershell -File tests\std_tests.ps1
powershell -File tests\optimizer_parity.ps1
powershell -File tests\run_parity.ps1
.\zc.exe --linux --rt program.zeph program
.\zc.exe --wasm --rt program.zeph program.wasm
node scripts\wasm-run.js program.wasm
powershell -File tests\crosscheck-linux.ps1
powershell -File tests\crosscheck-wasm.ps1
```

The Linux cross-check requires x86-64 WSL; WebAssembly requires Node.js.
The historical Windows C seed is in `bootstrap/`.

## Tests and layout

- `compiler/`: frontend, optimizer, and Zephyr runtime.
- `lib/std/`, `lib/os/`: standard library and Linux/WebAssembly OS runtimes.
- `bootstrap/`, `scripts/`: compiler bootstrap and build/run tools.
- `tests/`: existing tests, target cross-checks, and required source fixtures.
- `.github/workflows/macos.yml`: native Apple Silicon self-build and test job.

Test inputs formerly under examples and benchmarks are now in `tests/fixtures/`.
All existing test files are retained. ML/GPU tests and their reference checks are
archived under `tests/ml/`; their optional implementation libraries, shader
assets, and datasets have been removed. The main suite skips those checks.
See [tests/README.md](tests/README.md) for the test scope.

After editing runtime or standard-library sources, regenerate the compiler's
embedded sources with `scripts/embed-gen.ps1` before rebuilding. Never edit the
generated `>>>EMBED` section by hand. The Windows self-build does this automatically.
