
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
    v46879 = -33
    if (min(w(a0 * w(w(34 + a1) + w(24 - a1))), div(a0, w(mod(-16, 7) + 8)))) < (a1):
        if (shr(w(w((31 ^ -34) + min(a1, a1)) * min((-12 & 9), w(15 + a0))), (w((((50) if (v46879) < (a0) else (v46879)) & w(-50 + a1)) + a1)) & 15)) < (div((shr(xs[idx(20)], (28) & 15) ^ shl(a1, (max(v46879, 48)) & 15)), w(mod(max(w(w(-3 - a0) * (v46879 | a1)), -20), 7) + 8))):
            v42178 = acc
        else:
            _i = idx(min(shr(shr(-33, (w(v46879 - -45)) & 15), (shl(-29, (w(23 - -19)) & 15)) & 15), a1)); xs[_i] = a0
        if (a1) < (div(min(acc, (xs[idx(a1)] | 42)), w(mod(-26, 7) + 8))):
            v26867 = a0
            acc = w(w(acc * 31) + shr(mod(xs[idx(w(-50 + 22))], w(mod(mod(div(a1, w(mod(v26867, 7) + 8)), w(mod(w(v26867 - v26867), 7) + 8)), 7) + 8)), (a0) & 15))
            _i = idx(shl(div(min(xs[idx(a1)], a0), w(mod(-28, 7) + 8)), (shr(w(xs[idx(a1)] + min(v26867, a1)), (w(w(v26867 - -38) + min(41, -1))) & 15)) & 15)); xs[_i] = a1
        else:
            _i = idx(max(xs[idx(shl((a0 | -2), (-44) & 15))], (((max(a1, 50) & w(a0 + a1))) if (w(w(a1 + a1) - (2 ^ v46879))) < (shl(((a1) if (-25) < (27) else (a1)), (w(49 + v46879)) & 15)) else (min(42, a1))))); xs[_i] = 30
        v81467 = w(a0 - (w(w(a1 + -36) + v46879) & (v46879 ^ max(a1, v46879))))
    else:
        for i25066 in range(2):
            acc = w(w(acc * 31) + w((max(((a1) if (v46879) < (29) else (32)), 50) ^ v46879) + i25066))
            acc = w(w(acc * 31) + w(min(xs[idx(xs[idx(-44)])], (i25066 & (i25066 | v46879))) * (w(v46879 - v46879) ^ xs[idx(acc)])))
        v78398 = (w(min(37, mod(26, w(mod(v46879, 7) + 8))) + ((xs[idx(-11)]) if (-33) < (w(a1 * a1)) else ((a0 & v46879)))) | a1)
    acc = w(w(acc * 31) + -30)
    return a0
def f1(a0):
    global acc
    if ((w(w(div(a0, w(mod(15, 7) + 8)) * div(a0, w(mod(a0, 7) + 8))) + a0) | div(div((-28 & a0), w(mod(acc, 7) + 8)), w(mod((min(26, -32) & (a0 & a0)), 7) + 8)))) < (a0):
        acc = w(w(acc * 31) + acc)
    else:
        _i = idx(a0); xs[_i] = a0
        if (38) < (w(w(max(-13, w(a0 + a0)) * shl(min(a0, a0), (a0) & 15)) * min(a0, div(div(-46, w(mod(a0, 7) + 8)), w(mod(w(a0 + a0), 7) + 8))))):
            v46407 = a0
            v25888 = acc
            _i = idx(acc); xs[_i] = ((f0(v25888, xs[idx(a0)])) if (mod(acc, w(mod(f0(w(v46407 + v46407), -50), 7) + 8))) < (-17) else (v25888))
        else:
            _i = idx(w(-2 + ((f0(a0, 47) & a0) | -39))); xs[_i] = shr((shr(((47) if (a0) < (41) else (a0)), ((a0 ^ a0)) & 15) & div(max(13, -25), w(mod(((-4) if (1) < (-41) else (42)), 7) + 8))), (mod(((a0) if (w(a0 + a0)) < (mod(a0, w(mod(-46, 7) + 8))) else ((a0 ^ a0))), w(mod(a0, 7) + 8))) & 15)
    v84827 = shl(w(a0 - (f0(a0, 30) | shl(a0, (3) & 15))), ((min(-1, (4 & a0)) & 19)) & 15)
    for i6453 in range(11):
        acc = w(w(acc * 31) + mod(div(30, w(mod(((max(-26, a0)) if ((a0 ^ -33)) < ((-9 ^ v84827)) else (shr(a0, (i6453) & 15))), 7) + 8)), w(mod(div(f0(v84827, xs[idx(41)]), w(mod(acc, 7) + 8)), 7) + 8)))
    return w(w(f0(((6) if (48) < (42) else (-40)), (a0 & a0)) * max(a0, xs[idx(a0)])) * (((a0 | -27) & a0) ^ xs[idx(shl(a0, (-43) & 15))]))
def f2(a0):
    global acc
    v34782 = 6
    v55331 = ((-31) if (-10) < ((w(max(v34782, 29) + f1(-47)) | max(w(v34782 - -40), (v34782 | v34782)))) else (v34782))
    return 2
def f3(a0, a1):
    global acc
    v59805 = w(acc * f0(a0, min((a1 ^ a1), a1)))
    _i = idx(a0); xs[_i] = w(min((w(-23 - a1) & xs[idx(-39)]), a1) * v59805)
    for i71067 in range(7):
        if (((acc) if (38) < ((max(w(-21 - i71067), -27) | shr(-49, (shl(-11, (i71067) & 15)) & 15))) else (shl(max(div(a1, w(mod(-41, 7) + 8)), (-22 ^ 17)), (mod(acc, w(mod(-21, 7) + 8))) & 15)))) < (min((xs[idx(shr(a0, (a1) & 15))] ^ mod((-13 ^ a1), w(mod(v59805, 7) + 8))), shl((min(a0, 6) & w(i71067 * a1)), (a0) & 15))):
            _i = idx(-19); xs[_i] = min((w(w(i71067 - a0) - f1(a0)) ^ min((29 & -20), min(18, a1))), (47 & min(v59805, ((49) if (a0) < (a0) else (i71067)))))
            acc = w(w(acc * 31) + max(div(min((v59805 | -25), xs[idx(12)]), w(mod(a0, 7) + 8)), shl(shl((-1 | i71067), (-36) & 15), (a0) & 15)))
        else:
            _i = idx(shl(shl(w(w(-38 - i71067) - a0), (div(a0, w(mod(acc, 7) + 8))) & 15), (acc) & 15)); xs[_i] = div(f2(f1(w(v59805 + -21))), w(mod((shr(shr(i71067, (49) & 15), (w(a0 - -5)) & 15) | -28), 7) + 8))
    return w(-3 + a0)
def main():
    global acc
    acc = w(w(acc * 31) + (16 | w(xs[idx(1)] * (min(50, 42) ^ 28))))
    acc = w(w(acc * 31) + ((acc) if (mod(((31) if (((3) if (5) < (-45) else (8))) < (w(50 - -23)) else (min(-36, -50))), w(mod((acc ^ shl(46, (-40) & 15)), 7) + 8))) < (((w(w(21 * -33) - acc)) if (w(f1(27) + ((-41) if (13) < (-18) else (-11)))) < (((max(-23, -22)) if (acc) < (mod(34, w(mod(-48, 7) + 8))) else (f0(-37, 27)))) else (xs[idx(shl(-4, (24) & 15))]))) else (xs[idx(shr(min(11, 21), ((-39 & 7)) & 15))])))
    v41051 = 26
    v13052 = shl((((v41051 ^ v41051) | div(-36, w(mod(-9, 7) + 8))) | mod(acc, w(mod(shr(v41051, (v41051) & 15), 7) + 8))), (f0((w(-12 - 19) ^ min(v41051, 24)), shr(min(v41051, -13), (-16) & 15))) & 15)
    v15250 = mod(w(-20 + div(max(v41051, 10), w(mod(v13052, 7) + 8))), w(mod(f3(v41051, max(w(-4 + v13052), shr(v13052, (v13052) & 15))), 7) + 8))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
