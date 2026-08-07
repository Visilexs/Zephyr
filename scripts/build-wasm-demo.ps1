# scripts/build-wasm-demo.ps1 - compile a Zephyr program to wasm and wrap it in
# a single self-contained HTML file (the module is inlined as base64, so the page
# needs no server and no fetch). Defaults to examples/wasm/ascii.zeph.
#
#   .\scripts\build-wasm-demo.ps1 [source.zeph] [out.html]
param(
    [string]$Source = "examples\wasm\ascii.zeph",
    [string]$Out = "dist\zephyr-wasm-demo.html"
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Push-Location $root

$tmp = [IO.Path]::GetTempFileName() + ".wasm"
& .\zc.exe --wasm --rt $Source $tmp
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($tmp))
$size = (Get-Item $tmp).Length
Remove-Item $tmp

$outDir = Split-Path $Out
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory $outDir | Out-Null }

$head = [IO.File]::ReadAllText((Join-Path $PSScriptRoot "wasm-demo-head.html"))
$tail = [IO.File]::ReadAllText((Join-Path $PSScriptRoot "wasm-demo-tail.html"))
[IO.File]::WriteAllText($Out, $head + $b64 + $tail)

Write-Host "$Out  ($size bytes of wasm, $((Get-Item $Out).Length) bytes of page)"
Pop-Location
