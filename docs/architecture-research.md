# Compiler architecture research

Working document for `GOAL.md`. Every number is marked **[M]** (measured, with
the tool used) or **[E]** (estimated, with the reasoning). Tools live in `research/`.

## Current best architecture

*(Revised every cycle. Cycle 1 state, built on the measurements below.)*

1. **Content-addressed caching** of the compiled runtime and std first, then of
   every function. On x86, 0.26 s of the 0.28 s build of `fib.zeph` is the
   runtime [M], so this one step takes small-program builds from ~280 ms to an
   estimated 10–30 ms [E].
2. **Direct machine-code emission.** The text assembler (`assembleLine`) is 28%
   of a baseline self-compile [M], and emitting the text adds string-building
   costs on top.
3. **A compiler whose data does not touch the reference-counted heap on hot
   paths.** About 43% of baseline self-compile time is retain/release,
   allocation and GC [M]. In -O2 builds, `runtimeListPush` alone is 12% [M].
   This argues for flat IR in preallocated `[int]` arrays rather than structs
   and growable lists of objects.
4. **The optimizer as the only code generator, if it can be made fast enough.**
   Today -O2 costs ~4.6 ms per function more than baseline [M/E: (7.67 s − 3.14 s) / ~990 functions].
   Whether a separate fast tier is needed depends on how far items 2–3 cut that.
   See open question Q1.

The interpreted-compiler candidates are under evaluation in cycle 2.

## Scoreboard

| Target | Goal | Today, x86-64 Linux | Source |
|---|---|---|---|
| Small-program cold build (`fib.zeph`) | < 100 ms | 280 ms baseline, 530 ms -O2 | [M] `/usr/bin/time`, Xeon 2.1 GHz |
| Empty program cold build | < 100 ms | 260 ms (runtime only) | [M] |
| Self-compile (`zc.zeph`, 19k lines + runtime) | — | 3.14 s baseline, 7.67 s -O2; 256 MB / 471 MB peak RSS | [M] |
| Incremental rebuild | < 20 ms | same as a cold build (no caching) | [M] |
| Single-core geometric mean, -O2 vs gcc -O2 | ≤ 1.0–1.1× | see the table below | [M] `research/x86bench.py` |
| Bit-identical output across modes | required | checksums match on every workload so far | [M] |

## Measurements

### M1. Running zc on Linux (cycle 1)

`research/setup.sh` runs `zc.exe` under Wine 9 to compile `compiler/zc.zeph`
with `--linux`. The result is a native static ELF compiler. All later
measurements use it, so no Windows machine is needed.

Machine: Intel Xeon @ 2.1 GHz, 4 vCPUs, no SMT, Linux 6.18 VM; gcc 13.3.

### M2. x86-64 workloads vs C (cycle 1)

These are the original sizes, gcc `-O2 -fwrapv`, pinned to one CPU, median of
up to 5 runs, from `research/x86bench.py`. All checksums match.

| Workload | C ms | Zephyr ms | -O2 ms | -O2 / C |
|---|---:|---:|---:|---:|
| fib | 809 | 1825 | 1186 | 1.46 |
| matmul | 1003 | 594 | 553 | 0.55 |
| mandel | 546 | 707 | 538 | 0.98 |
| sort | 480 | 378 | 255 | 0.53 |
| strings | 346 | 566 | 516 | 1.49 |
| hashmap | 1157 | 1064 | 820 | 0.71 |
| cube | 368 | 475 | 425 | 1.15 |
| pi | 723 | 421 | 418 | 0.58 |
| liquid | 907 | 1239 | 1088 | 1.20 |
| shapes | 655 | 1318 | 1107 | 1.69 |
| closures | 647 | 1060 | 713 | 1.10 |
| wordfreq | 568 | 2173 | 1106 | 1.95 |
| nbody | 426 | 1465 | 524 | 1.23 |
| lexer | 553 | 2050 | 1209 | 2.19 |
| *(remaining rows are filled in when the run finishes)* | | | | |

x86 looks very different from the M5:

- matmul, hashmap and pi already beat C on x86, but mandel is at parity.
- fib is 1.46× on x86 versus 0.89× on ARM64.

The ARM64 results go through `arm64.py` and clang, so the two backends are not
the same code. The x86 backend is the native one.

### M3. Where compile time goes (cycle 1)

`research/sampler.c` is a ptrace sampling profiler that walks the RBP frame
chain. Valgrind cannot be used: zc's conservative GC stack scan faults under
it. Symbols come from a research build of zc that writes `--map` for ELF too
(a one-line change, applied only to a temporary copy). Sampling interval:
200–500 µs.

**`fib.zeph`, baseline, 5 × ~1,000 samples** [M]:

| Area | Share |
|---|---|
| Code generation to text (`generateProgram`) | 48.5% inclusive |
| AST inlining (`inlinePass`) | 27.7% |
| ↳ cloning nodes (`cloneInlineNode`) | 19.6% |
| Text assembler (`assembleLine`) | 13.1% |
| Lexing and parsing | 9.6% |
| Self time in allocate / retain / release / free-slots / GC / assign | ≈ 51% |
| ↳ GC alone | 9.6% |

**`zc.zeph` self-compile, baseline, 4,703 samples** [M]:

| Area | Share |
|---|---|
| Code generation (`generateProgram`) | 60.1% inclusive |
| Text assembler (`assembleLine`) | 27.9% |
| Inlining | 16.4% |
| Typechecking | 4.9% |
| Parsing | 4.5% |
| Self time in reference counting, allocation and GC | ≈ 43% |
| String building (concatenation, interpolation, integer formatting, repeat, join) | ≈ 12% self |

**`zc.zeph` self-compile, -O2, 13,152 samples** [M]:

| Area | Share |
|---|---|
| Optimizer (`tryOptimizeFunction`) | 69.9% inclusive |
| ↳ region compile | 46.7% |
| ↳ AST → SSA lowering | 22.8% |
| ↳ register allocation + liveness + live ranges | ≈ 16% |
| `runtimeListPush` | 11.9% self |
| `runtimeRetainReference` | 11.5% self |
| `runtimeNewDescribedList` | 5.3% self |

**What this means:**

- The compiler is bound by the memory model it is written in, not by algorithms.
  Everything allocation-shaped is the bottleneck.
- The text round-trip (emit text, then parse it back in `assembleLine` and
  `parseOperand`) is a large, entirely avoidable cost.

## Candidates evaluated

| Candidate | Verdict | Evidence |
|---|---|---|
| *(cycle 2: interpreter-first tiering, partial evaluation of an interpreter, copy-and-patch from interpreter handlers, meta-tracing, cached AOT)* | pending | |

## Open questions

- **Q1.** With caching, direct emission and a flat IR, what does -O2 cost per
  function? If it is under ~0.5 ms, a baseline tier buys nothing in any
  scenario except the first-ever build of a large program.
- **Q2.** How fast can an interpreter for Zephyr's IR be, relative to native
  code? This sets where interpreted tiers could ever win.
- **Q3.** What does copy-and-patch emission cost per IR op, and how fast is its
  code compared with today's baseline and -O2?

## Assumptions (made instead of asking)

- **A1.** "Interpreted compiler" means any architecture where an interpreter is
  the semantic source of truth or the first execution tier, with compiled code
  derived from it. It includes partial evaluation, meta-tracing, interpreter
  stencils (copy-and-patch) and self-optimizing interpreters.
- **A2.** x86-64 Linux numbers from this VM stand in for x86-64 Windows. Both use
  the same zc backend and differ only in the OS layer. They may differ in
  syscall-heavy workloads.
- **A3.** The workloads in `bench/` at revision `398aadd` are used, because they
  are the versions the C sources match.

## Log

- **2026-10-01, cycle 1.**
  - Built a Linux-native zc through Wine.
  - Measured all workloads on x86 against gcc.
  - Profiled the compiler.
  - Main findings: build time is dominated by the runtime, the memory model's
    overhead inside the compiler, and the text-assembly round trip.
  - Corrected a callgrind artifact: an unsymbolized profile blamed
    `runtimeStringReplace` for 73% of instructions. The run had actually crashed
    partway through, and those replaces take 8 ms [M].
