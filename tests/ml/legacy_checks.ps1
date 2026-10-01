# Archived ML checks, formerly part of run_tests.ps1.
# Dot-sourced by that runner only when the optional libraries are restored.
# Requires the runner's Check/RunSrc helpers and $root/$tmp variables.

# ---- lib/ml tensor descriptors and storage: acceptance A02 and A03 ----
Remove-Item "$tmp\tensor_test.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt tests\ml\tensor_test.zeph "$tmp\tensor_test.exe" 2>&1 | Out-Null
$tenBuilt = Test-Path "$tmp\tensor_test.exe"
$tenOut = if ($tenBuilt) { (cmd /c "`"$tmp\tensor_test.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
Check "ml-tensor" ($tenBuilt -and $tenOut -eq "tensor: 73 checks passed") "got: $tenOut"

# ---- and the inputs that must be REJECTED, one process each: a rejection is
# ---- a panic, so it cannot be asserted from inside the positive suite ----
$mlNeg = [ordered]@{
    "negdim"      = 'let t = tensorZeros(DType.F64, [0 - 2, 3])'
    "overflow"    = 'let t = tensorZeros(DType.F64, [3000000000, 3000000000])'
    "bytecap"     = 'let t = tensorZeros(DType.C64, [500000000000])'
    "idx-high"    = "let t = tensorZeros(DType.F64, [2, 3])`nprint(`"{tensorGet(t, [2, 0])}`")"
    "idx-neg"     = "let t = tensorZeros(DType.F64, [2, 3])`nprint(`"{tensorGet(t, [0 - 1, 0])}`")"
    "idx-rank"    = "let t = tensorZeros(DType.F64, [2, 3])`nprint(`"{tensorGet(t, [1])}`")"
    "reshape-n"   = "let t = tensorZeros(DType.F64, [2, 3])`nlet r = tensorReshape(t, [4, 2])"
    "reshape-nc"  = "let t = tensorZeros(DType.F64, [2, 3])`nlet r = tensorReshape(tensorTranspose(t, 0, 1), [6])"
    "slice-oob"   = "let t = tensorZeros(DType.F64, [2, 3])`nlet s = tensorSlice(t, 1, 1, 9)"
    "axis-oob"    = "let t = tensorZeros(DType.F64, [2, 3])`nlet x = tensorTranspose(t, 0, 5)"
    "bcast-bad"   = 'let s = broadcastShape([2, 3], [4, 3])'
    "stale-save"  = "let t = tensorZeros(DType.F64, [2])`nlet s = tensorSave(t)`ntensorSet(t, [0], 1.0)`nlet b = savedGet(s)"
    "dbl-release" = "let t = tensorZeros(DType.F64, [2])`nstorageRelease(t.storage)`nstorageRelease(t.storage)"
    "cplx-get"    = "let t = tensorZeros(DType.C32, [2])`nprint(`"{tensorGet(t, [0])}`")"
    "int-set"     = "let t = tensorZeros(DType.I64, [2])`ntensorSet(t, [0], 1.5)"
}
foreach ($nm in $mlNeg.Keys) {
    $src = "import `"ml/tensor.zeph`"`n" + $mlNeg[$nm]
    $f = Join-Path $tmp "mlneg_$nm.zeph"
    $x = Join-Path $tmp "mlneg_$nm.exe"
    Set-Content -Path $f -Value $src -Encoding ascii
    Remove-Item $x -ErrorAction SilentlyContinue
    & .\zc.exe --rt $f $x 2>&1 | Out-Null
    if (-not (Test-Path $x)) { Check "ml-reject:$nm" $false "did not compile"; continue }
    $o = (cmd /c "`"$x`" 2>&1" | Out-String).Trim()
    Check "ml-reject:$nm" ($LASTEXITCODE -ne 0 -and $o -match "panic:") "expected panic, got($LASTEXITCODE): $o"
}

# ---- lib/ml CPU operators: acceptance A04 and A05 ----
Remove-Item "$tmp\ops_test.exe" -ErrorAction SilentlyContinue
& .\zc.exe --rt tests\ml\ops_test.zeph "$tmp\ops_test.exe" 2>&1 | Out-Null
$opsBuilt = Test-Path "$tmp\ops_test.exe"
$opsOut = if ($opsBuilt) { (cmd /c "`"$tmp\ops_test.exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
Check "ml-ops" ($opsBuilt -and $opsOut -eq "ops: 107 checks passed") "got: $opsOut"

# ---- autograd and the differentiable phase forward: A06, A07, A14 ----
$adSuites = [ordered]@{
    "ml-autograd" = @("tests\ml\autograd_test.zeph", "autograd: 674 checks passed")
    "ml-phase-ad" = @("tests\ml\phase_ad_test.zeph", "phase ad: 180 checks passed")
    "ml-optim"    = @("tests\ml\optim_test.zeph", "optim: 82 checks passed")
    "ml-overfit"  = @("tests\ml\overfit_test.zeph", "overfit: 132 checks passed")
    "ml-ir"       = @("tests\ml\ir_test.zeph", "ir: 58 checks passed")
    "ml-opt"      = @("tests\ml\opt_test.zeph", "opt: 23 checks passed")
    "ml-fusion"   = @("tests\ml\fusion_test.zeph", "fusion: 40 checks passed")
    "ml-gru"      = @("tests\ml\gru_test.zeph", "gru: 275 checks passed")
    "ml-dataset"  = @("tests\ml\dataset_test.zeph", "dataset: 98 checks passed")
    "ml-transformer" = @("tests\ml\transformer_test.zeph", "transformer: 18 checks passed")
    "ml-ablation"  = @("tests\ml\ablation_test.zeph", "ablation: 19 checks passed")
    "ml-causal"    = @("tests\ml\causal_test.zeph", "causal: 20 checks passed")
    "ml-lifecycle" = @("tests\ml\lifecycle_test.zeph", "lifecycle: 11 checks passed")
}
foreach ($nm in $adSuites.Keys) {
    $src = $adSuites[$nm][0]
    $want = $adSuites[$nm][1]
    $exe = Join-Path $tmp "$nm.exe"
    Remove-Item $exe -ErrorAction SilentlyContinue
    & .\zc.exe --rt $src $exe 2>&1 | Out-Null
    $built = Test-Path $exe
    $out = if ($built) { (cmd /c "`"$exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
    $tail = ($out -split "`n" | Select-Object -Last 1).Trim()
    Check $nm ($built -and $tail -eq $want) "got: $tail"
}

# ---- phase forward port: acceptance A13, and A10 at the gate level ----
# phase_test.zeph runs its own rejection cases by relaunching itself, because
# a panic cannot be caught in-process; no separate entries are needed here.
$phaseSuites = [ordered]@{
    "ml-phase"       = @("tests\ml\phase_test.zeph", "phase: 205 checks passed")
    "ml-phase-gates" = @("tests\ml\phase_gates_test.zeph", "phase gates: 1981 checks passed")
}
foreach ($nm in $phaseSuites.Keys) {
    $src = $phaseSuites[$nm][0]
    $want = $phaseSuites[$nm][1]
    $exe = Join-Path $tmp "$nm.exe"
    Remove-Item $exe -ErrorAction SilentlyContinue
    & .\zc.exe --rt $src $exe 2>&1 | Out-Null
    $built = Test-Path $exe
    $out = if ($built) { (cmd /c "`"$exe`" 2>&1" | Out-String).Trim() -replace "`r", "" } else { "" }
    Check $nm ($built -and $out -eq $want) "got: $out"
}

# ---- GPU compute backend (A20) ----
# Skipped rather than failed when no Vulkan device is present: the backend is
# optional and its absence is an environment fact, not a defect. The kernels
# are also skipped over if they have not been built, since building them needs
# glslc from the Vulkan SDK, which is not required to work on the compiler.
$spvF64 = Join-Path $root "examples\shaders\matmul_f64.comp.spv"
$spvC64 = Join-Path $root "examples\shaders\matmul_c64.comp.spv"
if (-not ((Test-Path $spvF64) -and (Test-Path $spvC64))) {
    Write-Host "SKIP ml-gpu -- compute kernels not built (run scripts\build-compute-shaders.ps1)"
} else {
    $gpuExe = Join-Path $tmp "gpu_test.exe"
    Remove-Item $gpuExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tests\ml\gpu_test.zeph $gpuExe 2>&1 | Out-Null
    if (-not (Test-Path $gpuExe)) {
        Check "ml-gpu" $false "gpu_test.zeph did not compile"
    } else {
        $gout = (& $gpuExe 2>&1 | Out-String)
        if ($gout -match "vkCreateInstance" -or $gout -match "no Vulkan") {
            Write-Host "SKIP ml-gpu -- no Vulkan device available"
        } else {
            Check "ml-gpu" ($gout -match "gpu: 279 checks passed") "got tail: $($gout.Trim() -split "`n" | Select-Object -Last 1)"
        }
    }
}

# ---- GPU streams, events and allocator lifetime (A22) ----
# Same skip policy as ml-gpu: an absent Vulkan device is an environment
# fact, not a defect.
if (-not (Test-Path $spvF64)) {
    Write-Host "SKIP ml-gpu-stream -- compute kernels not built"
} else {
    $strExe = Join-Path $tmp "gpu_stream_test.exe"
    Remove-Item $strExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tests\ml\gpu_stream_test.zeph $strExe 2>&1 | Out-Null
    if (-not (Test-Path $strExe)) {
        Check "ml-gpu-stream" $false "gpu_stream_test.zeph did not compile"
    } else {
        $sout = (& $strExe 2>&1 | Out-String)
        if ($sout -match "vkCreateInstance" -or $sout -match "no Vulkan") {
            Write-Host "SKIP ml-gpu-stream -- no Vulkan device available"
        } else {
            Check "ml-gpu-stream" ($sout -match "gpu stream: 23 checks passed") "got tail: $($sout.Trim() -split "`n" | Select-Object -Last 1)"
        }
    }
}

# ---- GPU elementwise, reduction and gather kernels (A23, outputs) ----
if (-not (Test-Path $spvF64)) {
    Write-Host "SKIP ml-gpu-ops -- compute kernels not built"
} else {
    $opsExe = Join-Path $tmp "gpu_ops_test.exe"
    Remove-Item $opsExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tests\ml\gpu_ops_test.zeph $opsExe 2>&1 | Out-Null
    if (-not (Test-Path $opsExe)) {
        Check "ml-gpu-ops" $false "gpu_ops_test.zeph did not compile"
    } else {
        $oout = (& $opsExe 2>&1 | Out-String)
        if ($oout -match "vkCreateInstance" -or $oout -match "no Vulkan") {
            Write-Host "SKIP ml-gpu-ops -- no Vulkan device available"
        } else {
            Check "ml-gpu-ops" ($oout -match "gpu ops: 95 checks over 47 comparisons passed") "got tail: $($oout.Trim() -split "`n" | Select-Object -Last 1)"
        }
    }
}

# ---- GPU gradient and optimizer-update gates (A23) ----
if (-not (Test-Path $spvF64)) {
    Write-Host "SKIP ml-gpu-grad -- compute kernels not built"
} else {
    $grdExe = Join-Path $tmp "gpu_grad_test.exe"
    Remove-Item $grdExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tests\ml\gpu_grad_test.zeph $grdExe 2>&1 | Out-Null
    if (-not (Test-Path $grdExe)) {
        Check "ml-gpu-grad" $false "gpu_grad_test.zeph did not compile"
    } else {
        $gdout = (& $grdExe 2>&1 | Out-String)
        if ($gdout -match "vkCreateInstance" -or $gdout -match "no Vulkan") {
            Write-Host "SKIP ml-gpu-grad -- no Vulkan device available"
        } else {
            Check "ml-gpu-grad" ($gdout -match "gpu grad: 15 checks passed") "got tail: $($gdout.Trim() -split "`n" | Select-Object -Last 1)"
        }
    }
}

# ---- phase parity against the float64 numpy reference (A13) ----
# Skipped rather than failed when numpy is absent: it is a reference-side
# dependency, and its absence is not a defect in the compiler or the port.
$hasNumpy = $false
try {
    & python -c "import numpy" 2>&1 | Out-Null
    $hasNumpy = ($LASTEXITCODE -eq 0)
} catch { $hasNumpy = $false }
if (-not $hasNumpy) {
    Write-Host "SKIP ml-phase-parity -- numpy not available"
} else {
    $dumpExe = Join-Path $tmp "phase_dump.exe"
    $dumpTxt = Join-Path $tmp "phase_dump.txt"
    Remove-Item $dumpExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tests\ml\reference\phase_dump.zeph $dumpExe 2>&1 | Out-Null
    if (-not (Test-Path $dumpExe)) {
        Check "ml-phase-parity" $false "phase_dump.zeph did not compile"
    } else {
        cmd /c "`"$dumpExe`" > `"$dumpTxt`" 2>&1" | Out-Null
        $parity = (& python tests\ml\reference\check_phase.py $dumpTxt | Out-String).Trim()
        $ok = ($LASTEXITCODE -eq 0) -and ($parity -match "148/148 quantities passed")
        Check "ml-phase-parity" $ok "got tail: $($parity -split "`n" | Select-Object -Last 1)"
    }

    $gradExe = Join-Path $tmp "phase_grad_dump.exe"
    $gradTxt = Join-Path $tmp "phase_grad_dump.txt"
    Remove-Item $gradExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tests\ml\reference\phase_grad_dump.zeph $gradExe 2>&1 | Out-Null
    if (-not (Test-Path $gradExe)) {
        Check "ml-phase-grad" $false "phase_grad_dump.zeph did not compile"
    } else {
        cmd /c "`"$gradExe`" > `"$gradTxt`" 2>&1" | Out-Null
        $gr = (& python tests\ml\reference\check_phase_grad.py $gradTxt | Out-String).Trim()
        $gok = ($LASTEXITCODE -eq 0) -and ($gr -match "18/18 quantities agree")
        Check "ml-phase-grad" $gok "got tail: $($gr -split "`n" | Select-Object -Last 1)"
    }

    $optExe = Join-Path $tmp "optim_dump.exe"
    $optTxt = Join-Path $tmp "optim_dump.txt"
    Remove-Item $optExe -ErrorAction SilentlyContinue
    & .\zc.exe --rt tests\ml\reference\optim_dump.zeph $optExe 2>&1 | Out-Null
    if (-not (Test-Path $optExe)) {
        Check "ml-optim-parity" $false "optim_dump.zeph did not compile"
    } else {
        cmd /c "`"$optExe`" > `"$optTxt`" 2>&1" | Out-Null
        $op = (& python tests\ml\reference\check_optim.py $optTxt | Out-String).Trim()
        $ook = ($LASTEXITCODE -eq 0) -and ($op -match "77/77 quantities passed")
        Check "ml-optim-parity" $ook "got tail: $($op -split "`n" | Select-Object -Last 1)"
    }
}

$opNeg = [ordered]@{
    "dtype-mix"  = 'let x = tensorAdd(tensorZeros(DType.F64, [2]), tensorZeros(DType.F32, [2]))'
    "bcast-bad"  = 'let x = tensorAdd(tensorZeros(DType.F64, [2, 3]), tensorZeros(DType.F64, [4, 3]))'
    "mm-inner"   = 'let x = tensorMatmul(tensorZeros(DType.F64, [2, 3]), tensorZeros(DType.F64, [4, 2]))'
    "mm-rank"    = 'let x = tensorMatmul(tensorZeros(DType.F64, [2, 3, 1]), tensorZeros(DType.F64, [3, 2]))'
    "ro-write"   = "let r = tensorZeros(DType.F64, [1, 3])`nlet e = tensorExpand(r, [4, 3])`ntensorSet(e, [0, 0], 1.0)"
    "cast-down"  = 'let x = tensorCast(tensorZeros(DType.C64, [2]), DType.F64)'
    "abs2-real"  = 'let x = tensorAbs2(tensorZeros(DType.F64, [2]))'
    "conj-real"  = 'let x = tensorConjugate(tensorZeros(DType.F64, [2]))'
    "sum-cplx"   = 'let x = tensorSumAll(tensorZeros(DType.C64, [2]))'
    "mean-empty" = 'let x = tensorMeanAll(tensorZeros(DType.F64, [0]))'
    "expi-cplx"  = 'let x = tensorExpImaginary(tensorZeros(DType.C64, [2]), DType.C64)'
    "expand-bad" = 'let x = tensorExpand(tensorZeros(DType.F64, [3]), [4])'
    "int-arith"  = 'let x = tensorAdd(tensorZeros(DType.I64, [2]), tensorZeros(DType.I64, [2]))'
    "sel-dim"     = 'let x = tensorIndexSelect(tensorZeros(DType.F64, [2, 2]), 5, [0])'
    "sel-range"   = 'let x = tensorIndexSelect(tensorZeros(DType.F64, [2, 2]), 0, [2])'
    "sel-neg"     = 'let x = tensorIndexSelect(tensorZeros(DType.F64, [2, 2]), 0, [0 - 1])'
    "copy-dup"    = 'tensorIndexCopy(tensorZeros(DType.F64, [3]), 0, [1, 1], tensorZeros(DType.F64, [2]))'
    "copy-shape"  = 'tensorIndexCopy(tensorZeros(DType.F64, [3, 2]), 0, [0], tensorZeros(DType.F64, [1, 5]))'
    "copy-count"  = 'tensorIndexCopy(tensorZeros(DType.F64, [3]), 0, [0, 1], tensorZeros(DType.F64, [3]))'
    "copy-ro"     = "let r = tensorZeros(DType.F64, [1, 3])`nlet e = tensorExpand(r, [4, 3])`ntensorIndexCopy(e, 0, [0], tensorZeros(DType.F64, [1, 3]))"
    "cat-dim"     = 'let x = tensorConcat(tensorZeros(DType.F64, [2, 2]), tensorZeros(DType.F64, [2, 2]), 9)'
    "cat-shape"   = 'let x = tensorConcat(tensorZeros(DType.F64, [2, 2]), tensorZeros(DType.F64, [3, 2]), 1)'
    "cat-dtype"   = 'let x = tensorConcat(tensorZeros(DType.F64, [2]), tensorZeros(DType.F32, [2]), 0)'
    "map-cplx"    = 'let x = tensorTanh(tensorZeros(DType.C64, [2]))'
    "map-int"     = 'let x = tensorTanh(tensorZeros(DType.I64, [2]))'
    "roll-dim"    = 'let x = tensorRoll(tensorZeros(DType.F64, [2]), 3, 1)'
}
foreach ($nm in $opNeg.Keys) {
    $src = "import `"ml/ops.zeph`"`n" + $opNeg[$nm]
    $f = Join-Path $tmp "opneg_$nm.zeph"
    $x = Join-Path $tmp "opneg_$nm.exe"
    Set-Content -Path $f -Value $src -Encoding ascii
    Remove-Item $x -ErrorAction SilentlyContinue
    & .\zc.exe --rt $f $x 2>&1 | Out-Null
    if (-not (Test-Path $x)) { Check "ops-reject:$nm" $false "did not compile"; continue }
    $o = (cmd /c "`"$x`" 2>&1" | Out-String).Trim()
    Check "ops-reject:$nm" ($LASTEXITCODE -ne 0 -and $o -match "panic:") "expected panic, got($LASTEXITCODE): $o"
}
