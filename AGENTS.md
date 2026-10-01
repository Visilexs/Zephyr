# Project instructions

Read `README.md` for build commands and layout. `docs/spec.md` is authoritative
for Zephyr syntax, type rules, conversions, and runtime semantics; do not assume
Rust or Swift behavior. `docs/std.md` describes the standard library.

The live compiler is `compiler/zc.zeph`, with `compiler/optimizer.zeph` and
`compiler/runtime.zeph`. The `>>>EMBED` section is generated from the runtime
and `lib/std/*.zeph`: never edit it by hand. Use `scripts/embed-gen.ps1` after
changing those sources. Newly introduced syntax cannot be used in the compiler
until the bootstrap seed understands it.

Keep compiler seeds at the repository root. Use `./zc selfbuild` and
`python3 tests/macos_tests.py` and `python3 tests/macos_jit.py` on native Apple Silicon; use
`scripts/selfbuild.ps1` and the PowerShell test runners on Windows.
Do not run Windows-only suites on macOS or silently route native builds through
an instruction emulator or compatibility layer.
`zc run` uses native in-memory JIT execution with function hotness feedback.
Explicit output builds remain the AOT bootstrap and regression path. Keep their
benchmark results distinct; the JIT currently has no value speculation or OSR.

This checkout is scoped to the compiler, runtime, standard library, build tools,
and tests. Test fixtures are in `tests/fixtures/`. Retain the archived ML tests
under `tests/ml/`, but do not restore removed optional libraries or applications
unless requested. The core suite skips their checks.
