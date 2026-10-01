#!/usr/bin/env python3
"""Instruction-level hotspots of one function, from research/sampler.c output.
Disassembles the raw ELF image (zc writes no section headers) with objdump.
Usage: hotspots.py program program.map samples.txt [function] [min-permille]
"""
import bisect, collections, subprocess, sys

def main():
    exe, mapfile, samples = sys.argv[1:4]
    want = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != '-' else None
    minimum = int(sys.argv[5]) if len(sys.argv) > 5 else 5
    syms = sorted((0x400000 + int(a), n) for a, n in (l.split(' ', 1) for l in open(mapfile).read().splitlines() if l))
    addrs = [a for a, _ in syms]
    hits, total = collections.Counter(), 0
    for line in open(samples):
        f = line.split()
        if f: hits[int(f[0], 16)] += 1; total += 1
    per = collections.Counter()
    for a, n in hits.items():
        i = bisect.bisect_right(addrs, a) - 1
        if i >= 0: per[i] += n
    index = next(i for i, (_, n) in enumerate(syms) if n == want) if want else per.most_common(1)[0][0]
    lo = syms[index][0]
    hi = syms[index + 1][0] if index + 1 < len(syms) else lo + 65536
    print(f'{syms[index][1]}: {100 * per[index] / total:.1f}% of {total} samples, {hi - lo} bytes')
    dis = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386:x86-64', '-M', 'intel', '--adjust-vma=0x400000',
                          f'--start-address={lo}', f'--stop-address={hi}', exe], capture_output=True, text=True).stdout
    for line in dis.splitlines():
        head = line.strip().split(':', 1)
        try: a = int(head[0], 16)
        except ValueError: continue
        n = hits.get(a, 0)
        mark = f'{100 * n / total:5.1f}%' if n * 1000 >= minimum * total else '      '
        if n * 1000 >= minimum * total or '--all' in sys.argv:
            print(f'{mark}  {line.strip()[:120]}')

if __name__ == '__main__':
    main()
