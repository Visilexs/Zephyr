
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
    v91455 = div(w(min(div(a2, w(mod(19, 7) + 8)), -4) + div(acc, w(mod(a0, 7) + 8))), w(mod(shr(w(acc - ((a2) if (a0) < (a1) else (9))), (w(((-45) if (17) < (a0) else (a0)) + a2)) & 15), 7) + 8))
    for i3315 in range(6):
        acc = w(w(acc * 31) + w(10 + i3315))
        v73336 = mod(w(25 + (mod(42, w(mod(a2, 7) + 8)) ^ 46)), w(mod((a2 ^ a1), 7) + 8))
    return -23
def main():
    global acc
    acc = w(w(acc * 31) + min(-47, f0(w(-12 + 3), 7, mod(4, w(mod(shr(1, (-49) & 15), 7) + 8)))))
    v9434 = -30
    v97079 = v9434
    acc = w(w(acc * 31) + 19)
    for i18262 in range(7):
        acc = w(w(acc * 31) + (v9434 ^ (((v9434 | w(1 * -43))) if (-29) < (max(shl(v9434, (v97079) & 15), v97079)) else (shr(i18262, (v97079) & 15)))))
        if (shl(v97079, (((shr(min(v9434, i18262), (f0(v9434, 22, v9434)) & 15)) if (v97079) < (w(v97079 * acc)) else (i18262))) & 15)) < (max(max(w((49 | v97079) + w(v9434 - 16)), (v9434 | shr(-48, (i18262) & 15))), v9434)):
            acc = w(w(acc * 31) + (div(max(w(v97079 * i18262), f0(v97079, v97079, i18262)), w(mod(shl(w(v9434 + v97079), (1) & 15), 7) + 8)) | 25))
            _i = idx(shr(7, (((xs[idx(41)] & v97079) | min(mod(v97079, w(mod(i18262, 7) + 8)), shr(v9434, (v97079) & 15)))) & 15)); xs[_i] = f0(f0(acc, v9434, min(i18262, max(42, i18262))), 31, shr(v97079, ((((-44 ^ 30)) if (i18262) < (div(32, w(mod(29, 7) + 8))) else (-23))) & 15))
        else:
            acc = w(w(acc * 31) + f0(w((mod(v97079, w(mod(13, 7) + 8)) ^ max(-38, v9434)) - -48), 24, min((((37 & -16)) if (v9434) < ((v9434 | v97079)) else (49)), f0(v9434, w(v97079 - v9434), shr(-3, (v97079) & 15)))))
        acc = w(w(acc * 31) + (mod(f0(w(13 - v97079), min(v97079, 5), w(v9434 + i18262)), w(mod(w(min(-38, v9434) * (26 ^ i18262)), 7) + 8)) | -45))
    _i = idx(mod(w(v9434 * f0(xs[idx(v9434)], f0(v97079, -44, v97079), acc)), w(mod(v97079, 7) + 8))); xs[_i] = f0(v9434, (v97079 | (min(-17, v9434) ^ xs[idx(34)])), w(shl(mod(v9434, w(mod(-45, 7) + 8)), (((33) if (v9434) < (-23) else (v97079))) & 15) * v9434))
    acc = w(w(acc * 31) + w(w(v97079 * v97079) - mod(w(min(23, 33) - v9434), w(mod(div(shr(v97079, (-33) & 15), w(mod(xs[idx(v9434)], 7) + 8)), 7) + 8))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
