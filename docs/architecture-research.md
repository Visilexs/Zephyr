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
   - The target is 0.5–1 µs per value [E]. Whole-zc optimization would then take
     0.3–0.6 s cold, and edits are cached at function granularity.
   - Whether this target can be hit is the least-verified claim here (Q1, the
     next cycle).
5. **An IR interpreter as the executable specification**, not as a tier. It is
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
