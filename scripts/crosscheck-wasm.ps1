# scripts/crosscheck-wasm.ps1 - compile the same sources natively and to
# WebAssembly, run both, and require identical output. Needs node; skips cleanly
# without it.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Push-Location $root

$null = & node --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "node not found; skipping wasm cross-check" -ForegroundColor Yellow
    Pop-Location
    exit 0
}

$work = ".xwasm"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory $work | Out-Null

$pass = 0
$fail = 0
foreach ($src in (Get-ChildItem "examples\wasm\*.zeph" | Sort-Object Name)) {
    $n = $src.BaseName
    & .\zc.exe --rt $src.FullName "$work\$n.exe"
    & .\zc.exe --wasm --rt $src.FullName "$work\$n.wasm"
    $native = (& "$work\$n.exe" 2>&1 | Out-String) -replace "`r", ""
    $wasm = (& node scripts\wasm-run.js "$work\$n.wasm" 2>&1 | Out-String) -replace "`r", ""
    if ($native -eq $wasm) {
        Write-Host "PASS $n" -ForegroundColor Green
        $pass++
    } else {
        Write-Host "FAIL $n" -ForegroundColor Red
        Write-Host "  native: $($native -replace "`n", '\n')"
        Write-Host "  wasm:   $($wasm -replace "`n", '\n')"
        $fail++
    }
}

Remove-Item -Recurse -Force $work
Write-Host ""
Write-Host "$pass passed, $fail failed"
Pop-Location
if ($fail -gt 0) { exit 1 }
