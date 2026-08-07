// Allocation benchmark: build N short formatted strings, sum their lengths.
// format! heap-allocates an owned String per iteration. Matches strings.zeph/.c.
use std::env;

fn main() {
    let a: Vec<String> = env::args().collect();
    let n: i64 = if a.len() > 1 { a[1].parse().unwrap() } else { 2000000 };
    let mut acc: i64 = 0;
    for i in 0..n {
        let s = format!("item-{}-{}", i, (i * i) % 1000);
        acc += s.len() as i64;
    }
    println!("{}", acc);
}
