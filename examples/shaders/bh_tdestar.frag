#version 450

// Geodesic ray-tracing of a Schwarzschild black hole whose disc is a LIVE
// PARTICLE SIMULATION.
//
// Per pixel we integrate the exact null geodesic backwards from the camera,
//
//     d2u/dphi2 = -u + 3 M u^2        (u = 1/r)
//
// until the ray hits the disc plane, falls through the horizon, or escapes. The
// 3Mu^2 term is general relativity: it produces the shadow at sqrt(27) r_g, the
// photon ring, and the halo of the far disc lifted over the hole.
//
// Where the ray strikes the disc we look up the (r, phi) density grid that the
// compute pass just filled from 1.5M orbiting particles. So the gas is not
// painted on -- the clumps and spiral streamers are the simulation's, and
// because they are sampled at the RAY's crossing point rather than projected to
// the screen, they get lensed too: turbulent structure from the far side of the
// disc appears in the arch above the shadow.

layout(std430, binding = 1) readonly buffer Grid { uint G[]; };
layout(std430, binding = 2) readonly buffer Star { float S[]; };

layout(push_constant) uniform PC {
    vec4 eye;    // xyz camera, w time
    vec4 right;  // xyz basis,  w tan(fov/2)*aspect
    vec4 up;     // xyz basis,  w tan(fov/2)
    vec4 fwd;    // xyz basis,  w frame
    vec4 disc;   // r_isco, r_out, T_scale, exposure
    vec4 dims;   // W, H, NR, NPHI
    vec4 phys;   // alpha, H/R, turbulence, dt
    vec4 misc;   // r_horizon, r_escape, count, T_ref
} pc;

layout(location = 0) out vec4 outColor;

const float M    = 1.0;
const float RHOR = 2.0;
const float RESC = 900.0;
const float TAU  = 6.28318530718;
const float DPHI = 0.02;
const int   NSTEP = 420;

vec3 blackbody(float K) {
    float t = clamp(K, 1000.0, 40000.0) / 100.0;
    float r, g, b;
    if (t <= 66.0) { r = 255.0; } else { r = 329.698727446 * pow(t - 60.0, -0.1332047592); }
    if (t <= 66.0) { g = 99.4708025861 * log(t) - 161.1195681661; }
    else           { g = 288.1221695283 * pow(t - 60.0, -0.0755148492); }
    if (t >= 66.0)      { b = 255.0; }
    else if (t <= 19.0) { b = 0.0; }
    else                { b = 138.5177312231 * log(t - 10.0) - 305.0447927307; }
    return clamp(vec3(r, g, b) / 255.0, 0.0, 1.0);
}

float h31(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }

vec3 stars(vec3 d) {
    vec3 c = d * 210.0;
    vec3 i = floor(c);
    float h = h31(i);
    if (h < 0.9964) return vec3(0.0);
    vec3 f = fract(c) - 0.5;
    float s = exp(-dot(f, f) * 85.0) * (0.30 + 1.5 * fract(h * 137.0));
    return vec3(s) * mix(vec3(0.72, 0.80, 1.0), vec3(1.0, 0.87, 0.68), fract(h * 53.0));
}

// Distance from a segment to a point -- the star is a real 3D ball, and the
// ray reaching it is already bent, so it is intersected in world space along
// the geodesic rather than projected to the screen.
float seg_dist(vec3 a, vec3 b, vec3 c) {
    vec3 ab = b - a;
    float t = clamp(dot(c - a, ab) / max(dot(ab, ab), 1e-9), 0.0, 1.0);
    return length(a + ab * t - c);
}

vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

// bilinear sample of the particle density grid, wrapping in phi
float density(float r, float ang) {
    int NR = int(pc.dims.z), NPHI = int(pc.dims.w);
    float rout = pc.disc.y;
    float fr = r / rout * float(NR) - 0.5;
    float fp = ang / TAU * float(NPHI) - 0.5;
    int r0 = int(floor(fr)), p0 = int(floor(fp));
    float tr = fr - float(r0), tp = fp - float(p0);
    float acc = 0.0;
    for (int dr = 0; dr < 2; dr++) {
        int ri = clamp(r0 + dr, 0, NR - 1);
        float wr = (dr == 0) ? (1.0 - tr) : tr;
        for (int dp = 0; dp < 2; dp++) {
            int pi = (p0 + dp) % NPHI;
            if (pi < 0) pi += NPHI;
            float wp = (dp == 0) ? (1.0 - tp) : tp;
            acc += wr * wp * float(G[ri * NPHI + pi]);
        }
    }
    // counts -> surface density, normalised by the disc mean so a smooth disc
    // sits at 1.0 and clumps rise above it
    float cellA = (rout / float(NR)) * max(r, 0.5) * (TAU / float(NPHI));
    float sigma = acc / max(cellA, 1e-4);
    float risco = pc.disc.x;
    float sigma0 = pc.misc.z / (3.14159265 * (rout * rout - risco * risco));
    return sigma / max(sigma0, 1e-4);
}

void main() {
    vec2 res = vec2(pc.dims.x, pc.dims.y);
    vec2 uv = (gl_FragCoord.xy / res) * 2.0 - 1.0;
    uv.y = -uv.y;
    vec3 dir = normalize(pc.fwd.xyz + pc.right.xyz * uv.x * pc.right.w
                                    + pc.up.xyz    * uv.y * pc.up.w);
    vec3 cam = pc.eye.xyz;
    float t = pc.eye.w;

    float r0 = length(cam);
    vec3 e1 = cam / r0;
    vec3 nrm = cross(e1, dir);
    float nl = length(nrm);
    if (nl < 1e-7) { outColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
    nrm /= nl;
    vec3 e2 = cross(nrm, e1);

    float u  = 1.0 / r0;
    float du = -dot(dir, e1) / (r0 * nl);

    float phi = 0.0, sPrev = e1.y, rPrev = r0, phiPrev = 0.0;
    float risco = pc.disc.x, rout = pc.disc.y;

    vec3  com  = vec3(S[0], S[1], S[2]);
    float Rst  = S[3];
    bool  torn = S[5] > 0.5;
    vec3  Pprev = cam;

    for (int i = 0; i < NSTEP; i++) {
        float a1 = -u + 3.0 * M * u * u;
        float un = u + du * DPHI + 0.5 * a1 * DPHI * DPHI;
        float a2 = -un + 3.0 * M * un * un;
        du += 0.5 * (a1 + a2) * DPHI;
        u = un;
        phi += DPHI;
        if (u <= 0.0) break;
        float r = 1.0 / u;
        if (r <= RHOR) { outColor = vec4(0.0, 0.0, 0.0, 1.0); return; }   // the shadow

        vec3 Pnow = r * (cos(phi) * e1 + sin(phi) * e2);
        if (!torn) {
            float sd = seg_dist(Pprev, Pnow, com);
            if (sd < Rst) {
                // a hot white dwarf: limb-darkened, and blue-white beside the
                // orange disc because it is genuinely ~20000 K
                float lm = sqrt(max(1.0 - (sd / Rst) * (sd / Rst), 0.0));
                vec3 col = blackbody(20000.0) * (0.35 + 2.6 * lm) * 1.6;
                col = pow(aces(col), vec3(1.0 / 2.2));
                outColor = vec4(col, 1.0);
                return;
            }
        }
        Pprev = Pnow;

        float s = cos(phi) * e1.y + sin(phi) * e2.y;
        if (s * sPrev < 0.0) {
            float f = sPrev / (sPrev - s);
            float phic = phiPrev + f * DPHI;
            float rc = mix(rPrev, r, f);
            if (rc > risco && rc < rout) {
                float cp = cos(phic), sp = sin(phic);
                vec3 P = rc * (cp * e1 + sp * e2);

                // how much gas the simulation actually put here
                float ang = atan(P.z, P.x);
                if (ang < 0.0) ang += TAU;
                float dens = density(rc, ang);
                if (dens > 0.002) {
                    float drdphi = -du * rc * rc;
                    vec3 dm = normalize(drdphi * (cp * e1 + sp * e2)
                                      + rc * (-sp * e1 + cp * e2));
                    vec3 nobs = -dm;

                    vec3 phat = normalize(vec3(-P.z, 0.0, P.x));
                    float beta = sqrt(M / rc) / sqrt(max(1.0 - 2.0 * M / rc, 1e-4));
                    float dtau = sqrt(max(1.0 - 3.0 * M / rc, 1e-4));
                    float g = dtau / max(1.0 - dot(phat * beta, nobs), 0.05);

                    float fr = max(1.0 - sqrt(risco / rc), 0.0);
                    float Te = pc.disc.z * pow(fr / (rc * rc * rc), 0.25);
                    float To = g * Te;
                    float x = max(To, 1.0) / pc.misc.w;
                    float I = x * x * x * x * pc.disc.w * dens;   // I_obs = g^4 I_emit
                    vec3 col = blackbody(To) * I;

                    col = pow(aces(col), vec3(1.0 / 2.2));
                    float d = fract(sin(dot(gl_FragCoord.xy + t, vec2(12.9898, 78.233))) * 43758.5453);
                    outColor = vec4(col + (d - 0.5) / 255.0, 1.0);
                    return;
                }
                // a gap in the gas: the ray carries on through
            }
        }
        sPrev = s; rPrev = r; phiPrev = phi;
        if (r > RESC && du < 0.0) break;
    }

    float cp = cos(phi), sp = sin(phi);
    float drdphi = -du * rPrev * rPrev;
    vec3 dfin = normalize(drdphi * (cp * e1 + sp * e2) + rPrev * (-sp * e1 + cp * e2));
    outColor = vec4(pow(aces(stars(dfin)), vec3(1.0 / 2.2)), 1.0);
}
