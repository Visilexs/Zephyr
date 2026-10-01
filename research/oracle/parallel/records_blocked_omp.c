/* Record-table benchmark: C reference for bench/records.zeph. Records are
   stored inline in one contiguous array of structs.
   Same LCG, same operation order, same checksum.
   Build: gcc -O2 -ffp-contract=off records.c -o records
   Usage: records [count]
   research (M59): update loop in parallel, and the three reduction loops as
   64 fixed blocks (summed in block order): deterministic for any thread
   count, but float sums are reassociated relative to the serial program. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

typedef struct Record {
    long long id;
    long long category;
    long long quantity;
    long long flags;
    double price;
    double weight;
    double score;
    double discount;
} Record;

int main(int argc, char **argv) {
    long long count = argc > 1 ? atoll(argv[1]) : 1000000;
    const long long rounds = 40;

    Record *records = malloc(count * sizeof(Record));
    for (long long i = 0; i < count; i++) {
        Record *record = &records[i];
        record->id = i;
        record->category = nextRandom() % 8;
        record->quantity = nextRandom() % 1000;
        record->flags = nextRandom() % 16;
        record->price = (double)(nextRandom() % 100000) / 100.0;
        record->weight = (double)(nextRandom() % 10000) / 100.0;
        record->score = (double)(nextRandom() % 1000) / 10.0;
        record->discount = (double)(nextRandom() % 500) / 1000.0;
    }

    uint64_t checksum = 0;
    for (long long round = 0; round < rounds; round++) {
        long long targetCategory = round % 8;
        double revenue = 0.0;
        long long matchedCount = 0;
        { double pr[64] = {0}; long long pm[64] = {0};
          #pragma omp parallel for schedule(static)
          for (int b = 0; b < 64; b++) {
            long long lo = count * b / 64, hi = count * (b + 1) / 64;
            for (long long i = lo; i < hi; i++)
              if (records[i].category == targetCategory) { pr[b] += records[i].price * (double)records[i].quantity; pm[b]++; }
          }
          for (int b = 0; b < 64; b++) { revenue += pr[b]; matchedCount += pm[b]; } }

        long long flagBit = 1LL << (round % 4);
        long long heavyCount = 0;
        double heavyScore = 0.0;
        { double ps[64] = {0}; long long pc[64] = {0};
          #pragma omp parallel for schedule(static)
          for (int b = 0; b < 64; b++) {
            long long lo = count * b / 64, hi = count * (b + 1) / 64;
            for (long long i = lo; i < hi; i++)
              if (records[i].weight > 50.0 && (records[i].flags & flagBit) != 0 && records[i].quantity < 500) { pc[b]++; ps[b] += records[i].score; }
          }
          for (int b = 0; b < 64; b++) { heavyCount += pc[b]; heavyScore += ps[b]; } }

        double categoryTotals[8] = {0};
        long long categoryQuantities[8] = {0};
        { static double pt[64][8]; static long long pq[64][8];
          #pragma omp parallel for schedule(static)
          for (int b = 0; b < 64; b++) {
            for (int c = 0; c < 8; c++) { pt[b][c] = 0; pq[b][c] = 0; }
            long long lo = count * b / 64, hi = count * (b + 1) / 64;
            for (long long i = lo; i < hi; i++) { pt[b][records[i].category] += records[i].weight * records[i].discount; pq[b][records[i].category] += records[i].quantity; }
          }
          for (int b = 0; b < 64; b++) for (int c = 0; c < 8; c++) { categoryTotals[c] += pt[b][c]; categoryQuantities[c] += pq[b][c]; } }

        #pragma omp parallel for schedule(static)
        for (long long i = 0; i < count; i++) {
            Record *record = &records[i];
            record->quantity = (record->quantity * 7 + round + record->id) % 1000;
            record->score = record->score * 0.5 + record->price * 0.25;
            if ((record->flags & 1) != 0) record->price = record->price + record->discount;
            record->flags = (record->flags * 5 + 1) & 15;
            record->discount = record->discount * 0.75;
        }

        checksum = checksum * 31 + (uint64_t)(long long)(revenue * 100.0) + (uint64_t)matchedCount;
        checksum = checksum * 31 + (uint64_t)(long long)(heavyScore * 100.0) + (uint64_t)heavyCount;
        for (int i = 0; i < 8; i++)
            checksum = checksum * 31 + (uint64_t)(long long)(categoryTotals[i] * 1000.0) + (uint64_t)categoryQuantities[i];
    }
    printf("%lld\n", (long long)checksum);
    return 0;
}
