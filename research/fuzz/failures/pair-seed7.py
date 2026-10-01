
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
    for i9494 in range(9):
        acc = w(w(acc * 31) + a0)
    v54810 = a0
    return a0
def f1(a0, a1, a2):
    global acc
    for i8108 in range(10):
        acc = w(w(acc * 31) + w((a0 | (a1 ^ w(a1 * i8108))) - ((shl((0 | i8108), (a2) & 15)) if (((((a2) if (a0) < (i8108) else (i8108))) if (shr(39, (-40) & 15)) < (acc) else (w(23 * -10)))) < (max(((-42) if (a0) < (10) else (a2)), ((i8108) if (i8108) < (-6) else (a0)))) else (xs[idx(div(-5, w(mod(-2, 7) + 8)))]))))
        v77217 = a1
        acc = w(w(acc * 31) + min(w(f0((i8108 & a0)) - ((a0) if (a0) < (v77217) else (i8108))), a2))
    for i62147 in range(2):
        if (((max(w(acc + -6), max(max(a0, a1), acc))) if (mod(a2, w(mod(acc, 7) + 8))) < ((shl(max(a0, -12), (w(-17 * a1)) & 15) ^ shr(min(28, 47), (shr(44, (-25) & 15)) & 15))) else (w(max(w(-35 * 50), shl(a1, (a2) & 15)) + 42)))) < (f0((w(33 + 10) ^ max(a0, 33)))):
            acc = w(w(acc * 31) + xs[idx(shl(shl(a1, (min(i62147, -43)) & 15), (max(xs[idx(14)], w(49 + a0))) & 15))])
        else:
            _i = idx(w(w(shl(((-17) if (i62147) < (a1) else (-25)), ((i62147 | a0)) & 15) * xs[idx(50)]) + max(9, 0))); xs[_i] = (shr(i62147, (shl(w(-48 * i62147), (w(a2 + a0)) & 15)) & 15) ^ -21)
    _i = idx(a0); xs[_i] = (a1 ^ div(acc, w(mod(w(-27 * w(a0 * -17)), 7) + 8)))
    return -42
def f2(a0, a1):
    global acc
    acc = w(w(acc * 31) + xs[idx(div(w(shr(-30, (a0) & 15) - a1), w(mod(shl(a0, (-18) & 15), 7) + 8)))])
    return shr((xs[idx(f1(-21, a0, a1))] & 14), (mod(mod(a1, w(mod(div(a1, w(mod(20, 7) + 8)), 7) + 8)), w(mod(w(mod(a0, w(mod(a1, 7) + 8)) - a0), 7) + 8))) & 15)
def main():
    global acc
    acc = w(w(acc * 31) + -17)
    if (25) < (-48):
        acc = w(w(acc * 31) + 24)
        _i = idx((f1(acc, 42, (41 | xs[idx(43)])) | (w(shr(-40, (-47) & 15) + 31) | (((30) if (21) < (-44) else (-48)) & shr(12, (-17) & 15))))); xs[_i] = -42
    else:
        for i8657 in range(12):
            acc = w(w(acc * 31) + div(-21, w(mod(((mod((i8657 | i8657), w(mod(acc, 7) + 8))) if (f0(mod(28, w(mod(-25, 7) + 8)))) < (i8657) else (i8657)), 7) + 8)))
            acc = w(w(acc * 31) + shl(w(w(i8657 + f0(-24)) * i8657), ((div(max(i8657, i8657), w(mod(i8657, 7) + 8)) | (f1(i8657, i8657, -35) | shl(44, (i8657) & 15)))) & 15))
            v51139 = w(xs[idx(w(i8657 - (i8657 | i8657)))] * f2(w(7 * (-14 | i8657)), i8657))
    v96866 = div(shr(f0(-30), (14) & 15), w(mod(acc, 7) + 8))
    for i59373 in range(6):
        acc = w(w(acc * 31) + shr(v96866, (max(v96866, xs[idx(shl(i59373, (13) & 15))])) & 15))
        for i69366 in range(11):
            v32565 = ((i59373) if (mod(w(i59373 + acc), w(mod(i69366, 7) + 8))) < (((((div(i59373, w(mod(-36, 7) + 8))) if (-50) < (shr(v96866, (-12) & 15)) else (i69366))) if (v96866) < (-37) else (i69366))) else (v96866))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
