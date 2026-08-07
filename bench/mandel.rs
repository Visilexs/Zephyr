// Floating-point benchmark: Mandelbrot escape-time. Matches mandel.zeph/.c.
// rustc does not contract to FMA by default, so the checksum matches C's
// -ffp-contract=off build exactly.
use std::env;

fn main() {
    let a: Vec<String> = env::args().collect();
    let w: i64 = if a.len() > 1 { a[1].parse().unwrap() } else { 900 };
    let h = w;
    let maxit = 256;

    let mut total: i64 = 0;
    for py in 0..h {
        let y0 = py as f64 / h as f64 * 2.0 - 1.0;
        for px in 0..w {
            let x0 = px as f64 / w as f64 * 3.5 - 2.5;
            let (mut x, mut y) = (0.0f64, 0.0f64);
            let mut it = 0;
            while x * x + y * y <= 4.0 && it < maxit {
                let xt = x * x - y * y + x0;
                y = 2.0 * x * y + y0;
                x = xt;
                it += 1;
            }
            total += it;
        }
    }
    println!("{}", total);
}
