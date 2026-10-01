
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
    _i = idx(a0); xs[_i] = (-42 ^ min(w(div(-31, w(mod(a1, 7) + 8)) + 46), 40))
    return a1
def f1(a0):
    global acc
    acc = w(w(acc * 31) + w(min(((shl(a0, (-22) & 15)) if (a0) < (-42) else (acc)), a0) + acc))
    _i = idx(div(shl((xs[idx(a0)] | (a0 ^ a0)), ((a0 | 4)) & 15), w(mod(acc, 7) + 8))); xs[_i] = div(a0, w(mod(f0(30, shr(15, (w(a0 * a0)) & 15)), 7) + 8))
    acc = w(w(acc * 31) + acc)
    return w(w(a0 * a0) * a0)
def main():
    global acc
    if (48) < (f0(((-17) if (-14) < (w(-34 - 0)) else (f1(w(16 - 8)))), w(-4 * (acc | (-14 | 26))))):
        if ((((xs[idx((3 ^ -47))]) if (xs[idx((-32 & 49))]) < (((xs[idx(-17)]) if (-30) < (w(-41 * 26)) else (-5))) else (f1(f0(-39, 36)))) & -1)) < (((-29) if (max(w(f0(45, 29) + shr(-5, (-12) & 15)), mod(f1(11), w(mod(41, 7) + 8)))) < (((shl(15, (shl(6, (-22) & 15)) & 15)) if (div(22, w(mod(div(15, w(mod(-15, 7) + 8)), 7) + 8))) < (-1) else (41))) else (-8))):
            v78381 = (((w((-2 & -12) + -29) | ((5 ^ 40) | mod(-28, w(mod(-34, 7) + 8))))) if (w(-42 * max(div(-46, w(mod(-44, 7) + 8)), (14 & 6)))) < (w(mod(f0(-12, 0), w(mod(min(5, 24), 7) + 8)) - 8)) else (w((min(22, -45) ^ shr(26, (-2) & 15)) + 21)))
            acc = w(w(acc * 31) + mod(9, w(mod(f0(((((v78381) if (v78381) < (v78381) else (v78381))) if (1) < (v78381) else ((-12 & v78381))), (max(v78381, v78381) ^ w(v78381 * v78381))), 7) + 8)))
        else:
            acc = w(w(acc * 31) + acc)
            v16768 = 33
    else:
        acc = w(w(acc * 31) + w((shr(min(42, 47), (shr(-26, (-17) & 15)) & 15) & -31) - min(w((20 & 9) - f0(15, -44)), div((-8 ^ 9), w(mod(w(11 * 8), 7) + 8)))))
    acc = w(w(acc * 31) + max(((shl(shr(-17, (25) & 15), (27) & 15)) if (w((-7 ^ 42) * shr(-24, (-16) & 15))) < (-25) else (mod(15, w(mod(-34, 7) + 8)))), -21))
    v66036 = -5
    if (w(mod(mod(7, w(mod(min(-24, v66036), 7) + 8)), w(mod(2, 7) + 8)) - v66036)) < (v66036):
        if ((min((max(v66036, -16) ^ (v66036 ^ v66036)), f0(f1(v66036), shl(-20, (v66036) & 15))) & mod(xs[idx(((v66036) if (v66036) < (v66036) else (v66036)))], w(mod(-18, 7) + 8)))) < (mod(((shr(w(46 - v66036), ((v66036 & 41)) & 15)) if (v66036) < ((div(v66036, w(mod(v66036, 7) + 8)) | (v66036 ^ v66036))) else (11)), w(mod(w(w(xs[idx(-2)] * shr(v66036, (v66036) & 15)) + xs[idx(xs[idx(-24)])]), 7) + 8))):
            v8000 = xs[idx(w(w(acc - -8) - v66036))]
        else:
            v55197 = xs[idx((w(((v66036) if (-9) < (6) else (v66036)) + v66036) | shl((31 & v66036), (w(v66036 + v66036)) & 15)))]
    else:
        acc = w(w(acc * 31) + div(f1((7 | max(v66036, v66036))), w(mod(v66036, 7) + 8)))
        _i = idx(max(shl((w(v66036 - v66036) ^ ((v66036) if (v66036) < (-18) else (v66036))), (30) & 15), acc)); xs[_i] = (min(-8, f1(-49)) | v66036)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
