// Dynamic-dispatch benchmark: Rust reference for bench/shapes.zeph, using
// Vec<Box<dyn Shape>>. Same LCG, same operation order, same checksum.
// Build: rustc -O shapes.rs
// Usage: shapes [count]
use std::env;

struct Rng {
    state: u64,
}

impl Rng {
    fn next_random(&mut self) -> i64 {
        self.state = self.state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        ((self.state >> 33) & 2147483647) as i64
    }

    fn random_length(&mut self) -> f64 {
        (self.next_random() % 10000) as f64 / 1000.0 + 1.0
    }
}

trait Shape {
    fn area(&self) -> f64;
    fn perimeter(&self) -> f64;
    fn corner_count(&self) -> i64;
}

struct Circle {
    radius: f64,
}
impl Shape for Circle {
    fn area(&self) -> f64 {
        3.141592653589793 * self.radius * self.radius
    }
    fn perimeter(&self) -> f64 {
        2.0 * 3.141592653589793 * self.radius
    }
    fn corner_count(&self) -> i64 {
        0
    }
}

struct Rectangle {
    width: f64,
    height: f64,
}
impl Shape for Rectangle {
    fn area(&self) -> f64 {
        self.width * self.height
    }
    fn perimeter(&self) -> f64 {
        2.0 * (self.width + self.height)
    }
    fn corner_count(&self) -> i64 {
        4
    }
}

struct Triangle {
    side_a: f64,
    side_b: f64,
    side_c: f64,
}
impl Shape for Triangle {
    fn area(&self) -> f64 {
        let half_perimeter = (self.side_a + self.side_b + self.side_c) * 0.5;
        (half_perimeter * (half_perimeter - self.side_a) * (half_perimeter - self.side_b) * (half_perimeter - self.side_c)).sqrt()
    }
    fn perimeter(&self) -> f64 {
        self.side_a + self.side_b + self.side_c
    }
    fn corner_count(&self) -> i64 {
        3
    }
}

struct Polygon {
    xs: Vec<f64>,
    ys: Vec<f64>,
}
impl Shape for Polygon {
    fn area(&self) -> f64 {
        let vertex_count = self.xs.len();
        let mut twice_area = 0.0;
        for i in 0..vertex_count {
            let j = (i + 1) % vertex_count;
            twice_area += self.xs[i] * self.ys[j] - self.xs[j] * self.ys[i];
        }
        if twice_area < 0.0 {
            twice_area = -twice_area;
        }
        twice_area * 0.5
    }
    fn perimeter(&self) -> f64 {
        let vertex_count = self.xs.len();
        let mut total = 0.0;
        for i in 0..vertex_count {
            let j = (i + 1) % vertex_count;
            let delta_x = self.xs[j] - self.xs[i];
            let delta_y = self.ys[j] - self.ys[i];
            total += (delta_x * delta_x + delta_y * delta_y).sqrt();
        }
        total
    }
    fn corner_count(&self) -> i64 {
        self.xs.len() as i64
    }
}

fn make_circle(rng: &mut Rng) -> Box<dyn Shape> {
    Box::new(Circle { radius: rng.random_length() })
}

fn make_rectangle(rng: &mut Rng) -> Box<dyn Shape> {
    let width = rng.random_length();
    let height = rng.random_length();
    Box::new(Rectangle { width, height })
}

fn make_triangle(rng: &mut Rng) -> Box<dyn Shape> {
    let leg_a = rng.random_length();
    let leg_b = rng.random_length();
    Box::new(Triangle { side_a: leg_a, side_b: leg_b, side_c: (leg_a * leg_a + leg_b * leg_b).sqrt() })
}

fn make_polygon(rng: &mut Rng) -> Box<dyn Shape> {
    let vertex_count = rng.next_random() % 4 + 5;
    let mut xs = Vec::with_capacity(vertex_count as usize);
    let mut ys = Vec::with_capacity(vertex_count as usize);
    for _ in 0..vertex_count {
        xs.push(rng.random_length());
        ys.push(rng.random_length());
    }
    Box::new(Polygon { xs, ys })
}

fn main() {
    let arguments: Vec<String> = env::args().collect();
    let count: usize = if arguments.len() > 1 { arguments[1].parse().unwrap() } else { 300000 };
    let rounds: i64 = 20;
    let mut rng = Rng { state: 12345 };

    let monomorphic_shapes: Vec<Box<dyn Shape>> = (0..count).map(|_| make_circle(&mut rng)).collect();
    let bimorphic_shapes: Vec<Box<dyn Shape>> = (0..count)
        .map(|_| if rng.next_random() % 2 == 0 { make_circle(&mut rng) } else { make_rectangle(&mut rng) })
        .collect();
    let megamorphic_shapes: Vec<Box<dyn Shape>> = (0..count)
        .map(|_| match rng.next_random() % 4 {
            0 => make_circle(&mut rng),
            1 => make_rectangle(&mut rng),
            2 => make_triangle(&mut rng),
            _ => make_polygon(&mut rng),
        })
        .collect();

    let mut checksum: i64 = 0;
    for round in 0..rounds {
        let monomorphic_total: f64 = monomorphic_shapes.iter().fold(0.0, |total, shape| total + shape.area());
        let bimorphic_total: f64 = bimorphic_shapes.iter().fold(0.0, |total, shape| total + shape.perimeter());
        let mut megamorphic_total = 0.0;
        let mut corner_total: i64 = 0;
        for shape in &megamorphic_shapes {
            megamorphic_total += shape.area() + shape.perimeter() * 0.5;
            corner_total += shape.corner_count();
        }
        checksum = checksum.wrapping_mul(31).wrapping_add((monomorphic_total * 1000.0) as i64);
        checksum = checksum.wrapping_mul(31).wrapping_add((bimorphic_total * 1000.0) as i64);
        checksum = checksum
            .wrapping_mul(31)
            .wrapping_add((megamorphic_total * 1000.0) as i64)
            .wrapping_add(corner_total)
            .wrapping_add(round);
    }
    println!("{}", checksum);
}
