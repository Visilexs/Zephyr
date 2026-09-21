# Zephyr language specification

Version 0.2. Normative for the self-hosted compiler `compiler/zc.zeph` (built
as `zc.exe`), which is the canonical implementation. The C seed in
`bootstrap/zephyr.c` implements the same language, minus generics, closures,
and function-value types, and exists only to reconstruct the first `zc.exe`.

The compiler emits three native targets from the same source: Windows x86-64
(default), Linux x86-64 (`--linux`), and WebAssembly (`--wasm`) — see §7.

## 1. Source text

Zephyr source is a sequence of bytes interpreted as ASCII/UTF-8. Comments run
from `//` to end of line. Statements are terminated by a newline or by the
closing `}` of their block. Newlines inside `(...)` and `[...]` are ignored,
so calls and list literals may span lines.

### 1.1 Tokens

Keywords:

```
fn let var if else while for in return struct enum impl interface import as
extern from true false none and or not break continue
```

Identifiers: `[A-Za-z_][A-Za-z0-9_]*`, excluding keywords.

Literals:

- integer: `[0-9]+`, a 64-bit signed value
- float: `[0-9]+ '.' [0-9]+`
- string: `"..."` with escapes `\n \t \\ \" \{ \}` and interpolation `{expr}`;
  strings may not contain raw newlines
- `true`, `false`, `none`

Operators and punctuation:

```
+ - * / % == != < <= > >= = += -= *= /= -> .. . , : ? ( ) [ ] { }
& | ^ << >>
```

## 2. Grammar

EBNF; `NL` is one or more newline terminators.

```ebnf
program    = { toplevel } ;
toplevel   = fndecl | structdecl | enumdecl | impldecl | ifacedecl
           | externdecl | import | stmt ;
externdecl = "extern" "fn" ID "(" [ param { "," param } ] ")"
             [ "->" type ] "from" STRING ;                    (* §3.6, native DLL import *)

fndecl     = "fn" ID [ "[" ID { "," ID } "]" ]                (* type params *)
             "(" [ param { "," param } ] ")" [ "->" type ] block ;
param      = ID ":" type | "self" ;                           (* self only in impl/interface *)
structdecl = "struct" ID "{" { ID ":" type [ "," ] } "}" ;
enumdecl   = "enum" ID "{" ID { "," ID } "}" ;
impldecl   = "impl" ID "{" { fndecl } "}" ;                   (* methods on a struct *)
ifacedecl  = "interface" ID "{" { fnsig } "}" ;               (* method signatures *)
fnsig      = "fn" ID "(" [ param { "," param } ] ")" [ "->" type ] ;
import     = "import" STRING ;

type       = basetype [ "?" ] ;                              (* T? optional *)
basetype   = "int" | "i32" | "float" | "bool" | "str" | ID
           | "[" type "]"                                    (* list *)
           | "[" type ":" type "]"                           (* map *)
           | "fn" "(" [ type { "," type } ] ")" [ "->" type ] ; (* function value *)

block      = "{" { stmt } "}" ;
stmt       = decl | assign | ifstmt | while | for | return
           | "break" | "continue" | expr ;
decl       = ( "let" | "var" ) ID [ ":" type ] "=" expr ;
assign     = target ( "=" | "+=" | "-=" | "*=" | "/=" ) expr ;
target     = ID | postfix "." ID | postfix "[" expr "]" ;
ifstmt     = "if" expr block [ "else" ( ifstmt | block ) ] ;
while      = "while" expr block ;
for        = "for" ID "in" expr [ ".." expr ] block ;
return     = "return" [ expr ] ;

expr       = orexpr ;
orexpr     = andexpr { "or" andexpr } ;
andexpr    = eqexpr { "and" eqexpr } ;
eqexpr     = relexpr { ( "==" | "!=" ) relexpr } ;
relexpr    = shiftexpr { ( "<" | "<=" | ">" | ">=" ) shiftexpr } ;
shiftexpr  = addexpr { ( "|" | "^" ) addexpr } ;
addexpr    = mulexpr { ( "+" | "-" ) mulexpr } ;
mulexpr    = castexpr { ( "*" | "/" | "%" | "&" | "<<" | ">>" ) castexpr } ;
castexpr   = unary { "as" type } ;
unary      = ( "-" | "not" ) unary | postfix ;
postfix    = primary { "(" args ")" | "[" expr "]" | "." ID } ;
primary    = INT | FLOAT | STRING | "true" | "false" | "none" | ID
           | ID "{" fieldinits "}"                           (* struct literal *)
           | "fn" "(" [ param { "," param } ] ")" [ "->" type ] block  (* closure *)
           | "(" expr ")"
           | "[" args "]"                                    (* list literal *)
           | "[" [ expr ":" expr { "," expr ":" expr } | ":" ] "]" ; (* map literal *)
args       = [ expr { "," expr } ] ;
fieldinits = { ID ":" expr [ "," ] } ;
```

Binding strength, weakest to tightest: `or`, `and`, `== !=`, `< <= > >=`,
`| ^`, `+ -`, `* / % & << >>`, `as`, unary `- not`, postfix call/index/member.
All binary operators are left-associative. (The bitwise levels follow Go:
`& << >>` bind like `*`, `| ^` bind like `+`.)

Disambiguation: an identifier followed by `{` is a struct literal, except in
the header expression of `if`/`while`/`for`, where `{` begins the block
(parenthesize to force a literal there). `fn` and `struct` are only allowed
at the top level.

## 3. Types

`int` (64-bit signed, wrapping on overflow), `float` (IEEE 754 double),
`bool`, `str` (immutable byte string), `[T]` (growable list), `[K: V]` (hash
map), and named struct and enum types. `void` is the type of no value; it
cannot be named in source.

`i32` is a 32-bit signed integer that exists only as an `extern fn` return type
(§3.6): the low 32 bits of the return register, sign-extended to a Zephyr `int`.
It is not a general-purpose type — locals, fields and arithmetic all use `int`.

Two types are equal structurally, except structs and enums, which are equal
only if they are the same declaration. There is no null and no implicit
default value; every variable, field, and element is initialized at creation.

### 3.0 Enums

    enum Color { Red, Green, Blue }

Declares a distinct type whose values are the listed members, numbered from 0
in order. Members are reached through the type name (`Color.Green`) and fold
to their ordinal at compile time, so an enum value is just an `int` at
runtime and costs nothing. Enums support `==`/`!=` (only against the *same*
enum — comparing two different enum types is a type error), `as int` (the
ordinal) and `as str` (the member name). `print` shows the member name.

### 3.0.1 Maps

    var ages: [str: int] = ["alice": 30, "bob": 25]
    ages["carol"] = 41          // insert or update
    print(ages["alice"])        // panics if the key is absent
    print(ages.has("bob"))

`[K: V]` is a hash map. The key type `K` must be `int`, `str`, `bool`, or an
enum — types with value equality (`str` compares structurally). `[:]` is the
empty map literal and, like `[]`, needs an annotation to supply its type.

Reading a missing key panics; use `.has(k)` to test first. Methods: `.len()`,
`.has(k)`, `.remove(k)`, `.keys()` → `[K]`, `.values()` → `[V]`. Iterate with
`for k in m.keys()`. Iteration order is unspecified. Maps are open-addressed
and grow at 70% load, so insert/lookup are amortized O(1).

### 3.0.2 Modules

    import "util.zeph"
    import "sub/mathx.zeph"

`import` may appear at the top level of a file. It splices that file's
declarations — functions, structs, enums, and globals — into the importing
program, so imported names are used unqualified. Paths are relative to the
*importing* file's directory (absolute paths are taken as-is).

Each path is included at most once, so importing the same file twice is a
no-op and mutually-importing files terminate. There is no separate namespace:
imported names share the one global scope, and a duplicate name across files
is a redeclaration error.

### 3.0.3 Function values

    fn square(n: int) -> int { return n * n }

    fn map_list(xs: [int], f: fn(int) -> int) -> [int] {
        var out: [int] = []
        for x in xs { out.push(f(x)) }
        return out
    }

    let g = square              // a function name used as a value
    print(map_list([1, 2, 3], square))

`fn(T, ...) -> R` is the type of a function value (`-> R` is omitted for
void). A function's name used outside a call position evaluates to its code
address, so functions can be stored in variables, lists, maps, and struct
fields, and passed to and returned from other functions. Any expression of
function type may be called: `ops["up"](10)`.

Two function types are equal when their parameter types and return type match.
A local variable may shadow a function name; a global may not.

**Closures.** `fn(params) -> R { ... }` is an expression, and it captures the
enclosing locals it mentions **by value**, at the moment it is created:

    fn adder(k: int) -> fn(int) -> int {
        return fn(x: int) -> int { return x + k }   // k is snapshotted
    }
    let add3 = adder(3)
    print(add3(1))                                  // 4

Each evaluation makes a fresh closure, so a closure created in a loop keeps
that iteration's values. Capture is transitive — a nested closure may name a
variable from any enclosing scope. Because capture is by value, **assigning to
a captured variable is an error**; assign to a global, or return a new value.
Globals are not captured (they have a fixed address).

A function value is a `{code, environment}` pair; a plain function name used as
a value has an empty environment. Calls through a function value are identical
either way, so `fn(int) -> int` accepts both.

### 3.0.5 Generics

    fn contains[T](xs: [T], x: T) -> bool {
        for v in xs {
            if v == x { return true }
        }
        return false
    }

    print(contains([1, 2, 3], 2))       // true
    print(contains(["a", "b"], "b"))    // true — structural ==
    print([1, 2].contains(2))           // same call, UFCS

Functions may take type parameters in `[...]`. They are **inferred from the
arguments** — never written at the call site — and unification looks through
`[T]`, `[K: V]`, `T?`, and `fn(T) -> U`, so `map[T, U]` can infer `U` from the
return type of the function you pass it.

Generics are **monomorphised**: each distinct set of type arguments compiles to
its own copy of the body, which is then type-checked with `T` bound. That
copy's checking *is* the contract — `contains` compiles `v == x` for the
concrete `T`, so it works for `int`, `str`, and enums, and is rejected for
element types with no `==`. There is no trait or interface system, and none is
needed to express the standard library.

A generic function has no single type, so it cannot be used as a function value.

`std/list.zeph` is written entirely in these terms — `contains`, `index_of`,
`reverse`, `slice`, `map`, `filter`, `fold`, `any`, `all`, `first`, `last`,
`sort_by`. They were compiler builtins before generics existed. `import` it:

    import "std/list.zeph"

### 3.0.4 Optionals

    fn find(xs: [int], target: int) -> int? {
        for i in 0..xs.len() { if xs[i] == target { return i } }
        return none
    }

    print(find(xs, 8).or(-1))
    let v = ages.get("bob")     // int? — none if absent, no panic

`T?` holds either a value of `T` or `none`. Any `T` implicitly wraps into
`T?`; `none` fits every optional. Optionals do not nest (`T??` is an error).

Methods: `.has()` → bool, `.get()` → `T` (panics on none), `.or(d)` → `T`
(the value, or `d`). `print` shows `none` or the wrapped value. An optional
must be unwrapped before use — it is not a `T`, so `b + 1` on an `int?` is a
type error. `let x = none` needs an annotation to say which optional it is.

An optional is a pointer to a one-word cell, so `0`, `false`, and `""` are
ordinary values, cleanly distinct from `none` — `let z: int? = 0` has
`z.has() == true`.

### 3.0.6 Methods and interfaces

An `impl` block attaches functions to a struct:

    struct Point { x: float, y: float }
    impl Point {
        fn new(x: float, y: float) -> Point { return Point{x: x, y: y} }  // associated
        fn len(self) -> float { return sqrt(self.x*self.x + self.y*self.y) }  // method
    }

    let p = Point.new(3.0, 4.0)   // associated function: Type.name(...)
    print(p.len())                // method: self is the receiver

A method's first parameter is the literal word `self`, typed as the impl's
struct (no annotation). It is called as `recv.method(args)`. A function without
`self` is an *associated function*, called as `Type.func(args)`. Methods are
scoped to their type, so different structs may reuse a name (`Circle.area`,
`Rect.area`), and a method shadows any builtin of the same name for that type.
Method call syntax also still works as plain UFCS for free functions:
`x.f(y)` calls `f(x, y)` when no `Type.f` method exists.

An `interface` is a set of method signatures:

    interface Shape {
        fn area(self) -> float
        fn name(self) -> str
    }

Any struct whose `impl` provides all of an interface's methods (matching
parameter and return types) is usable where that interface is expected — the
conversion is implicit and structural, no `implements` clause. An interface
value is a fat reference (a `{vtable, data}` cell); calling a method on it
dispatches dynamically through the struct's vtable. This gives runtime
polymorphism — a `[Shape]` may hold circles and rects, and `s.area()` runs the
right one. Interface values cannot be printed directly; call a method instead.
There is no implementation inheritance: compose structs and share behaviour
through interfaces.

### 3.1 Declarations and inference

`let` introduces an immutable binding, `var` a mutable one. The type is the
type of the initializer, unless an annotation is given, in which case the
initializer must fit it (§3.2). An empty list literal `[]` is allowed only
where an annotation supplies its type. Shadowing is allowed in inner scopes;
redeclaring a name in the same scope is an error. Immutability applies to the
binding: fields of a `let` struct and elements of a `let` list may be
mutated.

Declarations at statement depth 0 of the program are **globals**: they are
visible inside every function that appears after them in the source, and they
are roots for the backstop collector (§4). Declarations nested in any block
(including top-level `if`/`for`/`while` bodies) are locals. Top-level code executes in source order.

### 3.2 Conversions

A value of type `S` *fits* type `T` if `S = T`, or `S = int` and `T = float`
(implicit widening). Widening applies at: initialization, assignment,
arguments, returns, list elements, struct fields, and mixed arithmetic or
comparison (the int operand widens).

All other conversions are explicit via `expr as type`:

| from \ to | int | float | str | bool |
|-----------|-----|-------|-----|------|
| **int**   | —   | exact | decimal | ✗ |
| **float** | truncate toward zero | — | shortest decimal (`%.15g`) | ✗ |
| **str**   | parse or panic | parse or panic | — | ✗ |
| **bool**  | ✗   | ✗     | `"true"`/`"false"` | — |

Lists and structs cannot be cast. `str` parses accept surrounding spaces and
panic (§6) on any other malformed input.

### 3.3 Operators

- `+ - * / %`: numeric. Two ints yield int (`/` truncates toward zero; `/`
  and `%` by zero panic). Any float operand yields float (`%` is not defined
  for floats). `+` on two strs concatenates.
- `& | ^ << >>`: bitwise, int operands only, int result. `<<`/`>>` shift by
  the low 6 bits of the right operand; `>>` is arithmetic (sign-preserving).
  Precedence (Go-style): `& << >>` bind at the `*` level, `| ^` at the `+`
  level.
- `== !=`: numbers (mixed widens), bools, or strs (byte equality). Not
  defined for lists or structs.
- `< <= > >=`: numbers or strs (lexicographic byte order).
- `and or not`: bools only; `and`/`or` short-circuit.
- Unary `-`: numeric.
- Conditions of `if`/`while` must be `bool`.

### 3.4 Functions

Parameter and return types are declared; a function with a non-void return
type must provably return on every path (a `return`, or an `if`/`else` whose
branches both return). Top-level code runs in order; functions and structs
may be referenced before their declaration. Function and variable namespaces
are shared: a call resolves builtins first, then declared functions.

Method syntax is universal function call syntax: `a.f(b)` is exactly
`f(a, b)` for any declared function `f` whose first parameter accepts `a`.

### 3.5 Builtins

| Builtin | Signature | Notes |
|---------|-----------|-------|
| `print(v)` | any → void | formats like §5, appends newline |
| `panic(m)` | str → (no return) | §6 |
| `sqrt(x)`  | float → float | int argument widens |
| `l.len()`  | [T] or str → int | |
| `l.push(v)`| [T], T → void | amortized O(1) |
| `l.pop()`  | [T] → T | panics when empty |
| `emit(s)`  | str → void | write to stdout without a newline |
| `chr(c)`   | int → str | one byte, 0..255; panics outside |
| `bits(x)`  | float → int | IEEE 754 bit pattern, zero cost |
| `s.byte(i)`| str, int → int | byte value 0..255, bounds-checked |
| `s.sub(lo, hi)` | str, int, int → str | half-open byte range; panics if invalid |
| `l.join()` | [str] → str | single-pass concatenation |
| `args()`   | → [str] | process arguments, `args()[0]` is the program |
| `read_file(p)` | str → str | whole file; panics if unreadable |
| `write_file(p, d)` | str, str → void | create/overwrite; panics on failure |
| `zeros(n)` | int → [int] | preallocated list of `n` zeros |
| `assert(c)` / `assert(c, m)` | bool, str? → void | panics with `m` (or "assertion failed") if `c` is false |
| `abs(x)`   | int→int / float→float | absolute value |
| `min(a, b)` / `max(a, b)` | numbers → number | int or float (widened if mixed) |
| `pow(b, e)` | int, int → int | fast exponentiation; `e < 0` yields 0 |

**String methods** (all byte-oriented, half-open ranges):

| Method | Signature | Notes |
|--------|-----------|-------|
| `s.contains(t)` | str → bool | substring test |
| `s.index_of(t)` | str → int | first byte index, or −1 |
| `s.starts_with(t)` / `s.ends_with(t)` | str → bool | prefix / suffix test |
| `s.split(sep)` | str → [str] | empty `sep` splits into bytes |
| `s.replace(old, new)` | str, str → str | all non-overlapping occurrences |
| `s.upper()` / `s.lower()` | → str | ASCII case |
| `s.trim()` | → str | strips leading/trailing ASCII whitespace |
| `s.repeat(n)` | int → str | `n` copies concatenated |

**List methods:**

| Method | Signature | Notes |
|--------|-----------|-------|
| `l.contains(x)` | T → bool | value equality (structural for `[str]`) |
| `l.index_of(x)` | T → int | first index, or −1 |
| `l.sort()` | → void | in place, ascending; `[int]`, `[float]`, `[str]`, `[bool]`, or `[enum]`. A native introsort (quicksort with a heapsort fallback and an insertion-sort finish) — for a custom order use `sort_by(cmp)` from `std/list.zeph`. |

`contains`, `index_of`, `reverse` and `slice` are **not** builtins — they are
generic library functions in `std/list.zeph` (§3.0.5).

The math builtins and `assert` work with any backend; the string and list
methods above are provided by the Zephyr-written runtime, so compile with `--rt`.

These names are reserved; user functions and variables may not use them.

### 3.6 Native interop (unsafe)

The safe language above never exposes a raw address. These builtins do — they
are the primitives the Zephyr-written runtime, the `lib/vk` Vulkan wrapper and
the `lib/ui` GUI toolkit are built from, and they bypass the memory-safety
guarantees of §4. Use them only through a checked wrapper such as
`lib/std/bytes.zeph` (the `Bytes` struct) unless you are writing one.

**Calling native code.** All arguments and returns are `int` (a raw 64-bit
value or address); the Win64 calling convention is used.

| Builtin | Signature | Notes |
|---------|-----------|-------|
| `win(name, args…)` | str, int… → int | Call a statically-imported DLL entry. `name` is a **string literal**; 1–16 int args, marshalled Win64. A `dll!func` prefix picks the DLL — `kernel32!` (default), `user32!`, `gdi32!`, `opengl32!`; a bare name is kernel32. E.g. `win("user32!GetDC", hwnd)`. |
| `callptr(addr, args…)` | int, int… → int | Call a function **address obtained at runtime** — `GetProcAddress`, `wglGetProcAddress`, a COM vtable slot. Same 1–16 int-arg marshalling as `win`. |

`extern fn NAME(p: int, …) -> T from "some.dll"` is the declarative form: it
desugars into an ordinary Zephyr wrapper that resolves the symbol lazily
(`LoadLibraryA` + `GetProcAddress`, cached) and then `callptr`s it. Every
parameter must be `int`; the return must be `int`, `i32`, or nothing.

```zephyr
extern fn MessageBoxA(hwnd: int, text: int, cap: int, flags: int) -> i32 from "user32.dll"
```

**Raw memory.** Addresses are plain `int`s; there is no bounds checking and the
runtime does not count or trace them (see the caution below).

| Builtin | Signature | Notes |
|---------|-----------|-------|
| `load64(a)` / `load8(a)` | int → int | Read 8 / 1 bytes at address `a`. |
| `store64(a, v)` / `store32(a, v)` / `store8(a, v)` | int, int → void | Write 8 / 4 / 1 bytes. |
| `addr(x)` | any → int | Address of a `str`, list, struct, or **function** value. A function yields its `{code, env}` closure cell — the handle a native callback thunk needs. |
| `stackptr()` | → int | Current stack pointer (`rsp`). |
| `bits(x)` | float → int | IEEE-754 bit pattern (also in §3.5), the bridge for passing floats through the int-only FFI. |

Off-heap memory is obtained by calling the OS directly, e.g.
`win("VirtualAlloc", 0, n, 12288, 4)` (MEM_RESERVE|COMMIT, PAGE_READWRITE).
Buffers the OS writes into (a `POINT`, a `RECT`, a swapchain image) **must**
live off-heap this way: a `zeros()`/list allocation is reclaimed as soon as the
last reference to it goes away (§4), and the address you handed the OS does not
count as one; a `VirtualAlloc` region is never reclaimed. The heap itself never
moves an object, so a raw address stays valid exactly as long as some Zephyr
variable still holds the value.

**Linux and WebAssembly.** On `--linux`/`--wasm`, `win("Foo", …)` is rewritten
to the kernel shim `k32_Foo(…)` from `lib/os/{linux,wasm}.zeph`; a non-kernel32
prefix (`user32!…`) is a compile error, and `extern fn … from` (which needs an
import table) is unavailable. Additional builtins on those targets:
`syscall(n, args…)` (raw Linux syscall, 1–7 args), and wasm-only `memgrow`,
`hostwrite`, `hostexit`.

All native interop requires the Zephyr runtime (`--rt`).

## 4. Memory model

All composite values (str, list, struct) are references to heap objects;
assignment and argument passing copy the reference. int, float, and bool are
values. Memory safety guarantees:

1. no dangling references — an object outlives every reference to it
2. no out-of-bounds access — every index is checked (panic on failure)
3. no null and no uninitialized reads — construction requires all values
4. no manual deallocation — there is nothing to double-free

**Reference counting.** Memory is reclaimed by counting, and the compiler
writes the counting for you — there is no `retain`, no `release`, and no
annotation. Every heap object carries a count; each slot holding a reference
(local, parameter, field, element, global) owns one, storing over a slot
releases what it held, and a function releases its locals as it returns. An
object is freed at the instant its last reference goes away, so reclamation is
spread through the program rather than pooled into a pause, and peak memory
tracks the live set rather than twice it. This is an implementation guarantee,
not a language-visible one: a program cannot observe *when* an object is freed.

The heap is **non-moving**. An object stays at the address it was allocated at
for its whole life, which is what makes `addr()` (§3.6) usable at all.

**Cycles and the backstop.** Counting alone cannot reclaim a cycle — a struct
reachable from itself keeps its own count above zero. A conservative mark-sweep
collector therefore stays linked underneath: it scans the machine stack and the
globals array for anything that looks like a heap pointer, so it can only ever
over-retain, never over-free. It runs only when allocation cannot be satisfied
past a growth target, which counting makes rare. A cycle is a leak rather than a
safety break — none of the four guarantees above depends on the collector — but
it is a leak the backstop eventually clears, at the cost of a pause. That pause
is the reason to avoid cyclic structures in latency-sensitive code.

Counts are **not atomic**, which is why a heap reference may never cross a
thread boundary (§8).

On the `--wasm` target the compiler emits no counting; that backend reclaims
with the collector alone.

## 5. Formatting

`print`, interpolation, and `as str` format values as: ints in decimal;
floats with `%.15g` (`5.0` prints as `5`); bools as `true`/`false`; strs
verbatim (but quoted, with `\" \\ \n \t` escaped, when nested inside a list
or struct); lists as `[e1, e2]`; structs as `Name{field: value, ...}`.

## 6. Panics

A panic prints `panic: <message>` to stderr and terminates the process with
exit code 1. Sources: `panic(msg)`, index out of bounds, `/` or `%` by zero
(int), `.pop()` on an empty list, failed `as int`/`as float` parse, and heap
exhaustion. Panics are not catchable.

## 7. Programs and linkage

A compiled program is a standalone native module. The self-hosted compiler
emits assembly, then assembles and links it with its own built-in assembler and
linker — no external tools. Exit code is 0 on normal completion, 1 on panic.
The generated code keeps every value in 64 bits: floats as IEEE bit patterns,
references as pointers.

### 7.1 Targets

The same source compiles to three targets, selected by a flag:

| Flag | Target | Output | Notes |
|------|--------|--------|-------|
| *(default)* | Windows x86-64 | PE64 `.exe` | imports only `kernel32.dll`; the built-in assembler + PE linker write it directly |
| `--linux` | Linux x86-64 | static ELF64 | no libc, no interpreter — the kernel is reached by raw `syscall`. Prepends `lib/os/linux.zeph`, which reimplements the kernel32 surface as `k32_*` |
| `--wasm` | WebAssembly | `.wasm` module | runtime included, reclaiming by collection rather than counting (§4); prepends `lib/os/wasm.zeph`. A separate non-x86 backend |

Not every feature reaches every target. WebAssembly currently omits file I/O,
closures, interfaces and threads; native interop (§3.6) via `extern fn … from`
is Windows-only, and non-kernel32 `win()` prefixes are Windows-only.
`scripts/crosscheck-linux.ps1` and `crosscheck-wasm.ps1` compile the same
sources for two targets and require byte-identical program output.

### 7.2 Command-line flags

```
zc.exe [flags] input.zeph [output]
```

| Flag | Effect |
|------|--------|
| `--rt` | Link the Zephyr-written runtime (memory management, strings, threads, native interop). Output depends only on the target's kernel interface. Required for anything in §3.5/§3.6/§8. |
| `--linux` / `--wasm` | Select the target (§7.1); default is Windows. |
| `-g` / `--debug` | Emit a `.zdbg` debug-info sidecar (native-exe output only). |
| `--version` | Print the compiler version; compiles nothing if given alone. |

The first non-flag argument is the input `.zeph`; the second is the output
path. An output path ending in `.s` writes the generated assembly instead of a
linked module.

## 8. Concurrency

Threads are available on the Windows target through `lib/std/thread.zeph`
(`import "std/thread.zeph"`), and require `--rt`.

| Function | Signature | Notes |
|----------|-----------|-------|
| `thread_spawn(f, arg)` | `fn(int)`, int → `Thread` | Run `f(arg)` on a new OS thread. |
| `t.join()` | `Thread` → void | Block until the thread finishes. |
| `parallel_for(n, f)` | int, `fn(int)` → void | Run `f(0)…f(n-1)` across `cpu_count()` workers, then join. |
| `cpu_count()` | → int | Logical processor count. |

The worker argument is deliberately an `int` — a worker index or a raw buffer
address — **never a heap reference**. Two reasons, either sufficient: it
travels through memory the collector does not scan, and reference counts are
not atomic (§4), so two threads adjusting the same count would race and free an
object that is still in use. Share data by passing an off-heap buffer address
(§3.6) and partitioning it by index.

There is **no user-facing mutex or atomics API**. None is needed while that
rule is kept: threads share no counted object. The backstop collector is
stop-the-world — it suspends every registered thread and scans each one's
register context and stack — so the rare collection is safe under concurrency
without any locking in user code. String interpolation is thread-safe (a per-thread
builder). Threads are not available on `--linux` or `--wasm`.
