#include <iostream>

long long fib(long long n) {
    if (n < 2) return n;
    return fib(n - 1) + fib(n - 2);
}

int main() {
    std::cout << fib(32) << "\n";
    long long sum = 0;
    for (long long i = 0; i < 100000000; i++)
        sum += i % 7;
    std::cout << sum << "\n";
    return 0;
}
