#!/usr/bin/env python3
"""Self and inclusive time per function from research/sampler.c output and a zc --map file.
Usage: samplereport.py samples.txt program.map [top]
"""
import bisect, collections, sys

def main():
    samples, mapfile = sys.argv[1], sys.argv[2]
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    syms = sorted((0x400000 + int(a), n) for a, n in (l.split(' ', 1) for l in open(mapfile).read().splitlines() if l))
    addrs = [a for a, _ in syms]
    def name(a):
        i = bisect.bisect_right(addrs, a) - 1
        return syms[i][1] if i >= 0 and a < 0x400000 + 64 * 1024 * 1024 else '?'
    self_t, incl = collections.Counter(), collections.Counter()
    n = 0
    for line in open(samples):
        frames = [int(x, 16) for x in line.split()]
        if not frames: continue
        n += 1
        names = [name(frames[0])] + [name(a - 1) for a in frames[1:]]
        self_t[names[0]] += 1
        for x in set(names): incl[x] += 1
    print(f'{n} samples')
    print('--- self'); [print(f'{100*c/n:6.2f}%  {k}') for k, c in self_t.most_common(top)]
    print('--- inclusive'); [print(f'{100*c/n:6.2f}%  {k}') for k, c in incl.most_common(top)]

if __name__ == '__main__':
    main()
