# Zephyr standard library

Import only the modules you need. Compile native examples with `zc.exe --rt example.zeph example.exe`; add `--linux` for Linux output. Functions can also be called through UFCS (`values.sum()`, `generator.next_int()`). Strings are byte strings, and integer values are signed 64-bit.

## string.zeph

```zeph
import "std/string.zeph"
```

All character operations work on bytes, not Unicode code points. Whitespace means space, tab, LF, and CR.

| Signature | Description |
| --- | --- |
| `reverse_str(text: str) -> str` | Reverse the bytes. |
| `ord(text: str) -> int` | First byte value; panic on empty input. |
| `trim_left(text: str) -> str` | Remove leading whitespace. |
| `trim_right(text: str) -> str` | Remove trailing whitespace. |
| `join_with(parts: [str], separator: str) -> str` | Join strings with a separator; empty list gives an empty string. |
| `pad_left(text: str, width: int, fill: str) -> str` | Pad on the left to the requested byte width with a one-byte fill. |
| `pad_right(text: str, width: int, fill: str) -> str` | Pad on the right; strings already wide enough are unchanged. |
| `fmt_fixed(value: float, decimals: int) -> str` | Format with nonnegative decimal places, rounding the exact binary value half away from zero. |
| `to_hex(value: int) -> str` | Lowercase hexadecimal without prefix; negatives use 16 two's-complement digits. |
| `to_binary(value: int) -> str` | Binary without prefix; negatives use 64 two's-complement digits. |
| `is_digit(byteValue: int) -> bool` | Test ASCII 0 through 9. |
| `is_alpha(byteValue: int) -> bool` | Test ASCII letters. |
| `is_alnum(byteValue: int) -> bool` | Test ASCII letters or digits. |
| `is_space(byteValue: int) -> bool` | Test space, tab, LF, or CR. |
| `is_upper(byteValue: int) -> bool` | Test ASCII uppercase letters. |
| `is_lower(byteValue: int) -> bool` | Test ASCII lowercase letters. |
| `chars(text: str) -> [str]` | Return one single-byte string per input byte. |
| `lines(text: str) -> [str]` | Split on LF and strip one trailing CR per line; preserve empty fields, including a final one. |
| `parse_int(text: str) -> int?` | Parse signed decimal with surrounding whitespace; return none for invalid syntax or overflow. |
| `parse_float(text: str) -> float?` | Parse signed decimal with optional fraction and exponent; return none for invalid syntax or overflow. |

Float parsing accepts `.5`, `1.`, and `1e3`; underflow produces signed zero. Fixed formatting rounds the stored binary float, so `fmt_fixed(2.675, 2)` is `"2.67"`.

Implementation helpers are callable because Zephyr has no private functions; applications should use the public operations above.

| Signature | Description |
| --- | --- |
| `string_fraction_bit(fraction: [int]) -> int` | Double decimal fraction digits in place and return the next binary bit. |
| `string_nonzero(digits: [int]) -> bool` | Test whether any decimal digit is nonzero. |
| `string_decimal_float(digits: [int], decimalPoint: int, sign: int) -> float?` | Convert decimal digits to a correctly rounded double, returning none on overflow. |
| `string_scale_digits(digits: [int], factor: int)` | Multiply decimal digits in place, least-significant digit first. |

```zeph
print(join_with(["red", "blue"], ", "))
print(fmt_fixed(parse_float("3.14159").get(), 2)) // 3.14
```

## random.zeph

```zeph
import "std/random.zeph"
```

The mutable `Rng { state: int }` uses xorshift64* with shifts 12, 25, 27 and multiplier 2685821657736338717. Its state period is 2^64-1; zero seed maps to a fixed nonzero state. Equal seeds give equal sequences. This generator is not cryptographic and must not be shared between threads without synchronization.

| Signature | Description |
| --- | --- |
| `rng_new(seed: int) -> Rng` | Create a deterministic generator. |
| `next_int(rng: Rng) -> int` | Advance state and return a full-width signed 64-bit result. |
| `int_between(rng: Rng, low: int, high: int) -> int` | Rejection-sample an unbiased integer in [low, high); panic unless low < high. |
| `next_float(rng: Rng) -> float` | Return a value in [0, 1) using 53 random bits. |
| `chance(rng: Rng, probability: float) -> bool` | Return true with the given probability; require 0 <= probability <= 1. |
| `shuffle[T](rng: Rng, items: [T])` | Shuffle in place with Fisher-Yates. |

```zeph
let generator = rng_new(42)
print(generator.int_between(1, 7))
let cards = ["a", "b", "c"]
generator.shuffle(cards)
```

## io.zeph

```zeph
import "std/io.zeph"
```

Typed kernel32 wrappers use the Linux syscall shim under `--linux`. All functions below work on Windows. Linux supports everything except `env` and `run`, which panic with clear "not supported on linux" messages. Linux output was compiled, but execution requires a Linux host. Paths and environment names reject embedded NUL bytes.

| Signature | Description |
| --- | --- |
| `read_line() -> str?` | Read stdin through LF, strip LF and one trailing CR; return none at EOF before any bytes. |
| `eprint(text: str)` | Write to stderr with a newline. |
| `exit(code: int)` | Terminate the process with the requested status. |
| `append_file(path: str, data: str)` | Append bytes, creating the file if absent; panic on failure. |
| `file_exists(path: str) -> bool` | Test whether the path exists. |
| `delete_file(path: str) -> bool` | Delete a file and report success. |
| `list_dir(path: str) -> [str]` | Return names only, excluding dot entries; panic if enumeration fails. |
| `env(name: str) -> str?` | Read an environment variable; missing is none, present empty is an empty string. |
| `now_ms() -> int` | Monotonic milliseconds with an unspecified origin. |
| `now_ns() -> int` | Monotonic nanoseconds, using QueryPerformanceCounter on Windows; precision depends on the clock. |
| `sleep_ms(milliseconds: int)` | Sleep for 0 <= milliseconds < 4294967295; panic outside that range. |
| `run(command: str) -> int` | Run a Windows command line, wait, and return its exit code; panic if launch fails. |

Commands are raw Windows command lines; invoke `cmd.exe /c` explicitly for shell syntax. Directory ordering is unspecified. Relative paths resolve from the process working directory.

The test suite includes a Linux compile-only check that validates the generated ELF header and references all I/O wrappers. It does not execute Linux binaries; Linux runtime behavior remains unverified in this Windows environment.

Implementation helpers are callable because Zephyr has no private functions:

| Signature | Description |
| --- | --- |
| `io_cstring(value: str) -> Bytes` | Reject embedded NUL and create a retained C string. |
| `io_write(handle: int, data: str)` | Write all bytes to a handle, handling partial writes and panicking on failure. |

```zeph
append_file("events.txt", "started\n")
let started = now_ms()
sleep_ms(20)
print(now_ms() - started)
```

## list.zeph

```zeph
import "std/list.zeph"
```

Generic operations are checked against the element type when instantiated. Reductions require a nonempty list. Sort comparison returns negative, zero, or positive for before, equivalent, or after.

| Signature | Description |
| --- | --- |
| `contains[T](items: [T], target: T) -> bool` | Test membership. |
| `indexOf[T](items: [T], target: T) -> int` | First matching index, or -1. |
| `reverse[T](items: [T])` | Reverse in place. |
| `slice[T](items: [T], low: int, high: int) -> [T]` | Copy [low, high); panic for invalid bounds. |
| `first[T](items: [T]) -> T?` | First element, or none. |
| `last[T](items: [T]) -> T?` | Last element, or none. |
| `map[T, U](items: [T], transform: fn(T) -> U) -> [U]` | Transform each element. |
| `filter[T](items: [T], keep: fn(T) -> bool) -> [T]` | Copy matching elements. |
| `fold[T, A](items: [T], start: A, combine: fn(A, T) -> A) -> A` | Reduce from an explicit initial accumulator. |
| `any[T](items: [T], predicate: fn(T) -> bool) -> bool` | Test whether at least one element matches. |
| `all[T](items: [T], predicate: fn(T) -> bool) -> bool` | Test whether every element matches; true on empty lists. |
| `count[T](items: [T], target: T) -> int` | Count equal elements. |
| `sortBy[T](items: [T], compare: fn(T, T) -> int)` | Stable in-place merge sort: O(n log n) comparisons and O(n) scratch storage. |
| `sum[T](items: [T]) -> T` | Add elements; panic on empty input. |
| `min_of[T](items: [T]) -> T` | Smallest element; panic on empty input. |
| `max_of[T](items: [T]) -> T` | Largest element; panic on empty input. |

```zeph
let values = [3, 1, 2]
sortBy(values, fn(left: int, right: int) -> int { return left - right })
print(values.sum()) // 6
```

## result.zeph

```zeph
import "std/result.zeph"
```

`enum Result[T, E] { Ok(T), Err(E) }`: what a function that can fail returns. Match on it (`Ok(value) { ... } Err(error) { ... }`) or use the methods.

| Signature | Description |
| --- | --- |
| `r.is_ok() -> bool` / `r.is_err() -> bool` | Which member it is. |
| `r.unwrap() -> T` | The value; panic with the error on Err. |
| `r.unwrap_or(fallback: T) -> T` | The value, or fallback. |
| `r.ok() -> T?` / `r.err() -> E?` | One side as an optional. |
| `r.map[U](transform: fn(T) -> U) -> Result[U, E]` | Transform the value; an Err passes through. |
| `r.map_err[F](transform: fn(E) -> F) -> Result[T, F]` | Transform the error; an Ok passes through. |
| `r.and_then[U](next: fn(T) -> Result[U, E]) -> Result[U, E]` | Chain a step that can fail; the first Err wins. |

```zeph
fn parse_port(text: str) -> Result[int, str] {
    let port = text as int
    if port < 1 or port > 65535 { return Result.Err("not a port: {text}") }
    return Result.Ok(port)
}
print(parse_port("8080").unwrap_or(80)) // 8080
```

## set.zeph

```zeph
import "std/set.zeph"
```

`struct Set[T]`: distinct values, backed by a `[T: bool]` map, so `T` must be a valid map key.

| Signature | Description |
| --- | --- |
| `set_of[T](items: [T]) -> Set[T]` | A set of the distinct items. |
| `Set.new() -> Set[T]` | An empty set; `T` comes from the expected type (`let s: Set[int] = Set.new()`). |
| `s.add(item: T)` / `s.remove(item: T)` | Insert or delete (no-ops when already so). |
| `s.has(item: T) -> bool` | Membership, O(1). |
| `s.len() -> int` | Number of items. |
| `s.items() -> [T]` | The items, in no particular order. |
| `s.union(other) -> Set[T]` / `s.intersection(other)` / `s.difference(other)` | New sets. |
| `s.is_subset(other) -> bool` | Every item of `s` is in `other`. |

## bytes.zeph

```zeph
import "std/bytes.zeph"
```

Raw fixed-size buffers are reference-counted and non-moving, with a GC backstop. Keep a `Bytes` value reachable while foreign code holds its address. Accessors bounds-check. Integer encodings are little-endian.

| Signature | Description |
| --- | --- |
| `Bytes.new(n: int) -> Bytes` | Allocate n zero-filled bytes aligned to 16 bytes. |
| `Bytes.len() -> int` | Buffer length in bytes. |
| `Bytes.addr() -> int` | Address of byte zero. |
| `Bytes.at(off: int) -> int` | Address at an offset, including the end pointer. |
| `Bytes.put8(off: int, v: int)` | Store one byte. |
| `Bytes.get8(off: int) -> int` | Read one unsigned byte. |
| `Bytes.put16(off: int, v: int)` | Store 16 bits. |
| `Bytes.get16(off: int) -> int` | Read an unsigned 16-bit value. |
| `Bytes.put32(off: int, v: int)` | Store 32 bits. |
| `Bytes.get32(off: int) -> int` | Read a zero-extended 32-bit value. |
| `Bytes.put64(off: int, v: int)` | Store 64 bits. |
| `Bytes.get64(off: int) -> int` | Read 64 bits. |
| `Bytes.putf32(off: int, x: float)` | Store an IEEE-754 single. |
| `Bytes.getf32(off: int) -> float` | Read an IEEE-754 single as a double. |
| `Bytes.putf64(off: int, x: float)` | Store an IEEE-754 double. |
| `Bytes.getf64(off: int) -> float` | Read an IEEE-754 double. |
| `Bytes.put_cstr(off: int, s: str)` | Copy bytes and append NUL. |
| `Bytes.put_str(off: int, s: str)` | Copy bytes without a terminator. |
| `Bytes.get_str(off: int, n: int) -> str` | Copy n bytes to a string. |
| `cbytes(s: str) -> Bytes` | Allocate a NUL-terminated copy. |
| `u64s(xs: [int]) -> Bytes` | Build a contiguous 64-bit array. |
| `u32s(xs: [int]) -> Bytes` | Build a contiguous 32-bit array. |
| `pack(items: [Bytes]) -> Bytes` | Pack equally sized byte buffers contiguously. |
| `cstrs(xs: [str]) -> CStrs` | Build a retained array of C-string pointers and buffers. |
| `CStrs.addr() -> int` | Address of pointer array, or zero if empty. |
| `CStrs.len() -> int` | Number of strings. |
| `f32_bits(x: float) -> int` | Convert double to single bits, rounding ties to even. |
| `f32_from(v: int) -> float` | Decode single bits into a double. |

```zeph
let buffer = Bytes.new(16)
buffer.put64(0, 42)
print(buffer.get64(0))
```

## thread.zeph

```zeph
import "std/thread.zeph"
```

Windows and Linux x86-64 workers receive an integer argument and require `--rt`. Thread closures stay rooted until joined; join every spawned thread. Share only off-heap values through integer addresses, never counted heap objects. Use `std/sync.zeph` for shared mutation.

| Signature | Description |
| --- | --- |
| `thread_spawn(threadFunction: fn(int), argument: int) -> Thread` | Start a worker and register it with the runtime collector. |
| `Thread.join()` | Wait for completion and release the worker's retained resources. |
| `parallel_for(workerCount: int, workerFunction: fn(int))` | Spawn one worker for each index in [0, workerCount), then join all. |
| `cpu_count() -> int` | Return the system processor count, falling back to one. |

Implementation helpers: `body_slot(threadBody: fn(int)) -> int` reserves a rooted closure slot; `tx_thunk() -> int` obtains the native calling-convention adapter. Applications should use the operations above.

```zeph
fn worker(index: int) { print(index) }
let task = thread_spawn(worker, 7)
task.join()
```

## sync.zeph

```zeph
import "std/sync.zeph"
```

Windows and Linux x86-64 synchronization uses off-heap native memory. Atomics and channels hold `int` values; encode floats with `bits` and decode with `floatFromBits`. The `Mutex`, `Atomic`, `Channel`, and `WaitGroup` wrappers are counted heap objects: pass or capture their integer `address` fields and construct a local wrapper in each worker. Never share the wrapper itself or send a counted heap object's address. Native allocations last until process exit; there is no explicit destruction API.

| Signature | Description |
| --- | --- |
| `mutex_new() -> Mutex` | Create a recursive mutex. |
| `Mutex.lock()` | Block until owned by this thread. |
| `Mutex.unlock()` | Release one acquisition; only the owner may unlock. |
| `Mutex.try_lock() -> bool` | Acquire immediately if available or already owned by this thread. |
| `atomic_new(initial: int) -> Atomic` | Create an aligned 64-bit cell. |
| `Atomic.load() -> int` | Atomic read with x86 acquire ordering. |
| `Atomic.store(value: int)` | Atomic write with x86 release ordering. |
| `Atomic.add(delta: int) -> int` | Lock-free addition; return the new value, wrapping on overflow. |
| `Atomic.swap(value: int) -> int` | Lock-free exchange; return the old value. |
| `Atomic.compare_exchange(expected: int, replacement: int) -> bool` | Replace only if equal; report success. |
| `channel_new(capacity: int) -> Channel` | Create a bounded FIFO; panic for nonpositive or overflowing capacity. |
| `Channel.send(value: int)` | Wait for space and enqueue; panic if closed, including while waiting. |
| `Channel.receive() -> int?` | Wait for a value; return none once closed and drained. |
| `Channel.try_receive() -> int?` | Return the oldest queued value, or none if empty or the channel lock is contended; never block. |
| `Channel.close()` | Close idempotently and wake blocked senders and receivers; queued values remain readable. |
| `Channel.len() -> int` | Return a synchronized snapshot of the queued count. |
| `wait_group_new() -> WaitGroup` | Create a group with zero outstanding work. |
| `WaitGroup.add(amount: int)` | Adjust outstanding work; panic on underflow or overflow. |
| `WaitGroup.done()` | Complete one unit of work, equivalent to add(-1). |
| `WaitGroup.wait()` | Wait until outstanding work reaches zero. |

Add work before launching workers or waiting. Wait groups can be reused after completion. Windows uses critical sections and condition variables; Linux uses futexes. Atomic read-modify-write operations use native x86-64 locked instructions. `try_receive` attempts to acquire the channel mutex without waiting and returns none on contention.

```zeph
import "std/thread.zeph"
let counter = atomic_new(0)
let counterAddress = counter.address
parallel_for(4, fn(workerIndex: int) {
    let localCounter = Atomic{address: counterAddress}
    let nextCount = localCounter.add(1)
})
print(counter.load()) // 4
```

Implementation helpers are callable because Zephyr has no private functions: `sync_alloc(byteCount: int) -> int` allocates zeroed native storage, and `sync_receive(memoryAddress: int, shouldWait: bool) -> int?` implements channel removal. Prefer the public wrappers.

The regression suite executes concurrency tests on Windows and compiles the same programs to Linux ELF. Linux execution requires a Linux host or working WSL.

## math.zeph

```zeph
import "std/math.zeph"
```

Functions use double precision. Angles are radians. Domain errors generally produce `NAN`; poles follow each function's mathematical convention. Constants include `E = 2.718281828459045`, `PI`, `TWO_PI`, `HALF_PI`, `LN2`, `INF`, and `NAN`. Range-reduction constants are implementation details.

| Signature | Description |
| --- | --- |
| `is_nan(x: float) -> bool` | Test for NaN. |
| `fabs(x: float) -> float` | Absolute value. |
| `fexp(x: float) -> float` | Exponential e^x. |
| `fln(x: float) -> float` | Natural logarithm; zero gives negative infinity. |
| `sinh(x: float) -> float` | Hyperbolic sine. |
| `cosh(x: float) -> float` | Hyperbolic cosine. |
| `tanh(x: float) -> float` | Hyperbolic tangent. |
| `fsin(x0: float) -> float` | Sine. |
| `fcos(x0: float) -> float` | Cosine. |
| `ftan(x: float) -> float` | Tangent. |
| `fcsc(x: float) -> float` | Cosecant. |
| `fsec(x: float) -> float` | Secant. |
| `fcot(x: float) -> float` | Cotangent. |
| `fatan(x0: float) -> float` | Arctangent. |
| `fasin(x: float) -> float` | Arcsine on [-1, 1]. |
| `facos(x: float) -> float` | Arccosine on [-1, 1]. |
| `facot(x: float) -> float` | Inverse cotangent with range (0, pi). |
| `fasec(x: float) -> float` | Inverse secant for absolute inputs at least one. |
| `facsc(x: float) -> float` | Inverse cosecant for absolute inputs at least one. |
| `gd(x: float) -> float` | Gudermannian. |
| `gd_inv(y: float) -> float` | Inverse Gudermannian for absolute inputs below pi/2. |
| `lgamma(x: float) -> float` | Logarithm of absolute gamma; poles give infinity. |
| `gamma(x: float) -> float` | Gamma; nonpositive integer poles give NaN. |
| `digamma(x0: float) -> float` | Logarithmic derivative of gamma. |
| `trunc(x: float) -> float` | Round toward zero, preserving signed zero. |
| `floor(x: float) -> float` | Round toward negative infinity. |
| `ceil(x: float) -> float` | Round toward positive infinity. |
| `round(x: float) -> float` | Round to nearest with halves away from zero. |
| `is_inf(x: float) -> bool` | Test for either signed infinity. |
| `exp(x: float) -> float` | Plain-named alias of fexp. |
| `ln(x: float) -> float` | Plain-named alias of fln. |
| `log10(x: float) -> float` | Base-ten logarithm. |
| `log2(x: float) -> float` | Base-two logarithm. |
| `cbrt(x: float) -> float` | Real cube root, including negative inputs. |
| `clamp(x: float, low: float, high: float) -> float` | Restrict x to [low, high]; panic for reversed bounds. |
| `clamp_int(x: int, low: int, high: int) -> int` | Integer clamp; panic for reversed bounds. |
| `powf(base: float, exponent: float) -> float` | Real power; integer exponents support negative bases; 0^0 is one. |
| `fmod(x: float, y: float) -> float` | Remainder with the sign of x; zero divisor gives NaN. |
| `atan2(y: float, x: float) -> float` | Quadrant-aware angle, including signed zeros. |
| `hypot(x: float, y: float) -> float` | Scaled sqrt(x*x + y*y), avoiding unnecessary overflow. |
| `integrate(f: fn(float) -> float, a: float, b: float, eps: float) -> float` | Adaptive Simpson integration with absolute error target eps. |
| `integrate_p(f: fn(float, float) -> float, p: float, a: float, b: float, eps: float) -> float` | Integrate f(t, p) over [a, b] with a fixed parameter. |

Derivative functions are ordinary callable functions:

| Signature | Description |
| --- | --- |
| `d_fsin(x: float) -> float` | Derivative of fsin. |
| `d_fcos(x: float) -> float` | Derivative of fcos. |
| `d_ftan(x: float) -> float` | Derivative of ftan. |
| `d_fcsc(x: float) -> float` | Derivative of fcsc. |
| `d_fsec(x: float) -> float` | Derivative of fsec. |
| `d_fcot(x: float) -> float` | Derivative of fcot. |
| `d_fasin(x: float) -> float` | Derivative of fasin. |
| `d_facos(x: float) -> float` | Derivative of facos. |
| `d_fatan(x: float) -> float` | Derivative of fatan. |
| `d_facot(x: float) -> float` | Derivative of facot. |
| `d_fasec(x: float) -> float` | Derivative of fasec. |
| `d_facsc(x: float) -> float` | Derivative of facsc. |
| `d_fln(x: float) -> float` | Derivative of fln. |
| `d_fexp(x: float) -> float` | Derivative of fexp. |
| `d_sinh(x: float) -> float` | Derivative of sinh. |
| `d_cosh(x: float) -> float` | Derivative of cosh. |
| `d_tanh(x: float) -> float` | Derivative of tanh. |
| `d_gd(x: float) -> float` | Derivative of gd. |
| `d_gd_inv(y: float) -> float` | Derivative of gd_inv. |
| `d_lgamma(x: float) -> float` | Derivative of lgamma. |
| `d_gamma(x: float) -> float` | Derivative of gamma. |

The following exported implementation helpers support the algorithms above; prefer the main operations in application code.

| Signature | Description |
| --- | --- |
| `round_i(v: float) -> int` | Round a range-reduced value to an integer; not the general float rounding API. |
| `lanczos_a(z: float) -> float` | Evaluate the Lanczos coefficient sum. |
| `is_nonpos_int(x: float) -> bool` | Classify nonpositive integer gamma poles. |
| `simpson(f: fn(float) -> float, a: float, b: float) -> float` | Evaluate one Simpson panel. |
| `adapt(f: fn(float) -> float, a: float, b: float, eps: float, whole: float, depth: int) -> float` | Recursively refine a Simpson estimate. |
| `simpson_p(f: fn(float, float) -> float, p: float, a: float, b: float) -> float` | Evaluate one parameterized Simpson panel. |
| `adapt_p(f: fn(float, float) -> float, p: float, a: float, b: float, eps: float, whole: float, depth: int) -> float` | Refine a parameterized Simpson estimate. |

```zeph
print(hypot(3.0, 4.0)) // 5
print(round(-1.5))     // -2
print(powf(-2.0, 3.0)) // -8
```

## math_core.zeph

```zeph
import "std/math_core.zeph"
```

This compatibility module contains the pre-existing math functions and constants documented in the math section, including derivatives, quadrature, and their implementation helpers. It excludes `E` and the newly added rounding, clamp, power, remainder, two-argument angle, norm, cube-root, plain-named logarithm/exponential, and infinity-classification functions.

Dependent libraries use this module to retain their original imported API without introducing the new global `E` into application programs. Each retained function has the same signature and description as in the math section. Applications wanting the complete API should import `std/math.zeph`.

```zeph
print(fexp(1.0))
print(fln(2.0))
```
