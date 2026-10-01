// End-to-end prototype of the proposed backend path (cycle 73): flat SSA IR ->
// linear-scan register allocation -> direct x86-64 encoding into executable
// memory -> run. Measures the quality of the code this simple design produces
// (with no peephole or instruction-selection cleverness) against gcc -O2, and
// its compile time per value.
//
// IR: typed values in flat arrays, blocks with parameters (no phis),
// terminators jump/branch with arguments. Ops: const, add, sub, addi, lt (with
// branch fusion), load (bounds-checked list element), call (self-recursion),
// ret.
// Build: gcc -O2 -o minijit research/proto/minijit.c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
typedef int64_t i64;
static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

enum { PARAM, CONST, ADD, SUB, ADDI, LOAD, CALL, LOADNC };   // LOADNC: element load after bounds-check elimination
enum { T_JMP, T_BR_LT, T_BR_GE, T_RET };
#define MV 256
#define MB 32
static int op[MV], a0[MV], a1[MV], blk[MV], nv; static i64 imm[MV];
static int bfirst[MB], bend[MB], bparams[MB][4], nbp[MB], term[MB], tx[MB], ty[MB], tgt[MB][2], targs[MB][2][4], ntargs[MB][2], nb;
static int newv(int o, int x, int y, i64 k, int b) { op[nv] = o; a0[nv] = x; a1[nv] = y; imm[nv] = k; blk[nv] = b; return nv++; }

// ---- linear scan over block-ordered positions (blocks are emitted in order) ----
static int reg[MV], start[MV], endp[MV], pos[MV];
static const int pool[] = { 3, 12, 13, 14, 15, 8, 9, 10, 11 };   // rbx r12-r15 (saved by the callee), r8-r11 (not)
static const int calleeSaved[] = { 1, 1, 1, 1, 1, 0, 0, 0, 0 };   // rdi/rsi carry arguments, so they're not allocated
static int crossesCall[MV];
static void allocate(void) {
    int p = 0;
    for (int b = 0; b < nb; b++) { for (int v = bfirst[b]; v < bend[b]; v++) pos[v] = p++; p++; }
    for (int v = 0; v < nv; v++) { start[v] = pos[v]; endp[v] = pos[v]; crossesCall[v] = 0; }
    for (int v = 0; v < nv; v++) {
        if (a0[v] >= 0 && pos[v] > endp[a0[v]]) endp[a0[v]] = pos[v];
        if (a1[v] >= 0 && pos[v] > endp[a1[v]]) endp[a1[v]] = pos[v];
    }
    for (int b = 0; b < nb; b++) {          // uses by terminators, and loop-carried extension
        int tp = pos[bend[b] - 1] + 1;
        int us[2] = { tx[b], ty[b] };
        for (int k = 0; k < 2; k++) if (us[k] >= 0 && tp > endp[us[k]]) endp[us[k]] = tp;
        for (int s = 0; s < 2; s++) for (int k = 0; k < ntargs[b][s]; k++) { int v = targs[b][s][k]; if (tp > endp[v]) endp[v] = tp; }
        for (int s = 0; s < 2; s++) { int t = tgt[b][s]; if (t >= 0 && t <= b)      // back edge: values live into the loop stay live to its end
            for (int v = 0; v < nv; v++) if (start[v] < pos[bfirst[t]] && endp[v] >= pos[bfirst[t]] && endp[v] < tp) endp[v] = tp; }
    }
    for (int v = 0; v < nv; v++) if (op[v] == CALL) for (int w = 0; w < nv; w++) if (w != v && start[w] < pos[v] && endp[w] > pos[v]) crossesCall[w] = 1;
    int owner[16]; for (int i = 0; i < 16; i++) owner[i] = -1;
    for (int v = 0; v < nv; v++) {          // values in position order = index order here
        for (int r = 0; r < 16; r++) if (owner[r] >= 0 && endp[owner[r]] < start[v]) owner[r] = -1;   // expire only the current owner
        reg[v] = -1;
        // Coalescing hint: a value passed as a block argument prefers the
        // register of the block parameter it flows into, so the move vanishes.
        int hint = -1;
        for (int b = 0; b < nb && hint < 0; b++) for (int sx = 0; sx < 2 && hint < 0; sx++) for (int k = 0; k < ntargs[b][sx]; k++)
            if (targs[b][sx][k] == v && tgt[b][sx] >= 0) { int param = bparams[tgt[b][sx]][k]; if (param < v && reg[param] >= 0) { hint = reg[param]; break; } }
        if (hint >= 0) {
            int ok = owner[hint] < 0 || endp[owner[hint]] <= start[v];
            for (int i = 0; i < (int)(sizeof pool / sizeof *pool); i++) if (pool[i] == hint && crossesCall[v] && !calleeSaved[i]) ok = 0;
            if (ok) { reg[v] = hint; owner[hint] = v; }
        }
        for (int i = 0; reg[v] < 0 && i < (int)(sizeof pool / sizeof *pool); i++) {
            if (owner[pool[i]] >= 0 || (crossesCall[v] && !calleeSaved[i])) continue;
            reg[v] = pool[i]; owner[pool[i]] = v; break;
        }
        if (reg[v] < 0) { fprintf(stderr, "out of registers (prototype has no spilling)\n"); exit(1); }
    }
}

// ---- x86-64 encoder ----
static uint8_t *code; static int len;
static void b8(int x) { code[len++] = (uint8_t)x; }
static void b32(int x) { memcpy(code + len, &x, 4); len += 4; }
static void rex(int w, int r, int bse) { b8(0x40 | w << 3 | (r >> 3) << 2 | (bse >> 3)); }
static void movrr(int d, int s) { if (d == s) return; rex(1, s, d); b8(0x89); b8(0xC0 | (s & 7) << 3 | (d & 7)); }
static void alu(int opc, int d, int s) { rex(1, s, d); b8(opc); b8(0xC0 | (s & 7) << 3 | (d & 7)); }
static void movimm(int d, i64 k) { if (k == (int32_t)k) { rex(1, 0, d); b8(0xC7); b8(0xC0 | (d & 7)); b32((int)k); } else { rex(1, 0, d); b8(0xB8 | (d & 7)); memcpy(code + len, &k, 8); len += 8; } }
static void addimm(int d, int k) { rex(1, 0, d); b8(0x81); b8(0xC0 | (d & 7)); b32(k); }
static void cmprr(int a, int b) { alu(0x39, a, b); }
static void push(int r) { if (r >= 8) b8(0x41); b8(0x50 | (r & 7)); }
static void pop(int r) { if (r >= 8) b8(0x41); b8(0x58 | (r & 7)); }
static int blockAt[MB]; static int fix[64], fixBlock[64], nfix;
static void jcc(int cc, int target) { b8(0x0F); b8(0x80 | cc); fix[nfix] = len; fixBlock[nfix++] = target; b32(0); }
static void jmp(int target) { b8(0xE9); fix[nfix] = len; fixBlock[nfix++] = target; b32(0); }
static int panicFix[16], npanic;

// Parallel moves for block arguments: stage every source in a scratch register
// (rax, rcx, rdx are never allocated), then write the destinations. That is
// correct for any permutation of up to 3 arguments.
static void moveArgs(int b, int s) {
    int t = tgt[b][s]; static const int scratch[3] = { 0, 1, 2 };
    int moving[4], n = 0;
    for (int k = 0; k < ntargs[b][s]; k++) if (reg[targs[b][s][k]] != reg[bparams[t][k]]) moving[n++] = k;   // coalesced ones need no move
    for (int j = 0; j < n; j++) movrr(scratch[j], reg[targs[b][s][moving[j]]]);
    for (int j = 0; j < n; j++) movrr(reg[bparams[t][moving[j]]], scratch[j]);
}

static void *compile(int listPtrReg /* the list base is the 2nd param */) {
    (void)listPtrReg;
    code = mmap(0, 1 << 16, PROT_READ | PROT_WRITE | PROT_EXEC, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    len = 0; nfix = 0; npanic = 0;
    // prologue: lean internal convention. Save the callee-saved registers used; args arrive in rdi, rsi.
    int saved[8], ns = 0;
    for (int i = 0; i < 5; i++) { int r = pool[i]; for (int v = 0; v < nv; v++) if (reg[v] == r) { saved[ns++] = r; break; } }
    if (ns % 2 == 0) b8(0x50 | 0);        // keep 16-byte alignment across calls (push rax as padding)
    for (int i = 0; i < ns; i++) push(saved[i]);
    // params: value ids 0.. map to rdi, rsi
    int argRegs[2] = { 7, 6 };
    int nparam = 0; for (int v = 0; v < nv; v++) if (op[v] == PARAM) nparam++;
    // move incoming args into their allocated registers through rax/rdx to avoid clobbering
    movrr(0, argRegs[0]); if (nparam > 1) movrr(2, argRegs[1]);
    for (int v = 0; v < nv; v++) if (op[v] == PARAM && (imm[v] == 0 || imm[v] == 1)) movrr(reg[v], imm[v] == 0 ? 0 : 2);
    for (int b = 0; b < nb; b++) {
        blockAt[b] = len;
        for (int v = bfirst[b]; v < bend[b]; v++) {
            int d = reg[v];
            switch (op[v]) {
            case PARAM: break;
            case CONST: movimm(d, imm[v]); break;
            case ADD: if (d == reg[a1[v]]) alu(0x01, d, reg[a0[v]]); else { movrr(d, reg[a0[v]]); alu(0x01, d, reg[a1[v]]); } break;
            case SUB: movrr(0, reg[a0[v]]); alu(0x29, 0, reg[a1[v]]); movrr(d, 0); break;
            case ADDI: movrr(d, reg[a0[v]]); addimm(d, (int)imm[v]); break;
            case LOAD: {   // d = list[index]; list = {len, data[]}; bounds-checked
                int L = reg[a0[v]], I = reg[a1[v]];
                rex(1, I, L); b8(0x3B); b8(0x00 | (I & 7) << 3 | (L & 7)); if ((L & 7) == 4) b8(0x24);   // cmp I, [L]
                b8(0x0F); b8(0x83); panicFix[npanic++] = len; b32(0);                                     // jae panic
                rex(1, d, 0); code[len - 1] |= (I >> 3) << 1 | (L >> 3); b8(0x8B); b8(0x44 | (d & 7) << 3); b8((3 << 6) | (I & 7) << 3 | (L & 7)); b8(8);   // mov d, [L + I*8 + 8]
                break; }
            case LOADNC: {  // d = list[index], check proved away: mov d, [L + I*8 + 8]
                int L = reg[a0[v]], I = reg[a1[v]];
                rex(1, d, 0); code[len - 1] |= (I >> 3) << 1 | (L >> 3); b8(0x8B); b8(0x44 | (d & 7) << 3); b8((3 << 6) | (I & 7) << 3 | (L & 7)); b8(8);
                break; }
            case CALL: {   // self call with one argument
                movrr(7, reg[a0[v]]); if (a1[v] >= 0) movrr(6, reg[a1[v]]);
                b8(0xE8); b32(-(len + 4)); movrr(d, 0); break; }
            }
        }
        // terminator
        if (term[b] == T_RET) {
            movrr(0, reg[tx[b]]);
            for (int i = ns - 1; i >= 0; i--) pop(saved[i]);
            if (ns % 2 == 0) b8(0x58 | 1);    // pop rcx (padding)
            b8(0xC3);
        } else if (term[b] == T_JMP) { moveArgs(b, 0); if (tgt[b][0] != b + 1) jmp(tgt[b][0]); }
        else {  // conditional: branch to tgt[1] when the condition holds, else fall through to tgt[0]
            cmprr(reg[tx[b]], reg[ty[b]]);
            int cc = term[b] == T_BR_LT ? 0xC : 0xD;      // jl / jge
            if (ntargs[b][1] == 0 && ntargs[b][0] == 0) { jcc(cc, tgt[b][1]); if (tgt[b][0] != b + 1) jmp(tgt[b][0]); }
            else { int skip = len; b8(0x0F); b8(0x80 | (cc ^ 1)); b32(0); moveArgs(b, 1); jmp(tgt[b][1]);
                   int here = len; int rel = here - (skip + 6); memcpy(code + skip + 2, &rel, 4); moveArgs(b, 0); if (tgt[b][0] != b + 1) jmp(tgt[b][0]); }
        }
    }
    int panicAt = len; movimm(0, -1); b8(0xC3);          // prototype: a failed bounds check returns -1
    for (int i = 0; i < nfix; i++) { int rel = blockAt[fixBlock[i]] - (fix[i] + 4); memcpy(code + fix[i], &rel, 4); }
    for (int i = 0; i < npanic; i++) { int rel = panicAt - (panicFix[i] + 4); memcpy(code + panicFix[i], &rel, 4); }
    return code;
}

static void reset(void) { nv = 0; nb = 0; memset(ntargs, 0, sizeof ntargs); memset(nbp, 0, sizeof nbp); }
static int block(void) { bfirst[nb] = nv; tgt[nb][0] = tgt[nb][1] = -1; tx[nb] = ty[nb] = -1; return nb++; }
static void endb(int b) { bend[b] = nv; }

static i64 nfib(i64 n) { return n < 2 ? n : nfib(n - 1) + nfib(n - 2); }
static i64 nsum(const i64 *list, int reps) { i64 s = 0; for (int r = 0; r < reps; r++) for (i64 i = 0; i < list[0]; i++) { if ((uint64_t)i >= (uint64_t)list[0]) return -1; s += list[1 + i]; } return s; }

int main(void) {
    setvbuf(stdout, 0, _IONBF, 0);
    // fib(n): b0: n=param; two=2; br n<two -> b1 else b2.  b1: ret n.  b2: a=fib(n-1); b=fib(n-2); ret a+b
    reset();
    int b0 = block(); int n = newv(PARAM, -1, -1, 0, b0); int two = newv(CONST, -1, -1, 2, b0); endb(b0);
    term[b0] = T_BR_LT; tx[b0] = n; ty[b0] = two;
    int b1 = block(); endb(b1); term[b1] = T_RET; tx[b1] = n;
    int b2 = block(); int n1 = newv(ADDI, n, -1, -1, b2); int f1 = newv(CALL, n1, -1, 0, b2); int n2 = newv(ADDI, n, -1, -2, b2);
    int f2 = newv(CALL, n2, -1, 0, b2); int r = newv(ADD, f1, f2, 0, b2); endb(b2); term[b2] = T_RET; tx[b2] = r;
    tgt[b0][1] = b1; tgt[b0][0] = b2;
    double c0 = now(); allocate(); i64 (*fib)(i64) = (i64 (*)(i64))compile(0); double c1 = now();
    printf("fib: %d values compiled in %.1f us (%d bytes)\n", nv, (c1 - c0) * 1e6, len);
    if (getenv("DUMP")) { FILE *f = fopen("/tmp/zr/fib.bin", "wb"); fwrite(code, 1, len, f); fclose(f); for (int v = 0; v < nv; v++) printf("  v%d op%d reg%d [%d,%d] call-crossing %d\n", v, op[v], reg[v], start[v], endp[v], crossesCall[v]); }
    double t0 = now(); i64 x = fib(getenv("N") ? atoi(getenv("N")) : 38); double t1 = now(); i64 y = nfib(getenv("N") ? atoi(getenv("N")) : 38); double t2 = now();
    printf("  fib(38): generated %.0f ms, gcc -O2 %.0f ms, ratio %.2f  %s\n", (t1 - t0) * 1e3, (t2 - t1) * 1e3, (t1 - t0) / (t2 - t1), x == y ? "ok" : "MISMATCH");

    // sum(list, reps): b0: list, reps, zero; jmp b1(s=0, r=0)
    // b1(s, r): br r < reps -> b2(s, r) else b5(s)
    // b2(s, r): jmp b3(s, r, i=0)
    // b3(s, r, i): len = load? (list length is list[0]: use LOAD with index -1 trick? use a dedicated length value from b0)
    reset();
    b0 = block(); int list = newv(PARAM, -1, -1, 0, b0); int reps = newv(PARAM, -1, -1, 1, b0); int zero = newv(CONST, -1, -1, 0, b0);
    int length = newv(CONST, -1, -1, 1000000, b0); endb(b0); term[b0] = T_JMP; tgt[b0][0] = 1; ntargs[b0][0] = 2; targs[b0][0][0] = zero; targs[b0][0][1] = zero;
    b1 = block(); int s1 = newv(PARAM, -1, -1, 9, b1); int r1 = newv(PARAM, -1, -1, 9, b1); endb(b1); bparams[b1][0] = s1; bparams[b1][1] = r1; nbp[b1] = 2;
    term[b1] = T_BR_LT; tx[b1] = r1; ty[b1] = reps; tgt[b1][1] = 2; tgt[b1][0] = 4; ntargs[b1][1] = 3; targs[b1][1][0] = s1; targs[b1][1][1] = r1; targs[b1][1][2] = zero;
    ntargs[b1][0] = 1; targs[b1][0][0] = s1;
    b2 = block(); int s2 = newv(PARAM, -1, -1, 9, b2); int r2 = newv(PARAM, -1, -1, 9, b2); int i2 = newv(PARAM, -1, -1, 9, b2); endb(b2);
    bparams[b2][0] = s2; bparams[b2][1] = r2; bparams[b2][2] = i2; nbp[b2] = 3;
    term[b2] = T_BR_LT; tx[b2] = i2; ty[b2] = length; tgt[b2][1] = 3; tgt[b2][0] = 1;
    ntargs[b2][1] = 0; ntargs[b2][0] = 2; int r2n = -1; (void)r2n;
    // b3: x = list[i]; s' = s + x; i' = i + 1; jmp b2(s', r, i')
    int b3 = block(); int xv = newv(LOAD, list, i2, 0, b3); int s3 = newv(ADD, s2, xv, 0, b3); int i3 = newv(ADDI, i2, -1, 1, b3); endb(b3);
    term[b3] = T_JMP; tgt[b3][0] = 2; ntargs[b3][0] = 3; targs[b3][0][0] = s3; targs[b3][0][1] = r2; targs[b3][0][2] = i3;
    // b2's exit (i >= length) goes back to b1 with (s, r + 1): needs an increment, so route through b5
    int b4 = block(); int sOut = newv(PARAM, -1, -1, 9, b4); endb(b4); bparams[b4][0] = sOut; nbp[b4] = 1; term[b4] = T_RET; tx[b4] = sOut;
    int b5 = block(); int s5 = newv(PARAM, -1, -1, 9, b5); int r5 = newv(PARAM, -1, -1, 9, b5); int r5n = newv(ADDI, r5, -1, 1, b5); endb(b5);
    bparams[b5][0] = s5; bparams[b5][1] = r5; nbp[b5] = 2; term[b5] = T_JMP; tgt[b5][0] = 1; ntargs[b5][0] = 2; targs[b5][0][0] = s5; targs[b5][0][1] = r5n;
    tgt[b2][0] = b5; ntargs[b2][0] = 2; targs[b2][0][0] = s2; targs[b2][0][1] = r2;
    // block-parameter values are defined by moves at the jumps, so they're "params" in the IR (op PARAM, imm 9 = block param)
    for (int v = 0; v < nv; v++) if (op[v] == PARAM && imm[v] == 9) op[v] = CONST, imm[v] = 0;   // placeholder: defined by incoming moves
    c0 = now(); allocate();
    // block params must not be clobbered by their CONST placeholder: drop those instructions
    for (int v = 0; v < nv; v++) if (op[v] == CONST && imm[v] == 0 && v != zero) op[v] = PARAM;
    for (int v = 0; v < nv; v++) if (op[v] == PARAM && v != list && v != reps) imm[v] = 99;
    i64 (*sum)(const i64 *, i64) = (i64 (*)(const i64 *, i64))compile(0); c1 = now();
    printf("sum: %d values compiled in %.1f us (%d bytes)\n", nv, (c1 - c0) * 1e6, len);
    i64 *data = malloc(8 * (1000000 + 1)); data[0] = 1000000; for (int k = 0; k < 1000000; k++) data[1 + k] = k % 7;
    t0 = now(); x = sum(data, 50); t1 = now(); y = nsum(data, 50); t2 = now();
    printf("  sum(50 x 1M): generated %.0f ms, gcc -O2 %.0f ms, ratio %.2f  %s (%lld)\n", (t1 - t0) * 1e3, (t2 - t1) * 1e3, (t1 - t0) / (t2 - t1), x == y ? "ok" : "MISMATCH", (long long)x);

    // sum, as loop rotation + bounds-check elimination would leave it (cycle 74):
    // the test moves to the bottom of the loop and the per-element check is gone
    // (proved by i < length <= list.len, with one check hoisted before the loop).
    reset();
    b0 = block(); list = newv(PARAM, -1, -1, 0, b0); reps = newv(PARAM, -1, -1, 1, b0); zero = newv(CONST, -1, -1, 0, b0);
    length = newv(CONST, -1, -1, 1000000, b0); endb(b0); term[b0] = T_JMP; tgt[b0][0] = 1; ntargs[b0][0] = 2; targs[b0][0][0] = zero; targs[b0][0][1] = zero;
    b1 = block(); s1 = newv(PARAM, -1, -1, 99, b1); r1 = newv(PARAM, -1, -1, 99, b1); endb(b1); bparams[b1][0] = s1; bparams[b1][1] = r1; nbp[b1] = 2;
    term[b1] = T_BR_LT; tx[b1] = r1; ty[b1] = reps; tgt[b1][1] = 2; ntargs[b1][1] = 3; targs[b1][1][0] = s1; targs[b1][1][1] = r1; targs[b1][1][2] = zero;
    tgt[b1][0] = 4; ntargs[b1][0] = 1; targs[b1][0][0] = s1;
    b2 = block(); s2 = newv(PARAM, -1, -1, 99, b2); r2 = newv(PARAM, -1, -1, 99, b2); i2 = newv(PARAM, -1, -1, 99, b2);
    xv = newv(LOADNC, list, i2, 0, b2); s3 = newv(ADD, s2, xv, 0, b2); i3 = newv(ADDI, i2, -1, 1, b2); endb(b2);
    bparams[b2][0] = s2; bparams[b2][1] = r2; bparams[b2][2] = i2; nbp[b2] = 3;
    term[b2] = T_BR_LT; tx[b2] = i3; ty[b2] = length; tgt[b2][1] = 2; ntargs[b2][1] = 3; targs[b2][1][0] = s3; targs[b2][1][1] = r2; targs[b2][1][2] = i3;
    tgt[b2][0] = 3; ntargs[b2][0] = 2; targs[b2][0][0] = s3; targs[b2][0][1] = r2;
    b3 = block(); s5 = newv(PARAM, -1, -1, 99, b3); r5 = newv(PARAM, -1, -1, 99, b3); r5n = newv(ADDI, r5, -1, 1, b3); endb(b3);
    bparams[b3][0] = s5; bparams[b3][1] = r5; nbp[b3] = 2; term[b3] = T_JMP; tgt[b3][0] = 1; ntargs[b3][0] = 2; targs[b3][0][0] = s5; targs[b3][0][1] = r5n;
    b4 = block(); sOut = newv(PARAM, -1, -1, 99, b4); endb(b4); bparams[b4][0] = sOut; nbp[b4] = 1; term[b4] = T_RET; tx[b4] = sOut;
    c0 = now(); allocate(); i64 (*sum2)(const i64 *, i64) = (i64 (*)(const i64 *, i64))compile(0); c1 = now();
    printf("sum, rotated + checks eliminated: %d values compiled in %.1f us (%d bytes)\n", nv, (c1 - c0) * 1e6, len);
    t0 = now(); x = sum2(data, 50); t1 = now(); y = nsum(data, 50); t2 = now();
    printf("  sum(50 x 1M): generated %.0f ms, gcc -O2 %.0f ms, ratio %.2f  %s\n", (t1 - t0) * 1e3, (t2 - t1) * 1e3, (t1 - t0) / (t2 - t1), x == y ? "ok" : "MISMATCH");

    // fib after accumulator recursion elimination (cycle 75), as the pass would produce it:
    //   b0: n param; jmp b1(acc=0, m=n)
    //   b1(acc, m): br m < 2 -> b3(acc, m) else b2(acc, m)
    //   b2(acc, m): t = fib(m - 1); acc' = acc + t; m' = m - 2; jmp b1(acc', m')
    //   b3(acc, m): ret acc + m
    reset();
    b0 = block(); n = newv(PARAM, -1, -1, 0, b0); zero = newv(CONST, -1, -1, 0, b0); endb(b0);
    term[b0] = T_JMP; tgt[b0][0] = 1; ntargs[b0][0] = 2; targs[b0][0][0] = zero; targs[b0][0][1] = n;
    b1 = block(); int accA = newv(PARAM, -1, -1, 99, b1); int mA = newv(PARAM, -1, -1, 99, b1); two = newv(CONST, -1, -1, 2, b1); endb(b1);
    bparams[b1][0] = accA; bparams[b1][1] = mA; nbp[b1] = 2;
    term[b1] = T_BR_LT; tx[b1] = mA; ty[b1] = two; tgt[b1][1] = 3; ntargs[b1][1] = 2; targs[b1][1][0] = accA; targs[b1][1][1] = mA;
    tgt[b1][0] = 2; ntargs[b1][0] = 2; targs[b1][0][0] = accA; targs[b1][0][1] = mA;
    b2 = block(); int accB = newv(PARAM, -1, -1, 99, b2); int mB = newv(PARAM, -1, -1, 99, b2); int m1 = newv(ADDI, mB, -1, -1, b2);
    int tB = newv(CALL, m1, -1, 0, b2); int accN = newv(ADD, accB, tB, 0, b2); int mN = newv(ADDI, mB, -1, -2, b2); endb(b2);
    bparams[b2][0] = accB; bparams[b2][1] = mB; nbp[b2] = 2; term[b2] = T_JMP; tgt[b2][0] = 1; ntargs[b2][0] = 2; targs[b2][0][0] = accN; targs[b2][0][1] = mN;
    b3 = block(); int accC = newv(PARAM, -1, -1, 99, b3); int mC = newv(PARAM, -1, -1, 99, b3); int resC = newv(ADD, accC, mC, 0, b3); endb(b3);
    bparams[b3][0] = accC; bparams[b3][1] = mC; nbp[b3] = 2; term[b3] = T_RET; tx[b3] = resC;
    c0 = now(); allocate(); i64 (*fibAcc)(i64) = (i64 (*)(i64))compile(0); c1 = now();
    printf("fib, accumulator form: %d values compiled in %.1f us (%d bytes)\n", nv, (c1 - c0) * 1e6, len);
    t0 = now(); x = fibAcc(38); t1 = now(); y = nfib(38); t2 = now();
    printf("  fib(38): generated %.0f ms, gcc -O2 %.0f ms, ratio %.2f  %s\n", (t1 - t0) * 1e3, (t2 - t1) * 1e3, (t1 - t0) / (t2 - t1), x == y ? "ok" : "MISMATCH");
    return 0;
}
