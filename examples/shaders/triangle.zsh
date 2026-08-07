// The fragment shader for samples/triangle.zeph, written in Zephyr rather than
// GLSL and compiled by tools/zspv.zeph.

in vec3 vColor
out vec4 outColor

fn main() {
    outColor = vec4(vColor, 1.0)
}
