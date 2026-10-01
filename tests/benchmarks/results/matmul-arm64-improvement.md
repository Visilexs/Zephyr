# Native ARM64 matrix multiplication improvement

Run: 2026-09-30T23:16:04.927334+00:00. Apple M5, macOS 27.0, native arm64.

Matrix size: 1100 × 1100. Every warm-up and timed run returned checksum `26952750000`.
One warm-up per build, up to 10 interleaved timed samples, 30-second accumulated budget per build (minimum three samples). Normal scheduling; CPU affinity was not fixed.
Times are median elapsed milliseconds including process startup; ± is median absolute deviation. Memory is peak resident set for one process.

| Build | Time (ms) | Time vs C (×) | Samples | Peak RSS (MiB) |
|---|---:|---:|---:|---:|
| Previous Zephyr -O2 | 4220.66 ± 18.17 | 9.54× | 8 | 30.3 |
| Updated Zephyr baseline | 374.80 ± 1.90 | 0.85× | 10 | 30.5 |
| Updated Zephyr -O2 | 375.01 ± 2.65 | 0.85× | 10 | 30.4 |
| C -O2 | 442.31 ± 2.32 | 1.00× | 10 | 29.3 |

Updated optimized Zephyr is 11.25× faster than the previous compiler in this run.

The updated compiler uses a guarded native NEON kernel for integer scaled-vector additions, with scalar fallback for unsafe bounds, aliases, packed byte lists, and side-effecting expressions. Its two-lane multiplication preserves all 64-bit wraparound results.
Validation: 46 native Mac checks, 126 arithmetic cases at both optimization levels, matrix sizes 0, 1, 2, 3, 5, 17, 31 and 1101 matching C, and a verified compiler self-build fixpoint.

The previous compiler and previous ARM64 selector were rebuilt from a snapshot taken before this change; updated builds use the rebuilt native compiler. The matrix workload was unchanged. C flags: `clang -arch arm64 -O2 -fwrapv -ffp-contract=off`.
Raw timings, compiler hashes, and toolchain details are in the adjacent JSON. This focused run does not replace the earlier full 19-workload report.
