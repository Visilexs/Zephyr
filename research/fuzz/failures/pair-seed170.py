
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
    acc = w(w(acc * 31) + a0)
    v1971 = mod((shr(8, (((19) if (a2) < (a0) else (a1))) & 15) & (w(a0 - a1) & a0)), w(mod(-27, 7) + 8))
    return (-21 | -13)
def f1(a0):
    global acc
    _i = idx(-50); xs[_i] = w(w((w(a0 * a0) & a0) * min(max(a0, -43), shl(a0, (-33) & 15))) - shr(39, (a0) & 15))
    if (xs[idx(shl(a0, (a0) & 15))]) < (w(a0 * a0)):
        v49922 = w(f0(shl(f0(43, a0, a0), (max(-3, a0)) & 15), acc, a0) + 16)
    else:
        _i = idx(a0); xs[_i] = (3 | min(15, 46))
    v71134 = w(max(mod(a0, w(mod(mod(22, w(mod(a0, 7) + 8)), 7) + 8)), div(((a0) if (a0) < (28) else (a0)), w(mod(a0, 7) + 8))) * 4)
    return f0(max(a0, w(23 * a0)), shr(f0(mod(-20, w(mod(-4, 7) + 8)), (a0 & a0), (45 ^ a0)), (f0(min(a0, 13), -25, w(a0 * a0))) & 15), min(43, shl(shr(-48, (-32) & 15), (((a0) if (-38) < (a0) else (-40))) & 15)))
def f2(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + (((a0) if (a1) < (a0) else (w(38 * ((a0) if (a2) < (a2) else (a2))))) & a2))
    v72934 = a0
    v97315 = xs[idx(a0)]
    return (acc ^ a0)
def main():
    global acc
    for i4310 in range(12):
        _i = idx(((xs[idx(w(w(i4310 * i4310) * w(i4310 * i4310)))]) if (min(i4310, 13)) < (min((((i4310 ^ -30)) if (xs[idx(i4310)]) < (f0(i4310, -37, i4310)) else (shl(-27, (23) & 15))), ((w(i4310 * i4310)) if (div(i4310, w(mod(i4310, 7) + 8))) < (min(38, 14)) else (i4310)))) else ((i4310 & (w(11 - i4310) ^ min(i4310, i4310)))))); xs[_i] = div(shl(acc, (i4310) & 15), w(mod(shr(-21, ((shr(i4310, (21) & 15) ^ -6)) & 15), 7) + 8))
        acc = w(w(acc * 31) + (w(min(mod(i4310, w(mod(i4310, 7) + 8)), -4) - (w(i4310 * i4310) | w(-50 * 1))) | i4310))
        acc = w(w(acc * 31) + 1)
    acc = w(w(acc * 31) + -33)
    for i23282 in range(7):
        v82408 = w(min(i23282, div((i23282 & i23282), w(mod(22, 7) + 8))) * f0(max(i23282, shl(i23282, (i23282) & 15)), -19, i23282))
        if (w((w((i23282 ^ v82408) - w(-20 - i23282)) | max(-21, i23282)) * v82408)) < (-15):
            _i = idx(shl(v82408, (-39) & 15)); xs[_i] = (w(i23282 + min((v82408 ^ -39), w(v82408 + -49))) & w(shl(shr(42, (i23282) & 15), (-16) & 15) + div(((15) if (i23282) < (v82408) else (v82408)), w(mod(max(i23282, v82408), 7) + 8))))
            _i = idx((((-26 ^ (v82408 | v82408)) & 50) & (i23282 & acc))); xs[_i] = (w(i23282 - w(w(i23282 + i23282) + -33)) | (((mod(v82408, w(mod(v82408, 7) + 8))) if (i23282) < (shr(5, (32) & 15)) else (i23282)) & mod(w(v82408 * 2), w(mod(shl(-48, (v82408) & 15), 7) + 8))))
            acc = w(w(acc * 31) + acc)
        else:
            _i = idx(i23282); xs[_i] = v82408
            _i = idx(-13); xs[_i] = v82408
    v27870 = w(min(div(mod(2, w(mod(44, 7) + 8)), w(mod((45 & -43), 7) + 8)), w((46 & 33) + shl(-35, (-34) & 15))) - f2(11, min(shl(-38, (-40) & 15), max(23, 24)), -3))
    _i = idx(w((((max(v27870, v27870) ^ ((v27870) if (v27870) < (-19) else (40)))) if (v27870) < ((w(44 + v27870) | 47)) else (-39)) * shl((div(48, w(mod(v27870, 7) + 8)) & max(v27870, v27870)), (w(v27870 * v27870)) & 15))); xs[_i] = (f0(xs[idx(div(-10, w(mod(-42, 7) + 8)))], f2(min(20, v27870), v27870, (-39 | 45)), -43) | shl(acc, (v27870) & 15))
    for i69747 in range(7):
        _i = idx(w(min(max(max(v27870, -9), 36), min(11, v27870)) + w(shr(w(2 * v27870), (v27870) & 15) + -32))); xs[_i] = i69747
        acc = w(w(acc * 31) + -22)
    _i = idx(acc); xs[_i] = ((acc | ((w(v27870 - 16)) if (w(48 * 41)) < (f2(v27870, -3, 49)) else (((-1) if (v27870) < (v27870) else (v27870))))) | -29)
    acc = w(w(acc * 31) + (w((((-30 & v27870)) if (w(v27870 * v27870)) < (-4) else (f1(v27870))) - (acc | w(v27870 - -10))) ^ 10))
    _i = idx(-45); xs[_i] = (4 ^ (xs[idx(shl(-47, (v27870) & 15))] & -16))
    v75013 = div(v27870, w(mod(21, 7) + 8))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
