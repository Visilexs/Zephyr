// Cost of loading a cached ~480 KB code image: read it, map it executable,
// patch ~5000 relocations, and call into it. Bound for a cache-backed zc run.
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>
int main(void) {
    struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC, &t0);
    int fd = open("/tmp/zr/e.out", O_RDONLY); size_t n = 481728;
    unsigned char *p = mmap(0, n, PROT_READ | PROT_WRITE, MAP_PRIVATE, fd, 0);
    unsigned char *code = mmap(0, n, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    memcpy(code, p, n);
    unsigned sum = 0; for (int i = 0; i < 5000; i++) { unsigned off = (i * 97) % (n - 8); *(int *)(code + off) += i; sum += code[off]; }
    mprotect(code, n, PROT_READ | PROT_EXEC);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    printf("load+copy+5000 relocations+protect: %.3f ms (%u)\n", (t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6, sum);
    return 0;
}
