Goal: native project-specific Zephyr ML + tested phase experiment
Spec version: 2026-09-21; source baseline 13f9f5832cc510f255f3316157033333d4f715fa

NOTE ON THIS FILE: two earlier updates to it silently did nothing. Both used
str.replace without asserting the pattern matched, and on Windows a default
read_text() decodes as cp1252, so any pattern containing an en-dash fails to
match and the call returns the string unchanged with exit code 0. The same bug
dropped five rows from RESULTS.md's acceptance matrix. Every edit to these
records now reads bytes, decodes UTF-8 explicitly, and asserts each
substitution. If you are editing this file, do the same.

Actual HEAD / branch / dirty files:
  branch std-math-functions, 19 commits, ahead of origin/main, not pushed
  origin/main still at 13f9f58, identical to the pinned baseline
  HEAD 1b6d7bb at the time of writing; the M3 artifacts sit above it

Approved milestone and remaining scope:
  M0 complete. M1a complete. M1b complete. M2a complete. M2b complete.
  M3 complete. M4 complete.
  M1 as a whole is complete except its tiny-overfit clause, which needs the
  optimizer from M4. A PyTorch oracle is still absent; numpy carries the
  reference, and the substitution is justified per-acceptance in RESULTS.md
  rather than waved through -- for the operators it covers, both are IEEE-754
  double arithmetic, and the one thing that could differ, complex memory
  layout, is checked at the byte level instead of assumed.
  Not started: M5 onward. M5 has been scoped but not begun -- see the GPU
  probe and compute-surface survey in .agent/env-ledger.md.

Decisions made and reasons:
  See DESIGN.md, D1..D18. The load-bearing ones: lib/ml is library code and
  sits outside the embedded std glob, so it cannot perturb the self-host
  fixpoint (now measured, not merely argued); rejection is a panic rather than
  an error value, matching the language; strides count elements and convert to
  bytes at exactly one site; broadcast views are read-only; there is no dtype
  promotion anywhere; parity is checked per step with bit-identical weights.

Implemented files / interfaces:
  lib/ml/tensor.zeph            DType, Storage, Tensor, views, saved tensors,
                                broadcast_shape and t_expand, read-only views,
                                fills/copy/cast, index odometer, allocation
                                accounting, t_hex for layout inspection
  lib/ml/ops.zeph               elementwise add/sub/mul/div with broadcasting,
                                neg, conj, abs2, real, imag, expi, complex
                                construction, sum/mean, sum_dim, matmul,
                                conjugate transpose -- real and complex; plus
                                real unary maps (tanh/cos/sin/exp/ln),
                                index_select, index_copy, roll and concat
  lib/ml/phase.zeph             Phase Reasoner v1 forward pass: validation,
                                normalized init, invariant features, the
                                controller, phase gate, both Givens stages,
                                stable log-domain readout. Written by Codex,
                                reviewed line by line against the spec here.
  tests/ml/tensor_test.zeph     73 positive checks (A02, A03)
  tests/ml/ops_test.zeph        107 positive checks (A04, A05)
  tests/ml/phase_test.zeph      205 checks, D=4/8/128 (A13). Windows only: it
                                runs its rejection cases as child processes
                                via CreateProcessA, because a panic cannot be
                                caught in-process.
  tests/ml/phase_gates_test.zeph  1,981 gate-level checks (A10), written here
                                rather than by the agent, and the only phase
                                suite that runs on all three targets
  lib/ml/autograd.zeph          eager reverse-mode AD: opcode-and-handle tape,
                                analytic VJPs for 28 primitives, version-checked
                                saved tensors, detach / no_grad / explicit reset
  lib/ml/phase_ad.zeph          the phase forward pass on the tape; a second
                                expression of phase.zeph, held to it by test
  tests/ml/autograd_test.zeph   674 checks, 36 finite-difference cases (A06, A07)
  tests/ml/phase_ad_test.zeph   180 checks (A06, A14)
  tools/ml_reference/phase_grad_dump.zeph + check_phase_grad.py
                                native gradients vs the analytic reference,
                                18 quantities (A06, A14)
  lib/ml/optim.zeph             SGD with momentum, AdamW with decoupled decay
                                and per-component complex moments, joint
                                gradient-norm clipping (Codex; verified here)
  lib/ml/checkpoint.zeph        versioned, checksummed, validated-before-
                                allocating format; atomic save via temp file
                                and MoveFileEx (Codex; verified here)
  tests/ml/optim_test.zeph      82 checks + 11 rejection processes (A08, A09)
  tests/ml/overfit_test.zeph    132 checks, native 32-example overfit (A14)
  tools/ml_reference/optim_dump.zeph + check_optim.py
                                77 quantities vs paired-real numpy (A08)
  tests/run_tests.ps1           + ml-tensor/ml-ops/ml-phase/ml-phase-gates and
                                ml-phase-parity blocks, 15 ml-reject and 26
                                ops-reject cases
  tools/ml_reference/tasks.py   Task A and B generators, independent solvers,
                                seeded splits (written by Codex, verified here)
  tools/ml_reference/test_tasks.py   13 check groups (A30, A31)
  tools/ml_reference/phase_model.py  float64 Phase Reasoner v1 and an exact
                                paired-real port, both with analytic reverse
                                passes (Codex; verified here twice over)
  tools/ml_reference/test_phase.py   12 check groups (A10, A11, A12), Codex
  tools/ml_reference/verify_phase.py 121 checks written here from the spec
                                documents rather than from the module
  tools/ml_reference/check_ops.py + ops_dump.zeph
                                numpy cross-check, 33 operators (A04, A05)
  tools/ml_reference/check_phase.py + phase_dump.zeph
                                per-step parity, 148 quantities, 16 steps
  lib/std/math.zeph             prerequisite accuracy work, see git history
  tests/math_fns.zeph           213 checks
  GOAL.md DESIGN.md RESULTS.md .agent/env-ledger.md

Environment and dependency versions:
  Windows 11 Pro 10.0.26200, Ryzen 7 9800X3D 8C/16T, 31.4 GB RAM
  RTX 5090, 32607 MiB, compute capability 12.0 DETECTED, driver 616.92
  Python 3.13.14, numpy 2.5.2, Node present, WSL present
  Vulkan SDK 1.4.357.0, runtime apiVersion 1.4.351, glslc present
  nvcuda.dll present; NVRTC, cuBLAS and the CUDA toolkit ABSENT
  gcc ABSENT, objdump ABSENT, PyTorch ABSENT
  Full ledger with the user-reported comparison in .agent/env-ledger.md

Commands actually run, exit codes, log paths:
  zc.exe --rt <src> <exe>                     0, for every suite below
  manual fixpoint zc -> stage-a -> b -> c     0, 691CB25F91B961F1, unchanged
                                              by any of the ML work
  scripts\crosscheck-linux.ps1                0, 7/7
  scripts\crosscheck-wasm.ps1                 0, 7/7
  tests/math_fns.zeph                         0, "math: 213 checks passed"
  tests/ml/tensor_test.zeph                   0, "tensor: 73 checks passed"
  tests/ml/ops_test.zeph                      0, "ops: 107 checks passed"
  tests/ml/phase_test.zeph                    0, "phase: 205 checks passed"
  tests/ml/phase_gates_test.zeph              0, "phase gates: 1981 checks"
  python tools/ml_reference/test_tasks.py     0, 13 groups
  python tools/ml_reference/test_phase.py     0, 12 groups, D=4/8/128
  python tools/ml_reference/verify_phase.py   0, 121 checks, 0 failed
  python tools/ml_reference/check_ops.py      0, 33/33 agree with numpy
  python tools/ml_reference/check_phase.py    0, 148/148 quantities, 16 steps
  tests/ml/autograd_test.zeph                 0, "autograd: 674 checks passed"
  tests/ml/phase_ad_test.zeph                 0, "phase ad: 180 checks passed"
  python tools/ml_reference/check_phase_grad.py  0, 18/18 vs analytic
  tests/ml/optim_test.zeph                    0, "optim: 82 checks passed"
  tests/ml/overfit_test.zeph                  0, loss 1.4006 -> 0.0460
  python tools/ml_reference/check_optim.py    0, 77/77 quantities
  extracted ad + parity blocks standalone     0, 33 passed, 0 failed
  vulkaninfo                                  0, shaderFloat64 = true
  extracted autograd block from run_tests     0, 2 passed, 0 failed
  extracted parity+reject block               0, 28 passed, 0 failed
  zc --linux + wsl, tensor/ops/phase_gates    0, same counts as Windows
  zc --wasm + node, tensor/ops/phase_gates    0, same counts as Windows
  extracted ops-reject block                  0, 26 passed, 0 failed
  extracted phase block from run_tests.ps1    0, 3 passed, 0 failed
  scripts\selfbuild.ps1                       1, objdump missing AFTER the
                                              fixpoint passed; not a failure
  tests\run_tests.ps1                         1, gcc missing, BLOCKED

Acceptance IDs: pass / fail / blocked / not_run:
  A00 pass, A02 pass, A03 pass, A04 pass, A05 pass, A10 pass, A11 pass,
  A06 pass, A07 pass, A12 pass, A13 pass, A30 pass, A31 pass
  A08 pass, A09 pass, A14 pass
  A01 partial: fixpoint and both crosschecks pass, the bootstrap suite is
  blocked. The blocker is structural, not a missing package -- see below.
  everything else not_run. See RESULTS.md for the evidence behind each.

Fixture/config/data/checkpoint hashes:
  Task splits are seeded (default 1729) and their hashes are recomputed and
  asserted disjoint by test_tasks.py rather than pinned in a file.
  Phase parity weights come from a mirrored LCG seeded 20260921, rebuilt
  independently on each side and asserted bit-identical rather than pinned.
  No model checkpoint exists yet.

Last measured results (or none):
  No model has been trained. No scientific measurement of any kind exists.
  Numerical measurements only, in RESULTS.md. Nothing measured so far says
  anything about whether the phase architecture works.

Known failure with exact reproduction:
  None outstanding. Two environment blockers, both pre-existing:
    powershell -File tests\run_tests.ps1   -> gcc not found, aborts at once.
      Root cause is structural: the suite drives bootstrap\zephyr.exe, the
      historical C seed, not the shipped zc.exe. The seed binary is committed
      but needs zephyr_rt.dll, which only gcc builds. So even with gcc this
      suite would not be testing the compiler we ship. Deliberately not
      rewritten to target zc.exe: its negative cases match the C compiler's
      exact error text, so a swap would manufacture failures. The math and ML
      suites are run directly through zc.exe instead, and the reject blocks
      are extracted and run standalone.
    powershell -File scripts\selfbuild.ps1 -> objdump not found at the last
      line, after the fixpoint has already passed.

Next one concrete action:
  M5. GPU feasibility comparison and one complete training backend. The
  groundwork is already recorded in .agent/env-ledger.md and it narrows the
  milestone considerably:

    * The Vulkan compute path exists and works -- storage buffers, descriptor
      sets, compute pipelines, dispatch, barriers, readback -- and
      examples/vulkan/compute.zeph proves it end to end on 1.5M elements.
    * tools/zspv.zeph CANNOT emit compute shaders (vertex/fragment only,
      float32 only, no storage buffers, no control flow), so kernels are
      hand-written GLSL compiled with glslc, which is present. No script
      automates that step yet; one is trivial to add.
    * shaderFloat64 is true on this device, so an fp64 path is possible at
      all. Whether it is affordable is unmeasured, and that measurement is
      the heart of the milestone: everything in lib/ml is float64 and both
      cross-check harnesses compare bit-identical float64 fixtures, so an
      fp32 backend would cost the parity evidence built over M2 to M4.

  Start with the smallest honest probe: one matmul kernel, fp64 and fp32,
  timed against the CPU implementation at the shapes the phase model
  actually uses, with correctness checked against lib/ml/ops. Report the
  fp64/fp32 ratio as a measurement. Do not commit to a backend before that
  number exists -- the whole milestone turns on it.

Rollback / preserved seed path:
  bootstrap/ untouched; no stage binary was ever promoted by hand. Every
  commit is on branch std-math-functions, nothing pushed, origin/main intact
  at 13f9f58.
