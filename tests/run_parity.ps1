# zc run parity: every program that builds and runs as an .exe must print the same
# stdout and exit with the same code when zc run executes it in-process.
# Usage: powershell -File tests\run_parity.ps1
$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot
Set-Location $root
$tmp = Join-Path $env:TEMP "zc_parity"
New-Item -ItemType Directory -Force $tmp | Out-Null

# program, arguments (small workloads keep this gate quick)
$programs = @()
foreach ($file in Get-ChildItem tests\fixtures\basics, tests\fixtures\threads, tests -Filter *.zeph -File) {
    $programs += , @($file.FullName, "")
}
$workloadArguments = @{ fib = "27"; matmul = "120"; mandel = "120"; sort = "20000"; strings = "20000"; hashmap = "20000"; cube = "200"; pi = "500"; liquid = "40" }
foreach ($name in $workloadArguments.Keys) { $programs += , @((Resolve-Path "tests\fixtures\workloads\$name.zeph").Path, $workloadArguments[$name]) }

$passed = 0; $failed = 0; $skipped = 0
foreach ($entry in $programs) {
    $source = $entry[0]; $arguments = $entry[1]
    $name = [IO.Path]::GetFileNameWithoutExtension($source)
    $exe = Join-Path $tmp "$name.exe"
    Remove-Item $exe -ErrorAction SilentlyContinue
    & .\zc.exe --rt $source $exe 2>&1 | Out-Null
    if (-not (Test-Path $exe)) { $skipped++; continue }          # programs that do not compile are not this gate's business
    Push-Location (Split-Path $source)
    $expected = (cmd /c "`"$exe`" $arguments 2>&1" | Out-String); $expectedCode = $LASTEXITCODE
    $actual = (cmd /c "`"$root\zc.exe`" run `"$source`" $arguments 2>&1" | Out-String); $actualCode = $LASTEXITCODE
    Pop-Location
    if ($expected -eq $actual -and $expectedCode -eq $actualCode) { $passed++ }
    else {
        $failed++
        Write-Host "FAIL $name (exit $expectedCode vs $actualCode)" -ForegroundColor Red
        Write-Host ("  exe:    " + ($expected.Trim() -split "`n" | Select-Object -First 3) -join " | ")
        Write-Host ("  zc run: " + ($actual.Trim() -split "`n" | Select-Object -First 3) -join " | ")
    }
}
Write-Host "$passed passed, $failed failed, $skipped not compilable"
if ($failed -gt 0) { exit 1 }
