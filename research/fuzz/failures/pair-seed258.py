
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

def f0(a0):
    global acc
    acc = w(w(acc * 31) + a0)
    acc = w(w(acc * 31) + a0)
    v70860 = shl((a0 & shr((48 & a0), (36) & 15)), (w(mod(min(24, a0), w(mod(min(a0, 50), 7) + 8)) + (div(a0, w(mod(50, 7) + 8)) | -49))) & 15)
    return (w(a0 * ((div(a0, w(mod(37, 7) + 8))) if (mod(-16, w(mod(a0, 7) + 8))) < ((a0 | a0)) else (div(13, w(mod(a0, 7) + 8))))) & a0)
def main():
    global acc
    v64951 = w(shr(div(9, w(mod(max(-24, -14), 7) + 8)), (35) & 15) + w(shr(w(-46 * 16), (30) & 15) * w(xs[idx(-22)] * (46 ^ 48))))
    _i = idx(max((w(w(v64951 + v64951) * f0(v64951)) ^ min(v64951, (v64951 | -34))), min(-7, max(shr(v64951, (v64951) & 15), v64951)))); xs[_i] = shr(max(w(shr(33, (v64951) & 15) * v64951), 39), (acc) & 15)
    _i = idx(w((v64951 ^ min(acc, 16)) * mod(((25) if (v64951) < (min(v64951, v64951)) else (v64951)), w(mod(shr(shr(v64951, (v64951) & 15), (div(49, w(mod(v64951, 7) + 8))) & 15), 7) + 8)))); xs[_i] = -43
    if (max(((acc) if (f0(((-15) if (v64951) < (48) else (v64951)))) < (w(acc * w(v64951 * -33))) else (36)), -38)) < ((v64951 & acc)):
        _i = idx(acc); xs[_i] = v64951
    else:
        if (w((div(v64951, w(mod(w(-28 - v64951), 7) + 8)) ^ xs[idx(mod(v64951, w(mod(v64951, 7) + 8)))]) * v64951)) < (v64951):
            acc = w(w(acc * 31) + w(w(shl(acc, (f0(36)) & 15) + ((w(v64951 - v64951)) if (v64951) < (3) else (-17))) + w(w(42 + -14) - w(w(34 * v64951) + (v64951 | -8)))))
        else:
            v50098 = v64951
            acc = w(w(acc * 31) + w(v50098 * shr(shl(shr(-35, (v64951) & 15), (w(v64951 * v64951)) & 15), ((-36 | mod(v50098, w(mod(v50098, 7) + 8)))) & 15)))
        _i = idx(18); xs[_i] = acc
    if (v64951) < (f0((v64951 | 13))):
        for i30383 in range(5):
            _i = idx((min(v64951, max(v64951, f0(-19))) ^ i30383)); xs[_i] = v64951
    else:
        for i88282 in range(4):
            _i = idx(mod(mod(w(min(-38, 15) - (v64951 | i88282)), w(mod(xs[idx(shr(-32, (i88282) & 15))], 7) + 8)), w(mod(shr(v64951, (acc) & 15), 7) + 8))); xs[_i] = max(acc, -19)
            v68846 = 42
        _i = idx(-9); xs[_i] = 32
    if (f0(-18)) < (((mod(-32, w(mod(v64951, 7) + 8))) if (v64951) < (div((w(v64951 + v64951) | div(v64951, w(mod(v64951, 7) + 8))), w(mod(-15, 7) + 8))) else (acc))):
        _i = idx(max(min(27, min(w(v64951 * 2), 18)), acc)); xs[_i] = v64951
    else:
        for i79470 in range(9):
            v84897 = (acc ^ ((w(i79470 - i79470) ^ i79470) | -40))
            _i = idx(v64951); xs[_i] = -50
        _i = idx(w(-30 - v64951)); xs[_i] = div(shl(min(20, mod(-11, w(mod(20, 7) + 8))), (acc) & 15), w(mod(f0(w(w(v64951 * v64951) + div(24, w(mod(v64951, 7) + 8)))), 7) + 8))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
