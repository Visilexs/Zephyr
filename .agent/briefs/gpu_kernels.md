# Task: write five GLSL compute kernels for a float64 ML backend

You have full sign-off to create and modify the files listed below. Do not ask
for approval; proceed and finish. Work only inside the repository at
`C:\Users\Visil\Documents\Ultra important project\Zephyr`.

## Context

`lib/ml/gpu.zeph` is a Vulkan compute backend for a tensor library. It
currently has one kernel, `examples/shaders/matmul_f64.comp` (real float64)
and `examples/shaders/matmul_c64.comp` (complex float64). Read both before
starting; match their style, their `#version 450`, their
`layout(local_size_x = ...) in;` declarations, and their std430 storage
buffer declarations.

The tensor library this serves is `lib/ml/tensor.zeph` and `lib/ml/ops.zeph`.
Read `t_binary`, `t_map1`, `t_sum_dim`, `t_index_select`, `t_roll` and
`t_concat` in `lib/ml/ops.zeph` so your kernels reproduce their exact
semantics. Where this brief and those functions disagree, the Zephyr code is
correct and you should follow it and say so in your report.

## The data contract, which is the same for every kernel

Elements are IEEE float64. A tensor buffer is declared `double data[]`.

A **real** tensor of N elements occupies N doubles. A **complex** tensor of N
elements occupies 2N doubles, interleaved re,im. This matches
`examples/shaders/matmul_c64.comp` exactly.

Tensors are **strided views**, not necessarily contiguous. Every kernel must
compute its source and destination positions from shape, strides and an
offset, never by assuming a flat contiguous layout. Strides and offsets are
expressed **in elements, not in doubles** -- so for a complex tensor the
double index is `2 * (offset + sum over d of idx[d] * stride[d])` and for a
real tensor it is `offset + sum over d of idx[d] * stride[d]`.

A **zero stride** means broadcast along that axis. This is how broadcasting
works and it must not be special-cased away: a zero stride simply makes every
index along that axis read the same element.

Maximum rank is 4. A tensor of rank r < 4 uses the first r entries of the
shape and stride vectors; entries at index >= r must be ignored, and the
caller sets them to shape 1, stride 0.

## Push constants, identical block in every kernel

```glsl
layout(push_constant) uniform Push {
    uvec4 meta;    // x = rank, y = numel (output elements), z = op, w = flags
    uvec4 oshape;  // output shape, unused trailing entries are 1
    uvec4 astr;    // strides of operand A, in elements
    uvec4 bstr;    // strides of operand B, in elements
    uvec4 ostr;    // strides of the output, in elements
    uvec4 offs;    // x = A offset, y = B offset, z = output offset, w unused
} pc;
```

96 bytes, inside the 128-byte guaranteed minimum. Use `uvec4`, not
`uint[4]`: array stride in a push constant block is a layout trap and uvec4
is unambiguous.

`flags` is a bitfield: **bit 0** set means operand A is complex, **bit 1**
operand B is complex, **bit 2** the output is complex. Test with
`(pc.meta.w & 1u) != 0u` and so on.

Write one shared helper in each kernel that turns a linear output index into
a 4-component index vector using `pc.oshape`, and one that turns that index
vector plus a stride vector plus an offset plus a complex flag into a double
index. Every kernel uses the same two helpers. Do not duplicate index
arithmetic inline.

Every kernel must begin with the bounds guard
`if (gid >= pc.meta.y) { return; }` where `gid` is the linear global
invocation index. The dispatch is one-dimensional: use
`layout(local_size_x = 256) in;` and `uint gid = gl_GlobalInvocationID.x;`.
Omitting this guard is a correctness bug, not an optimisation.

## The five kernels

Create these files in `examples/shaders/`:

### 1. `elem_binary_f64.comp`

Bindings 0 = A, 1 = B, 2 = out. `op` selects the operation, and these codes
are fixed by `t_binary` in `lib/ml/ops.zeph` -- do not renumber them:

| op | operation |
|---|---|
| 0 | add |
| 1 | sub |
| 2 | mul |
| 3 | div |

Must handle real and complex. Complex multiply is
`(ar*br - ai*bi, ar*bi + ai*br)`. Complex divide is
`((ar*br + ai*bi)/d, (ai*br - ar*bi)/d)` with `d = br*br + bi*bi`. Complex
add and subtract are componentwise.

Both operands are always the same dtype; you do not need to handle real
combined with complex here.

### 2. `elem_unary_f64.comp`

Bindings 0 = in, 1 = out. Operand strides come from `pc.astr` and
`pc.offs.x`. The codes 0 to 4 are fixed by the `MAP_` constants in
`lib/ml/ops.zeph`; 5 onward are new and you should use exactly these:

| op | operation | input | output |
|---|---|---|---|
| 0 | tanh | real or complex | same as input |
| 1 | cos | real or complex | same as input |
| 2 | sin | real or complex | same as input |
| 3 | exp | real or complex | same as input |
| 4 | ln | real or complex | same as input |
| 5 | neg | real or complex | same as input |
| 6 | abs2 | complex | **real**: `re*re + im*im` |
| 7 | conj | complex | complex: `(re, -im)` |
| 8 | real | complex | **real**: `re` |
| 9 | imag | complex | **real**: `im` |
| 10 | expi | **real** theta | **complex**: `(cos(theta), sin(theta))` |
| 11 | cast | real or complex | complex or real, see below |
| 12 | copy | real or complex | same as input |

Note that ops 6, 8, 9 and 10 change the dtype, which is why the flags
bitfield carries the input and output complex bits separately. Honour them.

`cast` real to complex sets the imaginary part to 0. `cast` complex to real
takes the real part and discards the imaginary part.

GLSL has no float64 transcendental built-ins. `tanh`, `cos`, `sin`, `exp` and
`log` exist for `float` only. You therefore need double-precision
implementations. Use these and nothing fancier:

* `exp(x)`: range-reduce by `k = round(x / ln2)`, `r = x - k*ln2` using a
  two-part ln2 (`ln2_hi = 0.693147180559945286lf`,
  `ln2_lo = 2.319046813846299558e-17lf`) so the reduction is accurate, then a
  Taylor or minimax polynomial in `r` over `[-ln2/2, ln2/2]` to at least 1e-17
  relative, then scale by `2^k` via `ldexp`-equivalent repeated multiplication
  or by constructing the power of two.
* `ln(x)`: decompose `x = m * 2^e` with `m` in `[sqrt(0.5), sqrt(2))`, use the
  `atanh` series in `s = (m-1)/(m+1)`, i.e.
  `ln(m) = 2*(s + s^3/3 + s^5/5 + ...)`, to at least 1e-17, then add
  `e * ln2` using the two-part ln2.
* `sin` and `cos`: range-reduce modulo pi/2 with a two-part or three-part pi/2
  constant, then a minimax polynomial for sine and cosine on `[-pi/4, pi/4]`.
* `tanh(x)`: for `|x| > 20` return `sign(x)`; otherwise
  `tanh(x) = (e^{2x} - 1) / (e^{2x} + 1)`, computed as
  `t = expm1(2x); t / (t + 2)` if you implement `expm1`, or via your `exp`
  with care for cancellation near zero -- for `|x| < 1e-8` return `x`.

**Do not fall back to float32 built-ins and cast.** That loses ten digits and
would silently fail the tolerance gates this backend is measured against.

The complex forms are: `exp(z) = e^{re} * (cos(im), sin(im))`;
`ln(z) = (0.5*ln(re*re+im*im), atan2(im, re))` -- you will need a double
`atan2`, so implement `atan` by argument reduction and a minimax polynomial
and build `atan2` from it with the correct quadrant handling;
`sin(z) = (sin(re)*cosh(im), cos(re)*sinh(im))`;
`cos(z) = (cos(re)*cosh(im), -sin(re)*sinh(im))`;
`tanh(z) = sinh(2re)/(cosh(2re)+cos(2im)), sin(2im)/(cosh(2re)+cos(2im))`.
`cosh` and `sinh` follow from your `exp`.

Put every one of these in a clearly named helper function with a short comment
saying what accuracy it targets.

### 3. `reduce_f64.comp`

Bindings 0 = in, 1 = out. Sums the input along **one** axis.

`meta.z` (the `op` slot) carries the **axis index** to reduce, not an
operation code. `meta.y` is the number of **output** elements. The length of
the reduced axis is passed in `offs.w`.

Each invocation owns one output element: it walks the reduced axis, summing
`offs.w` inputs, and writes one output. Use `pc.oshape` and `pc.ostr` for the
output position, and `pc.astr` for the input, where the stride along the
reduced axis tells you how to step. The reduced axis is **not** present in the
output shape; the caller passes the input strides with the reduced axis's
stride placed in `bstr.x` so you can step along it. Read `t_sum_dim` in
`lib/ml/ops.zeph` and match it.

Handle real and complex, accumulating both components for complex.

Accumulate in a local `double` (or two for complex) in a simple ascending
loop. Do not reorder for parallelism: the CPU reference sums ascending and
the tolerance gate compares against it.

### 4. `gather_f64.comp`

Bindings 0 = source, 1 = index buffer (`uint idx[]`), 2 = out.

One invocation per output element. The invocation computes its output index
vector, replaces component `meta.z` (the gather axis) with
`idx[original component value]`, and reads the source at the resulting
position. This one kernel covers `index_select`, `roll` and `concat`,
because all three are gathers that differ only in the index buffer the host
builds. Handle real and complex.

### 5. `scatter_add_f64.comp`

Bindings 0 = gradient, 1 = index buffer (`uint idx[]`), 2 = out.

The VJP of a gather. One invocation per **gradient** element. It computes the
destination the same way `gather_f64` computes its source, and **adds** into
it. Duplicate indices must accumulate, so the add must be atomic.

GLSL has no `atomicAdd` for `double`. Implement it with a compare-and-swap
loop over the 64-bit pattern: declare a second alias of the output buffer as
`uint64_t` (requires `#extension GL_EXT_shader_atomic_int64 : require` and
`GL_ARB_gpu_shader_int64`), and loop
`old = data[i]; new = doubleBitsToUint64(uint64BitsToDouble(old) + v);
until atomicCompSwap(data[i], old, new) == old`. If `glslc` rejects the
int64 atomic extension, fall back to declaring the buffer as `uvec2` and
doing the CAS on a `uint` pair is NOT correct -- instead say so clearly in
your report and leave the kernel out rather than shipping a racy version.
**The caller must also zero the output first; note that requirement in a
comment at the top of the file.**

## Build and definition of done

Add each new kernel to the file list in `scripts/build-compute-shaders.ps1`
(there is an array of names; extend it).

Then run, from the repository root:

```
powershell -File scripts/build-compute-shaders.ps1
```

It must print `ok` for every kernel including the three that already exist.
Then validate each new `.spv` with `spirv-val`.

You are done when:

1. All five `.comp` files exist in `examples/shaders/`.
2. `scripts/build-compute-shaders.ps1` lists all eight kernels and exits 0.
3. Every `.spv` passes `spirv-val`.
4. Your report states, for each kernel, the accuracy you believe the
   double-precision transcendentals achieve, and names anything you could not
   do -- especially if the int64 atomic extension was unavailable.

Do not write Zephyr code. Do not modify `lib/ml/gpu.zeph`, `lib/ml/ops.zeph`,
`lib/ml/tensor.zeph`, or anything under `tests/`. Kernels and the build script
only.

Report honestly. If a kernel is wrong or unfinished, say which and why. I will
verify every one of these numerically against the CPU implementation, so an
optimistic report will be caught and is worse than an accurate one.
