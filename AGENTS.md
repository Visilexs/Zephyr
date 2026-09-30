# Agent instructions

Read `CLAUDE.md` first. It holds this repo's project rules, layout and build steps, and they apply to every agent. This file only adds what changed since then.

## Benchmarks (changed 2026-09-30, commit 3304401)

`bench/run_suite.ps1` and `bench/time1.ps1` are gone. Use `bench/bench.py` for all benchmarking, from the repo root:

```
python bench/bench.py run --compiler zc_new.exe       # full suite; saves bench/results/<commit>-<time>.json
python bench/bench.py run --only vectors,lexer --languages c,zephyrO2 --compiler zc_new.exe
python bench/bench.py compare                         # two newest results (or: compare OLD.json NEW.json)
python bench/bench.py ab dirA/zc.exe dirB/zc.exe      # two compiler builds head to head
python bench/bench.py compile --compiler zc_new.exe   # compile-time scaling + zc self-compile
```

- **run:**
  - builds each workload in Zephyr, Zephyr -O2, C (gcc -O2) and Rust (rustc -O);
  - checks that all builds print the same checksum;
  - does one warm-up and then 10 timed runs, pinned to one CPU at high priority;
  - reports the median ± the median absolute deviation, and peak committed memory of the whole process tree.
  - Exit code 1 means a checksum mismatch. Treat that as a miscompile, not noise.
- **Comparing numbers:**
  - Don't compare against figures from the old runner. Workloads were resized to run at least ~250 ms each, so the old millisecond figures don't carry over.
  - Use `compare` or `ab` to judge a change. Only rows marked `*` are beyond the noise band. Run-to-run spread is under 1%.
- **ab:**
  - zc reads `compiler/runtime.zeph` and `lib/` from next to its own exe. Each compiler must sit in its own directory with its own runtime.
  - If both compilers share a directory, both builds use the same runtime.
- **compile:**
  - generates 200×200 call chains through `bench/compilegen.py`, for Zephyr, C, C++, Rust, Java and C#;
  - reports µs per function.
  - It is deliberately not pinned to one CPU, because pinning makes the multi-threaded compilers (javac, rustc, csc) look far slower. Keep it unpinned.
- **Toolchains:** gcc is at `C:\msys64\ucrt64\bin` and is found automatically. rustc, java and dotnet are on PATH.
- **Adding a workload:**
  - Write the same algorithm as `bench/<name>.zeph`, `.c` and `.rs`.
  - Read the size from argv[1] with a default, and use the shared LCG `nextRandom`.
  - Print exactly one checksum line.
  - Add a row to `suite` in `bench/bench.py`.
- **JIT-targeted workloads:**

  | workload | what it targets |
  |---|---|
  | `dispatch` | 8-way interface dispatch, past the optimizer's 4-vtable guard |
  | `records` | a list of boxed structs |
  | `strbuild` | per-substring allocation |
  | `bintrees` | allocation and recursion |

- Current measurements are in `docs/jit.md` under "Measurements".
