"""Independent verification of the Codex-written phase_model.py.

Written against MATHEMATICS.md / INTERFERENCE.md / READOUT.md directly, not
against the module's own test file, so agreement is evidence rather than
self-consistency. Targets A10, A11, A12.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from phase_model import (Config, PhaseModel, PairedRealModel, Coordinates,
                         pairings, givens, features)

ok = 0
fail = 0


def ck(name, cond, detail=''):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print('FAIL {}  {}'.format(name, detail))


def rejects(name, fn):
    try:
        fn()
        ck(name, False, 'accepted')
    except ValueError:
        ck(name, True)


def small(seed=7, **kw):
    cfg = Config(input_vocab=5, output_vocab=3, D=4, E=3, H=6, K=2, **kw)
    return PhaseModel(cfg, seed=seed)


op = Coordinates()
rng = np.random.default_rng(11)

# ---------------------------------------------------------------- A10
for D in (4, 8, 128):
    for stage in (0, 1):
        l, r = pairings(D, stage)
        idx = np.concatenate([l, r])
        ck('pair bijection D={} s={}'.format(D, stage),
           sorted(idx.tolist()) == list(range(D)))
        ck('pair bounds D={} s={}'.format(D, stage),
           l.min() >= 0 and r.max() < D and len(l) == D // 2)

rejects('odd D pairing', lambda: pairings(5, 0))
rejects('bad stage', lambda: pairings(4, 2))

# G^H G = I, from the doc's matrix rather than from the module
for _ in range(20):
    th, ph = rng.uniform(-np.pi, np.pi, 2)
    c, s, q = np.cos(th), np.sin(th), np.exp(1j * ph)
    G = np.array([[c, s * q], [-s * np.conj(q), c]])
    ck('G^H G = I', np.allclose(G.conj().T @ G, np.eye(2), atol=1e-14))

# the module's givens must equal that matrix applied pairwise
for D in (4, 128):
    for stage in (0, 1):
        z = rng.normal(size=(3, D)) + 1j * rng.normal(size=(3, D))
        th = rng.uniform(-np.pi, np.pi, (3, D // 2))
        ph = rng.uniform(-np.pi, np.pi, (3, D // 2))
        got = givens(z, th, ph, stage, op)
        l, r = pairings(D, stage)
        c, s, q = np.cos(th), np.sin(th), np.exp(1j * ph)
        want = z.copy()
        want[:, l] = c * z[:, l] + s * q * z[:, r]
        want[:, r] = -s * np.conj(q) * z[:, l] + c * z[:, r]
        tag = 'D={} s={}'.format(D, stage)
        ck('givens matches doc ' + tag, np.allclose(got, want, atol=1e-15),
           '{:.2e}'.format(np.abs(got - want).max()))
        ck('givens norm preserved ' + tag,
           np.allclose((np.abs(got) ** 2).sum(1), (np.abs(z) ** 2).sum(1), atol=1e-12))
        back = givens(got, -th, ph, stage, op)
        ck('givens inverse by G^H ' + tag, np.allclose(back, z, atol=1e-12),
           '{:.2e}'.format(np.abs(back - z).max()))

# simultaneity: writing in place would corrupt the second half of each pair
zs = np.array([[1 + 0j, 0j, 0j, 0j]])
ths = np.full((1, 2), np.pi / 3)
phs = np.zeros((1, 2))
gs = givens(zs, ths, phs, 0, op)
ck('givens reads both old values',
   abs(gs[0, 0] - np.cos(np.pi / 3)) < 1e-15 and abs(gs[0, 1] + np.sin(np.pi / 3)) < 1e-15,
   str(gs))

# phase gate preserves magnitude elementwise
z = rng.normal(size=(2, 16)) + 1j * rng.normal(size=(2, 16))
a = rng.uniform(-np.pi, np.pi, (2, 16))
ck('phase gate magnitude', np.allclose(np.abs(z * np.exp(1j * a)), np.abs(z), atol=1e-14))

# a full update preserves the norm with no renormalization anywhere
m = small()
z0 = rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))
z0 = z0 / np.sqrt((np.abs(z0) ** 2).sum(1, keepdims=True))
zu, _ = m.update(z0, rng.normal(size=(4, 3)))
e = np.abs((np.abs(zu) ** 2).sum(1) - 1).max()
ck('update norm preserved', e < 1e-13, '{:.2e}'.format(e))

# 10,000 fixed-angle gates, float64 drift
zd = z0[:1].copy()
th = rng.uniform(-np.pi, np.pi, (1, 2))
ph = rng.uniform(-np.pi, np.pi, (1, 2))
for i in range(10000):
    zd = givens(zd, th, ph, i & 1, op)
drift = abs((np.abs(zd) ** 2).sum() - 1)
ck('10k-gate drift', drift < 1e-12, '{:.2e}'.format(drift))

# ---------------------------------------------------------------- A11
m = small()
tok = np.array([[1, 2, 3, 4], [1, 2, 0, 0]])
base = m.forward(tok)
for gamma in (0.3, 1.0, -2.5):
    st = np.broadcast_to(m.parameters['z_init'], (2, 4)) * np.exp(1j * gamma)
    rot = m.forward(tok, initial=st)
    tag = 'g={}'.format(gamma)
    ck('global-phase prob invariance ' + tag,
       np.allclose(rot['probabilities'], base['probabilities'], atol=1e-13),
       '{:.2e}'.format(np.abs(rot['probabilities'] - base['probabilities']).max()))
    ck('global-phase state equivariance ' + tag,
       np.allclose(rot['state'], base['state'] * np.exp(1j * gamma), atol=1e-13))
    ck('global-phase angles unchanged ' + tag,
       np.allclose(rot['angles'][0], base['angles'][0], atol=1e-13))

zf = rng.normal(size=(1, 8)) + 1j * rng.normal(size=(1, 8))
ck('features global-phase invariant',
   np.allclose(features(zf * np.exp(1j * 0.7), op), features(zf, op), atol=1e-13))
zr = zf.copy()
zr[0, 3] = zr[0, 3] * np.exp(1j * 0.7)
ck('features relative-phase sensitive',
   not np.allclose(features(zr, op), features(zf, op), atol=1e-6))
nb = np.conj(zf) * np.roll(zf, -1, 1)
want = np.concatenate([np.abs(zf) ** 2, nb.real, nb.imag], axis=1)
ck('features match doc formula', np.allclose(features(zf, op), want, atol=1e-15))

# INTERFERENCE.md constructed case: squared amplitude is 1 + cos(delta)
for delta in (0.0, np.pi / 2, np.pi):
    zc = np.array([1, np.exp(1j * delta)]) / np.sqrt(2)
    row = np.array([1, 1]) / np.sqrt(2)
    ck('interference delta={:.2f}'.format(delta),
       abs(abs(zc @ row) ** 2 * 2 - (1 + np.cos(delta))) < 1e-14)

# ---------------------------------------------------------------- A12
m = small()
pm = PairedRealModel(m)
tgt = np.array([0, 2])
rc = m.forward(tok, tgt, backward=True)
rp = pm.forward(tok, tgt, backward=True)
ck('paired loss agrees', abs(rc['loss'] - rp['loss']) < 1e-13,
   '{:.2e}'.format(abs(rc['loss'] - rp['loss'])))
ck('paired probabilities agree',
   np.allclose(rc['probabilities'], rp['probabilities'], atol=1e-14))
ck('paired state agrees',
   np.allclose(np.stack([rc['state'].real, rc['state'].imag], -1), rp['state'], atol=1e-13))
for name, g in rc['gradients'].items():
    gp = rp['gradients'][name]
    if np.iscomplexobj(g):
        gp = gp[..., 0] + 1j * gp[..., 1]
    d = np.abs(g - gp).max()
    ck('paired grad ' + name, d < 1e-12, '{:.2e}'.format(d))
ck('paired model holds no complex parameter',
   not any(np.iscomplexobj(v) for v in pm.parameters.values()))
ck('paired state is real', not np.iscomplexobj(rp['state']))

# ----------------------------------------------- finite differences (A06/A12)
def loss_of(model, params):
    keep = model.parameters
    model.parameters = params
    try:
        return model.forward(tok, tgt)['loss']
    finally:
        model.parameters = keep


worst = {}
rng2 = np.random.default_rng(3)
for name, val in m.parameters.items():
    p = {k: v.copy() for k, v in m.parameters.items()}
    flat = p[name].ravel()
    picks = rng2.choice(flat.size, size=min(6, flat.size), replace=False)
    err = 0.0
    for i in picks:
        parts = (1.0, 1j) if np.iscomplexobj(flat) else (1.0,)
        for part in parts:
            h = 1e-6
            o = flat[i]
            flat[i] = o + h * part
            lp = loss_of(m, p)
            flat[i] = o - h * part
            lm = loss_of(m, p)
            flat[i] = o
            fd = (lp - lm) / (2 * h)
            an = rc['gradients'][name].ravel()[i]
            an = an.real if part == 1.0 else an.imag
            err = max(err, abs(fd - an) / (1 + abs(fd)))
    worst[name] = err
    ck('FD grad ' + name, err < 2e-7, 'rel {:.2e}'.format(err))

emb = rng2.normal(0, 0.3, (2, 4, 3))
r2 = m.forward(tok, tgt, embeddings=emb, backward=True)
err = 0.0
for _ in range(10):
    b = int(rng2.integers(2))
    t = int(rng2.integers(4))
    e3 = int(rng2.integers(3))
    if tok[b, t] == 0:
        ck('PAD embedding grad is zero', r2['input_embeddings'][b, t, e3] == 0.0)
        continue
    h = 1e-6
    o = emb[b, t, e3]
    emb[b, t, e3] = o + h
    lp = m.forward(tok, tgt, embeddings=emb)['loss']
    emb[b, t, e3] = o - h
    lm = m.forward(tok, tgt, embeddings=emb)['loss']
    emb[b, t, e3] = o
    err = max(err, abs((lp - lm) / (2 * h) - r2['input_embeddings'][b, t, e3]))
ck('FD input embeddings', err < 2e-7, '{:.2e}'.format(err))

# ---------------------------------------------------------- masks and counts
m2 = small()
long = np.array([[1, 2, 3, 4]])
padded = np.array([[1, 2, 3, 4, 0, 0]])
ck('PAD leaves state unchanged',
   np.allclose(m2.forward(long)['state'], m2.forward(padded)['state'], atol=1e-14))
ck('PAD contributes no controller gradient',
   np.allclose(m2.forward(long, np.array([1]), backward=True)['gradients']['W1'],
               m2.forward(padded, np.array([1]), backward=True)['gradients']['W1'],
               atol=1e-14))
b2 = m2.forward(np.array([[1, 2, 3, 4], [4, 3, 2, 1]]))
ck('batch independence',
   np.allclose(b2['state'][0], m2.forward(long)['state'][0], atol=1e-14))
for K in (0, 1, 4, 8):
    mk = PhaseModel(Config(input_vocab=5, output_vocab=3, D=4, E=3, H=6, K=K), seed=7)
    r = mk.forward(long)
    ck('K={} step count'.format(K),
       len(r['trajectory']) == 4 + K + 1 and len(r['angles']) == 4 + K)

# ------------------------------------------------------------------ readout
m3 = small()
r = m3.forward(tok)
ck('probabilities sum to one', np.allclose(r['probabilities'].sum(1), 1.0, atol=1e-14))
ck('log probabilities finite', np.isfinite(r['log_probabilities']).all())

zzero = np.zeros((1, 4), dtype=complex)
zzero[0, 0] = 1.0
mz = small()
mz.parameters['M'] = np.zeros((3, 4), dtype=complex)
rz = mz.forward(np.array([[1]]), initial=zzero)
ck('all-zero amplitude gives uniform', np.allclose(rz['probabilities'], 1 / 3, atol=1e-12))
ck('all-zero amplitude stays finite', np.isfinite(rz['log_probabilities']).all())

mn = small()
mn.parameters['M'] = mn.parameters['M'] * 1e-160
rn = mn.forward(np.array([[1]]), initial=zzero)
ck('near-zero amplitude finite', np.isfinite(rn['log_probabilities']).all())

# ------------------------------------------------------------------ rejections
rejects('zero initial state', lambda: m.forward(tok, initial=np.zeros((2, 4), dtype=complex)))
rejects('nonfinite initial state',
        lambda: m.forward(tok, initial=np.full((2, 4), np.nan, dtype=complex)))
rejects('token out of vocabulary', lambda: m.forward(np.array([[99]])))
rejects('negative token', lambda: m.forward(np.array([[-1]])))
rejects('target out of range', lambda: m.forward(tok, np.array([0, 99])))
rejects('odd D in config', lambda: Config(D=7))
rejects('nonpositive epsilon', lambda: Config(epsilon=0.0))
rejects('wrong initial shape', lambda: m.forward(tok, initial=np.zeros((2, 9), dtype=complex)))
rejects('float tokens', lambda: m.forward(np.array([[1.0, 2.0]])))

print('\n{} checks passed, {} failed'.format(ok, fail))
print('worst FD relative error: ' +
      ', '.join('{} {:.1e}'.format(k, v) for k, v in worst.items()))
sys.exit(1 if fail else 0)
