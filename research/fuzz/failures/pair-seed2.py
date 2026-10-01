
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
    acc = w(w(acc * 31) + -11)
    return a0
def main():
    global acc
    for i56448 in range(11):
        if (max(((41) if (w(max(i56448, 4) - (i56448 ^ i56448))) < ((max(36, i56448) | max(-5, i56448))) else (shr(acc, (max(8, 9)) & 15))), ((((-19 | -43) & w(i56448 - i56448))) if (shr((28 ^ i56448), (xs[idx(i56448)]) & 15)) < (w(min(-26, -37) * -16)) else (-47)))) < (-3):
            v20593 = w(w(shr(i56448, ((i56448 & i56448)) & 15) - w(f0(i56448) - -37)) + -34)
            acc = w(w(acc * 31) + acc)
        else:
            v44702 = 3
            _i = idx((div(i56448, w(mod(shr(w(-21 - -41), (v44702) & 15), 7) + 8)) | i56448)); xs[_i] = i56448
        v94865 = i56448
    v30346 = -47
    acc = w(w(acc * 31) + mod(f0(shl(xs[idx(v30346)], ((34 ^ -4)) & 15)), w(mod(-35, 7) + 8)))
    for i37955 in range(12):
        acc = w(w(acc * 31) + xs[idx(v30346)])
        acc = w(w(acc * 31) + max((i37955 & shl(w(10 + 42), (mod(i37955, w(mod(i37955, 7) + 8))) & 15)), i37955))
    if (xs[idx(mod((div(v30346, w(mod(v30346, 7) + 8)) ^ v30346), w(mod(w(w(v30346 - v30346) * mod(v30346, w(mod(v30346, 7) + 8))), 7) + 8)))]) < (2):
        for i47199 in range(9):
            _i = idx(w(shr(shl(f0(i47199), ((v30346 & 27)) & 15), (shl((v30346 & v30346), ((i47199 | v30346)) & 15)) & 15) * shl(w(acc * w(12 * -8)), (((div(50, w(mod(42, 7) + 8))) if (i47199) < (50) else (i47199))) & 15))); xs[_i] = mod(i47199, w(mod(max(22, mod((i47199 | i47199), w(mod(mod(0, w(mod(v30346, 7) + 8)), 7) + 8))), 7) + 8))
            acc = w(w(acc * 31) + v30346)
        if (mod(21, w(mod(v30346, 7) + 8))) < (-2):
            v46672 = v30346
            acc = w(w(acc * 31) + ((acc) if (((min(26, min(46, 40))) if (shl(min(v30346, v46672), (v30346) & 15)) < (31) else (mod(w(v46672 * v46672), w(mod(max(v30346, -27), 7) + 8))))) < (f0((max(v46672, v46672) & -1))) else ((shl((50 & v46672), (v30346) & 15) | shr(w(v46672 - 28), (v30346) & 15)))))
        else:
            acc = w(w(acc * 31) + v30346)
            acc = w(w(acc * 31) + f0(f0(min(w(v30346 * 38), xs[idx(v30346)]))))
        acc = w(w(acc * 31) + ((v30346 ^ -22) & v30346))
    else:
        _i = idx(w(acc - v30346)); xs[_i] = v30346
        v71585 = min(shr(v30346, (shr(v30346, (f0(0)) & 15)) & 15), ((shl(v30346, (v30346) & 15) | v30346) ^ (acc & v30346)))
    _i = idx(39); xs[_i] = (v30346 & v30346)
    for i81976 in range(1):
        v94610 = w(shr(min(v30346, -27), (w(((-15) if (-24) < (i81976) else (16)) * xs[idx(35)])) & 15) - 31)
        if (-23) < (div(f0((((v30346) if (-6) < (v94610) else (i81976)) | v94610)), w(mod(w(10 * 34), 7) + 8))):
            _i = idx(mod(mod(-47, w(mod(i81976, 7) + 8)), w(mod(min(w(w(v94610 + v30346) * 42), i81976), 7) + 8))); xs[_i] = acc
            acc = w(w(acc * 31) + shr(v30346, (-8) & 15))
            _i = idx(xs[idx(v30346)]); xs[_i] = xs[idx(i81976)]
        else:
            _i = idx(w(1 + i81976)); xs[_i] = acc
        for i92382 in range(8):
            _i = idx(v30346); xs[_i] = v94610
            v6367 = mod((w((i81976 | v94610) * max(37, 27)) & max(div(-14, w(mod(i81976, 7) + 8)), v30346)), w(mod(w(w(xs[idx(i81976)] * w(v94610 + -13)) - -19), 7) + 8))
            _i = idx(shr(max(v30346, v30346), (v6367) & 15)); xs[_i] = shr(v6367, (xs[idx((v94610 | -27))]) & 15)
    acc = w(w(acc * 31) + v30346)
    if (((max(min((-9 ^ 17), f0(v30346)), max(v30346, v30346))) if (shr((max(v30346, 33) ^ f0(v30346)), (((-28) if (-1) < (max(21, v30346)) else (acc))) & 15)) < ((min(f0(50), div(35, w(mod(v30346, 7) + 8))) ^ v30346)) else (shl(-29, (f0(div(v30346, w(mod(v30346, 7) + 8)))) & 15)))) < (max((shr(v30346, (shl(v30346, (v30346) & 15)) & 15) ^ ((28 ^ v30346) ^ shl(v30346, (v30346) & 15))), div(w(-11 + v30346), w(mod(-28, 7) + 8)))):
        if (((((w((v30346 | -25) * w(-7 + 42))) if (w(((v30346) if (-31) < (29) else (32)) - v30346)) < (v30346) else (v30346))) if (w(18 * 17)) < (mod(v30346, w(mod(-27, 7) + 8))) else (3))) < (acc):
            v8349 = ((v30346 & ((v30346 | v30346) | w(35 * v30346))) | w(min(acc, max(17, 34)) - (f0(v30346) | (v30346 & v30346))))
            acc = w(w(acc * 31) + shr(v8349, (min(v8349, v8349)) & 15))
            acc = w(w(acc * 31) + v30346)
        else:
            v17140 = ((xs[idx((v30346 & -26))] & -18) ^ mod(xs[idx(f0(-28))], w(mod(w(v30346 + acc), 7) + 8)))
    else:
        v28644 = (shl(shl((-11 ^ -32), (w(36 * v30346)) & 15), (w(mod(v30346, w(mod(-22, 7) + 8)) - shl(v30346, (v30346) & 15))) & 15) & div(1, w(mod(w(v30346 - w(v30346 - v30346)), 7) + 8)))
        acc = w(w(acc * 31) + (((acc ^ -13)) if (v28644) < (v28644) else (47)))
    if (w((v30346 | min(v30346, v30346)) * v30346)) < (v30346):
        v87052 = (shr(v30346, (w((v30346 & v30346) - (-50 ^ v30346))) & 15) ^ shr(32, (v30346) & 15))
        _i = idx((v30346 ^ 22)); xs[_i] = max(-11, w(w((-5 | v87052) * xs[idx(-38)]) - shr((v30346 | 11), (v87052) & 15)))
    else:
        acc = w(w(acc * 31) + -37)
        acc = w(w(acc * 31) + (v30346 | w(v30346 - shr(-46, (v30346) & 15))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
