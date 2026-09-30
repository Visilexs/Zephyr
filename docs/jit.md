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
  - A returned or inline-result owned local moves its count.
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
- cancelling of retain/release pairs around a single use
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
- loop headers aligned to 16 bytes; 8-bit immediates use the short encoding.

## Gates (all must pass before a commit)

- `tests/optimizer_parity.ps1 -Compiler .\zc_new.exe`: the 29 programs must
  produce identical output with and without `-O2`.
- The full suites (`tests/run_tests.ps1`, 201 tests, and `std_tests.ps1`, 40
  tests), run with a compiler variant whose default is `optimizerEnabled =
  true`.
- A compiler built with `-O2` must rebuild itself to a byte-identical fixpoint.
- The baseline corpus (no `-O2`) must stay byte-identical unless a runtime
  change is intended.

The runtime side (compiler/runtime.zeph, embedded by `scripts/embed-gen.ps1`):
size-class free lists hand small blocks back inline on release and
allocation, and a live map slot's state word holds `(hash << 1) | 1`, so
probes skip foreign keys without dereferencing them and a rehash never
rehashes.

## Measurements (2026-09-30)

Best of 3, in ms, from `bench/run_suite.ps1 3` on the dev machine (Windows 11).

| area | baseline | -O2 | C | Rust | -O2/C |
|---|---:|---:|---:|---:|---:|
| recursion (fib) | 20 | 11 | 10 | 20 | 1.10 |
| integer SIMD | 39 | 38 | 72 | 69 | 0.53 |
| float compute | 98 | 93 | 89 | 91 | 1.04 |
| sorting | 87 | 83 | 296 | 43 | 0.28 |
| alloc / GC | 122 | 95 | 171 | 155 | 0.56 |
| hash map | 42 | 36 | 30 | 70 | 1.20 |
| rasterization | 7 | 7 | 9 | 10 | 0.78 |
| bignum | 56 | 56 | 85 | 92 | 0.66 |
| fluid / neighbours | 2893 | 2471 | 2242 | 2510 | 1.10 |
| dynamic dispatch | 300 | 168 | 157 | 164 | 1.07 |
| closures / HOFs | 207 | 124 | 102 | 40 | 1.22 |
| string hash map | 230 | 98 | 68 | 97 | 1.44 |
| struct floats | 483 | 165 | 151 | 151 | 1.09 |
| tokenizer | 357 | 188 | 120 | 104 | 1.57 |
| small structs (vectors) | 677 | 104 | 69 | 90 | 1.51 |

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
