// vxngx - a flat C shim over NVIDIA NGX, for Zephyr's int-only FFI.
//
// Why this file exists: NVIDIA ships the app-facing NGX API only as a STATIC
// library (nvsdk_ngx_s.lib). There is no app-callable NGX DLL - nvngx_dlssd.dll
// is the feature module the driver loads, not an export surface. Zephyr's FFI is
// LoadLibraryA + GetProcAddress, i.e. DLL-only, so it cannot reach a .lib at all.
//
// This shim is the bridge. It also earns its keep: every NGX struct is laid out
// by the real headers here in C, so the Zephyr side never hand-computes an
// offset. Exports take and return only scalars and raw pointers.

#include <stdint.h>
#include <string.h>

// nvsdk_ngx_vk.h uses VkInstance/VkImageView/... but does not include Vulkan
// itself, so this order is load-bearing.
#include <vulkan/vulkan.h>
#include "nvsdk_ngx_vk.h"

#define EXPORT __declspec(dllexport)

// Bumped whenever an export's signature changes, so the Zephyr side can refuse
// to run against a stale DLL instead of corrupting the stack.
EXPORT int32_t vxngx_abi(void) { return 1; }

static size_t append(char *buf, size_t cap, size_t off, const char *s)
{
    if (!s) return off;
    size_t n = strlen(s);
    if (off + n + 2 > cap) return off;          // silently stop; caller sees a short list
    memcpy(buf + off, s, n);
    off += n;
    buf[off++] = '\n';
    return off;
}

// Flattens NGX's `const char ***` extension lists into one newline-separated,
// NUL-terminated blob: instance extensions first, then a "--\n" marker, then
// device extensions. Walking a pointer-to-pointer-to-pointer from Zephyr would
// be three load64 chains per string; this is one buffer read.
//
// Needs no VkInstance or VkDevice, which is exactly why it is the right call to
// prove the toolchain with.
EXPORT int32_t vxngx_required_extensions(char *buf, int32_t buflen,
                                         int32_t *out_inst_count,
                                         int32_t *out_dev_count)
{
    unsigned int ic = 0, dc = 0;
    const char **iv = 0, **dv = 0;

    if (buf && buflen > 0) buf[0] = 0;
    if (out_inst_count) *out_inst_count = 0;
    if (out_dev_count)  *out_dev_count  = 0;

    NVSDK_NGX_Result r = NVSDK_NGX_VULKAN_RequiredExtensions(&ic, &iv, &dc, &dv);
    if (r != NVSDK_NGX_Result_Success) return (int32_t)r;

    if (out_inst_count) *out_inst_count = (int32_t)ic;
    if (out_dev_count)  *out_dev_count  = (int32_t)dc;

    if (!buf || buflen <= 0) return (int32_t)r;

    size_t cap = (size_t)buflen;
    size_t off = 0;
    for (unsigned int i = 0; i < ic; i++) off = append(buf, cap, off, iv[i]);
    off = append(buf, cap, off, "--");
    for (unsigned int i = 0; i < dc; i++) off = append(buf, cap, off, dv[i]);
    buf[off < cap ? off : cap - 1] = 0;
    return (int32_t)r;
}
