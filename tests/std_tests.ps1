# Standard-library regression tests. Run from any directory.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
$pass = 0
$fail = 0
$tempRoot = Join-Path $env:TEMP ('zephyr std ' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot | Out-Null
function Check($name, $ok, $detail) {
    if ($ok) { $script:pass++; Write-Host "PASS $name" }
    else { $script:fail++; Write-Host "FAIL $name -- $detail" -ForegroundColor Red }
}
function RunSrc($name, $source, $stdin = '') {
    $sourcePath = Join-Path $tempRoot "$name.zeph"
    $exePath = Join-Path $tempRoot "$name.exe"
    Set-Content -LiteralPath $sourcePath -Value $source -Encoding ascii
    $compilerOutput = & .\zc.exe --rt $sourcePath $exePath 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $exePath)) {
        return @{code = -1; out = $compilerOutput.Trim(); err = 'compile failed'}
    }
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = $exePath
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardInput = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.EnvironmentVariables['ZEPHYR_STD_VALUE'] = 'library value'
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $start
    [void]$process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.StandardInput.Write($stdin)
    $process.StandardInput.Close()
    if (-not $process.WaitForExit(30000)) {
        $process.Kill()
        return @{code = -2; out = 'timed out'; err = ''}
    }
    return @{code = $process.ExitCode; out = $stdoutTask.Result.Replace([string][char]13, '').TrimEnd([char]10); err = $stderrTask.Result.Replace([string][char]13, '').TrimEnd([char]10)}
}
function TestSrc($name, $source, $expected = 'ok', $stdin = '') {
    $result = RunSrc $name $source $stdin
    Check $name ($result.code -eq 0 -and $result.out -ceq $expected) "exit=$($result.code), stdout=$($result.out), stderr=$($result.err)"
}
function TestPanic($name, $source, $message) {
    $result = RunSrc $name $source
    Check $name ($result.code -ne 0 -and $result.code -ne -1 -and ($result.out + $result.err).Contains($message)) "exit=$($result.code), stdout=$($result.out), stderr=$($result.err)"
}
TestSrc 'string_bytes' @'
import "std/string.zeph"
assert(reverse_str("abc") == "cba" and reverse_str("") == "", "reverse")
assert(ord("Az") == 65, "ord")
assert(trim_left(" \t\n" + chr(13) + " a ") == "a ", "trim left")
assert(trim_right(" a \t\n" + chr(13)) == " a", "trim right")
assert(trim_left("") == "" and trim_right(" \t\n") == "", "trim empty")
assert(join_with(["a", "", "b"], ":") == "a::b", "join")
let emptyParts: [str] = []
assert(join_with(emptyParts, ":") == "", "join empty")
assert(pad_left("ab", 5, "0") == "000ab", "pad left")
assert(pad_right("ab", 5, ".") == "ab...", "pad right")
assert(pad_left("abc", 1, "0") == "abc" and pad_right("", 0, ".") == "", "pad boundaries")
assert(is_digit(48) and is_digit(57) and not is_digit(47), "digit")
assert(is_alpha(65) and is_alpha(122) and not is_alpha(91), "alpha")
assert(is_alnum(57) and is_alnum(97) and not is_alnum(32), "alnum")
assert(is_space(32) and is_space(9) and is_space(10) and is_space(13) and not is_space(65), "space")
assert(is_upper(65) and is_upper(90) and not is_upper(97), "upper")
assert(is_lower(97) and is_lower(122) and not is_lower(65), "lower")
let letters = chars("ab" + chr(255))
assert(letters.len() == 3 and letters[2].byte(0) == 255 and chars("").len() == 0, "chars")
let rows = lines("a" + chr(13) + "\n\nb\n")
assert(rows.len() == 4 and rows[0] == "a" and rows[1] == "" and rows[2] == "b" and rows[3] == "", "lines")
assert(lines("").len() == 1, "empty lines")
print("ok")
'@
TestSrc 'string_format' @'
import "std/string.zeph"
assert(fmt_fixed(3.14159, 2) == "3.14", "pi")
assert(fmt_fixed(-1.25, 1) == "-1.3", "negative tie")
assert(fmt_fixed(2.5, 0) == "3" and fmt_fixed(-2.5, 0) == "-3", "integer tie")
assert(fmt_fixed(9.999, 2) == "10.00", "carry")
assert(fmt_fixed(0.0, 3) == "0.000", "zero")
assert(fmt_fixed(frombits(1 << 63), 2) == "-0.00", "negative zero")
assert(fmt_fixed(100000000000000000000.0, 2) == "100000000000000000000.00", "large fixed")
assert(fmt_fixed(1.125, 2) == "1.13", "exact tie")
assert(fmt_fixed(2.675, 2) == "2.67", "binary decimal boundary")
assert(fmt_fixed(1.0, 20) == "1.00000000000000000000", "many decimals")
assert(to_hex(0) == "0" and to_hex(255) == "ff", "hex")
assert(to_hex(-1) == "ffffffffffffffff" and to_hex(1 << 63) == "8000000000000000", "negative hex")
assert(to_binary(0) == "0" and to_binary(10) == "1010", "binary")
assert(to_binary(-1) == "1111111111111111111111111111111111111111111111111111111111111111", "negative binary")
print("ok")
'@
TestSrc 'string_parse' @'
import "std/string.zeph"
assert(parse_int(" \t+42\n").get() == 42 and parse_int("-42").get() == -42, "sign whitespace")
assert(parse_int("9223372036854775807").get() == 9223372036854775807, "max int")
assert(parse_int("-9223372036854775808").get() == (1 << 63), "min int")
for invalid in ["", " ", "+", "-", "1x", "1.0", "1 2", "9223372036854775808", "-9223372036854775809"] {
    assert(not parse_int(invalid).has(), "invalid int " + invalid)
}
assert(parse_float(" +1.25e2 ").get() == 125.0, "float exponent")
assert(parse_float("-.5").get() == -0.5 and parse_float("1.").get() == 1.0, "fraction forms")
assert(parse_float("2E-2").get() == 0.02, "negative exponent")
assert(parse_float("1e-9999").get() == 0.0, "underflow")
assert(parse_float("1e3").get() == 1000.0 and parse_float("+.5").get() == 0.5, "exponent and plus fraction")
assert(bits(parse_float("-1e-9999").get()) == (1 << 63), "signed underflow")
assert(parse_float("1000000000000000000000000000000e-30").get() == 1.0, "compensated exponent")
assert(bits(parse_float("1.7976931348623157e308").get()) == 9218868437227405311, "maximum finite float")
assert(bits(parse_float("4.9406564584124654e-324").get()) == 1, "minimum subnormal")
assert(not parse_float("1.7976931348623159e308").has(), "finite overflow")
assert(parse_float("1.00000000000000011102230246251565404236316680908203125").get() == 1.0, "ties to even")
for invalid in ["", " ", "+", ".", "1e", "1e+", "1.2.3", "NaN", "inf", "1e9999", "1 2"] {
    assert(not parse_float(invalid).has(), "invalid float " + invalid)
}
print("ok")
'@
TestPanic 'ord_empty' 'import "std/string.zeph"
ord("")' 'ord'
TestPanic 'pad_invalid' 'import "std/string.zeph"
pad_left("x", 3, "ab")' 'pad'
TestPanic 'format_negative_decimals' 'import "std/string.zeph"
fmt_fixed(1.0, -1)' 'fmt_fixed'
TestSrc 'math_rounding' @'
import "std/math.zeph"
assert(floor(-1.2) == -2.0 and floor(1.2) == 1.0, "floor")
assert(ceil(-1.2) == -1.0 and ceil(1.2) == 2.0, "ceil")
assert(trunc(-1.9) == -1.0 and trunc(1.9) == 1.0, "trunc")
assert(round(-1.5) == -2.0 and round(1.5) == 2.0 and round(1.49) == 1.0, "round")
let negativeZero = frombits(1 << 63)
assert(bits(trunc(negativeZero)) == bits(negativeZero) and bits(ceil(-0.25)) == bits(negativeZero), "signed zero")
for value in [4503599627370496.0, -4503599627370496.0, 9007199254740992.0, -9007199254740992.0] {
    assert(floor(value) == value and ceil(value) == value and trunc(value) == value and round(value) == value, "large integral")
}
assert(round(frombits(bits(0.5) - 1)) == 0.0, "below half")
assert(floor(INF) == INF and ceil(0.0 - INF) == 0.0 - INF and is_nan(round(NAN)), "nonfinite rounding")
assert(clamp(-2.0, 0.0, 1.0) == 0.0 and clamp(2.0, 0.0, 1.0) == 1.0 and clamp(0.5, 0.0, 1.0) == 0.5, "clamp")
assert(clamp_int(-2, 0, 1) == 0 and clamp_int(2, 0, 1) == 1 and clamp_int(0, 0, 1) == 0, "clamp int")
assert(is_inf(INF) and is_inf(0.0 - INF) and not is_inf(NAN) and not is_inf(1.0), "infinity")
print("ok")
'@
TestSrc 'math_values' @'
import "std/math.zeph"
fn close_value(actual: float, expected: float) {
    assert(fabs(actual - expected) <= fabs(expected) * 0.000000000001, "relative error")
}
close_value(powf(2.0, 0.5), 1.4142135623730951)
assert(powf(-2.0, 3.0) == -8.0 and powf(-2.0, -3.0) == -0.125 and powf(0.0, 0.0) == 1.0, "integer powers")
assert(is_nan(powf(-2.0, 0.5)), "negative fractional power")
assert(fmod(-5.5, 2.0) == -1.5 and fmod(5.5, -2.0) == 1.5, "fmod sign")
assert(bits(fmod(-4.0, 2.0)) == (1 << 63), "fmod signed zero")
assert(is_nan(fmod(1.0, 0.0)) and fmod(3.0, INF) == 3.0, "fmod special")
assert(fmod(frombits(9218868437227405311), 2.0) == 0.0, "fmod maximum finite")
assert(fmod(frombits(1123 << 52), 3.0) == 1.0, "fmod large quotient")
close_value(atan2(1.0, 1.0), PI / 4.0)
close_value(atan2(1.0, -1.0), 3.0 * PI / 4.0)
close_value(atan2(-1.0, -1.0), -3.0 * PI / 4.0)
close_value(atan2(-1.0, 1.0), 0.0 - PI / 4.0)
assert(atan2(0.0, -1.0) == PI and atan2(frombits(1 << 63), -1.0) == 0.0 - PI, "atan2 zero")
assert(atan2(1.0, 0.0) == HALF_PI and atan2(-1.0, 0.0) == 0.0 - HALF_PI, "atan2 axis")
assert(bits(atan2(-1.0, INF)) == (1 << 63), "atan2 signed zero at infinity")
close_value(hypot(3.0, 4.0), 5.0)
close_value(cbrt(-27.0), -3.0)
close_value(cbrt(2.0), 1.2599210498948732)
close_value(log10(1000.0), 3.0)
close_value(log2(32.0), 5.0)
close_value(exp(1.0), E)
close_value(ln(E), 1.0)
close_value(exp(-10.0), 0.000045399929762484854)
close_value(ln(0.125), -2.0794415416798357)
assert(hypot(0.0, 0.0) == 0.0 and cbrt(0.0) == 0.0, "zeros")
assert(is_inf(hypot(INF, NAN)) and is_nan(log10(-1.0)), "nonfinite")
print("ok")
'@
TestSrc 'random' @'
import "std/random.zeph"
import "std/list.zeph"
let firstRng = rng_new(123)
let secondRng = rng_new(123)
let goldenRng = rng_new(123)
for expected in [6263409555191053425, 2639717259894160666, 7864733624088036230, -6626401459311169198, 2310929218875517963] {
    assert(goldenRng.next_int() == expected, "xorshift64 star golden sequence")
}
for i in 0..1000 { assert(firstRng.next_int() == secondRng.next_int(), "same seed") }
let zeroRng = rng_new(0)
assert(zeroRng.next_int() != 0, "nonzero zero seed")
let generator = rng_new(9876)
var positiveSeen = false
var negativeSeen = false
for i in 0..10000 {
    let value = generator.next_int()
    if value > 0 { positiveSeen = true }
    if value < 0 { negativeSeen = true }
    let bounded = generator.int_between(-7, 13)
    assert(bounded >= -7 and bounded < 13, "bounded int")
    let fraction = generator.next_float()
    assert(fraction >= 0.0 and fraction < 1.0, "float range")
}
assert(positiveSeen and negativeSeen, "full signed range")
assert(generator.int_between(7, 8) == 7, "singleton")
assert(generator.int_between(1 << 63, (1 << 63) + 1) == (1 << 63), "minimum singleton")
assert(generator.int_between(9223372036854775806, 9223372036854775807) == 9223372036854775806, "maximum singleton")
var lowerSeen = false
var upperSeen = false
for i in 0..1000 {
    let endpoint = generator.int_between(-1, 1)
    assert(endpoint == -1 or endpoint == 0, "crossing zero bounds")
    if endpoint == -1 { lowerSeen = true }
    if endpoint == 0 { upperSeen = true }
}
assert(lowerSeen and upperSeen, "both inclusive endpoints reached")
for i in 0..100 {
    let wide = generator.int_between(1 << 63, 9223372036854775807)
    assert(wide < 9223372036854775807, "wide range")
}
assert(not generator.chance(0.0) and generator.chance(1.0), "chance endpoints")
var values: [int] = []
for i in 0..100 { values.push(i) }
generator.shuffle(values)
assert(values.sum() == 4950, "shuffle sum")
for i in 0..100 { assert(values.count(i) == 1, "shuffle permutation") }
let emptyValues: [int] = []
generator.shuffle(emptyValues)
let singleton = [1]
generator.shuffle(singleton)
assert(singleton[0] == 1, "singleton shuffle")
print("ok")
'@
TestPanic 'random_empty_range' 'import "std/random.zeph"
int_between(rng_new(1), 2, 2)' 'int_between'
TestSrc 'list_reductions' @'
import "std/list.zeph"
assert(sum([1, -2, 4]) == 3 and sum([1.5, 2.5]) == 4.0, "sum")
assert(min_of([2, -1, 3]) == -1 and max_of([2, -1, 3]) == 3, "extrema")
assert(min_of(["b", "a"]) == "a" and max_of([1.5, 2.5]) == 2.5, "generic extrema")
print("ok")
'@
foreach ($functionName in @('sum', 'min_of', 'max_of')) {
    TestPanic "list_empty_$functionName" ('import "std/list.zeph"' + [Environment]::NewLine + 'let values: [int] = []' + [Environment]::NewLine + "$functionName(values)") 'empty list'
}
TestSrc 'list_stable_sort' @'
import "std/list.zeph"
struct SortItem { key: int, original: int }
var comparisons = 0
fn compare_item(left: SortItem, right: SortItem) -> int {
    comparisons += 1
    return left.key - right.key
}
var items: [SortItem] = []
for i in 0..4096 { items.push(SortItem{key: (4096 - i) % 17, original: i}) }
sort_by(items, compare_item)
for i in 1..items.len() {
    assert(items[i - 1].key <= items[i].key, "sorted")
    if items[i - 1].key == items[i].key { assert(items[i - 1].original < items[i].original, "stable") }
}
assert(comparisons <= 49152, "n log n comparisons")
let emptyItems: [SortItem] = []
sort_by(emptyItems, compare_item)
print("ok")
'@
TestSrc 'io_read_line' @'
import "std/io.zeph"
assert(read_line().get() == "first", "first line")
assert(read_line().get() == "", "empty line")
assert(read_line().get() == "last", "unterminated line")
assert(not read_line().has(), "eof")
print("ok")
'@ 'ok' ("first" + [char]13 + [char]10 + [char]10 + "last")
TestSrc 'io_empty_stdin' 'import "std/io.zeph"
assert(not read_line().has(), "empty eof")
print("ok")'
$result = RunSrc 'io_stderr' 'import "std/io.zeph"
eprint("error line")'
Check 'io_stderr' ($result.code -eq 0 -and $result.out -eq '' -and $result.err -eq 'error line') "exit=$($result.code), stdout=$($result.out), stderr=$($result.err)"
$result = RunSrc 'io_exit' 'import "std/io.zeph"
exit(7)
print("unreachable")'
Check 'io_exit' ($result.code -eq 7 -and $result.out -eq '') "exit=$($result.code), stdout=$($result.out)"
$fileDirectory = Join-Path $tempRoot 'files with spaces'
New-Item -ItemType Directory -Path $fileDirectory | Out-Null
$fileDirectoryZeph = $fileDirectory.Replace('\', '/')
$fileSource = @'
import "std/io.zeph"
import "std/list.zeph"
let directory = "DIRECTORY"
let path = directory + "/append file.txt"
assert(not file_exists(path), "initial absence")
append_file(path, "first")
append_file(path, " second")
assert(file_exists(path) and read_file(path) == "first second", "append contents")
let names = list_dir(directory)
assert(names.len() == 1 and names.contains("append file.txt"), "directory names")
assert(not names.contains(".") and not names.contains(".."), "dot entries")
assert(delete_file(path) and not file_exists(path), "delete")
assert(not delete_file(path), "delete absent")
assert(list_dir(directory).len() == 0, "empty directory")
print("ok")
'@
TestSrc 'io_files' $fileSource.Replace('DIRECTORY', $fileDirectoryZeph)
TestPanic 'io_missing_directory' ('import "std/io.zeph"' + [Environment]::NewLine + 'list_dir("' + $fileDirectoryZeph + '/missing")') 'list_dir'
TestSrc 'io_environment_time_run' @'
import "std/io.zeph"
assert(env("ZEPHYR_STD_VALUE").get() == "library value", "environment")
assert(not env("ZEPHYR_STD_UNDEFINED_723817").has(), "missing environment")
let emptyName = cbytes("ZEPHYR_STD_EMPTY_723817")
let emptyValue = cbytes("")
assert(win("SetEnvironmentVariableA", emptyName.addr(), emptyValue.addr()) != 0, "set empty env")
assert(env("ZEPHYR_STD_EMPTY_723817").has() and env("ZEPHYR_STD_EMPTY_723817").get() == "", "empty environment")
let startMs = now_ms()
let startNs = now_ns()
sleep_ms(20)
assert(now_ms() >= startMs + 10 and now_ns() > startNs, "monotonic clocks")
assert(run("cmd.exe /c exit 7") == 7, "child exit")
print("ok")
'@
TestSrc 'all_imports' @'
import "std/string.zeph"
import "std/math.zeph"
import "std/random.zeph"
import "std/io.zeph"
import "std/list.zeph"
import "std/bytes.zeph"
import "std/thread.zeph"
print(fmt_fixed(sum([1.0, 2.0]), 1))
'@ '3.0'
$linuxSource = Join-Path $tempRoot 'linux_build.zeph'
$linuxOutput = Join-Path $tempRoot 'linux_build.elf'
Set-Content -LiteralPath $linuxSource -Encoding ascii -Value @'
import "std/io.zeph"
import "std/string.zeph"
import "std/math.zeph"
import "std/random.zeph"
import "std/list.zeph"
print(fmt_fixed(hypot(3.0, 4.0), 2))
print(sum([1, 2, 3]))
print(rng_new(42).next_int())
print(now_ms())
print(now_ns())
sleep_ms(0)
print(file_exists("."))
print(list_dir(".").len())
eprint("linux compile check")
if false {
    append_file("compile-only.tmp", "data")
    print(delete_file("compile-only.tmp"))
    print(read_line().has())
    print(env("PATH").has())
    print(run("unused"))
    exit(0)
}
'@
$linuxCompilerOutput = & .\zc.exe --linux --rt $linuxSource $linuxOutput 2>&1 | Out-String
$linuxCompileCode = $LASTEXITCODE
$elfHeader = $false
if (Test-Path -LiteralPath $linuxOutput) {
    $linuxBytes = [IO.File]::ReadAllBytes($linuxOutput)
    $elfHeader = $linuxBytes.Length -ge 4 -and $linuxBytes[0] -eq 127 -and $linuxBytes[1] -eq 69 -and $linuxBytes[2] -eq 76 -and $linuxBytes[3] -eq 70
}
Check 'linux_build (compile only)' ($linuxCompileCode -eq 0 -and $elfHeader) "exit=$linuxCompileCode, ELF=$elfHeader, compiler=$linuxCompilerOutput"
Write-Host "$pass passed, $fail failed"
if ($fail -ne 0) { Write-Host "Artifacts: $tempRoot"; exit 1 }
# The resolved deletion target must remain this run's unique temporary directory.
$resolvedTemp = [IO.Path]::GetFullPath($tempRoot)
$expectedParent = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
if (-not $resolvedTemp.StartsWith($expectedParent, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe temporary path' }
Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
exit 0
