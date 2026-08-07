// Wireframe cube (edges only), spinning a full turn. Matches cube.zeph/.c.
use std::env;

const W: i64 = 100;
const H: i64 = 100;

const VX: [f64; 8] = [-1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0, -1.0];
const VY: [f64; 8] = [-1.0, -1.0, 1.0, 1.0, -1.0, -1.0, 1.0, 1.0];
const VZ: [f64; 8] = [-1.0, -1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0];
const E0: [usize; 12] = [0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3];
const E1: [usize; 12] = [1, 2, 3, 0, 5, 6, 7, 4, 4, 5, 6, 7];

fn draw_line(grid: &mut [i64], x0: i64, y0: i64, x1: i64, y1: i64) {
    let mut dx = x1 - x0; if dx < 0 { dx = -dx; }
    let mut dy = y1 - y0; if dy < 0 { dy = -dy; }
    let stepx = if x0 < x1 { 1 } else { -1 };
    let stepy = if y0 < y1 { 1 } else { -1 };
    let mut err = dx - dy;
    let mut x = x0;
    let mut y = y0;
    loop {
        if x >= 0 && x < W && y >= 0 && y < H { grid[(y * W + x) as usize] = 1; }
        if x == x1 && y == y1 { break; }
        let e2 = 2 * err;
        if e2 > -dy { err -= dy; x += stepx; }
        if e2 < dx { err += dx; y += stepy; }
    }
}

fn main() {
    let frames: i64 = env::args().nth(1).and_then(|a| a.parse().ok()).unwrap_or(1500);
    let (tc, ts) = (0.8775825618903728_f64, 0.479425538604203_f64);      // cos/sin(0.5)
    let (stc, sts) = (0.9968017063026194_f64, 0.07991469396917269_f64);  // cos/sin(0.08)
    let mut c = 1.0_f64;
    let mut s = 0.0_f64;
    let mut chk: i64 = 0;
    let mut grid = vec![0i64; (W * H) as usize];
    let mut sx = [0i64; 8];
    let mut sy = [0i64; 8];
    for _ in 0..frames {
        for i in 0..(W * H) as usize { grid[i] = 0; }
        for v in 0..8 {
            let (x, y, z) = (VX[v], VY[v], VZ[v]);
            let rx = x * c + z * s;
            let rz = z * c - x * s;
            let ry = y * tc - rz * ts;
            let rz2 = y * ts + rz * tc;
            let depth = rz2 + 4.0;
            let sc = 60.0 / depth;
            sx[v] = (50.0 + rx * sc + 0.5) as i64;
            sy[v] = (50.0 + ry * sc + 0.5) as i64;
        }
        for e in 0..12 {
            draw_line(&mut grid, sx[E0[e]], sy[E0[e]], sx[E1[e]], sy[E1[e]]);
        }
        for i in 0..(W * H) as usize { chk += grid[i] * i as i64; }
        let nc = c * stc - s * sts;
        let ns = s * stc + c * sts;
        let nn = (nc * nc + ns * ns).sqrt();
        c = nc / nn;
        s = ns / nn;
    }
    println!("{}", chk);
}
