// Prototype: how fast can an interpreter for a typed, register-based Zephyr-like
// IR be, compared with native code? Answers research question Q2.
//
// The IR is three-address code over 64-bit frame slots. Types are static, so
// there are no tags or type checks. Bounds checks are kept, because Zephyr
// requires them. Dispatch uses computed goto (direct threading: each
// instruction stores its handler address).
//
// Build: gcc -O2 -o interp research/proto/interp.c   (clang works too)
// Run:   ./interp
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef int64_t i64;
enum { CONST, ADD, SUB, MUL, LT, JMP, JF, CALL, RET, LOADX, STOREX, FADD, FSUB, FMUL, FLT, ITOF, MOV, ADDI, LTI, HALT, NOPS };

typedef struct Ins { void *h; int op, a, b, c; i64 k; } Ins;
typedef struct Fn { Ins *code; int n, slots, params; } Fn;

static Fn fns[8];
static i64 stack[1 << 22];
static i64 *heapList; static i64 heapLen;     // one list, enough for the prototype
static void *handlers[NOPS];

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

// Interpreter. fp points at the frame; the return value goes in fp[0].
static void run(int fi, i64 *fp, int init) {
    if (init) {
        static void *t[NOPS] = { &&L_CONST, &&L_ADD, &&L_SUB, &&L_MUL, &&L_LT, &&L_JMP, &&L_JF, &&L_CALL, &&L_RET,
                                 &&L_LOADX, &&L_STOREX, &&L_FADD, &&L_FSUB, &&L_FMUL, &&L_FLT, &&L_ITOF, &&L_MOV, &&L_ADDI, &&L_LTI, &&L_HALT };
        memcpy(handlers, t, sizeof t); return;
    }
    Ins *ip = fns[fi].code;
#define NEXT goto *(++ip)->h
#define D(x) double x; memcpy(&x, &fp[ip->x], 8)
    goto *ip->h;
L_CONST: fp[ip->a] = ip->k; NEXT;
L_ADD:   fp[ip->a] = fp[ip->b] + fp[ip->c]; NEXT;
L_ADDI:  fp[ip->a] = fp[ip->b] + ip->k; NEXT;
L_SUB:   fp[ip->a] = fp[ip->b] - fp[ip->c]; NEXT;
L_MUL:   fp[ip->a] = fp[ip->b] * fp[ip->c]; NEXT;
L_LT:    fp[ip->a] = fp[ip->b] < fp[ip->c]; NEXT;
L_LTI:   fp[ip->a] = fp[ip->b] < ip->k; NEXT;
L_MOV:   fp[ip->a] = fp[ip->b]; NEXT;
L_JMP:   ip = fns[fi].code + ip->k; goto *ip->h;
L_JF:    if (!fp[ip->a]) { ip = fns[fi].code + ip->k; goto *ip->h; } NEXT;
L_CALL: { // a = destination, b = first argument slot, k = callee; arguments are copied into the new frame
        i64 *nf = fp + fns[fi].slots; Fn *f = &fns[ip->k];
        for (int i = 0; i < f->params; i++) nf[1 + i] = fp[ip->b + i];
        run((int)ip->k, nf, 0);
        fp[ip->a] = nf[0]; NEXT; }
L_RET:   fp[0] = fp[ip->a]; return;
L_LOADX: { i64 i = fp[ip->b]; if ((uint64_t)i >= (uint64_t)heapLen) { fprintf(stderr, "panic: index\n"); exit(1); } fp[ip->a] = heapList[i]; NEXT; }
L_STOREX:{ i64 i = fp[ip->b]; if ((uint64_t)i >= (uint64_t)heapLen) { fprintf(stderr, "panic: index\n"); exit(1); } heapList[i] = fp[ip->a]; NEXT; }
L_FADD: { D(b); D(c); double r = b + c; memcpy(&fp[ip->a], &r, 8); NEXT; }
L_FSUB: { D(b); D(c); double r = b - c; memcpy(&fp[ip->a], &r, 8); NEXT; }
L_FMUL: { D(b); D(c); double r = b * c; memcpy(&fp[ip->a], &r, 8); NEXT; }
L_FLT:  { D(b); D(c); fp[ip->a] = b < c; NEXT; }
L_ITOF: { double r = (double)fp[ip->b]; memcpy(&fp[ip->a], &r, 8); NEXT; }
L_HALT: return;
}

// --- a tiny assembler for the prototype IR ---
static Ins buf[256]; static int nb;
static int emit(int op, int a, int b, int c, i64 k) { buf[nb] = (Ins){ 0, op, a, b, c, k }; return nb++; }
static void finish(int fi, int slots, int params) {
    Fn *f = &fns[fi]; f->code = malloc(sizeof(Ins) * nb); memcpy(f->code, buf, sizeof(Ins) * nb);
    for (int i = 0; i < nb; i++) f->code[i].h = handlers[f->code[i].op];
    f->n = nb; f->slots = slots; f->params = params; nb = 0;
}
static i64 dbits(double d) { i64 x; memcpy(&x, &d, 8); return x; }

// --- native references ---
static i64 nfib(i64 n) { return n < 2 ? n : nfib(n - 1) + nfib(n - 2); }
static i64 nsum(i64 *a, i64 n, int reps) {
    i64 s = 0;
    for (int r = 0; r < reps; r++) for (i64 i = 0; i < n; i++) { if ((uint64_t)i >= (uint64_t)n) abort(); s += a[i]; }
    return s;
}
static i64 nmandel(int size) {           // iteration count over a size x size grid, max 50 iterations
    i64 total = 0;
    for (int y = 0; y < size; y++) for (int x = 0; x < size; x++) {
        double cr = x * (3.0 / size) - 2.0, ci = y * (2.0 / size) - 1.0, zr = 0, zi = 0; int it = 0;
        while (it < 50 && zr * zr + zi * zi < 4.0) { double t = zr * zr - zi * zi + cr; zi = 2 * zr * zi + ci; zr = t; it++; }
        total += it;
    }
    return total;
}

int main(void) {
    run(0, 0, 1);
    // fn 0: fib(n): slots 1 = n
    emit(LTI, 2, 1, 0, 2);          // 0: s2 = n < 2
    emit(JF, 2, 0, 0, 3);           // 1: if !s2 goto 3
    emit(RET, 1, 0, 0, 0);          // 2: return n
    emit(ADDI, 3, 1, 0, -1);        // 3: s3 = n - 1
    emit(CALL, 4, 3, 0, 0);         // 4: s4 = fib(s3)
    emit(ADDI, 3, 1, 0, -2);        // 5: s3 = n - 2
    emit(CALL, 5, 3, 0, 0);         // 6: s5 = fib(s3)
    emit(ADD, 6, 4, 5, 0);          // 7
    emit(RET, 6, 0, 0, 0);          // 8
    finish(0, 7, 1);
    // fn 1: sum(n, reps): slots 1 = n, 2 = reps, 3 = r, 4 = i, 5 = s, 6 = t, 7 = x
    emit(CONST, 5, 0, 0, 0);        // 0: s = 0
    emit(CONST, 3, 0, 0, 0);        // 1: r = 0
    emit(LT, 6, 3, 2, 0);           // 2: t = r < reps
    emit(JF, 6, 0, 0, 11);          // 3
    emit(CONST, 4, 0, 0, 0);        // 4: i = 0
    emit(LT, 6, 4, 1, 0);           // 5: t = i < n
    emit(JF, 6, 0, 0, 10);          // 6
    emit(LOADX, 7, 4, 0, 0);        // 7: x = list[i] (checked)
    emit(ADD, 5, 5, 7, 0);          // 8: s += x
    emit(ADDI, 4, 4, 0, 1);         // 9: i += 1   (fallthrough to the loop test)
    nb--; emit(ADDI, 4, 4, 0, 1); emit(JMP, 0, 0, 0, 5);  // 9, 10: i += 1; goto 5
    // fix the targets: the loop exit is now 11, the outer increment is at 11
    buf[6].k = 11; buf[3].k = 14;
    emit(ADDI, 3, 3, 0, 1);         // 11: r += 1
    emit(JMP, 0, 0, 0, 2);          // 12
    emit(HALT, 0, 0, 0, 0);         // 13 (unused)
    emit(RET, 5, 0, 0, 0);          // 14: return s
    finish(1, 8, 2);
    // fn 2: mandel(size): slots 1 = size, 2 = y, 3 = x, 4 = cr, 5 = ci, 6 = zr, 7 = zi, 8 = it, 9 = total,
    // 10..15 = temporaries, 16 = 3/size, 17 = 2/size, 18 = 2.0, 19 = 4.0, 20 = 50
    int L = 0;
    emit(CONST, 9, 0, 0, 0);                    // total = 0
    emit(CONST, 18, 0, 0, dbits(2.0)); emit(CONST, 19, 0, 0, dbits(4.0));
    emit(ITOF, 10, 1, 0, 0); emit(CONST, 11, 0, 0, dbits(3.0)); emit(CONST, 15, 0, 0, dbits(1.0));
    // 3/size and 2/size are passed precomputed through slots 16 and 17 by the caller (no FDIV in this IR)
    emit(CONST, 2, 0, 0, 0);                    // y = 0
    int yTest = emit(LT, 10, 2, 1, 0); int yJf = emit(JF, 10, 0, 0, 0);
    emit(CONST, 3, 0, 0, 0);                    // x = 0
    int xTest = emit(LT, 10, 3, 1, 0); int xJf = emit(JF, 10, 0, 0, 0);
    emit(ITOF, 10, 3, 0, 0); emit(FMUL, 10, 10, 16, 0); emit(FSUB, 4, 10, 18, 0);       // cr = x*(3/size) - 2
    emit(ITOF, 10, 2, 0, 0); emit(FMUL, 10, 10, 17, 0); emit(FSUB, 5, 10, 15, 0);       // ci = y*(2/size) - 1
    emit(CONST, 6, 0, 0, 0); emit(CONST, 7, 0, 0, 0); emit(CONST, 8, 0, 0, 0);
    int wTest = emit(LTI, 10, 8, 0, 50); int wJf1 = emit(JF, 10, 0, 0, 0);
    emit(FMUL, 11, 6, 6, 0); emit(FMUL, 12, 7, 7, 0); emit(FADD, 13, 11, 12, 0); emit(FLT, 10, 13, 19, 0);
    int wJf2 = emit(JF, 10, 0, 0, 0);
    emit(FSUB, 13, 11, 12, 0); emit(FADD, 13, 13, 4, 0);                                 // t = zr*zr - zi*zi + cr
    emit(FMUL, 14, 18, 6, 0); emit(FMUL, 14, 14, 7, 0); emit(FADD, 7, 14, 5, 0);       // zi = 2*zr*zi + ci
    emit(MOV, 6, 13, 0, 0); emit(ADDI, 8, 8, 0, 1); emit(JMP, 0, 0, 0, wTest);
    int wEnd = emit(ADD, 9, 9, 8, 0); emit(ADDI, 3, 3, 0, 1); emit(JMP, 0, 0, 0, xTest);
    int xEnd = emit(ADDI, 2, 2, 0, 1); emit(JMP, 0, 0, 0, yTest);
    int yEnd = emit(RET, 9, 0, 0, 0);
    buf[yJf].k = yEnd; buf[xJf].k = xEnd; buf[wJf1].k = wEnd; buf[wJf2].k = wEnd; (void)L;
    finish(2, 21, 1);

    // The checksums must agree between the interpreter and native code.
    int fibN = 32, sumN = 1000000, reps = 50, msize = 600;
    heapLen = sumN; heapList = malloc(8 * sumN); for (i64 i = 0; i < sumN; i++) heapList[i] = i % 7;

    double t0 = now(); i64 nf = nfib(fibN); double tn = now() - t0;
    stack[1] = fibN; t0 = now(); run(0, stack, 0); double ti = now() - t0;
    printf("fib(%d)      native %7.1f ms  interp %7.1f ms  ratio %5.2fx  %s\n", fibN, tn * 1e3, ti * 1e3, ti / tn, nf == stack[0] ? "ok" : "MISMATCH");

    t0 = now(); i64 ns = nsum(heapList, sumN, reps); tn = now() - t0;
    stack[1] = sumN; stack[2] = reps; t0 = now(); run(1, stack, 0); ti = now() - t0;
    printf("sum loop     native %7.1f ms  interp %7.1f ms  ratio %5.2fx  %s\n", tn * 1e3, ti * 1e3, ti / tn, ns == stack[0] ? "ok" : "MISMATCH");

    t0 = now(); i64 nm = nmandel(msize); tn = now() - t0;
    memset(stack, 0, 8 * 64); stack[1] = msize; stack[16] = dbits(3.0 / msize); stack[17] = dbits(2.0 / msize);
    t0 = now(); run(2, stack, 0); ti = now() - t0;
    printf("mandel(%d)  native %7.1f ms  interp %7.1f ms  ratio %5.2fx  %s\n", msize, tn * 1e3, ti * 1e3, ti / tn, nm == stack[0] ? "ok" : "MISMATCH");
    return 0;
}
