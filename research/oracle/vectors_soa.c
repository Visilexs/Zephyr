/* Bound for what SoA flattening + loop vectorization could give vectors.zeph:
   the flattened (SoA) loop from research/oracle/vectors_values.zeph in C, built
   with and without AVX2. Same operation order per particle, so results match the
   scalar version bit for bit (no reassociation, no FMA contraction). */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static int64_t rngState = 12345;
static int64_t nextRandom(void) { rngState = (int64_t)((uint64_t)rngState * 6364136223846793005ull + 1442695040888963407ull); return (rngState >> 33) & 2147483647; }
static double randomUnit(void) { return (double)(nextRandom() % 20001 - 10000) / 10000.0; }
#define N 4000
static double px[N], py[N], pz[N], vx[N], vy[N], vz[N];
int main(int argc, char **argv) {
    int steps = argc > 1 ? atoi(argv[1]) : 1000;
    for (int i = 0; i < N; i++) { px[i] = randomUnit(); py[i] = randomUnit(); pz[i] = randomUnit(); vx[i] = vy[i] = vz[i] = 0; }
    const double ax = 0.25, ay = -0.5, az = 0.125;
    for (int s = 0; s < steps; s++)
        for (int i = 0; i < N; i++) {
            double ox = ax - px[i], oy = ay - py[i], oz = az - pz[i];
            double d = ox * ox + oy * oy + oz * oz + 0.01, f = 0.001 / d;
            double nx = vx[i] + ox * f - vx[i] * 0.002, ny = vy[i] + oy * f - vy[i] * 0.002, nz = vz[i] + oz * f - vz[i] * 0.002;
            vx[i] = nx; vy[i] = ny; vz[i] = nz;
            px[i] += nx * 0.01; py[i] += ny * 0.01; pz[i] += nz * 0.01;
        }
    double total = 0;
    for (int i = 0; i < N; i++) { total += px[i] + 2.0 * py[i] + 3.0 * pz[i]; total += vx[i] - vy[i] + vz[i]; }
    printf("%lld\n", (long long)(total * 1000000.0));
    return 0;
}
