# Native Apple Silicon JIT benchmark

Started: 2026-10-01T00:13:42.873246+00:00. Machine: Apple M5; macOS 27.0; native ARM64.

All 19 selected original workloads use their original arguments. Every measurement launches a fresh process. JIT warm-up runs do not preserve compiled tiers into later measurements.

One validation/warm-up per mode; up to 10 rotated, interleaved timed samples. Per-mode cold-process timing budget: 30 seconds, with at least three samples. Normal scheduling; no fixed CPU affinity.

C and AOT entry timers surround the actual program entry and include flushing output. JIT entry timing includes tier compilation pauses. **Execution** subtracts those pauses and includes baseline-to-optimized transitions and profiling overhead; it is not steady-state timing. All measurements validate their checksum.

C uses Clang -O2 with signed wraparound and no floating-point contraction. Fresh AOT -O2 is a reference. JIT baseline disables profiling; JIT adaptive uses a 1,000-call threshold; JIT starts -O2 compiles optimized before execution and has no adaptive profiling.

Cold-process totals include startup and compilation for JIT. C/AOT cold-process totals execute prebuilt binaries; their build times are separate. Memory uses getrusage(RUSAGE_SELF) at guest completion; JIT host RSS excludes compiler/assembler child-process peaks. These metrics are not combined into a single memory claim.

19 workloads passed, 799 timed executions plus 95 warm-ups. Adaptive tier transitions occurred in 14 workloads.

Across all workloads, execution-only geometric means: adaptive JIT speedup over JIT baseline 1.129×; adaptive JIT time relative to C 2.513×; adaptive JIT time relative to fresh AOT -O2 1.894×; JIT starting -O2 time relative to C 1.348×.

| Workload | C execution ms | AOT -O2 execution ms | JIT baseline execution ms | Adaptive execution ms | JIT starts -O2 execution ms | Adaptive compile pause ms | Adaptive startup ms | Adaptive total ms | Hot functions | Checksums |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| fib | 618.57 | 551.87 | 992.20 | 639.19 | 653.33 | 333.44 | 4036.95 | 5051.11 | 1 | ok |
| matmul | 437.87 | 366.74 | 368.10 | 368.56 | 367.35 | 0.00 | 4045.17 | 4458.68 | 0 | ok |
| mandel | 293.50 | 554.86 | 473.79 | 471.72 | 551.64 | 0.00 | 4028.39 | 4549.77 | 0 | ok |
| sort | 375.18 | 163.19 | 209.56 | 208.72 | 162.91 | 0.00 | 4101.57 | 4354.01 | 0 | ok |
| strings | 232.42 | 174.56 | 279.60 | 282.03 | 173.64 | 0.00 | 4023.54 | 4348.48 | 0 | ok |
| hashmap | 300.88 | 556.08 | 809.94 | 821.62 | 544.28 | 0.00 | 4103.14 | 4906.65 | 0 | ok |
| cube | 205.37 | 289.03 | 298.41 | 293.73 | 287.93 | 323.73 | 4129.18 | 4797.51 | 1 | ok |
| pi | 306.38 | 243.73 | 403.22 | 402.59 | 243.57 | 321.22 | 4086.73 | 4861.49 | 1 | ok |
| liquid | 406.95 | 543.43 | 723.88 | 618.19 | 544.48 | 334.16 | 4088.36 | 5086.06 | 1 | ok |
| shapes | 165.97 | 301.16 | 656.64 | 615.91 | 303.15 | 5824.26 | 4143.15 | 10618.95 | 18 | ok |
| closures | 277.28 | 337.60 | 665.46 | 643.57 | 335.65 | 1934.83 | 4178.44 | 6835.58 | 6 | ok |
| wordfreq | 205.54 | 335.40 | 1467.79 | 1405.91 | 336.84 | 638.96 | 4088.10 | 6207.04 | 2 | ok |
| nbody | 238.07 | 303.15 | 1010.54 | 1014.03 | 303.94 | 324.62 | 4070.60 | 5454.53 | 1 | ok |
| lexer | 188.27 | 517.17 | 1062.20 | 931.47 | 512.75 | 1282.43 | 4029.03 | 6301.03 | 4 | ok |
| vectors | 182.58 | 422.51 | 22469.53 | 15247.87 | 423.31 | 1585.67 | 4031.79 | 20862.61 | 5 | ok |
| dispatch | 144.00 | 203.52 | 349.78 | 346.80 | 237.40 | 5622.95 | 4364.91 | 10414.18 | 17 | ok |
| records | 404.09 | 523.88 | 1350.98 | 1339.82 | 520.48 | 330.81 | 4223.22 | 5925.20 | 1 | ok |
| strbuild | 301.34 | 443.79 | 1038.67 | 747.40 | 448.75 | 1320.09 | 4171.73 | 6310.37 | 4 | ok |
| bintrees | 182.05 | 390.21 | 986.02 | 483.72 | 393.76 | 807.79 | 4346.63 | 5699.49 | 2 | ok |

Status: complete. Raw samples, build times, memory, source hashes, and promoted-function names are in the JSON.
