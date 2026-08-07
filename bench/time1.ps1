# Accurate best-of-N timer for a single exe+arg.  Usage: time1.ps1 exe arg [runs]
$exe = $args[0]; $arg = $args[1]; $runs = if ($args.Count -ge 3) { [int]$args[2] } else { 7 }
Add-Type -TypeDefinition @"
using System; using System.Diagnostics;
public class T1 { public static double Run(string e,string a){ var p=new Process();
 p.StartInfo.FileName=e; p.StartInfo.Arguments=a; p.StartInfo.UseShellExecute=false;
 p.StartInfo.RedirectStandardOutput=true; var sw=Stopwatch.StartNew(); p.Start();
 p.StandardOutput.ReadToEnd(); p.WaitForExit(); sw.Stop(); return sw.Elapsed.TotalMilliseconds; } }
"@
$best = [double]::MaxValue
for ($i = 0; $i -lt $runs; $i++) { $t = [T1]::Run($exe, "$arg"); if ($t -lt $best) { $best = $t } }
"{0:N0}" -f $best
