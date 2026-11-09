#!/usr/bin/env python3
"""Second keep round after the r70 gates (gates_r70 against gates_before): grip wrap pinky 120-135 -> 90 deg (the right
fist's fingers in the 0.75 hand cut), rim face/beard 0.0 -> 2.3 cm in AttackMelee/AttackRanged (beard underside at
the chin, GLB rest (0, 0.936, 0.058), inside the collar front at (0.023, 0.896, 0.101)), blade 2.1 -> 2.3 cm in script
Fidget2 (axe against the folded left forearm). Keeps, on top of work/keep_d_lock.npy: the whole right hand (part 0,
x < 0), voxel skin and beard faces within 5 cm of the two rim points, voxel skin faces that come within 3 cm of an axe
vertex in any Fidget2 key (posed on the installed GLB; mesh_in keeps the GLB face order). -> work/keep_e.npy"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
mi = np.load(HERE / 'work' / 'mesh_in.npz'); L = np.load(HERE / 'work' / 'labels.npz'); part = L['part']
V, T = mi['verts'], mi['faces']; cen = V[T].mean(1)
keep = np.load(HERE / 'work' / 'keep_d_lock.npy').copy(); n0 = int(keep.sum())
rhand = (part == 0) & (cen[:, 0] < 0)
to_mi = lambda p: np.array([p[0], -p[2], p[1] - 0.6358])
near = np.zeros(len(T), bool)
for p in ((0, 0.936, 0.058), (0.023, 0.896, 0.101)):
    near |= np.isin(part, (1, 20)) & (np.linalg.norm(V[T] - to_mi(p), axis=2).min(1) < 0.05)
m = Model(Glb(str(HERE / 'before' / 'mm9_dwarf.glb')))
P = [p['positions'] for p in m.primitives]; TT = [p['triangles'] for p in m.primitives]
off = np.cumsum([0] + [len(p) for p in P]); allT = np.vstack([t + o for t, o in zip(TT, off)])
axe_v = np.unique(allT[part == 30]); skin = np.flatnonzero(part == 1); fore = np.zeros(len(T), bool)
for t in m.clip_times('Fidget2'):
    pos = np.vstack([p for p, _ in m.skinned_positions(m.world(m.sample('Fidget2', t)))])
    d, _ = cKDTree(pos[axe_v]).query(pos[allT[skin]].reshape(-1, 3))
    fore[skin[(d.reshape(-1, 3) < 0.03).any(1)]] = True
keep |= rhand | near | fore
np.save(HERE / 'work' / 'keep_e.npy', keep)
print('KEEP_E right hand', int((rhand & ~np.load(HERE / 'work' / 'keep_d_lock.npy')).sum()), 'rim spot', int(near.sum()), 'forearm/axe', int(fore.sum()), 'total', n0, '->', int(keep.sum()))
