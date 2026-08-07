// spin67 in Rust — same algorithm as spin67.zeph for comparison.
// Usage: spin67 [frames] [nopause]
use std::env;
use std::thread::sleep;
use std::time::Duration;

const ART: [&str; 8] = [
    "   6666     77777777",
    "  66             777",
    " 66             77  ",
    " 66            77   ",
    " 6666666      77    ",
    " 66    66    77     ",
    " 66    66   77      ",
    "  666666   77       ",
];
const BW: usize = 20;
const BH: usize = 8;
const W: usize = 64;
const H: usize = 30;
const RAMP: [char; 9] = ['.', ':', '-', '=', '+', '*', '#', '%', '@'];

fn render(c: f64, s: f64, pts: &[(f64, f64, f64)], zbuf: &mut [f64], grid: &mut [i32]) -> String {
    for i in 0..W * H {
        zbuf[i] = 1e9;
        grid[i] = -1;
    }
    for &(x, y, z) in pts {
        let rx = x * c + z * s;
        let rz = z * c - x * s;
        let ry = y * 0.939373 - rz * 0.342898;
        let rz2 = y * 0.342898 + rz * 0.939373;
        let depth = rz2 + 16.0;
        let sc = 30.0 / depth;
        let sxi = (32.0 + rx * sc * 2.0 + 0.5) as i64;
        let syi = (15.0 + ry * sc + 0.5) as i64;
        if sxi >= 0 && (sxi as usize) < W && syi >= 0 && (syi as usize) < H {
            let idx = syi as usize * W + sxi as usize;
            if depth < zbuf[idx] {
                zbuf[idx] = depth;
                let b = ((6.0 - rz2) * 0.7) as i64;
                grid[idx] = b.clamp(0, 8) as i32;
            }
        }
    }
    let mut out = String::with_capacity(W * H + H + 8);
    out.push_str("\x1b[H");
    for yy in 0..H {
        for xx in 0..W {
            let g = grid[yy * W + xx];
            out.push(if g < 0 { ' ' } else { RAMP[g as usize] });
        }
        out.push('\n');
    }
    out
}

fn main() {
    let frames: usize = env::args().nth(1).and_then(|a| a.parse().ok()).unwrap_or(400);
    let nopause = env::args().nth(2).is_some();
    let mut pts = Vec::new();
    for (by, rowstr) in ART.iter().enumerate() {
        let row = rowstr.as_bytes();
        for bx in 0..BW {
            if bx < row.len() && row[bx] != b' ' {
                for ox in 0..2 {
                    for oy in 0..2 {
                        for lz in 0..3 {
                            pts.push((
                                (bx as f64 + ox as f64 * 0.5 - 10.0) * 0.55,
                                by as f64 + oy as f64 * 0.5 - 4.0,
                                lz as f64 * 0.4 - 0.4,
                            ));
                        }
                    }
                }
            }
        }
    }
    let mut zbuf = vec![0.0f64; W * H];
    let mut grid = vec![-1i32; W * H];
    print!("\x1b[2J\x1b[?25l");
    let (mut c, mut s) = (1.0f64, 0.0f64);
    for _ in 0..frames {
        println!("{}", render(c, s, &pts, &mut zbuf, &mut grid));
        if !nopause {
            sleep(Duration::from_millis(30));
        }
        let nc = c * 0.995004 - s * 0.099833;
        let ns = s * 0.995004 + c * 0.099833;
        let n = (nc * nc + ns * ns).sqrt();
        c = nc / n;
        s = ns / n;
    }
    print!("\x1b[?25h");
}
