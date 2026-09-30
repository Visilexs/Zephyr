/* String building and slicing benchmark: C reference for bench/strbuild.zeph.
   Each line is built in a freshly malloc'd buffer with snprintf appends;
   fields are viewed in place as pointer + length (no substring copies).
   Same LCG, same operation order, same checksum.
   Build: gcc -O2 strbuild.c -o strbuild
   Usage: strbuild [lines] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

static const char *names[] = { "alpha", "beta", "gamma", "delta", "epsilon", "zeta" };
static const char *keys[] = { "alpha", "beta", "gamma", "delta" };

/* The longest line is 6 fields of "epsilon=99999" plus commas: 83 bytes. */
static char *buildLine(size_t *lineLength) {
    char *line = malloc(128);
    size_t length = 0;
    long long fieldCount = nextRandom() % 4 + 3;
    for (long long j = 0; j < fieldCount; j++) {
        if (j > 0) line[length++] = ',';
        const char *name = names[nextRandom() % 6];
        length += (size_t)snprintf(line + length, 128 - length, "%s=%lld", name, nextRandom() % 100000);
    }
    *lineLength = length;
    return line;
}

static long long keyIndex(const char *name, size_t nameLength) {
    for (int i = 0; i < 4; i++) {
        if (strlen(keys[i]) == nameLength && memcmp(keys[i], name, nameLength) == 0) return i + 1;
    }
    return 0;
}

static long long parseDigits(const char *text, size_t textLength) {
    long long number = 0;
    for (size_t i = 0; i < textLength; i++) number = number * 10 + (unsigned char)text[i] - '0';
    return number;
}

int main(int argc, char **argv) {
    long long lineCount = argc > 1 ? atoll(argv[1]) : 1000000;

    uint64_t checksum = 0;
    long long totalLength = 0;
    for (long long lineIndex = 0; lineIndex < lineCount; lineIndex++) {
        size_t length;
        char *line = buildLine(&length);
        totalLength += (long long)length;
        size_t fieldStart = 0;
        while (fieldStart < length) {
            size_t fieldEnd = fieldStart;
            size_t separator = 0;
            while (fieldEnd < length && line[fieldEnd] != ',') {
                if (line[fieldEnd] == '=') separator = fieldEnd;
                fieldEnd++;
            }
            const char *name = line + fieldStart;
            size_t nameLength = separator - fieldStart;
            const char *valueText = line + separator + 1;
            size_t valueLength = fieldEnd - separator - 1;
            long long value = parseDigits(valueText, valueLength);
            checksum = checksum * 31 + (uint64_t)(keyIndex(name, nameLength) * value + (long long)nameLength + (unsigned char)valueText[0]);
            fieldStart = fieldEnd + 1;
        }
        free(line);
    }
    printf("%lld\n", (long long)(checksum + (uint64_t)totalLength));
    return 0;
}
