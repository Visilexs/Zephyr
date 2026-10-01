# Native Mac benchmark

Run from the repository root on Apple Silicon:

```sh
python3 tests/benchmarks/macos.py
```

The runner recovers the 19 original benchmark workloads and C/Rust comparison
sources from Git revision `398aadd` into temporary storage. It uses the original
workload sizes, one warm-up, and up to ten interleaved timed runs for each build.
As in the original harness, slow builds stop after spending 30 seconds on timed
runs, with at least three samples. Each process has a 300-second timeout.

Zephyr baseline and `-O2` builds use the root native `zc` driver's explicit output
path, so these measurements are AOT. C uses Apple
Clang `-O2`, signed wraparound, and disabled floating-point contraction. Rust
comparisons are included when `rustc` is installed. Every executable must be
ARM64 Mach-O, and checksums must match before timing ratios are considered valid.
Every timed run checks its output against the warm-up result as well.

macOS scheduling is normal and CPU affinity is not fixed. The memory metric is
peak resident memory of one workload process; it differs from the original
Windows runner's peak committed memory. Native process timing and memory
counters must be accessible to the process running this script.

JSON results contain checksums, raw timings, medians, median absolute deviation,
peak resident memory, build times, failures, compiler seed hash, and host/toolchain
details. A Markdown table accompanies each result file. Both files checkpoint
throughout the run. Default outputs are under `tests/benchmarks/results/`;
`--output path.json` chooses a fixed location. Windows results are not directly
comparable to these native ARM64 measurements.

Saved measurements:

- [Full 19-workload run](results/apple-silicon-full.md), before the native matrix kernel.
- [Matrix kernel before/after comparison](results/matmul-arm64-improvement.md),
  with the previous compiler, updated baseline/optimized builds, and C.
- [ARM64 code generation before/after comparison](results/arm64-easy-optimizations.md),
  covering all 19 workloads after adding the matrix kernel.
