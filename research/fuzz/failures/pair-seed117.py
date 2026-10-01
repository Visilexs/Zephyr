
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
    v20795 = (min(w(a0 - a0), ((a0 ^ a0) ^ shr(a0, (a0) & 15))) & w(-3 + div(w(a0 + -3), w(mod(a0, 7) + 8))))
    return min(a0, xs[idx(w(((18) if (23) < (-14) else (a0)) - shl(-2, (a0) & 15)))])
def f1(a0, a1, a2):
    global acc
    v74122 = max(w(a2 - min(shr(-16, (a2) & 15), (a2 & 24))), div(34, w(mod(max((a1 & 5), (-45 | a0)), 7) + 8)))
    acc = w(w(acc * 31) + f0(-33))
    return a1
def main():
    global acc
    v34984 = f1(44, div(acc, w(mod(28, 7) + 8)), w((div(-43, w(mod(13, 7) + 8)) & ((-12) if (22) < (-6) else (-46))) + w(max(-46, -26) + ((-47) if (39) < (4) else (17)))))
    if (shl(w(w(max(33, v34984) * xs[idx(-39)]) * shr(mod(v34984, w(mod(-39, 7) + 8)), (w(v34984 - -22)) & 15)), (v34984) & 15)) < (w(-28 + min(min((-40 & v34984), v34984), v34984))):
        _i = idx(max(((v34984) if (div(shl(v34984, (v34984) & 15), w(mod(-1, 7) + 8))) < ((shr(v34984, (-50) & 15) ^ acc)) else (v34984)), (15 & div(shl(v34984, (19) & 15), w(mod(v34984, 7) + 8))))); xs[_i] = min(-31, min(xs[idx(v34984)], ((-36 | v34984) | shr(49, (v34984) & 15))))
        v17728 = (f0((3 ^ xs[idx(v34984)])) ^ w(shr(50, (v34984) & 15) - -27))
        _i = idx((((shr(acc, ((-4 & -49)) & 15)) if (shl(xs[idx(v17728)], (shr(v34984, (v17728) & 15)) & 15)) < (shl(21, (-13) & 15)) else (w((v17728 ^ 32) * 11))) | w(w(xs[idx(v17728)] * -11) * 48))); xs[_i] = div(min(v34984, w(v17728 - v34984)), w(mod(min(v17728, w(19 * shl(v34984, (v34984) & 15))), 7) + 8))
    else:
        if (w((mod((v34984 ^ v34984), w(mod(shl(v34984, (v34984) & 15), 7) + 8)) | f1(((v34984) if (v34984) < (-26) else (-21)), xs[idx(46)], w(v34984 - -47))) - w(acc * shl((4 & v34984), (v34984) & 15)))) < (div(mod(-7, w(mod(w((-1 ^ 14) + v34984), 7) + 8)), w(mod(w((w(-45 - -31) | v34984) - -22), 7) + 8))):
            v27998 = ((max(((22) if (shr(v34984, (17) & 15)) < (v34984) else (v34984)), xs[idx(v34984)])) if (max(v34984, acc)) < ((mod(div(v34984, w(mod(v34984, 7) + 8)), w(mod(v34984, 7) + 8)) & max(v34984, acc))) else (shr((shr(31, (v34984) & 15) & 48), (w(-3 + (16 ^ v34984))) & 15)))
            _i = idx((v27998 | shl(shr(24, (v34984) & 15), (max(div(v27998, w(mod(v27998, 7) + 8)), shl(v27998, (v34984) & 15))) & 15))); xs[_i] = min((-28 | w(w(v27998 - 13) - w(v27998 * v34984))), v34984)
        else:
            _i = idx(v34984); xs[_i] = xs[idx(-44)]
    acc = w(w(acc * 31) + -36)
    if (acc) < (((7) if (max(xs[idx((v34984 & v34984))], v34984)) < (v34984) else (max(v34984, w(shr(v34984, (-3) & 15) + v34984))))):
        v40560 = (((w(w(v34984 * -14) - max(-17, v34984))) if (w((v34984 ^ -50) - ((46) if (v34984) < (v34984) else (v34984)))) < (-38) else ((mod(9, w(mod(14, 7) + 8)) ^ f1(v34984, v34984, 30)))) | (w(v34984 + acc) ^ xs[idx(max(v34984, v34984))]))
    else:
        for i38878 in range(6):
            _i = idx(f1(-7, v34984, (acc ^ shr(max(i38878, v34984), (min(-19, i38878)) & 15)))); xs[_i] = w(acc + i38878)
    _i = idx(shr(w(mod(w(-45 * v34984), w(mod(v34984, 7) + 8)) - xs[idx(acc)]), (v34984) & 15)); xs[_i] = w(xs[idx(min((-37 | v34984), (-23 ^ v34984)))] + w(acc * xs[idx(v34984)]))
    v35888 = mod(w(v34984 - w(max(v34984, v34984) * (34 | v34984))), w(mod(min(mod(max(v34984, -40), w(mod((v34984 ^ -46), 7) + 8)), xs[idx(shl(-49, (v34984) & 15))]), 7) + 8))
    v60685 = shr(v34984, (v34984) & 15)
    acc = w(w(acc * 31) + max(v60685, shr(v60685, (max(shr(v60685, (-11) & 15), (-38 ^ v34984))) & 15)))
    for i32152 in range(12):
        _i = idx((-6 | v35888)); xs[_i] = w(mod(v35888, w(mod(v34984, 7) + 8)) * w(v34984 + (v34984 ^ mod(v35888, w(mod(-25, 7) + 8)))))
        acc = w(w(acc * 31) + shl(acc, (max(shr(v35888, ((-33 | 31)) & 15), 21)) & 15))
        _i = idx(v34984); xs[_i] = v35888
    acc = w(w(acc * 31) + w(v34984 + f1(w(min(v35888, 49) - xs[idx(-11)]), w(v60685 * 22), min(f0(-17), shr(v35888, (v35888) & 15)))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
