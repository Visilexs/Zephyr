/* Benchmark: particle-based viscoelastic fluid (Clavet et al. 2005).
   C reference for bench/liquid.zeph -- same algorithm, same order of
   operations, same checksum. Build: gcc -O2 -ffp-contract=off liquid.c -o liquid
   Usage: liquid <steps> */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define W 320
#define H 240
#define N 6000
#define RADIUS 7.0
#define DT 1.0
#define GRAV 0.09
#define REST 4.5
#define K 0.055
#define KNEAR 0.28
#define SIGMA 0.03
#define BETA 0.06
#define GW (W / 7 + 1)
#define GH (H / 7 + 1)
#define CELLS (GW * GH)
#define CAP 40

static double px[N], py[N], ox[N], oy[N], vx[N], vy[N];
static long long cnt[CELLS];
static long long bucket[CELLS * CAP];
static long long nbr[256];
static double nd[256];

static long long clampi(long long v, long long lo, long long hi) {
    if (v < lo) return lo;
    if (v > hi) return hi;
    return v;
}

static void build_grid(void) {
    for (long long c = 0; c < CELLS; c++) cnt[c] = 0;
    for (long long i = 0; i < N; i++) {
        long long cx = clampi((long long)(px[i] / RADIUS), 0, GW - 1);
        long long cy = clampi((long long)(py[i] / RADIUS), 0, GH - 1);
        long long k = cy * GW + cx;
        long long n = cnt[k];
        if (n < CAP) {
            bucket[k * CAP + n] = i;
            cnt[k] = n + 1;
        }
    }
}

static long long neighbours(long long i) {
    double xi = px[i], yi = py[i];
    long long cx = clampi((long long)(xi / RADIUS), 0, GW - 1);
    long long cy = clampi((long long)(yi / RADIUS), 0, GH - 1);
    long long n = 0;
    for (long long gy = cy - 1; gy <= cy + 1; gy++) {
        if (gy < 0 || gy >= GH) continue;
        for (long long gx = cx - 1; gx <= cx + 1; gx++) {
            if (gx < 0 || gx >= GW) continue;
            long long k = gy * GW + gx;
            long long m = cnt[k];
            for (long long s = 0; s < m; s++) {
                long long j = bucket[k * CAP + s];
                if (j != i && n < 256) {
                    double dx = px[j] - xi;
                    double dy = py[j] - yi;
                    double d2 = dx * dx + dy * dy;
                    if (d2 < RADIUS * RADIUS) {
                        nbr[n] = j;
                        nd[n] = 1.0 - sqrt(d2) / RADIUS;
                        n++;
                    }
                }
            }
        }
    }
    return n;
}

static void viscosity(void) {
    for (long long i = 0; i < N; i++) {
        long long n = neighbours(i);
        for (long long s = 0; s < n; s++) {
            long long j = nbr[s];
            if (j > i) {
                double q = nd[s];
                double dx = px[j] - px[i];
                double dy = py[j] - py[i];
                double dist = sqrt(dx * dx + dy * dy);
                if (dist > 0.0001) {
                    dx = dx / dist;
                    dy = dy / dist;
                    double u = (vx[i] - vx[j]) * dx + (vy[i] - vy[j]) * dy;
                    if (u > 0.0) {
                        double im = DT * q * (SIGMA * u + BETA * u * u) * 0.5;
                        if (im > u * 0.5) im = u * 0.5;
                        vx[i] -= dx * im;
                        vy[i] -= dy * im;
                        vx[j] += dx * im;
                        vy[j] += dy * im;
                    }
                }
            }
        }
    }
}

static void relax(void) {
    for (long long i = 0; i < N; i++) {
        long long n = neighbours(i);
        double rho = 0.0, rho_near = 0.0;
        for (long long s = 0; s < n; s++) {
            double q = nd[s];
            rho += q * q;
            rho_near += q * q * q;
        }
        double pres = K * (rho - REST);
        double pres_near = KNEAR * rho_near;
        double dxi = 0.0, dyi = 0.0;
        for (long long s = 0; s < n; s++) {
            long long j = nbr[s];
            double q = nd[s];
            double dx = px[j] - px[i];
            double dy = py[j] - py[i];
            double dist = sqrt(dx * dx + dy * dy);
            if (dist > 0.0001) {
                dx = dx / dist;
                dy = dy / dist;
                double d = DT * DT * (pres * q + pres_near * q * q) * 0.5;
                px[j] += dx * d;
                py[j] += dy * d;
                dxi -= dx * d;
                dyi -= dy * d;
            }
        }
        px[i] += dxi;
        py[i] += dyi;
    }
}

static void step(void) {
    double wf = (double)W, hf = (double)H;
    for (long long i = 0; i < N; i++) vy[i] += GRAV * DT;
    build_grid();
    viscosity();
    for (long long i = 0; i < N; i++) {
        ox[i] = px[i];
        oy[i] = py[i];
        px[i] += vx[i] * DT;
        py[i] += vy[i] * DT;
    }
    build_grid();
    relax();
    for (long long i = 0; i < N; i++) {
        if (px[i] < 1.0) px[i] = 1.0;
        if (px[i] > wf - 2.0) px[i] = wf - 2.0;
        if (py[i] < 1.0) py[i] = 1.0;
        if (py[i] > hf - 2.0) py[i] = hf - 2.0;
        vx[i] = (px[i] - ox[i]) / DT;
        vy[i] = (py[i] - oy[i]) / DT;
    }
}

int main(int argc, char **argv) {
    long long steps = argc > 1 ? atoll(argv[1]) : 400;
    long long cols = 46;
    for (long long i = 0; i < N; i++) {
        px[i] = 4.0 + (double)(i % cols) * 1.72;
        py[i] = 236.0 - (double)(i / cols) * 1.72;
    }
    for (long long s = 0; s < steps; s++) step();
    long long chk = 0;
    for (long long i = 0; i < N; i++) {
        chk += (long long)(px[i] * 1000.0) * 3 + (long long)(py[i] * 1000.0) * 7;
        chk += (long long)(vx[i] * 1000.0) * 11 + (long long)(vy[i] * 1000.0) * 13;
    }
    printf("%lld\n", chk);
    return 0;
}
