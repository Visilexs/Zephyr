
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
    acc = w(w(acc * 31) + div(w(w(a2 * a0) - shr(acc, (a2) & 15)), w(mod(a1, 7) + 8)))
    for i68334 in range(5):
        for i58255 in range(1):
            _i = idx(w(14 - shr((w(i68334 + -24) & a2), (28) & 15))); xs[_i] = a1
        _i = idx(min(i68334, acc)); xs[_i] = div(-11, w(mod(((((43) if (shr(14, (39) & 15)) < (-11) else (w(-3 + -31)))) if ((w(-41 + i68334) | w(i68334 - 18))) < (w(min(i68334, -38) - min(i68334, i68334))) else (-13)), 7) + 8))
        _i = idx(mod(xs[idx(div(a1, w(mod(a0, 7) + 8)))], w(mod(acc, 7) + 8))); xs[_i] = a2
    return xs[idx(a1)]
def f1(a0, a1, a2):
    global acc
    for i36888 in range(6):
        v78870 = acc
        v49437 = ((a2) if (acc) < ((a2 ^ i36888)) else (29))
        v66388 = min(a1, shr(xs[idx(f0(v78870, v78870, a1))], (xs[idx(v49437)]) & 15))
    _i = idx((((42) if (f0(xs[idx(a1)], shl(a1, (a2) & 15), a2)) < (w(xs[idx(a1)] * shl(a1, (a1) & 15))) else (acc)) ^ -26)); xs[_i] = shl(23, ((shr(acc, ((a2 ^ a1)) & 15) ^ acc)) & 15)
    if (xs[idx(((f0(xs[idx(a1)], a0, div(-28, w(mod(27, 7) + 8)))) if (div(w(34 + a2), w(mod(-35, 7) + 8))) < (xs[idx(a2)]) else (w(shr(-39, (41) & 15) + min(48, 30)))))]) < (a1):
        if (xs[idx(a0)]) < (-21):
            _i = idx(min(max(shl(w(a2 + -38), (w(a1 + -17)) & 15), w(div(-2, w(mod(a1, 7) + 8)) + min(a2, -31))), max(div((-47 | a1), w(mod(((a1) if (a2) < (a1) else (-44)), 7) + 8)), a2))); xs[_i] = mod(min(xs[idx(w(43 - a2))], div(w(a2 - -35), w(mod(w(a1 - a0), 7) + 8))), w(mod(a1, 7) + 8))
            _i = idx(xs[idx(w(shr(xs[idx(16)], (f0(a0, a0, a2)) & 15) - w(mod(a2, w(mod(a2, 7) + 8)) * (a0 | a1))))]); xs[_i] = mod(mod(w(w(a0 - a1) - a0), w(mod(a2, 7) + 8)), w(mod(w(-21 * (min(38, a2) | mod(15, w(mod(-6, 7) + 8)))), 7) + 8))
        else:
            acc = w(w(acc * 31) + f0(min(shl(div(a0, w(mod(22, 7) + 8)), (w(-48 - a2)) & 15), min(w(-4 + a1), 39)), max(shr(f0(a1, -11, a2), ((38 | a0)) & 15), min(min(-34, -43), shl(a2, (a0) & 15))), a1))
    else:
        acc = w(w(acc * 31) + (f0(xs[idx(-11)], ((a2 ^ a2) & acc), a0) | -23))
        acc = w(w(acc * 31) + ((max(xs[idx(w(a0 * -2))], max((-13 ^ a1), a1))) if (min(a0, (shl(a0, (40) & 15) & w(-36 + a0)))) < (w(a1 + -28)) else (((acc | f0(a1, -25, -38)) & shl(((-29) if (34) < (a1) else (a1)), (w(-50 + a0)) & 15)))))
    return (a0 ^ shr(mod(5, w(mod(w(-19 * a0), 7) + 8)), (shr((a2 ^ a1), (a1) & 15)) & 15))
def f2(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + 15)
    return a0
def main():
    global acc
    for i99486 in range(7):
        v56106 = i99486
        _i = idx(max(f1(w(acc + i99486), -36, shr((-1 & 38), (mod(47, w(mod(i99486, 7) + 8))) & 15)), shr(v56106, (acc) & 15))); xs[_i] = ((min(v56106, max(v56106, v56106)) & shl(max(i99486, -48), (w(v56106 * -44)) & 15)) ^ (acc ^ acc))
    _i = idx(div(xs[idx(w((8 ^ 37) + div(4, w(mod(21, 7) + 8))))], w(mod(20, 7) + 8))); xs[_i] = 20
    if (shr(42, (-19) & 15)) < (w(shr(min(6, w(-12 + 46)), (acc) & 15) * mod(-50, w(mod(mod((-44 | 30), w(mod(w(13 * 36), 7) + 8)), 7) + 8)))):
        acc = w(w(acc * 31) + w(mod(f2(27, -25, -12), w(mod(div(w(6 + -48), w(mod(-30, 7) + 8)), 7) + 8)) * w(div(w(-8 + 7), w(mod(f0(4, -25, -39), 7) + 8)) * shl(w(-33 * 38), (7) & 15))))
        v53254 = max((((48 | 18) ^ -49) | min(48, max(-15, 31))), f1(div(shr(-23, (-3) & 15), w(mod(w(-50 - 32), 7) + 8)), w((38 & -13) * -29), div(-44, w(mod(44, 7) + 8))))
        v57701 = min((v53254 | v53254), -30)
    else:
        acc = w(w(acc * 31) + -17)
    acc = w(w(acc * 31) + -35)
    _i = idx(min(acc, 34)); xs[_i] = -27
    for i55566 in range(5):
        _i = idx((i55566 & mod(acc, w(mod((w(i55566 + i55566) & shl(3, (i55566) & 15)), 7) + 8)))); xs[_i] = (acc | i55566)
        v17745 = f0((acc & shl((i55566 | 33), ((i55566 | i55566)) & 15)), -43, 44)
        acc = w(w(acc * 31) + 27)
    if (-24) < (((-1 ^ (((-31 & -33)) if (acc) < (acc) else ((10 ^ 50)))) & min(3, -50))):
        if (acc) < (21):
            acc = w(w(acc * 31) + shl(w(max((-45 ^ 21), f2(44, -17, -35)) - ((acc) if ((5 | -5)) < (w(0 + -30)) else ((21 ^ 17)))), (w(-25 * -26)) & 15))
            _i = idx(div(49, w(mod(w(31 + xs[idx(div(0, w(mod(-32, 7) + 8)))]), 7) + 8))); xs[_i] = shr(w(max(w(8 - 30), 15) * acc), (29) & 15)
            v15913 = min(acc, mod(34, w(mod(-35, 7) + 8)))
        else:
            acc = w(w(acc * 31) + (34 | 34))
            acc = w(w(acc * 31) + w((((acc) if (w(1 - -50)) < ((7 ^ -15)) else (w(-31 * 7))) & -47) + w(34 + xs[idx(min(-16, 2))])))
        for i34754 in range(3):
            _i = idx((xs[idx(w(w(0 * i34754) - w(i34754 + i34754)))] ^ w(i34754 + (mod(-18, w(mod(i34754, 7) + 8)) & xs[idx(i34754)])))); xs[_i] = ((div(min(i34754, i34754), w(mod(min(acc, f1(i34754, i34754, i34754)), 7) + 8))) if (max(i34754, i34754)) < (xs[idx(i34754)]) else (i34754))
            v81432 = i34754
        _i = idx(min(acc, w(-17 + (f2(28, 46, -20) | 25)))); xs[_i] = w(w(acc + -28) - w(-13 - acc))
    else:
        _i = idx(-29); xs[_i] = (((((-42) if (-28) < (46) else (45)) & 14) & 30) ^ shr(30, (acc) & 15))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
