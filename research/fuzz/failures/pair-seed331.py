
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
    _i = idx(acc); xs[_i] = min(xs[idx(xs[idx(xs[idx(a0)])])], a0)
    return w(-46 - acc)
def f1(a0, a1, a2):
    global acc
    acc = w(w(acc * 31) + (acc & min(-46, 40)))
    _i = idx(((w(a0 - shr(a0, (a1) & 15)) ^ a2) & a2)); xs[_i] = (w(a0 + ((-46 & a1) & w(a1 - a2))) | f0(xs[idx(xs[idx(a1)])]))
    v33574 = w(max(w(acc + 6), f0(shr(a2, (7) & 15))) - 22)
    return ((acc) if (w((min(a0, 48) ^ w(a2 * 35)) * div(max(-10, -23), w(mod(w(a2 - 22), 7) + 8)))) < ((a0 | xs[idx(mod(47, w(mod(a2, 7) + 8)))])) else (w((w(a1 + -36) ^ f0(-13)) + (mod(a1, w(mod(a2, 7) + 8)) ^ f0(49)))))
def f2(a0, a1):
    global acc
    for i94446 in range(1):
        for i66932 in range(8):
            _i = idx(mod(-19, w(mod(w((i94446 & i66932) * 17), 7) + 8))); xs[_i] = a1
            _i = idx(acc); xs[_i] = (((w(i66932 * a1) | min(-1, -5)) | -25) & xs[idx(30)])
        acc = w(w(acc * 31) + acc)
    acc = w(w(acc * 31) + min(((acc & (a1 | a1)) & 31), -39))
    return (a1 ^ mod(w(f0(-27) * 49), w(mod(((a0 ^ a0) ^ a0), 7) + 8)))
def main():
    global acc
    for i74569 in range(1):
        acc = w(w(acc * 31) + (f2(mod(f1(-6, -39, i74569), w(mod(-20, 7) + 8)), shr(29, (acc) & 15)) ^ div(xs[idx(i74569)], w(mod(w(div(i74569, w(mod(i74569, 7) + 8)) + w(i74569 - i74569)), 7) + 8))))
        v75385 = f2(((i74569 & -1) & (w(36 + i74569) | w(0 + i74569))), w(i74569 * shr((i74569 ^ i74569), (mod(-5, w(mod(-21, 7) + 8))) & 15)))
    v32866 = -23
    for i85765 in range(11):
        _i = idx(w(max(((mod(i85765, w(mod(v32866, 7) + 8))) if (i85765) < (36) else (v32866)), max((-8 | -39), -36)) - i85765)); xs[_i] = (((w(f1(v32866, i85765, 47) * div(i85765, w(mod(-19, 7) + 8))) | -40)) if (xs[idx(i85765)]) < (i85765) else (v32866))
        acc = w(w(acc * 31) + shl(i85765, (xs[idx(w(w(-50 + -3) - shl(-45, (-48) & 15)))]) & 15))
        acc = w(w(acc * 31) + (shr((shr(v32866, (v32866) & 15) & v32866), (mod((v32866 & i85765), w(mod(xs[idx(i85765)], 7) + 8))) & 15) | v32866))
    v8158 = w((min(f2(-35, v32866), acc) ^ (xs[idx(v32866)] ^ min(v32866, v32866))) - -1)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
