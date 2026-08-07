# Zephyr benchmark suite: one harness across the major workload areas, each
# compared head-to-head against gcc -O2 and rustc -O. Every benchmark is the
# same algorithm in all three languages and prints one checksum line, which the
# harness verifies is byte-identical before it trusts any timing.
#
# Per benchmark it reports compile time, best/median wall-clock over N runs, and
# peak working-set memory. Usage:  powershell -File bench\run_suite.ps1 [runs]
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root
$runs = if ($args.Count -ge 1) { [int]$args[0] } else { 5 }

Add-Type -TypeDefinition @"
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
public class Proc {
    [StructLayout(LayoutKind.Sequential)]
    public struct PMC { public uint cb; public uint pf; public UIntPtr peak; public UIntPtr ws; public UIntPtr qpp; public UIntPtr qpu; public UIntPtr qnp; public UIntPtr qnu; public UIntPtr pfu; public UIntPtr ppf; }
    [DllImport("psapi.dll", SetLastError=true)] static extern bool GetProcessMemoryInfo(IntPtr h, out PMC c, uint s);
    public static double RunOnce(string exe, string arg, out string output, out ulong peakKB) {
        var p = new Process();
        p.StartInfo.FileName = exe; p.StartInfo.Arguments = arg;
        p.StartInfo.UseShellExecute = false; p.StartInfo.RedirectStandardOutput = true;
        var sw = Stopwatch.StartNew();
        p.Start(); output = p.StandardOutput.ReadToEnd().Trim(); p.WaitForExit();
        sw.Stop();
        PMC pmc; GetProcessMemoryInfo(p.Handle, out pmc, (uint)Marshal.SizeOf(typeof(PMC)));
        peakKB = (ulong)pmc.peak / 1024;
        return sw.Elapsed.TotalMilliseconds;
    }
}
"@

$tmp = $env:TEMP
$rustc = "$env:USERPROFILE\.cargo\bin\rustc.exe"
if (-not (Test-Path $rustc)) { $rc = Get-Command rustc -ErrorAction SilentlyContinue; if ($rc) { $rustc = $rc.Source } }
$haveRust = Test-Path $rustc

# name | area | workload arg | extra gcc flags
$suite = @(
    @{ name = "fib";     area = "recursion";       arg = "35";      gcc = "" }
    @{ name = "matmul";  area = "integer SIMD";    arg = "640";     gcc = "" }
    @{ name = "mandel";  area = "float compute";   arg = "900";     gcc = "-ffp-contract=off" }
    @{ name = "sort";    area = "sorting";         arg = "3000000"; gcc = "" }
    @{ name = "strings"; area = "alloc / GC";      arg = "2000000"; gcc = "" }
    @{ name = "hashmap"; area = "hash map";        arg = "2000000"; gcc = "" }
    @{ name = "cube";    area = "rasterization";   arg = "1500";    gcc = "-ffp-contract=off -lm" }
    @{ name = "pi";      area = "bignum";          arg = "20000";   gcc = "" }
    @{ name = "liquid";  area = "fluid / neighbours"; arg = "400";  gcc = "-ffp-contract=off -lm" }
)

function Median($xs) { $s = $xs | Sort-Object; return $s[[int]($s.Count / 2)] }

$summary = @()
foreach ($b in $suite) {
    $n = $b.name
    $ez = "$tmp\su_${n}_z.exe"; $ec = "$tmp\su_${n}_c.exe"; $er = "$tmp\su_${n}_r.exe"
    $exe = @{}

    # ---- compile ----
    $cz = (Measure-Command { & .\zc.exe --rt "bench\$n.zeph" $ez | Out-Null }).TotalMilliseconds
    if (-not (Test-Path $ez)) { Write-Host "SKIP $n : zeph compile failed"; continue }
    $exe["Zephyr"] = $ez

    $gccArgs = @("-O2") + ($b.gcc -split ' ' | Where-Object { $_ }) + @("bench\$n.c", "-o", $ec)
    $cc = (Measure-Command { & gcc @gccArgs }).TotalMilliseconds
    $exe["C"] = $ec

    $cr = $null
    if ($haveRust) {
        $cr = (Measure-Command { & $rustc -O "bench\$n.rs" -o $er 2>$null }).TotalMilliseconds
        $exe["Rust"] = $er
    }

    $langs = @("C"); if ($haveRust) { $langs += "Rust" }; $langs += "Zephyr"
    $comp = @{ "Zephyr" = $cz; "C" = $cc; "Rust" = $cr }

    # ---- correctness: checksums must be identical ----
    $sums = @{}
    foreach ($l in $langs) { $o = ""; $pk = [uint64]0; [Proc]::RunOnce($exe[$l], $b.arg, [ref]$o, [ref]$pk) | Out-Null; $sums[$l] = $o }
    $ok = ($sums.Values | Sort-Object -Unique).Count -eq 1

    # ---- timing + memory ----
    $rows = @()
    foreach ($l in $langs) {
        $times = @(); $peak = [uint64]0
        for ($i = 0; $i -lt $runs; $i++) {
            $o = ""; $pk = [uint64]0
            $times += [Proc]::RunOnce($exe[$l], $b.arg, [ref]$o, [ref]$pk)
            if ($pk -gt $peak) { $peak = $pk }
        }
        $best = ($times | Sort-Object)[0]
        $rows += [pscustomobject]@{
            Lang = $l; Compile_ms = [math]::Round($comp[$l]); Best_ms = [math]::Round($best)
            Median_ms = [math]::Round((Median $times)); PeakMem_KB = $peak
        }
    }

    $status = if ($ok) { "IDENTICAL" } else { "MISMATCH!" }
    "`n== {0}  ({1})   arg={2}   checksum {3}  [{4}]" -f $n, $b.area, $b.arg, $sums["C"], $status | Write-Host
    if (-not $ok) { $sums.GetEnumerator() | ForEach-Object { Write-Host ("   {0}: {1}" -f $_.Key, $_.Value) } }
    $rows | Format-Table Lang, Compile_ms, Best_ms, Median_ms, PeakMem_KB -AutoSize | Out-String | Write-Host

    $z = $rows | Where-Object { $_.Lang -eq "Zephyr" }
    $c = $rows | Where-Object { $_.Lang -eq "C" }
    $r = $rows | Where-Object { $_.Lang -eq "Rust" }
    $rust_ms = if ($r) { $r.Best_ms } else { "-" }
    $rust_kb = if ($r) { $r.PeakMem_KB } else { "-" }
    $zc = if ($c.Best_ms) { [math]::Round($z.Best_ms / $c.Best_ms, 2) } else { "-" }
    $zr = if ($r -and $r.Best_ms) { [math]::Round($z.Best_ms / $r.Best_ms, 2) } else { "-" }
    $csum = if ($ok) { "ok" } else { "MISMATCH" }
    $summary += [pscustomobject]@{
        Area = $b.area
        Zephyr_ms = $z.Best_ms; C_ms = $c.Best_ms; Rust_ms = $rust_ms
        "Z/C" = $zc; "Z/Rust" = $zr
        Zephyr_KB = $z.PeakMem_KB; C_KB = $c.PeakMem_KB; Rust_KB = $rust_kb
        Checksum = $csum
    }
    Remove-Item $ez, $ec, $er -ErrorAction SilentlyContinue
}

Write-Host "`n================ SUMMARY (best-of-$runs ms; Z/C and Z/Rust < 1.0 = Zephyr faster) ================"
$summary | Format-Table Area, Zephyr_ms, C_ms, Rust_ms, "Z/C", "Z/Rust", Zephyr_KB, C_KB, Rust_KB, Checksum -AutoSize
