
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
    v9389 = w(mod(w(min(-46, -34) - (-27 & 47)), w(mod(mod(((a0) if (-48) < (-18) else (a0)), w(mod(mod(a0, w(mod(a0, 7) + 8)), 7) + 8)), 7) + 8)) * (a0 | w(max(44, a0) + a0)))
    acc = w(w(acc * 31) + a0)
    _i = idx(((a0) if (v9389) < (w(v9389 * min(a0, shl(41, (a0) & 15)))) else ((max(div(a0, w(mod(a0, 7) + 8)), 43) | v9389)))); xs[_i] = w((v9389 | (((a0 ^ 46)) if (v9389) < (w(a0 * a0)) else (20))) - v9389)
    return w(-42 * -40)
def main():
    global acc
    _i = idx(((max((-13 | -12), 37) & w(-3 - -5)) | w(41 * div(-4, w(mod(-17, 7) + 8))))); xs[_i] = 22
    _i = idx(-24); xs[_i] = shr((((w(-35 - 26)) if (-30) < (-46) else (acc)) ^ -26), ((((-9 & div(-40, w(mod(15, 7) + 8)))) if (w(30 + div(45, w(mod(-40, 7) + 8)))) < (acc) else ((xs[idx(42)] | (-47 & -11))))) & 15)
    acc = w(w(acc * 31) + f0(div(xs[idx(div(10, w(mod(-5, 7) + 8)))], w(mod(f0(7), 7) + 8))))
    v9988 = -24
    acc = w(w(acc * 31) + max(v9988, xs[idx(v9988)]))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
