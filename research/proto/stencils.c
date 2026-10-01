// How fast is copy-and-patch code emission? A library of 32 stencils (byte
// templates of 12-48 bytes with 1-3 holes for frame offsets, immediates and
// branch displacements) is used to emit a long stream of IR ops: copy the
// stencil, then patch its holes. This bounds the stencil tier's code generation
// cost per IR op (scenario S7). It does not measure the quality of the code.
// Build: gcc -O2 -o stencils research/proto/stencils.c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct Stencil { uint8_t bytes[48]; int size, holes, holeAt[3], holeKind[3]; } Stencil;
static Stencil lib[32];
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

int main(int argc, char **argv) {
    long ops = argc > 1 ? atol(argv[1]) : 24000000;
    srand(1);
    for (int i = 0; i < 32; i++) {                  // synthetic stencils with realistic sizes
        Stencil *s = &lib[i]; s->size = 12 + (i * 7) % 37; s->holes = 1 + i % 3;
        for (int b = 0; b < s->size; b++) s->bytes[b] = (uint8_t)(rand() & 255);
        for (int h = 0; h < s->holes; h++) { s->holeAt[h] = (h * 9 + 2) % (s->size - 4); s->holeKind[h] = h; }
    }
    // the IR stream: opcode plus three operands, as a flat array
    int32_t *ir = malloc(sizeof(int32_t) * 4 * ops);
    for (long i = 0; i < ops; i++) { ir[4 * i] = rand() & 31; ir[4 * i + 1] = rand() & 1023; ir[4 * i + 2] = rand(); ir[4 * i + 3] = (int)(i - (rand() & 63)); }
    uint8_t *code = malloc((size_t)ops * 48);
    uint32_t *opStart = malloc(sizeof(uint32_t) * ops);
    memset(code, 0, (size_t)ops * 48);          // pre-fault: measure emission, not first-touch page faults
    memset(opStart, 0, sizeof(uint32_t) * ops);
    double t0 = now();
    size_t at = 0;
    for (long i = 0; i < ops; i++) {
        const Stencil *s = &lib[ir[4 * i]];
        opStart[i] = (uint32_t)at;
        memcpy(code + at, s->bytes, 48);           // fixed-size copy; only s->size bytes are kept
        for (int h = 0; h < s->holes; h++) {
            int32_t v = s->holeKind[h] == 0 ? 8 * ir[4 * i + 1]                       // frame slot offset
                      : s->holeKind[h] == 1 ? ir[4 * i + 2]                           // immediate
                      : (int32_t)(opStart[ir[4 * i + 3] < 0 ? 0 : ir[4 * i + 3]] - (at + s->size));   // backward branch
            memcpy(code + at + s->holeAt[h], &v, 4);
        }
        at += (size_t)s->size;
    }
    double t = now() - t0;
    unsigned sum = 0; for (size_t i = 0; i < at; i += 4096) sum += code[i];
    printf("%ld ops -> %zu bytes in %.1f ms: %.2f ns/op (%u)\n", ops, at, t * 1e3, t / ops * 1e9, sum);
    return 0;
}
