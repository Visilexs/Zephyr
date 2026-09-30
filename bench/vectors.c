/* Small-value-struct benchmark: C reference for bench/vectors.zeph. Vec3 is
   passed and returned by value, so every temporary lives in registers.
   Same LCG, same checksum.
   Build: gcc -O2 -ffp-contract=off vectors.c -o vectors
   Usage: vectors [steps] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct { double x, y, z; } Vec3;

static Vec3 add(Vec3 a, Vec3 b) { return (Vec3){ a.x + b.x, a.y + b.y, a.z + b.z }; }
static Vec3 subtract(Vec3 a, Vec3 b) { return (Vec3){ a.x - b.x, a.y - b.y, a.z - b.z }; }
static Vec3 scale(Vec3 a, double factor) { return (Vec3){ a.x * factor, a.y * factor, a.z * factor }; }
static double dot(Vec3 a, Vec3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

static double randomUnit(void) { return (double)(nextRandom() % 20001 - 10000) / 10000.0; }

#define PARTICLE_COUNT 4000

int main(int argc, char **argv) {
    long long steps = argc > 1 ? atoll(argv[1]) : 1000;
    static Vec3 positions[PARTICLE_COUNT], velocities[PARTICLE_COUNT];
    for (int i = 0; i < PARTICLE_COUNT; i++) {
        double x = randomUnit();
        double y = randomUnit();
        double z = randomUnit();
        positions[i] = (Vec3){ x, y, z };
        velocities[i] = (Vec3){ 0.0, 0.0, 0.0 };
    }
    Vec3 anchor = { 0.25, -0.5, 0.125 };
    for (long long step = 0; step < steps; step++) {
        for (int i = 0; i < PARTICLE_COUNT; i++) {
            Vec3 position = positions[i];
            Vec3 offset = subtract(anchor, position);
            double distanceSquared = dot(offset, offset) + 0.01;
            Vec3 pull = scale(offset, 0.001 / distanceSquared);
            Vec3 drag = scale(velocities[i], 0.002);
            Vec3 velocity = subtract(add(velocities[i], pull), drag);
            velocities[i] = velocity;
            positions[i] = add(position, scale(velocity, 0.01));
        }
    }
    double total = 0.0;
    for (int i = 0; i < PARTICLE_COUNT; i++) {
        total += positions[i].x + 2.0 * positions[i].y + 3.0 * positions[i].z;
        total += velocities[i].x - velocities[i].y + velocities[i].z;
    }
    printf("%lld\n", (long long)(total * 1000000.0));
    return 0;
}
