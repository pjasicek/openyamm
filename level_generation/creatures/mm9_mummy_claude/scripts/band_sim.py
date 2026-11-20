#!/usr/bin/env python3
"""The long band as a rope: MM9 keys its chain (Bone04-08) by hand, stiff and with the tip drifting off the forearm; on our thicker body it cut the thigh and folded. Here it is solved on the 30 fps keys: a chain of particles
pinned at the waist (rigid on Spine1) and on the right forearm, under gravity, kept out of capsules round the thighs, calves and torso, loops simulated three cycles with the seam spread, one-shots starting from Standing, trajectories low-passed.
Knots drive Bone04..Bone08 and the two helpers by rotation + translation channels, ribbon frames by parallel transport, so the strip has no twist. Args: <in glb> <out glb>"""
import sys, json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
import strips
IN, OUT = sys.argv[1:3]
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
ibm_list = m.inverse_binds; jn = [names[j] for j in m.joints]
parent = {c: i for i, n in enumerate(doc['nodes']) for c in n.get('children', [])}
strips.refine_band()
S = strips.STRIPS['band']; K = np.array(S['k'], float); BN = S['b']     # bind space = MM9 raw glTF
NP = 25                                                                 # particles
LEN = 0.86
tt = np.linspace(0, 1, NP)
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(K, axis=0), axis=1))]
knot_t = L / L[-1]
rest = LEN * L[-1] / (NP - 1)
print('band bind length', L[-1], 'rope', LEN * L[-1])
Sj = {b: np.linalg.inv(ibm_list[jn.index(b)]) for b in BN}
def pinned(w):
    """world positions of the two pins in this pose"""
    a = w[ix['Bip01 Spine1']] @ ibm_list[jn.index('XstripRoot')] @ np.r_[K[0], 1]
    b = w[ix['Bip01 R Forearm']] @ ibm_list[jn.index('XstripTip')] @ np.r_[K[-1], 1]
    return a[:3], b[:3]
def capsules(w):
    C = []
    p = lambda n: w[ix[n]][:3, 3]
    for s in 'LR':
        C.append((p(f'Bip01 {s} Thigh'), p(f'Bip01 {s} Calf'), 0.145, 0.095))
        C.append((p(f'Bip01 {s} Calf'), p(f'Bip01 {s} Foot'), 0.095, 0.07))
    C.append((p('Bip01 Pelvis'), p('Bip01 Spine2'), 0.195, 0.15))
    C.append((p('Bip01 Spine2'), p('Bip01 Neck'), 0.16, 0.13))
    return C
def collide(x, C):
    for a, b, ra, rb in C:
        ab = b - a; u = np.clip((x - a) @ ab / (ab @ ab), 0, 1)
        q = a + u[:, None] * ab; d = x - q; n = np.linalg.norm(d, axis=1); r = ra + (rb - ra) * u
        ins = n < r
        x[ins] = q[ins] + d[ins] / np.maximum(n[ins, None], 1e-6) * r[ins, None]
    x[x[:, 1] < 0.015, 1] = 0.015
def step(x, xp, a, b, C, dt, n_sub=3):
    h = dt / n_sub
    for s in range(n_sub):
        v = (x - xp) * 0.96
        xp = x.copy()
        x = x + v
        x[:, 1] -= 9.8 * h * h
        x[0], x[-1] = a, b
        for it in range(14):
            d = x[1:] - x[:-1]; n = np.linalg.norm(d, axis=1, keepdims=True); c = (n - rest) / np.maximum(n, 1e-6) * d * 0.5
            x[:-1] += c; x[1:] -= c
            d2 = x[2:] - x[:-2]; n2 = np.linalg.norm(d2, axis=1, keepdims=True); short = (n2 < 1.62 * rest)[:, 0]
            if short.any():                  # bending stiffness: no corner tighter than about 110 deg between particles
                c2 = ((n2 - 1.62 * rest) / np.maximum(n2, 1e-6) * d2 * 0.25)[short]
                ii = np.where(short)[0]
                x[ii] += c2; x[ii + 2] -= c2
            x[0], x[-1] = a, b
        collide(x[1:-1], C) if False else None
        y = x[1:-1].copy(); collide(y, C); x[1:-1] = y
    return x, xp
def pose_seq(clip, ts):
    W = [m.world(m.sample(clip, float(t))) for t in ts]
    return W
DUR = {a['name']: m.clip_times(a['name']) for a in doc['animations']}
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
LOOPS = ('Standing', 'Walking', 'Running', 'Backpedal', 'BackpedalRun')   # the last two: 2026-10-31 dropped-clip pass
# initial rope: straight between the pins of the Standing start, then relaxed
Ws = pose_seq('Standing', np.arange(0, DUR['Standing'][-1], 1 / 30))
a, b = pinned(Ws[0]); x = a + np.outer(tt, b - a) ; x[:, 1] -= np.sin(tt * np.pi) * 0.3
xp = x.copy()
for k in range(240):
    a, b = pinned(Ws[k % len(Ws)]); x, xp = step(x, xp, a, b, capsules(Ws[k % len(Ws)]), 1 / 30)
stand_state = (x.copy(), xp.copy())
res = {}
BOUND = {}
T0 = {}
for an in g.animations:
    name = an.name
    dur = float(DUR[name][-1])
    ts = np.linspace(0, dur, max(int(round(dur * 30)) + 1, 2)) if name != 'Dead' else None
    if name in ('Dead', 'Dead2'):
        continue
    W = pose_seq(name, ts); n = len(ts)
    if name in LOOPS:
        x, xp = stand_state[0].copy(), stand_state[1].copy()
        for c in range(3):
            X = []
            for k in range(n):
                a, b = pinned(W[k]); x, xp = step(x, xp, a, b, capsules(W[k]), 1 / 30); X.append(x.copy())
        X = np.array(X)
        r = (X[0] - X[-1])
        X = X + r[None] * np.linspace(0, 1, n)[:, None, None]
        X = gaussian_filter1d(X, 1.2, axis=0, mode='wrap')
        X[:, 0] = [pinned(w)[0] for w in W]; X[:, -1] = [pinned(w)[1] for w in W]
    else:
        x, xp = stand_state[0].copy(), stand_state[1].copy()
        X = []
        for k in range(n):
            a, b = pinned(W[k]); x, xp = step(x, xp, a, b, capsules(W[k]), 1 / 30); X.append(x.copy())
        if name == 'Coffin2':                         # a held pose (2026-10-31): the rope settles first, then holds still
            for k in range(240):
                a, b = pinned(W[-1]); x, xp = step(x, xp, a, b, capsules(W[-1]), 1 / 30)
            X = [x.copy()] * n
        X = np.array(X); X = gaussian_filter1d(X, 1.0, axis=0, mode='nearest')
        X[:, 0] = [pinned(w)[0] for w in W]; X[:, -1] = [pinned(w)[1] for w in W]
    for it_ in range(2):                              # along the chain: a low-pass, pins kept
        X[:, 1:-1] = 0.5 * X[:, 1:-1] + 0.25 * (X[:, :-2] + X[:, 2:])
    res[name] = (ts, X, W)
# Dead: Death's end state held
if 'Death' in res:
    res['Dead'] = (np.array([0.0, 1.0]), np.repeat(res['Death'][1][-1:], 2, 0), [res['Death'][2][-1]] * 2)
if 'Death2' in res:                                   # Dead2 (static_die2's corpse, 2026-10-31): Death2's end state held
    res['Dead2'] = (np.array([0.0, 1.0]), np.repeat(res['Death2'][1][-1:], 2, 0), [res['Death2'][2][-1]] * 2)
# bind frames at the knots
Tb = np.gradient(K, axis=0); Tb /= np.linalg.norm(Tb, axis=1, keepdims=True)
Nb = np.array([0, 0, 1.0]) - Tb * (Tb @ np.array([0, 0, 1.0]))[:, None]; Nb /= np.linalg.norm(Nb, axis=1, keepdims=True); Bb = np.cross(Tb, Nb)
kidx = np.clip(np.round(knot_t * (NP - 1)).astype(int), 0, NP - 1)
for an in g.animations:
    ts, X, W = res[an.name]
    n = len(ts)
    keep = [c for c in an.channels if names[c.target.node] not in BN]
    an.channels = keep
    inp = add(ts[:, None], 'SCALAR'); g.accessors[inp].min = [float(ts[0])]; g.accessors[inp].max = [float(ts[-1])]
    outT = {b: np.zeros((n, 3)) for b in BN}; outQ = {b: np.zeros((n, 4)) for b in BN}
    for k in range(n):
        x = X[k]
        Tan = np.gradient(x, axis=0); Tan /= np.maximum(np.linalg.norm(Tan, axis=1, keepdims=True), 1e-6)
        Ws_ = W[k]
        # normal at the root: the waist bone's take of the bind normal, then transported
        R0 = (Ws_[ix['Bip01 Spine1']] @ ibm_list[jn.index('XstripRoot')])[:3, :3]
        N = R0 @ Nb[0]; Nall = np.zeros_like(x)
        for i in range(NP):
            N = N - Tan[i] * (N @ Tan[i]); N /= max(np.linalg.norm(N), 1e-6); Nall[i] = N
        for bi, b in enumerate(BN):
            i = kidx[bi]; Tw = Tan[i]; Nw = Nall[i]; Bw = np.cross(Tw, Nw)
            F1 = np.c_[Tw, Nw, Bw]; F0 = np.c_[Tb[bi], Nb[bi], Bb[bi]]
            Q = F1 @ F0.T
            A = np.eye(4); A[:3, :3] = Q; A[:3, 3] = x[i] - Q @ K[bi]
            Wn = A @ Sj[b]
            W[k] = W[k]                                 # bones below in the chain use the new parents
            Ws_[ix[b]] = Wn
        for b in BN:
            nd = ix[b]; Wn = Ws_[nd]; L_ = np.linalg.inv(Ws_[parent[nd]]) @ Wn
            outT[b][k] = L_[:3, 3]; outQ[b][k] = matrix_quaternion(L_[:3, :3])
    for b in BN:
        q = outQ[b]
        for k in range(1, n):
            if q[k] @ q[k - 1] < 0: q[k] *= -1
        s1 = len(an.samplers); an.samplers.append(AnimationSampler(input=inp, output=add(outT[b], 'VEC3'), interpolation='LINEAR'))
        s2 = len(an.samplers); an.samplers.append(AnimationSampler(input=inp, output=add(q, 'VEC4'), interpolation='LINEAR'))
        an.channels.append(AnimationChannel(sampler=s1, target=AnimationChannelTarget(node=ix[b], path='translation')))
        an.channels.append(AnimationChannel(sampler=s2, target=AnimationChannelTarget(node=ix[b], path='rotation')))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('BAND SIM', len(res), 'clips')
