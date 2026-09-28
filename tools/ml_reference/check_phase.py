"""M3: independently rebuild weights and compare every actual forward intermediate.

Usage: python tools/ml_reference/check_phase.py dump.txt
No reference values are supplied to Zephyr. The float64 model is unchanged.
"""
import sys
from pathlib import Path

import numpy as np

from check_ops import cmp, f64
from phase_model import Config, PhaseModel


def parameters(config):
    """Reset the LCG per dimension; row-major, complex components interleaved."""
    seed = 20260921

    def rnd():
        nonlocal seed
        seed = (seed * 1103515245 + 12345) % 2147483648
        return (seed % 20001) / 100000.0 - 0.1

    d, e, h = config.D, config.E, config.H
    # This order is identical to phase_dump.zeph; never seed from dump values.
    shapes = {
        'embedding': (config.input_vocab, e), 'think': (e,),
        'W1': (h, e + 3*d), 'b1': (h,),
        'W2': (3*d, h), 'b2': (3*d,),
        'z_init': (d,), 'M': (config.output_vocab, d),
    }
    result = {}
    for name, shape in shapes.items():
        values = [complex(rnd(), rnd()) if name in ('z_init', 'M') else rnd()
                  for _ in range(int(np.prod(shape)))]
        result[name] = np.array(values).reshape(shape)
    return result


def reference(dimension):
    """Capture caches from the reference's own forward call, including PAD masks."""
    config = Config(input_vocab=7, output_vocab=3, D=dimension, E=3, H=5, K=4)
    model = PhaseModel(config)
    model.parameters = parameters(config)
    tokens = np.array([[1, 2, 3, 4], [5, 6, 0, 0], [0, 0, 0, 0]])
    caches = []
    original_update = model.update

    def capture(z, embedding):
        updated, cache = original_update(z, embedding)
        caches.append(cache)
        return updated, cache

    model.update = capture
    result = model.forward(tokens)
    prefix = f'D{dimension}'
    expected = {f'{prefix}.param.{name}': value for name, value in model.parameters.items()}
    expected[f'{prefix}.initial'] = result['trajectory'][0]
    for step, (inputs, hidden, bounded, angles, states) in enumerate(caches):
        active = np.flatnonzero(tokens[:, step] != config.pad) if step < tokens.shape[1] else np.arange(len(tokens))
        quantities = dict(active=active, features=inputs[:, config.E:], hidden=hidden,
                          angles=angles, phase=states[1], stage0=states[2],
                          stage1=states[3], state=result['trajectory'][step + 1])
        expected.update({f'{prefix}.step{step}.{name}': value for name, value in quantities.items()})
    expected[f'{prefix}.probabilities'] = result['probabilities']
    return expected


def load(path):
    """Accept native or Windows PowerShell redirected bit-pattern text strictly."""
    raw = Path(path).read_bytes()
    encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    values = {}
    for number, line in enumerate(raw.decode(encoding).splitlines(), 1):
        fields = line.split()
        if not fields:
            continue
        if len(fields) not in (2, 3):
            raise ValueError(f'Invalid dump line {number}')
        value = f64(fields[1]) if len(fields) == 2 else complex(f64(fields[1]), f64(fields[2]))
        values.setdefault(fields[0], []).append(value)
    return values


def main():
    dumped = load(sys.argv[1])
    expected = reference(4) | reference(8)
    results = []
    for name, wanted in expected.items():
        if name not in dumped:
            results.append((name, False, 'missing quantity'))
            continue
        cmp(name, dumped[name], wanted, results)
        if '.param.' in name:
            # Parity tolerance must not hide a different fixture or fill order.
            actual = np.asarray(dumped[name], dtype=wanted.dtype)
            exact = actual.tobytes() == wanted.ravel().tobytes()
            label, passed, detail = results[-1]
            results[-1] = (label, passed and exact, detail + f'; bit-identical={exact}')
    for name in sorted(dumped.keys() - expected.keys()):
        results.append((name, False, 'unexpected quantity'))
    for name, passed, detail in results:
        print(f'{"PASS" if passed else "FAIL"} {name}: {detail}')
    failed = sum(not passed for _, passed, _ in results)
    print(f'phase parity: {len(results) - failed}/{len(results)} quantities passed')
    return int(failed != 0)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, IndexError) as error:
        print(f'FAIL phase dump: {error}')
        sys.exit(1)
