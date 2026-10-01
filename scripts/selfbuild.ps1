# selfbuild.ps1 --- rebuild the Zephyr compiler using ONLY the Zephyr compiler.
# No gcc, no C. Ongoing workflow: edit compiler\zc.zeph, run this, and the
# Zephyr compiler recompiles itself into a new zc.exe.
#
# It needs an existing zc.exe to start from (the compiler is a binary seed,
# exactly like rustc or the Go toolchain). The first zc.exe was produced
# once from C via build.ps1; after that, only this script is needed.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root
[System.IO.Directory]::SetCurrentDirectory($root)

$zc = Join-Path $root "zc.exe"
$src   = Join-Path $root "compiler\zc.zeph"
$new   = Join-Path $root "zc.new.exe"
$chk   = Join-Path $root "zc.chk.exe"
$third = Join-Path $root "zc.third.exe"

if (-not (Test-Path $zc)) {
    Write-Host "no zc.exe --- seed once: .\bootstrap\build.ps1" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path (Join-Path (Join-Path $root "compiler") "runtime.zeph"))) {
    Write-Host "compiler/runtime.zeph missing" -ForegroundColor Red; exit 1
}
Remove-Item $new, $chk, $third -ErrorAction SilentlyContinue

# refresh the runtime + std sources embedded in the compiler binary, so a lone
# zc.exe always carries the same code the repo files describe
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\embed-gen.ps1")
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "== Zephyr compiles Zephyr: zc.exe -> zc.new.exe (no gcc, no C) =="
& $zc --rt $src $new
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $new)) { Write-Host "compile failed" -ForegroundColor Red; exit 1 }

Write-Host "== converge from the checked-in seed, then compare generations 2 and 3 =="
& $new --rt $src $chk
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $chk)) { Write-Host "generation 2 failed" -ForegroundColor Red; exit 1 }
& $chk --rt $src $third
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $third)) { Write-Host "generation 3 failed" -ForegroundColor Red; exit 1 }
$a = (Get-FileHash $chk -Algorithm SHA256).Hash
$b = (Get-FileHash $third -Algorithm SHA256).Hash
if ($a -ne $b) { Write-Host "FIXPOINT FAILED --- compiler is not self-consistent" -ForegroundColor Red; exit 1 }

Move-Item -Force $chk $zc
Remove-Item $new, $third
Write-Host "updated zc.exe ($($a.Substring(0,16))...) --- generations 2 and 3 are byte-identical"
& $zc --version
