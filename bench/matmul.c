// Dense integer matrix multiply, N x N, ikj order. Matches matmul.zeph/.rs.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(int argc, char** argv) {
    int N = argc > 1 ? atoi(argv[1]) : 512;
    int64_t* A = malloc((size_t)N * N * sizeof(int64_t));
    int64_t* B = malloc((size_t)N * N * sizeof(int64_t));
    int64_t* C = calloc((size_t)N * N, sizeof(int64_t));
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            A[i * N + j] = (i * 3 + j * 7 + 1) % 10;
            B[i * N + j] = (i * 5 + j * 2 + 3) % 10;
        }
    for (int i = 0; i < N; i++)
        for (int k = 0; k < N; k++) {
            int64_t aik = A[i * N + k];
            for (int j = 0; j < N; j++)
                C[i * N + j] += aik * B[k * N + j];
        }
    int64_t sum = 0;
    for (int i = 0; i < N * N; i++) sum += C[i];
    printf("%lld\n", (long long)sum);
    return 0;
}
