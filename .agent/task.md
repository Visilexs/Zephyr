Goal: native project-specific Zephyr ML + tested phase experiment
Spec version: 2026-09-21; source baseline 13f9f5832cc510f255f3316157033333d4f715fa

Actual HEAD / branch / dirty files:
  branch std-math-functions, ahead of origin/main by 4 commits, not pushed
  HEAD at clone was 13f9f58, identical to the pinned baseline; tree was clean
  Working tree clean at the end of this session

Approved milestone and remaining scope:
  M0 complete. M1b complete. M2a complete. M2b complete.
  M1a in progress: the numpy model reference is delegated to Codex and not
  yet verified. A PyTorch oracle proper is still blocked on the install.
  Not started: M3 onward.

Decisions made and reasons:
  See DESIGN.md, D1..D10. The load-bearing ones: lib/ml is library code and
  sits outside the embedded std glob, so it cannot perturb the self-host
  fixpoint; rejection is a panic rather than an error value, matching the
  language; strides count elements and convert to bytes at exactly one site.

Implemented files / interfaces:
  lib/ml/tensor.zeph            DType, Storage, Tensor, views, saved tensors,
                                broadcast_shape and t_expand, read-only views,
                                fills/copy/cast, index odometer, allocation
                                accounting, t_hex for layout inspection
  lib/ml/ops.zeph               elementwise add/sub/mul/div with broadcasting,
                                neg, conj, abs2, real, imag, expi, complex
                                construction, sum/mean, sum_dim, matmul,
                                conjugate transpose -- real and complex;
                                plus the M3 prerequisites: real unary maps
                                (tanh/cos/sin/exp/ln), index_select,
                                index_copy, roll and concat
  tests/ml/tensor_test.zeph     73 positive checks (A02, A03)
  tests/ml/ops_test.zeph        107 positive checks (A04, A05)
  tools/ml_reference/check_ops.py + ops_dump.zeph
                                numpy cross-check, 21 operators (A04, A05)
  tests/run_tests.ps1           + ml-tensor/ml-ops blocks, 15 ml-reject and
                                26 ops-reject cases
  tools/ml_reference/tasks.py   Task A and B generators, independent solvers,
                                seeded splits (written by Codex, verified here)
  tools/ml_reference/test_tasks.py  13 check groups (A30, A31)
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
  manual fixpoint zc -> stage-a -> b -> c     0, hashes equal each rebuild
  scripts\crosscheck-linux.ps1                0, 7/7
  scripts\crosscheck-wasm.ps1                 0, 7/7
  python tools/ml_reference/test_tasks.py     0, 13 groups
  tests/ml/tensor_test.zeph                   0, "tensor: 73 checks passed"
  tests/ml/ops_test.zeph                      0, "ops: 74 checks passed"
  python tools/ml_reference/check_ops.py      0, 33/33 agree with numpy
  python tools/ml_reference/test_phase.py     0, 12 groups, D=4/8/128
  python tools/ml_reference/verify_phase.py    0, 112 checks, 0 failed
  zc --linux + wsl, both ml suites            0, 73 and 107, same as Windows
  zc --wasm + node, both ml suites            0, 73 and 107, same as Windows
  embed-gen + manual 3-stage fixpoint         0, 691CB25F91B961F1 unchanged
  tests/math_fns.zeph                         0, "math: 213 checks passed"
  scripts\selfbuild.ps1                       1, objdump missing AFTER the
                                              fixpoint passed; not a failure
  tests\run_tests.ps1                         1, gcc missing, BLOCKED

Acceptance IDs: pass / fail / blocked / not_run:
  A00 pass, A02 pass, A03 pass, A04 pass, A05 pass, A10 pass, A11 pass,
  A12 pass, A30 pass, A31 pass
  A01 partial: fixpoint and crosschecks pass, the bootstrap suite is blocked
  everything else not_run. See RESULTS.md for the evidence behind each.

Fixture/config/data/checkpoint hashes:
  Task splits are seeded (default 1729) and their hashes are recomputed and
  asserted disjoint by test_tasks.py rather than pinned in a file. No model
  checkpoint exists yet.

Last measured results (or none):
  No model has been trained. No scientific measurement of any kind exists.
  Numerical measurements only, in RESULTS.md.

Known failure with exact reproduction:
  None outstanding. Two environment blockers, both pre-existing:
    powershell -File tests\run_tests.ps1   -> gcc not found, aborts at once
    powershell -File scripts\selfbuild.ps1 -> objdump not found at the last
                                              line, after the fixpoint passed

Next one concrete action:
  Verify the Codex-written tools/ml_reference/phase_model.py and test_phase.py
  the same way tasks.py was verified: re-run it, read the Givens and readout
  code against MATHEMATICS.md rather than trusting the report, and confirm the
  paired-real port really is a separate expression of the function and not the
  complex one in disguise. Then record A10, A11, A12 in RESULTS.md.

  After that, M3: port the phase forward pass to Zephyr on top of lib/ml/ops,
  and check it step by step against the numpy reference on shared fixtures.
  The operators it needs all exist now except the Givens pairing itself.

  A PyTorch oracle is still worth installing into a local environment when
  convenient, but it is no longer what blocks M3.

Rollback / preserved seed path:
  bootstrap/ untouched; no stage binary was ever promoted by hand. Every
  commit is on branch std-math-functions, nothing pushed, origin/main intact
  at 13f9f58.
