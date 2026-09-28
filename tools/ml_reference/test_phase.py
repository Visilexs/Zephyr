"""Batched float64 acceptance checks for Phase Reasoner v1; numpy only."""

import numpy as np

from phase_model import Config, Coordinates, PairedRealModel, PhaseModel, givens, pairings


def close(actual, expected, tolerance=1e-12):
    """Use absolute tolerances: no scale-dependent relaxation of acceptance."""
    actual, expected = np.asarray(actual), np.asarray(expected)
    assert actual.shape == expected.shape, (actual.shape, expected.shape)
    assert np.isfinite(actual).all() and np.isfinite(expected).all()
    error = np.max(np.abs(actual - expected), initial=0)
    assert error <= tolerance, (error, tolerance)


def mapped(value):
    return np.stack((value.real, value.imag), axis=-1) if np.iscomplexobj(value) else value


def finite_difference(function, value):
    """Richardson-extrapolated central differences, independently in x and y.

Two central stencils cancel the leading truncation error, allowing a 1e-10
absolute comparison without tiny, cancellation-dominated float64 steps.
"""
    gradient = np.zeros_like(value)
    for index in np.ndindex(value.shape):
        original = value[index].copy()
        for direction in ((1, 1j) if np.iscomplexobj(value) else (1,)):
            estimates = []
            try:
                for step in (1e-4, 5e-5):
                    value[index] = original + direction*step
                    plus = function()
                    value[index] = original - direction*step
                    minus = function()
                    estimates.append((plus - minus) / (2*step))
            finally:
                value[index] = original
            gradient[index] += direction * (4*estimates[1] - estimates[0]) / 3
    return gradient


def check_gates(dimension):
    """Check complete batched stage matrices, inverses, updates and drift."""
    rng, op = np.random.default_rng(10 + dimension), Coordinates()
    model = PhaseModel(Config(D=dimension, E=2, H=3))
    z = rng.normal(size=(3, dimension)) + 1j*rng.normal(size=(3, dimension))
    theta, phi = rng.normal(size=(2, 3, dimension//2))
    for stage in (0, 1):
        left, right = pairings(dimension, stage)
        indices = np.concatenate((left, right))
        assert np.all((indices >= 0) & (indices < dimension))
        assert len(np.unique(indices)) == dimension
        close(np.sort(indices), np.arange(dimension))
        for row in range(3):
            # Applying to row basis vectors yields G transpose.
            matrix = givens(np.eye(dimension, dtype=np.complex128), theta[row], phi[row], stage, op).T
            close(matrix.conj().T @ matrix, np.eye(dimension))
        output = givens(z, theta, phi, stage, op)
        close(givens(output, -theta, phi, stage, op), z)
        close(op.abs2(output).sum(axis=1), op.abs2(z).sum(axis=1))
        port = givens(mapped(z), theta, phi, stage, Coordinates(True))
        close(port, mapped(output))
    z /= np.sqrt(op.abs2(z).sum(axis=1, keepdims=True))
    for _ in range(12):
        z, _ = model.update(z, rng.normal(size=(3, 2)))
        close(op.abs2(z).sum(axis=1), np.ones(3))
    # Fixed-angle drift is separate from the nonlinear trajectory above.
    for _ in range(10000):
        z = givens(z, theta, phi, 0, op)
    close(op.abs2(z).sum(axis=1), np.ones(3), 1e-11)


def check_symmetry(dimension):
    """Test whole-model global equivariance and constructed relative sensitivity."""
    model = PhaseModel(Config(D=dimension, E=2, H=3))
    tokens = np.array([[1, 2, 0], [3, 4, 2]])
    reference = model.forward(tokens)
    gamma = np.exp(0.73j)
    model.parameters['z_init'] *= gamma
    rotated = model.forward(tokens)
    close(rotated['probabilities'], reference['probabilities'])
    for before, after in zip(reference['trajectory'], rotated['trajectory']):
        close(after, gamma*before)
    for before, after in zip(reference['angles'], rotated['angles']):
        close(after, before)
    port = PairedRealModel(model).forward(tokens)
    close(port['probabilities'], reference['probabilities'])
    # Zero controller means identity updates even with K=4 and real tokens.
    model = PhaseModel(Config(D=dimension, E=2, H=2, output_vocab=2))
    for name in ('W1', 'b1', 'W2', 'b2'):
        model.parameters[name].fill(0)
    model.parameters['M'].fill(0)
    model.parameters['M'][:, :2] = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
    initial = np.zeros((2, dimension), dtype=np.complex128)
    initial[:, :2] = [[1, 1], [1, -1]]
    output = model.forward(tokens, initial=initial)
    expected = np.array([[1 + model.config.epsilon, model.config.epsilon],
                         [model.config.epsilon, 1 + model.config.epsilon]]) / (1 + 2*model.config.epsilon)
    close(output['probabilities'], expected)
    assert output['probabilities'][0, 0] - output['probabilities'][1, 0] > 0.99
    close(PairedRealModel(model).forward(tokens, initial=mapped(initial))['probabilities'], expected)


def check_gradients(dimension):
    """Compare every analytic adjoint, independent finite differences and SGD."""
    model = PhaseModel(Config(D=dimension, E=2, H=2, input_vocab=4, K=4))
    port = PairedRealModel(model)
    tokens, targets = np.array([[1, 2, 0], [2, 0, 3]]), np.array([0, 2])
    complex_result = model.forward(tokens, targets, backward=True)
    real_result = port.forward(tokens, targets, backward=True)
    for name in ('probabilities', 'log_probabilities', 'loss', 'state', 'input_initial', 'input_embeddings'):
        close(real_result[name], mapped(complex_result[name]), 1e-10)
    for before, after in zip(complex_result['trajectory'], real_result['trajectory']):
        close(mapped(before), after, 1e-10)
    for name in model.parameters:
        complex_gradient = complex_result['gradients'][name]
        real_gradient = real_result['gradients'][name]
        close(real_gradient, mapped(complex_gradient), 1e-10)
        for implementation, expected in ((model, complex_gradient), (port, real_gradient)):
            numerical = finite_difference(lambda: implementation.forward(tokens, targets)['loss'],
                                          implementation.parameters[name])
            close(numerical, expected, 1e-10)
    # Differentiate continuous inputs independently of learned z_init/lookup.
    initial = np.stack((model.parameters['z_init'], model.parameters['z_init'] * (0.8 + 0.3j)))
    embedding = model.parameters['embedding'][tokens].copy()
    for implementation, state in ((model, initial), (port, mapped(initial))):
        result = implementation.forward(tokens, targets, initial=state, embeddings=embedding, backward=True)
        loss = lambda: implementation.forward(tokens, targets, initial=state, embeddings=embedding)['loss']
        close(finite_difference(loss, state), result['input_initial'], 1e-10)
        close(finite_difference(loss, embedding), result['input_embeddings'], 1e-10)
        if implementation is model:
            input_result = result
        else:
            close(result['input_initial'], mapped(input_result['input_initial']), 1e-10)
            close(result['input_embeddings'], input_result['input_embeddings'], 1e-10)
    close(finite_difference(lambda: np.sum(model.op.abs2(initial)), initial), 2*initial, 1e-10)
    close(model.op.abs2_backward(initial, np.ones(initial.shape)), 2*initial, 0)
    close(port.op.abs2_backward(mapped(initial), np.ones(initial.shape)), mapped(2*initial), 0)
    for name in model.parameters:
        model.parameters[name] -= 0.01 * complex_result['gradients'][name]
        port.parameters[name] -= 0.01 * real_result['gradients'][name]
        close(port.parameters[name], mapped(model.parameters[name]), 1e-10)
    close(port.forward(tokens)['probabilities'], model.forward(tokens)['probabilities'], 1e-10)


def check_masks_and_readout(dimension):
    """Exercise masks, independent sequences, exact THINK execution and edge heads."""
    tokens, targets = np.array([[1, 0, 2, 0], [0, 3, 0, 0]]), np.array([0, 1])
    for count in (0, 4):
        model = PhaseModel(Config(D=dimension, E=2, H=3, K=count))
        for implementation in (model, PairedRealModel(model)):
            result = implementation.forward(tokens, targets, backward=True)
            assert len(result['angles']) == tokens.shape[1] + count
            assert len(result['trajectory']) == tokens.shape[1] + count + 1
            # Compare against explicitly executed THINK updates, not just metadata.
            z = result['trajectory'][tokens.shape[1]].copy()
            for _ in range(count):
                z, _ = implementation.update(z, np.broadcast_to(implementation.parameters['think'], (2, 2)))
            close(z, result['state'])
            for step in range(tokens.shape[1]):
                mask = tokens[:, step] == 0
                assert result['trajectory'][step][mask].tobytes() == result['trajectory'][step+1][mask].tobytes()
                assert np.count_nonzero(result['input_embeddings'][mask, step]) == 0
            assert np.count_nonzero(result['gradients']['embedding'][0]) == 0
            summed = {name: np.zeros_like(value) for name, value in implementation.parameters.items()}
            for row in range(2):
                compact = tokens[row][tokens[row] != 0][None, :]
                independent = implementation.forward(compact, targets[row:row+1], backward=True)
                close(independent['probabilities'][0], result['probabilities'][row])
                for name in summed:
                    summed[name] += independent['gradients'][name] / 2
            for name in summed:
                close(summed[name], result['gradients'][name])
            if count == 0:
                assert np.count_nonzero(result['gradients']['think']) == 0
                pads = implementation.forward(np.zeros((2, 3), dtype=int), targets, backward=True)
                for name in ('embedding', 'think', 'W1', 'W2', 'b1', 'b2'):
                    assert np.count_nonzero(pads['gradients'][name]) == 0
            for scale in (1., 1e-150, 1e150, 0.):
                original = implementation.parameters['M'].copy()
                implementation.parameters['M'] *= scale
                output = implementation.forward(tokens, targets, backward=True)
                close(output['probabilities'].sum(axis=1), np.ones(2))
                assert np.isfinite(output['log_probabilities']).all()
                if scale == 0:
                    close(output['probabilities'], np.full((2, 3), 1/3))
                    for value in output['gradients'].values():
                        assert np.count_nonzero(value) == 0
                implementation.parameters['M'][...] = original
            implementation.parameters['M'].fill(np.nan)
            try:
                implementation.forward(tokens)
            except ValueError:
                pass
            else:
                assert False, 'Nonfinite readout accepted'
            implementation.parameters['M'][...] = original
            for invalid in (0., np.inf, np.nan):
                implementation.parameters['z_init'].fill(invalid)
                try:
                    implementation.forward(tokens)
                except ValueError:
                    pass
                else:
                    assert False, 'Invalid initial state accepted'


def main():
    """Print only one PASS line per completed group and the final total."""
    checks = 0
    for dimension in (4, 8, 128):
        check_gates(dimension)
        print(f'PASS: A10 batched stage unitarity, inverse, pairings and norm D={dimension}')
        checks += 1
        check_symmetry(dimension)
        print(f'PASS: A11 full-model global phase and constructed relative phase D={dimension}')
        checks += 1
        check_masks_and_readout(dimension)
        print(f'PASS: PAD gradients, THINK counts, normalization and readout edges D={dimension}')
        checks += 1
        if dimension in (4, 8):
            check_gradients(dimension)
            print(f'PASS: A12 mapped forward/loss/all gradients, finite differences and SGD D={dimension}')
            checks += 1
    default = PhaseModel()
    assert (default.config.D, default.config.E, default.config.H, default.config.K) == (128, 32, 128, 4)
    close(default.forward(np.array([[1, 2, 0], [3, 1, 2]]))['probabilities'].sum(axis=1), np.ones(2))
    print('PASS: specification default dimensions')
    checks += 1
    print(f'{checks} check groups passed.')


if __name__ == '__main__':
    main()
