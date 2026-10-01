
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
    acc = w(w(acc * 31) + shr(shr(max(w(-3 - a0), -44), (xs[idx(mod(a0, w(mod(-4, 7) + 8)))]) & 15), (xs[idx(a0)]) & 15))
    return a0
def f1(a0, a1, a2):
    global acc
    if (a1) < (acc):
        v53808 = f0(15)
        for i84966 in range(2):
            acc = w(w(acc * 31) + mod(xs[idx(xs[idx(w(-20 * a0))])], w(mod(shl(mod(-30, w(mod(max(v53808, -33), 7) + 8)), (min(i84966, f0(a2))) & 15), 7) + 8)))
            _i = idx(mod(((shl(i84966, (i84966) & 15) ^ acc) & w(shr(-33, (a2) & 15) * div(i84966, w(mod(-50, 7) + 8)))), w(mod(25, 7) + 8))); xs[_i] = shl(a2, (w(3 + -38)) & 15)
            _i = idx(i84966); xs[_i] = div(i84966, w(mod(a0, 7) + 8))
        acc = w(w(acc * 31) + w(f0(w(31 + max(v53808, -15))) * ((acc) if (w(a1 + f0(v53808))) < (w(48 * xs[idx(-33)])) else (xs[idx(a2)]))))
    else:
        if ((w(w((a0 | -26) + acc) - shr(26, (w(a1 * 9)) & 15)) | w(a1 + max((-16 | a0), w(15 * 3))))) < ((41 | w(min((-37 ^ a2), shl(a0, (a0) & 15)) * min(div(-39, w(mod(a1, 7) + 8)), a0)))):
            _i = idx(f0(w(w((a1 & 18) * mod(a0, w(mod(a1, 7) + 8))) * shl(a1, (a1) & 15)))); xs[_i] = mod(max(30, shr(((a0) if (17) < (a1) else (-6)), (w(a2 + a2)) & 15)), w(mod(f0(max(shr(a1, (a1) & 15), (a2 | a1))), 7) + 8))
            v96024 = 22
            v84749 = (f0((div(v96024, w(mod(-21, 7) + 8)) & a2)) | (w((a1 | a0) + (v96024 | 47)) ^ ((a2) if (a2) < (a1) else (w(a0 - v96024)))))
        else:
            _i = idx(max((min(a0, min(a2, -35)) ^ div(w(a1 * a1), w(mod(-15, 7) + 8))), w(shl(mod(20, w(mod(a2, 7) + 8)), (mod(-17, w(mod(a0, 7) + 8))) & 15) * w(f0(a1) * 35)))); xs[_i] = div((min(-18, div(a0, w(mod(a2, 7) + 8))) & 34), w(mod(shl(((a1 ^ -34) | a2), (a2) & 15), 7) + 8))
    acc = w(w(acc * 31) + w(shl(a2, (shl(f0(a2), (shr(a1, (a1) & 15)) & 15)) & 15) - a2))
    return (a1 | acc)
def f2(a0, a1):
    global acc
    v62811 = (acc & (max(div(17, w(mod(41, 7) + 8)), -40) & (a1 ^ shl(-38, (a1) & 15))))
    return -48
def f3(a0, a1, a2):
    global acc
    v1875 = w(w(w(((a0) if (28) < (-35) else (12)) - w(a2 + -45)) * div((a0 & -24), w(mod(max(a2, 25), 7) + 8))) + max(a0, 19))
    _i = idx(mod(w((a0 & (v1875 & a2)) * max(min(v1875, -27), shr(v1875, (a0) & 15))), w(mod((a1 ^ max(w(-6 * a1), -50)), 7) + 8))); xs[_i] = w(a0 - -12)
    return max(a0, acc)
def main():
    global acc
    acc = w(w(acc * 31) + w(32 * ((21) if (f3((-2 ^ 38), -41, -16)) < (-14) else (-18))))
    acc = w(w(acc * 31) + (shl(-14, (f3(w(-12 - 16), max(-38, 50), shr(18, (50) & 15))) & 15) | 18))
    acc = w(w(acc * 31) + shl(acc, (f1(w(mod(-44, w(mod(31, 7) + 8)) - max(-28, 33)), 50, w(acc - min(41, 3)))) & 15))
    acc = w(w(acc * 31) + (shr(10, (div((48 ^ -9), w(mod(w(-8 + 50), 7) + 8))) & 15) & 12))
    v19060 = -8
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
