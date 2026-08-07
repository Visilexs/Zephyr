// Sorting benchmark: fixed pseudo-shuffle, sort_unstable ascending,
// order-sensitive checksum. Matches sort.zeph/.c.
use std::env;

fn main() {
    let ar: Vec<String> = env::args().collect();
    let n: i64 = if ar.len() > 1 { ar[1].parse().unwrap() } else { 3000000 };
    let mut a: Vec<i64> = (0..n).map(|i| (i * 2654435761 + 12345) % 1000003).collect();
    a.sort_unstable();
    let mut chk: i64 = 0;
    for i in 0..n as usize {
        chk = (chk * 31 + a[i]) % 1000000007;
    }
    println!("{}", chk);
}
