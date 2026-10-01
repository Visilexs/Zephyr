// Prototype for research question Q1: what does an optimizing pipeline over a
// flat SSA IR cost per value, when no pass allocates per value?
//
// Pipeline, run on synthetic functions shaped like zc's regions (loops, branches,
// block parameters instead of phis, calls):
//   1. CFG: predecessors and reverse post-order
//   2. constant folding + copy propagation + simple GVN (hash of op and operands)
//   3. dead code elimination (use counts and a worklist)
//   4. liveness (backward dataflow on bitsets)
//   5. live intervals + linear-scan register allocation (14 GPRs, spills to slots)
//   6. x86-64 encoding into a byte buffer (REX, opcode, ModRM; real encodings)
// Every structure is a preallocated int array indexed by value or block number.
//
// Build: gcc -O2 -o flatopt research/proto/flatopt.c
// Usage: flatopt [values-per-function] [functions] [extended: 1 adds dominators,
//        loops, LICM, range analysis and a second fold + DCE round]
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

enum { OP_CONST, OP_PARAM, OP_ADD, OP_SUB, OP_MUL, OP_AND, OP_LT, OP_COPY, OP_LOAD, OP_STORE, OP_CALL, OP_BR, OP_JMP, OP_RET };
#define MAXV 200000
#define MAXB 20000
#define NREG 14

// SSA values == instructions. Block b owns instructions [bstart[b], bend[b]).
static int op[MAXV], a0[MAXV], a1[MAXV], blk[MAXV], uses[MAXV], repl[MAXV];
static int64_t imm[MAXV];
static int nv;
static int bstart[MAXB], bend[MAXB], succ0[MAXB], succ1[MAXB], npred[MAXB], predOff[MAXB + 1], preds[2 * MAXB];
static int rpo[MAXB], rpoIndex[MAXB], nb;
static int bparam0[MAXB], nbparam[MAXB];  // block parameters: values [bparam0, bparam0 + n) are OP_PARAM
static int jarg[MAXB][2][4];             // jump arguments: for each successor, values passed to its parameters
static uint64_t rng = 88172645463325252ull;
static unsigned rnd(void) { rng ^= rng << 13; rng ^= rng >> 7; rng ^= rng << 17; return (unsigned)rng; }

static int newv(int o, int x, int y, int64_t k, int b) { op[nv] = o; a0[nv] = x; a1[nv] = y; imm[nv] = k; blk[nv] = b; return nv++; }

// A random function: a chain of nb blocks; block i branches forward and sometimes back (loops).
static void generate(int target) {
    nv = 0; nb = 0;
    int perBlock = 12;
    int blocks = target / perBlock; if (blocks < 2) blocks = 2; if (blocks > MAXB - 1) blocks = MAXB - 1;
    for (int b = 0; b < blocks; b++) {
        bstart[b] = nv;
        bparam0[b] = nv; nbparam[b] = b == 0 ? 2 : 1 + rnd() % 3;
        for (int i = 0; i < nbparam[b]; i++) newv(OP_PARAM, -1, -1, i, b);
        int first = bstart[b];
        for (int i = 0; i < perBlock - 2; i++) {
            int r = rnd() % 16;
            int x = first + rnd() % (nv - first), y = first + rnd() % (nv - first);
            if (r < 2) newv(OP_CONST, -1, -1, rnd() % 100, b);
            else if (r < 6) newv(OP_ADD, x, y, 0, b);
            else if (r < 8) newv(OP_SUB, x, y, 0, b);
            else if (r < 9) newv(OP_MUL, x, y, 0, b);
            else if (r < 10) newv(OP_AND, x, y, 0, b);
            else if (r < 11) newv(OP_COPY, x, -1, 0, b);
            else if (r < 13) newv(OP_LOAD, x, -1, 8 * (rnd() % 4), b);
            else if (r < 14) newv(OP_STORE, x, y, 0, b);
            else if (r < 15) newv(OP_CALL, x, y, 0, b);
            else newv(OP_ADD, x, x, 0, b);   // x + x: a GVN/fold candidate
        }
        int cond = newv(OP_LT, nv - 1, nv - 2, 0, b);
        if (b == blocks - 1) { newv(OP_RET, cond, -1, 0, b); succ0[b] = succ1[b] = -1; }
        else {
            int back = b > 2 && rnd() % 4 == 0 ? b - 1 - rnd() % 2 : b + 1 + rnd() % 2;
            if (back >= blocks) back = blocks - 1;
            succ0[b] = b + 1; succ1[b] = back;
            newv(OP_BR, cond, -1, 0, b);
        }
        bend[b] = nv;
        nb++;
    }
    // Jump arguments: pass recent values of the source block.
    for (int b = 0; b < nb; b++) for (int s = 0; s < 2; s++) {
        int t = s ? succ1[b] : succ0[b]; if (t < 0) continue;
        for (int i = 0; i < nbparam[t]; i++) jarg[b][s][i] = bstart[b] + rnd() % (bend[b] - bstart[b] - 1);
    }
}

// --- 1. CFG ---
static int stackB[MAXB], visited[MAXB], childIdx[MAXB];
static void cfg(void) {
    memset(npred, 0, sizeof(int) * nb);
    for (int b = 0; b < nb; b++) { if (succ0[b] >= 0) npred[succ0[b]]++; if (succ1[b] >= 0 && succ1[b] != succ0[b]) npred[succ1[b]]++; }
    predOff[0] = 0; for (int b = 0; b < nb; b++) predOff[b + 1] = predOff[b] + npred[b];
    static int fill[MAXB]; memset(fill, 0, sizeof(int) * nb);
    for (int b = 0; b < nb; b++) {
        if (succ0[b] >= 0) preds[predOff[succ0[b]] + fill[succ0[b]]++] = b;
        if (succ1[b] >= 0 && succ1[b] != succ0[b]) preds[predOff[succ1[b]] + fill[succ1[b]]++] = b;
    }
    // iterative DFS post-order
    memset(visited, 0, sizeof(int) * nb);
    int sp = 0, n = nb; stackB[sp++] = 0; visited[0] = 1; childIdx[0] = 0;
    while (sp) {
        int b = stackB[sp - 1];
        int s = childIdx[b] == 0 ? succ0[b] : childIdx[b] == 1 ? succ1[b] : -2;
        if (s == -2) { rpo[--n] = b; sp--; continue; }
        childIdx[b]++;
        if (s >= 0 && !visited[s]) { visited[s] = 1; childIdx[s] = 0; stackB[sp++] = s; }
    }
    for (int i = 0; i < n; i++) rpo[i] = -1;   // unreachable blocks (none expected)
    for (int i = 0; i < nb; i++) if (rpo[i] >= 0) rpoIndex[rpo[i]] = i;
}

// --- 2. fold + copy propagation + GVN ---
#define HBITS 16
static int htab[1 << HBITS];
static int resolve(int v) { while (v >= 0 && repl[v] != v) v = repl[v]; return v; }
static void fold(void) {
    for (int v = 0; v < nv; v++) repl[v] = v;
    memset(htab, -1, sizeof htab);
    for (int i = 0; i < nb; i++) {
        int b = rpo[i]; if (b < 0) continue;
        for (int v = bstart[b]; v < bend[b]; v++) {
            if (a0[v] >= 0) a0[v] = resolve(a0[v]);
            if (a1[v] >= 0) a1[v] = resolve(a1[v]);
            int o = op[v];
            if (o == OP_COPY) { repl[v] = a0[v]; continue; }
            if (o >= OP_ADD && o <= OP_LT && op[a0[v]] == OP_CONST && op[a1[v]] == OP_CONST) {
                int64_t x = imm[a0[v]], y = imm[a1[v]];
                imm[v] = o == OP_ADD ? x + y : o == OP_SUB ? x - y : o == OP_MUL ? x * y : o == OP_AND ? (x & y) : x < y;
                op[v] = OP_CONST; a0[v] = a1[v] = -1;
            }
            if (o == OP_SUB && a0[v] == a1[v]) { op[v] = OP_CONST; imm[v] = 0; a0[v] = a1[v] = -1; }
            if ((op[v] >= OP_ADD && op[v] <= OP_LT) || op[v] == OP_CONST) {   // pure: value-number it (within the dominating RPO prefix, simplified)
                unsigned h = (unsigned)(op[v] * 31 + a0[v] * 1000003 + a1[v] * 7919 + (unsigned)imm[v]) & ((1 << HBITS) - 1);
                for (;;) {
                    int w = htab[h];
                    if (w < 0) { htab[h] = v; break; }
                    if (op[w] == op[v] && a0[w] == a0[v] && a1[w] == a1[v] && imm[w] == imm[v] && blk[w] == blk[v]) { repl[v] = w; break; }
                    h = (h + 1) & ((1 << HBITS) - 1);
                }
            }
        }
        for (int s = 0; s < 2; s++) { int t = s ? succ1[b] : succ0[b]; if (t < 0) continue; for (int k = 0; k < nbparam[t]; k++) jarg[b][s][k] = resolve(jarg[b][s][k]); }
    }
}

// --- 3. DCE ---
static int work[MAXV], live[MAXV];
static int sideEffect(int o) { return o == OP_STORE || o == OP_CALL || o == OP_BR || o == OP_RET || o == OP_PARAM; }
static void dce(void) {
    int n = 0;
    memset(live, 0, sizeof(int) * nv);
    for (int v = 0; v < nv; v++) if (repl[v] == v && sideEffect(op[v])) { live[v] = 1; work[n++] = v; }
    for (int b = 0; b < nb; b++) for (int s = 0; s < 2; s++) { int t = s ? succ1[b] : succ0[b]; if (t < 0) continue;
        for (int k = 0; k < nbparam[t]; k++) { int x = jarg[b][s][k]; if (!live[x]) { live[x] = 1; work[n++] = x; } } }
    while (n) {
        int v = work[--n];
        if (a0[v] >= 0 && !live[a0[v]]) { live[a0[v]] = 1; work[n++] = a0[v]; }
        if (a1[v] >= 0 && !live[a1[v]]) { live[a1[v]] = 1; work[n++] = a1[v]; }
    }
}

// --- 4. liveness on bitsets (one bit per value) ---
static uint64_t *liveIn, *liveOut; static int words;
static void liveness(void) {
    words = (nv + 63) / 64;
    static uint64_t storage[2 * MAXB * 64];   // enough for the sizes used here
    if ((size_t)2 * nb * words > sizeof storage / 8) { fprintf(stderr, "liveness storage too small\n"); exit(1); }
    liveIn = storage; liveOut = storage + (size_t)nb * words;
    memset(storage, 0, sizeof(uint64_t) * 2 * nb * words);
    static uint64_t tmp[MAXV / 64 + 1];
    int changed = 1;
    while (changed) {
        changed = 0;
        for (int i = nb - 1; i >= 0; i--) {
            int b = rpo[i]; if (b < 0) continue;
            uint64_t *out = liveOut + (size_t)b * words;
            for (int s = 0; s < 2; s++) { int t = s ? succ1[b] : succ0[b]; if (t < 0) continue;
                uint64_t *in = liveIn + (size_t)t * words;
                for (int w = 0; w < words; w++) out[w] |= in[w];
                for (int k = 0; k < nbparam[t]; k++) { int x = jarg[b][s][k]; out[x >> 6] |= 1ull << (x & 63); }
                for (int k = 0; k < nbparam[t]; k++) { int p = bparam0[t] + k; out[p >> 6] &= ~(1ull << (p & 63)); }
            }
            memcpy(tmp, out, 8 * words);
            for (int v = bend[b] - 1; v >= bstart[b]; v--) {
                if (!live[v] || repl[v] != v) continue;
                tmp[v >> 6] &= ~(1ull << (v & 63));
                if (a0[v] >= 0) tmp[a0[v] >> 6] |= 1ull << (a0[v] & 63);
                if (a1[v] >= 0) tmp[a1[v] >> 6] |= 1ull << (a1[v] & 63);
            }
            uint64_t *in = liveIn + (size_t)b * words;
            for (int w = 0; w < words; w++) if (in[w] != tmp[w]) { in[w] = tmp[w]; changed = 1; }
        }
    }
}

// --- 5. intervals + linear scan ---
static int start[MAXV], endp[MAXV], reg[MAXV], order[MAXV], active[NREG + 1], nspill;
static int cmpStart(const void *x, const void *y) { return start[*(int *)x] - start[*(int *)y]; }
static void regalloc(void) {
    // positions: instruction index in RPO layout
    static int pos[MAXV]; int p = 0;
    for (int i = 0; i < nb; i++) { int b = rpo[i]; if (b < 0) continue; for (int v = bstart[b]; v < bend[b]; v++) pos[v] = p++; }
    for (int v = 0; v < nv; v++) { start[v] = 1 << 30; endp[v] = -1; }
    for (int i = 0; i < nb; i++) {
        int b = rpo[i]; if (b < 0) continue;
        int bs = pos[bstart[b]], be = pos[bend[b] - 1];
        uint64_t *in = liveIn + (size_t)b * words, *out = liveOut + (size_t)b * words;
        for (int w = 0; w < words; w++) {
            uint64_t m = in[w] | out[w];
            while (m) { int v = w * 64 + __builtin_ctzll(m); m &= m - 1;
                if (in[w] >> (v & 63) & 1) { if (bs < start[v]) start[v] = bs; }
                if (out[w] >> (v & 63) & 1) { if (be > endp[v]) endp[v] = be; } }
        }
        for (int v = bstart[b]; v < bend[b]; v++) {
            if (!live[v] || repl[v] != v) continue;
            if (pos[v] < start[v]) start[v] = pos[v];
            if (pos[v] > endp[v]) endp[v] = pos[v];
            if (a0[v] >= 0 && pos[v] > endp[a0[v]]) endp[a0[v]] = pos[v];
            if (a1[v] >= 0 && pos[v] > endp[a1[v]]) endp[a1[v]] = pos[v];
        }
    }
    int n = 0; for (int v = 0; v < nv; v++) if (live[v] && repl[v] == v && endp[v] >= 0) order[n++] = v;
    qsort(order, n, sizeof(int), cmpStart);
    int freeMask = (1 << NREG) - 1, na = 0; nspill = 0;
    for (int i = 0; i < n; i++) {
        int v = order[i];
        for (int j = 0; j < na; ) { int w = active[j]; if (endp[w] < start[v]) { freeMask |= 1 << reg[w]; active[j] = active[--na]; } else j++; }
        if (freeMask) { int r = __builtin_ctz(freeMask); freeMask &= ~(1 << r); reg[v] = r; active[na++] = v; }
        else {  // spill the interval that ends last
            int far = 0; for (int j = 1; j < na; j++) if (endp[active[j]] > endp[active[far]]) far = j;
            int w = active[far];
            if (endp[w] > endp[v]) { reg[v] = reg[w]; reg[w] = -1 - nspill++; active[far] = v; }
            else reg[v] = -1 - nspill++;
        }
    }
}

// --- 6. encode ---
static uint8_t code[64 * MAXV]; static int clen;
static const int hw[NREG] = { 0, 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 };   // rax..r15 minus rsp, rbp
static void rr(int opc, int d, int s) {   // op r64, r64
    code[clen++] = 0x48 | (s >> 3 & 1) << 2 | (d >> 3 & 1); code[clen++] = opc; code[clen++] = 0xC0 | (s & 7) << 3 | (d & 7);
}
static void loadSpill(int r, int slot) { code[clen++] = 0x48 | (r >> 3 & 1) << 2; code[clen++] = 0x8B; code[clen++] = 0x84 | (r & 7) << 3; code[clen++] = 0x24; memcpy(code + clen, &(int32_t){ 8 * slot }, 4); clen += 4; }
static int physical(int v, int scratch) { int r = reg[v]; if (r >= 0) return hw[r]; loadSpill(scratch, -1 - r); return scratch; }
static void encode(void) {
    clen = 0;
    for (int i = 0; i < nb; i++) {
        int b = rpo[i]; if (b < 0) continue;
        for (int v = bstart[b]; v < bend[b]; v++) {
            if (!live[v] || repl[v] != v) continue;
            int o = op[v]; int d = reg[v] >= 0 ? hw[reg[v]] : 0;
            switch (o) {
            case OP_CONST: code[clen++] = 0x48 | (d >> 3 & 1); code[clen++] = 0xB8 | (d & 7); memcpy(code + clen, &imm[v], 8); clen += 8; break;
            case OP_ADD: case OP_SUB: case OP_AND: { int x = physical(a0[v], 0), y = physical(a1[v], 5);
                if (d != x) rr(0x89, d, x); rr(o == OP_ADD ? 0x01 : o == OP_SUB ? 0x29 : 0x21, d, y); break; }
            case OP_MUL: { int x = physical(a0[v], 0), y = physical(a1[v], 5); if (d != x) rr(0x89, d, x);
                code[clen++] = 0x48 | (d >> 3 & 1) << 2 | (y >> 3 & 1); code[clen++] = 0x0F; code[clen++] = 0xAF; code[clen++] = 0xC0 | (d & 7) << 3 | (y & 7); break; }
            case OP_LT: { int x = physical(a0[v], 0), y = physical(a1[v], 5); rr(0x39, x, y);
                code[clen++] = 0x0F; code[clen++] = 0x9C; code[clen++] = 0xC0 | (d & 7); break; }
            case OP_LOAD: { int x = physical(a0[v], 0); code[clen++] = 0x48 | (d >> 3 & 1) << 2 | (x >> 3 & 1); code[clen++] = 0x8B; code[clen++] = 0x80 | (d & 7) << 3 | (x & 7); memcpy(code + clen, &(int32_t){ (int32_t)imm[v] }, 4); clen += 4; break; }
            case OP_STORE: { int x = physical(a0[v], 0), y = physical(a1[v], 5); code[clen++] = 0x48 | (y >> 3 & 1) << 2 | (x >> 3 & 1); code[clen++] = 0x89; code[clen++] = 0x80 | (y & 7) << 3 | (x & 7); memset(code + clen, 0, 4); clen += 4; break; }
            case OP_CALL: code[clen++] = 0xE8; memset(code + clen, 0, 4); clen += 4; break;
            case OP_BR: { int x = physical(a0[v], 0); rr(0x85, x, x); code[clen++] = 0x0F; code[clen++] = 0x85; memset(code + clen, 0, 4); clen += 4; code[clen++] = 0xE9; memset(code + clen, 0, 4); clen += 4; break; }
            case OP_RET: code[clen++] = 0xC3; break;
            default: break;
            }
        }
    }
}


// --- extra passes for the "production-like" pipeline (cycle 55) ---
// 7. dominators (Cooper, Harvey & Kennedy iterative algorithm over RPO)
static int idom[MAXB], loopDepth[MAXB], loopHeader[MAXB];
static int intersect(int a, int b) { while (a != b) { while (rpoIndex[a] > rpoIndex[b]) a = idom[a]; while (rpoIndex[b] > rpoIndex[a]) b = idom[b]; } return a; }
static void dominators(void) {
    for (int b = 0; b < nb; b++) idom[b] = -1;
    idom[rpo[0]] = rpo[0];
    int changed = 1;
    while (changed) {
        changed = 0;
        for (int i = 1; i < nb; i++) {
            int b = rpo[i], d = -1;
            for (int k = predOff[b]; k < predOff[b + 1]; k++) { int p = preds[k]; if (idom[p] < 0) continue; d = d < 0 ? p : intersect(p, d); }
            if (d >= 0 && idom[b] != d) { idom[b] = d; changed = 1; }
        }
    }
}
static int dominates(int a, int b) { while (b != a && idom[b] != b) b = idom[b]; return a == b; }
// 8. natural loops: back edge t -> h with h dominating t; mark blocks by walking preds
static int loopStack[MAXB];
static void loops(void) {
    memset(loopDepth, 0, sizeof(int) * nb); memset(loopHeader, -1, sizeof(int) * nb);
    for (int t = 0; t < nb; t++) for (int s = 0; s < 2; s++) {
        int h = s ? succ1[t] : succ0[t]; if (h < 0 || !dominates(h, t)) continue;
        int sp = 0; loopStack[sp++] = t; static int mark[MAXB]; static int gen = 0; gen++;
        mark[h] = gen; loopDepth[h]++;
        while (sp) { int b = loopStack[--sp]; if (mark[b] == gen) continue; mark[b] = gen; loopDepth[b]++; loopHeader[b] = h;
            for (int k = predOff[b]; k < predOff[b + 1]; k++) loopStack[sp++] = preds[k]; }
    }
}
// 9. LICM: a pure op whose operands are defined outside the loop is hoisted (re-blocked to the
//    header's immediate dominator); iterate to a fixpoint over RPO
static void licm(void) {
    for (int i = 0; i < nb; i++) {
        int b = rpo[i]; if (loopHeader[b] < 0) continue;
        int h = loopHeader[b], pre = idom[h];
        for (int v = bstart[b]; v < bend[b]; v++) {
            if (!live[v] || repl[v] != v) continue;
            int o = op[v]; if (!(o >= OP_ADD && o <= OP_LT)) continue;
            int x = a0[v], y = a1[v];
            int xin = x >= 0 && loopDepth[blk[x]] >= loopDepth[b] && blk[x] != pre;
            int yin = y >= 0 && loopDepth[blk[y]] >= loopDepth[b] && blk[y] != pre;
            if (!xin && !yin) blk[v] = pre;            // hoisted (the scheduler would place it)
        }
    }
}
// 10. range analysis for bounds-check elimination: interval per value, forward over RPO,
//     one widening step at loop headers; a LOAD whose index range is within [0, 7] is "proved"
static int64_t lo[MAXV], hi[MAXV]; static long checksProved;
static void ranges(void) {
    for (int i = 0; i < nb; i++) {
        int b = rpo[i];
        for (int v = bstart[b]; v < bend[b]; v++) {
            int64_t L = INT64_MIN / 4, H = INT64_MAX / 4;
            int x = a0[v], y = a1[v];
            switch (op[v]) {
            case OP_CONST: L = H = imm[v]; break;
            case OP_AND: if (y >= 0 && lo[y] >= 0 && hi[y] < (1 << 20)) { L = 0; H = hi[y]; } break;
            case OP_ADD: if (x >= 0 && y >= 0) { L = lo[x] + lo[y]; H = hi[x] + hi[y]; } break;
            case OP_SUB: if (x >= 0 && y >= 0) { L = lo[x] - hi[y]; H = hi[x] - lo[y]; } break;
            case OP_LT: L = 0; H = 1; break;
            case OP_LOAD: if (x >= 0 && lo[x] >= 0 && hi[x] <= 7) checksProved++; break;
            default: break;
            }
            if (loopDepth[b] > 0 && op[v] == OP_PARAM) { L = INT64_MIN / 4; H = INT64_MAX / 4; }   // widened
            lo[v] = L; hi[v] = H;
        }
    }
}

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

int main(int argc, char **argv) {
    int size = argc > 1 ? atoi(argv[1]) : 500, count = argc > 2 ? atoi(argv[2]) : 2000;
    int extended = argc > 3 && atoi(argv[3]);
    double phase[8] = { 0 }; long totalValues = 0, totalBytes = 0, spills = 0, removed = 0;
    for (int f = 0; f < count; f++) {
        double t0 = now(); generate(size); double t1 = now();
        cfg(); double t2 = now(); fold(); double t3 = now(); dce(); double t4 = now();
        phase[3] += t4 - t3;
        if (extended) {                          // dominators, loops, LICM, ranges, then a second fold + DCE
            dominators(); loops(); licm(); ranges(); fold(); dce();
            double e1 = now(); phase[7] += e1 - t4; t4 = e1;
        }
        liveness(); double t5 = now(); regalloc(); double t6 = now(); encode(); double t7 = now();
        phase[0] += t1 - t0; phase[1] += t2 - t1; phase[2] += t3 - t2; phase[4] += t5 - t4; phase[5] += t6 - t5; phase[6] += t7 - t6;
        totalValues += nv; totalBytes += clen; spills += nspill;
        for (int v = 0; v < nv; v++) removed += !live[v] || repl[v] != v;
    }
    double opt = phase[1] + phase[2] + phase[3] + phase[4] + phase[5] + phase[6] + phase[7];
    printf("%d functions x ~%d values: %ld values, %.1f%% removed, %ld spills, %ld code bytes\n", count, size, totalValues, 100.0 * removed / totalValues, spills, totalBytes);
    const char *names[] = { "generate (not counted)", "cfg", "fold/copyprop/gvn", "dce", "liveness", "intervals+linear scan", "encode", "dom+loops+licm+ranges+refold" };
    for (int i = 0; i < 8; i++) printf("  %-24s %7.1f ns/value\n", names[i], 1e9 * phase[i] / totalValues);
    printf("  %-24s %7.1f ns/value  (%.3f us/value)\n", "TOTAL pipeline", 1e9 * opt / totalValues, 1e6 * opt / totalValues);
    return 0;
}
