// Per-operation cost of reference-count updates under three schemes, single
// thread, uncontended (the common case):
//   plain    non-atomic increment/decrement (Zephyr today)
//   atomic   lock-prefixed increment/decrement on every update
//   biased   owner-thread check, then a plain update (biased reference
//            counting: only non-owner threads pay for atomics)
// Each loop does one retain + one release per object over an array of objects,
// like a traversal that borrows nothing. A compiler barrier keeps gcc from
// cancelling each plain retain/release pair.
// Build: gcc -O2 -o rccost research/proto/rccost.c
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

typedef struct Obj { int64_t count; int64_t owner; int64_t payload; } Obj;
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

int main(void) {
    enum { N = 4096, REPS = 50000 };
    Obj *objs = calloc(N, sizeof(Obj)); Obj **refs = malloc(N * sizeof(Obj *));
    for (int i = 0; i < N; i++) { objs[i].count = 1; objs[i].owner = 7; refs[i] = &objs[(i * 2654435761u) % N]; }
    volatile int64_t me = 7; int64_t sink = 0;
    double t0 = now();
    for (int r = 0; r < REPS; r++) for (int i = 0; i < N; i++) { Obj *o = refs[i]; o->count++; __asm__ volatile("" ::: "memory"); sink += o->payload; if (--o->count == 0) abort(); }
    double plain = now() - t0;
    t0 = now();
    for (int r = 0; r < REPS; r++) for (int i = 0; i < N; i++) { Obj *o = refs[i]; atomic_fetch_add_explicit((_Atomic int64_t *)&o->count, 1, memory_order_relaxed); sink += o->payload;
        if (atomic_fetch_sub_explicit((_Atomic int64_t *)&o->count, 1, memory_order_acq_rel) == 1) abort(); }
    double atomic = now() - t0;
    t0 = now();
    for (int r = 0; r < REPS; r++) for (int i = 0; i < N; i++) { Obj *o = refs[i];
        if (o->owner == me) o->count++; else atomic_fetch_add_explicit((_Atomic int64_t *)&o->count, 1, memory_order_relaxed);
        __asm__ volatile("" ::: "memory");
        sink += o->payload;
        if (o->owner == me) { if (--o->count == 0) abort(); } else if (atomic_fetch_sub_explicit((_Atomic int64_t *)&o->count, 1, memory_order_acq_rel) == 1) abort(); }
    double biased = now() - t0;
    double ops = 2.0 * N * REPS;
    printf("per retain/release op: plain %.2f ns, atomic %.2f ns, biased %.2f ns (sink %lld)\n", plain / ops * 1e9, atomic / ops * 1e9, biased / ops * 1e9, (long long)sink);
    return 0;
}
