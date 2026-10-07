# Tests

Run `python3 tests/macos_tests.py` on native Apple Silicon. It verifies ARM64
Mach-O compiler/program outputs, language features, memory handling, I/O,
subprocesses, command-line arguments, baseline/optimized parity, regressions,
compile errors, bounds panics, and invocation outside the checkout. The math
fixture checks 213 assertions at both optimization levels. `./zc selfbuild`
separately verifies the native compiler's assembly fixpoint.

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

On Windows, run these after `scripts/selfbuild.ps1`, in this order:

| runner | checks |
|---|---|
| `pgo_roundtrip.ps1` | `--profile-generate`, a training run, then `--profile-use` gives the plain build's output on four programs |
| `run_tests.ps1` | language and runtime behaviour, including `fixtures/basics/integer_formatting.zeph` (digit boundaries, i64 extremes) |
| `std_tests.ps1` | the standard library |
| `optimizer_parity.ps1` | baseline and `-O2` give identical output, including the `regression/` cases and every battle workload at test size |
| `run_parity.ps1` | executables and `zc run` give identical output |
| `crosscheck-linux.ps1` | Windows and Linux (x86-64 WSL) output are byte-identical |
| `crosscheck-wasm.ps1` | Windows and WebAssembly (Node.js) output are byte-identical |
| `linux_extern.sh` | on Linux: `extern fn` through `dlopen`/`dlsym` (`tests/linux/`), baseline and `-O2`, as an executable and as an `.o` linked with gcc |

`regression/tail_recursion.zeph` covers the `-O2` tail-recursion rewrite:
- swapped parameters
- float chains
- `*` with the call on the left
- returns inside loops under an accumulator
- `^` after an effectful call
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
Cross-language performance comparisons on Windows use the separate
compiler-battle harness (see [../docs/optimizer.md](../docs/optimizer.md#measuring)).
