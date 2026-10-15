# Zephyr for LLM agents: a cheat sheet

A compact guide to writing correct Zephyr on the first try. The full rules are
in [spec.md](spec.md). Every `zephyr` block below is a complete program that
`tests/llm_examples.py` compiles and runs on Linux, so the examples are
known to work.

## Build, run, test

```text
zc run prog.zeph [args...]               compile and run now (Linux: implies --linux --rt)
zc --linux prog.zeph prog && chmod +x prog && ./prog
zc --linux -O2 prog.zeph prog            optimized build
zc --linux --test prog.zeph t && ./t     run the file's test blocks (each test in its own process)
zc --linux --test-filter parse prog.zeph t   only tests whose name contains "parse"
zc --error-format=json ...               compile errors as JSON lines
zc --help
```

- `--linux` implies `--rt` (the runtime). On Windows the default target is a
  PE `.exe` and you pass `--rt` yourself.
- Compile errors: `file:line:col: error: message`, maybe followed by
  `  note: ...` (generic instantiation site) and `  hint: ...`; exit code 2.
  The checker reports up to 20 errors per run, one per statement.
- JSON errors: one object per line on stderr:
  `{"file":"a.zeph","line":3,"col":5,"severity":"error","code":"type","message":"...","hint":null}`.
  `code` is `syntax`, `type`, `import` or `cli`.
- Runtime panics: `panic: file:line: message` on stderr, exit code 1. They
  include the values: `index 7 out of bounds for length 3`,
  `map key "b" not found`, `assertion failed: left == right` with both sides.
- `zc run` on Linux links into memory and execs the program: its exit code is
  the program's.

## Syntax by example

```zephyr
// statements end at a newline: no semicolons
let name = "zephyr"          // immutable binding
var count = 0                // mutable binding
count += 1                   // no ++ / --
const LIMIT = 10             // compile-time constant

fn add(a: int, b: int) -> int {
    return a + b
}

fn greet(who: str, greeting: str = "hello") -> str {   // default parameter
    return "{greeting}, {who}!"                          // interpolation with {expr}
}

print(add(2, 3))             // 5
print(greet(name))           // hello, zephyr!
print("a", 1, true)          // a 1 true  (several values, space separated)

if count > 0 and not (count > LIMIT) {     // and / or / not, never && || !
    print("positive")
} else if count == 0 {
    print("zero")
} else {
    print("negative")
}

let size = if count > 5 { "big" } else { "small" }   // if-expression, no ?:

for i in 0..3 { print(i) }             // 0 1 2 (end exclusive)
for i in 10..0 step -5 { print(i) }    // 10 5
var total = 0
while total < 10 { total += 3 }
for i, x in [10, 20] { print(i, x) }   // index and element
outer: for a in 0..3 {
    for b in 0..3 {
        if b == 2 { continue outer }
        if a == 2 { break outer }
    }
}
print(size, total)
```

## Types

| Type | Example | Notes |
|------|---------|-------|
| `int` | `42`, `0xFF`, `1_000` | 64-bit, wraps on overflow |
| `float` | `3.14`, `1e3` | double; `1.0` prints as `1` |
| `bool` | `true`, `false` | lowercase |
| `str` | `"hi {x}"`, `r"raw\n"`, `"""multi"""` | immutable bytes; `'a'` is an int (97) |
| `[T]` | `[1, 2, 3]`, `[]` with annotation | growable list |
| `[K: V]` | `["a": 1]`, `[:]` with annotation | hash map |
| `T?` | `none`, or any T | optional |
| `(A, B)` | `(1, "x")` | tuple, read with `.0`, `.1` |
| `fn(A) -> R` | `fn(x: int) -> int { return x }` | function value / closure |
| `[u8]`, `[f32]` | `"abc" as [u8]` | packed numeric buffers |

```zephyr
let xs: [int] = []                 // empty literals need a type
var ages: [str: int] = [:]
ages["ann"] = 31
print(ages.has("ann"), ages.get("bob").or(0))   // true 0
let n = "42" as int                // str -> int (panics on bad input)
let f = 7 as float                 // int -> float; ints also widen implicitly
let s = 3.5 as str                 // anything -> str
let t = (1, "one")
let (num, word) = t                // destructuring
print(xs.len(), n, f, s, num, word, t.1)
```

## Structs, enums, methods, interfaces

```zephyr
struct Point { x: float, y: float = 0.0 }      // field default

impl Point {
    fn new(x: float, y: float) -> Point { return Point{x: x, y: y} }  // associated fn
    fn norm(self) -> float { return sqrt(self.x * self.x + self.y * self.y) }
    fn moveBy(self, dx: float) { self.x += dx }                       // structs are references
}

enum Color { Red, Green, Blue }              // plain enum: an int at runtime

enum Shape {                                 // enum with values: a tagged union
    Circle(float)
    Rect(float, float)
    Empty
}

interface Named { fn name(self) -> str }
struct Dog { nick: str }
impl Dog { fn name(self) -> str { return "dog " + self.nick } }

fn area(s: Shape) -> float {
    return match s {                         // arms are `pattern { expr }`, no =>
        Circle(r) { 3.14159 * r * r }
        Rect(w, h) { w * h }
        Empty { 0.0 }
    }
}

let p = Point.new(3.0, 4.0)
p.moveBy(1.0)
print(p, p.norm())                           // Point{x: 4, y: 4} 5.65685424949238
let q = Point{x: 1.0}                        // y takes its default
let c = Color.Green
match c {
    Red { print("red") }
    Green, Blue { print("cool") }            // must cover every member, or use else
}
print(area(Shape.Rect(2.0, 3.0)), Shape.Circle(1.0) is Circle, q.y)
let pets: [Named] = [Dog{nick: "rex"}]       // structural: no `implements`
for pet in pets { print(pet.name()) }
print(c as int, c as str, Color.count)       // 1 Green 3
```

## Optionals instead of null

```zephyr
fn find(xs: [int], target: int) -> int? {
    for i, x in xs { if x == target { return i } }
    return none
}

let at = find([5, 6, 7], 6)
if let i = at { print("found at {i}") } else { print("missing") }
print(find([1], 9).or(-1))           // -1
print(at.has(), at.get(), at == none)
var maybe: str? = none               // `let x = none` needs an annotation
maybe = "now set"
print(maybe)
```

## Generics, closures, function values

```zephyr
import "std/list.zeph"

fn largest[T](items: [T]) -> T {     // type parameters are inferred, never written at the call
    var best = items[0]
    for x in items { if x > best { best = x } }
    return best
}

struct Box[T] { value: T }

fn adder(k: int) -> fn(int) -> int {
    return fn(x: int) -> int { return x + k }    // captures k by value
}

let add3 = adder(3)
print(largest([3, 9, 2]), largest(["a", "c", "b"]), add3(4))
let b = Box{value: "boxed"}
print(b.value)
let doubled = [1, 2, 3].map(fn(x: int) -> int { return x * 2 })   // UFCS: map(xs, f)
let evens = [1, 2, 3, 4].filter(fn(x: int) -> bool { return x % 2 == 0 })
print(doubled, evens, [1, 2, 3].contains(2), sum([1, 2, 3]))
var words = ["pear", "fig", "apple"]
words.sortBy(fn(a: str, b: str) -> int { return a.len() - b.len() })
print(words)
```

Closures capture by value: assigning to a captured local is an error. Use a
global, or return the new value. A generic function cannot be used as a value.

## Strings and lists

```zephyr
let s = "  Hello, World  ".trim()
print(s.len(), s.upper(), s.lower(), s.contains("World"), s.indexOf("o"))
print(s.startsWith("He"), s.endsWith("!"), s.replace("World", "Zephyr"))
print(s.split(", "), s.sub(0, 5), s.byte(0), chr(72), "ab".repeat(2))
for b in "hi" { print(b) }                    // bytes as ints: 104 105
var parts: [str] = []
parts.push("a")
parts.push("b")
print(parts.join(), parts.join("-"), parts.pop(), parts.len())
var nums = [3, 1, 2]
nums.sort()
print(nums, nums[0], zeros(3), min(2, 5), max(2.5, 1), abs(-4), pow(2, 10))
let text = """
    line one
    line two
    """
print(text)
```

## Modules and tests

```zephyr
import "std/string.zeph"              // plain import: names join this namespace
import "std/math.zeph" as m           // qualified: m.floor(...)

private fn helper() -> int { return 1 }   // visible in this file only

fn main() {                           // called after top-level code, if defined
    print(padLeft("7", 3, "0"), m.floor(2.7), helper(), parseInt("12").or(0))
}

test "padding" {                      // run with zc --test; ignored otherwise
    assert(padLeft("7", 3, "0") == "007")
}
```

## Memory and reference counting

- `int`, `float`, `bool` are values. `str`, lists, maps, structs, enums with
  values and closures are references: assignment and argument passing share
  the object, they do not copy it.
- Memory is reclaimed by compiler-inserted reference counting; there is no
  free, no retain, no annotation. Cycles (a struct reachable from itself) are
  only reclaimed by a backstop collector, so avoid them in long-running code.
- No null, no uninitialized values: every field must be given (or have a
  default) and every index is bounds-checked.
- `let` makes the binding immutable, not the object: a `let` list can still
  `push`, a `let` struct's fields can still change.

```zephyr
struct Counter { n: int }
fn bump(c: Counter) { c.n += 1 }       // mutates the caller's object
let c = Counter{n: 0}
bump(c)
let alias = c
alias.n += 10
print(c.n)                              // 11: one object, two references
let xs = [1, 2]
var copy: [int] = []
for x in xs { copy.push(x) }            // copy explicitly when you need a copy
copy.push(3)
print(xs, copy)
```

## Threads

Threads come from `std/thread.zeph`. A worker receives an `int` (an index or
an off-heap address), never a heap reference: counts are not atomic. Share
data through off-heap memory (`std/bytes.zeph`) or `std/sync.zeph` wrappers,
and join every worker.

```zephyr
import "std/thread.zeph"
import "std/sync.zeph"
import "std/bytes.zeph"

let results = Bytes.new(8 * 4)          // off-heap: 4 int slots
let resultsAddress = results.addr()
let total = newAtomic(0)
let totalAddress = total.address

parallelFor(4, fn(worker: int) {
    store64(resultsAddress + worker * 8, worker * worker)   // each worker owns its slot
    let shared = Atomic{address: totalAddress}               // rebuild the wrapper locally
    let previous = shared.add(worker)
})
var squares: [int] = []
for i in 0..4 { squares.push(results.get64(i * 8)) }
print(squares, total.load())             // [0, 1, 4, 9] 6

let t = spawnThread(fn(arg: int) { let unused = arg }, 7)
t.join()
```

## FFI and raw memory (unsafe)

```zephyr
import "std/bytes.zeph"

extern fn hypot(x: float, y: float) -> float from "libm.so.6"   // Linux: dlopen + dlsym
extern fn strlen(text: int) -> int from "libc.so.6"

let message = cString("hello")           // NUL-terminated off-heap copy
print(hypot(3.0, 4.0), strlen(message.addr()))
let buffer = Bytes.new(16)
buffer.put32(0, 1234)
buffer.putFloat64(8, 2.5)
print(buffer.get32(0), buffer.getFloat64(8))
let pid = syscall(39)                     // raw Linux syscall (getpid)
print(pid > 0)
```

Parameters of `extern fn` are `int` (integers, pointers) or `float` (C
`double`); the result is `int`, `i32`, `bool`, `float` or nothing. Pass
structs by pointer into `Bytes` memory. `load64/store64/load8/store8`,
`addr(x)` and `callPointer` bypass every safety guarantee.

## Standard library (import "std/NAME.zeph")

- `list`: `contains(xs, x)`, `indexOf(xs, x) -> int`, `reverse(xs)`,
  `slice(xs, lo, hi) -> [T]`, `first(xs) -> T?`, `last(xs) -> T?`,
  `map(xs, f) -> [U]`, `filter(xs, f) -> [T]`, `fold(xs, start, f) -> A`,
  `any(xs, f)`, `all(xs, f)`, `count(xs, x) -> int`, `sortBy(xs, cmp)` (cmp
  returns <0, 0, >0), `sum(xs)`, `minOf(xs)`, `maxOf(xs)`.
- `string`: `isDigit(b)`, `isAlpha(b)`, `isWhitespace(b)`, `ord(s) -> int`,
  `chars(s) -> [str]`, `reverseString(s)`, `trimLeft(s)`, `trimRight(s)`,
  `joinWith(parts, sep)`, `padLeft(s, width, fill)`, `padRight(...)`,
  `lines(s) -> [str]`, `toHex(n)`, `toBinary(n)`, `parseInt(s) -> int?`,
  `parseFloat(s) -> float?`, `formatFixed(x, decimals) -> str`.
- `math`: `pi`, `nan`, `infinity`, `floor`, `ceil`, `round`, `trunc`,
  `clamp(x, lo, hi)`, `clampInt`, `exp`, `ln`, `log10`, `log2`,
  `powf(b, e)`, `fmod`, `atan2(y, x)`, `hypot`, `cbrt`, `fsin`, `fcos`,
  `ftan`, `fatan`, `fasin`, `facos`, `isNan(x)`, `isInfinite(x)`.
  (`sqrt`, `abs`, `min`, `max`, `pow` are builtins.)
- `random`: `newRng(seed) -> Rng`, `rng.nextInt()`, `rng.intBetween(lo, hi)`,
  `rng.nextFloat()`, `rng.chance(p) -> bool`, `rng.shuffle(xs)`.
- `result`: `enum Result[T, E] { Ok(T), Err(E) }` with `isOk()`,
  `isError()`, `unwrap()`, `unwrapOr(d)`, `ok() -> T?`, `error() -> E?`,
  `map(f)`, `mapError(f)`, `andThen(f)`.
- `set`: `Set[T]` with `Set.new()`, `setOf(xs)`, `add`, `has`, `remove`,
  `len`, `items() -> [T]`, `union`, `intersection`, `difference`, `isSubset`.
- `io`: `readLine() -> str?`, `printError(s)`, `exit(code)`,
  `appendFile(path, s)`, `fileExists(path)`, `deleteFile(path)`,
  `listDirectory(path) -> [str]`, `nowMilliseconds()`, `nowNanoseconds()`,
  `sleepMilliseconds(ms)`. Builtins: `readFile(path)`, `writeFile(path, s)`,
  `args() -> [str]` (`args()[0]` is the program).
- `bytes`: `Bytes.new(n)`, `b.put8/16/32/64(off, v)`, `b.get8/16/32/64(off)`,
  `putFloat32/getFloat32`, `putFloat64/getFloat64`, `putString`,
  `getString(off, len)`, `b.addr()`, `cString(s) -> Bytes`.
- `thread`: `spawnThread(f, arg) -> Thread`, `t.join()`, `parallelFor(n, f)`,
  `cpuCount()`. `sync`: `newMutex()` (`lock`, `unlock`, `tryLock`),
  `newAtomic(v)` (`load`, `store`, `add`, `swap`, `compareExchange`),
  `newChannel(capacity)` (`send`, `receive() -> int?`, `tryReceive`, `close`),
  `newWaitGroup()` (`add`, `done`, `wait`).
- `linux`: `openPath`, `readAll(fd)`, `closeFd`, `memOpen(pid)`, `memRead`,
  `memWrite`, `vmRead`, `vmWrite`, `monotonicNanoseconds()`.
- `io` also: `tryReadFile(path) -> Result[str, str]`,
  `tryWriteFile(path, s) -> Result[int, str]` (errors like
  `"open x: no such file or directory"`), `environmentVariable(name) -> str?`,
  `run(command) -> int` (Linux: `/bin/sh -c`, exit code).
- `utf8`: `utf8RuneCount`, `utf8Codepoints`, `utf8Encode`, `utf8IsValid`,
  `utf8Sub(s, start, end)`, `utf8Truncate(s, n)`, `utf8TruncateBytes`,
  `utf8DisplayWidth`, `utf8Fit(s, columns)`, `utf8PadLeft/Right`.
- `json`: `jsonParse(s) -> Result[Json, str]`, `jsonTryParse(s) -> Json?`,
  `j.path("choices[0].delta.content")`, `jsonGetStr(j, path) -> str?`
  (also Int/Float/Bool), `j.get/at/asStr/asInt/items/keys`,
  `jsonObject().set(k, v)`, `jsonArray().add(v)`, `jsonText/jsonInt/jsonBool`,
  `jsonStringify(j)`, `jsonPretty(j, 2)`, `jsonParsePartial(prefix)`,
  `jsonPartialString(prefix, key)` for streamed tool-call arguments.
- `process` (Linux): `spawn(argv, SpawnOptions{}) -> Result[Process, str]`,
  `p.write(s) -> bool`, `p.closeStdin()`, `p.readAvailable(timeoutMs) -> str`,
  `p.readAll() -> str` (stderr lands in `p.stderrText`), `p.wait() -> int`,
  `p.tryWait() -> int?`, `p.kill()`, `runCapture(argv)` ->
  `ProcessOutput{code, stdout, stderr}`. Options: `environment: [str: str]`,
  `clearEnvironment`, `directory`, `mergeStderr`.
- `net` (Linux): `tcpConnect(host, port, timeoutMs) -> Result[TcpConnection, str]`,
  `conn.send(s) -> Result[int, str]`, `conn.recv(max) -> Result[str, str]`
  (`Ok("")` = closed), `conn.recvAll()`, `conn.close()`, `resolveHost(host)`.
- `http` (Linux): `request(method, url, headers, body) -> Result[Response, str]`
  (`r.status`, `r.body`, `r.header(name)`), `requestWith(..., HttpOptions{})`,
  `requestStream(..., options, fn(chunk: str) -> bool)`,
  `requestEvents(..., options, fn(event: SseEvent) -> bool)` for SSE
  (`event.event`, `event.data`, `event.id`; return false to stop). https://
  needs libcurl.so.4 at run time. An HTTP error status is still `Ok`.
  Write `{` in string literals as `\{` (JSON bodies): `"\{\"a\": 1}"`.

## Common mistakes and the correct form

| Wrong (other languages) | Right (Zephyr) |
|-------------------------|----------------|
| `a && b`, `a \|\| b`, `!a` | `a and b`, `a or b`, `not a` |
| `i++`, `i--` | `i += 1`, `i -= 1` |
| `x = 1;` | `x = 1` (newline ends a statement) |
| `let mut x = 0` | `var x = 0` |
| `null`, `nil`, `None` | an optional: `let x: int? = none` |
| `True`, `False` | `true`, `false` |
| `len(xs)`, `xs.length` | `xs.len()` |
| `str(x)`, `x.toString()` | `x as str` or `"{x}"` |
| `int("4")` | `"4" as int`, or `parseInt("4")` (std/string) for an `int?` |
| `string`, `i64`, `double` | `str`, `int`, `float` |
| `cond ? a : b` | `if cond { a } else { b }` |
| `match x { 1 => ... }` | `match x { 1 { ... } else { ... } }` |
| `for (i = 0; i < n; i++)` | `for i in 0..n { ... }` |
| `range(n)` | `0..n` |
| `xs.append(x)` | `xs.push(x)` |
| `let xs = []` | `let xs: [int] = []` |
| `first<int>(xs)` / `first[int](xs)` | `first(xs)`: type arguments are inferred |
| `"a" + 1` | `"a{1}"` or `"a" + (1 as str)` |
| `try`/`catch`, exceptions | return `T?` or `Result[T, E]`; panics are not catchable |
| assigning a captured variable in a closure | use a global, a struct field, or return the value |
| passing a list to `spawnThread` | pass an `int` index or an off-heap `Bytes` address |
| `fn` inside an `impl` without `self` called as `x.f()` | associated functions are `Type.f()` |

Other gotchas:

- A struct literal right after `if`/`while`/`for` needs parentheses:
  `if p == (Point{x: 1.0}) { ... }`.
- `x.f(y)` is UFCS: it calls a method `Type.f`, else a free function
  `f(x, y)`. That is how `std/list` functions read as methods.
- Integer `/` truncates toward zero; `/` and `%` by zero panic. `%` on
  floats is an error (use `fmod` from std/math).
- A function with a return type must return on every path (or `panic`).
- Reading a missing map key panics: use `.has(k)` or `.get(k).or(d)`.
- Strings are bytes: `.len()` counts bytes, `.byte(i)` is an int.
