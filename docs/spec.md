# Zephyr language specification

Version 0.2. Normative for the self-hosted compiler `compiler/zc.zeph` (built
as `zc.exe`), which is the canonical implementation. The C seed in
`bootstrap/zephyr.c` implements the same language, minus generics, closures,
and function-value types, and exists only to reconstruct the first `zc.exe`.

The compiler emits three native targets from the same source: Windows x86-64
(default), Linux x86-64 (`--linux`), and WebAssembly (`--wasm`) — see §7.

## 1. Source text

Zephyr source is a sequence of bytes interpreted as ASCII/UTF-8. Comments run
from `//` to end of line, or from `/*` to the matching `*/`; block comments
nest, so a commented-out region may itself contain comments. Statements are
terminated by a newline or by the closing `}` of their block. Newlines inside
`(...)` and `[...]` are ignored, so calls and list literals may span lines. A
line whose first token is `.` (but not `..`) continues the previous statement,
so a method chain can be written one call per line.

### 1.1 Tokens

Keywords:

```
fn let var const if else while for in return struct enum impl interface import
as extern from true false none and or not break continue match defer
```

`from` is only a keyword after an `extern fn` signature, and `step` only after
a range in a `for` header; elsewhere both are ordinary identifiers.

Identifiers: `[A-Za-z_][A-Za-z0-9_]*`, excluding keywords.

Literals:

- integer: decimal `[0-9]+`, hex `0x…`, binary `0b…`, octal `0o…`. An `_`
  may separate digits (`1_000_000`, `0xFF_FF`). A decimal literal above
  `9223372036854775807` is a compile error; hex, binary and octal literals
  may use all 64 bits, so `0xFFFFFFFFFFFFFFFF` is `-1`.
- float: `[0-9]+ '.' [0-9]+`, optionally followed by an exponent (`e` or `E`,
  an optional sign, digits): `6.02e23`, `2.5E-3`; `1e3` alone is also a
  float. A leading or trailing dot (`.5`, `5.`) is not a float.
- character: `'a'`, `'\n'`, `'\x1b'` — one byte, of type `int` (its value).
  Non-ASCII characters are written as strings.
- string: `"..."` with interpolation `{expr}` and escapes `\n \t \r \0 \\ \"
  \' \{ \} \xNN`. A plain string may not contain a raw newline.
- raw string: `r"..."` — taken verbatim: no escapes, no interpolation
  (`r"C:\dir\{x}"`).
- multi-line string: `"""..."""` (or raw `r"""..."""`). When the text starts on
  the line after the opening quotes and the closing quotes sit alone on their
  own line, the first newline is dropped and the closing line's indentation is
  removed from every line, so the literal can be indented with its code:

      let usage = """
          zc [flags] input.zeph output
            --rt   link the runtime
          """
      // "zc [flags] input.zeph output\n  --rt   link the runtime"

  A line indented less than the closing quotes is a compile error.
- `true`, `false`, `none`

Operators and punctuation:

```
+ - * / % == != < <= > >= = += -= *= /= %= &= |= ^= <<= >>=
-> .. . , : ? ( ) [ ] { } & | ^ << >> ~
```

## 2. Grammar

EBNF; `NL` is one or more newline terminators.

```ebnf
program    = { toplevel } ;
toplevel   = fndecl | structdecl | enumdecl | impldecl | ifacedecl
           | externdecl | import | typealias | stmt ;
typealias  = "type" ID "=" type ;
externdecl = "extern" "fn" ID "(" [ param { "," param } ] ")"
             [ "->" type ] "from" STRING ;                    (* §3.6, native DLL import *)

fndecl     = "fn" ID [ "[" ID { "," ID } "]" ]                (* type params *)
             "(" [ param { "," param } ] ")" [ "->" type ] block ;
param      = ID ":" type [ "=" expr ] | "self" ;              (* self only in impl/interface *)
structdecl = "struct" ID [ "[" ID { "," ID } "]" ]            (* type params *)
             "{" { ID ":" type [ "=" expr ] [ "," ] } "}" ;
enumdecl   = "enum" ID "{" ID { "," ID } "}" ;
impldecl   = "impl" ID [ "[" ID { "," ID } "]" ] "{" { fndecl } "}" ; (* methods on a struct or enum *)
ifacedecl  = "interface" ID "{" { fnsig } "}" ;               (* method signatures *)
fnsig      = "fn" ID "(" [ param { "," param } ] ")" [ "->" type ] ;
import     = "import" STRING ;

type       = basetype [ "?" ] ;                              (* T? optional *)
basetype   = "int" | "i32" | "float" | "bool" | "str"
           | ID [ "[" type { "," type } "]" ]                (* Box[int]: generic struct *)
           | "[" type "]"                                    (* list *)
           | "[" type ":" type "]"                           (* map *)
           | "fn" "(" [ type { "," type } ] ")" [ "->" type ]  (* function value *)
           | "(" type "," type { "," type } ")" ;             (* tuple *)

block      = "{" { stmt } "}" ;
stmt       = decl | assign | ifstmt | while | for | match | defer | return | fndecl
           | "break" [ ID ] | "continue" [ ID ] | expr ;
decl       = ( "let" | "var" | "const" ) ID [ ":" type ] "=" expr
           | ( "let" | "var" ) "(" ID { "," ID } ")" [ ":" type ] "=" expr ;
assign     = target ( "=" | "+=" | "-=" | "*=" | "/=" | "%="
                    | "&=" | "|=" | "^=" | "<<=" | ">>=" ) expr ;
target     = ID | postfix "." ID | postfix "[" expr "]" ;
ifstmt     = "if" [ "let" ID "=" ] expr block [ "else" ( ifstmt | block ) ] ;
while      = [ ID ":" ] "while" expr block ;
for        = [ ID ":" ] "for" ID [ "," ID ] "in" expr
             [ ".." expr [ "step" expr ] ] block ;
match      = "match" expr "{" { arm } [ "else" block ] "}" ;
arm        = pattern { "," pattern } block ;
pattern    = expr [ ".." expr ] ;                            (* value, range, or member *)
defer      = "defer" ( block | stmt ) ;
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
unary      = ( "-" | "not" | "~" ) unary | postfix ;
postfix    = primary { "(" args ")" | "[" expr "]" | "." ID } ;
primary    = INT | FLOAT | STRING | "true" | "false" | "none" | ID
           | "if" expr "{" expr "}" "else" ( "{" expr "}" | primary ) (* if-expression *)
           | "match" expr "{" { pattern { "," pattern } "{" expr "}" }
                 [ "else" "{" expr "}" ] "}"                (* match expression *)
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
All binary operators are left-associative, except that comparisons chain:
`a < b <= c` means `a < b and b <= c` (see §3.3). (The bitwise levels follow
Go: `& << >>` bind like `*`, `| ^` bind like `+`.) `x op= y` means
`x = x op y`.

Disambiguation: an identifier followed by `{` is a struct literal, except in
the header expression of `if`/`while`/`for`, where `{` begins the block
(parenthesize to force a literal there). `fn` and `struct` are only allowed
at the top level.

## 3. Types

`int` (64-bit signed, wrapping on overflow), `float` (IEEE 754 double),
`bool`, `str` (immutable byte string), `[T]` (growable list), `[K: V]` (hash
map), and named struct and enum types. `void` is the type of no value; it
cannot be named in source.

`i32` (listed in the grammar above) is a 32-bit signed integer that exists only as an `extern fn` return type
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

`n as Color` converts an int back to a member and panics if `n` is not a
member's ordinal. `Color.all()` is the list of members in order and
`Color.count` their number. An `impl Color { ... }` block adds methods and
associated functions to an enum exactly as to a struct (§3.0.6).

### 3.0.0 Type aliases and struct defaults

`type Name = T` at the top level gives an existing type a second name; the
two are the same type and mix freely. Aliases may refer to other aliases,
but not in a cycle.

    type Grid = [[int]]

A struct field may declare a default, `width: int = 800`, used when a
literal leaves the field out. An optional field with no default defaults to
`none`. Any other field a literal leaves out is an error. Defaults are
evaluated each time a literal uses them, under the same naming rule as
default parameters (§3.4).

### 3.0.0.1 Tuples

    fn divmod(a: int, b: int) -> (int, int) { return (a / b, a % b) }
    let (q, r) = divmod(17, 5)
    let pair = divmod(9, 2)
    print(pair.0)               // 4
    print(pair)                 // (4, 1)

`(T, U, ...)` is a tuple type of two or more elements and `(a, b, ...)` a
tuple value; `(x)` is still just `x` in parentheses. Elements are read with
`.0`, `.1`, ... and cannot be assigned: a tuple is built whole. Two tuple
types are the same when their element types are. `let (a, b) = t` (or `var`)
binds each element to a name; the number of names must match the tuple.
Tuples compare with `==` element by element, print as `(1, "a")`, and can be
map keys when their elements can (§3.0.1).

### 3.0.1 Maps

    var ages: [str: int] = ["alice": 30, "bob": 25]
    ages["carol"] = 41          // insert or update
    print(ages["alice"])        // panics if the key is absent
    print(ages.has("bob"))

`[K: V]` is a hash map. The key type `K` must be `int`, `str`, `bool`, an
enum, or a list, struct or optional built only from those — types compared by
value (§3.3). Floats (NaN is not equal to itself) and maps cannot be keys.
Lists and structs are mutable: changing one after using it as a key leaves it
filed under its old hash, so lookups of it become unreliable. `[:]` is the
empty map literal and, like `[]`, needs an annotation to supply its type.

Reading a missing key panics; use `.has(k)` to test first, or `.get(k)`,
which returns `V?` (§3.0.4). Methods: `.len()`, `.has(k)`, `.get(k)` → `V?`,
`.remove(k)`, `.keys()` → `[K]`, `.values()` → `[V]`. Iterate with
`for k in m.keys()`. Iteration order is unspecified. Maps are open-addressed
and rehash at 50% occupied slots (including tombstones), so insert/lookup
are amortized O(1).

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
address. Any expression of function type may be called: `ops["up"](10)`.

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

Generics are monomorphised: each distinct set of type arguments compiles to its
own copy of the body, type-checked with `T` bound. That checking is the whole
contract — `contains` compiles `v == x` for the concrete `T`, so it works for
`int`, `str` and enums, and is rejected for element types with no `==`. There is
no trait system.

A generic function has no single type, so it cannot be used as a function value.

`std/list.zeph` is written entirely in these terms — `contains`, `index_of`,
`reverse`, `slice`, `map`, `filter`, `fold`, `any`, `all`, `first`, `last`,
`sort_by`. They were compiler builtins before generics existed. `import` it:

    import "std/list.zeph"

### 3.0.5.1 Generic structs

    struct Pair[A, B] { first: A, second: B }
    struct Stack[T] { items: [T] = [] }

    impl Stack[T] {
        fn push(self, item: T) { self.items.push(item) }
        fn map_all[U](self, f: fn(T) -> U) -> Stack[U] { ... }
        fn new() -> Stack[T] { return Stack{} }
    }

    let p = Pair{first: 1, second: "one"}      // Pair[int, str], inferred
    var s: Stack[int] = Stack{}                // the annotation supplies T
    let t: Stack[str] = Stack.new()            // so does an expected result

A struct may take type parameters. `Name[T, ...]` names one instance of it;
each distinct set of type arguments is its own struct type, checked and
compiled separately, like a generic function (§3.0.5). A literal `Pair{...}`
infers the arguments from its field values, or takes them from the type the
context expects; empty `[]`, `[:]` and `none` values infer nothing. A generic
struct named without its type arguments is an error.

`impl Stack[T] { ... }` gives every instance the methods, which are generic
over the impl's parameters (and may add their own). A generic function's type
parameters are inferred from its arguments and, failing that, from the type
its result is expected to have. Instances print under the template's name
(`Pair{first: 1, second: "one"}`) and compare and hash structurally (§3.3).
Instances do not yet satisfy interfaces.

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
dispatches through the struct's vtable, so a `[Shape]` may hold circles and
rects. Interface values cannot be printed directly; call a method instead. There
is no implementation inheritance.

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

`const` declares an immutable binding whose value is known at compile time:
its initializer may use only literals, other consts declared before it, enum
members, and operators or `as` conversions over those. A top-level const is
initialized before any other top-level code, so every function may use it
regardless of where it is declared. Assigning to a const is an error.

    const MAX_PLAYERS = 8
    const GRID = MAX_PLAYERS * 4 + 1

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
- `~x`: bitwise complement of an int (`x ^ -1`).
- `== !=`: numbers (mixed widens), bools, strs (byte equality), enums, and
  — structurally — two lists, structs, optionals or maps of the same type:
  equal when their elements, fields, wrapped values or entries are equal
  (maps ignore order). Function and interface values have no `==`.
  `x == none` / `x != none` on an optional is a presence test, the same as
  `not x.has()` / `x.has()`. Comparing a structure that contains itself does
  not terminate.
- `< <= > >=`: numbers or strs (lexicographic byte order). Consecutive
  comparisons chain: `lo <= x < hi` is `lo <= x and x < hi`. The middle
  operand appears twice, so it may not contain a call; store a call's result
  in a variable first.
- `and or not`: bools only; `and`/`or` short-circuit.
- Unary `-`: numeric.
- Conditions of `if`/`while` must be `bool`.

### 3.4 Functions

Parameter and return types are declared; a function with a non-void return
type must provably return on every path: a `return`, a `panic(...)`, a
`while true` loop with no `break`, or an `if`/`else` whose branches both do. Top-level code runs in order; functions and structs
may be referenced before their declaration. Function and variable namespaces
are shared: a call resolves builtins first, then declared functions.

Method syntax is universal function call syntax: `a.f(b)` is exactly
`f(a, b)` for any declared function `f` whose first parameter accepts `a`.

A parameter may declare a default, `greeting: str = "Hello"`; a call may then
leave it out. Once one parameter has a default, every later one must too. The
default is evaluated at each call that uses it. It may use globals, consts and
functions but not the other parameters, and a call site where one of the names
it uses is a local variable is an error (rename the local).

A `fn` declared inside a function body is a local function: it is a closure
(§3.0.3) bound to a `let` of that name, so it captures by value and is visible
from its declaration to the end of the block. Local functions cannot be
generic or take default parameters.

### 3.4.1 Control flow

**If-expressions.** `if c { a } else { b }` is also an expression, which is
how Zephyr spells a conditional value (there is no `?:`). Each branch holds a
single expression, `else` is required, and `else if` chains:

    let size = if n > 100 { "big" } else if n > 10 { "medium" } else { "small" }

Both branches must have the same type (an `int` branch widens to `float` to
match a `float` one). If one branch is `none`, the result is the other
branch's type made optional: `if found { i } else { none }` is an `int?`.

**match.** A `match` compares one value against each arm's patterns in order
and runs the first arm that matches:

    match shape {
        Circle { area = PI * r * r }
        Square, Rect { area = w * h }
        else { area = 0.0 }
    }

A pattern is a value compared with `==` (a literal, a const, any expression),
a half-open range `lo..hi` (matches `lo <= x < hi`), or, when the subject is
an enum, a member name — bare (`Red`) or qualified (`Color.Red`). Commas list
several patterns for one arm. The subject is evaluated once. The optional
`else` arm comes last.

A match on an enum must cover every member (or have an `else` arm), and a
match on a `bool` must cover both values; a match on any other type needs an
`else` arm. Covering the same member twice is an error. Arms are written
`pattern { ... }` — there is no `=>`.

A match is also an expression. Each arm then holds a single expression, as an
if-expression's branches do, and the same coverage rules apply:

    let name = match c {
        Red { "red" }
        Green, Blue { "cool" }
    }

**if let.** `if let name = optional { ... } else { ... }` runs the first block
with `name` bound to the unwrapped value when the optional holds one, and the
`else` block (optional) when it is `none`.

**Loops.** Beyond `for i in lo..hi` and `for x in list`:

| Form | Iterates |
|------|----------|
| `for i in lo..hi step s` | from `lo` toward `hi` (excluded) in steps of `s`; a negative `s` counts down (`for i in 10..0 step -1` is 10 to 1). `s` may be any int expression; 0 panics. |
| `for i, x in list` | index and element |
| `for b in text` | the bytes of a `str`, as `int`s (`'a'` is also an `int`) |
| `for i, b in text` | index and byte |
| `for key in map` | the keys (same as `map.keys()`) |
| `for key, value in map` | keys and their values |

**Labeled loops.** A loop may carry a label, `name: for ...` or
`name: while ...`, and `break name` / `continue name` then act on that loop
instead of the innermost one:

    outer: for row in grid {
        for cell in row {
            if cell == 0 { continue outer }
            if cell < 0 { break outer }
        }
    }

**defer.** `defer stmt` or `defer { ... }` schedules code to run when control
leaves the enclosing block: at its end, and before every `return`, `break` or
`continue` that exits it. Several defers in one block run in reverse order.
A `return` value is computed before the deferred code runs. Deferred code may
not itself return, break or continue out; a panic ends the program without
running it.

    fn save(path: str, data: str) {
        let log = open_log()
        defer log.close()
        ...
    }

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
| `frombits(n)` | int → float | the inverse of `bits`, zero cost |
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
| `pow(b, e)` | int, int → int | fast exponentiation; `e < 0` yields 0 (integer division of 1 by `b^-e`) |

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
| `l.sort()` | → void | in place, ascending; `[int]`, `[float]`, `[str]`, `[bool]`, or `[enum]`. A native introsort (quicksort with a heapsort fallback and an insertion-sort finish) — for a custom order use `sort_by(cmp)` from `std/list.zeph`. |

`contains`, `index_of`, `reverse`, `slice` and `count` are **not** builtins —
they are generic library functions in `std/list.zeph` (§3.0.5), called with
method syntax once imported: `xs.contains(3)`.

`sqrt` is the only transcendental builtin, because it is one instruction.
Everything else lives in `std/math.zeph`, written in ordinary Zephyr for a
runtime with no libm: `fexp`, `fln`, `fsin`, `fcos`, `ftan` and the reciprocals
`fcsc`, `fsec`, `fcot`; the inverses `fatan`, `fasin`, `facos`, `facot`,
`fasec`, `facsc`; `sinh`, `cosh`, `tanh`; the gudermannian `gd` and `gd_inv`;
`gamma`, `lgamma` and `digamma`; a `d_`-prefixed analytic derivative for each;
and `integrate` / `integrate_p` for definite integrals by adaptive Simpson.
Constants `PI`, `TWO_PI`, `HALF_PI`, `LN2`, `NAN` and `INF` come with it.

Two conventions worth knowing before you use them. Arguments outside a
function's domain yield `NAN`, as `sqrt(-1.0)` already does, so test results
with `is_nan(x)` rather than comparing against a sentinel. And `facot` is the
continuous branch with range `(0, pi)` — the calculus convention — not the
`atan(1/x)` one that jumps at the origin.

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
| `load64(a)` / `load32(a)` / `load16(a)` / `load8(a)` | int → int | Read 8 / 4 / 2 / 1 bytes at address `a`; narrower reads zero-extend. |
| `store64(a, v)` / `store32(a, v)` / `store8(a, v)` | int, int → void | Write 8 / 4 / 1 bytes. |
| `addr(x)` | any → int | Address of a `str`, list, struct, or **function** value. A function yields its `{code, env}` closure cell — the handle a native callback thunk needs. |
| `stackptr()` | → int | Current stack pointer (`rsp`). |
| `bits(x)` | float → int | IEEE-754 bit pattern (also in §3.5), the bridge for passing floats through the int-only FFI. |

Off-heap memory is obtained by calling the OS directly, e.g.
`win("VirtualAlloc", 0, n, 12288, 4)` (MEM_RESERVE|COMMIT, PAGE_READWRITE).
Buffers the OS writes into (a `POINT`, a `RECT`, a swapchain image) **must**
live off-heap this way. A `zeros()`/list allocation is freed as soon as the last
reference goes away (§4), and the address you handed the OS does not count as
one; a `VirtualAlloc` region is never reclaimed. The heap does not move objects,
so a raw address stays valid exactly as long as some Zephyr variable still holds
the value.

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

Memory is reclaimed by reference counting, inserted by the compiler; there is no
retain, release or annotation in source. Every heap object carries a count. Each
slot holding a reference — local, parameter, field, element, global — owns one,
storing over a slot releases what it held, and a function releases its locals as
it returns. An object is freed when its last reference goes away, so peak memory
tracks the live set rather than twice it. A program cannot observe *when* an
object is freed; the timing is an implementation property, not a language rule.

The heap is non-moving. An object keeps its address for its whole life, which is
what makes `addr()` (§3.6) usable.

Counting cannot reclaim a cycle: a struct reachable from itself keeps its own
count above zero. A conservative mark-sweep collector stays linked underneath,
scanning the machine stack and the globals array for anything that looks like a
heap pointer, so it can only over-retain, never over-free. It runs only when
allocation cannot be satisfied past a growth target, which counting makes rare.
A cycle is a leak, not a safety break — none of the four guarantees above
depends on the collector — but clearing it costs a pause, which is why cyclic
structures are worth avoiding in latency-sensitive code.

Counts are not atomic. That is why a heap reference may never cross a thread
boundary (§8).

The `--wasm` backend emits no counting and reclaims with the collector alone.

## 5. Formatting

`print`, interpolation, and `as str` format values as: ints in decimal;
floats with `%.15g` (`5.0` prints as `5`); bools as `true`/`false`; strs
verbatim (but quoted, with `\" \\ \n \t` escaped, when nested inside a list
or struct); lists as `[e1, e2]`; structs as `Name{field: value, ...}`.

## 6. Panics

A panic prints `panic: <file>:<line>: <message>` to stderr (the source
location of the panicking operation) and terminates the process with exit
code 1. Sources: `panic(msg)`, index out of bounds, `/` or `%` by zero
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
Threads and synchronization primitives are available on both Windows and Linux
x86-64 with `--rt` (§8).
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

Threads are available on Windows and Linux x86-64 through `lib/std/thread.zeph`
(`import "std/thread.zeph"`), and require `--rt`.

| Function | Signature | Notes |
|----------|-----------|-------|
| `thread_spawn(f, arg)` | `fn(int)`, int → `Thread` | Run `f(arg)` on a new OS thread. |
| `t.join()` | `Thread` → void | Block until the thread finishes. |
| `parallel_for(n, f)` | int, `fn(int)` → void | Run `f(0)…f(n-1)` across n workers, then join. |
| `cpu_count()` | → int | Logical processor count. |

The worker argument is an `int` — a worker index or a raw buffer address — and
never a heap reference. Either reason alone is sufficient: it travels through
memory the collector does not scan, and counts are not atomic (§4), so two
threads adjusting the same count would race and free an object still in use.
Share data by passing an off-heap buffer address (§3.6) and partitioning it by
index.

`import "std/sync.zeph"` provides `Mutex`, `Atomic`, bounded FIFO `Channel`, and
`WaitGroup` wrappers over off-heap storage. Atomics and channels carry `int`
values; use `bits`/`frombits` for floats. Pass the integer `address` field to a
worker and construct its own local wrapper: the wrappers themselves are counted
heap objects and must not be shared. Their native storage lasts until process
exit. Synchronization does not make shared reference counts safe.

Linux starts threads with a machine-code `clone` trampoline on mapped stacks.
Futexes implement the startup gate, join, recursive critical sections, and
condition variables. Each thread has its own TLS table selected by stack range;
string interpolation uses a per-thread builder on both native targets.

On Windows the backstop collector remains stop-the-world: it suspends every
other registered thread and scans its register context and stack. Linux cannot
suspend threads without signal handlers, so collection is deferred while any
worker remains unjoined, including a worker requesting collection itself.
Reference counting continues to reclaim acyclic objects; cyclic garbage may grow
until the workers are joined and a later collection runs. Join every worker. Threads
are not available on `--wasm`.
