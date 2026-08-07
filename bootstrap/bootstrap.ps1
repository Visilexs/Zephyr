# Bootstrap the self-hosted Zephyr compiler and prove the fixpoint two ways:
#   Path A (gcc): zc emits .s, gcc assembles/links (portable reference).
#   Path B (native): zc assembles + PE-links its own .exe, no external tools.
# Both must reach a byte-identical fixpoint.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root

# ---------- Path A: gcc pipeline ----------
Write-Host "== Path A: gcc pipeline =="
.\bootstrap\zephyr.exe build compiler\zc.zeph -o compiler\zc1.exe --gcc
if ($LASTEXITCODE -ne 0) { exit 1 }
Measure-Command { .\compiler\zc1.exe compiler\zc.zeph compiler\stage2.s | Out-Host } |
    ForEach-Object { "zc1 compiled zc.zeph in {0:n0} ms" -f $_.TotalMilliseconds } | Write-Host
if ($LASTEXITCODE -ne 0) { exit 1 }
gcc compiler\stage2.s bootstrap\runtime.o -o compiler\zc2.exe
if ($LASTEXITCODE -ne 0) { exit 1 }
.\compiler\zc2.exe compiler\zc.zeph compiler\stage3.s
if ($LASTEXITCODE -ne 0) { exit 1 }
$s2 = Get-FileHash compiler\stage2.s -Algorithm SHA256
$s3 = Get-FileHash compiler\stage3.s -Algorithm SHA256
if ($s2.Hash -ne $s3.Hash) {
    Write-Host "FIXPOINT FAILED (gcc): stage2.s and stage3.s differ" -ForegroundColor Red
    exit 1
}
Write-Host "gcc fixpoint reached: stage2.s == stage3.s ($($s2.Hash.Substring(0,16))...)"

# ---------- Path B: native (no external toolchain) ----------
Write-Host ""
Write-Host "== Path B: native assembler + PE linker (no gcc) =="
.\bootstrap\zephyr.exe build compiler\zc.zeph -o compiler\zcN.exe
if ($LASTEXITCODE -ne 0) { exit 1 }
Copy-Item bootstrap\zephyr_rt.dll compiler\zephyr_rt.dll -Force
# zcN assembles itself into a native exe, twice; the two must be identical
Measure-Command { .\compiler\zcN.exe compiler\zc.zeph compiler\zcN2.exe | Out-Host } |
    ForEach-Object { "zcN self-assembled a native exe in {0:n0} ms" -f $_.TotalMilliseconds } | Write-Host
if ($LASTEXITCODE -ne 0) { exit 1 }
.\compiler\zcN2.exe compiler\zc.zeph compiler\zcN3.exe
if ($LASTEXITCODE -ne 0) { exit 1 }
$n2 = Get-FileHash compiler\zcN2.exe -Algorithm SHA256
$n3 = Get-FileHash compiler\zcN3.exe -Algorithm SHA256
if ($n2.Hash -ne $n3.Hash) {
    Write-Host "FIXPOINT FAILED (native): zcN2.exe and zcN3.exe differ" -ForegroundColor Red
    exit 1
}
Write-Host "native fixpoint reached: zcN2.exe == zcN3.exe ($($n2.Hash.Substring(0,16))...)"

Write-Host "== native zc compiles and runs the examples =="
foreach ($ex in @("hello", "fizzbuzz", "shapes", "convert")) {
    .\compiler\zcN2.exe "examples\basics\$ex.zeph" "compiler\$ex.exe"
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL compile $ex" -ForegroundColor Red; exit 1 }
    $a = (& ".\compiler\$ex.exe" | Out-String).Trim()
    $b = (& .\bootstrap\zephyr.exe run "examples\basics\$ex.zeph" | Out-String).Trim()
    if ($a -ne $b) { Write-Host "FAIL output mismatch: $ex" -ForegroundColor Red; exit 1 }
    Write-Host "PASS $ex (native self-hosted output matches C compiler)"
    Remove-Item "compiler\$ex.exe" -Confirm:$false
}
Remove-Item compiler\zcN*.exe, compiler\zephyr_rt.dll, compiler\zc1.exe, compiler\zc2.exe, `
    compiler\stage2.s, compiler\stage3.s -Confirm:$false -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "SELF-HOSTING VERIFIED: Zephyr compiles AND links itself, with and without gcc."
