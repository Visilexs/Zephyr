/* Hash-map benchmark: open-addressing (linear-probe) table over colliding
   integer keys, last write wins, then sum looked-up values.
   Matches hashmap.zeph/.rs (same keys, same last-write-wins semantics). */
#include <stdio.h>
#include <stdlib.h>

#define CAP (1 << 21)   /* 2,097,152 slots, comfortably > 500,009 live keys */

int main(int argc, char **argv) {
    long N = argc > 1 ? atol(argv[1]) : 2000000;
    long long *keys = malloc((size_t)CAP * sizeof(long long));
    long long *vals = malloc((size_t)CAP * sizeof(long long));
    char *used = calloc(CAP, 1);

    for (long i = 0; i < N; i++) {
        long long k = ((long long)i * 2654435761LL) % 500009;
        unsigned long long h = (unsigned long long)k * 11400714819323198485ULL;
        long slot = (long)(h >> 43) & (CAP - 1);
        while (used[slot] && keys[slot] != k) slot = (slot + 1) & (CAP - 1);
        used[slot] = 1; keys[slot] = k; vals[slot] = i;
    }

    long long chk = 0;
    for (long i = 0; i < N; i++) {
        long long k = ((long long)i * 2654435761LL) % 500009;
        unsigned long long h = (unsigned long long)k * 11400714819323198485ULL;
        long slot = (long)(h >> 43) & (CAP - 1);
        while (used[slot] && keys[slot] != k) slot = (slot + 1) & (CAP - 1);
        chk += used[slot] ? vals[slot] : 0;
    }
    printf("%lld\n", chk);
    return 0;
}
