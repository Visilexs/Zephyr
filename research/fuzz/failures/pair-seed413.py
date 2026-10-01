
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
    acc = w(w(acc * 31) + ((a0 | div(a0, w(mod(shl(39, (a0) & 15), 7) + 8))) ^ min((((a0 ^ a0)) if (min(a0, a0)) < (min(a0, 31)) else (a0)), ((shr(50, (a0) & 15)) if (min(a0, a0)) < ((43 ^ a0)) else (div(a0, w(mod(a0, 7) + 8)))))))
    return max(33, mod(shr(shr(38, (a0) & 15), (26) & 15), w(mod(-8, 7) + 8)))
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + f0(acc))
    for i19951 in range(10):
        v18163 = (f0(shl(-3, (a0) & 15)) | shr(a2, (mod(div(14, w(mod(a1, 7) + 8)), w(mod(xs[idx(a2)], 7) + 8))) & 15))
    acc = w(w(acc * 31) + -27)
    return w(50 + shl(w(max(-35, a0) * shl(50, (a1) & 15)), (xs[idx(min(a0, a0))]) & 15))
def f2(a0):
    global acc
    acc = w(w(acc * 31) + ((w(shr(w(-2 * -38), (-48) & 15) * div(36, w(mod((a0 | a0), 7) + 8)))) if (shr(46, (f1(w(-26 + a0), shr(a0, (22) & 15), (a0 & a0))) & 15)) < (33) else (div(((a0) if ((a0 & 11)) < (((a0) if (-13) < (a0) else (a0))) else (div(a0, w(mod(a0, 7) + 8)))), w(mod(((18) if (w(-43 - -7)) < (a0) else (min(a0, -33))), 7) + 8)))))
    acc = w(w(acc * 31) + f1((w(mod(a0, w(mod(a0, 7) + 8)) - div(20, w(mod(a0, 7) + 8))) | acc), (-19 | 38), shr(w(w(a0 + 14) * w(a0 + -34)), (w(min(a0, a0) + div(a0, w(mod(46, 7) + 8)))) & 15)))
    v26266 = div(mod(w(max(-14, 15) * max(a0, a0)), w(mod(min(shr(43, (a0) & 15), w(a0 - -1)), 7) + 8)), w(mod(shl(-41, (a0) & 15), 7) + 8))
    return (((a0) if (-43) < (max(a0, div(a0, w(mod(a0, 7) + 8)))) else (f1(xs[idx(48)], shr(a0, (45) & 15), a0))) | acc)
def f3(a0, a1):
    global acc
    acc = w(w(acc * 31) + w(acc * a0))
    v67486 = shr(a1, (w(f0(acc) * min((a0 ^ -26), shl(-35, (28) & 15)))) & 15)
    acc = w(w(acc * 31) + shl(v67486, (f1(div(min(a0, v67486), w(mod(w(v67486 * v67486), 7) + 8)), -13, a0)) & 15))
    return acc
def main():
    global acc
    v93116 = shl(f1(w(shl(32, (-49) & 15) * xs[idx(-9)]), xs[idx(((-3) if (42) < (2) else (8)))], -32), (shr(7, (w(-29 - max(-6, 25))) & 15)) & 15)
    _i = idx(v93116); xs[_i] = (v93116 ^ f1(f0(acc), (xs[idx(v93116)] ^ 27), -47))
    if (acc) < ((w(w(mod(v93116, w(mod(v93116, 7) + 8)) * -2) * v93116) | v93116)):
        acc = w(w(acc * 31) + v93116)
    else:
        acc = w(w(acc * 31) + w(div(v93116, w(mod(-10, 7) + 8)) - (((shl(v93116, (v93116) & 15) ^ v93116)) if (v93116) < (acc) else (v93116))))
        acc = w(w(acc * 31) + min(f2(v93116), v93116))
    v77335 = -1
    for i68070 in range(9):
        v20699 = v93116
    if ((((w(43 - shr(10, (v93116) & 15))) if (min((v93116 ^ 0), mod(v77335, w(mod(v93116, 7) + 8)))) < (33) else (v93116)) & xs[idx(mod(max(v77335, v77335), w(mod(w(v93116 - -44), 7) + 8)))])) < (shl((div(v93116, w(mod(mod(v77335, w(mod(v77335, 7) + 8)), 7) + 8)) | max(v77335, w(-46 - v77335))), ((-39 ^ w((v93116 | -11) - mod(11, w(mod(v77335, 7) + 8))))) & 15)):
        v72646 = (mod(xs[idx(f2(v77335))], w(mod(w(shr(v93116, (v93116) & 15) * (v77335 & v77335)), 7) + 8)) & xs[idx((28 ^ v93116))])
    else:
        v76269 = acc
        acc = w(w(acc * 31) + acc)
    if (v93116) < (shr(w(w(min(-11, -40) * shl(v93116, (v93116) & 15)) * v77335), (f2(v93116)) & 15)):
        v70896 = v77335
        for i2308 in range(4):
            _i = idx((shl(v70896, ((shr(-39, (v77335) & 15) ^ f2(v77335))) & 15) & v77335)); xs[_i] = xs[idx(w(((f0(18)) if (15) < (f2(-28)) else (shl(i2308, (-19) & 15))) - v77335))]
        _i = idx(w(min(f1(v70896, v70896, ((45) if (v77335) < (v93116) else (v93116))), (v70896 | f0(19))) + w(shr(max(v70896, v70896), (acc) & 15) - ((25) if (v77335) < (v77335) else ((10 ^ v77335)))))); xs[_i] = shl((xs[idx(w(-19 - 37))] | w(((v77335) if (v70896) < (-38) else (v70896)) * 11)), (v93116) & 15)
    else:
        _i = idx(min(shr(w(w(-5 + v93116) * w(v93116 - v77335)), (mod(v93116, w(mod(shr(v93116, (v93116) & 15), 7) + 8))) & 15), (w(div(v77335, w(mod(13, 7) + 8)) - max(v77335, v93116)) & div(-48, w(mod((v77335 ^ -22), 7) + 8))))); xs[_i] = 12
        _i = idx(v77335); xs[_i] = f2(24)
    for i66849 in range(4):
        if (7) < (acc):
            v61268 = -37
            acc = w(w(acc * 31) + w((w((v61268 ^ v93116) - i66849) & -19) * (((-44) if (shr(-38, (i66849) & 15)) < (((-43) if (i66849) < (v93116) else (-38))) else (w(v61268 - 19))) | v93116)))
            _i = idx(41); xs[_i] = mod(((v61268) if (xs[idx(max(20, v61268))]) < ((-38 & v93116)) else (v61268)), w(mod(((div(shl(i66849, (35) & 15), w(mod(v61268, 7) + 8))) if (acc) < (w(-38 + w(-15 + 14))) else ((16 ^ (24 | 3)))), 7) + 8))
        else:
            v96908 = w(i66849 * w(v77335 * xs[idx(shr(v77335, (v93116) & 15))]))
            _i = idx(xs[idx(w(mod((v93116 ^ v77335), w(mod(-17, 7) + 8)) + max(w(v77335 + v93116), (v77335 & i66849))))]); xs[_i] = ((div(shr((8 ^ v93116), (-18) & 15), w(mod(i66849, 7) + 8))) if (20) < (f1(v93116, w(shl(i66849, (-10) & 15) + ((36) if (v96908) < (v96908) else (22))), ((v77335) if (div(v93116, w(mod(14, 7) + 8))) < (max(27, 5)) else (f3(-7, v77335))))) else (v93116))
        v59219 = min(mod(min(xs[idx(v93116)], ((-35) if (v77335) < (21) else (v93116))), w(mod(-38, 7) + 8)), mod(28, w(mod(shl(v93116, (v77335) & 15), 7) + 8)))
        _i = idx(v93116); xs[_i] = -40
    for i88971 in range(3):
        v84289 = v93116
        for i9607 in range(2):
            acc = w(w(acc * 31) + mod(((((v77335) if (shr(v84289, (v93116) & 15)) < (((v84289) if (i88971) < (28) else (i88971))) else (w(50 + 16)))) if (f3((i9607 ^ -28), mod(-21, w(mod(-27, 7) + 8)))) < ((shr(26, (i88971) & 15) | ((39) if (v84289) < (v84289) else (v84289)))) else (v93116)), w(mod(shr(min(shr(v77335, (i9607) & 15), f3(i88971, i9607)), (-17) & 15), 7) + 8)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
