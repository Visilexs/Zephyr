
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
    v48024 = max(25, div(mod(w(a0 + a0), w(mod(shr(a1, (37) & 15), 7) + 8)), w(mod(w(a0 + ((a1) if (a1) < (a0) else (a1))), 7) + 8)))
    v34622 = (w(-19 * w(-20 + w(v48024 * 44))) ^ max(w(a1 - w(v48024 * a1)), (div(a1, w(mod(32, 7) + 8)) | w(v48024 * -24))))
    v17517 = w(shr((w(v34622 * -14) & w(-17 + 30)), (min(a0, min(-29, a1))) & 15) + a1)
    return (xs[idx(w(shr(-25, (a1) & 15) + a1))] & a1)
def f1(a0, a1, a2):
    global acc
    if (div(a1, w(mod(w(acc * mod((a0 ^ a0), w(mod(div(40, w(mod(-32, 7) + 8)), 7) + 8))), 7) + 8))) < (mod(w(xs[idx(shr(a0, (-30) & 15))] * 33), w(mod(w(div(a1, w(mod(-27, 7) + 8)) - w(46 + w(49 + -41))), 7) + 8))):
        _i = idx(((min(max(a2, a2), w(div(a2, w(mod(-45, 7) + 8)) - div(-27, w(mod(a0, 7) + 8))))) if (a0) < (mod(f0(w(a1 + a0), 18), w(mod(mod(w(a1 + -9), w(mod((a0 & a0), 7) + 8)), 7) + 8))) else (7))); xs[_i] = 5
        _i = idx((-48 | shr(w(-29 - shr(-10, (a1) & 15)), ((acc & xs[idx(a1)])) & 15))); xs[_i] = w(a2 * w(w(acc - ((3) if (-38) < (-34) else (31))) - w(mod(42, w(mod(a1, 7) + 8)) - w(44 + -14))))
        v86801 = a1
    else:
        acc = w(w(acc * 31) + a2)
        _i = idx(div(acc, w(mod((a2 | a1), 7) + 8))); xs[_i] = shl(shr(35, (w(f0(-45, a0) - w(1 - a1))) & 15), ((((f0(a2, 22) | max(8, -46))) if (acc) < (6) else ((div(a1, w(mod(a2, 7) + 8)) & (-35 ^ a1))))) & 15)
    return shl(((a1) if (xs[idx(f0(a2, a1))]) < (a2) else (shl(a1, (mod(-12, w(mod(a2, 7) + 8))) & 15))), ((((a1 | a1) ^ w(-46 + -34)) | ((w(14 + a0)) if (max(a1, 24)) < (min(a0, -12)) else ((a1 | 46))))) & 15)
def f2(a0, a1, a2):
    global acc
    for i25605 in range(6):
        acc = w(w(acc * 31) + w(1 + i25605))
        v4379 = (max(a1, (shl(-49, (a0) & 15) ^ -43)) | w(w(min(-20, a1) + 43) + (xs[idx(-43)] | shl(-38, (i25605) & 15))))
        v47489 = w(xs[idx((((41) if (i25605) < (-37) else (a1)) ^ w(-14 - -17)))] * xs[idx(a0)])
    _i = idx((-4 ^ (shr(((16) if (a1) < (a0) else (-18)), (mod(4, w(mod(-15, 7) + 8))) & 15) & w(a2 + mod(a0, w(mod(a1, 7) + 8)))))); xs[_i] = shr(max((acc | a1), shr(acc, (f0(-39, a0)) & 15)), (mod(div(2, w(mod(shl(19, (20) & 15), 7) + 8)), w(mod(div(a0, w(mod(shr(a2, (-3) & 15), 7) + 8)), 7) + 8))) & 15)
    acc = w(w(acc * 31) + w(w(min(acc, acc) * div(a2, w(mod(((a2) if (a0) < (-46) else (-6)), 7) + 8))) * xs[idx(2)]))
    return min(w(max(a1, a0) - ((a2) if (w(11 + 19)) < (max(20, a1)) else ((a0 & -41)))), mod((w(-7 - a1) ^ 48), w(mod(34, 7) + 8)))
def f3(a0, a1, a2):
    global acc
    v36798 = a2
    acc = w(w(acc * 31) + ((w((acc & div(10, w(mod(48, 7) + 8))) + (((-36) if (a1) < (a2) else (5)) & ((v36798) if (a2) < (a1) else (a1))))) if ((44 & (a0 ^ (v36798 ^ 49)))) < (div(-14, w(mod(min((v36798 ^ a0), (42 | a1)), 7) + 8))) else (div(shl((a2 & -48), (42) & 15), w(mod(w(acc + v36798), 7) + 8)))))
    acc = w(w(acc * 31) + w(shr(max(w(-33 - a0), w(a1 * 17)), (w(w(-24 - 26) - 8)) & 15) * ((48 & a0) | f0(a2, (33 | -9)))))
    return w(f1(26, ((a1) if (a0) < ((a2 & a0)) else (a0)), w(((a1) if (a0) < (a1) else (7)) - w(37 + a0))) + max(w(25 * shr(a0, (-41) & 15)), -4))
def main():
    global acc
    if (shl(-40, ((acc | -9)) & 15)) < (31):
        _i = idx((f0(shr(w(30 + 11), (12) & 15), f1(shl(-3, (-38) & 15), shr(22, (40) & 15), acc)) & -46)); xs[_i] = xs[idx((w(acc + (-4 ^ 24)) ^ min(41, w(-15 - -3))))]
        acc = w(w(acc * 31) + shl(((f3((29 | 5), -5, -42)) if (xs[idx(7)]) < ((-26 & -44)) else (shr(-48, ((-47 | -7)) & 15))), ((shl((-49 ^ 12), (div(-2, w(mod(23, 7) + 8))) & 15) ^ acc)) & 15))
    else:
        if (mod(mod(w(f0(-35, 50) - max(24, 37)), w(mod(f0(14, -13), 7) + 8)), w(mod(16, 7) + 8))) < (((max(-50, 29) ^ mod(shr(-28, (14) & 15), w(mod(w(7 + 36), 7) + 8))) ^ min(-8, (min(14, -46) & 44)))):
            _i = idx(max(min(xs[idx((28 ^ -31))], -9), -47)); xs[_i] = 11
        else:
            v378 = -45
        acc = w(w(acc * 31) + shr(max(36, max(max(33, -20), -20)), (div(21, w(mod(-25, 7) + 8))) & 15))
    acc = w(w(acc * 31) + (div(f3(min(38, 20), w(-22 + 14), w(-34 - 48)), w(mod(((34 & 4) | xs[idx(-36)]), 7) + 8)) & w(w(min(-11, 9) + 38) * (f3(15, -36, 24) ^ ((28) if (12) < (34) else (-47))))))
    v25675 = -28
    v75702 = mod(shl(w(f3(v25675, v25675, v25675) * 30), (w(v25675 + f0(4, -28))) & 15), w(mod(acc, 7) + 8))
    _i = idx(shl(div(((((-11) if (17) < (v25675) else (v25675))) if (acc) < (acc) else (w(v75702 * v25675))), w(mod(max(v75702, (28 | 20)), 7) + 8)), (v75702) & 15)); xs[_i] = ((((w(3 - -10) ^ (v25675 | 6))) if (min(w(16 + 33), (v75702 | v75702))) < (((v75702 & v75702) | acc)) else ((div(v75702, w(mod(v25675, 7) + 8)) | xs[idx(-44)]))) & -26)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
