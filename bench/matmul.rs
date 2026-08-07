// Dense integer matrix multiply, N x N, ikj order. Matches matmul.zeph/.c.
use std::env;

fn main() {
    let n: usize = env::args().nth(1).and_then(|a| a.parse().ok()).unwrap_or(512);
    let mut a = vec![0i64; n * n];
    let mut b = vec![0i64; n * n];
    let mut c = vec![0i64; n * n];
    for i in 0..n {
        for j in 0..n {
            a[i * n + j] = ((i * 3 + j * 7 + 1) % 10) as i64;
            b[i * n + j] = ((i * 5 + j * 2 + 3) % 10) as i64;
        }
    }
    for i in 0..n {
        for k in 0..n {
            let aik = a[i * n + k];
            for j in 0..n {
                c[i * n + j] += aik * b[k * n + j];
            }
        }
    }
    let sum: i64 = c.iter().sum();
    println!("{}", sum);
}
