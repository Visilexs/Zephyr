// String-keyed hash-map benchmark: Rust reference for bench/wordfreq.zeph,
// using std HashMap<String, i64> and a reused word buffer (a key is cloned
// only on first insertion). Same LCG, same checksum.
// Build: rustc -O wordfreq.rs
// Usage: wordfreq [words]
use std::collections::HashMap;
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

fn word_hash(word: &str) -> i64 {
    word.bytes().fold(7i64, |hash, byte| hash.wrapping_mul(31).wrapping_add(byte as i64))
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let word_count: usize = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 3000000 };
    let syllables = ["ka", "lo", "mi", "ne", "ru", "sa", "to", "vi", "ze", "po", "an", "el", "or", "ust", "ing", "ble"];
    let mut rng = Rng { state: 12345 };

    let mut frequencies: HashMap<String, i64> = HashMap::new();
    let mut word = String::with_capacity(64);
    for _ in 0..word_count {
        let syllable_count = rng.next_random() % 4 + 1;
        word.clear();
        for _ in 0..syllable_count {
            word.push_str(syllables[(rng.next_random() % 16) as usize]);
        }
        if let Some(frequency) = frequencies.get_mut(word.as_str()) {
            *frequency += 1;
        } else {
            frequencies.insert(word.clone(), 1);
        }
    }

    let checksum = frequencies
        .iter()
        .fold(0i64, |total, (word, &frequency)| total.wrapping_add(frequency.wrapping_mul(word_hash(word))));
    println!("{} {}", frequencies.len(), checksum);
}
