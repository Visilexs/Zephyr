// Binary-trees benchmark (benchmarks game): Rust reference for
// bench/bintrees.zeph, nodes are Option<Box<Node>> children.
// Same tree shapes, same checksum.
// Build: rustc -O bintrees.rs
// Usage: bintrees [maxDepth]
#![allow(non_snake_case, non_upper_case_globals)]
use std::env;

struct Node {
    left: Option<Box<Node>>,
    right: Option<Box<Node>>,
}

fn bottomUpTree(depth: i64) -> Box<Node> {
    if depth > 0 {
        Box::new(Node { left: Some(bottomUpTree(depth - 1)), right: Some(bottomUpTree(depth - 1)) })
    } else {
        Box::new(Node { left: None, right: None })
    }
}

fn itemCheck(node: &Node) -> i64 {
    let mut total = 1;
    if let Some(left) = &node.left {
        total += itemCheck(left);
    }
    if let Some(right) = &node.right {
        total += itemCheck(right);
    }
    total
}

const minimumDepth: i64 = 4;

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let mut maximumDepth: i64 = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 16 };
    if maximumDepth < minimumDepth + 2 {
        maximumDepth = minimumDepth + 2;
    }

    let mut checksum: i64 = itemCheck(&bottomUpTree(maximumDepth + 1));
    let longLivedTree = bottomUpTree(maximumDepth);

    let mut depth = minimumDepth;
    while depth <= maximumDepth {
        let iterations: i64 = 1 << (maximumDepth - depth + minimumDepth);
        let mut check: i64 = 0;
        for _ in 0..iterations {
            check += itemCheck(&bottomUpTree(depth));
        }
        checksum = checksum.wrapping_mul(31).wrapping_add(check);
        depth += 2;
    }
    checksum = checksum.wrapping_mul(31).wrapping_add(itemCheck(&longLivedTree));
    println!("{}", checksum);
}
