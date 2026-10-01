# Native ARM64 code generation improvements

Run: 2026-09-30T23:40:01.140427+00:00. Apple M5, macOS 27.0.

Same original workload sizes, native optimized Zephyr before and after this change. The before compiler already includes the matrix NEON kernel. Each build had one warm-up and five timed samples, alternating execution order each round. Every output matched the checksum from the original full suite.
Median elapsed milliseconds including process startup; ± is median absolute deviation. Normal scheduling, no fixed CPU affinity. This run compares Zephyr versions; C was not rerun.

| Workload | Before (ms) | After (ms) | Speedup (×) |
|---|---:|---:|---:|
| fib | 750.74 ± 1.33 | 546.80 ± 5.00 | 1.37× |
| matmul | 370.25 ± 0.66 | 367.00 ± 0.84 | 1.01× |
| mandel | 540.47 ± 1.58 | 539.21 ± 0.96 | 1.00× |
| sort | 177.76 ± 1.35 | 164.55 ± 0.46 | 1.08× |
| strings | 239.31 ± 0.18 | 173.62 ± 0.24 | 1.38× |
| hashmap | 728.63 ± 32.44 | 592.15 ± 34.29 | 1.23× |
| cube | 843.27 ± 8.56 | 297.61 ± 2.21 | 2.83× |
| pi | 295.33 ± 3.47 | 253.60 ± 0.41 | 1.16× |
| liquid | 664.91 ± 0.90 | 553.41 ± 0.63 | 1.20× |
| shapes | 383.79 ± 4.07 | 307.82 ± 0.54 | 1.25× |
| closures | 435.33 ± 2.96 | 347.98 ± 2.49 | 1.25× |
| wordfreq | 491.98 ± 2.11 | 341.43 ± 0.61 | 1.44× |
| nbody | 434.05 ± 0.36 | 310.76 ± 0.85 | 1.40× |
| lexer | 671.08 ± 1.35 | 532.83 ± 3.08 | 1.26× |
| vectors | 648.88 ± 1.31 | 432.77 ± 1.29 | 1.50× |
| dispatch | 227.36 ± 0.28 | 208.10 ± 1.03 | 1.09× |
| records | 602.24 ± 0.89 | 513.72 ± 0.57 | 1.17× |
| strbuild | 616.13 ± 1.87 | 450.10 ± 0.75 | 1.37× |
| bintrees | 567.31 ± 2.58 | 395.73 ± 0.67 | 1.43× |
| mandel (baseline) | 476.49 ± 0.94 | 479.77 ± 0.32 | 0.99× |

All 19 workloads passed. Geometric mean speedup: 1.30×. Raw samples, memory measurements, and hashes are in the adjacent JSON.

The changes select direct integer arithmetic and immediate operands, direct floating loads and exact immediate double constants, short conditional branches when in range, four-word array fills, and a guarded two-lane NEON weighted-sum kernel. Integer wraparound, float bit patterns, bounds panics, and scalar fallback behavior are preserved.

Validation: 55 native Mac checks, 878 native instruction checks, 231 independent weighted-sum cases at both optimization levels, and a verified compiler self-build fixpoint. The native compiler image decreased from 22.49 to 16.98 MiB.

Mandelbrot remains slower with `-O2`: 539.21 ms versus 479.77 ms in the updated baseline. Resolving that regression requires further optimizer investigation.
