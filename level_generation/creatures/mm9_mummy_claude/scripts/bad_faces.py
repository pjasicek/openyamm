#!/usr/bin/env python3
"""Where the collapsed faces are: for a clip and time, list bad faces (bind position, area ratio, flip) by region. Args: <glb> <clip> <t> <region substring>"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); clip, t, sub = sys.argv[2], float(sys.argv[3]), sys.argv[4]
doc = m.glb.json; names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
pr = m.primitives[0]; rest = np.asarray(pr['positions'], float); T = pr['triangles'].reshape(-1, 3)
J, W = pr['joints'], pr['weights']
fw = np.zeros((len(T), len(names)))
for k in range(4):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1)
w = m.world(m.sample(clip, t)); P = m.skinned_positions(w)[0][0]
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); n, a = tri(P)
pal = w[m.joints] @ m.inverse_binds; nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
bad = (a0 > 1e-9) & ((a < .2 * a0) | (d < 0))
print('bad', bad.sum(), 'a0 median of all', np.median(a0))
for f in np.where(bad)[0]:
    nm = names[dom[f]]
    if sub in nm:
        c = rest[T[f]].mean(0); print(nm, 'bind', c.round(3), 'area', round(a[f] / a0[f], 2), 'dot', round(d[f], 2), 'a0', round(a0[f] * 1e4, 2))
