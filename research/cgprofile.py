#!/usr/bin/env python3
"""Aggregate a callgrind profile of a Zephyr ELF by function, using a zc --map file.

Run callgrind with: --dump-instr=yes --compress-pos=no --compress-strings=no
Usage: cgprofile.py callgrind.out program.map [top]
The map holds "offset name" lines; ELF text sits at 0x400000 + offset (see writeElf).
"""
import bisect, collections, sys

def main():
    out, mapfile = sys.argv[1], sys.argv[2]
    top = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    syms = sorted((0x400000 + int(a), n) for a, n in (l.split(' ', 1) for l in open(mapfile).read().splitlines() if l))
    addrs = [a for a, _ in syms]
    self_cost = collections.Counter()
    skip = False
    total = 0
    for line in open(out):
        if line.startswith('calls='):
            skip = True; continue          # next cost line is inclusive cost of the call
        if not line.startswith('0x'):
            continue
        if skip:
            skip = False; continue
        parts = line.split()
        addr, cost = int(parts[0], 16), int(parts[2])
        i = bisect.bisect_right(addrs, addr) - 1
        name = syms[i][1] if i >= 0 else '?'
        self_cost[name] += cost; total += cost
    print(f'total {total:,} instructions')
    for name, c in self_cost.most_common(top):
        print(f'{c:>14,} {100*c/total:6.2f}%  {name}')

if __name__ == '__main__':
    main()
