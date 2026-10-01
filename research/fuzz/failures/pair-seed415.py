
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
    v73381 = (a0 | 49)
    if (v73381) < (v73381):
        v42445 = xs[idx(max(((a0) if (w(a0 * -22)) < (min(v73381, a0)) else (w(-32 * a0))), acc))]
        for i99513 in range(12):
            _i = idx(-43); xs[_i] = max((i99513 & 35), v73381)
            acc = w(w(acc * 31) + (((mod((v73381 | i99513), w(mod(v42445, 7) + 8)) | v73381)) if (w(min(max(21, a0), -11) * min(i99513, w(v73381 - v42445)))) < (i99513) else (-25)))
            acc = w(w(acc * 31) + mod(i99513, w(mod(shl(mod(w(-6 + v42445), w(mod(-18, 7) + 8)), ((acc | (v42445 | v73381))) & 15), 7) + 8)))
    else:
        acc = w(w(acc * 31) + w((-15 ^ v73381) * acc))
    return acc
def f1(a0, a1):
    global acc
    if (w(shr(acc, (max(shr(a1, (6) & 15), a0)) & 15) * min(div(18, w(mod((-5 ^ a1), 7) + 8)), 36))) < (mod(mod(((1 | -37) ^ -18), w(mod(a0, 7) + 8)), w(mod(mod(a0, w(mod((((a0 | a0)) if (shl(8, (-25) & 15)) < (acc) else (10)), 7) + 8)), 7) + 8))):
        v71730 = w(w(w(a1 * mod(a0, w(mod(a1, 7) + 8))) * w(a1 * a0)) * xs[idx(4)])
        v92159 = (((-34 ^ min((a1 & v71730), -47))) if (w(acc + -41)) < (-15) else (v71730))
    else:
        v58896 = mod(max(((f0(a0)) if (div(31, w(mod(a0, 7) + 8))) < (w(a0 - a1)) else (shr(a1, (-27) & 15))), -45), w(mod(min(w(w(a0 - a0) + acc), (w(-28 - a0) & 18)), 7) + 8))
        if (w(xs[idx(6)] + max(24, f0(acc)))) < ((shl(min(-9, max(a1, 32)), (max(a1, shr(v58896, (v58896) & 15))) & 15) ^ (f0(a1) ^ w(mod(a1, w(mod(a0, 7) + 8)) + w(a1 + a1))))):
            v91136 = mod(w(a1 - w(min(20, 0) * a1)), w(mod((17 & w(a0 + w(a0 - a0))), 7) + 8))
            v35504 = a0
            acc = w(w(acc * 31) + acc)
        else:
            _i = idx(w(acc * w(-31 - w(shl(a1, (a0) & 15) - shl(v58896, (v58896) & 15))))); xs[_i] = a0
            v86540 = min((f0(shr(a0, (v58896) & 15)) ^ w(w(a0 - a0) * shl(5, (a0) & 15))), (-2 & a0))
    return min(shl(div(shl(a1, (a1) & 15), w(mod(a1, 7) + 8)), (((a0 | 31) & max(a1, a1))) & 15), shr(shl(f0(a1), (a1) & 15), (shl(shr(a0, (a0) & 15), (a1) & 15)) & 15))
def f2(a0, a1, a2):
    global acc
    _i = idx(((a0) if ((f1(div(a1, w(mod(a0, 7) + 8)), ((a1) if (a0) < (-34) else (a1))) & a2)) < (w(a1 * ((a0) if (w(a1 + a1)) < ((a2 ^ a2)) else (27)))) else (45))); xs[_i] = a0
    return a2
def main():
    global acc
    acc = w(w(acc * 31) + shl((acc | w(f0(47) * max(36, 28))), (max(mod((23 & 35), w(mod(39, 7) + 8)), 6)) & 15))
    for i13838 in range(12):
        v50853 = shl(-36, (((w(mod(-21, w(mod(i13838, 7) + 8)) - f0(i13838))) if ((i13838 | min(38, i13838))) < (w(i13838 * (i13838 | 45))) else ((w(i13838 * i13838) & w(i13838 * i13838))))) & 15)
        v17777 = xs[idx(((w(42 * div(2, w(mod(20, 7) + 8)))) if (min(-37, w(v50853 * i13838))) < (-24) else (shl((5 & -25), (w(-23 - i13838)) & 15))))]
        acc = w(w(acc * 31) + f2(33, w(((20 | 15) ^ div(i13838, w(mod(v17777, 7) + 8))) * ((13) if (shr(19, (7) & 15)) < (w(-3 + -34)) else (((v17777) if (-3) < (45) else (i13838))))), shl(-1, ((v17777 | acc)) & 15)))
    if (w(-48 - 34)) < (max(min(acc, w(12 * f2(0, -33, -23))), -41)):
        v3052 = shr(33, ((min(mod(21, w(mod(-37, 7) + 8)), -45) ^ -10)) & 15)
    else:
        v14600 = 47
    v27208 = f0(-40)
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
