
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

def f0(a0, a1):
    global acc
    _i = idx(a1); xs[_i] = shr(min(shr(w(a1 * 50), (div(-21, w(mod(a1, 7) + 8))) & 15), a0), ((w(w(a1 - -31) + (a1 & -4)) & w(mod(a0, w(mod(-50, 7) + 8)) * max(34, a0)))) & 15)
    return 46
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + f0(shr(38, (mod(32, w(mod(-9, 7) + 8))) & 15), a0))
    _i = idx(mod(45, w(mod(a2, 7) + 8))); xs[_i] = ((max(xs[idx(-42)], a0) ^ (min(a1, 24) ^ max(31, a0))) | mod(f0(a1, 28), w(mod(w(30 * (-1 | 50)), 7) + 8)))
    return a0
def f2(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + shr(shr(w(w(a0 + a1) - mod(-37, w(mod(a1, 7) + 8))), (shl(acc, (19) & 15)) & 15), (acc) & 15))
    if (-43) < (((acc) if ((mod(((a2) if (a2) < (a2) else (a2)), w(mod(w(a2 + a2), 7) + 8)) & min(a1, w(a2 * a0)))) < (w(w(max(a1, a1) * a2) + acc)) else (3))):
        for i84424 in range(3):
            v72644 = a1
            acc = w(w(acc * 31) + (w(div(acc, w(mod(49, 7) + 8)) - max(21, w(-19 - a1))) & -23))
        v10802 = xs[idx(w(a1 + (w(-15 * a1) ^ shl(-5, (31) & 15))))]
        v17959 = v10802
    else:
        v21919 = a0
    v27635 = f1(mod(a2, w(mod(w(a1 * a2), 7) + 8)), acc, 35)
    return w(w(acc * a0) * div(a2, w(mod(16, 7) + 8)))
def main():
    global acc
    _i = idx((((mod(21, w(mod(xs[idx(-18)], 7) + 8))) if (-3) < (w(acc + f1(-41, -39, -28))) else (20)) & ((mod(-10, w(mod(-22, 7) + 8)) & ((32) if (18) < (-40) else (0))) | shr(w(-11 - 5), (f2(-44, 21, 22)) & 15)))); xs[_i] = div((12 | -26), w(mod(w((w(31 * -24) & xs[idx(-48)]) * 42), 7) + 8))
    v11665 = div(-47, w(mod(f1((11 ^ 47), div(-29, w(mod(shl(7, (-46) & 15), 7) + 8)), ((-16 | -5) & mod(45, w(mod(27, 7) + 8)))), 7) + 8))
    acc = w(w(acc * 31) + (shl(w(shr(v11665, (v11665) & 15) + v11665), ((v11665 | 8)) & 15) | xs[idx(div(max(-12, -4), w(mod((v11665 | v11665), 7) + 8)))]))
    acc = w(w(acc * 31) + v11665)
    v67319 = 6
    _i = idx(f1(-8, -47, w(w(v11665 - min(2, -39)) - w(w(v11665 * 38) - (-16 & v11665))))); xs[_i] = max(f2(v11665, acc, xs[idx(xs[idx(v67319)])]), f1(w(w(v67319 + -31) * (31 ^ -48)), (w(12 + 5) | max(27, v11665)), (xs[idx(v11665)] & w(v67319 - 32))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
