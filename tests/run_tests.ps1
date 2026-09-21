# Zephyr test suite. Builds the compiler, then runs positive, negative, and panic tests.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root
& .\bootstrap\build.ps1
if ($LASTEXITCODE -ne 0) { exit 1 }

$pass = 0; $fail = 0
$tmp = Join-Path $env:TEMP "zephyr_tests"
New-Item -ItemType Directory -Force $tmp | Out-Null

function Check($name, $ok, $detail) {
    if ($ok) { $script:pass++; Write-Host "PASS $name" }
    else { $script:fail++; Write-Host "FAIL $name -- $detail" -ForegroundColor Red }
}

function RunSrc($name, $src) {
    $f = Join-Path $tmp "$name.zeph"
    Set-Content -Path $f -Value $src -Encoding ascii
    $out = cmd /c ".\bootstrap\zephyr.exe run `"$f`" 2>&1"
    return @{ code = $LASTEXITCODE; out = ($out | Out-String).Trim() }
}

# ---- positive: examples with expected output ----
$expected = @{
    "hello"   = "Hello, Zephyr!"
    "convert" = "10.5`n6.28`n13`ncount is 13`n3.5`n-7"
    "shapes"  = "5`n5`nPoint{x: 6, y: 8}`n3`n(0, 0)`n(3, 4)`n(6, 8)"
}
foreach ($name in $expected.Keys) {
    $out = (& .\bootstrap\zephyr.exe run "examples\basics\$name.zeph" | Out-String).Trim() -replace "`r", ""
    $want = $expected[$name] -replace "`r", ""
    Check "example:$name" ($out -eq $want) "got: $out"
}

# fizzbuzz: compare against computed expectation
$fb = for ($i = 1; $i -le 100; $i++) {
    if ($i % 15 -eq 0) { "FizzBuzz" } elseif ($i % 3 -eq 0) { "Fizz" }
    elseif ($i % 5 -eq 0) { "Buzz" } else { "$i" }
}
$out = (& .\bootstrap\zephyr.exe run "examples\basics\fizzbuzz.zeph" | Out-String).Trim() -replace "`r", ""
Check "example:fizzbuzz" ($out -eq (($fb -join "`n"))) "fizzbuzz mismatch"

# ---- language features ----
$r = RunSrc "features" @'
fn fib(n: int) -> int {
    if n < 2 { return n }
    return fib(n - 1) + fib(n - 2)
}
print(fib(20))

var total = 0
for i in 0..10 {
    if i % 2 == 0 { continue }
    if i > 7 { break }
    total += i
}
print(total)

let words = ["c", "a", "b"]
var best = words[0]
for w in words {
    if w < best { best = w }
}
print(best)

struct Box { v: int }
fn bump(b: Box, by: int) { b.v += by }
let box = Box{v: 40}
box.bump(2)
print(box.v)

var xs: [int] = []
xs.push(7)
xs.push(8)
print(xs.pop() + xs.len())

let cond = true and not false or false
print(cond)
print("esc: \"q\" \\ {1 + 1}")
'@
Check "features" ($r.code -eq 0 -and $r.out -eq "6765`n16`na`n42`n9`ntrue`nesc: `"q`" \ 2".Replace("`n", [Environment]::NewLine).Trim()) "got($($r.code)): $($r.out)"

# ---- bitwise operators ----
$r = RunSrc "bitwise" @'
print(12 & 10)
print(12 | 10)
print(12 ^ 10)
print(1 << 40)
print(-16 >> 2)
print(1 + 1 << 3)
print(1 | 2 ^ 3 & 2)
var n = 5
var s = 3
print(n << s)
print(255 & n + 3)
'@
$exp = @("8","14","6","1099511627776","-4","9","1","40","8") -join [Environment]::NewLine
Check "bitwise" ($r.code -eq 0 -and $r.out -eq $exp) "got($($r.code)): $($r.out)"

# ---- Zephyr runtime (--rt): kernel32-only exe, runtime written in Zephyr ----
$rtdir = Join-Path $tmp "rt_iso"
New-Item -ItemType Directory -Force $rtdir | Out-Null
$rtsrc = @'
struct P { x: int, y: int }
let greeting = "runtime in {1 + 1 - 2}? no, in Zephyr"
print(greeting)
var xs: [int] = []
for i in 1..6 { xs.push(i * i) }
print(xs)
print(xs.len())
let p = P{x: 7, y: 8}
print(p)
print(p.x + p.y)
print("42" as int + 8)
print(12 & 10)
print(1 << 30)
var sum = 0
for i in 1..101 { sum += i }
print("sum={sum}")
'@
Set-Content -Path "$tmp\rtprog.zeph" -Value $rtsrc -Encoding ascii
& .\bootstrap\zephyr.exe build "$tmp\rtprog.zeph" -o "$rtdir\rtprog.exe" --rt 2>&1 | Out-Null
$rtBuilt = Test-Path "$rtdir\rtprog.exe"
# run in an isolated dir with NO zephyr_rt.dll present
$rtOut = if ($rtBuilt) { (cmd /c "`"$rtdir\rtprog.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$rtWant = (& .\bootstrap\zephyr.exe run "$tmp\rtprog.zeph" | Out-String).Trim() -replace "`r", ""
$noDll = -not (Test-Path "$rtdir\zephyr_rt.dll")
Check "rt:zephyr-runtime" ($rtBuilt -and $noDll -and $rtOut -eq $rtWant) "built=$rtBuilt noDll=$noDll out=$rtOut"

# ---- unsafe intrinsics: raw memory + addr (byte widths must be exact) ----
$r = RunSrc "intrinsics" @'
var s = " ".sub(0, 0)
for i in 0..4 { s = s + " " }
let p = addr(s) + 8
// write high-to-low so an over-wide store would clobber earlier bytes
store8(p + 3, 68)
store8(p + 2, 67)
store8(p + 1, 66)
store8(p + 0, 65)
print(s)
print(load8(p + 0))
print(load8(p + 3))
var xs: [int] = [7, 0]
let d = load64(addr(xs) + 16)   // list data pointer
store64(d, 99)
print(xs[0])
print(load64(d))
'@
$exp = @("ABCD","65","68","99","99") -join [Environment]::NewLine
Check "intrinsics" ($r.code -eq 0 -and $r.out -eq $exp) "got($($r.code)): $($r.out)"

# ---- ffi_runtime example: I/O + int formatting in pure Zephyr via kernel32 ----
& .\bootstrap\zephyr.exe build examples\basics\ffi_runtime.zeph -o "$tmp\ffir.exe" | Out-Null
Copy-Item bootstrap\zephyr_rt.dll "$tmp\zephyr_rt.dll" -Force
$out = (& "$tmp\ffir.exe" | Out-String).Trim() -replace "`r", ""
$want = "integers formatted and printed by a Zephyr-written runtime:`n0`n42`n-1234567`n1000000000`nsum 1..100 = 5050" -replace "`r", ""
Check "ffi-runtime" ($out -eq $want) "got: $out"

# ---- emit: stdout without newline ----
$r = RunSrc "emit" @'
emit("a")
emit("b{1 + 1}")
emit("\n")
print("done")
'@
Check "emit" ($r.code -eq 0 -and $r.out -eq "ab2$([Environment]::NewLine)done") "got($($r.code)): $($r.out)"

# ---- GC stress: allocate far past the threshold ----
$r = RunSrc "gcstress" @'
struct P { s: str, n: int }
var keep: [str] = []
for i in 0..200000 {
    let p = P{s: "item {i}", n: i}
    if i % 10000 == 0 { keep.push(p.s) }
}
print(keep.len())
print(keep[19])
'@
Check "gc-stress" ($r.code -eq 0 -and $r.out -eq "20$([Environment]::NewLine)item 190000") "got($($r.code)): $($r.out)"

# ---- division semantics: constant divisors (magic multiply) must match idiv ----
$r = RunSrc "divsem" @'
var vals = [-7, 7, -100, 100, 0, 9223372036854775807]
var divs = [1, -1, 2, -2, 3, 7, 10, 65537, 4096]
for n in vals {
    for d in divs {
        print("{n / d} {n % d}")
    }
}
print(-7 / 2)
print(-7 % 2)
print(7 / -2)
print(7 % -2)
print(-9 % 3)
'@
# expected: computed with the same trunc-toward-zero rules
$exp = @()
foreach ($n in @([long]-7, 7, -100, 100, 0, 9223372036854775807)) {
    foreach ($d in @([long]1, -1, 2, -2, 3, 7, 10, 65537, 4096)) {
        $q = [math]::Truncate($n / [double]$d)
        # PS double division loses precision on big ints; compute exactly:
        $q = [long][math]::Truncate([decimal]$n / [decimal]$d)
        $rm = $n - $q * $d
        $exp += "$q $rm"
    }
}
$exp += "-3"; $exp += "-1"; $exp += "-3"; $exp += "1"; $exp += "0"
Check "div-semantics" ($r.code -eq 0 -and $r.out -eq (($exp -join [Environment]::NewLine))) "mismatch"

# ---- globals + new builtins (io, str utils, args) ----
$tmpFwd = $tmp -replace "\\", "/"
$r = RunSrc "globals_io" @"
let GREET = "hi"
var counter = 0
fn bump() { counter += 1 }
fn greet() -> str { return GREET }
bump()
bump()
print(counter)
print(greet())
let s = "hello world"
print(s.byte(0))
print(s.sub(6, 11))
print(chr(65) + chr(66))
print(["a", "b", "c"].join())
write_file("$tmpFwd/io_test.txt", "round {1 + 1}")
print(read_file("$tmpFwd/io_test.txt"))
print(args().len())
"@
$want = "2`nhi`n104`nworld`nAB`nabc`nround 2`n1".Replace("`n", [Environment]::NewLine)
Check "globals-io" ($r.code -eq 0 -and $r.out -eq $want) "got($($r.code)): $($r.out)"

# a heap object whose only reference is a global must survive collection
$r = RunSrc "globals_gc" @'
var g = "keep {123}"
fn churn() {
    for i in 0..100000 { let t = "x{i}" }
}
churn()
print(g)
'@
Check "globals-gc" ($r.code -eq 0 -and $r.out -eq "keep 123") "got($($r.code)): $($r.out)"

# ---- compile errors ----
$errors = @{
    "type-mismatch"  = 'let x: int = "hi"'
    "immutable"      = "let x = 1`nx = 2"
    "unknown-var"    = "print(y)"
    "non-bool-cond"  = "if 1 { print(1) }"
    "missing-return" = "fn f() -> int { let x = 1 }"
    "bad-cast"       = "let b = true`nlet n = b as int"
    "arity"          = "fn f(a: int) -> int { return a }`nprint(f(1, 2))"
    "void-assign"    = "let xs = [1]`nlet y = xs.push(2)"
}
foreach ($name in $errors.Keys) {
    $r = RunSrc "err_$name" $errors[$name]
    Check "error:$name" ($r.code -ne 0 -and $r.out -match "error:") "expected compile error, got($($r.code)): $($r.out)"
}

# ---- runtime panics ----
$panics = @{
    "index-oob"   = "let xs = [1, 2]`nprint(xs[5])"
    "div-zero"    = "let z = 0`nprint(1 / z)"
    "bad-parse"   = 'let n = "abc" as int'
    "empty-pop"   = "var xs: [int] = []`nprint(xs.pop())"
    "user-panic"  = 'panic("boom")'
}
foreach ($name in $panics.Keys) {
    $r = RunSrc "panic_$name" $panics[$name]
    Check "panic:$name" ($r.code -eq 1 -and $r.out -match "panic:") "expected panic, got($($r.code)): $($r.out)"
}

# ---- self-hosted stdlib builtins (compiled by zc.exe --rt) ----
Remove-Item "$tmp\stdlib.exe" -ErrorAction SilentlyContinue
$stdBuild = (& .\zc.exe --rt examples\basics\stdlib.zeph "$tmp\stdlib.exe" 2>&1 | Out-String).Trim()
$stdBuilt = Test-Path "$tmp\stdlib.exe"
if (-not $stdBuilt) { Write-Host "  stdlib build output: $stdBuild" -ForegroundColor Yellow }
$stdOut = if ($stdBuilt) { (cmd /c "`"$tmp\stdlib.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$stdWant = @("7","3","8","65536","HELLO, WORLD","Hello, Zephyr","true","7","true","3","hi","ababab","true","5","2","[1, 3, 5, 9]","3.14159","1.4142135623731","0.25","Green","true","2","30","2","true","false","2","1","-1","30","0","none","true","[1, 4, 9, 16]","81","[1, 4, 9]","[2, 4]","10","[101, 102]","true","ok") -join "`n"
Check "stdlib-builtins" ($stdBuilt -and $stdOut -eq $stdWant) "got: $stdOut"

# ---- std/math.zeph function family: trig reciprocals, inverse trig,
# ---- hyperbolics, gamma/digamma, gudermannian, derivatives, quadrature ----
Remove-Item "$tmp\math_fns.exe" -ErrorAction SilentlyContinue
$mathBuild = (& .\zc.exe --rt tests\math_fns.zeph "$tmp\math_fns.exe" 2>&1 | Out-String).Trim()
$mathBuilt = Test-Path "$tmp\math_fns.exe"
if (-not $mathBuilt) { Write-Host "  math build output: $mathBuild" -ForegroundColor Yellow }
$mathOut = if ($mathBuilt) { (cmd /c "`"$tmp\math_fns.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
Check "std-math-fns" ($mathBuilt -and $mathOut -eq "math: 213 checks passed") "got: $mathOut"

# ---- lib/ml tensor descriptors and storage: acceptance A02 and A03 ----
Remove-Item "$tmp\tensor_test.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt tests\ml\tensor_test.zeph "$tmp\tensor_test.exe" 2>&1 | Out-Null
$tenBuilt = Test-Path "$tmp\tensor_test.exe"
$tenOut = if ($tenBuilt) { (cmd /c "`"$tmp\tensor_test.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
Check "ml-tensor" ($tenBuilt -and $tenOut -eq "tensor: 73 checks passed") "got: $tenOut"

# ---- and the inputs that must be REJECTED, one process each: a rejection is
# ---- a panic, so it cannot be asserted from inside the positive suite ----
$mlNeg = [ordered]@{
    "negdim"      = 'let t = t_zeros(DType.F64, [0 - 2, 3])'
    "overflow"    = 'let t = t_zeros(DType.F64, [3000000000, 3000000000])'
    "bytecap"     = 'let t = t_zeros(DType.C64, [500000000000])'
    "idx-high"    = "let t = t_zeros(DType.F64, [2, 3])`nprint(`"{t_get(t, [2, 0])}`")"
    "idx-neg"     = "let t = t_zeros(DType.F64, [2, 3])`nprint(`"{t_get(t, [0 - 1, 0])}`")"
    "idx-rank"    = "let t = t_zeros(DType.F64, [2, 3])`nprint(`"{t_get(t, [1])}`")"
    "reshape-n"   = "let t = t_zeros(DType.F64, [2, 3])`nlet r = t_reshape(t, [4, 2])"
    "reshape-nc"  = "let t = t_zeros(DType.F64, [2, 3])`nlet r = t_reshape(t_transpose(t, 0, 1), [6])"
    "slice-oob"   = "let t = t_zeros(DType.F64, [2, 3])`nlet s = t_slice(t, 1, 1, 9)"
    "axis-oob"    = "let t = t_zeros(DType.F64, [2, 3])`nlet x = t_transpose(t, 0, 5)"
    "bcast-bad"   = 'let s = broadcast_shape([2, 3], [4, 3])'
    "stale-save"  = "let t = t_zeros(DType.F64, [2])`nlet s = t_save(t)`nt_set(t, [0], 1.0)`nlet b = saved_get(s)"
    "dbl-release" = "let t = t_zeros(DType.F64, [2])`nstorage_release(t.st)`nstorage_release(t.st)"
    "cplx-get"    = "let t = t_zeros(DType.C32, [2])`nprint(`"{t_get(t, [0])}`")"
    "int-set"     = "let t = t_zeros(DType.I64, [2])`nt_set(t, [0], 1.5)"
}
foreach ($nm in $mlNeg.Keys) {
    $src = "import `"ml/tensor.zeph`"`n" + $mlNeg[$nm]
    $f = Join-Path $tmp "mlneg_$nm.zeph"
    $x = Join-Path $tmp "mlneg_$nm.exe"
    Set-Content -Path $f -Value $src -Encoding ascii
    Remove-Item $x -ErrorAction SilentlyContinue
    & .\zc.exe --rt $f $x 2>&1 | Out-Null
    if (-not (Test-Path $x)) { Check "ml-reject:$nm" $false "did not compile"; continue }
    $o = (cmd /c "`"$x`" 2>&1" | Out-String).Trim()
    Check "ml-reject:$nm" ($LASTEXITCODE -ne 0 -and $o -match "panic:") "expected panic, got($LASTEXITCODE): $o"
}

# ---- lib/ml CPU operators: acceptance A04 and A05 ----
Remove-Item "$tmp\ops_test.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt tests\ml\ops_test.zeph "$tmp\ops_test.exe" 2>&1 | Out-Null
$opsBuilt = Test-Path "$tmp\ops_test.exe"
$opsOut = if ($opsBuilt) { (cmd /c "`"$tmp\ops_test.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
Check "ml-ops" ($opsBuilt -and $opsOut -eq "ops: 107 checks passed") "got: $opsOut"

# ---- phase forward port: acceptance A13, and A10 at the gate level ----
# phase_test.zeph runs its own rejection cases by relaunching itself, because
# a panic cannot be caught in-process; no separate entries are needed here.
$phaseSuites = [ordered]@{
    "ml-phase"       = @("tests\ml\phase_test.zeph", "phase: 205 checks passed")
    "ml-phase-gates" = @("tests\ml\phase_gates_test.zeph", "phase gates: 1981 checks passed")
}
foreach ($nm in $phaseSuites.Keys) {
    $src = $phaseSuites[$nm][0]
    $want = $phaseSuites[$nm][1]
    $exe = Join-Path $tmp "$nm.exe"
    Remove-Item $exe -ErrorAction SilentlyContinue
    & .\zc.exe --rt $src $exe 2>&1 | Out-Null
    $built = Test-Path $exe
    $out = if ($built) { (cmd /c "`"$exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
    Check $nm ($built -and $out -eq $want) "got: $out"
}

# ---- phase parity against the float64 numpy reference (A13) ----
# Skipped rather than failed when numpy is absent: it is a reference-side
# dependency, and its absence is not a defect in the compiler or the port.
$hasNumpy = $false
try {
    & python -c "import numpy" 2>&1 | Out-Null
    $hasNumpy = ($LASTEXITCODE -eq 0)
} catch { $hasNumpy = $false }
if (-not $hasNumpy) {
    Write-Host "SKIP ml-phase-parity -- numpy not available"
} else {
    $dumpExe = Join-Path $tmp "phase_dump.exe"
    $dumpTxt = Join-Path $tmp "phase_dump.txt"
    Remove-Item $dumpExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tools\ml_reference\phase_dump.zeph $dumpExe 2>&1 | Out-Null
    if (-not (Test-Path $dumpExe)) {
        Check "ml-phase-parity" $false "phase_dump.zeph did not compile"
    } else {
        cmd /c "`"$dumpExe`" > `"$dumpTxt`" 2>&1" | Out-Null
        $parity = (& python tools\ml_reference\check_phase.py $dumpTxt | Out-String).Trim()
        $ok = ($LASTEXITCODE -eq 0) -and ($parity -match "148/148 quantities passed")
        Check "ml-phase-parity" $ok "got tail: $($parity -split "`n" | Select-Object -Last 1)"
    }
}

$opNeg = [ordered]@{
    "dtype-mix"  = 'let x = t_add(t_zeros(DType.F64, [2]), t_zeros(DType.F32, [2]))'
    "bcast-bad"  = 'let x = t_add(t_zeros(DType.F64, [2, 3]), t_zeros(DType.F64, [4, 3]))'
    "mm-inner"   = 'let x = t_matmul(t_zeros(DType.F64, [2, 3]), t_zeros(DType.F64, [4, 2]))'
    "mm-rank"    = 'let x = t_matmul(t_zeros(DType.F64, [2, 3, 1]), t_zeros(DType.F64, [3, 2]))'
    "ro-write"   = "let r = t_zeros(DType.F64, [1, 3])`nlet e = t_expand(r, [4, 3])`nt_set(e, [0, 0], 1.0)"
    "cast-down"  = 'let x = t_cast(t_zeros(DType.C64, [2]), DType.F64)'
    "abs2-real"  = 'let x = t_abs2(t_zeros(DType.F64, [2]))'
    "conj-real"  = 'let x = t_conj(t_zeros(DType.F64, [2]))'
    "sum-cplx"   = 'let x = t_sum_all(t_zeros(DType.C64, [2]))'
    "mean-empty" = 'let x = t_mean_all(t_zeros(DType.F64, [0]))'
    "expi-cplx"  = 'let x = t_expi(t_zeros(DType.C64, [2]), DType.C64)'
    "expand-bad" = 'let x = t_expand(t_zeros(DType.F64, [3]), [4])'
    "int-arith"  = 'let x = t_add(t_zeros(DType.I64, [2]), t_zeros(DType.I64, [2]))'
    "sel-dim"     = 'let x = t_index_select(t_zeros(DType.F64, [2, 2]), 5, [0])'
    "sel-range"   = 'let x = t_index_select(t_zeros(DType.F64, [2, 2]), 0, [2])'
    "sel-neg"     = 'let x = t_index_select(t_zeros(DType.F64, [2, 2]), 0, [0 - 1])'
    "copy-dup"    = 't_index_copy(t_zeros(DType.F64, [3]), 0, [1, 1], t_zeros(DType.F64, [2]))'
    "copy-shape"  = 't_index_copy(t_zeros(DType.F64, [3, 2]), 0, [0], t_zeros(DType.F64, [1, 5]))'
    "copy-count"  = 't_index_copy(t_zeros(DType.F64, [3]), 0, [0, 1], t_zeros(DType.F64, [3]))'
    "copy-ro"     = "let r = t_zeros(DType.F64, [1, 3])`nlet e = t_expand(r, [4, 3])`nt_index_copy(e, 0, [0], t_zeros(DType.F64, [1, 3]))"
    "cat-dim"     = 'let x = t_concat(t_zeros(DType.F64, [2, 2]), t_zeros(DType.F64, [2, 2]), 9)'
    "cat-shape"   = 'let x = t_concat(t_zeros(DType.F64, [2, 2]), t_zeros(DType.F64, [3, 2]), 1)'
    "cat-dtype"   = 'let x = t_concat(t_zeros(DType.F64, [2]), t_zeros(DType.F32, [2]), 0)'
    "map-cplx"    = 'let x = t_tanh(t_zeros(DType.C64, [2]))'
    "map-int"     = 'let x = t_tanh(t_zeros(DType.I64, [2]))'
    "roll-dim"    = 'let x = t_roll(t_zeros(DType.F64, [2]), 3, 1)'
}
foreach ($nm in $opNeg.Keys) {
    $src = "import `"ml/ops.zeph`"`n" + $opNeg[$nm]
    $f = Join-Path $tmp "opneg_$nm.zeph"
    $x = Join-Path $tmp "opneg_$nm.exe"
    Set-Content -Path $f -Value $src -Encoding ascii
    Remove-Item $x -ErrorAction SilentlyContinue
    & .\zc.exe --rt $f $x 2>&1 | Out-Null
    if (-not (Test-Path $x)) { Check "ops-reject:$nm" $false "did not compile"; continue }
    $o = (cmd /c "`"$x`" 2>&1" | Out-String).Trim()
    Check "ops-reject:$nm" ($LASTEXITCODE -ne 0 -and $o -match "panic:") "expected panic, got($LASTEXITCODE): $o"
}

# ---- modules: import splices declarations, once, resolved relative to the importer ----
$moddir = Join-Path $tmp "mod"
New-Item -ItemType Directory -Force "$moddir\sub" | Out-Null
Set-Content "$moddir\sub\mathx.zeph" "fn square(n: int) -> int { return n * n }" -Encoding ascii
Set-Content "$moddir\util.zeph" @'
import "sub/mathx.zeph"
enum Level { Low, High }
fn greet(who: str) -> str { return "hello, {who}" }
let UTIL_VERSION = 2
'@ -Encoding ascii
Set-Content "$moddir\a.zeph" "import `"b.zeph`"`nfn fa() -> int { return 1 }" -Encoding ascii
Set-Content "$moddir\b.zeph" "import `"a.zeph`"`nfn fb() -> int { return 2 }" -Encoding ascii
Set-Content "$moddir\main.zeph" @'
import "util.zeph"
import "util.zeph"
import "a.zeph"
print(greet("world"))
print(square(7))
print(UTIL_VERSION)
print(Level.High)
print(fa() + fb())
'@ -Encoding ascii
Remove-Item "$moddir\main.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$moddir\main.zeph" "$moddir\main.exe" 2>&1 | Out-Null
$modBuilt = Test-Path "$moddir\main.exe"
$modOut = if ($modBuilt) { (cmd /c "`"$moddir\main.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$modWant = @("hello, world","49","2","High","3") -join "`n"
Check "modules-import" ($modBuilt -and $modOut -eq $modWant) "got: $modOut"

# ---- OOP: impl methods, associated functions, interface dynamic dispatch ----
$oopdir = Join-Path $tmp "oop"
New-Item -ItemType Directory -Force $oopdir | Out-Null
Set-Content "$oopdir\p.zeph" @'
struct Counter { n: int }
impl Counter {
    fn make(start: int) -> Counter { return Counter{n: start} }
    fn bump(self, by: int) -> Counter { return Counter.make(self.n + by) }
    fn get(self) -> int { return self.n }
}
interface Animal {
    fn sound(self) -> str
    fn legs(self) -> int
}
struct Dog { name: str }
impl Dog { fn sound(self) -> str { return "woof" }  fn legs(self) -> int { return 4 } }
struct Bird { }
impl Bird { fn sound(self) -> str { return "tweet" }  fn legs(self) -> int { return 2 } }
fn total_legs(xs: [Animal]) -> int {
    var t = 0
    for a in xs { t = t + a.legs() }
    return t
}
let c = Counter.make(10).bump(5).bump(100)
print(c.get())
var zoo: [Animal] = []
zoo.push(Dog{name: "Rex"})
zoo.push(Bird{})
for a in zoo { print(a.sound()) }
print(total_legs(zoo))
'@ -Encoding ascii
Remove-Item "$oopdir\p.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$oopdir\p.zeph" "$oopdir\p.exe" 2>&1 | Out-Null
$oopBuilt = Test-Path "$oopdir\p.exe"
$oopOut = if ($oopBuilt) { (cmd /c "`"$oopdir\p.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$oopWant = @("115","woof","tweet","6") -join "`n"
Check "oop" ($oopBuilt -and $oopOut -eq $oopWant) "got: $oopOut"

# ---- multi-statement closure passed as an argument (newlines inside parens) ----
$cldir = Join-Path $tmp "clos"
New-Item -ItemType Directory -Force $cldir | Out-Null
Set-Content "$cldir\c.zeph" @'
fn twice(f: fn(int)) {
    f(1)
    f(2)
}
var log: [int] = []
twice(fn(n: int) {
    let a = n * 10
    let b = a + n
    log.push(b)
})
print(log)
var xs = [1, 2,
          3]
print(xs.len())
'@ -Encoding ascii
Remove-Item "$cldir\c.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$cldir\c.zeph" "$cldir\c.exe" 2>&1 | Out-Null
$clBuilt = Test-Path "$cldir\c.exe"
$clOut = if ($clBuilt) { (cmd /c "`"$cldir\c.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$clWant = @("[11, 22]","3") -join "`n"
Check "closure-arg-newlines" ($clBuilt -and $clOut -eq $clWant) "got: $clOut"

# ---- float codegen + literal parsing regressions ----
$fldir = Join-Path $tmp "flt"
New-Item -ItemType Directory -Force $fldir | Out-Null
Set-Content "$fldir\f.zeph" @'
// for-in over a [float]: the element var may be xmm-promoted, and the loop
// must publish it to that register or every iteration reads 0
let xs = [1.0, 2.5, 0.1]
var sum = 0.0
for v in xs { sum = sum + v }
print(sum)
for v in xs { print(v) }
// leading zeros must not consume the mantissa budget
print(bits(0.00000000000000001))
print(bits(0.0001))
'@ -Encoding ascii
Remove-Item "$fldir\f.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$fldir\f.zeph" "$fldir\f.exe" 2>&1 | Out-Null
$flBuilt = Test-Path "$fldir\f.exe"
$flOut = if ($flBuilt) { (cmd /c "`"$fldir\f.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$flWant = @("3.6","1","2.5","0.1","4352464011485697175","4547007122018943789") -join "`n"
Check "float-forin-and-literals" ($flBuilt -and $flOut -eq $flWant) "got: $flOut"

# ---- threads: allocation and GC across several stacks ----
# Run more than once: a collector that misses another thread's roots fails
# intermittently, not deterministically.
$thdir = Join-Path $tmp "thr"
New-Item -ItemType Directory -Force $thdir | Out-Null
Set-Content "$thdir\t.zeph" @'
import "std/thread.zeph"
let N = 6
var res = win("VirtualAlloc", 0, N * 8, 12288, 4)
fn work(id: int) {
    var acc = 0
    for r in 0..800 {
        var keep: [int] = []
        for k in 0..30 {
            var tmp: [int] = []
            tmp.push(id)
            tmp.push(k)
            acc = acc + tmp[0] + tmp[1]
            if k % 8 == 0 { keep.push(acc) }
        }
        acc = acc + keep.len()
    }
    store64(res + id * 8, acc)
}
fn want(id: int) -> int {
    var acc = 0
    for r in 0..800 {
        var n = 0
        for k in 0..30 {
            acc = acc + id + k
            if k % 8 == 0 { n += 1 }
        }
        acc = acc + n
    }
    return acc
}
var ts: [Thread] = []
for i in 0..N { ts.push(thread_spawn(work, i)) }
for t in ts { t.join() }
var bad = 0
for i in 0..N {
    if load64(res + i * 8) != want(i) { bad += 1 }
}
print(bad)
'@ -Encoding ascii
Remove-Item "$thdir\t.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$thdir\t.zeph" "$thdir\t.exe" 2>&1 | Out-Null
$thBuilt = Test-Path "$thdir\t.exe"
$thOk = $thBuilt
if ($thBuilt) {
    foreach ($i in 1..4) {
        $o = (cmd /c "`"$thdir\t.exe`" 2>&1" | Out-String).Trim() -replace "`r", ""
        if ($o -ne "0") { $thOk = $false; $thOut = $o }
    }
}
Check "threads-gc" $thOk "got: $thOut"

# ---- concurrent string interpolation (the builder is per-thread) ----
Set-Content "$thdir\s.zeph" @'
import "std/thread.zeph"
let N = 6
var bad = win("VirtualAlloc", 0, N * 8, 12288, 4)
fn work(id: int) {
    var wrong = 0
    for r in 0..1500 {
        let s = "w{id}:{r}"
        var parts: [str] = []
        parts.push("w")
        parts.push(id as str)
        parts.push(":")
        parts.push(r as str)
        if s != parts.join() { wrong += 1 }
    }
    store64(bad + id * 8, wrong)
}
var ts: [Thread] = []
for i in 0..N { ts.push(thread_spawn(work, i)) }
for t in ts { t.join() }
var total = 0
for i in 0..N { total = total + load64(bad + i * 8) }
print(total)
'@ -Encoding ascii
Remove-Item "$thdir\s.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$thdir\s.zeph" "$thdir\s.exe" 2>&1 | Out-Null
$siBuilt = Test-Path "$thdir\s.exe"
$siOk = $siBuilt
if ($siBuilt) {
    foreach ($i in 1..3) {
        $o = (cmd /c "`"$thdir\s.exe`" 2>&1" | Out-String).Trim() -replace "`r", ""
        if ($o -ne "0") { $siOk = $false; $siOut = $o }
    }
}
Check "threads-interpolation" $siOk "got: $siOut"

# ---- regression: a division nested inside an expression that holds a temp ----
# The reciprocal fast path used a hardcoded r10 -- one of the expression temp
# registers -- so a promoted division silently destroyed a parked operand.
$rgdir = Join-Path $tmp "regress"
New-Item -ItemType Directory -Force $rgdir | Out-Null
Set-Content -Path "$rgdir\d.zeph" -Encoding ascii -Value @'
fn g(n: int, d: int) -> int {
    var s = 0
    var i = 0
    while i < n {
        s += (i + 2) + ((i / d) + ((i % d) + (i * 3)))
        i += 1
    }
    return s
}
fn h(n: int, d: int) -> int {
    var s = 0
    var i = 0
    while i < n {
        s += ((i + 1) * ((i + 2) + ((i / d) + ((i % d) + (i * 3))))) % 1000003
        i += 1
    }
    return s
}
print(g(1000, 13))
print(h(1000, 13))
'@
Remove-Item "$rgdir\d.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$rgdir\d.zeph" "$rgdir\d.exe" 2>&1 | Out-Null
$dOut = if (Test-Path "$rgdir\d.exe") { (cmd /c "`"$rgdir\d.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$dWant = @("2043956", "402750512") -join "`n"
Check "div-temp-clobber" ($dOut -eq $dWant) "got: $dOut"

# ---- regression: floats whose integer part exceeds i64 ----
# `y as int` saturates past 2^63, which used to make the digit loop emit
# negative digits (1e20 printed as "0.-).0-*(+,))+(0(").
Set-Content -Path "$rgdir\f.zeph" -Encoding ascii -Value @'
var big = 1.0
var i = 0
while i < 20 {
    big = big * 10.0
    i += 1
}
print(big)
print(0.0 - big)
print(9223372036854775808.0)
print(1.5)
'@
Remove-Item "$rgdir\f.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt "$rgdir\f.zeph" "$rgdir\f.exe" 2>&1 | Out-Null
$fOut = if (Test-Path "$rgdir\f.exe") { (cmd /c "`"$rgdir\f.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
$fWant = @("100000000000000000000", "-100000000000000000000", "9223372036854775808", "1.5") -join "`n"
Check "float-big-format" ($fOut -eq $fWant) "got: $fOut"

Write-Host ""
Write-Host "$pass passed, $fail failed"
if ($fail) { exit 1 }
