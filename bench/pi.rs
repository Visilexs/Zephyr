// pi.rs — N digits of pi via Machin's formula, same algorithm as pi.c/pi.zeph.
use std::env;

const BASE: i64 = 1_000_000_000;

fn arctan_small(x: i64, mul: i64, w: &mut [i64], res: &mut [i64]) {
    let n = w.len();
    for v in w.iter_mut() {
        *v = 0;
    }
    w[0] = 1;
    let mut rem: i64 = 0;
    for i in 0..n {
        let cur = rem * BASE + w[i];
        let q = cur / x;
        w[i] = q;
        rem = cur - q * x;
    }
    for i in 0..n {
        res[i] += mul * w[i];
    }
    let x2 = x * x;
    let mut k: i64 = 1;
    let mut sign: i64 = -1;
    let mut start = 0usize;
    while start < n {
        let d = 2 * k + 1;
        let mut rw: i64 = 0;
        let mut rt: i64 = 0;
        let m = mul * sign;
        for i in start..n {
            let cur = rw * BASE + w[i];
            let q = cur / x2;
            w[i] = q;
            rw = cur - q * x2;
            let curt = rt * BASE + q;
            let qt = curt / d;
            rt = curt - qt * d;
            res[i] += m * qt;
        }
        while start < n && w[start] == 0 {
            start += 1;
        }
        k += 1;
        sign = -sign;
    }
}

fn main() {
    let d: usize = env::args().nth(1).and_then(|a| a.parse().ok()).unwrap_or(10000);
    let n = d / 9 + 3;
    let mut res = vec![0i64; n];
    let mut w = vec![0i64; n];
    arctan_small(5, 16, &mut w, &mut res);
    arctan_small(239, -4, &mut w, &mut res);
    let mut carry: i64 = 0;
    for i in (1..n).rev() {
        let v = res[i] + carry;
        carry = v / BASE;
        let mut m = v - carry * BASE;
        if m < 0 {
            m += BASE;
            carry -= 1;
        }
        res[i] = m;
    }
    res[0] += carry;
    let mut out = String::with_capacity(9 * n + 16);
    out.push_str(&format!("{}.", res[0]));
    for i in 1..n {
        out.push_str(&format!("{:09}", res[i]));
    }
    out.truncate(d + 2);
    println!("{}", out);
}
