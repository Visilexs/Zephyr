
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
    acc = w(w(acc * 31) + shr(a1, (a0) & 15))
    return (shl(a0, (min((a2 | a2), div(36, w(mod(a0, 7) + 8)))) & 15) | 31)
def main():
    global acc
    v69942 = div(xs[idx(shl(w(4 - 47), (acc) & 15))], w(mod(-9, 7) + 8))
    acc = w(w(acc * 31) + f0((shl(((v69942) if (v69942) < (-19) else (v69942)), (w(v69942 + v69942)) & 15) | ((w(v69942 * v69942)) if (max(v69942, v69942)) < ((-13 & 27)) else (min(11, 41)))), f0(min(max(v69942, 49), -13), ((28) if ((-39 | v69942)) < (v69942) else (w(v69942 + v69942))), -16), min(max(v69942, shl(v69942, (v69942) & 15)), v69942)))
    acc = w(w(acc * 31) + f0((v69942 ^ v69942), max(mod(v69942, w(mod(min(v69942, 50), 7) + 8)), v69942), ((acc ^ v69942) ^ v69942)))
    acc = w(w(acc * 31) + div(div(v69942, w(mod(((v69942) if (mod(v69942, w(mod(49, 7) + 8))) < (((-2) if (v69942) < (v69942) else (26))) else (shl(v69942, (v69942) & 15))), 7) + 8)), w(mod(33, 7) + 8)))
    acc = w(w(acc * 31) + v69942)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
