// Megamorphic dispatch benchmark: Rust reference for bench/dispatch.zeph,
// using Vec<Box<dyn Transform>> over eight implementing types.
// Same LCG, same operation order, same checksum.
// Build: rustc -O dispatch.rs
// Usage: dispatch [count]
#![allow(non_snake_case, non_upper_case_globals)]
use std::env;

static mut rngState: u64 = 12345;

fn nextRandom() -> i64 {
    unsafe {
        rngState = rngState.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((rngState >> 33) & 2147483647) as i64
    }
}

const valueMask: i64 = 1048575;

trait Transform {
    fn apply(&self, value: i64) -> i64;
    fn weight(&self) -> i64;
}

struct Adder { amount: i64 }
impl Transform for Adder {
    fn apply(&self, value: i64) -> i64 { (value + self.amount) & valueMask }
    fn weight(&self) -> i64 { self.amount & 7 }
}

struct Multiplier { factor: i64 }
impl Transform for Multiplier {
    fn apply(&self, value: i64) -> i64 { (value * self.factor) & valueMask }
    fn weight(&self) -> i64 { 1 }
}

struct XorMasker { key: i64 }
impl Transform for XorMasker {
    fn apply(&self, value: i64) -> i64 { value ^ self.key }
    fn weight(&self) -> i64 { 2 }
}

struct Rotator { shift: i64 }
impl Transform for Rotator {
    fn apply(&self, value: i64) -> i64 { ((value << self.shift) | (value >> (20 - self.shift))) & valueMask }
    fn weight(&self) -> i64 { self.shift }
}

struct Clamper { low: i64, high: i64 }
impl Transform for Clamper {
    fn apply(&self, value: i64) -> i64 {
        if value < self.low { return self.low; }
        if value > self.high { return self.high; }
        value
    }
    fn weight(&self) -> i64 { 3 }
}

struct AffineMixer { scale: i64, offset: i64 }
impl Transform for AffineMixer {
    fn apply(&self, value: i64) -> i64 { (value * self.scale + self.offset) & valueMask }
    fn weight(&self) -> i64 { 4 }
}

struct Divider { divisor: i64 }
impl Transform for Divider {
    fn apply(&self, value: i64) -> i64 { value / self.divisor + self.divisor * 1000 }
    fn weight(&self) -> i64 { self.divisor }
}

struct Complementer { bias: i64 }
impl Transform for Complementer {
    fn apply(&self, value: i64) -> i64 { (valueMask - value + self.bias) & valueMask }
    fn weight(&self) -> i64 { 5 }
}

fn makeTransform() -> Box<dyn Transform> {
    match nextRandom() % 8 {
        0 => Box::new(Adder { amount: nextRandom() % 1000 }),
        1 => Box::new(Multiplier { factor: nextRandom() % 64 + 1 }),
        2 => Box::new(XorMasker { key: nextRandom() & valueMask }),
        3 => Box::new(Rotator { shift: nextRandom() % 19 + 1 }),
        4 => {
            let low = nextRandom() % 100000;
            let high = low + nextRandom() % 900000;
            Box::new(Clamper { low, high })
        }
        5 => {
            let scale = nextRandom() % 32 + 1;
            let offset = nextRandom() % 1000;
            Box::new(AffineMixer { scale, offset })
        }
        6 => Box::new(Divider { divisor: nextRandom() % 16 + 1 }),
        _ => Box::new(Complementer { bias: nextRandom() % 1000 }),
    }
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let count: usize = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 1000000 };
    let rounds: i64 = 20;

    let transforms: Vec<Box<dyn Transform>> = (0..count).map(|_| makeTransform()).collect();

    let mut checksum: i64 = 0;
    for round in 0..rounds {
        let mut value = round;
        let mut weightTotal: i64 = 0;
        for transform in &transforms {
            value = transform.apply(value);
            weightTotal += transform.weight();
        }
        checksum = checksum.wrapping_mul(31).wrapping_add(value);
        checksum = checksum.wrapping_mul(31).wrapping_add(weightTotal);
    }
    println!("{}", checksum);
}
