# Spike 3: Vulkan storage images

Implemented compute writes to a device-local RGBA8 2D storage image, numerical GPU readback, and transfer/blit presentation. Tested on the **NVIDIA GeForce RTX 5090**, using Vulkan SDK **1.4.357.0**. The default example is headless; `--present` additionally presents eight frames and exits.

## Files changed

| File | Change |
| --- | --- |
| `tools/vkgen.c` | Generate storage-image/layout/format-feature constants; `VkDescriptorImageInfo`, `VkImageBlit`, `VkMemoryBarrier`, `VkFormatProperties`; flattened blit offsets and image-barrier ranges. Generated creation helpers use off-heap output scratch. |
| `lib/vk/consts.zeph` | Regenerated sizes, offsets and constants from the installed SDK headers. |
| `lib/vk/structs.zeph` | Regenerated chainable Bytes builders and creation helpers. |
| `lib/vk/raw.zeph` | Add `vkCmdBlitImage`, `vkGetPhysicalDeviceFormatProperties`, and paired `vk_output`/`vk_free_output` helpers using VirtualAlloc/VirtualFree. |
| `lib/vk/gfx.zeph` | Add `GpuImage`, storage-image allocation/descriptors/destruction, format checks, explicit image barriers, RGBA8 image readback with transfer-to-host dependency, transfer-only swapchains, and configurable acquisition wait stage. Existing entry points forward with their original behavior; rebuild preserves usage. Move native output scratch off-heap. |
| `lib/vk/win.zeph` | Allocate native-written window message/rectangle scratch off-heap; release it on close. |
| `examples/vulkan/storage_image.zeph` | Top-level runnable example, compute-queue check, full-image CPU comparison, clear PASS/FAIL, optional finite swapchain presentation and cleanup. |
| `examples/shaders/storage_image.comp` | GLSL 450, 16x16 workgroups, bounds check, UV gradient and filled orange circle. |
| `examples/shaders/storage_image.comp.spv` | Compiled with SDK glslangValidator; validated with spirv-val for Vulkan 1.0. |
| `examples/vulkan/compute.zeph` | Fix pre-existing execution-only inter-dispatch barriers: add shader write-to-read/write memory dependency and shader-to-host dependency. Move mapping output scratch off-heap. |
| `spikes/SPIKE3_REPORT.md` | This report. |

`triangle.zeph` is unchanged. No compiler or language changes, sampler, fragment shader, or zspv use.

## Reproduce

Run from the repository root in PowerShell:

```powershell
& "$env:VULKAN_SDK\Bin\glslangValidator.exe" -V examples/shaders/storage_image.comp -o examples/shaders/storage_image.comp.spv
& "$env:VULKAN_SDK\Bin\spirv-val.exe" --target-env vulkan1.0 examples/shaders/storage_image.comp.spv
.\zc.exe --rt examples\vulkan\storage_image.zeph spikes\storage_image.exe
.\zc.exe --rt examples\vulkan\compute.zeph spikes\storage_regression_compute.exe
.\zc.exe --rt examples\vulkan\triangle.zeph spikes\storage_regression_triangle.exe
$env:VK_LAYER_VALIDATE_SYNC = "1"
$env:VK_LAYER_SYNCVAL_SHADER_ACCESSES_HEURISTIC = "1"
cmd /c ".\spikes\storage_image.exe --validate 2>&1"
cmd /c ".\spikes\storage_image.exe --validate --present 2>&1"
cmd /c ".\spikes\storage_regression_compute.exe --validate 2>&1"
cmd /c ".\spikes\storage_regression_triangle.exe --validate 2>&1"
```

The repo's `vk_layer_settings.txt` routes warnings/errors to stdout. A separate `VK_LOADER_DEBUG=layer` run confirmed that the Khronos validation DLL was inserted for both instance and device, and that the driver selected the RTX 5090. Synchronization settings follow the [LunarG validation documentation](https://vulkan.lunarg.com/doc/view/latest/windows/khronos_validation_layer.html).

## GPU evidence

All three final builds and all four final runs exited **0**, with no validation warnings/errors. Shader compilation and SPIR-V validation also exited **0**. Both generated binding files matched fresh generator output byte-for-byte; the checked-in SPIR-V matched a fresh GLSL compilation byte-for-byte. `git diff --check` passed.

Storage-image output (headless has the same pixel results and omits the presentation line):

```text
gpu: NVIDIA GeForce RTX 5090
dispatched 17 x 13 workgroups into 257x193 RGBA8 storage image
centre rgba = 255,64,16,255
corner rgba = 0,0,64,255
PASS: GPU readback verified 49601 pixels (7213 circle, 42388 gradient), 0 mismatches
PASS: blitted storage image and presented 8 swapchain frames
PASS: storage image resources destroyed cleanly
```

This is actual readback: `vkCmdCopyImageToBuffer` copies the optimal-tiled image into a HOST_VISIBLE | HOST_COHERENT staging allocation. A transfer-to-host memory barrier and fence wait precede `vkMapMemory`; the CPU then reads the mapped bytes and compares **every pixel**, allowing one UNORM quantization step for RGB and requiring alpha 255. Both circle and gradient must be present. The compute-write-to-transfer-read image barrier uses explicit access masks, following [Khronos synchronization guidance](https://docs.vulkan.org/guide/latest/synchronization_examples.html).

Negative control: compiled a temporary copy of the shader with `imageStore(target, p, vec4(0.0))`, and a temporary copy of the same verifier pointing to that SPIR-V. It ran on the GPU and correctly exited **1**:

```text
MISMATCH (0,0): got 0,0,0,0 expected 0,0,64,255
centre rgba = 0,0,0,0
corner rgba = 0,0,0,0
FAIL: storage image readback has 49601 mismatched pixels
panic: storage image GPU pixels disagree with CPU pattern
```

Regression output:

```text
[compute]
gpu: NVIDIA GeForce RTX 5090
storage buffer: 22 MB for 1500000 particles
seeded
compute pipeline ok
dispatched 8 steps x 5860 workgroups
verified 6 sampled particles, 0 mismatches
OK

[triangle]
gpu: NVIDIA GeForce RTX 5090
pipeline ok
drew
centre rgba = 252,77,61,255
corner rgba = 25,28,33,255
wrote out.bmp (512x512)
OK
```

## Gaps, fixes and limits

- Existing barriers and image-to-buffer copy bindings were reusable. Image descriptors and blitting were missing and are now implemented. No sampler is needed for this path; sampler support remains absent.
- Stronger shader-access synchronization validation exposed seven pre-existing WRITE_AFTER_WRITE diagnostics in `compute.zeph`. Its empty inter-dispatch barriers were fixed, not suppressed. Native-written scratch in the wrapper/generated creators/window helpers was also migrated off-heap.
- `Gfx.make` still selects a graphics/presentation queue without requiring compute. The new example checks the selected family's compute bit and fails clearly if absent; automatic selection of a different compute-capable family is not implemented.
- The existing surface format/present-mode policy is retained. Transfer-destination surface usage and both blit-format capabilities are checked. The finite presentation example fails clearly if the swapchain becomes out of date; it is not a resize stress test.
- The new convenience image/readback functions deliberately cover RGBA8, one mip, one layer and one queue. No general format conversion/readback framework or queue-family ownership transfers were added. The tests establish behavior on this GPU, not portability to every Vulkan device.

## 3D storage-image assessment

**Small wrapper addition, not a large redesign.** Add `VK_IMAGE_TYPE_3D` and `VK_IMAGE_VIEW_TYPE_3D`, carry depth through image creation/allocation/readback, use an `image3D` compute shader and a 3D dispatch, and check format/extent limits. The current descriptor, allocation and barrier machinery is reusable; `VkImageCreateInfo` already exposes depth. Add a numerical test sampling different depth slices before calling it proven.

A **voxel renderer** is a separate, larger task: volume traversal, scene representation, memory budgeting and rendering a 2D output image. Present that 2D result through the blit path added here. This spike does not implement or test 3D storage images.
