#!/usr/bin/env python3
"""Differential testing: compile random programs (research/fuzz/genprog.py) at
baseline and -O2 with the same zc and compare their outputs. A difference, a
crash or a compile failure in one mode only is reported with its seed.
Usage: [GEN=genref.py] difftest.py FIRST_SEED COUNT [workers]
"""
import concurrent.futures, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZC = os.environ.get('ZC_LINUX', '/tmp/zr/root/zc')
GENERATOR = os.environ.get('GEN', 'genprog.py')     # or genref.py

def one(seed):
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / 'p.zeph'
        src.write_text(subprocess.run([sys.executable, str(HERE / GENERATOR), str(seed)], capture_output=True, text=True, check=True).stdout)
        results = []
        for flags in ([], ['-O2']):
            exe = Path(d) / ('o2' if flags else 'base')
            c = subprocess.run([ZC, '--linux', '--rt', *flags, str(src), str(exe)], capture_output=True, text=True, timeout=120)
            if c.returncode:
                results.append(('compile-fail', (c.stdout + c.stderr)[-200:])); continue
            os.chmod(exe, 0o755)
            try:
                r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=30)
                results.append((r.returncode, r.stdout.strip()[-200:]))
            except subprocess.TimeoutExpired:
                results.append(('timeout', ''))
        if results[0] != results[1]:
            keep = HERE / 'failures'; keep.mkdir(exist_ok=True)
            (keep / f'{GENERATOR[:-3]}-seed{seed}.zeph').write_text(src.read_text())
            return seed, results
        return None

def main():
    first, count = int(sys.argv[1]), int(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    bad = 0
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        for r in pool.map(one, range(first, first + count)):
            if r:
                bad += 1
                print('MISMATCH seed', r[0], 'baseline:', r[1][0], ' -O2:', r[1][1], flush=True)
    print(f'{count} programs, {bad} mismatches')

if __name__ == '__main__':
    main()
