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
| `tools/ml_reference/test_tasks.py` | 13 groups, 10,240 examples per task | ~8s |

## Interpretation, kept separate

Nothing here says anything about the phase architecture. No model has been
built, nothing has been trained, and no comparison against any baseline
exists. The task generators being correct means the *data* is sound, not that
the hypothesis has support. `gamma` agreeing with itself by two routes is
evidence about the implementation, not about anything scientific.
