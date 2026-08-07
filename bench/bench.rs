fn fib(n: i64) -> i64 {
    if n < 2 { return n; }
    fib(n - 1) + fib(n - 2)
}

fn main() {
    println!("{}", fib(32));
    let mut sum: i64 = 0;
    for i in 0..100_000_000i64 {
        sum += i % 7;
    }
    println!("{}", sum);
}
