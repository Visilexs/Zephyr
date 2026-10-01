
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
    acc = w(w(acc * 31) + w(acc - (min(w(-23 - 38), a0) ^ shr(-34, (a1) & 15))))
    return a0
def main():
    global acc
    v13617 = f0(-49, xs[idx(-10)])
    if (50) < (v13617):
        for i43489 in range(5):
            v52217 = (max(46, 17) ^ w(xs[idx(((30) if (26) < (-44) else (i43489)))] * xs[idx(v13617)]))
            acc = w(w(acc * 31) + i43489)
            acc = w(w(acc * 31) + w((v13617 | i43489) * xs[idx(v52217)]))
        for i49846 in range(9):
            acc = w(w(acc * 31) + min(-31, 36))
            v93634 = shr(max(min(shl(-23, (v13617) & 15), 21), w(((v13617) if (i49846) < (i49846) else (i49846)) * i49846)), (40) & 15)
            v20102 = v93634
    else:
        v19870 = (xs[idx(-3)] | v13617)
    for i91910 in range(5):
        for i11411 in range(9):
            _i = idx(div(min(w(max(i91910, 44) * div(i91910, w(mod(v13617, 7) + 8))), w(v13617 * mod(v13617, w(mod(i11411, 7) + 8)))), w(mod(max(i11411, w((-1 ^ 35) + i91910)), 7) + 8))); xs[_i] = (i91910 | (w(w(-2 - i91910) + max(i91910, -19)) & min(w(33 - 47), shr(i91910, (-11) & 15))))
            acc = w(w(acc * 31) + (w(v13617 + div((-43 ^ v13617), w(mod(shl(i11411, (24) & 15), 7) + 8))) ^ w(-42 + 39)))
            _i = idx(w(((div(acc, w(mod(div(-18, w(mod(-3, 7) + 8)), 7) + 8))) if (max(shr(v13617, (28) & 15), w(i11411 - 46))) < (div(acc, w(mod(min(v13617, 15), 7) + 8))) else (((w(v13617 - v13617)) if (i91910) < (((12) if (i11411) < (i91910) else (47))) else (i11411)))) * ((-19) if (div((-15 ^ i11411), w(mod(shl(i91910, (8) & 15), 7) + 8))) < (i11411) else (xs[idx((-12 & i11411))])))); xs[_i] = i11411
        for i61738 in range(6):
            acc = w(w(acc * 31) + mod(mod(xs[idx(-33)], w(mod(((4 ^ 41) ^ -15), 7) + 8)), w(mod(max(v13617, i91910), 7) + 8)))
            _i = idx(-50); xs[_i] = (v13617 & v13617)
        v43634 = (shr(v13617, (f0(i91910, i91910)) & 15) ^ 46)
    acc = w(w(acc * 31) + -46)
    acc = w(w(acc * 31) + f0(39, -5))
    v37996 = ((xs[idx(max(4, v13617))] | mod(w(v13617 * v13617), w(mod(f0(38, v13617), 7) + 8))) & shl(mod(w(43 - v13617), w(mod(((-30) if (v13617) < (v13617) else (-45)), 7) + 8)), ((((45 & -37)) if (max(v13617, 3)) < (v13617) else (shr(48, (v13617) & 15)))) & 15))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
