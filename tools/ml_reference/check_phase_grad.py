"""Compare native phase gradients against the reference's analytic reverse
pass -- acceptance A06 and A14.

Finite differences already cover these gradients inside Zephyr. This is the
sharper test: phase_model.py's analytic reverse pass agrees with its own
central differences to 3.7e-10, while the complex and paired-real models agree
with each other to 1e-12, so the stencil is the loose party. Comparing the
native gradients against the analytic ones removes that slack.

The weight fill is imported from check_phase rather than copied, so the two
harnesses cannot drift. No reference value is ever supplied to Zephyr.

Usage: python tools/ml_reference/check_phase_grad.py <dump file>
"""
import sys

import numpy as np

from check_ops import cmp, f64
from check_phase import load, parameters
from phase_model import Config, PhaseModel

TOKENS = np.array([[1, 2, 3, 4], [5, 6, 0, 0], [0, 0, 0, 0]])
TARGETS = np.array([0, 2, 1])


def reference(dimension):
    config = Config(input_vocab=7, output_vocab=3, D=dimension, E=3, H=5, K=4)
    model = PhaseModel(config)
    model.parameters = parameters(config)
    result = model.forward(TOKENS, TARGETS, backward=True)
    prefix = 'D{}'.format(dimension)
    expected = {'{}.param.{}'.format(prefix, k): v for k, v in model.parameters.items()}
    expected['{}.loss'.format(prefix)] = np.array([result['loss']])
    for name, value in result['gradients'].items():
        expected['{}.grad.{}'.format(prefix, name)] = value
    return expected


def main():
    dumped = load(sys.argv[1])
    expected = reference(4) | reference(8)
    results = []

    # The dump carries no parameters, only the loss and gradients; the weights
    # are still rebuilt above and their agreement is established by
    # check_phase.py against the same LCG. Drop them from the comparison here
    # rather than reporting them as missing.
    expected = {k: v for k, v in expected.items() if '.param.' not in k}

    for name, wanted in expected.items():
        if name not in dumped:
            results.append((name, False, 'missing quantity'))
            continue
        cmp(name, dumped[name], wanted, results)
    for name in sorted(dumped.keys() - expected.keys()):
        results.append((name, False, 'unexpected quantity'))

    for name, passed, detail in results:
        print('{} {}: {}'.format('PASS' if passed else 'FAIL', name, detail))
    failed = sum(not passed for _, passed, _ in results)
    print('\nphase gradients: {}/{} quantities agree with the analytic reference'
          .format(len(results) - failed, len(results)))
    return int(failed != 0)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, IndexError, KeyError) as error:
        print('FAIL phase gradient dump: {}'.format(error))
        sys.exit(1)
