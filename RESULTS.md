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
| A01 | **partial** | Self-host fixpoint holds (stages A/B/C byte-identical, verified by hand at each rebuild). Linux crosscheck 7/7 including its own fixpoint; wasm 7/7; 12/12 self-hosted example and stdlib checks. `tests\run_tests.ps1` is **blocked**, and the reason is worth stating precisely rather than as "gcc missing": the suite's first action is `bootstrap\build.ps1`, and every case it then runs goes through `bootstrap\zephyr.exe run`. It therefore exercises the historical C seed, which `bootstrap/README.md` itself describes as kept only so the toolchain can be reconstructed, adding that nothing in that folder runs in day-to-day use. `bootstrap\zephyr.exe` is present and committed, but refuses to start without `zephyr_rt.dll`, which only gcc builds. The blocker is therefore structural, not incidental: even with gcc installed this suite would not be testing the self-hosted compiler we ship. It was deliberately not rewritten to drive `zc.exe` instead, because many of its negative cases assert on the C compiler's exact error text and a swap would manufacture failures and a pass that meant less than it appeared to. What does cover the live compiler here: the three-stage fixpoint, both crosschecks, and every suite under `tests/` run directly through `zc.exe`. |
| A02 | **passed** | `tests/ml/tensor_test.zeph`, 73 checks, plus 15 rejection cases each in their own process. Covers dtype sizes, scalar and empty shapes, row-major strides, broadcasting including 1-against-0, and rejection of negative dimensions, element overflow, the byte cap, out-of-range and wrong-rank indices, bad reshape, non-contiguous reshape, slice and axis bounds, and incompatible broadcast. |
| A03 | **passed** | Same suite. Owner/view sharing, writes visible in both directions, a view outliving the owner handle, version bumps through views, stale-save detection, and 50 allocate/release cycles returning to a zero baseline with peak at one buffer rather than fifty. |
| A04 | **passed** | `tests/ml/ops_test.zeph`, 107 checks, plus 26 rejection cases in their own processes. Independently, `tools/ml_reference/check_ops.py` agrees with numpy on all 33 operators, most bit-exact. Non-contiguous inputs are covered by running the same operators through transposed and sliced views. |
| A05 | **passed** | Same suites. Complex mul, div, conj, abs2, expi and matmul against analytic values; byte layout compared against numpy's `complex64`/`complex128`, which share PyTorch's memory format. |
| A06 | **passed** | `tests/ml/autograd_test.zeph`, 674 checks. Thirty-six cases, each differentiated analytically and then probed with central differences on the same graph, real and imaginary parts perturbed separately. Because Zephyr has no closures a case is an integer and one `build()` is the dispatch, so the analytic path and every probe call identical code and cannot drift apart. `grad(abs2(z))` is asserted to be **exactly** 2z rather than close, since it is the case that pins the dL = Re(conj(g) dz) convention. Broadcast and shared-parameter contributions are covered: a row reused across four rows receives four summed contributions and its gradient is reduced back to its own shape, a handle used twice accumulates both paths, and x*x differentiates to 2x through that accumulation rather than a special rule. The whole-model gradients are covered separately by A14 below. |
| A07 | **passed** | Same suite. `av_backward` consumes the tape and a second call panics; a tensor mutated in place between forward and reverse makes the reverse pass panic, through the version-checked `Saved` type from M2a, rather than returning a plausible wrong gradient; `detach` yields a leaf with the value and no history; `no_grad` records no node and resumes cleanly; an operation whose inputs all require no gradient records nothing at all, so inference costs no tape rather than a tape that is discarded. Tape growth is measured, not bounded loosely: one step records exactly three nodes and twenty-five steps leave exactly three. |
| A08 | **passed** | `tests/ml/optim_test.zeph` (82 checks) and `tools/ml_reference/check_optim.py` (77/77 quantities against a paired-real numpy AdamW, all but one bit-exact at 0.000e+00). The two failure modes that still appear to train are tested explicitly rather than assumed: **decoupled weight decay** is checked by giving a parameter a zero gradient and requiring it to decay by exactly lr*wd*p while both moments stay zero, which is what separates AdamW from Adam with L2; and **separate real and imaginary moments** are checked against two independent real parameters whose gradients differ by six orders of magnitude (0.001 against 1000), compared with `t_hex`, so a shared second moment or a moment of a magnitude could not survive. Also covered: SGD by hand-computed value, momentum over three steps, two AdamW steps so bias correction is distinguishable, global gradient-norm clipping scaling all parameters jointly and leaving them bit-unchanged under the threshold, and step counts. |
| A09 | **passed** | Same suite, plus `lib/ml/checkpoint.zeph`. Round trip is bit-exact via `t_hex` for real and complex tensors and for both moment buffers. **Resume equivalence** is the strong form: six continuous steps versus three steps, checkpoint, restore, three more, compared bit-exactly on parameters, both moments and the step count, with non-constant gradients so a dropped moment or a reset counter would show. **Interrupted writes preserve the prior file**, verified by comparing the original file's actual bytes after a failed write, after a mid-write interruption, and after a rename deliberately forced to fail by holding a lock on the target -- and the successful replacement path is checked too, so the failure paths are not passing vacuously. Eleven malformed inputs are rejected with distinct messages, each in its own process: bad magic, unknown version, truncated file, declared length exceeding the file, shape/payload mismatch, bad checksum, and four oversized-metadata cases refused **before** any allocation. |
| A20 | **passed** | Device and toolchain probe recorded in `.agent/env-ledger.md`. `lib/ml/gpu.zeph` runs matmul forward and backward on the device for real and complex float64, and `tools/gpu_step_bench.zeph` drives a whole phase training step -- forward and backward, real and complex -- through it. `tests/ml/gpu_test.zeph` (277 checks) compares both directions against the CPU path and against the autograd tape, whose matmul VJP is itself verified against finite differences, and also covers non-contiguous transposed operands and a shape that is not a multiple of the workgroup. Unavailable-backend messages name the missing file, the script that builds it and the tool that script needs, and are checked on a path that really is absent rather than asserted. Three mutations were caught: a dropped complex cross term (83 failures), a plain transpose where the backward needs a conjugate transpose (70), and a removed shader bounds guard (32). |
| A21 | **blocked** | The Vulkan arm is complete. `tools/gpu_step_bench.zeph` runs the same full training step on both paths and reports correctness first: the loss agrees to 3e-15 and the gradients agree across 104,160 components to 4e-14 at the specification size. Warm median and p95, cold pipeline build, host transfer rate, peak device memory and fp32 against fp64 are all in `.agent/env-ledger.md`. **No forward-only winner is reported as a winner:** at D=8 the backend is 1.01x ahead on the forward pass and 0.98x behind on the full step, and the benchmark prints that verdict explicitly; at D=128 it is 7.79x ahead on the forward pass and 5.43x on the full step, so the win narrows by about 40% once the backward is included. **The CUDA arm cannot be run on this machine** -- NVRTC, cuBLAS and the CUDA toolkit are all absent -- so the Vulkan-against-CUDA comparison this criterion asks for does not exist and is not claimed. |
| A22 | **passed** | `tests/ml/gpu_stream_test.zeph`, 23 checks, implementing the reference-test list in the specification's memory-runtime document one for one: owner deleted while view lives, view deleted before owner, producer on stream A consumed on B, release immediately after launch, host source mutated during flight, allocation failure (in a child process, since it panics), repeated loop returning to a stable live-byte baseline, and a 40-iteration delayed-completion stress that checks the no-in-flight-reuse invariant at every acquisition rather than once at the end. Completion is polled per fence via `vkGetFenceStatus`; `vkDeviceWaitIdle` is not used. Three host-side use-after-frees were found and fixed by giving the pool ownership of any event passed to `pool_touch`. Mutation-tested: immediate recycling of in-flight storage, refcount-ignoring release, and cross-stream wait removal are all caught -- the last only after the producer was enlarged from 64x64 to 1024x1024, because at the smaller size the test was vacuous and passed with the wait deleted. It now asserts the producer is still running when the consumer is submitted. |
| A23 | **passed** | Output gates: `tests/ml/gpu_ops_test.zeph`, 95 checks over 47 comparisons at 1e-12, covering four binary ops, thirteen unary ops, `sum_dim` on every axis, gather (with `roll` and `concat` expressed through it) and scatter-add with repeated indices, in both dtypes at ranks 1 to 3; transpose, slice, reshape and expand are metadata under the stride contract and are tested by feeding non-contiguous views into the other kernels. Gradient and update gates: `tests/ml/gpu_grad_test.zeph`, 15 checks, running one phase training step entirely on the CPU and again with every supported op on the device -- loss, 964 gradient components and 964 parameter components after an AdamW step with weight decay all agree to 1e-12, and a fourth gate confirms 54 matmuls actually reached the device so the agreement is not the two paths being the same code. No VJP is reimplemented for the device: the VJPs are compositions of the hooked primitives, which is what makes this "supported with VJP" rather than "the forward agrees". Mutation-tested at both levels. Complex transcendentals are device-only (`t_map1` panics on complex), are not reached by the model, and are not claimed. |
| A24 | **passed** | `lib/ml/ir.zeph` and `tests/ml/ir_test.zeph`, 58 checks, implementing the acceptance list at the end of the specification's tensor-IR section one item at a time. Eight invalid-IR cases, each built by mutating a real capture, every diagnostic naming its tape node; a clean graph must still verify, so rejection is not unconditional. Eager versus captured output and gradient equivalence through a replay interpreter that panics on an unknown opcode rather than skipping it. Guard misses on shape, dtype and arity, each reporting what it got against what was specialised, with the eager fallback exercised afterwards. Cache invalidation across all eight key components the specification lists, one changed at a time. A rank-5 graph produces a source-located diagnostic that also says it must stay eager. The real phase model captures and verifies clean. Mutation-tested; one hash test was found to be passing for the wrong reason and replaced. Found and fixed a real bug: the `OP_CAST` VJP panicked on a same-dtype cast. |
| A25 | **passed** | `tests/ml/opt_test.zeph` (23 checks) and `tests/ml/fusion_test.zeph` (40 checks), implementing the optimization section's gate list for three optimizations: a hoisted-stride matmul, the fused Givens stage, and the fused controller nonlinearity. **The profile came first**, as that section demands, and contradicted the candidate order it suggests: at the specification's dimensions matmul was 94.85% of the forward pass and the elementwise work the fusion targets was about 1.9%, so matmul was fixed first and the fusions were written only once re-profiling made them worth writing. End to end the step went 8093 ms to 564 ms, 14.3x, with the loss bit-identical at every stage. Forward parity is **bit-exact via `t_hex`**, not a tolerance: each kernel evaluates the composed expression in the same order, including the multiplications by the zero imaginary part that a real-to-complex cast introduces, so equality is the correct gate and a reassociation would be caught. Gradients are bit-exact for the matmul and the controller fusion; for the Givens fusion the adjoint is a short closed form rather than a transcription of the composed backward, so they are gated at 1e-14 relative and the measured worst is 3.6e-16, printed scaled by 1e18 because Zephyr's `print` is fixed-point and would show it as a flat 0. **Pairing:** each stage is checked to write all D output coordinates exactly once and to preserve every row's norm, and the two overlapping stages are shown to be genuinely sequenced -- reversing them gives a different answer, and running both against the same input gives a third -- so the ordering is a fact about the code rather than an intention. There is no in-kernel barrier because there is no fused GPU stage: on the host the sequencing is two calls, and the specification's block-barrier case does not arise. **Memory report:** the tape falls from 426 to 186 nodes at specification size, 292 to 132 in the gate, with identical output storage; peak allocator bytes are not reported because this library does not expose that counter. Both latencies are reported separately and the suite asserts the optimized path is faster cold and warm, which is what enforces "a slower optimization remains disabled". Seven mutations caught: reversed matmul accumulation (5 failures), matmul validation bypassed (2), wrong sign on the Givens second row (10), overlapping instead of disjoint pairs (13), conjugate dropped from the Givens adjoint (2), bias added after the nonlinearity instead of before (7), and the 1-tanh^2 factor dropped from the controller adjoint (3). Two bugs in the suite itself were found and fixed on the way: a comparison that reused already-updated checkpoints, and an invalid-input case whose mutation was applied after the parameters were built, so it was testing nothing. |
| A32, A33, A40, A41 | **not_run** | Not started. The specification defines no A15–A19, A26–A29 or A34–A39; the 27 defined IDs are A00–A14, A20–A25, A30–A33, A40 and A41. |
| A10 | **passed** | `tools/ml_reference/test_phase.py` (12 groups, D=4/8/128 and the spec defaults) *and* an independently written `tools/ml_reference/verify_phase.py`, 121 checks, coded from MATHEMATICS.md rather than from the module. Pair bijection and bounds at D=4/8/128, G^H G=I built from the doc's own matrix, inverse by G^H, norm preservation, simultaneity, and 10,000 fixed-angle gates drifting 1.1e-16. No renormalization exists anywhere in the update path. The native port is covered separately by `tests/ml/phase_gates_test.zeph`, 1,981 checks and the only phase suite that runs on all three targets, which pins the pairing `phase_givens` builds in Zephyr at D=4, 8 **and 128** -- the per-step parity harness only reaches D=4 and D=8, and a pairing that was a bijection but paired the wrong coordinates would preserve the norm perfectly and go unnoticed. It also checks inverse by G^H, per-stage norm preservation, the stage-B wrap from the last coordinate to the first, and that the two stages are genuinely different permutations. Its assertions were confirmed load-bearing by mutation: perturbing the expected pairing makes it panic on the first check. |
| A11 | **passed** | Same two suites. Probabilities invariant and state equivariant under global phase at three angles, controller angles unchanged, features invariant under global phase but sensitive to relative phase and matching the doc formula bit-for-bit. The constructed interference example is internally inconsistent in the specification -- with the normalized row it states, the squared amplitude is (1+cos(delta))/2, not the 1+cos(delta) the prose claims -- so both forms are asserted explicitly and the discrepancy is recorded as DESIGN.md D16 rather than absorbed into a tolerance. The claim the paragraph actually makes, that two orthonormal rows sweep [1,0] to [0,1] while global phase moves neither, holds exactly. |
| A12 | **passed** | Same two suites. The paired-real port agrees with the complex model on loss, probabilities, state and every one of the eight parameter gradients to 1e-12, and holds no complex array at all. Both are checked against central differences: worst relative error 3.7e-10, real and imaginary parts separately. The mapped optimizer step is the SGD check in test_phase.py; AdamW waits for M4. |
| A13 | **passed** | `tools/ml_reference/check_phase.py` compares the Zephyr port against the verified float64 reference on **148 quantities and all 16 steps** at D=4 and D=8: not just the final probabilities but, for every step, the invariant features, the controller hidden layer, the angles, the post-phase state, both Givens stage outputs, the resulting state and the active-row mask. Worst disagreement 2.3e-16. The two sides build their weights independently from a mirrored LCG and all 16 parameter tensors are asserted **bit-identical**, so the agreement cannot be an artifact of a drifting fixture. Masks preserve state exactly (compared as hex, not within a tolerance); K=0/1/4 give exact update counts and are cross-checked by recomposing K THINK steps independently; zero, subnormal and near-overflow readouts all stay finite. |
| A14 | **passed** | Native forward and backward are finite and verified. `tools/ml_reference/check_phase_grad.py` agrees with the reference's **analytic** reverse pass on 18/18 quantities at D=4 and D=8 -- the loss and all eight parameter gradients, complex ones on both components -- to between 2.6e-17 and 1.9e-15. That is the sharp form of the test: finite differences inside Zephyr already pass, but the reference's own stencil error is 3.7e-10 while its two model implementations agree to 1e-12, so the analytic comparison removes slack the stencil cannot. `tests/ml/phase_ad_test.zeph` adds 180 checks including forward agreement with the M3-verified `phase.zeph`. The bounded overfit is `tests/ml/overfit_test.zeph`, 132 checks: 32 examples driven from loss 1.4006 to 0.0460 and accuracy 0.5 to 0.96875 in 120 steps and 10.8s, with **no Python runtime dependency** -- data, model, gradients, AdamW and metrics are all native and the reported numbers come out of the binary. |
| A30 | **passed** | `tools/ml_reference/test_tasks.py`. Solver agrees with the label on 10,240 examples per task, recomputing from the token sequence alone. Task A query-only baseline sits within 0.125 ± 0.04 of chance on every split. Task B per-example: ≥2 feasible until the final clue, exactly 1 after, and the final clue combined with the original candidate list admits ≥2. |
| A31 | **passed** | Same suite. Seeded split hashes reproducible and pairwise disjoint, no duplicates within a split, frozen vocabulary covering all test tokens, composition and length bins non-empty, exact class balance, and class mean lengths equal to 1e-12 so length does not leak the target. |

## Measurements

### End-to-end profile and what it changed (A25)

`tools/ml_profile.zeph`, at the specification's dimensions (D=128, E=32,
H=128, K=2, batch 32, T=4). The per-op column comes from replaying the
captured IR node by node with a timer around each, which covers all opcodes
the model reaches rather than only the six op families a hook-based profiler
would see.

| Stage | Step | Forward | Backward | Optimizer | Tape nodes |
|---|---|---|---|---|---|
| before any optimization | 8093 ms | 2646 | 5416 | 32 | 426 |
| hoisted-stride matmul | 778 ms | 218 | — | 32 | 426 |
| plus the fused Givens stage | 597 ms | 170 | 395 | 32 | 198 |
| plus the fused controller | 564 ms | 160 | 372 | 32 | 186 |

14.3x end to end. The loss is bit-identical across all four rows at
1.31231441239229.

Forward share by op, before and after:

| op | before | after |
|---|---|---|
| matmul | 94.85% (2480 ms) | 46.70% (69.3 ms) |
| concat | 1.00% | 13.35% |
| mul | 0.93% | 7.59% |
| givens (was 17 nodes of elementwise) | — | 2.62% |
| bias_tanh (was tanh + broadcast add) | — | 3.09% |

Two cautions about that table rather than one. The `transpose` row, 16% after
optimization, is **replay overhead and not real work**: `av_transpose` is
metadata on the tape, and the replay interpreter materialises it with
`t_copy` so that a node has a value to hand on. It does not exist in the
eager forward pass. And replay timing carries a roughly constant per-node
cost, so a cheap op with a large node count is partly reporting dispatch, not
arithmetic -- which is why the node count is printed next to every time.

Isolated kernel speedups, warm, from the two gate suites:

| Kernel | Shape | Composed | Fused | Speedup |
|---|---|---|---|---|
| matmul | [64,256]x[256,128] | 264 ms | 7.3 ms | 36.3x |
| givens stage 0 | [64,128] | 9.7 ms | 0.65 ms | 14.2x |
| bias_tanh | [64,256] | 2.8 ms | 0.86 ms | 3.2x |

The matmul figure is not an arithmetic improvement. The reference reads every
element through `t_get`, which allocates a two-element index list per access;
for that shape it is 1.7 million list allocations to do 1.7 million
multiply-adds. The kernel computes the same sums in the same order with the
byte strides hoisted out of the inner loop, which is why the result is
bit-identical rather than merely close.

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
| `tools/ml_reference/verify_phase.py` | 121 | ~5s |
| `tests/ml/phase_test.zeph` | 205 | ~1s |
| `tests/ml/phase_gates_test.zeph` | 1,981 | ~1s |
| `tools/ml_reference/check_phase.py` | 148 quantities, 16 steps | ~2s |
| `tests/ml/autograd_test.zeph` | 674 | ~3s |
| `tests/ml/phase_ad_test.zeph` | 180 | ~4s |
| `tests/ml/optim_test.zeph` | 82, plus 11 rejection processes | ~6s |
| `tests/ml/overfit_test.zeph` | 132 | ~11s |
| `tools/ml_reference/check_optim.py` | 77 quantities | ~2s |
| `tests/ml/gpu_test.zeph` | 277 | ~3s, skipped without a Vulkan device |
| `tools/ml_reference/check_phase_grad.py` | 18 quantities | ~2s |
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

| Target | tensor | ops | phase gates |
|---|---|---|---|
| Windows x86-64 PE (kernel32) | 73 passed | 107 passed | 1,981 passed |
| Linux x86-64 static ELF (raw syscalls, no libc) | 73 passed | 107 passed | 1,981 passed |
| WebAssembly (node) | 73 passed | 107 passed | 1,981 passed |

`tests/ml/phase_test.zeph` is deliberately absent from this table: it is
Windows-only by construction, because it runs its rejection cases as child
processes through `CreateProcessA` (a panic cannot be caught in-process). So
the forward-pass invariants -- norm preservation, global-phase invariance, PAD
identity, THINK counts, readout edges -- are currently verified on Windows
only. The gate-level suite, which needs no subprocess, covers all three.

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

### Phase forward port against the reference, per step

D=4 and D=8, four sequence tokens then four THINK steps, batch of three
including a fully padded row.

| Quantity | worst scaled disagreement |
|---|---|
| all 16 parameter tensors | 0.0, bit-identical |
| active-row masks | 0.0 |
| controller hidden layer | 5.2e-17 |
| angles | 8.7e-17 |
| invariant features | 2.1e-16 |
| post-phase state | 1.9e-16 |
| Givens stage 0 and stage 1 | 2.0e-16 |
| state after each step | 2.0e-16 |
| probabilities | 2.3e-16 |

A couple of ulp, consistent with a different summation order and with this
repository's own `fsin`/`fcos` standing in for libm. Nothing here is a
tolerance chosen to make a comparison pass: the weights are bit-identical, and
a quantity missing from the dump or present but unexpected is a failure rather
than a silent omission.

### Native gradients against the reference's analytic reverse pass

Whole model, mean NLL, batch of three including a fully padded row, four
tokens and four THINK steps.

| Quantity | D=4 | D=8 |
|---|---|---|
| loss | 2.1e-16 | 1.1e-16 |
| embedding | 2.6e-17 | 3.7e-17 |
| think | 1.6e-16 | 9.5e-17 |
| W1 | 1.3e-15 | 4.3e-16 |
| b1 | 5.3e-16 | 1.1e-15 |
| W2 | 1.4e-15 | 1.1e-15 |
| b2 | 1.2e-15 | 1.9e-15 |
| z_init, complex | 5.8e-16 | 1.7e-15 |
| M, complex | 1.5e-15 | 1.6e-15 |

A few ulp, on gradients that pass through the controller, both Givens stages,
the phase gate, the readout and z_init's normalization. The complex
parameters agree on both components, so two independently written
implementations carry the dL = Re(conj(g) dz) convention identically.

These are sharper than the finite-difference numbers elsewhere in this file
for a reason worth stating: the stencil is the loose party. The reference's
analytic gradients agree with its own central differences only to 3.7e-10,
while its complex and paired-real models agree with each other to 1e-12.
Comparing native gradients against the analytic ones therefore tests
something the stencil cannot resolve.

### Optimizers against a paired-real numpy reference

77 quantities: parameters, both moment buffers and the step count, after
each of SGD, SGD with momentum and AdamW, at one, two and three steps, for
real and complex parameters, plus the clipping path.

| Result | Quantities |
|---|---|
| bit-exact, 0.000e+00 | 76 |
| 3.7e-17 | 1, the clipping norm under threshold |

Bit-exactness is the point rather than a bonus. A complex parameter is
required to match two independent real parameters exactly, so the complex
path cannot be quietly averaging, sharing a second moment, or working from a
magnitude -- all of which still descend, and all of which would pass a loose
tolerance.

### Bounded overfit, native (A14)

D=8, E=4, H=16, K=1, 32 examples of length 4, AdamW at lr 0.02, 120 steps.

| | start | end |
|---|---|---|
| mean NLL | 1.40064338692914 | 0.04599491937856 |
| accuracy | 0.5 | 0.96875 (31 of 32) |

Wall clock 10.8s. Gradients are scanned for NaN every step rather than only
at the end, and divergence is excluded by a separate check from improvement.

**This measures the plumbing, not the architecture.** The labels are
deliberately pseudo-random and unrelated to the tokens, which makes fitting
them a capacity and optimization check: it shows the tape, the VJPs and AdamW
compose into a working training loop. It says nothing about the phase
architecture, about generalization, or about the hypothesis this project
exists to test, and it must not be cited as if it did.

### Mutation testing of the gradient suites

A passing test that cannot fail is worth nothing, so the two AD suites were
checked by deliberately breaking the code they cover.

| Mutation | Caught by |
|---|---|
| drop the 1-t^2 factor from the tanh VJP | central differences |
| drop the conjugate from the complex product rule | central differences |
| flip a sign in the expi VJP | central differences |
| drop the conjugate from the Givens b-branch | forward agreement with phase.zeph |
| reverse the cyclic neighbour in the feature map | forward agreement with phase.zeph |

The last two matter most: both are self-consistently differentiable, so
finite differences alone would pass them. They are caught only because
`phase_ad` is required to reproduce the independently verified `phase.zeph`.

## Interpretation, kept separate

Nothing here says anything about the phase architecture. No model has been
built, nothing has been trained, and no comparison against any baseline
exists. The task generators being correct means the *data* is sound, not that
the hypothesis has support. `gamma` agreeing with itself by two routes is
evidence about the implementation, not about anything scientific.
