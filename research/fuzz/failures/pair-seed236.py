
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
    acc = w(w(acc * 31) + (mod(div(max(a0, a0), w(mod((a0 & a1), 7) + 8)), w(mod(3, 7) + 8)) | div(min(w(a1 + 21), acc), w(mod(max((a0 | 40), mod(-45, w(mod(45, 7) + 8))), 7) + 8))))
    acc = w(w(acc * 31) + min(a0, w(acc * (min(7, a1) & 21))))
    _i = idx(min(w(a0 + w(a0 + a1)), div(33, w(mod(a0, 7) + 8)))); xs[_i] = div(w(a1 + a0), w(mod(11, 7) + 8))
    return (div(a0, w(mod(a0, 7) + 8)) | (-46 | div(max(a0, 8), w(mod(a1, 7) + 8))))
def f1(a0, a1):
    global acc
    v98641 = -39
    if (19) < (max(a0, (a1 | (13 ^ a1)))):
        for i29751 in range(12):
            acc = w(w(acc * 31) + a0)
            v75975 = v98641
        acc = w(w(acc * 31) + f0(mod(div(a1, w(mod(v98641, 7) + 8)), w(mod(w(min(12, a1) * shl(a0, (a0) & 15)), 7) + 8)), -12))
        acc = w(w(acc * 31) + 16)
    else:
        acc = w(w(acc * 31) + shl(a0, (xs[idx(mod(w(19 + 44), w(mod(w(-48 - a0), 7) + 8)))]) & 15))
    return shl(37, (w(0 * shr(a0, (f0(7, a0)) & 15))) & 15)
def f2(a0, a1, a2):
    global acc
    v58638 = mod(shr((a1 & a1), (shr(w(a0 * 26), (a0) & 15)) & 15), w(mod(div(w(mod(a2, w(mod(15, 7) + 8)) * a0), w(mod(mod(a2, w(mod(48, 7) + 8)), 7) + 8)), 7) + 8))
    v64262 = max(a1, a2)
    acc = w(w(acc * 31) + a2)
    return a0
def main():
    global acc
    _i = idx(35); xs[_i] = 28
    _i = idx(w(shr(((23) if ((-46 & -34)) < (21) else ((37 & -22))), (min(w(47 + -49), min(28, 36))) & 15) - mod((7 | f1(-13, 42)), w(mod(max(w(36 - 47), shl(-33, (34) & 15)), 7) + 8)))); xs[_i] = f1(29, mod(acc, w(mod(7, 7) + 8)))
    _i = idx(shl(((18) if (30) < (w(shl(-29, (17) & 15) - shr(9, (-3) & 15))) else (shl(-16, (mod(33, w(mod(-49, 7) + 8))) & 15))), (16) & 15)); xs[_i] = -25
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
