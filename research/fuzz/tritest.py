#!/usr/bin/env python3
"""Three-way differential test: baseline, -O2 and the Python reference
(left-to-right evaluation) for programs from genpair.py. It reports which side
departs from the reference, separating miscompiles from evaluation-order
divergence.
Usage: tritest.py FIRST_SEED COUNT [workers]
"""
import collections, concurrent.futures, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ZC = os.environ.get('ZC_LINUX', '/tmp/zr/root/zc')

def one(seed):
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([sys.executable, str(HERE / 'genpair.py'), str(seed), d], check=True)
        ref = subprocess.run([sys.executable, os.path.join(d, 'p.py')], capture_output=True, text=True, timeout=60)
        if ref.returncode: return seed, 'reference-error', ref.stderr[-200:]
        outs = []
        for flags in ([], ['-O2']):
            exe = os.path.join(d, 'o' if flags else 'b')
            c = subprocess.run([ZC, '--linux', '--rt', *flags, os.path.join(d, 'p.zeph'), exe], capture_output=True, text=True, timeout=120)
            if c.returncode: return seed, 'compile-fail', (c.stdout + c.stderr)[-200:]
            os.chmod(exe, 0o755)
            outs.append(subprocess.run([exe], capture_output=True, text=True, timeout=30).stdout.strip())
        r = ref.stdout.strip(); b, o = outs
        kind = 'agree' if b == o == r else 'O2 differs' if b == r else 'baseline differs' if o == r else 'both differ from reference' if b == o else 'all three differ'
        if kind != 'agree':
            keep = HERE / 'failures'; keep.mkdir(exist_ok=True)
            for ext in ('zeph', 'py'):
                (keep / f'pair-seed{seed}.{ext}').write_text(Path(d, f'p.{ext}').read_text())
        return seed, kind, ''

def main():
    first, count = int(sys.argv[1]), int(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    tally = collections.Counter()
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        for seed, kind, info in pool.map(one, range(first, first + count)):
            tally[kind] += 1
            if kind != 'agree': print(seed, kind, info, flush=True)
    print(dict(tally))

if __name__ == '__main__':
    main()
