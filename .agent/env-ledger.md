# Environment ledger — acceptance A00

Probed 2026-09-21 on the machine running the work. The specification's
resource envelope was **user-reported**; this file records what was actually
**detected**, and the two are compared rather than conflated. No global
driver, package or OS setting was changed to produce any of it.

## Hardware

| Item | Spec says (user-reported) | Detected here | Agrees |
|---|---|---|---|
| GPU | RTX 5090, 32 GB | NVIDIA GeForce RTX 5090, 32607 MiB | yes |
| Compute capability | 12.0, *inferred from NVIDIA's table* | **12.0, reported by nvidia-smi** | yes, now measured |
| GPU driver | not stated | 616.92 (WDDM 32.0.16.1692) | — |
| CPU | Ryzen 7 9800X3D | AMD Ryzen 7 9800X3D, 8C/16T | yes |
| System RAM | 32 GB | 31.4 GB usable | yes |
| OS | Windows | Windows 11 Pro 10.0.26200 | yes |

Compute capability 12.0 is the consumer Blackwell target, distinct from
data-center 10.x. Per `zephyr-ml/07_GPU_BACKEND.md`, do not build `sm_100a`
kernels on the strength of the shared "Blackwell" name.

## Toolchains

| Tool | State | Consequence |
|---|---|---|
| `gcc` | **absent** | `bootstrap\build.ps1` cannot run, so `tests\run_tests.ps1` aborts before its first test. Blocks every `RunSrc` check. |
| `objdump` | **absent** | `scripts\selfbuild.ps1` exits 1 on its final DLL-listing line, *after* the fixpoint comparison and the promotion of `zc.exe` have both succeeded. Not a fixpoint failure. |
| `nvcc` / CUDA toolkit | **absent** | No NVRTC, no cuBLAS. |
| `nvcuda.dll` | present, 32.0.16.1692 | The CUDA **Driver API** ships with the driver and is reachable now. |
| `nvrtc64_*.dll` | absent | Runtime kernel compilation needs the toolkit. |
| `cublas64_*.dll` | absent | Vendor GEMM needs the toolkit. |
| Vulkan | SDK 1.4.357.0, `glslc` present, runtime apiVersion 1.4.351 on the 5090 | The Vulkan compute path is available end to end today. |
| Node, WSL, Python 3.13, numpy 2.5.2 | present | wasm and Linux crosschecks run; Python reference work is unblocked. |
| PyTorch | **absent** | M1a's oracle cannot run until it is installed in a local environment. |

### What this means for M5

The specification's provisional recommendation was to spike Vulkan against
CUDA and probably pick CUDA. On this machine as it stands, **Vulkan is the
only backend that can be exercised without installing anything**, and CUDA is
reachable only as far as the Driver API — enough to allocate, copy and launch
a precompiled module, not enough for NVRTC or cuBLAS. That does not decide
M5, which the spec requires be decided on measured end-to-end evidence, but it
does mean a CUDA spike has an install step in front of it that the Vulkan
spike does not. Record the toolkit version actually installed when that
happens; do not install one merely to claim a pass.

## Baseline build — acceptance A01

| Check | Result |
|---|---|
| Repository | `Visilexs/Zephyr` at `13f9f5832cc510f255f3316157033333d4f715fa` — identical to the SHA the specification was written against |
| Working tree at clone | clean |
| Seed binary | `bootstrap/` left untouched; no stage binary promoted by hand |
| Self-host fixpoint | **holds.** Stages A, B and C byte-identical at every rebuild in this session |
| Linux crosscheck | 7/7, including its own Linux self-build fixpoint |
| Wasm crosscheck | 7/7 |
| Self-hosted example + stdlib checks | 12/12, driven directly by `zc.exe --rt` |
| `tests\run_tests.ps1` | **BLOCKED, not passed** — no C compiler. Never reached its first assertion. |

## GPU compute probe, for M5

Measured with `vulkaninfo` from the installed SDK. Only what was read back is
recorded; nothing here is inferred from the part number.

| Property | Value |
|---|---|
| deviceName | NVIDIA GeForce RTX 5090 |
| shaderFloat64 | **true** |
| shaderInt64 | true |
| maxComputeSharedMemorySize | 49152 bytes |
| maxComputeWorkGroupInvocations | 1024 |
| maxStorageBufferRange | 4294967295 bytes |

`shaderFloat64` being true is the finding that matters, because everything in
`lib/ml` is float64 and both cross-check harnesses compare against a float64
reference with bit-identical fixtures. A float32-only compute path would have
forced either a second numerical standard or the abandonment of those
comparisons.

What this does **not** establish is throughput. Consumer NVIDIA parts have
historically run FP64 at a small fraction of their FP32 rate, and no rate has
been measured here. Support and speed are different questions and M5 asks for
measured step timings, so the tradeoff between an fp64 path that preserves
the existing parity evidence and an fp32 path that does not must be measured
rather than assumed.

## Measured matmul throughput, fp32 against fp64

`tools/gpu_probe.zeph`, RTX 5090, hand-written GLSL compiled with `glslc`,
correctness checked against `lib/ml/ops` before any timing is reported.
Warm median of 30 submissions (10 at the compute-bound sizes).

| shape | cpu ms | f32 ms | f64 ms | f64/f32 | rel err f32 | rel err f64 |
|---|---|---|---|---|---|---|
| controller W1 [32,416]x[416,128] | 216 | 0.113 | 0.122 | 1.08 | 6.6e-6 | 7e-15 |
| controller W2 [32,128]x[128,384] | 200 | 0.059 | 0.074 | 1.25 | 2.3e-6 | 2e-15 |
| readout [32,128]x[128,3] | 1.54 | 0.058 | 0.067 | 1.16 | 6.8e-7 | 1e-15 |
| square [256,256]x[256,256] | 2176 | 0.129 | 0.198 | 1.54 | 5.2e-6 | 5e-15 |
| n=512 compute-bound | -- | 0.900 (p95 0.979) | 1.143 (p95 1.498) | 1.27 | 2.5e-6 | 4e-15 |
| n=1024 compute-bound | -- | 11.32 (p95 11.80) | 17.45 (p95 18.08) | **1.54** | 6.6e-6 | 2e-15 |

**The 1.54 is not the FP64 arithmetic penalty and must not be quoted as one.**
At n=1024 the fp32 kernel achieves 190 GFLOP/s, which is roughly 0.2% of this
device's fp32 peak. The kernel is naive -- one global load per operand per
multiply-accumulate, no tiling, no shared memory -- so it is bandwidth-bound,
not ALU-bound. fp64 moves twice the bytes and lands at 1.54x, close to the 2x
a purely bandwidth-bound kernel predicts. The ALU ratio on consumer NVIDIA
parts is about 1/64, and none of it is visible here because the ALUs are idle
waiting on memory.

### Correction: fp64 on the device is not bit-identical to fp64 on the host

The earlier justification for an fp64 path -- that it preserves the
bit-identical float64 fixtures the cross-check harnesses compare -- is wrong,
and measurement showed it. Re-running `tests/ml/gpu_test.zeph` with every
tolerance set to exactly 0.0 fails 80 of its 272 numeric comparisons. The
disagreements are all around 1e-15 relative, consistent with the driver
contracting multiply-add pairs into FMA, which changes the rounding of the
accumulation.

So the honest statement is narrower: **fp64 on the device preserves float64
accuracy, not bit-identity.** The bit-exact `t_hex`-against-numpy comparisons
are inherently CPU-side and stay that way. fp64 is still the right choice for
the backend, but for the weaker and sufficient reason that 1e-15 agreement
keeps the GPU path meaningfully comparable to the verified CPU path, where
fp32's 6.6e-6 would not.

The consequence runs the wrong way from the comfortable reading: **the ratio
is favourable only because the kernel is slow.** Any tiling work that makes
the fp32 kernel approach its ceiling will widen the gap toward 64x, because
fp64 has far less headroom -- it is already at about 8% of its own peak. An
fp64 backend is cheap today and gets relatively more expensive with every
optimisation.

Two other measurements, both larger than the arithmetic:

* **Host upload runs at 327 MiB/s** (16 MiB in 49 ms). That is the per-byte
  `store8` loop the current mapped-memory API forces, not the bus. At n=1024
  upload costs 49 ms against 17 ms of compute, so transfer dominates by 3x. A
  bulk copy into mapped memory would buy more than any kernel tuning.
* **Cold pipeline build is 0.21-0.33 ms**, negligible, and the same for both
  precisions.

Also worth recording because it distorts any speedup claim: the CPU reference
`t_matmul` runs at 15 MFLOP/s, which is slow enough that GPU-vs-CPU ratios
here measure `t_get`/`t_set` overhead rather than the GPU.

## Full training step, CPU against the Vulkan backend

`tools/gpu_step_bench.zeph`. A step is what `overfit_test.zeph` runs every
iteration -- `pad_loss` over the batch, `av_backward` over the tape, gradient
clipping, AdamW -- with the only difference being whether `t_matmul`
dispatches to the device. Timing is reported only after both paths are shown
to produce the same loss and the same gradients.

| config | matmuls/step | fwd cpu ms | fwd gpu ms | fwd x | step cpu ms | step gpu ms | step x | peak device |
|---|---|---|---|---|---|---|---|---|
| small D=8 E=4 H=16 b=32 T=4 K=1 | 33 | 25.0 | 24.7 | 1.01 | 79.1 | 80.6 | **0.98** | 14.8 KB |
| spec D=128 E=32 H=128 b=32 T=4 K=2 | 39 | 2735.8 | 351.0 | 7.79 | 8395.0 | 1546.3 | **5.43** | 565 KB |

Medians of 12 and 6 timed repetitions; p95 within 1% of the median in every
row except the small forward pass.

Agreement: loss matches to 3e-15 relative at both sizes, and the gradients
match across **104,160 components** at the specification size with a worst
relative disagreement of 4e-14.

**The small configuration is a forward-only winner and therefore not a
winner.** It is 1.01x ahead on the forward pass and 0.98x behind on the full
step. A21 asks specifically that this case not be reported as a win, and the
benchmark prints the verdict rather than leaving it to be noticed: at that
size 33 dispatches of a tiny matmul cost more in submission and host transfer
than they save, and the backward pass adds the transposes and the second
matmul per node that tip it over. The backend is only worth enabling at the
specification dimension.

Note also that the win **narrows** from 7.79x to 5.43x once the backward pass
is included, for the same reason. Any speedup quoted from a forward pass alone
overstates the backend by about 40% here.

Two caveats that keep these numbers honest:

* The CPU side is `t_matmul`, which runs at about 15 MFLOP/s. Both sides are
  naive, so the comparison is fair as a same-workload measurement, but 5.43x
  is a statement about this pair of implementations and not about CPUs and
  GPUs in general.
* At the specification size a step still spends most of its GPU time in host
  upload, which the per-byte `store8` path caps at 327 MiB/s. The ceiling on
  this backend is the transfer API, not the kernel.

The benchmark is a tool rather than a suite entry: two minutes at the
specification size is too slow for `run_tests.ps1`, and the correctness it
depends on is already covered there by `ml-gpu`.

## Streams, events and allocator lifetime (A22)

`lib/ml/gpu_stream.zeph` and `tests/ml/gpu_stream_test.zeph`, 23 checks. The
suite implements the specification's own reference-test list one for one
rather than inventing a different set.

Design follows three sentences in the memory-runtime document. "Stream is an
ordered execution lane, not guaranteed independent hardware" -- so lanes need
no dedicated hardware queue. "Cross-stream consumers must wait on producer
events" -- so an event carries a binary semaphore for the device as well as a
fence for the host. "Releasing a tensor handle cannot immediately recycle
in-flight storage" -- so release moves an allocation to a retired list, and
only a completed fence promotes it to the free list. `vkDeviceWaitIdle`
appears nowhere; completion is polled per fence through `vkGetFenceStatus`,
the one binding that had to be hand-added.

### Three bugs the tests found, all the same bug

Each was a host-side use-after-free, which is the failure A22 is named for:

1. The pool created an event per allocation and `pool_touch` overwrote it,
   leaking the first and double-destroying the second.
2. The test destroyed its own events while the allocator still held those
   fence handles, so the next `vkGetFenceStatus` read freed memory.
3. `pool_destroy` destroyed events before waiting on the allocations that
   referenced them.

The resolution is that the pool takes ownership of any event handed to
`pool_touch`. The allocator outlives the submitter's interest in a
submission, so it cannot borrow the handle it polls.

A fourth, milder one: `stream_submit` allocated a command buffer per
submission and never freed it. The event now owns it and frees it after the
wait.

### Mutation testing, including one that did not fail

| mutation | result |
|---|---|
| recycle in-flight storage immediately | **caught** |
| ignore the refcount, retire on first release | **caught** |
| ignore cross-stream waits | **caught, but only after two rewrites** |
| put both lanes on one queue | passes, correctly |

The third row is the honest part. Deleting the cross-stream wait originally
left the suite green. Twice. The producer was 64x64 and finished in about
0.06 ms, while the host spends about 0.3 ms building the consumer's pipeline
and descriptor set, so the consumer could not have started early even without
a wait -- the test was measuring nothing. Moving the producer to 1024x1024,
where it runs for about 17 ms, made the wait load-bearing, and the test now
asserts that the producer was still running when the consumer was submitted
so it can never silently go vacuous again.

The fourth row is not a failure. One queue is in-order, so both lanes on one
queue still produce the right answer; the second queue is what makes the test
able to tell a real wait from luck, not what makes the code correct.

### One change outside lib/ml

`lib/vk/gfx.zeph` now requests two queues from the chosen family instead of
one, clamped to what the family exposes, and stores the second as
`Gfx.queue2`. Queue 0 and every existing caller are untouched. Verified by
re-running `examples/vulkan/compute.zeph` (6 sampled particles, 0 mismatches)
and the 277-check `ml-gpu` suite.

### Known portability gap, not yet fixed

`gfx.zeph` passes no `pEnabledFeatures` at device creation, so `shaderFloat64`
and `shaderBufferInt64Atomics` are used without being enabled. This driver
permits it and every result here is correct, but it is undefined behaviour by
the specification and would be the first thing to fail on another vendor.

## Op-coverage ledger (A23 scope, A41 requirement)

Derived by `tools/op_census.zeph`, which runs one real full step -- forward
and backward, real and complex -- and counts the opcodes the tape recorded.
A hand-maintained list would be wrong within a week; this asks the model.

426 tape nodes at D=16 E=8 H=32 K=2 batch 8 T=4. 25 distinct ops are reached
(LEAF is not a recorded node; SUB and COMPLEX are implemented and tested but
the phase model never uses them).

| op | nodes | of which complex | | op | nodes | of which complex |
|---|---|---|---|---|---|---|
| MUL | 101 | 55 | | TRANSPOSE | 13 | 9 |
| ADD | 41 | 29 | | TANH | 12 | 8 |
| INDEX_SELECT | 40 | 21 | | COS | 12 | 6 |
| CONCAT | 30 | 19 | | SIN | 12 | 5 |
| SLICE | 30 | 11 | | ABS2 | 8 | 6 |
| CAST | 25 | 10 | | RESHAPE | 7 | 5 |
| CONJ | 18 | 11 | | EXPAND | 7 | 4 |
| EXPI | 18 | 11 | | REAL | 6 | 5 |
| NEG | 13 | 4 | | IMAG | 6 | 5 |
| MATMUL | 13 | 10 | | ROLL | 6 | 5 |
| SUM_DIM | 2 | 2 | | LN | 2 | 1 |
| SUM_ALL | 1 | 0 | | MEAN_ALL | 1 | 0 |
| DIV | 1 | 1 | | EXP | 1 | 0 |

Only MATMUL is currently on the device, so A23 covers the other 24.

The census also settles a question the earlier measurements raised. MATMUL is
13 of 426 nodes, and it is the only one that is O(n^3); every other op here is
O(n) or O(n^2) in its operands. Moving an O(n) op to the device costs an
upload and a download of the same order as its work, against a host transfer
path measured at 327 MiB/s, so per-op dispatch would make those ops slower
rather than faster. A23's coverage requirement is therefore only compatible
with a useful backend if tensors stay resident on the device between ops,
which is the same lifetime problem A22 tests.

## Existing compute surface in this repository

Surveyed before planning M5, so the milestone starts from what is actually
here.

| Capability | State |
|---|---|
| Vulkan compute pipelines, storage buffers, descriptor sets, dispatch, barriers | present in `lib/vk/gfx.zeph`, proven end to end |
| A working numeric compute kernel | `examples/vulkan/compute.zeph`: 1.5M-element integration over 8 dispatches, read back and checked against a CPU closed form |
| Host-visible upload and readback | present |
| matmul, reduction, or any training kernel | **absent** |
| `tools/zspv.zeph` emitting compute shaders | **cannot** -- vertex and fragment only, float32 only, no storage buffers, no control flow |
| GLSL `.comp` to SPIR-V automation | **absent**; existing `.comp.spv` files were built out of band. `glslc` is present, so a script is straightforward |
| Regenerating Vulkan bindings via `tools/vkgen.c` | **blocked**, needs gcc. Existing generated coverage is broad, so new bindings would be hand-added instead |

So the plumbing exists and the gap is at the kernel-authoring layer. Kernels
would be hand-written GLSL compiled with `glslc`, as `particles.comp` already
is, rather than written in Zephyr through `zspv`.

The fixpoint was verified by hand rather than by trusting `selfbuild.ps1`'s
exit code, using the staged procedure in `zephyr-ml/15_BOOTSTRAP_PLAN.md`:
`embed-gen`, then `zc.exe` → stage-a → stage-b → stage-c, comparing SHA-256.
