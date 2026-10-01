# PGO round trip: --profile-generate, run, --profile-use; the profiled build
# must print what the plain -O2 build prints and must accept its own profile.
# Usage: powershell -File tests\pgo_roundtrip.ps1 [-Compiler path\to\zc.exe]
param([string]$Compiler = "")
$ErrorActionPreference = "Continue"
$root = Split-Path $PSScriptRoot
Set-Location $root
if ($Compiler -eq "") { $Compiler = Join-Path $root "zc.exe" }
$tmp = Join-Path $env:TEMP "zc_pgo_roundtrip"
New-Item -ItemType Directory -Force $tmp | Out-Null

$programs = @(
    @("tests\fixtures\workloads\inl_superpath.zeph", "75"),
    @("tests\fixtures\workloads\inl_hotcold.zeph", "870"),
    @("tests\fixtures\workloads\liquid.zeph", "40"),
    @("tests\regression\tail_recursion.zeph", "")
)
$passed = 0; $failed = 0
foreach ($entry in $programs) {
    $source = $entry[0]; $arguments = $entry[1]
    $name = [IO.Path]::GetFileNameWithoutExtension($source)
    $profile = Join-Path $tmp "$name.zprof"
    $plain = Join-Path $tmp "$name.plain.exe"; $generate = Join-Path $tmp "$name.gen.exe"; $profiled = Join-Path $tmp "$name.pgo.exe"
    Remove-Item $profile, $plain, $generate, $profiled -ErrorAction SilentlyContinue
    & $Compiler --rt -O2 $source $plain 2>&1 | Out-Null
    & $Compiler --rt -O2 --profile-generate $profile $source $generate 2>&1 | Out-Null
    $expected = (& $plain $arguments 2>&1 | Out-String)
    $instrumented = (& $generate $arguments 2>&1 | Out-String)
    $useOutput = (& $Compiler --rt -O2 --profile-use $profile $source $profiled 2>&1 | Out-String)
    $actual = (& $profiled $arguments 2>&1 | Out-String)
    if ((Test-Path $profile) -and $instrumented -eq $expected -and $actual -eq $expected -and $useOutput -notmatch "warning") {
        $passed++; Write-Host "PASS $name"
    } else {
        $failed++; Write-Host "FAIL $name (profile written: $(Test-Path $profile))"
    }
}
Write-Host "$passed passed, $failed failed"
if ($failed -gt 0) { exit 1 }
