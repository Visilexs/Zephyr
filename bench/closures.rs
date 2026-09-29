// Higher-order-function benchmark: Rust reference for bench/closures.zeph,
// using iterator adaptors and closures capturing per-round locals.
// Same LCG, same checksum.
// Build: rustc -O closures.rs
// Usage: closures [count]
use std::env;

struct Rng {
    state: u64,
}

impl Rng {
    fn next_random(&mut self) -> i64 {
        self.state = self.state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.state >> 33) & 2147483647) as i64
    }
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let item_count: usize = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 200000 };
    let rounds: i64 = 10;
    let modulus: i64 = 1000003;
    let mut rng = Rng { state: 12345 };

    let data: Vec<i64> = (0..item_count).map(|_| rng.next_random() % 1000000).collect();

    let mut checksum: i64 = 0;
    for round in 0..rounds {
        let multiplier = round * 2 + 3;
        let offset = round * 7 + 1;
        let divisor = round % 5 + 3;
        let remainder = round % 3;
        let weight = round + 1;
        let mask = round * 12345;
        let threshold = round * 1000;

        let mapped: Vec<i64> = data.iter().map(|&value| (value * multiplier + offset) % modulus).collect();
        let mut kept: Vec<i64> = mapped.iter().copied().filter(|&value| value % divisor != remainder).collect();
        let weighted_total = kept.iter().fold(0i64, |total, &value| total + value * weight);
        kept.sort_by_key(|&value| value ^ mask);
        let ordered_total: i64 = kept.iter().enumerate().map(|(i, &value)| value * (i as i64 % 1000)).sum();
        let found_threshold = kept.iter().any(|&value| value == threshold);

        checksum = checksum.wrapping_mul(31).wrapping_add(weighted_total);
        checksum = checksum.wrapping_mul(31).wrapping_add(ordered_total);
        checksum = checksum
            .wrapping_mul(31)
            .wrapping_add(kept.len() as i64)
            .wrapping_add(if found_threshold { 1 } else { 0 });
    }
    println!("{}", checksum);
}
