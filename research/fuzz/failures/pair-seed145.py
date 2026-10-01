
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
    acc = w(w(acc * 31) + acc)
    return div(-43, w(mod(((((a2) if (mod(5, w(mod(a2, 7) + 8))) < (a1) else (div(a2, w(mod(a1, 7) + 8))))) if (a1) < ((w(a0 + 48) ^ w(a0 - a2))) else (shr(a1, (xs[idx(a1)]) & 15))), 7) + 8))
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + div(xs[idx(-45)], w(mod(-42, 7) + 8)))
    return (min(shr(w(-42 * a0), (mod(a1, w(mod(a2, 7) + 8))) & 15), (acc | acc)) & w(30 + -44))
def f2(a0, a1):
    global acc
    for i27029 in range(8):
        v9864 = (-18 & a1)
        v49672 = shl(max(w((v9864 ^ a1) + w(17 - a0)), v9864), (w(-44 * div(w(-32 * 50), w(mod(shr(a0, (i27029) & 15), 7) + 8)))) & 15)
    v97375 = w((a1 | (shr(48, (a1) & 15) | acc)) * (-30 | a0))
    return a1
def f3(a0, a1):
    global acc
    for i90570 in range(10):
        acc = w(w(acc * 31) + div(acc, w(mod(div(w((-10 | a0) - xs[idx(i90570)]), w(mod(mod(shl(a0, (a1) & 15), w(mod(xs[idx(a0)], 7) + 8)), 7) + 8)), 7) + 8)))
        v10514 = i90570
    return xs[idx(a1)]
def main():
    global acc
    acc = w(w(acc * 31) + xs[idx(w(w(w(-10 + 5) + w(-12 + 18)) * acc))])
    v21141 = div(-44, w(mod(acc, 7) + 8))
    _i = idx(v21141); xs[_i] = v21141
    _i = idx(v21141); xs[_i] = (v21141 & w((v21141 | div(v21141, w(mod(v21141, 7) + 8))) * v21141))
    for i24080 in range(1):
        for i67146 in range(4):
            acc = w(w(acc * 31) + (w(((i67146 & v21141) & i24080) - 34) & w(shr((20 & v21141), (-5) & 15) + shr(w(-45 - i24080), (mod(i67146, w(mod(6, 7) + 8))) & 15))))
            acc = w(w(acc * 31) + (37 & shr(shl((-49 & i24080), (-36) & 15), (mod(i24080, w(mod(5, 7) + 8))) & 15)))
    acc = w(w(acc * 31) + mod(f1(v21141, shr(v21141, (max(v21141, v21141)) & 15), v21141), w(mod((((v21141 | -22) & f3(v21141, v21141)) & shr((v21141 & v21141), ((v21141 & v21141)) & 15)), 7) + 8)))
    v49013 = w(v21141 * w(w(mod(0, w(mod(-31, 7) + 8)) + min(v21141, v21141)) + v21141))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
