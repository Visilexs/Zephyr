
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
    if ((-36 | shr(shr(((48) if (-37) < (a2) else (-15)), (w(38 * 31)) & 15), (w(max(35, a1) + 42)) & 15))) < (w(mod(min(w(a0 - a0), (a1 ^ a1)), w(mod(shl(36, (w(a0 + a2)) & 15), 7) + 8)) + w(w(-37 * (a0 ^ 16)) * (min(a1, -21) & w(-29 * a2))))):
        v5717 = w((8 ^ div(w(a2 - 9), w(mod(w(a1 * -38), 7) + 8))) - min(((47) if (xs[idx(46)]) < (((-14) if (6) < (a1) else (-39))) else ((-26 & 15))), a2))
        _i = idx(a0); xs[_i] = min(a0, ((39) if (((-15 & a1) ^ acc)) < (w(w(v5717 - a0) + v5717)) else (a2)))
        v46027 = w(w((((a0 & v5717)) if (shr(42, (a0) & 15)) < (shr(v5717, (a1) & 15)) else (w(11 * a2))) * w(w(-5 * a0) * max(v5717, v5717))) + w(mod(max(a2, a0), w(mod(-47, 7) + 8)) - xs[idx(w(a2 - a1))]))
    else:
        v50772 = 17
    return acc
def f1(a0, a1):
    global acc
    acc = w(w(acc * 31) + w(a1 - a1))
    return 10
def f2(a0, a1, a2):
    global acc
    _i = idx(acc); xs[_i] = w(a0 - (a0 ^ a0))
    for i51924 in range(9):
        v26723 = w(shl(39, (shl(-39, ((a2 & -22)) & 15)) & 15) + a1)
        _i = idx(shl(div(shr(div(-47, w(mod(a2, 7) + 8)), (w(1 - a2)) & 15), w(mod(28, 7) + 8)), (mod(-4, w(mod(mod(v26723, w(mod(((36) if (i51924) < (v26723) else (-9)), 7) + 8)), 7) + 8))) & 15)); xs[_i] = acc
        acc = w(w(acc * 31) + w(((((v26723) if (a0) < (v26723) else (a2)) | v26723) & xs[idx(xs[idx(-13)])]) - 4))
    for i74735 in range(1):
        if (acc) < (mod(((max(w(a0 - -28), a0)) if (w(8 - shl(-24, (a0) & 15))) < (xs[idx(min(a0, -36))]) else ((a1 & ((13) if (22) < (i74735) else (-30))))), w(mod((((min(i74735, i74735)) if (shl(-13, (31) & 15)) < ((32 & a2)) else ((a1 ^ a2))) ^ max(shl(-8, (a0) & 15), (40 | -20))), 7) + 8))):
            v47221 = min((acc & ((-19) if (xs[idx(-18)]) < (mod(-32, w(mod(i74735, 7) + 8))) else (shl(a2, (a2) & 15)))), shl(mod(min(9, 28), w(mod(a1, 7) + 8)), (shl(shr(a2, (47) & 15), (w(a0 + a0)) & 15)) & 15))
            v62239 = (w(-41 * 9) ^ a2)
        else:
            v64589 = w(max(div(a2, w(mod(-31, 7) + 8)), 45) - i74735)
            _i = idx(22); xs[_i] = min(22, -12)
        _i = idx(shr((shr(f0(a1, -2, 22), (a2) & 15) ^ a0), (div(a1, w(mod((((i74735) if (11) < (a0) else (-3)) & 6), 7) + 8))) & 15)); xs[_i] = ((a0 & (acc & a0)) ^ a0)
    return mod(a1, w(mod(div(min(w(a0 - a1), acc), w(mod(a2, 7) + 8)), 7) + 8))
def f3(a0):
    global acc
    _i = idx(acc); xs[_i] = w(a0 * w(w(shr(a0, (17) & 15) + ((a0) if (a0) < (a0) else (a0))) * a0))
    return -39
def main():
    global acc
    acc = w(w(acc * 31) + w(w(w(f0(9, -42, -41) - -19) + -16) * shr(w(((32) if (-15) < (-3) else (40)) - 6), (-11) & 15)))
    acc = w(w(acc * 31) + 11)
    v39761 = ((xs[idx(w(37 * max(50, 28)))]) if (6) < (-5) else (div(mod(min(15, 4), w(mod(shl(10, (-26) & 15), 7) + 8)), w(mod(w((-19 | -48) - ((-17) if (-18) < (2) else (39))), 7) + 8))))
    for i83496 in range(5):
        v21767 = mod(shl(acc, (w(acc * w(-28 + v39761))) & 15), w(mod(shr(shr(div(34, w(mod(i83496, 7) + 8)), (max(i83496, i83496)) & 15), (mod(((37) if (-31) < (v39761) else (-25)), w(mod(i83496, 7) + 8))) & 15), 7) + 8))
        v49972 = -46
        if (div(v39761, w(mod((mod(xs[idx(-3)], w(mod(w(i83496 + 28), 7) + 8)) | v49972), 7) + 8))) < (shl(min(mod(div(v39761, w(mod(-7, 7) + 8)), w(mod(44, 7) + 8)), acc), (w(-5 * w(shl(i83496, (v39761) & 15) * max(v21767, i83496)))) & 15)):
            v69485 = acc
            acc = w(w(acc * 31) + v69485)
            v46436 = f0(acc, w(i83496 - -30), max(-30, v39761))
        else:
            _i = idx((acc & 10)); xs[_i] = -2
    acc = w(w(acc * 31) + (shr(shr(min(v39761, -40), (w(v39761 - -25)) & 15), ((v39761 | (v39761 ^ v39761))) & 15) ^ w(47 - w(f1(v39761, v39761) + v39761))))
    acc = w(w(acc * 31) + f1(13, shl((v39761 ^ div(-42, w(mod(v39761, 7) + 8))), ((shr(11, (v39761) & 15) | -23)) & 15)))
    if (-28) < (mod((mod(v39761, w(mod(min(v39761, v39761), 7) + 8)) ^ -1), w(mod(min(f1(5, shr(v39761, (v39761) & 15)), -27), 7) + 8))):
        acc = w(w(acc * 31) + f0(xs[idx((mod(v39761, w(mod(21, 7) + 8)) & (-16 | v39761)))], f1(v39761, -3), v39761))
    else:
        acc = w(w(acc * 31) + shr(min(div(w(37 + v39761), w(mod(shr(v39761, (v39761) & 15), 7) + 8)), xs[idx(v39761)]), ((shr(mod(-10, w(mod(v39761, 7) + 8)), (shr(28, (18) & 15)) & 15) ^ v39761)) & 15))
        _i = idx(5); xs[_i] = shl(v39761, (v39761) & 15)
    acc = w(w(acc * 31) + (mod(v39761, w(mod(xs[idx((27 & v39761))], 7) + 8)) | 39))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
