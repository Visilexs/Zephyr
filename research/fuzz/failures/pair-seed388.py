
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
    for i23595 in range(11):
        acc = w(w(acc * 31) + a0)
    if (w(a1 * mod(-7, w(mod(w(a0 + a1), 7) + 8)))) < (-16):
        _i = idx(acc); xs[_i] = a1
        v14354 = a1
    else:
        acc = w(w(acc * 31) + w(w(xs[idx(w(-39 + a1))] + mod((-33 | -5), w(mod(a1, 7) + 8))) + 16))
    return w(a0 + 31)
def f1(a0, a1):
    global acc
    acc = w(w(acc * 31) + shr(w((a1 ^ ((a0) if (-15) < (a1) else (a1))) + a0), ((mod(xs[idx(a1)], w(mod((a0 | a1), 7) + 8)) & -39)) & 15))
    if (min((-29 ^ a1), w(a1 + (16 ^ w(a1 - 50))))) < (shl(shl((w(a0 + a0) | a1), (9) & 15), (a1) & 15)):
        v4336 = -13
    else:
        if (26) < (w((acc ^ f0(shl(a1, (a1) & 15), shr(a1, (-6) & 15))) - w(8 + (19 ^ min(44, a0))))):
            v9045 = mod(a1, w(mod(a1, 7) + 8))
            v75694 = mod(shl(29, (div(div(33, w(mod(v9045, 7) + 8)), w(mod(w(39 + -31), 7) + 8))) & 15), w(mod(((w(f0(a1, 32) * xs[idx(a1)])) if (div(v9045, w(mod(v9045, 7) + 8))) < (w(max(v9045, 5) * min(-26, -26))) else (v9045)), 7) + 8))
            _i = idx(v9045); xs[_i] = min(((shr(mod(50, w(mod(a0, 7) + 8)), (f0(v75694, 47)) & 15)) if (xs[idx(div(a1, w(mod(v75694, 7) + 8)))]) < (a1) else (-32)), -13)
        else:
            v23446 = a0
        if (a0) < (w((xs[idx(div(29, w(mod(a0, 7) + 8)))] ^ max(f0(49, a1), (a0 | -27))) + a1)):
            _i = idx(acc); xs[_i] = 39
            _i = idx(((a1) if (25) < (shr((((a1) if (-16) < (a1) else (a0)) & f0(a0, a0)), (acc) & 15)) else (-45))); xs[_i] = max(38, w(((a0 & 38) | ((-15) if (a1) < (49) else (a1))) - 27))
        else:
            v53870 = w(shl(14, (mod((-38 | a0), w(mod(a0, 7) + 8))) & 15) * xs[idx(w((-22 | 22) + a0))])
            _i = idx(a0); xs[_i] = (f0(shr(max(-45, a1), (v53870) & 15), 42) | v53870)
    acc = w(w(acc * 31) + a0)
    return 27
def f2(a0, a1):
    global acc
    v70660 = -36
    return 45
def main():
    global acc
    v92672 = 18
    v34777 = acc
    for i42503 in range(5):
        v21277 = v34777
        v48159 = max((w(div(36, w(mod(v92672, 7) + 8)) - -36) & shr(i42503, (i42503) & 15)), w((max(6, v92672) ^ 32) + ((32 ^ -20) & -17)))
    _i = idx(f0((-33 ^ mod(shr(-48, (v92672) & 15), w(mod(w(-30 - v92672), 7) + 8))), 26)); xs[_i] = (((w(((v34777) if (37) < (-9) else (v34777)) + div(-6, w(mod(40, 7) + 8))) | acc)) if (-39) < ((mod(min(-44, v92672), w(mod(v34777, 7) + 8)) ^ w(max(v34777, v34777) - (v92672 ^ v34777)))) else (mod(-44, w(mod(v92672, 7) + 8))))
    acc = w(w(acc * 31) + mod(max((((10 | v34777)) if ((v34777 & v92672)) < (acc) else (mod(v34777, w(mod(27, 7) + 8)))), min((v92672 ^ v34777), (v92672 & v34777))), w(mod(v92672, 7) + 8)))
    v23161 = div(acc, w(mod((((v92672 | w(v92672 + v92672))) if (v34777) < (w(v34777 * max(v34777, -31))) else (xs[idx(17)])), 7) + 8))
    v636 = w(v34777 - min((shr(v92672, (-39) & 15) ^ max(-25, -20)), shl(acc, (v34777) & 15)))
    _i = idx(v34777); xs[_i] = (shr((w(v92672 - -18) ^ w(19 - v34777)), (min(shl(6, (v636) & 15), w(-46 * v23161))) & 15) & shr((shr(47, (v92672) & 15) | max(v23161, -49)), (shl((v92672 ^ v92672), (-49) & 15)) & 15))
    v66695 = mod(((7) if (-41) < (div(div(-4, w(mod(v34777, 7) + 8)), w(mod(8, 7) + 8))) else (w((v34777 | 40) * mod(-31, w(mod(v636, 7) + 8))))), w(mod(acc, 7) + 8))
    _i = idx(w((shr(-41, ((v636 | 24)) & 15) | -40) - ((xs[idx(v636)]) if (max(v34777, (v34777 | v34777))) < ((f1(v636, -25) | v636)) else (w(((48) if (-45) < (-12) else (-20)) + shr(v66695, (v23161) & 15)))))); xs[_i] = xs[idx(((v92672) if (8) < (v66695) else (div(xs[idx(v636)], w(mod(v23161, 7) + 8)))))]
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
