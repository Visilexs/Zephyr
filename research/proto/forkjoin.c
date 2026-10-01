// What does automatic loop parallelism cost and gain? Measures (1) the round-trip
// latency of an empty parallel-for on a spinning thread pool (the minimum grain
// a compiler must require before splitting a loop), and (2) the vectors kernel
// in SoA form (research/oracle/vectors_soa.c) split across 1..T threads, with
// one fork-join per time step, exactly as auto-parallelization of the inner
// loop would produce. Results must match the serial run bit for bit.
// Build: gcc -O2 -pthread -o forkjoin research/proto/forkjoin.c
// Usage: forkjoin [threads] [steps]
#include <pthread.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define N 4000
static double px[N], py[N], pz[N], vx[N], vy[N], vz[N];
static int threads;
static _Atomic long generation; static _Atomic int done;
static void (*task)(int lo, int hi);

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

static void chunk(int id, void (*f)(int, int)) { int lo = (int)((long)N * id / threads), hi = (int)((long)N * (id + 1) / threads); f(lo, hi); }

static void *worker(void *arg) {
    int id = (int)(long)arg; long seen = 0;
    for (;;) {
        long g;
        while ((g = atomic_load_explicit(&generation, memory_order_acquire)) == seen) __builtin_ia32_pause();
        if (g < 0) return 0;
        seen = g;
        chunk(id, task);
        atomic_fetch_add_explicit(&done, 1, memory_order_release);
    }
}

static void parallelFor(void (*f)(int, int)) {
    task = f; atomic_store(&done, 0);
    atomic_fetch_add_explicit(&generation, 1, memory_order_release);
    chunk(0, f);
    while (atomic_load_explicit(&done, memory_order_acquire) != threads - 1) __builtin_ia32_pause();
}

static void nothing(int lo, int hi) { (void)lo; (void)hi; }
static void stepRange(int lo, int hi) {
    const double ax = 0.25, ay = -0.5, az = 0.125;
    for (int i = lo; i < hi; i++) {
        double ox = ax - px[i], oy = ay - py[i], oz = az - pz[i];
        double d = ox * ox + oy * oy + oz * oz + 0.01, f = 0.001 / d;
        double nx = vx[i] + ox * f - vx[i] * 0.002, ny = vy[i] + oy * f - vy[i] * 0.002, nz = vz[i] + oz * f - vz[i] * 0.002;
        vx[i] = nx; vy[i] = ny; vz[i] = nz;
        px[i] += nx * 0.01; py[i] += ny * 0.01; pz[i] += nz * 0.01;
    }
}

static int64_t rngState = 12345;
static int64_t nextRandom(void) { rngState = (int64_t)((uint64_t)rngState * 6364136223846793005ull + 1442695040888963407ull); return (rngState >> 33) & 2147483647; }
static double randomUnit(void) { return (double)(nextRandom() % 20001 - 10000) / 10000.0; }

int main(int argc, char **argv) {
    threads = argc > 1 ? atoi(argv[1]) : 4;
    int steps = argc > 2 ? atoi(argv[2]) : 35000;
    pthread_t t[64];
    for (int i = 1; i < threads; i++) pthread_create(&t[i], 0, worker, (void *)(long)i);
    // (1) empty parallel-for round trip
    int reps = 200000; double t0 = now();
    for (int r = 0; r < reps; r++) parallelFor(nothing);
    double empty = (now() - t0) / reps;
    // (2) the vectors kernel; checksum at the given step count
    rngState = 12345;
    for (int i = 0; i < N; i++) { px[i] = randomUnit(); py[i] = randomUnit(); pz[i] = randomUnit(); vx[i] = vy[i] = vz[i] = 0; }
    t0 = now();
    for (int s = 0; s < steps; s++) parallelFor(stepRange);
    double kernel = now() - t0;
    double total = 0;
    for (int i = 0; i < N; i++) { total += px[i] + 2.0 * py[i] + 3.0 * pz[i]; total += vx[i] - vy[i] + vz[i]; }
    printf("threads %d: empty parallel-for %.2f us, kernel %.1f ms (%.2f us per step), checksum %.17g\n",
           threads, empty * 1e6, kernel * 1e3, kernel / steps * 1e6, total);
    atomic_store(&generation, -1);
    for (int i = 1; i < threads; i++) pthread_join(t[i], 0);
    return 0;
}
