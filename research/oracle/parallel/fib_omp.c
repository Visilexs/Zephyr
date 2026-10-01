/* Recursion benchmark, parallel oracle (research M59). fib is pure (no global
   writes), so a compiler may expand the call tree to a fixed depth and run the
   leaves as a dynamic parallel loop; integer + makes the sum exact.
   OpenMP tasks (#pragma omp task + taskwait) reached only ~2.2x on 4 cores:
   libgomp's task scheduling leaves threads idle. The explicit leaf list gets 4.0x. */
#include <stdio.h>
#include <stdlib.h>

long long fib(long long n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

static long long leaves[1 << 12];
static int leafCount = 0;
static void expand(long long n, int depth) {
    if (depth == 10 || n < 20) { leaves[leafCount++] = n; return; }
    expand(n - 1, depth + 1);
    expand(n - 2, depth + 1);
}

int main(int argc, char **argv) {
    long long N = argc > 1 ? atoll(argv[1]) : 35;
    expand(N, 0);
    long long total = 0;
    #pragma omp parallel for reduction(+:total) schedule(dynamic, 1)
    for (int i = 0; i < leafCount; i++) total += fib(leaves[i]);
    printf("%lld\n", total);
    return 0;
}
