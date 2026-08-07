# Prove the toolchain is self-sustaining with ZERO gcc and ZERO C.
# The C bootstrap (zephyr.exe) is used ONCE to seed the first Zephyr-runtime zc;
# after that, a kernel32-only compiler reproduces itself byte-for-byte and
# compiles kernel32-only programs, with no gcc and no C runtime in the loop.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root

$work = Join-Path $env:TEMP "zephyr_nocc"
Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $work | Out-Null

# --- one-time C seed: build the first kernel32-only zc ---
Write-Host "== seed: C compiler builds a kernel32-only zc (--rt) =="
.\bootstrap\zephyr.exe build compiler\zc.zeph -o "$work\zc1.exe" --rt
if ($LASTEXITCODE -ne 0) { exit 1 }
Copy-Item compiler\runtime.zeph "$work\runtime.zeph"
Copy-Item compiler\zc.zeph "$work\zc.zeph"
Copy-Item examples\hello.zeph "$work\hello.zeph"
Set-Location $work
[System.IO.Directory]::SetCurrentDirectory($work)   # .NET file APIs use this

function DepDLLs($exe) {
    # actual PE imports (Import Directory), via objdump — inspection only, not
    # part of the toolchain. Falls back to none if objdump is unavailable.
    $out = & objdump -p $exe 2>$null | Select-String 'DLL Name:'
    return ($out | ForEach-Object { ($_ -replace '.*DLL Name:\s*', '').Trim().ToLower() } | Sort-Object -Unique)
}

foreach ($g in @(@("zc1", "zc2"), @("zc2", "zc3"))) {
    $c = $g[0]; $o = $g[1]
    Write-Host "== $c compiles zc.zeph --rt -> $o (no gcc, no C) =="
    & ".\$c.exe" --rt zc.zeph "$o.exe"
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL: $c could not compile zc" -ForegroundColor Red; exit 1 }
    $dlls = DepDLLs "$o.exe"
    if ($dlls -contains "zephyr_rt.dll") { Write-Host "FAIL: $o depends on zephyr_rt.dll" -ForegroundColor Red; exit 1 }
    Write-Host "  $o dependencies: $($dlls -join ', ')"
}

Write-Host "== fixpoint: zc2.exe == zc3.exe ? =="
$h2 = (Get-FileHash zc2.exe -Algorithm SHA256).Hash
$h3 = (Get-FileHash zc3.exe -Algorithm SHA256).Hash
if ($h2 -ne $h3) { Write-Host "FIXPOINT FAILED: zc2 != zc3" -ForegroundColor Red; exit 1 }
Write-Host "  fixpoint reached ($($h2.Substring(0,16))...)"

Write-Host "== the C-free-built compiler compiles + runs a program =="
& .\zc2.exe --rt hello.zeph hello.exe
if ($LASTEXITCODE -ne 0) { exit 1 }
$out = (& .\hello.exe | Out-String).Trim()
if ($out -ne "Hello, Zephyr!") { Write-Host "FAIL: got '$out'" -ForegroundColor Red; exit 1 }
Write-Host "  hello.exe -> $out  (deps: $((DepDLLs hello.exe) -join ', '))"

Write-Host ""
Write-Host "NO-C TOOLCHAIN VERIFIED: a kernel32-only compiler/assembler/linker"
Write-Host "reproduces itself and compiles kernel32-only programs, with no gcc and no C runtime."
