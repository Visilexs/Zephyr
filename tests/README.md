# Tests

Run `python3 tests/macos_tests.py` on native Apple Silicon. It verifies ARM64
Mach-O compiler/program outputs, language features, memory handling, I/O,
subprocesses, command-line arguments, baseline/optimized parity, regressions,
compile errors, bounds panics, and invocation outside the checkout. The math
fixture checks 213 assertions at both optimization levels. `./zc selfbuild`
separately verifies the native compiler's assembly fixpoint.

Run `python3 tests/macos_jit.py` to verify native in-memory execution and adaptive
tier transitions against the retained AOT path. It covers recursive frames,
shared globals, references, closures, interfaces, stack and floating arguments,
cold functions, optimization failures, I/O, guest panics, and compile errors.
Existing original regression fixtures are also exercised through the JIT.
See [../docs/jit.md](../docs/jit.md) for the current profiling scope.

The native integer array fast path is checked against 126 independent wrapping
arithmetic cases, odd loop tails, aliased arrays, empty ranges, overflowing
indices, expressions with side effects, packed byte lists, and bounds panics.
Weighted sums have 231 independent wrapping arithmetic cases, including odd
tails and nonzero starting indices. Fill checks cover short ranges and surrounding
canaries. The suite also runs `macos_codegen.py`: 878 native instruction checks
cover integer operations, every immediate double encoding, NaN and signed-zero
payloads, condition flags, and a conditional branch beyond one megabyte.

The complete native performance suite is available through
`python3 tests/benchmarks/macos.py`. See [benchmarks/README.md](benchmarks/README.md)
for its 19 workloads, comparison toolchains, and measurement policy.

On Windows, run `run_tests.ps1` for language/runtime checks, `std_tests.ps1` for
the standard library, `optimizer_parity.ps1` for baseline/optimized equivalence,
and `run_parity.ps1` for executable/in-process equivalence. Target cross-checks
are `crosscheck-linux.ps1` (x86-64 WSL) and `crosscheck-wasm.ps1` (Node.js).
The historical C-bootstrap checks are `bootstrap.ps1` and `nocc.ps1`; they
require rebuilding the C seed with `bootstrap/build.ps1` first.

Windows correctness checks after `scripts/selfbuild.ps1`:

```powershell
python scripts/embed-gen.py --check
python tests/argument_tests.py --compiler .\zc.exe
python tests/accumulator_recursion.py --compiler .\zc.exe
python tests/entry_return.py --compiler .\zc.exe
python tests/spill_codegen.py --compiler .\zc.exe
python tests/differential.py --cases 100 --seed 20261001
python tests/differential.py --pure --cases 100 --seed 20261001
```

The accumulator check verifies integer recursion results, wrapping overflow,
side-effect exclusions, and exact optimization reports at baseline, `-O2`, and
`-O2 -g`. The experimental pass applies only to the Windows target.

The entry-return check verifies all six signed comparisons, extreme integers,
argument preservation, and excluded guard/calling-convention forms. It inspects
assembly and forces real calls to check fast returns before frame setup.

The spill-codegen check generates a bounded register-pressure program and checks
baseline/optimized results against a wrapping-integer model. Assembly assertions
cover spill updates, value/branch comparisons, and encodable operand fallbacks.

The argument checks include empty arguments, whitespace, and arguments beyond
the old 2,048-byte limit. The seeded fuzzer compares baseline and `-O2` with an
independent model for bounded integer expressions and known results for floats,
ownership, closures, interfaces, maps, generics, and string building. Pure mode
excludes calls that mutate shared state. Failures are reduced by removing
independent source units and saved with expected output under `repro/`; the
printed seed reproduces the original program. This is bounded coverage, not
an interpreter for the full language.

`regression/evaluation_order.zeph` and `regression/global_store_exit.zeph` run
in both the core and optimizer parity suites. Parity includes all 19 workloads
at small test sizes; it does not measure their performance. Self-build compares
generations 2 and 3, allowing the checked-in seed to predate its source.

`fixtures/basics/`, `fixtures/threads/`, and `fixtures/wasm/` hold the source
programs used by those suites. `fixtures/workloads/` contains the Zephyr-only
workloads used by the parity tests. The native performance harness lives under
`benchmarks/` and recovers comparison sources into temporary storage from Git.

All original test files remain in the checkout. `ml/` preserves the former
optional ML/GPU regressions. `ml/legacy_checks.ps1` holds the checks extracted
from the main runner, and `ml/reference/` retains their reference tests and
comparison helpers. These are archived: the ML/Vulkan/UI implementations,
datasets, and shaders are outside this checkout's scope. The main Windows suite
prints an explicit skip when the ML library is absent. Running these archived
tests requires restoring their dependencies from the original repository.

Windows/Linux/WebAssembly suites require their respective hosts and have not
been execution-tested by the Apple Silicon cleanup validation.
