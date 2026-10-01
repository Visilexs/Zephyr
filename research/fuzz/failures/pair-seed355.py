
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
    acc = w(w(acc * 31) + ((a0 & min(a0, min(a0, a0))) | a0))
    for i98265 in range(11):
        _i = idx(i98265); xs[_i] = 21
    v74015 = w(xs[idx(xs[idx(xs[idx(a0)])])] * min(a0, (mod(a0, w(mod(19, 7) + 8)) ^ (a0 & -23))))
    return a0
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + mod(min(-1, (w(a0 - a1) & div(31, w(mod(18, 7) + 8)))), w(mod((20 & 4), 7) + 8)))
    for i64978 in range(3):
        acc = w(w(acc * 31) + min(shr((f0(i64978) & -6), (div((-37 & a2), w(mod((a1 | 22), 7) + 8))) & 15), w(-19 + 16)))
    return w(min((w(13 - a1) & ((a2) if (-41) < (-43) else (a1))), w(a1 - acc)) + ((a0) if (w(((a1) if (a0) < (a0) else (a1)) - w(a2 * a2))) < (-20) else (xs[idx(a1)])))
def main():
    global acc
    acc = w(w(acc * 31) + ((5 | max(mod(7, w(mod(14, 7) + 8)), -34)) & f1(div(mod(45, w(mod(-7, 7) + 8)), w(mod(max(5, 47), 7) + 8)), xs[idx(37)], ((-42 | 42) | 0))))
    acc = w(w(acc * 31) + -15)
    _i = idx(f0(w(-44 + (16 & w(-30 - 30))))); xs[_i] = xs[idx(acc)]
    v12777 = min(((((acc) if (w(23 - -43)) < (((-47) if (18) < (25) else (50))) else (f1(3, 46, 23)))) if (f1((39 & -7), (49 & 16), acc)) < (w(mod(-31, w(mod(-24, 7) + 8)) + f1(1, 9, -24))) else ((w(42 * 42) | -15))), w(div(-48, w(mod(w(32 * -4), 7) + 8)) + (acc ^ shl(-49, (43) & 15))))
    acc = w(w(acc * 31) + shr(w(xs[idx(((-50) if (-41) < (-45) else (44)))] + ((shr(v12777, (v12777) & 15)) if (max(49, 4)) < (shr(v12777, (v12777) & 15)) else (w(v12777 * -29)))), (w(v12777 * (46 | div(37, w(mod(v12777, 7) + 8))))) & 15))
    _i = idx(v12777); xs[_i] = f0(shr(v12777, (div(max(7, 40), w(mod(xs[idx(30)], 7) + 8))) & 15))
    _i = idx(mod(42, w(mod(shl(v12777, (w(mod(v12777, w(mod(46, 7) + 8)) * -1)) & 15), 7) + 8))); xs[_i] = v12777
    for i59129 in range(3):
        if (max(max(w(max(i59129, i59129) - acc), (div(22, w(mod(v12777, 7) + 8)) & shr(-5, (14) & 15))), min(v12777, w(xs[idx(-30)] + i59129)))) < (xs[idx((i59129 & (-3 & max(19, 44))))]):
            acc = w(w(acc * 31) + mod(48, w(mod(xs[idx(i59129)], 7) + 8)))
            acc = w(w(acc * 31) + i59129)
            v27469 = (shl(xs[idx(f1(v12777, i59129, i59129))], ((-20 ^ f1(49, v12777, 38))) & 15) & -26)
        else:
            _i = idx(v12777); xs[_i] = (max(xs[idx(-39)], (v12777 ^ f1(-40, 43, 19))) | max(min(shr(27, (0) & 15), ((v12777) if (v12777) < (-10) else (v12777))), -16))
        if (w(max(v12777, ((w(15 + i59129)) if (w(i59129 * v12777)) < ((v12777 ^ 45)) else (i59129))) - v12777)) < ((acc & (f0(w(v12777 * i59129)) & acc))):
            _i = idx(min(div(div(shr(v12777, (v12777) & 15), w(mod(20, 7) + 8)), w(mod(27, 7) + 8)), v12777)); xs[_i] = w(-17 + ((min(i59129, v12777) | (-1 | 4)) | i59129))
            v4875 = i59129
            acc = w(w(acc * 31) + w(i59129 + f1(((i59129 & i59129) | w(i59129 - i59129)), shl(-16, (v12777) & 15), (-42 | w(-11 + i59129)))))
        else:
            acc = w(w(acc * 31) + (max(((-33) if (23) < (min(i59129, 44)) else (i59129)), acc) | max(-24, shl(xs[idx(-23)], (w(-37 + -7)) & 15))))
            _i = idx(acc); xs[_i] = -18
        for i82338 in range(10):
            v53690 = (i82338 ^ v12777)
            _i = idx(min(5, acc)); xs[_i] = mod(10, w(mod(w(mod((46 & 20), w(mod(w(i59129 + i82338), 7) + 8)) + acc), 7) + 8))
            acc = w(w(acc * 31) + v53690)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
