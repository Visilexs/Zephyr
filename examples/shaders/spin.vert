#version 450
layout(push_constant) uniform Push { float angle; float aspect; } pc;
vec2 positions[3] = vec2[](vec2(0.0, -0.62), vec2(0.56, 0.36), vec2(-0.56, 0.36));
vec3 colors[3] = vec3[](vec3(1.0, 0.25, 0.2), vec3(1.0, 0.62, 0.15), vec3(0.92, 0.13, 0.42));
layout(location = 0) out vec3 vColor;
void main() {
    vec2 p = positions[gl_VertexIndex];
    float s = sin(pc.angle), c = cos(pc.angle);
    p = vec2(p.x * c - p.y * s, p.x * s + p.y * c);
    p.x /= pc.aspect;
    gl_Position = vec4(p, 0.0, 1.0);
    vColor = colors[gl_VertexIndex];
}
