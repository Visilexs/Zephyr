
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
    if (mod(-6, w(mod(-7, 7) + 8))) < (w(a2 + acc)):
        v64942 = 16
        acc = w(w(acc * 31) + min(w(shl(div(a0, w(mod(32, 7) + 8)), ((4 | a0)) & 15) + a0), w(min(47, w(1 * a0)) + w(v64942 + w(a0 - a2)))))
        _i = idx(shl(w(max(shl(a2, (v64942) & 15), a0) - min(shr(37, (a0) & 15), xs[idx(a2)])), (a1) & 15)); xs[_i] = w(min(a1, (acc ^ w(40 + 14))) + -33)
    else:
        v77163 = xs[idx(a1)]
    acc = w(w(acc * 31) + a2)
    return (((div(w(a2 * a0), w(mod(-6, 7) + 8)) & div(a2, w(mod(max(a0, a0), 7) + 8)))) if (w(shl(shl(a0, (a1) & 15), (acc) & 15) + min(min(a0, -42), xs[idx(-25)]))) < (w(w(45 * (35 & a2)) + shl(max(a1, a2), (23) & 15))) else ((29 ^ div((a0 | 27), w(mod(div(a0, w(mod(a0, 7) + 8)), 7) + 8)))))
def f1(a0):
    global acc
    _i = idx(f0(a0, shr(min(-46, shl(a0, (a0) & 15)), (-11) & 15), mod(w(div(0, w(mod(17, 7) + 8)) - a0), w(mod((-23 & -46), 7) + 8)))); xs[_i] = ((f0(xs[idx(-15)], 32, 38)) if (4) < (max(a0, ((acc) if (div(0, w(mod(a0, 7) + 8))) < ((24 | 37)) else (a0)))) else (w(mod(mod(17, w(mod(a0, 7) + 8)), w(mod((a0 & a0), 7) + 8)) - div(-9, w(mod(-7, 7) + 8)))))
    return -7
def f2(a0):
    global acc
    acc = w(w(acc * 31) + f1(w(w(acc * -40) - acc)))
    _i = idx(w(a0 * xs[idx(w(-46 * a0))])); xs[_i] = div(div(a0, w(mod(div(mod(15, w(mod(a0, 7) + 8)), w(mod(f1(a0), 7) + 8)), 7) + 8)), w(mod(w(max(xs[idx(a0)], shl(a0, (a0) & 15)) * max(shl(a0, (-20) & 15), w(a0 * -37))), 7) + 8))
    return w(mod((((12) if (a0) < (a0) else (a0)) | a0), w(mod(shl(shr(10, (11) & 15), (w(-3 * -45)) & 15), 7) + 8)) * w(a0 + ((a0) if (w(a0 - -41)) < ((a0 & 3)) else (-33))))
def main():
    global acc
    if (acc) < (f1(-8)):
        _i = idx(w(max(xs[idx(10)], div((-18 | 4), w(mod((8 | -32), 7) + 8))) * shl(mod(shr(28, (-33) & 15), w(mod(-6, 7) + 8)), (-29) & 15))); xs[_i] = xs[idx(20)]
    else:
        v72670 = -23
    _i = idx((-7 | w(div(shr(15, (1) & 15), w(mod(-33, 7) + 8)) * w(max(37, -5) + w(-13 + -21))))); xs[_i] = shl(-35, (-30) & 15)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
