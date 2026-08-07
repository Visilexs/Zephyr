#version 450

// Volumetric geodesic ray-marching: the gas is a 3D VOLUME, and the ray that
// samples it is bent by gravity.
//
// Per pixel we integrate the exact null geodesic  d2u/dphi2 = -u + 3 M u^2
// backwards from the camera, and at every step we sample a 3D cylindrical
// density grid filled by the particle simulation, accumulating emission and
// absorption along the way. There is no disc plane anywhere in here: the flow
// has real thickness, the debris stream is three-dimensional, and the star is
// just the densest part of the same volume.
//
// The shadow, photon ring and the halo of the far disc lifted over the hole all
// still fall out of the 3Mu^2 term.

layout(std430, binding = 1) readonly buffer Vox  { uint V[]; };
layout(std430, binding = 2) readonly buffer Star { float S[]; };

layout(push_constant) uniform PC {
    vec4 eye;    // xyz camera, w time
    vec4 right;  // xyz basis, w tan(fov/2)*aspect
    vec4 up;     // xyz basis, w tan(fov/2)
    vec4 fwd;    // xyz basis, w frame
    vec4 disc;   // r_isco, r_grid, T_scale, exposure
    vec4 dims;   // W, H, NR, NPHI
    vec4 phys;   // alpha, H/R, turbulence, dt
    vec4 misc;   // r_horizon, r_escape, count, T_ref
} pc;

layout(location = 0) out vec4 outColor;

const float M    = 1.0;
const float RHOR = 2.0;
const float RESC = 900.0;
const float TAU  = 6.28318530718;
const float DPHI = 0.022;
const int   NSTEP = 400;

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
    vec3 c = d * 210.0; vec3 i = floor(c);
    float h = h31(i);
    if (h < 0.9964) return vec3(0.0);
    vec3 f = fract(c) - 0.5;
    float s = exp(-dot(f, f) * 85.0) * (0.30 + 1.5 * fract(h * 137.0));
    return vec3(s) * mix(vec3(0.72, 0.80, 1.0), vec3(1.0, 0.87, 0.68), fract(h * 53.0));
}
vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
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
    float phi = 0.0, rPrev = r0;
    vec3  Pprev = cam;

    int   NR   = int(pc.dims.z), NPHI = int(pc.dims.w);
    int   NZ   = int(S[12]);
    float ZEXT = S[13];
    float rgrid = pc.disc.y, risco = pc.disc.x;
    float Tref = pc.misc.w, Tscale = pc.disc.z, expo = pc.disc.w;
    // mean particles per voxel, so a smooth disc normalises to about 1
    float norm = pc.misc.z / (float(NR) * float(NPHI) * float(NZ)) * 40.0;

    vec3  accum = vec3(0.0);
    float trans = 1.0;

    for (int i = 0; i < NSTEP; i++) {
        float a1 = -u + 3.0 * M * u * u;
        float un = u + du * DPHI + 0.5 * a1 * DPHI * DPHI;
        float a2 = -un + 3.0 * M * un * un;
        du += 0.5 * (a1 + a2) * DPHI;
        u = un;
        phi += DPHI;
        if (u <= 0.0) break;
        float r = 1.0 / u;
        if (r <= RHOR) { trans = 0.0; break; }          // through the horizon

        vec3 Pnow = r * (cos(phi) * e1 + sin(phi) * e2);
        float seglen = length(Pnow - Pprev);

        // ---- sample the 3D volume at this step ----
        float rp = length(Pnow.xz);
        if (rp < rgrid && rp > 0.2 && abs(Pnow.y) < ZEXT) {
            float ang = atan(Pnow.z, Pnow.x);
            if (ang < 0.0) ang += TAU;
            // trilinear in (r, phi, z), wrapping in phi -- nearest-neighbour
            // made the star a visible cube at this voxel size
            float fr2 = rp / rgrid * float(NR) - 0.5;
            float fp2 = ang / TAU * float(NPHI) - 0.5;
            float fz2 = (Pnow.y + ZEXT) / (2.0 * ZEXT) * float(NZ) - 0.5;
            int r0i = int(floor(fr2)), p0i = int(floor(fp2)), z0i = int(floor(fz2));
            float tr = fr2 - float(r0i), tp = fp2 - float(p0i), tz = fz2 - float(z0i);
            float dgas = 0.0, dstar = 0.0;
            for (int dr2 = 0; dr2 < 2; dr2++) {
                int ri = clamp(r0i + dr2, 0, NR - 1);
                float wr = (dr2 == 0) ? (1.0 - tr) : tr;
                for (int dp2 = 0; dp2 < 2; dp2++) {
                    int pi2 = (p0i + dp2) % NPHI; if (pi2 < 0) pi2 += NPHI;
                    float wp = (dp2 == 0) ? (1.0 - tp) : tp;
                    for (int dz2 = 0; dz2 < 2; dz2++) {
                        int zi = clamp(z0i + dz2, 0, NZ - 1);
                        float wz = (dz2 == 0) ? (1.0 - tz) : tz;
                        float w = wr * wp * wz;
                        int idx = ((ri * NPHI + pi2) * NZ + zi) * 2;
                        dgas  += w * float(V[idx]);
                        dstar += w * float(V[idx + 1]);
                    }
                }
            }
            dgas /= norm; dstar /= norm;
            float dens = dgas + dstar;
            if (dens > 0.01) {
                // Doppler and redshift from the local circular orbit; exact for
                // the disc, approximate for debris still settling
                vec3 nobs = normalize(cam - Pnow);
                vec3 phat = normalize(vec3(-Pnow.z, 0.0, Pnow.x));
                float rr = max(rp, risco);
                float beta = sqrt(M / rr) / sqrt(max(1.0 - 2.0 * M / rr, 1e-4));
                float dtau = sqrt(max(1.0 - 3.0 * M / max(r, 3.01), 1e-4));
                float g = dtau / max(1.0 - dot(phat * beta, nobs), 0.05);

                vec3 emis = vec3(0.0);
                if (dgas > 0.0) {
                    float fr = max(1.0 - sqrt(risco / rr), 0.0);
                    float Te = Tscale * pow(fr / (rr * rr * rr), 0.25);
                    float To = g * Te;
                    float x = max(To, 1.0) / Tref;
                    emis += blackbody(To) * (x * x * x * x) * dgas;
                }
                if (dstar > 0.0) {
                    // stellar material: a hot white dwarf, blue-white beside
                    // the orange disc because it really is ~20000 K
                    float To = g * 20000.0;
                    float x = max(To, 1.0) / Tref;
                    emis += blackbody(To) * (x * x * x * x) * dstar * 0.004;
                }
                float dl = seglen;
                accum += trans * emis * expo * dl;
                trans *= exp(-dens * 0.28 * dl);         // self-absorption
                if (trans < 0.01) break;
            }
        }
        Pprev = Pnow;
        rPrev = r;
        if (r > RESC && du < 0.0) break;
    }

    // whatever light still gets through comes from the sky behind
    if (trans > 0.01) {
        float cp = cos(phi), sp = sin(phi);
        float drdphi = -du * rPrev * rPrev;
        vec3 dfin = normalize(drdphi * (cp * e1 + sp * e2) + rPrev * (-sp * e1 + cp * e2));
        accum += trans * stars(dfin);
    }

    vec3 col = pow(aces(accum), vec3(1.0 / 2.2));
    float d = fract(sin(dot(gl_FragCoord.xy + t, vec2(12.9898, 78.233))) * 43758.5453);
    outColor = vec4(col + (d - 0.5) / 255.0, 1.0);
}
