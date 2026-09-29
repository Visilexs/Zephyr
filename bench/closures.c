/* Higher-order-function benchmark: C reference for bench/closures.zeph.
   Every stage is a generic helper taking a function pointer plus a context
   struct holding the captured values. Bottom-up merge sort, as in Zephyr's
   std sortBy. Same LCG, same checksum.
   Build: gcc -O2 closures.c -o closures
   Usage: closures [count] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

typedef long long (*TransformFunction)(const void *context, long long value);
typedef int (*PredicateFunction)(const void *context, long long value);
typedef long long (*CombineFunction)(const void *context, long long total, long long value);
typedef long long (*CompareFunction)(const void *context, long long left, long long right);

static long long *mapInts(const long long *items, long long length, TransformFunction transform, const void *context) {
    long long *result = malloc((length ? length : 1) * sizeof *result);
    for (long long i = 0; i < length; i++) result[i] = transform(context, items[i]);
    return result;
}

static long long *filterInts(const long long *items, long long length, PredicateFunction keep, const void *context, long long *resultLength) {
    long long *result = malloc((length ? length : 1) * sizeof *result);
    long long keptCount = 0;
    for (long long i = 0; i < length; i++)
        if (keep(context, items[i])) result[keptCount++] = items[i];
    *resultLength = keptCount;
    return result;
}

static long long foldInts(const long long *items, long long length, long long start, CombineFunction combine, const void *context) {
    long long accumulator = start;
    for (long long i = 0; i < length; i++) accumulator = combine(context, accumulator, items[i]);
    return accumulator;
}

static int anyInts(const long long *items, long long length, PredicateFunction predicate, const void *context) {
    for (long long i = 0; i < length; i++)
        if (predicate(context, items[i])) return 1;
    return 0;
}

static void sortIntsBy(long long *items, long long length, CompareFunction compare, const void *context) {
    if (length < 2) return;
    long long *scratch = malloc(length * sizeof *scratch);
    for (long long width = 1; width < length; width *= 2) {
        for (long long start = 0; start < length; start += 2 * width) {
            long long middle = start + width < length ? start + width : length;
            long long end = middle + width < length ? middle + width : length;
            long long leftIndex = start, rightIndex = middle;
            for (long long i = start; i < end; i++) {
                if (leftIndex < middle && (rightIndex >= end || compare(context, items[leftIndex], items[rightIndex]) <= 0))
                    scratch[i] = items[leftIndex++];
                else
                    scratch[i] = items[rightIndex++];
            }
        }
        memcpy(items, scratch, length * sizeof *items);
    }
    free(scratch);
}

typedef struct AffineContext { long long multiplier, offset, modulus; } AffineContext;
static long long affineTransform(const void *context, long long value) {
    const AffineContext *affine = context;
    return (value * affine->multiplier + affine->offset) % affine->modulus;
}

typedef struct RemainderContext { long long divisor, remainder; } RemainderContext;
static int keepOtherRemainders(const void *context, long long value) {
    const RemainderContext *filter = context;
    return value % filter->divisor != filter->remainder;
}

typedef struct WeightContext { long long weight; } WeightContext;
static long long addWeighted(const void *context, long long total, long long value) {
    return total + value * ((const WeightContext *)context)->weight;
}

typedef struct MaskContext { long long mask; } MaskContext;
static long long compareMasked(const void *context, long long left, long long right) {
    long long mask = ((const MaskContext *)context)->mask;
    return (left ^ mask) - (right ^ mask);
}

typedef struct EqualsContext { long long target; } EqualsContext;
static int equalsTarget(const void *context, long long value) {
    return value == ((const EqualsContext *)context)->target;
}

int main(int argc, char **argv) {
    long long itemCount = argc > 1 ? atoll(argv[1]) : 200000;
    const long long rounds = 10;
    const long long modulus = 1000003;

    long long *data = malloc(itemCount * sizeof *data);
    for (long long i = 0; i < itemCount; i++) data[i] = nextRandom() % 1000000;

    uint64_t checksum = 0;
    for (long long round = 0; round < rounds; round++) {
        AffineContext affine = { round * 2 + 3, round * 7 + 1, modulus };
        RemainderContext remainderFilter = { round % 5 + 3, round % 3 };
        WeightContext weight = { round + 1 };
        MaskContext mask = { round * 12345 };
        EqualsContext threshold = { round * 1000 };

        long long *mapped = mapInts(data, itemCount, affineTransform, &affine);
        long long keptLength;
        long long *kept = filterInts(mapped, itemCount, keepOtherRemainders, &remainderFilter, &keptLength);
        long long weightedTotal = foldInts(kept, keptLength, 0, addWeighted, &weight);
        sortIntsBy(kept, keptLength, compareMasked, &mask);
        long long orderedTotal = 0;
        for (long long i = 0; i < keptLength; i++) orderedTotal += kept[i] * (i % 1000);
        int foundThreshold = anyInts(kept, keptLength, equalsTarget, &threshold);

        checksum = checksum * 31 + (uint64_t)weightedTotal;
        checksum = checksum * 31 + (uint64_t)orderedTotal;
        checksum = checksum * 31 + (uint64_t)keptLength + (uint64_t)(foundThreshold ? 1 : 0);
        free(mapped);
        free(kept);
    }
    printf("%lld\n", (long long)checksum);
    return 0;
}
