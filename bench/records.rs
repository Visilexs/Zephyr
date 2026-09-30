// Record-table benchmark: Rust reference for bench/records.zeph, with the
// records stored inline in a Vec<Record>.
// Same LCG, same operation order, same checksum.
// Build: rustc -O records.rs
// Usage: records [count]
#![allow(non_snake_case, non_upper_case_globals)]
use std::env;

static mut rngState: u64 = 12345;

fn nextRandom() -> i64 {
    unsafe {
        rngState = rngState.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((rngState >> 33) & 2147483647) as i64
    }
}

struct Record {
    id: i64,
    category: i64,
    quantity: i64,
    flags: i64,
    price: f64,
    weight: f64,
    score: f64,
    discount: f64,
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let count: i64 = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 1000000 };
    let rounds: i64 = 40;

    let mut records: Vec<Record> = Vec::new();
    for i in 0..count {
        let category = nextRandom() % 8;
        let quantity = nextRandom() % 1000;
        let flags = nextRandom() % 16;
        let price = (nextRandom() % 100000) as f64 / 100.0;
        let weight = (nextRandom() % 10000) as f64 / 100.0;
        let score = (nextRandom() % 1000) as f64 / 10.0;
        let discount = (nextRandom() % 500) as f64 / 1000.0;
        records.push(Record { id: i, category, quantity, flags, price, weight, score, discount });
    }

    let mut checksum: i64 = 0;
    for round in 0..rounds {
        let targetCategory = round % 8;
        let mut revenue = 0.0;
        let mut matchedCount: i64 = 0;
        for record in &records {
            if record.category == targetCategory {
                revenue += record.price * record.quantity as f64;
                matchedCount += 1;
            }
        }

        let flagBit: i64 = 1 << (round % 4);
        let mut heavyCount: i64 = 0;
        let mut heavyScore = 0.0;
        for record in &records {
            if record.weight > 50.0 && (record.flags & flagBit) != 0 && record.quantity < 500 {
                heavyCount += 1;
                heavyScore += record.score;
            }
        }

        let mut categoryTotals = [0.0f64; 8];
        let mut categoryQuantities = [0i64; 8];
        for record in &records {
            categoryTotals[record.category as usize] += record.weight * record.discount;
            categoryQuantities[record.category as usize] += record.quantity;
        }

        for record in records.iter_mut() {
            record.quantity = (record.quantity * 7 + round + record.id) % 1000;
            record.score = record.score * 0.5 + record.price * 0.25;
            if (record.flags & 1) != 0 {
                record.price = record.price + record.discount;
            }
            record.flags = (record.flags * 5 + 1) & 15;
            record.discount = record.discount * 0.75;
        }

        checksum = checksum.wrapping_mul(31).wrapping_add((revenue * 100.0) as i64).wrapping_add(matchedCount);
        checksum = checksum.wrapping_mul(31).wrapping_add((heavyScore * 100.0) as i64).wrapping_add(heavyCount);
        for i in 0..8 {
            checksum = checksum
                .wrapping_mul(31)
                .wrapping_add((categoryTotals[i] * 1000.0) as i64)
                .wrapping_add(categoryQuantities[i]);
        }
    }
    println!("{}", checksum);
}
