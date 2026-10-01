
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
    acc = w(w(acc * 31) + w((a0 ^ w(((46) if (a0) < (a0) else (32)) + w(a0 + 12))) + w(a0 - min(acc, div(-47, w(mod(a0, 7) + 8))))))
    _i = idx(((acc & a0) & w(acc + 21))); xs[_i] = mod(w(a0 + (w(-5 + a0) | a0)), w(mod(a0, 7) + 8))
    return div(div(16, w(mod(shl(a0, (a0) & 15), 7) + 8)), w(mod(w(a0 - w((4 | a0) + shl(a0, (a0) & 15))), 7) + 8))
def f1(a0):
    global acc
    v75597 = a0
    for i17130 in range(10):
        v44466 = min(xs[idx(f0((v75597 | i17130)))], max((a0 & max(i17130, i17130)), (min(a0, -4) | max(i17130, v75597))))
    _i = idx(((w(w(f0(-49) * w(50 + v75597)) * (w(a0 + a0) & max(a0, a0)))) if (v75597) < (mod(47, w(mod(acc, 7) + 8))) else (40))); xs[_i] = ((-25) if (div(a0, w(mod(min(shr(-47, (v75597) & 15), v75597), 7) + 8))) < (mod((f0(v75597) & ((a0) if (v75597) < (a0) else (-33))), w(mod((min(a0, 26) ^ max(a0, 41)), 7) + 8))) else (-37))
    return a0
def main():
    global acc
    if (xs[idx(-14)]) < (-42):
        v80403 = max(shl(acc, (f1((-30 & -11))) & 15), -44)
        _i = idx((39 | v80403)); xs[_i] = w(w(6 * 12) - mod(9, w(mod(v80403, 7) + 8)))
        v84809 = w((49 ^ w(acc + div(v80403, w(mod(50, 7) + 8)))) - acc)
    else:
        for i12970 in range(6):
            _i = idx(w(i12970 * (18 | 6))); xs[_i] = min(acc, ((-48) if (shr(max(-23, i12970), (w(i12970 + 33)) & 15)) < (i12970) else (i12970)))
            v98661 = min(i12970, ((shl(i12970, (div(10, w(mod(i12970, 7) + 8))) & 15)) if (max(shr(-19, (i12970) & 15), mod(i12970, w(mod(-45, 7) + 8)))) < ((w(i12970 * -15) | max(i12970, -41))) else (div((i12970 & i12970), w(mod(shr(-48, (-37) & 15), 7) + 8)))))
            _i = idx(xs[idx(w(v98661 + v98661))]); xs[_i] = v98661
        acc = w(w(acc * 31) + w(-29 * div(38, w(mod(-23, 7) + 8))))
    acc = w(w(acc * 31) + 13)
    _i = idx(w(shl(w(-1 - f0(50)), (-21) & 15) + ((min(((-38) if (15) < (-49) else (16)), w(36 * -41))) if (w(mod(-6, w(mod(-34, 7) + 8)) - (-31 | 49))) < (shl((2 & -35), (max(16, -35)) & 15)) else ((max(1, 19) | 36))))); xs[_i] = 38
    for i29505 in range(2):
        if (w(((w((i29505 ^ 11) - acc)) if (w(42 - xs[idx(i29505)])) < (f1(xs[idx(i29505)])) else (-7)) - ((((min(i29505, 28)) if ((9 ^ i29505)) < (shl(i29505, (i29505) & 15)) else (48))) if ((i29505 ^ 41)) < ((((i29505) if (-43) < (i29505) else (i29505)) ^ i29505)) else (acc)))) < (div(((acc) if (i29505) < (xs[idx(shl(27, (i29505) & 15))]) else (mod(shl(-11, (i29505) & 15), w(mod((-38 | i29505), 7) + 8)))), w(mod(f0((i29505 | w(i29505 * i29505))), 7) + 8))):
            acc = w(w(acc * 31) + div(f0((acc ^ -46)), w(mod(xs[idx(xs[idx(i29505)])], 7) + 8)))
            _i = idx(w(i29505 + (((i29505 ^ i29505)) if (i29505) < (w(min(i29505, i29505) - f0(-6))) else (-45)))); xs[_i] = -11
        else:
            _i = idx(f1(w((xs[idx(i29505)] ^ max(i29505, -24)) - shl(w(42 + i29505), ((i29505 | 35)) & 15)))); xs[_i] = ((acc) if (div(i29505, w(mod(mod((i29505 & i29505), w(mod(div(-22, w(mod(i29505, 7) + 8)), 7) + 8)), 7) + 8))) < (min((w(4 - i29505) ^ acc), acc)) else (f1(-8)))
            v95595 = xs[idx(i29505)]
        acc = w(w(acc * 31) + w(w(-47 - shl(w(i29505 + i29505), ((i29505 | 38)) & 15)) + shr(min((i29505 ^ -32), shl(i29505, (i29505) & 15)), ((shl(i29505, (i29505) & 15) & w(i29505 + i29505))) & 15)))
        acc = w(w(acc * 31) + i29505)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
