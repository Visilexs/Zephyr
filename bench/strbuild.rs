// String building and slicing benchmark: Rust reference for
// bench/strbuild.zeph. Each line is an owned String built with push/write!;
// fields are &str slices of it (no substring copies).
// Same LCG, same operation order, same checksum.
// Build: rustc -O strbuild.rs
// Usage: strbuild [lines]
#![allow(non_snake_case, non_upper_case_globals)]
use std::env;
use std::fmt::Write;

static mut rngState: u64 = 12345;

fn nextRandom() -> i64 {
    unsafe {
        rngState = rngState.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((rngState >> 33) & 2147483647) as i64
    }
}

const names: [&str; 6] = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta"];
const keys: [&str; 4] = ["alpha", "beta", "gamma", "delta"];

fn buildLine() -> String {
    let fieldCount = nextRandom() % 4 + 3;
    let mut line = String::new();
    for j in 0..fieldCount {
        if j > 0 {
            line.push(',');
        }
        let name = names[(nextRandom() % 6) as usize];
        write!(line, "{}={}", name, nextRandom() % 100000).unwrap();
    }
    line
}

fn keyIndex(name: &str) -> i64 {
    for i in 0..keys.len() {
        if name == keys[i] {
            return i as i64 + 1;
        }
    }
    0
}

fn parseDigits(text: &str) -> i64 {
    let mut number: i64 = 0;
    for &character in text.as_bytes() {
        number = number * 10 + character as i64 - b'0' as i64;
    }
    number
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let lineCount: i64 = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 1000000 };

    let mut checksum: i64 = 0;
    let mut totalLength: i64 = 0;
    for _lineIndex in 0..lineCount {
        let line = buildLine();
        let bytes = line.as_bytes();
        let length = bytes.len();
        totalLength += length as i64;
        let mut fieldStart = 0;
        while fieldStart < length {
            let mut fieldEnd = fieldStart;
            let mut separator = 0;
            while fieldEnd < length && bytes[fieldEnd] != b',' {
                if bytes[fieldEnd] == b'=' {
                    separator = fieldEnd;
                }
                fieldEnd += 1;
            }
            let name = &line[fieldStart..separator];
            let valueText = &line[separator + 1..fieldEnd];
            let value = parseDigits(valueText);
            checksum = checksum
                .wrapping_mul(31)
                .wrapping_add(keyIndex(name) * value + name.len() as i64 + valueText.as_bytes()[0] as i64);
            fieldStart = fieldEnd + 1;
        }
    }
    println!("{}", checksum.wrapping_add(totalLength));
}
