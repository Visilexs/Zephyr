#!/usr/bin/env python3
"""Generate the same random program twice: as Zephyr, and as Python that
defines its meaning with an explicit left-to-right evaluation order. The
Python version is a tiny executable specification (the role of the IR
interpreter in layer 6). It gives a third opinion when baseline and -O2
disagree.

Semantics in the Python reference:
  - 64-bit wraparound after every int operation;
  - `/` truncates toward zero and `%` takes the sign of the dividend (spec §3.3);
  - `>>` is arithmetic and `<<` wraps;
  - operands are evaluated left to right, including reads of globals before
    calls further right in the same expression.
Usage: genpair.py SEED OUTDIR   (writes OUTDIR/p.zeph and OUTDIR/p.py)
"""
import os, random, sys

PURE = os.environ.get('PURE') == '1'     # functions don't write acc or xs, so order can't matter

PRELUDE = '''
def w(x):
    x &= (1 << 64) - 1
    return x - (1 << 64) if x >> 63 else x
def div(a, b):
    q = abs(a) // abs(b)
    return w(q if (a >= 0) == (b > 0) else -q)
def mod(a, b):
    return w(a - div(a, b) * b)
def shl(a, b): return w(a << b)
def shr(a, b): return a >> b
xs = [1, 2, 3, 5, 8, 13]
acc = 0
def idx(i): return ((i % len(xs)) + len(xs)) % len(xs)
'''

class Gen:
    def __init__(self, seed):
        self.r = random.Random(seed); self.functions = []; self.inFunction = False

    def expr(self, vars, depth=0):
        """Returns (zephyr, python) for an int expression; Python evaluates left to right."""
        r = self.r
        if depth > 3 or r.random() < 0.3:
            if vars and r.random() < 0.6:
                v = r.choice(vars); return v, v
            c = r.randint(-50, 50); return str(c), str(c)
        op = r.choice(['+', '-', '*', '&', '|', '^', '<<', '>>', '/', '%', 'min', 'max', 'call', 'list', 'if', 'acc'])
        if op == 'acc':
            if PURE and self.inFunction: return '1', '1'
            return 'acc', 'acc'
        if op == 'call' and not self.functions:
            op = '+'
        if op == 'call' and self.functions:
            name, arity = r.choice(self.functions)
            args = [self.expr(vars, depth + 1) for _ in range(arity)]
            return f'{name}({", ".join(a[0] for a in args)})', f'{name}({", ".join(a[1] for a in args)})'
        a = self.expr(vars, depth + 1); b = self.expr(vars, depth + 1)
        if op in ('/', '%'):
            # Divisor ((b) % 7 + 8) is in 2..14, so never zero.
            dz, dp = f'(({b[0]}) % 7 + 8)', f'w(mod({b[1]}, 7) + 8)'
            return (f'({a[0]} {op} {dz})', f'{"div" if op == "/" else "mod"}({a[1]}, {dp})')
        if op in ('<<', '>>'):
            return (f'({a[0]} {op} (({b[0]}) & 15))', f'{"shl" if op == "<<" else "shr"}({a[1]}, ({b[1]}) & 15)')
        if op in ('min', 'max'):
            return f'{op}({a[0]}, {b[0]})', f'{op}({a[1]}, {b[1]})'
        if op == 'list':
            return f'xs[(({a[0]}) % xs.len() + xs.len()) % xs.len()]', f'xs[idx({a[1]})]'
        if op == 'if':
            t = self.expr(vars, depth + 1); e = self.expr(vars, depth + 1)
            return (f'(if {a[0]} < {b[0]} {{ {t[0]} }} else {{ {e[0]} }})', f'(({t[1]}) if ({a[1]}) < ({b[1]}) else ({e[1]}))')
        if op in ('+', '-', '*'):
            return f'({a[0]} {op} {b[0]})', f'w({a[1]} {op} {b[1]})'
        return f'({a[0]} {op} {b[0]})', f'({a[1]} {op} {b[1]})'

    def block(self, vars, indent, budget, inFunction):
        r = self.r; z, p = [], []; local = list(vars)
        zpad, ppad = '    ' * indent, '    ' * indent
        for _ in range(r.randint(1, budget)):
            k = r.random()
            if PURE and inFunction and (0.3 <= k < 0.55 or k >= 0.85): k = 0.0
            if k < 0.3:
                v = f'v{r.randint(0, 99999)}'; e = self.expr(local)
                z.append(f'{zpad}var {v} = {e[0]}'); p.append(f'{ppad}{v} = {e[1]}'); local.append(v)
            elif k < 0.55:
                e = self.expr(local)
                z.append(f'{zpad}acc = acc * 31 + {e[0]}'); p.append(f'{ppad}acc = w(w(acc * 31) + {e[1]})')
            elif k < 0.7 and indent < 3:
                i = f'i{r.randint(0, 99999)}'; n = r.randint(1, 12)
                bz, bp = self.block(local + [i], indent + 1, 3, inFunction)
                z.append(f'{zpad}for {i} in 0..{n} {{'); z += bz; z.append(f'{zpad}}}')
                p.append(f'{ppad}for {i} in range({n}):'); p += bp or [f'{ppad}    pass']
            elif k < 0.85 and indent < 3:
                a = self.expr(local); b = self.expr(local)
                tz, tp = self.block(local, indent + 1, 3, inFunction); ez, ep = self.block(local, indent + 1, 2, inFunction)
                z.append(f'{zpad}if {a[0]} < {b[0]} {{'); z += tz; z.append(f'{zpad}}} else {{'); z += ez; z.append(f'{zpad}}}')
                p.append(f'{ppad}if ({a[1]}) < ({b[1]}):'); p += tp or [f'{ppad}    pass']; p.append(f'{ppad}else:'); p += ep or [f'{ppad}    pass']
            else:
                a = self.expr(local); b = self.expr(local)
                z.append(f'{zpad}xs[(({a[0]}) % xs.len() + xs.len()) % xs.len()] = {b[0]}')
                p.append(f'{ppad}_i = idx({a[1]}); xs[_i] = {b[1]}')
        return z, p

    def program(self):
        z = ['// generated by research/fuzz/genpair.py', 'var xs: [int] = [1, 2, 3, 5, 8, 13]', 'var acc = 0']
        p = [PRELUDE]
        for f in range(self.r.randint(1, 4)):
            arity = self.r.randint(1, 3); params = [f'a{k}' for k in range(arity)]; name = f'f{f}'
            self.inFunction = True
            bz, bp = self.block(params, 1, 3, True)
            ret = self.expr(params)
            self.inFunction = False
            z.append(f'fn {name}({", ".join(x + ": int" for x in params)}) -> int {{'); z += bz; z.append(f'    return {ret[0]}'); z.append('}')
            p.append(f'def {name}({", ".join(params)}):'); p.append('    global acc'); p += bp; p.append(f'    return {ret[1]}')
            self.functions.append((name, arity))
        bz, bp = self.block([], 1, 10, False)
        z.append('fn main() {'); z += bz
        z += ['    var total = acc', '    for x in xs { total = total * 1000003 + x }', '    print(total)', '}']
        p.append('def main():'); p.append('    global acc'); p += bp
        p += ['    total = acc', '    for x in xs: total = w(w(total * 1000003) + x)', '    print(total)', 'main()']
        return '\n'.join(z) + '\n', '\n'.join(p) + '\n'

if __name__ == '__main__':
    seed, out = int(sys.argv[1]), sys.argv[2]
    zs, ps = Gen(seed).program()
    open(os.path.join(out, 'p.zeph'), 'w').write(zs); open(os.path.join(out, 'p.py'), 'w').write(ps)
