// Wireframe cube (edges only), spinning a full turn. Matches cube.zeph/.rs.
// Build with -ffp-contract=off so no FMA fusion changes the rounding; then the
// checksum is byte-identical to the Zephyr and Rust versions.
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define W 100
#define H 100

static const double VX[8] = { -1, 1, 1, -1, -1, 1, 1, -1 };
static const double VY[8] = { -1, -1, 1, 1, -1, -1, 1, 1 };
static const double VZ[8] = { -1, -1, -1, -1, 1, 1, 1, 1 };
static const int E0[12] = { 0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3 };
static const int E1[12] = { 1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7 };

static int grid[W * H];
static int sx[8], sy[8];

static void draw_line(int x0, int y0, int x1, int y1) {
    int dx = x1 - x0; if (dx < 0) dx = -dx;
    int dy = y1 - y0; if (dy < 0) dy = -dy;
    int stepx = x0 < x1 ? 1 : -1;
    int stepy = y0 < y1 ? 1 : -1;
    int err = dx - dy;
    int x = x0, y = y0;
    for (;;) {
        if (x >= 0 && x < W && y >= 0 && y < H) grid[y * W + x] = 1;
        if (x == x1 && y == y1) break;
        int e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x += stepx; }
        if (e2 < dx) { err += dx; y += stepy; }
    }
}

int main(int argc, char** argv) {
    int frames = argc > 1 ? atoi(argv[1]) : 1500;
    const double tc = 0.8775825618903728, ts = 0.479425538604203;   // cos/sin(0.5)
    const double stc = 0.9968017063026194, sts = 0.07991469396917269; // cos/sin(0.08)
    double c = 1.0, s = 0.0;
    long long chk = 0;
    for (int f = 0; f < frames; f++) {
        for (int i = 0; i < W * H; i++) grid[i] = 0;
        for (int v = 0; v < 8; v++) {
            double x = VX[v], y = VY[v], z = VZ[v];
            double rx = x * c + z * s;
            double rz = z * c - x * s;
            double ry = y * tc - rz * ts;
            double rz2 = y * ts + rz * tc;
            double depth = rz2 + 4.0;
            double sc = 60.0 / depth;
            sx[v] = (int)(50.0 + rx * sc + 0.5);
            sy[v] = (int)(50.0 + ry * sc + 0.5);
        }
        for (int e = 0; e < 12; e++)
            draw_line(sx[E0[e]], sy[E0[e]], sx[E1[e]], sy[E1[e]]);
        for (int i = 0; i < W * H; i++) chk += (long long)grid[i] * i;
        double nc = c * stc - s * sts;
        double ns = s * stc + c * sts;
        double nn = sqrt(nc * nc + ns * ns);
        c = nc / nn;
        s = ns / nn;
    }
    printf("%lld\n", chk);
    return 0;
}
