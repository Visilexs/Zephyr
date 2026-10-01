
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
    if (-12) < (w(shl((40 ^ -6), (acc) & 15) + a0)):
        acc = w(w(acc * 31) + (a1 | 32))
        v9837 = a1
    else:
        acc = w(w(acc * 31) + -4)
    acc = w(w(acc * 31) + a0)
    return mod(w((w(a1 + -21) & w(a0 + a1)) * div(w(-15 - -12), w(mod(shl(a0, (10) & 15), 7) + 8))), w(mod(w(a1 + max(50, ((-50) if (-34) < (-25) else (30)))), 7) + 8))
def main():
    global acc
    if (-4) < (w(max(f0(shr(-39, (-43) & 15), (-33 & -18)), 1) - -20)):
        for i69871 in range(7):
            v93168 = w(xs[idx(shr((i69871 | 28), (xs[idx(4)]) & 15))] * shr(acc, (xs[idx(shr(i69871, (i69871) & 15))]) & 15))
            v58912 = acc
    else:
        v98773 = (-23 & w(((-33 ^ 26) | 11) + f0(max(10, -12), min(-49, -27))))
        v52151 = max(min(shl(xs[idx(v98773)], (v98773) & 15), acc), w(xs[idx(min(28, v98773))] * acc))
    acc = w(w(acc * 31) + xs[idx(-24)])
    _i = idx(7); xs[_i] = w(-44 - f0((38 | min(31, 42)), shl(w(1 + 50), (49) & 15)))
    for i51669 in range(12):
        if (min(xs[idx(w((-38 | i51669) + ((i51669) if (i51669) < (1) else (-16))))], i51669)) < (w(i51669 * w(20 + w(((0) if (i51669) < (41) else (i51669)) - 10)))):
            _i = idx(shr(w(acc * w(div(i51669, w(mod(i51669, 7) + 8)) * shl(i51669, (i51669) & 15))), ((-47 & max((i51669 ^ -24), xs[idx(42)]))) & 15)); xs[_i] = mod(mod(((shr(i51669, (32) & 15)) if (((i51669) if (i51669) < (21) else (-29))) < (i51669) else (div(i51669, w(mod(i51669, 7) + 8)))), w(mod(w(div(i51669, w(mod(39, 7) + 8)) - i51669), 7) + 8)), w(mod(xs[idx((13 | w(i51669 * -13)))], 7) + 8))
        else:
            _i = idx(i51669); xs[_i] = w(-50 + xs[idx(shl(w(i51669 - i51669), (div(33, w(mod(43, 7) + 8))) & 15))])
            acc = w(w(acc * 31) + ((mod(max(mod(i51669, w(mod(-31, 7) + 8)), shr(i51669, (-10) & 15)), w(mod(((w(-35 + i51669)) if (-20) < (w(i51669 * i51669)) else ((17 & -24))), 7) + 8))) if (w((shr(-49, (i51669) & 15) | acc) + -18)) < (31) else (-10)))
        v93014 = ((shr(-39, (i51669) & 15)) if (i51669) < (i51669) else (4))
    acc = w(w(acc * 31) + div((w((39 | -1) + 38) ^ max((12 ^ 9), (22 & 11))), w(mod(-46, 7) + 8)))
    for i72762 in range(7):
        acc = w(w(acc * 31) + min(w(w(mod(i72762, w(mod(i72762, 7) + 8)) * f0(i72762, i72762)) - i72762), w((mod(38, w(mod(i72762, 7) + 8)) | shr(i72762, (-39) & 15)) + w(w(-25 - i72762) - 39))))
        v69765 = -36
        for i6282 in range(9):
            v87339 = div((mod(div(v69765, w(mod(i72762, 7) + 8)), w(mod(((i72762) if (i72762) < (i72762) else (i6282)), 7) + 8)) | shr(w(12 * i72762), (-22) & 15)), w(mod(-48, 7) + 8))
    acc = w(w(acc * 31) + mod(f0(mod(max(-31, 34), w(mod(xs[idx(-47)], 7) + 8)), xs[idx(xs[idx(6)])]), w(mod(-19, 7) + 8)))
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
