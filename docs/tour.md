# A tour of Zephyr

Everything you need to write Zephyr, in ten minutes. Statements end at the end
of the line — no semicolons. Comments start with `//`.

## Hello

```zephyr
let name = "Zephyr"
print("Hello, {name}!")
```

Any expression can be interpolated into a string with `{...}`. `print` accepts
a value of any type and formats it sensibly.

## Variables: `let` and `var`

```zephyr
let x = 3          // immutable binding, type inferred (int)
var y = 2.5        // mutable binding (float)
y = y + 1.0        // ok
// x = 4           // compile error: 'x' is immutable
let z: float = 1   // explicit annotation; int widens to float
```

Every variable must be initialized — there is no null, and no way to read an
undefined value. `let` fixes the *binding*: a `let` list or struct can still
have its contents mutated (they are references), you just can't reassign the
name.

## Types

| Type      | Example              |
|-----------|----------------------|
| `int`     | `42`, `-7` (64-bit)  |
| `float`   | `3.14` (64-bit IEEE) |
| `bool`    | `true`, `false`      |
| `str`     | `"hi\n"`             |
| `[T]`     | `[1, 2, 3]` (list)   |
| `[K: V]`  | `["a": 1]` (hash map) |
| `T?`      | `none` or a `T` (optional) |
| `fn(T) -> R` | a function value / closure |
| structs   | `Point{x: 1.0, y: 2.0}` |
| enums     | `Color.Red` |

The composite types (maps, optionals, closures, generics, `enum`) are covered
below; the full rules are in the [spec](spec.md).

## Conversions

`int` widens to `float` implicitly (`1 + 2.5` is `3.5`). Everything else is
explicit with `as`:

```zephyr
let n = 42
print(n as float / 4.0)     // 10.5
print(-7.9 as int)          // -7  (truncates toward zero)
let pi = "3.14" as float    // parses; panics on bad input
let msg = "n = " + (n as str)
```

`as` binds tighter than arithmetic: `n as float / 4.0` is `(n as float) / 4.0`.
The full conversion table is in the [spec](spec.md#conversions).

## Operators

Arithmetic `+ - * / %`, bitwise `& | ^ << >>` (int only; `<<`/`>>` are
arithmetic shifts), comparison `== != < <= > >=`, logic `and or not`.
Bitwise precedence follows Go: `& << >>` bind like `*`, `| ^` bind like `+`.
Conditions must be `bool` — `if 1 { ... }` is a compile error, not a truthiness
puzzle. `/` and `%` on two ints are integer operations (and panic on zero);
involve a float and you get float division. `+` also concatenates strings.
Compound assignment `+= -= *= /=` works on any assignable target.

## Control flow

```zephyr
if score >= 90 { print("A") }
else if score >= 80 { print("B") }
else { print("C") }

var n = 10
while n > 0 { n -= 1 }

for i in 0..5 {          // 0, 1, 2, 3, 4 — half-open range
    if i == 3 { break }
    if i == 1 { continue }
    print(i)
}

for word in ["a", "b"] {  // iterate any list
    print(word)
}
```

## Functions

```zephyr
fn clamp(x: int, lo: int, hi: int) -> int {
    if x < lo { return lo }
    if x > hi { return hi }
    return x
}
```

Parameter and return types are required (omit `->` for no return value). The
compiler verifies that every path returns. Functions can be called before
they're defined.

## Lists

```zephyr
let xs = [10, 20, 30]
print(xs[1])          // 20 — bounds-checked; xs[99] panics, never corrupts
print(xs.len())       // 3
xs.push(40)
print(xs.pop())       // 40
var empty: [str] = [] // empty literals need a type annotation
```

## Structs and methods

```zephyr
struct Point { x: float, y: float }

fn scale(p: Point, k: float) -> Point {
    return Point{x: p.x * k, y: p.y * k}
}

let p = Point{x: 3.0, y: 4.0}
let q = p.scale(2.0)     // any function is callable as a method on its
let r = scale(p, 2.0)    // first argument — these are the same call
print(q)                 // Point{x: 6, y: 8}
```

Struct literals must initialize every field. Structs are reference types
allocated on the GC heap.

## Globals

Top-level `let`/`var` declarations are globals, visible inside every function
declared **after** them (declare globals before the functions that use them).
Declarations inside a top-level `if`/`for`/`while` block stay local.

```zephyr
var hits = 0
fn record() { hits += 1 }
record()
print(hits)   // 1
```

## More types: enums, maps, optionals

```zephyr
enum Color { Red, Green, Blue }   // distinct type; prints its member name
let c = Color.Green
print(c)                          // Green
print(c == Color.Green)           // true

var ages: [str: int] = ["ana": 30]   // hash map
ages["ben"] = 25
print(ages.has("ben"))            // true
print(ages.get("nope").or(0))     // 0 — safe lookup returns an optional

fn first_even(xs: [int]) -> int? {   // T? holds a value or `none`
    for x in xs { if x % 2 == 0 { return x } }
    return none
}
print(first_even([1, 3, 4]).or(-1))  // 4
```

An optional must be unwrapped (`.or(default)`, `.get()`, `.has()`) before use —
it is not a plain `T`.

## Closures and generics

```zephyr
fn adder(k: int) -> fn(int) -> int {
    return fn(x: int) -> int { return x + k }   // captures k by value
}
let add3 = adder(3)
print(add3(10))                  // 13

fn contains[T](xs: [T], x: T) -> bool {   // type parameter, inferred at the call
    for v in xs { if v == x { return true } }
    return false
}
print([1, 2, 3].contains(2))     // true
print(["a", "b"].contains("z"))  // false — same code, monomorphised per type
```

Functions are first-class values (`let g = adder`), and generics are inferred
from the arguments — never written at the call site.

## Multiple files

```zephyr
import "std/list.zeph"     // splices that file's declarations in; used unqualified
import "sub/mathx.zeph"    // paths are relative to the importing file
```

`std/list.zeph` is the standard library — `map`, `filter`, `fold`, `sort_by`,
`contains` and friends — written as ordinary generic Zephyr, not baked into the
compiler.

## Errors

Zephyr has no exceptions. Unrecoverable errors **panic**: a message to stderr
and exit code 1. Panics come from `panic("msg")`, out-of-bounds indexing,
division by zero, popping an empty list, or a failed `str` parse in `as`.

## Builtins

Functions: `print(v)`, `emit(s)` (stdout without a newline — use it to stream
large output instead of assembling one huge string), `panic(msg)`, `sqrt(x)`,
`chr(code)` (byte → 1-char str), `bits(f)` (float → its IEEE bit pattern as
int), `args()` (command-line arguments as `[str]`), `read_file(path)`,
`write_file(path, data)`.

Methods: `.len()` (list or str), `.push(v)`, `.pop()`, `.byte(i)` (str byte
as int, bounds-checked), `.sub(lo, hi)` (substring, half-open), `.join()`
(concatenate a `[str]` in one pass — use this instead of `+` in loops).

These are enough to write real programs — the Zephyr compiler itself
([compiler/zc.zeph](../compiler/zc.zeph)) is written with them.

## Beyond the basics

This tour covers the safe core. Three things it deliberately skips, each in the
[specification](spec.md):

- **Other targets** — the same source also compiles to a static Linux ELF
  (`--linux`) and to WebAssembly (`--wasm`), not just a Windows `.exe`. (§7)
- **Native interop** — `win("user32!MessageBoxA", …)`, `extern fn … from
  "x.dll"`, and raw-memory builtins let pure Zephyr call the OS and the GPU.
  This is unsafe by nature; the `Bytes` type in `lib/std/bytes.zeph` is the
  checked way to use it. (§3.6)
- **Threads** — `std/thread.zeph` gives `thread_spawn` and `parallel_for`. (§8)

Those primitives are what the `lib/vk` Vulkan wrapper and the graphics demos
are built from — see [docs/graphics.md](graphics.md).
