/* Binary-trees benchmark (benchmarks game): C reference for
   bench/bintrees.zeph, one malloc per node and a recursive free.
   Same tree shapes, same checksum.
   Build: gcc -O2 bintrees.c -o bintrees
   Usage: bintrees [maxDepth] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

typedef struct Node { struct Node *left, *right; } Node;

static Node *bottomUpTree(long long depth) {
    Node *node = malloc(sizeof *node);
    if (depth > 0) {
        node->left = bottomUpTree(depth - 1);
        node->right = bottomUpTree(depth - 1);
    } else {
        node->left = node->right = NULL;
    }
    return node;
}

static long long itemCheck(const Node *node) {
    long long total = 1;
    if (node->left) total += itemCheck(node->left);
    if (node->right) total += itemCheck(node->right);
    return total;
}

static void deleteTree(Node *node) {
    if (node->left) deleteTree(node->left);
    if (node->right) deleteTree(node->right);
    free(node);
}

int main(int argc, char **argv) {
    const long long minimumDepth = 4;
    long long maximumDepth = argc > 1 ? atoll(argv[1]) : 16;
    if (maximumDepth < minimumDepth + 2) maximumDepth = minimumDepth + 2;

    Node *stretchTree = bottomUpTree(maximumDepth + 1);
    uint64_t checksum = (uint64_t)itemCheck(stretchTree);
    deleteTree(stretchTree);
    Node *longLivedTree = bottomUpTree(maximumDepth);

    for (long long depth = minimumDepth; depth <= maximumDepth; depth += 2) {
        long long iterations = 1LL << (maximumDepth - depth + minimumDepth);
        long long check = 0;
        #pragma omp parallel for reduction(+:check) schedule(static)
        for (long long i = 0; i < iterations; i++) {
            Node *tree = bottomUpTree(depth);
            check += itemCheck(tree);
            deleteTree(tree);
        }
        checksum = checksum * 31 + (uint64_t)check;
    }
    checksum = checksum * 31 + (uint64_t)itemCheck(longLivedTree);
    deleteTree(longLivedTree);
    printf("%lld\n", (long long)checksum);
    return 0;
}
