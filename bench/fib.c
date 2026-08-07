/* Recursion benchmark: naive recursive Fibonacci. Matches fib.zeph / fib.rs. */
#include <stdio.h>
#include <stdlib.h>

long long fib(long long n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

int main(int argc, char **argv) {
    long long N = argc > 1 ? atoll(argv[1]) : 35;
    printf("%lld\n", fib(N));
    return 0;
}
