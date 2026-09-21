# Results

Measurements only. Interpretation is kept separate and marked as such, per
`phase-llm/EVALUATION.md`. A number that was not produced by a command run in
this repository does not belong here.

Status vocabulary: `passed`, `blocked`, `not_run`. Nothing is recorded as
passed on the strength of an exit code alone.

## Acceptance matrix

| ID | Status | Evidence |
|---|---|---|
| A00 | **passed** | `.agent/env-ledger.md`. Detected hardware matches the user-reported envelope; compute capability 12.0 now measured rather than inferred. No global change made. |
| A01 | **partial** | Self-host fixpoint holds (stages A/B/C byte-identical, verified by hand at each rebuild). Linux crosscheck 7/7 including its own fixpoint; wasm 7/7; 12/12 self-hosted example and stdlib checks. `tests\run_tests.ps1` is **blocked** — no C compiler, so it aborts before its first assertion. |
| A02 | **passed** | `tests/ml/tensor_test.zeph`, 73 checks, plus 15 rejection cases each in their own process. Covers dtype sizes, scalar and empty shapes, row-major strides, broadcasting including 1-against-0, and rejection of negative dimensions, element overflow, the byte cap, out-of-range and wrong-rank indices, bad reshape, non-contiguous reshape, slice and axis bounds, and incompatible broadcast. |
| A03 | **passed** | Same suite. Owner/view sharing, writes visible in both directions, a view outliving the owner handle, version bumps through views, stale-save detection, and 50 allocate/release cycles returning to a zero baseline with peak at one buffer rather than fifty. |
| A30 | **passed** | `tools/ml_reference/test_tasks.py`. Solver agrees with the label on 10,240 examples per task, recomputing from the token sequence alone. Task A query-only baseline sits within 0.125 ± 0.04 of chance on every split. Task B per-example: ≥2 feasible until the final clue, exactly 1 after, and the final clue combined with the original candidate list admits ≥2. |
| A31 | **passed** | Same suite. Seeded split hashes reproducible and pairwise disjoint, no duplicates within a split, frozen vocabulary covering all test tokens, composition and length bins non-empty, exact class balance, and class mean lengths equal to 1e-12 so length does not leak the target. |
| A04–A29, A32–A41 | **not_run** | Not started. |

## Measurements

### Self-host fixpoint

Verified by hand rather than via `selfbuild.ps1`'s exit code, which fails on a
missing `objdump` *after* the comparison has already passed. Procedure from
`zephyr-ml/15_BOOTSTRAP_PLAN.md`: `embed-gen`, then zc.exe → stage-a →
stage-b → stage-c, comparing SHA-256.

| After | zc.exe = stage-a = stage-b = stage-c |
|---|---|
| inverse trig / special functions | `183ED8CB10ACF6E4…` |
| parameterised quadrature | `404D119B10ACF6E4…` |
| fln contract + docs | `85355088F3E87175…` |
| 2pi reduction split | `691CB25F91B961F1…` |

A==B==C each time, which is stronger than the required B==C.

### std/math accuracy against libm

295 values, compared against Python's `math` using a different formula on the
reference side wherever one exists.

| | |
|---|---|
| Functions within 1e-15 | 30 of 33 |
| Bit-exact | 3 |
| Worst case | 1.557e-13, at `gamma(170)` |
| Next worst | 6.37e-14 `digamma(-0.5)`, 6.20e-14 `digamma(1.5)` |

`gamma(170)` is inherent to `exp(lgamma)` where lgamma ≈ 701; `digamma(1.5)`
is 2.3e-15 in absolute terms and only looks poor because digamma has a root
at 1.4616.

### Defects found and fixed in the pre-existing std/math

| Defect | Measured before | After |
|---|---|---|
| `fexp` carried float32 range bounds | `exp(100)` short by 5 orders of magnitude, `exp(700)` by 266, `exp(-100)` flushed to 0 | full f64 range |
| `tanh` cancellation near zero | 6.1e-9 relative at x=1e-8 | at 1 ulp |
| `fsin` term count | ~5e-10 at ±π, capping tan/csc/cot/gd_inv/digamma | ~1e-16 |
| `fln` term count | ~1e-13 absolute, multiplied by (z+0.5) inside gamma | ~1e-16 |
| single rounded 2π in reduction | 7.736e-11 at x=1e6, growing linearly | 0.0 at x=1e6 |

### Gamma by two independent routes

Lanczos rational approximation against numerical integration of the Euler
integral, sharing nothing but `exp` and `ln`.

| x | relative disagreement |
|---|---|
| 0.25 – 1.5 | 3.2e-14 to 9.5e-14 |
| 2 | 2.4e-13 (worst) |
| 3 – 17 | ≤ 3e-15 |

`gamma(0.5)²` lands on π to 6e-13. Quadrature path costs ~0.44s for the whole
sweep.

### Test suite sizes

| Suite | Checks | Runtime |
|---|---|---|
| `tests/math_fns.zeph` | 213 | 0.49s |
| `tests/ml/tensor_test.zeph` | 73 | instant |
| tensor rejection cases | 15 processes | ~5s |
| `tests/ml/ops_test.zeph` | 107 | instant |
| ops rejection cases | 26 processes | ~8s |
| `tools/ml_reference/test_phase.py` | 12 groups, D=4/8/128 | ~6s |
| `tools/ml_reference/verify_phase.py` | 112 | ~5s |
| `tools/ml_reference/test_tasks.py` | 13 groups, 10,240 examples per task | ~8s |

### CPU operators against numpy

33 operators, values crossing as IEEE-754 bit patterns rather than decimal
text so nothing is lost to formatting.

| Result | Operators |
|---|---|
| bit-exact, 0.0 error | add, sub, mul, div, broadcast add, neg, sum_dim 0 and 1, sum_all, mean_all, mul through transposed operands, complex add, conj, real, imag, index_select (both dims, real and complex), roll (both directions, real and complex), concat (both dims) |
| 1-4 ulp | tanh 1.1e-16, cos 1.7e-16, exp 3.3e-16, sin 3.5e-16, matmul 3.3e-16, complex matmul 4.4e-16, abs2 3.1e-16, complex mul 4.3e-17, complex div 2.1e-17, expi 8.3e-17 |

The non-zero cases differ only in accumulation order, and `expi` additionally
goes through this repository's own `fsin`/`fcos` rather than libm. The same
is true of tanh/cos/sin/exp: every pure data-movement operator is bit-exact,
and only the ones routed through `lib/std/math.zeph` differ at all.

numpy stands in for PyTorch here, which is not installed. For these operators
the two agree by construction: both are IEEE-754 double arithmetic, and
numpy's `complex128` has the same memory layout as `torch.complex128`. The
byte-level check confirms that layout directly -- Zephyr's `C32` buffer for
1.5-2.25j is `0000c03f000010c0`, which is what numpy writes for `complex64`.

### The ML library on all three targets

The tensor and operator suites were compiled for each backend from the same
sources and run. Not a milestone requirement -- recorded because portability
is cheap to lose silently and M5/M8 depend on it.

| Target | tensor | ops |
|---|---|---|
| Windows x86-64 PE (kernel32) | 73 passed | 107 passed |
| Linux x86-64 static ELF (raw syscalls, no libc) | 73 passed | 107 passed |
| WebAssembly (node) | 73 passed | 107 passed |

Identical counts, and identical assertions, so the stride arithmetic, the
complex component layout and the reference-counted buffers all behave the
same on a target with no libc and on one with a collector instead of counting.

### Self-host fixpoint is unaffected by the ML work

Re-verified after `lib/ml` grew to two modules: `embed-gen`, then
zc.exe -> stage-a -> stage-b -> stage-c, all four `691CB25F91B961F1...`,
byte-identical to the hash recorded before any ML code existed. `lib/ml` sits
outside the `lib\std\*.zeph` embed glob, so this is the measured form of
DESIGN.md D1 rather than an argument for it.

### Reference model gradients against central differences

Phase Reasoner v1 at D=4, all eight parameters, real and imaginary parts
perturbed separately, step 1e-6, two-sided.

| Parameter | worst relative error |
|---|---|
| M | 8.6e-11 |
| b2 | 1.2e-10 |
| think | 1.6e-10 |
| b1 | 1.7e-10 |
| z_init | 2.2e-10 |
| embedding, W2 | 2.5e-10 |
| W1 | 3.7e-10 |

The floor here is the finite difference, not the analytic gradient: the
complex and paired-real models agree with each other to 1e-12, an order of
magnitude tighter than either agrees with the stencil.

## Interpretation, kept separate

Nothing here says anything about the phase architecture. No model has been
built, nothing has been trained, and no comparison against any baseline
exists. The task generators being correct means the *data* is sound, not that
the hypothesis has support. `gamma` agreeing with itself by two routes is
evidence about the implementation, not about anything scientific.
