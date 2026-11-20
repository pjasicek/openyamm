#!/usr/bin/env python3
"""Where the collapsed faces of one clip key sit (diagnosis). Args: <glb> <clip> <seconds> [region substring]"""
import sys, re
from pathlib import Path
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); clip, t = sys.argv[2], float(sys.argv[3])
doc = m.glb.json; names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
prims = [p for p in m.primitives if p['skinned']]
offs = np.cumsum([0] + [len(p['positions']) for p in prims])
T = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + offs[i] for i, p in enumerate(prims)])
J = np.vstack([p['joints'] for p in prims]); W = np.vstack([p['weights'] for p in prims])
mg = lambda pz: np.vstack([x[0] for x in pz])
rest = mg(m.skinned_positions(m.world({})))
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3): np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); ok = a0 > 1e-9
w = m.world(m.sample(clip, t)); P = mg(m.skinned_positions(w)); n, a = tri(P)
pal = w[m.joints] @ m.inverse_binds
nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
badA = ok & (a < 0.2 * a0); badF = ok & (d < 0)
print('collapse', badA.sum(), 'flip', badF.sum())
import os, json
if os.environ.get('DUMP'): json.dump({'faces': np.where(badA | badF)[0].tolist(), 'prims': [len(np.asarray(p['triangles']).reshape(-1, 3)) for p in prims]}, open(os.environ['DUMP'], 'w'))
dom = fw.argmax(1); cen = rest[T].mean(1)
want = sys.argv[4] if len(sys.argv) > 4 else ''
for i in np.where(badA | badF)[0]:
    nm = names[dom[i]]
    if want and want not in nm: continue
    print(nm, 'rest', np.round(cen[i], 3), 'area cm2', round(float(a0[i]) * 1e4, 2), 'A' if badA[i] else '', 'F' if badF[i] else '')
