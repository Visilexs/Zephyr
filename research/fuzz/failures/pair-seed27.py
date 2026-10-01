
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
    _i = idx(a2); xs[_i] = max(w(12 + w(xs[idx(44)] * w(32 + a0))), min(shr((a1 | 45), (w(17 - a1)) & 15), div(w(a2 - a0), w(mod(xs[idx(a1)], 7) + 8))))
    acc = w(w(acc * 31) + div(a2, w(mod(a0, 7) + 8)))
    return acc
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + f0(mod(a2, w(mod(a1, 7) + 8)), w(shl(acc, ((a0 & a0)) & 15) + -38), a2))
    return w(-5 + shl(a2, (f0(w(a0 - a0), acc, a1)) & 15))
def f2(a0):
    global acc
    acc = w(w(acc * 31) + ((shl(a0, (a0) & 15)) if (-12) < ((min(w(-35 - a0), a0) | a0)) else (((w(max(-12, -26) * shr(43, (-20) & 15))) if (shr(a0, (((a0) if (a0) < (a0) else (a0))) & 15)) < (f1(shr(a0, (30) & 15), 12, ((39) if (a0) < (a0) else (a0)))) else (a0)))))
    for i84218 in range(3):
        acc = w(w(acc * 31) + w((w(((a0) if (50) < (a0) else (i84218)) - div(a0, w(mod(32, 7) + 8))) & a0) + i84218))
        for i19675 in range(2):
            _i = idx(w(div(w(w(i84218 * a0) + -31), w(mod(i84218, 7) + 8)) + w(((i84218 | 44) & min(i84218, i19675)) - i84218))); xs[_i] = f1(((49 & -14) ^ f1(div(a0, w(mod(-41, 7) + 8)), xs[idx(i19675)], (i19675 ^ a0))), acc, acc)
            acc = w(w(acc * 31) + f1(min(w(w(34 + -48) + f0(i19675, 3, -45)), div(-34, w(mod(12, 7) + 8))), 20, acc))
            v81455 = (i84218 ^ i84218)
    for i54747 in range(1):
        acc = w(w(acc * 31) + shl(a0, ((max(acc, shr(i54747, (i54747) & 15)) & xs[idx(w(-46 - i54747))])) & 15))
        for i65040 in range(9):
            acc = w(w(acc * 31) + f1((shr(w(3 + a0), (f1(15, i65040, -14)) & 15) & max(a0, shl(-2, (i54747) & 15))), 45, w(-32 - a0)))
            v45472 = acc
            acc = w(w(acc * 31) + w(f0(31, f0(shl(-21, (v45472) & 15), min(v45472, 8), a0), shr(48, (i54747) & 15)) + a0))
    return a0
def f3(a0, a1, a2):
    global acc
    _i = idx(mod(min(-48, (w(a0 - -9) ^ f1(a1, a1, 30))), w(mod(shr(w(((a0) if (a2) < (-34) else (a2)) - w(47 * -49)), (div(((16) if (a2) < (a2) else (-19)), w(mod(shr(25, (-19) & 15), 7) + 8))) & 15), 7) + 8))); xs[_i] = (shr(((28 & 5) ^ a2), ((a1 | a2)) & 15) | -26)
    acc = w(w(acc * 31) + div(a2, w(mod(shl(((w(a0 + a0)) if ((a2 ^ -50)) < ((a1 ^ a2)) else (shl(a0, (-24) & 15))), ((25 ^ -46)) & 15), 7) + 8)))
    acc = w(w(acc * 31) + acc)
    return mod(shr(48, (xs[idx(xs[idx(a2)])]) & 15), w(mod(shl(37, (a0) & 15), 7) + 8))
def main():
    global acc
    acc = w(w(acc * 31) + (acc & xs[idx((f1(-23, -19, -10) ^ 47))]))
    v7725 = (min(xs[idx(21)], mod(xs[idx(-50)], w(mod(mod(-6, w(mod(-35, 7) + 8)), 7) + 8))) ^ -3)
    v38262 = v7725
    acc = w(w(acc * 31) + -34)
    if (shl(shr(w(w(v38262 + v38262) - 48), ((w(23 + v38262) & shr(v7725, (v7725) & 15))) & 15), (acc) & 15)) < (w(w(f1(div(-43, w(mod(-3, 7) + 8)), -11, v7725) + (v7725 & v38262)) + ((v38262 & shr(-40, (v38262) & 15)) ^ (27 | acc)))):
        if (19) < (w((v7725 & f3(max(v7725, v38262), v38262, v38262)) - v38262)):
            acc = w(w(acc * 31) + min(div(f2(acc), w(mod(v7725, 7) + 8)), w(-3 + shr(shr(-6, (v38262) & 15), (32) & 15))))
        else:
            v69787 = -24
    else:
        if (xs[idx(max(v38262, v38262))]) < (40):
            _i = idx((((xs[idx(shl(v7725, (v38262) & 15))]) if ((((v38262) if (-7) < (v38262) else (v7725)) & f1(v7725, v7725, v38262))) < (f2((v7725 & v38262))) else (mod(((v7725) if (v38262) < (-20) else (v7725)), w(mod(v38262, 7) + 8)))) | ((shr(-29, (v7725) & 15)) if (xs[idx(min(v38262, 50))]) < (div(20, w(mod(v7725, 7) + 8))) else (min(v38262, v7725))))); xs[_i] = v7725
            _i = idx(mod((f0(div(-17, w(mod(v38262, 7) + 8)), ((v38262) if (22) < (v38262) else (v38262)), v38262) ^ shl(acc, (acc) & 15)), w(mod((f2(shr(-37, (v38262) & 15)) ^ f2(((v38262) if (v38262) < (v38262) else (42)))), 7) + 8))); xs[_i] = v38262
            acc = w(w(acc * 31) + div(shr((w(v38262 + 44) ^ w(v38262 + -26)), (max(v7725, f0(-13, v7725, v7725))) & 15), w(mod(((shl(15, (w(v38262 + v7725)) & 15)) if (max(mod(36, w(mod(v7725, 7) + 8)), v38262)) < (shl(((v38262) if (v7725) < (v7725) else (-2)), (shr(22, (v7725) & 15)) & 15)) else (16)), 7) + 8)))
        else:
            acc = w(w(acc * 31) + max(v38262, shr(shr(((v38262) if (24) < (-49) else (20)), (w(v7725 + v38262)) & 15), (w(mod(v38262, w(mod(v38262, 7) + 8)) - (-39 ^ v38262))) & 15)))
            _i = idx(min(-32, (w((29 | 42) - xs[idx(v38262)]) & 4))); xs[_i] = w(xs[idx(v38262)] + min(v38262, acc))
    acc = w(w(acc * 31) + acc)
    _i = idx((v38262 & acc)); xs[_i] = shr(w(-11 * max((-31 & v38262), w(v38262 * v38262))), (shl(acc, (v7725) & 15)) & 15)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
