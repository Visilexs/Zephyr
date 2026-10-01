#!/usr/bin/env python3
"""gcc PGO gain on the 19 C references (M25): -fprofile-generate, train on the
benchmark input, -fprofile-use, median of 3 runs each. Needs the 398aadd bench/
sources extracted to /tmp/zr/old/bench (see research/x86bench.py)."""
import subprocess, statistics, time, os
suite=[("fib","43",""),("matmul","1100",""),("mandel","1700","-ffp-contract=off"),("sort","6000000",""),("strings","4000000",""),("hashmap","32000000",""),("cube","80000","-ffp-contract=off -lm"),("pi","40000",""),("liquid","100","-ffp-contract=off -lm"),("shapes","600000","-ffp-contract=off -lm"),("closures","600000",""),("wordfreq","14000000",""),("nbody","200","-ffp-contract=off -lm"),("lexer","2500000",""),("vectors","35000","-ffp-contract=off"),("dispatch","",""),("records","",""),("strbuild","",""),("bintrees","","")]
def t(cmd):
    runs=[]
    for i in range(3):
        s=time.perf_counter(); subprocess.run(['taskset','-c','3']+cmd,capture_output=True); runs.append(time.perf_counter()-s)
    return statistics.median(runs)
ratios=[]
for n,a,f in suite:
    src=f'/tmp/zr/old/bench/{n}.c'; args=[a] if a else []
    fl=f.split(); lm=['-lm'] if '-lm' in fl else []; fl=[x for x in fl if x!='-lm']
    subprocess.run(['gcc','-O2','-fwrapv',*fl,src,'-o',f'{n}.plain',*lm],check=True)
    subprocess.run(['gcc','-O2','-fwrapv',*fl,'-fprofile-generate',src,'-o',f'{n}.gen',*lm],check=True)
    subprocess.run([f'./{n}.gen',*args],capture_output=True)
    subprocess.run(['gcc','-O2','-fwrapv',*fl,'-fprofile-use','-Wno-missing-profile',src,'-o',f'{n}.pgo',*lm],check=True)
    p=t([f'./{n}.plain',*args]); q=t([f'./{n}.pgo',*args]); ratios.append(q/p)
    print(f'{n:9s} plain {p*1000:7.0f} ms  pgo {q*1000:7.0f} ms  pgo/plain {q/p:.3f}',flush=True)
print('geomean pgo/plain', round(statistics.geometric_mean(ratios),3))
