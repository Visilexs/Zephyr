# The M7 sweep driver.
#
# Nothing here decides anything. Every budget, learning rate and seed is a
# constant inside tools\m7_run.zeph and is copied into each run record; this
# script only enumerates the runs and calls that binary once per run.
#
# It is resumable by construction: a run whose record already exists is
# skipped, so a sweep that dies at hour nine restarts at hour nine. That is
# also why each run is its own process rather than one long-lived one.
#
# The protocol it implements, which is declared here and not changed later:
#
#   Stage 1, tuning. Seed 1 only, all three learning rates, every family,
#   both tasks. Selection is by validation NLL. Equal tuning budget for every
#   family, which is the one thing the baselines document insists on holding
#   equal.
#   Stage 2, seeds. The learning rate chosen in stage 1 is rerun at seeds 2
#   and 3. Seed 1 is already done and is not rerun.
#
# Usage:
#   .\scripts\m7-sweep.ps1                 run everything still missing
#   .\scripts\m7-sweep.ps1 -Smoke          validation only, never reads the
#                                          frozen composition/length splits
#   .\scripts\m7-sweep.ps1 -Families phase,gru_state -Tasks a
#   .\scripts\m7-sweep.ps1 -WhatIf         list what would run, and stop
param(
    [string[]]$Families = @("phase", "gru_state", "gru_param", "gru_quad",
                            "incoherent", "realrot", "transformer",
                            "k0", "k1", "k4", "k8"),
    [string[]]$Tasks = @("a", "b"),
    [int[]]$Seeds = @(1, 2, 3),
    [int[]]$LrIndices = @(0, 1, 2),
    [switch]$Smoke,
    [switch]$WhatIf
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root

$runs = Join-Path $root "runs\m7"
New-Item -ItemType Directory -Force $runs | Out-Null

if (-not (Test-Path (Join-Path $root "data\m7\manifest.json"))) {
    Write-Host "data\m7 is missing. Run: python tools\ml_reference\freeze_datasets.py" -ForegroundColor Red
    exit 1
}

$exe = Join-Path $root "m7_run.exe"
Write-Host "building the runner..."
& (Join-Path $root "zc.exe") --rt (Join-Path $root "tools\m7_run.zeph") $exe
if (-not (Test-Path $exe)) { Write-Host "m7_run.zeph did not compile" -ForegroundColor Red; exit 1 }

# ---- stage 1: the learning-rate search, seed 1 -------------------------------
$plan = @()
foreach ($task in $Tasks) {
    foreach ($fam in $Families) {
        foreach ($lr in $LrIndices) {
            $plan += [pscustomobject]@{ fam = $fam; task = $task; seed = 1; lr = $lr; stage = 1 }
        }
    }
}

function Record-Path($r) {
    $tag = "$($r.fam)-$($r.task)-s$($r.seed)-lr$($r.lr)"
    if ($Smoke) { $tag = "$tag-smoke" }
    return (Join-Path $runs "$tag.json")
}

function Invoke-Run($r) {
    $out = Record-Path $r
    if (Test-Path $out) { Write-Host "skip   $($r.fam) $($r.task) seed $($r.seed) lr $($r.lr) -- already recorded"; return }
    if ($WhatIf) { Write-Host "would  $($r.fam) $($r.task) seed $($r.seed) lr $($r.lr)"; return }
    Write-Host "run    $($r.fam) $($r.task) seed $($r.seed) lr $($r.lr)"
    $started = Get-Date
    if ($Smoke) {
        & $exe $r.fam $r.task $r.seed $r.lr $out "smoke"
    } else {
        & $exe $r.fam $r.task $r.seed $r.lr $out
    }
    if ($LASTEXITCODE -ne 0) {
        # A failed run is a result, not an excuse to stop: the protocol asks
        # for failure cases to be available. Record it and carry on.
        Write-Host "FAILED $($r.fam) $($r.task) seed $($r.seed) lr $($r.lr) (exit $LASTEXITCODE)" -ForegroundColor Red
        $err = @{ run_id = "$($r.fam)-$($r.task)-s$($r.seed)-lr$($r.lr)"; family = $r.fam; task = $r.task
                  seed = $r.seed; lr_index = $r.lr; status = "failed"; error = "exit $LASTEXITCODE" }
        ($err | ConvertTo-Json) | Set-Content -Path $out -Encoding utf8
    }
    Write-Host ("       {0:n1} minutes" -f ((Get-Date) - $started).TotalMinutes)
}

foreach ($r in $plan) { Invoke-Run $r }

if ($WhatIf) {
    Write-Host ""
    Write-Host "stage 1 is $($plan.Count) runs; stage 2 adds up to $($Families.Count * $Tasks.Count * ($Seeds.Count - 1))"
    exit 0
}

# ---- stage 2: the remaining seeds at the selected learning rate ----------------
# The rate is chosen by validation NLL, read back out of the stage-1 records.
# Reading it from the records rather than remembering it means the selection
# is auditable after the fact.
foreach ($task in $Tasks) {
    foreach ($fam in $Families) {
        $best = $null
        $bestNll = [double]::MaxValue
        foreach ($lr in $LrIndices) {
            $f = Record-Path ([pscustomobject]@{ fam = $fam; task = $task; seed = 1; lr = $lr })
            if (-not (Test-Path $f)) { continue }
            $j = Get-Content $f -Raw | ConvertFrom-Json
            if ($j.status -ne "completed") { continue }
            if ($j.validation_nll -lt $bestNll) { $bestNll = $j.validation_nll; $best = $lr }
        }
        if ($null -eq $best) {
            Write-Host "no completed stage-1 run for $fam on task $task; skipping its extra seeds" -ForegroundColor Yellow
            continue
        }
        Write-Host "$fam task ${task}: selected lr index $best by validation nll $bestNll"
        foreach ($seed in $Seeds) {
            if ($seed -eq 1) { continue }
            Invoke-Run ([pscustomobject]@{ fam = $fam; task = $task; seed = $seed; lr = $best; stage = 2 })
        }
    }
}

Write-Host ""
Write-Host "sweep complete. Records are in runs\m7."
Write-Host "Aggregate them with tools\ml_reference\m7_report.py once every run has a record."
