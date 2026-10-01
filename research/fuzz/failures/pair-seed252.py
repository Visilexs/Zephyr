
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
    acc = w(w(acc * 31) + min(a0, (div(w(-45 * a2), w(mod(w(a2 + a0), 7) + 8)) & shr((a0 & a2), (45) & 15))))
    acc = w(w(acc * 31) + 19)
    return (((w(a0 + a1) | a0) ^ w(43 * w(48 * a1))) & shr(w(a0 - a1), (a2) & 15))
def main():
    global acc
    acc = w(w(acc * 31) + (w(max(50, (2 ^ -31)) - (w(-45 - 24) ^ w(-38 * -30))) | -17))
    acc = w(w(acc * 31) + -49)
    v14985 = shr(w(mod(w(-43 * 6), w(mod((26 | 5), 7) + 8)) - f0(max(48, 35), w(50 + 38), f0(-34, -13, 33))), (((-26) if ((27 | (10 & 49))) < ((max(47, 4) | div(29, w(mod(31, 7) + 8)))) else (acc))) & 15)
    v44061 = shr((acc & w(v14985 * v14985)), (w(-12 + mod(f0(v14985, -26, -11), w(mod((v14985 & v14985), 7) + 8)))) & 15)
    if (min(div(min(v14985, f0(38, 9, v44061)), w(mod(4, 7) + 8)), shr(div(w(v14985 * v14985), w(mod(v14985, 7) + 8)), ((xs[idx(28)] | 16)) & 15))) < (xs[idx((w(41 - v44061) & min(((-23) if (v44061) < (v44061) else (v44061)), w(17 * 46))))]):
        for i46993 in range(7):
            v44036 = w(v44061 + (shr(v44061, (mod(2, w(mod(13, 7) + 8))) & 15) & i46993))
            _i = idx(-33); xs[_i] = -41
            acc = w(w(acc * 31) + acc)
        for i97360 in range(3):
            _i = idx(min(38, v44061)); xs[_i] = -14
            _i = idx(v14985); xs[_i] = acc
            acc = w(w(acc * 31) + 26)
        acc = w(w(acc * 31) + ((v14985) if (div(acc, w(mod(v14985, 7) + 8))) < (shr(xs[idx(v14985)], (v44061) & 15)) else (w(max(6, v14985) + 46))))
    else:
        if (v14985) < (acc):
            _i = idx(max((div((v44061 | v44061), w(mod(acc, 7) + 8)) & ((div(v14985, w(mod(20, 7) + 8))) if (39) < (v44061) else ((21 | -12)))), 47)); xs[_i] = ((f0(w(v14985 - (v14985 ^ v14985)), v44061, f0(v14985, w(v14985 * -32), mod(48, w(mod(v14985, 7) + 8))))) if (mod(v44061, w(mod((shl(-38, (v44061) & 15) ^ v44061), 7) + 8))) < (xs[idx(v14985)]) else (7))
        else:
            _i = idx(w(mod(min((14 & 50), v44061), w(mod(33, 7) + 8)) - acc)); xs[_i] = (acc | w(min(w(v44061 + v44061), v44061) - xs[idx(min(-24, 5))]))
    for i8620 in range(3):
        acc = w(w(acc * 31) + min(acc, v44061))
    acc = w(w(acc * 31) + (-5 ^ w(w(-21 - w(-7 + 12)) + (v14985 ^ (v44061 | v44061)))))
    acc = w(w(acc * 31) + v44061)
    acc = w(w(acc * 31) + -40)
    for i93195 in range(7):
        acc = w(w(acc * 31) + i93195)
        for i74218 in range(6):
            acc = w(w(acc * 31) + v44061)
            acc = w(w(acc * 31) + i74218)
        _i = idx(v14985); xs[_i] = ((w(acc + v14985)) if (v14985) < ((((w(-32 - v14985) | w(v14985 + i93195))) if (xs[idx(max(-33, i93195))]) < ((min(v14985, -13) ^ acc)) else (5))) else (div(mod((11 & v44061), w(mod(max(i93195, -36), 7) + 8)), w(mod(((v14985 & v14985) ^ acc), 7) + 8))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
