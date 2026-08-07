# package.ps1 - assemble a self-contained Zephyr distribution for end users.
# Produces dist\zephyr-<version>\ (a runnable install) and dist\zephyr-<version>.zip.
# Ships only what a user needs to compile programs: the compiler, the runtime,
# the standard library, docs, and examples. No bootstrap C sources, tests, or
# benchmarks.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root

$version = "0.2"
$name = "zephyr-$version"
$out = Join-Path $root "dist\$name"

if (-not (Test-Path (Join-Path $root "zc.exe"))) {
    Write-Host "zc.exe not found - run .\selfbuild.ps1 first" -ForegroundColor Red
    exit 1
}

# fresh staging directory
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
New-Item -ItemType Directory -Force $out | Out-Null
New-Item -ItemType Directory -Force (Join-Path $out "docs") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $out "examples") | Out-Null

# the compiler is single-file: runtime.zeph and std/ are embedded in zc.exe
# (a runtime.zeph placed next to the exe would override the embedded copy)
Copy-Item "zc.exe" $out

# docs a user actually reads (skip internal design notes)
Copy-Item "docs\tour.md" (Join-Path $out "docs")
Copy-Item "docs\spec.md" (Join-Path $out "docs")

# example source (no build artifacts)
Copy-Item "examples\basics\*.zeph" (Join-Path $out "examples")

# getting-started guide as the package README
Copy-Item "dist\GETTING-STARTED.md" (Join-Path $out "README.md")

# sanity check: the packaged compiler builds a std-importing program from a
# BARE directory -- proving the embedded runtime and std library work with no
# support files at all
$probe = Join-Path $env:TEMP "zephyr_pkg_probe"
if (Test-Path $probe) { Remove-Item $probe -Recurse -Force }
New-Item -ItemType Directory -Force $probe | Out-Null
Copy-Item (Join-Path $out "zc.exe") (Join-Path $probe "zc.exe")
Set-Content (Join-Path $probe "check.zeph") @'
import "std/list.zeph"
print(map([1, 2, 3], fn(x: int) -> int { return x + 1 }))
'@ -Encoding ascii
Push-Location $env:TEMP     # cwd away from any runtime.zeph
& (Join-Path $probe "zc.exe") --rt (Join-Path $probe "check.zeph") (Join-Path $probe "check.exe")
$got = (& (Join-Path $probe "check.exe") | Out-String).Trim()
Pop-Location
Remove-Item $probe -Recurse -Force
if ($got -ne "[2, 3, 4]") {
    Write-Host "package self-check FAILED (got: $got)" -ForegroundColor Red
    exit 1
}

# zip it
$zip = Join-Path $root "dist\$name.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $out -DestinationPath $zip

$size = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Host "packaged $name (self-check: [2, 3, 4] OK)"
Write-Host "  folder: dist\$name\"
Write-Host "  zip:    dist\$name.zip  ($size MB)"
