#!/usr/bin/env python3
"""Clamp a hand's bend at the wrist inside clips (Scholar Fidget: MM9 folds the left hand back 114 deg; on our hand the skin round the wrist
then tore open into a dark wedge and the fingers went back into the sleeve). The hand's rotation relative to its bind (local) is limited to MAX
degrees (shortest-arc slerp toward the bind), smoothly: angles above KNEE are compressed toward MAX. Other channels unchanged.
Args: <in> <out> <clip:side:max:knee> ...   (Bip01 names)"""
import sys
import numpy as np
from pygltflib import GLTF2
IN, OUT = sys.argv[1:3]
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
def qmul(p, q):
    x1, y1, z1, w1 = p.T; x2, y2, z2, w2 = q.T
    return np.c_[w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]
def conj(q): return q * [-1, -1, -1, 1]
for spec in sys.argv[3:]:
    clip, s, mx, knee = spec.split(':'); mx, knee = np.radians(float(mx)), np.radians(float(knee))
    idx = names.index(f'Bip01 {s} Hand'); qb = np.array(g.nodes[idx].rotation or [0, 0, 0, 1], float)
    an = next(a for a in g.animations if a.name == clip)
    for c in an.channels:
        if c.target.node != idx or c.target.path != 'rotation': continue
        x = g.accessors[an.samplers[c.sampler].output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
        Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).astype(float)
        R = qmul(np.tile(conj(qb), (len(Q), 1)), Q); R *= np.sign(R[:, 3:4] + 1e-12)
        th = 2 * np.arccos(np.clip(R[:, 3], -1, 1)); ax = R[:, :3] / np.maximum(np.linalg.norm(R[:, :3], axis=1, keepdims=True), 1e-12)
        th2 = np.where(th > knee, knee + (mx - knee) * np.tanh((th - knee) / max(mx - knee, 1e-6)), th)
        R2 = np.c_[ax * np.sin(th2 / 2)[:, None], np.cos(th2 / 2)]
        Q2 = qmul(np.tile(qb, (len(Q), 1)), R2)
        blob[o:o + Q2.size * 4] = Q2.astype('f4').tobytes()
        print('WRISTCLAMP', clip, s, 'max bend before', round(float(np.degrees(th.max())), 1), 'after', round(float(np.degrees(th2.max())), 1))
g.set_binary_blob(bytes(blob)); g.save(OUT)
