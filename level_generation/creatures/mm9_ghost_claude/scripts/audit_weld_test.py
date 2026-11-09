#!/usr/bin/env python3
"""Is the audit's hand flag real? Two measurements. (1) Jacket to robe distance at the waist in every clip (they overlap, never welded). (2) A copy of the GLB with one sliver triangle joining jacket and robe, so the audit sees them as one component; hands and cuffs are untouched. If their flags go, the flags came from the unwelded waist, not from a gap at the wrist. Args: in.glb out.glb"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g); doc = g.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
mesh = next(x for x in doc['meshes'] if x.get('name') == 'Ghost')
pi = next(k for k, p in enumerate(mesh['primitives']) if doc['materials'][p['material']]['name'].startswith('Ghost_'))
pr = m.primitives[pi]
# jacket and robe are separate surfaces: label by welded connectivity
key = np.round(pr['positions'], 5)
_, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
par = np.arange(inv.max() + 1)
def find(x):
    while par[x] != x:
        par[x] = par[par[x]]; x = par[x]
    return x
for t in pr['triangles']:
    a_, b_, c_ = find(inv[t[0]]), find(inv[t[1]]), find(inv[t[2]])
    par[b_] = a_; par[c_] = a_
lab = np.array([find(i) for i in inv])
u_, n_ = np.unique(lab, return_counts=True)
big = u_[np.argsort(n_)[::-1][:2]]
A0, B0 = lab == big[0], lab == big[1]
isr, isup = (A0, B0) if pr['positions'][A0, 1].min() < pr['positions'][B0, 1].min() else (B0, A0)
print('components', len(u_), 'robe', isr.sum(), 'jacket', isup.sum())
worst = 0
for a in doc['animations']:
    c = a['name']
    if c == 'Dead':
        continue
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 24):
        P = m.skinned_positions(m.world(m.sample(c, float(t))))[pi][0]
        d = cKDTree(P[isr]).query(P[isup])[0].min()
        s = np.abs(m.world(m.sample(c, float(t)))[m.joints[0]][:3, :3]).max()
        worst = max(worst, d if c != 'Death' else 0)
print('jacket to robe, closest vertices, worst frame of the living clips: %.1f mm' % (worst * 1000))
P = pr['positions']
r = np.nonzero(isr)[0]; u = np.nonzero(isup)[0]
d, j = cKDTree(P[r]).query(P[u]); k = d.argmin()
a, b = u[k], r[j[k]]
c = r[cKDTree(P[r]).query(P[b], k=2)[1][1]]
acc = doc['accessors'][mesh['primitives'][pi]['indices']]
T = g.accessor(mesh['primitives'][pi]['indices']).astype(np.uint32)
new = np.concatenate([T.ravel(), [a, b, c]]).astype(np.uint32)
g.bin += b'\0' * 0 if False else bytes(-len(g.bin) % 4)
doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(g.bin), 'byteLength': new.nbytes})
g.bin += new.tobytes()
doc['accessors'].append({'bufferView': len(doc['bufferViews']) - 1, 'componentType': 5125, 'count': len(new), 'type': 'SCALAR'})
doc['buffers'][0]['byteLength'] = len(g.bin)
mesh['primitives'][pi]['indices'] = len(doc['accessors']) - 1
g.write(sys.argv[2])
print('joined vertices', a, b, 'at', P[a].round(3))
