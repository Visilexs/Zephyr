"""Float64 Phase Reasoner v1 and its exact 2D-real-coordinate port.

Paired coordinates use a trailing axis of length two, [real, imaginary].
Gradients use dL = Re(sum(conj(g) * dz)), hence grad(abs2(z)) = 2*z.
"""

from dataclasses import dataclass
import numpy as np


def pairings(dimension, stage):
    """Return the disjoint even or odd cyclic coordinate pairs."""
    if dimension < 2 or dimension % 2 or stage not in (0, 1):
        raise ValueError('Expected an even dimension and stage 0 or 1')
    left = np.arange(stage, dimension, 2)
    return left, (left + 1) % dimension


class Coordinates:
    """Complex arithmetic, or the same arithmetic using only float64 arrays."""

    def __init__(self, paired=False):
        self.paired = paired

    def pack(self, x, y):
        return np.stack((x, y), axis=-1) if self.paired else x + 1j * y

    def parts(self, z):
        return (z[..., 0], z[..., 1]) if self.paired else (z.real, z.imag)

    def scale(self, z, value):
        return z * (np.asarray(value)[..., None] if self.paired else value)

    def conj(self, z):
        if not self.paired:
            return z.conj()
        return z * np.array([1., -1.])

    def mul(self, a, b):
        if not self.paired:
            return a * b
        x, y = self.parts(a)
        u, v = self.parts(b)
        return self.pack(x * u - y * v, x * v + y * u)

    def phase(self, angle):
        return self.pack(np.cos(angle), np.sin(angle))

    def times_i(self, z):
        x, y = self.parts(z)
        return self.pack(-y, x)

    def inner(self, a, b):
        x, y = self.parts(a)
        u, v = self.parts(b)
        return x * u + y * v

    def abs2(self, z):
        return self.inner(z, z)

    def abs2_backward(self, z, gradient):
        """Real-coordinate adjoint: a unit upstream gradient returns exactly 2z."""
        return self.scale(z, 2 * gradient)

    def project(self, z, matrix):
        if not self.paired:
            return z @ matrix.T
        x, y = self.parts(z)
        a, b = self.parts(matrix)
        return self.pack(x @ a.T - y @ b.T, x @ b.T + y @ a.T)

    def project_backward(self, z, matrix, gradient):
        """Adjoints of the bias-free projection, including batch reduction."""
        if not self.paired:
            return gradient @ matrix.conj(), gradient.T @ z.conj()
        x, y = self.parts(z)
        a, b = self.parts(matrix)
        u, v = self.parts(gradient)
        return (self.pack(u @ a + v @ b, -u @ b + v @ a),
                self.pack(u.T @ x + v.T @ y, -u.T @ y + v.T @ x))


def features(z, coordinates):
    """The normative cyclic 3D invariant feature map."""
    x, y = coordinates.parts(z)
    u, v = np.roll(x, -1, axis=1), np.roll(y, -1, axis=1)
    return np.concatenate((x*x + y*y, x*u + y*v, x*v - y*u), axis=1)


def features_backward(z, gradient, coordinates):
    """Include both appearances of each coordinate in cyclic neighbor products."""
    x, y = coordinates.parts(z)
    u, v = np.roll(x, -1, axis=1), np.roll(y, -1, axis=1)
    a, b, c = np.split(gradient, 3, axis=1)
    gx = 2*a*x + b*u + c*v + np.roll(b*x - c*y, 1, axis=1)
    gy = 2*a*y + b*v - c*u + np.roll(b*y + c*x, 1, axis=1)
    return coordinates.pack(gx, gy)


def givens(z, theta, phi, stage, coordinates):
    """Apply one simultaneous stage, reading both old values before writes."""
    left, right = pairings(z.shape[1], stage)
    a, b = z[:, left], z[:, right]
    c, s, q = np.cos(theta), np.sin(theta), coordinates.phase(phi)
    out = z.copy()
    out[:, left] = coordinates.scale(a, c) + coordinates.scale(coordinates.mul(q, b), s)
    out[:, right] = -coordinates.scale(coordinates.mul(coordinates.conj(q), a), s) + coordinates.scale(b, c)
    return out


def givens_backward(z, theta, phi, stage, gradient, op):
    """Analytic state and angle VJPs for the normative signs/conjugation."""
    left, right = pairings(z.shape[1], stage)
    a, b, ga, gb = z[:, left], z[:, right], gradient[:, left], gradient[:, right]
    c, s, q = np.cos(theta), np.sin(theta), op.phase(phi)
    qb, qa = op.mul(q, b), op.mul(op.conj(q), a)
    gt = op.inner(ga, -op.scale(a, s) + op.scale(qb, c))
    gt += op.inner(gb, -op.scale(qa, c) - op.scale(b, s))
    gp = op.inner(ga, op.times_i(op.scale(qb, s)))
    gp += op.inner(gb, op.times_i(op.scale(qa, s)))
    return givens(gradient, -theta, phi, stage, op), gt, gp


@dataclass(frozen=True)
class Config:
    input_vocab: int = 8
    output_vocab: int = 3
    D: int = 128
    E: int = 32
    H: int = 128
    K: int = 4
    pad: int = 0
    epsilon: float = 1e-8

    def __post_init__(self):
        pairings(self.D, 0)
        if min(self.input_vocab, self.output_vocab, self.E, self.H) < 1 or self.K < 0:
            raise ValueError('Invalid dimensions or THINK count')
        if not 0 <= self.pad < self.input_vocab or not np.isfinite(self.epsilon) or self.epsilon <= 0:
            raise ValueError('Invalid PAD or epsilon')


class PhaseModel:
    """Batched recurrence with an optional analytic mean-NLL reverse pass.

THINK has its own shared learned embedding. Integer tokens have no derivative;
input gradients are provided for continuous token embeddings and raw initial
states. An omitted initial state uses the learned z_init and its normalization.
"""

    def __init__(self, config=Config(), seed=1729):
        self.config = config
        self.op = Coordinates()
        rng = np.random.default_rng(seed)
        d, e, h = config.D, config.E, config.H
        def real(shape):
            return rng.normal(0, 0.15, shape)
        self.parameters = {
            'embedding': real((config.input_vocab, e)), 'think': real((e,)),
            'W1': real((h, e + 3*d)), 'b1': real((h,)),
            'W2': real((3*d, h)), 'b2': real((3*d,)),
            'z_init': real((d,)) + 1j*real((d,)),
            'M': real((config.output_vocab, d)) + 1j*real((config.output_vocab, d)),
        }

    def update(self, z, embedding):
        """Compute all angles once from the pre-update state; return a VJP cache."""
        p, op, d = self.parameters, self.op, self.config.D
        inputs = np.concatenate((embedding, features(z, op)), axis=1)
        hidden = np.tanh(inputs @ p['W1'].T + p['b1'])
        bounded = np.tanh(hidden @ p['W2'].T + p['b2'])
        angles = np.pi * bounded
        states = [z, op.mul(z, op.phase(angles[:, :d]))]
        for stage in (0, 1):
            offset = d + stage*d
            states.append(givens(states[-1], angles[:, offset:offset+d//2],
                                 angles[:, offset+d//2:offset+d], stage, op))
        return states[-1], (inputs, hidden, bounded, angles, states)

    def update_backward(self, cache, gradient, gradients):
        """Reverse gates and then the controller, adding both state paths."""
        inputs, hidden, bounded, angles, states = cache
        p, op, d, e = self.parameters, self.op, self.config.D, self.config.E
        angle_gradient = np.zeros_like(angles)
        for stage in (1, 0):
            offset = d + stage*d
            gradient, gt, gp = givens_backward(
                states[stage+1], angles[:, offset:offset+d//2],
                angles[:, offset+d//2:offset+d], stage, gradient, op)
            angle_gradient[:, offset:offset+d//2] = gt
            angle_gradient[:, offset+d//2:offset+d] = gp
        angle_gradient[:, :d] = op.inner(gradient, op.times_i(states[1]))
        gz = op.mul(gradient, op.phase(-angles[:, :d]))
        output_gradient = angle_gradient * np.pi * (1 - bounded*bounded)
        gradients['W2'] += output_gradient.T @ hidden
        gradients['b2'] += output_gradient.sum(axis=0)
        gh = (output_gradient @ p['W2']) * (1 - hidden*hidden)
        gradients['W1'] += gh.T @ inputs
        gradients['b1'] += gh.sum(axis=0)
        gi = gh @ p['W1']
        return gz + features_backward(states[0], gi[:, e:], op), gi[:, :e]

    def readout(self, z):
        """Stable log-domain smoothed squared amplitudes, with no softmax of weights."""
        amplitudes = self.op.project(z, self.parameters['M'])
        if not np.isfinite(amplitudes).all():
            raise ValueError('Nonfinite readout amplitude')
        x, y = self.op.parts(amplitudes)
        with np.errstate(divide='ignore'):
            log_weights = 2 * np.log(np.hypot(x, y))
        log_s = np.logaddexp(log_weights, np.log(self.config.epsilon))
        log_p = log_s - np.logaddexp.reduce(log_s, axis=1, keepdims=True)
        return np.exp(log_p), log_p, amplitudes, log_s

    def forward(self, tokens, targets=None, *, initial=None, embeddings=None, backward=False):
        """Return probabilities, full trajectory, angles, and optional loss/gradients.

initial is raw [B,D] complex or [B,D,2] paired-real and is normalized once.
embeddings optionally overrides the token lookup with [B,T,E] real values.
PAD rows are never sent through the controller, in either direction.
"""
        cfg, p, op = self.config, self.parameters, self.op
        tokens = np.asarray(tokens)
        if tokens.ndim != 2 or tokens.shape[0] == 0 or tokens.dtype.kind not in 'iu':
            raise ValueError('Tokens must be a nonempty integer [B,T] batch')
        if np.any(tokens < 0) or np.any(tokens >= cfg.input_vocab):
            raise ValueError('Token outside vocabulary')
        batch, length = tokens.shape
        raw = np.broadcast_to(p['z_init'], (batch,) + p['z_init'].shape).copy() if initial is None else np.asarray(initial, dtype=p['z_init'].dtype)
        if raw.shape != (batch,) + p['z_init'].shape:
            raise ValueError('Invalid initial state shape')
        norm = np.sqrt(op.abs2(raw).sum(axis=1, keepdims=True))
        if not np.isfinite(norm).all() or np.any(norm == 0):
            raise ValueError('Initial norm must be finite and nonzero')
        embedded = p['embedding'][tokens] if embeddings is None else np.asarray(embeddings, dtype=np.float64)
        if embedded.shape != (batch, length, cfg.E) or not np.isfinite(embedded).all():
            raise ValueError('Invalid input embeddings')
        z = op.scale(raw, 1 / norm)
        trajectory, caches, gate_angles = [z.copy()], [], []
        for step in range(length + cfg.K):
            active = np.flatnonzero(tokens[:, step] != cfg.pad) if step < length else np.arange(batch)
            embedding = embedded[active, step] if step < length else np.broadcast_to(p['think'], (batch, cfg.E))
            updated, cache = self.update(z[active], embedding)
            z = z.copy()
            z[active] = updated
            caches.append((active, cache))
            gate_angles.append(cache[3])
            trajectory.append(z.copy())
        probabilities, log_p, amplitudes, log_s = self.readout(z)
        result = dict(probabilities=probabilities, log_probabilities=log_p, state=z,
                      trajectory=trajectory, angles=gate_angles, think_steps=cfg.K)
        if targets is None:
            if backward:
                raise ValueError('Targets required for backward')
            return result
        targets = np.asarray(targets)
        if targets.shape != (batch,) or targets.dtype.kind not in 'iu' or np.any(targets < 0) or np.any(targets >= cfg.output_vocab):
            raise ValueError('Invalid targets')
        result['loss'] = -log_p[np.arange(batch), targets].mean()
        if not backward:
            return result
        gradients = {name: np.zeros_like(value) for name, value in p.items()}
        gw = np.broadcast_to(np.exp(-np.logaddexp.reduce(log_s, axis=1, keepdims=True)), log_s.shape).copy()
        gw[np.arange(batch), targets] -= np.exp(-log_s[np.arange(batch), targets])
        ga = op.abs2_backward(amplitudes, gw / batch)
        gz, gradients['M'] = op.project_backward(z, p['M'], ga)
        input_embeddings = np.zeros_like(embedded)
        for step in reversed(range(len(caches))):
            active, cache = caches[step]
            gz[active], ge = self.update_backward(cache, gz[active], gradients)
            if step < length:
                input_embeddings[active, step] = ge
                if embeddings is None:
                    np.add.at(gradients['embedding'], tokens[active, step], ge)
            else:
                gradients['think'] += ge.sum(axis=0)
        normalized = trajectory[0]
        radial = op.inner(gz, normalized).sum(axis=1, keepdims=True)
        input_initial = op.scale(gz - op.scale(normalized, radial), 1 / norm)
        if initial is None:
            gradients['z_init'] = input_initial.sum(axis=0)
        result.update(gradients=gradients, input_initial=input_initial, input_embeddings=input_embeddings)
        return result


class PairedRealModel(PhaseModel):
    """Mapped port: all forward and reverse arithmetic operates on real arrays."""

    def __init__(self, model):
        self.config = model.config
        self.op = Coordinates(paired=True)
        self.parameters = {
            name: self.op.pack(value.real, value.imag) if np.iscomplexobj(value) else value.copy()
            for name, value in model.parameters.items()
        }
