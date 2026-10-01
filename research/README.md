# Research tools

These tools back `docs/architecture-research.md`. Each measurement there names
the tool that produced it (M1, M2, …). Nothing here changes the shipping
compiler. Experiments that needed a modified compiler or runtime used copies
in `/tmp`, and the changes are kept in `patches/`.

## Setup (Linux x86-64)

```sh
sh research/setup.sh          # installs Wine if needed; builds /tmp/zr/root/zc, a Linux-native zc
gcc -O2 -o /tmp/zr/sampler research/sampler.c
```

`setup.sh` builds `zc.exe --linux` from `compiler/zc.zeph` under Wine once.
Every measurement afterwards runs native Linux code (M1).

- For profiling, apply `patches/zc-elf-symbol-map.patch` to a copy of
  `compiler/zc.zeph` and build that compiler too, so `--map` also writes ELF
  maps.
- zc resolves `compiler/` and `lib/` next to its own binary. A modified runtime
  therefore needs its own directory: a copy of zc next to a patched copy of
  `compiler/`.
- The benchmark tools read the original workloads and C references from Git
  revision `398aadd` (`git archive 398aadd bench`), so that revision must be
  in your clone.

## Measuring

| Tool | Use |
|---|---|
| `x86bench.py` | the 19 workloads against gcc -O2: checksums, medians, geometric mean (M2) |
| `pgo_c.py` | gcc PGO gain on the C references (M25) |
| `sampler.c` + `samplereport.py` | ptrace sampling profiler with RBP frame walks; self and inclusive time per function (M3) |
| `hotspots.py` | instruction-level hotspots of one function, disassembling zc's ELF output (M11, M18, M49) |
| `profile_all.py` | cost category breakdown for every workload (M6) |
| `cgprofile.py` | callgrind aggregation; zc's GC stack scan faults under valgrind, so prefer the sampler |
| `zc2gas.sh` + `start.s` | reassemble zc's assembly with GNU as, for hand-edited codegen experiments (M20) |
| `leanframe.py` | rewrite chosen functions in reassembled output to the lean internal frame (M21, M29) |
| `immutable_scan.py` | how many struct types are never field-assigned (M16) |

## Prototypes (`proto/`)

| File | Question it answers |
|---|---|
| `interp.c` | how fast a typed register interpreter can be (M4) |
| `flatopt.c`, `flatopt.zeph` | cost per SSA value of a flat-array optimizer, in C and Zephyr; `extended=1` adds dominators, loops, LICM and ranges (M4b, M47) |
| `minijit.c` | end to end: flat IR, linear scan, coalescing, x86 encoding, run; plus an inliner and naive spilling (M55, cycles 74–77) |
| `stencils.c`, `stencilcode.c` | copy-and-patch emission speed and code quality (M31, M51) |
| `declsplit.zeph` | finding changed declarations without parsing (M10) |
| `forkjoin.c` | parallel loop overhead and speedup (M8) |
| `allocmodels.c` | allocation strategies on bintrees: malloc, generic and specialized RC, 8-byte header, regions, tracing GC (M13, M52) |
| `mapmodels.c` | string-map designs (M24) |
| `rccost.c` | plain, biased and atomic reference-count update cost (M26) |
| `mmapload.c` | cost of loading a cached code image (M17) |

## Oracles (`oracle/`)

An oracle is the program a proposed transformation would produce, written by
hand. Timing it bounds the transformation's gain before anyone builds it.

- `.zeph` oracles are compared with the original workload under the same
  compiler.
- `.c` oracles change a C reference to have Zephyr's representation (M44, M45)
  or to show a bound (`vectors_soa.c`).
- `parallel/` holds OpenMP versions of the C references (M48) and per-thread
  regions (cycle 57).

## Differential fuzzing (`fuzz/`)

```sh
python3 research/fuzz/difftest.py 1000 600 4                     # genprog: ints, lists, structs, globals
PURE=1 python3 research/fuzz/difftest.py 1000 600 4              # no side effects in calls, so order can't matter
GEN=genref.py python3 research/fuzz/difftest.py 1 400 4          # ownership and reference-count patterns
GEN=genext.py python3 research/fuzz/difftest.py 1 500 4          # floats, closures, interfaces
GEN=genmap.py python3 research/fuzz/difftest.py 1 400 4          # maps, generics
python3 research/fuzz/tritest.py 100 400 4                       # three-way, against a Python reference (left to right)
python3 research/fuzz/reduce.py failures/seedN.zeph out.zeph     # shrink a mismatch
```

- `failures/` keeps every mismatching program.
- `repro/` keeps the reduced ones, starting with the -O2 loop-exit forwarding
  bug (`loop-exit-global-1009.zeph`, `pure-1292.zeph`) (M39, M40).

## Results (`results/`)

Raw JSON from the runs cited in the document:

- `x86-linux.json` and `x86-linux-rerun.json` (M2, cycle 64);
- `profile-O2.json` (M6);
- `oracles-same-session.json` (M53);
- `store-forwarding-O2-original.json` and `store-forwarding-O2-patched.json` (M56);
- `order-original.json`, `order-blunt.json` and `order-targeted.json` (M57).
