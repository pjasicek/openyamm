#!/usr/bin/env python3
"""MM9's fingers have two joints; ours three. The bend of MM9's second joint is shared out: second joint 55 %, third the rest, so the fingertip keeps MM9's direction and the finger curls instead of snapping at one knuckle. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
IN, OUT = sys.argv[1:3]
K = 0.55
m = Model(Glb(IN)); doc = m.glb.json; names = [n.get('name') for n in doc['nodes']]; ix = {n: i for i, n in enumerate(names)}
jn = [names[j] for j in m.joints]; ibm = {n: m.inverse_binds[i] for i, n in enumerate(jn)}
g = GLTF2().load(IN); blob = bytearray(g.binary_blob())
def add(arr, typ):
    global blob
    while len(blob) % 4: blob.append(0)
    o = len(blob); d = arr.astype('f4').tobytes(); blob += d
    g.bufferViews.append(BufferView(buffer=0, byteOffset=o, byteLength=len(d)))
    g.accessors.append(Accessor(bufferView=len(g.bufferViews) - 1, componentType=5126, count=len(arr), type=typ))
    return len(g.accessors) - 1
def frac(R, k):
    a = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if a < 1e-6: return np.eye(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(a)) if a < np.pi - 1e-3 else np.linalg.eigh((R + R.T) / 2)[1][:, -1]
    t = a * k; K_ = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(t) * K_ + (1 - np.cos(t)) * K_ @ K_
for an in g.animations:
    ch0 = next(c for c in an.channels if names[c.target.node] == 'Bip01 Pelvis')
    tin = an.samplers[ch0.sampler].input
    a = g.accessors[tin]; bv = g.bufferViews[a.bufferView]
    ts = np.frombuffer(bytes(blob[(bv.byteOffset or 0) + (a.byteOffset or 0):(bv.byteOffset or 0) + (a.byteOffset or 0) + 4 * a.count]), 'f4').copy()
    Ws = [m.world(m.sample(an.name, float(t))) for t in ts]
    work = []
    for s in 'LR':
        for f in range(5):
            work.append((f'Bip01 {s} Finger{f}', f'Bip01 {s} Finger{f}1', f'Bip01 {s} Finger{f}2'))
    edit = {x for w in work for x in w[1:]}
    an.channels = [c for c in an.channels if not (names[c.target.node] in edit and c.target.path == 'rotation')]
    for f0, f1, f2 in work:
        Q1 = np.zeros((len(ts), 4)); Q2 = np.zeros((len(ts), 4))
        for k, W in enumerate(Ws):
            S0 = (W[ix[f0]] @ ibm[f0])[:3, :3]; S1 = (W[ix[f1]] @ ibm[f1])[:3, :3]
            mid = S0 @ frac(S0.T @ S1, K)
            B1 = np.linalg.inv(ibm[f1])[:3, :3]; B2 = np.linalg.inv(ibm[f2])[:3, :3]
            Wm1 = mid @ B1; Wm2 = S1 @ B2
            Q1[k] = matrix_quaternion(W[ix[f0]][:3, :3].T @ Wm1); Q2[k] = matrix_quaternion(Wm1.T @ Wm2)
        for q in (Q1, Q2):
            for k in range(1, len(q)):
                if q[k] @ q[k - 1] < 0: q[k] *= -1
        for nm, q in ((f1, Q1), (f2, Q2)):
            s_ = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(q, 'VEC4'), interpolation='LINEAR'))
            an.channels.append(AnimationChannel(sampler=s_, target=AnimationChannelTarget(node=ix[nm], path='rotation')))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('FINGER keys', len(g.animations), 'clips')
