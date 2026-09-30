# The optimizing tier

`zc -O2` (and `zc run -O2`) routes every function and outlined loop that it can
lower through an SSA optimizer in `compiler/optimizer.zeph`. Anything the tier
cannot lower falls back to the baseline code generator. The fallback is per
function first, and per outermost loop when the whole function fails. So `-O2`
never rejects a program the baseline accepts. `--opt-report` prints each
decision and the reason for any bail. `--map` writes `<exe>.map` (RVA and
symbol) for profiling.

## Pipeline

**Lowering** (AST to SSA, Braun et al. construction):

- Calls:
  - small user functions are inlined (at most 60 AST nodes, depth 3, not
    recursive);
  - a single-return predicate is inlined straight into its branch;
  - a callee handed a closure literal is inlined with a budget of 300 nodes,
    and calls through that closure then inline the closure body, with its
    captures bound to their SSA values;
  - interface calls are devirtualized through guards, for up to 4 vtables;
  - small runtime helpers are inlined like user functions.
- Closures:
  - closure bodies compile in the tier, with the env as the deepest stack
    argument;
  - closure literals and function values are lowered.
- Maps: `m[k]`, `m[k] = v`, and a fused `m[k] = m.get(k).or(d) ± x` that
  probes once.
- Reference counting: fresh values are pending temporaries, and owned locals
  are chosen by a fixpoint.
  - A returned or inline-result owned local moves its count. So does any
    owned local at its last mention in a block, when that mention is single
    and on the statement's straight-line path (no branch, loop, closure or
    inlined body around it).
  - A plain-struct local whose last use is the source of a list element
    store is released before the store, so the element it came from can be
    overwritten in place (a uniquely held element of the same shape gets its
    fields rewritten instead of a new allocation).
  - Borrowed values are pinned only when later code may free. An
    interprocedural may-free summary covers user calls and every
    implementation behind an interface call.

**Cleanup:**

- unreachable-block removal
- trivial phi removal
- constant folding, including canonical compares and `x cmp x`
- `lo <= x and x <= hi` fused into one unsigned compare, `(x - lo) <=u (hi - lo)`
- jump threading
- straight-block merging
- DCE
- cancelling of retain/release pairs around a single use, and of
  `release(retain(v))` in one block with no freeing call between
- scalar replacement: a struct with no reference fields whose value is only
  read field by field, counted and released never touches memory; its loads
  become the values stored at creation. Such structs are also allocated with
  descriptor 0, so releasing one skips the shape walk.

**Loops:**

- Dominators.
- GVN with memory epochs: list, field and global loads are reused until a
  store or freeing call, with store-to-load forwarding for globals. String
  bytes count as immutable.
- LICM: loads that the loop itself cannot change are hoisted per loop.
- GVN runs again after hoisting. List lengths and data pointers have their own
  epoch: element stores don't invalidate them, only calls and raw stores do.
- Bounds-check elimination from a non-negative fixpoint plus dominating
  compares against the length, or against a `min()` of it.
- `x % 2^k` and `x / 2^k` on non-negative x become a mask or shift.
- Code sinking to the lowest dominator of a value's uses.

**Backend:**

- critical-edge splitting;
- linear scan over live ranges with holes, with phi coalescing; eviction
  compares loop-weighted uses per live position;
- 11 integer registers: r11 is allocatable except across an invariant
  division, which uses it as scratch;
- register promotion of spilled values that a loop only reads;
- `load64(a + b + c)` and friends use the addressing mode `[a + b + c]`;
  a single-use float load feeds its reader as a memory operand; constant
  stores use immediates;
- loop rotation: a back edge to a header holding only phis and a compare
  repeats the compare instead of jumping back;
- `lea` peepholes, fused compare-and-branch, and forwarder-block skipping;
- loop headers aligned to 16 bytes; 8-bit immediates use the short encoding;
- retains are inlined (a heap-range check and an increment) and no longer
  count as calls for register allocation; releases decrement inline and call
  the runtime only when the count would reach zero.

## Gates (all must pass before a commit)

- `tests/optimizer_parity.ps1 -Compiler .\zc_new.exe`: the 32 programs must
  produce identical output with and without `-O2`.
- The full suites (`tests/run_tests.ps1`, 201 tests, and `std_tests.ps1`, 40
  tests), run with a compiler variant whose default is `optimizerEnabled =
  true`.
- A compiler built with `-O2` must rebuild itself to a byte-identical fixpoint.
- That compiler, copied alone into an empty directory, must compile and run a
  program from its embedded runtime (the fixpoint never exercises it, because
  a runtime.zeph sits beside the compiler in the repo).
- The baseline corpus (no `-O2`) must stay byte-identical unless a runtime
  change is intended.

The runtime side (compiler/runtime.zeph, embedded by `scripts/embed-gen.ps1`):
size-class free lists hand small blocks back inline on release and
allocation, and a live map slot's state word holds `(hash << 1) | 1`, so
probes skip foreign keys without dereferencing them and a rehash never
rehashes.

## Measurements (2026-09-30, commit b44b77a)

From `python bench/bench.py run`: the median of 10 runs in ms, pinned to one CPU at high
priority, on a Ryzen 7 9800X3D (Windows 11). Every workload is sized so the fastest
language takes at least ~250 ms. Run-to-run spread (median absolute deviation) is
under 1% except the string hash map baseline (1.2%). Peak memory is peak committed
memory for the whole process tree.

| area | baseline | -O2 | C | Rust | -O2/C | -O2 MB | C MB |
|---|---:|---:|---:|---:|---:|---:|---:|
| recursion (fib) | 787 | 378 | 295 | 732 | 1.28 | 8.7 | 0.6 |
| integer SIMD | 185 | 183 | 342 | 326 | 0.54 | 53.3 | 28.4 |
| float compute | 336 | 304 | 304 | 312 | 1.00 | 8.7 | 0.6 |
| sorting | 170 | 128 | 592 | 84 | 0.22 | 56.8 | 46.5 |
| alloc / GC | 259 | 190 | 348 | 302 | 0.55 | 8.7 | 0.6 |
| hash map | 329 | 244 | 289 | 836 | 0.85 | 85.6 | 34.7 |
| rasterization | 187 | 177 | 268 | 290 | 0.66 | 8.7 | 0.7 |
| bignum | 210 | 204 | 325 | 352 | 0.63 | 8.7 | 0.7 |
| fluid / neighbours | 672 | 594 | 531 | 591 | 1.12 | 8.7 | 1.4 |
| dynamic dispatch | 596 | 323 | 374 | 368 | 0.87 | 419.2 | 94.5 |
| closures / HOFs | 558 | 329 | 341 | 113 | 0.97 | 65.5 | 18.3 |
| string hash map | 985 | 363 | 276 | 398 | 1.31 | 33.0 | 14.4 |
| struct floats | 957 | 324 | 296 | 298 | 1.09 | 8.7 | 0.7 |
| tokenizer | 913 | 473 | 305 | 268 | 1.55 | 520.7 | 162.7 |
| small structs (vectors) | 16491 | 409 | 266 | 239 | 1.54 | 8.7 | 0.8 |
| megamorphic dispatch | 368 | 243 | 238 | 215 | 1.02 | 179.4 | 41.2 |
| struct records | 1142 | 567 | 429 | 433 | 1.32 | 203.8 | 61.8 |
| string building | 774 | 360 | 313 | 263 | 1.15 | 8.7 | 0.7 |
| binary trees | 627 | 300 | 355 | 388 | 0.85 | 41.1 | 9.7 |

The last four rows target known gaps in the tier: dispatch past the 4-vtable
guard, lists of boxed structs, per-substring allocation, and allocation-heavy
recursion. 8.7 MB is the runtime's initial heap reservation.

**Compile-time scaling** (`python bench/bench.py compile`): 200 generated call
chains, each 200 functions deep (40,000 functions), in µs per function, median of 3.

| | check | object / `.s` | build | optimized build |
|---|---:|---:|---:|---:|
| Zephyr | - | 63 | 73 | 251 (-O2) |
| C (gcc) | 5 | 326 | 334 | 88 |
| C++ (g++) | 12 | 354 | 361 | 95 |
| Rust | 59 | 107 | 109 | 206 |
| C# (csc) | - | - | 120 | 112 |
| Java (javac, 114x114) | - | - | 54 | - |

The -O2 build costs 3.5x the baseline on this input. zc compiles itself in 937 ms
(baseline) and 2727 ms (-O2), with a peak of 468 MB and 936 MB respectively. Both
figures are for zc_new.exe, which is not itself built with -O2.

## Known limits and next steps

- **No live-range splitting.** A group keeps one register or one slot for its
  whole life, and promotion only helps loops that have a free register. Dense
  inlined regions (the closures driver loop) still spill.
- **Where the remaining gaps come from.** The C tokenizer slices its source
  and the C word counter builds words in a stack buffer; Zephyr allocates a
  string per token or word. Int maps use 24-byte slots (state, key, value)
  where C uses 16, so the table is 1.5x bigger and misses more.
- **Unlowered constructs.** Reference assignment to globals ("fresh value into
  a borrowed variable") and packed `[byte]` lists fall back to the baseline.
- **Phases not yet started.** Tier-up inside `zc run`, speculation and
  deoptimization, SIMD in the tier, and a code cache with PGO.
