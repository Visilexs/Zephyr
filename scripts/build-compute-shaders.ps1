# Compile the ML compute kernels from GLSL to SPIR-V.
#
# Separate from scripts\build-shaders.ps1, which drives tools\zspv.zeph: zspv
# emits vertex and fragment shaders only, float32 only, with no storage
# buffers and no control flow, so it cannot express a matmul. These kernels are
# hand-written GLSL and go through glslc from the Vulkan SDK.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $root "examples\shaders"

$glslc = (Get-Command glslc -ErrorAction SilentlyContinue)
if (-not $glslc) {
    Write-Error "glslc not found on PATH. Install the Vulkan SDK, or add its Bin directory."
}

$fail = 0
foreach ($f in @("matmul_f32.comp", "matmul_f64.comp")) {
    $in  = Join-Path $src $f
    $out = "$in.spv"
    & glslc --target-env=vulkan1.2 -O $in -o $out
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  $f"; $fail++; continue }
    $n = (Get-Item $out).Length
    Write-Host "ok    $f -> $(Split-Path -Leaf $out) ($n bytes)"
}
if ($fail -gt 0) { exit 1 }
