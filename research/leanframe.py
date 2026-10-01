#!/usr/bin/env python3
"""Rewrite selected functions in zc assembly (after research/zc2gas.sh) to a
lean internal frame: callee-saved registers pushed and popped, with no frame
pointer and no stack realignment. That's the convention measured in M21.

Only functions that are safe to rewrite are changed:
  - no rbp-relative operands besides the prologue and epilogue themselves
    (rsp-relative spill slots below the save area are kept, with their bytes);
  - every call goes to a function that is itself rewritten, or is a panic,
    which never returns, so stack alignment past it doesn't matter.
Usage: leanframe.py in.s out.s function [function...]
"""
import re, sys

def rewrite(text, name, lean):
    a = text.index(name + ':\n'); b = text.find('\n\n', a); b = len(text) if b < 0 else b
    body = text[a:b]
    m = re.match(re.escape(name) + r':\n  push rbp\n  mov rbp, rsp\n  and rsp, -16\n(?:  sub rsp, (\d+)\n)?', body)
    if not m: raise SystemExit(f'{name}: unexpected prologue')
    saves = re.findall(r'  mov \[rsp \+ (\d+)\], (r\w+)\n', body[m.end():m.end() + 400])
    saved = []
    rest = body[m.end():]
    for off, reg in saves:
        line = f'  mov [rsp + {off}], {reg}\n'
        if not rest.startswith(line): break
        rest = rest[len(line):]; saved.append((int(off), reg))
    restore = ''.join(f'  mov {reg}, [rsp + {off}]\n' for off, reg in saved) + '  mov rsp, rbp\n  pop rbp\n  ret'
    if restore not in rest: raise SystemExit(f'{name}: unexpected epilogue')
    inner = rest.replace(restore, '')
    if re.search(r'\[rbp', inner): raise SystemExit(f'{name}: uses rbp-relative slots; not rewritten')
    # Spill slots below the save area stay addressable: keep that many bytes.
    slotBytes = min([off for off, _ in saved] or [int(m.group(1) or 0)])
    if any(int(k) >= slotBytes for k in re.findall(r'\[rsp \+ (\d+)\]', inner)):
        raise SystemExit(f'{name}: rsp slots overlap the save area')
    for call in re.findall(r'  call (\S+)', rest):
        if call not in lean and not call.startswith('runtimePanic'):
            raise SystemExit(f'{name}: calls {call}, which keeps the old convention')
    pushes = ''.join(f'  push {reg}\n' for _, reg in saved) + (f'  sub rsp, {slotBytes}\n' if slotBytes else '')
    pops = (f'  add rsp, {slotBytes}\n' if slotBytes else '') + ''.join(f'  pop {reg}\n' for _, reg in reversed(saved)) + '  ret'
    new = name + ':\n' + pushes + rest.replace(restore, pops)
    return text[:a] + new + text[b:]

def main():
    src, dst, names = sys.argv[1], sys.argv[2], sys.argv[3:]
    text = open(src).read()
    for n in names: text = rewrite(text, n, set(names))
    open(dst, 'w').write(text)
    print('rewrote', ', '.join(names))

if __name__ == '__main__':
    main()
