# Design decisions

Decisions taken while implementing, with the reason. Measurements live in
`RESULTS.md`; this file is for choices. Append, do not rewrite: a superseded
decision should be struck through with the reason it changed, so a later
session can see what was already tried.

## D1 — the ML library is library code, not compiler builtins

`lib/ml/` is ordinary Zephyr over the existing `Bytes`. Adding a builtin means
editing `is_builtin_name`, the typecheck dispatch chain and a codegen case
inside a 6,200-line compiler, which is only justified for something needing a
raw instruction — `sqrt` earns that, tensor descriptors do not. This matches
`zephyr-ml/02_ARCHITECTURE.md`: library semantics first, language types only
once storage and AD semantics are settled.

## D2 — `lib/ml` stays outside the embedded standard library

`scripts/embed-gen.ps1` globs `lib\std\*.zeph` and bakes those sources into the
compiler binary. `lib/ml/` deliberately sits outside that glob, which
`zephyr-ml/15_BOOTSTRAP_PLAN.md` explicitly sanctions. Two consequences worth
knowing: ML changes do not perturb the self-host fixpoint at all, and a lone
`zc.exe` carried away from the repo cannot resolve `import "ml/..."`. The
first is worth much more than the second right now.

## D3 — rejection is a panic, not an error value

Zephyr has optionals but no error type, and its own list indexing panics out of
range. A tensor library that returned `Tensor?` everywhere would force
`.or(...)` at every call site and make the common path unreadable. Invalid
shapes, out-of-range indices, stale saved tensors and dtype misuse therefore
panic with a message naming the cause. This satisfies "fail before access" and
matches how the language already behaves.

Consequence: a rejection cannot be asserted from inside a positive test,
because it takes the process down. The negative cases are separate one-line
programs driven from `tests/run_tests.ps1`, the same shape as the existing
`$panics` table.

## D4 — two allocation caps, with two different jobs

`MAX_ELEMS` (2^40) is the overflow guard. Checked before each dimension
multiply, it makes the element count provably unable to wrap i64, and since
the widest dtype is 16 bytes the byte product is then bounded by 2^44 and
cannot wrap either.

`MAX_BYTES` (128 GiB) is a sanity cap, and is deliberately **not** derived from
`MAX_ELEMS`. An earlier version set it to 2^44, which made it unreachable —
dead code that looked like a safety check. With it unreachable, an absurd
request fell through to the allocator and came back as a bare "heap full",
naming neither the request nor the limit.

## D5 — strides and offsets count elements, bytes only at the access site

One conversion point, `t_byte_offset`, which every read and write goes
through. A stride expressed in bytes has to be re-derived whenever the dtype
changes, and mixing the two units is a classic source of silent corruption.

## D6 — views rely on the counted heap, not on manual lifetime

Zephyr structs are reference types on a counted, non-moving heap, so a view
holding a `Storage` keeps the buffer alive by itself and observes the owner's
mutation version with no extra machinery. Use-after-free is therefore not
representable for CPU storage, which is most of what A03 asks about.

The byte counters are diagnostics only and need an explicit
`storage_release` to be accurate. They exist for the GPU allocator later,
where a buffer genuinely cannot be recycled until the device has finished
with it, and where the deferred-free accounting will matter.

## D7 — the mutation version is the saved-tensor guard

`t_save` records the storage version; `saved_get` refuses if it has moved.
Because views share the `Storage`, a write through *any* view invalidates a
save taken on the owner. This is the mechanism `zephyr-ml/06_AUTOGRAD.md`
requires before backward reads a saved value, put in place now so the tape
cannot be built without it.

## D8 — complex is interleaved, with component-width names

`C32` is two f32 components (8 bytes) and maps to `torch.complex64`; `C64` is
two f64 components (16 bytes) and maps to `torch.complex128`. `dtype_name`
returns `c32_components` / `c64_components` rather than a bare width, so the
name cannot be silently matched against PyTorch's. Storage is real then
imaginary, which is also the canonical checkpoint layout.

## D9 — the task solvers must not see the generator

`tools/ml_reference/tasks.py` recomputes every answer from the emitted token
sequence alone, by re-parsing the grammar. A solver that consulted the
generator's bookkeeping would agree with it trivially and A30 would prove
nothing.

Note one deviation, recorded rather than smoothed over: A31 says "no target in
input", which is impossible for associative recall — the value has to be
stored somewhere for the task to be solvable. The enforceable reading, and the
one EXPERIMENTS.md actually states, is that no target is *appended after*
`ANSWER`. That is what is asserted.

## D10 — accuracy fixes in std/math preceded the ML work

`gamma`, `sinh` and `cosh` cannot be correct while `fexp` carries float32
range bounds, so four accuracy defects in the pre-existing library were fixed
first: `fexp` range, `tanh` cancellation near zero, `fsin` term count, `fln`
term count, and later the 2pi reduction split. All are recorded in the git
history with measurements. Nothing outside `lib/std/math.zeph` imported it, so
no caller changed.

## D11 — broadcast views are read-only, enforced by the descriptor

`t_expand` produces a zero-stride view, which means many logical elements
alias one stored element. A write through such a view would silently scatter,
so `Tensor` carries `ro: bool` and all three setters panic on it. This is
stricter than PyTorch, which permits the write and lets the aliasing surprise
you. Rejecting it costs nothing here: nothing in the planned autograd needs to
write through a broadcast.

## D12 — no dtype promotion, ever

`t_add(f32, f64)` panics rather than promoting. Promotion rules are the most
common source of silent precision loss in a framework, and the phase model has
exactly one dtype per tensor decided up front. A cast is available as `t_cast`
and has to be written down.

## D13 — numpy is the operator oracle, and says what it can

PyTorch is not installed, so `check_ops.py` compares against numpy. That is
sound for A04/A05 specifically because both are IEEE-754 double arithmetic,
and the one thing numpy could differ on — complex memory layout — is checked
directly at the byte level with `t_hex` rather than assumed. Where accumulation
order is unspecified (matmul, sums) the agreement is 1–4 ulp, not bit-exact,
and that is recorded as such rather than hidden behind a loose tolerance.

## D14 — one gather covers three needs, and refuses duplicate scatter indices

`t_index_select` serves the embedding lookup (dim 0), the Givens pair
extraction (dim 1) and `t_roll`, which is a permutation of the same call.
Writing three operators would have triplicated the stride traversal, which is
where the bugs live. Its counterpart `t_index_copy` **panics on a duplicate
index** rather than letting the last write win. Every use in this model is a
disjoint pairing, so a duplicate is a caller bug; when the backward pass later
needs genuine accumulation that will be a separate, named scatter-add.

## D15 — the reference model came from a delegated agent and was verified twice

`tools/ml_reference/phase_model.py` and `test_phase.py` were written by Codex
against a written brief. Its own suite passing is not evidence, so
`verify_phase.py` was written separately, from `MATHEMATICS.md`,
`INTERFERENCE.md` and `READOUT.md` rather than from the module: it rebuilds
the Givens matrix from the document, checks the module against that, and
checks every gradient against central differences. 112 checks, independent of
the 12 Codex wrote. Both are kept — agreement between two suites written from
the same spec by different authors is the point.

## D16 — INTERFERENCE.md's constructed example is internally inconsistent

The document specifies the state `z=(1,exp(i*delta))/sqrt(2)` and the readout
row `(1,1)/sqrt(2)`, then says the squared amplitude "equals 1+cos(delta),
ranging from 0 to 2". Both cannot be true. With that normalized row the value
is `(1+cos(delta))/2`, ranging 0 to 1. The figure 1+cos(delta) is what the
*unnormalized* row `(1,1)` gives.

We keep the normalized row and assert the value it actually produces, because
the document states that row explicitly and because normalized rows are what
make the two-orthonormal-row probability claim in the same paragraph come out
right. Both forms are asserted in `verify_phase.py` so the arithmetic is on
the record rather than papered over with a stray factor of two.

Nothing scientific turns on this. The paragraph's actual claim -- that two
orthonormal rows sweep the probability from fully constructive [1,0] through
[0.5,0.5] to fully destructive [0,1] while global phase moves neither -- holds
exactly, and is now asserted directly instead of being inferred from the
scalar. This is a normalization bookkeeping error in the prose, recorded
rather than silently corrected, and it needs a versioned fixture update only
if a later document depends on the literal 0-to-2 range.

## D17 -- parity is checked per step, with bit-identical weights

`check_phase.py` compares every intermediate the forward pass actually
produced -- features, hidden layer, angles, post-phase state, both stage
outputs, the state, and the active mask -- rather than the final
probabilities alone. A wrong sign inside one Givens stage can still land on a
plausible output distribution, so an end-to-end comparison would be weak
evidence for the thing M3 is supposed to establish.

Two properties make the comparison mean something. The weights are rebuilt
independently on each side from a mirrored LCG and then asserted
**bit-identical**, so the tolerance cannot be quietly absorbing a different
fixture or fill order. And the harness fails on a quantity that is missing
from the dump as well as on one that is present but unexpected, so a port
that computed nothing could not pass vacuously.

The native side reproduces the intermediates from the same function the
forward pass uses. They are returned by it, never recomputed for the test,
because a recomputed intermediate checks the test's arithmetic rather than
the implementation's.

## D18 -- the pairing is pinned natively, not only through parity

The parity harness runs at D=4 and D=8. The specification's own dimension is
D=128, and `phase_givens` constructs its pairing in Zephyr independently of
the reference. A pairing that was a valid bijection but paired the wrong
coordinates would preserve the norm exactly and produce a perfectly plausible
trajectory, so norm checks cannot catch it.

`tests/ml/phase_gates_test.zeph` therefore pins the pairing directly at D=4, 8
and 128, using theta=pi/2 and phi=0 to turn a stage into a pure signed swap so
each coordinate's partner is readable straight off the output. It also asserts
the pairs are disjoint and cover every coordinate exactly once, that the stage
inverts under -theta (G^H), that stage B wraps the last coordinate onto the
first, and that the two stages are not the same permutation. Two of its checks
exist only to keep the rest non-vacuous: that a stage genuinely changes the
state, and that stages A and B differ.

## D19 -- the tape records opcodes and handles, not closures

A closure-based tape is the usual design and is not available here: wasm has
no closures, and lib/ml has so far compiled and passed identically as a
Windows PE, a static Linux ELF and wasm. Recording closures would trade that
away silently, for a milestone that never mentions it.

So a node holds an opcode, up to two input handles, saved tensors, and small
integer and float argument lists. Inputs are integer handles into a global
variable table rather than tensors, which means a node cannot alias its
input, cannot hold a stale descriptor, and the graph is a plain integer DAG.

Because handles are allocated in forward order, a node's inputs always have
smaller handles than its output. One descending sweep therefore visits every
node after all of its consumers, and no topological sort is needed.

## D20 -- in-place mutation is an error, not a wrong number

Saved tensors go through the version-checked `Saved` type from M2a, which was
built for this and had been unused. If a saved tensor's storage is mutated
between the forward and reverse passes, `saved_get` panics. The alternative
is a gradient that is quietly computed from the wrong values, which is the
single worst failure mode an AD system has, because every downstream number
still looks plausible.

## D21 -- the tape is explicitly reset, and that is asserted

A07 requires the tape not to grow without bound across steps. Rather than
trimming heuristically, the tape is reset explicitly and `av_nodes()` is
exported so a test can measure it. The test asserts that one step records
exactly three nodes and that twenty-five steps leave three -- an exact
measured count, not a loose upper bound that a leak could hide under.

`no_grad` suppresses recording rather than discarding afterwards, and an
operation whose inputs all require no gradient records nothing at all, so
inference costs no tape at all rather than a tape that is thrown away.
