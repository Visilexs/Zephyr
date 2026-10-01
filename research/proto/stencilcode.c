// Code quality of a simple copy-and-patch tier (Q8). Stencil code keeps every
// SSA value in a frame slot: each op loads its operands from the frame and
// stores its result back, with no register allocation across ops. That is
// modelled here with a volatile frame array, on the same kernels as
// research/proto/interp.c (fib, bounds-checked sum, mandel). Same results.
// Build: gcc -O2 -o stencilcode research/proto/stencilcode.c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
typedef int64_t i64;
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

static i64 sfib(i64 n) {                 // frame: 0 n, 1 t, 2 a, 3 b
    volatile i64 f[4]; f[0] = n;
    f[1] = f[0] < 2; if (f[1]) return f[0];
    f[1] = f[0] - 1; f[2] = sfib(f[1]);
    f[1] = f[0] - 2; f[3] = sfib(f[1]);
    f[1] = f[2] + f[3]; return f[1];
}
static i64 ssum(const i64 *a, i64 n, int reps) {   // frame: 0 s, 1 r, 2 i, 3 t, 4 x
    volatile i64 f[5]; f[0] = 0;
    for (f[1] = 0; f[1] < reps; f[1] = f[1] + 1)
        for (f[2] = 0; (f[3] = f[2] < n); f[2] = f[2] + 1) {
            if ((uint64_t)f[2] >= (uint64_t)n) abort();
            f[4] = a[f[2]]; f[0] = f[0] + f[4];
        }
    return f[0];
}
static i64 smandel(int size) {           // frame of doubles and ints, one slot per value
    volatile double d[10]; volatile i64 k[5]; k[0] = 0;
    for (k[1] = 0; k[1] < size; k[1] = k[1] + 1) for (k[2] = 0; k[2] < size; k[2] = k[2] + 1) {
        d[0] = k[2] * (3.0 / size) - 2.0; d[1] = k[1] * (2.0 / size) - 1.0; d[2] = 0; d[3] = 0; k[3] = 0;
        for (;;) {
            if (!(k[3] < 50)) break;
            d[4] = d[2] * d[2]; d[5] = d[3] * d[3]; d[6] = d[4] + d[5]; if (!(d[6] < 4.0)) break;
            d[7] = d[4] - d[5]; d[7] = d[7] + d[0]; d[8] = 2 * d[2]; d[8] = d[8] * d[3]; d[3] = d[8] + d[1]; d[2] = d[7];
            k[3] = k[3] + 1;
        }
        k[0] = k[0] + k[3];
    }
    return k[0];
}
static i64 nfib(i64 n) { return n < 2 ? n : nfib(n - 1) + nfib(n - 2); }
int main(void) {
    i64 n = 1000000; i64 *a = malloc(8 * n); for (i64 i = 0; i < n; i++) a[i] = i % 7;
    double t0 = now(); i64 r1 = sfib(32); double t1 = now(); i64 r2 = ssum(a, n, 50); double t2 = now(); i64 r3 = smandel(600); double t3 = now();
    double u0 = now(); i64 q1 = nfib(32); double u1 = now();
    printf("stencil-style: fib(32) %.1f ms (native %.1f ms), sum %.1f ms, mandel %.1f ms   [%lld %lld %lld %s]\n",
           (t1 - t0) * 1e3, (u1 - u0) * 1e3, (t2 - t1) * 1e3, (t3 - t2) * 1e3, (long long)r1, (long long)r2, (long long)r3, r1 == q1 ? "ok" : "MISMATCH");
    return 0;
}
