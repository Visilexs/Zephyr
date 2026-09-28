# Alternate kernel implementations

Two agents were given disjoint halves of the kernel set and both wrote
`elem_binary_f64.comp` and `elem_unary_f64.comp` anyway, each overwriting the
other more than once. Three distinct versions of the unary kernel resulted.

The one in `examples/shaders/` is what ships. The other two are kept here
because **all of them pass the 95 output checks and the 15 gradient checks**,
so the choice between them was not made on correctness, and discarding work
that passes the gates would be throwing away information.

| file | SPIR-V size | notes |
|---|---|---|
| `examples/shaders/elem_unary_f64.comp` | 40,344 B | ships |
| `elem_unary_f64.alt.comp` | -- | fdlibm minimax coefficients, `fma` throughout, signed-zero and infinity handling, Payne-Hanek range guard, overflow-safe scaled complex log |
| `elem_unary_f64.alt2.comp` | 66,156 B | the largest, and the most thorough on edge cases |

Worth revisiting if a tolerance gate is ever tightened below 1e-12, or when
the backend has to run on a driver other than this one: the alternates handle
signed zeros, infinities and `atan2` at the axes more carefully than the
shipped version, which was selected for having been verified rather than for
being the most careful.

Not built by `scripts/build-compute-shaders.ps1` -- these are reference
copies, not part of the build.
