// Zephyr compiler — lex -> parse -> typecheck -> x86-64 assembly.
// Written in C; emits Intel-syntax GAS assembly, assembled+linked by gcc
// together with runtime.o (GC, strings, lists). Output is a native .exe.
//
// Generated-code conventions:
//   - every value is 64 bits (int=i64, bool=0/1, float=f64 bits, rest=ptr)
//   - expression results in rax; temps on the machine stack (push/pop)
//   - Zephyr->Zephyr calls: args pushed left-to-right, caller cleans up,
//     arg i at [rbp + 16 + 8*(nparams-1-i)], return in rax
//   - locals at [rbp - 16 - 8*slot] (rbp-8 holds saved r12)
//   - calls into the C runtime align rsp to 16 and reserve shadow space,
//     using r12 (callee-saved) to remember rsp
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdarg.h>
#include <time.h>
#ifdef _WIN32
#include <windows.h>
#include <process.h>
#endif

// ---------------- util ----------------
static const char* g_file = "?";

static void die(int line, const char* fmt, ...) {
    va_list ap;
    fprintf(stderr, "%s:%d: error: ", g_file, line);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fputc('\n', stderr);
    exit(1);
}

static void* xmalloc(size_t n) {
    void* p = calloc(1, n ? n : 1);
    if (!p) { fprintf(stderr, "out of memory\n"); exit(1); }
    return p;
}

static char* xstrndup(const char* s, size_t n) {
    char* p = xmalloc(n + 1);
    memcpy(p, s, n);
    return p;
}

typedef struct { void** items; int len, cap; } Vec;
static void vpush(Vec* v, void* item) {
    if (v->len == v->cap) {
        v->cap = v->cap ? v->cap * 2 : 8;
        v->items = realloc(v->items, v->cap * sizeof(void*));
        if (!v->items) { fprintf(stderr, "out of memory\n"); exit(1); }
    }
    v->items[v->len++] = item;
}

// ---------------- lexer ----------------
enum {
    T_EOF, T_NL, T_INT, T_FLOAT, T_STR, T_ID,
    T_FN, T_LET, T_VAR, T_IF, T_ELSE, T_WHILE, T_FOR, T_IN, T_RETURN, T_STRUCT,
    T_AS, T_TRUE, T_FALSE, T_AND, T_OR, T_NOT, T_BREAK, T_CONTINUE,
    T_LP, T_RP, T_LB, T_RB, T_LS, T_RS, T_COMMA, T_COLON, T_DOT, T_DOTDOT,
    T_PLUS, T_MINUS, T_STAR, T_SLASH, T_PCT,
    T_LT, T_GT, T_LE, T_GE, T_EQEQ, T_NE, T_ASSIGN, T_ARROW,
    T_PLUSEQ, T_MINUSEQ, T_STAREQ, T_SLASHEQ,
    T_AMP, T_PIPE, T_CARET, T_SHL, T_SHR,
};

static const char* tokname(int t) {
    static const char* names[] = {
        "end of file", "newline", "int literal", "float literal", "string", "identifier",
        "fn", "let", "var", "if", "else", "while", "for", "in", "return", "struct",
        "as", "true", "false", "and", "or", "not", "break", "continue",
        "(", ")", "{", "}", "[", "]", ",", ":", ".", "..",
        "+", "-", "*", "/", "%",
        "<", ">", "<=", ">=", "==", "!=", "=", "->",
        "+=", "-=", "*=", "/=",
        "&", "|", "^", "<<", ">>",
    };
    return names[t];
}

typedef struct { int is_expr; char* text; int line; } StrPart;

typedef struct {
    int t, line;
    char* s;            // identifier text
    long long i;        // int literal
    double f;           // float literal
    Vec* parts;         // string literal parts
} Tok;

typedef struct { Tok* toks; int len, cap; } TokBuf;

static void tpush(TokBuf* b, Tok t) {
    if (b->len == b->cap) {
        b->cap = b->cap ? b->cap * 2 : 256;
        b->toks = realloc(b->toks, b->cap * sizeof(Tok));
        if (!b->toks) { fprintf(stderr, "out of memory\n"); exit(1); }
    }
    b->toks[b->len++] = t;
}

static int kw_lookup(const char* s, size_t n) {
    static const struct { const char* w; int t; } kws[] = {
        {"fn", T_FN}, {"let", T_LET}, {"var", T_VAR}, {"if", T_IF}, {"else", T_ELSE},
        {"while", T_WHILE}, {"for", T_FOR}, {"in", T_IN}, {"return", T_RETURN},
        {"struct", T_STRUCT}, {"as", T_AS}, {"true", T_TRUE}, {"false", T_FALSE},
        {"and", T_AND}, {"or", T_OR}, {"not", T_NOT}, {"break", T_BREAK},
        {"continue", T_CONTINUE},
    };
    for (size_t k = 0; k < sizeof kws / sizeof kws[0]; k++)
        if (strlen(kws[k].w) == n && memcmp(kws[k].w, s, n) == 0) return kws[k].t;
    return T_ID;
}

static Tok* lex(const char* src, int start_line, int* out_len) {
    TokBuf b = {0};
    size_t i = 0, n = strlen(src);
    int line = start_line, depth = 0;
    while (i < n) {
        char c = src[i];
        int tl = line;
        if (c == '\n') {
            if (depth == 0) tpush(&b, (Tok){ .t = T_NL, .line = line });
            i++; line++; continue;
        }
        if (c == ' ' || c == '\t' || c == '\r') { i++; continue; }
        if (c == '/' && src[i + 1] == '/') { while (i < n && src[i] != '\n') i++; continue; }

        if (c >= '0' && c <= '9') {
            size_t j = i;
            while (j < n && src[j] >= '0' && src[j] <= '9') j++;
            int isf = 0;
            if (src[j] == '.' && src[j + 1] != '.' && src[j + 1] >= '0' && src[j + 1] <= '9') {
                isf = 1; j++;
                while (j < n && src[j] >= '0' && src[j] <= '9') j++;
            }
            char* text = xstrndup(src + i, j - i);
            Tok t = { .t = isf ? T_FLOAT : T_INT, .line = tl };
            if (isf) t.f = strtod(text, NULL); else t.i = strtoll(text, NULL, 10);
            free(text);
            tpush(&b, t);
            i = j; continue;
        }

        if (c == '"') {
            i++;
            Vec* parts = xmalloc(sizeof(Vec));
            char buf[4096]; size_t bl = 0;
            for (;;) {
                if (i >= n || src[i] == '\n') die(tl, "unterminated string");
                char ch = src[i];
                if (bl >= sizeof buf - 4) die(tl, "string segment too long");
                if (ch == '"') { i++; break; }
                if (ch == '\\') {
                    char e = src[i + 1], v;
                    switch (e) {
                    case 'n': v = '\n'; break; case 't': v = '\t'; break;
                    case '\\': v = '\\'; break; case '"': v = '"'; break;
                    case '{': v = '{'; break; case '}': v = '}'; break;
                    default: die(line, "unknown escape \\%c", e); v = 0;
                    }
                    buf[bl++] = v; i += 2; continue;
                }
                if (ch == '{') { // interpolation
                    if (bl) {
                        StrPart* p = xmalloc(sizeof(StrPart));
                        p->text = xstrndup(buf, bl); bl = 0;
                        vpush(parts, p);
                    }
                    int d = 1; size_t j = i + 1;
                    while (j < n && d > 0) {
                        if (src[j] == '{') d++;
                        else if (src[j] == '}') { d--; if (!d) break; }
                        else if (src[j] == '\n') die(line, "unterminated interpolation");
                        j++;
                    }
                    if (d > 0) die(line, "unterminated interpolation");
                    StrPart* p = xmalloc(sizeof(StrPart));
                    p->is_expr = 1; p->line = line;
                    p->text = xstrndup(src + i + 1, j - i - 1);
                    vpush(parts, p);
                    i = j + 1; continue;
                }
                buf[bl++] = ch; i++;
            }
            if (bl || parts->len == 0) {
                StrPart* p = xmalloc(sizeof(StrPart));
                p->text = xstrndup(buf, bl);
                vpush(parts, p);
            }
            tpush(&b, (Tok){ .t = T_STR, .line = tl, .parts = parts });
            continue;
        }

        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_') {
            size_t j = i;
            while (j < n && ((src[j] >= 'a' && src[j] <= 'z') || (src[j] >= 'A' && src[j] <= 'Z') ||
                             (src[j] >= '0' && src[j] <= '9') || src[j] == '_')) j++;
            int t = kw_lookup(src + i, j - i);
            Tok tok = { .t = t, .line = tl };
            if (t == T_ID) tok.s = xstrndup(src + i, j - i);
            tpush(&b, tok);
            i = j; continue;
        }

        static const struct { const char* p; int t; } puncts[] = {
            {"->", T_ARROW}, {"..", T_DOTDOT}, {"==", T_EQEQ}, {"!=", T_NE},
            {"<=", T_LE}, {">=", T_GE}, {"+=", T_PLUSEQ}, {"-=", T_MINUSEQ},
            {"*=", T_STAREQ}, {"/=", T_SLASHEQ}, {"<<", T_SHL}, {">>", T_SHR},
            {"(", T_LP}, {")", T_RP}, {"{", T_LB}, {"}", T_RB}, {"[", T_LS}, {"]", T_RS},
            {",", T_COMMA}, {":", T_COLON}, {".", T_DOT}, {"+", T_PLUS}, {"-", T_MINUS},
            {"*", T_STAR}, {"/", T_SLASH}, {"%", T_PCT}, {"<", T_LT}, {">", T_GT}, {"=", T_ASSIGN},
            {"&", T_AMP}, {"|", T_PIPE}, {"^", T_CARET},
        };
        int matched = -1;
        for (size_t k = 0; k < sizeof puncts / sizeof puncts[0]; k++)
            if (strncmp(src + i, puncts[k].p, strlen(puncts[k].p)) == 0) { matched = (int)k; break; }
        if (matched < 0) die(tl, "unexpected character '%c'", c);
        int t = puncts[matched].t;
        if (t == T_LP || t == T_LS) depth++;
        if (t == T_RP || t == T_RS) { if (depth) depth--; }
        tpush(&b, (Tok){ .t = t, .line = tl });
        i += strlen(puncts[matched].p);
    }
    tpush(&b, (Tok){ .t = T_EOF, .line = line });
    *out_len = b.len;
    return b.toks;
}

// ---------------- AST ----------------
enum {
    N_PROG, N_FN, N_STRUCTDEF, N_PARAM, N_FIELDDEF,
    N_DECL, N_ASSIGN, N_IF, N_WHILE, N_FORR, N_FORIN,
    N_RET, N_BRK, N_CONT, N_EXPRST,
    N_INT, N_FLOAT, N_BOOL, N_STRLIT, N_STRTXT, N_INTERP,
    N_ID, N_LIST, N_SLIT, N_FIELDINIT,
    N_NEG, N_NOT, N_BIN, N_CAST, N_INDEX, N_MEMBER, N_CALL,
    N_TYNAME, N_TYLIST,
    N_INLINE, N_IRET,       // produced by the inliner, never by the parser
};

typedef struct Type Type;
typedef struct Node Node;

struct Node {
    int k, line, op;        // op: binop token / third slot for forin
    char* name;
    long long ival;
    double fval;
    Node *a, *b, *c;        // generic children (cond/then, obj/idx, lo/hi...)
    Vec kids;               // stmt lists, args, fields, parts, params
    Type* ty;               // set by checker
    int slot;               // local slot / param idx / field idx / td idx
    int aux;                // id kind / call kind / cast kind / binop category / extra slot
    void* ref;              // FDef* / SDef*
    int mut;                // decl mutability
};

static Node* node(int k, int line) {
    Node* n = xmalloc(sizeof(Node));
    n->k = k; n->line = line;
    return n;
}

// ---------------- parser ----------------
typedef struct {
    Tok* toks; int len, p;
    int no_struct;          // >0: '{' after identifier starts a block, not a struct literal
} Parser;

static Node* p_expr(Parser* ps, int minbp);
static Node* p_stmt(Parser* ps);
static Node* p_type(Parser* ps);
static Vec p_block(Parser* ps);

static Tok* peek(Parser* ps) { return &ps->toks[ps->p]; }
static Tok* pnext(Parser* ps) { return &ps->toks[ps->p < ps->len - 1 ? ps->p++ : ps->p]; }
static int at(Parser* ps, int t) { return peek(ps)->t == t; }
static Tok* expect(Parser* ps, int t, const char* what) {
    Tok* x = peek(ps);
    if (x->t != t)
        die(x->line, "expected %s, got '%s'", what ? what : tokname(t),
            x->t == T_ID ? x->s : tokname(x->t));
    return pnext(ps);
}
static void skip_nl(Parser* ps) { while (at(ps, T_NL)) pnext(ps); }
static void terminator(Parser* ps) {
    if (at(ps, T_EOF) || at(ps, T_RB)) return;
    if (at(ps, T_NL)) { skip_nl(ps); return; }
    die(peek(ps)->line, "expected newline after statement, got '%s'",
        peek(ps)->t == T_ID ? peek(ps)->s : tokname(peek(ps)->t));
}
static int else_ahead(Parser* ps) {
    int k = ps->p;
    while (ps->toks[k].t == T_NL) k++;
    if (ps->toks[k].t == T_ELSE) { ps->p = k; return 1; }
    return 0;
}

static Node* p_type(Parser* ps) {
    Tok* t = peek(ps);
    if (t->t == T_LS) {
        pnext(ps);
        Node* n = node(N_TYLIST, t->line);
        n->a = p_type(ps);
        expect(ps, T_RS, "']'");
        return n;
    }
    Tok* id = expect(ps, T_ID, "a type");
    Node* n = node(N_TYNAME, id->line);
    n->name = id->s;
    return n;
}

static Node* p_fn(Parser* ps) {
    Tok* start = pnext(ps); // fn
    Node* n = node(N_FN, start->line);
    n->name = expect(ps, T_ID, "function name")->s;
    expect(ps, T_LP, "'('");
    if (!at(ps, T_RP)) {
        for (;;) {
            Tok* pn = expect(ps, T_ID, "parameter name");
            expect(ps, T_COLON, "':'");
            Node* p = node(N_PARAM, pn->line);
            p->name = pn->s;
            p->a = p_type(ps);
            vpush(&n->kids, p);
            if (at(ps, T_COMMA)) { pnext(ps); continue; }
            break;
        }
    }
    expect(ps, T_RP, "')'");
    if (at(ps, T_ARROW)) { pnext(ps); n->a = p_type(ps); }
    Vec body = p_block(ps);
    n->b = node(N_PROG, start->line); // body holder
    n->b->kids = body;
    return n;
}

static Node* p_structdef(Parser* ps) {
    Tok* start = pnext(ps); // struct
    Node* n = node(N_STRUCTDEF, start->line);
    n->name = expect(ps, T_ID, "struct name")->s;
    expect(ps, T_LB, "'{'");
    skip_nl(ps);
    while (!at(ps, T_RB)) {
        Tok* fn = expect(ps, T_ID, "field name");
        expect(ps, T_COLON, "':'");
        Node* f = node(N_FIELDDEF, fn->line);
        f->name = fn->s;
        f->a = p_type(ps);
        vpush(&n->kids, f);
        if (at(ps, T_COMMA)) pnext(ps);
        skip_nl(ps);
    }
    expect(ps, T_RB, "'}'");
    return n;
}

static Vec p_block(Parser* ps) {
    expect(ps, T_LB, "'{'");
    skip_nl(ps);
    Vec stmts = {0};
    while (!at(ps, T_RB)) {
        if (at(ps, T_EOF)) die(peek(ps)->line, "expected '}'");
        vpush(&stmts, p_stmt(ps));
        if (!at(ps, T_RB)) terminator(ps);
    }
    expect(ps, T_RB, "'}'");
    return stmts;
}

static Node* p_header_expr(Parser* ps) {
    ps->no_struct++;
    Node* e = p_expr(ps, 1);
    ps->no_struct--;
    return e;
}

static Node* p_if(Parser* ps) {
    Tok* t = pnext(ps); // if
    Node* n = node(N_IF, t->line);
    n->a = p_header_expr(ps);
    n->b = node(N_PROG, t->line);
    n->b->kids = p_block(ps);
    if (else_ahead(ps)) {
        pnext(ps); // else
        n->c = node(N_PROG, t->line);
        if (at(ps, T_IF)) vpush(&n->c->kids, p_if(ps));
        else n->c->kids = p_block(ps);
    }
    return n;
}

static Node* p_stmt(Parser* ps) {
    Tok* t = peek(ps);
    switch (t->t) {
    case T_LET: case T_VAR: {
        pnext(ps);
        Node* n = node(N_DECL, t->line);
        n->mut = t->t == T_VAR;
        n->name = expect(ps, T_ID, "variable name")->s;
        if (at(ps, T_COLON)) { pnext(ps); n->b = p_type(ps); }
        expect(ps, T_ASSIGN, "'='");
        n->a = p_expr(ps, 1);
        return n;
    }
    case T_IF: return p_if(ps);
    case T_WHILE: {
        pnext(ps);
        Node* n = node(N_WHILE, t->line);
        n->a = p_header_expr(ps);
        n->b = node(N_PROG, t->line);
        n->b->kids = p_block(ps);
        return n;
    }
    case T_FOR: {
        pnext(ps);
        Node* n;
        char* name = expect(ps, T_ID, "loop variable")->s;
        expect(ps, T_IN, "'in'");
        Node* first = p_header_expr(ps);
        if (at(ps, T_DOTDOT)) {
            pnext(ps);
            n = node(N_FORR, t->line);
            n->a = first;
            n->b = p_header_expr(ps);
        } else {
            n = node(N_FORIN, t->line);
            n->a = first;
        }
        n->name = name;
        n->c = node(N_PROG, t->line);
        n->c->kids = p_block(ps);
        return n;
    }
    case T_RETURN: {
        pnext(ps);
        Node* n = node(N_RET, t->line);
        if (!at(ps, T_NL) && !at(ps, T_RB) && !at(ps, T_EOF)) n->a = p_expr(ps, 1);
        return n;
    }
    case T_BREAK: pnext(ps); return node(N_BRK, t->line);
    case T_CONTINUE: pnext(ps); return node(N_CONT, t->line);
    case T_FN: case T_STRUCT:
        die(t->line, "'%s' declarations are only allowed at the top level", tokname(t->t));
    }
    Node* e = p_expr(ps, 1);
    Tok* nx = peek(ps);
    int desugar =
        nx->t == T_PLUSEQ ? T_PLUS : nx->t == T_MINUSEQ ? T_MINUS :
        nx->t == T_STAREQ ? T_STAR : nx->t == T_SLASHEQ ? T_SLASH : 0;
    if (nx->t == T_ASSIGN || desugar) {
        pnext(ps);
        if (e->k != N_ID && e->k != N_MEMBER && e->k != N_INDEX)
            die(nx->line, "invalid assignment target");
        Node* n = node(N_ASSIGN, nx->line);
        n->a = e;
        Node* rhs = p_expr(ps, 1);
        if (desugar) {
            Node* bin = node(N_BIN, nx->line);
            bin->op = desugar; bin->a = e; bin->b = rhs;
            rhs = bin;
        }
        n->b = rhs;
        return n;
    }
    Node* n = node(N_EXPRST, e->line);
    n->a = e;
    return n;
}

static int binprec(int t) {
    switch (t) {
    case T_OR: return 1;
    case T_AND: return 2;
    case T_EQEQ: case T_NE: return 3;
    case T_LT: case T_LE: case T_GT: case T_GE: return 4;
    case T_PLUS: case T_MINUS: case T_PIPE: case T_CARET: return 5; // Go-style
    case T_STAR: case T_SLASH: case T_PCT: case T_AMP: case T_SHL: case T_SHR: return 6;
    case T_AS: return 7;
    default: return 0;
    }
}

static Node* p_unary(Parser* ps);

static Node* p_expr(Parser* ps, int minbp) {
    Node* lhs = p_unary(ps);
    for (;;) {
        Tok* t = peek(ps);
        int bp = binprec(t->t);
        if (!bp || bp < minbp) break;
        pnext(ps);
        if (t->t == T_AS) {
            Node* n = node(N_CAST, t->line);
            n->a = lhs;
            n->b = p_type(ps);
            lhs = n;
            continue;
        }
        Node* n = node(N_BIN, t->line);
        n->op = t->t;
        n->a = lhs;
        n->b = p_expr(ps, bp + 1);
        lhs = n;
    }
    return lhs;
}

static Node* p_primary(Parser* ps);

static Node* p_postfix(Parser* ps) {
    Node* e = p_primary(ps);
    for (;;) {
        if (at(ps, T_LP)) {
            Tok* t = pnext(ps);
            Node* n = node(N_CALL, t->line);
            n->a = e;
            int save = ps->no_struct; ps->no_struct = 0;
            if (!at(ps, T_RP)) for (;;) {
                vpush(&n->kids, p_expr(ps, 1));
                if (at(ps, T_COMMA)) { pnext(ps); continue; }
                break;
            }
            ps->no_struct = save;
            expect(ps, T_RP, "')'");
            e = n;
        } else if (at(ps, T_LS)) {
            Tok* t = pnext(ps);
            Node* n = node(N_INDEX, t->line);
            n->a = e;
            int save = ps->no_struct; ps->no_struct = 0;
            n->b = p_expr(ps, 1);
            ps->no_struct = save;
            expect(ps, T_RS, "']'");
            e = n;
        } else if (at(ps, T_DOT)) {
            pnext(ps);
            Tok* name = expect(ps, T_ID, "member name");
            Node* n = node(N_MEMBER, name->line);
            n->a = e;
            n->name = name->s;
            e = n;
        } else break;
    }
    return e;
}

static Node* p_unary(Parser* ps) {
    Tok* t = peek(ps);
    if (t->t == T_MINUS) { pnext(ps); Node* n = node(N_NEG, t->line); n->a = p_unary(ps); return n; }
    if (t->t == T_NOT) { pnext(ps); Node* n = node(N_NOT, t->line); n->a = p_unary(ps); return n; }
    return p_postfix(ps);
}

static Node* p_slit(Parser* ps, Tok* nameTok) {
    expect(ps, T_LB, "'{'");
    skip_nl(ps);
    Node* n = node(N_SLIT, nameTok->line);
    n->name = nameTok->s;
    while (!at(ps, T_RB)) {
        Tok* fn = expect(ps, T_ID, "field name");
        expect(ps, T_COLON, "':'");
        Node* f = node(N_FIELDINIT, fn->line);
        f->name = fn->s;
        int save = ps->no_struct; ps->no_struct = 0;
        f->a = p_expr(ps, 1);
        ps->no_struct = save;
        vpush(&n->kids, f);
        if (at(ps, T_COMMA)) pnext(ps);
        skip_nl(ps);
    }
    expect(ps, T_RB, "'}'");
    return n;
}

static Node* p_primary(Parser* ps) {
    Tok* t = peek(ps);
    switch (t->t) {
    case T_INT: { pnext(ps); Node* n = node(N_INT, t->line); n->ival = t->i; return n; }
    case T_FLOAT: { pnext(ps); Node* n = node(N_FLOAT, t->line); n->fval = t->f; return n; }
    case T_TRUE: case T_FALSE: {
        pnext(ps);
        Node* n = node(N_BOOL, t->line);
        n->ival = t->t == T_TRUE;
        return n;
    }
    case T_STR: {
        pnext(ps);
        Node* n = node(N_STRLIT, t->line);
        for (int i = 0; i < t->parts->len; i++) {
            StrPart* p = t->parts->items[i];
            if (!p->is_expr) {
                Node* s = node(N_STRTXT, t->line);
                s->name = p->text;
                vpush(&n->kids, s);
            } else {
                int sublen;
                Parser sub = { .toks = lex(p->text, p->line, &sublen), .len = 0 };
                sub.len = sublen;
                skip_nl(&sub);
                Node* wrap = node(N_INTERP, p->line);
                wrap->a = p_expr(&sub, 1);
                skip_nl(&sub);
                if (!at(&sub, T_EOF)) die(p->line, "unexpected token in string interpolation");
                vpush(&n->kids, wrap);
            }
        }
        return n;
    }
    case T_ID: {
        pnext(ps);
        if (at(ps, T_LB) && ps->no_struct == 0) return p_slit(ps, t);
        Node* n = node(N_ID, t->line);
        n->name = t->s;
        return n;
    }
    case T_LP: {
        pnext(ps);
        int save = ps->no_struct; ps->no_struct = 0;
        Node* e = p_expr(ps, 1);
        ps->no_struct = save;
        expect(ps, T_RP, "')'");
        return e;
    }
    case T_LS: {
        pnext(ps);
        Node* n = node(N_LIST, t->line);
        int save = ps->no_struct; ps->no_struct = 0;
        if (!at(ps, T_RS)) for (;;) {
            vpush(&n->kids, p_expr(ps, 1));
            if (at(ps, T_COMMA)) { pnext(ps); continue; }
            break;
        }
        ps->no_struct = save;
        expect(ps, T_RS, "']'");
        return n;
    }
    }
    die(t->line, "expected an expression, got '%s'", t->t == T_ID ? t->s : tokname(t->t));
    return NULL;
}

static Node* parse(Tok* toks, int len) {
    Parser ps = { .toks = toks, .len = len };
    Node* prog = node(N_PROG, 1);
    skip_nl(&ps);
    while (!at(&ps, T_EOF)) {
        Node* n;
        if (at(&ps, T_FN)) n = p_fn(&ps);
        else if (at(&ps, T_STRUCT)) n = p_structdef(&ps);
        else n = p_stmt(&ps);
        vpush(&prog->kids, n);
        terminator(&ps);
    }
    return prog;
}

// ---------------- types & checker ----------------
enum { K_INT, K_FLOAT, K_BOOL, K_STR, K_VOID, K_LIST, K_STRUCT };

typedef struct SDef { char* name; Vec fnames; Vec ftypes; int line; } SDef;
typedef struct FDef {
    char* name; Vec pnames; Vec ptypes; Type* ret;
    Node* body; int nslots; int line;
    struct Node* pristine;      // untouched copy of body, for the inliner
    int pristine_nslots;
    int regcall;                // <=4 params: args in rcx/rdx/r8/r9
} FDef;

struct Type { int k; Type* el; SDef* sd; };

static Type TY_INT = { K_INT }, TY_FLOAT = { K_FLOAT }, TY_BOOL = { K_BOOL },
            TY_STR = { K_STR }, TY_VOID = { K_VOID };

static Type* list_of(Type* el) {
    Type* t = xmalloc(sizeof(Type));
    t->k = K_LIST; t->el = el;
    return t;
}
static Type* struct_of(SDef* sd) {
    Type* t = xmalloc(sizeof(Type));
    t->k = K_STRUCT; t->sd = sd;
    return t;
}

static int type_eq(Type* a, Type* b) {
    if (a->k != b->k) return 0;
    if (a->k == K_LIST) return type_eq(a->el, b->el);
    if (a->k == K_STRUCT) return a->sd == b->sd;
    return 1;
}
static char* type_str(Type* t) {
    if (t->k == K_LIST) {
        char* e = type_str(t->el);
        char* s = xmalloc(strlen(e) + 3);
        sprintf(s, "[%s]", e);
        return s;
    }
    if (t->k == K_STRUCT) return t->sd->name;
    static char* names[] = { "int", "float", "bool", "str", "void" };
    return names[t->k];
}
static int is_num(Type* t) { return t->k == K_INT || t->k == K_FLOAT; }
static int fits(Type* want, Type* got) {
    return type_eq(want, got) || (want->k == K_FLOAT && got->k == K_INT);
}

// call kinds
enum { CK_USER, CK_PRINT, CK_PANIC, CK_SQRT, CK_LEN, CK_PUSH, CK_POP,
       CK_ARGS, CK_READF, CK_WRITEF, CK_CHR, CK_BYTE, CK_SUB, CK_JOIN, CK_BITS,
       CK_EMIT,
       CK_LOAD64, CK_LOAD8, CK_STORE64, CK_STORE32, CK_STORE8, CK_STACKPTR, CK_WIN,
       CK_ZEROS };
// cast kinds
enum { C_NONE, C_TRUNC, C_I2F, C_TOSTR, C_S2I, C_S2F };
// binop operand categories
enum { BC_INT, BC_FLOAT, BC_STR, BC_BOOL };
// identifier kinds
enum { ID_LOCAL, ID_PARAM, ID_GLOBAL };

static Vec g_structs, g_fns;
static Vec g_descs;             // Type* interning table for runtime type descriptors

static SDef* find_struct(const char* name) {
    for (int i = 0; i < g_structs.len; i++) {
        SDef* s = g_structs.items[i];
        if (strcmp(s->name, name) == 0) return s;
    }
    return NULL;
}
static FDef* find_fn(const char* name) {
    for (int i = 0; i < g_fns.len; i++) {
        FDef* f = g_fns.items[i];
        if (strcmp(f->name, name) == 0) return f;
    }
    return NULL;
}
static int is_builtin_name(const char* n) {
    static const char* names[] = { "print", "panic", "sqrt", "len", "push", "pop",
                                   "args", "read_file", "write_file", "chr",
                                   "byte", "sub", "join", "bits", "emit",
                                   "load64", "load8", "store64", "store32", "store8",
                                   "stackptr", "win", "addr", "zeros", "frombits" };
    for (size_t i = 0; i < sizeof names / sizeof names[0]; i++)
        if (strcmp(n, names[i]) == 0) return 1;
    return 0;
}

static int td_index(Type* t) {
    for (int i = 0; i < g_descs.len; i++)
        if (type_eq(g_descs.items[i], t)) return i;
    vpush(&g_descs, t);
    return g_descs.len - 1;
}

static Type* resolve_type(Node* te) {
    if (te->k == N_TYLIST) return list_of(resolve_type(te->a));
    const char* n = te->name;
    if (strcmp(n, "int") == 0) return &TY_INT;
    if (strcmp(n, "float") == 0) return &TY_FLOAT;
    if (strcmp(n, "bool") == 0) return &TY_BOOL;
    if (strcmp(n, "str") == 0) return &TY_STR;
    if (strcmp(n, "void") == 0) die(te->line, "'void' is not a usable type");
    SDef* sd = find_struct(n);
    if (!sd) die(te->line, "unknown type '%s'", n);
    return struct_of(sd);
}

typedef struct { char* name; Type* ty; int mut; int kind; int idx; } VarInfo;
typedef struct Scope { Vec vars; struct Scope* parent; } Scope;

typedef struct {
    FDef* fn;               // top level uses a synthetic FDef
    int is_top;
    int in_loop;
    int at_global;          // direct top-level statement: decls become globals
    int* nslots;
    int nparams;
} Ctx;

static int g_nglobals;
static int g_rt_top;   // top-level statements contributed by runtime.zeph (--rt)

static VarInfo* env_find(Scope* s, const char* name) {
    for (; s; s = s->parent)
        for (int i = 0; i < s->vars.len; i++) {
            VarInfo* v = s->vars.items[i];
            if (strcmp(v->name, name) == 0) return v;
        }
    return NULL;
}
static VarInfo* env_add(Scope* s, char* name, Type* ty, int mut, int kind, int idx) {
    VarInfo* v = xmalloc(sizeof(VarInfo));
    v->name = name; v->ty = ty; v->mut = mut; v->kind = kind; v->idx = idx;
    vpush(&s->vars, v);
    return v;
}

static Type* ce(Node* e, Scope* env, Ctx* ctx);

static Node* coerce(Node* e, Type* want, const char* what) {
    if (type_eq(want, e->ty)) return e;
    if (want->k == K_FLOAT && e->ty->k == K_INT) {
        Node* c = node(N_CAST, e->line);
        c->a = e; c->aux = C_I2F; c->ty = &TY_FLOAT;
        return c;
    }
    die(e->line, "%s: expected %s, got %s", what, type_str(want), type_str(e->ty));
    return e;
}

static void check_stmts(Vec* stmts, Scope* parent, Ctx* ctx);

static Type* check_bin(Node* e, Scope* env, Ctx* ctx) {
    int op = e->op;
    ce(e->a, env, ctx);
    ce(e->b, env, ctx);
    Type *lt = e->a->ty, *rt = e->b->ty;
    if (op == T_AND || op == T_OR) {
        if (lt->k != K_BOOL || rt->k != K_BOOL)
            die(e->line, "'%s' needs bool operands, got %s and %s", tokname(op), type_str(lt), type_str(rt));
        return &TY_BOOL;
    }
    if (op == T_EQEQ || op == T_NE) {
        if (is_num(lt) && is_num(rt)) {
            if (lt->k == K_FLOAT || rt->k == K_FLOAT) {
                e->a = coerce(e->a, &TY_FLOAT, "comparison");
                e->b = coerce(e->b, &TY_FLOAT, "comparison");
                e->aux = BC_FLOAT;
            } else e->aux = BC_INT;
        } else if (type_eq(lt, rt) && lt->k == K_BOOL) e->aux = BC_BOOL;
        else if (type_eq(lt, rt) && lt->k == K_STR) e->aux = BC_STR;
        else die(e->line, "'%s' is not defined for %s and %s%s", tokname(op), type_str(lt), type_str(rt),
                 lt->k == K_STRUCT || lt->k == K_LIST ? " (compare fields/elements explicitly)" : "");
        return &TY_BOOL;
    }
    if (op == T_LT || op == T_LE || op == T_GT || op == T_GE) {
        if (is_num(lt) && is_num(rt)) {
            if (lt->k == K_FLOAT || rt->k == K_FLOAT) {
                e->a = coerce(e->a, &TY_FLOAT, "comparison");
                e->b = coerce(e->b, &TY_FLOAT, "comparison");
                e->aux = BC_FLOAT;
            } else e->aux = BC_INT;
        } else if (lt->k == K_STR && rt->k == K_STR) e->aux = BC_STR;
        else die(e->line, "'%s' needs two numbers or two strings, got %s and %s",
                 tokname(op), type_str(lt), type_str(rt));
        return &TY_BOOL;
    }
    if (op == T_AMP || op == T_PIPE || op == T_CARET || op == T_SHL || op == T_SHR) {
        if (lt->k != K_INT || rt->k != K_INT)
            die(e->line, "'%s' needs int operands, got %s and %s", tokname(op), type_str(lt), type_str(rt));
        e->aux = BC_INT;
        return &TY_INT;
    }
    if (op == T_PLUS && lt->k == K_STR && rt->k == K_STR) { e->aux = BC_STR; return &TY_STR; }
    if (!is_num(lt) || !is_num(rt))
        die(e->line, "'%s' needs numeric operands, got %s and %s%s", tokname(op), type_str(lt), type_str(rt),
            op == T_PLUS && (lt->k == K_STR || rt->k == K_STR)
                ? " (convert with 'as str' or use string interpolation)" : "");
    if (lt->k == K_FLOAT || rt->k == K_FLOAT) {
        e->a = coerce(e->a, &TY_FLOAT, "arithmetic");
        e->b = coerce(e->b, &TY_FLOAT, "arithmetic");
        e->aux = BC_FLOAT;
        return &TY_FLOAT;
    }
    e->aux = BC_INT;
    return &TY_INT;
}

static Type* check_call(Node* e, Scope* env, Ctx* ctx) {
    Node* c = e->a;
    if (c->k == N_MEMBER) {
        Type* ot = ce(c->a, env, ctx);
        if (ot->k == K_STRUCT) {
            SDef* sd = ot->sd;
            for (int i = 0; i < sd->fnames.len; i++)
                if (strcmp(sd->fnames.items[i], c->name) == 0)
                    die(e->line, "'%s' is a field, not a method", c->name);
        }
        if (strcmp(c->name, "len") == 0) {
            if (ot->k != K_LIST && ot->k != K_STR)
                die(e->line, ".len() needs a list or str, got %s", type_str(ot));
            if (e->kids.len != 0) die(e->line, ".len() takes no arguments");
            e->aux = CK_LEN;
            return &TY_INT;
        }
        if (strcmp(c->name, "push") == 0) {
            if (ot->k != K_LIST) die(e->line, ".push() needs a list, got %s", type_str(ot));
            if (e->kids.len != 1) die(e->line, ".push(value) takes exactly one argument");
            ce(e->kids.items[0], env, ctx);
            e->kids.items[0] = coerce(e->kids.items[0], ot->el, "push");
            e->aux = CK_PUSH;
            return &TY_VOID;
        }
        if (strcmp(c->name, "pop") == 0) {
            if (ot->k != K_LIST) die(e->line, ".pop() needs a list, got %s", type_str(ot));
            if (e->kids.len != 0) die(e->line, ".pop() takes no arguments");
            e->aux = CK_POP;
            return ot->el;
        }
        if (strcmp(c->name, "byte") == 0) {
            if (ot->k != K_STR) die(e->line, ".byte(i) needs a str, got %s", type_str(ot));
            if (e->kids.len != 1) die(e->line, ".byte(i) takes exactly one int argument");
            if (ce(e->kids.items[0], env, ctx)->k != K_INT)
                die(e->line, ".byte(i) index must be int");
            e->aux = CK_BYTE;
            return &TY_INT;
        }
        if (strcmp(c->name, "sub") == 0) {
            if (ot->k != K_STR) die(e->line, ".sub(lo, hi) needs a str, got %s", type_str(ot));
            if (e->kids.len != 2) die(e->line, ".sub(lo, hi) takes exactly two int arguments");
            if (ce(e->kids.items[0], env, ctx)->k != K_INT ||
                ce(e->kids.items[1], env, ctx)->k != K_INT)
                die(e->line, ".sub(lo, hi) bounds must be int");
            e->aux = CK_SUB;
            return &TY_STR;
        }
        if (strcmp(c->name, "join") == 0) {
            if (ot->k != K_LIST || ot->el->k != K_STR)
                die(e->line, ".join() needs a [str], got %s", type_str(ot));
            if (e->kids.len != 0) die(e->line, ".join() takes no arguments");
            e->aux = CK_JOIN;
            return &TY_STR;
        }
        FDef* f = find_fn(c->name);
        if (!f) die(e->line, "unknown method or function '%s'", c->name);
        // UFCS: obj.f(a, b) == f(obj, a, b)
        if (e->kids.len + 1 != f->ptypes.len)
            die(e->line, "'%s' expects %d argument(s), got %d", f->name, f->ptypes.len, e->kids.len + 1);
        c->a = coerce(c->a, f->ptypes.items[0], "argument 1");
        for (int i = 0; i < e->kids.len; i++) {
            ce(e->kids.items[i], env, ctx);
            char what[32];
            snprintf(what, sizeof what, "argument %d", i + 2);
            e->kids.items[i] = coerce(e->kids.items[i], f->ptypes.items[i + 1], what);
        }
        e->aux = CK_USER;
        e->ref = f;
        e->op = 1; // marker: method-style, obj is extra first arg
        return f->ret;
    }
    if (c->k != N_ID) die(e->line, "only named functions can be called");
    if (strcmp(c->name, "print") == 0) {
        if (e->kids.len != 1) die(e->line, "print(value) takes exactly one argument");
        Type* t = ce(e->kids.items[0], env, ctx);
        if (t->k == K_VOID) die(e->line, "cannot print a void expression");
        e->aux = CK_PRINT;
        e->slot = td_index(t);
        return &TY_VOID;
    }
    if (strcmp(c->name, "panic") == 0) {
        if (e->kids.len != 1) die(e->line, "panic(message) takes exactly one str argument");
        Type* t = ce(e->kids.items[0], env, ctx);
        if (t->k != K_STR) die(e->line, "panic message must be str, got %s", type_str(t));
        e->aux = CK_PANIC;
        return &TY_VOID;
    }
    if (strcmp(c->name, "sqrt") == 0) {
        if (e->kids.len != 1) die(e->line, "sqrt(x) takes exactly one argument");
        Type* t = ce(e->kids.items[0], env, ctx);
        if (!is_num(t)) die(e->line, "sqrt needs a number, got %s", type_str(t));
        e->kids.items[0] = coerce(e->kids.items[0], &TY_FLOAT, "sqrt");
        e->aux = CK_SQRT;
        return &TY_FLOAT;
    }
    if (strcmp(c->name, "zeros") == 0) {
        if (e->kids.len != 1) die(e->line, "zeros(n) takes exactly one int argument");
        if (ce(e->kids.items[0], env, ctx)->k != K_INT) die(e->line, "zeros size must be int");
        e->aux = CK_ZEROS;
        return list_of(&TY_INT);
    }
    if (strcmp(c->name, "args") == 0) {
        if (e->kids.len != 0) die(e->line, "args() takes no arguments");
        e->aux = CK_ARGS;
        return list_of(&TY_STR);
    }
    if (strcmp(c->name, "read_file") == 0) {
        if (e->kids.len != 1) die(e->line, "read_file(path) takes exactly one str argument");
        if (ce(e->kids.items[0], env, ctx)->k != K_STR) die(e->line, "read_file path must be str");
        e->aux = CK_READF;
        return &TY_STR;
    }
    if (strcmp(c->name, "write_file") == 0) {
        if (e->kids.len != 2) die(e->line, "write_file(path, data) takes two str arguments");
        if (ce(e->kids.items[0], env, ctx)->k != K_STR ||
            ce(e->kids.items[1], env, ctx)->k != K_STR)
            die(e->line, "write_file arguments must be str");
        e->aux = CK_WRITEF;
        return &TY_VOID;
    }
    if (strcmp(c->name, "emit") == 0) {
        if (e->kids.len != 1) die(e->line, "emit(s) takes exactly one str argument");
        if (ce(e->kids.items[0], env, ctx)->k != K_STR) die(e->line, "emit argument must be str");
        e->aux = CK_EMIT;
        return &TY_VOID;
    }
    // ---- unsafe low-level intrinsics (for writing the runtime in Zephyr) ----
    { struct { const char* n; int k; int args; } LL[] = {
        {"load64", CK_LOAD64, 1}, {"load8", CK_LOAD8, 1}, {"store64", CK_STORE64, 2},
        {"store32", CK_STORE32, 2}, {"store8", CK_STORE8, 2}, {"stackptr", CK_STACKPTR, 0} };
      for (size_t i = 0; i < sizeof LL / sizeof LL[0]; i++) if (strcmp(c->name, LL[i].n) == 0) {
        if (e->kids.len != LL[i].args) die(e->line, "%s takes %d argument(s)", LL[i].n, LL[i].args);
        for (int j = 0; j < e->kids.len; j++)
            if (ce(e->kids.items[j], env, ctx)->k != K_INT) die(e->line, "%s arguments must be int", LL[i].n);
        e->aux = LL[i].k;
        return LL[i].k == CK_LOAD64 || LL[i].k == CK_LOAD8 || LL[i].k == CK_STACKPTR ? &TY_INT : &TY_VOID;
      }
    }
    // addr(ref): the raw pointer of a str/list/struct as an int (unsafe)
    if (strcmp(c->name, "addr") == 0) {
        if (e->kids.len != 1) die(e->line, "addr(x) takes exactly one argument");
        Type* t = ce(e->kids.items[0], env, ctx);
        if (t->k != K_STR && t->k != K_LIST && t->k != K_STRUCT)
            die(e->line, "addr() needs a str, list, or struct");
        e->aux = CK_BITS; // identity in codegen: the reference already is the pointer
        return &TY_INT;
    }
    // win(name, a, b, ...): Win64 call into kernel32; name is a string literal
    if (strcmp(c->name, "win") == 0) {
        if (e->kids.len < 1 || e->kids.len > 9)
            die(e->line, "win(name, args...) takes 1-9 arguments");
        Node* nm = e->kids.items[0];
        if (nm->k != N_STRLIT || nm->kids.len != 1 || ((Node*)nm->kids.items[0])->k != N_STRTXT)
            die(e->line, "win() first argument must be a plain string literal (the kernel32 function)");
        for (int j = 1; j < e->kids.len; j++)
            if (ce(e->kids.items[j], env, ctx)->k != K_INT) die(e->line, "win() call arguments must be int");
        e->aux = CK_WIN;
        return &TY_INT;
    }
    if (strcmp(c->name, "bits") == 0) {
        if (e->kids.len != 1) die(e->line, "bits(x) takes exactly one float argument");
        if (ce(e->kids.items[0], env, ctx)->k != K_FLOAT) die(e->line, "bits argument must be float");
        e->aux = CK_BITS;
        return &TY_INT;
    }
    if (strcmp(c->name, "frombits") == 0) {
        if (e->kids.len != 1) die(e->line, "frombits(x) takes exactly one int argument");
        if (ce(e->kids.items[0], env, ctx)->k != K_INT) die(e->line, "frombits argument must be int");
        e->aux = CK_BITS;   // identity: same bits, retyped as float
        return &TY_FLOAT;
    }
    if (strcmp(c->name, "chr") == 0) {
        if (e->kids.len != 1) die(e->line, "chr(code) takes exactly one int argument");
        if (ce(e->kids.items[0], env, ctx)->k != K_INT) die(e->line, "chr code must be int");
        e->aux = CK_CHR;
        return &TY_STR;
    }
    if (env_find(env, c->name)) die(e->line, "'%s' is a variable, not a function", c->name);
    FDef* f = find_fn(c->name);
    if (!f) die(e->line, "unknown function '%s'", c->name);
    if (e->kids.len != f->ptypes.len)
        die(e->line, "'%s' expects %d argument(s), got %d", f->name, f->ptypes.len, e->kids.len);
    for (int i = 0; i < e->kids.len; i++) {
        ce(e->kids.items[i], env, ctx);
        char what[32];
        snprintf(what, sizeof what, "argument %d", i + 1);
        e->kids.items[i] = coerce(e->kids.items[i], f->ptypes.items[i], what);
    }
    e->aux = CK_USER;
    e->ref = f;
    return f->ret;
}

static Type* ce_inner(Node* e, Scope* env, Ctx* ctx) {
    switch (e->k) {
    case N_INT: return &TY_INT;
    case N_FLOAT: return &TY_FLOAT;
    case N_BOOL: return &TY_BOOL;
    case N_STRLIT:
        for (int i = 0; i < e->kids.len; i++) {
            Node* p = e->kids.items[i];
            if (p->k == N_INTERP) {
                Type* t = ce(p->a, env, ctx);
                if (t->k == K_VOID) die(p->line, "cannot interpolate a void expression");
                p->slot = td_index(t);
            }
        }
        return &TY_STR;
    case N_ID: {
        VarInfo* v = env_find(env, e->name);
        if (!v) {
            if (find_fn(e->name) || is_builtin_name(e->name))
                die(e->line, "'%s' is a function — call it with (...)", e->name);
            die(e->line, "unknown variable '%s'", e->name);
        }
        e->aux = v->kind;
        e->slot = v->idx;
        return v->ty;
    }
    case N_LIST: {
        if (e->kids.len == 0)
            die(e->line, "cannot infer the type of an empty list literal; "
                         "annotate the variable, e.g. let xs: [int] = []");
        Type* el = ce(e->kids.items[0], env, ctx);
        for (int i = 1; i < e->kids.len; i++) {
            Type* t = ce(e->kids.items[i], env, ctx);
            if (fits(el, t)) continue;
            if (fits(t, el)) { el = t; continue; }
            die(e->line, "mixed element types in list: %s and %s", type_str(el), type_str(t));
        }
        for (int i = 0; i < e->kids.len; i++)
            e->kids.items[i] = coerce(e->kids.items[i], el, "list element");
        return list_of(el);
    }
    case N_SLIT: {
        SDef* sd = find_struct(e->name);
        if (!sd) die(e->line, "unknown struct '%s'", e->name);
        if (e->kids.len != sd->fnames.len)
            die(e->line, "struct '%s' has %d field(s), literal provides %d",
                sd->name, sd->fnames.len, e->kids.len);
        char seen[256] = {0};
        for (int i = 0; i < e->kids.len; i++) {
            Node* f = e->kids.items[i];
            int idx = -1;
            for (int j = 0; j < sd->fnames.len; j++)
                if (strcmp(sd->fnames.items[j], f->name) == 0) { idx = j; break; }
            if (idx < 0) die(f->line, "struct '%s' has no field '%s'", sd->name, f->name);
            if (seen[idx]) die(f->line, "duplicate field '%s'", f->name);
            seen[idx] = 1;
            f->slot = idx;
            ce(f->a, env, ctx);
            f->a = coerce(f->a, sd->ftypes.items[idx], "struct field");
        }
        e->ref = sd;
        return struct_of(sd);
    }
    case N_NEG: {
        Type* t = ce(e->a, env, ctx);
        if (!is_num(t)) die(e->line, "unary '-' needs a number, got %s", type_str(t));
        return t;
    }
    case N_NOT: {
        Type* t = ce(e->a, env, ctx);
        if (t->k != K_BOOL) die(e->line, "'not' needs a bool, got %s", type_str(t));
        return &TY_BOOL;
    }
    case N_BIN: return check_bin(e, env, ctx);
    case N_CAST: {
        Type* from = ce(e->a, env, ctx);
        Type* to = resolve_type(e->b);
        int f = from->k, t = to->k;
        int cast = -1;
        if (f == t && f != K_LIST && f != K_STRUCT) cast = C_NONE;
        else if (f == K_INT && t == K_FLOAT) cast = C_I2F;
        else if (f == K_FLOAT && t == K_INT) cast = C_TRUNC;
        else if ((f == K_INT || f == K_FLOAT || f == K_BOOL) && t == K_STR) cast = C_TOSTR;
        else if (f == K_STR && t == K_INT) cast = C_S2I;
        else if (f == K_STR && t == K_FLOAT) cast = C_S2F;
        if (cast < 0) die(e->line, "no conversion from %s to %s", type_str(from), type_str(to));
        e->aux = cast;
        if (cast == C_TOSTR) e->slot = td_index(from);
        return to;
    }
    case N_INDEX: {
        Type* ot = ce(e->a, env, ctx);
        if (ot->k != K_LIST) die(e->line, "cannot index into %s", type_str(ot));
        Type* it = ce(e->b, env, ctx);
        if (it->k != K_INT) die(e->line, "list index must be int, got %s", type_str(it));
        return ot->el;
    }
    case N_MEMBER: {
        Type* ot = ce(e->a, env, ctx);
        if (ot->k == K_STRUCT) {
            SDef* sd = ot->sd;
            for (int i = 0; i < sd->fnames.len; i++)
                if (strcmp(sd->fnames.items[i], e->name) == 0) {
                    e->slot = i;
                    return sd->ftypes.items[i];
                }
            die(e->line, "struct '%s' has no field '%s' (methods must be called: .%s(...))",
                sd->name, e->name, e->name);
        }
        die(e->line, "%s has no field '%s'", type_str(ot), e->name);
        return NULL;
    }
    case N_CALL: return check_call(e, env, ctx);
    }
    die(e->line, "internal: unknown expression kind %d", e->k);
    return NULL;
}

static Type* ce(Node* e, Scope* env, Ctx* ctx) {
    Type* t = ce_inner(e, env, ctx);
    e->ty = t;
    return t;
}

static void check_stmt(Node* s, Scope* env, Ctx* ctx) {
    switch (s->k) {
    case N_DECL: {
        for (int i = 0; i < env->vars.len; i++)
            if (strcmp(((VarInfo*)env->vars.items[i])->name, s->name) == 0)
                die(s->line, "'%s' is already declared in this scope", s->name);
        if (is_builtin_name(s->name)) die(s->line, "'%s' is a builtin name", s->name);
        if (find_fn(s->name)) die(s->line, "'%s' is already a function", s->name);
        Type* ty;
        if (s->a->k == N_LIST && s->a->kids.len == 0) {
            // empty list literal: type comes from the annotation
            if (!s->b) die(s->line, "cannot infer the type of an empty list; "
                                    "annotate it: let %s: [T] = []", s->name);
            ty = resolve_type(s->b);
            if (ty->k != K_LIST) die(s->line, "empty list literal needs a list type, got %s", type_str(ty));
            s->a->ty = ty;
        } else {
            Type* et = ce(s->a, env, ctx);
            if (et->k == K_VOID) die(s->line, "cannot assign a void expression");
            ty = et;
            if (s->b) {
                ty = resolve_type(s->b);
                s->a = coerce(s->a, ty, "initializer");
            }
        }
        s->ty = ty;
        if (ctx->at_global) {
            s->aux = ID_GLOBAL;
            s->slot = g_nglobals++;
        } else {
            s->aux = ID_LOCAL;
            s->slot = (*ctx->nslots)++;
        }
        env_add(env, s->name, ty, s->mut, s->aux, s->slot);
        return;
    }
    case N_ASSIGN: {
        Node* t = s->a;
        ce(s->b, env, ctx);
        if (t->k == N_ID) {
            VarInfo* v = env_find(env, t->name);
            if (!v) die(t->line, "unknown variable '%s'", t->name);
            if (!v->mut) die(t->line, "'%s' is immutable (declared with 'let'; use 'var' to allow reassignment)", t->name);
            t->aux = v->kind;
            t->slot = v->idx;
            t->ty = v->ty;
            s->b = coerce(s->b, v->ty, "assignment");
        } else if (t->k == N_MEMBER) {
            Type* ft = ce(t, env, ctx);
            s->b = coerce(s->b, ft, "assignment");
        } else { // index
            Type* et = ce(t, env, ctx);
            s->b = coerce(s->b, et, "assignment");
        }
        return;
    }
    case N_IF: {
        Type* ct = ce(s->a, env, ctx);
        if (ct->k != K_BOOL) die(s->line, "if condition must be bool, got %s", type_str(ct));
        check_stmts(&s->b->kids, env, ctx);
        if (s->c) check_stmts(&s->c->kids, env, ctx);
        return;
    }
    case N_WHILE: {
        Type* ct = ce(s->a, env, ctx);
        if (ct->k != K_BOOL) die(s->line, "while condition must be bool, got %s", type_str(ct));
        Ctx c2 = *ctx; c2.in_loop = 1;
        check_stmts(&s->b->kids, env, &c2);
        return;
    }
    case N_FORR: {
        Type *lo = ce(s->a, env, ctx), *hi = ce(s->b, env, ctx);
        if (lo->k != K_INT || hi->k != K_INT)
            die(s->line, "range bounds must be int, got %s..%s", type_str(lo), type_str(hi));
        s->slot = (*ctx->nslots)++; // loop var
        s->aux = (*ctx->nslots)++;  // limit
        Scope inner = { .parent = env };
        env_add(&inner, s->name, &TY_INT, 0, ID_LOCAL, s->slot);
        Ctx c2 = *ctx; c2.in_loop = 1;
        check_stmts(&s->c->kids, &inner, &c2);
        return;
    }
    case N_FORIN: {
        Type* lt = ce(s->a, env, ctx);
        if (lt->k != K_LIST) die(s->line, "for-in needs a list, got %s", type_str(lt));
        s->slot = (*ctx->nslots)++; // loop var
        s->aux = (*ctx->nslots)++;  // list ptr
        s->op = (*ctx->nslots)++;   // index
        Scope inner = { .parent = env };
        env_add(&inner, s->name, lt->el, 0, ID_LOCAL, s->slot);
        Ctx c2 = *ctx; c2.in_loop = 1;
        check_stmts(&s->c->kids, &inner, &c2);
        return;
    }
    case N_RET: {
        if (ctx->is_top) die(s->line, "'return' outside a function");
        Type* want = ctx->fn->ret;
        if (want->k == K_VOID) {
            if (s->a) die(s->line, "this function does not return a value");
            return;
        }
        if (!s->a) die(s->line, "expected a return value of type %s", type_str(want));
        ce(s->a, env, ctx);
        s->a = coerce(s->a, want, "return");
        return;
    }
    case N_BRK: case N_CONT:
        if (!ctx->in_loop) die(s->line, "'%s' outside a loop", s->k == N_BRK ? "break" : "continue");
        return;
    case N_EXPRST:
        ce(s->a, env, ctx);
        return;
    case N_FN: case N_STRUCTDEF:
        return;
    }
    die(s->line, "internal: unknown statement kind %d", s->k);
}

static void check_stmts(Vec* stmts, Scope* parent, Ctx* ctx) {
    Scope scope = { .parent = parent };
    Ctx c2 = *ctx;
    c2.at_global = 0; // decls in nested blocks are locals even at the top level
    for (int i = 0; i < stmts->len; i++) check_stmt(stmts->items[i], &scope, &c2);
}

static int always_returns(Vec* stmts) {
    for (int i = 0; i < stmts->len; i++) {
        Node* s = stmts->items[i];
        if (s->k == N_RET) return 1;
        if (s->k == N_IF && s->c && always_returns(&s->b->kids) && always_returns(&s->c->kids)) return 1;
    }
    return 0;
}

static FDef* g_top;             // synthetic FDef for top-level code

static void check(Node* prog) {
    // pass 1a: struct names (so fields can reference other structs in any order)
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_STRUCTDEF) continue;
        if (find_struct(n->name)) die(n->line, "duplicate struct '%s'", n->name);
        SDef* sd = xmalloc(sizeof(SDef));
        sd->name = n->name; sd->line = n->line;
        vpush(&g_structs, sd);
        n->ref = sd;
    }
    // pass 1b: struct fields
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_STRUCTDEF) continue;
        SDef* sd = n->ref;
        for (int j = 0; j < n->kids.len; j++) {
            Node* f = n->kids.items[j];
            for (int k = 0; k < sd->fnames.len; k++)
                if (strcmp(sd->fnames.items[k], f->name) == 0)
                    die(f->line, "duplicate field '%s' in struct '%s'", f->name, sd->name);
            vpush(&sd->fnames, f->name);
            vpush(&sd->ftypes, resolve_type(f->a));
        }
    }
    // pass 1c: function signatures
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_FN) continue;
        if (find_fn(n->name)) die(n->line, "duplicate function '%s'", n->name);
        if (is_builtin_name(n->name)) die(n->line, "'%s' is a builtin and cannot be redefined", n->name);
        FDef* f = xmalloc(sizeof(FDef));
        f->name = n->name; f->line = n->line;
        for (int j = 0; j < n->kids.len; j++) {
            Node* p = n->kids.items[j];
            for (int k = 0; k < f->pnames.len; k++)
                if (strcmp(f->pnames.items[k], p->name) == 0)
                    die(p->line, "duplicate parameter '%s'", p->name);
            vpush(&f->pnames, p->name);
            vpush(&f->ptypes, resolve_type(p->a));
        }
        f->ret = n->a ? resolve_type(n->a) : &TY_VOID;
        f->body = n->b;
        f->regcall = f->pnames.len <= 4;
        vpush(&g_fns, f);
        n->ref = f;
    }
    // pass 2: bodies and top-level statements, in source order.
    // Top-level declarations are globals, visible inside every function that
    // appears after them (declare globals before the functions that use them).
    g_top = xmalloc(sizeof(FDef));
    g_top->name = "zephyr_main";
    g_top->ret = &TY_VOID;
    Scope globals = {0};
    int top_nslots = 0;
    Ctx topctx = { .fn = g_top, .is_top = 1, .at_global = 1, .nslots = &top_nslots };
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k == N_STRUCTDEF) continue;
        if (n->k == N_FN) {
            FDef* f = n->ref;
            Scope params = { .parent = &globals };
            for (int j = 0; j < f->pnames.len; j++)
                env_add(&params, f->pnames.items[j], f->ptypes.items[j], 0, ID_PARAM, j);
            int nslots = 0;
            Ctx ctx = { .fn = f, .nslots = &nslots, .nparams = f->pnames.len };
            check_stmts(&f->body->kids, &params, &ctx);
            f->nslots = nslots;
            if (f->ret->k != K_VOID && !always_returns(&f->body->kids))
                die(f->line, "function '%s' must return %s on all paths", f->name, type_str(f->ret));
            continue;
        }
        check_stmt(n, &globals, &topctx);
    }
    g_top->nslots = top_nslots;
}

// ---------------- inliner ----------------
// Expands calls to small user functions in place. A call is hoisted out of an
// expression into `param decls + N_INLINE stmts + result temp` only along a
// pure evaluation prefix, so observable order of side effects is preserved.
#define INLINE_MAX_NODES 128
#define INLINE_MAX_DEPTH 4
#define MAX_SLOTS 4096

// ---- global demotion ----
// A global that no function references only exists for top-level code, so it
// can live in zephyr_main's frame instead (and become register-promotable).
static int g_gdemote[MAX_SLOTS];    // global idx -> new local slot, or -1

static void count_global_refs(Node* n, int* counts) {
    if (!n) return;
    if (n->k == N_ID && n->aux == ID_GLOBAL && n->slot < MAX_SLOTS) counts[n->slot]++;
    count_global_refs(n->a, counts); count_global_refs(n->b, counts);
    count_global_refs(n->c, counts);
    for (int i = 0; i < n->kids.len; i++) count_global_refs(n->kids.items[i], counts);
}

static void demote_rewrite(Node* n) {
    if (!n) return;
    if ((n->k == N_ID || n->k == N_DECL) && n->aux == ID_GLOBAL &&
        n->slot < MAX_SLOTS && g_gdemote[n->slot] >= 0) {
        n->aux = ID_LOCAL;
        n->slot = g_gdemote[n->slot];
    }
    demote_rewrite(n->a); demote_rewrite(n->b); demote_rewrite(n->c);
    for (int i = 0; i < n->kids.len; i++) demote_rewrite(n->kids.items[i]);
}

static void demote_globals(Node* prog) {
    if (g_nglobals == 0) return;
    static int fnrefs[MAX_SLOTS];
    memset(fnrefs, 0, sizeof(int) * (g_nglobals < MAX_SLOTS ? g_nglobals : MAX_SLOTS));
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k == N_FN) count_global_refs(((FDef*)n->ref)->body, fnrefs);
    }
    for (int g = 0; g < g_nglobals && g < MAX_SLOTS; g++)
        g_gdemote[g] = fnrefs[g] == 0 ? g_top->nslots++ : -1;
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_FN && n->k != N_STRUCTDEF) demote_rewrite(n);
    }
}

static int* g_inl_nslots;       // current function's slot counter
static Vec* g_hoisted;          // statements to insert before the current one

static int node_count(Node* n) {
    if (!n) return 0;
    int c = 1 + node_count(n->a) + node_count(n->b) + node_count(n->c);
    for (int i = 0; i < n->kids.len; i++) c += node_count(n->kids.items[i]);
    return c;
}

// no calls, no panics, no side effects anywhere in the tree
static int strict_pure(Node* e) {
    if (!e) return 1;
    switch (e->k) {
    case N_INT: case N_FLOAT: case N_BOOL: case N_ID: return 1;
    case N_NEG: case N_NOT: case N_MEMBER: return strict_pure(e->a);
    case N_CAST:
        return (e->aux == C_NONE || e->aux == C_I2F || e->aux == C_TRUNC) && strict_pure(e->a);
    case N_BIN:
        if (e->op == T_SLASH || e->op == T_PCT) return 0; // may panic
        return strict_pure(e->a) && strict_pure(e->b);
    default: return 0;
    }
}

typedef struct { int pbase, lbase, resultslot, depth; } InlMap;

static Node* clone_node(Node* n, InlMap* m) {
    if (!n) return NULL;
    Node* c = xmalloc(sizeof(Node));
    *c = *n;
    c->kids.items = NULL; c->kids.len = c->kids.cap = 0;
    for (int i = 0; i < n->kids.len; i++) vpush(&c->kids, clone_node(n->kids.items[i], m));
    c->a = clone_node(n->a, m);
    c->b = clone_node(n->b, m);
    c->c = clone_node(n->c, m);
    if (!m) return c; // plain structural copy (pristine capture)
    switch (c->k) {
    case N_ID:
        if (c->aux == ID_PARAM) { c->aux = ID_LOCAL; c->slot = m->pbase + c->slot; }
        else if (c->aux == ID_LOCAL) c->slot += m->lbase;
        break;
    case N_DECL: if (c->aux == ID_LOCAL) c->slot += m->lbase; break;
    case N_FORR: c->slot += m->lbase; c->aux += m->lbase; break;
    case N_FORIN: c->slot += m->lbase; c->aux += m->lbase; c->op += m->lbase; break;
    case N_RET: c->k = N_IRET; c->slot = m->resultslot; break;
    case N_IRET: case N_INLINE: c->slot += m->lbase; break;
    case N_CALL: if (c->aux == CK_USER) c->ival = m->depth; break;
    }
    return c;
}

static int inlinable_call(Node* e) {
    if (e->k != N_CALL || e->aux != CK_USER || e->ival >= INLINE_MAX_DEPTH) return 0;
    if (g_inl_nslots && *g_inl_nslots > 600) return 0;  // frame-size safety valve:
        // stop expanding into a function whose frame has already ballooned, so a
        // compiler-sized program full of mutually-recursive helpers can't blow up
    return ((FDef*)e->ref)->pristine != NULL;
}

static int try_expr(Node** ep);

// expand an inlinable call: hoist param decls + inlined body, return result temp
static Node* expand_call(Node* call) {
    FDef* f = call->ref;
    InlMap m;
    m.depth = call->ival + 1;
    m.pbase = *g_inl_nslots; *g_inl_nslots += f->pnames.len;
    m.lbase = *g_inl_nslots; *g_inl_nslots += f->pristine_nslots;
    m.resultslot = (*g_inl_nslots)++;
    int pi = 0;
    Node* args[64];
    int nargs = 0;
    if (call->op == 1) args[nargs++] = call->a->a; // UFCS receiver
    for (int i = 0; i < call->kids.len; i++) args[nargs++] = call->kids.items[i];
    for (int i = 0; i < nargs; i++) {
        try_expr(&args[i]); // inline inside the argument first
        Node* d = node(N_DECL, call->line);
        d->name = "(inlined arg)";
        d->aux = ID_LOCAL;
        d->slot = m.pbase + pi++;
        d->a = args[i];
        vpush(g_hoisted, d);
    }
    Node* inl = node(N_INLINE, call->line);
    inl->name = f->name;
    inl->slot = m.resultslot;
    for (int i = 0; i < f->pristine->kids.len; i++)
        vpush(&inl->kids, clone_node(f->pristine->kids.items[i], &m));
    vpush(g_hoisted, inl);
    Node* id = node(N_ID, call->line);
    id->aux = ID_LOCAL;
    id->slot = m.resultslot;
    id->ty = call->ty;
    return id;
}

// walk an expression left-to-right; expand inlinable calls reachable through a
// pure prefix; returns 1 if the (rewritten) expression is now strictly pure
static int try_expr(Node** ep) {
    Node* e = *ep;
    switch (e->k) {
    case N_INT: case N_FLOAT: case N_BOOL: case N_ID: return 1;
    case N_NEG: case N_NOT: return try_expr(&e->a);
    case N_MEMBER: return try_expr(&e->a);
    case N_CAST:
        return try_expr(&e->a) &&
               (e->aux == C_NONE || e->aux == C_I2F || e->aux == C_TRUNC);
    case N_BIN:
        if (e->op == T_AND || e->op == T_OR)
            return try_expr(&e->a) && strict_pure(e->b); // rhs is conditional: hands off
        if (!try_expr(&e->a)) return 0;
        if (!try_expr(&e->b)) return 0;
        return e->op != T_SLASH && e->op != T_PCT;
    case N_CALL:
        if (inlinable_call(e)) { *ep = expand_call(e); return 1; }
        return 0;
    default: return 0;
    }
}

static void hoist_block(Vec* stmts);

static void hoist_stmt(Node* s) {
    switch (s->k) {
    case N_DECL: try_expr(&s->a); return;
    case N_ASSIGN:
        // target parts are evaluated before the value; only touch the value
        // when the target cannot observe the reorder
        if (s->a->k == N_ID || (s->a->k == N_MEMBER && strict_pure(s->a->a)))
            try_expr(&s->b);
        return;
    case N_RET: case N_IRET: if (s->a) try_expr(&s->a); return;
    case N_EXPRST: try_expr(&s->a); return;
    case N_IF:
        try_expr(&s->a);
        hoist_block(&s->b->kids);
        if (s->c) hoist_block(&s->c->kids);
        return;
    case N_WHILE: // condition re-evaluates each iteration: cannot hoist it
        hoist_block(&s->b->kids);
        return;
    case N_FORR:
        if (try_expr(&s->a)) try_expr(&s->b);
        hoist_block(&s->c->kids);
        return;
    case N_FORIN:
        try_expr(&s->a);
        hoist_block(&s->c->kids);
        return;
    case N_INLINE:
        hoist_block(&s->kids);
        return;
    }
}

static void hoist_block(Vec* stmts) {
    Vec out = {0};
    Vec* save = g_hoisted;
    for (int i = 0; i < stmts->len; i++) {
        Node* s = stmts->items[i];
        g_hoisted = &out;
        if (s->k != N_FN && s->k != N_STRUCTDEF) hoist_stmt(s);
        vpush(&out, s);
    }
    g_hoisted = save;
    *stmts = out;
}

// ---------------- loop-invariant code motion + CSE ----------------
// Hoists non-faulting invariant arithmetic (e.g. i*N) out of loops into
// pre-loop temporaries, sharing one temp per distinct expression (CSE).
// Only pure, non-faulting expressions are hoisted (no index/div/call), so
// hoisting can never change fault behavior or observable order.
static int* g_licm_nslots;

typedef struct { int keys[256]; int n; } ModSet;
static void ms_add(ModSet* m, int kind, int slot) {
    int key = kind * 1000000 + slot;
    for (int i = 0; i < m->n; i++) if (m->keys[i] == key) return;
    if (m->n < 256) m->keys[m->n++] = key;
}
static int ms_has(ModSet* m, int kind, int slot) {
    int key = kind * 1000000 + slot;
    for (int i = 0; i < m->n; i++) if (m->keys[i] == key) return 1;
    return 0;
}

// scalar variables rebound in a statement tree (assign target ids, decls, loop vars)
static void collect_mods(Node* n, ModSet* m) {
    if (!n) return;
    switch (n->k) {
    case N_DECL: ms_add(m, n->aux, n->slot); break;
    case N_ASSIGN: if (n->a->k == N_ID) ms_add(m, n->a->aux, n->a->slot); break;
    case N_FORR: ms_add(m, ID_LOCAL, n->slot); ms_add(m, ID_LOCAL, n->aux); break;
    case N_FORIN: ms_add(m, ID_LOCAL, n->slot); ms_add(m, ID_LOCAL, n->aux); ms_add(m, ID_LOCAL, n->op); break;
    }
    collect_mods(n->a, m); collect_mods(n->b, m); collect_mods(n->c, m);
    for (int i = 0; i < n->kids.len; i++) collect_mods(n->kids.items[i], m);
}

static int expr_equal(Node* a, Node* b) {
    if (a->k != b->k) return 0;
    switch (a->k) {
    case N_INT: case N_BOOL: return a->ival == b->ival;
    case N_FLOAT: return a->fval == b->fval;
    case N_ID: return a->aux == b->aux && a->slot == b->slot;
    case N_BIN: return a->op == b->op && expr_equal(a->a, b->a) && expr_equal(a->b, b->b);
    case N_NEG: case N_NOT: return expr_equal(a->a, b->a);
    case N_CAST: return a->aux == b->aux && expr_equal(a->a, b->a);
    default: return 0;
    }
}

static int licm_invariant(Node* e, ModSet* m) {
    switch (e->k) {
    case N_INT: case N_FLOAT: case N_BOOL: return 1;
    case N_ID: return !ms_has(m, e->aux, e->slot);
    case N_BIN:
        if (e->op == T_SLASH || e->op == T_PCT) return 0;   // may fault
        if (e->op == T_AND || e->op == T_OR) return 0;      // short-circuits
        return licm_invariant(e->a, m) && licm_invariant(e->b, m);
    case N_NEG: case N_NOT: return licm_invariant(e->a, m);
    case N_CAST:
        return (e->aux == C_NONE || e->aux == C_I2F || e->aux == C_TRUNC) && licm_invariant(e->a, m);
    default: return 0;    // index/member/call/strlit: not hoisted (may fault/alloc)
    }
}
static int licm_worth(Node* e) { return e->k == N_BIN || e->k == N_NEG || e->k == N_CAST; }

typedef struct { Node* expr; int slot; Type* ty; } Hoisted;
static Hoisted g_hoist[512];
static int g_nhoist;

static Node* mk_licm_id(int slot, Type* ty) {
    Node* n = node(N_ID, 0);
    n->name = "(licm)"; n->aux = ID_LOCAL; n->slot = slot; n->ty = ty;
    return n;
}

static void hoist_walk(Node** ep, ModSet* m) {
    Node* e = *ep;
    if (!e) return;
    if (licm_worth(e) && licm_invariant(e, m)) {
        int slot = -1;
        for (int i = 0; i < g_nhoist; i++) if (expr_equal(g_hoist[i].expr, e)) { slot = g_hoist[i].slot; break; }
        if (slot < 0) {
            slot = (*g_licm_nslots)++;
            if (g_nhoist < 512) { g_hoist[g_nhoist].expr = e; g_hoist[g_nhoist].slot = slot; g_hoist[g_nhoist].ty = e->ty; g_nhoist++; }
        }
        *ep = mk_licm_id(slot, e->ty);
        return;
    }
    switch (e->k) {
    case N_BIN: hoist_walk(&e->a, m); hoist_walk(&e->b, m); break;
    case N_NEG: case N_NOT: case N_CAST: hoist_walk(&e->a, m); break;
    case N_INDEX: hoist_walk(&e->a, m); hoist_walk(&e->b, m); break;
    case N_MEMBER: hoist_walk(&e->a, m); break;
    case N_CALL:
        if (e->a && e->a->k == N_MEMBER) hoist_walk(&e->a->a, m);
        for (int i = 0; i < e->kids.len; i++) hoist_walk((Node**)&e->kids.items[i], m);
        break;
    case N_STRLIT:
        for (int i = 0; i < e->kids.len; i++) {
            Node* p = e->kids.items[i];
            if (p->k == N_INTERP) hoist_walk(&p->a, m);
        }
        break;
    case N_LIST: for (int i = 0; i < e->kids.len; i++) hoist_walk((Node**)&e->kids.items[i], m); break;
    case N_SLIT: for (int i = 0; i < e->kids.len; i++) { Node* f = e->kids.items[i]; hoist_walk(&f->a, m); } break;
    }
}

static void lc_stmt(Node* s, ModSet* m) {
    switch (s->k) {
    case N_DECL: hoist_walk(&s->a, m); break;
    case N_ASSIGN:
        if (s->a->k == N_INDEX) { hoist_walk(&s->a->a, m); hoist_walk(&s->a->b, m); }
        else if (s->a->k == N_MEMBER) hoist_walk(&s->a->a, m);
        hoist_walk(&s->b, m);
        break;
    case N_RET: case N_IRET: if (s->a) hoist_walk(&s->a, m); break;
    case N_EXPRST: hoist_walk(&s->a, m); break;
    case N_IF:
        hoist_walk(&s->a, m);
        for (int i = 0; i < s->b->kids.len; i++) lc_stmt(s->b->kids.items[i], m);
        if (s->c) for (int i = 0; i < s->c->kids.len; i++) lc_stmt(s->c->kids.items[i], m);
        break;
    case N_WHILE:   // hoist from the body but NOT the re-evaluated condition
        for (int i = 0; i < s->b->kids.len; i++) lc_stmt(s->b->kids.items[i], m);
        break;
    case N_FORR:
        hoist_walk(&s->a, m); hoist_walk(&s->b, m);
        for (int i = 0; i < s->c->kids.len; i++) lc_stmt(s->c->kids.items[i], m);
        break;
    case N_FORIN:
        hoist_walk(&s->a, m);
        for (int i = 0; i < s->c->kids.len; i++) lc_stmt(s->c->kids.items[i], m);
        break;
    case N_INLINE:
        for (int i = 0; i < s->kids.len; i++) lc_stmt(s->kids.items[i], m);
        break;
    }
}

static void licm_stmts(Vec* stmts);
static void licm_block(Node* blk) { if (blk) licm_stmts(&blk->kids); }

static void licm_stmts(Vec* stmts) {
    // inner loops first, so their hoisted temps can hoist further out
    for (int i = 0; i < stmts->len; i++) {
        Node* s = stmts->items[i];
        if (s->k == N_IF) { licm_block(s->b); if (s->c) licm_block(s->c); }
        else if (s->k == N_WHILE) licm_block(s->b);
        else if (s->k == N_FORR || s->k == N_FORIN) licm_block(s->c);
        else if (s->k == N_INLINE) licm_stmts(&s->kids);
    }
    Vec out = {0};
    for (int i = 0; i < stmts->len; i++) {
        Node* s = stmts->items[i];
        if (s->k == N_FORR || s->k == N_FORIN || s->k == N_WHILE) {
            Node* body = s->k == N_WHILE ? s->b : s->c;
            ModSet m = {0};
            if (s->k == N_FORR) { ms_add(&m, ID_LOCAL, s->slot); ms_add(&m, ID_LOCAL, s->aux); }
            else if (s->k == N_FORIN) { ms_add(&m, ID_LOCAL, s->slot); ms_add(&m, ID_LOCAL, s->aux); ms_add(&m, ID_LOCAL, s->op); }
            for (int j = 0; j < body->kids.len; j++) collect_mods(body->kids.items[j], &m);
            g_nhoist = 0;
            for (int j = 0; j < body->kids.len; j++) lc_stmt(body->kids.items[j], &m);
            for (int h = 0; h < g_nhoist; h++) {
                Node* d = node(N_DECL, s->line);
                d->name = "(licm)"; d->aux = ID_LOCAL; d->slot = g_hoist[h].slot;
                d->a = g_hoist[h].expr; d->ty = g_hoist[h].ty; d->mut = 0;
                vpush(&out, d);
            }
        }
        vpush(&out, s);
    }
    *stmts = out;
}

static void licm_pass(Node* prog) {
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_FN) continue;
        FDef* f = n->ref;
        g_licm_nslots = &f->nslots;
        licm_block(f->body);
    }
    g_licm_nslots = &g_top->nslots;
    Vec top = {0};
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_FN && n->k != N_STRUCTDEF) vpush(&top, n);
    }
    licm_stmts(&top);
    // write hoisted top-level decls back into prog order (fns/structs kept)
    Vec merged = {0};
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k == N_FN || n->k == N_STRUCTDEF) vpush(&merged, n);
    }
    for (int i = 0; i < top.len; i++) vpush(&merged, top.items[i]);
    prog->kids = merged;
}

static void inline_pass(Node* prog) {
    // capture pristine bodies before anything gets rewritten
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_FN) continue;
        FDef* f = n->ref;
        if (node_count(f->body) <= INLINE_MAX_NODES) {
            f->pristine = clone_node(f->body, NULL);
            f->pristine_nslots = f->nslots;
        }
    }
    for (int round = 0; round < INLINE_MAX_DEPTH; round++) {
        for (int i = 0; i < prog->kids.len; i++) {
            Node* n = prog->kids.items[i];
            if (n->k != N_FN) continue;
            FDef* f = n->ref;
            g_inl_nslots = &f->nslots;
            hoist_block(&f->body->kids);
        }
        g_inl_nslots = &g_top->nslots;
        hoist_block(&prog->kids);
    }
}

// ---------------- codegen ----------------
static FILE* g_out;
static int g_label;
static int g_brk[64], g_cont[64], g_loopdepth;
static int g_inlend[64], g_inldepth;
static FDef* g_curfn;

typedef struct { int id; char* data; int len; } DataStr;
static Vec g_dstrs;             // Zephyr string constants (len-prefixed)
static Vec g_dcstrs;            // C string constants (NUL-terminated, for descriptors)

static Vec g_alines;            // buffered .text lines, peepholed before writing

static void aline(const char* s) { vpush(&g_alines, xstrndup(s, strlen(s))); }

static void o(const char* fmt, ...) {
    char buf[512] = "  ";
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf + 2, sizeof buf - 3, fmt, ap);
    va_end(ap);
    aline(buf);
}
static void olabel(int l) {
    char buf[32];
    snprintf(buf, sizeof buf, ".L%d:", l);
    aline(buf);
}
static int newlabel(void) { return g_label++; }

static int add_dstr(const char* data, int len) {
    DataStr* d = xmalloc(sizeof(DataStr));
    d->id = g_dstrs.len;
    d->data = xstrndup(data, len);
    d->len = len;
    vpush(&g_dstrs, d);
    return d->id;
}
static int add_cstr(const char* s) {
    for (int i = 0; i < g_dcstrs.len; i++)
        if (strcmp(((DataStr*)g_dcstrs.items[i])->data, s) == 0) return i;
    DataStr* d = xmalloc(sizeof(DataStr));
    d->id = g_dcstrs.len;
    d->data = (char*)s;
    d->len = (int)strlen(s);
    vpush(&g_dcstrs, d);
    return d->id;
}

// call into the C runtime with proper Win64 alignment + shadow space
static void rcall(const char* fn) {
    o("mov r12, rsp");
    o("and rsp, -16");
    o("sub rsp, 32");
    o("call %s", fn);
    o("mov rsp, r12");
}

static void gen_expr(Node* e);
static void slot_addr(char* buf, int kind, int idx);

// runtime functions keep bare names (rt_alloc) so they satisfy the code
// generator's hardcoded runtime calls; everything else gets an lm_ prefix.
static const char* fn_label(const char* name) {
    static char buf[300];
    if (strncmp(name, "rt_", 3) == 0) { snprintf(buf, sizeof buf, "%s", name); return buf; }
    snprintf(buf, sizeof buf, "lm_%s", name);
    return buf;
}

// ---- optimization helpers ----
// leaf = an expression that can be loaded into any register with one mov
static int is_leaf(Node* e) {
    return e->k == N_INT || e->k == N_FLOAT || e->k == N_BOOL || e->k == N_ID;
}

static void gen_leaf(const char* reg, Node* e) {
    switch (e->k) {
    case N_INT:
        if (e->ival >= -2147483648LL && e->ival <= 2147483647LL) o("mov %s, %lld", reg, e->ival);
        else o("movabs %s, %lld", reg, e->ival);
        return;
    case N_FLOAT: {
        uint64_t bits;
        memcpy(&bits, &e->fval, 8);
        o("movabs %s, %llu", reg, (unsigned long long)bits);
        return;
    }
    case N_BOOL: o("mov %s, %d", reg, (int)e->ival); return;
    case N_ID: {
        char addr[48];
        slot_addr(addr, e->aux, e->slot);
        o("mov %s, %s", reg, addr);
        return;
    }
    }
}

// evaluate a binop's operands into rax (lhs) and rcx (rhs), avoiding
// push/pop when either side is a leaf
static void gen_operands(Node* l, Node* r) {
    if (is_leaf(r)) {
        gen_expr(l);
        gen_leaf("rcx", r);
    } else if (is_leaf(l)) {
        gen_expr(r);
        o("mov rcx, rax");
        gen_leaf("rax", l);
    } else {
        gen_expr(l);
        o("push rax");
        gen_expr(r);
        o("mov rcx, rax");
        o("pop rax");
    }
}

// n / d or n % d with n in rax and constant d; truncates toward zero like idiv.
// The magic-number path (magic64) had a sign bug for large negative dividends,
// which silently corrupted the bootstrap (it mis-formatted integers near 2^62).
// This is the fossil seed -- correctness matters, speed does not -- so it always
// uses idiv now. The self-hosted compiler carries the fast reciprocal path.
static void gen_const_div(long long d, int is_mod) {
    if (d == 1) { if (is_mod) o("xor eax, eax"); return; }
    if (d == -1) { if (is_mod) o("xor eax, eax"); else o("neg rax"); return; }
    o("movabs rcx, %lld", d);
    o("cqo");
    o("idiv rcx");                           // no zero check: d is a nonzero constant
    if (is_mod) o("mov rax, rdx");
}

// ---- register promotion ----
// The hottest locals/params of each function live in callee-saved registers
// for the whole function body. Every generated function saves/restores the
// registers it uses, and the C runtime preserves them per the Win64 ABI, so
// promoted values survive all calls; the conservative GC sees them via its
// setjmp register spill.
#define NPROMO_REGS 6
static const char* PROMO_REGS[NPROMO_REGS] = { "rbx", "rsi", "rdi", "r13", "r14", "r15" };
static const char* g_lreg[MAX_SLOTS];   // local slot -> register name (or NULL)
static const char* g_preg[256];         // param idx -> register name (or NULL)
static int g_npromo;

static void slot_addr(char* buf, int kind, int idx) {
    if (kind == ID_LOCAL) {
        if (idx < MAX_SLOTS && g_lreg[idx]) { strcpy(buf, g_lreg[idx]); return; }
        sprintf(buf, "[rbp - %d]", 16 + 8 * g_npromo + 8 * idx);
    }
    else if (kind == ID_GLOBAL) sprintf(buf, "[rip + __zephyr_globals + %d]", 8 * idx);
    else {
        if (idx < 256 && g_preg[idx]) { strcpy(buf, g_preg[idx]); return; }
        if (g_curfn->regcall) // spilled to a home slot after the locals
            sprintf(buf, "[rbp - %d]", 16 + 8 * g_npromo + 8 * (g_curfn->nslots + idx));
        else
            sprintf(buf, "[rbp + %d]", 16 + 8 * (g_curfn->pnames.len - 1 - idx));
    }
}
static const char* ARG_REGS[4] = { "rcx", "rdx", "r8", "r9" };
static int addr_is_reg(const char* a) { return a[0] != '['; }

// reference counting walk for promotion decisions
static int g_lcount[MAX_SLOTS], g_pcount[256];

static void count_refs(Node* n, int weight) {
    if (!n) return;
    if (n->k == N_ID) {
        if (n->aux == ID_LOCAL && n->slot < MAX_SLOTS) g_lcount[n->slot] += weight;
        else if (n->aux == ID_PARAM && n->slot < 256) g_pcount[n->slot] += weight;
    }
    // code inside loops and deep inline expansions runs more often
    int w = weight;
    if (n->k == N_WHILE || n->k == N_FORR || n->k == N_FORIN) w = weight * 8 < 4096 ? weight * 8 : 4096;
    else if (n->k == N_INLINE) w = weight * 2 < 4096 ? weight * 2 : 4096;
    count_refs(n->a, n->k == N_FORR || n->k == N_FORIN || n->k == N_WHILE ? weight : w);
    count_refs(n->b, w);
    count_refs(n->c, w);
    for (int i = 0; i < n->kids.len; i++) count_refs(n->kids.items[i], w);
}

static void compute_promotions(Vec* stmts, int nslots, int nparams) {
    memset(g_lreg, 0, sizeof(const char*) * (nslots < MAX_SLOTS ? nslots + 1 : MAX_SLOTS));
    memset(g_preg, 0, sizeof(const char*) * (nparams < 256 ? nparams + 1 : 256));
    memset(g_lcount, 0, sizeof(int) * (nslots < MAX_SLOTS ? nslots + 1 : MAX_SLOTS));
    memset(g_pcount, 0, sizeof(int) * (nparams < 256 ? nparams + 1 : 256));
    g_npromo = 0;
    for (int i = 0; i < stmts->len; i++) count_refs(stmts->items[i], 1);
    if (nslots > MAX_SLOTS) nslots = MAX_SLOTS;
    if (nparams > 256) nparams = 256;
    for (int r = 0; r < NPROMO_REGS; r++) {
        int best = 0, bl = -1, bp = -1;
        for (int i = 0; i < nslots; i++)
            if (!g_lreg[i] && g_lcount[i] > best) { best = g_lcount[i]; bl = i; bp = -1; }
        for (int i = 0; i < nparams; i++)
            if (!g_preg[i] && g_pcount[i] > best) { best = g_pcount[i]; bp = i; bl = -1; }
        if (best < 2) break;
        if (bl >= 0) g_lreg[bl] = PROMO_REGS[g_npromo];
        else g_preg[bp] = PROMO_REGS[g_npromo];
        g_npromo++;
    }
}

static void gen_bounds_check(const char* listreg, const char* idxreg) {
    // panics unless 0 <= idx < len; unsigned compare covers negatives
    int ok = newlabel();
    o("cmp %s, [%s]", idxreg, listreg);
    o("jb .L%d", ok);
    if (strcmp(idxreg, "rax") == 0) { o("mov rdx, [%s]", listreg); o("mov rcx, rax"); }
    else { o("mov r8, [rcx]"); o("mov rcx, %s", idxreg); o("mov rdx, r8"); }
    rcall("rt_bounds_fail");
    olabel(ok);
}

// ---------------- AVX2 kernel for the AXPY inner-loop pattern ----------------
// Recognizes  for j in lo..hi { C[iC + j] += S * B[iB + j] }  over i64 lists and
// emits a 4-wide AVX2 kernel (vs Rust's 2-wide SSE2), with a bounds pre-check
// and a scalar remainder loop.
static void abyteN(const int* b, int n) {
    char line[192]; char* p = line + sprintf(line, "  .byte ");
    for (int i = 0; i < n; i++) p += sprintf(p, "%s%d", i ? "," : "", b[i] & 0xff);
    aline(line);
}
// one AVX2 instruction via 3-byte VEX. map:1=0F,2=0F38. pp:0,1=66,2=F3.
// reg=ModRM.reg (ymm dest or /ext); vvvv=src1 ymm (0 if none); rm is either a
// ymm reg (base<0) or memory [base+disp]. imm>=0 appends an imm8.
static void avx(int map, int pp, int W, int opcode, int reg, int vvvv, int rmreg, int base, int disp, int imm) {
    int b[16], n = 0;
    int R = (reg >> 3) & 1, mem = base >= 0;
    int rmlow = mem ? base : rmreg, B = (rmlow >> 3) & 1;
    b[n++] = 0xC4;
    b[n++] = ((~R & 1) << 7) | (1 << 6) | ((~B & 1) << 5) | map;   // ~X=1
    b[n++] = (W << 7) | ((~vvvv & 0xF) << 3) | (1 << 2) | pp;      // L=1 (256-bit)
    b[n++] = opcode;
    if (mem) {
        int mod, dsz;
        if (disp == 0 && (base & 7) != 5) { mod = 0; dsz = 0; }
        else if (disp >= -128 && disp <= 127) { mod = 1; dsz = 1; }
        else { mod = 2; dsz = 4; }
        int rm = base & 7, sib = rm == 4;
        b[n++] = (mod << 6) | ((reg & 7) << 3) | (sib ? 4 : rm);
        if (sib) b[n++] = (0 << 6) | (4 << 3) | rm;
        if (dsz == 1) b[n++] = disp & 0xff;
        else if (dsz == 4) for (int i = 0; i < 4; i++) b[n++] = (disp >> (8 * i)) & 0xff;
    } else {
        b[n++] = (3 << 6) | ((reg & 7) << 3) | (rmreg & 7);
    }
    if (imm >= 0) b[n++] = imm & 0xff;
    abyteN(b, n);
}
static void v_load(int d, int base, int disp) { avx(1, 2, 0, 0x6F, d, 0, 0, base, disp, -1); }
static void v_store(int base, int disp, int s) { avx(1, 2, 0, 0x7F, s, 0, 0, base, disp, -1); }
static void v_muludq(int d, int s1, int s2) { avx(1, 1, 0, 0xF4, d, s1, s2, -1, 0, -1); }
static void v_addq(int d, int s1, int s2) { avx(1, 1, 0, 0xD4, d, s1, s2, -1, 0, -1); }
static void v_srlq(int d, int s, int imm) { avx(1, 1, 0, 0x73, 2, d, s, -1, 0, imm); }
static void v_sllq(int d, int s, int imm) { avx(1, 1, 0, 0x73, 6, d, s, -1, 0, imm); }
static void v_zeroupper(void) { int b[3] = { 0xC5, 0xF8, 0x77 }; abyteN(b, 3); }

static int uses_local(Node* e, int slot) {
    if (!e) return 0;
    if (e->k == N_ID && e->aux == ID_LOCAL && e->slot == slot) return 1;
    if (uses_local(e->a, slot) || uses_local(e->b, slot) || uses_local(e->c, slot)) return 1;
    for (int i = 0; i < e->kids.len; i++) if (uses_local(e->kids.items[i], slot)) return 1;
    return 0;
}
// idx == INV + J : return the invariant addend, else NULL
static Node* axpy_inv(Node* idx, int jslot) {
    if (idx->k != N_BIN || idx->op != T_PLUS) return NULL;
    int aj = idx->a->k == N_ID && idx->a->aux == ID_LOCAL && idx->a->slot == jslot;
    int bj = idx->b->k == N_ID && idx->b->aux == ID_LOCAL && idx->b->slot == jslot;
    if (aj && !uses_local(idx->b, jslot)) return idx->b;
    if (bj && !uses_local(idx->a, jslot)) return idx->a;
    return NULL;
}

static void gen_stmts(Vec* stmts, int retlabel);
static void gen_expr(Node* e);

static int try_axpy(Node* s, int retlabel) {
    if (s->k != N_FORR) return 0;
    int jslot = s->slot;
    if (s->c->kids.len != 1) return 0;
    Node* asn = s->c->kids.items[0];
    if (asn->k != N_ASSIGN) return 0;
    Node* tgt = asn->a;                                   // C[iC+j]
    if (tgt->k != N_INDEX || tgt->a->k != N_ID || tgt->ty->k != K_INT) return 0;
    Node* iC = axpy_inv(tgt->b, jslot);
    if (!iC) return 0;
    Node* ex = asn->b;                                    // C[iC+j] + (S * B[iB+j])
    if (ex->k != N_BIN || ex->op != T_PLUS || ex->a != tgt) return 0;
    Node* mul = ex->b;
    if (mul->k != N_BIN || mul->op != T_STAR) return 0;
    Node *S, *Bacc;
    if (mul->b->k == N_INDEX) { S = mul->a; Bacc = mul->b; }
    else if (mul->a->k == N_INDEX) { S = mul->b; Bacc = mul->a; }
    else return 0;
    if (Bacc->a->k != N_ID || Bacc->ty->k != K_INT) return 0;
    Node* iB = axpy_inv(Bacc->b, jslot);
    if (!iB) return 0;
    if (uses_local(S, jslot)) return 0;

    Node* LC = tgt->a; Node* LB = Bacc->a;
    if (LC->aux == LB->aux && LC->slot == LB->slot) return 0;  // same array: avoid aliasing
    int scal = newlabel(), sdone = newlabel(), vloop = newlabel(), vskip = newlabel();
    char ja[48]; slot_addr(ja, ID_LOCAL, jslot);
    // frame: [rsp+0..31] S broadcast; temps at fixed offsets
    o("sub rsp, 128");
    gen_expr(LC); o("mov rcx, [rax + 16]"); o("mov [rsp + 32], rcx"); o("mov rcx, [rax]"); o("mov [rsp + 40], rcx");
    gen_expr(LB); o("mov rcx, [rax + 16]"); o("mov [rsp + 48], rcx"); o("mov rcx, [rax]"); o("mov [rsp + 56], rcx");
    gen_expr(iC); o("mov [rsp + 64], rax");
    gen_expr(iB); o("mov [rsp + 72], rax");
    gen_expr(s->a); o("mov [rsp + 80], rax");             // lo
    gen_expr(s->b); o("mov [rsp + 88], rax");             // hi
    gen_expr(S);
    o("mov [rsp + 0], rax"); o("mov [rsp + 8], rax"); o("mov [rsp + 16], rax"); o("mov [rsp + 24], rax");
    o("mov rax, [rsp + 64]"); o("add rax, [rsp + 80]"); o("mov [rsp + 96], rax");   // startC = iC+lo
    o("mov rax, [rsp + 72]"); o("add rax, [rsp + 80]"); o("mov [rsp + 104], rax");  // startB = iB+lo
    o("mov rax, [rsp + 88]"); o("sub rax, [rsp + 80]"); o("and rax, -4"); o("mov [rsp + 112], rax"); // bulk
    o("mov rax, [rsp + 80]"); o("add rax, [rsp + 112]"); o("mov [rsp + 120], rax");  // vend = lo+bulk
    o("mov rax, [rsp + 80]"); o("mov %s, rax", ja);       // j = lo (default for scalar path)
    // bounds pre-check; any failure -> scalar loop (which checks per element)
    o("mov rax, [rsp + 112]"); o("cmp rax, 0"); o("jle .L%d", vskip);
    o("mov rax, [rsp + 96]"); o("cmp rax, 0"); o("jl .L%d", vskip);
    o("mov rcx, [rsp + 96]"); o("add rcx, [rsp + 112]"); o("cmp rcx, [rsp + 40]"); o("jg .L%d", vskip);
    o("mov rax, [rsp + 104]"); o("cmp rax, 0"); o("jl .L%d", vskip);
    o("mov rcx, [rsp + 104]"); o("add rcx, [rsp + 112]"); o("cmp rcx, [rsp + 56]"); o("jg .L%d", vskip);
    // vector kernel: r10=C ptr, r11=B ptr, rax=group count
    o("mov r10, [rsp + 32]"); o("mov rax, [rsp + 96]"); o("lea r10, [r10 + rax*8]");
    o("mov r11, [rsp + 48]"); o("mov rax, [rsp + 104]"); o("lea r11, [r11 + rax*8]");
    o("mov rax, [rsp + 112]"); o("sar rax, 2");           // groups = bulk/4
    v_load(0, 4, 0);            // ymm0 = broadcast S ([rsp], base=rsp=4)
    v_srlq(5, 0, 32);           // ymm5 = S >> 32
    olabel(vloop);
    v_load(1, 11, 0);           // ymm1 = B[4]  ([r11])
    v_srlq(3, 1, 32);           // ymm3 = B >> 32
    v_muludq(2, 0, 1);          // ymm2 = Slo*Blo
    v_muludq(4, 0, 3);          // ymm4 = Slo*Bhi
    v_muludq(3, 5, 1);          // ymm3 = Shi*Blo
    v_addq(4, 4, 3);            // ymm4 = cross
    v_sllq(4, 4, 32);
    v_addq(2, 2, 4);            // ymm2 = product
    v_load(1, 10, 0);           // ymm1 = C[4]  ([r10])
    v_addq(1, 1, 2);
    v_store(10, 0, 1);          // C[4] = result
    o("add r11, 32"); o("add r10, 32"); o("sub rax, 1"); o("jne .L%d", vloop);
    v_zeroupper();
    o("mov rax, [rsp + 120]"); o("mov %s, rax", ja);      // j = vend
    olabel(vskip);
    // scalar remainder (or full loop if pre-check failed): while j < hi
    olabel(scal);
    o("mov rax, %s", ja); o("cmp rax, [rsp + 88]"); o("jge .L%d", sdone);
    gen_stmts(&s->c->kids, retlabel);
    if (addr_is_reg(ja)) o("inc %s", ja); else o("inc qword ptr %s", ja);
    o("jmp .L%d", scal);
    olabel(sdone);
    o("add rsp, 128");
    return 1;
}

static void gen_binop(Node* e) {
    int op = e->op;
    if (op == T_AND || op == T_OR) {
        int skip = newlabel(), end = newlabel();
        gen_expr(e->a);
        o("test rax, rax");
        o(op == T_AND ? "je .L%d" : "jne .L%d", skip);
        gen_expr(e->b);
        o("jmp .L%d", end);
        olabel(skip);
        o(op == T_AND ? "xor eax, eax" : "mov eax, 1");
        olabel(end);
        return;
    }
    int cat = e->aux;
    // int/int division or modulo by a nonzero constant: no idiv, no zero check
    if (cat == BC_INT && (op == T_SLASH || op == T_PCT) && e->b->k == N_INT && e->b->ival != 0) {
        gen_expr(e->a);
        gen_const_div(e->b->ival, op == T_PCT);
        return;
    }
    // int op with a small constant rhs: use an immediate operand
    if ((cat == BC_INT || cat == BC_BOOL) && e->b->k == N_INT &&
        e->b->ival >= -2147483648LL && e->b->ival <= 2147483647LL) {
        long long v = e->b->ival;
        switch (op) {
        case T_PLUS: gen_expr(e->a); o("add rax, %lld", v); return;
        case T_MINUS: gen_expr(e->a); o("sub rax, %lld", v); return;
        case T_STAR: gen_expr(e->a); o("imul rax, rax, %lld", v); return;
        case T_AMP: gen_expr(e->a); o("and rax, %lld", v); return;
        case T_PIPE: gen_expr(e->a); o("or rax, %lld", v); return;
        case T_CARET: gen_expr(e->a); o("xor rax, %lld", v); return;
        case T_SHL: gen_expr(e->a); o("shl rax, %lld", v & 63); return;
        case T_SHR: gen_expr(e->a); o("sar rax, %lld", v & 63); return;
        case T_EQEQ: case T_NE: case T_LT: case T_LE: case T_GT: case T_GE: {
            static const struct { int t; const char* cc; } ccs[] = {
                {T_EQEQ, "e"}, {T_NE, "ne"}, {T_LT, "l"}, {T_LE, "le"}, {T_GT, "g"}, {T_GE, "ge"},
            };
            const char* cc = "e";
            for (size_t i = 0; i < 6; i++) if (ccs[i].t == op) cc = ccs[i].cc;
            gen_expr(e->a);
            o("cmp rax, %lld", v);
            o("set%s al", cc);
            o("movzx eax, al");
            return;
        }
        }
    }
    // int op with a variable operand: fold the load into the instruction
    if (cat == BC_INT || cat == BC_BOOL) {
        Node *l = e->a, *r = e->b;
        if (l->k == N_ID && r->k != N_ID && !is_leaf(r) && (op == T_PLUS || op == T_STAR)) {
            Node* t = l; l = r; r = t; // commutative: compute the complex side first
        }
        if (r->k == N_ID) {
            char addr[48];
            slot_addr(addr, r->aux, r->slot);
            switch (op) {
            case T_PLUS: gen_expr(l); o("add rax, %s", addr); return;
            case T_MINUS: gen_expr(l); o("sub rax, %s", addr); return;
            case T_STAR: gen_expr(l); o("imul rax, %s", addr); return;
            case T_EQEQ: case T_NE: case T_LT: case T_LE: case T_GT: case T_GE: {
                static const struct { int t; const char* cc; } ccs[] = {
                    {T_EQEQ, "e"}, {T_NE, "ne"}, {T_LT, "l"}, {T_LE, "le"}, {T_GT, "g"}, {T_GE, "ge"},
                };
                const char* cc = "e";
                for (size_t i = 0; i < 6; i++) if (ccs[i].t == op) cc = ccs[i].cc;
                gen_expr(l);
                o("cmp rax, %s", addr);
                o("set%s al", cc);
                o("movzx eax, al");
                return;
            }
            }
        }
    }
    if (cat == BC_STR) {
        gen_expr(e->a);
        o("push rax");
        gen_expr(e->b);
        o("mov rcx, rax");   // rhs
        o("pop rax");        // lhs
        if (op == T_PLUS) {
            o("mov rdx, rcx");
            o("mov rcx, rax");
            rcall("rt_str_concat");
            return;
        }
        if (op == T_EQEQ || op == T_NE) {
            o("mov rdx, rcx");
            o("mov rcx, rax");
            rcall("rt_str_eq");
            if (op == T_NE) o("xor rax, 1");
            return;
        }
        // <, <=, >, >= via rt_str_cmp
        o("mov rdx, rcx");
        o("mov rcx, rax");
        rcall("rt_str_cmp");
        o("cmp rax, 0");
        o("set%s al", op == T_LT ? "l" : op == T_LE ? "le" : op == T_GT ? "g" : "ge");
        o("movzx eax, al");
        return;
    }
    gen_operands(e->a, e->b);   // numeric/bool: lhs in rax, rhs in rcx, no push/pop for leaves
    if (cat == BC_FLOAT) {
        o("movq xmm0, rax");
        o("movq xmm1, rcx");
        switch (op) {
        case T_PLUS: o("addsd xmm0, xmm1"); break;
        case T_MINUS: o("subsd xmm0, xmm1"); break;
        case T_STAR: o("mulsd xmm0, xmm1"); break;
        case T_SLASH: o("divsd xmm0, xmm1"); break;
        case T_PCT: die(e->line, "internal: float %%"); break;
        case T_GT: o("comisd xmm0, xmm1"); o("seta al"); o("movzx eax, al"); return;
        case T_GE: o("comisd xmm0, xmm1"); o("setae al"); o("movzx eax, al"); return;
        case T_LT: o("comisd xmm1, xmm0"); o("seta al"); o("movzx eax, al"); return;
        case T_LE: o("comisd xmm1, xmm0"); o("setae al"); o("movzx eax, al"); return;
        case T_EQEQ:
            o("ucomisd xmm0, xmm1");
            o("setnp al"); o("sete cl"); o("and al, cl"); o("movzx eax, al");
            return;
        case T_NE:
            o("ucomisd xmm0, xmm1");
            o("setp al"); o("setne cl"); o("or al, cl"); o("movzx eax, al");
            return;
        }
        o("movq rax, xmm0");
        return;
    }
    // int / bool
    switch (op) {
    case T_PLUS: o("add rax, rcx"); return;
    case T_MINUS: o("sub rax, rcx"); return;
    case T_STAR: o("imul rax, rcx"); return;
    case T_AMP: o("and rax, rcx"); return;
    case T_PIPE: o("or rax, rcx"); return;
    case T_CARET: o("xor rax, rcx"); return;
    case T_SHL: o("shl rax, cl"); return;
    case T_SHR: o("sar rax, cl"); return;
    case T_SLASH: case T_PCT: {
        int ok = newlabel();
        o("test rcx, rcx");
        o("jne .L%d", ok);
        rcall(op == T_SLASH ? "rt_div_zero" : "rt_mod_zero");
        olabel(ok);
        o("cqo");
        o("idiv rcx");
        if (op == T_PCT) o("mov rax, rdx");
        return;
    }
    case T_EQEQ: case T_NE: case T_LT: case T_LE: case T_GT: case T_GE: {
        static const struct { int t; const char* cc; } ccs[] = {
            {T_EQEQ, "e"}, {T_NE, "ne"}, {T_LT, "l"}, {T_LE, "le"}, {T_GT, "g"}, {T_GE, "ge"},
        };
        const char* cc = "e";
        for (size_t i = 0; i < 6; i++) if (ccs[i].t == op) cc = ccs[i].cc;
        o("cmp rax, rcx");
        o("set%s al", cc);
        o("movzx eax, al");
        return;
    }
    }
    die(e->line, "internal: unknown binop");
}

// emit "jump to label if cond is false", fusing comparisons into cmp+jcc
// instead of materializing a bool and testing it
static void gen_branch_false(Node* cond, int label) {
    if (cond->k == N_BIN && cond->aux == BC_INT &&
        (cond->op == T_EQEQ || cond->op == T_NE || cond->op == T_LT ||
         cond->op == T_LE || cond->op == T_GT || cond->op == T_GE)) {
        static const struct { int t; const char* inv; } ccs[] = {
            {T_EQEQ, "jne"}, {T_NE, "je"}, {T_LT, "jge"}, {T_LE, "jg"}, {T_GT, "jle"}, {T_GE, "jl"},
        };
        const char* inv = "je";
        for (size_t i = 0; i < 6; i++) if (ccs[i].t == cond->op) inv = ccs[i].inv;
        char addr[48];
        if (cond->b->k == N_INT && cond->b->ival >= -2147483648LL && cond->b->ival <= 2147483647LL) {
            if (cond->a->k == N_ID) {
                slot_addr(addr, cond->a->aux, cond->a->slot);
                o(addr_is_reg(addr) ? "cmp %s, %lld" : "cmp qword ptr %s, %lld", addr, cond->b->ival);
            } else {
                gen_expr(cond->a);
                o("cmp rax, %lld", cond->b->ival);
            }
        } else if (cond->b->k == N_ID) {
            gen_expr(cond->a);
            slot_addr(addr, cond->b->aux, cond->b->slot);
            o("cmp rax, %s", addr);
        } else {
            gen_operands(cond->a, cond->b);
            o("cmp rax, rcx");
        }
        o("%s .L%d", inv, label);
        return;
    }
    if (cond->k == N_BIN && cond->aux == BC_FLOAT &&
        (cond->op == T_LT || cond->op == T_LE || cond->op == T_GT || cond->op == T_GE)) {
        // a<b == b>a; unordered (NaN) compares false, and jbe/jb are taken on
        // unordered, so the false-branch is correct for NaN too
        gen_operands(cond->a, cond->b);
        o("movq xmm0, rax");
        o("movq xmm1, rcx");
        if (cond->op == T_LT) { o("comisd xmm1, xmm0"); o("jbe .L%d", label); }
        else if (cond->op == T_LE) { o("comisd xmm1, xmm0"); o("jb .L%d", label); }
        else if (cond->op == T_GT) { o("comisd xmm0, xmm1"); o("jbe .L%d", label); }
        else { o("comisd xmm0, xmm1"); o("jb .L%d", label); }
        return;
    }
    if (cond->k == N_NOT) { // if not x -> jump when x is true
        gen_expr(cond->a);
        o("test rax, rax");
        o("jne .L%d", label);
        return;
    }
    gen_expr(cond);
    o("test rax, rax");
    o("je .L%d", label);
}

// mirror of gen_branch_false: jump to label when the condition is TRUE
static void gen_branch_true(Node* cond, int label) {
    if (cond->k == N_BIN && cond->aux == BC_INT &&
        (cond->op == T_EQEQ || cond->op == T_NE || cond->op == T_LT ||
         cond->op == T_LE || cond->op == T_GT || cond->op == T_GE)) {
        static const struct { int t; const char* cc; } ccs[] = {
            {T_EQEQ, "je"}, {T_NE, "jne"}, {T_LT, "jl"}, {T_LE, "jle"}, {T_GT, "jg"}, {T_GE, "jge"},
        };
        const char* cc = "je";
        for (size_t i = 0; i < 6; i++) if (ccs[i].t == cond->op) cc = ccs[i].cc;
        char addr[48];
        if (cond->b->k == N_INT && cond->b->ival >= -2147483648LL && cond->b->ival <= 2147483647LL) {
            if (cond->a->k == N_ID) {
                slot_addr(addr, cond->a->aux, cond->a->slot);
                o(addr_is_reg(addr) ? "cmp %s, %lld" : "cmp qword ptr %s, %lld", addr, cond->b->ival);
            } else {
                gen_expr(cond->a);
                o("cmp rax, %lld", cond->b->ival);
            }
        } else if (cond->b->k == N_ID) {
            gen_expr(cond->a);
            slot_addr(addr, cond->b->aux, cond->b->slot);
            o("cmp rax, %s", addr);
        } else {
            gen_operands(cond->a, cond->b);
            o("cmp rax, rcx");
        }
        o("%s .L%d", cc, label);
        return;
    }
    if (cond->k == N_BIN && cond->aux == BC_FLOAT &&
        (cond->op == T_LT || cond->op == T_LE || cond->op == T_GT || cond->op == T_GE)) {
        gen_operands(cond->a, cond->b);
        o("movq xmm0, rax");
        o("movq xmm1, rcx");
        // ja/jae are not taken on unordered, so NaN correctly stays false
        if (cond->op == T_LT) { o("comisd xmm1, xmm0"); o("ja .L%d", label); }
        else if (cond->op == T_LE) { o("comisd xmm1, xmm0"); o("jae .L%d", label); }
        else if (cond->op == T_GT) { o("comisd xmm0, xmm1"); o("ja .L%d", label); }
        else { o("comisd xmm0, xmm1"); o("jae .L%d", label); }
        return;
    }
    if (cond->k == N_NOT) {
        gen_expr(cond->a);
        o("test rax, rax");
        o("je .L%d", label);
        return;
    }
    gen_expr(cond);
    o("test rax, rax");
    o("jne .L%d", label);
}

static void gen_call(Node* e) {
    switch (e->aux) {
    case CK_PRINT:
        gen_expr(e->kids.items[0]);
        o("mov rcx, rax");
        o("lea rdx, [rip + __td%d]", e->slot);
        rcall("rt_print_val");
        return;
    case CK_PANIC:
        gen_expr(e->kids.items[0]);
        o("mov rcx, rax");
        rcall("rt_panic_str");
        return;
    case CK_SQRT:
        gen_expr(e->kids.items[0]);
        o("movq xmm0, rax");
        o("sqrtsd xmm0, xmm0");
        o("movq rax, xmm0");
        return;
    case CK_LEN:
        gen_expr(e->a->a);
        o("mov rax, [rax]");
        return;
    case CK_PUSH:
        gen_expr(e->a->a);
        o("push rax");
        gen_expr(e->kids.items[0]);
        o("mov rdx, rax");
        o("pop rcx");
        rcall("rt_list_push");
        return;
    case CK_POP:
        gen_expr(e->a->a);
        o("mov rcx, rax");
        rcall("rt_list_pop");
        return;
    case CK_ARGS:
        rcall("rt_args");
        return;
    case CK_ZEROS:                 // preallocated [int] of n zeros (rt_list_new zeroes it)
        gen_expr(e->kids.items[0]);
        o("mov rcx, rax");
        rcall("rt_list_new");
        return;
    case CK_BITS:
        gen_expr(e->kids.items[0]); // a float already IS its bit pattern in rax
        return;
    case CK_READF:
        gen_expr(e->kids.items[0]);
        o("mov rcx, rax");
        rcall("rt_read_file");
        return;
    case CK_WRITEF:
        gen_expr(e->kids.items[0]);
        o("push rax");
        gen_expr(e->kids.items[1]);
        o("mov rdx, rax");
        o("pop rcx");
        rcall("rt_write_file");
        return;
    case CK_CHR:
        gen_expr(e->kids.items[0]);
        o("mov rcx, rax");
        rcall("rt_chr");
        return;
    case CK_EMIT:
        gen_expr(e->kids.items[0]);
        o("mov rcx, rax");
        rcall("rt_emit");
        return;
    case CK_LOAD64:
        gen_expr(e->kids.items[0]);
        o("mov rax, [rax]");
        return;
    case CK_LOAD8:
        gen_expr(e->kids.items[0]);
        o("movzx eax, byte ptr [rax]");
        return;
    case CK_STORE64:
        gen_expr(e->kids.items[0]);
        o("push rax");
        gen_expr(e->kids.items[1]);
        o("pop rcx");
        o("mov [rcx], rax");
        return;
    case CK_STORE32:
        gen_expr(e->kids.items[0]);
        o("push rax");
        gen_expr(e->kids.items[1]);
        o("pop rcx");
        o("mov [rcx], eax");
        return;
    case CK_STORE8:
        gen_expr(e->kids.items[0]);
        o("push rax");
        gen_expr(e->kids.items[1]);
        o("pop rcx");
        o("mov [rcx], al");
        return;
    case CK_STACKPTR:
        o("mov rax, rsp");
        return;
    case CK_WIN: {
        // Win64 call to a kernel32 import: first 4 int args in rcx/rdx/r8/r9,
        // args 5+ on the stack at [rsp+32], [rsp+40], ...
        int nargs = e->kids.len - 1;
        // push args so [rsp]=argN ... [rsp+8*(N-1)]=arg1
        for (int i = 1; i <= nargs; i++) {
            gen_expr(e->kids.items[i]);
            o("push rax");
        }
        const char* ar[4] = { "rcx", "rdx", "r8", "r9" };
        for (int i = 0; i < nargs && i < 4; i++)
            o("mov %s, [rsp + %d]", ar[i], 8 * (nargs - 1 - i));
        o("mov r12, rsp");
        o("and rsp, -16");
        int stackargs = nargs > 4 ? nargs - 4 : 0;
        int frame = 32 + 8 * stackargs;
        frame = (frame + 15) & ~15;         // keep rsp 16-aligned at the call
        o("sub rsp, %d", frame);
        for (int k = 0; k < stackargs; k++) {
            o("mov rax, [r12 + %d]", 8 * (nargs - 5 - k)); // arg(5+k)
            o("mov [rsp + %d], rax", 32 + 8 * k);
        }
        Node* nm = e->kids.items[0];
        const char* fn = ((Node*)nm->kids.items[0])->name;
        o("call __imp_k_%s", fn); // kernel32 import; assembler makes it a Win64 IAT call
        o("mov rsp, r12");
        if (nargs) o("add rsp, %d", 8 * nargs);
        return;
    }
    case CK_BYTE:
        gen_expr(e->a->a);
        o("push rax");
        gen_expr(e->kids.items[0]);
        o("pop rcx");
        gen_bounds_check("rcx", "rax");     // str layout matches: len at [ptr]
        o("movzx eax, byte ptr [rcx + rax + 8]");
        return;
    case CK_SUB:
        gen_expr(e->a->a);
        o("push rax");
        gen_expr(e->kids.items[0]);
        o("push rax");
        gen_expr(e->kids.items[1]);
        o("mov r8, rax");
        o("pop rdx");
        o("pop rcx");
        rcall("rt_str_sub");
        return;
    case CK_JOIN:
        gen_expr(e->a->a);
        o("mov rcx, rax");
        rcall("rt_join");
        return;
    }
    // user function (plain or UFCS)
    FDef* f = e->ref;
    Node* args[64];
    int nargs = 0;
    if (e->op == 1) args[nargs++] = e->a->a; // method-style: obj first
    for (int i = 0; i < e->kids.len; i++) args[nargs++] = e->kids.items[i];
    if (f->regcall) {
        // non-leaf args evaluate in source order (last stays in rax), leaves
        // load directly into their registers afterwards
        int last_nonleaf = -1;
        for (int i = 0; i < nargs; i++) if (!is_leaf(args[i])) last_nonleaf = i;
        for (int i = 0; i < nargs; i++) {
            if (is_leaf(args[i])) continue;
            gen_expr(args[i]);
            if (i != last_nonleaf) o("push rax");
        }
        if (last_nonleaf >= 0) o("mov %s, rax", ARG_REGS[last_nonleaf]);
        for (int i = nargs - 1; i >= 0; i--) {
            if (is_leaf(args[i]) || i == last_nonleaf) continue;
            o("pop %s", ARG_REGS[i]);
        }
        for (int i = 0; i < nargs; i++)
            if (is_leaf(args[i])) gen_leaf(ARG_REGS[i], args[i]);
        o("call %s", fn_label(f->name));
        return;
    }
    for (int i = 0; i < nargs; i++) {
        gen_expr(args[i]);
        o("push rax");
    }
    o("call %s", fn_label(f->name));
    if (nargs) o("add rsp, %d", 8 * nargs);
}

static void gen_expr(Node* e) {
    switch (e->k) {
    case N_INT: o("movabs rax, %lld", e->ival); return;
    case N_FLOAT: {
        uint64_t bits;
        memcpy(&bits, &e->fval, 8);
        o("movabs rax, %llu", (unsigned long long)bits);
        return;
    }
    case N_BOOL: o("mov eax, %d", (int)e->ival); return;
    case N_STRLIT: {
        if (e->kids.len == 1 && ((Node*)e->kids.items[0])->k == N_STRTXT) {
            Node* p = e->kids.items[0];
            o("lea rax, [rip + __s%d]", add_dstr(p->name, (int)strlen(p->name)));
            return;
        }
        // interpolation: append parts into the shared builder, one allocation
        // at the end; mark/truncate makes nested interpolations safe
        rcall("rt_sb_begin");
        o("push rax");
        for (int i = 0; i < e->kids.len; i++) {
            Node* p = e->kids.items[i];
            if (p->k == N_STRTXT) {
                o("lea rcx, [rip + __s%d]", add_dstr(p->name, (int)strlen(p->name)));
                rcall("rt_sb_txt");
            } else { // N_INTERP
                gen_expr(p->a);
                o("mov rcx, rax");
                o("lea rdx, [rip + __td%d]", p->slot);
                rcall("rt_sb_val");
            }
        }
        o("pop rcx");
        rcall("rt_sb_end");
        return;
    }
    case N_ID: {
        char addr[48];
        slot_addr(addr, e->aux, e->slot);
        o("mov rax, %s", addr);
        return;
    }
    case N_LIST: {
        o("mov rcx, %d", e->kids.len);
        rcall("rt_list_new");
        o("push rax");
        for (int i = 0; i < e->kids.len; i++) {
            gen_expr(e->kids.items[i]);
            o("mov rdx, [rsp]");
            o("mov rdx, [rdx + 16]");
            o("mov [rdx + %d], rax", 8 * i);
        }
        o("pop rax");
        return;
    }
    case N_SLIT: {
        SDef* sd = e->ref;
        o("mov rcx, %d", 8 * sd->fnames.len);
        rcall("rt_alloc");
        o("push rax");
        for (int i = 0; i < e->kids.len; i++) {
            Node* f = e->kids.items[i];
            gen_expr(f->a);
            o("mov rdx, [rsp]");
            o("mov [rdx + %d], rax", 8 * f->slot);
        }
        o("pop rax");
        return;
    }
    case N_NEG:
        gen_expr(e->a);
        if (e->ty->k == K_FLOAT) {
            o("movabs rcx, %llu", 0x8000000000000000ULL);
            o("xor rax, rcx");
        } else o("neg rax");
        return;
    case N_NOT:
        gen_expr(e->a);
        o("xor rax, 1");
        return;
    case N_BIN: gen_binop(e); return;
    case N_CAST:
        gen_expr(e->a);
        switch (e->aux) {
        case C_NONE: return;
        case C_I2F: o("cvtsi2sd xmm0, rax"); o("movq rax, xmm0"); return;
        case C_TRUNC: o("movq xmm0, rax"); o("cvttsd2si rax, xmm0"); return;
        case C_TOSTR:
            o("mov rcx, rax");
            o("lea rdx, [rip + __td%d]", e->slot);
            rcall("rt_to_str");
            return;
        case C_S2I: o("mov rcx, rax"); rcall("rt_str_to_int"); return;
        case C_S2F: o("mov rcx, rax"); rcall("rt_str_to_float"); return;
        }
        return;
    case N_INDEX:
        if (is_leaf(e->a)) {           // list is a simple var: no stack shuffle
            gen_expr(e->b);            // index -> rax
            gen_leaf("rcx", e->a);     // list ptr -> rcx
        } else {
            gen_expr(e->a);
            o("push rax");
            gen_expr(e->b);
            o("pop rcx");
        }
        gen_bounds_check("rcx", "rax");
        o("mov rcx, [rcx + 16]");
        o("mov rax, [rcx + rax*8]");
        return;
    case N_MEMBER:
        gen_expr(e->a);
        o("mov rax, [rax + %d]", 8 * e->slot);
        return;
    case N_CALL: gen_call(e); return;
    }
    die(e->line, "internal: cannot generate expression kind %d", e->k);
}

static void gen_stmts(Vec* stmts, int retlabel);

static void gen_stmt(Node* s, int retlabel) {
    char addr[48];
    switch (s->k) {
    case N_DECL:
        gen_expr(s->a);
        slot_addr(addr, s->aux, s->slot);
        o("mov %s, rax", addr);
        return;
    case N_ASSIGN: {
        Node* t = s->a;
        if (t->k == N_ID) {
            gen_expr(s->b);
            slot_addr(addr, t->aux, t->slot);
            o("mov %s, rax", addr);
        } else if (t->k == N_MEMBER) {
            gen_expr(t->a);
            o("push rax");
            gen_expr(s->b);
            o("pop rcx");
            o("mov [rcx + %d], rax", 8 * t->slot);
        } else { // index
            if (is_leaf(t->a)) {          // list is a var: load it last, skip its push/pop
                gen_expr(t->b);           // index -> rax
                if (is_leaf(s->b)) {
                    o("mov rdx, rax");    // index -> rdx
                    gen_leaf("rax", s->b);// value -> rax
                } else {
                    o("push rax");        // save index
                    gen_expr(s->b);       // value -> rax
                    o("pop rdx");         // index
                }
                gen_leaf("rcx", t->a);    // list -> rcx
            } else {
                gen_expr(t->a);
                o("push rax");
                gen_expr(t->b);
                o("push rax");
                gen_expr(s->b);
                o("pop rdx");   // index
                o("pop rcx");   // list
            }
            gen_bounds_check("rcx", "rdx");
            o("mov r8, [rcx + 16]");
            o("mov [r8 + rdx*8], rax");
        }
        return;
    }
    case N_IF: {
        int els = newlabel(), end = newlabel();
        gen_branch_false(s->a, els);
        gen_stmts(&s->b->kids, retlabel);
        if (s->c) o("jmp .L%d", end);
        olabel(els);
        if (s->c) { gen_stmts(&s->c->kids, retlabel); olabel(end); }
        return;
    }
    case N_WHILE: { // rotated: entry guard, test at the bottom
        int top = newlabel(), cont = newlabel(), end = newlabel();
        gen_branch_false(s->a, end);
        olabel(top);
        g_brk[g_loopdepth] = end; g_cont[g_loopdepth] = cont; g_loopdepth++;
        gen_stmts(&s->b->kids, retlabel);
        g_loopdepth--;
        olabel(cont);
        gen_branch_true(s->a, top);
        olabel(end);
        return;
    }
    case N_FORR: { // rotated: entry guard, increment+test at the bottom
        if (try_axpy(s, retlabel)) return;   // AVX2 fast path for the AXPY idiom
        int top = newlabel(), cont = newlabel(), end = newlabel();
        char v[48], lim[48];
        slot_addr(v, ID_LOCAL, s->slot);
        slot_addr(lim, ID_LOCAL, s->aux);
        gen_expr(s->a);
        o("mov %s, rax", v);
        gen_expr(s->b);
        o("mov %s, rax", lim);
        if (addr_is_reg(v) || addr_is_reg(lim)) o("cmp %s, %s", v, lim);
        else { o("mov rax, %s", v); o("cmp rax, %s", lim); }
        o("jge .L%d", end);
        olabel(top);
        g_brk[g_loopdepth] = end; g_cont[g_loopdepth] = cont; g_loopdepth++;
        gen_stmts(&s->c->kids, retlabel);
        g_loopdepth--;
        olabel(cont);
        if (addr_is_reg(v)) o("inc %s", v);
        else o("inc qword ptr %s", v);
        if (addr_is_reg(v) || addr_is_reg(lim)) o("cmp %s, %s", v, lim);
        else { o("mov rax, %s", v); o("cmp rax, %s", lim); }
        o("jl .L%d", top);
        olabel(end);
        return;
    }
    case N_FORIN: { // rotated like for-range; length re-read so growth is seen
        int top = newlabel(), cont = newlabel(), end = newlabel();
        char lst[48], idx[48], v[48];
        slot_addr(lst, ID_LOCAL, s->aux);
        slot_addr(idx, ID_LOCAL, s->op);
        slot_addr(v, ID_LOCAL, s->slot);
        gen_expr(s->a);
        o("mov %s, rax", lst);
        if (addr_is_reg(idx)) o("mov %s, 0", idx);
        else o("mov qword ptr %s, 0", idx);
        o("cmp qword ptr [rax], 0");
        o("jle .L%d", end);
        olabel(top);
        o("mov rcx, %s", lst);
        o("mov rax, %s", idx);
        o("mov rdx, [rcx + 16]");
        o("mov rax, [rdx + rax*8]");
        o("mov %s, rax", v);
        g_brk[g_loopdepth] = end; g_cont[g_loopdepth] = cont; g_loopdepth++;
        gen_stmts(&s->c->kids, retlabel);
        g_loopdepth--;
        olabel(cont);
        if (addr_is_reg(idx)) o("inc %s", idx);
        else o("inc qword ptr %s", idx);
        o("mov rcx, %s", lst);
        o("mov rax, %s", idx);
        o("cmp rax, [rcx]");
        o("jl .L%d", top);
        olabel(end);
        return;
    }
    case N_RET:
        if (s->a) gen_expr(s->a);
        o("jmp .L%d", retlabel);
        return;
    case N_INLINE: {
        // contract: every IRET leaves the result in rax and jumps here;
        // one store at the end label instead of one per return path
        int end = newlabel();
        g_inlend[g_inldepth++] = end;
        gen_stmts(&s->kids, retlabel);
        g_inldepth--;
        olabel(end);
        slot_addr(addr, ID_LOCAL, s->slot);
        o("mov %s, rax", addr);
        return;
    }
    case N_IRET:
        if (s->a) gen_expr(s->a);
        o("jmp .L%d", g_inlend[g_inldepth - 1]);
        return;
    case N_BRK: o("jmp .L%d", g_brk[g_loopdepth - 1]); return;
    case N_CONT: o("jmp .L%d", g_cont[g_loopdepth - 1]); return;
    case N_EXPRST: gen_expr(s->a); return;
    case N_FN: case N_STRUCTDEF: return;
    }
    die(s->line, "internal: cannot generate statement kind %d", s->k);
}

static void gen_stmts(Vec* stmts, int retlabel) {
    for (int i = 0; i < stmts->len; i++) gen_stmt(stmts->items[i], retlabel);
}

static void gen_fn_body(const char* label, FDef* f, Vec* stmts) {
    g_curfn = f;
    compute_promotions(stmts, f->nslots, f->pnames.len);
    char lbuf[300];
    snprintf(lbuf, sizeof lbuf, "%s:", label);
    aline(lbuf);
    o("push rbp");
    o("mov rbp, rsp");
    o("push r12");
    for (int i = 0; i < g_npromo; i++) o("push %s", PROMO_REGS[i]);
    int frame = f->nslots + (f->regcall ? f->pnames.len : 0);
    if (frame) o("sub rsp, %d", 8 * frame);
    if (f->regcall) {
        char pa[48];
        for (int i = 0; i < f->pnames.len; i++) {
            slot_addr(pa, ID_PARAM, i); // promoted register or home slot
            o("mov %s, %s", pa, ARG_REGS[i]);
        }
    } else {
        for (int i = 0; i < f->pnames.len && i < 256; i++)
            if (g_preg[i]) o("mov %s, [rbp + %d]", g_preg[i], 16 + 8 * (f->pnames.len - 1 - i));
    }
    int retlabel = newlabel();
    // Hand the globals array to the collector as a root set. This must land
    // *after* the runtime's own top-level initializers, which would otherwise
    // overwrite the pointer we just gave it. Those initializers never
    // allocate, so no collection can happen before this point.
    int is_main = strcmp(label, "zephyr_main") == 0 && g_nglobals;
    for (int i = 0; i < stmts->len; i++) {
        if (is_main && i == g_rt_top) {
            o("lea rcx, [rip + __zephyr_globals]");
            o("mov rdx, %d", g_nglobals);
            rcall("rt_set_globals");
        }
        gen_stmt(stmts->items[i], retlabel);
    }
    if (is_main && g_rt_top >= stmts->len) {
        o("lea rcx, [rip + __zephyr_globals]");
        o("mov rdx, %d", g_nglobals);
        rcall("rt_set_globals");
    }
    olabel(retlabel);
    o("lea rsp, [rbp - %d]", 8 + 8 * g_npromo);
    for (int i = g_npromo - 1; i >= 0; i--) o("pop %s", PROMO_REGS[i]);
    o("pop r12");
    o("pop rbp");
    o("ret");
    aline("");
}

// ---- peephole over the buffered .text lines ----
static int is_store_rax(const char* l, char* mem, size_t cap) {
    // "  mov TARGET, rax" where TARGET is a register or memory operand
    if (strncmp(l, "  mov ", 6) != 0) return 0;
    size_t len = strlen(l);
    if (len < 12 || strcmp(l + len - 5, ", rax") != 0) return 0;
    size_t n = len - 11;
    if (n == 0 || n + 1 > cap) return 0;
    memcpy(mem, l + 6, n);
    mem[n] = 0;
    return strcmp(mem, "rax") != 0;
}
static int is_load_rax(const char* l, char* mem, size_t cap) {
    // "  mov rax, SRC"
    if (strncmp(l, "  mov rax, ", 11) != 0) return 0;
    size_t n = strlen(l) - 11;
    if (n == 0 || n + 1 > cap) return 0;
    memcpy(mem, l + 11, n);
    mem[n] = 0;
    return 1;
}

static void peephole(void) {
    char m1[64], m2[64];
    for (int pass = 0; pass < 3; pass++) {
        char** L = (char**)g_alines.items;
        int n = g_alines.len;
        for (int i = 0; i + 1 < n; i++) {
            if (!L[i]) continue;
            int j = i + 1;
            while (j < n && !L[j]) j++;
            if (j >= n) break;
            // jmp to the immediately following label
            if (strncmp(L[i], "  jmp .L", 8) == 0) {
                char want[32];
                snprintf(want, sizeof want, "%s:", L[i] + 6);
                if (strcmp(L[j], want) == 0) { L[i] = NULL; continue; }
            }
            // store rax to T, then a reload of T with only rax/T-preserving
            // instructions (cmp/test/conditional jumps) in between
            if (is_store_rax(L[i], m1, sizeof m1)) {
                int k = j, steps = 0, stop = 0;
                while (k < n && steps < 6 && !stop) {
                    if (!L[k]) { k++; continue; }
                    if (is_load_rax(L[k], m2, sizeof m2)) {
                        if (strcmp(m1, m2) == 0) L[k] = NULL;
                        break; // any other rax load redefines rax
                    }
                    if (strncmp(L[k], "  cmp ", 6) == 0 || strncmp(L[k], "  test ", 7) == 0 ||
                        (L[k][0] == ' ' && L[k][2] == 'j' && strncmp(L[k], "  jmp", 5) != 0)) {
                        k++; steps++; continue;
                    }
                    stop = 1;
                }
            }
            // load rax; cmp rax, ...; jcc; identical adjacent reload -> drop the reload
            if (is_load_rax(L[i], m1, sizeof m1)) {
                if (L[j] && strncmp(L[j], "  cmp rax, ", 11) == 0) {
                    int a = j + 1;
                    while (a < n && !L[a]) a++;
                    if (a < n && strncmp(L[a], "  j", 3) == 0 && strncmp(L[a], "  jmp", 5) != 0) {
                        int b = a + 1;
                        while (b < n && !L[b]) b++;
                        if (b < n && is_load_rax(L[b], m2, sizeof m2) && strcmp(m1, m2) == 0)
                            L[b] = NULL;
                    }
                }
            }
        }
    }
    // compact
    int w = 0;
    for (int i = 0; i < g_alines.len; i++)
        if (g_alines.items[i]) g_alines.items[w++] = g_alines.items[i];
    g_alines.len = w;
}

static void emit_bytes(const char* data, int len) {
    char line[16 + 16 * 4];
    for (int i = 0; i < len; i += 16) {
        char* p = line;
        p += sprintf(p, "  .byte ");
        for (int j = i; j < len && j < i + 16; j++)
            p += sprintf(p, "%s%d", j > i ? "," : "", (unsigned char)data[j]);
        aline(line);
    }
}

static void gen_program(Node* prog) {
    aline(".intel_syntax noprefix");
    aline(".text");
    aline(".globl zephyr_main");
    aline("");
    for (int i = 0; i < prog->kids.len; i++) {
        Node* n = prog->kids.items[i];
        if (n->k != N_FN) continue;
        FDef* f = n->ref;
        char label[256];
        snprintf(label, sizeof label, "%s", fn_label(f->name));
        gen_fn_body(label, f, &f->body->kids);
    }
    // top-level statements
    {
        Vec top = {0};
        for (int i = 0; i < prog->kids.len; i++) {
            Node* n = prog->kids.items[i];
            if (n->k != N_FN && n->k != N_STRUCTDEF) vpush(&top, n);
        }
        gen_fn_body("zephyr_main", g_top, &top);
    }
    peephole();

    // data: Zephyr string constants ({i64 len; bytes})
    char ln[128];
    aline(".section .rdata");
    for (int i = 0; i < g_dstrs.len; i++) {
        DataStr* d = g_dstrs.items[i];
        aline(".balign 8");
        snprintf(ln, sizeof ln, "__s%d:", d->id); aline(ln);
        snprintf(ln, sizeof ln, "  .quad %d", d->len); aline(ln);
        emit_bytes(d->data, d->len);
    }
    // type descriptors (may pull in new cstrs/descs while emitting — loop by index)
    for (int i = 0; i < g_descs.len; i++) {
        Type* t = g_descs.items[i];
        aline(".balign 8");
        snprintf(ln, sizeof ln, "__td%d:", i); aline(ln);
        switch (t->k) {
        case K_INT: aline("  .quad 0"); break;
        case K_FLOAT: aline("  .quad 1"); break;
        case K_BOOL: aline("  .quad 2"); break;
        case K_STR: aline("  .quad 3"); break;
        case K_LIST:
            aline("  .quad 4");
            snprintf(ln, sizeof ln, "  .quad __td%d", td_index(t->el)); aline(ln);
            break;
        case K_STRUCT: {
            SDef* sd = t->sd;
            aline("  .quad 5");
            snprintf(ln, sizeof ln, "  .quad __c%d", add_cstr(sd->name)); aline(ln);
            snprintf(ln, sizeof ln, "  .quad %d", sd->fnames.len); aline(ln);
            for (int j = 0; j < sd->fnames.len; j++) {
                snprintf(ln, sizeof ln, "  .quad __c%d", add_cstr(sd->fnames.items[j])); aline(ln);
                snprintf(ln, sizeof ln, "  .quad __td%d", td_index(sd->ftypes.items[j])); aline(ln);
            }
            break;
        }
        }
    }
    for (int i = 0; i < g_dcstrs.len; i++) {
        DataStr* d = g_dcstrs.items[i];
        snprintf(ln, sizeof ln, "__c%d:", d->id); aline(ln);
        emit_bytes(d->data, d->len);
        aline("  .byte 0");
    }
    if (g_nglobals) {
        aline(".section .bss");
        aline(".balign 8");
        aline("__zephyr_globals:");
        snprintf(ln, sizeof ln, "  .space %d", 8 * g_nglobals); aline(ln);
    }
}

// ---------------- assembler ----------------
// Encodes exactly the instruction vocabulary this compiler emits — nothing
// more. Two-phase: assemble all lines recording symbols and fixups, then the
// PE writer lays out sections and patches everything.
enum { S_TEXT, S_RDATA, S_BSS };
enum { FX_REL32, FX_IAT32, FX_ABS64 }; // rel32 to symbol / to IAT slot / abs va

typedef struct { char name[80]; int sect; uint32_t off; int defined; int predef; } ASym;
typedef struct { uint32_t off; int sect; int kind; int sym; int32_t addend; } AFix;
typedef struct { unsigned char* p; size_t len, cap; } BBuf;

static Vec a_syms, a_fixes, a_imports;
static BBuf a_text, a_rdata;
static uint32_t a_bss;
static int a_sect;
static const char* a_curline; // for error messages

static void asm_die(const char* msg) {
    fprintf(stderr, "internal assembler error: %s\n  line: %s\n", msg, a_curline ? a_curline : "?");
    exit(1);
}

static void bput8(BBuf* b, int v) {
    if (b->len == b->cap) {
        b->cap = b->cap ? b->cap * 2 : 65536;
        b->p = realloc(b->p, b->cap);
        if (!b->p) asm_die("out of memory");
    }
    b->p[b->len++] = (unsigned char)v;
}
static void bput32(BBuf* b, uint32_t v) { for (int i = 0; i < 4; i++) bput8(b, (v >> (8 * i)) & 0xff); }
static void bput64(BBuf* b, uint64_t v) { for (int i = 0; i < 8; i++) bput8(b, (v >> (8 * i)) & 0xff); }

#define SYMHASH_SZ 65536
static int symhash[SYMHASH_SZ]; // value = sym index + 1, 0 = empty
static int symhash_init_done;

static uint32_t str_hash(const char* s) {
    uint32_t h = 2166136261u;
    while (*s) { h ^= (unsigned char)*s++; h *= 16777619u; }
    return h;
}

static int sym_intern(const char* name) {
    if (!symhash_init_done) { memset(symhash, 0, sizeof symhash); symhash_init_done = 1; }
    uint32_t h = str_hash(name) & (SYMHASH_SZ - 1);
    while (symhash[h]) {
        int idx = symhash[h] - 1;
        if (strcmp(((ASym*)a_syms.items[idx])->name, name) == 0) return idx;
        h = (h + 1) & (SYMHASH_SZ - 1);
    }
    ASym* s = xmalloc(sizeof(ASym));
    snprintf(s->name, sizeof s->name, "%s", name);
    vpush(&a_syms, s);
    symhash[h] = a_syms.len;
    return a_syms.len - 1;
}
// read-only: is `name` a locally-defined (or pre-scanned) label?
static int sym_is_local(const char* name) {
    if (!symhash_init_done) return 0;
    uint32_t h = str_hash(name) & (SYMHASH_SZ - 1);
    while (symhash[h]) {
        int idx = symhash[h] - 1;
        ASym* s = a_syms.items[idx];
        if (strcmp(s->name, name) == 0) return s->predef || s->defined;
        h = (h + 1) & (SYMHASH_SZ - 1);
    }
    return 0;
}
// each import belongs to a DLL: 0 = zephyr_rt.dll (rt_*), 1 = kernel32.dll (win)
typedef struct { char* name; int dll; } AImport;
static int import_intern2(const char* name, int dll) {
    for (int i = 0; i < a_imports.len; i++)
        if (strcmp(((AImport*)a_imports.items[i])->name, name) == 0) return i;
    AImport* im = xmalloc(sizeof(AImport));
    im->name = xstrndup(name, strlen(name));
    im->dll = dll;
    vpush(&a_imports, im);
    return a_imports.len - 1;
}
static int import_intern(const char* name) { return import_intern2(name, 0); }
static void add_fix(int kind, int sym, int32_t addend) { // at current text/rdata end
    AFix* f = xmalloc(sizeof(AFix));
    f->sect = a_sect;
    f->off = a_sect == S_TEXT ? (uint32_t)a_text.len : (uint32_t)a_rdata.len;
    f->kind = kind;
    f->sym = sym;
    f->addend = addend;
    vpush(&a_fixes, f);
}

// ---- operand parsing ----
enum { OP_NONE, OP_REG, OP_XMM, OP_IMM, OP_MEM, OP_SYM };
typedef struct {
    int kind, reg, size;               // size: 64/32/8
    long long imm;
    int base, index, scale;            // -1 none; base -2 = rip
    int32_t disp;
    char sym[128];
} Op;

static int reg_lookup(const char* s, int* size) {
    static const char* r64[16] = { "rax","rcx","rdx","rbx","rsp","rbp","rsi","rdi",
                                   "r8","r9","r10","r11","r12","r13","r14","r15" };
    for (int i = 0; i < 16; i++) if (strcmp(s, r64[i]) == 0) { *size = 64; return i; }
    if (strcmp(s, "eax") == 0) { *size = 32; return 0; }
    if (strcmp(s, "ecx") == 0) { *size = 32; return 1; }
    if (strcmp(s, "al") == 0) { *size = 8; return 0; }
    if (strcmp(s, "cl") == 0) { *size = 8; return 1; }
    return -1;
}

static void parse_operand(const char* text, Op* op) {
    memset(op, 0, sizeof *op);
    op->base = op->index = -1;
    op->size = 64;
    while (*text == ' ') text++;
    if (strncmp(text, "qword ptr ", 10) == 0) { text += 10; }
    else if (strncmp(text, "byte ptr ", 9) == 0) { op->size = 8; text += 9; }
    if (*text == '[') {
        op->kind = OP_MEM;
        char buf[128];
        snprintf(buf, sizeof buf, "%s", text + 1);
        char* close = strchr(buf, ']');
        if (!close) asm_die("missing ]");
        *close = 0;
        // split on +/- tokens
        char* p = buf;
        int sign = 1;
        while (*p) {
            while (*p == ' ') p++;
            if (*p == '+') { sign = 1; p++; continue; }
            if (*p == '-') { sign = -1; p++; continue; }
            if (!*p) break;
            char tok[96]; int tl = 0;
            while (*p && *p != ' ' && *p != '+' && *p != '-') tok[tl++] = *p++;
            tok[tl] = 0;
            if (tl == 0) continue;
            if ((tok[0] >= '0' && tok[0] <= '9')) {
                op->disp += sign * (int32_t)strtoll(tok, NULL, 10);
            } else if (strcmp(tok, "rip") == 0) {
                op->base = -2;
            } else {
                char* star = strchr(tok, '*');
                int rs;
                if (star) {
                    *star = 0;
                    int r = reg_lookup(tok, &rs);
                    if (r < 0) asm_die("bad index register");
                    op->index = r;
                    op->scale = atoi(star + 1);
                } else {
                    int r = reg_lookup(tok, &rs);
                    if (r >= 0) {
                        if (op->base == -1) op->base = r;
                        else { op->index = r; op->scale = 1; }
                    } else {
                        snprintf(op->sym, sizeof op->sym, "%s", tok);
                    }
                }
            }
            sign = 1;
        }
        return;
    }
    if ((*text >= '0' && *text <= '9') || *text == '-') {
        op->kind = OP_IMM;
        op->imm = *text == '-' ? strtoll(text, NULL, 10) : (long long)strtoull(text, NULL, 10);
        return;
    }
    if (text[0] == 'x' && text[1] == 'm' && text[2] == 'm') {
        op->kind = OP_XMM;
        op->reg = atoi(text + 3);
        return;
    }
    int size, r = reg_lookup(text, &size);
    if (r >= 0) { op->kind = OP_REG; op->reg = r; op->size = size; return; }
    op->kind = OP_SYM;
    snprintf(op->sym, sizeof op->sym, "%s", text);
}

// ---- encoding ----
static int g_trail; // immediate bytes that follow the modrm/disp (rel32 math)

// emit REX + opcode bytes + modrm/sib/disp for `reg` (register field, may be
// an opcode extension) against r/m operand `rm` (register or memory)
static void enc_rm(int rexw, const unsigned char* opc, int nopc, int reg, Op* rm,
                   int pfx66, int pfxF2) {
    if (pfx66) bput8(&a_text, 0x66);
    if (pfxF2) bput8(&a_text, 0xF2);
    int rex = (rexw ? 8 : 0) | ((reg >> 3) & 1) << 2;
    int modrm_rm, mod = 3, sib = -1;
    int32_t disp = 0;
    int dispsz = 0, ripfix = 0;
    if (rm->kind == OP_MEM) {
        disp = rm->disp;
        if (rm->base == -2) { // rip-relative
            mod = 0; modrm_rm = 5; dispsz = 4; ripfix = 1;
        } else {
            int base = rm->base;
            if (rm->index >= 0) {
                int ss = rm->scale == 8 ? 3 : rm->scale == 4 ? 2 : rm->scale == 2 ? 1 : 0;
                sib = (ss << 6) | ((rm->index & 7) << 3) | (base & 7);
                rex |= ((rm->index >> 3) & 1) << 1;
                modrm_rm = 4;
            } else if ((base & 7) == 4) { // rsp/r12 need a SIB
                sib = (0 << 6) | (4 << 3) | (base & 7);
                modrm_rm = 4;
            } else {
                modrm_rm = base & 7;
            }
            rex |= (base >> 3) & 1;
            if (disp == 0 && (base & 7) != 5) { mod = 0; dispsz = 0; }
            else if (disp >= -128 && disp <= 127) { mod = 1; dispsz = 1; }
            else { mod = 2; dispsz = 4; }
        }
    } else { // register
        modrm_rm = rm->reg & 7;
        rex |= (rm->reg >> 3) & 1;
        mod = 3;
    }
    if (rex) bput8(&a_text, 0x40 | rex);
    for (int i = 0; i < nopc; i++) bput8(&a_text, opc[i]);
    bput8(&a_text, (mod << 6) | ((reg & 7) << 3) | modrm_rm);
    if (sib >= 0) bput8(&a_text, sib);
    if (ripfix) {
        add_fix(FX_REL32, sym_intern(rm->sym), disp - g_trail);
        bput32(&a_text, 0);
    } else if (dispsz == 1) bput8(&a_text, disp & 0xff);
    else if (dispsz == 4) bput32(&a_text, (uint32_t)disp);
    g_trail = 0;
}

static void enc_rr(int rexw, const unsigned char* opc, int nopc, int reg, int rmreg,
                   int pfx66, int pfxF2) {
    Op rm = { .kind = OP_REG, .reg = rmreg };
    enc_rm(rexw, opc, nopc, reg, &rm, pfx66, pfxF2);
}

static int cc_code(const char* cc) { // condition nibble for 0F 9x / 0F 8x
    if (strcmp(cc, "e") == 0) return 0x4;
    if (strcmp(cc, "ne") == 0) return 0x5;
    if (strcmp(cc, "l") == 0) return 0xC;
    if (strcmp(cc, "le") == 0) return 0xE;
    if (strcmp(cc, "g") == 0) return 0xF;
    if (strcmp(cc, "ge") == 0) return 0xD;
    if (strcmp(cc, "a") == 0) return 0x7;
    if (strcmp(cc, "ae") == 0) return 0x3;
    if (strcmp(cc, "b") == 0) return 0x2;
    if (strcmp(cc, "be") == 0) return 0x6;
    if (strcmp(cc, "p") == 0) return 0xA;
    if (strcmp(cc, "np") == 0) return 0xB;
    return -1;
}

// add/sub/cmp/and/or/xor share the classic ALU encoding pattern
typedef struct { const char* name; int opc_rm_r, opc_r_rm, ext; } Alu;
static const Alu ALUS[] = {
    { "add", 0x01, 0x03, 0 }, { "or", 0x09, 0x0B, 1 }, { "and", 0x21, 0x23, 4 },
    { "sub", 0x29, 0x2B, 5 }, { "xor", 0x31, 0x33, 6 }, { "cmp", 0x39, 0x3B, 7 },
};

static void asm_ins(const char* mn, Op* a, Op* b, Op* c, int nops) {
    unsigned char opc[3];
    if (strcmp(mn, "push") == 0) {
        if (a->reg >= 8) bput8(&a_text, 0x41);
        bput8(&a_text, 0x50 + (a->reg & 7));
        return;
    }
    if (strcmp(mn, "pop") == 0) {
        if (a->reg >= 8) bput8(&a_text, 0x41);
        bput8(&a_text, 0x58 + (a->reg & 7));
        return;
    }
    if (strcmp(mn, "ret") == 0) { bput8(&a_text, 0xC3); return; }
    if (strcmp(mn, "cqo") == 0) { bput8(&a_text, 0x48); bput8(&a_text, 0x99); return; }
    if (strcmp(mn, "movabs") == 0) {
        int rex = 8 | ((a->reg >> 3) & 1);
        bput8(&a_text, 0x40 | rex);
        bput8(&a_text, 0xB8 + (a->reg & 7));
        bput64(&a_text, (uint64_t)b->imm);
        return;
    }
    if (strcmp(mn, "mov") == 0) {
        if (a->kind == OP_REG && b->kind == OP_IMM) {
            if (a->size == 32) { // mov eax, imm32
                if (a->reg >= 8) bput8(&a_text, 0x41);
                bput8(&a_text, 0xB8 + (a->reg & 7));
                bput32(&a_text, (uint32_t)b->imm);
            } else {
                if (b->imm < -2147483648LL || b->imm > 2147483647LL) asm_die("mov imm too large");
                opc[0] = 0xC7;
                enc_rm(1, opc, 1, 0, a, 0, 0);
                bput32(&a_text, (uint32_t)b->imm);
            }
            return;
        }
        if (a->kind == OP_MEM && b->kind == OP_IMM) { // mov qword ptr [m], imm32
            opc[0] = 0xC7;
            g_trail = 4;
            enc_rm(1, opc, 1, 0, a, 0, 0);
            bput32(&a_text, (uint32_t)b->imm);
            return;
        }
        if (a->kind == OP_REG && b->kind == OP_REG) { opc[0] = 0x89; enc_rr(1, opc, 1, b->reg, a->reg, 0, 0); return; }
        if (a->kind == OP_REG && b->kind == OP_MEM) { opc[0] = 0x8B; enc_rm(1, opc, 1, a->reg, b, 0, 0); return; }
        if (a->kind == OP_MEM && b->kind == OP_REG) { // store; honor source width
            opc[0] = b->size == 8 ? 0x88 : 0x89;
            enc_rm(b->size == 64, opc, 1, b->reg, a, 0, 0);
            return;
        }
        asm_die("unsupported mov form");
    }
    for (size_t k = 0; k < sizeof ALUS / sizeof ALUS[0]; k++) {
        if (strcmp(mn, ALUS[k].name) != 0) continue;
        const Alu* al = &ALUS[k];
        int w = a->size != 32 && a->size != 8;
        if (b->kind == OP_IMM) {
            if (b->imm < -2147483648LL || b->imm > 2147483647LL) asm_die("alu imm too large");
            opc[0] = a->size == 8 ? 0x80 : 0x81;
            g_trail = a->size == 8 ? 1 : 4;
            enc_rm(w, opc, 1, al->ext, a, 0, 0);
            if (a->size == 8) bput8(&a_text, (int)b->imm & 0xff);
            else bput32(&a_text, (uint32_t)b->imm);
            return;
        }
        if (a->kind == OP_REG && b->kind == OP_MEM) { opc[0] = al->opc_r_rm; enc_rm(w, opc, 1, a->reg, b, 0, 0); return; }
        if (b->kind == OP_REG) { // reg/mem, reg
            opc[0] = a->size == 8 ? al->opc_rm_r - 1 : al->opc_rm_r;
            enc_rm(w, opc, 1, b->reg, a, 0, 0);
            return;
        }
        asm_die("unsupported alu form");
    }
    if (strcmp(mn, "test") == 0) { opc[0] = 0x85; enc_rr(1, opc, 1, b->reg, a->reg, 0, 0); return; }
    if (strcmp(mn, "imul") == 0) {
        if (nops == 1) { opc[0] = 0xF7; enc_rm(1, opc, 1, 5, a, 0, 0); return; }
        if (nops == 3) {
            opc[0] = 0x69;
            enc_rm(1, opc, 1, a->reg, b, 0, 0);
            bput32(&a_text, (uint32_t)c->imm);
            return;
        }
        opc[0] = 0x0F; opc[1] = 0xAF;
        enc_rm(1, opc, 2, a->reg, b, 0, 0);
        return;
    }
    if (strcmp(mn, "idiv") == 0) { opc[0] = 0xF7; enc_rm(1, opc, 1, 7, a, 0, 0); return; }
    if (strcmp(mn, "neg") == 0) { opc[0] = 0xF7; enc_rm(1, opc, 1, 3, a, 0, 0); return; }
    if (strcmp(mn, "inc") == 0) { opc[0] = 0xFF; enc_rm(1, opc, 1, 0, a, 0, 0); return; }
    if (strcmp(mn, "sar") == 0 || strcmp(mn, "shl") == 0) {
        int ext = mn[1] == 'a' ? 7 : 4;
        if (b->kind == OP_REG) { // shift by cl
            opc[0] = 0xD3;
            enc_rm(1, opc, 1, ext, a, 0, 0);
        } else {
            opc[0] = 0xC1;
            g_trail = 1;
            enc_rm(1, opc, 1, ext, a, 0, 0);
            bput8(&a_text, (int)b->imm & 0xff);
        }
        return;
    }
    if (strcmp(mn, "movzx") == 0) { // movzx eax, r8 / byte ptr [m]
        opc[0] = 0x0F; opc[1] = 0xB6;
        enc_rm(0, opc, 2, a->reg, b, 0, 0);
        return;
    }
    if (strcmp(mn, "lea") == 0) { opc[0] = 0x8D; enc_rm(1, opc, 1, a->reg, b, 0, 0); return; }
    if (strncmp(mn, "set", 3) == 0) {
        int cc = cc_code(mn + 3);
        if (cc < 0) asm_die("bad setcc");
        opc[0] = 0x0F; opc[1] = 0x90 + cc;
        enc_rm(0, opc, 2, 0, a, 0, 0);
        return;
    }
    if (strcmp(mn, "jmp") == 0) {
        bput8(&a_text, 0xE9);
        add_fix(FX_REL32, sym_intern(a->sym), 0);
        bput32(&a_text, 0);
        return;
    }
    if (mn[0] == 'j') {
        int cc = cc_code(mn + 1);
        if (cc < 0) asm_die("bad jcc");
        bput8(&a_text, 0x0F);
        bput8(&a_text, 0x80 + cc);
        add_fix(FX_REL32, sym_intern(a->sym), 0);
        bput32(&a_text, 0);
        return;
    }
    if (strcmp(mn, "call") == 0) {
        if (strncmp(a->sym, "__imp_k_", 8) == 0) { // kernel32 import, indirect
            bput8(&a_text, 0xFF);
            bput8(&a_text, 0x15);
            add_fix(FX_IAT32, import_intern2(a->sym + 8, 1), 0);
            bput32(&a_text, 0);
        } else if (strncmp(a->sym, "rt_", 3) == 0 && !sym_is_local(a->sym)) {
            // rt_* with no local definition: import it from zephyr_rt.dll (indirect)
            bput8(&a_text, 0xFF);
            bput8(&a_text, 0x15);
            add_fix(FX_IAT32, import_intern(a->sym), 0);
            bput32(&a_text, 0);
        } else {                            // local function: direct rel32 call
            bput8(&a_text, 0xE8);
            add_fix(FX_REL32, sym_intern(a->sym), 0);
            bput32(&a_text, 0);
        }
        return;
    }
    if (strcmp(mn, "movq") == 0) {
        opc[0] = 0x0F;
        if (a->kind == OP_XMM) { opc[1] = 0x6E; enc_rm(1, opc, 2, a->reg, b, 1, 0); }
        else { opc[1] = 0x7E; enc_rm(1, opc, 2, b->reg, a, 1, 0); }
        return;
    }
    {
        static const struct { const char* n; int op; int pfx; } SSE[] = {
            { "addsd", 0x58, 0xF2 }, { "subsd", 0x5C, 0xF2 }, { "mulsd", 0x59, 0xF2 },
            { "divsd", 0x5E, 0xF2 }, { "sqrtsd", 0x51, 0xF2 },
            { "comisd", 0x2F, 0x66 }, { "ucomisd", 0x2E, 0x66 },
        };
        for (size_t k = 0; k < sizeof SSE / sizeof SSE[0]; k++) {
            if (strcmp(mn, SSE[k].n) != 0) continue;
            opc[0] = 0x0F; opc[1] = (unsigned char)SSE[k].op;
            Op rm = { .kind = OP_REG, .reg = b->reg };
            enc_rm(0, opc, 2, a->reg, &rm, SSE[k].pfx == 0x66, SSE[k].pfx == 0xF2);
            return;
        }
    }
    if (strcmp(mn, "cvtsi2sd") == 0) {
        opc[0] = 0x0F; opc[1] = 0x2A;
        Op rm = { .kind = OP_REG, .reg = b->reg };
        enc_rm(1, opc, 2, a->reg, &rm, 0, 1);
        return;
    }
    if (strcmp(mn, "cvttsd2si") == 0) {
        opc[0] = 0x0F; opc[1] = 0x2C;
        Op rm = { .kind = OP_REG, .reg = b->reg };
        enc_rm(1, opc, 2, a->reg, &rm, 0, 1);
        return;
    }
    asm_die("unknown mnemonic");
}

static void asm_line(const char* line) {
    a_curline = line;
    if (!line[0]) return;
    if (line[0] != ' ') { // label or directive at column 0
        if (line[0] == '.') {
            if (strncmp(line, ".section .rdata", 15) == 0) a_sect = S_RDATA;
            else if (strncmp(line, ".section .bss", 13) == 0) a_sect = S_BSS;
            else if (strcmp(line, ".text") == 0) a_sect = S_TEXT;
            else if (strncmp(line, ".balign", 7) == 0) {
                int al = atoi(line + 8);
                if (a_sect == S_RDATA) while (a_rdata.len % al) bput8(&a_rdata, 0);
                else if (a_sect == S_BSS) while (a_bss % al) a_bss++;
            }
            else if (strncmp(line, ".intel_syntax", 13) == 0 || strncmp(line, ".globl", 6) == 0) {}
            else if (line[strlen(line) - 1] == ':') goto label; // .L labels
            else asm_die("unknown directive");
            return;
        }
    label:;
        char name[80];
        size_t n = strlen(line);
        if (line[n - 1] != ':') asm_die("expected label");
        if (n - 1 >= sizeof name) asm_die("label too long");
        memcpy(name, line, n - 1);
        name[n - 1] = 0;
        int si = sym_intern(name);
        ASym* s = a_syms.items[si];
        if (s->defined) asm_die("duplicate label");
        s->defined = 1;
        s->sect = a_sect;
        s->off = a_sect == S_TEXT ? (uint32_t)a_text.len
               : a_sect == S_RDATA ? (uint32_t)a_rdata.len : a_bss;
        return;
    }
    const char* p = line + 2;
    if (p[0] == '.') { // data directives
        if (strncmp(p, ".quad ", 6) == 0) {
            const char* v = p + 6;
            if ((*v >= '0' && *v <= '9') || *v == '-') {
                bput64(&a_rdata, (uint64_t)strtoll(v, NULL, 10));
            } else {
                add_fix(FX_ABS64, sym_intern(v), 0);
                bput64(&a_rdata, 0);
            }
            return;
        }
        if (strncmp(p, ".byte ", 6) == 0) {
            BBuf* dst = a_sect == S_TEXT ? &a_text : &a_rdata;  // raw bytes into either section
            const char* v = p + 6;
            while (*v) {
                bput8(dst, atoi(v));
                while (*v && *v != ',') v++;
                if (*v == ',') v++;
            }
            return;
        }
        if (strncmp(p, ".space ", 7) == 0) { a_bss += (uint32_t)atoi(p + 7); return; }
        asm_die("unknown data directive");
    }
    // instruction: mnemonic + comma-separated operands
    char mn[16];
    int ml = 0;
    while (*p && *p != ' ' && ml < 15) mn[ml++] = *p++;
    mn[ml] = 0;
    while (*p == ' ') p++;
    Op ops[3];
    int nops = 0;
    while (*p && nops < 3) {
        char opt[128];
        int ol = 0, depth = 0;
        while (*p && (depth > 0 || *p != ',') && ol < 127) {
            if (*p == '[') depth++;
            if (*p == ']') depth--;
            opt[ol++] = *p++;
        }
        while (ol > 0 && opt[ol - 1] == ' ') ol--;
        opt[ol] = 0;
        if (*p == ',') p++;
        while (*p == ' ') p++;
        parse_operand(opt, &ops[nops++]);
    }
    asm_ins(mn, nops > 0 ? &ops[0] : NULL, nops > 1 ? &ops[1] : NULL,
            nops > 2 ? &ops[2] : NULL, nops);
}

// ---------------- PE writer ----------------
#define IMAGE_BASE 0x140000000ULL

static uint32_t pe_align(uint32_t v, uint32_t a) { return (v + a - 1) & ~(a - 1); }

static void wr(FILE* f, const void* p, size_t n) { fwrite(p, 1, n, f); }
static void w2(FILE* f, uint16_t v) { wr(f, &v, 2); }
static void w4(FILE* f, uint32_t v) { wr(f, &v, 4); }
static void w8f(FILE* f, uint64_t v) { wr(f, &v, 8); }

static void write_pe(const char* path) {
    // runtime mode: the runtime is compiled in as Zephyr; depend only on kernel32
    int rt_mode = sym_is_local("rt_alloc");
    uint32_t entry_off = (uint32_t)a_text.len;
    a_sect = S_TEXT;
    if (rt_mode) {
        bput8(&a_text, 0x48); bput8(&a_text, 0x83); bput8(&a_text, 0xEC); bput8(&a_text, 0x28); // sub rsp,40
        bput8(&a_text, 0xE8); add_fix(FX_REL32, sym_intern("zephyr_main"), 0); bput32(&a_text, 0);  // call zephyr_main
        bput8(&a_text, 0x31); bput8(&a_text, 0xC9);                                               // xor ecx,ecx
        bput8(&a_text, 0xFF); bput8(&a_text, 0x15);
        add_fix(FX_IAT32, import_intern2("ExitProcess", 1), 0); bput32(&a_text, 0);               // call ExitProcess
        bput8(&a_text, 0xCC);
    } else {
        // stub: lea rcx,[rip+zephyr_main]; sub rsp,40; call [rip+IAT rt_start]; int3
        bput8(&a_text, 0x48); bput8(&a_text, 0x8D); bput8(&a_text, 0x0D);
        add_fix(FX_REL32, sym_intern("zephyr_main"), 0);
        bput32(&a_text, 0);
        bput8(&a_text, 0x48); bput8(&a_text, 0x83); bput8(&a_text, 0xEC); bput8(&a_text, 0x28);
        bput8(&a_text, 0xFF); bput8(&a_text, 0x15);
        add_fix(FX_IAT32, import_intern("rt_start"), 0);
        bput32(&a_text, 0);
        bput8(&a_text, 0xCC);
    }

    // import area layout (start of .rdata section), grouped by DLL — only DLLs
    // that actually have imports get a descriptor
    int nimp = a_imports.len;
    const char* dll_names_all[2] = { "zephyr_rt.dll", "kernel32.dll" };
    int used[2] = {0, 0};
    for (int i = 0; i < nimp; i++) used[((AImport*)a_imports.items[i])->dll] = 1;
    int dmap[2], ndll = 0;                 // ordered list of present DLL ids
    const char* dll_names[2];
    for (int d = 0; d < 2; d++) if (used[d]) { dll_names[ndll] = dll_names_all[d]; dmap[ndll++] = d; }
    int* slot = xmalloc(sizeof(int) * (nimp ? nimp : 1)); // IAT entry index per import
    int grp_start[2] = {0, 0};
    int nentries = 0;
    for (int gi = 0; gi < ndll; gi++) {
        int d = dmap[gi];
        grp_start[gi] = nentries;
        for (int i = 0; i < nimp; i++)
            if (((AImport*)a_imports.items[i])->dll == d) { slot[i] = nentries++; }
        nentries++; // per-DLL null terminator
    }
    uint32_t idt_sz = (uint32_t)(ndll + 1) * 20;
    uint32_t ilt_off = idt_sz;
    uint32_t iat_off = ilt_off + 8 * (uint32_t)nentries;
    uint32_t names_off = iat_off + 8 * (uint32_t)nentries;
    uint32_t* name_offs = xmalloc(sizeof(uint32_t) * (nimp ? nimp : 1));
    uint32_t no = names_off;
    for (int i = 0; i < nimp; i++) {
        name_offs[i] = no;
        no += 2 + (uint32_t)strlen(((AImport*)a_imports.items[i])->name) + 1;
        if (no & 1) no++;
    }
    uint32_t dll_off[2];
    for (int d = 0; d < ndll; d++) { dll_off[d] = no; no += (uint32_t)strlen(dll_names[d]) + 1; }
    uint32_t idata_size = pe_align(no, 16);

    // section layout
    uint32_t text_rva = 0x1000;
    uint32_t text_size = (uint32_t)a_text.len;
    uint32_t rdata_rva = pe_align(text_rva + text_size, 0x1000);
    uint32_t data_off = idata_size;                 // program rdata after imports
    uint32_t rdata_size = idata_size + (uint32_t)a_rdata.len;
    uint32_t bss_rva = pe_align(rdata_rva + rdata_size, 0x1000);
    int have_bss = a_bss > 0;
    uint32_t image_size = pe_align(bss_rva + (have_bss ? a_bss : 0), 0x1000);
    uint32_t iat_rva = rdata_rva + iat_off;

    // resolve fixups
    for (int i = 0; i < a_fixes.len; i++) {
        AFix* fx = a_fixes.items[i];
        uint64_t target;
        if (fx->kind == FX_IAT32) {
            target = iat_rva + 8 * (uint32_t)slot[fx->sym];
        } else {
            ASym* s = a_syms.items[fx->sym];
            if (!s->defined) {
                fprintf(stderr, "internal assembler error: undefined symbol '%s'\n", s->name);
                exit(1);
            }
            target = (s->sect == S_TEXT ? text_rva : s->sect == S_RDATA ? rdata_rva + data_off : bss_rva)
                   + s->off;
        }
        if (fx->kind == FX_ABS64) {
            uint64_t v = IMAGE_BASE + target;
            memcpy(a_rdata.p + fx->off, &v, 8);
        } else { // rel32 forms, always patched in .text
            int32_t rel = (int32_t)((int64_t)(target + fx->addend) -
                                    (int64_t)(text_rva + fx->off + 4));
            memcpy(a_text.p + fx->off, &rel, 4);
        }
    }

    FILE* f = fopen(path, "wb");
    if (!f) { fprintf(stderr, "error: cannot write '%s'\n", path); exit(2); }
    int nsect = have_bss ? 3 : 2;
    uint32_t hdrs_size = 0x400;
    uint32_t text_raw = hdrs_size;
    uint32_t rdata_raw = text_raw + pe_align(text_size, 0x200);
    uint32_t file_size = rdata_raw + pe_align(rdata_size, 0x200);

    // DOS header
    unsigned char dos[64] = { 'M', 'Z' };
    dos[0x3C] = 0x40;
    wr(f, dos, 64);
    w4(f, 0x00004550);                  // "PE\0\0"
    w2(f, 0x8664); w2(f, (uint16_t)nsect);
    w4(f, 0); w4(f, 0); w4(f, 0);       // timestamp, symtab, nsyms
    w2(f, 240); w2(f, 0x0022);          // opt hdr size, EXE | large-address-aware
    // optional header
    w2(f, 0x20B); w2(f, 0x0100);        // PE32+, linker version
    w4(f, pe_align(text_size, 0x200)); w4(f, pe_align(rdata_size, 0x200)); w4(f, 0);
    w4(f, text_rva + entry_off);        // entry point
    w4(f, text_rva);
    w8f(f, IMAGE_BASE);
    w4(f, 0x1000); w4(f, 0x200);        // section, file alignment
    w2(f, 6); w2(f, 0);                 // OS version 6.0
    w2(f, 0); w2(f, 0);
    w2(f, 6); w2(f, 0);                 // subsystem version 6.0
    w4(f, 0);
    w4(f, image_size); w4(f, hdrs_size);
    w4(f, 0);                           // checksum
    w2(f, 3);                           // console subsystem
    w2(f, 0x8100);                      // NX compatible, TS aware; no ASLR (abs64 data)
    w8f(f, 0x800000); w8f(f, 0x10000);  // stack reserve/commit
    w8f(f, 0x100000); w8f(f, 0x1000);   // heap reserve/commit
    w4(f, 0); w4(f, 16);                // loader flags, dir count
    for (int i = 0; i < 16; i++) {      // data directories
        if (i == 1) { w4(f, rdata_rva); w4(f, idt_sz); }
        else if (i == 12) { w4(f, iat_rva); w4(f, 8 * (uint32_t)nentries); }
        else { w4(f, 0); w4(f, 0); }
    }
    // section headers
    struct { const char* name; uint32_t vsz, rva, rsz, raw, chr; } sects[3] = {
        { ".text", text_size, text_rva, pe_align(text_size, 0x200), text_raw, 0x60000020 },
        { ".rdata", rdata_size, rdata_rva, pe_align(rdata_size, 0x200), rdata_raw, 0x40000040 },
        { ".bss", a_bss, bss_rva, 0, 0, 0xC0000080 },
    };
    for (int i = 0; i < nsect; i++) {
        char nm[8] = {0};
        memcpy(nm, sects[i].name, strlen(sects[i].name));
        wr(f, nm, 8);
        w4(f, sects[i].vsz); w4(f, sects[i].rva);
        w4(f, sects[i].rsz); w4(f, sects[i].raw);
        w4(f, 0); w4(f, 0); w4(f, 0);
        w4(f, sects[i].chr);
    }
    // pad to headers size, write .text
    for (long pos = ftell(f); pos < (long)text_raw; pos++) fputc(0, f);
    wr(f, a_text.p, a_text.len);
    for (long pos = ftell(f); pos < (long)rdata_raw; pos++) fputc(0, f);
    // .rdata: import structures first
    {
        BBuf id = {0};
        // import descriptor table: one entry per DLL, then a null entry
        for (int d = 0; d < ndll; d++) {
            bput32(&id, rdata_rva + ilt_off + 8 * (uint32_t)grp_start[d]); // OriginalFirstThunk
            bput32(&id, 0); bput32(&id, 0);                               // timestamp, forwarder
            bput32(&id, rdata_rva + dll_off[d]);                          // Name
            bput32(&id, rdata_rva + iat_off + 8 * (uint32_t)grp_start[d]); // FirstThunk
        }
        for (int i = 0; i < 5; i++) bput32(&id, 0);                       // null descriptor
        // ILT then IAT (identical on disk), grouped by DLL with null terminators
        for (int pass = 0; pass < 2; pass++) {
            for (int gi = 0; gi < ndll; gi++) {
                for (int i = 0; i < nimp; i++)
                    if (((AImport*)a_imports.items[i])->dll == dmap[gi])
                        bput64(&id, rdata_rva + name_offs[i]);
                bput64(&id, 0);
            }
        }
        for (int i = 0; i < nimp; i++) {
            bput8(&id, 0); bput8(&id, 0); // hint
            const char* nmi = ((AImport*)a_imports.items[i])->name;
            do bput8(&id, *nmi); while (*nmi++);
            if (id.len & 1) bput8(&id, 0);
        }
        for (int d = 0; d < ndll; d++) {
            const char* dn = dll_names[d];
            do bput8(&id, *dn); while (*dn++);
        }
        while (id.len < idata_size) bput8(&id, 0);
        wr(f, id.p, id.len);
        free(id.p);
    }
    wr(f, a_rdata.p, a_rdata.len);
    for (long pos = ftell(f); pos < (long)file_size; pos++) fputc(0, f);
    fclose(f);
    free(name_offs);
}

// pre-scan: mark every defined label so `call rt_X` can pick local-vs-import
static void asm_prescan(void) {
    for (int i = 0; i < g_alines.len; i++) {
        const char* l = g_alines.items[i];
        if (!l[0] || l[0] == ' ' || l[0] == '.') continue;
        size_t n = strlen(l);
        if (l[n - 1] != ':') continue;
        int ok = (l[0] == '_' || (l[0] >= 'A' && l[0] <= 'Z') || (l[0] >= 'a' && l[0] <= 'z'));
        for (size_t k = 1; k < n - 1 && ok; k++)
            if (!(l[k] == '_' || (l[k] >= 'A' && l[k] <= 'Z') || (l[k] >= 'a' && l[k] <= 'z') ||
                  (l[k] >= '0' && l[k] <= '9'))) ok = 0;
        if (!ok) continue;
        char name[80];
        if (n - 1 >= sizeof name) continue;
        memcpy(name, l, n - 1);
        name[n - 1] = 0;
        int si = sym_intern(name);       // sequence before the index: sym_intern
        ((ASym*)a_syms.items[si])->predef = 1; // reallocs a_syms.items via vpush
    }
}

static void assemble_and_link(const char* exepath) {
    a_sect = S_TEXT;
    asm_prescan();
    for (int i = 0; i < g_alines.len; i++) asm_line(g_alines.items[i]);
    write_pe(exepath);
}

// ---------------- driver ----------------
static char* read_file(const char* path) {
    FILE* f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "error: cannot read '%s'\n", path); exit(2); }
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    char* buf = xmalloc(n + 1);
    if (n && fread(buf, 1, n, f) != (size_t)n) { fprintf(stderr, "error: read failed\n"); exit(2); }
    fclose(f);
    return buf;
}

static void exe_dir(char* buf, size_t cap) {
#ifdef _WIN32
    GetModuleFileNameA(NULL, buf, (DWORD)cap);
    char* slash = strrchr(buf, '\\');
    if (slash) *slash = 0;
#else
    strcpy(buf, ".");
#endif
}

int main(int argc, char** argv) {
    const char* usage = "usage: zephyr <run|build|check> file.zeph [-o out.exe] [-S] [--gcc] [--rt]\n";
    if (argc < 3) { fputs(usage, stderr); return 2; }
    const char* cmd = argv[1];
    const char* file = argv[2];
    int keep_asm = 0, use_gcc = 0, rt_zephyr = 0;
    const char* outpath = NULL;
    for (int i = 3; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) outpath = argv[++i];
        else if (strcmp(argv[i], "-S") == 0) keep_asm = 1;
        else if (strcmp(argv[i], "--gcc") == 0) use_gcc = 1;
        else if (strcmp(argv[i], "--rt") == 0) rt_zephyr = 1;   // link the Zephyr runtime (kernel32 only)
        else { fputs(usage, stderr); return 2; }
    }
    int is_run = strcmp(cmd, "run") == 0, is_build = strcmp(cmd, "build") == 0,
        is_check = strcmp(cmd, "check") == 0;
    if (!is_run && !is_build && !is_check) { fputs(usage, stderr); return 2; }

    g_file = file;
    char* src = read_file(file);
    int nlines = 1;
    for (char* p = src; *p; p++) if (*p == '\n') nlines++;

    clock_t t0 = clock();
    int ntoks;
    Tok* toks = lex(src, 1, &ntoks);
    Node* prog = parse(toks, ntoks);
    if (rt_zephyr) {
        // prepend the Zephyr runtime's declarations so rt_* resolve locally
        char rtsrc[1024];
        exe_dir(rtsrc, sizeof rtsrc - 32);
        strcat(rtsrc, "\\runtime.zeph");
        FILE* rf = fopen(rtsrc, "rb");
        if (!rf) { fprintf(stderr, "error: runtime.zeph not found next to zephyr.exe (%s)\n", rtsrc); return 2; }
        fclose(rf);
        const char* saved = g_file;
        g_file = rtsrc;
        char* rtext = read_file(rtsrc);
        int rtn;
        Tok* rttoks = lex(rtext, 1, &rtn);
        Node* rtprog = parse(rttoks, rtn);
        g_file = saved;
        Vec merged = {0};
        for (int i = 0; i < rtprog->kids.len; i++) {
            Node* n = rtprog->kids.items[i];
            if (n->k != N_FN && n->k != N_STRUCTDEF) g_rt_top++;
            vpush(&merged, n);
        }
        for (int i = 0; i < prog->kids.len; i++) vpush(&merged, prog->kids.items[i]);
        prog->kids = merged;
    }
    check(prog);
    demote_globals(prog);
    inline_pass(prog);
    //licm_pass(prog); // removed: buggy, and AXPY matcher does not need it
    double front_ms = (clock() - t0) * 1000.0 / CLOCKS_PER_SEC;

    if (is_check) {
        printf("ok: %s (%d lines, %.1f ms)\n", file, nlines, front_ms);
        return 0;
    }

    // output paths
    char exepath[1024], spath[1024];
    if (outpath) snprintf(exepath, sizeof exepath, "%s", outpath);
    else {
        snprintf(exepath, sizeof exepath, "%s", file);
        char* dot = strrchr(exepath, '.');
        if (dot && strcmp(dot, ".zeph") == 0) *dot = 0;
        strcat(exepath, ".exe");
    }
    snprintf(spath, sizeof spath, "%s.s", exepath);

    gen_program(prog);
    if (keep_asm || use_gcc) {
        g_out = fopen(spath, "wb");
        if (!g_out) { fprintf(stderr, "error: cannot write '%s'\n", spath); return 2; }
        for (int i = 0; i < g_alines.len; i++) {
            fputs(g_alines.items[i], g_out);
            fputc('\n', g_out);
        }
        fclose(g_out);
    }

    if (use_gcc) {
        double gen_ms = (clock() - t0) * 1000.0 / CLOCKS_PER_SEC;
        char rtpath[1024];
        exe_dir(rtpath, sizeof rtpath - 32);
        strcat(rtpath, "\\runtime.o");
        FILE* rt = fopen(rtpath, "rb");
        if (!rt) {
            fprintf(stderr, "error: runtime.o not found next to zephyr.exe (%s)\n"
                            "build it with: gcc -O2 -c src/runtime.c -o runtime.o\n", rtpath);
            return 2;
        }
        fclose(rt);
        clock_t t1 = clock();
        intptr_t rc = _spawnlp(_P_WAIT, "gcc", "gcc", spath, rtpath, "-o", exepath, NULL);
        if (rc == -1) { fprintf(stderr, "error: could not run gcc (is it on PATH?)\n"); return 2; }
        if (rc != 0) { fprintf(stderr, "error: assembler/linker failed (%d)\n", (int)rc); return 1; }
        double link_ms = (clock() - t1) * 1000.0 / CLOCKS_PER_SEC;
        if (!keep_asm) remove(spath);
        if (is_build) {
            printf("built %s (compile %.1f ms + assemble/link %.0f ms)\n", exepath, gen_ms, link_ms);
            return 0;
        }
        fflush(stdout);
        intptr_t code = _spawnl(_P_WAIT, exepath, exepath, NULL);
        if (code == -1) { fprintf(stderr, "error: could not run %s\n", exepath); return 2; }
        return (int)code;
    }

    // built-in assembler + PE linker: no external toolchain
    assemble_and_link(exepath);
    double total_ms = (clock() - t0) * 1000.0 / CLOCKS_PER_SEC;

    // programs link against zephyr_rt.dll: put a copy next to the output
    // (skipped with --rt: the runtime is compiled in, only kernel32 is needed)
    if (!rt_zephyr) {
        char dllsrc[1024], dlldst[1024];
        exe_dir(dllsrc, sizeof dllsrc - 32);
        strcat(dllsrc, "\\zephyr_rt.dll");
        snprintf(dlldst, sizeof dlldst, "%s", exepath);
        char* slash = strrchr(dlldst, '\\');
        char* fslash = strrchr(dlldst, '/');
        if (fslash > slash) slash = fslash;
        if (slash) { slash[1] = 0; strcat(dlldst, "zephyr_rt.dll"); }
        else snprintf(dlldst, sizeof dlldst, "zephyr_rt.dll");
        if (_stricmp(dllsrc, dlldst) != 0) {
            if (!CopyFileA(dllsrc, dlldst, FALSE)) {
                fprintf(stderr, "error: cannot copy %s next to the output\n"
                                "build it with: gcc -O2 -shared src/runtime.c -o zephyr_rt.dll\n", dllsrc);
                return 2;
            }
        }
    }

    if (is_build) {
        printf("built %s (%.1f ms, built-in assembler)\n", exepath, total_ms);
        return 0;
    }
    // run
    fflush(stdout);
    intptr_t code = _spawnl(_P_WAIT, exepath, exepath, NULL);
    if (code == -1) { fprintf(stderr, "error: could not run %s\n", exepath); return 2; }
    return (int)code;
}
