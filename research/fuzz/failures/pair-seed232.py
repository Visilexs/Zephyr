
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
    _i = idx(-15); xs[_i] = ((max(w(-16 * a0), xs[idx(26)]) & a0) ^ w((w(a0 + a0) ^ w(30 + a0)) + a0))
    return mod(a0, w(mod(div(xs[idx(6)], w(mod(w(a0 * a0), 7) + 8)), 7) + 8))
def f1(a0):
    global acc
    _i = idx(min(div(a0, w(mod(w(max(a0, -1) * w(a0 - a0)), 7) + 8)), a0)); xs[_i] = div(div((shr(-10, (a0) & 15) & a0), w(mod(shl(w(a0 - a0), (xs[idx(19)]) & 15), 7) + 8)), w(mod((xs[idx(shr(a0, (a0) & 15))] | ((((-33) if (a0) < (12) else (28))) if (shl(a0, (a0) & 15)) < (((-12) if (a0) < (a0) else (a0))) else (4))), 7) + 8))
    acc = w(w(acc * 31) + min(w(w(acc + -12) - (a0 & div(-48, w(mod(a0, 7) + 8)))), (((a0) if (min(50, a0)) < (div(a0, w(mod(-14, 7) + 8))) else (((a0) if (a0) < (a0) else (a0)))) & (a0 & ((a0) if (a0) < (a0) else (a0))))))
    return max(a0, xs[idx(a0)])
def f2(a0, a1):
    global acc
    v19807 = (xs[idx(14)] | f1(min((-6 ^ a1), a1)))
    return (acc & a1)
def main():
    global acc
    for i6810 in range(3):
        v37818 = (i6810 | w((shl(25, (i6810) & 15) & w(37 * 0)) + -45))
    v55849 = 15
    v92188 = w(shr(xs[idx(37)], (w(-37 - w(v55849 * -19))) & 15) * 22)
    if (w(w(shr(xs[idx(v55849)], (w(-2 - v92188)) & 15) - max(w(v55849 + -21), w(v92188 - v92188))) + w(mod(v55849, w(mod(((-11) if (v55849) < (v55849) else (v92188)), 7) + 8)) * (-20 ^ v55849)))) < (min(f0(shl(xs[idx(v92188)], ((v92188 ^ v55849)) & 15)), w(v55849 - w(min(-30, v55849) - v55849)))):
        acc = w(w(acc * 31) + v92188)
        v74214 = 15
        acc = w(w(acc * 31) + w(w(w(v92188 * -8) + f1((v92188 ^ -36))) + ((v92188) if (f2((v74214 | 0), max(v92188, -2))) < (f1(v55849)) else (v74214))))
    else:
        acc = w(w(acc * 31) + w(f0(v92188) - (v92188 & xs[idx(mod(42, w(mod(-34, 7) + 8)))])))
    acc = w(w(acc * 31) + v92188)
    acc = w(w(acc * 31) + w(f2(3, shl(xs[idx(v55849)], (mod(v55849, w(mod(v92188, 7) + 8))) & 15)) - -27))
    acc = w(w(acc * 31) + min(div(v55849, w(mod(div(acc, w(mod(shr(v92188, (v55849) & 15), 7) + 8)), 7) + 8)), shl(div(shr(v55849, (-37) & 15), w(mod(((48) if (v55849) < (v92188) else (v55849)), 7) + 8)), (-8) & 15)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
