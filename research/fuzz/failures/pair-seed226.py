
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
    for i77827 in range(1):
        acc = w(w(acc * 31) + w(((i77827) if (max(max(-48, i77827), w(a0 * a0))) < (i77827) else (i77827)) + (i77827 & -14)))
    _i = idx(a0); xs[_i] = 5
    acc = w(w(acc * 31) + a0)
    return shl(shl(shr(w(a0 * a0), (w(a0 + a0)) & 15), ((33 & min(a0, 34))) & 15), (min(a0, a0)) & 15)
def f1(a0, a1):
    global acc
    for i31897 in range(2):
        if ((xs[idx(a0)] | xs[idx(xs[idx((i31897 ^ 36))])])) < (a1):
            _i = idx(shr((shl(min(a0, a1), (5) & 15) & (shr(i31897, (a1) & 15) & f0(-4))), (max(w(xs[idx(21)] * (-18 & i31897)), w(shr(a0, (a0) & 15) * (-15 & 25)))) & 15)); xs[_i] = mod(w(min((44 ^ i31897), (a0 ^ a1)) + mod(w(i31897 * a1), w(mod(f0(-8), 7) + 8))), w(mod((f0(shr(i31897, (a0) & 15)) ^ -8), 7) + 8))
            acc = w(w(acc * 31) + w(xs[idx(div((a1 ^ a1), w(mod(max(i31897, 0), 7) + 8)))] * a1))
        else:
            v58962 = 17
            acc = w(w(acc * 31) + w(acc - max(w((-24 ^ 16) - 2), div(w(37 - -33), w(mod(((40) if (1) < (a1) else (a1)), 7) + 8)))))
        acc = w(w(acc * 31) + a1)
        acc = w(w(acc * 31) + w(f0(f0(mod(a0, w(mod(i31897, 7) + 8)))) + div(w(f0(a1) - w(a0 * i31897)), w(mod(xs[idx((a1 ^ a1))], 7) + 8))))
    _i = idx(f0(max(max((a1 & a0), a1), shr(w(a1 - a1), (max(a0, a1)) & 15)))); xs[_i] = f0(-9)
    return (a0 | (a1 | 24))
def f2(a0, a1, a2):
    global acc
    v28507 = a2
    _i = idx(w(min(shr(a0, (a0) & 15), (f1(-49, v28507) ^ xs[idx(-21)])) - a0)); xs[_i] = mod(shl(37, (min((v28507 | -7), a2)) & 15), w(mod(shr(w(v28507 - (20 | a1)), (max(((18) if (a0) < (a0) else (50)), shl(a0, (a0) & 15))) & 15), 7) + 8))
    if (acc) < (((a2) if (a0) < (xs[idx(a1)]) else (a1))):
        if (-43) < (((6) if (shl(mod(22, w(mod(-40, 7) + 8)), ((-19 & div(a1, w(mod(-42, 7) + 8)))) & 15)) < (xs[idx((div(a2, w(mod(-36, 7) + 8)) & 39))]) else (f1(xs[idx(shr(a1, (-11) & 15))], w(a2 * a0))))):
            acc = w(w(acc * 31) + w(-27 * div(1, w(mod(xs[idx(min(a0, 29))], 7) + 8))))
        else:
            _i = idx(w(w(shr(a2, (a0) & 15) - 40) + shl(shl(a1, (f0(12)) & 15), (-26) & 15))); xs[_i] = ((v28507) if (w(a0 * shr(a2, (div(v28507, w(mod(a0, 7) + 8))) & 15))) < (w(a2 - a0)) else (w((max(a2, 25) ^ v28507) + w(xs[idx(a0)] + min(a2, a1)))))
            _i = idx(-21); xs[_i] = xs[idx(shr(a0, (a0) & 15))]
        acc = w(w(acc * 31) + a1)
    else:
        acc = w(w(acc * 31) + f1(28, a1))
        acc = w(w(acc * 31) + f1(((a0 | f0(v28507)) & 35), a0))
    return min(xs[idx(mod(acc, w(mod(-50, 7) + 8)))], a1)
def f3(a0):
    global acc
    v78641 = 29
    acc = w(w(acc * 31) + min(max(acc, mod(shr(a0, (v78641) & 15), w(mod(shr(0, (a0) & 15), 7) + 8))), a0))
    _i = idx(shr(v78641, (v78641) & 15)); xs[_i] = (w(v78641 * v78641) & w((a0 ^ v78641) * w(acc * f2(v78641, a0, a0))))
    return shr(w(xs[idx(w(a0 + 12))] + w(-11 * mod(-42, w(mod(0, 7) + 8)))), (-27) & 15)
def main():
    global acc
    _i = idx(f1((shl(f3(25), (mod(12, w(mod(-11, 7) + 8))) & 15) | (shr(-17, (22) & 15) & w(44 * -34))), max(-33, (f1(18, 18) | -3)))); xs[_i] = ((min(mod(10, w(mod(47, 7) + 8)), -12) & min(min(19, 21), 48)) | (max(28, max(1, 16)) & xs[idx(((5) if (15) < (-36) else (34)))]))
    for i39606 in range(4):
        for i81125 in range(10):
            v76676 = i81125
            _i = idx(xs[idx(-44)]); xs[_i] = shr(shl((f0(-34) ^ (33 ^ 10)), ((v76676 ^ (i81125 | 33))) & 15), (xs[idx(i39606)]) & 15)
        if (div(i39606, w(mod(acc, 7) + 8))) < (div(25, w(mod(xs[idx((div(i39606, w(mod(6, 7) + 8)) | i39606))], 7) + 8))):
            _i = idx(26); xs[_i] = shl(shl(f0(mod(-12, w(mod(i39606, 7) + 8))), (f3((i39606 ^ 24))) & 15), (shl(i39606, (-16) & 15)) & 15)
        else:
            _i = idx(acc); xs[_i] = w(shl((i39606 ^ ((i39606) if (-23) < (i39606) else (-48))), ((-23 | w(22 * i39606))) & 15) - i39606)
            _i = idx(((f2((mod(i39606, w(mod(18, 7) + 8)) & -11), ((min(-13, i39606)) if (-10) < (max(i39606, -4)) else (((i39606) if (i39606) < (-44) else (-11)))), shl(xs[idx(33)], (w(-29 - i39606)) & 15))) if (mod(mod((i39606 | 7), w(mod(((i39606) if (i39606) < (35) else (-22)), 7) + 8)), w(mod(-23, 7) + 8))) < (div(div(xs[idx(28)], w(mod(((39) if (-13) < (i39606) else (i39606)), 7) + 8)), w(mod(-26, 7) + 8))) else ((w(acc + shr(i39606, (i39606) & 15)) ^ i39606)))); xs[_i] = i39606
    if (acc) < (div((-5 ^ mod(-43, w(mod(39, 7) + 8))), w(mod((max(w(-6 - -30), (24 & -2)) ^ -40), 7) + 8))):
        v67930 = min(w(-32 * max(50, min(-36, 8))), ((49 | shr(41, (9) & 15)) & div(w(-13 * 18), w(mod(-7, 7) + 8))))
        if (max(14, -33)) < (w(f1(f0(max(37, v67930)), w(f1(v67930, -11) * v67930)) * v67930)):
            _i = idx(((((v67930) if (f0(acc)) < (v67930) else (-34))) if (v67930) < (mod(((acc) if (-39) < (xs[idx(v67930)]) else (((v67930) if (v67930) < (v67930) else (34)))), w(mod((div(26, w(mod(-4, 7) + 8)) | v67930), 7) + 8))) else (w(-41 + f3(acc))))); xs[_i] = (25 & acc)
            v61345 = (-1 & v67930)
        else:
            v49326 = -44
            v95119 = 2
        _i = idx(v67930); xs[_i] = (w(w(xs[idx(v67930)] * w(36 * v67930)) - mod(max(v67930, 15), w(mod(shl(-17, (v67930) & 15), 7) + 8))) ^ -46)
    else:
        acc = w(w(acc * 31) + 32)
    acc = w(w(acc * 31) + max((-1 ^ acc), shr(-37, (w((-42 ^ -46) - -24)) & 15)))
    acc = w(w(acc * 31) + mod(((((16) if ((30 ^ 50)) < (div(18, w(mod(-27, 7) + 8))) else (max(16, -19)))) if ((((-17) if (27) < (30) else (30)) | max(21, 12))) < (min(shl(23, (7) & 15), w(22 - 19))) else (max((21 | 8), shl(-14, (14) & 15)))), w(mod(max(w(min(9, -34) * (-10 | 36)), 27), 7) + 8)))
    v21011 = (min(shl(-45, (22) & 15), div(19, w(mod(w(-12 * 14), 7) + 8))) & ((w(12 * -40) ^ -12) | min(max(6, -26), xs[idx(-30)])))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
