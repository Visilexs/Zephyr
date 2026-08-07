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

if (-not (Test-Path $zc)) {
    Write-Host "no zc.exe --- seed once: .\build.ps1; .\zephyr.exe build compiler\zc.zeph -o zc.exe --rt" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path (Join-Path (Join-Path $root "compiler") "runtime.zeph"))) {
    Write-Host "compiler/runtime.zeph missing" -ForegroundColor Red; exit 1
}
Remove-Item $new, $chk -ErrorAction SilentlyContinue

# refresh the runtime + std sources embedded in the compiler binary, so a lone
# zc.exe always carries the same code the repo files describe
powershell -ExecutionPolicy Bypass -File (Join-Path $root "scripts\embed-gen.ps1")
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "== Zephyr compiles Zephyr: zc.exe -> zc.new.exe (no gcc, no C) =="
& $zc --rt $src $new
if (-not (Test-Path $new)) { Write-Host "compile produced no output" -ForegroundColor Red; exit 1 }

Write-Host "== fixpoint: the new compiler recompiles itself, byte-identically =="
& $new --rt $src $chk
if (-not (Test-Path $chk)) { Write-Host "new compiler produced no output" -ForegroundColor Red; exit 1 }
$a = (Get-FileHash $new -Algorithm SHA256).Hash
$b = (Get-FileHash $chk -Algorithm SHA256).Hash
Remove-Item $chk -ErrorAction SilentlyContinue
if ($a -ne $b) { Write-Host "FIXPOINT FAILED --- compiler is not self-consistent" -ForegroundColor Red; exit 1 }

Move-Item -Force $new $zc
$dlls = (& objdump -p $zc 2>$null | Select-String 'DLL Name:' | ForEach-Object { ($_ -replace '.*DLL Name:\s*','').Trim() }) -join ', '
Write-Host "updated zc.exe ($($a.Substring(0,16))...) --- self-reproducing; imports: $dlls"
& $zc --version
