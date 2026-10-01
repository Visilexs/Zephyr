
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
    v12529 = (a2 & -34)
    acc = w(w(acc * 31) + div(-16, w(mod((acc & -19), 7) + 8)))
    return w(w(w(shl(a1, (a0) & 15) + (a0 & a0)) * shl(((30) if (20) < (a0) else (a1)), (9) & 15)) + w(shl(mod(a0, w(mod(6, 7) + 8)), (shl(a0, (-7) & 15)) & 15) + a2))
def main():
    global acc
    _i = idx(max(50, f0(shl(-41, (shr(32, (28) & 15)) & 15), mod(41, w(mod(-1, 7) + 8)), xs[idx(9)]))); xs[_i] = mod((1 | shr(w(12 - 13), ((12 & 12)) & 15)), w(mod(min((div(-15, w(mod(42, 7) + 8)) & w(-13 * 2)), f0(-32, 39, (-33 | 41))), 7) + 8))
    v71378 = max(20, -44)
    for i74197 in range(3):
        if (v71378) < (w(div(w(max(v71378, 18) * v71378), w(mod(xs[idx(w(v71378 - i74197))], 7) + 8)) * i74197)):
            _i = idx((min(((16) if ((v71378 | -10)) < (div(i74197, w(mod(i74197, 7) + 8))) else (i74197)), w((-15 ^ i74197) + v71378)) ^ shr(i74197, ((shr(v71378, (6) & 15) ^ (v71378 | i74197))) & 15))); xs[_i] = ((min(xs[idx(i74197)], shr(36, (acc) & 15))) if (-10) < (shr(-16, ((((i74197) if (v71378) < (45) else (i74197)) & xs[idx(49)])) & 15)) else (max(-43, w(shr(v71378, (31) & 15) * mod(-37, w(mod(v71378, 7) + 8))))))
            v61188 = i74197
        else:
            acc = w(w(acc * 31) + w((w(w(-31 * -46) - -6) | -41) * f0(i74197, v71378, min(-39, i74197))))
        for i45100 in range(12):
            acc = w(w(acc * 31) + w(w(v71378 - f0(shr(i45100, (i45100) & 15), v71378, shl(v71378, (47) & 15))) - div(div(w(1 - i74197), w(mod(shl(-12, (-33) & 15), 7) + 8)), w(mod((w(i74197 * i45100) | -34), 7) + 8))))
            _i = idx(-7); xs[_i] = shr(w(w(i45100 * acc) * min(19, v71378)), (33) & 15)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
