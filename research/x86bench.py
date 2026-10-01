#!/usr/bin/env python3
"""x86-64 Linux benchmark of the 19 original workloads: C (gcc -O2), Zephyr, Zephyr -O2.

Research tool for GOAL.md. Needs a Linux-native zc built by research/setup.sh,
and the original benchmark sources (C and Zephyr) from Git revision 398aadd.
Usage: python3 research/x86bench.py [--only fib,matmul] [--runs 5] [--out results.json]
"""
import argparse, json, os, statistics, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZC = Path(os.environ.get('ZC_LINUX', '/tmp/zr/root/zc'))

SUITE = [  # name, argument, extra gcc flags (same table as the original bench/bench.py)
    ("fib", "43", ""), ("matmul", "1100", ""), ("mandel", "1700", "-ffp-contract=off"),
    ("sort", "6000000", ""), ("strings", "4000000", ""), ("hashmap", "32000000", ""),
    ("cube", "80000", "-ffp-contract=off -lm"), ("pi", "40000", ""),
    ("liquid", "100", "-ffp-contract=off -lm"), ("shapes", "600000", "-ffp-contract=off -lm"),
    ("closures", "600000", ""), ("wordfreq", "14000000", ""), ("nbody", "200", "-ffp-contract=off -lm"),
    ("lexer", "2500000", ""), ("vectors", "35000", "-ffp-contract=off"), ("dispatch", "", ""),
    ("records", "", ""), ("strbuild", "", ""), ("bintrees", "", ""),
]

def sources(work):
    out = work / 'src'; out.mkdir()
    tar = subprocess.run(['git', '-C', str(ROOT), 'archive', '398aadd', 'bench'], check=True, capture_output=True).stdout
    subprocess.run(['tar', '-x', '-C', str(out)], input=tar, check=True)
    return out / 'bench'

def build(kind, name, flags, src, work):
    exe = work / f'{name}.{kind}'
    start = time.perf_counter()
    if kind == 'c':
        cmd = ['gcc', '-O2', '-fwrapv', *flags.split(), str(src / f'{name}.c'), '-o', str(exe)]
        if '-lm' in cmd: cmd.remove('-lm'); cmd.append('-lm')
    else:
        cmd = [str(ZC), '--linux', '--rt', *(['-O2'] if kind == 'zO2' else []), str(src / f'{name}.zeph'), str(exe)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ZC.parent)
    if r.returncode: return None, f'build failed: {r.stdout[-300:]}{r.stderr[-300:]}'
    os.chmod(exe, 0o755)
    return exe, time.perf_counter() - start

def run(exe, arg, timeout):
    start = time.perf_counter()
    r = subprocess.run(['taskset', '-c', '1', str(exe), *([arg] if arg else [])], capture_output=True, text=True, timeout=timeout)
    return time.perf_counter() - start, r.stdout.strip(), r.returncode

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--only'); p.add_argument('--runs', type=int, default=5)
    p.add_argument('--kinds', default='c,z,zO2'); p.add_argument('--timeout', type=float, default=120)
    p.add_argument('--out', default=str(ROOT / 'research' / 'results' / 'x86-linux.json'))
    a = p.parse_args()
    kinds = a.kinds.split(',')
    suite = [s for s in SUITE if not a.only or s[0] in a.only.split(',')]
    results = {}
    with tempfile.TemporaryDirectory(prefix='x86bench-') as d:
        work = Path(d); src = sources(work)
        for name, arg, flags in suite:
            row = results[name] = {}
            for kind in kinds:
                exe, info = build(kind, name, flags, src, work)
                if exe is None: row[kind] = {'error': info}; continue
                times, outs = [], set()
                try:
                    for i in range(a.runs):
                        t, out, code = run(exe, arg, a.timeout)
                        times.append(t); outs.add((out, code))
                        if sum(times) > 30 and i >= 2: break
                except subprocess.TimeoutExpired:
                    row[kind] = {'error': 'timeout', 'build_s': info}; continue
                row[kind] = {'median_s': statistics.median(times), 'times': times, 'build_s': info, 'output': sorted(outs)}
            ok = len({str(v.get('output')) for v in row.values() if 'output' in v}) == 1
            row['checksums_match'] = ok
            c = row.get('c', {}).get('median_s')
            cells = [f"{k}={row[k]['median_s']*1000:.0f}ms" if 'median_s' in row.get(k, {}) else f"{k}={row.get(k, {}).get('error')}" for k in kinds]
            ratio = f" O2/C={row['zO2']['median_s']/c:.2f}" if c and 'median_s' in row.get('zO2', {}) else ''
            print(name, *cells, ratio, 'ok' if ok else 'CHECKSUM MISMATCH', flush=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({'machine': subprocess.run(['sh', '-c', "grep -m1 'model name' /proc/cpuinfo"], capture_output=True, text=True).stdout.strip(),
                                       'zc': str(ZC), 'results': results}, indent=1))
    ratios = [r['zO2']['median_s'] / r['c']['median_s'] for r in results.values() if 'median_s' in r.get('zO2', {}) and 'median_s' in r.get('c', {}) and r['checksums_match']]
    if ratios: print(f'geomean -O2/C over {len(ratios)}: {statistics.geometric_mean(ratios):.3f}')

if __name__ == '__main__':
    main()
