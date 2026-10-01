/* bintrees with one bump arena per thread (regions, M7/M13), parallelized over
   the per-depth iterations like bintrees_omp.c. Tests whether per-thread
   regions remove the allocator contention that limits malloc (M48).
   Build: gcc -O2 -fopenmp -o bt bintrees_region_omp.c ; OMP_NUM_THREADS=n ./bt [depth] */
#include <omp.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct Node { struct Node *left, *right; } Node;
static _Thread_local char *arena; static _Thread_local size_t top;
static Node *alloc(void) { Node *n = (Node *)(arena + top); top += sizeof(Node); return n; }
static Node *bottomUpTree(int d) { Node *n = alloc(); if (d > 0) { n->left = bottomUpTree(d - 1); n->right = bottomUpTree(d - 1); } else n->left = n->right = 0; return n; }
static long long itemCheck(const Node *n) { long long t = 1; if (n->left) t += itemCheck(n->left); if (n->right) t += itemCheck(n->right); return t; }

int main(int argc, char **argv) {
    int minimumDepth = 4, maximumDepth = argc > 1 ? atoi(argv[1]) : 16;
    #pragma omp parallel
    { arena = malloc((size_t)1 << 28); top = 0; }
    size_t mark = top;
    uint64_t checksum = (uint64_t)itemCheck(bottomUpTree(maximumDepth + 1));
    top = mark;
    Node *longLived = bottomUpTree(maximumDepth);
    for (int depth = minimumDepth; depth <= maximumDepth; depth += 2) {
        long long iterations = 1LL << (maximumDepth - depth + minimumDepth), check = 0;
        #pragma omp parallel for reduction(+:check) schedule(static)
        for (long long i = 0; i < iterations; i++) { size_t m = top; check += itemCheck(bottomUpTree(depth)); top = m; }
        checksum = checksum * 31 + (uint64_t)check;
    }
    checksum = checksum * 31 + (uint64_t)itemCheck(longLived);
    printf("%lld\n", (long long)checksum);
    return 0;
}
