# scripts/crosscheck-linux.ps1 - compile the same sources for Windows and for
# Linux, run both, and require identical output. Needs WSL with an x86_64 distro;
# skips cleanly if there isn't one.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Push-Location $root

$arch = (wsl -e uname -m 2>$null)
if ($LASTEXITCODE -ne 0 -or $arch -notmatch "x86_64") {
    Write-Host "no x86_64 WSL distro; skipping Linux cross-check" -ForegroundColor Yellow
    Pop-Location
    exit 0
}

$work = ".xcheck"
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory $work | Out-Null

$cases = @(
    "examples\basics\convert.zeph",
    "examples\basics\fizzbuzz.zeph",
    "examples\basics\hello.zeph",
    "examples\basics\oop.zeph",
    "examples\basics\shapes.zeph",
    "examples\basics\stdlib.zeph"
)

$pass = 0
$fail = 0
foreach ($c in $cases) {
    $n = [IO.Path]::GetFileNameWithoutExtension($c)
    & .\zc.exe --rt $c "$work\$n.exe"
    & .\zc.exe --linux --rt $c "$work\$n.elf"
    $w = (& "$work\$n.exe" 2>&1 | Out-String) -replace "`r", ""
    $l = (wsl -e sh -c "chmod +x $work/$n.elf && ./$work/$n.elf" 2>&1 | Out-String) -replace "`r", ""
    if ($w -eq $l) {
        Write-Host "PASS $n" -ForegroundColor Green
        $pass++
    } else {
        Write-Host "FAIL $n" -ForegroundColor Red
        Write-Host "  win:   $($w -replace "`n", '\n')"
        Write-Host "  linux: $($l -replace "`n", '\n')"
        $fail++
    }
}

# The compiler itself, cross-compiled and then reproducing its own binary on Linux.
& .\zc.exe --linux --rt compiler\zc.zeph "$work\zc-linux"
$fx = wsl -e sh -c "chmod +x $work/zc-linux && ./$work/zc-linux --linux --rt compiler/zc.zeph $work/zc-linux2 && cmp -s $work/zc-linux $work/zc-linux2 && echo yes"
if ($fx -match "yes") {
    Write-Host "PASS zc-linux self-build fixpoint" -ForegroundColor Green
    $pass++
} else {
    Write-Host "FAIL zc-linux self-build fixpoint" -ForegroundColor Red
    $fail++
}

Remove-Item -Recurse -Force $work
Write-Host ""
Write-Host "$pass passed, $fail failed"
Pop-Location
if ($fail -gt 0) { exit 1 }
