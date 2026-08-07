#version 450

// Resolve the HDR accumulation buffer to the swapchain: filmic tone map, sRGB
// encode, and one step of dither. The accumulation happened in 20.12 fixed
// point, so faint gas keeps its colour ratio all the way here -- which is what
// removes the olive banding an 8-bit additive framebuffer produces.

// readonly: the fragment stage only samples the accumulator. Without the
// NonWritable decoration this needs the fragmentStoresAndAtomics feature.
layout(std430, binding = 1) readonly buffer Accum { uint A[]; };

layout(push_constant) uniform PC {
    vec4 eye; vec4 right; vec4 up; vec4 fwd;
    vec4 disc; vec4 dims; vec4 phys; vec4 misc;
} pc;

layout(location = 0) out vec4 outColor;

vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

void main() {
    int W = int(pc.dims.x);
    ivec2 p = ivec2(gl_FragCoord.xy);
    uint b = uint((p.y * W + p.x) * 3);
    vec3 c = vec3(float(A[b]), float(A[b + 1u]), float(A[b + 2u])) / 4096.0;

    // The camera always looks at the hole, so it projects to the exact centre
    // of the screen: the photon ring is a circle of radius b_crit/|eye| there.
    vec2 ctr = vec2(pc.dims.x, pc.dims.y) * 0.5;
    float dl = length(pc.eye.xyz);
    float rpix = pc.dims.w / dl * pc.right.w;          // shadow radius, in pixels
    float d = length(gl_FragCoord.xy - ctr) / rpix;
    if (d > 1.0 && d < 1.7) {
        float t = (d - 1.0) / 0.7;
        c += vec3(1.0, 0.80, 0.56) * exp(-t * 7.0) * 0.9;
    }

    c = aces(c);
    c = pow(c, vec3(1.0 / 2.2));
    float dth = fract(sin(dot(gl_FragCoord.xy + pc.eye.w, vec2(12.9898, 78.233))) * 43758.5453);
    outColor = vec4(c + (dth - 0.5) / 255.0, 1.0);
}
