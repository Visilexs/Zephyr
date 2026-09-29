// Struct-heavy float benchmark: Rust reference for bench/nbody.zeph. Same LCG,
// same operation order, same checksum.
// Build: rustc -O nbody.rs
// Usage: nbody [steps]
use std::env;

const BODY_COUNT: usize = 1000;
const TIME_STEP: f64 = 0.001;
const SOFTENING: f64 = 0.01;

struct Rng {
    state: u64,
}

impl Rng {
    fn next_random(&mut self) -> i64 {
        self.state = self.state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.state >> 33) & 2147483647) as i64
    }
}

#[derive(Clone, Copy)]
struct Body {
    x: f64,
    y: f64,
    z: f64,
    vx: f64,
    vy: f64,
    vz: f64,
    mass: f64,
}

fn make_body(rng: &mut Rng) -> Body {
    let x = (rng.next_random() % 20001 - 10000) as f64 / 1000.0;
    let y = (rng.next_random() % 20001 - 10000) as f64 / 1000.0;
    let z = (rng.next_random() % 20001 - 10000) as f64 / 1000.0;
    let vx = (rng.next_random() % 2001 - 1000) as f64 / 10000.0;
    let vy = (rng.next_random() % 2001 - 1000) as f64 / 10000.0;
    let vz = (rng.next_random() % 2001 - 1000) as f64 / 10000.0;
    let mass = (rng.next_random() % 1000 + 1) as f64 / 1000.0;
    Body { x, y, z, vx, vy, vz, mass }
}

fn advance(bodies: &mut [Body]) {
    for i in 0..bodies.len() {
        let (head, tail) = bodies.split_at_mut(i + 1);
        let first = &mut head[i];
        for second in tail.iter_mut() {
            let delta_x = first.x - second.x;
            let delta_y = first.y - second.y;
            let delta_z = first.z - second.z;
            let distance_squared = delta_x * delta_x + delta_y * delta_y + delta_z * delta_z + SOFTENING;
            let distance = distance_squared.sqrt();
            let magnitude = TIME_STEP / (distance_squared * distance);
            let second_pull = second.mass * magnitude;
            let first_pull = first.mass * magnitude;
            first.vx -= delta_x * second_pull;
            first.vy -= delta_y * second_pull;
            first.vz -= delta_z * second_pull;
            second.vx += delta_x * first_pull;
            second.vy += delta_y * first_pull;
            second.vz += delta_z * first_pull;
        }
    }
    for body in bodies.iter_mut() {
        body.x += TIME_STEP * body.vx;
        body.y += TIME_STEP * body.vy;
        body.z += TIME_STEP * body.vz;
    }
}

fn energy(bodies: &[Body]) -> f64 {
    let mut total = 0.0;
    for (i, first) in bodies.iter().enumerate() {
        total += 0.5 * first.mass * (first.vx * first.vx + first.vy * first.vy + first.vz * first.vz);
        for second in &bodies[i + 1..] {
            let delta_x = first.x - second.x;
            let delta_y = first.y - second.y;
            let delta_z = first.z - second.z;
            total -= first.mass * second.mass / (delta_x * delta_x + delta_y * delta_y + delta_z * delta_z + SOFTENING).sqrt();
        }
    }
    total
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let steps: usize = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 100 };
    let mut rng = Rng { state: 12345 };
    let mut bodies: Vec<Body> = (0..BODY_COUNT).map(|_| make_body(&mut rng)).collect();
    for _ in 0..steps {
        advance(&mut bodies);
    }

    let mut checksum = (energy(&bodies) * 1000000000.0) as i64;
    for body in &bodies {
        checksum = checksum.wrapping_mul(31).wrapping_add((body.x * 1000000.0) as i64);
        checksum = checksum.wrapping_mul(31).wrapping_add((body.y * 1000000.0) as i64);
        checksum = checksum.wrapping_mul(31).wrapping_add((body.z * 1000000.0) as i64);
    }
    println!("{}", checksum);
}
