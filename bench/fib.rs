// Recursion benchmark: naive recursive Fibonacci. Matches fib.zeph / fib.c.
use std::env;

fn fib(n: i64) -> i64 {
    if n < 2 { return n; }
    fib(n - 1) + fib(n - 2)
}

fn main() {
    let a: Vec<String> = env::args().collect();
    let n: i64 = if a.len() > 1 { a[1].parse().unwrap() } else { 35 };
    println!("{}", fib(n));
}
