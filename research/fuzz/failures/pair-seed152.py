
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
    return (27 & a0)
def f1(a0, a1, a2):
    global acc
    v71577 = mod(min(div(xs[idx(a0)], w(mod(-27, 7) + 8)), w(shl(a0, (a0) & 15) + ((a2) if (-48) < (-9) else (a2)))), w(mod(-4, 7) + 8))
    return w(max(9, xs[idx(a0)]) - xs[idx((-21 & w(a1 * a0)))])
def f2(a0):
    global acc
    acc = w(w(acc * 31) + -14)
    return ((((xs[idx(w(a0 * a0))]) if (min(max(a0, a0), acc)) < (acc) else (acc))) if ((mod(((a0) if (a0) < (-28) else (-25)), w(mod((-28 & a0), 7) + 8)) | a0)) < (a0) else (20))
def f3(a0, a1, a2):
    global acc
    _i = idx(xs[idx(a1)]); xs[_i] = xs[idx((a1 ^ w(shr(a1, (a0) & 15) * ((a0) if (-42) < (-42) else (9)))))]
    acc = w(w(acc * 31) + (w(26 - shr(31, (-17) & 15)) & shr((max(-20, 31) | a1), (f2(-14)) & 15)))
    return w(shl(div(20, w(mod((48 & a2), 7) + 8)), (((w(-20 * a1)) if (15) < (a2) else (a1))) & 15) + w(a1 + w((a2 ^ a2) - xs[idx(40)])))
def main():
    global acc
    _i = idx(-22); xs[_i] = shr(-14, (acc) & 15)
    acc = w(w(acc * 31) + 16)
    _i = idx((max(w(shl(34, (-15) & 15) - mod(36, w(mod(-10, 7) + 8))), shr(div(-38, w(mod(50, 7) + 8)), (xs[idx(-34)]) & 15)) & -26)); xs[_i] = xs[idx(-13)]
    acc = w(w(acc * 31) + f2((-31 ^ shl(-48, (f2(-8)) & 15))))
    for i90543 in range(1):
        v92942 = min(-25, i90543)
    for i94368 in range(7):
        acc = w(w(acc * 31) + (acc ^ i94368))
    v30959 = max(shr((22 | acc), (f1(10, (49 ^ -27), w(-35 * -33))) & 15), mod(acc, w(mod(-25, 7) + 8)))
    v29008 = v30959
    v48950 = ((min(div(v30959, w(mod(max(v29008, -35), 7) + 8)), min(shr(v30959, (-35) & 15), 0))) if (w(min(max(v29008, v30959), f2(-47)) + f3(43, w(45 + v29008), ((v29008) if (v29008) < (v29008) else (v29008))))) < (f0(v30959, div(f2(v29008), w(mod(f2(39), 7) + 8)), min(shl(12, (v29008) & 15), (v30959 ^ v30959)))) else ((((v30959) if (v29008) < (((-1) if (v29008) < (v30959) else (v29008))) else (v29008)) | ((0 & v30959) ^ w(v29008 - 33)))))
    v33403 = ((w(v48950 * f1(v29008, v48950, v48950)) & 45) | xs[idx((((v48950 & v30959)) if (13) < (v48950) else (v30959)))])
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
