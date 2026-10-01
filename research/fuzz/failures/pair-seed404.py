
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
    acc = w(w(acc * 31) + (w(w(acc + a0) + 43) & a1))
    return div(shl(a1, (xs[idx(w(a0 + -13))]) & 15), w(mod(div(xs[idx(shl(a1, (a1) & 15))], w(mod(11, 7) + 8)), 7) + 8))
def main():
    global acc
    v67357 = w(div(xs[idx(-25)], w(mod(w(xs[idx(-38)] * -34), 7) + 8)) - 2)
    if (36) < (-38):
        v53491 = v67357
    else:
        acc = w(w(acc * 31) + v67357)
    acc = w(w(acc * 31) + f0(acc, div(((shl(v67357, (v67357) & 15)) if ((v67357 & -46)) < (39) else (w(v67357 + v67357))), w(mod(xs[idx(shr(v67357, (43) & 15))], 7) + 8))))
    _i = idx(f0(v67357, div(v67357, w(mod(acc, 7) + 8)))); xs[_i] = xs[idx(xs[idx(v67357)])]
    acc = w(w(acc * 31) + v67357)
    v72313 = min((((-38 & 44) ^ max(v67357, v67357)) & shl(div(v67357, w(mod(-49, 7) + 8)), (acc) & 15)), w(-5 * -1))
    acc = w(w(acc * 31) + f0(v67357, max(w(v72313 + shr(-39, (-19) & 15)), w(w(v72313 - -7) + w(v67357 + v67357)))))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
