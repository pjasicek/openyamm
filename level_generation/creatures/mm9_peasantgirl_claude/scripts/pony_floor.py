#!/usr/bin/env python3
"""Long hair on the floor (PeasantGirl): in Death and Dead MM9's Ponytail chain lays the hair along the body; ours is 10 cm longer than MM9's,
so the lying corpse put its tip 11 cm under the floor and the floor pass then lifted the whole corpse. Per key, if the lowest hair vertex
(weighted to the Ponytail chain) is under FLOOR, Ponytail1 turns in world space about its joint, about the horizontal axis across the
chain, until that vertex is on the floor (two Newton steps). Args: <in glb> <out glb> [floor y]"""
import sys
from pathlib import Path
import numpy as np
from pygltflib import GLTF2
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
IN, OUT = sys.argv[1:3]; FLOOR = float(sys.argv[3]) if len(sys.argv) > 3 else 0.01
g = GLTF2().load(IN); blob = bytearray(g.binary_blob()); names = [n.name for n in g.nodes]
m = Model(Glb(IN)); jn = [names[j] for j in m.joints]
i1 = names.index('Bip01 Ponytail1'); ip = names.index('Bip01 Head')
pj = [jn.index('Bip01 Ponytail1'), jn.index('Bip01 Ponytail11')]
sel = [np.isin(pr['joints'], pj) & (pr['weights'] > 0.3) for pr in m.primitives]
sel = [s.any(1) for s in sel]
def hair_low(W):
    sp = m.skinned_positions(W); best = (1e9, None)
    for k, s in enumerate(sel):
        if s.any():
            X = sp[k][0][s]; i = np.argmin(X[:, 1])
            if X[i, 1] < best[0]: best = (X[i, 1], X[i])
    return best
def rot(axis, th):
    axis = axis / np.linalg.norm(axis); K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
rep = {}
for an in g.animations:
    if an.name not in ('Death', 'Dead'): continue
    ch = next(c for c in an.channels if c.target.node == i1 and c.target.path == 'rotation')
    s = an.samplers[ch.sampler]; ta = g.accessors[s.input]; tv = g.bufferViews[ta.bufferView]
    ts = np.frombuffer(bytes(blob[(tv.byteOffset or 0) + (ta.byteOffset or 0):(tv.byteOffset or 0) + (ta.byteOffset or 0) + 4 * ta.count]), 'f4')
    x = g.accessors[s.output]; v = g.bufferViews[x.bufferView]; o = (v.byteOffset or 0) + (x.byteOffset or 0)
    Q = np.frombuffer(blob, 'f4', x.count * 4, o).reshape(x.count, 4).copy().astype(float)
    worst = 0.0; fixed = 0
    for k, t in enumerate(ts):
        loc = m.sample(an.name, float(t))
        for it in range(3):
            W = m.world(loc); y, p = hair_low(W)
            if y >= FLOOR - 1e-4: break
            j = W[i1][:3, 3]; r = p - j; worst = min(worst, y)
            axis = np.cross(r, [0, 1.0, 0])                  # turning about it lifts p
            if np.linalg.norm(axis) < 1e-6: break
            L = np.linalg.norm(r - axis / np.linalg.norm(axis) * (r @ axis / np.linalg.norm(axis)))
            th = np.arcsin(np.clip((FLOOR - y) / max(L, 1e-3), -1, 1))
            Rw = rot(axis, th)
            Rp = W[ip][:3, :3]; Rp = Rp / np.linalg.norm(Rp, axis=0)
            Lr = quaternion_matrix(Q[k]); Q[k] = matrix_quaternion(Rp.T @ Rw @ Rp @ Lr)
            loc[i1] = [loc[i1][0], Q[k].copy(), loc[i1][2]]
            fixed += it == 0
    for k in range(1, len(Q)):
        if Q[k] @ Q[k - 1] < 0: Q[k] = -Q[k]
    blob[o:o + Q.size * 4] = Q.astype('f4').tobytes(); rep[an.name] = (round(worst, 3), fixed)
g.set_binary_blob(bytes(blob)); g.save(OUT); print('PONY floor (lowest hair before, keys fixed)', rep)
