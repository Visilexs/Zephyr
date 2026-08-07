#include <stdio.h>

long long fib(long long n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

int main(void) {
    printf("%lld\n", fib(32));
    long long sum = 0;
    for (long long i = 0; i < 100000000; i++)
        sum += i % 7;
    printf("%lld\n", sum);
    return 0;
}
