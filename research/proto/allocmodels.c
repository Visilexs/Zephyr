// Allocation strategies on the bintrees workload (same trees, same checksum as
// bench/bintrees.zeph at revision 398aadd), isolating representation choices:
//   malloc   C reference: malloc + recursive free
//   rc24     Zephyr-like: 24-byte header {count, descriptor, size}, size-class
//            free list, zeroing on allocation, recursive release through the
//            descriptor (pointer fields freed when the count reaches zero)
//   rc8      the same with an 8-byte header {count:32, descriptor:32}
//   region   bump allocation in an arena, reset when the tree dies
//   rc24cell rc24 plus today's optional representation: each non-none child
//            pointer goes through its own counted one-word cell (spec 3.0.4)
//   gc       tracing instead of counting: bump allocation into a nursery; when
//            it fills, mark from the roots (the long-lived tree and the tree
//            being built) and sweep unmarked nodes to a free list (non-moving,
//            as the spec requires). Frees happen at collections, not at last use.
// Nodes are {left, right}; `none` is a null pointer (no optional cells, as a
// niche-optimized representation would do; Zephyr today adds a cell per child).
// Build: gcc -O2 -o allocmodels research/proto/allocmodels.c
// Usage: allocmodels MODEL [maxDepth]
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct Node { struct Node *left, *right; } Node;
static int model, header;
static char *arena; static size_t top;
static void *freeList;                     // one size class: all nodes are the same size
static void *cellFree;                     // free list of optional cells (rc24cell)


// --- model 5: non-moving tracing (mark-sweep) with a bump nursery ---
#ifndef GCCAP
#define GCCAP (1 << 23)
#endif
static Node gcHeap[GCCAP]; static unsigned char gcMark[GCCAP]; static size_t gcBump; static Node *gcFree; static size_t gcCollections;
static Node *gcRoots[64]; static int gcRootCount;
static void gcMarkFrom(Node *n) { while (n) { size_t i = (size_t)(n - gcHeap); if (gcMark[i]) return; gcMark[i] = 1; gcMarkFrom(n->left); n = n->right; } }
static void gcCollect(void) {
    gcCollections++;
    memset(gcMark, 0, gcBump);
    for (int r = 0; r < gcRootCount; r++) gcMarkFrom(gcRoots[r]);
    gcFree = 0;
    for (size_t i = 0; i < gcBump; i++) if (!gcMark[i]) { gcHeap[i].left = gcFree; gcFree = &gcHeap[i]; }
}
static Node *gcAlloc(void) {
    if (gcFree) { Node *n = gcFree; gcFree = n->left; return n; }
    if (gcBump < GCCAP) return &gcHeap[gcBump++];
    gcCollect();
    if (!gcFree) { fprintf(stderr, "gc heap full\n"); exit(1); }
    Node *n = gcFree; gcFree = n->left; return n;
}

static Node *alloc(void) {
    if (model == 5) return gcAlloc();
    if (model == 0) return malloc(sizeof(Node));
    if (model == 3) { Node *n = (Node *)(arena + top); top += sizeof(Node); return n; }
    char *block;
    if (freeList) { block = freeList; freeList = *(void **)freeList; }
    else { block = malloc(header + sizeof(Node)); block += header; }
    if (header == 24) { ((int64_t *)block)[-3] = 1; ((int64_t *)block)[-2] = 0x1234; ((int64_t *)block)[-1] = sizeof(Node); }
    else { ((int64_t *)block)[-1] = ((int64_t)0x1234 << 32) | 1; }
    memset(block, 0, sizeof(Node));
    return (Node *)block;
}

static void release(Node *n) {
    if (!n) return;
    if (model == 0) { release(n->left); release(n->right); free(n); return; }
    int64_t *count = header == 24 ? &((int64_t *)n)[-3] : &((int64_t *)n)[-1];
    if (header == 24 ? --*count != 0 : ((--*count) & 0xffffffff) != 0) return;
    if (model == 4) {
        for (int k = 0; k < 2; k++) {
            Node *c = k ? n->right : n->left;
            if (c && --((int64_t *)c)[-3] == 0) { release(*(Node **)c); *(void **)c = cellFree; cellFree = c; }
        }
    } else { release(n->left); release(n->right); }
    *(void **)n = freeList; freeList = n;
}

static Node *cell(Node *child) {            // a counted one-word box around child
    char *block;
    if (cellFree) { block = cellFree; cellFree = *(void **)cellFree; }
    else { block = malloc(24 + 16); block += 24; }
    ((int64_t *)block)[-3] = 1; ((int64_t *)block)[-2] = 0x5678; ((int64_t *)block)[-1] = 8;
    *(Node **)block = child;
    return (Node *)block;
}
static Node *bottomUpTree(int depth) {
    Node *n = alloc();
    if (model == 5) { n->left = n->right = 0; gcRoots[gcRootCount++] = n; }   // a partial tree is a root while it is built
    if (depth > 0) {
        Node *l = bottomUpTree(depth - 1);
        if (model == 5) n->left = l;
        Node *r = bottomUpTree(depth - 1);
        n->left = model == 4 ? cell(l) : l; n->right = model == 4 ? cell(r) : r;
    }
    else n->left = n->right = 0;
    if (model == 5) gcRootCount--;
    return n;
}
static const Node *child(const Node *p) { return model == 4 && p ? *(Node **)p : p; }
static long long itemCheck(const Node *n) {
    long long t = 1;
    if (n->left) t += itemCheck(child(n->left));
    if (n->right) t += itemCheck(child(n->right));
    return t;
}
static void drop(Node *n, size_t mark) { if (model == 3) top = mark; else if (model == 5) { (void)n; } else release(n); }

int main(int argc, char **argv) {
    const char *names[] = { "malloc", "rc24", "rc8", "region", "rc24cell", "gc" };
    for (model = 0; model < 6 && strcmp(argv[1], names[model]); model++) {}
    if (model == 6) { fprintf(stderr, "unknown model\n"); return 2; }
    header = model == 1 || model == 4 ? 24 : 8;
    if (model == 3) arena = malloc((size_t)1 << 30);
    int minimumDepth = 4, maximumDepth = argc > 2 ? atoi(argv[2]) : 16;
    struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC, &t0);
    size_t mark = top;
    Node *stretch = bottomUpTree(maximumDepth + 1);
    uint64_t checksum = (uint64_t)itemCheck(stretch);
    drop(stretch, mark);
    Node *longLived = bottomUpTree(maximumDepth);
    if (model == 5) gcRoots[gcRootCount++] = longLived;
    for (int depth = minimumDepth; depth <= maximumDepth; depth += 2) {
        long long iterations = 1LL << (maximumDepth - depth + minimumDepth), check = 0;
        for (long long i = 0; i < iterations; i++) { size_t m = top; Node *t = bottomUpTree(depth); check += itemCheck(t); drop(t, m); }
        checksum = checksum * 31 + (uint64_t)check;
    }
    checksum = checksum * 31 + (uint64_t)itemCheck(longLived);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    printf("%-7s %lld  %.1f ms%s\n", names[model], (long long)checksum, (t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6, model == 5 ? "  (collections counted below)" : "");
    if (model == 5) printf("        %zu collections, nursery %d nodes\n", gcCollections, GCCAP);
    return 0;
}
