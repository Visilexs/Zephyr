# Native Apple Silicon benchmark

Run: 2026-09-30T22:33:58.264874+00:00. Machine: Apple M5. macOS 27.0.

All 19 workloads passed with matching checksums over 559 timed executions and one warm-up per build. Optimized Zephyr was 2.21× faster than its baseline; C was 2.32× faster than optimized Zephyr. These comparisons use geometric means across workloads.

All 19 upstream workloads use their original arguments. One warm-up and up to 10 interleaved timed runs per build; the original 30-second accumulated timing budget allows a minimum of three samples for slow builds.

C uses Apple Clang -O2, defined signed wraparound, and disabled floating-point contraction. Zephyr uses the native ARM64 driver. Rust is included when installed. Processes use normal scheduling, without fixed CPU affinity. Memory is peak resident memory of each workload process.

Compile times include the complete build, including the native driver, instruction selection, assembly, and linking. Runtime times include process startup. Timings are valid only where every checksum agrees.

| Workload | Zephyr ms | -O2 ms | C ms | Rust ms | -O2/C | -O2 RSS MB | Samples Z/Z-O2/C/R | Checksums |
|---|---:|---:|---:|---:|---:|---:|---|---|
| fib | 1651.7 | 1092.3 | 622.1 | — | 1.76 | 1.9 | 10/10/10/— | ok |
| matmul | 4251.3 | 4235.3 | 443.9 | — | 9.54 | 30.3 | 8/8/10/— | ok |
| mandel | 485.4 | 580.6 | 310.2 | — | 1.87 | 1.9 | 10/10/10/— | ok |
| sort | 369.3 | 212.9 | 384.9 | — | 0.55 | 47.7 | 10/10/10/— | ok |
| strings | 534.9 | 297.5 | 239.3 | — | 1.24 | 1.9 | 10/10/10/— | ok |
| hashmap | 1181.3 | 788.8 | 262.4 | — | 3.01 | 51.2 | 10/10/10/— | ok |
| cube | 1352.6 | 955.4 | 208.3 | — | 4.59 | 2.0 | 10/10/10/— | ok |
| pi | 535.0 | 312.5 | 313.5 | — | 1.00 | 2.1 | 10/10/10/— | ok |
| liquid | 1046.9 | 810.3 | 406.8 | — | 1.99 | 2.8 | 10/10/10/— | ok |
| shapes | 996.5 | 453.8 | 169.3 | — | 2.68 | 209.1 | 10/10/10/— | ok |
| closures | 935.8 | 468.1 | 280.2 | — | 1.67 | 30.8 | 10/10/10/— | ok |
| wordfreq | 2344.2 | 582.5 | 214.3 | — | 2.72 | 18.7 | 10/10/10/— | ok |
| nbody | 1863.0 | 435.2 | 237.7 | — | 1.83 | 2.0 | 10/10/10/— | ok |
| lexer | 1657.3 | 773.4 | 193.6 | — | 3.99 | 271.2 | 10/10/10/— | ok |
| vectors | 41917.8 | 888.3 | 186.3 | — | 4.77 | 2.4 | 3/10/10/— | ok |
| dispatch | 476.5 | 282.0 | 151.0 | — | 1.87 | 91.7 | 10/10/10/— | ok |
| records | 2154.9 | 724.0 | 386.1 | — | 1.88 | 104.9 | 10/10/10/— | ok |
| strbuild | 1783.5 | 741.4 | 304.7 | — | 2.43 | 2.0 | 10/10/10/— | ok |
| bintrees | 1526.9 | 740.6 | 183.3 | — | 4.04 | 20.5 | 10/10/10/— | ok |

Status: complete. Rust: unavailable; rustc not installed.

Errors and raw samples are recorded in the accompanying JSON. Windows results use different compiler, instruction-set, scheduling, and memory measurements and should not be compared directly.
