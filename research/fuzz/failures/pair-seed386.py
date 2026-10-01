
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
    acc = w(w(acc * 31) + w(shr(a2, (-13) & 15) + min(a2, w((-34 | 7) + 16))))
    v8694 = (min(18, max(w(a1 - 41), (a2 & a1))) ^ acc)
    return min(a1, 44)
def f1(a0, a1):
    global acc
    v78204 = w(f0(mod(xs[idx(a0)], w(mod(shr(26, (a0) & 15), 7) + 8)), w(f0(10, a1, a1) - a1), (a1 | a0)) + (((w(a0 * a0) & (a0 & a1))) if (w(-10 * w(a0 - a1))) < (acc) else (w(div(a0, w(mod(-9, 7) + 8)) - xs[idx(29)]))))
    acc = w(w(acc * 31) + (xs[idx(xs[idx(div(a1, w(mod(a1, 7) + 8)))])] | ((acc) if ((w(a1 + a1) & shr(a1, (a1) & 15))) < (35) else (((26 ^ 8) | f0(a1, -27, a1))))))
    for i83210 in range(5):
        for i393 in range(12):
            acc = w(w(acc * 31) + f0(((a0) if ((((i393) if (29) < (i83210) else (i83210)) | v78204)) < (v78204) else ((((i393 | a1)) if ((i393 ^ -4)) < (min(18, i393)) else (min(v78204, -4))))), shl(((a0) if ((i393 ^ i393)) < (f0(i83210, v78204, -25)) else ((49 | i393))), (-46) & 15), ((a0) if (a0) < (mod(a0, w(mod(v78204, 7) + 8))) else (f0(div(v78204, w(mod(-18, 7) + 8)), a1, w(33 + a0))))))
            _i = idx((a0 ^ div(shr((a1 ^ i393), (((-8) if (v78204) < (-16) else (a1))) & 15), w(mod((mod(i393, w(mod(15, 7) + 8)) ^ min(v78204, -31)), 7) + 8)))); xs[_i] = -33
        _i = idx(shl(shl(((mod(a1, w(mod(i83210, 7) + 8))) if (((a1) if (v78204) < (-20) else (a0))) < ((-32 ^ -20)) else (acc)), (div(10, w(mod((-33 & 38), 7) + 8))) & 15), (a1) & 15)); xs[_i] = -14
        acc = w(w(acc * 31) + a0)
    return w(shl(max(f0(a1, a0, -30), 13), (38) & 15) - (a0 | div(div(a1, w(mod(a0, 7) + 8)), w(mod(shl(a0, (a0) & 15), 7) + 8))))
def f2(a0, a1):
    global acc
    _i = idx((max(f0(div(a1, w(mod(a0, 7) + 8)), a1, a1), a1) | shr(w(32 - 43), (w(max(26, a0) - -41)) & 15))); xs[_i] = div(((shl(shl(a1, (-47) & 15), (((-17) if (a1) < (a0) else (3))) & 15)) if (a1) < (shl(xs[idx(a0)], (a1) & 15)) else (xs[idx(min(a1, -43))])), w(mod(acc, 7) + 8))
    v15799 = a0
    v24506 = 34
    return w(-50 - w(w(shl(a0, (a0) & 15) - mod(a0, w(mod(33, 7) + 8))) - (w(-48 - a0) & a1)))
def main():
    global acc
    acc = w(w(acc * 31) + w(-41 - 36))
    if (max(mod(33, w(mod(-33, 7) + 8)), (w(shr(21, (3) & 15) * 17) & max(acc, shl(23, (32) & 15))))) < (shr(-38, (shl(w(w(12 * -46) + xs[idx(6)]), (23) & 15)) & 15)):
        _i = idx(2); xs[_i] = shr(w(((6) if (mod(-21, w(mod(-14, 7) + 8))) < ((2 & 40)) else (50)) - div(-3, w(mod(w(-38 - 44), 7) + 8))), ((div(xs[idx(41)], w(mod(shr(22, (12) & 15), 7) + 8)) | max(w(-46 + 50), mod(5, w(mod(17, 7) + 8))))) & 15)
        if (17) < (35):
            acc = w(w(acc * 31) + 0)
            v17820 = acc
        else:
            acc = w(w(acc * 31) + (42 | ((w(acc + shr(-43, (-3) & 15))) if (w(w(48 * -47) * w(14 + 4))) < (f1(xs[idx(35)], (-4 ^ 42))) else (w(14 + -13)))))
            _i = idx((23 | shr(-2, (7) & 15))); xs[_i] = -30
        _i = idx((4 ^ -32)); xs[_i] = mod((acc ^ w(max(-14, -33) * shr(-12, (38) & 15))), w(mod(w(41 * f0(0, f0(32, 49, -35), 33)), 7) + 8))
    else:
        acc = w(w(acc * 31) + (((shr((48 | -48), (shr(41, (2) & 15)) & 15)) if (w(9 + xs[idx(25)])) < (shl(mod(-32, w(mod(-24, 7) + 8)), (49) & 15)) else (f1(2, xs[idx(-17)]))) ^ w(-6 + w(xs[idx(-26)] - (29 ^ -47)))))
        for i29259 in range(11):
            acc = w(w(acc * 31) + 32)
            _i = idx(xs[idx(((div(i29259, w(mod(41, 7) + 8)) | w(i29259 + -19)) & (xs[idx(i29259)] | div(i29259, w(mod(i29259, 7) + 8)))))]); xs[_i] = -39
            v29383 = w(w(i29259 + i29259) + (w(w(48 * -7) * mod(-36, w(mod(i29259, 7) + 8))) | max(-47, xs[idx(-16)])))
    acc = w(w(acc * 31) + acc)
    acc = w(w(acc * 31) + min(acc, ((15 & -39) ^ w(w(-27 + -41) * 33))))
    v30526 = (w(17 + 41) | div(mod(47, w(mod(25, 7) + 8)), w(mod(shl(w(-13 * 50), (f2(-50, -1)) & 15), 7) + 8)))
    acc = w(w(acc * 31) + v30526)
    v90072 = w(acc * 45)
    if (max(max(w(21 - 29), -40), (v90072 | w(v90072 - -11)))) < (w(-27 + ((w(v90072 + min(v90072, v90072))) if (min((-2 & v90072), shr(v90072, (v90072) & 15))) < (v30526) else (((div(-9, w(mod(-11, 7) + 8))) if (shr(-28, (-29) & 15)) < (v90072) else (-36)))))):
        if (shr(w(mod(w(v30526 * v90072), w(mod(f2(v30526, -24), 7) + 8)) * max((v90072 & -28), (v90072 ^ v30526))), (v30526) & 15)) < (w(v30526 + v30526)):
            _i = idx(((f0(w((0 | v30526) + v30526), shr(((v90072) if (v30526) < (v30526) else (v30526)), (xs[idx(-17)]) & 15), -46)) if (xs[idx((div(v90072, w(mod(v90072, 7) + 8)) & (11 | v30526)))]) < (((shr(max(7, v30526), (div(-46, w(mod(-50, 7) + 8))) & 15)) if (f1(div(v90072, w(mod(v90072, 7) + 8)), w(v30526 - v90072))) < (((w(v30526 - v90072)) if (w(-32 + -43)) < (shr(21, (-32) & 15)) else (min(38, v90072)))) else (min(-46, mod(1, w(mod(v30526, 7) + 8)))))) else (v90072))); xs[_i] = v90072
            acc = w(w(acc * 31) + min(div(div(max(v90072, v30526), w(mod(acc, 7) + 8)), w(mod(-44, 7) + 8)), shr(v90072, (div(shl(v30526, (v30526) & 15), w(mod(shl(v30526, (v90072) & 15), 7) + 8))) & 15)))
            _i = idx(((min(max(v30526, v30526), shl(v30526, (19) & 15)) ^ max(v30526, v30526)) | w(min(xs[idx(v90072)], shl(v30526, (v30526) & 15)) + w((31 | -7) * xs[idx(-20)])))); xs[_i] = w((mod(max(v90072, 21), w(mod(v30526, 7) + 8)) ^ v90072) - f1(shr((v90072 | 42), (shr(v30526, (v30526) & 15)) & 15), v30526))
        else:
            v52064 = w(div(v90072, w(mod(30, 7) + 8)) + max(v30526, acc))
        acc = w(w(acc * 31) + v30526)
        for i78229 in range(7):
            v98850 = mod(mod(w((v30526 ^ 38) * mod(10, w(mod(v30526, 7) + 8))), w(mod(f2(w(v90072 * 46), -23), 7) + 8)), w(mod(acc, 7) + 8))
            v77695 = v90072
            _i = idx(40); xs[_i] = ((v90072) if (13) < (w((v90072 ^ w(v30526 - i78229)) - 16)) else (37))
    else:
        v29139 = shl(f1(v30526, shr(w(28 + v90072), (mod(v90072, w(mod(v30526, 7) + 8))) & 15)), (f0(f1(v90072, v30526), acc, min(acc, (v90072 & v90072)))) & 15)
        _i = idx(mod(25, w(mod(f1(div(shl(18, (-10) & 15), w(mod(v29139, 7) + 8)), ((f2(29, v30526)) if (w(-42 * v90072)) < (((-31) if (-23) < (-27) else (19))) else (mod(v29139, w(mod(-11, 7) + 8))))), 7) + 8))); xs[_i] = v30526
    for i60390 in range(5):
        if (((v30526 | 34) | v30526)) < ((min(-1, w(w(v30526 + v90072) + max(12, i60390))) & (v90072 & mod(shr(i60390, (v90072) & 15), w(mod(v90072, 7) + 8))))):
            acc = w(w(acc * 31) + 40)
            v29079 = acc
        else:
            acc = w(w(acc * 31) + xs[idx(-32)])
            v1779 = shr(f0(div(f2(v90072, i60390), w(mod(i60390, 7) + 8)), w(max(-22, v90072) - ((v30526) if (33) < (v90072) else (18))), (xs[idx(v30526)] | mod(v90072, w(mod(2, 7) + 8)))), (w((mod(v30526, w(mod(0, 7) + 8)) ^ v30526) + xs[idx(acc)])) & 15)
        _i = idx(i60390); xs[_i] = xs[idx(w(w(shr(13, (i60390) & 15) + ((v30526) if (-2) < (6) else (i60390))) * ((40) if (xs[idx(i60390)]) < (-48) else (min(35, i60390)))))]
        v26950 = i60390
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
