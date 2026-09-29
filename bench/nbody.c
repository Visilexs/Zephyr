/* Struct-heavy float benchmark: C reference for bench/nbody.zeph. Same LCG,
   same operation order, same checksum.
   Build: gcc -O2 -ffp-contract=off nbody.c -o nbody -lm
   Usage: nbody [steps] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

#define BODY_COUNT 1000
#define TIME_STEP 0.001
#define SOFTENING 0.01

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

typedef struct Body { double x, y, z, vx, vy, vz, mass; } Body;

static Body makeBody(void) {
    Body body;
    body.x = (double)(nextRandom() % 20001 - 10000) / 1000.0;
    body.y = (double)(nextRandom() % 20001 - 10000) / 1000.0;
    body.z = (double)(nextRandom() % 20001 - 10000) / 1000.0;
    body.vx = (double)(nextRandom() % 2001 - 1000) / 10000.0;
    body.vy = (double)(nextRandom() % 2001 - 1000) / 10000.0;
    body.vz = (double)(nextRandom() % 2001 - 1000) / 10000.0;
    body.mass = (double)(nextRandom() % 1000 + 1) / 1000.0;
    return body;
}

static void advance(Body *bodies, int count) {
    for (int i = 0; i < count; i++) {
        Body *first = &bodies[i];
        for (int j = i + 1; j < count; j++) {
            Body *second = &bodies[j];
            double deltaX = first->x - second->x;
            double deltaY = first->y - second->y;
            double deltaZ = first->z - second->z;
            double distanceSquared = deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ + SOFTENING;
            double distance = sqrt(distanceSquared);
            double magnitude = TIME_STEP / (distanceSquared * distance);
            double secondPull = second->mass * magnitude;
            double firstPull = first->mass * magnitude;
            first->vx -= deltaX * secondPull;
            first->vy -= deltaY * secondPull;
            first->vz -= deltaZ * secondPull;
            second->vx += deltaX * firstPull;
            second->vy += deltaY * firstPull;
            second->vz += deltaZ * firstPull;
        }
    }
    for (int i = 0; i < count; i++) {
        Body *body = &bodies[i];
        body->x += TIME_STEP * body->vx;
        body->y += TIME_STEP * body->vy;
        body->z += TIME_STEP * body->vz;
    }
}

static double energy(const Body *bodies, int count) {
    double total = 0.0;
    for (int i = 0; i < count; i++) {
        const Body *first = &bodies[i];
        total += 0.5 * first->mass * (first->vx * first->vx + first->vy * first->vy + first->vz * first->vz);
        for (int j = i + 1; j < count; j++) {
            const Body *second = &bodies[j];
            double deltaX = first->x - second->x;
            double deltaY = first->y - second->y;
            double deltaZ = first->z - second->z;
            total -= first->mass * second->mass / sqrt(deltaX * deltaX + deltaY * deltaY + deltaZ * deltaZ + SOFTENING);
        }
    }
    return total;
}

int main(int argc, char **argv) {
    long long steps = argc > 1 ? atoll(argv[1]) : 100;
    static Body bodies[BODY_COUNT];
    for (int i = 0; i < BODY_COUNT; i++) bodies[i] = makeBody();
    for (long long step = 0; step < steps; step++) advance(bodies, BODY_COUNT);

    uint64_t checksum = (uint64_t)(long long)(energy(bodies, BODY_COUNT) * 1000000000.0);
    for (int i = 0; i < BODY_COUNT; i++) {
        checksum = checksum * 31 + (uint64_t)(long long)(bodies[i].x * 1000000.0);
        checksum = checksum * 31 + (uint64_t)(long long)(bodies[i].y * 1000000.0);
        checksum = checksum * 31 + (uint64_t)(long long)(bodies[i].z * 1000000.0);
    }
    printf("%lld\n", (long long)checksum);
    return 0;
}
