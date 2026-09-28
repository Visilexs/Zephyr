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
$validator = (Get-Command spirv-val -ErrorAction SilentlyContinue)
if (-not $validator) {
    Write-Error "spirv-val not found on PATH. Install the Vulkan SDK, or add its Bin directory."
}

$fail = 0
foreach ($f in @("matmul_f32.comp", "matmul_f64.comp", "matmul_c64.comp",
                 "elem_binary_f64.comp", "elem_unary_f64.comp",
                 "reduce_f64.comp", "gather_f64.comp", "scatter_add_f64.comp")) {
    $in  = Join-Path $src $f
    if (-not (Test-Path $in)) { Write-Host "FAIL  $f (missing source)"; $fail++; continue }
    $out = "$in.spv"
    & glslc --target-env=vulkan1.2 -O $in -o $out
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  $f"; $fail++; continue }
    & $validator.Source --target-env vulkan1.2 $out
    if ($LASTEXITCODE -ne 0) { Write-Host "FAIL  $f (SPIR-V validation)"; $fail++; continue }
    $n = (Get-Item $out).Length
    Write-Host "ok    $f -> $(Split-Path -Leaf $out) ($n bytes)"
}
if ($fail -gt 0) { exit 1 }
