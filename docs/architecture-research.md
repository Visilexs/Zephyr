# Compiler architecture research

Working document for `GOAL.md`. Every number is marked **[M]** (measured, with
the tool used) or **[E]** (estimated, with the reasoning). Tools live in `research/`.

## At a glance (cycle 59)

**Verdict:**

- One optimizing native compiler over one flat IR, made cheap by caching every
  compiled declaration under a hash of its content.
- An IR interpreter as the executable specification and oracle, **not as an
  execution tier**.
- Interpreters run 5–16× slower than native [M4]. Runtime profiles are worth
  ≤ 5–13% for this language [M25]. A warm cached `zc run` reaches its first
  instruction in ≈ 3 ms [M17]. So an interpreted or JIT tier has nothing left
  to win, except cold builds of very large programs (copy-and-patch is kept in
  reserve for that) [S7, M31].

**Where the speed comes from, measured by oracles:**

| Lever | Example |
|---|---|
| Representation: per-type allocation, nullable optionals, 8-byte headers, values flattened into lists, interface value = object pointer, slices, in-place append, regions | bintrees 3.0× → 0.29× C; records 1.25× → 1.01×; wordfreq and dispatch gaps fully explained [M7, M13, M27, M33, M44, M45] |
| Every function compiled whole, the same analyses everywhere | vectors −32%; removes a 6× placement cliff [M41, M42] |
| Backend: lean calling convention, accumulator recursion, vectorization | fib 1.46× → 0.95× C [M29] |
| Automatic parallelism | 3.2–3.9× on 4 cores, bit-identical [M8, M48] |

**Today → projected:**

| Measure | Today | Projected |
|---|---|---|
| Geometric mean vs gcc -O2 | 1.253× | 0.94× from measured oracles and C models; lower with SoA/AVX2 |
| Small-program build | ~300 ms | 5–15 ms |
| Incremental rebuild of zc | full rebuild | ~10–15 ms |

**Correctness:** differential fuzzing found an -O2 miscompile class, and an
evaluation-order split between the tiers that the spec leaves open [M39,
M40]. The spec should state left-to-right evaluation.

**No syntax changes are needed.** The build order with gates is below.

## Current best architecture

*(Revised every cycle. Cycle 72 state. Each claim cites a measurement.)*

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
   - Projections: small-program cold build ~5–15 ms [M parts: M46, M17]
     (from ~300 ms [M]);
     zc incremental rebuild ~10–15 ms [E].
   - A warm `zc run` reaches its first instruction in ≈ 3 ms (zc start
     1.7 ms + image load 0.4 ms) [M17].
   - Builds stay deterministic, because the cache only skips work. Parallel
     compilation must emit in a fixed order, so selfbuild fixpoints still hold.
2. **One flat IR.**
   - Typed SSA with block parameters, stored in preallocated `[int]` arrays.
   - The compiler's own hot data never touches the reference-counted heap.
     Today 43% of compile time is reference counting, allocation and GC [M3].
   - The flat pipeline runs at 0.23–0.27 µs per value in Zephyr [M4b], against
     7.3 µs for today's -O2 [M5]. An 11-pass version with dominators, loops,
     LICM and range analysis costs 0.18–0.23 µs per value in C, ~0.3–0.55 µs in
     Zephyr [M47].
   - Cold compile target ≈ 5–10 µs per small function [E]. Today zc takes
     165 µs, about gcc -O2's speed; tcc takes 1.6 µs [M32].
   - A flat lexer in Zephyr scans ~55 MB/s including token storage [M14:
     38.7 MB in ~0.7 s], so lexing zc.zeph costs ~20 ms.
3. **One optimizing native backend, emitting machine code directly.**
   - No text assembler, which is 28% of a self-compile today [M3].
   - Instruction selection, register allocation over all 16 GPRs and 16 XMMs.
     Hand allocation of one hot loop gave −27% (M20); compiling it as a whole
     function gave −32% (M41).
   - **Every function compiled whole.** No baseline fallback with outlined loop
     regions, because region outlining keeps every loop variable live across
     the loop. The vectors oracle goes from 804 to 551 ms when its loop sits in
     a whole-compiled function [M41].
   - Linear scan with two-address hints and a smaller scratch reservation.
     Interval splitting is lower priority than first thought [M30, corrected
     by M41].
   - Same analyses wherever code is placed. Today the original vectors is 6.3×
     slower in a function than at top level [M41]. Placement gate: within
     10%.
   - An internal calling convention: no frame pointer, no stack realignment,
     shrink-wrapped saves. Calls cost 1.47× C's today [M12]; a lean prologue
     alone is −15% on fib [M21].
   - It decides 11 of the 19 workloads [M6].
   - Missing passes, measured or identified:
     - accumulator recursion elimination; with the lean frame, fib goes from
       1.46× to 0.95× C [M9, M21, M29];
     - signed magic-number division [M7];
     - SoA loop vectorization with alias versioning [M7], and straight-line
       vectorization of paired x/y/z arithmetic, which gcc uses in both vectors
       and nbody [M7, M18];
     - inlining of hot loop bodies [M11].
   - Megamorphic sites stay indirect calls, since branch trees are slower
     [M28]. Interface methods pass arguments in registers, not on the stack
     (−3%) [M28].
   - Debug builds are this backend with passes off.
4. **Representation layer**, using closed-world, whole-program facts:
   - **Immutability inference:** never-mutated struct types become values,
     flattened into their containers (SoA). shapes: 1.83× → 1.40× [M11];
     vectors: bound 0.40× C with AVX2 [M7].
   - **Mutable records flattened too**, with element references as (list,
     index) pairs. records: 1.25× → 1.01–1.05× C [M27, M53].
   - **Region inference** for structures that die at the end of a statement or
     call. bintrees: 3.0–3.1× → 0.28–0.29× C [M7, M53]. Tracing GC was
     evaluated as an alternative and rejected: no faster than regions, and it
     breaks the spec's peak-memory promise [M52].
   - **Allocation and release specialized per type** instead of the generic
     descriptor-driven runtime paths. Worth ≈ 2.7× on bintrees in the C model
     [M13] and 4.1× in Zephyr (739 → 180 ms, 0.69× C) [M33].
   - **Nullable-pointer optionals** for reference types, no cells (−30% [M13]).
   - **8-byte object header** instead of 24 (−28% [M13]).
   - **Interface values as plain object pointers**, with the vtable found
     through the object's descriptor and no `{vtable, data}` cell. That
     representation explains ~90% of dispatch's gap [M45].
   - **Slices for substrings** and flattened token-like records. lexer: 2.22× →
     1.56× [M14].
   - **In-place append when the string is uniquely owned**, plus slices.
     strbuild: 2.0–2.2× → 1.29× [M23, M53]. wordfreq's whole 1.9× gap is
     concatenation [M44].
   - **No cycle collection when the type graph is acyclic**, and tracing
     restricted to cycle-capable types otherwise. lexer −12.5%, shapes −6%,
     wordfreq −5% [M36].
   - **Runtime data structures co-designed with the optimizer:** small strings,
     hashes stored in map slots, a formatter in the fast division domain.
     strings: 1.49× → 1.22× [M7].
5. **Automatic loop parallelism**, enabled by layer 4 (no reference-count
   traffic on SoA data).
   - 3.17× on 4 cores, bit-identical [M8]. Also mandel 3.94×, matmul 3.69×,
     bintrees 1.76× with malloc and 2.7× with per-thread regions
     (18 ms, ~16× serial C) [M48].
   - Only for loops with ≥ 5–10 µs of work per invocation.
   - Counts stay non-atomic. Atomic counts are 12× slower and biased ones 1.4×
     [M26], so parallel bodies must provably do no count updates on shared
     objects.
6. **The IR interpreter as the executable specification.**
   - A differential-testing oracle for every pass, run with the random program
     generators in `research/fuzz/`. Those found a real -O2 miscompile class
     and an evaluation-order split between today's tiers [M39, M40].
   - The compile-time evaluator and the debugger.
   - It is not an execution tier. Interpreters run 5–16× slower than native
     [M4], and with caching there is no latency left for a tier to hide [M10].
   - Runtime profiles, a JIT's other advantage, are worth ≤ 5–13% at best and
     −4% on average here [M25]. So profiles stay opt-in.
   - Copy-and-patch from the interpreter's handlers stays in reserve (18–20 ns
     per op in C [M31]). It is triggered if the optimizer ever exceeds ~2 µs
     per value, or for cold builds of programs above ~100 k lines without a
     shared cache (scenario S7).

### Flat IR design sketch for step 3 (cycle 65)

**Today** (`compiler/optimizer.zeph` lines 135–232):

- 73 opcodes, all fairly low-level: loads, stores, `irListData`,
  `irBoundsCheck`, `irCall`.
- Parallel lists, but each instruction's operands are a separate heap list
  (`irOperands: [[int]]`).
- Struct, list, interface and reference-count semantics are already lowered
  into loads, stores and calls. The representation passes of layer 4 therefore
  have nothing high-level to work on.

**Proposed layout:** structure-of-arrays, every array preallocated and grown
by doubling, no per-instruction heap objects.

| Array | Per value | Meaning |
|---|---|---|
| `op`, `type` | int, int | opcode; type id (int, float, bool, or a reference to type T) |
| `a0`, `a1`, `a2` | int ×3 | fixed operands: value ids, or −1 |
| `imm` | int | immediate, field index, site id, or type id |
| `block` | int | owning block |
| `extra`, `extraCount` | int ×2 | start and length in one shared `args` pool, for calls, block arguments and multi-way switches |

Blocks get parallel arrays: first and last value, parameter start and count,
successors, and the terminator's argument range in `args`. That is ~9 ints per
value, ~72 bytes. All of zc (622 k values) is ~45 MB, freed as a few arrays.

**Three levels in one IR**, where lowering replaces ops in place:

1. **Semantic.** `alloc T`, `field.get` / `field.set`, `list.get` / `set` /
   `len` / `push`, `iface.call slot`, `closure.make`, `str.*` as intrinsics,
   `retain` / `release`, `check.bounds` / `check.zero` carrying a panic site, and
   plain calls with Zephyr's evaluation order already explicit (left to right).
   **The IR interpreter executes this level: it is the executable spec.**
2. **Representation.** After layer 4's decisions: flattened fields and SoA
   lists (`soa.get`, `soa.set`), regions (`region.enter`, `region.alloc`,
   `region.exit`), reference-count ops removed or specialized per type, and
   interface values as object pointers.
3. **Machine.** Loads, stores and address modes, the internal calling
   convention, and instruction-selected x86 or ARM64 ops before register
   allocation.

**Effects per opcode**, from a static table: reads and writes by memory class
(type id plus field, which gives type-based alias analysis for free), may-free,
may-panic and may-call. Optimizations query effects, never opcode lists.

**Differential checking between levels:** the interpreter runs level 1, and an
instrumented build runs levels 2 and 3. Lowering bugs like M39's are then caught
at the level where they happen.

### What changes on Apple Silicon (cycle 63)

These numbers combine the repository's own M5 results with components measured
here on x86. ARM64 itself was not measured in this environment (A2, Q9).

| Measure | macOS today [M, `tests/benchmarks/results/`] | Projected with the proposed design [E] |
|---|---|---|
| Build of a small benchmark program | median **4.8 s** baseline, **2.6 s** -O2 (19 workloads); clang builds the C versions in 45 ms | ~5–15 ms: the same frontend and cache as x86 (M46), a native ARM64 encoder instead of `arm64.py` + clang |
| `zc run` startup | ~4.0–4.3 s per run (JIT report) | ≈ 3 ms (M17 components) |
| Tier-up pause | 321–335 ms per function, constant (clang) | none: no tiers; cached optimized code |
| -O2 runtime vs clang -O2 (geometric mean) | 1.28× (M5 report) | the same levers as x86. Expected to land near the x86 projection (~0.94×), but unmeasured |

**macOS-specific requirements for the native backend:**

- **Code signing.** Apple Silicon only runs signed executables, and an ad-hoc
  signature is enough. Today clang's linker produces it. A native Mach-O writer
  must emit `LC_CODE_SIGNATURE` with a CodeDirectory of SHA-256 page hashes:
  ~500 KB of code is ~1 ms of hashing [E].
- **JIT memory for `zc run`.** In-process execution needs `MAP_JIT` memory and
  `pthread_jit_write_protect_np` toggling, since writable and executable is
  never allowed at the same time. Today `bootstrap/macos/jit.c` covers this, and
  it stays.
- **No clang and no Python on the build path.** Mach-O writing, signing and
  ARM64 encoding all move into zc. The existing ELF/PE writers (~220 lines,
  M35) are the model.

### Language changes the architecture needs

**No syntax changes.** Readability is unaffected, and the bootstrap seed needs
no new syntax.

- **One spec clarification:** expression operands, including reads of globals,
  are evaluated **left to right**. -O2 already follows this in 98% of
  order-sensitive cases; baseline doesn't [M40].
- **Representation changes programs cannot observe:**
  - **nullable-pointer optionals:** `T?` has no identity or `addr()`;
  - **an 8-byte header:** sizes and headers are not observable;
  - **flattened and SoA values:** only for types with no `addr()` use; struct
    `==` is already structural;
  - **slices for `str.sub`:** strings are immutable;
  - **regions:** the spec says freeing time is unobservable, but promises that
    peak memory tracks the live set, so regions must be per statement or per
    call, never long-lived.
- **One place the spec constrains the design:** the heap is non-moving and
  `addr()` exposes addresses (spec §3.6, §4). So flattening must exclude any
  type whose values reach `addr()`, and no moving collector is possible.

**Projected single-core geometric mean vs gcc -O2** (cycle 53 update):

| Basis | Geometric mean |
|---|---:|
| Today [M] | 1.253 |
| Every workload at its best **measured** oracle (each one applies a single transformation; untested workloads at today's value) [M] | **0.98** (cycle 68, same-session values) |
| The same, with vectors at its C-measured SoA + AVX2 bound (0.40) | 0.93 |
| Measured oracles + C-representation models: wordfreq ≈ 1.0 (M44), dispatch ≈ 1.05 (M45) | **0.935** |
| The same, plus the vectors SoA + AVX2 bound | 0.885 |

Per-workload values used in the 0.99 row:

| Workload | Value | Source |
|---|---:|---|
| fib | 0.95 | M29 |
| matmul | 0.55 | today |
| mandel | 0.98 | today |
| sort | 0.53 | today |
| strings | 1.22 | M7 |
| hashmap | 0.71 | today |
| cube | 1.15 | today |
| pi | 0.58 | today |
| liquid | 1.20 | today |
| shapes | 1.41 | M11, M53 |
| closures | 1.10 | today |
| wordfreq | 1.95 | today; M24 inconclusive |
| nbody | 1.23 | today |
| lexer | 1.56 | M14 |
| vectors | 1.24 | M20, hand register allocation |
| dispatch | 1.43 | M28 |
| records | 1.05 | M27, M53 |
| strbuild | 1.29 | M23, M53 |
| bintrees | 0.28 | M7, M53 |

Combining transformations should compound: for example, register allocation
plus the lean convention plus header shrinking on the same workload. Those
combinations haven't been measured, so they aren't counted. Parallel workloads
go well below 1.0 on multicore machines [M8].

### Build order with acceptance gates

Each step ships behind a flag, and must pass bit-identical parity against the
current pipeline on every test and on the 19 workloads before the next step
starts. It must also pass a differential-fuzzing run of `research/fuzz/` with
zero unexplained mismatches (M39). A gate is the measured number the step must reach. Each is derived from
the oracle or prototype that justified the step.

| Step | What | Gate (x86-64 Linux, this VM class) | Basis |
|---|---|---|---|
| 1 | Cache the compiled runtime and std as machine code | Empty-program build ≤ 30 ms (today 260 ms) | M3 |
| 2 | Direct byte emission from the current backend (drop the text assembler) | Self-compile −25% | M3 (28%) |
| 3 | Flat IR for the optimizer's data (`[int]` arrays) | -O2 cost ≤ 2 µs per value (today 7.3) | M4b, M5 |
| 4 | Internal convention + linear scan with splitting | fib ≤ 1.05 s; vectors oracle ≤ 0.65 s | M20, M21 |
| 5 | Specialized per-type allocation and release, nullable optionals, 8-byte header | bintrees ≤ 200 ms (today 740) | M13, M33 |
| 6 | Immutability/flattening (SoA), slices, in-place append | records ≤ 1.05× C, lexer ≤ 1.6× C, strbuild ≤ 1.5× C | M14, M23, M27 |
| 7 | Acyclic type-graph analysis: no cycle collector | lexer −10% | M36 |
| 8 | Declaration-level cache + incremental rebuild | zc edit-one-function rebuild ≤ 20 ms; a forced whole-program fact flip rebuilds byte-identically to a clean build | M10, M17, M54 |
| 9 | Vectorizer (straight-line + SoA loops), accumulator recursion | nbody ≤ 1.1× C; vectors ≤ 0.6× C; fib ≤ 0.95× C; matmul stays ≤ 0.55× C without the pattern kernel; cube ≤ 1.0× C | M18–M21, M29, M34, M38 |
| 10 | Region inference | bintrees ≤ 100 ms | M7 |
| 11 | Automatic loop parallelism | vectors ≥ 3× on 4 cores, bit-identical | M8 |
| 3b | Every function compiled whole: no baseline fallback, no outlined regions | Placement gate: top-level vs in-function kernels within 10% (vectors today: 0.72 vs 4.51 s; oracle 0.80 vs 0.55 s) | M41 |
| 12 | ARM64 instruction selection over the same IR | macOS: no clang, no `arm64.py`; `zc run fib` ≤ 10 ms to first instruction | M17, macOS results |

The IR interpreter (oracle/sanitizer) is built alongside step 3. Every later
step's parity tests run against it as well as against the old pipeline.

## Scoreboard

| Target | Goal | Today, x86-64 Linux | Source |
|---|---|---|---|
| Small-program cold build (`fib.zeph`) | < 100 ms | 280 ms baseline, 530 ms -O2 | [M] `/usr/bin/time`, Xeon 2.1 GHz |
| Empty program cold build | < 100 ms | 260 ms (runtime only) | [M] |
| Self-compile (`zc.zeph`, 19k lines + runtime) | — | 3.14 s baseline, 7.67 s -O2; 256 MB / 471 MB peak RSS | [M] |
| 40,000 small functions (compilegen 200×200) | — | zc 6.6 s (baseline) / 22.5 s (-O2); tcc 0.063 s; clang -O0 3.5 s; gcc -O2 6.3 s | [M] M32 |
| Incremental rebuild | < 20 ms | same as a cold build today; ~10–15 ms projected for zc with declaration-level caching | [M] today; [E] projection from M10 |
| Single-core geometric mean, -O2 vs gcc -O2 | ≤ 1.0–1.1× | **1.253×** over 19 workloads today; **0.99×** with each workload at its best measured oracle; **0.94×** including C-representation models | [M] `research/x86bench.py`; oracles M7–M45 |
| Bit-identical output across modes | required | **Not met today:** the 19 workloads match, but 18 of 600 random programs (3%) print different results at baseline and -O2 | [M] M2, M39 |
| Peak memory vs C | report it | geometric mean 0.66×. Small programs are 0.2–0.5× (static binary, no libc). Allocation-heavy: lexer 4.23×, dispatch 2.26×, shapes 2.20×, bintrees 1.97×, records 1.65×. Oracles: bintrees 19 → 5 MB (region, M7), shapes 205 → 168 MB (flattening, M11) | [M] M37 |
| Compiler size | report it | 24.4 k hand-written Zephyr lines today: zc.zeph 14.3 k (excluding the 4,980-line generated EMBED), optimizer 7.2 k, runtime 2.9 k; plus ~1 k lines of Python/C for macOS. Proposed design: ~28–33 k lines with native x86 and ARM64 backends, an IR interpreter and the cache, after deleting the baseline generator, text assembler, `arm64.py` and `jit.py`; +15–30% overall | [M] today (section markers); [E] proposed |

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

**Re-run on a quiet machine (cycle 64,** `research/results/x86-linux-rerun.json`**):**

- Geometric mean **1.255**, against 1.253 in the first run, so the headline is
  robust.
- Single workloads moved by up to ~±10% between runs:
  - dispatch 1.47 → 1.70;
  - vectors 1.69 → 1.52;
  - shapes 1.69 → 1.81;
  - strings 1.49 → 1.57.
- That is the noise band for this VM: single-workload differences under ~10%
  are only trusted from same-session A/B comparisons. All oracle comparisons in
  this document use same-session A/B runs.

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

**Cycle 49 instruction-level profile [M]:**

- In Zephyr, `runtimeFindMapEntry` takes 62% of samples. Two loads account for
  42.5% of all samples:
  - the probe's slot-state load (21.9%, at the `test` after it);
  - the key string's length, loaded after a tag match (20.6%).
- The C reference spends 35% in `tableIncrement` and ~38% in libc (`malloc`,
  `memcmp`).
- Zephyr's map already stores hash tags in slot state, rehashes at ≤ 50% load
  (`runtime.zeph` line 1530) like C, and dereferences the key only on a tag
  match, also like C.
- **So the 2× is not from load factor or missing hash tags.** The remaining
  hypotheses are:
  - probes per lookup, from how the slot index is derived from the hash
    (`hash >> shift` and the tag layout);
  - cache behaviour of keys scattered across the heap.
- Next test: count probes per lookup in a scratch runtime and compare with C's
  table.

**Cycle 50: probes per lookup** (`research/patches/runtime-probe-count.patch`,
14 M words, 69,904 distinct) [M]:

- 14.07 M lookups and 14.93 M probe steps, so **1.06 probes per lookup**.
- 14.0 M tag hits, so essentially every lookup finds its key at once.

**Probing is near-ideal. Rejected:** probe count and slot-index derivation.
What's left for Q6:

- **Memory latency:** at 2¹⁸ slots × 24 B ≈ 6 MB plus ~3.5 MB of keys, the
  table exceeds this core's 2 MB of L2. C's table is 2¹⁸ × 32 B, also outside L2.
- **Per-lookup overhead:**
  - the call into `runtimeStringsEqual`;
  - hashing a string built by 1–4 concatenations, against C's stack buffer;
  - the concatenations' allocations (`runtimeAppendString`, 11.6%).

The remaining oracle to write: a C model differing from the C reference only
in string allocation per concatenation.

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

### M26. Sharing across threads: what atomic counts would cost (cycle 20)

`research/proto/rccost.c` does one retain and one release per object over 4,096
objects in shuffled order, single-threaded and uncontended. A compiler barrier
stops gcc from cancelling the plain pairs [M]:

| Scheme | ns per count update | vs plain |
|---|---:|---:|
| Plain non-atomic (today) | 0.48–0.50 | 1.0× |
| Biased (owner check, then plain; other threads atomic) | 0.68–0.73 | ~1.4× |
| Always atomic | 5.9–6.2 | ~12× |

**What this means:**

- Atomic counts everywhere are out: 12× per update, on code where count
  updates are a large share of the time (M3, M13).
- Biased counting would allow sharing at +40% per update. That is still a tax
  on all code, to benefit only code that shares.
- **Adopted instead:**
  1. Parallel loops only where the compiler proves the body does no count
     updates on shared objects (layer 5; SoA values make this the common case).
  2. Parallel compilation through share-nothing workers that exchange the flat
     `[int]`-array IR by copy, or through processes. The flat IR from layer 2
     makes the copy cheap.
- This keeps today's 0.5 ns plain counts for all single-threaded code.

### M27. records: flattening mutable records (cycle 21)

`bench/records.zeph` updates struct fields in place through list elements.
Today each element is a pointer to a separate object (24-byte header + 64-byte
payload), against C's inline 64-byte structs. The oracle
`research/oracle/records_soa.zeph` stores one list per field. The original's
element aliases (`for record in records { record.f = … }`) become index
accesses, which is what (list, index) element references would compile to.
Same checksum, `hyperfine -N`, 5 runs [M]:

| Version | Time | vs C |
|---|---:|---:|
| `bench/records.zeph`, -O2 | 1.27 s | 1.25 |
| SoA oracle | **1.03 s** | **1.01** |
| C (inline array of structs) | 1.02 s | 1.00 |

**What this means:** mutable records need flattening too, not only immutable
ones (M16). The mechanism is element references as (list, index) pairs.

- They are safe because a list's storage is reachable only through the list.
- They need care at growth: a `push` that reallocates must leave existing
  (list, index) references valid. It does, since the reference names the list,
  not the storage address.

This moves the M16 "future work" item into the plan.

### M28. dispatch: megamorphic calls (cycle 22)

Measured with `hyperfine -N` on one core, 6–8 runs. Every variant produces the
same checksum [M]:

| Version | Time |
|---|---:|
| `bench/dispatch.zeph`, -O2 | 0.45–0.49 s |
| Closed-world tagged struct with inlined bodies behind a 3-level branch tree (`research/oracle/dispatch_tagged.zeph`) | 0.50 s (**slower**) |
| Tagged struct + per-kind function table, one indirect call (`dispatch_table.zeph`) | 0.49 s (no change) |
| Reassembled: arguments in registers, no frames on the 16 method bodies | 0.47 s (−3%) |
| C, vtables + malloc | 0.29–0.32 s |
| Construction only (`rounds = 0`): Zephyr vs C | 95 ms vs 45 ms |

**Findings:**

- With 8 implementations in random order, a branch tree on the tag costs more
  than one mispredicted indirect call. Closed-world dispatch should keep
  indirect calls at megamorphic sites, and use guards only where a profile or
  static count shows ≤ 2–4 targets.
- Interface methods take their arguments on the stack (`[rbp + 16]`,
  `[rbp + 24]`), which puts the serial value chain through memory. Fixing that
  is worth only 3% here: store-to-load forwarding is cheap next to the
  mispredicted indirect call.
- Of the ~170 ms gap:
  - ~50 ms is construction, the generic allocation path (M13);
  - the dispatch loop is ~1.4× C. The remaining loop cost is attributed to
    the extra dependent load through the `{vtable, data}` cell and to object
    size (~80 bytes per element against ~32) [E; not isolated by an oracle].

### M29. Combining two transformations on fib (cycle 24)

`research/leanframe.py` rewrites chosen functions in reassembled zc output to
the lean internal frame. It keeps `rsp`-relative spill slots and refuses
functions it cannot rewrite safely. Applied to the accumulator oracle (M21),
`hyperfine -N`, 8 runs [M]:

| Version | fib(43) | vs C |
|---|---:|---:|
| Accumulator oracle, zc frame | 836 ms | 1.02 |
| Accumulator oracle + lean frame | **777 ms** | **0.95** |
| C -O2 | 817 ms | 1.00 |

The two transformations compound, as expected, and fib ends up faster than C.
This is the first measured combination. The projection now uses 0.95 for fib.

### M30. Lean frames on shapes; what zc's register allocator lacks (cycle 25)

**Negative results [M]:**

| Experiment | Before | After |
|---|---:|---:|
| `leanframe.py` on `area`, `perimeter`, `cornerCount` in `shapes_flat` | 794 ms | 798 ms (no change; C 606 ms) |
| Moving the vectors oracle's top-level loop into `fn main()` | 816 ms | 784 ms (−4%) |

Call overhead does not limit shapes. Its remaining 1.31× sits with memory:
system time is 81–91 ms against C's 42 ms. In the function version, `main`
falls back to baseline (`call kind 7`), and its outlined hot loop still reports
**17 spills over 217 values**.

**The allocator, from `compiler/optimizer.zeph` line 4168:**

- Linear scan over live ranges with holes ("inactive" intervals), phi
  coalescing, spill costs, and eviction of the cheapest active group.
- **No interval splitting.** A value is either in one register for its whole
  life or spilled for its whole life.
- 14 allocatable XMMs (`xmm2`–`xmm15`). `xmm0` and `xmm1` are reserved as
  scratch.
- A value that crosses any call must take a callee-saved register. Under the
  Win64-style convention that means `xmm6`–`xmm15` only, and the prologue saves
  all ten of them.

The hand allocation in M20 used splitting-free but two-address-aware reuse
(computing `pull = offset × f` in place) and freed the scratch registers. That
was worth −27%.

**Recommendation for layer 3:** linear scan with interval splitting (the
Wimmer & Franz design used in HotSpot C1), with hints from x86's two-operand
instructions and a smaller scratch reservation. Reserve the cost of a full
graph-colouring allocator for hot loops only, if splitting proves insufficient.

The flat prototype's basic linear scan costs 69 ns per value in Zephyr (M4b);
splitting is estimated at ≤ 2× that [E].

### M31. Copy-and-patch emission speed (cycle 28)

`research/proto/stencils.c` emits a stream of IR ops from 32 synthetic
stencils: 12–48 bytes each, with 1–3 holes for frame offsets, immediates and
backward branch displacements. Each op is a fixed 48-byte copy plus the patches
[M]:

| Ops | Time | Per op |
|---:|---:|---:|
| 24 M (727 MB of code), buffer pre-touched | 0.44–0.48 s | 18–20 ns |
| 0.6 M | 10.5–12.2 ms | 18–20 ns |
| 24 M, fresh buffer (first-touch page faults included) | 1.9–3.7 s | 78–155 ns |

**What this means:**

- The 20 ns-per-op estimate used in the cycle 2 and S7 rows is confirmed in C.
  In Zephyr it is ~40 ns [E, from M4b's ~2× factor].
- **Page faults dominate when the output buffer is fresh.** Any tier that
  generates large amounts of code should reuse its code buffers or pre-map
  them. That applies to the optimizing tier too.

### M32. Compile speed against other compilers (cycle 29)

The program is generated by `bench/compilegen.py` (revision 398aadd): 200 call
chains × 200 functions deep, seed 1. That is 40,000 tiny functions in ~40 k
lines. Same checksum everywhere. `hyperfine -N`, 3 runs [M]:

| Compiler | Time | Per function |
|---|---:|---:|
| tcc 0.9.27 | **63 ms** | 1.6 µs |
| clang 18 -O0 | 3.47 s | 87 µs |
| gcc 13 -O2 | 6.26 s | 157 µs |
| zc, baseline (`--linux --rt`) | 6.59 s | 165 µs |
| gcc 13 -O0 | 10.2 s | 254 µs |
| zc -O2 | 22.5 s | 563 µs |

**zc's profile on this program** (6,038 samples) has the same shape as the
self-compile (M3):

| Area | Share |
|---|---|
| Reference counting, allocation and GC | ~50% self (GC alone 8.5%) |
| AST inlining | 32% inclusive; cloning nodes 16% |
| Code generation | 42% |
| Text assembler | 16% |

There is no quadratic hotspot: it is per-node cost.

**What this means:**

- Today zc's baseline is gcc -O2-class in compile speed, and 100× slower than
  tcc.
- tcc shows what direct single-pass emission with flat data reaches.
- For the proposed design, the flat pipeline at ~0.25 µs per value with ~10
  values per small function, plus a flat frontend, gives an estimated
  5–10 µs per function [E]. That is 0.2–0.4 s for this program cold, 20–30×
  faster than today, and caching makes rebuilds ~ms.
- Matching tcc outright would need the frontend to emit code as it parses,
  which is incompatible with whole-program optimization. It is therefore not
  a target. tcc is the reference point for the stencil reserve (C3).

### M33. Specialized reference counting in Zephyr itself (cycle 31)

`research/oracle/bintrees_rcspecial.zeph` keeps reference counting but
specializes it to `Node`:

- nodes in flat arrays: left, right and count;
- a per-type free list;
- recursive release when a count reaches zero;
- nullable indices instead of optional cells;
- no regions.

Same checksum, `hyperfine -N`, 6 runs [M]:

| Version | Time | vs C (malloc/free) |
|---|---:|---:|
| `bench/bintrees.zeph`, -O2 | 739 ms | 2.8 |
| **Specialized RC (this oracle)** | **180 ms** | **0.69** |
| Region + flattening (M7) | 73 ms | 0.28 |
| C model `rc8` / `rc24` (M13) | 148 / 205 ms | — |

**What this means:** M13's C-model conclusion holds in Zephyr-compiled code.
Specializing allocation and release to the type, plus nullable optionals, gives
4.1× and beats C's malloc/free, while keeping reference-counting semantics
(deterministic frees, peak memory tracks the live set). Regions are a further
2.5× on top, where the analysis can prove them.

### M34. cube: baseline vector kernels against the optimizer (cycle 32)

`tryOptimizeFunction` (`compiler/optimizer.zeph` line 7022) leaves a whole
function on baseline when it contains a loop the baseline compiles to a native
vector kernel. In cube, that is the framebuffer clear and the checksum fold
inside `render`. A scratch compiler (`/tmp` copy, not the shipping one) with
the rule disabled optimizes `render` (246 values, 1 spill) but loses the
kernels. Same checksum [M]:

| Build | cube (80,000) |
|---|---:|
| zc -O2 today (`render` on baseline with kernels) | 418 ms |
| Scratch zc, `render` optimized without kernels | 692 ms (+66%) |
| C -O2 | 355 ms |

**What this means:**

- The vector kernels are worth more than optimizing the rest of the function,
  so the current rule is right for today's compiler.
- The proposed design removes the trade-off: the optimizing tier gets its own
  vectorizer (layer 3), so no function has to choose between scalar
  optimization and vectorized loops.
- Two separately built tiers create cross-tier trade-offs like this one. That
  is one more argument for a single code generator.

### M35. liquid, and where the compiler's lines go (cycle 33)

**liquid** (`neighbours`, 66% of time): the hot instructions are `sqrtsd`, a
`divsd` by `RADIUS = 7.0`, and bounds-check compares against lengths spilled to
`[rsp + …]` [M, `research/hotspots.py`]. Division by 7.0 can't be strength-
reduced exactly, so C divides too. The remaining gap matches the allocator
finding (M30); there is no new lever.

**Compiler composition** (section markers in `compiler/zc.zeph`) [M]:

| Section | Lines |
|---|---:|
| Generated EMBED (runtime and std as text) | 4,980 |
| "imports" section, which spans much of the frontend | 5,498 |
| Monomorphization | 1,989 |
| WebAssembly backend | 1,917 |
| Parser | 1,243 |
| Reference counting | 1,196 |
| AVX2 kernel | 1,035 |
| Text assembler | 854 |
| Types | 759 |
| Lexer | 505 |
| Checker | 464 |
| Register calling convention | 204 |
| ELF writer | 167 |
| PE writer | 52 |

The proposed design deletes the baseline generator, the text assembler and the
pattern kernels (subsumed by the vectorizer), and adds native instruction
selection for x86 and ARM64, the cache and the interpreter. Estimate: +15–30%
total [E].

### M36. Skipping cycle collection when no cycle is possible (cycle 34)

Zephyr's conservative mark-sweep collector exists only to reclaim cycles
(spec §4). It runs whenever the heap grows past its target, so programs whose
live set grows pay for repeated full scans even when their types cannot form a
cycle. A scratch runtime (`/tmp` copy) makes `runtimeCollectGarbage` return
immediately, which is valid only for acyclic programs. Outputs identical
(md5), `hyperfine -N` [M]:

| Workload | With collector → without | Change |
|---|---|---:|
| lexer | 1.190 → 1.041 s, RSS 274 → 268 MB | **−12.5%** |
| shapes | 1.060 → 0.996 s | −6% |
| wordfreq | 1.098 → 1.041 s | −5% |
| dispatch, records, hashmap, sort, closures, strings, strbuild | within ±2–4% | noise |

**Sound version for the architecture:**

- Whole-program type analysis: a cycle needs a cycle in the type graph, where
  struct fields, list elements, optionals, closures' captured types and
  interface implementations are the edges.
- If no type in the program can reach itself, the collector is never needed
  and is not linked.
- Otherwise only objects of cycle-capable types need tracing: the collector
  scans roots, but marks through cycle-capable types only.
- The compiler itself (`Node.children: [Node]`) is cycle-capable, so it would
  use the restricted form.

### M37. Peak memory, Zephyr -O2 against C (cycle 36)

Measured as peak RSS from `/usr/bin/time -f %M`, at the benchmark sizes [M]:

| Workload | Zephyr MB | C MB | Ratio |
|---|---:|---:|---:|
| fib, mandel, strings, strbuild | 0.3 | 1.5–1.6 | ~0.2 |
| cube, nbody, pi, vectors, liquid | 0.4–1.2 | 1.7–2.5 | 0.24–0.47 |
| matmul | 28.3 | 29.3 | 0.96 |
| sort | 46.2 | 92.9 | 0.50 |
| wordfreq | 16.9 | 15.4 | 1.10 |
| hashmap | 48.8 | 35.6 | 1.37 |
| closures | 25.4 | 18.3 | 1.39 |
| records | 103.3 | 62.6 | 1.65 |
| bintrees | 18.8 | 9.5 | 1.97 |
| shapes | 200.6 | 91.2 | 2.20 |
| dispatch | 90.1 | 39.8 | 2.26 |
| lexer | 267.4 | 63.1 | 4.23 |
| **Geometric mean** | | | **0.66** |

**What this means:**

- Zephyr's static, libc-free binaries win on small programs.
- On allocation-heavy ones, Zephyr uses 1.4–4.2× more memory than C, for the
  same reasons as the time gaps:
  - 24-byte headers;
  - interface cells and optional cells;
  - a separate heap object per record;
  - a copied substring per token.
- The representation layer (layer 4) addresses memory and time together.
  bintrees falls from 19 MB to 5 MB with a region (M7), below C's 9.5 MB.

### M38. Where Zephyr already beats C, and must keep winning (cycle 37)

| Workload | -O2 / C | Reason | Evidence |
|---|---:|---|---|
| pi | 0.58 | Loop-invariant divisors (`cur / x2`, `curt / d`) get a magic multiplier computed once at loop entry (`irDivideByInvariant`). gcc emits `idiv` every iteration. | C source lines 34–39; gcc output has 4 `idiv`/`div` in loops |
| sort | 0.53 | The runtime's sort is specialized to the element type. C's `qsort` calls a comparator through a function pointer on every comparison. | `bench/sort.c` line 16 |
| hashmap | 0.71 | Hash tags stored in map slots (commit "map hash tags"). The C reference keeps a separate `used` byte array. | `bench/hashmap.c` |
| matmul | 0.55 | AVX2 kernel for the AXPY pattern | `zc.zeph` "AVX2 kernel" section |

All four are specialization wins: knowledge a C compiler doesn't have, or
that C's library interface hides. They belong in the new design:

- **invariant-divisor magic:** a pass in layer 3;
- **monomorphized runtime algorithms:** layer 4's runtime co-design;
- **stored hash tags:** already in the runtime;
- **the AXPY kernel:** subsumed by the vectorizer. Its result (0.55×) is the
  vectorizer's gate for matmul.

### M39. Differential fuzzing finds -O2 miscompiles in today's zc (cycle 38)

**Tools:**

- `research/fuzz/genprog.py` generates random, deterministic, panic-free
  Zephyr programs: functions, loops, wrapping ints, lists, structs, optionals,
  interpolation and globals mutated inside called functions.
- `research/fuzz/difftest.py` compiles each at baseline and at -O2 with the
  same zc and compares the output.
- `research/fuzz/reduce.py` shrinks a mismatch.
- `research/fuzz/genref.py` is a second generator aimed at ownership and
  reference-count patterns.

**Result [M]:** seeds 1000–1599 of `genprog.py` gave **18 mismatches in 600
programs (3%)**. Every program compiles and exits 0 in both modes; only the
printed checksums differ. The failing sources are in `research/fuzz/failures/`.

**Seed 1009, reduced** to 20 lines in
`research/fuzz/repro/loop-exit-global-1009.zeph`:

- baseline prints 13, -O2 prints 12;
- `for i in 0..1 { acc = i }` stores into the global `acc`;
- the next statement `acc = acc * 1 + max(…)` reads `acc`.

-O2 computes that read as `lea rbx, [r8 + r9]`, where `r8` is the loop
counter after its final increment (1), not the last value stored to `acc` (0).
The forwarded value of the global after the loop is off by one iteration. It
only reproduces together with a later call that modifies `acc` (`f1(…, f0(1),
…)`); in simpler programs the read goes back to memory and the result is right.

**Classification of the 18 (cycle 39):**

- `PURE=1 genprog.py` makes called functions never assign globals or push to
  `xs`, so no result can depend on evaluation order. Seeds 1000–1599 in that
  mode gave **1 mismatch in 600** (seed 1292).
- Seed 1292, reduced (`research/fuzz/repro/pure-1292.zeph`), shows the same
  bug as seed 1009: `for i in 0..11 { acc = i }`, then a read of `acc` gives
  11 at -O2 (the incremented counter) where baseline gives 10.
- Reduced seeds 1162, 1260 and 1404 (`research/fuzz/repro/min*.zeph`) all have
  the shape `acc = acc * 1 + (… f0(…) …)` where `f0` assigns `acc`. Their
  results depend on when the outer `acc` is read relative to the call.
- **Conclusion:**
  - one definite miscompile class: a global assigned from the loop counter,
    forwarded past the loop exit with the post-increment value;
  - the remaining ~16 mismatches are the two tiers disagreeing on evaluation
    order, which the spec leaves undefined.
- Both break the project's parity requirement. The second is fixed by
  specifying the order (left-to-right is the usual choice) and making both
  tiers follow it.

**Ownership-focused fuzzing (cycle 40):** `GEN=genref.py`, seeds 1–400, gave
**0 mismatches and no crashes** [M]. The generator covers aliases into lists of
structs, globals replaced while still in use, string building and slicing,
lists of lists, closures capturing lists, and string-keyed maps. -O2's
reference-count handling holds up under these patterns. The bugs found are in
scalar value forwarding, not in ownership.

**Floats, closures and interfaces (cycle 47):** `GEN=genext.py` covers
bounded float arithmetic, sqrt and division, interface dispatch over three
implementations, closures capturing values, and float lists. Side-effect free.
Seeds 1–500 gave **0 mismatches** [M].

**Fuzzing totals:**

| Generator | Programs | Mismatches |
|---|---:|---:|
| `genprog` | 600 | 18 (1 miscompile class plus evaluation order) |
| `genprog` PURE | 600 | 1 (same class) |
| `genref` | 400 | 0 |
| `genext` | 500 | 0 |
| `genmap` (maps, generics) | 400 | 0 |
| Repository fixtures (`tests/*.zeph`, `tests/fixtures/basics`, `tests/regression`, thread fixtures), baseline vs -O2 on Linux | 39 | 0 |
| `genpair` three-way | 400 | 47 departures from left-to-right, almost all in baseline |

**Spec gap found at the same time:** `docs/spec.md` does not define evaluation
order. `acc = acc + bump()`, where `bump` modifies `acc`, gives 101 in both
modes, meaning `acc` is read after the call. Left-to-right would give 1. Both
tiers agree, but the language should state the order.

**What this means for the architecture:**

- Random differential testing finds real optimizer bugs at a rate of about 3%
  of generated programs, on a compiler that passes its own parity suites.
- That is direct evidence for layer 6, the interpreter as oracle, and for
  making differential fuzzing part of every step's gate.
- A third opinion is needed to know which side is wrong when tiers disagree.
  The spec-level IR interpreter provides it.

### M40. A three-way oracle: baseline, -O2 and an executable reference (cycle 41)

`research/fuzz/genpair.py` emits each random program twice:

- as Zephyr;
- as Python with explicitly defined semantics: 64-bit wraparound after every
  int operation, `/` truncating toward zero, `%` with the dividend's sign,
  arithmetic `>>`, and strict left-to-right evaluation, including reads of
  globals before calls further right in the same expression.

`research/fuzz/tritest.py` runs all three and classifies the outcome. This is a
miniature of layer 6, the interpreter as executable specification.

**The reference itself is validated:** with `PURE=1`, where functions never
write globals so order can't matter, 60 of 60 programs agree three ways [M].

**Order-sensitive programs, seeds 100–499** [M]:

| Outcome | Programs |
|---|---:|
| All three agree | 353 (88%) |
| **Baseline departs from left-to-right; -O2 follows it** | **39 (9.75%)** |
| Both tiers agree with each other but not with left-to-right | 6 (1.5%) |
| All three differ | 2 (0.5%) |
| -O2 departs; baseline follows | 0 |

**What this means:**

- -O2 almost always evaluates left to right. Baseline often reads a global
  after a later call in the same expression has changed it.
- Today's tiers therefore implement different evaluation orders, and the spec
  doesn't say which is right.
- **Recommendation:** specify left-to-right in `docs/spec.md`, since it's what
  -O2 already does in 98% of these programs. Then fix baseline, and the
  remaining -O2 cases, to match.
- For the architecture: the executable specification decides such questions
  once, and both tiers are tested against it.

The 2 "all three differ" seeds are candidates for further miscompiles, such as
the M39 loop-exit class. Their sources are in
`research/fuzz/failures/pair-seed*.zeph`, with `.py` references.

### M41. Placement cliffs: the same loop at top level and in a function (cycle 43)

Hot loops written at top level, or in a function that falls back to baseline,
are compiled as outlined `zopt_region`s. Their source variables are loaded from
the frame on entry and written back on exit. The test moves the same loop into
an ordinary function that -O2 compiles whole. Outputs identical,
`hyperfine -N` [M]:

| Program | Top level (region) | In a function | Change |
|---|---:|---:|---:|
| vectors oracle (SoA values, M7) | 804 ms, 17 spills | **551 ms, 5 spills** | **−32%** |
| `bench/records.zeph` | 1.246 s | 1.174 s | −6% |
| `bench/closures.zeph` | 0.684 s | 0.646 s | −5.5% |
| shapes, dispatch, lexer, wordfreq, strings, mandel, matmul, strbuild | — | — | within ±5% |
| **`bench/vectors.zeph` (original, `Vec3` structs)** | **720 ms** | **4.51 s** | **+526%** |

**What this means:**

1. **Correction to M20/M30.** Most of the vectors-oracle spilling came from
   region outlining, not from the allocator lacking interval splitting. As a
   whole function the same loop reaches 551 ms, faster than the hand
   allocation (0.61 s) and level with non-vectorized C (0.56 s). Interval
   splitting stays on the list, with lower priority.
2. **Today's optimizations are context-dependent heuristics.** In the original
   vectors, moving the loop into a function loses the in-place reuse of list
   elements. 36% of the time then goes to allocating and releasing `Vec3`
   (profile), and the program is 6.3× slower. That is exactly the kind of
   performance cliff the earlier conversation warned about.
3. **Architecture requirements that follow:**
   - one code path for every function: no baseline fallback with outlined
     regions;
   - the same analyses wherever code is placed;
   - `--opt-report` must state allocation and reuse decisions per site;
   - a new **placement gate**: each workload's hot kernel, at top level and in a
     function, must run within 10% of each other.
     `research/oracle/vectors_in_function.zeph` and
     `vectors_values_in_function.zeph` are the first two test cases.

### M42. Placement cliffs with data passed as parameters (cycle 45)

Idiomatic code passes its data to functions instead of reading globals.
Outputs identical [M]:

| Program | Top level (globals) | Function, data as parameters |
|---|---:|---:|
| vectors (`research/oracle/vectors_params.zeph`) | 0.71 s | **4.26 s (6×)** |
| records (`research/oracle/records_params.zeph`) | 1.30 s | 1.23 s |

**What this means:**

- The vectors cliff (M41) isn't about globals specifically. It is about the
  pattern that stores freshly built struct values back into list elements
  (`velocities[i] = velocity`). The in-place reuse that makes that cheap fires
  only for top-level code on list globals.
- records, which updates fields in place and never rebuilds structs, has no
  cliff.
- **Implication for measurement:** the benchmark suite is written in
  top-level style, so its geometric mean (1.253× C) can flatter -O2 on
  idiomatic code. Wherever a workload's style allows it, the suite should gain
  a function/parameter variant, and its numbers should count in the
  scoreboard alongside the originals.

### M43. How often objects die before their allocating frame returns (cycle 48)

**Method.** A scratch runtime (a `/tmp` copy) records `stackPointer()` at every
allocation, in a side table indexed by object address, and compares it at every
free. With 512 bytes of slack for runtime frames, a free counts as **in frame**
if the stack hasn't unwound past the allocating frame, and as **escaped**
otherwise. Objects never freed are live until exit. All at -O2 [M]:

| Workload | Allocations | Freed in frame | Escaped | Never freed |
|---|---:|---:|---:|---:|
| bintrees | 29.9 M | 29.6 M (99%) | 0.0 M | 0.3 M |
| lexer | 12.97 M | 12.97 M (100%) | ~0 | ~0 |
| wordfreq | 10.5 M | 10.37 M (98.8%) | 0.06 M | 0.07 M |
| strbuild | 16.0 M | 10.5 M (65.7%) | 5.5 M | ~0 |
| strings | 4.0 M | ~0 | 4.0 M (*) | ~0 |
| pi | 13.4 k | 8.9 k (67%) | 4.4 k | — |
| shapes | 4.5 M | 0.3 M | ~0 | 4.2 M (live data) |
| dispatch | 2.0 M | ~0 | ~0 | 2.0 M (live data) |
| records | 1.0 M | ~0 | ~0 | 1.0 M (live data) |
| vectors, nbody, closures, small kernels | ≤ 8 k | — | — | — |

(*) strings' strings are allocated inside runtime interpolation helpers. The
helper's frame returns before the user code frees them, so the metric counts
them as escaped. This is a measurement artifact: they die in the user's frame.
Part of strbuild's "escaped" share is the same artifact.

**What this means:**

- For allocation-heavy workloads whose objects die, **two-thirds to all of
  them die before the allocating user frame returns.** That is the upper bound
  for function-scope regions. Statement-scope regions need the stricter proof
  M7 used.
- Long-lived data (shapes, dispatch, records) is not a region candidate. Those
  workloads need the density fixes (M11, M27, M13).
- Region inference (layer 4, step 10) has broad potential on the
  allocation-heavy class. A real escape analysis in the compiler will capture
  some fraction of this upper bound [E].

### M44. wordfreq: the gap is string building, not the map (cycle 51)

`research/oracle/wordfreq_alloc.c` is the C reference with exactly one change:
each word is built by repeated concatenation into newly allocated heap strings
(32-byte header + bytes, the previous one freed), as Zephyr does. Same
checksum [M]:

| Version | Time |
|---|---:|
| C reference (word in a stack buffer) | 0.59 s |
| **C with Zephyr-style concatenation** | **1.135 s** |
| Zephyr -O2 | 1.097 s |

**The whole 1.9× gap is word construction.** The map is as good as C's, and
M50 showed 1.06 probes per lookup.

The profile blamed `runtimeFindMapEntry` (62%) because allocation churn
evicts the table and keys from cache, so the cost shows up on the map's loads.
That's the M22 lesson again: profiles locate stalls, oracles find causes.

**Fix:** in-place append when the string is uniquely owned (M23), or lowering
`word = word + piece` in a loop to a builder. Expected to bring wordfreq to
about C's 0.59 s [E, from this oracle]. **Q6 is closed.**

### M45. dispatch: the gap is the interface representation (cycle 52)

`research/oracle/dispatch_cells.c` is the C reference with Zephyr's
representation:

- each list element points to a counted `{vtable, data}` cell (24-byte header);
- the cell points to the object, which also has a 24-byte header;
- calls go `cell->vtable->apply(cell->data, …)`.

Same checksum [M]:

| Version | Time |
|---|---:|
| C reference (object with an inline vtable pointer, malloc) | 329 ms |
| **C with Zephyr's cell + header representation** | **464 ms** |
| Zephyr -O2 | 480 ms |

**What this means:**

- Representation explains about 90% of dispatch's gap. **Q7 is closed.**
- The fix: an interface value is the object pointer itself, with the vtable
  found through the object's descriptor (one load from the header), and no
  cell allocation. Plus the 8-byte header (M13).
- This refines M11. In shapes, removing only the cell, while keeping 24-byte
  headers and growing every object to six fields, gained nothing. In
  dispatch's small objects the cell is a large share of the bytes. Both
  results point to the same lever, bytes per element.

### M46. User code's share of a small-program build (cycle 54)

`hyperfine -N`, 15 runs, baseline `--linux --rt` [M]:

| Program | Build time |
|---|---:|
| Empty `fn main() { }` | 309 ± 11 ms |
| `fib.zeph` (10 lines) | 307 ± 11 ms |
| `bench/lexer.zeph` (151 lines) | 318 ± 20 ms |
| `bench/shapes.zeph` (140 lines) | 318 ± 19 ms |

User code costs ≤ 10 ms even at today's per-node speed (165 µs per function,
M32); the rest is the runtime. With the compiled runtime cached (build step
1), a small-program build is ≈ zc start (1.7 ms, M17) + user code (≤ 10 ms) +
link (~1–3 ms) ≈ **5–15 ms**. That confirms, from measured parts, the
"10–30 ms" projection and step 1's ≤ 30 ms gate, without any of the other
steps.

### M47. A heavier optimizer pipeline: cost per value (cycle 55)

`research/proto/flatopt.c` with `extended = 1` adds, on the same flat arrays:

- dominators (Cooper–Harvey–Kennedy);
- natural-loop detection;
- loop-invariant code motion of pure ops;
- interval range analysis for bounds-check elimination, with widening at loop
  headers;
- a second fold/copy-propagation/GVN round and a second DCE.

That makes 11 passes in total. C, ns per SSA value, one core [M]:

| Function size | Basic 6 passes | Extended 11 passes | Added passes alone |
|---|---:|---:|---:|
| ~500 values | 123 | 179 (+46%) | 52 |
| ~2000 values | 140 | 226 (+61%) | 79 |

Using Zephyr's measured 1.6–2.4× factor (M4b), the extended pipeline is
~0.3–0.55 µs per value in Zephyr [E]. Not yet included: inlining, reference
count optimization, the vectorizer, interval splitting and pattern-based
instruction selection. Even if those double the cost again, the total stays at
~0.6–1.1 µs per value: within the 0.7–1.4 µs estimate used in the cycle 2
evaluation, toward its low end, and below the 2 µs copy-and-patch gate.

### M48. Parallel speedups on more workloads (cycle 56)

The C references get one OpenMP pragma each
(`research/oracle/parallel/*_omp.c`) on the loop an auto-parallelizer would
pick:

- mandel's row loop;
- matmul's `i` loop;
- bintrees' per-depth iteration loop.

Integer reductions only, so results stay exact. 4 vCPUs, `hyperfine -N` [M]:

| Workload | Serial | 4 threads | Speedup | Checksum |
|---|---:|---:|---:|---|
| mandel | 0.587 s | 0.149 s | **3.94×** | identical |
| matmul | 1.100 s | 0.299 s | **3.69×** | identical |
| bintrees | 0.284 s | 0.162 s | 1.76× | identical |
| vectors (M8, SoA) | 604 ms | 191 ms | 3.17× | identical |

**What this means:**

- Data-parallel kernels scale nearly linearly.
- bintrees is limited by `malloc` lock contention and its serial phases (the
  stretch tree and the long-lived tree).
- In the proposed design, per-thread regions (M7) remove the allocator
  contention. Measured in cycle 57: `research/oracle/parallel/bintrees_region_omp.c`
  (one bump arena per thread) goes from 48.6 ms on 1 thread to **18.0 ms on 4
  threads (2.7×; the serial stretch and long-lived trees bound the rest)**,
  with the same checksum. That is ~16× faster than serial malloc C (284 ms)
  [M].
- The safety conditions from M8 hold for all three: index-disjoint writes,
  integer reductions, no shared reference-count traffic. A Zephyr compiler
  could prove each of them.

### M50. Object lifetimes inside the compiler (cycle 61)

The compiler is built with the M43-instrumented runtime, plus
`research/patches/zc-print-lifetimes.patch`, which prints the counters at the
end of the driver. zc built at baseline [M]:

| Compile | Allocations | Freed within the allocating frame | Escaped upward | Live until exit |
|---|---:|---:|---:|---:|
| `zc.zeph` self-compile | 12.80 M | 7.17 M (56%) | 2.72 M (21%) | 2.91 M (23%) |
| `bench/lexer.zeph` at -O2 | 3.75 M | 2.49 M (66%) | 0.68 M (18%) | 0.58 M (16%) |
| compilegen 40 k functions | 33.16 M | 16.71 M (50%) | 8.21 M (25%) | 8.24 M (25%) |

**What this means:**

- In the compiler, half to two-thirds of allocations die before the frame that
  allocated them returns. That upper bound for function-scope regions is
  similar to the allocation-heavy workloads (M43).
- About a quarter (the AST, symbol tables, assembly text) lives for the whole
  compile and is exactly what the flat-IR rewrite turns into a few big arrays.
- 12.8 M allocations for one self-compile, at ~0.1–0.25 µs each including
  release (M13, M33), is 1.3–3 s. That matches M3's finding that allocation,
  reference counting and GC are ~43% of the 3.14 s self-compile.

### M51. How good is simple copy-and-patch code? (cycle 62)

`research/proto/stencilcode.c` models stencil code that keeps every value in
a frame slot: each op loads its operands from the frame and stores its result,
modelled with a `volatile` frame. Same kernels as M4, same results, one core
[M]:

| Kernel | Stencil-style | Native gcc -O2 | Interpreter (M4) | zc baseline today, vs C (M2, M4 basis) |
|---|---:|---:|---:|---:|
| fib(32) | 15–17 ms (**~4×**) | 3.8–4.3 ms | 14× | ~2.3× |
| Bounds-checked sum, 50 M | 98–100 ms (**~6.8×**) | 14.5 ms | 19× | — |
| mandel 600² | 58–64 ms (**~3.4×**) | 17.9 ms | 5.3× | ~1.3× |

**What this means (Q8):**

- Simple stencil code is 2–3× faster than an interpreter, but 1.5–3× slower
  than zc's current baseline, which keeps values in registers within
  expressions.
- Stencils that pass the top values in registers would close part of that
  [E].
- Either way, a copy-and-patch tier suits only scenario S7: the first build of
  a very large program with an empty cache. It should not replace debug builds.
  The optimizing backend with passes off compiles at similar cost per value
  and runs faster.
- **Q8 is closed.** C3 stays in reserve, scoped to S7.

### M52. Tracing GC instead of reference counting? (cycle 66)

`research/proto/allocmodels.c gc` is a non-moving mark-sweep collector with a
bump young generation. It marks from the roots (the long-lived tree and the
partial trees under construction), then sweeps to a free list. Frees happen at
collections, not at last use. bintrees, same checksum, one core [M]:

| Model | Time | Peak RSS | Collections |
|---|---:|---:|---:|
| GC, young generation 2¹⁸ nodes | 163 ms | 6.0 MB | 112 |
| **GC, young generation 2²⁰ nodes** | **124 ms** | 19.1 MB | 16 |
| GC, young generation 2²² nodes | 156 ms | 71.3 MB | 3 |
| GC, young generation 2²³ nodes | 188 ms | 141 MB | 1 |
| Specialized RC, 8-byte header (`rc8`, M13) | 148–195 ms | 9.8 MB | — |
| Regions (M7) | 49–80 ms | 5.8 MB | — |

**What this means:**

- At its best young-generation size, tracing is ~1.2–1.5× faster than
  specialized reference counting on this workload. It uses 2× the memory, and
  its speed depends strongly on generation size.
- Regions beat both, at the least memory.
- **Spec §4 promises that peak memory tracks the live set, "rather than twice
  it".** Tracing breaks that promise by design.
- **Verdict:** keep specialized reference counting plus regions. Tracing is
  not a fallback worth its spec cost. Where region inference fails,
  specialized reference counting is within ~1.5× of tracing GC with half its
  memory.

### M53. Every oracle re-timed in one session (cycle 68)

`hyperfine -N`, 6 runs each, core 3, one quiet session
(`research/results/oracles-same-session.json`) [M]. Ratios are to C in the
same session:

| Workload | Original -O2 | Oracle(s) | C |
|---|---|---|---:|
| bintrees | 770 ms (3.10) | specialized RC 175 ms (0.70); region 70 ms (0.28) | 248 ms |
| vectors | 694 ms (1.59) | SoA values at top level 764 ms (1.75); **SoA values in a function 542 ms (1.24)** | 436 ms |
| lexer | 1232 ms (2.35) | slices + SoA tokens 816 ms (1.56) | 524 ms |
| strbuild | 974 ms (2.01) | slices 852 ms (1.76); **slices + in-place append 625 ms (1.29)** | 485 ms |
| records | 1326 ms (1.25) | SoA 1117 ms (1.05) | 1061 ms |
| shapes | 1134 ms (1.90) | flattened 840 ms (1.41) | 596 ms |
| fib | 1247 ms (1.43) | accumulator 838 ms (0.96) | 870 ms |

All earlier single-session results are confirmed within the noise band.
strbuild's in-place oracle comes out better than first measured (1.29 against
1.45).

### M54. Whole-program facts against incremental rebuilds (cycle 71)

**The attack:**

- Layer 4's decisions rest on whole-program facts: "`Vec3` is never mutated",
  "the type graph is acyclic", "these are all of `Shape`'s implementations".
- An edit anywhere can flip a fact and invalidate code everywhere, which could
  defeat the 10–15 ms incremental target (M10).

**Design:** every fact becomes a cache input. Each function's cache key
includes the hashes of the facts it relied on, so a flip recompiles exactly the
dependents.

**Cost of the worst flips in the compiler itself** [M for counts, E for time]:

- The 813 functions of `zc.zeph` + `optimizer.zeph`, counted by type name:
  - `Node`: 308 functions;
  - `Token`: 8;
  - `StructDefinition`, `FunctionDefinition`: 6 each;
  - `Operand`: 5;
  - `VariableInformation`: 4;
  - `InlineFrame`: 3;
  - every other type: ≤ 2.
- A flip on `Node` would recompile ~308 functions × ~530 values × 0.5–1 µs
  (M47) ≈ **80–160 ms**. Recompiling all 813 functions ≈ 0.2–0.45 s.
- `Node` is already mutable and cycle-capable, so in practice its facts never
  flip. The types whose facts can flip (the immutable ones, M16) are named in
  1–3 functions.

**Verdict:** whole-program facts are compatible with incremental builds. A
fact flip is a rare, bounded rebuild in the hundreds of milliseconds, against
~10–15 ms for a normal edit. The cache must record fact dependencies
explicitly. This adds one item to step 8's gate: a forced fact flip rebuilds
correctly, verified by a byte-compare against a clean build.

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
| S7 cold build of a very large program (1 M lines ≈ 24 M SSA values, using zc's 24 values per line [M5]; empty shared cache) | 24 M × ~1 µs ≈ 24 s single-threaded, ~6 s on 4 cores [E], + frontend ~2–4 s [E] | Starts after the frontend, then interprets at 5–16× slowdown [M4] | 24 M × 18–20 ns ≈ 0.5 s of stencils in C [M31], ~1 s in Zephyr [E], + frontend; full speed comes later from background optimization | n/a | n/a |
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
- **C3 also wins S7 (added in cycle 27):** a cold build of a program of about
  1 M lines with an empty cache. There, stencils cut seconds of code
  generation to about half a second.
  - This is the one scenario where the stencil family, the closest relative of
    an interpreted compiler, clearly wins.
  - So C3 stays in reserve, triggered either by the 2 µs-per-value gate or by
    programs above ~100 k lines without a shared cache.
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

**Attack in cycle 58: correctness by construction.** The fuzzing (M39, M40)
showed today's tiers diverge, through one miscompile class and through
evaluation order. Does an interpreted design prevent that by construction?

- In C3, copy-and-patch stencils are compiled from the interpreter's handlers.
  That is a crude first Futamura projection: the interpreter specialized to one
  program. A stencil tier therefore can't disagree with the interpreter on
  per-op semantics.
- In C1, the debug build is the optimizing backend with passes off. It shares
  the AST → IR lowering with the optimized build. The IR interpreter defines
  each op's meaning, and tests check both.
- **What actually diverged in M39/M40:** evaluation order, which is decided in
  lowering, and value forwarding across a loop exit, which is an optimization
  pass. Both designs share the lowering. Neither derives optimization passes
  from the interpreter, so neither prevents pass bugs by construction.
- **Verdict unchanged.** Per-op correctness by construction is a real but
  small benefit of C3, because per-op semantics weren't where the bugs were.
  The oracle plus differential fuzzing is what catches lowering and pass bugs,
  under either design. Recorded so the attack isn't repeated.

| Candidate | Verdict | Deciding evidence |
|---|---|---|
| C1 cached AOT, one optimizing tier | **Adopted** as the execution model | S1, S4, S5 above; M3 |
| C2 interpreter first, then JIT | Rejected as a tier | M4: 5–16× native, 4–7× worse than current baseline; nothing to speculate on |
| C3 copy-and-patch from interpreter handlers | **In reserve**, gated on Q1 | Wins only on an empty cache |
| C4 partial evaluation of an interpreter | Rejected | Its strength is speculation; an extra compiler for no gain |
| C5 meta-tracing | Rejected | Recursion and branchy code trace poorly; same warm-up problem as C2 |
| C6 IR interpreter as executable spec and oracle | **Adopted** in that role | Removes the parity-bug class; required for compile-time evaluation anyway |

### Backend candidates (consolidated in cycle 69)

| Candidate | Result | Verdict | Evidence |
|---|---|---|---|
| Text assembly + zc assembler (today) | 28% of a self-compile is the assembler | Replace with direct encoding | M3 |
| Outlined loop regions inside baseline functions (today) | vectors oracle 804 → 551 ms when compiled whole; a 6× cliff in the other direction for rebuilt structs | Replace: every function compiled whole | M41, M42 |
| Linear scan without splitting (today) | 17 spills in a region; 5 when the loop is compiled whole | Keep linear scan; add two-address hints. Splitting is low priority (Q4) | M30, M41 |
| Hand-quality register allocation | −27% on the vectors loop | Target quality; whole-function compilation gets most of it | M20, M41 |
| Lean internal calling convention | −15% on fib; 0% on shapes; −3% for register-passed interface arguments | **Adopted** | M21, M28, M30 |
| Accumulator recursion elimination | fib 1.43 → 0.96× C; 0.95× with the lean frame | **Adopted** | M21, M29 |
| Signed magic division | strings −22% via a formatter patch | **Adopted**, as an optimizer pass | M7, M22 |
| Invariant-divisor magic (exists today) | pi 0.54–0.58× C | **Keep** | M38 |
| Straight-line vectorization (pair x/y/z ops) | explains ~60% of nbody's gap and ~22% of vectors' | **Adopted**, after allocation | M18, M19 |
| SoA loop vectorization + alias versioning | vectors bound 0.40× C (AVX2) | **Adopted**; it replaces the pattern kernels | M7, M34, M38 |
| Pattern-specific native kernels (today) | cube: worth more than optimizing the rest of the function | Subsume into the vectorizer | M34 |
| Branch-tree devirtualization at megamorphic sites | slower than an indirect call | Rejected; keep indirect calls | M28 |
| Profile-guided optimization (gcc as proxy) | geometric mean 1.042 (worse); best −13% | Opt-in only | M25 |

### Memory management candidates (consolidated in cycle 67)

All rows are bintrees unless noted, same checksum, one core.

| Candidate | Result | Verdict | Evidence |
|---|---|---|---|
| Today's generic reference counting: 24-byte header, optional cells, descriptor-driven release | 739–800 ms, 19 MB | Replace | M7, M33 |
| Reference counting specialized per type, nullable optionals | 180 ms in Zephyr (0.69× C); C model 148–205 ms | **Adopted as the default** | M13, M33 |
| + 8-byte header | −28% in the C model | **Adopted** | M13 |
| + regions where escape analysis proves death at statement or call end | 49–80 ms, 5–6 MB (0.29× C) | **Adopted, guarded by proof** | M7, M43, M50 |
| Per-thread regions in parallel loops | 2.7× on 4 threads (18 ms) | **Adopted with layer 5** | M48, cycle 57 |
| Tracing GC (non-moving, generational) | best 124 ms / 19 MB; breaks the spec's peak-memory promise | Rejected | M52 |
| Atomic reference counts everywhere | 12× per count update | Rejected | M26 |
| Biased reference counting | 1.4× per count update | Rejected; parallel bodies are proven count-free instead | M26 |
| Cycle collector always linked | lexer −12.5% without it | **Only when the type graph has cycles**; tracing restricted to cycle-capable types | M36 |

## Open questions

**Answered:**

- **Q1** (cycle 3): a flat pipeline costs 0.23–0.27 µs per value in Zephyr
  [M4b]. A production pipeline is estimated at 0.7–1.4 µs.
- **Q2** (cycle 2): an interpreter runs 5–16× slower than native [M4].
- **Q3** (cycle 28): copy-and-patch emission costs 18–20 ns per op in C [M31].
  The quality of its code is still open; see Q8.

**Open, in priority order:**

- **Q4. Deprioritized (cycle 69):** most of the spilling M20 attributed to
  missing interval splitting was region outlining (M41). Compiled whole, the
  same loop has 5 spills and reaches non-vectorized C. Revisit only if
  whole-function compilation leaves hot spills.
- **Q5. Mostly answered (cycles 48 and 61, M43, M50):** 66–100% of freed
  objects in allocation-heavy workloads, and 50–66% of all allocations in the
  compiler, die before their allocating frame returns. Still open: how much of
  that a static escape analysis proves.
- **Q6. Answered (cycle 51, M44):** wordfreq's gap is entirely
  string building by repeated concatenation. The fix is in-place append.
- **Q7. Answered (cycle 52, M45):** dispatch's gap is the `{vtable, data}`
  cell and 24-byte headers. The fix is interface value = object pointer, with
  the vtable through the header.
- **Q8. Answered (cycle 62, M51):** simple stencil code runs 3.4–6.8× native,
  slower than today's baseline. C3 is for S7 only.
- **Q9.** Do x86-64 Linux numbers transfer to Windows (A2), and do the
  architecture's gains transfer to ARM64? Needs a Windows or Apple Silicon
  host.
- **Q10.** Are there more miscompile classes? Partly answered: floats,
  closures and interfaces found 0 in 500 programs (cycle 47), and maps and
  generics 0 in 400 (cycle 60). Threads: the two thread fixtures match across
  tiers (cycle 70), but random thread programs aren't generated, because
  scheduling makes them nondeterministic.

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
- **2026-10-01, cycle 20.**
  - Count-update costs (M26): plain 0.5 ns, biased 0.7 ns, atomic 6 ns.
  - Kept non-atomic counts. Parallelism requires bodies proven free of count
    updates, and parallel compilation uses share-nothing workers.
  - Saved `research/pgo_c.py` for M25.
- **2026-10-01, cycle 21.**
  - records SoA oracle (M27): 1.25× → 1.01× C. Mutable records flattened via
    (list, index) element references joins the plan.
- **2026-10-01, cycle 22.**
  - dispatch (M28): branch-tree devirtualization is slower than indirect
    calls, and table dispatch is unchanged.
  - Register arguments gain 3%. Construction is 2.1× C.
  - The rest is attributed to the extra load through the interface cell and to
    density.
- **2026-10-01, cycle 23.**
  - Recomputed the projection from measured oracles only: 0.99× C geometric
    mean (0.93× with the vectors SoA bound).
- **2026-10-01, cycle 24.**
  - Built `research/leanframe.py`.
  - The accumulator oracle + lean frame gives fib 0.95× C (M29), the first
    measured combination of two transformations.
- **2026-10-01, cycle 25.**
  - Lean frames: no gain on shapes. Moving the top-level loop into a function:
    −4% on vectors.
  - Characterised zc's allocator (M30): linear scan without splitting, 14 XMMs
    with 2 reserved, and callee-saved constraints across calls.
  - Recommended linear scan with splitting and two-address hints.
- **2026-10-01, cycles 26–27.**
  - -O2 coverage on all 19 workloads: only 2 baseline fallbacks (a pi loop with
    `call kind 15`, and cube's `render`, which holds a native kernel).
  - Added scenario S7, a cold build of ~1 M lines: copy-and-patch wins it,
    ~0.5 s against ~6–24 s of optimized code generation [E].
  - C3's reserve triggers now include program size.
- **2026-10-01, cycle 28.**
  - Copy-and-patch emission measured at 18–20 ns per op (M31), confirming the
    estimate.
  - First-touch page faults can make it 4–8× slower, so code buffers should be
    reused.
- **2026-10-01, cycle 29.**
  - Compile-speed comparison (M32): zc baseline 6.6 s ≈ gcc -O2 6.3 s, against
    tcc's 63 ms, on 40 k tiny functions.
  - The profile shows per-node cost (memory management ~50%), not a quadratic
    hotspot.
- **2026-10-01, cycle 31.**
  - Specialized-RC oracle in Zephyr (M33): bintrees 739 → 180 ms (0.69× C),
    confirming M13 without regions.
- **2026-10-01, cycle 32.**
  - cube (M34): disabling the native-kernel bail optimizes `render` but costs
    +66%. Vectorization must live in the optimizing tier, so functions don't
    have to choose between tiers.
- **2026-10-01, cycle 33.**
  - liquid's gap matches the allocator finding.
  - Added the compiler-size row: 24.4 k hand-written lines today, an estimated
    28–33 k for the proposed design with two native backends.
- **2026-10-01, cycle 34.**
  - Cycle-collection cost (M36): skipping it gives lexer −12.5%, shapes −6%,
    wordfreq −5%.
  - Proposed whole-program type-graph acyclicity analysis to remove it soundly.
- **2026-10-01, cycle 35.**
  - Added the build order with measurable acceptance gates, each tied to the
    oracle or prototype that justified the step.
- **2026-10-01, cycle 36.**
  - Peak memory (M37): geometric mean 0.66× C, but 1.4–4.2× on the
    allocation-heavy workloads. Same causes and fixes as the time gaps.
- **2026-10-01, cycle 37.**
  - Where Zephyr beats C (M38): invariant-divisor magic (pi), a type-specialized
    sort, map hash tags, the AXPY kernel.
  - All four are kept in the design; matmul's 0.55× becomes the vectorizer's
    gate.
- **2026-10-01, cycle 38.**
  - Built random-program differential fuzzing (M39): 18 of 600 programs (3%)
    print different results at baseline and -O2.
  - Reduced seed 1009 to 20 lines: after `for i in 0..1 { acc = i }`, -O2 uses
    the incremented loop counter as the global's value.
  - Also found that the spec doesn't define evaluation order.
- **2026-10-01, cycle 39.**
  - Side-effect-free fuzzing: 1 mismatch in 600 programs, which reduces to the
    same loop-exit forwarding bug as seed 1009.
  - The other reduced mismatches depend on evaluation order (spec gap).
- **2026-10-01, cycle 40.**
  - Ownership-focused fuzzing (`genref.py`, 400 programs): 0 mismatches.
- **2026-10-01, cycle 41.**
  - Three-way oracle (M40) with a Python executable reference, validated
    60/60 on side-effect-free programs.
  - On 400 order-sensitive programs: baseline departs from left-to-right in
    9.75%; -O2 never departs where baseline follows it.
  - Recommended specifying left-to-right evaluation.
- **2026-10-01, cycle 42.**
  - Reduced the "all three differ" seed 230: it's order-dependent (a loop where
    `acc = acc * 1 + f0(…)` and `f0` modifies `acc`), not a new miscompile.
  - Rewrote the open-questions list (Q4–Q10).
- **2026-10-01, cycle 43.**
  - Placement experiments (M41). Most of the vectors-oracle spilling is region
    outlining (−32% as a whole function), which corrects M20/M30.
  - The original vectors is 6.3× slower in a function, because in-place
    element reuse is lost.
  - Added the placement gate and step 3b.
- **2026-10-01, cycle 45.**
  - With the lists passed as parameters, vectors is still 6× slower (M42);
    records has no cliff.
  - The cliff is in rebuilding a struct and storing it into a list element.
  - Recommended function-style variants for the benchmark suite.
- **2026-10-01, cycle 46.**
  - Wrote down the language changes the architecture needs: none in syntax,
    one spec clarification (left-to-right evaluation), and representation
    changes that programs cannot observe.
- **2026-10-01, cycle 47.**
  - Float/closure/interface fuzzing (`genext.py`, 500 programs): 0 mismatches.
  - Added the fuzzing totals table.
- **2026-10-01, cycle 48.**
  - Lifetime instrumentation in a scratch runtime (M43): 66–100% of freed
    objects in the allocation-heavy workloads die before their allocating
    frame returns. That is the upper bound for function-scope regions.
- **2026-10-01, cycle 49.**
  - wordfreq instruction profile: Zephyr's map already matches C's design
    (hash tags, 50% load).
  - Two cache-missing loads take 42% of time. Q6 remains open; next is
    counting probes per lookup.
- **2026-10-01, cycle 50.**
  - wordfreq probes: 1.06 per lookup, which rejects probing as the cause.
  - The candidates left are memory latency and per-lookup overheads (string
    building, comparison call, hashing).
- **2026-10-01, cycle 51.**
  - wordfreq solved (M44): C with Zephyr-style concatenation takes 1.135 s
    against Zephyr's 1.097 s, so the gap is string building and the map is
    fine.
  - Q6 closed.
- **2026-10-01, cycle 52.**
  - dispatch solved (M45): C with Zephyr's cell + header representation takes
    464 ms against Zephyr's 480 ms and plain C's 329 ms.
  - Q7 closed. Interface value = object pointer joins layer 4.
- **2026-10-01, cycle 53.**
  - Projection with C-representation models (M44, M45): 0.94× C geometric
    mean, and 0.885× with the vectors SoA bound.
- **2026-10-01, cycle 54.**
  - User code is ≤ 10 ms of a ~310 ms small-program build (M46). With a cached
    runtime, small builds take ~5–15 ms; step 1's gate is confirmed by
    measured parts.
- **2026-10-01, cycle 55.**
  - Extended the prototype to 11 passes (M47): 0.18–0.23 µs per value in C,
    ~0.3–0.55 µs projected for Zephyr.
  - The production estimate of 0.7–1.4 µs holds, at its low end.
- **2026-10-01, cycle 56.**
  - OpenMP versions of the C references (M48): mandel 3.94×, matmul 3.69×,
    bintrees 1.76× on 4 cores, all bit-identical.
- **2026-10-01, cycle 57.**
  - Parallel bintrees with per-thread regions: 2.7× on 4 threads (18 ms),
    against 1.76× with malloc. Confirms that regions remove the contention.
- **2026-10-01, cycle 58.**
  - Attacked the C1 verdict with correctness by construction (stencils derived
    from the interpreter). The fuzzing bugs were in lowering and an
    optimization pass, which neither design derives from the interpreter.
    Verdict unchanged.
- **2026-10-01, cycle 59.**
  - Closures is fully inlined; its gap is about half region placement.
  - Added an "At a glance" summary, since the current-best section had grown
    past a five-minute read.
- **2026-10-01, cycle 60.**
  - Map and generics fuzzing (`genmap.py`, 400 programs): 0 mismatches.
- **2026-10-01, cycle 61.**
  - Compiler lifetimes (M50): 50–66% of allocations die in their allocating
    frame, ~20% escape and ~25% live until exit.
- **2026-10-01, cycle 62.**
  - Stencil-style code quality (M51): 3.4–6.8× native, which is 2–3× better
    than an interpreter but worse than zc's current baseline.
  - Q8 closed; C3 is scoped to S7.
- **2026-10-01, cycle 63.**
  - Added the Apple Silicon section: macOS builds take 4.8 s / 2.6 s today
    (repo results), against a projected 5–15 ms.
  - Listed the macOS-specific requirements: ad-hoc code signing and MAP_JIT.
- **2026-10-01, cycle 64.**
  - Quiet re-run of the full suite: geometric mean 1.255 (the original was
    1.253).
  - Per-workload noise is up to ±10%, which is why same-session A/B
    comparisons are required.
- **2026-10-01, cycle 65.**
  - Wrote the flat IR design sketch: structure-of-arrays with an operand pool,
    three levels (semantic, representation, machine) with the interpreter on
    the semantic level, and an effects table.
  - Based on the existing 73-opcode IR, whose per-instruction `[[int]]`
    operands are a measured cost (M3).
- **2026-10-01, cycle 66.**
  - Tracing GC model (M52): best 124 ms / 19 MB on bintrees, against
    specialized RC 148–195 ms / 9.8 MB and regions 49–80 ms / 5.8 MB.
  - Rejected tracing because of the spec's memory promise and because regions
    win.
- **2026-10-01, cycle 67.**
  - Consolidated the memory-management candidates into one table.
- **2026-10-01, cycle 68.**
  - Re-timed all oracles in one session (M53); results are consistent.
  - Projection updated with the same-session values: measured-only ≈ 0.98,
    with C models ≈ 0.93.
- **2026-10-01, cycle 69.**
  - Consolidated the backend candidates into one table.
  - Deprioritized Q4 (interval splitting) on the strength of M41.
- **2026-10-01, cycle 70.**
  - Parity of all 39 repository fixtures, including the threads fixtures:
    identical at baseline and -O2 on Linux. Random fuzzing finds what the
    fixtures don't.
- **2026-10-01, cycle 71.**
  - Whole-program facts against incremental builds (M54): the worst
    realistic flip rebuilds ~308 functions in ~80–160 ms.
  - Facts become cache inputs; added a fact-flip check to step 8's gate.
- **2026-10-01, cycle 72.**
  - Consistency pass on the current-best section: same-session values (M53),
    per-thread regions, the M52 rejection, and the fuzzing evidence in layer 6.
