
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
    v21932 = -39
    return (mod(w((a0 & 44) + mod(a0, w(mod(-18, 7) + 8))), w(mod((mod(a2, w(mod(a0, 7) + 8)) ^ min(a2, a0)), 7) + 8)) | a0)
def f1(a0, a1):
    global acc
    v97358 = a1
    if (min((div(shr(a0, (a0) & 15), w(mod(33, 7) + 8)) | a1), acc)) < (min(v97358, min(shr(w(a1 - 6), (w(a1 * -2)) & 15), xs[idx(shr(a1, (a1) & 15))]))):
        v84636 = f0(a1, w(w(w(a0 * 17) + shl(-33, (a0) & 15)) + a0), acc)
        v43612 = ((a0 & acc) & mod(8, w(mod(f0((a1 | a1), -14, shr(-33, (v97358) & 15)), 7) + 8)))
        _i = idx(shr(((((shr(-17, (v84636) & 15)) if ((-28 | a1)) < (shr(v97358, (v43612) & 15)) else (w(v43612 + a1)))) if (v43612) < (acc) else (shr(f0(v97358, v84636, v84636), (xs[idx(a0)]) & 15))), (mod(w(max(40, 27) * a0), w(mod(shl(max(v43612, -14), ((v43612 ^ v43612)) & 15), 7) + 8))) & 15)); xs[_i] = -20
    else:
        _i = idx(48); xs[_i] = shr(max(((48 ^ v97358) & a1), 10), (w(max(acc, shr(-29, (a0) & 15)) - (shr(7, (-10) & 15) | (v97358 ^ 48)))) & 15)
        acc = w(w(acc * 31) + -7)
    return xs[idx((29 & 41))]
def f2(a0, a1):
    global acc
    acc = w(w(acc * 31) + shr((-34 & xs[idx(a0)]), (xs[idx(((-21 & -20) | acc))]) & 15))
    return xs[idx((mod((-49 & -32), w(mod(48, 7) + 8)) ^ ((div(a1, w(mod(-9, 7) + 8))) if (w(-41 - 26)) < (a1) else (max(-32, 21)))))]
def f3(a0, a1, a2):
    global acc
    _i = idx((f0(f0(div(a1, w(mod(30, 7) + 8)), w(a0 + a2), a2), shr(shl(15, (a0) & 15), (shr(-13, (-25) & 15)) & 15), f0(-33, 1, shl(a1, (a1) & 15))) & min(a0, xs[idx(min(-33, -32))]))); xs[_i] = (a1 ^ (w(a0 * 30) & 42))
    return xs[idx(div(max((a2 & a0), (-36 | -3)), w(mod(a1, 7) + 8)))]
def main():
    global acc
    for i2942 in range(7):
        if ((xs[idx((xs[idx(i2942)] & (i2942 | i2942)))] & i2942)) < (((shl(i2942, (-10) & 15)) if (f3((div(i2942, w(mod(i2942, 7) + 8)) | (i2942 & i2942)), (f0(-39, 28, 6) | i2942), max(16, w(4 - i2942)))) < (i2942) else (acc))):
            v78774 = w(div(mod(acc, w(mod(div(-40, w(mod(10, 7) + 8)), 7) + 8)), w(mod(shl(i2942, ((i2942 & -4)) & 15), 7) + 8)) + f1(i2942, div(i2942, w(mod(div(17, w(mod(i2942, 7) + 8)), 7) + 8))))
            _i = idx(xs[idx(v78774)]); xs[_i] = acc
            _i = idx(v78774); xs[_i] = mod(max(w(-34 - 30), -27), w(mod(mod((f0(v78774, v78774, i2942) | (v78774 & i2942)), w(mod((w(-37 + 13) | div(46, w(mod(i2942, 7) + 8))), 7) + 8)), 7) + 8))
        else:
            v2703 = min(w(24 - mod((i2942 ^ 35), w(mod(mod(27, w(mod(i2942, 7) + 8)), 7) + 8))), mod(acc, w(mod(i2942, 7) + 8)))
        acc = w(w(acc * 31) + w(div(f3(max(i2942, -17), shr(5, (i2942) & 15), -29), w(mod(f2(mod(i2942, w(mod(-7, 7) + 8)), (-7 & -44)), 7) + 8)) * w(div(((i2942) if (i2942) < (i2942) else (7)), w(mod(w(i2942 * i2942), 7) + 8)) - ((shl(i2942, (i2942) & 15)) if (w(i2942 + -2)) < (i2942) else (((i2942) if (i2942) < (17) else (34)))))))
    acc = w(w(acc * 31) + ((13) if (9) < (-6) else (min(((22) if (w(-17 - 14)) < (mod(0, w(mod(25, 7) + 8))) else (div(46, w(mod(-35, 7) + 8)))), xs[idx(w(-36 * -16))]))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
