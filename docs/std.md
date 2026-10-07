# Zephyr standard library

Import only the modules you need. Compile with `./zc example.zeph /tmp/example` on Apple Silicon or `zc.exe --rt example.zeph example.exe` on Windows; add `--linux` to the Windows command for Linux output. Functions can also be called through UFCS (`values.sum()`, `generator.nextInt()`). Strings are byte strings, and integer values are signed 64-bit.

## string.zeph

```zeph
import "std/string.zeph"
```

All character operations work on bytes, not Unicode code points. Whitespace means space, tab, LF, and CR.

| Signature | Description |
| --- | --- |
| `reverseString(text: str) -> str` | Reverse the bytes. |
| `ord(text: str) -> int` | First byte value; panic on empty input. |
| `trimLeft(text: str) -> str` | Remove leading whitespace. |
| `trimRight(text: str) -> str` | Remove trailing whitespace. |
| `joinWith(parts: [str], separator: str) -> str` | Join strings with a separator; empty list gives an empty string. |
| `padLeft(text: str, width: int, fill: str) -> str` | Pad on the left to the requested byte width with a one-byte fill. |
| `padRight(text: str, width: int, fill: str) -> str` | Pad on the right; strings already wide enough are unchanged. |
| `formatFixed(value: float, decimals: int) -> str` | Format with nonnegative decimal places, rounding the exact binary value half away from zero. |
| `toHex(value: int) -> str` | Lowercase hexadecimal without prefix; negatives use 16 two's-complement digits. |
| `toBinary(value: int) -> str` | Binary without prefix; negatives use 64 two's-complement digits. |
| `isDigit(byteValue: int) -> bool` | Test ASCII 0 through 9. |
| `isAlpha(byteValue: int) -> bool` | Test ASCII letters. |
| `isAlphanumeric(byteValue: int) -> bool` | Test ASCII letters or digits. |
| `isWhitespace(byteValue: int) -> bool` | Test space, tab, LF, or CR. |
| `isUpper(byteValue: int) -> bool` | Test ASCII uppercase letters. |
| `isLower(byteValue: int) -> bool` | Test ASCII lowercase letters. |
| `chars(text: str) -> [str]` | Return one single-byte string per input byte. |
| `lines(text: str) -> [str]` | Split on LF and strip one trailing CR per line; preserve empty fields, including a final one. |
| `parseInt(text: str) -> int?` | Parse signed decimal with surrounding whitespace; return none for invalid syntax or overflow. |
| `parseFloat(text: str) -> float?` | Parse signed decimal with optional fraction and exponent; return none for invalid syntax or overflow. |

Float parsing accepts `.5`, `1.`, and `1e3`; underflow produces signed zero. Fixed formatting rounds the stored binary float, so `formatFixed(2.675, 2)` is `"2.67"`.

Implementation helpers are callable because Zephyr has no private functions; applications should use the public operations above.

| Signature | Description |
| --- | --- |
| `nextFractionBit(fraction: [int]) -> int` | Double decimal fraction digits in place and return the next binary bit. |
| `hasNonzeroDigit(digits: [int]) -> bool` | Test whether any decimal digit is nonzero. |
| `decimalDigitsToFloat(digits: [int], decimalPoint: int, sign: int) -> float?` | Convert decimal digits to a correctly rounded double, returning none on overflow. |
| `scaleDecimalDigits(digits: [int], factor: int)` | Multiply decimal digits in place, least-significant digit first. |

```zeph
print(joinWith(["red", "blue"], ", "))
print(formatFixed(parseFloat("3.14159").get(), 2)) // 3.14
```

## random.zeph

```zeph
import "std/random.zeph"
```

The mutable `Rng { state: int }` uses xorshift64* with shifts 12, 25, 27 and multiplier 2685821657736338717. Its state period is 2^64-1; zero seed maps to a fixed nonzero state. Equal seeds give equal sequences. This generator is not cryptographic and must not be shared between threads without synchronization.

| Signature | Description |
| --- | --- |
| `newRng(seed: int) -> Rng` | Create a deterministic generator. |
| `nextInt(generator: Rng) -> int` | Advance state and return a full-width signed 64-bit result. |
| `intBetween(generator: Rng, low: int, high: int) -> int` | Rejection-sample an unbiased integer in [low, high); panic unless low < high. |
| `nextFloat(generator: Rng) -> float` | Return a value in [0, 1) using 53 random bits. |
| `chance(generator: Rng, probability: float) -> bool` | Return true with the given probability; require 0 <= probability <= 1. |
| `shuffle[T](generator: Rng, items: [T])` | Shuffle in place with Fisher-Yates. |

```zeph
let generator = newRng(42)
print(generator.intBetween(1, 7))
let cards = ["a", "b", "c"]
generator.shuffle(cards)
```

## io.zeph

```zeph
import "std/io.zeph"
```

Typed kernel32 wrappers use the Linux syscall shim under `--linux`. All functions below work on Windows. Linux supports everything except `environmentVariable` and `run`, which panic with clear "not supported on linux" messages. Linux output was compiled, but execution requires a Linux host. Paths and environment names reject embedded NUL bytes.

| Signature | Description |
| --- | --- |
| `readLine() -> str?` | Read stdin through LF, strip LF and one trailing CR; return none at EOF before any bytes. |
| `printError(text: str)` | Write to stderr with a newline. |
| `exit(code: int)` | Terminate the process with the requested status. |
| `appendFile(path: str, data: str)` | Append bytes, creating the file if absent; panic on failure. |
| `fileExists(path: str) -> bool` | Test whether the path exists. |
| `deleteFile(path: str) -> bool` | Delete a file and report success. |
| `listDirectory(path: str) -> [str]` | Return names only, excluding dot entries; panic if enumeration fails. |
| `environmentVariable(name: str) -> str?` | Read an environment variable; missing is none, present empty is an empty string. |
| `nowMilliseconds() -> int` | Monotonic milliseconds with an unspecified origin. |
| `nowNanoseconds() -> int` | Monotonic nanoseconds, using QueryPerformanceCounter on Windows; precision depends on the clock. |
| `sleepMilliseconds(milliseconds: int)` | Sleep for 0 <= milliseconds < 4294967295; panic outside that range. |
| `run(command: str) -> int` | Run a Windows command line, wait, and return its exit code; panic if launch fails. |

Commands are raw Windows command lines; invoke `cmd.exe /c` explicitly for shell syntax. Directory ordering is unspecified. Relative paths resolve from the process working directory.

The test suite includes a Linux compile-only check that validates the generated ELF header and references all I/O wrappers. It does not execute Linux binaries; Linux runtime behavior remains unverified in this Windows environment.

Implementation helpers are callable because Zephyr has no private functions:

| Signature | Description |
| --- | --- |
| `checkedCString(value: str) -> Bytes` | Reject embedded NUL and create a retained C string. |
| `writeToHandle(handle: int, data: str)` | Write all bytes to a handle, handling partial writes and panicking on failure. |

```zeph
appendFile("events.txt", "started\n")
let started = nowMilliseconds()
sleepMilliseconds(20)
print(nowMilliseconds() - started)
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
| `minOf[T](items: [T]) -> T` | Smallest element; panic on empty input. |
| `maxOf[T](items: [T]) -> T` | Largest element; panic on empty input. |

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
| `r.isOk() -> bool` / `r.isError() -> bool` | Which member it is. |
| `r.unwrap() -> T` | The value; panic with the error on Err. |
| `r.unwrapOr(fallback: T) -> T` | The value, or fallback. |
| `r.ok() -> T?` / `r.error() -> E?` | One side as an optional. |
| `r.map[U](transform: fn(T) -> U) -> Result[U, E]` | Transform the value; an Err passes through. |
| `r.mapError[F](transform: fn(E) -> F) -> Result[T, F]` | Transform the error; an Ok passes through. |
| `r.andThen[U](next: fn(T) -> Result[U, E]) -> Result[U, E]` | Chain a step that can fail; the first Err wins. |

```zeph
fn parsePort(text: str) -> Result[int, str] {
    let port = text as int
    if port < 1 or port > 65535 { return Result.Err("not a port: {text}") }
    return Result.Ok(port)
}
print(parsePort("8080").unwrapOr(80)) // 8080
```

## set.zeph

```zeph
import "std/set.zeph"
```

`struct Set[T]`: distinct values, backed by a `[T: bool]` map, so `T` must be a valid map key.

| Signature | Description |
| --- | --- |
| `setOf[T](items: [T]) -> Set[T]` | A set of the distinct items. |
| `Set.new() -> Set[T]` | An empty set; `T` comes from the expected type (`let s: Set[int] = Set.new()`). |
| `s.add(item: T)` / `s.remove(item: T)` | Insert or delete (no-ops when already so). |
| `s.has(item: T) -> bool` | Membership, O(1). |
| `s.len() -> int` | Number of items. |
| `s.items() -> [T]` | The items, in no particular order. |
| `s.union(other) -> Set[T]` / `s.intersection(other)` / `s.difference(other)` | New sets. |
| `s.isSubset(other) -> bool` | Every item of `s` is in `other`. |

## bytes.zeph

```zeph
import "std/bytes.zeph"
```

Raw fixed-size buffers are reference-counted and non-moving, with a GC backstop. Keep a `Bytes` value reachable while foreign code holds its address. Accessors bounds-check. Integer encodings are little-endian.

| Signature | Description |
| --- | --- |
| `Bytes.new(size: int) -> Bytes` | Allocate size zero-filled bytes aligned to 16 bytes. |
| `Bytes.len() -> int` | Buffer length in bytes. |
| `Bytes.addr() -> int` | Address of byte zero. |
| `Bytes.at(offset: int) -> int` | Address at an offset, including the end pointer. |
| `Bytes.put8(offset: int, value: int)` | Store one byte. |
| `Bytes.get8(offset: int) -> int` | Read one unsigned byte. |
| `Bytes.put16(offset: int, value: int)` | Store 16 bits. |
| `Bytes.get16(offset: int) -> int` | Read an unsigned 16-bit value. |
| `Bytes.put32(offset: int, value: int)` | Store 32 bits. |
| `Bytes.get32(offset: int) -> int` | Read a zero-extended 32-bit value. |
| `Bytes.put64(offset: int, value: int)` | Store 64 bits. |
| `Bytes.get64(offset: int) -> int` | Read 64 bits. |
| `Bytes.putFloat32(offset: int, value: float)` | Store an IEEE-754 single. |
| `Bytes.getFloat32(offset: int) -> float` | Read an IEEE-754 single as a double. |
| `Bytes.putFloat64(offset: int, value: float)` | Store an IEEE-754 double. |
| `Bytes.getFloat64(offset: int) -> float` | Read an IEEE-754 double. |
| `Bytes.putCString(offset: int, text: str)` | Copy bytes and append NUL. |
| `Bytes.putString(offset: int, text: str)` | Copy bytes without a terminator. |
| `Bytes.getString(offset: int, length: int) -> str` | Copy length bytes to a string. |
| `cString(text: str) -> Bytes` | Allocate a NUL-terminated copy. |
| `uint64Array(values: [int]) -> Bytes` | Build a contiguous 64-bit array. |
| `uint32Array(values: [int]) -> Bytes` | Build a contiguous 32-bit array. |
| `pack(items: [Bytes]) -> Bytes` | Pack equally sized byte buffers contiguously. |
| `cStringArray(strings: [str]) -> CStrs` | Build a retained array of C-string pointers and buffers. |
| `CStrs.addr() -> int` | Address of pointer array, or zero if empty. |
| `CStrs.len() -> int` | Number of strings. |
| `float32Bits(value: float) -> int` | Convert double to single bits, rounding ties to even. |
| `float32FromBits(singleBits: int) -> float` | Decode single bits into a double. |

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
| `spawnThread(threadFunction: fn(int), argument: int) -> Thread` | Start a worker and register it with the runtime collector. |
| `Thread.join()` | Wait for completion and release the worker's retained resources. |
| `parallelFor(workerCount: int, workerFunction: fn(int))` | Spawn one worker for each index in [0, workerCount), then join all. |
| `cpuCount() -> int` | Return the system processor count, falling back to one. |
| `freeze[T](value: T)` | Freeze a structure that worker threads share read-only: it and everything reachable from it stop being reference counted (no atomic writes to shared headers) and are never freed by counting. Still safe to mutate; anything stored into it later is counted normally. Use on long-lived shared state (tables, samplers, registries). |

Implementation helpers: `retainThreadBody(threadBody: fn(int)) -> int` reserves a rooted closure slot; `threadEntryThunk() -> int` obtains the native calling-convention adapter. Applications should use the operations above.

```zeph
fn worker(index: int) { print(index) }
let task = spawnThread(worker, 7)
task.join()
```

## sync.zeph

```zeph
import "std/sync.zeph"
```

Windows and Linux x86-64 synchronization uses off-heap native memory. Atomics and channels hold `int` values; encode floats with `bits` and decode with `floatFromBits`. The `Mutex`, `Atomic`, `Channel`, and `WaitGroup` wrappers are counted heap objects: pass or capture their integer `address` fields and construct a local wrapper in each worker. Never share the wrapper itself or send a counted heap object's address. Native allocations last until process exit; there is no explicit destruction API.

| Signature | Description |
| --- | --- |
| `newMutex() -> Mutex` | Create a recursive mutex. |
| `Mutex.lock()` | Block until owned by this thread. |
| `Mutex.unlock()` | Release one acquisition; only the owner may unlock. |
| `Mutex.tryLock() -> bool` | Acquire immediately if available or already owned by this thread. |
| `newAtomic(initial: int) -> Atomic` | Create an aligned 64-bit cell. |
| `Atomic.load() -> int` | Atomic read with x86 acquire ordering. |
| `Atomic.store(value: int)` | Atomic write with x86 release ordering. |
| `Atomic.add(delta: int) -> int` | Lock-free addition; return the new value, wrapping on overflow. |
| `Atomic.swap(value: int) -> int` | Lock-free exchange; return the old value. |
| `Atomic.compareExchange(expected: int, replacement: int) -> bool` | Replace only if equal; report success. |
| `newChannel(capacity: int) -> Channel` | Create a bounded FIFO; panic for nonpositive or overflowing capacity. |
| `Channel.send(value: int)` | Wait for space and enqueue; panic if closed, including while waiting. |
| `Channel.receive() -> int?` | Wait for a value; return none once closed and drained. |
| `Channel.tryReceive() -> int?` | Return the oldest queued value, or none if empty or the channel lock is contended; never block. |
| `Channel.close()` | Close idempotently and wake blocked senders and receivers; queued values remain readable. |
| `Channel.len() -> int` | Return a synchronized snapshot of the queued count. |
| `newWaitGroup() -> WaitGroup` | Create a group with zero outstanding work. |
| `WaitGroup.add(amount: int)` | Adjust outstanding work; panic on underflow or overflow. |
| `WaitGroup.done()` | Complete one unit of work, equivalent to add(-1). |
| `WaitGroup.wait()` | Wait until outstanding work reaches zero. |

Add work before launching workers or waiting. Wait groups can be reused after completion. Windows uses critical sections and condition variables; Linux uses futexes. Atomic read-modify-write operations use native x86-64 locked instructions. `tryReceive` attempts to acquire the channel mutex without waiting and returns none on contention.

```zeph
import "std/thread.zeph"
let counter = newAtomic(0)
let counterAddress = counter.address
parallelFor(4, fn(workerIndex: int) {
    let localCounter = Atomic{address: counterAddress}
    let nextCount = localCounter.add(1)
})
print(counter.load()) // 4
```

Implementation helpers are callable because Zephyr has no private functions: `allocateSyncStorage(byteCount: int) -> int` allocates zeroed native storage, and `receiveFromChannel(memoryAddress: int, shouldWait: bool) -> int?` implements channel removal. Prefer the public wrappers.

The regression suite executes concurrency tests on Windows and compiles the same programs to Linux ELF. Linux execution requires a Linux host or working WSL.

## math.zeph

```zeph
import "std/math.zeph"
```

Functions use double precision. Angles are radians. Domain errors generally produce `nan`; poles follow each function's mathematical convention. Constants include `eulerNumber = 2.718281828459045`, `pi`, `twoPi`, `halfPi`, `ln2`, `infinity`, and `nan`. Range-reduction constants are implementation details.

| Signature | Description |
| --- | --- |
| `isNan(x: float) -> bool` | Test for NaN. |
| `fabs(x: float) -> float` | Absolute value. |
| `fexp(x: float) -> float` | Exponential e^x. |
| `fln(x: float) -> float` | Natural logarithm; zero gives negative infinity. |
| `sinh(x: float) -> float` | Hyperbolic sine. |
| `cosh(x: float) -> float` | Hyperbolic cosine. |
| `tanh(x: float) -> float` | Hyperbolic tangent. |
| `fsin(angle: float) -> float` | Sine. |
| `fcos(angle: float) -> float` | Cosine. |
| `ftan(x: float) -> float` | Tangent. |
| `fcsc(x: float) -> float` | Cosecant. |
| `fsec(x: float) -> float` | Secant. |
| `fcot(x: float) -> float` | Cotangent. |
| `fatan(input: float) -> float` | Arctangent. |
| `fasin(x: float) -> float` | Arcsine on [-1, 1]. |
| `facos(x: float) -> float` | Arccosine on [-1, 1]. |
| `facot(x: float) -> float` | Inverse cotangent with range (0, pi). |
| `fasec(x: float) -> float` | Inverse secant for absolute inputs at least one. |
| `facsc(x: float) -> float` | Inverse cosecant for absolute inputs at least one. |
| `gd(x: float) -> float` | Gudermannian. |
| `gdInverse(y: float) -> float` | Inverse Gudermannian for absolute inputs below pi/2. |
| `lgamma(x: float) -> float` | Logarithm of absolute gamma; poles give infinity. |
| `gamma(x: float) -> float` | Gamma; nonpositive integer poles give NaN. |
| `digamma(input: float) -> float` | Logarithmic derivative of gamma. |
| `trunc(x: float) -> float` | Round toward zero, preserving signed zero. |
| `floor(x: float) -> float` | Round toward negative infinity. |
| `ceil(x: float) -> float` | Round toward positive infinity. |
| `round(x: float) -> float` | Round to nearest with halves away from zero. |
| `isInfinite(x: float) -> bool` | Test for either signed infinity. |
| `exp(x: float) -> float` | Plain-named alias of fexp. |
| `ln(x: float) -> float` | Plain-named alias of fln. |
| `log10(x: float) -> float` | Base-ten logarithm. |
| `log2(x: float) -> float` | Base-two logarithm. |
| `cbrt(x: float) -> float` | Real cube root, including negative inputs. |
| `clamp(x: float, low: float, high: float) -> float` | Restrict x to [low, high]; panic for reversed bounds. |
| `clampInt(x: int, low: int, high: int) -> int` | Integer clamp; panic for reversed bounds. |
| `powf(base: float, exponent: float) -> float` | Real power; integer exponents support negative bases; 0^0 is one. |
| `fmod(x: float, y: float) -> float` | Remainder with the sign of x; zero divisor gives NaN. |
| `atan2(y: float, x: float) -> float` | Quadrant-aware angle, including signed zeros. |
| `hypot(x: float, y: float) -> float` | Scaled sqrt(x*x + y*y), avoiding unnecessary overflow. |
| `integrate(f: fn(float) -> float, a: float, b: float, eps: float) -> float` | Adaptive Simpson integration with absolute error target eps. |
| `integrateWithParameter(f: fn(float, float) -> float, p: float, a: float, b: float, eps: float) -> float` | Integrate f(t, p) over [a, b] with a fixed parameter. |

Derivative functions are ordinary callable functions:

| Signature | Description |
| --- | --- |
| `derivativeFsin(x: float) -> float` | Derivative of fsin. |
| `derivativeFcos(x: float) -> float` | Derivative of fcos. |
| `derivativeFtan(x: float) -> float` | Derivative of ftan. |
| `derivativeFcsc(x: float) -> float` | Derivative of fcsc. |
| `derivativeFsec(x: float) -> float` | Derivative of fsec. |
| `derivativeFcot(x: float) -> float` | Derivative of fcot. |
| `derivativeFasin(x: float) -> float` | Derivative of fasin. |
| `derivativeFacos(x: float) -> float` | Derivative of facos. |
| `derivativeFatan(x: float) -> float` | Derivative of fatan. |
| `derivativeFacot(x: float) -> float` | Derivative of facot. |
| `derivativeFasec(x: float) -> float` | Derivative of fasec. |
| `derivativeFacsc(x: float) -> float` | Derivative of facsc. |
| `derivativeFln(x: float) -> float` | Derivative of fln. |
| `derivativeFexp(x: float) -> float` | Derivative of fexp. |
| `derivativeSinh(x: float) -> float` | Derivative of sinh. |
| `derivativeCosh(x: float) -> float` | Derivative of cosh. |
| `derivativeTanh(x: float) -> float` | Derivative of tanh. |
| `derivativeGd(x: float) -> float` | Derivative of gd. |
| `derivativeGdInverse(y: float) -> float` | Derivative of gdInverse. |
| `derivativeLgamma(x: float) -> float` | Derivative of lgamma. |
| `derivativeGamma(x: float) -> float` | Derivative of gamma. |

The following exported implementation helpers support the algorithms above; prefer the main operations in application code.

| Signature | Description |
| --- | --- |
| `roundToInt(value: float) -> int` | Round a range-reduced value to an integer; not the general float rounding API. |
| `lanczosSum(z: float) -> float` | Evaluate the Lanczos coefficient sum. |
| `isNonPositiveInteger(x: float) -> bool` | Classify nonpositive integer gamma poles. |
| `simpson(f: fn(float) -> float, a: float, b: float) -> float` | Evaluate one Simpson panel. |
| `adaptiveSimpson(f: fn(float) -> float, a: float, b: float, eps: float, whole: float, depth: int) -> float` | Recursively refine a Simpson estimate. |
| `simpsonWithParameter(f: fn(float, float) -> float, p: float, a: float, b: float) -> float` | Evaluate one parameterized Simpson panel. |
| `adaptiveSimpsonWithParameter(f: fn(float, float) -> float, p: float, a: float, b: float, eps: float, whole: float, depth: int) -> float` | Refine a parameterized Simpson estimate. |

```zeph
print(hypot(3.0, 4.0)) // 5
print(round(-1.5))     // -2
print(powf(-2.0, 3.0)) // -8
```

## math_core.zeph

```zeph
import "std/math_core.zeph"
```

This compatibility module contains the pre-existing math functions and constants documented in the math section, including derivatives, quadrature, and their implementation helpers. It excludes `eulerNumber` and the newly added rounding, clamp, power, remainder, two-argument angle, norm, cube-root, plain-named logarithm/exponential, and infinity-classification functions.

Dependent libraries use this module to retain their original imported API without introducing the new global `eulerNumber` into application programs. Each retained function has the same signature and description as in the math section. Applications wanting the complete API should import `std/math.zeph`.

```zeph
print(fexp(1.0))
print(fln(2.0))
```
