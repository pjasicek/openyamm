#!/usr/bin/env python3
"""Keys of the half-joint helpers: on the child bone's key times, the helper's skin rotation is half way between the parent side and the child, turning about the child's joint. Args: <in glb> <out glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model, matrix_quaternion
from pygltflib import GLTF2, Accessor, BufferView, AnimationSampler, AnimationChannel, AnimationChannelTarget
from rig_bones import half_pairs
IN, OUT = sys.argv[1:3]
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
def half_rot(R):
    """half of a rotation matrix by its rotation vector"""
    a = np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1))
    if a < 1e-6: return np.eye(3)
    v = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * np.sin(a)) if a < np.pi - 1e-3 else None
    if v is None:
        w, V = np.linalg.eigh((R + R.T) / 2); v = V[:, w.argmax()]
    t = a / 2; K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + np.sin(t) * K + (1 - np.cos(t)) * K @ K
pairs = half_pairs()
for an in g.animations:
    any_ch = next(c for c in an.channels if names[c.target.node] == 'Bip01 Spine')
    tin = an.samplers[any_ch.sampler].input
    a = g.accessors[tin]; bv = g.bufferViews[a.bufferView]
    ts = np.frombuffer(bytes(blob[(bv.byteOffset or 0) + (a.byteOffset or 0):(bv.byteOffset or 0) + (a.byteOffset or 0) + 4 * a.count]), 'f4').copy()
    Ws = [m.world(m.sample(an.name, float(t))) for t in ts]
    hn = {h for h, *_ in pairs}
    an.channels = [c for c in an.channels if names[c.target.node] not in hn]
    for h, c, pn, _ in pairs:
        T = np.zeros((len(ts), 3)); Q = np.zeros((len(ts), 4))
        Bc = np.linalg.inv(ibm[c])
        for k, W in enumerate(Ws):
            Sp = W[ix[pn]] @ ibm[pn]; Sc = W[ix[c]] @ ibm[c]
            Rrel = Sp[:3, :3].T @ Sc[:3, :3]
            Sh = Sp[:3, :3] @ half_rot(Rrel)
            Wh = np.eye(4); Wh[:3, :3] = Sh @ Bc[:3, :3]; Wh[:3, 3] = W[ix[c]][:3, 3]
            L = np.linalg.inv(W[ix[pn]]) @ Wh
            T[k] = L[:3, 3]; Q[k] = matrix_quaternion(L[:3, :3])
        for k in range(1, len(Q)):
            if Q[k] @ Q[k - 1] < 0: Q[k] *= -1
        s1 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(T, 'VEC3'), interpolation='LINEAR'))
        s2 = len(an.samplers); an.samplers.append(AnimationSampler(input=tin, output=add(Q, 'VEC4'), interpolation='LINEAR'))
        an.channels.append(AnimationChannel(sampler=s1, target=AnimationChannelTarget(node=ix[h], path='translation')))
        an.channels.append(AnimationChannel(sampler=s2, target=AnimationChannelTarget(node=ix[h], path='rotation')))
g.buffers[0].byteLength = len(blob); g.set_binary_blob(bytes(blob)); g.save(OUT)
print('HALF keys', len(pairs), 'helpers', len(g.animations), 'clips')
