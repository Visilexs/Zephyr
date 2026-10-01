
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
    acc = w(w(acc * 31) + w(shl((45 & a2), (w(21 - a2)) & 15) + a1))
    acc = w(w(acc * 31) + w(div(47, w(mod(a2, 7) + 8)) - (-37 | (mod(a2, w(mod(a0, 7) + 8)) | a2))))
    return w(shl(w(shr(-50, (a1) & 15) - 45), ((w(-1 * -15) ^ a2)) & 15) * a2)
def f1(a0, a1):
    global acc
    v52442 = a1
    for i97727 in range(11):
        v18408 = xs[idx(f0(w(a1 * mod(v52442, w(mod(13, 7) + 8))), w(mod(i97727, w(mod(v52442, 7) + 8)) * (v52442 ^ a1)), a0))]
        v62852 = min(a1, (max(v52442, w(31 - v18408)) & acc))
    return xs[idx((acc & acc))]
def f2(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + -7)
    return w(w((-22 | (a0 | 23)) - (xs[idx(a0)] | min(7, a0))) + w(max(xs[idx(a0)], shr(a0, (-22) & 15)) - div(a2, w(mod(a0, 7) + 8))))
def main():
    global acc
    for i39649 in range(4):
        if ((div(f2((i39649 & i39649), i39649, i39649), w(mod(i39649, 7) + 8)) & f1(-2, i39649))) < (max(max((max(i39649, i39649) ^ mod(i39649, w(mod(44, 7) + 8))), (42 ^ f1(i39649, i39649))), (mod((-48 ^ i39649), w(mod(-7, 7) + 8)) & shl(w(-24 - -6), (min(-3, i39649)) & 15)))):
            acc = w(w(acc * 31) + xs[idx(shl((((i39649) if (i39649) < (30) else (i39649)) ^ (i39649 & i39649)), (mod(w(i39649 * i39649), w(mod((i39649 | i39649), 7) + 8))) & 15))])
            v47639 = 7
        else:
            _i = idx((xs[idx((i39649 | acc))] | shl(((w(23 * i39649)) if ((-10 | i39649)) < (mod(i39649, w(mod(24, 7) + 8))) else (i39649)), (i39649) & 15))); xs[_i] = shl(max(shl(16, (-10) & 15), xs[idx(shl(i39649, (i39649) & 15))]), (acc) & 15)
            v15989 = 24
        v4665 = (w(w(shr(-48, (i39649) & 15) + w(i39649 - i39649)) + shl(i39649, (i39649) & 15)) ^ w(shr(i39649, (div(i39649, w(mod(34, 7) + 8))) & 15) + mod(i39649, w(mod((41 | i39649), 7) + 8))))
        if (((shl(max(v4665, i39649), (xs[idx(v4665)]) & 15) | i39649) | min(min(((-49) if (i39649) < (i39649) else (i39649)), (v4665 ^ 50)), w(shr(-26, (-42) & 15) * acc)))) < (((((v4665) if (-16) < (acc) else (v4665))) if ((mod(min(2, v4665), w(mod(f2(-24, v4665, v4665), 7) + 8)) | min(-6, f2(49, i39649, v4665)))) < (w(v4665 + w(3 - v4665))) else ((i39649 ^ min(acc, (38 | v4665)))))):
            v80404 = shr(div(-18, w(mod(35, 7) + 8)), (i39649) & 15)
        else:
            v16029 = xs[idx(shr(w(i39649 - max(-1, -41)), (-6) & 15))]
            acc = w(w(acc * 31) + div(w((f0(v16029, 43, v16029) | ((-46) if (i39649) < (v16029) else (i39649))) + shl(mod(i39649, w(mod(i39649, 7) + 8)), (w(v4665 + -6)) & 15)), w(mod(v16029, 7) + 8)))
    for i15738 in range(2):
        if (shr(((w(i15738 + 28) & w(i15738 - 39)) ^ xs[idx(-40)]), (min(div(mod(5, w(mod(i15738, 7) + 8)), w(mod(max(i15738, i15738), 7) + 8)), w(mod(i15738, w(mod(i15738, 7) + 8)) - ((i15738) if (i15738) < (i15738) else (i15738))))) & 15)) < (w(w(-13 - w(xs[idx(-47)] + acc)) - i15738)):
            _i = idx(div((36 ^ i15738), w(mod(i15738, 7) + 8))); xs[_i] = f2(w(w(min(-26, i15738) * (i15738 ^ i15738)) + ((shr(i15738, (i15738) & 15)) if (div(i15738, w(mod(-47, 7) + 8))) < ((i15738 | 4)) else (i15738))), max(shl(10, (i15738) & 15), (-36 | div(i15738, w(mod(i15738, 7) + 8)))), (acc ^ acc))
            v19171 = div(i15738, w(mod(i15738, 7) + 8))
        else:
            v22791 = i15738
            v42307 = min(max(max(max(-5, 32), div(-1, w(mod(v22791, 7) + 8))), div(11, w(mod(i15738, 7) + 8))), shr(44, (((f0(v22791, -22, v22791)) if (mod(v22791, w(mod(i15738, 7) + 8))) < (v22791) else (i15738))) & 15))
        acc = w(w(acc * 31) + i15738)
    v39296 = -35
    _i = idx(w((shr(w(v39296 + v39296), (w(v39296 * v39296)) & 15) ^ w(v39296 - ((v39296) if (41) < (v39296) else (v39296)))) - v39296)); xs[_i] = -27
    if (((((v39296) if (w(shr(42, (30) & 15) - v39296)) < (w(((v39296) if (v39296) < (v39296) else (-47)) - -50)) else ((((v39296) if (v39296) < (v39296) else (-30)) & shl(v39296, (v39296) & 15))))) if (-48) < (v39296) else (min(v39296, acc)))) < (13):
        if (w(v39296 * shr(w(min(39, 50) + (v39296 | v39296)), (xs[idx(acc)]) & 15))) < (w(41 + w(shl(v39296, ((17 & 19)) & 15) - -12))):
            _i = idx(31); xs[_i] = v39296
            acc = w(w(acc * 31) + (div(v39296, w(mod(8, 7) + 8)) | xs[idx(-48)]))
        else:
            v94198 = (acc & ((w(10 + acc)) if ((shr(27, (-41) & 15) | (v39296 ^ v39296))) < (28) else (46)))
        for i15670 in range(2):
            acc = w(w(acc * 31) + min(((min(-35, i15670) & i15670) ^ acc), div(23, w(mod(min(-15, v39296), 7) + 8))))
        for i90429 in range(10):
            _i = idx(42); xs[_i] = v39296
            _i = idx((mod(div(50, w(mod(v39296, 7) + 8)), w(mod(((min(v39296, v39296)) if (i90429) < (w(34 - v39296)) else (i90429)), 7) + 8)) ^ min(div(27, w(mod(shl(38, (v39296) & 15), 7) + 8)), w(w(v39296 - v39296) + (v39296 | 28))))); xs[_i] = min((w(38 - (i90429 & i90429)) ^ mod(shr(i90429, (i90429) & 15), w(mod(-40, 7) + 8))), min(div(((v39296) if (i90429) < (-46) else (v39296)), w(mod(min(i90429, v39296), 7) + 8)), mod(div(i90429, w(mod(47, 7) + 8)), w(mod(div(v39296, w(mod(-41, 7) + 8)), 7) + 8))))
            _i = idx((shl(v39296, (16) & 15) ^ shr(((acc) if (i90429) < (max(46, -4)) else ((i90429 | i90429))), (w(min(i90429, -12) * mod(31, w(mod(v39296, 7) + 8)))) & 15))); xs[_i] = max(w((9 ^ acc) - xs[idx(i90429)]), v39296)
    else:
        if (min(acc, ((acc) if (f0(w(-24 + v39296), shl(35, (v39296) & 15), ((v39296) if (-6) < (v39296) else (v39296)))) < (f2(w(46 * v39296), w(19 + v39296), v39296)) else (((-9) if (-28) < (w(-7 + v39296)) else (v39296)))))) < ((div(min(-23, min(v39296, v39296)), w(mod(-36, 7) + 8)) & shl((f2(46, v39296, v39296) ^ v39296), (div(f2(v39296, v39296, v39296), w(mod((-45 | -16), 7) + 8))) & 15))):
            v6680 = v39296
            _i = idx(shl(w(w(acc - v6680) * shl(v6680, (acc) & 15)), (w(f0(5, shr(v39296, (v6680) & 15), ((v6680) if (v39296) < (v6680) else (v6680))) - f1(min(v6680, -41), min(-27, 27)))) & 15)); xs[_i] = -46
            _i = idx(f1(w(div(10, w(mod((33 ^ v39296), 7) + 8)) - w(xs[idx(v39296)] * v39296)), v39296)); xs[_i] = -24
        else:
            acc = w(w(acc * 31) + (((((shr(v39296, (v39296) & 15) & w(v39296 + v39296))) if (w((v39296 | -5) * (v39296 | -12))) < (xs[idx(v39296)]) else (46))) if (shr(v39296, (min(w(v39296 + v39296), (-35 | v39296))) & 15)) < (v39296) else (((-16) if (v39296) < (-33) else ((w(-13 + v39296) ^ max(v39296, v39296)))))))
            acc = w(w(acc * 31) + v39296)
        v73173 = w(v39296 * mod(w(w(v39296 + -36) * xs[idx(20)]), w(mod((-4 & acc), 7) + 8)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
