// Benchmark: particle-based viscoelastic fluid (Clavet et al. 2005).
// Rust reference for bench/liquid.zeph -- same algorithm, same order of
// operations, same checksum. Build: rustc -O liquid.rs
// Usage: liquid <steps>

const W: usize = 320;
const H: usize = 240;
const N: usize = 6000;
const RADIUS: f64 = 7.0;
const DT: f64 = 1.0;
const GRAV: f64 = 0.09;
const REST: f64 = 4.5;
const K: f64 = 0.055;
const KNEAR: f64 = 0.28;
const SIGMA: f64 = 0.03;
const BETA: f64 = 0.06;
const GW: i64 = (W / 7 + 1) as i64;
const GH: i64 = (H / 7 + 1) as i64;
const CELLS: usize = (GW * GH) as usize;
const CAP: i64 = 40;

struct Sim {
    px: Vec<f64>,
    py: Vec<f64>,
    ox: Vec<f64>,
    oy: Vec<f64>,
    vx: Vec<f64>,
    vy: Vec<f64>,
    cnt: Vec<i64>,
    bucket: Vec<i64>,
    nbr: Vec<i64>,
    nd: Vec<f64>,
}

fn clampi(v: i64, lo: i64, hi: i64) -> i64 {
    if v < lo {
        lo
    } else if v > hi {
        hi
    } else {
        v
    }
}

impl Sim {
    fn new() -> Sim {
        Sim {
            px: vec![0.0; N],
            py: vec![0.0; N],
            ox: vec![0.0; N],
            oy: vec![0.0; N],
            vx: vec![0.0; N],
            vy: vec![0.0; N],
            cnt: vec![0; CELLS],
            bucket: vec![0; CELLS * CAP as usize],
            nbr: vec![0; 256],
            nd: vec![0.0; 256],
        }
    }

    fn build_grid(&mut self) {
        for c in 0..CELLS {
            self.cnt[c] = 0;
        }
        for i in 0..N {
            let cx = clampi((self.px[i] / RADIUS) as i64, 0, GW - 1);
            let cy = clampi((self.py[i] / RADIUS) as i64, 0, GH - 1);
            let k = cy * GW + cx;
            let n = self.cnt[k as usize];
            if n < CAP {
                self.bucket[(k * CAP + n) as usize] = i as i64;
                self.cnt[k as usize] = n + 1;
            }
        }
    }

    fn neighbours(&mut self, i: usize) -> usize {
        let xi = self.px[i];
        let yi = self.py[i];
        let cx = clampi((xi / RADIUS) as i64, 0, GW - 1);
        let cy = clampi((yi / RADIUS) as i64, 0, GH - 1);
        let mut n = 0usize;
        for gy in (cy - 1)..=(cy + 1) {
            if gy < 0 || gy >= GH {
                continue;
            }
            for gx in (cx - 1)..=(cx + 1) {
                if gx < 0 || gx >= GW {
                    continue;
                }
                let k = gy * GW + gx;
                let m = self.cnt[k as usize];
                for s in 0..m {
                    let j = self.bucket[(k * CAP + s) as usize] as usize;
                    if j != i && n < 256 {
                        let dx = self.px[j] - xi;
                        let dy = self.py[j] - yi;
                        let d2 = dx * dx + dy * dy;
                        if d2 < RADIUS * RADIUS {
                            self.nbr[n] = j as i64;
                            self.nd[n] = 1.0 - d2.sqrt() / RADIUS;
                            n += 1;
                        }
                    }
                }
            }
        }
        n
    }

    fn viscosity(&mut self) {
        for i in 0..N {
            let n = self.neighbours(i);
            for s in 0..n {
                let j = self.nbr[s] as usize;
                if j > i {
                    let q = self.nd[s];
                    let mut dx = self.px[j] - self.px[i];
                    let mut dy = self.py[j] - self.py[i];
                    let dist = (dx * dx + dy * dy).sqrt();
                    if dist > 0.0001 {
                        dx = dx / dist;
                        dy = dy / dist;
                        let u = (self.vx[i] - self.vx[j]) * dx + (self.vy[i] - self.vy[j]) * dy;
                        if u > 0.0 {
                            let mut im = DT * q * (SIGMA * u + BETA * u * u) * 0.5;
                            if im > u * 0.5 {
                                im = u * 0.5;
                            }
                            self.vx[i] -= dx * im;
                            self.vy[i] -= dy * im;
                            self.vx[j] += dx * im;
                            self.vy[j] += dy * im;
                        }
                    }
                }
            }
        }
    }

    fn relax(&mut self) {
        for i in 0..N {
            let n = self.neighbours(i);
            let mut rho = 0.0;
            let mut rho_near = 0.0;
            for s in 0..n {
                let q = self.nd[s];
                rho += q * q;
                rho_near += q * q * q;
            }
            let pres = K * (rho - REST);
            let pres_near = KNEAR * rho_near;
            let mut dxi = 0.0;
            let mut dyi = 0.0;
            for s in 0..n {
                let j = self.nbr[s] as usize;
                let q = self.nd[s];
                let mut dx = self.px[j] - self.px[i];
                let mut dy = self.py[j] - self.py[i];
                let dist = (dx * dx + dy * dy).sqrt();
                if dist > 0.0001 {
                    dx = dx / dist;
                    dy = dy / dist;
                    let d = DT * DT * (pres * q + pres_near * q * q) * 0.5;
                    self.px[j] += dx * d;
                    self.py[j] += dy * d;
                    dxi -= dx * d;
                    dyi -= dy * d;
                }
            }
            self.px[i] += dxi;
            self.py[i] += dyi;
        }
    }

    fn step(&mut self) {
        let wf = W as f64;
        let hf = H as f64;
        for i in 0..N {
            self.vy[i] += GRAV * DT;
        }
        self.build_grid();
        self.viscosity();
        for i in 0..N {
            self.ox[i] = self.px[i];
            self.oy[i] = self.py[i];
            self.px[i] += self.vx[i] * DT;
            self.py[i] += self.vy[i] * DT;
        }
        self.build_grid();
        self.relax();
        for i in 0..N {
            if self.px[i] < 1.0 {
                self.px[i] = 1.0;
            }
            if self.px[i] > wf - 2.0 {
                self.px[i] = wf - 2.0;
            }
            if self.py[i] < 1.0 {
                self.py[i] = 1.0;
            }
            if self.py[i] > hf - 2.0 {
                self.py[i] = hf - 2.0;
            }
            self.vx[i] = (self.px[i] - self.ox[i]) / DT;
            self.vy[i] = (self.py[i] - self.oy[i]) / DT;
        }
    }
}

fn main() {
    let steps: i64 = std::env::args()
        .nth(1)
        .and_then(|a| a.parse().ok())
        .unwrap_or(400);
    let mut sim = Sim::new();
    let cols = 46;
    for i in 0..N {
        sim.px[i] = 4.0 + ((i % cols) as f64) * 1.72;
        sim.py[i] = 236.0 - ((i / cols) as f64) * 1.72;
    }
    for _ in 0..steps {
        sim.step();
    }
    let mut chk: i64 = 0;
    for i in 0..N {
        chk += (sim.px[i] * 1000.0) as i64 * 3 + (sim.py[i] * 1000.0) as i64 * 7;
        chk += (sim.vx[i] * 1000.0) as i64 * 11 + (sim.vy[i] * 1000.0) as i64 * 13;
    }
    println!("{}", chk);
}
