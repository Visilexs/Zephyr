
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
    acc = w(w(acc * 31) + div(a1, w(mod(shl(w(a1 - w(a0 - -37)), ((a0 | (29 ^ a0))) & 15), 7) + 8)))
    return xs[idx(acc)]
def f1(a0, a1, a2):
    global acc
    if (48) < (w(((min(a0, w(12 - a1))) if (mod(max(6, a1), w(mod((39 ^ 40), 7) + 8))) < (((4 ^ 0) ^ a2)) else (f0(a2, ((a1) if (a1) < (a0) else (-6))))) * shr(max(w(a2 + a2), a0), (mod((a0 & a1), w(mod(min(47, a0), 7) + 8))) & 15))):
        for i6057 in range(3):
            v89320 = w(acc - xs[idx(mod(((a0) if (-37) < (i6057) else (i6057)), w(mod(a0, 7) + 8)))])
            v54541 = a0
        for i74755 in range(8):
            _i = idx(w(a1 - w(a1 * w(min(a0, a0) + min(38, i74755))))); xs[_i] = 44
            v82950 = mod(4, w(mod((38 ^ -22), 7) + 8))
            v63410 = xs[idx(-42)]
    else:
        if ((w(min((-6 | a1), (a1 & a0)) + a0) ^ shl(f0(max(-8, a2), f0(-24, 13)), (w(a2 + (42 & a2))) & 15))) < (min(shr(xs[idx(w(a1 * a2))], (a0) & 15), w(acc * a2))):
            acc = w(w(acc * 31) + w(xs[idx(43)] - w(f0(min(-33, a0), a0) - -17)))
        else:
            _i = idx(w(21 - 41)); xs[_i] = a0
            acc = w(w(acc * 31) + shl(mod(shr(f0(a1, -7), (18) & 15), w(mod((w(48 * a0) & shl(44, (-43) & 15)), 7) + 8)), (shl((a0 | a2), (a1) & 15)) & 15))
    v90539 = w(max(w(f0(8, -4) - div(a0, w(mod(a1, 7) + 8))), min(a0, max(a2, a0))) + max(w(acc - ((11) if (a1) < (a0) else (a2))), ((w(a1 * -32)) if (shl(a2, (a0) & 15)) < (mod(a1, w(mod(a2, 7) + 8))) else (a2))))
    return f0(acc, (-7 | (-38 | (10 ^ a0))))
def f2(a0):
    global acc
    v78588 = ((shr(max(a0, a0), (div(25, w(mod(-8, 7) + 8))) & 15) & a0) & a0)
    v95339 = a0
    acc = w(w(acc * 31) + w(mod(shr(shl(v78588, (v95339) & 15), (max(-41, -19)) & 15), w(mod(shl(mod(-16, w(mod(v78588, 7) + 8)), ((v78588 ^ a0)) & 15), 7) + 8)) + div(-30, w(mod((mod(-30, w(mod(-38, 7) + 8)) | shl(v95339, (24) & 15)), 7) + 8))))
    return acc
def main():
    global acc
    acc = w(w(acc * 31) + min(shr((((-40 & -21)) if (-37) < (f0(35, -33)) else (w(-36 * -10))), (max(-34, 39)) & 15), 0))
    _i = idx(xs[idx(shr(xs[idx((38 & -30))], (27) & 15))]); xs[_i] = (min(mod(27, w(mod(w(25 * 20), 7) + 8)), 23) ^ w(xs[idx((-24 ^ -22))] + f2(min(-1, -49))))
    if (f0(w(19 * w(min(1, -26) + max(33, -17))), w(18 - min(-19, min(-27, -4))))) < ((((mod(-43, w(mod(8, 7) + 8)) & (35 | 12)) ^ (max(12, 13) & (-28 | -8))) ^ acc)):
        v83266 = w(mod(min(48, 42), w(mod(acc, 7) + 8)) - 7)
    else:
        v62111 = max(w(f1(w(46 + 43), 32, w(-34 * 14)) + -37), 44)
        _i = idx(w(shl((mod(-18, w(mod(39, 7) + 8)) ^ shl(23, (v62111) & 15)), (41) & 15) + ((((xs[idx(12)]) if (shl(v62111, (v62111) & 15)) < (v62111) else ((-15 & 41)))) if (9) < (21) else (mod(v62111, w(mod(27, 7) + 8)))))); xs[_i] = -26
    v48643 = 32
    acc = w(w(acc * 31) + -28)
    v69087 = 49
    if (mod(div((acc ^ shr(v48643, (v69087) & 15)), w(mod(5, 7) + 8)), w(mod(21, 7) + 8))) < (v69087):
        acc = w(w(acc * 31) + (v69087 ^ (-28 & w(v69087 - v69087))))
        for i48478 in range(10):
            acc = w(w(acc * 31) + (w(acc * v69087) & f2(v48643)))
            v32776 = ((w(i48478 - w(max(v69087, v48643) * v48643))) if (w(-37 * 47)) < (acc) else (w(f0(f0(3, v48643), w(36 + -36)) * v69087)))
    else:
        if (mod(shr(min(mod(v48643, w(mod(-27, 7) + 8)), 29), (v48643) & 15), w(mod(shr(max(-18, v69087), (f0(w(v48643 - v69087), min(v69087, -2))) & 15), 7) + 8))) < ((shr(v69087, (w(acc * xs[idx(v69087)])) & 15) & v69087)):
            _i = idx((shr(xs[idx(shl(v69087, (42) & 15))], ((-23 ^ (-16 & -27))) & 15) & v48643)); xs[_i] = xs[idx((v69087 | v69087))]
            _i = idx(v69087); xs[_i] = max(((w(v69087 * (-28 | v48643))) if (v48643) < (v48643) else (w((v69087 & v69087) + w(v48643 * v69087)))), shl(((v69087) if (f1(v69087, 46, 7)) < (f0(v48643, v69087)) else (w(v69087 * v48643))), (f1(((-50) if (v69087) < (v69087) else (34)), acc, xs[idx(v69087)])) & 15))
        else:
            acc = w(w(acc * 31) + f2(v69087))
            _i = idx(min(v69087, (w(10 - v48643) ^ v48643))); xs[_i] = w(((min(v48643, -18) & div(18, w(mod(v48643, 7) + 8))) | w(f2(v48643) + (v69087 & v69087))) - v48643)
        v89687 = mod(w(v48643 + v48643), w(mod(max(min(shl(v69087, (33) & 15), v69087), (v69087 & w(v48643 * v69087))), 7) + 8))
    v79820 = w(max(shl(acc, (shl(v48643, (v48643) & 15)) & 15), w(min(v69087, v69087) - ((-40) if (v48643) < (-19) else (v48643)))) - (w(-34 - v48643) & max(div(v48643, w(mod(v69087, 7) + 8)), (v69087 | v69087))))
    if (xs[idx(w(div(w(v48643 * v69087), w(mod(mod(v79820, w(mod(-11, 7) + 8)), 7) + 8)) * (shl(v79820, (v79820) & 15) | shl(v69087, (v69087) & 15))))]) < (mod(v69087, w(mod(12, 7) + 8))):
        v70213 = v79820
        _i = idx((min(max(shl(v69087, (v70213) & 15), v69087), ((v69087) if (w(v79820 + v69087)) < (v79820) else (shl(v69087, (-5) & 15)))) | f2(max(v48643, v79820)))); xs[_i] = mod(w(w((v70213 ^ v69087) - acc) * 20), w(mod(shl(25, (acc) & 15), 7) + 8))
    else:
        for i16994 in range(7):
            v871 = w(mod(min(w(33 - i16994), acc), w(mod(acc, 7) + 8)) + ((w(shr(v79820, (v69087) & 15) + div(36, w(mod(29, 7) + 8)))) if (acc) < (((acc) if (shr(17, (i16994) & 15)) < (i16994) else (48))) else (w(w(33 + v48643) * w(v79820 + v48643)))))
            acc = w(w(acc * 31) + div(34, w(mod(-14, 7) + 8)))
            _i = idx((-32 & -49)); xs[_i] = w((acc | w(mod(6, w(mod(44, 7) + 8)) - v48643)) + f2(v69087))
        acc = w(w(acc * 31) + (f1(w(w(v79820 - 42) + w(v69087 - -1)), min(div(38, w(mod(v69087, 7) + 8)), (v79820 ^ -17)), ((acc) if (shr(v69087, (v69087) & 15)) < (shr(-41, (22) & 15)) else (w(31 * 40)))) | shl(min(v79820, f1(49, 3, 20)), (shr(w(v79820 - -35), (w(v79820 * v79820)) & 15)) & 15)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
