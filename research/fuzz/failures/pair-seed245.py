
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
    v43217 = (((a1 | w(w(-7 + a0) - w(33 + a0)))) if (shl((acc | mod(a0, w(mod(a1, 7) + 8))), (mod(a0, w(mod(acc, 7) + 8))) & 15)) < (a0) else (a1))
    acc = w(w(acc * 31) + xs[idx(a0)])
    return a0
def f1(a0, a1):
    global acc
    acc = w(w(acc * 31) + mod((shr(a0, (a1) & 15) & acc), w(mod(w(a1 * ((((-9) if (a1) < (a1) else (-31))) if (min(-7, -28)) < (acc) else ((19 | 49)))), 7) + 8)))
    if (acc) < ((a0 & a1)):
        v57132 = w(min(shr(div(14, w(mod(-10, 7) + 8)), (max(a0, -33)) & 15), a0) + xs[idx(max(mod(a1, w(mod(a1, 7) + 8)), a1))])
        _i = idx(4); xs[_i] = shl(acc, (-16) & 15)
    else:
        acc = w(w(acc * 31) + shl(acc, (max(mod(xs[idx(a1)], w(mod(mod(a0, w(mod(a0, 7) + 8)), 7) + 8)), w((a0 & -9) - 30))) & 15))
        for i9736 in range(12):
            acc = w(w(acc * 31) + shr((shr(div(a1, w(mod(a0, 7) + 8)), (mod(a0, w(mod(i9736, 7) + 8))) & 15) | -44), (-2) & 15))
            _i = idx(shr((-15 & 45), (i9736) & 15)); xs[_i] = min(a1, xs[idx(shr(i9736, (mod(-50, w(mod(30, 7) + 8))) & 15))])
            acc = w(w(acc * 31) + (((div(min(-40, a1), w(mod(mod(i9736, w(mod(a1, 7) + 8)), 7) + 8)) & acc)) if ((a1 & max(((a0) if (a1) < (a0) else (a1)), 3))) < (w(max(shr(-4, (a1) & 15), -7) - max(xs[idx(i9736)], a1))) else (max((w(-26 * a1) & mod(a1, w(mod(a1, 7) + 8))), shl((22 & -9), (f0(a1, a1)) & 15)))))
    return ((xs[idx(div(33, w(mod(a0, 7) + 8)))] & a1) ^ w(w(a0 + min(-21, a1)) - div(acc, w(mod((14 | 13), 7) + 8))))
def main():
    global acc
    _i = idx(div((mod(2, w(mod(mod(-1, w(mod(-28, 7) + 8)), 7) + 8)) ^ max(13, (6 ^ 15))), w(mod(shr(min(shr(22, (12) & 15), 4), (f0((-1 & -9), max(5, 14))) & 15), 7) + 8))); xs[_i] = -16
    v21114 = 46
    acc = w(w(acc * 31) + v21114)
    v96109 = (div(acc, w(mod(shl(f0(42, v21114), (f0(v21114, v21114)) & 15), 7) + 8)) & v21114)
    acc = w(w(acc * 31) + (w(max(w(41 - v21114), -25) * w((v96109 & 30) - xs[idx(v21114)])) ^ 6))
    v10019 = 36
    _i = idx(v10019); xs[_i] = mod(-18, w(mod(div(xs[idx(v21114)], w(mod(w(div(v96109, w(mod(v96109, 7) + 8)) * shl(-25, (v96109) & 15)), 7) + 8)), 7) + 8))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
