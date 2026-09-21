# M7 control family: GRU baselines

Implement the GRU control models the experiment protocol requires, natively
in Zephyr, differentiable through the existing autograd tape.

Repo root: `C:\Users\Visil\Documents\Ultra important project\Zephyr`
Compile and run: `.\zc.exe --rt src.zeph out.exe` then `.\out.exe`

## Read these first

- `lib/ml/phase_ad.zeph` -- the phase model on the tape. Your module must
  mirror its shape: a params struct, a `*_params` constructor that allocates
  leaves in a fixed order, a `*_loss` entry point, and a list accessor. Copy
  its conventions rather than inventing new ones.
- `lib/ml/autograd.zeph` -- the `av_*` operators you may use.
- `tests/ml/phase_ad_test.zeph` and `tests/ml/opt_test.zeph` -- test style.

## Hard constraint

Build **only** out of existing `av_*` operators. Do not add an opcode, do not
write a VJP, do not touch `lib/ml/ops.zeph`, `lib/ml/autograd.zeph`,
`lib/ml/ir.zeph` or `lib/ml/phase_ad.zeph`. Those files have other work in
flight and the whole point of this control is that it reuses the verified
autograd rather than adding unverified ones. If an operator you want does not
exist, compose it: `sigmoid(x) = 0.5 * (tanh(0.5 * x) + 1)` is exact enough
and needs nothing new.

## Deliverable: `lib/ml/gru.zeph`

```zephyr
struct GruConfig {
    input_vocab: int,
    output_vocab: int,
    E: int,          // embedding width
    Hn: int,         // hidden width
    head: int,       // 0 = linear softmax, 1 = quadratic
    pad: int,
    eps: float,
}

struct GruParams {
    config: GruConfig,
    embedding: Tensor,   // [input_vocab, E]
    Wz: Tensor,          // [Hn, E + Hn]
    bz: Tensor,          // [Hn]
    Wr: Tensor,          // [Hn, E + Hn]
    br: Tensor,          // [Hn]
    Wn: Tensor,          // [Hn, E + Hn]
    bn: Tensor,          // [Hn]
    Wo: Tensor,          // [output_vocab, Hn]
    bo: Tensor,          // [output_vocab]
    h0: Tensor,          // [Hn]
}

struct GruAD { ... the same fields as tape handles, plus config ... }

fn gru_param_list(p: GruParams) -> [Tensor]      // fixed order, 10 tensors
fn gru_params(p: GruParams, req: bool) -> GruAD  // leaves in that same order
fn gru_loss(m: GruAD, tokens: Tensor, targets: [int]) -> int
```

The recurrence, standard GRU, per step t with input row x_t and state h:

```
c  = concat(x_t, h)            along the feature dimension
z  = sigmoid(c @ Wz^T + bz)
r  = sigmoid(c @ Wr^T + br)
cn = concat(x_t, r * h)
n  = tanh(cn @ Wn^T + bn)
h' = (1 - z) * n + z * h
```

Two requirements that are easy to get wrong and are the point of the control:

1. **PAD rows keep their state exactly.** The phase model masks
   arithmetically rather than branching, because a branch is control flow the
   tape cannot see -- read `pad_mask` and how `pad_loss` applies it, and do
   the same thing here: `h_next = mask * h' + (1 - mask) * h`. A PAD row's
   state must be bit-identical to its previous state.
2. **The head.** `head == 0` is a linear softmax over `h_T @ Wo^T + bo`,
   giving probabilities and an NLL loss. `head == 1` is the quadratic head
   that mirrors the phase model's readout: take `u = h_T @ Wo^T + bo`, then
   `p = (u * u + eps) / sum(u * u + eps)`, using the same normalisation shape
   as `pad_readout`. Read `pad_readout` and match its structure and its eps
   handling, because "same readout normalization" is what makes it a fair
   control.

The loss is mean negative log likelihood of the target class, computed the
same way `pad_loss` computes it. Read that function; do not invent a
different reduction.

## Deliverable: `tests/ml/gru_test.zeph`

Follow the conventions in `tests/ml/opt_test.zeph`: a `chk(cond, what)`
counter, `FAIL:` lines, a final `print("gru: N checks passed")`, and a panic
if any failed. Cover at least:

- **Gradients against central differences**, for every one of the ten
  parameter tensors, both heads. Perturb an element by h, recompute the loss
  both ways, compare with the analytic gradient to a stated relative
  tolerance. This is the check that matters most; the others are cheap.
- **PAD keeps state exactly**: a row whose later steps are all PAD has a
  final state bit-identical (`t_hex`) to its state at the last real token.
- **Probabilities are a distribution**: non-negative and summing to 1 within
  1e-12, for both heads.
- **The quadratic head is invariant to the sign of `u`** and the linear one
  is not, so the two heads are actually different functions.
- A shape/validation rejection or two, run in child processes the way
  `opt_test.zeph` does it, since a panic cannot be caught in process.
- **It must overfit**: 32 examples with fixed random labels driven to near
  zero loss in a few hundred AdamW steps, asserting the loss fell by a large
  factor. Use `lib/ml/optim.zeph`. This catches a model that is
  differentiable but cannot learn.

Register it in `tests/run_tests.ps1` alongside the `"ml-fusion"` entry,
copying that entry's exact format.

## Definition of done

Both files compile and the test binary prints `gru: N checks passed` with
exit code 0. Report the actual command, the actual output, and N. Report
anything you could not make work rather than removing the check. Do not
commit; leave the work in the tree.

## Zephyr notes that will save you time

No semicolons. `and` / `or` / `not` are words, not symbols. `let` is
immutable, `var` mutable. Ranges are half-open. String interpolation uses
braces, so a literal brace is written `\{` and `\}`. `push` is a builtin
name and cannot be used as a local or a parameter. `fn` declarations are only
allowed at top level, never nested inside an `if`. There is no tuple type;
return a list. `t_sum_all` returns a float, not a tensor -- `t_sum_to_one`
gives the tensor. Imports resolve relative to `zc.exe`, so write
`import "ml/autograd.zeph"`.
