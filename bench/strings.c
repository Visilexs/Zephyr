/* Allocation benchmark: build N short formatted strings, sum their lengths.
   Each iteration heap-allocates an owned string, like strings.zeph/.rs. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv) {
    long long N = argc > 1 ? atoll(argv[1]) : 2000000;
    long long acc = 0;
    for (long long i = 0; i < N; i++) {
        char *s = malloc(64);
        snprintf(s, 64, "item-%lld-%lld", i, (i * i) % 1000);
        acc += (long long)strlen(s);
        free(s);
    }
    printf("%lld\n", acc);
    return 0;
}
