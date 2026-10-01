# Compiler architecture research

Working document for `GOAL.md`. Every number is marked **[M]** (measured, with
the tool used) or **[E]** (estimated, with the reasoning). Tools live in `research/`.

## Current best architecture

*(Revised every cycle. Cycle 7 state. Each claim cites a measurement.)*

**Summary:**

- An IR interpreter is the executable specification, not a tier.
- All code that runs is native, from a single optimizing compiler over one flat
  IR.
- Caching every compiled declaration under a hash of its content is what makes
  "always optimized" affordable.
- The runtime's speed comes mostly from representation: small object headers,
  values flattened into containers, regions, and runtime data structures
  designed together with the optimizer.
- Parallelism comes after that.

### The layers, in build order

1. **Cache layer.**
   - Content-addressed caching keyed per top-level declaration: a hash of its
     source plus the hashes of everything it depends on or inlines.
   - Change detection costs 7 ms on the 1 MB `zc.zeph` [M10].
   - The compiled runtime and std are cached first: they are 93% of a
     small-program build today [M3].
   - Projections: small-program cold build ~10–30 ms [E] (from 280 ms [M]);
     zc incremental rebuild ~10–15 ms [E].
2. **One flat IR.**
   - Typed SSA with block parameters, stored in preallocated `[int]` arrays.
   - The compiler's own hot data never touches the reference-counted heap.
     Today 43% of compile time is reference counting, allocation and GC [M3].
   - The flat pipeline runs at 0.23–0.27 µs per value in Zephyr [M4b], against
     7.3 µs for today's -O2 [M5].
3. **One optimizing native backend, emitting machine code directly.**
   - No text assembler, which is 28% of a self-compile today [M3].
   - Instruction selection, register allocation over all 16 GPRs and 16 XMMs.
     Hand allocation of one hot loop gave −27% (M20).
   - An internal calling convention: no frame pointer, no stack realignment,
     shrink-wrapped saves. Calls cost 1.47× C's today [M12]; a lean prologue
     alone is −15% on fib [M21].
   - It decides 11 of the 19 workloads [M6].
   - Missing passes, measured or identified:
     - accumulator recursion elimination (fib 1.46× → 0.96× C) [M9, M21];
     - signed magic-number division [M7];
     - SoA loop vectorization with alias versioning [M7], and straight-line
       vectorization of paired x/y/z arithmetic, which gcc uses in both vectors
       and nbody [M7, M18];
     - profile-guided inlining of hot loop bodies [M11].
   - Debug builds are this backend with passes off.
4. **Representation layer**, using closed-world, whole-program facts:
   - **Immutability inference:** never-mutated struct types become values,
     flattened into their containers (SoA). shapes: 1.83× → 1.40× [M11];
     vectors: bound 0.40× C with AVX2 [M7].
   - **Region inference** for structures that die at the end of a statement or
     call. bintrees: 3.00× → 0.29× C [M7].
   - **Allocation and release specialized per type** instead of the generic
     descriptor-driven runtime paths. Worth ≈ 2.7× on bintrees [M13].
   - **Nullable-pointer optionals** for reference types, no cells (−30% [M13]).
   - **8-byte object header** instead of 24 (−28% [M13]).
   - **Slices for substrings** and flattened token-like records. lexer: 2.22× →
     1.56× [M14].
   - **In-place append when the string is uniquely owned**, plus slices.
     strbuild: 2.2× → 1.45× [M23].
   - **Runtime data structures co-designed with the optimizer:** small strings,
     hashes stored in map slots, a formatter in the fast division domain.
     strings: 1.49× → 1.22× [M7].
5. **Automatic loop parallelism**, enabled by layer 4 (no reference-count
   traffic on SoA data).
   - 3.17× on 4 cores, bit-identical [M8].
   - Only for loops with ≥ 5–10 µs of work per invocation.
6. **The IR interpreter as the executable specification.**
   - A differential-testing oracle for every pass.
   - The compile-time evaluator and the debugger.
   - It is not an execution tier. Interpreters run 5–16× slower than native
     [M4], and with caching there is no latency left for a tier to hide [M10].
   - Runtime profiles, a JIT's other advantage, are worth ≤ 5–13% at best and
     −4% on average here [M25]. So profiles stay opt-in.
   - Copy-and-patch from the interpreter's handlers stays in reserve, in case
     the optimizer ever exceeds ~2 µs per value.

**Projected single-core geometric mean vs gcc -O2:**

| Basis | Geometric mean |
|---|---:|
| Today [M] | 1.253 |
| Measured oracle results only, other workloads unchanged | ≈ 1.02 |
| Including the estimated fixes listed above | ≈ 0.88 [E] |

Parallel workloads go well below 1.0 on multicore machines.

## Scoreboard

| Target | Goal | Today, x86-64 Linux | Source |
|---|---|---|---|
| Small-program cold build (`fib.zeph`) | < 100 ms | 280 ms baseline, 530 ms -O2 | [M] `/usr/bin/time`, Xeon 2.1 GHz |
| Empty program cold build | < 100 ms | 260 ms (runtime only) | [M] |
| Self-compile (`zc.zeph`, 19k lines + runtime) | — | 3.14 s baseline, 7.67 s -O2; 256 MB / 471 MB peak RSS | [M] |
| Incremental rebuild | < 20 ms | same as a cold build today; ~10–15 ms projected for zc with declaration-level caching | [M] today; [E] projection from M10 |
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

### M8. Automatic loop parallelism: overhead and gain (cycle 5)

`research/proto/forkjoin.c` runs the SoA vectors kernel with one fork-join per
time step, which is exactly what automatic parallelization of the inner loop
would produce. It uses a spinning pool with a generation counter. 4 vCPUs [M]:

| Threads | Empty parallel-for round trip | Kernel, 35,000 steps | Speedup |
|---:|---:|---:|---:|
| 1 | 0.02 µs | 604 ms | 1.00 |
| 2 | 0.16 µs | 314 ms | 1.92 |
| 3 | 0.44 µs | 230 ms | 2.63 |
| 4 | 0.67 µs | 191 ms | **3.17** |

Results are bit-identical to the serial run at 100 steps and at 35,000 steps.
Splitting by index doesn't change any element's arithmetic order.

**What this means:**

- A spinning pool's round trip is ~0.6 µs. A compiler should parallelize a loop
  only when its estimated work per invocation is ≥ 5–10 µs [E: 10× overhead],
  roughly 2,000 iterations of a vectors-sized body.
- A sleeping pool (futex wake ~5–50 µs [E]) raises that threshold 10–100×.
  So the runtime should spin briefly before sleeping.
- **The safety conditions a compiler must prove:**
  - each iteration writes only element `i` of lists it doesn't read at other
    indices;
  - no calls with effects;
  - lengths are constant in the loop, so bounds checks can be hoisted and the
    first panic stays deterministic;
  - no float reduction across iterations;
  - and the one Zephyr-specific condition: no reference-count traffic on shared
    objects.
- Value types and SoA (M7) are what make the last condition hold.
- Bound for vectors with SoA + AVX2 + 4 threads: ~0.06 s against C's 0.45 s
  (0.13× C) [E: 0.18 s / 3.17].

### M9. fib: not a calling-convention problem (cycle 5)

gcc -O2 turns one of fib's two recursive calls into a loop that accumulates the
result: `fib(n) = fib(n−1) + fib(n−2)` becomes a loop over the second call.
That's legal because integer `+` is associative under wraparound.

- gcc's `fib` contains 4 calls in total. zc self-inlines 4 levels and contains
  32 [M: `fibc.s` vs zc `-O2` output].
- The prologues are comparable: gcc pushes 6 registers, zc stores 6 and also
  realigns the stack.
- So the 1.46× gap comes from one missing pass, accumulator recursion
  elimination, not from the convention. It applies to every recursive function
  of the shape `f(x) = g(f(a), f(b))` with `g` associative.

### M10. Incremental rebuild: finding what changed (cycle 6)

`research/proto/declsplit.zeph` splits a source file into top-level
declarations and hashes each one. It handles strings with interpolation, raw and
triple-quoted strings, char literals, and nesting comments. It works without
lexing or parsing the whole file [M]:

| File | Size | Declarations | Split | Hash (FNV-1a) |
|---|---:|---:|---:|---:|
| `compiler/zc.zeph` | 1.05 MB | 992 (504 `fn`, matching `grep -c '^fn '`) | 5.3 ms (196 MB/s) | 1.5 ms (697 MB/s) |
| `compiler/optimizer.zeph` | 0.33 MB | 549 (309 `fn`) | 3.0 ms (111 MB/s) | 0.5 ms |

**An edit-one-function rebuild of zc, estimated:**

| Step | Cost |
|---|---|
| Split and hash, to find the changed declaration | ~7 ms [M] |
| Re-lex, parse and check that declaration | < 1 ms [E] |
| Optimize it (~530 values at ~1 µs each, M4b) | ~0.5 ms [E] |
| Re-link cached machine code (~5 MB) | ~2–5 ms [E] |
| **Total** | **~10–15 ms [E]** |

That meets the < 20 ms target, as long as the cache tracks dependencies:

- a changed signature re-checks its callers;
- a changed struct or global re-checks its users;
- every function that inlined the changed one is recompiled.

**What this means for the interpreted-compiler question:**

- An interpreter tier saves only code generation. It still needs the frontend.
- With declaration-level caching, the frontend work per edit is one declaration
  and code generation is under a millisecond.
- So the time an interpreter tier could save is tiny, which strengthens the C1
  verdict.

### M11. shapes: memory density, not dispatch (cycle 7)

Hypothesis tested: the `{vtable, data}` interface cell (spec §3.5) adds an
allocation and a dependent load per element, as instruction-level sampling
suggested (`research/hotspots.py`: the hottest instructions are the loads
through the cell). Results [M]:

| Version | Time | Peak RSS | vs C |
|---|---:|---:|---:|
| `bench/shapes.zeph`, -O2 | 1.06 s | 205 MB | 1.83 |
| Closed-world tagged struct, no interface cell (`research/oracle/shapes_tagged.zeph`) | 1.06 s | 198 MB | 1.83 |
| Shapes flattened into the list, SoA (`research/oracle/shapes_flat.zeph`) | 0.81 s | 168 MB | 1.40 |
| C, vtable pointers, malloc | 0.58 s | 93 MB | 1.00 |

**What this means:**

- **Removing the interface cell gains nothing.** The loads it adds overlap
  with the object loads.
- **The cost is bytes per element.** Every heap object has a 24-byte header
  (count, descriptor, size; `runtime.zeph` line 11), so a circle in a `[Shape]`
  is ~80 bytes against C's ~40. The traversal is sequential, so bandwidth
  decides the time.
- **Flattening values into the list recovers 24%.** What's left is call
  overhead: `area` and `perimeter` are ~1 KB each, too big for the inliner's
  60-node limit, so each element pays a full prologue.
- **Implications:**
  1. A smaller object header. Packing a 32-bit count and a 32-bit descriptor
     index into one word, with the size taken from the descriptor or size
     class, would save 16 bytes per object in every allocation-heavy workload [E].
  2. Flattening immutable values into containers matters more than removing
     dispatch.
  3. Profile-guided inlining of hot loop bodies, using the persisted profiles
     of C1.

### M12. Per-call overhead (cycle 8)

A function too large to inline but with a two-instruction hot path, called
200 M times (`/tmp` microbenchmark, recipe in the log) [M]:

| | Time per call |
|---|---:|
| zc -O2 | 1.9 ns |
| gcc -O2 `noinline` | 1.3 ns |
| **Ratio** | **1.47×** |

zc's prologue always does `push rbp; mov rbp, rsp; and rsp, -16; sub rsp, N`
and saves the callee-saved registers on entry, even when the hot path uses none
of them. gcc keeps no frame and saves registers only on the paths that need
them (shrink-wrapping).

An internal Zephyr-to-Zephyr convention would fix this:

- no stack realignment, because it is kept by construction;
- no frame pointer, because unwinding uses the frame map;
- shrink-wrapped saves.

This matters for every call-bound workload: fib, closures, dispatch, shapes.

### M13. Allocation strategy, isolated (cycle 8)

`research/proto/allocmodels.c` runs bintrees in C under different allocation
models. All models produce the same checksum as Zephyr [M]:

| Model | Time | Peak RSS |
|---|---:|---:|
| Zephyr today (`bench/bintrees.zeph`, -O2) | 800 ms | 19 MB |
| `rc24cell`: same representation as today (24-byte header, a counted cell per optional child, free list), but code specialized to the type | 294 ms | 26 MB |
| `rc24`: optionals as nullable pointers (no cells) | 205 ms | 14 MB |
| `rc8`: plus an 8-byte header | 148 ms | 10 MB |
| `region`: bump arena, reset per tree | 49 ms | 6 MB |
| glibc malloc/free (the C reference) | 290 ms | 10 MB |

**Decomposition of Zephyr's 800 ms:**

| Cause | Approximate cost | Fix |
|---|---:|---|
| Generic runtime paths (descriptor-driven release loops, out-of-line allocation with thread and heap checks, separate zeroing calls) | ≈ 500 ms | Allocation and release specialized per type at compile time; the compiler knows every layout statically |
| Optional cells | ≈ 90 ms | Nullable-pointer representation for reference optionals; `T?` has no identity, so this is unobservable |
| 24-byte header | ≈ 55 ms | 8-byte header |

A region on top of those fixes takes it to ~50 ms.

**Even without regions, reference counting with these representation fixes
beats malloc/free C by ~2×** (148 ms against 290 ms). Reference counting is not
the problem. The generic runtime is.

### M14. lexer: substrings as slices, tokens flattened (cycle 9)

**Profile of -O2 [M]:**

- `tokenize` takes 64% inclusive.
- Substring copying takes 22%.
- Allocation takes 24%.
- **The conservative GC takes 15%.** The token list keeps the heap growing past
  its target, so collections run.

`research/oracle/lexer_slices.zeph` is the oracle. `Token` is immutable, so
`[Token]` becomes parallel lists, and `str.sub` returns a (start, end) slice of
the source instead of a copy. Same checksum [M]:

| Version | Time | Peak RSS | vs C |
|---|---:|---:|---:|
| `bench/lexer.zeph`, -O2 | 1.20 s | 274 MB | 2.22 |
| Slices + SoA tokens | 0.84 s | 248 MB | 1.56 |
| C | 0.54 s | 65 MB | 1.00 |

**What this means:**

- Substrings as slices (a string view that keeps its parent alive) plus
  flattening remove the allocation and GC pressure: −30%.
- The rest is the scanning loop itself. It goes through `source.byte(i)` with a
  bounds check per byte, and the character tests are calls (`isLetter`,
  `isDigit`). Bounds-check elimination over monotone indices, and a
  256-entry class table, are the remaining levers [E].
- **Slice risk:** a small slice can keep a huge parent alive. The standard
  mitigation is to copy when the slice is under 1/k of its parent at the moment
  it is stored into a long-lived container [E].

### M15. Evidence for the interpreter as executable specification (cycle 9)

`git log` on `main` (172 commits, full history) shows about 25 commits about
the -O2 tier. At least 3 of them fix ownership or reference-count correctness:

- "never sink a string length load past a release"
- "a local copied from a global owns its value when the region may replace the global"
- "GC: mark objects through interior pointers"

Parity between tiers is maintained by `tests/optimizer_parity.ps1`,
`tests/run_parity.ps1` and the macOS JIT/AOT parity script. An IR interpreter
with checked memory semantics would catch premature frees deterministically,
which compiled code can silently survive. It would poison freed objects and
check counts on every access. That makes it a sanitizer and an oracle in one,
which supports role C6.

### M16. How often immutability inference applies (cycle 10)

`research/immutable_scan.py`, grouped per program (the compiler's files count
as one program), counts struct types never field-assigned. It is conservative:
any `.f =` or compound assignment to a field name counts against every struct
in that program with a field of that name [M].

**Across the repo:** 46 of 62 struct types (74%) are never field-assigned.

| Program | Immutable types | Mutated types |
|---|---|---|
| Workloads | vectors `Vec3`, lexer `Token`, all four shapes | nbody `Body` (updated in place), Mandelbrot-style numeric code has no structs |
| The compiler | 3 of 14: `InlineFrame`, `FunctionSignature`, `Instantiation` | The rest, including `Node`, `Token` and `Operand` |

**What this means:**

- Immutability inference covers the common case in user programs.
- The compiler itself barely benefits: its speed must come from the flat-IR
  rewrite (layer 2), not from inference.
- Mutable records stored in lists (nbody) need a second mechanism: element
  references represented as (list, index) pairs, so a flattened element can be
  mutated in place through an alias. This is future work [E]; nbody is already
  at 1.23× C.

### M17. Fixed costs of a cache-backed `zc run` (cycle 11)

Measured with `hyperfine -N` and a C loader microbenchmark [M]:

| Step | Time |
|---|---:|
| Start the 7.5 MB static zc and exit (`zc --version`) | 1.7 ± 0.3 ms |
| Map a 480 KB cached code image, patch 5,000 relocations, make it executable | 0.3–0.4 ms |
| Run an empty compiled program, process start to exit | 0.23 ms |

**Time to first instruction for `zc run fib.zeph` with a warm cache:**

- start zc: 1.7 ms;
- split and hash the source, then parse, check and compile two small
  functions: under 1 ms [E from M4b/M10];
- load the image: 0.4 ms.

That is **≈ 3 ms in total** [M components, E sum]. Today it is 280 ms of
compile, and 4 s on macOS. An interpreter tier could save at most the ~0.1 ms
of code generation inside that 3 ms. Scenario S1 of the cycle 2 evaluation is
now confirmed with measured components.

### M18. nbody: straight-line vectorization, not aliasing (cycle 12)

**Hypothesis:** body `i`'s velocity is loaded, updated and stored on every
inner iteration, a chain carried through memory. Instruction samples cluster on
that `subsd`/`movsd` pair. zc cannot keep the velocity in a register because
`bodies[j]` might be the same object as `bodies[i]`.

**Test:** `research/oracle/nbody_promoted.zeph` keeps `first.v*` in locals
across the inner loop. That's legal here, and a compiler would guard it with
one identity check. Results [M]:

| Version | Time |
|---|---:|
| `bench/nbody.zeph`, -O2 | 0.52 s |
| Scalar promotion oracle | 0.52 s |
| C | 0.43 s |

**Rejected.** Out-of-order execution hides the store-to-load forwarding chain,
and the samples were skid from the long-latency `divsd`/`sqrtsd` before it.

gcc's code contains packed `mulpd`, `addpd`, `subpd` and `divpd` (5 + 4 + 2 + 3
packed ops alongside the scalar ones). It vectorizes x/y pairs within one
iteration (straight-line vectorization).

**Same finding as vectors (M7).** For float workloads, straight-line pairing of
independent lanes is the missing backend capability. Loop vectorization over
SoA is the larger version of the same thing. Both belong in layer 3.

### M19. How much of each float gap is vectorization? (cycle 13)

Rebuilding the C references with `-fno-tree-vectorize -fno-tree-slp-vectorize`
gives a scalar-only C [M]:

| Workload | C -O2 | C, no vectorization | Zephyr -O2 | Gap explained by vectorization |
|---|---:|---:|---:|---:|
| nbody | 0.44 s | 0.49 s | 0.52 s | ~60% |
| vectors | 0.49 s | 0.56 s | 0.81 s | ~22% |
| mandel | 0.63 s | 0.63 s | 0.54 s | none (Zephyr is faster) |
| cube | 0.38 s | 0.38 s | 0.43 s | none |
| liquid | 0.90 s | 0.89 s | 1.09 s | none |

**Correction to M18:** vectorization explains most of nbody's gap but only a
fifth of vectors'. The larger remaining factor across vectors, cube and liquid
is scalar code quality. The vectors inner loop (M7) shows the specific losses:

- floats spilled to the stack while XMM registers are free;
- six separate bounds checks;
- constants reloaded from memory.

These point at the register allocator and at bounds-check elimination, not at
a vectorizer. Priorities inside layer 3 are, in order:

1. register allocation over the full XMM file, with no spills under low
   pressure;
2. bounds-check elimination for loops with a constant trip count over lists of
   known length;
3. straight-line vectorization, then loop vectorization.

### M20. Register allocation, measured by hand-editing zc's output (cycle 14)

**New tool:**

- `research/zc2gas.sh` converts zc's `--linux` assembly so GNU as accepts it:
  - adds explicit sizes on memory-immediate forms;
  - marks `.rdata` as allocatable.
- `research/start.s` supplies the entry stub that zc's ELF writer adds itself.
- The result links with `gcc -nostdlib -static` and produces identical output.

This makes **hand-edited codegen experiments** possible: change the hot loop
in the assembly and measure, without building the compiler change first.

**Experiment.** In `research/oracle/vectors_values.zeph`'s inner loop, zc
spills seven float values to the stack and reloads constants from memory each
iteration. I re-allocated the loop by hand:

- no spills (zc had used 15 XMM registers without reusing dead ones);
- two hot constants hoisted into xmm14/xmm15;
- the same six bounds checks and the same arithmetic order.

Results [M]:

| Version | Time | Checksum at 100 steps |
|---|---:|---|
| zc -O2 allocation, reassembled by GNU as | 0.82–0.92 s | 202045867 |
| Hand allocation | **0.59–0.67 s (−27%)** | 202045867 |
| C, no vectorization (M19) | 0.56 s | 202045867 |
| C -O2 | 0.49 s | 202045867 |

**What this means:**

- In vectors, the whole scalar gap comes from register allocation: hand
  allocation reaches non-vectorized C.
- The rest (0.56 → 0.49) is vectorization.
- This confirms M19's ordering: allocator first, then vectorization.
- Bounds checks were kept, so they are not a significant cost here: predictable
  branches on registers.

### M21. fib: calling convention and accumulator recursion (cycle 15)

Both results use the reassembly path from M20 [M]:

| Version | fib(43) |
|---|---:|
| zc -O2, reassembled | 1.23 s |
| Lean internal prologue: 6 `push`/`pop`, no frame pointer, no `and rsp, -16` | **1.05 s (−15%)** |
| Lean prologue + shrink-wrapped `n < 2` exit | 1.07 s (no further gain; the inlined leaves already avoid most entries) |
| Source oracle with accumulator recursion elimination (`research/oracle/fib_accumulate.zeph`), today's prologue | **0.80 s** |
| C -O2 | 0.83 s |

**What this means:**

- Two separable backend items close fib completely.
- The internal convention is worth 15% on call-heavy code. It applies to every
  workload with non-inlined calls.
- Accumulator recursion elimination alone reaches C.
- Together they should beat C [E].

### M22. Sampled profiles overstate long-latency instructions (cycle 16)

The formatter fix from M7, timed with `hyperfine -N`, 8 runs [M]:

| Workload | Formatter's sampled self-time (before → after) | Time (before → after) |
|---|---|---|
| strings | 63% → much lower | 544 → 423 ms (**−22%**) |
| strbuild | 25% → 11% | 1.020 → 0.992 s (**−3%**) |

In strbuild, the sampled share fell 14 points but the time barely moved.
Samples pile up on long-latency instructions (`idiv`) and the instructions just
after them, while the CPU overlaps that latency with other work.

**Method rule from now on:** profiles generate hypotheses, and only oracle
timings count as evidence. Every gain in the current-best section is backed by
an oracle or a rebuilt binary, not by a profile share.

strbuild's remaining 2.1× gap: its C version views substrings in place
(pointer + length), while Zephyr's `.sub` copies. That is the same lever as
lexer's slices (M14, −30%) [E for strbuild].

### M23. strbuild: slices and in-place append (cycle 17)

Oracles with identical output (md5 of stdout), `hyperfine -N`, 6–10 runs [M]:

| Version | Time | vs C |
|---|---:|---:|
| `bench/strbuild.zeph`, -O2 | ~0.99 s | 2.2 |
| `.sub` as slices (`research/oracle/strbuild_slices.zeph`) | 0.86–0.87 s | 1.95 |
| Line-building only, with slices (diagnostic) | 0.72 s | — |
| Slices + in-place append to the uniquely owned line (`strbuild_inplace.zeph`) | **0.62 s** | **1.45** |
| C (`snprintf` into a malloc'd buffer) | 0.43 s | 1.00 |

**What this means:**

- `line += "{name}={n}"` copies the whole line on every field. When `line`'s
  count is 1, the compiler can append into its buffer instead: reuse-when-unique,
  as in Perceus. Together with slices that is −37%.
- The rest is byte-at-a-time `[u8]` pushes and interpolation-builder overhead.
  A bulk append (`memcpy` of a whole string) is the next lever [E].

### M24. wordfreq: inconclusive (cycle 18)

Two attempts to bound a string-map redesign. Neither is trustworthy, and they
are recorded so they aren't repeated:

1. **Zephyr oracle** (`research/oracle/wordfreq_table.zeph`): open addressing
   with stored hashes, a key arena, and a word built in a reused `[u8]` buffer.
   - It ran in **2.23 s against 1.09 s for today's -O2**. Same checksum.
   - Byte-at-a-time Zephyr code (a `push` per byte, indexed reads for hashing
     and comparison) is far slower than the runtime's word-at-a-time
     primitives, so a Zephyr-source oracle can't bound runtime data-structure
     changes.
   - **Lesson:** use C models for runtime-representation questions, and Zephyr
     oracles for compiler-transformation questions.
2. **C model** (`research/proto/mapmodels.c`):
   - Today's representation: a counted string per concatenation, slots
     without stored hashes, word-at-a-time hash. **1.35 s**, close to real
     Zephyr's 1.09 s.
   - Redesign: in-place word building and stored hashes. **1.05 s (−22%)**.
   - But the C reference with the same design runs in **0.54–0.57 s**, so the
     model is missing something, probably its hash function or table
     parameters.
   - A follow-up that switched hashes was invalid (it called `getenv` per
     lookup).

**Status:** the wordfreq gap (1.95× C) is unexplained beyond "string
construction and map representation". Proposed next step: profile the C
reference against the model at instruction level before drawing conclusions.

### M25. What profiles are worth: gcc PGO on the 19 C references (cycle 19)

This is a proxy for the value of a JIT's runtime profiles, or of C1's
persisted profiles. Each program is built with `-fprofile-generate`, trained on
its own benchmark input, rebuilt with `-fprofile-use`, and timed as the median
of 3 runs on one core [M]:

| Effect | Workloads (PGO time / plain time) |
|---|---|
| Faster | strbuild 0.869, lexer 0.915, bintrees 0.930, sort 0.960, mandel 0.968, shapes 0.977, wordfreq 0.990 |
| Neutral (±1.5%) | matmul 0.997, records 1.005, fib 1.008, nbody 1.012, dispatch 1.015 |
| Slower | closures 1.041, liquid 1.045, hashmap 1.033, strings 1.061, pi 1.061, **vectors 1.507**, **cube 1.674** |
| **Geometric mean** | **1.042 (slower)** |

**What this means:**

- Even with training input identical to the test input, the best case for a
  profile, profile feedback buys at most ~5–13% on branchy string and
  allocation code. Elsewhere it does nothing or does harm.
- For a statically typed, monomorphized language, the information a JIT gathers
  at runtime is worth little.
- **That strengthens C1 (cached AOT, no JIT tier).** Persisted profiles should
  be an opt-in, measured optimization applied per function, never a default.

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
- **2026-10-01, cycle 5.**
  - Parallel-loop prototype (M8): 3.17× on 4 vCPUs, bit-identical; 0.6 µs fork-join.
  - fib's gap comes from one missing pass, accumulator recursion elimination
    (M9), not from the calling convention.
- **2026-10-01, cycle 6.**
  - Attacked the "no interpreter tier" verdict from the frontend side.
  - Declaration splitting and hashing of zc.zeph takes 7 ms (M10), so
    incremental rebuilds can hit < 20 ms without an interpreter.
  - An interpreter tier would only skip code generation, which is now the
    cheap part.
- **2026-10-01, cycle 7.**
  - shapes: the interface cell is not the cost; memory density is.
  - The 24-byte header makes objects 2× C's size, and flattening recovers 24%
    (M11).
- **2026-10-01, cycle 8.**
  - Per-call overhead is 1.47× C, from the prologue and missing shrink-wrapping
    (M12).
  - C allocation models (M13) split bintrees' 800 ms into: ~500 ms of generic
    runtime paths, ~90 ms of optional cells and ~55 ms of header size.
  - Reference counting with fixed representation beats malloc C 2×; regions
    reach 49 ms.
  - Microbenchmark recipe for M12: `work(a, b)` with a cold 40-statement branch
    (over the 60-node inline limit) and a hot `return a + b`, called in a
    200 M-iteration loop; C uses `__attribute__((noinline))`.
- **2026-10-01, cycle 9.**
  - lexer oracle (M14): slices + SoA tokens take it from 2.22× to 1.56× C, and
    remove GC pressure (15% of time).
  - Commit history (M15): at least 3 ownership miscompile fixes in about 25
    -O2 commits, which supports the interpreter-as-sanitizer/oracle role.
- **2026-10-01, cycle 10.**
  - Immutability scan (M16): 74% of struct types in the repo's programs are
    never mutated, but only 3 of 14 in the compiler.
- **2026-10-01, cycle 11.**
  - Fixed costs of a cached `zc run` (M17): ~3 ms to the first instruction,
    which confirms S1.
- **2026-10-01, cycle 12.**
  - nbody: a scalar-promotion oracle gave no gain. The gap is gcc's
    straight-line vectorization of x/y pairs (M18), the same capability as in
    vectors.
- **2026-10-01, cycle 13.**
  - C without vectorization (M19): vectorization explains ~60% of nbody's gap
    but only ~22% of vectors'.
  - Corrected M18. Register allocation and bounds-check elimination come before
    vectorization.
- **2026-10-01, cycle 14.**
  - Built a path to reassemble zc output with GNU as (`research/zc2gas.sh`).
  - Hand register allocation of the vectors loop: −27%, reaching
    non-vectorized C (M20). Register allocation explains the scalar gap.
- **2026-10-01, cycle 15.**
  - fib via reassembly (M21): the lean internal prologue is −15%;
    shrink-wrapping adds nothing here.
  - An accumulator-recursion oracle runs at 0.80 s against C's 0.83 s.
- **2026-10-01, cycle 16.**
  - The formatter fix gives strings −22% but strbuild only −3%, although
    strbuild's profile share fell 14 points (M22).
  - Adopted the rule that profiles are hypotheses and oracles are evidence.
- **2026-10-01, cycle 17.**
  - strbuild oracles (M23): slices −12%; slices + in-place append of a uniquely
    owned line −37% (2.2× → 1.45× C).
- **2026-10-01, cycle 18.**
  - wordfreq attempts (M24) were inconclusive. The Zephyr oracle was slower
    than today's runtime, and the C model didn't reproduce the C reference.
  - Recorded the method lesson: C models for runtime representation, Zephyr
    oracles for compiler transformations.
- **2026-10-01, cycle 19.**
  - gcc PGO on the C references (M25): geometric mean 1.042 (slower), best
    −13%, worst +67%. Profile feedback is a weak lever here, which supports C1
    further.
