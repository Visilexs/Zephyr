# -O2 parity: every program must print the same stdout and exit with the same
# code whether the optimizing tier compiled it or the baseline did.
# Usage: powershell -File tests\optimizer_parity.ps1 [-Compiler path\to\zc.exe] [-Report]
param([string]$Compiler = "", [switch]$Report)
$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot
Set-Location $root
if ($Compiler -eq "") { $Compiler = Join-Path $root "zc.exe" }
$tmp = Join-Path $env:TEMP "zc_optimizer_parity"
New-Item -ItemType Directory -Force $tmp | Out-Null

$programs = @()
foreach ($file in Get-ChildItem examples\basics, examples\threads, tests -Filter *.zeph -File) {
    $programs += , @($file.FullName, "")
}
$programs += , @((Resolve-Path "tests\regression\byteComparisonBranches.zeph").Path, "")
$programs += , @((Resolve-Path "tests\regression\typedRawSlotReuse.zeph").Path, "")
$programs += , @((Resolve-Path "tests\regression\scaledAddressValues.zeph").Path, "")
$benchArguments = @{ fib = "27"; matmul = "120"; mandel = "120"; sort = "20000"; strings = "20000"; hashmap = "20000"; cube = "200"; pi = "500"; liquid = "40";
                     shapes = "3000"; closures = "2000"; wordfreq = "30000"; nbody = "10"; lexer = "10000"; vectors = "20" }
foreach ($name in $benchArguments.Keys) { $programs += , @((Resolve-Path "bench\$name.zeph").Path, $benchArguments[$name]) }

$passed = 0; $failed = 0; $skipped = 0
foreach ($entry in $programs) {
    $source = $entry[0]; $arguments = $entry[1]
    $name = [IO.Path]::GetFileNameWithoutExtension($source)
    $baseline = Join-Path $tmp "$name.base.exe"
    $optimized = Join-Path $tmp "$name.opt.exe"
    Remove-Item $baseline, $optimized -ErrorAction SilentlyContinue
    & $Compiler --rt $source $baseline 2>&1 | Out-Null
    if (-not (Test-Path $baseline)) { $skipped++; continue }          # programs that do not compile are not this gate's business
    $compileOutput = (& $Compiler --rt -O2 --opt-report $source $optimized 2>&1 | Out-String)
    if ($Report) { $compileOutput -split "`n" | Where-Object { $_ -match "^opt: " -and $_ -notmatch "runtime" } | ForEach-Object { Write-Host "  [$name] $_" } }
    if (-not (Test-Path $optimized)) {
        $failed++
        Write-Host "FAIL ${name}: -O2 did not compile" -ForegroundColor Red
        Write-Host ("  " + ($compileOutput.Trim() -split "`n" | Select-Object -Last 3) -join " | ")
        continue
    }
    Push-Location (Split-Path $source)
    $expected = (cmd /c "`"$baseline`" $arguments 2>&1" | Out-String); $expectedCode = $LASTEXITCODE
    $actual = (cmd /c "`"$optimized`" $arguments 2>&1" | Out-String); $actualCode = $LASTEXITCODE
    Pop-Location
    if ($expected -eq $actual -and $expectedCode -eq $actualCode) { $passed++ }
    else {
        $failed++
        Write-Host "FAIL $name (exit $expectedCode vs $actualCode)" -ForegroundColor Red
        Write-Host ("  baseline: " + ($expected.Trim() -split "`n" | Select-Object -First 3) -join " | ")
        Write-Host ("  -O2:      " + ($actual.Trim() -split "`n" | Select-Object -First 3) -join " | ")
    }
}
Write-Host "$passed passed, $failed failed, $skipped not compilable"
if ($failed -gt 0) { exit 1 }
