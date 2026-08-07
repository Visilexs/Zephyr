// Zephyr runtime - linked into every compiled Zephyr program.
// Provides: conservative mark-sweep GC, strings, lists, printing, panics.
// All Zephyr values are 64 bits: int=i64, bool=0/1, float=f64 bit pattern,
// str/list/struct = pointer to GC payload.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <setjmp.h>
#ifdef _WIN32
#include <windows.h>
#endif

typedef struct { int64_t len; char data[]; } Str;
typedef struct { int64_t len; int64_t cap; uint64_t* data; } List;

void rt_panic(const char* msg) {
    fflush(stdout);
    fprintf(stderr, "panic: %s\n", msg);
    exit(1);
}

// ---------------- GC: conservative mark-sweep over bump-allocated chunks ----
// Objects are carved out of 256 KB chunks with a bump pointer; dead objects go
// to segregated free lists for reuse instead of free(). Collection scans the
// machine stack (and registers via setjmp) for values that look like payload
// pointers, then transitively scans marked payloads.
// 8-byte header; free-list links live in the (dead) payload, and the sweep
// walks chunks directly, so no per-object list pointer is needed.
typedef struct Obj { uint32_t size; uint16_t cls; uint16_t mark; } Obj;

enum { M_WHITE = 0, M_MARK = 1, M_FREE = 2 };

#define GC_BIG 0xFFFF
#define NCLASSES 12
static const uint32_t class_sizes[NCLASSES] =
    { 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 1024 };

// Each chunk carries a bitmap with one bit per 8-byte granule, set when an
// object is first carved at that address (addresses never move, so the bit
// is permanent). "Is this a heap pointer?" is then a range check + bit test
// instead of a sorted-array search rebuilt every collection.
#define CHUNK_BYTES (1 << 18)
typedef struct Chunk {
    struct Chunk* next;
    char* used;                 // bump high-water mark once the chunk retires
    uint8_t bits[CHUNK_BYTES / 64];
} Chunk;
static Chunk* all_chunks = NULL;
static Chunk* cur_chunk = NULL;
static char* bump = NULL;
static char* bump_end = NULL;
static Obj* freelists[NCLASSES];

static Chunk** chunk_arr = NULL;    // sorted by address, for candidate lookup
static int n_chunks = 0, chunk_cap = 0;
static uintptr_t heap_min = ~(uintptr_t)0, heap_max = 0;

static Obj** bigs = NULL;           // oversized objects live outside chunks
static int n_bigs = 0, big_cap = 0;

static size_t heap_live = 0;
static size_t gc_threshold = 1 << 19;
static uintptr_t stack_base;
static uint8_t class_map[129]; // (rounded size >> 3) -> size class

static void gc_init(void) {
    int cls = 0;
    for (int i = 0; i <= 128; i++) {
        while ((uint32_t)(i * 8) > class_sizes[cls]) cls++;
        class_map[i] = (uint8_t)cls;
    }
}

static void add_chunk_sorted(Chunk* c) {
    if (n_chunks == chunk_cap) {
        chunk_cap = chunk_cap ? chunk_cap * 2 : 16;
        chunk_arr = realloc(chunk_arr, chunk_cap * sizeof(Chunk*));
        if (!chunk_arr) rt_panic("out of memory (gc)");
    }
    int i = n_chunks++;
    while (i > 0 && (uintptr_t)chunk_arr[i - 1] > (uintptr_t)c) {
        chunk_arr[i] = chunk_arr[i - 1];
        i--;
    }
    chunk_arr[i] = c;
    if ((uintptr_t)c < heap_min) heap_min = (uintptr_t)c;
    if ((uintptr_t)c + CHUNK_BYTES > heap_max) heap_max = (uintptr_t)c + CHUNK_BYTES;
}

static uint64_t* g_globals = NULL;      // Zephyr global variables (extra GC roots)
static int64_t g_nglobals = 0;

void rt_set_globals(uint64_t* p, int64_t n) { g_globals = p; g_nglobals = n; }

static Obj* find_obj(uintptr_t p) { // p must equal a payload start
    if (p >= heap_min && p < heap_max && !(p & 7)) {
        int lo = 0, hi = n_chunks;
        while (lo < hi) {
            int mid = (lo + hi) / 2;
            if ((uintptr_t)chunk_arr[mid] + CHUNK_BYTES <= p) lo = mid + 1;
            else hi = mid;
        }
        if (lo < n_chunks) {
            uintptr_t base = (uintptr_t)chunk_arr[lo];
            if (p >= base + sizeof(Chunk) + sizeof(Obj) && p < base + CHUNK_BYTES) {
                size_t g = (p - base) >> 3;
                if (chunk_arr[lo]->bits[g >> 3] & (1u << (g & 7)))
                    return (Obj*)(p - sizeof(Obj));
            }
        }
    }
    for (int i = 0; i < n_bigs; i++)
        if ((uintptr_t)(bigs[i] + 1) == p) return bigs[i];
    return NULL;
}

static Obj** worklist = NULL;
static size_t wl_len = 0, wl_cap = 0;

static void mark_candidate(uintptr_t p) {
    Obj* o = find_obj(p);
    if (!o || o->mark != M_WHITE) return;
    o->mark = M_MARK;
    if (wl_len == wl_cap) {
        wl_cap = wl_cap ? wl_cap * 2 : 256;
        worklist = realloc(worklist, wl_cap * sizeof(Obj*));
        if (!worklist) rt_panic("out of memory (gc)");
    }
    worklist[wl_len++] = o;
}

static void scan_range(uintptr_t lo, uintptr_t hi) {
    lo = (lo + 7) & ~(uintptr_t)7;
    for (uintptr_t a = lo; a + 8 <= hi; a += 8)
        mark_candidate(*(uintptr_t*)a);
}

static void gc_collect(void) {
    // invariant: no object is M_MARK on entry (sweep resets live ones)
    wl_len = 0;
    jmp_buf regs;               // spills callee-saved registers onto the stack
    setjmp(regs);
    scan_range((uintptr_t)&regs, stack_base); // fills the worklist with roots
    if (g_nglobals)
        scan_range((uintptr_t)g_globals, (uintptr_t)(g_globals + g_nglobals));
    while (wl_len) {
        Obj* o = worklist[--wl_len];
        uintptr_t payload = (uintptr_t)(o + 1);
        scan_range(payload, payload + o->size);
    }

    // sweep: walk every chunk; objects are contiguous, sizes chain them
    heap_live = 0;
    for (Chunk* c = all_chunks; c; c = c->next) {
        char* p = (char*)c + sizeof(Chunk);
        char* end = c == cur_chunk ? bump : c->used;
        while (p < end) {
            Obj* o = (Obj*)p;
            p += sizeof(Obj) + o->size;
            if (o->mark == M_MARK) {
                o->mark = M_WHITE;
                heap_live += o->size + sizeof(Obj);
            } else if (o->mark == M_WHITE) { // newly dead -> free list
                o->mark = M_FREE;
                *(Obj**)(o + 1) = freelists[o->cls];
                freelists[o->cls] = o;
            } // M_FREE: already on a free list
        }
    }
    for (int i = 0; i < n_bigs; ) {
        Obj* o = bigs[i];
        if (o->mark == M_MARK) {
            o->mark = M_WHITE;
            heap_live += o->size + sizeof(Obj);
            i++;
        } else {
            bigs[i] = bigs[--n_bigs];
            free(o);
        }
    }
    size_t next = heap_live + heap_live / 2; // 1.5x: tighter peak than 2x
    gc_threshold = next > (1 << 19) ? next : (1 << 19);
}

void* rt_alloc(uint64_t size) {
    if (heap_live > gc_threshold) gc_collect();
    if (size > 0x7FFFFFF0ULL) rt_panic("allocation too large");
    uint64_t need = (size + 7) & ~7ULL;
    int cls = need <= 1024 ? class_map[need >> 3] : -1;
    Obj* o;
    if (cls < 0) { // oversized: plain calloc, freed for real at sweep
        o = calloc(1, sizeof(Obj) + need);
        if (!o) { gc_collect(); o = calloc(1, sizeof(Obj) + need); }
        if (!o) rt_panic("out of memory");
        o->cls = GC_BIG;
        if (n_bigs == big_cap) {
            big_cap = big_cap ? big_cap * 2 : 16;
            bigs = realloc(bigs, big_cap * sizeof(Obj*));
            if (!bigs) rt_panic("out of memory (gc)");
        }
        bigs[n_bigs++] = o;
    } else {
        need = class_sizes[cls];
        if (freelists[cls]) {
            o = freelists[cls];
            freelists[cls] = *(Obj**)(o + 1); // link lives in the dead payload
            memset(o + 1, 0, need);
        } else {
            if (!bump || bump + sizeof(Obj) + need > bump_end) {
                Chunk* c = calloc(1, CHUNK_BYTES); // fresh chunks are pre-zeroed
                if (!c) { gc_collect(); c = calloc(1, CHUNK_BYTES); }
                if (!c) rt_panic("out of memory");
                c->next = all_chunks;
                all_chunks = c;
                add_chunk_sorted(c);
                if (cur_chunk) cur_chunk->used = bump; // retire old chunk
                cur_chunk = c;
                bump = (char*)c + sizeof(Chunk);
                bump_end = (char*)c + CHUNK_BYTES;
            }
            o = (Obj*)bump;
            bump += sizeof(Obj) + need;
            // permanent object-start bit for the conservative membership test
            uintptr_t base = (uintptr_t)bump_end - CHUNK_BYTES;
            size_t g = ((uintptr_t)(o + 1) - base) >> 3;
            ((Chunk*)base)->bits[g >> 3] |= (uint8_t)(1u << (g & 7));
        }
        o->cls = (uint16_t)cls;
    }
    o->size = (uint32_t)need;
    o->mark = M_WHITE;
    heap_live += need + sizeof(Obj);
    return o + 1;
}

// ---------------- strings ----------------
static Str* str_new(int64_t len) {
    Str* s = rt_alloc(sizeof(Str) + len);
    s->len = len;
    return s;
}

Str* rt_str_concat(Str* a, Str* b) {
    Str* s = str_new(a->len + b->len);
    memcpy(s->data, a->data, a->len);
    memcpy(s->data + a->len, b->data, b->len);
    return s;
}

int64_t rt_str_eq(Str* a, Str* b) {
    return a->len == b->len && memcmp(a->data, b->data, a->len) == 0;
}

int64_t rt_str_cmp(Str* a, Str* b) {
    int64_t n = a->len < b->len ? a->len : b->len;
    int c = memcmp(a->data, b->data, n);
    if (c) return c < 0 ? -1 : 1;
    return a->len < b->len ? -1 : a->len > b->len ? 1 : 0;
}

static void str_cbuf(Str* s, char* buf, size_t cap) {
    size_t n = (size_t)s->len < cap - 1 ? (size_t)s->len : cap - 1;
    memcpy(buf, s->data, n);
    buf[n] = 0;
}

int64_t rt_str_to_int(Str* s) {
    char buf[64], msg[96];
    str_cbuf(s, buf, sizeof buf);
    char* p = buf;
    while (*p == ' ' || *p == '\t') p++;
    char* end;
    long long v = strtoll(p, &end, 10);
    while (*end == ' ' || *end == '\t') end++;
    if (end == p || *end) {
        snprintf(msg, sizeof msg, "cannot convert \"%s\" to int", buf);
        rt_panic(msg);
    }
    return v;
}

uint64_t rt_str_to_float(Str* s) {
    char buf[64], msg[96];
    str_cbuf(s, buf, sizeof buf);
    char* p = buf;
    while (*p == ' ' || *p == '\t') p++;
    char* end;
    double v = strtod(p, &end);
    while (*end == ' ' || *end == '\t') end++;
    if (end == p || *end) {
        snprintf(msg, sizeof msg, "cannot convert \"%s\" to float", buf);
        rt_panic(msg);
    }
    uint64_t bits;
    memcpy(&bits, &v, 8);
    return bits;
}

Str* rt_str_sub(Str* s, int64_t lo, int64_t hi) {
    if (lo < 0 || hi < lo || hi > s->len) {
        char msg[96];
        snprintf(msg, sizeof msg, "invalid substring %lld..%lld (len %lld)",
                 (long long)lo, (long long)hi, (long long)s->len);
        rt_panic(msg);
    }
    Str* r = str_new(hi - lo);
    memcpy(r->data, s->data + lo, hi - lo);
    return r;
}

Str* rt_chr(int64_t c) {
    if (c < 0 || c > 255) {
        char msg[64];
        snprintf(msg, sizeof msg, "chr(%lld) out of range 0..255", (long long)c);
        rt_panic(msg);
    }
    Str* s = str_new(1);
    s->data[0] = (char)c;
    return s;
}

// ---------------- lists ----------------
List* rt_list_new(int64_t n) {
    List* l = rt_alloc(sizeof(List));
    int64_t cap = n > 4 ? n : 4;
    l->data = rt_alloc(cap * 8);
    l->len = n;
    l->cap = cap;
    return l;
}

void rt_list_push(List* l, uint64_t v) {
    if (l->len == l->cap) {
        int64_t cap = l->cap * 2;
        uint64_t* nd = rt_alloc(cap * 8);
        memcpy(nd, l->data, l->len * 8);
        l->data = nd;
        l->cap = cap;
    }
    l->data[l->len++] = v;
}

uint64_t rt_list_pop(List* l) {
    if (l->len == 0) rt_panic("pop from empty list");
    return l->data[--l->len];
}

void rt_bounds_fail(int64_t i, int64_t len) {
    char msg[96];
    snprintf(msg, sizeof msg, "index %lld out of bounds (len %lld)", (long long)i, (long long)len);
    rt_panic(msg);
}

void rt_div_zero(void) { rt_panic("division by zero"); }
void rt_mod_zero(void) { rt_panic("modulo by zero"); }

Str* rt_join(List* parts) {
    int64_t total = 0;
    for (int64_t i = 0; i < parts->len; i++)
        total += ((Str*)(uintptr_t)parts->data[i])->len;
    Str* r = str_new(total);
    int64_t at = 0;
    for (int64_t i = 0; i < parts->len; i++) {
        Str* p = (Str*)(uintptr_t)parts->data[i];
        memcpy(r->data + at, p->data, p->len);
        at += p->len;
    }
    return r;
}

// ---------------- OS: files & args ----------------
static int g_argc;
static char** g_argv;

Str* rt_read_file(Str* path) {
    char cpath[1024], msg[1100];
    str_cbuf(path, cpath, sizeof cpath);
    FILE* f = fopen(cpath, "rb");
    if (!f) { snprintf(msg, sizeof msg, "cannot read file \"%s\"", cpath); rt_panic(msg); }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    Str* s = str_new(n);
    if (n && fread(s->data, 1, n, f) != (size_t)n) {
        snprintf(msg, sizeof msg, "error reading file \"%s\"", cpath);
        rt_panic(msg);
    }
    fclose(f);
    return s;
}

void rt_write_file(Str* path, Str* data) {
    char cpath[1024], msg[1100];
    str_cbuf(path, cpath, sizeof cpath);
    FILE* f = fopen(cpath, "wb");
    if (!f) { snprintf(msg, sizeof msg, "cannot write file \"%s\"", cpath); rt_panic(msg); }
    if (data->len && fwrite(data->data, 1, data->len, f) != (size_t)data->len) {
        snprintf(msg, sizeof msg, "error writing file \"%s\"", cpath);
        rt_panic(msg);
    }
    fclose(f);
}

List* rt_args(void) {
    List* l = rt_list_new(g_argc);
    for (int i = 0; i < g_argc; i++) {
        size_t n = strlen(g_argv[i]);
        Str* s = str_new(n);
        memcpy(s->data, g_argv[i], n);
        l->data[i] = (uint64_t)(uintptr_t)s;
    }
    return l;
}

void rt_panic_str(Str* s) {
    char buf[512];
    str_cbuf(s, buf, sizeof buf);
    rt_panic(buf);
}

// ---------------- to-string / print ----------------
// The compiler emits a static type descriptor per printed type:
//   [0]=kind (0 int, 1 float, 2 bool, 3 str, 4 list, 5 struct)
//   list:   [1]=elem descriptor ptr
//   struct: [1]=name cstr, [2]=nfields, then per field: name cstr, descriptor ptr
typedef struct { char* p; size_t len, cap; } Buf;

static void bput(Buf* b, const char* s, size_t n) {
    if (b->len + n > b->cap) {
        b->cap = (b->len + n) * 2 + 64;
        b->p = realloc(b->p, b->cap);
        if (!b->p) rt_panic("out of memory");
    }
    memcpy(b->p + b->len, s, n);
    b->len += n;
}
static void bputc(Buf* b, char c) { bput(b, &c, 1); }

static void ts(Buf* b, uint64_t v, uint64_t* td, int repr) {
    char tmp[40];
    switch ((int)td[0]) {
    case 0: { // int: manual digits, ~10x faster than snprintf
        int64_t sv = (int64_t)v;
        uint64_t u = sv < 0 ? (uint64_t)0 - (uint64_t)sv : (uint64_t)sv;
        char* p = tmp + sizeof tmp;
        do { *--p = (char)('0' + (u % 10)); u /= 10; } while (u);
        if (sv < 0) *--p = '-';
        bput(b, p, (size_t)(tmp + sizeof tmp - p));
        break;
    }
    case 1: {
        double d;
        memcpy(&d, &v, 8);
        bput(b, tmp, snprintf(tmp, sizeof tmp, "%.15g", d));
        break;
    }
    case 2: v ? bput(b, "true", 4) : bput(b, "false", 5); break;
    case 3: {
        Str* s = (Str*)(uintptr_t)v;
        if (!repr) { bput(b, s->data, s->len); break; }
        bputc(b, '"');
        for (int64_t i = 0; i < s->len; i++) {
            char c = s->data[i];
            if (c == '"' || c == '\\') { bputc(b, '\\'); bputc(b, c); }
            else if (c == '\n') bput(b, "\\n", 2);
            else if (c == '\t') bput(b, "\\t", 2);
            else bputc(b, c);
        }
        bputc(b, '"');
        break;
    }
    case 4: {
        List* l = (List*)(uintptr_t)v;
        bputc(b, '[');
        for (int64_t i = 0; i < l->len; i++) {
            if (i) bput(b, ", ", 2);
            ts(b, l->data[i], (uint64_t*)td[1], 1);
        }
        bputc(b, ']');
        break;
    }
    case 5: {
        char* name = (char*)td[1];
        int64_t nf = (int64_t)td[2];
        bput(b, name, strlen(name));
        bputc(b, '{');
        for (int64_t f = 0; f < nf; f++) {
            if (f) bput(b, ", ", 2);
            char* fn = (char*)td[3 + 2 * f];
            bput(b, fn, strlen(fn));
            bput(b, ": ", 2);
            ts(b, ((uint64_t*)(uintptr_t)v)[f], (uint64_t*)td[4 + 2 * f], 1);
        }
        bputc(b, '}');
        break;
    }
    }
}

static Buf g_tsbuf; // persistent scratch: grows once, reused every call

Str* rt_to_str(uint64_t v, uint64_t* td) {
    g_tsbuf.len = 0;
    ts(&g_tsbuf, v, td, 0);
    Str* s = str_new(g_tsbuf.len);
    memcpy(s->data, g_tsbuf.p, g_tsbuf.len);
    return s;
}

void rt_print_val(uint64_t v, uint64_t* td) {
    if (td[0] == 3) { // plain str: write directly, no buffer copy
        Str* s = (Str*)(uintptr_t)v;
        fwrite(s->data, 1, s->len, stdout);
        fputc('\n', stdout);
        return;
    }
    g_tsbuf.len = 0;
    ts(&g_tsbuf, v, td, 0);
    bputc(&g_tsbuf, '\n');
    fwrite(g_tsbuf.p, 1, g_tsbuf.len, stdout);
}

void rt_emit(Str* s) { // print without newline, no buffer copy
    fwrite(s->data, 1, s->len, stdout);
}

// ---------------- string builder (interpolation) ----------------
// One shared byte buffer; nesting works by mark/truncate, so an interpolated
// expression may itself build strings without corrupting the outer one.
static Buf g_sb;

int64_t rt_sb_begin(void) { return (int64_t)g_sb.len; }
void rt_sb_txt(Str* s) { bput(&g_sb, s->data, s->len); }
void rt_sb_val(uint64_t v, uint64_t* td) { ts(&g_sb, v, td, 0); }
Str* rt_sb_end(int64_t mark) {
    Str* s = str_new(g_sb.len - (size_t)mark);
    memcpy(s->data, g_sb.p + mark, g_sb.len - (size_t)mark);
    g_sb.len = (size_t)mark;
    return s;
}

// ---------------- entry ----------------
// Two front doors. main(): the classic path, linked statically by gcc.
// rt_start(): the zephyr_rt.dll path — the compiler's built-in PE linker emits
// an exe whose entry stub calls rt_start(zephyr_main) with no C runtime of its
// own, so args come from GetCommandLineA.
#ifndef ZEPHYR_RT_DLL
extern void zephyr_main(void);

int main(int argc, char** argv) {
    volatile char base;
    stack_base = (uintptr_t)&base;
    gc_init();
    g_argc = argc;
    g_argv = argv;
    zephyr_main();
    fflush(stdout);
    return 0;
}
#endif

#ifdef _WIN32
static char* s_args[256];

static void parse_cmdline(void) {
    static char buf[32768];
    const char* cl = GetCommandLineA();
    size_t n = strlen(cl);
    if (n >= sizeof buf) n = sizeof buf - 1;
    memcpy(buf, cl, n);
    buf[n] = 0;
    char* p = buf;
    g_argc = 0;
    g_argv = s_args;
    while (*p && g_argc < 256) {
        while (*p == ' ' || *p == '\t') p++;
        if (!*p) break;
        char* out = p;
        s_args[g_argc++] = p;
        int quoted = 0;
        while (*p && (quoted || (*p != ' ' && *p != '\t'))) {
            if (*p == '"') { quoted = !quoted; p++; continue; }
            *out++ = *p++;
        }
        if (*p) p++;
        *out = 0;
    }
}

// no dllexport: MinGW auto-exports every non-static symbol only when nothing
// is explicitly marked, and the generated code needs all rt_* exported
void rt_start(void (*lm)(void)) {
    volatile char base;
    stack_base = (uintptr_t)&base;
    gc_init();
    parse_cmdline();
    lm();
    fflush(stdout);
    ExitProcess(0);
}
#endif
