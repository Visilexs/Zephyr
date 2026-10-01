
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
    acc = w(w(acc * 31) + w(a1 + ((((-44 ^ a0) | xs[idx(10)])) if (shr((-3 | a0), (-41) & 15)) < (min(w(a0 * 34), w(4 * -36))) else (w(div(a1, w(mod(-1, 7) + 8)) * (a1 & a0))))))
    v56381 = a1
    v26791 = (shr(-46, (acc) & 15) & w(max(a1, acc) - 9))
    return max(-22, w(min(14, -4) + (a1 | shr(14, (a1) & 15))))
def f1(a0, a1):
    global acc
    _i = idx((w(15 - ((a0) if (shl(16, (a0) & 15)) < ((a1 | a0)) else (div(3, w(mod(a0, 7) + 8))))) ^ shl(max(f0(a0, -46), xs[idx(a1)]), (mod(37, w(mod((a1 & a0), 7) + 8))) & 15))); xs[_i] = min(a0, mod(xs[idx(w(a1 + a0))], w(mod(a1, 7) + 8)))
    if (mod(14, w(mod(min(a0, w(shr(a1, (a1) & 15) - (a1 & a0))), 7) + 8))) < (acc):
        for i22328 in range(3):
            v71342 = a1
            _i = idx(26); xs[_i] = 27
        acc = w(w(acc * 31) + 34)
    else:
        acc = w(w(acc * 31) + div(f0(f0(a1, a0), max(mod(-11, w(mod(-23, 7) + 8)), w(a0 + a0))), w(mod(a1, 7) + 8)))
        _i = idx(mod(w((acc & ((a1) if (a0) < (0) else (a1))) + w(div(a0, w(mod(a1, 7) + 8)) + xs[idx(a1)])), w(mod(shr(a0, (shr(22, (w(a1 + 8)) & 15)) & 15), 7) + 8))); xs[_i] = xs[idx(min(f0(min(47, -4), a1), div(a1, w(mod(min(46, a1), 7) + 8))))]
    acc = w(w(acc * 31) + max(a1, (((mod(a1, w(mod(26, 7) + 8))) if (div(a0, w(mod(a1, 7) + 8))) < (a1) else ((-24 ^ 29))) | max((a1 | 32), min(-41, 17)))))
    return a1
def f2(a0):
    global acc
    acc = w(w(acc * 31) + shr(-21, (a0) & 15))
    for i77299 in range(3):
        if ((f1(max(-25, i77299), min(mod(a0, w(mod(-13, 7) + 8)), mod(-31, w(mod(16, 7) + 8)))) | min(a0, i77299))) < (i77299):
            acc = w(w(acc * 31) + shl(i77299, (max(((-17 & i77299) | -27), w(w(-1 + i77299) - i77299))) & 15))
            _i = idx(f0(max((17 | div(-22, w(mod(i77299, 7) + 8))), f0(w(33 - 38), a0)), ((a0 | -5) & shr(w(-14 + i77299), ((46 ^ i77299)) & 15)))); xs[_i] = xs[idx(29)]
            _i = idx(28); xs[_i] = i77299
        else:
            _i = idx(max(w(min(acc, shr(-38, (13) & 15)) - (((36) if (i77299) < (-26) else (a0)) ^ ((i77299) if (-36) < (i77299) else (-9)))), ((shr(13, ((16 | a0)) & 15)) if (xs[idx(shl(a0, (-32) & 15))]) < ((i77299 ^ (a0 | 8))) else (div(i77299, w(mod(w(a0 + a0), 7) + 8)))))); xs[_i] = xs[idx((w(-32 + shl(a0, (i77299) & 15)) ^ i77299))]
            v10469 = -3
        v94526 = ((xs[idx(xs[idx(i77299)])] & div(acc, w(mod(w(i77299 + a0), 7) + 8))) ^ acc)
    for i51479 in range(12):
        acc = w(w(acc * 31) + -30)
        for i22037 in range(12):
            _i = idx(mod(shr(-10, (min((-42 ^ a0), f0(i51479, i51479))) & 15), w(mod(w(i51479 + a0), 7) + 8))); xs[_i] = w(shr(i22037, ((a0 | (29 ^ a0))) & 15) + max((i51479 ^ (a0 & a0)), w(w(a0 - 40) + i22037)))
            acc = w(w(acc * 31) + w((36 & 10) * xs[idx(mod(acc, w(mod(xs[idx(i22037)], 7) + 8)))]))
            v73353 = xs[idx(xs[idx((-6 ^ acc))])]
        v99064 = max(i51479, xs[idx(i51479)])
    return acc
def f3(a0):
    global acc
    acc = w(w(acc * 31) + w(a0 + -3))
    _i = idx(w((max(f0(22, a0), a0) & f1((a0 | a0), xs[idx(a0)])) - a0)); xs[_i] = min(shl(xs[idx(19)], (a0) & 15), shl(shr(-49, (27) & 15), (((a0 ^ a0) & xs[idx(1)])) & 15))
    acc = w(w(acc * 31) + mod(max(w((a0 ^ a0) + (a0 | -32)), min(xs[idx(a0)], w(a0 + 4))), w(mod(acc, 7) + 8)))
    return a0
def main():
    global acc
    v58239 = shr(min(((5 & 11) ^ (10 | 13)), f1(shr(43, (21) & 15), xs[idx(43)])), ((f3(w(40 - -24)) & -17)) & 15)
    v67539 = shr((v58239 & div(w(v58239 + -4), w(mod(w(v58239 + v58239), 7) + 8))), (xs[idx(w(xs[idx(v58239)] + max(0, v58239)))]) & 15)
    v42927 = v58239
    v49888 = v42927
    for i77353 in range(11):
        _i = idx(v42927); xs[_i] = ((w(v58239 - min(shl(v58239, (46) & 15), 7))) if (w(xs[idx((-9 ^ v49888))] * w((-5 & v42927) + w(v67539 - v42927)))) < (xs[idx(-15)]) else (min(f2(v67539), (v58239 & v49888))))
        v14703 = v49888
    _i = idx(((shl(div(v42927, w(mod(-32, 7) + 8)), (max(v67539, v49888)) & 15) & (-36 & 11)) ^ v49888)); xs[_i] = div(div(-41, w(mod(shl((-9 ^ v49888), (v58239) & 15), 7) + 8)), w(mod(shl(div((v49888 | 8), w(mod(v67539, 7) + 8)), (min((v58239 & v42927), (v58239 & v67539))) & 15), 7) + 8))
    if (max(v67539, v49888)) < ((xs[idx(((v49888 ^ v67539) ^ w(v67539 + v42927)))] | ((14) if (v58239) < (mod(w(v58239 + 19), w(mod((13 & -11), 7) + 8))) else ((w(v67539 + -26) ^ acc))))):
        acc = w(w(acc * 31) + w(div((shr(48, (-35) & 15) & -19), w(mod(w(v67539 - (v67539 & -8)), 7) + 8)) - 18))
    else:
        acc = w(w(acc * 31) + xs[idx(((w(v49888 + -31) | div(v58239, w(mod(v58239, 7) + 8))) ^ acc))])
    _i = idx(v42927); xs[_i] = mod(28, w(mod(mod((v67539 | xs[idx(v49888)]), w(mod(shl(v42927, (div(21, w(mod(v58239, 7) + 8))) & 15), 7) + 8)), 7) + 8))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
