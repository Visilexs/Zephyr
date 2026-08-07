/* Floating-point benchmark: Mandelbrot escape-time. Matches mandel.zeph/.rs.
   Build with -ffp-contract=off so no FMA fusion perturbs the checksum. */
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    long W = argc > 1 ? atol(argv[1]) : 900;
    long H = W;
    int MAXIT = 256;

    long long total = 0;
    for (long py = 0; py < H; py++) {
        double y0 = (double)py / (double)H * 2.0 - 1.0;
        for (long px = 0; px < W; px++) {
            double x0 = (double)px / (double)W * 3.5 - 2.5;
            double x = 0.0, y = 0.0;
            int it = 0;
            while (x * x + y * y <= 4.0 && it < MAXIT) {
                double xt = x * x - y * y + x0;
                y = 2.0 * x * y + y0;
                x = xt;
                it++;
            }
            total += it;
        }
    }
    printf("%lld\n", total);
    return 0;
}
