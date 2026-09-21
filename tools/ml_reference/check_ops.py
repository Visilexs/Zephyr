"""Cross-check lib/ml/ops.zeph against numpy -- acceptance A04 and A05.

Reads the bit-exact dump written by the companion .zeph program, rebuilds the
same operands in numpy, and compares. Values cross the boundary as IEEE-754
bit patterns rather than decimal text, so nothing is lost to formatting and a
disagreement is a real disagreement.

numpy is the reference here rather than PyTorch, which is not installed. For
these operators the two agree by construction: both are IEEE-754 double
arithmetic in the same order, and numpy's complex128 has the identical memory
layout to torch.complex128.

Usage: python check_ops.py <dump file>
"""
import struct
import sys

import numpy as np

TOL = 1e-13


def f64(bits_str):
    """Reconstruct a double from the signed 64-bit pattern Zephyr printed."""
    return struct.unpack('<d', struct.pack('<q', int(bits_str)))[0]


def load(path):
    """Group the dump into {tag: [values]}, real or complex per line width."""
    out = {}
    for line in open(path):
        parts = line.split()
        if not parts:
            continue
        tag = parts[0]
        if len(parts) == 2:
            out.setdefault(tag, []).append(f64(parts[1]))
        elif len(parts) == 3:
            out.setdefault(tag, []).append(complex(f64(parts[1]), f64(parts[2])))
    return out


def cmp(name, got, want, results):
    got = np.asarray(got).ravel()
    want = np.asarray(want).ravel()
    if got.shape != want.shape:
        results.append((name, False, f'shape {got.shape} vs {want.shape}'))
        return
    err = np.abs(got - want)
    scale = 1.0 + np.abs(want)
    rel = float(np.max(err / scale)) if err.size else 0.0
    results.append((name, rel <= TOL, f'max scaled err {rel:.3e}'))


def main():
    d = load(sys.argv[1])
    A = np.array(d['A']).reshape(4, 5)
    B = np.array(d['B']).reshape(4, 5)
    R = np.array(d['R']).reshape(1, 5)
    M = np.array(d['M']).reshape(5, 3)
    CA = np.array(d['CA']).reshape(3, 2)
    CB = np.array(d['CB']).reshape(3, 2)
    CM = np.array(d['CM']).reshape(2, 4)

    res = []
    cmp('add', d['add'], A + B, res)
    cmp('sub', d['sub'], A - B, res)
    cmp('mul', d['mul'], A * B, res)
    cmp('div', d['div'], A / B, res)
    cmp('broadcast add', d['bcast'], A + R, res)
    cmp('neg', d['neg'], -A, res)
    cmp('sum_dim 0', d['sumdim0'], A.sum(axis=0, keepdims=True), res)
    cmp('sum_dim 1', d['sumdim1'], A.sum(axis=1, keepdims=True), res)
    cmp('sum_all', d['sumall'], np.array([A.sum()]), res)
    cmp('mean_all', d['meanall'], np.array([A.mean()]), res)
    cmp('mul, transposed operands', d['trmul'], (A.T * B.T), res)
    cmp('matmul', d['matmul'], A @ M, res)

    cmp('complex add', d['cadd'], CA + CB, res)
    cmp('complex mul', d['cmul'], CA * CB, res)
    cmp('complex div', d['cdiv'], CA / CB, res)
    cmp('conj', d['cconj'], np.conj(CA), res)
    cmp('abs2', d['cabs2'], np.abs(CA) ** 2, res)
    cmp('real', d['creal'], CA.real, res)
    cmp('imag', d['cimag'], CA.imag, res)
    cmp('expi', d['cexpi'], np.exp(1j * CA.real), res)
    cmp('complex matmul', d['cmatmul'], CA @ CM, res)

    width = max(len(n) for n, _, _ in res)
    bad = 0
    for name, ok, detail in res:
        print(f'{"PASS" if ok else "FAIL"} {name:<{width}}  {detail}')
        if not ok:
            bad += 1
    print(f'\n{len(res) - bad}/{len(res)} operators agree with numpy '
          f'within {TOL:g} scaled error')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
