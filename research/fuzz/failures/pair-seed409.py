
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
    _i = idx(xs[idx(shl(w(a0 + 10), (25) & 15))]); xs[_i] = div(shr(a0, ((-39 | a0)) & 15), w(mod(w(min((43 & a0), shl(-18, (a0) & 15)) + w(div(a0, w(mod(a0, 7) + 8)) + a0)), 7) + 8))
    for i35719 in range(6):
        if (xs[idx((w(max(a0, 15) - ((-45) if (29) < (i35719) else (i35719))) | a0))]) < (44):
            _i = idx(w(mod(a0, w(mod(acc, 7) + 8)) - ((shr((i35719 | a0), (w(i35719 + -30)) & 15)) if (w(min(a0, 44) + xs[idx(a0)])) < ((7 & (a0 & i35719))) else ((-49 & i35719))))); xs[_i] = w(xs[idx(shl(i35719, (i35719) & 15))] + (a0 | 6))
            acc = w(w(acc * 31) + div(i35719, w(mod((acc & min(div(a0, w(mod(a0, 7) + 8)), i35719)), 7) + 8)))
            _i = idx(((a0) if (div(a0, w(mod(3, 7) + 8))) < (xs[idx(xs[idx(min(a0, a0))])]) else (mod(w(((a0) if (i35719) < (20) else (a0)) + a0), w(mod(33, 7) + 8))))); xs[_i] = min(min(w(mod(i35719, w(mod(a0, 7) + 8)) + shr(0, (i35719) & 15)), w(i35719 - a0)), xs[idx(w(a0 - ((a0) if (i35719) < (i35719) else (i35719))))])
        else:
            v95471 = -28
    if (w(w(a0 * div(1, w(mod(acc, 7) + 8))) + div(xs[idx((-18 & 14))], w(mod(31, 7) + 8)))) < (a0):
        for i3062 in range(6):
            acc = w(w(acc * 31) + i3062)
        acc = w(w(acc * 31) + w(xs[idx((acc & w(-43 - -4)))] * max(shl(26, (shl(23, (-7) & 15)) & 15), a0)))
        if (a0) < (xs[idx(xs[idx(w(25 * -24))])]):
            acc = w(w(acc * 31) + min(w(w(a0 * -41) + w(shl(a0, (a0) & 15) + shl(a0, (a0) & 15))), w(((a0 | a0) & xs[idx(40)]) + a0)))
            v4349 = (((div(a0, w(mod(w(41 - 31), 7) + 8))) if (max(29, w(34 - a0))) < (a0) else (w(a0 + div(34, w(mod(a0, 7) + 8))))) & shr(max(((39) if (-14) < (a0) else (a0)), min(a0, a0)), ((w(a0 + a0) | w(a0 * a0))) & 15))
            v76638 = shr((w(max(14, a0) - w(36 + v4349)) & a0), (w(w(mod(v4349, w(mod(a0, 7) + 8)) * xs[idx(a0)]) * v4349)) & 15)
        else:
            acc = w(w(acc * 31) + min(a0, w(-17 * a0)))
    else:
        _i = idx(xs[idx(18)]); xs[_i] = ((w(((a0) if ((22 ^ a0)) < (a0) else (acc)) * div((a0 | a0), w(mod(shl(-28, (a0) & 15), 7) + 8)))) if (shl((a0 | (a0 & a0)), (a0) & 15)) < (-22) else (mod(a0, w(mod((w(a0 - a0) | div(1, w(mod(39, 7) + 8))), 7) + 8))))
    return min(shl(w(shl(a0, (-43) & 15) * (-22 | 47)), (shr(29, (((a0) if (a0) < (36) else (26))) & 15)) & 15), (-29 & w(max(a0, a0) - a0)))
def f1(a0):
    global acc
    v42243 = max(shr(a0, (div(-19, w(mod(shl(15, (32) & 15), 7) + 8))) & 15), ((mod((-15 & -35), w(mod(-5, 7) + 8))) if (24) < (div(((a0) if (14) < (-7) else (a0)), w(mod(a0, 7) + 8))) else (shl(shl(a0, (24) & 15), (min(-2, a0)) & 15))))
    return w(-27 + div(w(a0 + acc), w(mod(-23, 7) + 8)))
def f2(a0):
    global acc
    acc = w(w(acc * 31) + w(mod(a0, w(mod(50, 7) + 8)) + acc))
    for i15244 in range(11):
        v83495 = 35
    acc = w(w(acc * 31) + a0)
    return ((a0 ^ w(min(17, a0) * 28)) ^ w(a0 - ((a0 ^ a0) & a0)))
def f3(a0, a1):
    global acc
    acc = w(w(acc * 31) + f0(a0))
    _i = idx(a0); xs[_i] = div(-48, w(mod((14 & f0(f2(-25))), 7) + 8))
    return shr(w(a0 + w(a1 * max(-19, -4))), (w(((div(a0, w(mod(18, 7) + 8))) if (w(a1 - a1)) < (a1) else (a0)) + ((a1) if (a1) < (a0) else (-21)))) & 15)
def main():
    global acc
    for i59526 in range(6):
        acc = w(w(acc * 31) + f2(i59526))
        _i = idx(mod(-36, w(mod((min(i59526, w(-44 - i59526)) | -20), 7) + 8))); xs[_i] = (w(i59526 - mod((29 ^ i59526), w(mod(min(22, i59526), 7) + 8))) | i59526)
        v77727 = w(min(i59526, div(i59526, w(mod(f3(49, i59526), 7) + 8))) * (shr(i59526, (w(i59526 - -11)) & 15) | div(max(-1, i59526), w(mod((i59526 ^ 38), 7) + 8))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
