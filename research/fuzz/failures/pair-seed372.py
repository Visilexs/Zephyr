
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
    acc = w(w(acc * 31) + a1)
    acc = w(w(acc * 31) + shl(mod(a2, w(mod(shl(max(-13, 45), (w(-16 - a1)) & 15), 7) + 8)), (8) & 15))
    _i = idx(shl(min(-45, w(a1 + a1)), (47) & 15)); xs[_i] = a2
    return a1
def main():
    global acc
    for i90665 in range(9):
        v74700 = xs[idx(f0(shr(w(i90665 + i90665), (w(14 + i90665)) & 15), -15, i90665))]
    v82285 = ((-34) if (-5) < (shr(-19, (shr(w(47 * -40), (w(6 - 42)) & 15)) & 15)) else (((-40) if (shl(shl(-45, (-30) & 15), (f0(-35, 13, -43)) & 15)) < (-37) else (max(max(20, -44), shl(-44, (-44) & 15))))))
    for i43083 in range(12):
        acc = w(w(acc * 31) + min(w(39 - w(min(-22, v82285) + v82285)), v82285))
        _i = idx(w(acc + w(shl(f0(13, 14, 2), (-28) & 15) - 49))); xs[_i] = w(max((45 ^ min(i43083, v82285)), -49) + -6)
    for i99770 in range(7):
        if (i99770) < (i99770):
            _i = idx(shr(mod(mod(div(v82285, w(mod(i99770, 7) + 8)), w(mod(w(7 * 4), 7) + 8)), w(mod(w(shl(30, (v82285) & 15) + v82285), 7) + 8)), ((div(shr(v82285, (i99770) & 15), w(mod(-15, 7) + 8)) & i99770)) & 15)); xs[_i] = (xs[idx(f0(i99770, max(v82285, -2), mod(i99770, w(mod(-36, 7) + 8))))] | f0(v82285, w(w(v82285 * 50) - min(i99770, i99770)), v82285))
            _i = idx(i99770); xs[_i] = -46
            v31165 = xs[idx(div(f0(acc, w(v82285 * -23), v82285), w(mod(acc, 7) + 8)))]
        else:
            _i = idx(shl(min((w(36 + i99770) & (i99770 ^ i99770)), i99770), (f0(v82285, i99770, max(xs[idx(-49)], 0))) & 15)); xs[_i] = (min(f0(v82285, (i99770 ^ -40), i99770), xs[idx(shr(49, (9) & 15))]) ^ (-3 | 28))
            acc = w(w(acc * 31) + f0(f0(v82285, shl(v82285, (((-16) if (v82285) < (v82285) else (6))) & 15), mod((-10 | i99770), w(mod(w(v82285 + i99770), 7) + 8))), shr(v82285, (div(v82285, w(mod(-37, 7) + 8))) & 15), (xs[idx(w(i99770 + v82285))] & acc)))
        for i42153 in range(12):
            acc = w(w(acc * 31) + i42153)
            acc = w(w(acc * 31) + w(((shr(i99770, (shr(i42153, (i42153) & 15)) & 15)) if (w(w(v82285 - i42153) - shl(-1, (v82285) & 15))) < (v82285) else (div((i42153 ^ v82285), w(mod((i99770 ^ i99770), 7) + 8)))) + i99770))
            v65747 = div(f0(shr(acc, (-4) & 15), i42153, min((i42153 | i99770), f0(v82285, 39, v82285))), w(mod(v82285, 7) + 8))
    acc = w(w(acc * 31) + 48)
    for i47819 in range(1):
        for i48035 in range(11):
            acc = w(w(acc * 31) + acc)
        if (div(shl(i47819, (div(i47819, w(mod(-47, 7) + 8))) & 15), w(mod(shl(6, (mod(-45, w(mod(v82285, 7) + 8))) & 15), 7) + 8))) < (acc):
            acc = w(w(acc * 31) + xs[idx(shr(w(min(v82285, 39) * shl(i47819, (-39) & 15)), (max(mod(i47819, w(mod(49, 7) + 8)), 30)) & 15))])
            v96938 = v82285
        else:
            v18749 = i47819
        for i7166 in range(11):
            v75083 = xs[idx(w(i7166 * shr(-1, (v82285) & 15)))]
            v64164 = (shr((w(37 + 9) | w(-36 - i47819)), (-45) & 15) | 5)
            v52154 = -23
    v7759 = v82285
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
