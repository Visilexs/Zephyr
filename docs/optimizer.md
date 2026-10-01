# The -O2 optimizer

`-O2` compiles each function through an SSA tier (`compiler/optimizer.zeph`).
Anything the tier cannot handle falls back to the baseline code generator, so
`-O2` never rejects a valid program. Without `-O2`, output is unchanged by
everything described here except the front-end inliner, which always runs.

The goal is runtime speed. Inlining, specialization and outlining are only
kept where they make the generated code faster.

## Pipeline

The driver (`compiler/zc.zeph`) runs these steps in order:

1. Parse, splice imports, and prepend the runtime, so user code, the standard
   library and the runtime form one program.
2. `setUpProfile` instruments or reads a profile (`--profile-generate` /
   `--profile-use`; see [Profiles](#profiles)).
3. Check types and monomorphise generics.
4. Run the whole-program front-end passes:
   - `foldGlobals`
   - `preserveEntryReturns`
   - `accumulatorRecursionPass`
   - `tailRecursionPass`
   - `propagateConstantArguments`
   - `splitColdTails`
   - `inlinePass`
   - `constantFoldAll`
5. Generate code. Under `-O2` each function goes through
   `tryOptimizeFunction`. A loop that lowers on its own while its function
   does not becomes an outlined `zopt_regionN`.

### SSA tier passes

`compileRegion` runs these passes in order:

1. Remove unreachable blocks and trivial phis, then fold constants.
2. Thread branches, up to 4 rounds, re-folding after each round.
3. Eliminate dead code.
4. Cancel retain/release pairs.
5. Replace scalar aggregates.
6. Optimize loops: GVN/CSE, loop-invariant code motion, bounds-check
   elimination, and sinking.
7. Fold address arithmetic, then run dead-code elimination again.
8. Check borrows: refuse any borrowed reference whose owner could be freed
   while it is still live.
9. Split critical edges and order blocks, with cold blocks last.
10. Allocate registers by linear scan.
11. Promote spilled read-only loop values into free registers.
12. Emit code. The prologue saves only the callee-saved registers the
    function actually uses.

If a region bails out, the reason is reported with `--opt-report`. A loop
region that fails with inlining on is retried once with inlining off.

### Loop-invariant list access

LICM hoists a list's length and data pointer out of a loop when two
conditions hold:

- The loop never resizes a list.
- Either the loop cannot free anything, or the list outlives the loop: it is
  a parameter, or a global the loop never stores to.

Assignments and releases of *other* references do not prevent the hoist. A
data pointer loaded from such a global also stays valid across those calls,
which the borrow check accepts.

## Inlining

There are two inliners:

- **Front end** (`inlinePass`, AST). It always runs and substitutes literal
  and scalar arguments.
- **SSA tier**. It runs while lowering a region under `-O2`. It handles known
  closures, and turns interface calls with at most 4 implementors into
  guarded dispatch.

### Pristine route

Under `-O2`, a non-runtime function that has a pre-inline body is lowered
from that body. The SSA inliner, which sees the optimized result, makes the
decisions instead of the front end. Runtime callees are inlined only inside
loops.

Recursive functions keep the front-end route, so they keep its
self-expansion. This applies to:

- functions in a recursive call-graph SCC
- functions whose front-end body contains an inlined copy of a recursive
  function

The SSA inliner also refuses to add one more level of a recursive callee at
the leaves of such an expansion when the caller is outside the callee's SCC.

### Trial ladder

The trial ladder runs when an inline was refused because of a node or depth
limit. It never runs for `runtime*` owners.

- The region is recompiled with node limits 120, 250, 500, 1000 and 2000 and
  depth limits 4, 6, 10, 16 and 32.
- A step is kept only when the **region cost estimate** is at least 3% lower
  and hot instructions stay under `min(8 × default + 200, 6000)`.
- String literals created by a rejected trial are rolled back.

The region cost estimate is computed in `emitRegionCode`. It sums, over all
blocks:

```
loopWeight × (instructions + stack-touching lines + call costs)
```

A call costs its overhead plus the callee's measured entry cost. If the
callee isn't compiled yet, its cost is the call graph's static estimate. A
callee in the same SCC counts only its own size, so the cost of recursion
can't compound.

### Call graph

`-O2 --callgraph-report` prints the call graph, built once after checking:

- SCCs found with Tarjan's algorithm
- static frequencies, computed top-down from the entry points with
  `8^loopDepth` per loop and 50/50 per branch
- per-site kind (direct, interface, closure), weight, and which arguments are
  literals

Calls that lowering adds are not in the graph, for example map lookups, list
pushes, allocation and reference counting.

### Cold code

`findColdBlocks` marks these blocks cold:

- blocks that end in a panic or are unreachable
- conditional arms that call a void user function (the error-reporting shape)
- blocks whose predecessors are all cold
- with a profile, blocks executed less than 0.1% of the time

Cold blocks are emitted after the hot body.

### Partial inlining

`splitColdTails` handles the early-exit shape
`prefix; if guard { fast; return }; slowTail`. It applies when:

- the prefix declares only effect-free scalars
- the guard has no side effects
- the hot part is at most 60 nodes and the tail at least 60

The function then becomes `prefix; if guard { fast; return }; return
f__coldTail(params)`. The tail clone is the unchanged original, so no
live-in analysis is needed, and the trimmed function now fits both inliners.

## Specialization

`propagateConstantArguments` does two things.

**Interprocedural constant propagation.** If every direct call passes the
same literal for a parameter the body never assigns, the body uses the
literal. This repeats to a fixpoint, so constants travel down call chains.

It skips:

- functions used as values
- methods
- `runtime*` helpers

**Specialization clones.** A call that passes literals for *steering*
parameters calls a clone with those literals substituted. A parameter steers
when it appears in a branch or loop condition, a range bound, a divisor, or a
shift amount, and it must also:

- never be assigned
- be passed through unchanged by every self-call

Clones are made only for callees that will not inline anyway, because they
are recursive or larger than 60 nodes. They are keyed by the vector of
literal values, at most 4 per function. A recursive call that passes the same
literals lands on the clone itself.

## Recursion

- **`accumulatorRecursionPass`** turns the single-parameter
  `f(n - a) + f(n - b)` shape into a loop plus one recursive call.
- **`tailRecursionPass`**:
  - turns every `return f(args)` outside an inner loop into parameter
    updates plus a jump back to the start of the body
  - folds `return E op f(args)` for integer `+ * & | ^` into an
    accumulator; wrapping arithmetic keeps this reassociation exact
  - requires changed parameters to be scalars; reference parameters may only
    pass through
  - leaves calls inside inner loops as calls
- **`preserveEntryReturns`** returns before frame setup when a function
  starts with a guard such as `if n < 2 { return n }`.

## Profiles

```powershell
.\zc.exe -O2 --rt --profile-generate app.zprof app.zeph app-train.exe
.\app-train.exe training-input
.\zc.exe -O2 --rt --profile-use app.zprof app.zeph app.exe
```

`--profile-generate` adds counters:

- one counter per function entry and two per `if` (one per arm)
- numbered in source order after imports expand, so the numbering is stable
  across rebuilds of the same source
- inserted as ordinary source before checking, so it works with or without
  `-O2`
- written when the program exits normally

`--profile-use` maps the counters to branch probabilities. Those
probabilities feed the region cost estimate, spill costs and cold layout.
Trials are skipped for functions the profile never entered. A profile whose
counter count doesn't match the program is ignored with a warning. Without
profile flags, output is byte-identical to a build that has no profile
support.

The profile is context-insensitive: clones and inlined copies share their
source's counters. On the benchmark suite it is currently neutral. The
consumers that would gain from it are not built yet: indirect-target and
value profiles, and outlining rare `if` arms.

## Reports

| Flag | Shows |
|---|---|
| `--opt-report` | For each function, whether it was optimized or left on baseline (with the reason), its IR values, spills, and hot+cold instructions. Also every inline (front end and SSA), constant parameters, clones, partial inlining, and loop retries. |
| `-O2 --callgraph-report` | SCCs, then every reached function, hottest first, with its outgoing sites. |
| `--opt-dump` | The SSA IR of each region. |
| `--map` | `<output>.map` with code symbol addresses, for samplers. |

## Measuring

Performance changes are judged with the compiler-battle harness, which runs
each workload in Zephyr, C (gcc) and Rust with matching checksums. There are
two suites: the main suite of 19 workloads, and the `inl_*` inlining suite of
13 workloads.

- Noise is about 2%. Treat a change as real only if it appears in a repeated
  or paired battle.
- Run battles on a quiet machine. Test gates running in parallel can shift
  timings by up to 2× even with CPU pinning; drift in the C column gives this
  away.
- Code alignment alone can move a small recursive kernel such as fib by about
  ±10%.

Measured effects of the passes above:

| change | effect |
|---|---|
| trial ladder + pristine route | inl_branchy −54%, inl_constchain −46%, inl_repeat −17%, inl_chain −6%; main suite flat |
| cold layout + pristine route | inl_hotcold −31% |
| partial inlining | inl_bigcold about −28% |
| specialization clones | inl_specialize about −18% |
| tail recursion | inl_recursive's `sumScaled` about −7% |
| list access hoisting | vectors −9% |
| two-digit integer formatting | strbuild −11% |

## Known gaps

- **Register allocation.** Linear scan without live-range splitting, and no
  shrink-wrapping of callee-saved saves. Large loop bodies spill:
  - closures: 39 spill slots
  - liquid: 15
  - records: 11
- **Structs.** Struct values are boxed on the heap. Small-struct temporaries
  (vectors) and record arrays (records) pay for that indirection.
- **Map updates.** `m[k] = m.get(k).or(0) + 1` hashes and probes twice.
- **Vector width.** Vector kernels use AVX2 (`ymm`), not AVX-512.
- **Rare branches.** Partial inlining does not handle a rare `if` arm with
  code after it, which would need live-outs.
- **Recursion.** No base-case range threading, and no unroll budgets per SCC.
