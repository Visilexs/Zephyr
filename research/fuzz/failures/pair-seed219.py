
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
    acc = w(w(acc * 31) + mod(mod(w(6 - (-34 | a1)), w(mod(min(w(42 * a1), max(a0, -49)), 7) + 8)), w(mod(a1, 7) + 8)))
    return (3 & -40)
def f1(a0, a1):
    global acc
    for i84495 in range(12):
        acc = w(w(acc * 31) + i84495)
        if (((xs[idx(min(xs[idx(-19)], (i84495 ^ -3)))]) if (w(i84495 + (a0 & a0))) < (38) else (xs[idx(w(w(i84495 * a1) - ((24) if (27) < (i84495) else (50))))]))) < (max(shl(i84495, (min(shr(i84495, (35) & 15), 10)) & 15), (w(max(a1, a0) + mod(34, w(mod(a1, 7) + 8))) ^ shl(shl(a0, (a1) & 15), (shr(i84495, (-18) & 15)) & 15)))):
            acc = w(w(acc * 31) + f0(min(div(a1, w(mod(a0, 7) + 8)), a0), ((shl(shl(38, (18) & 15), (mod(a0, w(mod(i84495, 7) + 8))) & 15)) if (-23) < ((mod(-5, w(mod(a0, 7) + 8)) & ((5) if (a1) < (-42) else (-37)))) else (w(w(a1 * -17) * (-17 | a1)))), div(35, w(mod(acc, 7) + 8))))
            _i = idx(a1); xs[_i] = max(i84495, a1)
            acc = w(w(acc * 31) + w(a1 * shl(((a0) if (w(a1 * 33)) < (w(a0 + a1)) else (((a0) if (a0) < (-24) else (a0)))), (-43) & 15)))
        else:
            v746 = i84495
            _i = idx(w(shr(xs[idx(f0(9, a1, 24))], (6) & 15) - ((w(31 * (-50 & a1))) if (shl(a0, (mod(v746, w(mod(a0, 7) + 8))) & 15)) < (f0(min(-44, -24), f0(7, a0, a0), a0)) else (w(12 + 44))))); xs[_i] = ((v746 | mod(shr(a1, (v746) & 15), w(mod(v746, 7) + 8))) ^ w(div(w(-22 + 43), w(mod(max(42, 38), 7) + 8)) * acc))
        v76847 = (a1 | (min(24, (-8 | a1)) & f0(f0(26, a0, -31), 12, (i84495 | -7))))
    for i57535 in range(3):
        if (w(w(xs[idx(f0(a1, -27, -34))] + shr(a0, (acc) & 15)) - a1)) < (a1):
            _i = idx(i57535); xs[_i] = mod(((mod(42, w(mod(a0, 7) + 8)) & max(-44, i57535)) ^ min(acc, ((29) if (i57535) < (a0) else (i57535)))), w(mod(((shr(i57535, (w(-44 + -7)) & 15)) if ((w(a0 * -40) ^ div(22, w(mod(a0, 7) + 8)))) < ((min(i57535, a0) ^ min(i57535, a0))) else (shl(-2, ((a0 & -40)) & 15))), 7) + 8))
            _i = idx(shr(-35, (xs[idx(((a1) if ((a0 ^ a0)) < (mod(a1, w(mod(-4, 7) + 8))) else (a0)))]) & 15)); xs[_i] = acc
        else:
            _i = idx(a0); xs[_i] = (div((max(a0, -45) | shr(a0, (-10) & 15)), w(mod(mod(xs[idx(i57535)], w(mod((i57535 | -27), 7) + 8)), 7) + 8)) | f0(shl((-22 | -11), (a1) & 15), i57535, max(a1, a0)))
    return xs[idx(shr(a1, (acc) & 15))]
def f2(a0):
    global acc
    acc = w(w(acc * 31) + -38)
    return a0
def main():
    global acc
    v75476 = xs[idx(w(div(xs[idx(45)], w(mod(-31, 7) + 8)) + w(xs[idx(5)] - (45 & -40))))]
    if ((f0((w(v75476 * v75476) | w(v75476 + -13)), v75476, acc) & (v75476 ^ w(v75476 * (v75476 ^ -22))))) < (max(28, v75476)):
        acc = w(w(acc * 31) + 3)
        acc = w(w(acc * 31) + min(mod(min((v75476 ^ -47), v75476), w(mod(mod(9, w(mod(v75476, 7) + 8)), 7) + 8)), 20))
        acc = w(w(acc * 31) + min(w(min(-33, v75476) - ((shl(v75476, (-4) & 15)) if (div(-17, w(mod(v75476, 7) + 8))) < (((v75476) if (-43) < (v75476) else (-50))) else (div(v75476, w(mod(v75476, 7) + 8))))), f0(div(v75476, w(mod(v75476, 7) + 8)), div(-30, w(mod(f1(v75476, 17), 7) + 8)), v75476)))
    else:
        v18326 = w(div(-31, w(mod((shl(v75476, (20) & 15) ^ ((v75476) if (v75476) < (v75476) else (v75476))), 7) + 8)) - shr(v75476, (7) & 15))
    if (f0(min((acc & v75476), 32), 2, shr(v75476, (v75476) & 15))) < (v75476):
        _i = idx(((acc) if (max(v75476, v75476)) < ((v75476 & (v75476 & acc))) else (shl(div(((-24) if (v75476) < (43) else (42)), w(mod(shr(v75476, (v75476) & 15), 7) + 8)), (w(((v75476) if (10) < (4) else (v75476)) * w(v75476 - v75476))) & 15)))); xs[_i] = max(div(acc, w(mod(v75476, 7) + 8)), (acc ^ f1(40, acc)))
        for i56885 in range(6):
            _i = idx(acc); xs[_i] = acc
            v17930 = shl(w(min((v75476 & v75476), (47 | i56885)) + mod(acc, w(mod(i56885, 7) + 8))), (v75476) & 15)
    else:
        acc = w(w(acc * 31) + (div(-22, w(mod(div((v75476 & v75476), w(mod((19 & 10), 7) + 8)), 7) + 8)) ^ shr((div(v75476, w(mod(v75476, 7) + 8)) & v75476), (((v75476 | v75476) | w(45 * -46))) & 15)))
        v46292 = (-33 | w(w((12 | v75476) - (48 ^ 26)) - acc))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
