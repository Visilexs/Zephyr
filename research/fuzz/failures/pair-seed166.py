
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
    acc = w(w(acc * 31) + 12)
    if (mod(shl(w((a2 & a0) + div(a0, w(mod(a2, 7) + 8))), (a1) & 15), w(mod(a2, 7) + 8))) < (w(a2 - mod((w(a2 * 4) & min(a2, 15)), w(mod(min(27, mod(a1, w(mod(a0, 7) + 8))), 7) + 8)))):
        acc = w(w(acc * 31) + (mod(47, w(mod(-25, 7) + 8)) | w(-41 + ((a0 & a1) | ((a1) if (a0) < (a2) else (-10))))))
        v65977 = w(a1 + shr(a1, (div(shr(a0, (a1) & 15), w(mod(max(11, a2), 7) + 8))) & 15))
        _i = idx(w(w(((min(a1, -39)) if ((10 | a1)) < (mod(-20, w(mod(a1, 7) + 8))) else (-31)) + a2) - max(w((-34 ^ a1) + -47), w(w(a0 + -27) * shl(a2, (a2) & 15))))); xs[_i] = div(w(a2 + 12), w(mod(max((acc ^ -38), ((v65977 ^ -47) & max(a0, -19))), 7) + 8))
    else:
        v78058 = a1
        _i = idx(shl(a0, (-17) & 15)); xs[_i] = -16
    _i = idx(shl(11, ((((a1 & 41) ^ w(a0 + 27)) & a0)) & 15)); xs[_i] = div((w(w(44 + 46) + 45) ^ min((49 ^ a0), 36)), w(mod(a0, 7) + 8))
    return shl(((w(mod(a2, w(mod(a2, 7) + 8)) + min(14, a1))) if (a1) < (a0) else (w(27 - max(a0, -3)))), ((-45 | mod(min(a2, -30), w(mod(-19, 7) + 8)))) & 15)
def f1(a0, a1, a2):
    global acc
    v54866 = (mod((min(a0, 18) ^ a2), w(mod(max(min(a2, a0), f0(-23, a2, 47)), 7) + 8)) ^ (shl(w(10 + a2), (div(a1, w(mod(a2, 7) + 8))) & 15) & max(min(a0, a2), 7)))
    v36610 = (11 & shr(w(w(-13 - a1) - f0(2, 22, 30)), (w(28 * mod(a0, w(mod(a2, 7) + 8)))) & 15))
    return a2
def main():
    global acc
    v51288 = ((-2 | xs[idx(shl(-47, (10) & 15))]) ^ (acc ^ (11 & mod(-43, w(mod(-49, 7) + 8)))))
    if (w(max(shl(max(0, -1), (max(v51288, v51288)) & 15), (v51288 & w(v51288 + v51288))) * v51288)) < (acc):
        acc = w(w(acc * 31) + v51288)
    else:
        if (-39) < (w(acc + w(div((31 ^ v51288), w(mod(w(v51288 - v51288), 7) + 8)) + v51288))):
            _i = idx(acc); xs[_i] = v51288
        else:
            _i = idx(shl(div(((v51288) if (1) < (v51288) else (w(v51288 - 23))), w(mod(w(w(v51288 * v51288) - div(v51288, w(mod(v51288, 7) + 8))), 7) + 8)), (-40) & 15)); xs[_i] = w(w((w(v51288 + v51288) ^ 27) - -40) * (((min(43, -41)) if (((v51288) if (-26) < (v51288) else (v51288))) < (mod(-42, w(mod(v51288, 7) + 8))) else (shl(v51288, (49) & 15))) ^ shl(v51288, (acc) & 15)))
    for i55190 in range(2):
        v24646 = (shr(((min(26, v51288)) if ((i55190 ^ i55190)) < (v51288) else (div(i55190, w(mod(40, 7) + 8)))), (((div(v51288, w(mod(-27, 7) + 8))) if (max(i55190, -3)) < (div(v51288, w(mod(v51288, 7) + 8))) else (max(-9, v51288)))) & 15) & w(11 + xs[idx(f1(0, -42, 41))]))
    acc = w(w(acc * 31) + shr(-26, (acc) & 15))
    v73424 = ((shr(19, (v51288) & 15)) if (-47) < (9) else ((v51288 ^ shr(w(v51288 + v51288), (f1(v51288, v51288, v51288)) & 15))))
    acc = w(w(acc * 31) + -50)
    if (acc) < (div(div((40 | 13), w(mod((w(v73424 - v51288) ^ v51288), 7) + 8)), w(mod(v51288, 7) + 8))):
        for i94721 in range(4):
            _i = idx(f1(i94721, -46, (div(v73424, w(mod(shl(-7, (-10) & 15), 7) + 8)) ^ w(v73424 - xs[idx(v73424)])))); xs[_i] = w(v51288 + (shl(-15, (w(v51288 + v51288)) & 15) | min(mod(-43, w(mod(41, 7) + 8)), (27 ^ v51288))))
        acc = w(w(acc * 31) + xs[idx(v73424)])
    else:
        for i86882 in range(9):
            _i = idx(acc); xs[_i] = acc
            acc = w(w(acc * 31) + w(34 - w(f1(((i86882) if (i86882) < (-30) else (v51288)), f0(i86882, v73424, i86882), (-4 & v51288)) * ((w(2 * v73424)) if ((-21 ^ i86882)) < (w(-19 + 2)) else (f0(v73424, 1, -37))))))
            v20395 = shr(max(div(w(i86882 * v73424), w(mod(shl(v51288, (v51288) & 15), 7) + 8)), shr(v73424, (36) & 15)), (i86882) & 15)
        v47110 = (v73424 ^ shr((w(-27 - v73424) ^ v51288), (min(shl(v51288, (v51288) & 15), mod(v51288, w(mod(17, 7) + 8)))) & 15))
    _i = idx(((xs[idx(div(v73424, w(mod(div(v51288, w(mod(v51288, 7) + 8)), 7) + 8)))]) if (32) < (v51288) else (xs[idx(v73424)]))); xs[_i] = div(shl((shr(v51288, (v51288) & 15) & (3 | 9)), (min(w(v51288 - v51288), shl(-14, (v51288) & 15))) & 15), w(mod(shr(v51288, (w((20 & v51288) * ((v51288) if (-41) < (-46) else (-32)))) & 15), 7) + 8))
    v15694 = xs[idx(v51288)]
    if ((max(max(f1(v51288, -23, v73424), 45), shr(((v15694) if (v73424) < (v15694) else (v15694)), (min(-19, -30)) & 15)) | -9)) < (min(v73424, (min(w(-49 * 25), ((v73424) if (-12) < (v15694) else (24))) ^ ((w(-34 + -15)) if (w(22 - -39)) < (w(v15694 * -39)) else (min(v15694, v73424)))))):
        if ((w(((v51288 ^ 10) | v15694) - -39) & v15694)) < (acc):
            v68802 = (-9 | 7)
            v68086 = f0(acc, (v73424 & v51288), max(v73424, max(w(v73424 + -43), (v51288 & v15694))))
        else:
            v2328 = f0(v51288, (max(shr(-30, (38) & 15), v73424) ^ (acc ^ f1(v51288, 42, -42))), (-12 | ((mod(25, w(mod(-2, 7) + 8))) if (div(v15694, w(mod(v73424, 7) + 8))) < (39) else (-22))))
        v69016 = acc
    else:
        if (v51288) < (w(mod(v73424, w(mod(max(xs[idx(-13)], shl(v73424, (-31) & 15)), 7) + 8)) - f1(shr(f1(v15694, v51288, 21), (((v73424) if (v51288) < (v73424) else (v15694))) & 15), v15694, mod(v73424, w(mod((-20 | v51288), 7) + 8))))):
            _i = idx(min(w(mod((-20 ^ v15694), w(mod((35 | v51288), 7) + 8)) + w(mod(-7, w(mod(-50, 7) + 8)) * xs[idx(13)])), v73424)); xs[_i] = v73424
            _i = idx(shl(f1(mod(min(v51288, -32), w(mod(v73424, 7) + 8)), w(-46 - v15694), (max(v51288, v15694) & mod(6, w(mod(v51288, 7) + 8)))), (v73424) & 15)); xs[_i] = (w(v51288 + w(w(v51288 - v51288) + w(v73424 - -8))) ^ shl(shl(v15694, (v73424) & 15), (shr(w(v15694 * v15694), (v51288) & 15)) & 15))
            _i = idx((((-26) if (-24) < (xs[idx(f0(v15694, v51288, v51288))]) else ((w(35 * v51288) | -40))) & v51288)); xs[_i] = xs[idx(shr(w(max(v15694, 47) * v15694), (v73424) & 15))]
        else:
            _i = idx(w((mod((21 & v73424), w(mod((38 | -33), 7) + 8)) & v73424) - v15694)); xs[_i] = mod(-38, w(mod(div((div(v51288, w(mod(v73424, 7) + 8)) & w(v73424 * 27)), w(mod(-7, 7) + 8)), 7) + 8))
            v94469 = (max(v15694, mod(w(-3 + v73424), w(mod(acc, 7) + 8))) ^ 12)
        for i74129 in range(7):
            _i = idx(max(acc, w((xs[idx(9)] ^ v15694) + mod(mod(-5, w(mod(v73424, 7) + 8)), w(mod((41 | 7), 7) + 8))))); xs[_i] = shr(37, ((max(w(v15694 - -17), -15) | w(f1(v73424, v15694, -39) + v73424))) & 15)
            v58861 = 41
            _i = idx(w(v73424 * w(v73424 + w(xs[idx(v73424)] * mod(v15694, w(mod(v51288, 7) + 8)))))); xs[_i] = (xs[idx(((max(4, v58861)) if (w(v51288 - 8)) < (mod(v15694, w(mod(v73424, 7) + 8))) else (shl(39, (v58861) & 15))))] & (mod(mod(v58861, w(mod(40, 7) + 8)), w(mod(v51288, 7) + 8)) ^ xs[idx(max(-36, v58861))]))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
