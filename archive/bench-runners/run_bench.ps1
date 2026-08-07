# Benchmark Zephyr against C and C++ (same program: fib(32) + 100M-iteration loop).
# Measures compile time and best-of-3 runtime for each.
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot
Set-Location $root

function TimeIt($script) {
    (Measure-Command $script).TotalMilliseconds
}

function BestRun($exe) {
    $out = (& $exe) -join "|"
    $best = [double]::MaxValue
    for ($i = 0; $i -lt 3; $i++) {
        $t = TimeIt { & $exe | Out-Null }
        if ($t -lt $best) { $best = $t }
    }
    return @{ ms = [math]::Round($best); out = $out }
}

$results = @()

# Zephyr
$c = TimeIt { .\bootstrap\zephyr.exe build examples\bench.zeph -o bench\bench_zephyr.exe | Out-Null }
$r = BestRun ".\bench\bench_zephyr.exe"
$results += [pscustomobject]@{ Lang = "Zephyr"; Compile_ms = [math]::Round($c); Run_ms = $r.ms; Out = $r.out }

# C -O2 / -O0
$c = TimeIt { gcc -O2 bench\bench.c -o bench\bench_c2.exe }
$r = BestRun ".\bench\bench_c2.exe"
$results += [pscustomobject]@{ Lang = "C (gcc -O2)"; Compile_ms = [math]::Round($c); Run_ms = $r.ms; Out = $r.out }

$c = TimeIt { gcc -O0 bench\bench.c -o bench\bench_c0.exe }
$r = BestRun ".\bench\bench_c0.exe"
$results += [pscustomobject]@{ Lang = "C (gcc -O0)"; Compile_ms = [math]::Round($c); Run_ms = $r.ms; Out = $r.out }

# C++ -O2
$c = TimeIt { g++ -O2 bench\bench.cpp -o bench\bench_cpp.exe }
$r = BestRun ".\bench\bench_cpp.exe"
$results += [pscustomobject]@{ Lang = "C++ (g++ -O2)"; Compile_ms = [math]::Round($c); Run_ms = $r.ms; Out = $r.out }

# Rust (optional, if installed)
$rustc = Get-Command rustc -ErrorAction SilentlyContinue
if ($rustc) {
    $c = TimeIt { rustc -O bench\bench.rs -o bench\bench_rs.exe }
    $r = BestRun ".\bench\bench_rs.exe"
    $results += [pscustomobject]@{ Lang = "Rust (rustc -O)"; Compile_ms = [math]::Round($c); Run_ms = $r.ms; Out = $r.out }
}

$results | Format-Table Lang, Compile_ms, Run_ms, Out -AutoSize
Remove-Item bench\bench_*.exe -Confirm:$false
