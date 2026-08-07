# Compile the Zephyr-written shaders (.zsh) with zspv, and validate them.
#
# GLSL sources are still here and still authoritative for the shaders zspv
# cannot express yet (anything using textures, loops, or GLSL.std.450 builtins).
# zspv covers the subset it covers; this script only rebuilds those.

$sdk = $env:VULKAN_SDK
if (-not $sdk) { $sdk = "C:\VulkanSDK\1.4.350.0" }
$val = Join-Path $sdk "Bin\spirv-val.exe"

if (-not (Test-Path ".\zspv.exe")) {
    Write-Host "building zspv..."
    & .\zc.exe --rt tools\zspv.zeph zspv.exe
}

Get-ChildItem "examples\shaders" -Filter *.zsh | ForEach-Object {
    $out = Join-Path $_.DirectoryName ($_.BaseName + ".zsh.spv")
    & .\zspv.exe $_.FullName $out
    if (Test-Path $val) {
        & $val $out
        if ($LASTEXITCODE -ne 0) { throw "spirv-val rejected $out" }
        Write-Host "  validated $($_.Name)"
    }
}
