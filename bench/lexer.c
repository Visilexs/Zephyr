/* String-processing benchmark: C reference for bench/lexer.zeph. The source
   is built in a growable byte buffer; tokens are (kind, pointer, length)
   slices into it, pushed to a growable array. Same LCG, same checksum.
   Build: gcc -O2 lexer.c -o lexer
   Usage: lexer [tokens] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static uint64_t rngState = 12345;

static long long nextRandom(void) {
    rngState = rngState * 6364136223846793005ULL + 1442695040888963407ULL;
    return (long long)((rngState >> 33) & 2147483647ULL);
}

enum TokenKind { Identifier, Keyword, Number, StringLiteral, Operator };

typedef struct Token { enum TokenKind kind; const char *text; size_t length; } Token;

static const char identifierCharacters[] = "abcdefghijklmnopqrstuvwxyz0123456789_";
static const char commentCharacters[] = "abcdefghijklmnopqrstuvwxyz ";
static const char *const keywords[8] = { "if", "else", "while", "fn", "return", "let", "var", "for" };
static const char *const operators[17] = { "+", "-", "*", "/", "=", "==", "<", "<=", ">", ">=", "->", "(", ")", "{", "}", ",", "." };

typedef struct Buffer { char *bytes; size_t length, capacity; } Buffer;

static void pushByte(Buffer *buffer, char character) {
    if (buffer->length == buffer->capacity) {
        buffer->capacity = buffer->capacity ? buffer->capacity * 2 : 64;
        buffer->bytes = realloc(buffer->bytes, buffer->capacity);
    }
    buffer->bytes[buffer->length++] = character;
}

static void appendText(Buffer *buffer, const char *text) {
    while (*text) pushByte(buffer, *text++);
}

static Buffer generateSource(long long tokenCount) {
    Buffer buffer = { NULL, 0, 0 };
    for (long long i = 0; i < tokenCount; i++) {
        long long choice = nextRandom() % 10;
        if (choice < 3) {
            long long length = nextRandom() % 8 + 1;
            pushByte(&buffer, (char)('a' + nextRandom() % 26));
            for (long long j = 1; j < length; j++) pushByte(&buffer, identifierCharacters[nextRandom() % 37]);
        } else if (choice == 3) {
            appendText(&buffer, keywords[nextRandom() % 8]);
        } else if (choice < 6) {
            long long length = nextRandom() % 6 + 1;
            for (long long j = 0; j < length; j++) pushByte(&buffer, (char)('0' + nextRandom() % 10));
        } else if (choice < 8) {
            appendText(&buffer, operators[nextRandom() % 17]);
        } else if (choice == 8) {
            long long length = nextRandom() % 10;
            pushByte(&buffer, '"');
            for (long long j = 0; j < length; j++) pushByte(&buffer, identifierCharacters[nextRandom() % 37]);
            pushByte(&buffer, '"');
        } else {
            long long length = nextRandom() % 12;
            appendText(&buffer, "//");
            for (long long j = 0; j < length; j++) pushByte(&buffer, commentCharacters[nextRandom() % 27]);
            pushByte(&buffer, '\n');
        }
        long long separator = nextRandom() % 8;
        if (separator == 0) pushByte(&buffer, '\n');
        else if (separator == 1) appendText(&buffer, "  ");
        else if (separator > 2) pushByte(&buffer, ' ');
    }
    return buffer;
}

static int isLetter(int character) {
    return (character >= 'a' && character <= 'z') || (character >= 'A' && character <= 'Z') || character == '_';
}

static int isDigit(int character) { return character >= '0' && character <= '9'; }

static int isKeyword(const char *word, size_t length) {
    for (int i = 0; i < 8; i++)
        if (strlen(keywords[i]) == length && memcmp(keywords[i], word, length) == 0) return 1;
    return 0;
}

static long long lineCount, commentCount;

static Token *tokenize(const char *source, size_t length, size_t *tokenTotal) {
    size_t capacity = 64, count = 0;
    Token *tokens = malloc(capacity * sizeof *tokens);
    size_t position = 0;
    while (position < length) {
        unsigned char character = (unsigned char)source[position];
        if (character == ' ' || character == '\t' || character == '\r') { position++; continue; }
        if (character == '\n') { lineCount++; position++; continue; }
        size_t start = position;
        enum TokenKind kind = Operator;
        if (isLetter(character)) {
            while (position < length && (isLetter((unsigned char)source[position]) || isDigit((unsigned char)source[position]))) position++;
            kind = Identifier;
        } else if (isDigit(character)) {
            while (position < length && isDigit((unsigned char)source[position])) position++;
            kind = Number;
        } else if (character == '"') {
            position++;
            while (position < length && source[position] != '"') position++;
            if (position < length) position++;
            kind = StringLiteral;
        } else if (character == '/' && position + 1 < length && source[position + 1] == '/') {
            while (position < length && source[position] != '\n') position++;
            commentCount++;
            continue;
        } else {
            position++;
            if (position < length) {
                unsigned char next = (unsigned char)source[position];
                if ((next == '=' && (character == '=' || character == '<' || character == '>')) || (character == '-' && next == '>'))
                    position++;
            }
        }
        if (kind == Identifier && isKeyword(source + start, position - start)) kind = Keyword;
        if (count == capacity) {
            capacity *= 2;
            tokens = realloc(tokens, capacity * sizeof *tokens);
        }
        tokens[count++] = (Token){ kind, source + start, position - start };
    }
    *tokenTotal = count;
    return tokens;
}

int main(int argc, char **argv) {
    long long tokenCount = argc > 1 ? atoll(argv[1]) : 1000000;
    const int passes = 3;

    Buffer source = generateSource(tokenCount);
    uint64_t checksum = 0;
    for (int pass = 0; pass < passes; pass++) {
        lineCount = 0;
        commentCount = 0;
        size_t tokenTotal;
        Token *tokens = tokenize(source.bytes, source.length, &tokenTotal);
        long long kindCounts[5] = { 0, 0, 0, 0, 0 };
        uint64_t hash = 0;
        for (size_t i = 0; i < tokenTotal; i++) {
            kindCounts[tokens[i].kind]++;
            hash = hash * 31 + (uint64_t)tokens[i].kind;
            for (size_t j = 0; j < tokens[i].length; j++) hash = hash * 131 + (unsigned char)tokens[i].text[j];
        }
        checksum = checksum * 31 + tokenTotal;
        for (int k = 0; k < 5; k++) checksum = checksum * 31 + (uint64_t)kindCounts[k];
        checksum = checksum * 31 + (uint64_t)lineCount;
        checksum = checksum * 31 + (uint64_t)commentCount;
        checksum = checksum * 31 + hash;
        free(tokens);
    }
    printf("%zu %lld\n", source.length, (long long)checksum);
    return 0;
}
