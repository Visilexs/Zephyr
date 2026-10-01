/* Oracle (M44): bench/wordfreq.c (revision 398aadd) with one heap string per
   concatenation, as Zephyr builds words today. Everything else unchanged. */
/* String-keyed hash-map benchmark: C reference for bench/wordfreq.zeph.
   Words are built in a stack buffer and counted in an open-addressing
   (linear-probe) string table that doubles at 50% load; keys are copied only
   on first insertion. Same LCG, same checksum.
   Build: gcc -O2 wordfreq.c -o wordfreq
   Usage: wordfreq [words] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

static uint64_t wordHash(const char *word, size_t length) {
    uint64_t hash = 7;
    for (size_t i = 0; i < length; i++) hash = hash * 31 + (unsigned char)word[i];
    return hash;
}

static uint64_t tableHash(const char *word, size_t length) {
    uint64_t hash = 14695981039346656037ULL; /* FNV-1a */
    for (size_t i = 0; i < length; i++) hash = (hash ^ (unsigned char)word[i]) * 1099511628211ULL;
    return hash;
}

typedef struct Entry { char *key; size_t length; uint64_t hash; long long frequency; } Entry;
typedef struct Table { Entry *entries; size_t capacity, used; } Table;

static void tableGrow(Table *table) {
    size_t newCapacity = table->capacity * 2;
    Entry *newEntries = calloc(newCapacity, sizeof *newEntries);
    for (size_t i = 0; i < table->capacity; i++) {
        Entry *entry = &table->entries[i];
        if (!entry->key) continue;
        size_t slot = entry->hash & (newCapacity - 1);
        while (newEntries[slot].key) slot = (slot + 1) & (newCapacity - 1);
        newEntries[slot] = *entry;
    }
    free(table->entries);
    table->entries = newEntries;
    table->capacity = newCapacity;
}

static void tableIncrement(Table *table, const char *word, size_t length) {
    uint64_t hash = tableHash(word, length);
    size_t slot = hash & (table->capacity - 1);
    for (;;) {
        Entry *entry = &table->entries[slot];
        if (!entry->key) break;
        if (entry->hash == hash && entry->length == length && memcmp(entry->key, word, length) == 0) {
            entry->frequency++;
            return;
        }
        slot = (slot + 1) & (table->capacity - 1);
    }
    Entry *entry = &table->entries[slot];
    entry->key = malloc(length);
    memcpy(entry->key, word, length);
    entry->length = length;
    entry->hash = hash;
    entry->frequency = 1;
    if (++table->used * 2 > table->capacity) tableGrow(table);
}

int main(int argc, char **argv) {
    long long wordCount = argc > 1 ? atoll(argv[1]) : 3000000;
    static const char *const syllables[16] = { "ka", "lo", "mi", "ne", "ru", "sa", "to", "vi", "ze", "po", "an", "el", "or", "ust", "ing", "ble" };
    size_t syllableLengths[16];
    for (int i = 0; i < 16; i++) syllableLengths[i] = strlen(syllables[i]);

    Table table = { calloc(1024, sizeof(Entry)), 1024, 0 };
    char word[64];
    for (long long i = 0; i < wordCount; i++) {
        long long syllableCount = nextRandom() % 4 + 1;
        // Oracle (M44): Zephyr's representation, one new heap string per
        // concatenation (24-byte header + length + bytes), the old one freed.
        size_t length = 0;
        char *heapWord = NULL;
        for (long long j = 0; j < syllableCount; j++) {
            long long syllableIndex = nextRandom() % 16;
            size_t add = syllableLengths[syllableIndex];
            char *next = malloc(32 + length + add);
            if (heapWord) memcpy(next + 32, heapWord + 32, length);
            memcpy(next + 32 + length, syllables[syllableIndex], add);
            free(heapWord);
            heapWord = next; length += add;
        }
        tableIncrement(&table, heapWord + 32, length);
        free(heapWord);
        (void)word;
    }

    uint64_t checksum = 0;
    for (size_t i = 0; i < table.capacity; i++) {
        Entry *entry = &table.entries[i];
        if (entry->key) checksum += (uint64_t)entry->frequency * wordHash(entry->key, entry->length);
    }
    printf("%zu %lld\n", table.used, (long long)checksum);
    return 0;
}
