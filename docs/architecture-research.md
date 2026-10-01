# Compiler architecture research

Working document for `GOAL.md`. Every number is marked **[M]** (measured, with
the tool used) or **[E]** (estimated, with the reasoning). Tools live in `research/`.

## Current best architecture

*(Revised every cycle. Cycle 2 state.)*

**In one paragraph:** semantics are defined once, by an interpreter for a flat,
typed IR. That interpreter is the executable specification. It serves as the
correctness oracle for compiled code and as the compile-time evaluator. Code
that runs is native: one optimizing compiler over the same IR, made cheap by
caching every compiled function under a hash of its content. There is no
interpreter tier and no JIT tier, because with caching neither wins any
measured scenario by more than tens of milliseconds, and then only on an empty
cache (see the cycle 2 candidate evaluation). Copy-and-patch, with stencils
generated from the interpreter's handlers, is kept in reserve. It is adopted
only if the rewritten optimizer costs more than ~2 µs per SSA value.

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
4. **The optimizer as the only code generator.**
   - Today -O2 costs ~7.3 µs per SSA value on top of baseline [M: (7.67 s − 3.14 s) / 622,155 values in `--opt-report`].
     That is in the range commonly reported for LLVM -O2, with much less
     optimization.
   - A flat-array pipeline written in Zephyr runs at 0.23–0.27 µs per value [M4b]
     (CFG, fold/copy-propagation/GVN, DCE, bitset liveness, linear scan, x86
     encoding). A production pipeline does more: inlining, loop optimizations,
     RC elimination, bounds-check elimination. Allowing 3–5× more work gives
     0.7–1.4 µs per value [E].
   - Whole-zc optimization would then take 0.4–0.9 s cold, and edits are cached
     at function granularity.
   - The copy-and-patch gate (2 µs) is very likely met, so C3 stays in reserve.
5. **Priorities by measured payoff (cycle 4, M6/M7):**
   1. **Backend quality** decides 11 of 19 workloads: calling convention,
      register allocation over all GPRs and XMMs, vectorization with SoA.
   2. **Runtime library co-designed with the optimizer** decides 5: signed
      magic division, small strings, hashes stored in map slots.
   3. **Regions plus immutable-type flattening:** fewer workloads, but the
      largest single gain (bintrees 3.00× → 0.29× C).
6. **An IR interpreter as the executable specification**, not as a tier. It is
   used for differential testing of every optimization, compile-time
   evaluation, and debugging. That is the role in which an interpreter is
   worth having for Zephyr.

## Scoreboard

| Target | Goal | Today, x86-64 Linux | Source |
|---|---|---|---|
| Small-program cold build (`fib.zeph`) | < 100 ms | 280 ms baseline, 530 ms -O2 | [M] `/usr/bin/time`, Xeon 2.1 GHz |
| Empty program cold build | < 100 ms | 260 ms (runtime only) | [M] |
| Self-compile (`zc.zeph`, 19k lines + runtime) | — | 3.14 s baseline, 7.67 s -O2; 256 MB / 471 MB peak RSS | [M] |
| Incremental rebuild | < 20 ms | same as a cold build (no caching) | [M] |
| Single-core geometric mean, -O2 vs gcc -O2 | ≤ 1.0–1.1× | **1.253×** over 19 workloads | [M] `research/x86bench.py` |
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
| vectors | 447 | 29628 | 755 | 1.69 |
| dispatch | 323 | 627 | 473 | 1.47 |
| records | 1024 | 2317 | 1326 | 1.29 |
| strbuild | 462 | 1477 | 1011 | 2.19 |
| bintrees | 259 | 1305 | 775 | 3.00 |
| **geometric mean** | | | | **1.253** |

The worst x86 gaps are allocation and string workloads: bintrees 3.00,
strbuild 2.19, lexer 2.19, wordfreq 1.95, shapes 1.69, vectors 1.69. Baseline
vectors is 66× C, because every `Vec3` temporary is a heap object.

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

### M4. Interpreter speed for a Zephyr-like IR (cycle 2)

`research/proto/interp.c` is a best-case interpreter design for a statically
typed language:

- typed register IR over 64-bit frame slots;
- no tags and no type checks;
- bounds checks kept, as Zephyr requires;
- direct threading with computed goto.

Results, compared with the same algorithm compiled natively, on one pinned
core [M]:

| Kernel | gcc -O2 native | Interpreter (gcc) | Slowdown | Slowdown (clang build) |
|---|---:|---:|---:|---:|
| fib(32), call-heavy | 3.8 ms | 60 ms | 15.6× | 9.0× |
| Bounds-checked sum, 50 M elements | 17.7 ms | 297 ms | 16.8× | 16.1× |
| mandel 600², float | 17.7 ms | 96 ms | 5.4× | 5.5× |

Zephyr's current baseline compiler is 2.3× C on fib and 1.3× C on mandel
(table M2). **An interpreter tier would therefore run 4–7× slower than code zc
already emits without optimization.** Better interpreter tricks
(superinstructions, keeping the top of stack in a register, static register
caching) typically recover 1.5–2× [E, from published interpreter work]. That
still leaves an interpreter 2–5× behind Zephyr's baseline.

### M5. -O2 coverage and cost (cycle 2)

`--opt-report` on `compiler/zc.zeph` [M]:

- **Coverage:** 945 functions optimized and 107 left on baseline.
- **Bail-out reasons for the 107:**
  - 98 are `call kind 36`. These are the raw OS calls in the OS layer.
  - 4 are `call kind 21`, 2 are `call kind 35`.
  - The rest are one each: a region too large (40,608 values), a string
    operator, and an unpinned reference live across a call.
- **Size and spills:** 622,155 SSA values in 1,171 regions, with 6,075 spills.

Combined with the timings in M3, that is about 7.3 µs per value of extra -O2
cost.

### M4b. Flat-array optimizing pipeline: C vs Zephyr (cycle 3)

`research/proto/flatopt.c` and `research/proto/flatopt.zeph` implement the same
pipeline over preallocated int arrays, run on synthetic functions shaped like
zc's regions:

- loops and branches;
- block parameters instead of phis;
- calls, loads and stores;
- about 23% of values foldable or dead.

The pipeline:

1. CFG and reverse post-order;
2. constant folding, copy propagation and hash-based GVN;
3. DCE with a worklist;
4. iterative bitset liveness;
5. live intervals and linear scan over 14 GPRs;
6. real x86-64 encodings into a byte buffer.

Nothing is allocated per value. Results, one pinned core, ns per SSA value [M]:

| Function size | C (gcc -O2) | Zephyr (zc -O2) | Zephyr / C |
|---|---:|---:|---:|
| ~100 values | 149 | 767 | 5.1× |
| ~500 values | 113 | 270 | 2.4× |
| ~2000 values | 144 | 233 | 1.6× |

**Per-phase breakdown, Zephyr at ~500 values:**

| Phase | ns per value |
|---|---:|
| CFG | 12 |
| fold/GVN | 102 |
| DCE | 27 |
| liveness | 26 |
| linear scan | 69 |
| encode | 32 |

The ~100-value case is dominated by fixed per-function costs: clearing a
65,536-entry hash table every call, which generation counters would remove.
zc's real regions average ~530 values (622,155 values / 1,171 regions, M5), so
the ~500 row is the representative one.

**What this means:**

- Zephyr's own int-array code is good enough to host a fast compiler: within
  1.6–2.4× of C on the same algorithm.
- The current optimizer's 7.3 µs per value is not inherent to the language or
  the problem. It comes from heap-object IR, list growth and reference counting
  (M3).

### M6. Where -O2 time goes in each workload (cycle 4)

`research/profile_all.py` profiles each workload with the sampler and groups
self time by function category [M].

| Dominant cost | Workloads (-O2 / C on x86) | Lever |
|---|---|---|
| User code, ≥ 90% | fib 1.46, mandel 0.98, cube 1.15, pi 0.58, liquid 1.20, shapes 1.69, closures 1.10, nbody 1.23, vectors 1.69, dispatch 1.47, records 1.29 | Backend quality: calling convention, register allocation, vectorization, dispatch |
| Runtime library, 60–91% | strings 1.49, hashmap 0.71, wordfreq 1.95, strbuild 2.19, sort 0.53 | Runtime data structures and their codegen |
| Allocation + reference counting | bintrees 3.00 (60%), lexer 2.19 (25%) | Regions, flattening, borrow inference |

**Correction:** the conversation that produced `GOAL.md` claimed the memory
model was the biggest lever. On x86, that is true only for 2 of the 19
workloads. Backend quality decides 11 of them, and the runtime library 5.

Two labelling notes:

- Optimized whole functions keep their `lm_` names; `zopt_regionN` names are
  outlined loops. Both are user code.
- matmul's time sits in the guarded native kernel, which falls outside the
  categories.

### M7. Oracle rewrites: hand-applied transformations (cycle 4)

Each oracle is the program the proposed optimization would produce, written by
hand and timed. This bounds the gain without building the optimization.

| Workload | Transformation | -O2 today | Oracle | C | Oracle / C |
|---|---|---:|---:|---:|---:|
| bintrees | Region per statement + Node flattened into int arrays (`research/oracle/bintrees_region.zeph`) | 0.80 s, 19 MB | **0.075 s, 5 MB** | 0.259 s | **0.29** |
| vectors | `Vec3` as values in SoA arrays (`vectors_values.zeph`) | 0.81 s | 0.82 s (no change) | 0.45 s | 1.82 |
| vectors | The same SoA loop in C at -O2 / -O3 -mavx2 (`vectors_soa.c`): the vectorization bound | | 0.29 s / 0.18 s | 0.45 s | 0.64 / 0.40 |
| strings | Integer formatter on positive values, so /10 uses the multiply path (scratch runtime copy) | 0.55 s | **0.44 s** | 0.36 s | 1.22 |

**What the oracles show:**

1. **Regions plus flattening are worth 11× on tree workloads** and beat
   malloc/free C by 3.4×. A tree that dies at the end of its statement is the
   common pattern: build, consume, drop. Arena allocation is a bump; freeing it
   is one reset.
2. **-O2 already scalar-replaces small structs without reference fields** in
   vectors. The remaining 1.8× gap is that gcc pairs x/y arithmetic into SSE2
   (`mulpd`, `divpd`) and zc doesn't vectorize. SoA plus 4-wide AVX2 would put
   Zephyr at 0.40× C.
   - The inner loop also spills XMM values to the stack while XMM registers are
     free, and saves all ten callee-saved XMM registers, as the Win64 ABI
     requires. The allocator doesn't use the full register file well.
3. **A small runtime fix moved strings 20%.** The optimizer's fast
   divide-by-constant handles only non-negative values. The runtime's integer
   formatter deliberately works on negative values (to survive i64 MIN), so
   every digit took two slow `idiv`s.
   - Lesson for the architecture: the runtime library has to be co-designed with
     the optimizer. Signed magic-number division would fix the whole class.
4. **wordfreq (map runtime 63%):**
   - The C version builds words in a stack buffer and keeps each key's hash in
     its table slot.
   - Zephyr allocates every concatenated word, and every probe follows the key
     pointer to compare.
   - Small-string optimization (short strings stored inline in the 64-bit word)
     and hashes stored in slots are the expected fix [E].

**Benchmark validity issue found:** at its benchmark size (35,000 steps), every
particle in vectors converges onto the anchor. The checksum is then the
constant −1,500,000,000 (total = −1500 exactly) for any implementation that
converges, so it barely checks correctness. It should be checked at a smaller
step count, such as 100 steps, where it is 202,045,867.

## Candidates evaluated

### Cycle 2: execution and tiering architecture

**Inputs to the simulation:**

- interpreter 5–16× native [M4];
- current zc baseline ≈ 1.3–2.3× native [M2];
- copy-and-patch emission ≈ 10–30 ns per IR op [E: a memcpy of one stencil plus 1–3 patched holes, as reported for copy-and-patch, Xu & Kjolstad 2021];
- rewritten optimizer 0.5–1 µs per value [E, Q1];
- frontend for the whole of zc ≈ 0.3 s today [M3: parse, check and inline shares of 3.14 s];
- the runtime is ~10% of zc's values [E, from relative source size].

**Scenarios played out** (times are estimates built on the inputs above):

| Scenario | C1: cached AOT, one optimizing tier | C2: interpreter first, then optimizing JIT | C3: copy-and-patch baseline + optimizing tier, cached | C4: partial evaluation of an interpreter (Truffle style) | C5: meta-tracing (PyPy style) |
|---|---|---|---|---|---|
| S1 `zc run fib.zeph`, runtime cached | ~5 ms to the first instruction, then full speed | ~3 ms to start; the hot path interprets 15× slower until compiled; needs OSR for `main` loops | ~4 ms, then baseline speed until tier-up | Warm-up while the partial evaluator specializes; a large engine to ship | Warm-up until traces form; recursion like fib is a known weak spot for tracing |
| S2 same, empty cache (first ever) | + 30–60 ms to optimize the runtime once | no extra cost | + ~2 ms | n/a | n/a |
| S3 first build of zc itself (622k values) | 0.3–0.6 s of optimizing + 0.3 s frontend | 0 s of codegen, but the compiler then runs 5–16× slower until it warms up, which for a short compile never happens | ~20 ms + 0.3 s frontend; runs at baseline speed | Same warm-up problem as C2 | Same |
| S4 edit one function, rebuild | ms, dominated by frontend re-check | same | same | same | same |
| S5 long-running simulation | Peak from the first instruction; profiles persist for the next build | Peak after warm-up; profiling overhead stays | Peak after tier-up | Peak after warm-up; best at speculation, which a static closed-world language barely needs | Peak only on loop-shaped code |
| S6 compile-time evaluation, REPL, debugger | Needs an evaluator anyway | Natural | Natural if stencils come from interpreter handlers | Natural | Natural |
| Engineering cost | One code generator | Interpreter + JIT + OSR + deopt | Stencil generator + optimizing tier | A partial evaluator is itself a large optimizing compiler | Tracing JIT + interpreter |

**Verdicts:**

- **C1 wins S1, S4 and S5, and every scenario where the cache is warm.**
- **C2 and C5 lose outright.** Speculation and deopt are what make interpreter
  tiers pay off in dynamic languages. A statically typed, monomorphized,
  closed-world language has almost nothing to speculate on, so the tiers cost
  warm-up and bring little back.
- **C4 loses for the same reason.** Truffle's strength is collapsing dynamic
  dispatch through speculation. Here the partial evaluator would be an extra
  optimizing compiler that buys nothing the lowering doesn't already know.
- **C3's only win is S2/S3, an empty cache:** tens to a few hundred
  milliseconds, once per compiler version.
- **The interpreted-compiler idea survives in a different role (C6):** an IR
  interpreter as the executable specification.
  - It acts as an oracle: every optimized function is tested for identical
    behaviour against it.
  - It evaluates code at compile time and backs the debugger.
  - It removes the "two implementations disagree" class of bugs. Today,
    baseline/-O2/JIT parity is maintained by hand.
- **Deciding evidence:** M4 (interpreters are 5–16× native) and the fact that
  caching removes the latency an interpreter tier exists to hide (M3: 93% of a
  small build is the runtime).
- **What would overturn this:** the rewritten optimizer missing ~2 µs per value
  (then C3 becomes worthwhile for S3), or a use case where code must run without
  any cache or code generation, such as a read-only sandbox.

| Candidate | Verdict | Deciding evidence |
|---|---|---|
| C1 cached AOT, one optimizing tier | **Adopted** as the execution model | S1, S4, S5 above; M3 |
| C2 interpreter first, then JIT | Rejected as a tier | M4: 5–16× native, 4–7× worse than current baseline; nothing to speculate on |
| C3 copy-and-patch from interpreter handlers | **In reserve**, gated on Q1 | Wins only on an empty cache |
| C4 partial evaluation of an interpreter | Rejected | Its strength is speculation; an extra compiler for no gain |
| C5 meta-tracing | Rejected | Recursion and branchy code trace poorly; same warm-up problem as C2 |
| C6 IR interpreter as executable spec and oracle | **Adopted** in that role | Removes the parity-bug class; required for compile-time evaluation anyway |

## Open questions

- **Q1. Answered in cycle 3.** A flat pipeline costs 0.23–0.27 µs per value in
  Zephyr [M4b]; a production one is estimated at 0.7–1.4 µs [E]. That is
  ~0.4 ms for an average 530-value region.
- **Q2. Answered in cycle 2.** 5–16× slower than native [M4].
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
- **2026-10-01, cycle 2.**
  - Completed the x86 table: geometric mean 1.253× gcc.
  - Built an interpreter prototype (M4): 5–16× native.
  - Measured -O2 coverage and per-value cost (M5).
  - Simulated six scenarios across five tiering architectures.
  - Verdict: cached AOT with one optimizing tier for execution; the interpreter
    as executable specification.
  - Next: Q1, whether a flat-array optimizer in Zephyr can reach about 1 µs per
    value. That is the claim everything above now rests on.
  - Note on AGENTS.md: Wine is used only once, to produce a Linux-native zc.
    Every measurement runs native Linux code, not emulation.
- **2026-10-01, cycle 3.**
  - Q1: built the same flat optimizing pipeline in C and in Zephyr.
  - Zephyr runs at 0.23–0.27 µs per value, 1.6–2.4× the C version and ~30×
    cheaper than today's -O2.
  - This confirms cached AOT with one optimizing tier; C3 stays in reserve.
  - Next weakest claim: the runtime gains promised by semantic optimizations
    (value types, borrow inference, regions), which are still pure estimates.
  - Plan: measure their upper bound by hand-applying each transformation to the
    worst workloads.
- **2026-10-01, cycle 4.**
  - Oracle rewrites (M7):
    - bintrees with a region plus flattening: 0.29× C;
    - vectors: allocation is already gone, the remaining gap is vectorization
      (SoA + AVX2 bound 0.40× C);
    - strings: formatter fix 1.49× → 1.22× C.
  - Per-workload cost breakdown (M6) reordered the priorities: backend first,
    runtime library second, memory model third.
  - Found that the vectors checksum is degenerate at its benchmark size.
