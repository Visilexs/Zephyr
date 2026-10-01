/* Megamorphic dispatch benchmark: C reference for bench/dispatch.zeph. Each
   object starts with a pointer to a vtable of function pointers; the list
   holds pointers to heap-allocated objects of eight types.
   Same LCG, same operation order, same checksum.
   Build: gcc -O2 dispatch.c -o dispatch
   Usage: dispatch [count] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

#define valueMask 1048575LL

typedef struct TransformVtable {
    long long (*apply)(const void *transform, long long value);
    long long (*weight)(const void *transform);
} TransformVtable;

typedef struct Transform { const TransformVtable *vtable; } Transform;

typedef struct Adder { const TransformVtable *vtable; long long amount; } Adder;
typedef struct Multiplier { const TransformVtable *vtable; long long factor; } Multiplier;
typedef struct XorMasker { const TransformVtable *vtable; long long key; } XorMasker;
typedef struct Rotator { const TransformVtable *vtable; long long shift; } Rotator;
typedef struct Clamper { const TransformVtable *vtable; long long low, high; } Clamper;
typedef struct AffineMixer { const TransformVtable *vtable; long long scale, offset; } AffineMixer;
typedef struct Divider { const TransformVtable *vtable; long long divisor; } Divider;
typedef struct Complementer { const TransformVtable *vtable; long long bias; } Complementer;

static long long adderApply(const void *transform, long long value) { return (value + ((const Adder *)transform)->amount) & valueMask; }
static long long adderWeight(const void *transform) { return ((const Adder *)transform)->amount & 7; }

static long long multiplierApply(const void *transform, long long value) { return (value * ((const Multiplier *)transform)->factor) & valueMask; }
static long long multiplierWeight(const void *transform) { (void)transform; return 1; }

static long long xorMaskerApply(const void *transform, long long value) { return value ^ ((const XorMasker *)transform)->key; }
static long long xorMaskerWeight(const void *transform) { (void)transform; return 2; }

static long long rotatorApply(const void *transform, long long value) {
    long long shift = ((const Rotator *)transform)->shift;
    return ((value << shift) | (value >> (20 - shift))) & valueMask;
}
static long long rotatorWeight(const void *transform) { return ((const Rotator *)transform)->shift; }

static long long clamperApply(const void *transform, long long value) {
    const Clamper *clamper = transform;
    if (value < clamper->low) return clamper->low;
    if (value > clamper->high) return clamper->high;
    return value;
}
static long long clamperWeight(const void *transform) { (void)transform; return 3; }

static long long affineMixerApply(const void *transform, long long value) {
    const AffineMixer *mixer = transform;
    return (value * mixer->scale + mixer->offset) & valueMask;
}
static long long affineMixerWeight(const void *transform) { (void)transform; return 4; }

static long long dividerApply(const void *transform, long long value) {
    long long divisor = ((const Divider *)transform)->divisor;
    return value / divisor + divisor * 1000;
}
static long long dividerWeight(const void *transform) { return ((const Divider *)transform)->divisor; }

static long long complementerApply(const void *transform, long long value) { return (valueMask - value + ((const Complementer *)transform)->bias) & valueMask; }
static long long complementerWeight(const void *transform) { (void)transform; return 5; }

static const TransformVtable adderVtable = { adderApply, adderWeight };
static const TransformVtable multiplierVtable = { multiplierApply, multiplierWeight };
static const TransformVtable xorMaskerVtable = { xorMaskerApply, xorMaskerWeight };
static const TransformVtable rotatorVtable = { rotatorApply, rotatorWeight };
static const TransformVtable clamperVtable = { clamperApply, clamperWeight };
static const TransformVtable affineMixerVtable = { affineMixerApply, affineMixerWeight };
static const TransformVtable dividerVtable = { dividerApply, dividerWeight };
static const TransformVtable complementerVtable = { complementerApply, complementerWeight };

static Transform *makeTransform(void) {
    long long kind = nextRandom() % 8;
    if (kind == 0) {
        Adder *adder = malloc(sizeof *adder);
        adder->vtable = &adderVtable;
        adder->amount = nextRandom() % 1000;
        return (Transform *)adder;
    }
    if (kind == 1) {
        Multiplier *multiplier = malloc(sizeof *multiplier);
        multiplier->vtable = &multiplierVtable;
        multiplier->factor = nextRandom() % 64 + 1;
        return (Transform *)multiplier;
    }
    if (kind == 2) {
        XorMasker *masker = malloc(sizeof *masker);
        masker->vtable = &xorMaskerVtable;
        masker->key = nextRandom() & valueMask;
        return (Transform *)masker;
    }
    if (kind == 3) {
        Rotator *rotator = malloc(sizeof *rotator);
        rotator->vtable = &rotatorVtable;
        rotator->shift = nextRandom() % 19 + 1;
        return (Transform *)rotator;
    }
    if (kind == 4) {
        Clamper *clamper = malloc(sizeof *clamper);
        clamper->vtable = &clamperVtable;
        clamper->low = nextRandom() % 100000;
        clamper->high = clamper->low + nextRandom() % 900000;
        return (Transform *)clamper;
    }
    if (kind == 5) {
        AffineMixer *mixer = malloc(sizeof *mixer);
        mixer->vtable = &affineMixerVtable;
        mixer->scale = nextRandom() % 32 + 1;
        mixer->offset = nextRandom() % 1000;
        return (Transform *)mixer;
    }
    if (kind == 6) {
        Divider *divider = malloc(sizeof *divider);
        divider->vtable = &dividerVtable;
        divider->divisor = nextRandom() % 16 + 1;
        return (Transform *)divider;
    }
    Complementer *complementer = malloc(sizeof *complementer);
    complementer->vtable = &complementerVtable;
    complementer->bias = nextRandom() % 1000;
    return (Transform *)complementer;
}

int main(int argc, char **argv) {
    long long count = argc > 1 ? atoll(argv[1]) : 1000000;
    const long long rounds = 20;

    Transform **transforms = malloc(count * sizeof(Transform *));
    for (long long i = 0; i < count; i++) transforms[i] = makeTransform();

    // research (M59): loop distribution. Rounds are independent apart from
    // the checksum fold, so they run in parallel into per-round slots and the
    // fold runs serially afterwards, in round order.
    long long values[64], weights[64];
    #pragma omp parallel for schedule(dynamic, 1)
    for (long long round = 0; round < rounds; round++) {
        long long value = round;
        long long weightTotal = 0;
        for (long long i = 0; i < count; i++) {
            Transform *transform = transforms[i];
            value = transform->vtable->apply(transform, value);
            weightTotal += transform->vtable->weight(transform);
        }
        values[round] = value;
        weights[round] = weightTotal;
    }
    uint64_t checksum = 0;
    for (long long round = 0; round < rounds; round++) {
        checksum = checksum * 31 + (uint64_t)values[round];
        checksum = checksum * 31 + (uint64_t)weights[round];
    }
    printf("%lld\n", (long long)checksum);
    return 0;
}
