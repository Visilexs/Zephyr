
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
    _i = idx(xs[idx(acc)]); xs[_i] = div(w(shl(-11, ((a1 ^ -1)) & 15) + mod(w(-10 + 12), w(mod(mod(-19, w(mod(a0, 7) + 8)), 7) + 8))), w(mod(xs[idx(min(a1, a0))], 7) + 8))
    v64783 = w(21 - min(mod(max(a1, 14), w(mod(div(a1, w(mod(a0, 7) + 8)), 7) + 8)), (-31 | 43)))
    acc = w(w(acc * 31) + (w(mod(mod(v64783, w(mod(a0, 7) + 8)), w(mod(3, 7) + 8)) + (acc & 1)) & w(a0 + (v64783 ^ w(-38 * -31)))))
    return 12
def f1(a0):
    global acc
    acc = w(w(acc * 31) + f0(mod(((w(-24 * a0)) if (44) < (w(a0 * a0)) else (w(a0 - a0))), w(mod(xs[idx(max(a0, -27))], 7) + 8)), (-48 ^ f0(21, a0))))
    return a0
def main():
    global acc
    if (-7) < (mod(w(w(w(-14 - -26) + mod(21, w(mod(-41, 7) + 8))) + div(41, w(mod((-9 | -44), 7) + 8))), w(mod(-32, 7) + 8))):
        acc = w(w(acc * 31) + div(8, w(mod(min(5, max(-36, (-25 ^ -9))), 7) + 8)))
        v45538 = 9
        _i = idx(w(div(-24, w(mod(xs[idx(mod(v45538, w(mod(v45538, 7) + 8)))], 7) + 8)) + v45538)); xs[_i] = v45538
    else:
        acc = w(w(acc * 31) + f1(min((11 | min(-6, 20)), (48 | shl(26, (-27) & 15)))))
    _i = idx(xs[idx(((-8) if (f1(mod(12, w(mod(-46, 7) + 8)))) < (min(max(-46, 27), w(12 * 25))) else (w(div(24, w(mod(-24, 7) + 8)) * f0(-49, 49)))))]); xs[_i] = max(-9, ((acc) if (min(min(-2, 32), 9)) < (max(div(13, w(mod(49, 7) + 8)), mod(21, w(mod(35, 7) + 8)))) else (45)))
    if (div(23, w(mod(w(max((41 & 36), 34) * min(-28, w(39 - 11))), 7) + 8))) < (xs[idx(shl(w(shl(-6, (48) & 15) - f1(42)), ((shr(-44, (-37) & 15) & shr(50, (10) & 15))) & 15))]):
        _i = idx(w(acc + 43)); xs[_i] = w(max(((45) if (shr(-10, (-49) & 15)) < (mod(-33, w(mod(-15, 7) + 8))) else (w(19 + 4))), -35) - shl(41, (33) & 15))
        acc = w(w(acc * 31) + -21)
        _i = idx(f0(min(((45) if (-47) < (xs[idx(-15)]) else ((6 | -10))), shl(shr(-28, (-27) & 15), (div(-16, w(mod(-33, 7) + 8))) & 15)), 27)); xs[_i] = xs[idx(acc)]
    else:
        for i80704 in range(2):
            acc = w(w(acc * 31) + f0(shr(((max(i80704, i80704)) if (shl(i80704, (i80704) & 15)) < (w(i80704 + -11)) else (i80704)), (w((i80704 | i80704) - (-17 & i80704))) & 15), i80704))
            _i = idx((w(shl(i80704, (w(i80704 + i80704)) & 15) * (shr(-38, (-6) & 15) & i80704)) & (i80704 & acc))); xs[_i] = div(max((mod(-36, w(mod(i80704, 7) + 8)) & (i80704 ^ i80704)), w((i80704 & -43) + xs[idx(i80704)])), w(mod(w((-33 ^ 1) + i80704), 7) + 8))
    v94498 = acc
    v57372 = (max((-21 & w(v94498 * v94498)), max(v94498, w(v94498 * v94498))) | ((((50) if (-35) < (v94498) else (v94498)) ^ w(v94498 * v94498)) | (min(v94498, v94498) & mod(v94498, w(mod(-46, 7) + 8)))))
    _i = idx(w(23 + v57372)); xs[_i] = w(shr(v94498, (shl(v94498, ((v94498 ^ -19)) & 15)) & 15) - (11 | w(min(-20, v94498) - max(v57372, -25))))
    if (v57372) < (v94498):
        v34131 = (((shl(w(v94498 - v94498), (w(-7 + v94498)) & 15)) if (min(f0(21, v94498), f0(v57372, 14))) < (shl((v57372 ^ -48), (xs[idx(v57372)]) & 15)) else (((mod(-39, w(mod(v94498, 7) + 8))) if (w(44 + v94498)) < (w(-24 + 49)) else (((48) if (v57372) < (20) else (v94498)))))) ^ shr(w(26 + ((v94498) if (v94498) < (v57372) else (v57372))), (v57372) & 15))
        if (w((w(w(22 + v57372) - ((v94498) if (v94498) < (-47) else (v34131))) ^ w(w(-8 * 30) - w(6 * -2))) + (mod((v57372 & v34131), w(mod(w(v34131 + -16), 7) + 8)) ^ v34131))) < ((49 | (((v94498 & 8)) if (v94498) < (w(f1(-19) + ((v94498) if (43) < (33) else (v57372)))) else (f0(mod(30, w(mod(v34131, 7) + 8)), (v57372 | -1)))))):
            v95894 = v34131
            _i = idx(v34131); xs[_i] = min(v94498, v34131)
            v96143 = shr(max(w(max(v94498, v57372) - w(-25 - v57372)), 28), (v57372) & 15)
        else:
            acc = w(w(acc * 31) + w(v57372 + max((((-39) if (-32) < (v94498) else (14)) | ((v57372) if (-2) < (49) else (v94498))), w(div(v94498, w(mod(8, 7) + 8)) - mod(v57372, w(mod(v94498, 7) + 8))))))
            v33073 = shl(v57372, (w(v34131 + 5)) & 15)
    else:
        v17591 = w(v57372 - v94498)
        acc = w(w(acc * 31) + div(v17591, w(mod((max(w(v17591 - v57372), w(41 - v17591)) & v57372), 7) + 8)))
    v94456 = div(42, w(mod(v57372, 7) + 8))
    v15458 = 38
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
