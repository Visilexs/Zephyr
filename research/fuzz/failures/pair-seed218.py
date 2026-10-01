
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

def f0(a0):
    global acc
    if (min(-44, max(max(shr(a0, (a0) & 15), acc), -34))) < (w(((max(((-12) if (-40) < (-29) else (a0)), a0)) if (div(((a0) if (a0) < (-16) else (-26)), w(mod(xs[idx(a0)], 7) + 8))) < ((max(a0, a0) | a0)) else (w(-21 * max(a0, -22)))) * a0)):
        v95224 = 19
    else:
        acc = w(w(acc * 31) + a0)
    return ((-27) if (26) < (-22) else (shl(a0, (27) & 15)))
def f1(a0, a1):
    global acc
    if (acc) < ((a1 & mod(shr(34, ((-19 ^ a1)) & 15), w(mod(f0(div(a0, w(mod(-35, 7) + 8))), 7) + 8)))):
        acc = w(w(acc * 31) + shr(min(((a0 | a1) | f0(33)), max(-34, -26)), (div(f0(shr(a1, (a1) & 15)), w(mod(acc, 7) + 8))) & 15))
        v56169 = a1
    else:
        acc = w(w(acc * 31) + mod((div(w(a0 * -49), w(mod((a0 | a1), 7) + 8)) & shl(min(a0, a1), ((-25 | a0)) & 15)), w(mod(w(42 - shr(acc, (a0) & 15)), 7) + 8)))
    for i67680 in range(8):
        acc = w(w(acc * 31) + w(acc - a1))
    if (acc) < (w(shr((div(-22, w(mod(a0, 7) + 8)) ^ 44), (shl(acc, (a0) & 15)) & 15) - -45)):
        _i = idx((acc | max(w(((a1) if (-9) < (a1) else (47)) - a1), 14))); xs[_i] = a0
    else:
        _i = idx(max(a1, mod(a1, w(mod(div(37, w(mod(f0(46), 7) + 8)), 7) + 8)))); xs[_i] = div(-6, w(mod(xs[idx(-9)], 7) + 8))
        v67641 = max((shl(a0, (a1) & 15) & a1), a0)
    return max(max(shl(a0, (acc) & 15), (17 & xs[idx(a0)])), a1)
def f2(a0, a1):
    global acc
    v87258 = (((((-33 | 32)) if (a0) < (a1) else (div(29, w(mod(a1, 7) + 8)))) & min(a1, mod(a1, w(mod(a0, 7) + 8)))) & -7)
    for i73435 in range(8):
        acc = w(w(acc * 31) + (((shr(w(42 - 13), (w(-37 * 44)) & 15)) if (f1(v87258, w(v87258 + a1))) < (i73435) else (min((a0 & i73435), v87258))) ^ w(acc + w(f0(-20) + xs[idx(6)]))))
        v29685 = -45
    return mod(xs[idx(max(mod(30, w(mod(a0, 7) + 8)), -35))], w(mod(w(shr(min(-29, a1), (mod(a1, w(mod(41, 7) + 8))) & 15) + f0(w(a1 * a0))), 7) + 8))
def main():
    global acc
    v37681 = mod(-14, w(mod(((min(shl(33, (-11) & 15), acc)) if (50) < (4) else (36)), 7) + 8))
    acc = w(w(acc * 31) + f0(v37681))
    v83631 = v37681
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
