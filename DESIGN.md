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
