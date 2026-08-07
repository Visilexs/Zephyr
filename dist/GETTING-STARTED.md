# Zephyr 0.2

A small, statically-typed, memory-safe language that compiles straight to
native Windows x86-64 executables. This package is everything you need to
compile and run Zephyr programs — the compiler is self-contained and its output
imports only `kernel32.dll`.

## What's in the box

```
zc.exe            the compiler — ONE file, no dependencies
examples/         sample programs
docs/tour.md      learn the language in ten minutes
docs/spec.md      the full language reference
```

`zc.exe` is fully self-contained: the runtime and the standard library
(`import "std/list.zeph"`) are embedded in the executable. You can copy the
single file anywhere — even without this folder — and compile from any
directory. (If you ever want to modify the runtime, place a `runtime.zeph`
next to the exe and it overrides the embedded copy.)

## Install

Unzip anywhere, then either run `zc.exe` by its full path or add this folder to
your `PATH`:

```powershell
$env:PATH += ";C:\path\to\zephyr-0.2"      # this session only
```

To make it permanent, add the folder to your PATH in *System → Environment
Variables*.

## Compile and run

```powershell
zc.exe --rt hello.zeph hello.exe
.\hello.exe
```

`--rt` links the Zephyr runtime and produces a standalone `.exe` that depends on
nothing but `kernel32.dll`. Give an output path ending in `.s` instead of `.exe`
to read the generated x86-64 assembly.

Try one of the samples:

```powershell
zc.exe --rt examples\fizzbuzz.zeph fizzbuzz.exe && .\fizzbuzz.exe
zc.exe --rt examples\stdlib.zeph   demo.exe     && .\demo.exe
```

## Your first program

```zephyr
// hello.zeph
let name = "world"
print("Hello, {name}!")
```

```powershell
zc.exe --rt hello.zeph hello.exe
.\hello.exe            # Hello, world!
```

## Using the standard library

```zephyr
import "std/list.zeph"

let xs = [3, 1, 4, 1, 5]
print(xs.contains(4))                                   // true
print(map(xs, fn(x: int) -> int { return x * x }))      // [9, 1, 16, 1, 25]
print(filter(xs, fn(x: int) -> bool { return x > 2 }))  // [3, 4, 5]
```

`import "std/list.zeph"` resolves against the compiler's folder, so it works no
matter where your own source lives.

## Command reference

```
zc.exe --rt <input.zeph> <output.exe>   compile to a native, kernel32-only exe
zc.exe --rt <input.zeph> <output.s>     emit x86-64 assembly instead
zc.exe --version                        print the compiler version
```

## Where to go next

- **[docs/tour.md](docs/tour.md)** — a ten-minute tour of the whole language.
- **[docs/spec.md](docs/spec.md)** — grammar, type rules, conversions, builtins,
  memory model.

## Notes

- Windows x86-64 only. Programs are native PE executables.
- Errors are reported as panics: a message on stderr and exit code 1 (bad index,
  divide-by-zero, failed parse, `panic("...")`). There are no exceptions.
- Memory is managed by a garbage collector; there are no pointers, no manual
  allocation, and every list access is bounds-checked.
