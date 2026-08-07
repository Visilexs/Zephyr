# bootstrap/build.ps1 - reconstruct the C seed and produce the first zc.exe.
# This is the ONLY step that needs gcc/C. It exists so the toolchain can be
# rebuilt from source if the zc.exe binary is ever lost. Day to day you use
# ..\selfbuild.ps1 (Zephyr compiling Zephyr), which needs none of this.
$ErrorActionPreference = "Stop"
$here = $PSScriptRoot
$root = Split-Path $here
Push-Location $here    # build here, but don't leak cwd to the caller
try {
    # C bootstrap compiler + C runtime (built in-place, they stay in bootstrap\)
    gcc -O2 -Wall -o zephyr.exe zephyr.c
    if ($LASTEXITCODE -ne 0) { exit 1 }
    gcc -O2 -Wall -c runtime.c -o runtime.o
    if ($LASTEXITCODE -ne 0) { exit 1 }
    gcc -O2 -Wall -shared -DZEPHYR_RT_DLL runtime.c -o zephyr_rt.dll
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Copy-Item "$root\compiler\runtime.zeph" runtime.zeph -Force   # for zephyr.exe --rt

    # seed the Zephyr compiler: C compiler emits the first kernel32-only zc.exe
    .\zephyr.exe build "$root\compiler\zc.zeph" -o "$root\zc.exe" --rt
    if ($LASTEXITCODE -ne 0) { exit 1 }
    Write-Host "built C seed (bootstrap\zephyr.exe, zephyr_rt.dll) and seeded zc.exe"
    Write-Host "from here on, use .\selfbuild.ps1 - no gcc, no C"
} finally {
    Pop-Location
}
