# Region inlining: design

Status: proposal, nothing implemented. Goal: maximize generated-code speed,
treating source functions as optional boundaries. More inlining is only a
means. Every phase is accepted or rejected by `compiler-battle` runtime
numbers. Fewer calls or smaller IR do not count as evidence.

## 1. What exists today

Pipeline (zc.zeph driver, ~19420): parse → imports → runtime prepended into
one program → check (monomorphises generics) → foldGlobals →
preserveEntryReturns → accumulatorRecursionPass → **inlinePass** →
constantFoldAll → generateProgram. Each function then goes through
`tryOptimizeFunction` (-O2), which falls back to baseline. Loops that lower
on their own become `zopt_regionN`.

### Two independent inliners

| | AST `inlinePass` (zc.zeph:6847) | SSA inliner (optimizer.zeph:2440) |
|---|---|---|
| when | always, also without -O2 | while lowering a region under -O2 |
| size gate | callee ≤ 128 AST nodes | callee ≤ 60 nodes (300 with a closure argument) |
| depth | `call.integerValue >= 4` stops; 4 rounds | `inlineStack ≥ 3`, no self-recursion |
| budget | caller slotCount ≤ 600 | region ≤ 16000 IR values (24000 hard limit) |
| benefit model | none | none |
| order safety | `tryChild` pure-prefix walk | lowering order |
| extras | literal/scalar argument substitution | known-closure inlining, guarded devirtualization over ≤4 implementors |

`tryOptimizeFunction` (optimizer.zeph:7106) coordinates the two with a retry
ladder. It tries the pre-inline body, then the inlined body, then retries
with inlining off, then retries the pre-inline body if the region is too
large. A failed attempt is only a fallback, never re-weighed for profit.

### SSA tier passes

`compileRegion`, 7059, in order:

1. Fold constants to a fixpoint (at most 8 rounds; SCCP-like).
2. Thread branches (at most 4 rounds).
3. Dead-code elimination.
4. Retain/release pair cancellation.
5. Scalar replacement of aggregates.
6. Loop optimizations (GVN/CSE, LICM, bounds-check elimination, sinking).
7. Address folding.
8. Register allocation by linear scan with **no live-range splitting**.
9. Prologue that saves **every** used callee-saved register at entry, with
   no shrink-wrapping.

### Whole-program visibility

User code, the standard library and the runtime are one `functionDefinitions`
list. `extern fn` / `__xresolve` / `win()` are the only foreign edges.
Function-value escapes are known (`referenceCountScanAddress`).

### Frequency information

- Static: loop depth only (`loopWeight = 8^depth`), used only by the
  register allocator.
- Panic and bounds-check stubs are cold *text* (`emitCold`), but not cold
  blocks.
- Dynamic: the macOS ARM64 JIT counts calls per function to choose its tier.
  There is no branch, edge, value or indirect-target profile, no OSR, no
  deoptimization, and no profile input to AOT builds. Windows x86 has no JIT.

### Missing entirely

- call graph
- SCCs
- caller lists
- per-site frequencies
- callee summaries
- value specialization (only type specialization for generics)
- cold outlining
- interprocedural constant propagation

## 2. Measured situation

- **Coverage is not the bottleneck.** `--opt-report` over the 19 battle
  workloads shows 3,500+ functions optimized and 2 left on baseline.
- **The gaps are in the decisions and in what happens after inlining.**

Main-suite losses against gcc -O2 and what the autopsies blame:

| workload | vs C | cause seen | inlining-related lever |
|---|---:|---|---|
| lexer | 1.51 | refcounting 12%, substring helper, spills | partial inlining of runtime helpers, region-level retain/release cancellation |
| vectors | 1.50 | each `Vec3` temporary is heap-allocated (the hot-loop "calls" are allocation and panic stubs) | allocation elimination once helpers are inlined; scalar replacement through stores |
| records | 1.37 | 11 spills in the hot loop | register-allocator splitting (bigger regions make this worse) |
| wordfreq | 1.29 | 65% in `runtimeFindMapEntry` → generic map lookup | specialize on key type, inline the probe fast path |
| fib | 1.28 | loop shape after 4-deep self-inlining | recursion handling, base-case threading (below) |
| strbuild | 1.17 | 30% in `runtimeAppendStringBuilderInteger` | partial inlining (capacity check hot, growth cold) |

### Lessons from the fib investigation (2026-10-01)

These constrain the design directly.

- **Unrolling until the call count matched gcc did not help.** At 8 levels
  Zephyr made exactly as many calls as gcc (93.9M) and was no faster. Extra
  depth turned into spills of the outer levels' values.
- **gcc's own two variants differ by 37% with identical call counts.**
  `-O2` runs in 180 ms; `-fno-tree-loop-optimize` runs in 131 ms. The deciding
  factor was the shape of the code after inlining: it threads the base case
  (stops at n ∈ {1,2} and adds a constant) and uses one branch per
  iteration.
- **Code alignment alone moves Zephyr's fib by ±10%.** Single runs and
  harness microbenchmarks mislead, so judge every change on the battle
  across layouts.

**Conclusion:** the model has to evaluate the *optimized result* of an
expansion, including register pressure. A pre-expansion size heuristic is
not enough.

## 3. Architectural limitations to remove

1. **Two inliners with conflicting fixed limits.** Neither one knows what
   the other did. Depth caps of 4 and 3 are arbitrary, so a 40-level chain
   of tiny functions cannot collapse today.
2. **Decisions come before optimization and never look at its result.** Only
   one constant fold runs after all AST rounds. The SSA inliner does not
   re-decide after folding.
3. **No frequency information.** Cold and hot call sites are treated alike.
   Nothing directs the budget toward hot paths.
4. **Functions are indivisible.** A function with a 5-line fast path and a
   150-line slow path is either fully inlined or not at all.
5. **No value specialization.**
6. **The back end penalizes large regions.**
   - Without live-range splitting, a value live across a large region keeps
     one home for its whole life.
   - Callee-saved registers are saved at entry even when only a cold path
     needs them.
   - Cold blocks are laid out among hot ones.
7. **No profile input**, and no speculation beyond guarded vtable dispatch.

## 4. Proposed architecture

```
          ┌──────────── whole-program analysis (once) ────────────┐
          │ call graph · SCCs · static/profile frequencies ·      │
          │ callee summaries · constant-argument lattice          │
          └──────────────────────────┬────────────────────────────┘
                                     │
 per function, hot first:            ▼
   decision tree D (empty) ─▶ lower(f, D) ─▶ optimize ─▶ estimate cost C(D)
            ▲                                                │
            └──── pick best remaining call site, extend D ◀──┘
                  accept only if C(D') < C(D) - margin and within budget
```

### 4.1 One decision authority

- Under -O2, the AST `inlinePass` stops making profitability decisions. It
  keeps only trivially profitable expansions: leaf callees of ≤ 16 nodes, so
  that baseline-only paths do not regress.
- The optimizer lowers pre-inline bodies (`preInlineBodies` already exists).
- The SSA inliner stops applying fixed limits (`inlineStack ≥ 3`, 60 nodes).
  Instead it follows an **inline decision tree**: a set of call-site paths
  such as `A → site 3 (B) → site 1 (D)`, where a site is a pre-order index of
  calls in that function's pristine body.
- Lowering with a given tree is deterministic, so a region can be re-lowered
  as the tree grows. `tryOptimizeFunction` already re-lowers several times,
  so this changes no code structure.
- Without -O2, the AST inliner stays exactly as it is.

### 4.2 Whole-program call graph (new `callgraph` section of optimizer.zeph)

Built once after `check`, from AST call nodes.

**Nodes (one per function):**
- pristine AST node count
- **summary**:
  - optimized IR size
  - estimated machine bytes, split into hot and cold
  - estimated cost per invocation
  - register pressure: peak live GP and XMM values
  - number of values live across calls
- flags: may-free, touches-globals, recursive

**Edges (one per call site):**
- kind: direct, interface (implementor set, as used by
  `lowerGuardedDispatch`), or closure (function literals reaching the
  parameter, flow-insensitive)
- static frequency
- argument lattice per position: constant, known type, or unknown

**Analyses:**
- **SCCs:** Tarjan. Self-loops and mutual recursion are explicit.
- **Frequencies:**
  - Top-down from the entry points (`zephyrMain`, test runner).
  - Call-site weight is block frequency × caller frequency.
  - Block frequency is `8^loopDepth`, halved per non-loop branch arm, and
    ≈0 on panic, bounds-fail, `runtimeFail`, and calls into
    functions-that-never-return.
  - Within an SCC, the recursion multiplier is capped.
  - A profile replaces all of this when present (§4.9).
- **Summaries:** computed bottom-up in reverse topological order of SCCs, by
  lowering and optimizing each function standalone. That is the existing
  path with code emission turned off.
- **Constant sensitivity:** for each parameter, the summary also records how
  many IR values and how many dead blocks a constant there would remove,
  found by forward dataflow over the callee's optimized IR. A call site with
  constant arguments therefore knows its expected post-inline size before
  any trial.

### 4.3 Profitability

The objective is a static estimate of execution cost. Size is only a
budget. For a region R:

```
cost(R) = Σ_blocks freq(b) · Σ_instructions c(i)
        + Σ_remaining calls freq(s) · (callOverhead + calleeCost(s))
        + spillPenalty · Σ freq-weighted spill loads and stores      (after real regalloc)
        + prologuePenalty · saved callee-saved registers · entryFreq
```

`c(i)` is a per-opcode latency/throughput weight, calibrated against the
battle suite.

Accept extending decision tree D with site s when:

```
cost(R_D) − cost(R_D+s) > margin(freq)    and
hotBytes(R_D+s) − hotBytes(R_D) ≤ budgetLeft(R)    and
compile work for R ≤ compileBudget
```

- **The benefit is measured on the result, not modelled.** `R_D+s` is lowered
  and run through the whole pipeline, register allocation included. Any
  constant folding, branch folding, devirtualization, scalar replacement or
  allocation elimination the expansion exposes shows up as lower cost.
  Extra spills show up as higher cost, which is exactly the fib failure.
  "Secondary optimizations enabled" is therefore not a heuristic term.
- **Summaries keep this affordable.** A summary-predicted score ranks the
  candidates, and only the top K per round get a real trial lowering
  (K ≈ 4).
- **Termination.** There is no depth limit. Expansion stops when no
  candidate improves cost. A finite global budget guarantees termination:
  hot-byte growth per region, total program growth, and trials per function.
- **Hot bytes, not total bytes, are charged against the I-cache budget.**
  Cold blocks are laid out away from hot code (§4.5), so inlining code that
  stays cold is nearly free.
- **Global order.** Functions are processed hottest first. A callee that has
  been inlined into all of its callers and has no address taken is deleted.
  That shrinks the program and makes inlining into hot callers cheaper.

### 4.4 Iterative region optimization

The loop in the diagram *is* the iteration. Each round:

1. Lower the function with decision tree D and run the full pass pipeline.
2. Collect the call sites that remain *after* optimization. Some calls have
   vanished (dead branches); some are new (devirtualized, or callees of
   inlined code).
3. Re-score them using the post-optimization argument values. A constant
   that appeared through folding upgrades a site, which is the "B shrank from
   100 to 15 instructions" case.
4. Trial the top K candidates and accept the best.

To make the trials cheaper:
- Add an outer fixpoint around fold → thread → DCE → GVN, which today run
  once or a bounded number of times, while the region keeps shrinking.
- Cache lowering per decision-tree prefix when trial cost starts to dominate.

### 4.5 Hot/cold splitting and partial inlining

Three layers, cheapest first:

1. **Cold block layout.** In `emitRegionCode`, order blocks by frequency
   instead of plain reverse post-order: cold blocks (panic, error-call,
   rarely-taken arms) go after the hot code, in the existing
   `optimizerColdLines` area. Calls in cold blocks are never inlining
   candidates.
2. **Shrink-wrapped callee-saved registers.** Save a callee-saved register
   only on the paths that use it. The `callOnly` comment in zc.zeph:6851
   already names this as the missing piece.
   - **Splitting.** Split live ranges at loop and region boundaries and
     around cold calls, so values used only in cold code stop taking hot
     registers.
   - **Why this comes first.** Without these two changes, larger regions get
     slower, as fib at depth 8 showed.
3. **Partial inlining via cold outlining.** This is an AST pass before
   lowering. A callee qualifies when it has a cheap hot part and a cold
   remainder, in one of two shapes:
   - an early-exit guard: `if cond { fast; return }` followed by a slow tail
   - a rare branch: `if rareCond { big block }`
   
   The cold part moves into a synthesized `foo__cold` function, and the
   hot remainder becomes inlinable at full depth.
   - **Live-ins** become parameters. Scalars pass by value; references pass
     borrowed, using the existing convention.
   - **Live-outs**, in v1, are allowed only when the cold part ends the
     function (it returns or panics). This covers `runtimeAppendStringBuilder*`
     (capacity growth), map lookups (resize and collision tails), and
     validation and error paths.
   - **Coldness** comes from summary frequencies or a profile; without a
     profile, from structural rules (the branch reaches `runtimeFail` or a
     panic, writes only to an error global, or is a slow fallback reached
     only after a failed fast check).

### 4.6 Hot-path regions ("superfunctions")

Once partial inlining and cold layout exist, a dominant chain A → B → D
needs no new mechanism:

- the A→B and B→D sites score high, so B and D inline along the hot path
- the B→E and A→C sites stay calls in cold blocks
- cold parts of A, B and D are outlined

The resulting region is the superfunction.

Two things still need new infrastructure:
- **Trace regions across loop back-edges in different functions**, such as a
  hot loop in A whose body is mostly D. These need region outlining of an
  entire path, a generalization of `zopt_regionN`.
- **Guarded speculation on path dominance.** This needs profile data (§4.9)
  and a fallback, which AOT gets by keeping the generic call in the cold
  block.

### 4.7 Function specialization

- **Key:** function plus constant-argument vector (and, later, a
  dominant-type vector). The mechanism reuses generic instantiation's
  clone-and-cache (zc.zeph:3655): `cloneNode` the pristine body, substitute
  the constants, and give it a new `FunctionDefinition`.
- **When to clone instead of inline:** when the callee's
  constant-sensitivity summary predicts at least a 30% reduction and the
  specialized body still does not pay to inline. Typical cases are many call
  sites, a large body, or recursion.
- **Explosion control:**
  - at most N clones per function (N = 4)
  - only for sites above a frequency threshold
  - clones are charged against program-growth budgets
  - recursion keeps the key: `f(x, 7)` calling `f(y, 7)` reuses the clone,
    so recursive specialization terminates
- **Interprocedural constant propagation** comes with it: when every caller
  passes the same constant, specialize in place without cloning.

### 4.8 Recursion

- **SCC-aware expansion.** A site whose callee is in the caller's SCC is a
  candidate like any other, but each expansion along a path consumes a
  per-SCC unroll budget, so termination is guaranteed. The budget is about
  8 expansions per path at most, and the cost model usually stops earlier.
  There is no fixed depth.
- **Generalized tail recursion.** `accumulatorRecursionPass` covers one
  shape. It needs general tail-call elimination (self tail call → parameter
  update plus jump, any arity, any types), and accumulation for associative
  operators beyond `+`.
- **Base-case threading.** This is the fib lesson. After a recursive callee
  is unrolled into its own loop, the loop condition already implies the
  inlined base-case guard: inside `while n ≥ 2`, the guard `n − 1 < 2` holds
  only when n = 2. Jump threading over correlated integer conditions lets
  the loop exit straight to the constant result.
  - This is a general SSA pass (range-based branch threading) that also helps
    non-recursive code.
- **Mutual recursion.** Inline the non-recursive members of the SCC, which
  leaves one self-recursive function. Then apply the above.
- **Partial unrolling of non-tail recursion.** This is what bounded
  expansion produces. Accept it only if the measured cost improves, since
  fib showed it often does not.

### 4.9 Profile-guided decisions (AOT first, no JIT needed)

- **`--profile-generate`:**
  - instruments block or edge counters (32/64-bit counters per IR block in a
    global table)
  - records the observed targets (top 4) of indirect and interface calls
  - samples argument values on sites whose callee summary says a constant
    would pay
  - writes `program.zprof` at exit
- **`--profile-use program.zprof`:** loads the profile keyed by function and
  call-site path (stable across rebuilds of the same source; mismatched keys
  are ignored). The profile then replaces static frequencies, provides
  branch probabilities for cold/hot classification, supplies speculative
  targets for guarded devirtualization (already implemented for vtables),
  and drives value specialization with a guard.
- **Higher confidence widens the budgets.** A site with ≥ 99% dominance
  gets the hot-path budget of §4.6.

### 4.10 Adaptive and JIT integration (future; macOS ARM64 only today)

The decision-tree interface is tier-agnostic. A JIT recompilation can pass
the same planner a live profile instead of a `.zprof` file. To go beyond
AOT it needs:

- frame-state maps at guard points, for deoptimization to the baseline tier
- OSR entry for long-running loops
- dependency tracking, so a function is recompiled when a speculated
  invariant breaks (e.g. a new interface implementor or closure target
  appears)

With those, it can do:
- speculative inlining of a dominant indirect target without keeping a
  generic fallback inline
- value speculation
- trace-shaped regions

None of this is required by the AOT phases. The AOT design keeps generic
fallbacks in cold blocks instead of deoptimizing.

## 5. Phases

Each phase ships alone. Its gate: the inlining suite and the main suite with
checksums OK, no workload slower beyond 2% across two battle runs,
`scripts/selfbuild.ps1` fixpoint, and every `tests\*.ps1` passing.

| phase | content | needs |
|---|---|---|
| P0 | inlining benchmark suite (in progress); `--opt-report` lists inline decisions with per-function code bytes | none |
| P1 | call graph, SCCs, static frequencies, callee summaries; report only, no behavior change | none |
| P2 | single decision authority: SSA inliner driven by the decision tree; summary-ranked candidates; trial lowering judged by the estimated cost; fixed depth and size caps removed; outer fixpoint of the existing passes | P1 |
| P3 | frequency-ordered cold block layout; shrink-wrapped callee-saved saves; live-range splitting around cold calls and loops | none (P1 helps); prerequisite for very deep regions |
| P4 | partial inlining via AST cold outlining (guard and rare-branch shapes) | P1, P3 |
| P5 | constant-argument specialization and interprocedural constant propagation | P1, P2 |
| P6 | recursion: SCC budgets, general tail-call elimination, range-based branch threading (base case) | P2 |
| P7 | AOT PGO: `--profile-generate` / `--profile-use`, indirect-target and value profiles | P1 |
| later | JIT speculation, deoptimization, OSR, trace regions | macOS JIT; frame-state maps |

### Status of P0 and P1 (2026-10-01)

Both are done and report-only. All 31 workloads produce byte-identical
assembly, with and without -O2 and with and without the report flags.

**`--opt-report` (P0)** gains three things:
- `opt: front-end inlined into F: g, h x3`, one line per caller.
- `opt: inlined into F: ...`, for the SSA inliner on the attempt that
  compiled.
- `N+M instructions` (hot + cold) on every `optimized` line.

**`-O2 --callgraph-report` (P1)** prints:
- a summary: node, site and SCC counts
- the recursive SCCs
- every reached function, hottest first, with its static frequency, AST
  size, compiled stats (IR values, spills, instructions) and outgoing
  sites (kind, weight, literal-argument positions)

What P1 showed:
- **inl_chain:** `run` front-end inlines step0..3. The SSA tier then inlines
  step4, step8 and step12, each pre-expanded four levels deep. Every step
  from step16 on stays a call, so the fixed depth caps cut the chain at
  about 16 levels.
- **Calls the lowering adds are missing.** Map lookup, list push,
  allocation and reference counting are not AST calls, so they are not in
  the graph. wordfreq's hot `runtimeFindMapEntry` is invisible, and about
  177 runtime functions show as unreached. **P2 needs these edges:** map
  each builtin call kind to the runtime functions it lowers to.
- **Static frequencies split every `if` 50/50.** The 99.8% A→B→D path in
  inl_superpath shows up as 0.5/0.5. Only P7 profiles fix this.

**P2 versus P3:** P3 is listed after P2 but may need to land first. If P2's
measurements show larger regions losing to spills, P3 goes first. The cost
model will report that directly as spill-penalty growth.

### Status of P2 (2026-10-01)

Shipped as trial inlining, not the full decision tree. The pieces:
- **Region cost estimate.** In `emitRegionCode`, Σ over blocks of loopWeight
  × (instructions + stack-touching lines + call costs). A call costs its
  overhead plus the callee's measured `functionEntryCosts`. If the callee
  isn't compiled yet, its cost is the call graph's transitive static cost.
  Same-SCC callees count only their own size, so recursion can't compound.
- **Trial ladder.** This runs only when a region refused an inline on a
  limit, and never for `runtime*` owners. It recompiles the region with
  node limits 120/250/500/1000/2000 and depth limits 4/6/10/16/32. A step is
  kept when it is ≥3% cheaper and its hot instructions stay under
  min(8×default+200, 6000). `dataStringLiterals` rolls back before each
  trial, so rejected trials don't bloat the binary.
- **Pristine route.** Non-runtime functions with a pre-inline body lower
  from it. The SSA inliner, not the front end, then decides. Runtime callees
  are inlined only inside loops. This fixed inl_hotcold, where the front end
  had mass-inlined `reportError`.

Paired battle (two interleaved rounds, pre-P0 vs P2):

| workload | change |
|---|---|
| inl_branchy | −54% |
| inl_constchain | −46% |
| inl_repeat | −17.4% |
| inl_chain | −5.6% |
| main suite | flat, nothing beyond ±2% |
| geomean | −5.0% |

Compile time grows where trials run: inl_mutual went from 216 to 1070 ms.
inl_chain now collapses fully. Its remaining gap is algebraic (instruction
combining), not inlining.

Still open from the P2 design:
- lowering-added runtime call edges
- ranking candidates by summary
- an outer fixpoint over the passes

### Status of P3 (2026-10-01)

**Cold block layout.** `findColdBlocks` treats these blocks as cold:
- blocks ending in panic or unreachable
- conditional arms that call a void user function (the `reportError` shape)

It looks through split-edge jump blocks, so `a or b` arms count too. Coldness
then propagates to blocks whose predecessors are all cold. `emitRegionCode`
emits cold blocks after the hot body, so error calls in inl_hotcold sit
after `ret`.

**Pristine-route fix.** The first paired battle of the pristine route made
fib 137% slower and inl_recursive 132% slower: lowering the pre-inline body
dropped the front end's self-expansion, and the SSA inliner never inlines a
region into itself. Functions in a recursive call-graph SCC now keep the old
route.

**Second pristine-route fix, found in the P3-vs-P4 battle.** inl_recursive
was +35% in every snapshot from P3 on. `run` takes treeWalk unrolled 15 deep
from the front end, and P3 replaced that with the SSA inliner's single
level. Fixes:
- A function whose front-end body holds an inlined copy of a recursive
  function keeps the old route.
- The SSA inliner no longer adds one more level of a recursive callee at the
  leaves of such an expansion from outside its SCC. Inside the SCC that
  level pays (mixTree__coldTail, inl_mutual's generators), so it stays.

The region cost estimate can't arbitrate this, because it prices a
recursive call as one call; a trial version picked the wrong side
everywhere. Quick check: inl_recursive 530 → 390 ms (P2: 404), and every
other recursive workload is unchanged.

**Shrink-wrapping was not done.** In inl_bigcold the fast path itself holds
callee-saved registers and a spilled parameter, so moving the saves gains
nothing without live-range splitting. P4 (partial inlining) attacks the same
shape more cheaply.

### Status of P4 (2026-10-01)

`splitColdTails` (zc.zeph, -O2 only, before the front-end inliner) handles
the early-exit guard shape:

```
prefix; if guard { fast; return }; slowTail
```

It applies when the prefix only declares effect-free scalars, the guard has
no effects, the hot part is ≤60 nodes and the tail ≥60. The function becomes
`prefix; if guard { fast; return }; return f__coldTail(params)`.

The `__coldTail` clone is the unchanged original. It re-runs the prefix,
finds the guard false and runs the tail, so no live-in analysis is needed.
The trimmed function then fits both inliners.

`--opt-report` prints `opt: partial inline: f keeps N nodes, its M-node
tail moves to f__coldTail`.

Among the battle workloads it fires only on inl_bigcold, where it is about
−28% in a quick check (paired battle pending). Not done: the rare-branch
shape `if rare { big }` with code after it, which needs live-outs.

### Status of P5 (2026-10-01)

Both passes run in zc.zeph at -O2, after checking and before P4's split and
the front-end inliner (`propagateConstantArguments`).

**Interprocedural constant propagation.** If every direct call passes the
same literal for a parameter the body never assigns, the body uses the
literal and the signature stays. This repeats to a fixpoint, so constants
travel down chains: all 55 parameters of inl_constchain's level0..leaf.

The pass skips:
- functions used as values
- methods (interface dispatch reaches them unseen)
- `runtime*` helpers

**Specialization clones.** A call that passes literals for parameters that
steer the callee calls a clone with the literals substituted. Steering means
the parameter appears in a branch or loop condition, a range bound, or a
divisor or shift amount; it is never assigned; and every self-call passes it
through unchanged, so a counter like `depth - 1` never keys a clone. The
clone only happens when the callee won't inline anyway: it calls itself, or
it is over 60 nodes.

Clones are keyed by the literal vector, at most 4 per function. After
substitution a pass-through recursive call carries the same literals, so it
lands on the clone itself. `--opt-report` prints each constant parameter and
each clone with its key.

New workload `inl_specialize` (battle and optimizer_parity): a recursive tree
walk with a constant mode and divisor at two sites, plus a loop body with
three constant flag sets. It is −18% in a quick check (paired battle
pending). Clones also form on inl_branchy, inl_repeat and pi, with no
measurable change there.

Not done:
- dead originals stay emitted
- no frequency threshold (needs P7 profiles)
- no growth budget beyond the per-function cap

### Status of P6 (2026-10-01)

**General self tail recursion** (`tailRecursionPass`, zc.zeph, -O2). It runs
after `accumulatorRecursionPass`, which still handles fib's one-parameter
shape.

The rewrite:
- Every `return f(args)` outside an inner loop becomes parameter updates
  plus `continue` of a `while true` around the body. Temporaries are used
  when more than one parameter changes, and a trailing `break` keeps
  fall-through.
- `return E op f(args)` with integer `+ * & | ^` first folds E into one
  accumulator. The accumulator starts at the operator's identity, and every
  other return, including those inside inner loops, answers `acc op value`.
  Wrapping arithmetic makes the reassociation exact. When the call is the
  left operand, E must be strictly pure.

Limits:
- A changed parameter must be a scalar. Reference parameters may only pass
  through.
- Sites inside inner loops stay calls.

`tests/regression/tail_recursion.zeph` (optimizer_parity) covers:
- swapped parameters
- a float else-if chain
- `*` with the call on the left
- returns inside a loop under an accumulator
- `^` after an effectful call
- a void callee in the body

Among the battle workloads it fires only on inl_recursive's `sumScaled`:
about −7% in a quick check, paired battle pending.

Not done:
- Base-case range threading.
- SCC unroll budgets: fib's function is byte-identical across P2..P6, and
  its gap to C is the loop shape found in the original fib work.
- Void tail calls written as statements.

**Measurement note.** Test gates running at the same time as a battle shift
its timings by up to 2× even with CPU pinning. The C reference column shows
the drift. The P2-vs-P3 fib "regression" was such an artifact; the fib asm
was byte-identical. Battles are rerun on a quiet machine.

### Status of P7 (2026-10-01)

**Counters.** `--profile-generate FILE` and `--profile-use FILE` (zc.zeph,
`setUpProfile`). Counters are numbered in source order once imports expand:
one per function entry, two per `if` (then and else). The numbers are
stable across rebuilds of the same source, and a header with the counter
count rejects a stale profile with a warning.

**Generate.** Instrumentation is parsed source, `zephyrProfileCounters[k] +=
1`, inserted before checking. No codegen changes, and it works with or
without -O2. A top-level writer appended at the end saves the counts when
the program ends normally.

**Use.** Each `if` carries `referenceIndex = then-counter + 1`, which
clones and inlined copies keep, so the profile is context-insensitive.
Consumers in the SSA tier:
- block profile scales: arm probability times the enclosing scale
- `profiledWeight` = loopWeight × scale × 64, used by the region cost
  estimate (inline trials) and by spill costs
- blocks under 0.001 are cold in P3 layout
- trials are skipped for functions the profile never entered

Without profile flags the output is byte-identical to P6 on all 32 battle
workloads. `tests/pgo_roundtrip.ps1` checks that generate, train and use give
the plain build's output on four programs.

**Result: neutral.** Sweep with training at ¼ of the battle input: all
outputs match, every workload within ±2% except liquid +5% and inl_indirect
+4%, measured while a battle ran, so noisy. The profile changes layout and
spill choices, but nothing that limits these workloads.

Payoff needs consumers that create opportunities:
- indirect and interface target profiles: inl_indirect's dominant targets
  are already the first-tried implementor, so there is nothing to gain there
- value profiles for guarded specialization
- profile-driven outlining of rare `if` arms with live-outs, the P4
  rare-branch shape

There is no battle-harness PGO column yet; add one with the first consumer
that wins.

## 6. Benchmarks

The `inl_*` suite in compiler-battle (`battle.py run --suite inlining`) runs
the same algorithm in Zephyr, C and Rust, with one checksum and data-driven
inputs:

| workload | question it answers |
|---|---|
| inl_chain | Can 40 levels of tiny functions collapse into one region? |
| inl_tiny | Does a dense composition of one-line helpers become straight-line code? |
| inl_bigcold | Partial inlining: 5 hot lines inside a 150-line function |
| inl_branchy | Does a constant op selector fold a 10-way branch per site? |
| inl_repeat | Code growth vs. specialization across 12 sites of one medium function |
| inl_recursive | Non-tail tree recursion and linear recursion |
| inl_mutual | Recursive-descent parser SCC, plus even/odd |
| inl_indirect | Closure and interface calls with a 99%-dominant target |
| inl_constchain | Constants carried 10 levels deep decide leaf branches |
| inl_loopcalls | Calls containing loops, and loops containing calls |
| inl_hotcold | Never-firing error handlers with string formatting |
| inl_superpath | A→B→D dominant over C and E |

**Baseline (2026-10-01, `results\battles\9f90186-dirty-20261001-165130.json`).**
Ratio is Zephyr -O2 time / gcc -O2 time:

| workload | ratio | workload | ratio | workload | ratio |
|---|---:|---|---:|---|---:|
| branchy | 6.12 | repeat | 1.97 | mutual | 1.15 |
| constchain | 3.84 | chain | 1.69 | loopcalls | 1.02 |
| hotcold | 2.94 | tiny | 1.31 | indirect | 0.91 |
| bigcold | 2.85 | superpath | 1.29 | recursive | 0.87 |

The geometric mean is 1.78. In the worst cases the callee is too big for the
60-node gate even though constant arguments would fold most of it away.
For example, `apply` (105 IR values) is called from 6 constant-selector
sites, and `level9`..`level0` each compile standalone. This is the
constant-sensitivity case of §4.2.

**Metrics, in priority order:**
1. runtime: median of 5, interleaved, pinned
2. machine-code size: `binaryKb`, plus per-function bytes from the map file
3. compile time: `compileMs`
4. regression risk: checksums, parity tests

Each phase reports before/after on both suites. "Calls removed" is logged
for diagnosis only.

## 7. Open questions

- **Calibrating the cost weights `c(i)`.** Start with uniform 1 plus
  latencies for divide, load and call, then fit against battle results.
  Keep it simple until the data says otherwise.
- **Trial cost.** If trial lowering makes -O2 compile time grow beyond about
  3× on the suite, add memoized lowering per decision-tree prefix before
  shrinking K.
- **Baseline (-O0) regressions.** The AST inliner changes only under -O2, so
  baseline output must stay byte-identical. Check with `optimizer_parity`
  and assembly diffs.
