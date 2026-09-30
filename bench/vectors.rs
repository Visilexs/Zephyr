// Small-value-struct benchmark: Rust reference for bench/vectors.zeph. Vec3
// is Copy, so every temporary stays in registers. Same LCG, same checksum.
// Build: rustc -O vectors.rs
// Usage: vectors [steps]

#[derive(Clone, Copy)]
struct Vec3 { x: f64, y: f64, z: f64 }

fn add(a: Vec3, b: Vec3) -> Vec3 { Vec3 { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z } }
fn subtract(a: Vec3, b: Vec3) -> Vec3 { Vec3 { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z } }
fn scale(a: Vec3, factor: f64) -> Vec3 { Vec3 { x: a.x * factor, y: a.y * factor, z: a.z * factor } }
fn dot(a: Vec3, b: Vec3) -> f64 { a.x * b.x + a.y * b.y + a.z * b.z }

struct Random { state: u64 }

impl Random {
    fn next(&mut self) -> i64 {
        self.state = self.state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.state >> 33) & 2147483647) as i64
    }
    fn unit(&mut self) -> f64 { (self.next() % 20001 - 10000) as f64 / 10000.0 }
}

const PARTICLE_COUNT: usize = 4000;

fn main() {
    let steps: i64 = std::env::args().nth(1).map(|a| a.parse().unwrap()).unwrap_or(1000);
    let mut random = Random { state: 12345 };
    let mut positions = Vec::with_capacity(PARTICLE_COUNT);
    let mut velocities = Vec::with_capacity(PARTICLE_COUNT);
    for _ in 0..PARTICLE_COUNT {
        let x = random.unit();
        let y = random.unit();
        let z = random.unit();
        positions.push(Vec3 { x, y, z });
        velocities.push(Vec3 { x: 0.0, y: 0.0, z: 0.0 });
    }
    let anchor = Vec3 { x: 0.25, y: -0.5, z: 0.125 };
    for _ in 0..steps {
        for i in 0..PARTICLE_COUNT {
            let position = positions[i];
            let offset = subtract(anchor, position);
            let distance_squared = dot(offset, offset) + 0.01;
            let pull = scale(offset, 0.001 / distance_squared);
            let drag = scale(velocities[i], 0.002);
            let velocity = subtract(add(velocities[i], pull), drag);
            velocities[i] = velocity;
            positions[i] = add(position, scale(velocity, 0.01));
        }
    }
    let mut total = 0.0;
    for i in 0..PARTICLE_COUNT {
        total += positions[i].x + 2.0 * positions[i].y + 3.0 * positions[i].z;
        total += velocities[i].x - velocities[i].y + velocities[i].z;
    }
    println!("{}", (total * 1000000.0) as i64);
}
