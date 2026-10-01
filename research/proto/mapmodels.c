// wordfreq (bench/wordfreq.zeph at revision 398aadd) under two string/map
// designs, same word stream and checksum:
//   today   Zephyr's representation: every concatenation allocates a new
//           counted string (24-byte header + length word + bytes, copied), the
//           table slot is {state, key pointer, value} with no stored hash, and
//           each probe compares through the key pointer. Hashing is
//           word-at-a-time, as in runtimeHashString.
//   redesign the word is built in place in one buffer, slots store the hash,
//           and keys are copied once on first insertion (what the C reference does).
// Build: gcc -O2 -fwrapv -o mapmodels research/proto/mapmodels.c
// Usage: mapmodels today|redesign [words]
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static uint64_t rng = 12345;
static long long nextRandom(void) { rng = rng * 6364136223846793005ULL + 1442695040888963407ULL; return (long long)((rng >> 33) & 2147483647ULL); }
static const char *syl[16] = { "ka", "lo", "mi", "ne", "ru", "sa", "to", "vi", "ze", "po", "an", "el", "or", "ust", "ing", "ble" };

typedef struct Str { int64_t count, descriptor, size, length; char bytes[]; } Str;   // 24-byte header + length
static Str *newStr(size_t n) { Str *s = malloc(sizeof(Str) + ((n + 7) & ~7ul) + 8); s->count = 1; s->descriptor = 1; s->size = n; s->length = (int64_t)n; return s; }
static void dropStr(Str *s) { if (--s->count == 0) free(s); }
static Str *concat(Str *a, const char *b, size_t bn) { Str *s = newStr((size_t)a->length + bn); memcpy(s->bytes, a->bytes, (size_t)a->length); memcpy(s->bytes + a->length, b, bn); return s; }
static uint64_t hashWords(const char *p, size_t n) {   // word-at-a-time, like runtimeHashString
    uint64_t h = n * 0x9E3779B97F4A7C15ull; size_t i = 0;
    for (; i + 8 <= n; i += 8) { uint64_t w; memcpy(&w, p + i, 8); h = (h ^ w) * 0x9E3779B97F4A7C15ull; h ^= h >> 29; }
    if (i < n) { uint64_t w = 0; memcpy(&w, p + i, n - i); h = (h ^ w) * 0x9E3779B97F4A7C15ull; }
    h = (h ^ (h >> 32)) * 0xff51afd7ed558ccdull; return h ^ (h >> 29);
}
static uint64_t wordHash(const char *w, size_t n) { uint64_t h = 7; for (size_t i = 0; i < n; i++) h = h * 31 + (unsigned char)w[i]; return h; }

typedef struct Slot { int64_t state; Str *key; int64_t value; uint64_t hash; } Slot;
static Slot *slots; static size_t capacity = 1024, used;
static int storedHash;

static void grow(void) {
    Slot *old = slots; size_t oc = capacity; capacity *= 2; slots = calloc(capacity, sizeof(Slot));
    for (size_t i = 0; i < oc; i++) if (old[i].state) {
        uint64_t h = storedHash ? old[i].hash : hashWords(old[i].key->bytes, (size_t)old[i].key->length);
        size_t s = h & (capacity - 1); while (slots[s].state) s = (s + 1) & (capacity - 1); slots[s] = old[i];
    }
    free(old);
}
static void increment(const char *w, size_t n, Str *owned) {
    uint64_t h = hashWords(w, n); size_t s = h & (capacity - 1);
    for (; slots[s].state; s = (s + 1) & (capacity - 1)) {
        if (storedHash && slots[s].hash != h) continue;
        Str *k = slots[s].key;
        if ((size_t)k->length == n && memcmp(k->bytes, w, n) == 0) { slots[s].value++; return; }
    }
    Str *key = owned; if (!key) { key = newStr(n); memcpy(key->bytes, w, n); } else key->count++;
    slots[s].state = 1; slots[s].key = key; slots[s].value = 1; slots[s].hash = h;
    if (++used * 2 > capacity) grow();
}

int main(int argc, char **argv) {
    int today = strcmp(argv[1], "today") == 0; storedHash = !today;
    long long words = argc > 2 ? atoll(argv[2]) : 3000000;
    slots = calloc(capacity, sizeof(Slot));
    char buffer[64];
    for (long long i = 0; i < words; i++) {
        long long count = nextRandom() % 4 + 1;
        const char *first = syl[nextRandom() % 16];
        if (today) {
            Str *w = newStr(strlen(first)); memcpy(w->bytes, first, strlen(first));
            for (long long j = 1; j < count; j++) { const char *t = syl[nextRandom() % 16]; Str *n = concat(w, t, strlen(t)); dropStr(w); w = n; }
            increment(w->bytes, (size_t)w->length, w);
            dropStr(w);
        } else {
            size_t n = strlen(first); memcpy(buffer, first, n);
            for (long long j = 1; j < count; j++) { const char *t = syl[nextRandom() % 16]; size_t m = strlen(t); memcpy(buffer + n, t, m); n += m; }
            increment(buffer, n, 0);
        }
    }
    long long checksum = 0;
    for (size_t s = 0; s < capacity; s++) if (slots[s].state) checksum += slots[s].value * (long long)wordHash(slots[s].key->bytes, (size_t)slots[s].key->length);
    printf("%zu %lld\n", used, checksum);
    return 0;
}
