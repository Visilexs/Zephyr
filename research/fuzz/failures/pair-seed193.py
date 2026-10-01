
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
    for i68948 in range(4):
        acc = w(w(acc * 31) + shl(acc, (div(max(shr(-23, (a0) & 15), 50), w(mod(max(min(a0, i68948), mod(a0, w(mod(a0, 7) + 8))), 7) + 8))) & 15))
    v10950 = max(-3, acc)
    return acc
def f1(a0):
    global acc
    acc = w(w(acc * 31) + w(w(f0(xs[idx(21)]) * shr(w(0 - -29), (xs[idx(a0)]) & 15)) + w(a0 * (-5 ^ (a0 ^ a0)))))
    return w(div(a0, w(mod(shl(acc, (div(a0, w(mod(a0, 7) + 8))) & 15), 7) + 8)) - div(min(w(a0 - a0), a0), w(mod(xs[idx(shl(28, (-9) & 15))], 7) + 8)))
def f2(a0):
    global acc
    v37821 = a0
    v7858 = w(w(a0 + shl(max(17, -10), (div(v37821, w(mod(-1, 7) + 8))) & 15)) + w((a0 | shr(-38, (v37821) & 15)) * f1(shl(-19, (a0) & 15))))
    return div(shr(shl((-46 ^ a0), (((a0) if (-37) < (a0) else (-9))) & 15), (a0) & 15), w(mod((shl(w(-15 - a0), (-46) & 15) ^ a0), 7) + 8))
def f3(a0):
    global acc
    _i = idx(w(w(f0(((a0) if (a0) < (a0) else (a0))) - 36) + w(shr(a0, (f0(13)) & 15) * ((f0(-35)) if (min(-46, -8)) < (a0) else (shl(a0, (a0) & 15)))))); xs[_i] = w(f2(min(-4, (-33 | a0))) + f0(a0))
    acc = w(w(acc * 31) + a0)
    return -30
def main():
    global acc
    for i86993 in range(12):
        _i = idx(i86993); xs[_i] = (i86993 | mod(max(((41) if (21) < (i86993) else (i86993)), i86993), w(mod(44, 7) + 8)))
    acc = w(w(acc * 31) + min(41, -24))
    _i = idx(acc); xs[_i] = w(w(div(f1(-22), w(mod(div(-5, w(mod(11, 7) + 8)), 7) + 8)) * shr(w(1 * 27), (f3(13)) & 15)) + 2)
    v56171 = max(acc, w(-12 - shl(div(-33, w(mod(-49, 7) + 8)), (-11) & 15)))
    v72793 = v56171
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
