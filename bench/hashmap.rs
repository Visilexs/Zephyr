// Hash-map benchmark: std HashMap over colliding integer keys, last write wins,
// then sum looked-up values. Matches hashmap.zeph/.c.
use std::collections::HashMap;
use std::env;

fn main() {
    let a: Vec<String> = env::args().collect();
    let n: i64 = if a.len() > 1 { a[1].parse().unwrap() } else { 2000000 };
    let mut m: HashMap<i64, i64> = HashMap::new();
    for i in 0..n {
        m.insert((i * 2654435761) % 500009, i);
    }
    let mut chk: i64 = 0;
    for i in 0..n {
        chk += *m.get(&((i * 2654435761) % 500009)).unwrap_or(&0);
    }
    println!("{}", chk);
}
