
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
    acc = w(w(acc * 31) + min(((a2) if (((48) if (w(a2 + a0)) < (xs[idx(a2)]) else (35))) < (min(shl(a0, (-5) & 15), (a2 ^ -20))) else (w((a0 | a2) + a0))), min(((w(a0 - -21)) if (w(a2 + a1)) < (((2) if (-3) < (a1) else (a1))) else ((a1 ^ -30))), -2)))
    if (w(shr(div(-42, w(mod(w(a1 * -11), 7) + 8)), (acc) & 15) * ((w((-6 & a0) * xs[idx(a2)])) if (-31) < (max(28, div(a2, w(mod(-31, 7) + 8)))) else ((xs[idx(a1)] | shl(-41, (a0) & 15)))))) < (a2):
        _i = idx(min(w(a0 * 31), xs[idx(41)])); xs[_i] = shr(w(((max(42, a1)) if (shl(-4, (a2) & 15)) < (((a0) if (a0) < (a1) else (a1))) else (w(-19 - a0))) * a0), ((div(acc, w(mod((a2 & a1), 7) + 8)) & 37)) & 15)
        _i = idx(a0); xs[_i] = 50
    else:
        if (div(a2, w(mod(mod(div(((31) if (a0) < (a2) else (a1)), w(mod(((a0) if (a1) < (a1) else (a0)), 7) + 8)), w(mod(((8 ^ a1) | w(26 + -12)), 7) + 8)), 7) + 8))) < (w(w((shr(a2, (-43) & 15) | -40) - ((8 | a1) & a2)) + w(a2 + xs[idx(-11)]))):
            v80643 = (w(min(w(a1 + 7), max(a1, -8)) * w(0 + -19)) ^ (a1 | shl(a1, (shl(a0, (a0) & 15)) & 15)))
        else:
            _i = idx(a0); xs[_i] = (w(w(38 - acc) * a2) ^ w(shl(xs[idx(a0)], (shr(-24, (a2) & 15)) & 15) - (-31 & w(a0 + 49))))
            v39565 = w(a1 - (1 ^ w(shr(a0, (40) & 15) - w(a2 + 6))))
        v91358 = div(a2, w(mod(shr(shr(div(a1, w(mod(-47, 7) + 8)), ((a0 ^ a0)) & 15), (a2) & 15), 7) + 8))
    for i5140 in range(1):
        if (div(shr(((24) if (min(43, 46)) < (shl(a1, (i5140) & 15)) else (22)), (w(w(8 + a2) + w(-45 - a1))) & 15), w(mod(w(xs[idx(shr(-40, (-8) & 15))] + mod((45 & 46), w(mod(a1, 7) + 8))), 7) + 8))) < (w(div(max(max(-46, a1), w(-28 - a1)), w(mod(((a1) if (a0) < (42) else (div(48, w(mod(a0, 7) + 8)))), 7) + 8)) * acc)):
            _i = idx(div(div(w(w(a0 - 5) + (i5140 & -24)), w(mod(((-20 ^ a2) | min(-29, a0)), 7) + 8)), w(mod(i5140, 7) + 8))); xs[_i] = max(6, w(shl(div(a0, w(mod(-12, 7) + 8)), (mod(a2, w(mod(-17, 7) + 8))) & 15) + (a1 | a1)))
        else:
            _i = idx(max(-3, w(a1 + a0))); xs[_i] = w((w(15 + min(a1, a0)) ^ 29) - w(28 + a1))
            acc = w(w(acc * 31) + a2)
        if (shr(-18, (mod(div(mod(-40, w(mod(i5140, 7) + 8)), w(mod(mod(a2, w(mod(16, 7) + 8)), 7) + 8)), w(mod(xs[idx(w(3 * i5140))], 7) + 8))) & 15)) < (((i5140 ^ shr(shr(11, (33) & 15), (div(-42, w(mod(40, 7) + 8))) & 15)) | shl((w(a0 * i5140) & min(a1, a2)), (w((a2 | 18) + a2)) & 15))):
            _i = idx(shr((-45 & a1), (min(acc, div(shr(a0, (a2) & 15), w(mod(mod(i5140, w(mod(i5140, 7) + 8)), 7) + 8)))) & 15)); xs[_i] = max(w(a2 - min(-7, a2)), div(((-43) if (max(-32, a1)) < (w(49 - -15)) else (a2)), w(mod(a2, 7) + 8)))
            _i = idx(min(shl(w(shl(-32, (a0) & 15) + (15 ^ a1)), (a1) & 15), (w(a1 + div(1, w(mod(26, 7) + 8))) | (w(a1 * -34) ^ w(a2 + a2))))); xs[_i] = mod(w(w(div(a1, w(mod(a0, 7) + 8)) * w(a1 + a2)) + a1), w(mod(i5140, 7) + 8))
            v27302 = shr(w(-11 - a0), (a0) & 15)
        else:
            _i = idx(w(div(i5140, w(mod(i5140, 7) + 8)) + (shl(a2, ((i5140 & -15)) & 15) ^ xs[idx(20)]))); xs[_i] = w(shr(30, (i5140) & 15) - ((max((a1 & i5140), 9)) if (mod((a2 & -30), w(mod(max(a0, a0), 7) + 8))) < (max(shl(a2, (14) & 15), mod(a2, w(mod(-15, 7) + 8)))) else (i5140)))
            _i = idx(div(mod(mod(w(a0 * a0), w(mod((a2 ^ -41), 7) + 8)), w(mod(w((i5140 & a2) + shl(a2, (-14) & 15)), 7) + 8)), w(mod(shr(w((a2 & 3) - shr(6, (a2) & 15)), (w(41 - a1)) & 15), 7) + 8))); xs[_i] = (a0 ^ w((w(-4 + a1) | w(i5140 - a1)) * mod(mod(a2, w(mod(i5140, 7) + 8)), w(mod(xs[idx(a1)], 7) + 8))))
    return acc
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + ((max(w(a0 + -9), acc) | ((w(a1 * a0)) if (mod(-11, w(mod(a2, 7) + 8))) < ((a1 ^ a2)) else (-3))) ^ min(w(((a2) if (-36) < (-14) else (a0)) - a0), w(a1 + -25))))
    if ((a2 & a0)) < (a1):
        if (div(-24, w(mod(shr(a1, (max(xs[idx(a0)], 22)) & 15), 7) + 8))) < (w(((a2) if (-31) < (w((a2 ^ -16) + shl(a1, (35) & 15))) else (shr(f0(a2, -42, 45), (a2) & 15))) * 49)):
            _i = idx(1); xs[_i] = ((w(w(f0(-21, -14, 9) + 29) - a0)) if (-14) < (mod(a1, w(mod(xs[idx(shr(a2, (a0) & 15))], 7) + 8))) else (((min((a1 | a1), mod(a2, w(mod(a0, 7) + 8)))) if (w(-39 - -38)) < ((div(30, w(mod(33, 7) + 8)) ^ mod(a1, w(mod(a0, 7) + 8)))) else (max(f0(a2, a0, -5), f0(a1, a1, -44))))))
            _i = idx(w(div(mod(a2, w(mod(min(a1, a0), 7) + 8)), w(mod(((shl(-3, (-25) & 15)) if (mod(45, w(mod(a1, 7) + 8))) < (w(-15 + -45)) else (shr(a1, (a0) & 15))), 7) + 8)) * div(xs[idx(min(a1, 38))], w(mod(-46, 7) + 8)))); xs[_i] = ((w(a2 * w(shr(4, (36) & 15) * a0))) if ((-29 ^ acc)) < (a2) else (xs[idx((xs[idx(a2)] | 12))]))
            v7454 = div(xs[idx(a0)], w(mod(shl(a2, (shr(shl(a0, (a0) & 15), (max(a0, -2)) & 15)) & 15), 7) + 8))
        else:
            v22257 = max(xs[idx(a2)], xs[idx((f0(a2, a0, a1) ^ 6))])
        v61994 = (a1 | min(acc, min(a2, (a0 & a1))))
    else:
        if (div(shr((shr(-7, (20) & 15) ^ min(a1, 47)), (f0((a1 & 35), f0(a2, a0, a0), 47)) & 15), w(mod(35, 7) + 8))) < (min(33, -10)):
            _i = idx(-21); xs[_i] = acc
        else:
            _i = idx(f0(mod(a2, w(mod(w(22 - -40), 7) + 8)), ((acc | f0(6, -9, 18)) & w(a0 * w(a1 - a2))), w(min(15, a2) + shr(mod(a2, w(mod(9, 7) + 8)), (mod(a0, w(mod(-1, 7) + 8))) & 15)))); xs[_i] = 48
            _i = idx(-12); xs[_i] = min(12, -42)
    if (((a0) if (f0(a2, shl((a2 & -4), (41) & 15), a0)) < ((a1 ^ a1)) else (shl(a0, (xs[idx(shl(a0, (a0) & 15))]) & 15)))) < (w(a0 - w(acc - (a0 | div(a0, w(mod(17, 7) + 8)))))):
        acc = w(w(acc * 31) + a2)
    else:
        for i7198 in range(2):
            v89410 = shr(w(shr(xs[idx(6)], ((9 | 47)) & 15) + ((a2) if (a2) < (a0) else (a2))), (shl(shl(w(a0 - 12), ((46 ^ -15)) & 15), ((shl(30, (i7198) & 15) ^ acc)) & 15)) & 15)
    return -49
def main():
    global acc
    _i = idx(div(((32) if (shl(50, (max(-14, -34)) & 15)) < ((mod(50, w(mod(44, 7) + 8)) ^ 17)) else ((w(-43 - -35) ^ shr(3, (-19) & 15)))), w(mod(w(shr(w(30 + -38), (23) & 15) * div(f1(6, -18, 43), w(mod(-11, 7) + 8))), 7) + 8))); xs[_i] = ((-34 ^ (((36 ^ 40)) if (45) < (acc) else (shr(-6, (7) & 15)))) & 49)
    if (acc) < (42):
        if (37) < (xs[idx(xs[idx(28)])]):
            _i = idx((shl(xs[idx(shl(41, (31) & 15))], (w(40 - w(-20 + -16))) & 15) ^ -22)); xs[_i] = w(-45 + f1(div(49, w(mod((-37 ^ -10), 7) + 8)), (-37 & 36), div(13, w(mod(21, 7) + 8))))
        else:
            _i = idx(shl(w(-35 * shr(shr(40, (31) & 15), ((-30 | -29)) & 15)), (-29) & 15)); xs[_i] = acc
            _i = idx(div(15, w(mod(-33, 7) + 8))); xs[_i] = xs[idx(34)]
        for i78042 in range(4):
            acc = w(w(acc * 31) + f1(min(((17 & i78042) & mod(i78042, w(mod(47, 7) + 8))), w((18 & i78042) + acc)), f0(f1(i78042, div(-37, w(mod(i78042, 7) + 8)), w(i78042 * 32)), 6, 44), i78042))
    else:
        for i87751 in range(3):
            v68696 = w(-26 - mod(w(mod(i87751, w(mod(17, 7) + 8)) + xs[idx(38)]), w(mod(i87751, 7) + 8)))
            acc = w(w(acc * 31) + i87751)
            v56463 = i87751
    for i15221 in range(1):
        _i = idx(-22); xs[_i] = xs[idx(xs[idx(div(-19, w(mod(i15221, 7) + 8)))])]
        for i23260 in range(4):
            _i = idx((-33 | xs[idx(i23260)])); xs[_i] = w(w(-20 + w(-23 + max(i23260, i15221))) - shr(w(-38 - (i23260 & i15221)), ((i23260 | w(i15221 * i23260))) & 15))
        v1987 = 24
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
