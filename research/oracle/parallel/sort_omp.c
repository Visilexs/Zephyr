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
    // research (M59): a library parallel sort: 4 chunks sorted in parallel,
    // then two rounds of pairwise merges. Integers, so the order is unique.
    long long *tmp = malloc((size_t)N * sizeof(long long));
    long bounds[5]; for (int c = 0; c <= 4; c++) bounds[c] = N * c / 4;
    #pragma omp parallel for schedule(static)
    for (int c = 0; c < 4; c++) qsort(a + bounds[c], (size_t)(bounds[c + 1] - bounds[c]), sizeof(long long), cmp);
    for (int width = 1; width < 4; width *= 2) {
        #pragma omp parallel for schedule(static)
        for (int c = 0; c < 4; c += 2 * width) {
            long lo = bounds[c], mid = bounds[c + width], hi = bounds[c + 2 * width], i = lo, j = mid, k = lo;
            while (i < mid && j < hi) tmp[k++] = a[i] <= a[j] ? a[i++] : a[j++];
            while (i < mid) tmp[k++] = a[i++];
            while (j < hi) tmp[k++] = a[j++];
        }
        long long *swap = a; a = tmp; tmp = swap;
    }
    long long chk = 0;
    for (long i = 0; i < N; i++)
        chk = (chk * 31 + a[i]) % 1000000007;
    printf("%lld\n", chk);
    return 0;
}
