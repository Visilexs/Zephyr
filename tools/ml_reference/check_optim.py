"""A08: compare IEEE-754 dumps with independent paired-real numpy optimizers.

Usage: python tools/ml_reference/check_optim.py <dump>
Companion: tests/ml/optim_dump.zeph. Inputs come only from the mirrored LCG.
"""
import sys
from pathlib import Path

import numpy as np

from check_ops import TOL, cmp, f64


def load(path):
    """Read the existing bit-pattern protocol, including PowerShell UTF-16."""
    raw = Path(path).read_bytes()
    encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    out = {}
    for number, line in enumerate(raw.decode(encoding).splitlines(), 1):
        parts = line.split()
        if not parts:
            continue
        if len(parts) not in (2, 3):
            raise ValueError(f'invalid dump line {number}')
        value = f64(parts[1]) if len(parts) == 2 else complex(f64(parts[1]), f64(parts[2]))
        out.setdefault(parts[0], []).append(value)
    return out


def reference():
    """Complex arrays stay paired-real throughout all optimizer arithmetic."""
    seed = 20260921

    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % 2147483648
        return (seed % 20001) / 100000.0 - 0.1

    def fixture(paired, gradient=False):
        shape = (4, 2) if paired else (6,)
        values = np.array([rnd() for _ in range(int(np.prod(shape)))]).reshape(shape)
        if gradient:
            if paired:
                values[:, 0] *= 0.001
                values[:, 1] *= 1000.0
            else:
                values[0] = 0.0
        return values

    expected = {}

    def remember(tag, arrays):
        expected[f'{tag}.real'] = arrays[0].copy()
        # Complex packing is only for the output protocol, never moment math.
        expected[f'{tag}.complex'] = arrays[1][:, 0] + 1j * arrays[1][:, 1]

    initial = [fixture(False), fixture(True)]
    remember('input', initial)
    grads = []
    for step in range(3):
        grads.append([fixture(False, True), fixture(True, True)])
        remember(f'input.g{step}', grads[-1])

    for name, momentum in [('sgd', 0.0), ('momentum', 0.6), ('adamw', 0.0)]:
        params = [p.copy() for p in initial]
        first = [np.zeros_like(p) for p in params]
        second = [np.zeros_like(p) for p in params]
        for step, gradients in enumerate(grads):
            for i, (p, g) in enumerate(zip(params, gradients)):
                if name == 'adamw':
                    first[i] = 0.8 * first[i] + (1.0 - 0.8) * g
                    second[i] = 0.95 * second[i] + (1.0 - 0.95) * g * g
                    mh = first[i] / (1.0 - 0.8 ** (step + 1))
                    vh = second[i] / (1.0 - 0.95 ** (step + 1))
                    params[i] = p - 0.03 * 0.07 * p - 0.03 * mh / (np.sqrt(vh) + 1e-8)
                else:
                    first[i] = momentum * first[i] + (g + 0.07 * p)
                    params[i] = p - 0.03 * first[i]
            remember(f'{name}.{step}', params)
            remember(f'{name}.{step}.m', first)
            remember(f'{name}.{step}.v', second)
            expected[f'{name}.{step}.count'] = np.array([step + 1.0])

    # One joint norm, treating imaginary entries as independent coordinates.
    norm = np.linalg.norm(np.concatenate([g.ravel() for g in grads[0]]))
    clipped = [g * (0.5 / norm) for g in grads[0]]
    expected['clip.norm'] = np.array([norm])
    remember('clip', clipped)
    expected['clip.small_norm'] = np.array([np.linalg.norm(np.concatenate([g.ravel() for g in clipped]))])
    remember('clip.unchanged', clipped)
    return expected


def main():
    dumped = load(sys.argv[1])
    expected = reference()
    results = []
    for name, wanted in expected.items():
        if name not in dumped:
            results.append((name, False, 'missing quantity'))
            continue
        cmp(name, dumped[name], wanted, results)
        if name.startswith('input.'):
            actual = np.asarray(dumped[name], dtype=wanted.dtype)
            exact = actual.tobytes() == wanted.ravel().tobytes()
            label, passed, detail = results[-1]
            results[-1] = (label, passed and exact, detail + f'; bit-identical={exact}')
    for name in sorted(dumped.keys() - expected.keys()):
        results.append((name, False, 'unexpected quantity'))
    for name, passed, detail in results:
        print(f'{"PASS" if passed else "FAIL"} {name}: {detail}')
    failed = sum(not passed for _, passed, _ in results)
    print(f'optim parity: {len(results) - failed}/{len(results)} quantities passed (tolerance {TOL:g})')
    return int(failed != 0)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, IndexError) as error:
        print(f'FAIL optim dump: {error}')
        sys.exit(1)
