
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
    if (-48) < (-32):
        _i = idx(a0); xs[_i] = a0
        _i = idx(a0); xs[_i] = 15
        acc = w(w(acc * 31) + xs[idx(((-21) if (max(min(32, a0), w(a0 + 50))) < (w(a0 + w(a0 + 21))) else (-5)))])
    else:
        acc = w(w(acc * 31) + ((((w(-6 + w(a0 + a0))) if (7) < (div(w(a0 + a0), w(mod(mod(a0, w(mod(a0, 7) + 8)), 7) + 8))) else (shr(min(a0, 39), (-28) & 15)))) if (div((w(a0 + 44) & a0), w(mod(div(a0, w(mod(acc, 7) + 8)), 7) + 8))) < (a0) else ((w((a0 | a0) + (a0 & a0)) & ((min(a0, a0)) if (shl(a0, (a0) & 15)) < ((42 & a0)) else (a0))))))
        v91382 = shl(-24, (w(((((a0) if (a0) < (a0) else (-19))) if (shr(a0, (a0) & 15)) < ((a0 ^ a0)) else (w(a0 + -29))) * a0)) & 15)
    for i60230 in range(8):
        acc = w(w(acc * 31) + div(((w(min(7, i60230) + (a0 & i60230))) if ((7 & min(23, a0))) < (i60230) else ((shr(11, (-35) & 15) | shl(i60230, (i60230) & 15)))), w(mod(acc, 7) + 8)))
    for i88640 in range(7):
        if (shr(w(min(min(a0, a0), w(i88640 * a0)) + acc), (shr(acc, ((shl(21, (27) & 15) ^ min(26, a0))) & 15)) & 15)) < (i88640):
            acc = w(w(acc * 31) + min(xs[idx(w(acc + shr(a0, (-29) & 15)))], w(div(w(a0 - i88640), w(mod(acc, 7) + 8)) - a0)))
            acc = w(w(acc * 31) + shr(shr(xs[idx(acc)], (23) & 15), (46) & 15))
        else:
            _i = idx(w(i88640 + i88640)); xs[_i] = shr(w(max(-36, a0) - -13), ((shr((a0 | -3), (acc) & 15) | (max(-43, 8) ^ i88640))) & 15)
        for i21761 in range(4):
            _i = idx(w(max((-20 | (i88640 & a0)), shl(38, (i88640) & 15)) + 32)); xs[_i] = a0
            _i = idx(acc); xs[_i] = (((shr(div(a0, w(mod(-42, 7) + 8)), (w(15 - i21761)) & 15)) if (w((a0 & i88640) - mod(i88640, w(mod(28, 7) + 8)))) < (w(mod(i21761, w(mod(30, 7) + 8)) * (i88640 ^ i88640))) else (mod(a0, w(mod((i21761 | -10), 7) + 8)))) ^ min(27, (w(-21 - 32) | i88640)))
        _i = idx(i88640); xs[_i] = shr(44, (w(i88640 - 21)) & 15)
    return (max(w(a0 + shr(47, (a0) & 15)), shl((a0 ^ -43), ((a0 ^ a0)) & 15)) | -10)
def f1(a0):
    global acc
    acc = w(w(acc * 31) + (39 & acc))
    return max(acc, acc)
def main():
    global acc
    v27836 = ((f0(11)) if (mod(w(xs[idx(8)] * (42 | 33)), w(mod(w(1 * w(50 - 6)), 7) + 8))) < (div(acc, w(mod(xs[idx(((-20) if (-9) < (-22) else (-40)))], 7) + 8))) else (48))
    for i85099 in range(12):
        _i = idx(w(w(v27836 + (div(38, w(mod(-41, 7) + 8)) ^ (v27836 | -47))) + shr(v27836, (xs[idx(((-12) if (i85099) < (-15) else (i85099)))]) & 15))); xs[_i] = shr(-16, (w(-21 + div((v27836 ^ -1), w(mod(shr(v27836, (i85099) & 15), 7) + 8)))) & 15)
        v92817 = (acc & mod(v27836, w(mod(xs[idx(shl(v27836, (v27836) & 15))], 7) + 8)))
        if (shr(i85099, (w(((w(11 + v92817)) if (w(v27836 * v27836)) < (shl(-36, (27) & 15)) else (w(i85099 - v27836))) + xs[idx(37)])) & 15)) < (w(-46 * 18)):
            acc = w(w(acc * 31) + i85099)
        else:
            acc = w(w(acc * 31) + i85099)
            _i = idx(v92817); xs[_i] = w(v92817 * i85099)
    v23403 = (acc & ((v27836) if (f1(acc)) < (v27836) else ((w(v27836 - -16) & xs[idx(v27836)]))))
    _i = idx(acc); xs[_i] = w(((shl(shl(v23403, (-47) & 15), (w(-21 - v23403)) & 15)) if (v27836) < (v27836) else ((w(-11 - 7) & v23403))) * (16 & f1(w(v27836 * v23403))))
    v83811 = v27836
    _i = idx((div(w(-36 * (v83811 | -39)), w(mod(xs[idx(w(v27836 - -32))], 7) + 8)) | (shl((v83811 | v83811), (xs[idx(-34)]) & 15) & -47))); xs[_i] = shl(v27836, (v23403) & 15)
    acc = w(w(acc * 31) + v27836)
    for i36503 in range(5):
        for i5034 in range(4):
            acc = w(w(acc * 31) + f1(div(min(i5034, w(-1 + -37)), w(mod(w(min(-37, v83811) * i36503), 7) + 8))))
            _i = idx(w(div(34, w(mod(acc, 7) + 8)) - max(div(acc, w(mod(xs[idx(10)], 7) + 8)), w(20 + w(42 - 27))))); xs[_i] = div(f1(xs[idx(-22)]), w(mod(shl(w(shl(i5034, (-31) & 15) - mod(i5034, w(mod(v83811, 7) + 8))), (-18) & 15), 7) + 8))
            _i = idx(v27836); xs[_i] = (max(shl(i36503, ((24 ^ v83811)) & 15), v23403) ^ xs[idx(v83811)])
    total = acc
    for x in xs: total = w(w(total * 1000003) + x)
    print(total)
main()
