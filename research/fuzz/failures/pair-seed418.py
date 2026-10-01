
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
    acc = w(w(acc * 31) + a1)
    return w(a1 - mod(mod((a0 & a1), w(mod(w(a0 * a0), 7) + 8)), w(mod(34, 7) + 8)))
def f1(a0, a1):
    global acc
    v17034 = xs[idx(((-23) if (w(a0 * 34)) < ((acc ^ -34)) else ((f0(a0, a1) & (a1 & 18)))))]
    _i = idx(a1); xs[_i] = a1
    for i55343 in range(11):
        acc = w(w(acc * 31) + -41)
    return -40
def f2(a0):
    global acc
    v43104 = a0
    _i = idx(w(v43104 + -30)); xs[_i] = (a0 & w(((v43104) if (shl(-46, (49) & 15)) < ((-11 | v43104)) else (w(-38 - 19))) * div(acc, w(mod(-8, 7) + 8))))
    return max(shr(shl(f1(a0, 18), (acc) & 15), (-20) & 15), a0)
def main():
    global acc
    if (min((w(div(8, w(mod(17, 7) + 8)) + 6) & acc), shr(mod((38 ^ -34), w(mod(div(10, w(mod(-1, 7) + 8)), 7) + 8)), (((-6) if (w(41 + 20)) < (mod(-11, w(mod(-35, 7) + 8))) else (w(-18 * -33)))) & 15))) < (acc):
        _i = idx(mod((-42 ^ -50), w(mod((xs[idx(mod(43, w(mod(-3, 7) + 8)))] & 7), 7) + 8))); xs[_i] = -28
        v54952 = max(-30, min(w((-8 & -16) * 1), (min(9, -48) & shl(17, (1) & 15))))
        if ((w((v54952 ^ xs[idx(v54952)]) + mod(acc, w(mod(w(v54952 + v54952), 7) + 8))) | shl((v54952 ^ v54952), (shl(mod(-29, w(mod(v54952, 7) + 8)), (f2(v54952)) & 15)) & 15))) < (w(w(v54952 + 6) - max(w(((-19) if (v54952) < (v54952) else (-39)) - ((v54952) if (-26) < (34) else (v54952))), div(v54952, w(mod(w(v54952 - 29), 7) + 8))))):
            _i = idx(v54952); xs[_i] = -37
        else:
            v4978 = w(shr(((v54952) if (w(v54952 - -40)) < (v54952) else (min(v54952, v54952))), (w(w(-38 - v54952) * f0(v54952, -30))) & 15) * shl(w(((v54952) if (34) < (v54952) else (v54952)) + mod(-13, w(mod(v54952, 7) + 8))), (max((-40 & v54952), w(36 * -32))) & 15))
    else:
        v41968 = 12
    acc = w(w(acc * 31) + (div(div(min(8, 4), w(mod(min(-49, 20), 7) + 8)), w(mod((div(9, w(mod(0, 7) + 8)) ^ max(33, 43)), 7) + 8)) | 8))
    if (acc) < (shl(37, (div((w(-14 + 34) & acc), w(mod(f1((36 & 39), ((-2) if (5) < (-40) else (41))), 7) + 8))) & 15)):
        acc = w(w(acc * 31) + -42)
    else:
        v39981 = (min(((5 | -25) ^ w(28 - 42)), -49) & w(acc - max((23 ^ 33), ((-40) if (-49) < (29) else (32)))))
        v63510 = w(acc * ((f0(max(v39981, 35), shr(-47, (v39981) & 15))) if (acc) < (shr((-48 & -34), (mod(v39981, w(mod(v39981, 7) + 8))) & 15)) else (-1)))
    v10136 = -47
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
