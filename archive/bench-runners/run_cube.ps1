# Standardized wireframe-cube render benchmark: Zephyr vs C vs Rust.
# Identical algorithm (spin a hollow cube, Bresenham the 12 edges into a
# framebuffer, fold the buffer into a checksum), same deterministic spin, so the
# checksum is identical across all three. Reports compile time, best/median
# runtime over several runs, and peak working-set memory.
# The C build uses -ffp-contract=off so no FMA fusion perturbs the checksum.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root
$F = if ($args.Count -ge 1) { [int]$args[0] } else { 6000 }
$runs = 5

Add-Type -TypeDefinition @"
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
public class CU {
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

# ---- compile ----
$compile = @{}
$compile["Zephyr"]  = (Measure-Command { & .\zc.exe --rt bench\cube.zeph "$tmp\cb_l.exe" | Out-Null }).TotalMilliseconds
$compile["C"]     = (Measure-Command { gcc -O2 -ffp-contract=off bench\cube.c -o "$tmp\cb_c.exe" -lm }).TotalMilliseconds
$haveRust = Test-Path $rustc
if ($haveRust) { $compile["Rust"] = (Measure-Command { & $rustc -O bench\cube.rs -o "$tmp\cb_r.exe" }).TotalMilliseconds }

$exe = @{ "Zephyr" = "$tmp\cb_l.exe"; "C" = "$tmp\cb_c.exe"; "Rust" = "$tmp\cb_r.exe" }
$langs = if ($haveRust) { @("C", "Rust", "Zephyr") } else { @("C", "Zephyr") }

# ---- correctness ----
$sums = @{}
foreach ($l in $langs) { $o = ""; $pk = [uint64]0; [CU]::RunOnce($exe[$l], "$F", [ref]$o, [ref]$pk) | Out-Null; $sums[$l] = $o }
$ok = ($sums.Values | Sort-Object -Unique).Count -eq 1
Write-Host "checksum (frames=$F): $($sums['C'])  identical across languages: $ok"
if (-not $ok) { $sums.GetEnumerator() | ForEach-Object { Write-Host "  $($_.Key): $($_.Value)" }; exit 1 }

# ---- timing + memory ----
$rows = @()
foreach ($l in $langs) {
    $times = @(); $peak = [uint64]0
    for ($i = 0; $i -lt $runs; $i++) {
        $o = ""; $pk = [uint64]0
        $t = [CU]::RunOnce($exe[$l], "$F", [ref]$o, [ref]$pk)
        $times += $t; if ($pk -gt $peak) { $peak = $pk }
    }
    $ts = $times | Sort-Object
    $rows += [pscustomobject]@{
        Lang       = $l
        Compile_ms = [math]::Round($compile[$l])
        Best_ms    = [math]::Round($ts[0])
        Median_ms  = [math]::Round($ts[[int]($runs / 2)])
        PeakMem_KB = $peak
    }
}
"`nWireframe cube, {0} frames (100x100, 12 edges), best of {1} runs:" -f $F, $runs | Write-Host
$rows | Format-Table Lang, Compile_ms, Best_ms, Median_ms, PeakMem_KB -AutoSize
Remove-Item "$tmp\cb_l.exe","$tmp\cb_c.exe","$tmp\cb_r.exe" -ErrorAction SilentlyContinue
