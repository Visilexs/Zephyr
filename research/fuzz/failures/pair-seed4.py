
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
    if (w(a1 * w(a1 - (-47 & div(-26, w(mod(a1, 7) + 8)))))) < (max(35, shr(a0, (mod(a1, w(mod(shl(a1, (a0) & 15), 7) + 8))) & 15))):
        acc = w(w(acc * 31) + w(a1 - acc))
    else:
        v88313 = a0
        for i57822 in range(5):
            acc = w(w(acc * 31) + min(shl((shr(a1, (a1) & 15) & v88313), (mod(min(v88313, a1), w(mod(xs[idx(29)], 7) + 8))) & 15), i57822))
    return a0
def f1(a0, a1):
    global acc
    v5871 = max(max((shl(a0, (a0) & 15) & a0), acc), min((mod(2, w(mod(-25, 7) + 8)) & shr(a1, (a1) & 15)), xs[idx(acc)]))
    v27271 = xs[idx((min(f0(a0, v5871), (v5871 ^ v5871)) | xs[idx(div(a1, w(mod(-41, 7) + 8)))]))]
    acc = w(w(acc * 31) + f0(shl(21, (acc) & 15), ((mod(acc, w(mod(f0(v5871, v27271), 7) + 8))) if (a0) < (div((a0 | 16), w(mod(mod(-41, w(mod(v27271, 7) + 8)), 7) + 8))) else ((((a1 ^ a1)) if (-25) < (acc) else (min(a0, -50)))))))
    return (acc & acc)
def main():
    global acc
    v32170 = mod((w(min(19, 9) + mod(14, w(mod(50, 7) + 8))) ^ ((-32) if (div(48, w(mod(26, 7) + 8))) < (min(-33, 5)) else ((-14 ^ -3)))), w(mod(-6, 7) + 8))
    for i12250 in range(2):
        for i23550 in range(6):
            acc = w(w(acc * 31) + 27)
            v98899 = max((i12250 & w((i12250 & 45) * 34)), f0(shr(shr(18, (7) & 15), (f1(-10, i12250)) & 15), div(i23550, w(mod(max(i12250, -31), 7) + 8))))
            acc = w(w(acc * 31) + max(mod(div(acc, w(mod(w(i12250 * i12250), 7) + 8)), w(mod((div(i12250, w(mod(v32170, 7) + 8)) ^ -40), 7) + 8)), i23550))
        for i82772 in range(12):
            _i = idx((w(w((v32170 | i12250) + w(v32170 * -18)) * mod(min(v32170, v32170), w(mod(-12, 7) + 8))) | (i82772 | shr(i82772, (((-2) if (40) < (37) else (v32170))) & 15)))); xs[_i] = shl(-5, (xs[idx(w(shl(i82772, (i12250) & 15) - min(-40, -10)))]) & 15)
    acc = w(w(acc * 31) + shr(-7, (((w(v32170 + 29) & w(v32170 - v32170)) | max(mod(30, w(mod(-46, 7) + 8)), v32170))) & 15))
    if (mod(mod(xs[idx(shl(v32170, (-15) & 15))], w(mod(v32170, 7) + 8)), w(mod(mod((min(v32170, 39) | 35), w(mod(47, 7) + 8)), 7) + 8))) < (v32170):
        _i = idx(v32170); xs[_i] = -13
        _i = idx((w((w(-27 + -17) ^ v32170) * max((v32170 ^ v32170), w(-17 - 35))) | acc)); xs[_i] = v32170
        acc = w(w(acc * 31) + acc)
    else:
        acc = w(w(acc * 31) + w(w(v32170 - v32170) - max((shl(-27, (-23) & 15) & v32170), min(acc, mod(0, w(mod(v32170, 7) + 8))))))
        for i45958 in range(6):
            acc = w(w(acc * 31) + i45958)
    v43320 = v32170
    acc = w(w(acc * 31) + w(26 - w(w(shr(-33, (-33) & 15) + v43320) + max(v43320, v32170))))
    acc = w(w(acc * 31) + shl((-25 & ((v32170 | v43320) | w(-44 * 27))), (v32170) & 15))
    v36804 = v43320
    acc = w(w(acc * 31) + w(mod(w(v43320 - v32170), w(mod(w(-25 - shl(45, (-39) & 15)), 7) + 8)) - v43320))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
