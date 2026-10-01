#!/usr/bin/env python3
"""Profile every -O2 workload and split its time into cost categories.

Needs the map-writing zc from research/setup.sh's notes (ZC_MAP, default
/tmp/zr/root2/zc) and research/sampler.c built as /tmp/zr/sampler.
Usage: profile_all.py [--only a,b] [--out research/results/profile-O2.json]
"""
import argparse, bisect, collections, json, os, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZC = Path(os.environ.get('ZC_MAP', '/tmp/zr/root2/zc'))
SAMPLER = os.environ.get('SAMPLER', '/tmp/zr/sampler')
ARGS = {"fib": "43", "matmul": "1100", "mandel": "1700", "sort": "6000000", "strings": "4000000", "hashmap": "32000000",
        "cube": "80000", "pi": "40000", "liquid": "100", "shapes": "600000", "closures": "600000", "wordfreq": "14000000",
        "nbody": "200", "lexer": "2500000", "vectors": "35000", "dispatch": "", "records": "", "strbuild": "", "bintrees": ""}

def category(name):
    n = name.lower()
    if any(k in n for k in ('retain', 'release', 'assignreference', 'frameslots', 'referencecount')): return 'refcount'
    if any(k in n for k in ('allocate', 'freeblock', 'growheap', 'largebin', 'bitmap', 'takefree')): return 'alloc'
    if 'collectgarbage' in n or 'mark' in n and n.startswith('runtime'): return 'gc'
    if any(k in n for k in ('string', 'substring', 'concatenate', 'interpolation', 'builder', 'format', 'join', 'split', 'char')): return 'string runtime'
    if 'map' in n and n.startswith('runtime'): return 'map runtime'
    if 'list' in n and n.startswith('runtime'): return 'list runtime'
    if n.startswith('runtime') or n.startswith('linux') or n.startswith('kernel32'): return 'other runtime'
    # -O2 code keeps lm_ names for whole functions and uses zopt_regionN for
    # outlined loops, so both prefixes are user code (use --opt-report for tiers).
    if n.startswith('zopt_') or n.startswith('lm_'): return 'user code'
    return 'other'

def main():
    p = argparse.ArgumentParser(); p.add_argument('--only'); p.add_argument('--out', default=str(ROOT / 'research/results/profile-O2.json'))
    a = p.parse_args()
    names = [n for n in ARGS if not a.only or n in a.only.split(',')]
    tar = subprocess.run(['git', '-C', str(ROOT), 'archive', '398aadd', 'bench'], check=True, capture_output=True).stdout
    results = {}
    with tempfile.TemporaryDirectory() as d:
        work = Path(d); subprocess.run(['tar', '-x', '-C', d], input=tar, check=True)
        for name in names:
            exe = work / name
            subprocess.run([str(ZC), '--linux', '--rt', '-O2', '--map', str(work / 'bench' / f'{name}.zeph'), str(exe)], check=True, cwd=ZC.parent, capture_output=True)
            os.chmod(exe, 0o755)
            samples = work / f'{name}.samples'
            subprocess.run(['taskset', '-c', '2', SAMPLER, str(samples), '300', str(exe), *([ARGS[name]] if ARGS[name] else [])], check=True, capture_output=True)
            syms = sorted((0x400000 + int(x), n) for x, n in (l.split(' ', 1) for l in open(str(exe) + '.map').read().splitlines() if l))
            addrs = [s[0] for s in syms]
            cats, funcs, total = collections.Counter(), collections.Counter(), 0
            for line in open(samples):
                f = line.split()
                if not f: continue
                i = bisect.bisect_right(addrs, int(f[0], 16)) - 1
                fn = syms[i][1] if i >= 0 else '?'
                funcs[fn] += 1; cats[category(fn)] += 1; total += 1
            results[name] = {'samples': total, 'categories': {k: round(100 * v / total, 1) for k, v in cats.most_common()},
                             'top': [(k, round(100 * v / total, 1)) for k, v in funcs.most_common(6)]}
            print(name, results[name]['categories'], flush=True)
            print('    top:', results[name]['top'], flush=True)
    Path(a.out).write_text(json.dumps(results, indent=1))

if __name__ == '__main__':
    main()
