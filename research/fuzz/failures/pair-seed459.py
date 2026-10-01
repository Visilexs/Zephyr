
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
    v57931 = min(max(((shl(39, (a1) & 15)) if (a0) < (w(a0 + a1)) else ((a1 & a0))), (div(a0, w(mod(a0, 7) + 8)) & (-34 ^ -21))), (a0 | a1))
    v25357 = max(a0, v57931)
    acc = w(w(acc * 31) + shl(a0, (w(shl(v57931, (36) & 15) * acc)) & 15))
    return max(a1, a0)
def f1(a0, a1):
    global acc
    v30056 = (min((24 | (-5 & -14)), a1) & (-19 ^ (f0(a0, -39) | a0)))
    acc = w(w(acc * 31) + (f0(shr(shr(-1, (a0) & 15), (((11) if (a1) < (48) else (-14))) & 15), w(acc * w(a0 - v30056))) | (a1 & min(shl(-31, (a1) & 15), ((13) if (8) < (13) else (a0))))))
    return ((div(xs[idx(min(-23, 0))], w(mod(max(div(a0, w(mod(a1, 7) + 8)), max(47, -29)), 7) + 8))) if (div(a1, w(mod(w(-49 + a1), 7) + 8))) < (a1) else (a1))
def main():
    global acc
    acc = w(w(acc * 31) + f1(div(-19, w(mod(50, 7) + 8)), w(w(w(6 - 35) * 24) + xs[idx(mod(6, w(mod(-32, 7) + 8)))])))
    for i78345 in range(5):
        acc = w(w(acc * 31) + -5)
    v6927 = ((max(((shr(-29, (1) & 15)) if (-41) < (-31) else (acc)), (w(-42 * -19) & -15))) if (max(div(mod(-6, w(mod(2, 7) + 8)), w(mod(w(7 + -20), 7) + 8)), max(mod(-46, w(mod(29, 7) + 8)), w(47 - 44)))) < (div(acc, w(mod(-35, 7) + 8))) else (shr(shl(38, (((11) if (-36) < (31) else (-47))) & 15), (min(17, -27)) & 15)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
