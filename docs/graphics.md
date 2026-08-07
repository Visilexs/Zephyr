# Graphics & GPU in Zephyr

Zephyr is a memory-safe language with no pointers — yet the same repo drives
GDI windows, OpenGL, and Vulkan compute, and renders a real-time
geodesic-ray-traced black hole. This guide covers how: the native-interop
layer everything rests on, the `lib/vk` Vulkan wrapper, the Zephyr→SPIR-V
shader compiler, and the `examples/graphics` programs that exercise it all.

The interop primitives themselves (`win`, `callptr`, `extern fn … from`, the
raw-memory builtins) are specified in [spec.md §3.6](spec.md); this document is
the practical layer on top. Everything here needs `--rt` and is
Windows-only unless noted.

## The two layers

There are two ways to reach the platform, and the examples use both:

- **Raw** — `win("user32!CreateWindowExA", …)`, `callptr(addr, …)`, and
  `load64`/`store32`/`addr`. This is how the OpenGL demos and the `lib/ui`
  toolkit are written: direct Win64 calls with hand-packed structs. It is
  unsafe (raw addresses, no bounds checks) and verbose, but it needs nothing
  but the language.
- **Wrapped** — `import "vk/gfx.zeph"` and `import "std/bytes.zeph"`. The
  Vulkan wrapper hides the offset arithmetic behind typed struct builders and a
  `Gfx` facade; `Bytes` is the safe way to build any native struct. This is how
  the Vulkan demos are written.

### `Bytes` — safe native structs

`lib/std/bytes.zeph` wraps a heap allocation with typed, bounds-checked
accessors. It is the recommended way to build anything the OS or GPU reads.

```zephyr
import "std/bytes.zeph"

var pt = Bytes.new(16)          // a POINT (two 32-bit LONGs), plus room
let ok = GetCursorPos(pt.addr())
let x  = pt.get32(0)
let y  = pt.get32(4)
```

`Bytes.new(n)` allocates; `.addr()` is the address to hand to native code;
`.put8/16/32/64`, `.get8/16/32/64`, `.putf32/getf32` read and write fields;
`.put_cstr/put_str/get_str` handle strings. Free helpers: `cbytes(s)`
(a NUL-terminated C string), `u32s([…])`/`u64s([…])` (packed integer arrays),
`pack([Bytes…])` (concatenate struct builders into an array), and `f32_bits`/
`f32_from` (double ↔ 32-bit-float bit patterns, for the int-only FFI).

> One rule that matters: a buffer the OS or GPU **writes into** across time (a
> swapchain image, a cursor `POINT` read every frame) must be `VirtualAlloc`'d,
> not a `Bytes`/list allocation, because the conservative collector can reclaim
> the latter. See spec.md §3.6.

## The Vulkan wrapper — `lib/vk`

Five files, imported through `vk/gfx.zeph`:

| File | Contents |
|------|----------|
| `raw.zeph` | mechanical Vulkan bindings — every `vk*` entry point as an `extern`/`callptr` against `vulkan-1.dll`, all params `int` |
| `consts.zeph` | result codes, enums, and struct sizes/offsets — **generated** by `tools/vkgen.c` from the Vulkan SDK headers (1.4.350) |
| `structs.zeph` | typed `Bytes` builders — `VkFooCreateInfo.new().field(x)…`, each `new()` fills in `sType` |
| `win.zeph` | a minimal Win32 window for presentation (uses `DefWindowProcA` + `PeekMessageA`, so no Zephyr window-proc callback is ever needed) |
| `gfx.zeph` | the high-level `Gfx` facade |

`vkgen.c` is the one piece of C left in the graphics path, and it is a
*generator*, not a dependency — it turns the SDK headers into the two
`.zeph` files above, which are then ordinary checked-in source.

### The `Gfx` facade

`Gfx` owns the instance, device, queue and command pool. Structs it returns:
`GpuBuffer{buf, mem, size}`, `Swapchain`, `Target{image, mem, view, fb, w, h}`,
`DescSet{layout, pool, set}`.

**Lifecycle**
- `Gfx.init(appname, layers) -> Gfx` — headless (no window).
- `Gfx.init_windowed(appname, layers, wnd) -> Gfx` — with a surface to present into.
- `g.gpu_name() -> str`, `g.shutdown()`.

Pass `["VK_LAYER_KHRONOS_validation"]` as `layers` to turn on the validation
layers — the demos wire this to a `--validate` flag, and it is worth running:
it caught two real bugs in the compute port (a storage buffer that needed
`readonly` in the fragment stage, and a `vkCmdPushConstants` stage-flag
mismatch).

**Buffers & memory**
- `g.buffer(size, usage, memflags) -> GpuBuffer`, `g.destroy_buffer(b)`.
- `g.read_buffer(b, n) -> Bytes` — map and copy back to the CPU.
- `g.alloc(size, typebits, flags)` / `g.find_mem_type(bits, flags)` — lower-level helpers.

**Shaders & pipelines**
- `g.shader(path) -> int` — load a compiled `.spv` into a shader module.
- `g.pipeline_layout(setlayouts, push_size, push_stages) -> int`.
- `g.compute_pipeline(shader, layout, entry) -> int`.
- `g.storage_set(buffers, stages) -> DescSet` — a descriptor set binding a list
  of storage buffers at bindings 0…n-1 (the shape almost every compute pass
  wants); `g.destroy_desc_set(d)`.

Graphics pipelines are built with the `structs.zeph` builders directly
(`VkGraphicsPipelineCreateInfo.new()…`) — see `examples/graphics` and the
`triangle`/`window` samples.

**Rendering**
- `g.surface_format() -> int`.
- `g.swapchain(format, renderpass, old) -> Swapchain`, `g.destroy_swapchain(s)`,
  `g.rebuild(s, renderpass) -> Swapchain?` (on resize; `none` while minimised).
- `g.frame(s, rec) -> bool` — acquire, record and present one frame; `rec` is a
  callback `fn(cmdbuf: int, imageIndex: int)`. Returns `false` when the
  swapchain is out of date (resized) so you can `rebuild`.
- `g.target(w, h, renderpass) -> Target` / `g.destroy_target(t)` — an offscreen
  render target; `g.readback(t) -> Bytes` pulls the pixels back.
- `g.immediate(rec)` — record and submit a one-shot command buffer;
  `rec` is `fn(cmdbuf: int)`.
- `g.fence(signalled)`, `g.semaphore()`.

Free helper: `write_bmp(path, px, w, h)` writes a `Bytes` pixel buffer to a BMP
(how the headless samples save their output).

## Shaders

Two ways to get a `.spv` module for `g.shader(…)`:

1. **GLSL** — write `.comp`/`.vert`/`.frag`, compile with the SDK's
   `glslangValidator -V shader.frag -o shader.frag.spv`. This is what the black
   hole demos use, because the geodesic integrator is easiest to read in GLSL.
2. **Zephyr shaders (`.zsh`)** — `tools/zspv.zeph` is a **Zephyr→SPIR-V
   compiler written in Zephyr**: the same lex/parse/emit shape as the main
   compiler, but it emits a SPIR-V 1.0 module directly (SSA ids instead of
   register allocation — no ABI, no relocations). Write the shader in Zephyr
   syntax and compile with `zspv.exe shader.zsh out.spv`. `scripts/build-shaders`
   drives both paths.

## The `examples/graphics` walkthrough

The graphics examples build up in difficulty, each a working program:

| Example | What it shows |
|---------|---------------|
| `particles.zeph` | CPU particle rasterizer — additive splatting into an integer grid, `StretchDIBits` to a GDI window. No GPU. |
| `particles_gl.zeph` | the same particles drawn through OpenGL 1.1 client arrays. |
| `particles_gpu.zeph` | a full **OpenGL transform-feedback** particle engine — state lives in two VBOs, a vertex shader integrates the physics, nothing crosses the bus. 1M particles. |
| `cube3d.zeph`, `ocean.zeph`, `fluid.zeph`, `liquid.zeph` | software 3D and fluid (SPH) demos, all pure-Zephyr CPU. |
| `ui_demo.zeph`, `ide.zeph` | the `lib/ui` immediate-mode toolkit — widgets, panels, a JetBrains-style IDE mock. |

### The black hole family

Six programs, each a real step up, sharing the same physics:

| Example | Renderer |
|---------|----------|
| `blackhole.zeph` | CPU software rasterizer — 24k particles, an accretion disc and the shadow. |
| `blackhole_gpu.zeph` | **OpenGL** transform-feedback — 1.5M particles of turbulent accretion (Paczyński–Wiita gravity, Shakura–Sunyaev α-viscosity, MRI turbulence), tone-mapped from an HDR float framebuffer. |
| `blackhole_vk.zeph` | **Vulkan**, a per-pixel geodesic ray-tracer — integrates the null geodesic `u″ = −u + 3Mu²` so the shadow, photon ring and the Interstellar-style halo emerge from light bending, with the whole scene in push constants (no vertex buffers, no descriptors). |
| `blackhole_vkp.zeph` | the OpenGL particle sim **ported to Vulkan compute** — an SSBO + `atomicAdd` into a fixed-point HDR buffer, resolved by a fragment shader. |
| `blackhole_vkl.zeph` | the two **merged** — particles deposit their density into a grid, and the geodesic ray-tracer samples it, so the simulated gas is gravitationally lensed. |
| `blackhole_tde.zeph` | a **tidal disruption event** — a self-gravitating star, deposited into a 3D voxel volume that the geodesic ray-march walks through. The star comes apart on its own at the tidal radius. |

The shaders for these live in `examples/shaders` (GLSL `.comp`/`.vert`/`.frag`
alongside their compiled `.spv`). A typical build-and-run:

```powershell
glslangValidator -V examples/shaders/blackhole.frag -o examples/shaders/blackhole.frag.spv
.\zc.exe --rt examples\graphics\blackhole_vk.zeph blackhole_vk.exe
.\blackhole_vk.exe                 # drag to orbit, wheel to zoom, Esc to quit
.\blackhole_vk.exe --validate      # with the Vulkan validation layers on
```

## Where to look next

- [spec.md §3.6](spec.md) — the native-interop primitives, normatively.
- `lib/vk/gfx.zeph` — the wrapper source; the method list above maps to it directly.
- `examples/vulkan/triangle.zeph`, `window.zeph`, `compute.zeph` — the smallest
  complete Vulkan programs (headless triangle, presented triangle, compute over
  a storage buffer).
- `lib/ui/README.md` — the immediate-mode GUI toolkit.
