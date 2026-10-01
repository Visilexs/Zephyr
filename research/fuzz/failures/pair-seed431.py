
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
    if (a0) < (4):
        v11879 = w(a0 + ((((15) if (a0) < (-18) else (a0)) ^ w(a0 - 10)) ^ w(acc - acc)))
        acc = w(w(acc * 31) + a0)
        v39848 = v11879
    else:
        v34121 = shr((div((a0 | a0), w(mod(xs[idx(a0)], 7) + 8)) & mod(w(-13 - -25), w(mod(w(a0 * a0), 7) + 8))), (w(a0 * shr(((a0) if (-48) < (-3) else (6)), (a0) & 15))) & 15)
        v58226 = v34121
    _i = idx((w(xs[idx(w(a0 + a0))] + xs[idx(-47)]) | (-43 ^ div(-18, w(mod(a0, 7) + 8))))); xs[_i] = div(w(a0 + div(min(a0, a0), w(mod(max(a0, 48), 7) + 8))), w(mod(w(a0 - a0), 7) + 8))
    if (a0) < (shl(a0, ((-12 | shr(a0, ((47 & -45)) & 15))) & 15)):
        acc = w(w(acc * 31) + shl(w(((max(15, a0)) if (a0) < ((a0 ^ a0)) else (min(44, a0))) * mod(max(a0, a0), w(mod(a0, 7) + 8))), (mod(div(w(-14 + a0), w(mod(a0, 7) + 8)), w(mod((w(a0 + 19) & a0), 7) + 8))) & 15))
    else:
        _i = idx(acc); xs[_i] = w((w(xs[idx(a0)] - w(4 * 7)) ^ (shl(33, (a0) & 15) | shl(-27, (32) & 15))) + 27)
        acc = w(w(acc * 31) + w(((-5) if (shl(w(11 - a0), (div(a0, w(mod(-36, 7) + 8))) & 15)) < (w(a0 * w(a0 + a0))) else (-14)) + a0))
    return max(a0, 37)
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + xs[idx(a0)])
    return a0
def f2(a0, a1, a2):
    global acc
    _i = idx((acc | acc)); xs[_i] = shr(-42, (w(shl(w(18 - a1), ((a2 | -16)) & 15) + (w(a0 * 10) & 33))) & 15)
    for i97730 in range(4):
        acc = w(w(acc * 31) + ((47) if (shl(w(24 + w(a1 * i97730)), (a1) & 15)) < ((div(shl(-22, (a0) & 15), w(mod(w(13 - a2), 7) + 8)) | max(shr(-41, (a2) & 15), w(47 - 47)))) else (mod(w(div(a1, w(mod(a2, 7) + 8)) * div(i97730, w(mod(a1, 7) + 8))), w(mod(min(shl(a1, (a2) & 15), max(a0, i97730)), 7) + 8)))))
        for i20263 in range(2):
            acc = w(w(acc * 31) + w((a2 | mod(-9, w(mod(mod(24, w(mod(a1, 7) + 8)), 7) + 8))) + (a2 ^ i20263)))
            v4783 = shr(a2, ((28 & -48)) & 15)
        v8640 = a0
    _i = idx(a2); xs[_i] = w(div(shl(a2, ((a2 & -42)) & 15), w(mod(shl(w(a0 - a1), (27) & 15), 7) + 8)) * a0)
    return mod(-43, w(mod((a1 ^ ((shr(a0, (a1) & 15)) if (acc) < ((a0 | -17)) else (w(a2 - a2)))), 7) + 8))
def main():
    global acc
    acc = w(w(acc * 31) + w(w((w(-43 - -49) & 5) - xs[idx(xs[idx(23)])]) * 46))
    for i20492 in range(2):
        for i85246 in range(1):
            _i = idx(xs[idx(-50)]); xs[_i] = i20492
            v94990 = acc
            acc = w(w(acc * 31) + (shr(max(w(i85246 - -24), i20492), (i20492) & 15) | -48))
    v75602 = (20 ^ min(f1(w(-3 * 3), 27, (-44 | 45)), -17))
    acc = w(w(acc * 31) + f1(div(((v75602) if (v75602) < (mod(v75602, w(mod(v75602, 7) + 8))) else (v75602)), w(mod(((w(v75602 * 22)) if ((v75602 | 43)) < (v75602) else (acc)), 7) + 8)), 25, w(acc - v75602)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
