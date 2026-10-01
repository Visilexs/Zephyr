
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

def f0(a0, a1, a2):
    global acc
    v37018 = shl(a2, (w((a2 | w(a2 - a1)) + ((a0 & -10) | min(a0, a2)))) & 15)
    acc = w(w(acc * 31) + ((min((((42 ^ v37018)) if (a1) < (a1) else (v37018)), shr(((a2) if (42) < (a1) else (-28)), ((-43 ^ a0)) & 15))) if ((shl(w(a1 * 24), (a2) & 15) ^ 9)) < (acc) else (shr(10, (shr(1, (w(32 - -11)) & 15)) & 15))))
    if (v37018) < (w(div(div(w(a1 + a0), w(mod(mod(-36, w(mod(a0, 7) + 8)), 7) + 8)), w(mod(div((25 ^ a0), w(mod(max(-7, 2), 7) + 8)), 7) + 8)) - (a1 ^ acc))):
        _i = idx((((v37018 & a2)) if (w((((5 | a1)) if (acc) < (a2) else (w(a1 + 19))) + (5 & max(a0, -29)))) < ((shr(w(a0 * a0), (a1) & 15) & w(w(a0 * 21) * 17))) else (max(shr((a0 & a1), (acc) & 15), shr((-25 ^ a2), (a0) & 15))))); xs[_i] = max(xs[idx(shl(w(v37018 + a2), (-3) & 15))], shr(shl(((-43) if (a2) < (a1) else (v37018)), (w(-29 + -11)) & 15), (-44) & 15))
        _i = idx(-30); xs[_i] = w(w(25 * min(div(-38, w(mod(a2, 7) + 8)), v37018)) * w(-19 + shr(shl(v37018, (a2) & 15), ((a2 ^ -12)) & 15)))
    else:
        acc = w(w(acc * 31) + max(((mod(xs[idx(a1)], w(mod(w(v37018 * v37018), 7) + 8))) if (shl(shl(a2, (39) & 15), (w(a0 * -44)) & 15)) < (((mod(a0, w(mod(a1, 7) + 8))) if (v37018) < (w(v37018 - -14)) else (acc))) else (xs[idx(xs[idx(a2)])])), ((max(v37018, a1) | acc) | mod(a2, w(mod(xs[idx(-20)], 7) + 8)))))
    return xs[idx(a1)]
def f1(a0, a1, a2):
    global acc
    v13845 = a1
    v53689 = mod(-45, w(mod(max(a1, ((1 | 8) ^ w(2 + a0))), 7) + 8))
    v73732 = a0
    return w(a2 - w((((-2 ^ -2)) if (min(a2, a1)) < (div(a0, w(mod(-50, 7) + 8))) else (a2)) - w((-19 | a1) * ((a0) if (a1) < (-36) else (a2)))))
def f2(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + (((w(max(-40, a1) - (a2 & -4))) if (w(min(37, a2) * (-38 & a2))) < (div(w(a0 * a2), w(mod(a0, 7) + 8))) else ((min(30, a2) & acc))) ^ a2))
    acc = w(w(acc * 31) + f0(w(acc * 35), w(xs[idx(xs[idx(a0)])] * f1(w(a2 * -31), a2, w(a2 * a1))), w(acc * ((min(-47, a1)) if (max(36, a0)) < (f0(-8, a2, -39)) else (f0(-35, a0, a0))))))
    v88276 = -6
    return -16
def f3(a0, a1):
    global acc
    if ((mod(w(div(-7, w(mod(a0, 7) + 8)) + div(a1, w(mod(a1, 7) + 8))), w(mod(w(((14) if (a0) < (a1) else (-5)) * a1), 7) + 8)) ^ a1)) < (((w(div(a0, w(mod(a1, 7) + 8)) * w(9 - a1)) & w(div(-43, w(mod(a1, 7) + 8)) + a1)) & (f2(div(a1, w(mod(41, 7) + 8)), shl(a1, (a1) & 15), a1) ^ a0))):
        if ((min(shr(w(a0 + 6), (mod(a0, w(mod(36, 7) + 8))) & 15), a0) | w(a1 - shr(a1, (a1) & 15)))) < (div(div(w(w(a0 - a0) * 45), w(mod(shr(w(a1 - 31), (a1) & 15), 7) + 8)), w(mod(max(max(shr(-33, (a1) & 15), shr(a1, (-18) & 15)), (max(38, a0) & min(-17, 10))), 7) + 8))):
            v19411 = 24
            _i = idx((min(min(shr(v19411, (-47) & 15), max(-17, v19411)), a0) | xs[idx(-10)])); xs[_i] = (a1 & w(div(w(v19411 * a1), w(mod(a0, 7) + 8)) + div(((a0) if (a1) < (v19411) else (a1)), w(mod(a0, 7) + 8))))
        else:
            _i = idx(min(xs[idx(a1)], -19)); xs[_i] = w(a1 * max(mod(37, w(mod(48, 7) + 8)), (shr(a0, (-15) & 15) | acc)))
            acc = w(w(acc * 31) + 26)
        v22499 = w((mod(max(34, -41), w(mod(a0, 7) + 8)) | shr(shr(16, (45) & 15), (min(a1, a1)) & 15)) - a1)
    else:
        if (mod(a1, w(mod(f1(f0(w(a0 + a1), w(a0 - 17), shl(a1, (a0) & 15)), 26, (min(a1, a1) & (a1 ^ 1))), 7) + 8))) < (min((min(a0, (a0 & 27)) | xs[idx(w(a0 + 15))]), a1)):
            _i = idx(a0); xs[_i] = w((-32 & mod(a0, w(mod(shr(-10, (a1) & 15), 7) + 8))) * w(((a0 & 14) | max(a0, 32)) - shl(mod(-45, w(mod(-43, 7) + 8)), ((46 ^ -49)) & 15)))
            acc = w(w(acc * 31) + w(shr((shl(a0, (a0) & 15) & a1), (min(-14, min(a1, a0))) & 15) * (shr(w(a1 + -17), (xs[idx(a0)]) & 15) & w(w(17 - a0) - w(18 + a0)))))
            _i = idx(a1); xs[_i] = max(w(mod((a0 | a1), w(mod(shr(a1, (a1) & 15), 7) + 8)) + mod(21, w(mod(w(a1 - a0), 7) + 8))), (a1 & 17))
        else:
            _i = idx(w(max(xs[idx(a1)], f1(f1(a1, a1, a0), a0, acc)) - f0(-17, shl((a1 & a0), (f0(25, a0, -14)) & 15), a0))); xs[_i] = mod(shr(mod(a0, w(mod(a0, 7) + 8)), (shr(xs[idx(a1)], (a1) & 15)) & 15), w(mod(f1(34, a0, (min(-24, a0) | a1)), 7) + 8))
            v207 = a1
    return (shr(div(max(12, a1), w(mod(a1, 7) + 8)), (w(max(-16, a1) * w(a1 - 25))) & 15) ^ min(a0, a1))
def main():
    global acc
    if (min(14, (-22 | f2(w(15 - 7), mod(-29, w(mod(-7, 7) + 8)), div(45, w(mod(21, 7) + 8)))))) < (20):
        if (xs[idx(min((21 & (-46 ^ -1)), shr(shr(9, (-41) & 15), (f1(-46, -14, -21)) & 15)))]) < (mod(22, w(mod(shr(w((-12 & -48) - shl(27, (-10) & 15)), (div(max(-23, 50), w(mod(shl(-15, (43) & 15), 7) + 8))) & 15), 7) + 8))):
            v6836 = w(1 + shr(48, (-4) & 15))
        else:
            acc = w(w(acc * 31) + w(div(8, w(mod(w(22 - 29), 7) + 8)) + mod((-14 & 40), w(mod(f2(((10) if (-15) < (39) else (-25)), mod(36, w(mod(34, 7) + 8)), shl(-34, (-12) & 15)), 7) + 8))))
        acc = w(w(acc * 31) + max(div(max(min(2, 42), w(-50 - -4)), w(mod((xs[idx(38)] & -14), 7) + 8)), xs[idx((33 | mod(14, w(mod(-39, 7) + 8))))]))
    else:
        v61745 = acc
    _i = idx(-29); xs[_i] = acc
    if (27) < (23):
        if (-33) < (w(((xs[idx(((8) if (6) < (41) else (9)))]) if (shl((30 | 11), (-6) & 15)) < (49) else (mod(-30, w(mod(f1(-43, -17, 37), 7) + 8)))) + (w((-20 & 50) * f2(-19, -21, -27)) ^ -41))):
            v74634 = 50
            _i = idx(v74634); xs[_i] = mod(acc, w(mod(div(-11, w(mod(w(acc + 34), 7) + 8)), 7) + 8))
            acc = w(w(acc * 31) + w(shr(shr(xs[idx(v74634)], (max(v74634, v74634)) & 15), (40) & 15) * 49))
        else:
            v2388 = max(43, -4)
        if (xs[idx(-1)]) < (f3((mod(max(41, 2), w(mod(38, 7) + 8)) | max(6, (33 | -8))), (-45 & 45))):
            _i = idx(-48); xs[_i] = shl(max(-23, (((-1) if (47) < (1) else (36)) & mod(-31, w(mod(-8, 7) + 8)))), (42) & 15)
            acc = w(w(acc * 31) + w(-32 * xs[idx(xs[idx(f0(40, 25, -34))])]))
            _i = idx(xs[idx(min(w(xs[idx(43)] + 33), w(-39 * max(-29, 0))))]); xs[_i] = min(-2, 45)
        else:
            v4396 = mod(37, w(mod(mod(((shl(13, (24) & 15)) if ((-6 & 42)) < (max(18, 50)) else (shr(3, (21) & 15))), w(mod(acc, 7) + 8)), 7) + 8))
            v22793 = (v4396 | w((v4396 | v4396) * w(acc + xs[idx(v4396)])))
    else:
        for i26623 in range(1):
            v61157 = -12
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
