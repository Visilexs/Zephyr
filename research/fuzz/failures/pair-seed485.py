
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
    acc = w(w(acc * 31) + w(acc + min(shr(a0, (shl(2, (17) & 15)) & 15), w(xs[idx(a0)] * w(a0 - -23)))))
    return ((acc) if (((w(a0 * a0) | w(31 * a0)) & shl(-13, (shl(a0, (a0) & 15)) & 15))) < (div(32, w(mod(max((a0 | -27), min(a0, -26)), 7) + 8))) else (mod(a0, w(mod(xs[idx(shr(a0, (-50) & 15))], 7) + 8))))
def f1(a0, a1):
    global acc
    v64054 = ((a1 ^ a1) & 50)
    v41713 = max((-31 ^ f0(a0)), f0(f0(w(a0 * v64054))))
    _i = idx(a1); xs[_i] = shr((mod(w(7 - v41713), w(mod(-8, 7) + 8)) & (((-35 | a1)) if (xs[idx(a1)]) < (mod(-9, w(mod(a1, 7) + 8))) else (shl(v64054, (-24) & 15)))), (shr(v64054, (a1) & 15)) & 15)
    return (a0 ^ -33)
def main():
    global acc
    for i41223 in range(3):
        for i47761 in range(6):
            acc = w(w(acc * 31) + f0(i47761))
            v70471 = 2
            v42765 = acc
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
