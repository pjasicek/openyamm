#!/usr/bin/env python3
"""Floor contact of the dying clips: source vertices (installed LOD0, glb_pose skinning at 30 fps) that come within NEAR m of the
clip frame's lowest point in Death, Death2 and Dead, mapped to work/mesh_in.npz by bind position; the faces touching them are kept
exactly (the d80 corpse went 4 mm lower in Death on its cut back/buttocks; the creature's floor pass lifted the installed corpse
onto the floor). Usage: floor_keep.py <base keep .npy> <out .npy>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
NEAR = float(os.environ.get('NEAR', .008))
m = Model(Glb(HERE / 'before' / 'mm9_trellborg.glb'))
P = [p for p in m.primitives if p['node'] == m.primitives[0]['node'] and p['skinned']][:3]
X0 = np.vstack([p['positions'] for p in P]); low = np.zeros(len(X0), bool)
for clip in ('Death', 'Death2', 'Dead'):
    for t in np.arange(0, max(m.clip_times(clip)) + 1e-6, 1 / 30):
        Y = np.vstack([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(clip, float(t))))) if k < len(P)])
        low |= Y[:, 1] < Y[:, 1].min() + NEAR
d = np.load(HERE / 'work/mesh_in.npz'); V, F = d['verts'], d['faces']
G = X0[:, [0, 2, 1]] * [1, -1, 1]
off = np.median(V, 0) - np.median(G, 0)
for _ in range(5):
    dist, nn = cKDTree(V).query(G + off); off += np.median(V[nn] - (G + off), 0)
dist, nn = cKDTree(V).query(G[low] + off)
print('low source vertices', int(low.sum()), 'mapped, max distance', float(dist.max()))
lv = np.zeros(len(V), bool); lv[nn[dist < 1e-4]] = True
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= lv[F].any(1)
np.save(sys.argv[2], keep); print('FLOORKEEP', n0, '->', int(keep.sum()))
