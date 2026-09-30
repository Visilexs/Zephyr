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
- jump threading
- straight-block merging
- DCE
- cancelling of retain/release pairs around a single use

**Loops:**

- Dominators.
- GVN with memory epochs: list, field and global loads are reused until a
  store or freeing call, with store-to-load forwarding for globals. String
  bytes count as immutable.
- LICM: loads that the loop itself cannot change are hoisted per loop.
- GVN runs again after hoisting.
- Bounds-check elimination from a non-negative fixpoint plus dominating
  compares.
- `x % 2^k` and `x / 2^k` on non-negative x become a mask or shift.
- Code sinking to the lowest dominator of a value's uses.

**Backend:**

- critical-edge splitting;
- linear scan over live ranges with holes, with phi coalescing and spill costs
  weighted by loop depth;
- register promotion of spilled values that a loop only reads;
- `lea` peepholes, fused compare-and-branch, and forwarder-block skipping;
- loop headers aligned to 16 bytes.

## Gates (all must pass before a commit)

- `tests/optimizer_parity.ps1 -Compiler .\zc_new.exe`: the 29 programs must
  produce identical output with and without `-O2`.
- The full suites (`tests/run_tests.ps1`, 201 tests, and `std_tests.ps1`, 40
  tests), run with a compiler variant whose default is `optimizerEnabled =
  true`.
- A compiler built with `-O2` must rebuild itself to a byte-identical fixpoint.
- The baseline corpus (no `-O2`) must stay byte-identical unless a runtime
  change is intended.

## Measurements (2026-09-30)

Best of 3, in ms, from `bench/run_suite.ps1 3` on the dev machine (Windows 11).

| area | baseline | -O2 | C | Rust | -O2/C |
|---|---:|---:|---:|---:|---:|
| recursion (fib) | 20 | 12 | 10 | 20 | 1.20 |
| integer SIMD | 39 | 38 | 72 | 69 | 0.53 |
| float compute | 97 | 93 | 88 | 91 | 1.06 |
| sorting | 86 | 91 | 297 | 43 | 0.31 |
| alloc / GC | 130 | 104 | 171 | 154 | 0.61 |
| hash map | 35 | 31 | 30 | 68 | 1.03 |
| rasterization | 7 | 7 | 9 | 10 | 0.78 |
| bignum | 57 | 56 | 85 | 92 | 0.66 |
| fluid / neighbours | 2840 | 2500 | 2250 | 2506 | 1.11 |
| dynamic dispatch | 301 | 175 | 158 | 154 | 1.11 |
| closures / HOFs | 202 | 126 | 102 | 40 | 1.24 |
| string hash map | 245 | 124 | 68 | 95 | 1.82 |
| struct floats | 481 | 166 | 150 | 152 | 1.11 |
| tokenizer | 360 | 201 | 120 | 104 | 1.68 |

## Known limits and next steps

- **No live-range splitting.** A group keeps one register or one slot for its
  whole life, and promotion only helps loops that have a free register. Dense
  inlined regions (the closures driver loop) still spill.
- **Where the remaining gaps come from.** The string map and the tokenizer
  spend their time in the runtime: FNV byte hashing, 24-byte map slots, and
  allocating substrings and tokens. The next wins there are runtime changes: a
  word-at-a-time hash, a hash cached in the slot, and an inline small-object
  allocation fast path.
- **Unlowered constructs.** Reference assignment to globals ("fresh value into
  a borrowed variable") and packed `[byte]` lists fall back to the baseline.
- **Phases not yet started.** Tier-up inside `zc run`, speculation and
  deoptimization, SIMD in the tier, and a code cache with PGO.
