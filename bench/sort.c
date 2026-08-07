/* Sorting benchmark: fixed pseudo-shuffle, qsort ascending, order-sensitive
   checksum. Same input and sorted order as sort.zeph/.rs => same checksum. */
#include <stdio.h>
#include <stdlib.h>

static int cmp(const void *a, const void *b) {
    long long x = *(const long long *)a, y = *(const long long *)b;
    return (x > y) - (x < y);
}

int main(int argc, char **argv) {
    long N = argc > 1 ? atol(argv[1]) : 3000000;
    long long *a = malloc((size_t)N * sizeof(long long));
    for (long i = 0; i < N; i++)
        a[i] = ((long long)i * 2654435761LL + 12345) % 1000003;
    qsort(a, (size_t)N, sizeof(long long), cmp);
    long long chk = 0;
    for (long i = 0; i < N; i++)
        chk = (chk * 31 + a[i]) % 1000000007;
    printf("%lld\n", chk);
    return 0;
}
