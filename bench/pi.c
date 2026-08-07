// pi.c — N digits of pi via Machin's formula: pi = 16*atan(1/5) - 4*atan(1/239).
// Base-10^9 fixed point; terms accumulate into i64 limbs without carrying
// (headroom is ample), normalized once at the end.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define BASE 1000000000LL

static int64_t* res;
static int64_t* w;
static int N;

static void arctan_small(int64_t x, int64_t mul) {
    memset(w, 0, (size_t)N * 8);
    w[0] = 1;
    int64_t rem = 0;
    for (int i = 0; i < N; i++) {          // w = 1/x
        int64_t cur = rem * BASE + w[i];
        int64_t q = cur / x;
        w[i] = q;
        rem = cur - q * x;
    }
    for (int i = 0; i < N; i++) res[i] += mul * w[i];
    int64_t x2 = x * x;
    int64_t k = 1, sign = -1;
    int start = 0;
    while (start < N) {
        int64_t d = 2 * k + 1;
        int64_t rw = 0, rt = 0;
        int64_t m = mul * sign;
        for (int i = start; i < N; i++) {
            int64_t cur = rw * BASE + w[i]; // w /= x^2
            int64_t q = cur / x2;
            w[i] = q;
            rw = cur - q * x2;
            int64_t curt = rt * BASE + q;   // term = w / (2k+1)
            int64_t qt = curt / d;
            rt = curt - qt * d;
            res[i] += m * qt;
        }
        while (start < N && w[start] == 0) start++;
        k++;
        sign = -sign;
    }
}

int main(int argc, char** argv) {
    long long D = argc > 1 ? atoll(argv[1]) : 10000;
    N = (int)(D / 9 + 3);
    res = calloc((size_t)N, 8);
    w = malloc((size_t)N * 8);
    arctan_small(5, 16);
    arctan_small(239, -4);
    int64_t carry = 0;                      // single end normalization
    for (int i = N - 1; i >= 1; i--) {
        int64_t v = res[i] + carry;
        carry = v / BASE;
        int64_t m = v - carry * BASE;
        if (m < 0) { m += BASE; carry -= 1; }
        res[i] = m;
    }
    res[0] += carry;
    char* out = malloc((size_t)(9LL * N + 16));
    char* p = out;
    p += sprintf(p, "%lld.", (long long)res[0]);
    for (int i = 1; i < N; i++) p += sprintf(p, "%09lld", (long long)res[i]);
    out[D + 2] = 0;                         // exactly D digits after "3."
    puts(out);
    return 0;
}
