# Standard-library regression tests. Run from any directory.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot)
# A redirected stdin is written with the console's input encoding, and a UTF-8
# console (code page 65001) makes .NET prepend a byte-order mark the programs
# under test would read as input.
try { [Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { }
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
assert(reverseString("abc") == "cba" and reverseString("") == "", "reverse")
assert(ord("Az") == 65, "ord")
assert(trimLeft(" \t\n" + chr(13) + " a ") == "a ", "trim left")
assert(trimRight(" a \t\n" + chr(13)) == " a", "trim right")
assert(trimLeft("") == "" and trimRight(" \t\n") == "", "trim empty")
assert(joinWith(["a", "", "b"], ":") == "a::b", "join")
let emptyParts: [str] = []
assert(joinWith(emptyParts, ":") == "", "join empty")
assert(padLeft("ab", 5, "0") == "000ab", "pad left")
assert(padRight("ab", 5, ".") == "ab...", "pad right")
assert(padLeft("abc", 1, "0") == "abc" and padRight("", 0, ".") == "", "pad boundaries")
assert(isDigit(48) and isDigit(57) and not isDigit(47), "digit")
assert(isAlpha(65) and isAlpha(122) and not isAlpha(91), "alpha")
assert(isAlphanumeric(57) and isAlphanumeric(97) and not isAlphanumeric(32), "alnum")
assert(isWhitespace(32) and isWhitespace(9) and isWhitespace(10) and isWhitespace(13) and not isWhitespace(65), "space")
assert(isUpper(65) and isUpper(90) and not isUpper(97), "upper")
assert(isLower(97) and isLower(122) and not isLower(65), "lower")
let letters = chars("ab" + chr(255))
assert(letters.len() == 3 and letters[2].byte(0) == 255 and chars("").len() == 0, "chars")
let rows = lines("a" + chr(13) + "\n\nb\n")
assert(rows.len() == 4 and rows[0] == "a" and rows[1] == "" and rows[2] == "b" and rows[3] == "", "lines")
assert(lines("").len() == 1, "empty lines")
print("ok")
'@
TestSrc 'string_format' @'
import "std/string.zeph"
assert(formatFixed(3.14159, 2) == "3.14", "pi")
assert(formatFixed(-1.25, 1) == "-1.3", "negative tie")
assert(formatFixed(2.5, 0) == "3" and formatFixed(-2.5, 0) == "-3", "integer tie")
assert(formatFixed(9.999, 2) == "10.00", "carry")
assert(formatFixed(0.0, 3) == "0.000", "zero")
assert(formatFixed(floatFromBits(1 << 63), 2) == "-0.00", "negative zero")
assert(formatFixed(100000000000000000000.0, 2) == "100000000000000000000.00", "large fixed")
assert(formatFixed(1.125, 2) == "1.13", "exact tie")
assert(formatFixed(2.675, 2) == "2.67", "binary decimal boundary")
assert(formatFixed(1.0, 20) == "1.00000000000000000000", "many decimals")
assert(toHex(0) == "0" and toHex(255) == "ff", "hex")
assert(toHex(-1) == "ffffffffffffffff" and toHex(1 << 63) == "8000000000000000", "negative hex")
assert(toBinary(0) == "0" and toBinary(10) == "1010", "binary")
assert(toBinary(-1) == "1111111111111111111111111111111111111111111111111111111111111111", "negative binary")
print("ok")
'@
TestSrc 'string_parse' @'
import "std/string.zeph"
assert(parseInt(" \t+42\n").get() == 42 and parseInt("-42").get() == -42, "sign whitespace")
assert(parseInt("9223372036854775807").get() == 9223372036854775807, "max int")
assert(parseInt("-9223372036854775808").get() == (1 << 63), "min int")
for invalid in ["", " ", "+", "-", "1x", "1.0", "1 2", "9223372036854775808", "-9223372036854775809"] {
    assert(not parseInt(invalid).has(), "invalid int " + invalid)
}
assert(parseFloat(" +1.25e2 ").get() == 125.0, "float exponent")
assert(parseFloat("-.5").get() == -0.5 and parseFloat("1.").get() == 1.0, "fraction forms")
assert(parseFloat("2E-2").get() == 0.02, "negative exponent")
assert(parseFloat("1e-9999").get() == 0.0, "underflow")
assert(parseFloat("1e3").get() == 1000.0 and parseFloat("+.5").get() == 0.5, "exponent and plus fraction")
assert(bits(parseFloat("-1e-9999").get()) == (1 << 63), "signed underflow")
assert(parseFloat("1000000000000000000000000000000e-30").get() == 1.0, "compensated exponent")
assert(bits(parseFloat("1.7976931348623157e308").get()) == 9218868437227405311, "maximum finite float")
assert(bits(parseFloat("4.9406564584124654e-324").get()) == 1, "minimum subnormal")
assert(not parseFloat("1.7976931348623159e308").has(), "finite overflow")
assert(parseFloat("1.00000000000000011102230246251565404236316680908203125").get() == 1.0, "ties to even")
for invalid in ["", " ", "+", ".", "1e", "1e+", "1.2.3", "NaN", "inf", "1e9999", "1 2"] {
    assert(not parseFloat(invalid).has(), "invalid float " + invalid)
}
print("ok")
'@
TestPanic 'ord_empty' 'import "std/string.zeph"
ord("")' 'ord'
TestPanic 'pad_invalid' 'import "std/string.zeph"
padLeft("x", 3, "ab")' 'pad'
TestPanic 'format_negative_decimals' 'import "std/string.zeph"
formatFixed(1.0, -1)' 'formatFixed'
TestSrc 'math_rounding' @'
import "std/math.zeph"
assert(floor(-1.2) == -2.0 and floor(1.2) == 1.0, "floor")
assert(ceil(-1.2) == -1.0 and ceil(1.2) == 2.0, "ceil")
assert(trunc(-1.9) == -1.0 and trunc(1.9) == 1.0, "trunc")
assert(round(-1.5) == -2.0 and round(1.5) == 2.0 and round(1.49) == 1.0, "round")
let negativeZero = floatFromBits(1 << 63)
assert(bits(trunc(negativeZero)) == bits(negativeZero) and bits(ceil(-0.25)) == bits(negativeZero), "signed zero")
for value in [4503599627370496.0, -4503599627370496.0, 9007199254740992.0, -9007199254740992.0] {
    assert(floor(value) == value and ceil(value) == value and trunc(value) == value and round(value) == value, "large integral")
}
assert(round(floatFromBits(bits(0.5) - 1)) == 0.0, "below half")
assert(floor(infinity) == infinity and ceil(0.0 - infinity) == 0.0 - infinity and isNan(round(nan)), "nonfinite rounding")
assert(clamp(-2.0, 0.0, 1.0) == 0.0 and clamp(2.0, 0.0, 1.0) == 1.0 and clamp(0.5, 0.0, 1.0) == 0.5, "clamp")
assert(clampInt(-2, 0, 1) == 0 and clampInt(2, 0, 1) == 1 and clampInt(0, 0, 1) == 0, "clamp int")
assert(isInfinite(infinity) and isInfinite(0.0 - infinity) and not isInfinite(nan) and not isInfinite(1.0), "infinity")
print("ok")
'@
TestSrc 'math_values' @'
import "std/math.zeph"
fn close_value(actual: float, expected: float) {
    assert(fabs(actual - expected) <= fabs(expected) * 0.000000000001, "relative error")
}
close_value(powf(2.0, 0.5), 1.4142135623730951)
assert(powf(-2.0, 3.0) == -8.0 and powf(-2.0, -3.0) == -0.125 and powf(0.0, 0.0) == 1.0, "integer powers")
assert(isNan(powf(-2.0, 0.5)), "negative fractional power")
assert(fmod(-5.5, 2.0) == -1.5 and fmod(5.5, -2.0) == 1.5, "fmod sign")
assert(bits(fmod(-4.0, 2.0)) == (1 << 63), "fmod signed zero")
assert(isNan(fmod(1.0, 0.0)) and fmod(3.0, infinity) == 3.0, "fmod special")
assert(fmod(floatFromBits(9218868437227405311), 2.0) == 0.0, "fmod maximum finite")
assert(fmod(floatFromBits(1123 << 52), 3.0) == 1.0, "fmod large quotient")
close_value(atan2(1.0, 1.0), pi / 4.0)
close_value(atan2(1.0, -1.0), 3.0 * pi / 4.0)
close_value(atan2(-1.0, -1.0), -3.0 * pi / 4.0)
close_value(atan2(-1.0, 1.0), 0.0 - pi / 4.0)
assert(atan2(0.0, -1.0) == pi and atan2(floatFromBits(1 << 63), -1.0) == 0.0 - pi, "atan2 zero")
assert(atan2(1.0, 0.0) == halfPi and atan2(-1.0, 0.0) == 0.0 - halfPi, "atan2 axis")
assert(bits(atan2(-1.0, infinity)) == (1 << 63), "atan2 signed zero at infinity")
close_value(hypot(3.0, 4.0), 5.0)
close_value(cbrt(-27.0), -3.0)
close_value(cbrt(2.0), 1.2599210498948732)
close_value(log10(1000.0), 3.0)
close_value(log2(32.0), 5.0)
close_value(exp(1.0), eulerNumber)
close_value(ln(eulerNumber), 1.0)
close_value(exp(-10.0), 0.000045399929762484854)
close_value(ln(0.125), -2.0794415416798357)
assert(hypot(0.0, 0.0) == 0.0 and cbrt(0.0) == 0.0, "zeros")
assert(isInfinite(hypot(infinity, nan)) and isNan(log10(-1.0)), "nonfinite")
print("ok")
'@
TestSrc 'random' @'
import "std/random.zeph"
import "std/list.zeph"
let firstRng = newRng(123)
let secondRng = newRng(123)
let goldenRng = newRng(123)
for expected in [6263409555191053425, 2639717259894160666, 7864733624088036230, -6626401459311169198, 2310929218875517963] {
    assert(goldenRng.nextInt() == expected, "xorshift64 star golden sequence")
}
for i in 0..1000 { assert(firstRng.nextInt() == secondRng.nextInt(), "same seed") }
let zeroRng = newRng(0)
assert(zeroRng.nextInt() != 0, "nonzero zero seed")
let generator = newRng(9876)
var positiveSeen = false
var negativeSeen = false
for i in 0..10000 {
    let value = generator.nextInt()
    if value > 0 { positiveSeen = true }
    if value < 0 { negativeSeen = true }
    let bounded = generator.intBetween(-7, 13)
    assert(bounded >= -7 and bounded < 13, "bounded int")
    let fraction = generator.nextFloat()
    assert(fraction >= 0.0 and fraction < 1.0, "float range")
}
assert(positiveSeen and negativeSeen, "full signed range")
assert(generator.intBetween(7, 8) == 7, "singleton")
assert(generator.intBetween(1 << 63, (1 << 63) + 1) == (1 << 63), "minimum singleton")
assert(generator.intBetween(9223372036854775806, 9223372036854775807) == 9223372036854775806, "maximum singleton")
var lowerSeen = false
var upperSeen = false
for i in 0..1000 {
    let endpoint = generator.intBetween(-1, 1)
    assert(endpoint == -1 or endpoint == 0, "crossing zero bounds")
    if endpoint == -1 { lowerSeen = true }
    if endpoint == 0 { upperSeen = true }
}
assert(lowerSeen and upperSeen, "both inclusive endpoints reached")
for i in 0..100 {
    let wide = generator.intBetween(1 << 63, 9223372036854775807)
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
intBetween(newRng(1), 2, 2)' 'intBetween'
TestSrc 'list_reductions' @'
import "std/list.zeph"
assert(sum([1, -2, 4]) == 3 and sum([1.5, 2.5]) == 4.0, "sum")
assert(minOf([2, -1, 3]) == -1 and maxOf([2, -1, 3]) == 3, "extrema")
assert(minOf(["b", "a"]) == "a" and maxOf([1.5, 2.5]) == 2.5, "generic extrema")
print("ok")
'@
foreach ($functionName in @('sum', 'minOf', 'maxOf')) {
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
sortBy(items, compare_item)
for i in 1..items.len() {
    assert(items[i - 1].key <= items[i].key, "sorted")
    if items[i - 1].key == items[i].key { assert(items[i - 1].original < items[i].original, "stable") }
}
assert(comparisons <= 49152, "n log n comparisons")
let emptyItems: [SortItem] = []
sortBy(emptyItems, compare_item)
print("ok")
'@
TestSrc 'io_read_line' @'
import "std/io.zeph"
assert(readLine().get() == "first", "first line")
assert(readLine().get() == "", "empty line")
assert(readLine().get() == "last", "unterminated line")
assert(not readLine().has(), "eof")
print("ok")
'@ 'ok' ("first" + [char]13 + [char]10 + [char]10 + "last")
TestSrc 'io_empty_stdin' 'import "std/io.zeph"
assert(not readLine().has(), "empty eof")
print("ok")'
$result = RunSrc 'io_stderr' 'import "std/io.zeph"
printError("error line")'
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
assert(not fileExists(path), "initial absence")
appendFile(path, "first")
appendFile(path, " second")
assert(fileExists(path) and readFile(path) == "first second", "append contents")
let names = listDirectory(directory)
assert(names.len() == 1 and names.contains("append file.txt"), "directory names")
assert(not names.contains(".") and not names.contains(".."), "dot entries")
assert(deleteFile(path) and not fileExists(path), "delete")
assert(not deleteFile(path), "delete absent")
assert(listDirectory(directory).len() == 0, "empty directory")
print("ok")
'@
TestSrc 'io_files' $fileSource.Replace('DIRECTORY', $fileDirectoryZeph)
TestPanic 'io_missing_directory' ('import "std/io.zeph"' + [Environment]::NewLine + 'listDirectory("' + $fileDirectoryZeph + '/missing")') 'listDirectory'
TestSrc 'io_environment_time_run' @'
import "std/io.zeph"
assert(environmentVariable("ZEPHYR_STD_VALUE").get() == "library value", "environment")
assert(not environmentVariable("ZEPHYR_STD_UNDEFINED_723817").has(), "missing environment")
let emptyName = cString("ZEPHYR_STD_EMPTY_723817")
let emptyValue = cString("")
assert(win("SetEnvironmentVariableA", emptyName.addr(), emptyValue.addr()) != 0, "set empty env")
assert(environmentVariable("ZEPHYR_STD_EMPTY_723817").has() and environmentVariable("ZEPHYR_STD_EMPTY_723817").get() == "", "empty environment")
let startMs = nowMilliseconds()
let startNs = nowNanoseconds()
sleepMilliseconds(20)
assert(nowMilliseconds() >= startMs + 10 and nowNanoseconds() > startNs, "monotonic clocks")
assert(run("cmd.exe /c exit 7") == 7, "child exit")
print("ok")
'@
# Run every concurrency scenario on Windows and compile the same source to Linux ELF.
function TestThreadSrc($name, $source) {
    TestSrc $name $source
    $sourcePath = Join-Path $tempRoot "$name.zeph"
    $elfPath = Join-Path $tempRoot "$name.elf"
    $compilerOutput = & .\zc.exe --linux --rt $sourcePath $elfPath 2>&1 | Out-String
    $compileCode = $LASTEXITCODE
    $validElf = $false
    if (Test-Path -LiteralPath $elfPath) {
        $elfBytes = [IO.File]::ReadAllBytes($elfPath)
        $validElf = $elfBytes.Length -ge 4 -and $elfBytes[0] -eq 127 -and $elfBytes[1] -eq 69 -and $elfBytes[2] -eq 76 -and $elfBytes[3] -eq 70
    }
    Check "$name linux (compile only)" ($compileCode -eq 0 -and $validElf) "exit=$compileCode, ELF=$validElf, compiler=$compilerOutput"
}
TestThreadSrc 'sync_mutex' @'
import "std/thread.zeph"
import "std/sync.zeph"
let counterAddress = allocateSyncStorage(8)
let guard = newMutex()
let guardAddress = guard.address
assert(guard.tryLock(), "uncontended try lock")
assert(guard.tryLock(), "recursive try lock")
guard.unlock()
let blockedWorker = spawnThread(fn(unusedIndex: int) {
    let localGuard = Mutex{address: guardAddress}
    assert(not localGuard.tryLock(), "other thread cannot acquire")
}, 0)
blockedWorker.join()
guard.unlock()
parallelFor(8, fn(workerIndex: int) {
    let localGuard = Mutex{address: guardAddress}
    for i in 0..2000 {
        localGuard.lock()
        store64(counterAddress, load64(counterAddress) + 1)
        localGuard.unlock()
    }
})
assert(load64(counterAddress) == 16000, "mutex exact counter")
assert(cpuCount() >= 1, "processor count")
print("ok")
'@
TestThreadSrc 'sync_atomic' @'
import "std/thread.zeph"
import "std/sync.zeph"
let counter = newAtomic(3)
assert(counter.load() == 3, "initial load")
counter.store(10)
assert(counter.add(-2) == 8, "add returns new value")
assert(counter.swap(20) == 8 and counter.load() == 20, "swap returns old value")
assert(not counter.compareExchange(19, 30) and counter.load() == 20, "failed compare exchange")
assert(counter.compareExchange(20, 30) and counter.load() == 30, "successful compare exchange")
counter.store(0)
let counterAddress = counter.address
parallelFor(8, fn(workerIndex: int) {
    let localCounter = Atomic{address: counterAddress}
    for i in 0..5000 { let nextCount = localCounter.add(1) }
})
assert(counter.load() == 40000, "atomic exact counter")
print("ok")
'@
TestThreadSrc 'sync_channel' @'
import "std/thread.zeph"
import "std/sync.zeph"
let messages = newChannel(3)
assert(not messages.tryReceive().has(), "empty try receive")
let channelAddress = messages.address
let channelGuard = Mutex{address: channelAddress}
channelGuard.lock()
let probingWorker = spawnThread(fn(unusedIndex: int) {
    let localMessages = Channel{address: channelAddress}
    assert(not localMessages.tryReceive().has(), "contended try receive never blocks")
}, 0)
probingWorker.join()
channelGuard.unlock()
let producer = spawnThread(fn(unusedIndex: int) {
    let localMessages = Channel{address: channelAddress}
    for i in 1..1001 { localMessages.send(i) }
    localMessages.close()
}, 0)
var receivedSum = 0
for i in 1..1001 {
    let message = messages.receive()
    assert(message.has() and message.get() == i, "FIFO sequence")
    receivedSum += message.get()
}
assert(receivedSum == 500500, "received sum")
assert(not messages.receive().has(), "closed drained receive")
producer.join()
assert(messages.len() == 0 and not messages.tryReceive().has(), "closed drained length")
let buffered = newChannel(2)
buffered.send(7)
buffered.send(9)
assert(buffered.len() == 2, "buffered length")
buffered.close()
buffered.close()
assert(buffered.receive().get() == 7 and buffered.tryReceive().get() == 9, "drain after close")
assert(not buffered.receive().has(), "none after drain")
print("ok")
'@
TestThreadSrc 'sync_wait_group' @'
import "std/thread.zeph"
import "std/sync.zeph"
let completed = newAtomic(0)
let completedAddress = completed.address
let group = newWaitGroup()
let groupAddress = group.address
group.wait()
group.add(8)
var workers: [Thread] = []
for i in 0..8 {
    workers.push(spawnThread(fn(workerIndex: int) {
        let localGroup = WaitGroup{address: groupAddress}
        let localCompleted = Atomic{address: completedAddress}
        let nextCount = localCompleted.add(1)
        localGroup.done()
    }, i))
}
group.wait()
assert(completed.load() == 8, "wait observes all workers")
for worker in workers { worker.join() }
group.add(2)
group.add(-2)
group.wait()
print("ok")
'@
TestThreadSrc 'thread_tls_reuse' @'
import "std/thread.zeph"
for i in 0..20 {
    parallelFor(4, fn(workerIndex: int) {
        for j in 0..100 {
            let message = "worker {workerIndex} value {j}"
            assert(message == "worker " + (workerIndex as str) + " value " + (j as str), "thread-local interpolation")
        }
    })
}
print("ok")
'@
TestPanic 'sync_invalid_capacity' 'import "std/sync.zeph"
newChannel(0)' 'channel: invalid capacity'
TestPanic 'sync_capacity_overflow' 'import "std/sync.zeph"
newChannel(9223372036854775807)' 'channel: invalid capacity'
TestPanic 'sync_send_closed' 'import "std/sync.zeph"
let messages = newChannel(1)
messages.close()
messages.send(1)' 'channel: send after close'
TestPanic 'sync_wait_group_underflow' 'import "std/sync.zeph"
let group = newWaitGroup()
group.done()' 'wait_group: invalid count'
TestSrc 'result_and_set' @'
import "std/result.zeph"
import "std/set.zeph"
fn parse_port(text: str) -> Result[int, str] {
    let port = text as int
    if port < 1 or port > 65535 { return Result.Err("not a port: {text}") }
    return Result.Ok(port)
}
let good = parse_port("8080")
let bad = parse_port("70000")
assert(good.isOk() and bad.isError(), "is_ok")
assert(good.unwrap() == 8080 and bad.unwrapOr(1) == 1, "unwrap")
assert(good.ok().get() == 8080 and bad.ok() == none, "ok")
assert(bad.error().get() == "not a port: 70000" and good.error() == none, "err")
let doubled = good.map(fn(port: int) -> int { return port * 2 })
assert(doubled.unwrap() == 16160, "map")
let described = good.map(fn(port: int) -> str { return "port {port}" })
assert(described.unwrap() == "port 8080", "map type change")
let coded = bad.mapError(fn(message: str) -> int { return message.len() })
assert(coded.error().get() == 17, "map_err")
let chained = good.andThen(fn(port: int) -> Result[int, str] { return parse_port("{port + 57536}") })
assert(chained.isError(), "and_then error")
assert("{good} {bad}" == "Ok(8080) Err(\"not a port: 70000\")", "print")
let seen = setOf(["a", "b", "a"])
seen.add("c")
seen.remove("b")
assert(seen.len() == 2 and seen.has("a") and not seen.has("b"), "set basics")
let other: Set[str] = Set.new()
other.add("c")
other.add("d")
assert(seen.union(other).len() == 3 and seen.intersection(other).items() == ["c"], "union/intersection")
assert(seen.difference(other).items() == ["a"] and other.intersection(seen).isSubset(seen), "difference/subset")
let pairs = setOf([(1, 2), (1, 2), (2, 1)])
assert(pairs.len() == 2, "tuple set")
print("ok")
'@
TestPanic 'result_unwrap_err' 'import "std/result.zeph"
let r: Result[int, str] = Result.Err("boom")
print(r.unwrap())' 'unwrap on an Err: boom'
TestSrc 'all_imports' @'
import "std/string.zeph"
import "std/math.zeph"
import "std/random.zeph"
import "std/io.zeph"
import "std/list.zeph"
import "std/bytes.zeph"
import "std/thread.zeph"
import "std/sync.zeph"
import "std/result.zeph"
import "std/set.zeph"
print(formatFixed(sum([1.0, 2.0]), 1))
'@ '3.0'
$linuxSource = Join-Path $tempRoot 'linux_build.zeph'
$linuxOutput = Join-Path $tempRoot 'linux_build.elf'
Set-Content -LiteralPath $linuxSource -Encoding ascii -Value @'
import "std/io.zeph"
import "std/string.zeph"
import "std/math.zeph"
import "std/random.zeph"
import "std/list.zeph"
print(formatFixed(hypot(3.0, 4.0), 2))
print(sum([1, 2, 3]))
print(newRng(42).nextInt())
print(nowMilliseconds())
print(nowNanoseconds())
sleepMilliseconds(0)
print(fileExists("."))
print(listDirectory(".").len())
printError("linux compile check")
if false {
    appendFile("compile-only.tmp", "data")
    print(deleteFile("compile-only.tmp"))
    print(readLine().has())
    print(environmentVariable("PATH").has())
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
