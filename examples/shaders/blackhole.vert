#version 450

// One oversized triangle covering the screen. No vertex buffers, no
// descriptors -- the whole image is produced by the fragment shader.
void main() {
    vec2 p = vec2(float((gl_VertexIndex << 1) & 2), float(gl_VertexIndex & 2));
    gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}
