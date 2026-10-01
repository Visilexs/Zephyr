
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
    v46892 = ((w(-4 - xs[idx(min(a0, 41))])) if (shr(((w(a2 + -2)) if (w(a1 + 18)) < (a1) else (w(-43 + a2))), (a1) & 15)) < (a1) else (max(-36, (-24 | xs[idx(a0)]))))
    _i = idx(a2); xs[_i] = 24
    acc = w(w(acc * 31) + (-44 & a1))
    return shl((shr(max(23, a0), (w(a1 + a1)) & 15) & w(div(-27, w(mod(27, 7) + 8)) + -2)), (((-11 | (a2 | a2)) ^ div(acc, w(mod(a2, 7) + 8)))) & 15)
def f1(a0):
    global acc
    v38282 = (((div(a0, w(mod(a0, 7) + 8)) & shr(a0, (a0) & 15)) | mod(-44, w(mod((9 & a0), 7) + 8))) | (29 | f0(a0, w(34 - a0), w(a0 - a0))))
    v47519 = max(a0, f0(min((6 & 11), w(50 * -38)), a0, max(v38282, a0)))
    return min(f0(a0, xs[idx(a0)], a0), w(div(-8, w(mod(-37, 7) + 8)) + (-48 ^ (26 | 16))))
def f2(a0, a1, a2):
    global acc
    if (w(a1 + a1)) < (xs[idx(acc)]):
        v81059 = xs[idx(a1)]
    else:
        v50919 = (mod(shl(((a1) if (a1) < (a0) else (2)), (a2) & 15), w(mod(w(f1(a0) - ((a1) if (4) < (37) else (-15))), 7) + 8)) | w(min(xs[idx(a2)], shr(-28, (a1) & 15)) - f1(w(-34 * a2))))
    for i8009 in range(12):
        for i18148 in range(6):
            _i = idx(i18148); xs[_i] = acc
            _i = idx(min(w(f0(shr(i8009, (-14) & 15), (a2 ^ -20), (a0 | a2)) * i18148), i8009)); xs[_i] = w(a2 * min(a2, max(min(i8009, 3), a1)))
            _i = idx(acc); xs[_i] = a1
        if (div(a1, w(mod(shr(div(w(a0 + 15), w(mod((44 | 46), 7) + 8)), ((max(i8009, a0) & shl(a0, (-43) & 15))) & 15), 7) + 8))) < (a2):
            _i = idx(w(f1(min((-48 | a0), i8009)) * max(((-31 | a1) ^ i8009), (shr(a0, (-32) & 15) | 32)))); xs[_i] = f0(w(a1 * -18), i8009, a2)
            acc = w(w(acc * 31) + f1(max(-5, shr(i8009, (xs[idx(a1)]) & 15))))
            v84677 = (xs[idx(a0)] ^ w(div(max(-43, a0), w(mod(((44) if (a1) < (-47) else (a0)), 7) + 8)) * min(a0, f1(i8009))))
        else:
            _i = idx(i8009); xs[_i] = f1(i8009)
    acc = w(w(acc * 31) + (-26 ^ (a2 | (-39 ^ w(a2 * 37)))))
    return (-45 | a0)
def f3(a0, a1, a2):
    global acc
    if (w(min(max(-17, max(a0, a0)), -12) + shr(max(a2, mod(a1, w(mod(a0, 7) + 8))), (f1((a2 ^ 30))) & 15))) < (a1):
        for i38985 in range(9):
            acc = w(w(acc * 31) + xs[idx(w(w(-47 * shr(2, (i38985) & 15)) - shr(div(-31, w(mod(i38985, 7) + 8)), (a1) & 15)))])
            _i = idx(a2); xs[_i] = mod((mod(min(i38985, 3), w(mod(f0(a1, a2, a0), 7) + 8)) & 5), w(mod(-32, 7) + 8))
            v78814 = xs[idx(shl(xs[idx(div(i38985, w(mod(i38985, 7) + 8)))], (a1) & 15))]
        acc = w(w(acc * 31) + ((5) if (w(mod(shr(a2, (a2) & 15), w(mod(16, 7) + 8)) - -10)) < (f2((min(14, a0) ^ (-13 & a1)), shl(a0, (shr(26, (44) & 15)) & 15), xs[idx(mod(a2, w(mod(0, 7) + 8)))])) else (((25) if (div(div(a2, w(mod(19, 7) + 8)), w(mod(acc, 7) + 8))) < ((-10 ^ max(a1, a1))) else (w(mod(a0, w(mod(-33, 7) + 8)) + f0(-43, 49, a1)))))))
        acc = w(w(acc * 31) + 22)
    else:
        v58967 = div(acc, w(mod(shl(w(w(24 + a1) - (-43 | -6)), (-7) & 15), 7) + 8))
    if (a0) < (xs[idx(min(a2, xs[idx((43 | a1))]))]):
        v92770 = a0
        for i79262 in range(1):
            v12575 = (w(max(w(43 - a2), w(a0 - a1)) + max(38, -48)) & shr((xs[idx(a0)] & f2(v92770, -5, a1)), (shr(w(41 - 2), (v92770) & 15)) & 15))
            v84014 = w(mod(w((a2 | a0) - (a0 ^ 31)), w(mod(a1, 7) + 8)) - mod(v12575, w(mod(min(a1, shl(a0, (45) & 15)), 7) + 8)))
    else:
        acc = w(w(acc * 31) + -46)
    acc = w(w(acc * 31) + 4)
    return xs[idx(f2(max(min(a0, 8), mod(a2, w(mod(7, 7) + 8))), a1, w(mod(33, w(mod(a2, 7) + 8)) * ((a2) if (a0) < (a0) else (a0)))))]
def main():
    global acc
    if ((35 & 31)) < ((((f0(min(-31, 44), (-12 | -6), 38) | -27)) if (acc) < (shl(acc, (w(w(6 + -21) + mod(16, w(mod(-36, 7) + 8)))) & 15)) else (w(w(w(3 - 30) - (8 ^ 14)) + (25 | acc))))):
        v65130 = min(max(50, f0(-48, 20, shl(48, (40) & 15))), 8)
        _i = idx(shl(mod(-45, w(mod(v65130, 7) + 8)), (acc) & 15)); xs[_i] = f0(w(v65130 + xs[idx(max(v65130, v65130))]), xs[idx(div(v65130, w(mod(v65130, 7) + 8)))], max(-12, (div(-25, w(mod(38, 7) + 8)) & shr(v65130, (v65130) & 15))))
        acc = w(w(acc * 31) + (w(min(v65130, (v65130 ^ v65130)) - (w(15 * -23) ^ (19 | -20))) | w(max((v65130 | 37), -33) * -44)))
    else:
        acc = w(w(acc * 31) + -28)
        for i92494 in range(11):
            _i = idx(xs[idx(i92494)]); xs[_i] = min((w(w(-47 + i92494) - -3) & (((i92494) if (-16) < (i92494) else (i92494)) ^ min(-34, 44))), xs[idx(shl(i92494, (-7) & 15))])
    v96100 = 9
    if (29) < (w(v96100 - v96100)):
        _i = idx(w(f1(v96100) - (f1(f0(v96100, v96100, v96100)) ^ f3(((-10) if (v96100) < (v96100) else (49)), min(v96100, v96100), -48)))); xs[_i] = (w((shl(-2, (-20) & 15) & v96100) - (v96100 | (v96100 | v96100))) ^ v96100)
        acc = w(w(acc * 31) + v96100)
        v15860 = div(max(w(shr(v96100, (v96100) & 15) + -33), v96100), w(mod(shr(-18, (div(shr(v96100, (v96100) & 15), w(mod(v96100, 7) + 8))) & 15), 7) + 8))
    else:
        acc = w(w(acc * 31) + max(f3(acc, v96100, max(v96100, min(-10, v96100))), 4))
        v24141 = ((shr(-10, (v96100) & 15)) if (div((div(-31, w(mod(26, 7) + 8)) ^ xs[idx(14)]), w(mod(v96100, 7) + 8))) < (v96100) else (f3(v96100, v96100, (min(-18, v96100) ^ v96100))))
    if (acc) < (((((v96100 & v96100)) if (min(30, (v96100 & v96100))) < (min(v96100, v96100)) else (v96100)) & w((acc ^ 43) + -50))):
        if (v96100) < (w(w(xs[idx(xs[idx(-12)])] * w(v96100 * f1(v96100))) - w(v96100 - acc))):
            v78737 = shr(w(shr(-36, (-43) & 15) + 18), (w(v96100 + (v96100 ^ min(-26, v96100)))) & 15)
            _i = idx(w(w(v78737 + ((v78737) if (shr(v96100, (-25) & 15)) < ((v78737 | 18)) else (v78737))) - mod(xs[idx(v96100)], w(mod(w(((-43) if (v78737) < (v78737) else (4)) * (v96100 ^ 28)), 7) + 8)))); xs[_i] = acc
        else:
            _i = idx(shr(-38, (w(mod(acc, w(mod(max(v96100, v96100), 7) + 8)) - xs[idx(v96100)])) & 15)); xs[_i] = v96100
            _i = idx(w(w(v96100 + 38) + max((-48 | w(v96100 + v96100)), acc))); xs[_i] = v96100
        acc = w(w(acc * 31) + acc)
        if (div(w((acc ^ xs[idx(22)]) * mod(min(v96100, v96100), w(mod(w(20 + v96100), 7) + 8))), w(mod(w(div(w(31 * v96100), w(mod(-19, 7) + 8)) * shl(((v96100) if (v96100) < (v96100) else (12)), ((v96100 & v96100)) & 15)), 7) + 8))) < (v96100):
            acc = w(w(acc * 31) + (w(-4 + w(v96100 * acc)) | v96100))
        else:
            _i = idx(v96100); xs[_i] = (mod(w(-44 - shr(v96100, (v96100) & 15)), w(mod(min(((v96100) if (26) < (-42) else (v96100)), acc), 7) + 8)) & div(21, w(mod(xs[idx(v96100)], 7) + 8)))
    else:
        v98888 = v96100
        acc = w(w(acc * 31) + div(xs[idx(v98888)], w(mod(v98888, 7) + 8)))
    if (v96100) < (div(v96100, w(mod(acc, 7) + 8))):
        _i = idx(min(acc, v96100)); xs[_i] = max((((acc) if (xs[idx(-34)]) < ((-27 ^ 28)) else (-5)) | f3(min(-48, v96100), f1(29), v96100)), v96100)
        v98465 = w((((v96100 ^ v96100) ^ w(42 - -6)) ^ w((31 | v96100) - div(50, w(mod(-33, 7) + 8)))) + (v96100 & (23 | v96100)))
        _i = idx((v96100 & w(acc * w(48 + w(v98465 * -1))))); xs[_i] = shr(16, (v96100) & 15)
    else:
        acc = w(w(acc * 31) + shr(47, (max((((v96100) if (v96100) < (-41) else (v96100)) | (37 & v96100)), v96100)) & 15))
        if (27) < (29):
            _i = idx(w((-17 ^ 48) * ((f2(v96100, -23, w(v96100 * v96100))) if (mod(((v96100) if (v96100) < (v96100) else (20)), w(mod(v96100, 7) + 8))) < (w((-6 & v96100) * f3(v96100, v96100, v96100))) else ((-38 & div(-37, w(mod(-42, 7) + 8))))))); xs[_i] = min(w(25 + ((((-8) if (v96100) < (v96100) else (-34))) if (min(38, v96100)) < (shl(v96100, (41) & 15)) else ((41 ^ v96100)))), div(((w(-50 - v96100)) if (max(v96100, 13)) < (v96100) else (f1(v96100))), w(mod(div(shl(-15, (v96100) & 15), w(mod(max(-38, v96100), 7) + 8)), 7) + 8)))
        else:
            v87327 = max(max(w(shl(v96100, (v96100) & 15) - v96100), v96100), mod(v96100, w(mod(v96100, 7) + 8)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
