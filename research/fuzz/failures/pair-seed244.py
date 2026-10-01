
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
    acc = w(w(acc * 31) + (div(div((a1 | a1), w(mod(a0, 7) + 8)), w(mod(a0, 7) + 8)) | w(-7 + a0)))
    if (47) < (w(37 + a1)):
        v11777 = a0
    else:
        acc = w(w(acc * 31) + xs[idx(w(((max(a0, a1)) if (-23) < (shl(a1, (-13) & 15)) else (xs[idx(50)])) - (a0 ^ acc)))])
    v68450 = a0
    return w(max(a0, a0) + shl(xs[idx((a0 ^ 4))], (div(shl(a0, (40) & 15), w(mod((a1 ^ a1), 7) + 8))) & 15))
def f1(a0):
    global acc
    v60763 = w(w(1 * (-29 ^ mod(48, w(mod(18, 7) + 8)))) - -7)
    acc = w(w(acc * 31) + w(w((-27 | acc) - w((a0 | 50) * w(v60763 * v60763))) * (div(w(a0 + 37), w(mod((16 ^ a0), 7) + 8)) | ((23) if (v60763) < (div(v60763, w(mod(5, 7) + 8))) else (min(a0, v60763))))))
    for i82699 in range(12):
        for i73313 in range(3):
            _i = idx(v60763); xs[_i] = (acc | (xs[idx(((-44) if (v60763) < (3) else (i73313)))] ^ f0(div(11, w(mod(i82699, 7) + 8)), i73313)))
            v31881 = xs[idx(mod(w(f0(a0, i82699) + i82699), w(mod(27, 7) + 8)))]
            v90088 = w(div(((-27) if (21) < (w(a0 - v60763)) else (w(i73313 * 17))), w(mod(max(mod(v60763, w(mod(i82699, 7) + 8)), f0(i73313, i73313)), 7) + 8)) * shl(shl(v60763, (i73313) & 15), (min(mod(v31881, w(mod(i73313, 7) + 8)), i73313)) & 15))
        acc = w(w(acc * 31) + w(mod(w(a0 + mod(30, w(mod(i82699, 7) + 8))), w(mod(xs[idx(mod(v60763, w(mod(21, 7) + 8)))], 7) + 8)) * i82699))
    return a0
def f2(a0):
    global acc
    _i = idx(-35); xs[_i] = min(acc, a0)
    return acc
def f3(a0):
    global acc
    _i = idx(a0); xs[_i] = a0
    _i = idx(acc); xs[_i] = ((w(mod(a0, w(mod(a0, 7) + 8)) * -33) & min((a0 | a0), a0)) | f2(((2 | a0) & xs[idx(-16)])))
    v48467 = mod(w(f1(div(a0, w(mod(10, 7) + 8))) * shr((-43 | a0), (((-47) if (a0) < (a0) else (40))) & 15)), w(mod(a0, 7) + 8))
    return (w(div(max(-33, a0), w(mod(w(a0 - -34), 7) + 8)) + min(-4, min(a0, a0))) & shr(a0, (48) & 15))
def main():
    global acc
    acc = w(w(acc * 31) + ((w(w(-38 * (-32 | 5)) + min(div(-17, w(mod(1, 7) + 8)), -7))) if (w(((-41 | 30) | f3(-31)) - div(acc, w(mod(w(-17 + -34), 7) + 8)))) < (xs[idx(35)]) else ((div(max(-8, 24), w(mod((16 ^ 46), 7) + 8)) ^ (w(33 + -25) ^ ((-26) if (32) < (-43) else (-9)))))))
    v78706 = (-44 | xs[idx(w(w(-2 + 46) * min(26, 37)))])
    acc = w(w(acc * 31) + max(46, mod(v78706, w(mod(16, 7) + 8))))
    acc = w(w(acc * 31) + (shl((v78706 | f0(13, v78706)), (39) & 15) & div(min((-20 & v78706), xs[idx(-28)]), w(mod(v78706, 7) + 8))))
    acc = w(w(acc * 31) + f2(min(-23, (49 ^ (v78706 & v78706)))))
    v8640 = (mod(f2(v78706), w(mod((w(v78706 - -19) ^ acc), 7) + 8)) ^ v78706)
    _i = idx(v78706); xs[_i] = (17 ^ v8640)
    for i64044 in range(3):
        v20223 = div(xs[idx(w(-44 * shr(v78706, (v78706) & 15)))], w(mod((v8640 | (f2(5) | (-2 ^ v8640))), 7) + 8))
        _i = idx(v20223); xs[_i] = v78706
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
