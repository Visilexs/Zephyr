
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
    if (min(-19, ((a0) if (-42) < (max(max(a0, 24), a1)) else (w(mod(a1, w(mod(a1, 7) + 8)) + a1))))) < (27):
        for i95658 in range(4):
            v56910 = w(max(28, (w(46 - a1) ^ w(i95658 + a0))) + div((i95658 | a0), w(mod((((25 & i95658)) if (w(24 + i95658)) < ((3 ^ a1)) else (shr(a1, (i95658) & 15))), 7) + 8)))
    else:
        acc = w(w(acc * 31) + -49)
    acc = w(w(acc * 31) + (w((acc ^ max(a0, -45)) - acc) | a0))
    return w(shl(a0, (acc) & 15) - shl(acc, (-32) & 15))
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + xs[idx(shl(min((a2 ^ a0), (a2 | -9)), (-29) & 15))])
    v86899 = min((xs[idx(shr(a1, (13) & 15))] & min(30, w(a1 - a0))), ((min(f0(a1, 43), shl(a0, (-17) & 15))) if ((max(-39, a0) & xs[idx(a2)])) < (min(acc, w(a2 + a1))) else (-39)))
    return w(-16 - w(min(w(a2 - a1), shr(a2, (a0) & 15)) * a0))
def f2(a0):
    global acc
    for i2307 in range(8):
        for i67685 in range(10):
            _i = idx(xs[idx(mod(w((i2307 & 13) + ((i67685) if (i2307) < (a0) else (i67685))), w(mod(w(a0 - i2307), 7) + 8)))]); xs[_i] = -7
        for i92119 in range(9):
            _i = idx(mod(((w(-29 * a0) ^ w(-30 - i2307)) ^ shr(div(i2307, w(mod(i2307, 7) + 8)), (a0) & 15)), w(mod((((acc) if ((i92119 | 29)) < (acc) else (div(a0, w(mod(a0, 7) + 8)))) | i92119), 7) + 8))); xs[_i] = -36
            v80967 = w((xs[idx(acc)] ^ (xs[idx(4)] & i2307)) * -2)
        v44527 = -5
    return shr(acc, (w(acc + shr(shr(a0, (a0) & 15), (div(46, w(mod(38, 7) + 8))) & 15))) & 15)
def f3(a0):
    global acc
    for i59312 in range(5):
        if (w(shl(a0, (i59312) & 15) + a0)) < (-16):
            _i = idx(w(max(w(shl(i59312, (-36) & 15) - div(a0, w(mod(a0, 7) + 8))), f0((13 ^ i59312), i59312)) + (a0 ^ -21))); xs[_i] = max(-38, f0(f0(21, shl(-48, (4) & 15)), shl(w(24 + -28), (-11) & 15)))
            v25129 = w(div((acc | shl(i59312, (i59312) & 15)), w(mod(max(f2(i59312), shl(-26, (a0) & 15)), 7) + 8)) - w(min(-18, mod(i59312, w(mod(-27, 7) + 8))) - mod(a0, w(mod(xs[idx(i59312)], 7) + 8))))
        else:
            v22873 = shl(-10, (shr(i59312, (w(i59312 * shr(i59312, (i59312) & 15))) & 15)) & 15)
        _i = idx(w(-37 - i59312)); xs[_i] = xs[idx(mod(((48 ^ -15) ^ i59312), w(mod(shl(div(-18, w(mod(a0, 7) + 8)), (w(-38 - i59312)) & 15), 7) + 8)))]
    if (-5) < (a0):
        if (div((xs[idx(max(a0, 14))] ^ (shr(a0, (a0) & 15) ^ ((a0) if (a0) < (-12) else (a0)))), w(mod(w(a0 + shl(26, (shl(a0, (a0) & 15)) & 15)), 7) + 8))) < (f2(f1(div(w(a0 - 7), w(mod(acc, 7) + 8)), 14, shl(26, (f0(a0, a0)) & 15)))):
            v71045 = max(f1(-15, min(xs[idx(26)], a0), mod(a0, w(mod(acc, 7) + 8))), w((w(a0 + 36) | shr(34, (a0) & 15)) * -41))
        else:
            v57236 = min(w(f1(w(a0 * 23), f0(a0, a0), shr(-30, (-41) & 15)) + a0), a0)
        if (div(w(((a0) if (-9) < (w(47 - a0)) else (shl(a0, (a0) & 15))) * mod(((a0) if (a0) < (a0) else (-46)), w(mod(-24, 7) + 8))), w(mod(a0, 7) + 8))) < (max(a0, 30)):
            _i = idx(w((a0 | a0) * f0(div((a0 & a0), w(mod(mod(-21, w(mod(-23, 7) + 8)), 7) + 8)), ((w(-13 + -11)) if ((-43 | 13)) < (w(a0 - a0)) else (-30))))); xs[_i] = (xs[idx(w(acc * xs[idx(a0)]))] ^ div((max(a0, -44) ^ shr(a0, (a0) & 15)), w(mod(a0, 7) + 8)))
        else:
            acc = w(w(acc * 31) + w(a0 * min((acc & 42), mod(shr(-17, (37) & 15), w(mod(mod(49, w(mod(a0, 7) + 8)), 7) + 8)))))
    else:
        if (shr(w(div(min(a0, -16), w(mod((a0 & 16), 7) + 8)) + w(a0 * a0)), (((shr(mod(-10, w(mod(24, 7) + 8)), ((a0 ^ a0)) & 15)) if (w(w(a0 * a0) * ((36) if (a0) < (a0) else (a0)))) < ((a0 | (a0 ^ a0))) else (a0))) & 15)) < (mod(div(acc, w(mod(f2(w(34 * a0)), 7) + 8)), w(mod(a0, 7) + 8))):
            _i = idx(-4); xs[_i] = 49
            acc = w(w(acc * 31) + xs[idx(shr(46, (w(xs[idx(a0)] + -14)) & 15))])
        else:
            v76153 = -26
    acc = w(w(acc * 31) + acc)
    return f1(w(div(xs[idx(a0)], w(mod(w(-2 - -18), 7) + 8)) + div((44 & a0), w(mod(w(9 - a0), 7) + 8))), 28, a0)
def main():
    global acc
    for i5578 in range(11):
        acc = w(w(acc * 31) + w(f1(w(xs[idx(23)] + 22), (20 | w(10 + i5578)), f3(w(i5578 - i5578))) - w(46 * w(-49 + i5578))))
    if (w(shl(max(w(50 * -29), 19), ((shl(-50, (41) & 15) & mod(-6, w(mod(-44, 7) + 8)))) & 15) + -31)) < ((19 | 5)):
        _i = idx(-31); xs[_i] = 45
    else:
        acc = w(w(acc * 31) + acc)
        v32825 = -23
    v83797 = div(44, w(mod(max(((w(8 - 6)) if ((-6 ^ -17)) < (-43) else (div(-19, w(mod(20, 7) + 8)))), 37), 7) + 8))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
