#version 450

// Per-pixel backwards geodesic ray-tracing of a Schwarzschild black hole.
//
// Everything is in geometrized units, r_g = GM/c^2 = 1 and c = 1, so the
// geometry is exact: horizon at 2, photon sphere at 3, ISCO at 6.
//
// For each pixel we fire a ray from the camera and integrate the NULL GEODESIC
// backwards until it either falls through the horizon, escapes to infinity, or
// strikes the accretion disc. Photon motion in Schwarzschild is planar, and in
// the orbital plane with u = 1/r it obeys the exact orbit equation
//
//     d2u/dphi2 = -u + 3 M u^2
//
// The 3Mu^2 term is the whole of general relativity here: drop it and you get a
// straight line. Keeping it is what bends light around the hole, and it makes
// three things appear on their own, with nothing drawn by hand:
//
//   * the SHADOW, at its true apparent radius sqrt(27) r_g -- rays inside it
//     spiral through the horizon no matter which way they were aimed
//   * the PHOTON RING, where rays loop the photon sphere many times before
//     escaping, piling many images of the disc into a razor-thin arc
//   * the HALO, the far side of the disc lifted up and over the hole, plus the
//     underside curled beneath it -- the image that a flat-space renderer can
//     never produce, because the disc behind the hole is simply hidden
//
// Emission is the same physics as the particle version: a Novikov-Thorne
// blackbody disc with relativistic Doppler beaming and gravitational redshift.

layout(push_constant) uniform PC {
    vec4 eye;     // xyz camera position (r_g),      w = time (r_g/c)
    vec4 right;   // xyz camera right basis vector,  w = tan(fov/2)*aspect
    vec4 up;      // xyz camera up basis vector,     w = tan(fov/2)
    vec4 fwd;     // xyz camera forward basis vector
    vec4 disc;    // r_isco, r_out, T_scale, exposure
    vec4 misc;    // turbulence, res.x, res.y, step count
    vec4 phys;    // T_ref, dphi, 0, 0
} pc;

layout(location = 0) out vec4 outColor;

const float M    = 1.0;      // gravitational radius = 1 by construction
const float RHOR = 2.0;      // event horizon, 2M
const float RESC = 900.0;    // far enough to call it escaped

// ---------------- Planck blackbody locus -> sRGB ----------------
// (fit to Mitchell Charity's tabulated blackbody colours)
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

// ---------------- value noise, for the turbulent gas ----------------
float h31(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float vn(vec3 x) {
    vec3 i = floor(x); vec3 f = fract(x);
    f = f * f * (3.0 - 2.0 * f);
    float a = mix(h31(i + vec3(0,0,0)), h31(i + vec3(1,0,0)), f.x);
    float b = mix(h31(i + vec3(0,1,0)), h31(i + vec3(1,1,0)), f.x);
    float c = mix(h31(i + vec3(0,0,1)), h31(i + vec3(1,0,1)), f.x);
    float d = mix(h31(i + vec3(0,1,1)), h31(i + vec3(1,1,1)), f.x);
    return mix(mix(a, b, f.y), mix(c, d, f.y), f.z);
}
float fbm(vec3 x) { return 0.60 * vn(x) + 0.28 * vn(x * 2.03) + 0.12 * vn(x * 4.07); }

// ---------------- background stars ----------------
// Sampled with the ray's FINAL direction, so the star field is gravitationally
// lensed too: look near the shadow's edge and the sky is visibly smeared.
vec3 stars(vec3 d) {
    vec3 c = d * 210.0;
    vec3 i = floor(c);
    float h = h31(i);
    if (h < 0.9964) return vec3(0.0);
    vec3 f = fract(c) - 0.5;
    float s = exp(-dot(f, f) * 85.0) * (0.30 + 1.5 * fract(h * 137.0));
    return vec3(s) * mix(vec3(0.72, 0.80, 1.0), vec3(1.0, 0.87, 0.68), fract(h * 53.0));
}

// ---------------- ACES filmic tone curve (Narkowicz 2015) ----------------
vec3 aces(vec3 x) {
    return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

void main() {
    vec2 res = vec2(pc.misc.y, pc.misc.z);
    vec2 uv = (gl_FragCoord.xy / res) * 2.0 - 1.0;
    uv.y = -uv.y;                                   // Vulkan framebuffer Y runs down
    vec3 dir = normalize(pc.fwd.xyz
                       + pc.right.xyz * uv.x * pc.right.w
                       + pc.up.xyz    * uv.y * pc.up.w);
    vec3 cam = pc.eye.xyz;
    float t = pc.eye.w;

    // ---- set up the photon's orbital plane ----
    // The trajectory stays in the plane spanned by the camera position and the
    // ray, so the problem is 2D: e1 points at the camera (phi = 0) and e2 is
    // the direction phi advances in.
    float r0 = length(cam);
    vec3 e1 = cam / r0;
    vec3 nrm = cross(e1, dir);
    float nl = length(nrm);
    if (nl < 1e-7) { outColor = vec4(0.0, 0.0, 0.0, 1.0); return; }  // dead centre
    nrm /= nl;
    vec3 e2 = cross(nrm, e1);

    // u = 1/r, and du/dphi from the ray's radial vs tangential split
    float u  = 1.0 / r0;
    float du = -dot(dir, e1) / (r0 * nl);

    float dphi = pc.phys.y;
    int   N    = int(pc.misc.w);

    float phi  = 0.0;
    float sPrev = e1.y;      // sign of the world-y coordinate at phi = 0
    float rPrev = r0;
    float phiPrev = 0.0;

    for (int i = 0; i < N; i++) {
        // one velocity-Verlet step of  u'' = -u + 3 M u^2
        float a1 = -u + 3.0 * M * u * u;
        float un = u + du * dphi + 0.5 * a1 * dphi * dphi;
        float a2 = -un + 3.0 * M * un * un;
        du += 0.5 * (a1 + a2) * dphi;
        u = un;
        phi += dphi;

        if (u <= 0.0) break;                       // turned around at infinity
        float r = 1.0 / u;
        if (r <= RHOR) {                           // through the horizon: the shadow
            outColor = vec4(0.0, 0.0, 0.0, 1.0);
            return;
        }

        // world y changes sign exactly when the ray crosses the disc plane
        float s = cos(phi) * e1.y + sin(phi) * e2.y;
        if (s * sPrev < 0.0) {
            float f = sPrev / (sPrev - s);
            float phic = phiPrev + f * dphi;
            float rc = mix(rPrev, r, f);
            if (rc > pc.disc.x && rc < pc.disc.y) {
                // ---------------- hit the disc ----------------
                float cp = cos(phic), sp = sin(phic);
                vec3 P = rc * (cp * e1 + sp * e2);
                // tangent to the trajectory = the direction we were marching
                float drdphi = -du * rc * rc;
                vec3 dP = drdphi * (cp * e1 + sp * e2) + rc * (-sp * e1 + cp * e2);
                vec3 dm = normalize(dP);
                vec3 nobs = -dm;                   // emitter -> observer

                // Keplerian orbit, prograde about +Y. The LOCAL orbital speed
                // measured by a static observer; 0.5c at the ISCO.
                vec3 phat = normalize(vec3(-P.z, 0.0, P.x));
                float beta = sqrt(M / rc) / sqrt(max(1.0 - 2.0 * M / rc, 1e-4));
                vec3 vorb = phat * beta;

                // dtau/dt for a circular geodesic: gravitational redshift and
                // time dilation together, vanishing at the photon sphere
                float dtau = sqrt(max(1.0 - 3.0 * M / rc, 1e-4));
                float g = dtau / max(1.0 - dot(vorb, nobs), 0.05);

                // Novikov-Thorne thin-disc temperature, peaking at 8.17 r_g
                float fr = max(1.0 - sqrt(pc.disc.x / rc), 0.0);
                float Te = pc.disc.z * pow(fr / (rc * rc * rc), 0.25);
                float To = g * Te;

                // turbulent gas: the pattern co-rotates with the flow, so
                // differential rotation shears it into spirals by itself
                float om = sqrt(M / (rc * rc * rc));
                float ang = atan(P.z, P.x) - om * t;
                vec3 np = vec3(rc * 0.30, cos(ang) * rc * 0.10, sin(ang) * rc * 0.10);
                float dens = mix(1.0 - pc.misc.x, 1.0 + pc.misc.x, fbm(np));

                // I_obs = g^4 I_emit and I ~ T^4, so brightness is just T_obs^4
                float x = max(To, 1.0) / pc.phys.x;
                float I = x * x * x * x * pc.disc.w * max(dens, 0.0);
                vec3 col = blackbody(To) * I;

                col = aces(col);
                col = pow(col, vec3(1.0 / 2.2));
                float dth = fract(sin(dot(gl_FragCoord.xy + t, vec2(12.9898, 78.233))) * 43758.5453);
                outColor = vec4(col + (dth - 0.5) / 255.0, 1.0);
                return;
            }
        }

        sPrev = s; rPrev = r; phiPrev = phi;
        if (r > RESC && du < 0.0) break;            // outbound and far away
    }

    // ---- escaped: the (lensed) sky ----
    float cp = cos(phi), sp = sin(phi);
    float drdphi = -du * rPrev * rPrev;
    vec3 dfin = normalize(drdphi * (cp * e1 + sp * e2) + rPrev * (-sp * e1 + cp * e2));
    vec3 col = stars(dfin);
    col = pow(aces(col), vec3(1.0 / 2.2));
    outColor = vec4(col, 1.0);
}
