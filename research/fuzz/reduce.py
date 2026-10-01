#!/usr/bin/env python3
"""Shrink a program whose baseline and -O2 outputs differ (difftest.py), by
repeatedly deleting lines (and simplifying expressions to 0/1) while the
mismatch persists. Keeps the program compiling in both modes.
Usage: reduce.py in.zeph out.zeph
"""
import os, re, subprocess, sys, tempfile
from pathlib import Path

ZC = os.environ.get('ZC_LINUX', '/tmp/zr/root/zc')

def outputs(text):
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / 'p.zeph'; src.write_text(text); res = []
        for flags in ([], ['-O2']):
            exe = Path(d) / ('o' if flags else 'b')
            c = subprocess.run([ZC, '--linux', '--rt', *flags, str(src), str(exe)], capture_output=True, text=True, timeout=120)
            if c.returncode: return None
            os.chmod(exe, 0o755)
            try: r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=20)
            except subprocess.TimeoutExpired: return None
            if r.returncode: return None
            res.append(r.stdout)
        return res

def bad(text):
    o = outputs(text)
    return o is not None and o[0] != o[1]

def main():
    text = Path(sys.argv[1]).read_text()
    assert bad(text), 'input does not reproduce'
    changed = True
    while changed:
        changed = False
        lines = text.split('\n')
        chunk = max(1, len(lines) // 8)
        while chunk >= 1:
            i = 0
            while i < len(lines):
                trial = lines[:i] + lines[i + chunk:]
                t = '\n'.join(trial)
                if bad(t):
                    lines = trial; text = t; changed = True
                else:
                    i += chunk
            chunk //= 2
        # simplify integer literals
        for m in sorted(set(re.findall(r'(?<![\w.])-?\d+(?![\w.])', text)), key=len, reverse=True):
            for rep in ('0', '1'):
                t = re.sub(r'(?<![\w.])' + re.escape(m) + r'(?![\w.])', rep, text)
                if t != text and bad(t):
                    text = t; changed = True; break
    Path(sys.argv[2]).write_text(text)
    print(text)
    print('outputs (baseline, -O2):', outputs(text))

if __name__ == '__main__':
    main()
