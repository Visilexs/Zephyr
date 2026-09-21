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
