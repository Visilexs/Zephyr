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

Typed kernel32 wrappers; under `--linux` they go through the syscall shims in `lib/os/linux.zeph`, and everything below works on both targets. Paths and environment names reject embedded NUL bytes.

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
| `run(command: str) -> int` | Run a command, wait, and return its exit code; panic if launch fails. |
| `tryReadFile(path: str) -> Result[str, str]` | The whole file (read to EOF, so `/proc` files and FIFOs work), or `Err("open PATH: no such file or directory")`-style text. Never panics on I/O. |
| `tryWriteFile(path: str, data: str) -> Result[int, str]` | Create or truncate and write; `Ok(byte count)` or `Err` text. |
| `ioErrorText(code: int) -> str` | Text for a `GetLastError` code (Linux errno values are tagged `0x20000000` by the shim). |

`run` on Windows takes a raw command line (invoke `cmd.exe /c` for shell syntax). On Linux it runs `/bin/sh -c COMMAND` with the process's environment and inherited stdin/stdout/stderr; a command killed by signal N returns 128 + N, and 127 means the shell could not start the command. For pipes, see `process.zeph`. `environmentVariable` on Linux reads `/proc/self/environ` (the environment the process started with). Directory ordering is unspecified. Relative paths resolve from the process working directory.

```zeph
match tryReadFile("config.json") {
    Ok(text) { print(text.len()) }
    Err(message) { print(message) }    // open config.json: no such file or directory
}
print(run("test -d /tmp"), environmentVariable("HOME").or("?"))
```

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

## utf8.zeph

```zeph
import "std/utf8.zeph"
```

Strings stay byte strings; these functions read them as UTF-8. Invalid input never panics: a byte that does not start a valid sequence decodes as U+FFFD (65533) and advances one byte, so every byte belongs to exactly one rune. Widths follow terminal columns (a table-free approximation of `wcwidth`).

| Signature | Description |
| --- | --- |
| `utf8DecodeAt(text: str, index: int) -> (int, int)` | (codepoint, byte length) at byte `index`; invalid, truncated, overlong or surrogate sequences give (65533, 1). Panics only when `index` is outside the string. |
| `utf8Encode(codepoint: int) -> str` | The encoding of one codepoint; out-of-range values and surrogates encode U+FFFD. |
| `utf8FromCodepoints(codepoints: [int]) -> str` | The string of these codepoints. |
| `utf8Codepoints(text: str) -> [int]` | Every codepoint, in order. |
| `utf8RuneCount(text: str) -> int` | Number of runes (each invalid byte counts one). |
| `utf8IsValid(text: str) -> bool` | Well-formed UTF-8 throughout. |
| `utf8RuneOffset(text: str, runeIndex: int) -> int` | Byte offset where rune `runeIndex` starts (the byte length past the end). |
| `utf8Sub(text: str, start: int, end: int) -> str` | Runes [start, end), bounds clamped. |
| `utf8Truncate(text: str, count: int) -> str` | The first `count` runes; never splits a sequence. |
| `utf8TruncateBytes(text: str, maxBytes: int) -> str` | Longest prefix of at most `maxBytes` bytes that ends on a rune boundary. |
| `utf8RuneWidth(cp: int) -> int` | Terminal columns of one codepoint: 0 (controls, combining marks, ZWJ), 2 (East Asian wide, most emoji) or 1. |
| `utf8DisplayWidth(text: str) -> int` | Columns of the whole string. |
| `utf8TruncateWidth(text: str, columns: int) -> str` | Longest prefix that fits in `columns`. |
| `utf8PadRight(text: str, columns: int) -> str` / `utf8PadLeft(...)` | Pad with spaces to `columns`; wider text is returned unchanged. |
| `utf8Fit(text: str, columns: int) -> str` | Exactly `columns` wide: truncated with "…" or padded. For table cells. |

```zeph
let text = "héllo, 世界"
print(text.len(), utf8RuneCount(text), utf8DisplayWidth(text))   // 14 9 11
print(utf8Truncate(text, 4), utf8Fit("世界世界", 5) + "|")        // héll 世界…|
```

## json.zeph

```zeph
import "std/json.zeph"
```

`enum Json { Null, Bool(bool), Number(float), Text(str), Array([Json]), Object([str], [Json]) }`. Parsing never panics: malformed input gives `Err` with the byte offset. Objects keep keys in source order (duplicates are kept; lookups find the first). Numbers are floats; `asInt` truncates.

Building:

| Signature | Description |
| --- | --- |
| `jsonObject() -> Json` / `jsonArray() -> Json` | Empty object / array. |
| `jsonText(s)`, `jsonNumber(x)`, `jsonInt(n)`, `jsonBool(b)`, `jsonTextList(items: [str])` | Leaf values; `Json.Null` for null. |
| `j.set(key: str, value: Json) -> Json` | Object: set or replace, return self (chains). Panics on a non-object. |
| `j.add(value: Json) -> Json` | Array: append, return self. Panics on a non-array. |

Reading:

| Signature | Description |
| --- | --- |
| `j.get(key) -> Json?` / `j.at(index) -> Json?` / `j.has(key) -> bool` | Member / element access; none on a missing member or the wrong kind. |
| `j.path(path: str) -> Json?` | Dig by path: `"choices[0].delta.content"`, `"[2]"`, `"a.b"`. |
| `j.asStr() -> str?`, `j.asFloat() -> float?`, `j.asInt() -> int?`, `j.asBool() -> bool?`, `j.isNull() -> bool` | Typed views; none for another kind. |
| `j.items() -> [Json]`, `j.keys() -> [str]`, `j.len() -> int`, `j.kind() -> str` | Elements, keys in order, count, and `"null"`/`"bool"`/`"number"`/`"string"`/`"array"`/`"object"`. |
| `jsonGetStr(j, path) -> str?`, `jsonGetFloat`, `jsonGetInt`, `jsonGetBool` | `j.path(path)` plus the typed view. |

Parsing and writing:

| Signature | Description |
| --- | --- |
| `jsonParse(text: str) -> Result[Json, str]` | One RFC 8259 document; `Err("... at byte N")` otherwise. |
| `jsonTryParse(text: str) -> Json?` | Same, without the message. |
| `jsonParsePartial(text: str) -> Json?` | A prefix of a document still streaming in, with every open string/array/object closed: `{"a": [1, 2` gives `{"a":[1,2]}`. Members whose value has not started, and numbers or literals that may still grow, are left out. none when the prefix can never become valid. |
| `jsonPartialFields(src: str) -> [JsonPartialField]` | String-valued members of a prefix at any depth (`key`, `value`, `complete`), for showing tool-call arguments while a model writes them. |
| `jsonPartialString(src: str, key: str) -> str?` | The (possibly partial) value of the first string member `key`. |
| `jsonStringify(j) -> str` / `jsonStringifyAscii(j)` | Compact text; the Ascii form escapes non-ASCII as `\uXXXX`. |
| `jsonPretty(j, indent: int) -> str` | Indented text. |
| `jsonQuote(s) -> str` / `jsonQuoteAscii(s)` | A JSON string literal. |
| `jsonFormatNumber(x: float) -> str` | Shortest round-tripping decimal (JavaScript layout); NaN/infinity become `null`. |

```zeph
match jsonParse("\{\"choices\": [\{\"delta\": \{\"content\": \"Hi\"}}]}") {
    Ok(value) { print(jsonGetStr(value, "choices[0].delta.content").or("")) }   // Hi
    Err(message) { print(message) }
}
let reply = jsonObject().set("ok", jsonBool(true)).set("n", jsonInt(3))
print(jsonStringify(reply))                                        // {"ok":true,"n":3}
print(jsonPartialString("\{\"path\": \"src/ma", "path").or(""))     // src/ma
```

## process.zeph (Linux)

```zeph
import "std/process.zeph"
```

Child processes with stdin/stdout/stderr pipes, built on raw syscalls (`pipe2`, `fork`, `dup2`, `execve`, `poll`, `wait4`). `argv[0]` is looked up on `PATH` unless it contains `/`. Spawn failures (not found, permission denied, bad directory) are `Err`, never panics. `spawn` ignores `SIGPIPE`, so writing to a child that has exited returns false instead of killing the program.

| Signature | Description |
| --- | --- |
| `struct SpawnOptions { environment: [str: str]?, clearEnvironment = false, directory = "", mergeStderr = false }` | `environment` sets variables on top of the inherited ones (or on an empty environment with `clearEnvironment`); `directory` is the child's working directory; `mergeStderr` sends stderr into the stdout pipe. `SpawnOptions{}` for defaults. |
| `spawn(argv: [str], options: SpawnOptions) -> Result[Process, str]` | Start the program. |
| `p.write(text: str) -> bool` | Write all of it to stdin (blocks while the pipe is full). False after the child closed stdin. |
| `p.closeStdin()` | Send EOF. |
| `p.readAvailable(timeoutMilliseconds: int = 0) -> str` | What stdout holds now, waiting at most the timeout (-1: until data or EOF). `""` when nothing came; `p.stdoutOpen` turns false at EOF. Ready stderr is appended to `p.stderrText`. |
| `p.readAll() -> str` | Stdout to EOF, collecting stderr into `p.stderrText` at the same time (no deadlock on a chatty stderr). |
| `p.wait() -> int` | Close stdin, wait, return the exit code (128 + N if killed by signal N). |
| `p.tryWait() -> int?` | The exit code if the child has exited, else none; never blocks. |
| `p.kill(signal: int = 15) -> bool` | Send a signal; false once reaped. |
| `p.close()` | Close every pipe still open. |
| `runCapture(argv: [str]) -> Result[ProcessOutput, str]` | Run to completion with stdin closed: `ProcessOutput{code, stdout, stderr}`. |
| `runCaptureWith(argv, options, input: str) -> Result[ProcessOutput, str]` | Same, with options and stdin text. |
| `currentEnvironment() -> [str]` | This process's `NAME=value` entries. |

Writing a large input with `write` before reading can deadlock if the child fills its stdout pipe first; for big inputs interleave `write` with `readAvailable`.

```zeph
match spawn(["sh", "-c", "read x; echo got $x"], SpawnOptions{}) {
    Ok(child) {
        let sent = child.write("hi\n")
        child.closeStdin()
        print(child.readAll().trim(), child.wait())      // got hi 0
    }
    Err(message) { print(message) }
}
let listing = runCapture(["ls", "/nope"]).unwrap()
print(listing.code, listing.stderr.len() > 0)            // 2 true
```

## net.zeph (Linux)

```zeph
import "std/net.zeph"
```

TCP client sockets and host resolution on raw syscalls. Nothing panics on network errors: every call returns a `Result` or optional. Sockets are non-blocking underneath; `send`/`recv` wait at most `conn.timeoutMilliseconds` (set from the connect timeout, changeable), then give `Err("recv HOST:PORT: timed out")`.

Resolution order: IP literals, `/etc/hosts`, then one UDP DNS A-record query (retried once) to the first IPv4 `nameserver` in `/etc/resolv.conf`. IPv6 works for literals (`::1`, `[::1]`) and `/etc/hosts` entries; DNS asks only for A records.

| Signature | Description |
| --- | --- |
| `tcpConnect(host: str, port: int, timeoutMilliseconds: int = 30000) -> Result[TcpConnection, str]` | Resolve and connect to the first address that accepts; `Err("connect HOST:PORT: connection refused")` and the like. |
| `conn.send(data: str) -> Result[int, str]` | Send everything (MSG_NOSIGNAL). |
| `conn.recv(maxBytes: int = 65536) -> Result[str, str]` | What arrives first, up to maxBytes; `Ok("")` when the peer closed. |
| `conn.recvAll() -> Result[str, str]` | Everything until the peer closes. |
| `conn.shutdownWrite()` / `conn.close()` | Half-close / close. |
| `resolveHost(host: str, timeoutMilliseconds: int = 5000) -> Result[[IpAddress], str]` | All addresses found (`/etc/hosts` IPv4 entries first). |
| `dnsQueryA(host, server: IpAddress, port: int, timeoutMilliseconds: int) -> Result[[IpAddress], str]` | One A query to a given server; `Ok([])` for NXDOMAIN. |
| `hostsLookup(host) -> [IpAddress]`, `systemNameserver() -> IpAddress?` | The two resolution sources. |
| `parseIpv4(text) -> IpAddress?`, `parseIpv6(text)`, `parseIp(text)` | Address literals; `addr.text()` formats one, `addr.family` is 4 or 6. |

```zeph
match tcpConnect("127.0.0.1", 8000, 2000) {
    Ok(conn) {
        let sent = conn.send("GET / HTTP/1.0\r\n\r\n")
        print(conn.recvAll().unwrapOr("").len())
        conn.close()
    }
    Err(message) { print(message) }
}
```

## http.zeph (Linux)

```zeph
import "std/http.zeph"
```

An HTTP/1.1 client. `http://` URLs go over `net.zeph`; `https://` URLs go through libcurl (`libcurl.so.4`, loaded with `dlopen` on first use; any distro's libcurl package). Without libcurl, an https request is `Err("https: libcurl.so.4 is not available (install libcurl to use https:// URLs)")`. Importing this module makes the executable dynamically linked (it imports `dlopen`/`dlsym`), whether or not https is used.

Network errors, timeouts and malformed responses are `Err(text)`; an HTTP error status is still `Ok` (check `status`). Bodies may be Content-Length, chunked or close-delimited. Requests send `Connection: close` (one request per connection) and redirects are not followed. `Host`, `User-Agent`, `Accept` and `Content-Length` are added unless the headers map sets them. Response header names are lowercased; repeats are joined with `", "`.

| Signature | Description |
| --- | --- |
| `request(method, url, headers: [str: str], body: str) -> Result[Response, str]` | One request with default options; the body is collected. |
| `requestWith(method, url, headers, body, options: HttpOptions) -> Result[Response, str]` | Same, with options. |
| `get(url) -> Result[Response, str]`, `postJson(url, json: str, headers) -> Result[Response, str]` | Shorthands; `postJson` sets `Content-Type: application/json`. |
| `requestStream(method, url, headers, body, options, onChunk: fn(str) -> bool) -> Result[Response, str]` | Calls `onChunk` with each piece of decoded body as it arrives; returning false stops and closes. The Response's body is `""`. |
| `requestEvents(method, url, headers, body, options, onEvent: fn(SseEvent) -> bool) -> Result[Response, str]` | Server-Sent Events: `onEvent` per complete event; false stops. Adds `Accept: text/event-stream` unless set. |
| `struct HttpOptions { timeoutMilliseconds = 60000, useCurl = false, caFile = "", insecure = false }` | Timeout for connect and each read (libcurl: the whole transfer); `useCurl` sends http:// through libcurl too; `caFile` trusts a PEM bundle; `insecure` skips certificate checks. |
| `struct Response { status, reason, headers: [str: str], body }` | `r.header(name) -> str?` (any case), `r.isSuccess()` (2xx). |
| `struct SseEvent { event, data, id }` | `event` defaults to `"message"`; multi-line `data:` fields are joined with `"\n"`; `id` is the last id seen. |
| `SseParser{}` / `parser.feed(chunk: str) -> [SseEvent]` | The incremental event-stream parser, for bytes from elsewhere. Handles any split, LF/CRLF/CR line ends and `:` comments. |
| `parseUrl(url) -> Result[Url, str]`, `parseResponseHead(head) -> Result[Response, str]` | Helpers: `Url{scheme, host, port, path}`. |

With libcurl the body is decoded by curl, and the status and headers are known when the transfer ends: the streaming callbacks still run as data arrives.

```zeph
var headers: [str: str] = [:]
headers["Authorization"] = "Bearer " + environmentVariable("API_KEY").or("")   // std/io
headers["Content-Type"] = "application/json"
let body = "\{\"model\": \"m\", \"stream\": true, \"messages\": []}"
let result = requestEvents("POST", "https://api.example.com/v1/chat", headers, body, HttpOptions{},
    fn(event: SseEvent) -> bool {
        if event.data == "[DONE]" { return false }
        if let delta = jsonTryParse(event.data) {                                   // std/json
            print(jsonGetStr(delta, "choices[0].delta.content").or(""))
        }
        return true
    })
if let message = result.error() { print(message) }
```
