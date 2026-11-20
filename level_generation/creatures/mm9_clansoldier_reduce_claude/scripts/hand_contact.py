#!/usr/bin/env python3
"""Body faces the hands and forearms touch (after mm9_monk_reduce_claude/scripts/hand_contact.py): the first chart-guarded step
(mp45 before this set) pushed the arm/hand gate up (Fidget2 R 0.9 -> 2.7 cm, Standing L 0 -> 1.0 cm, DeadStatic L 49 frames), the
cut coat/skirt/sash under the resting hands. Every installed LOD0 face that is not on an arm (vertices dominated by that side's
Forearm/Hand/finger joints) or a weapon, whose posed centroid comes within R m of a posed arm vertex in any frame (24 fps) of every
clip, mirrored across x (the model is symmetric), is added to the keep set. GLB face order = work/mesh_in.npz order.
Usage: hand_contact.py <base keep .npy> <out .npy>   (env R, default 0.03)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.03'))
m = Model(Glb(str(HERE / 'before' / 'mm9_clansoldier.glb'))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
PR = [p for p in m.primitives if p['node'] == m.primitives[0]['node']][:4]
off = np.cumsum([0] + [len(p['positions']) for p in PR])
T = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, off)])
dom = np.concatenate([np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]) for p in PR])
lab = np.load(HERE / 'work' / 'face_labels.npz'); mat = lab['mat']
hits = np.zeros(len(T), bool)
for s in 'LR':
    arm = np.array([d.startswith(f'Bip01 {s} ') and any(k in d for k in ('Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')) for d in dom])
    av = np.flatnonzero(arm); target = ~arm[T].any(1) & (mat != 3)
    for c in m.clips:
        for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 24):
            P = np.vstack([sp[0] for sp in m.skinned_positions(m.world(m.sample(c, float(t))))[:4]])
            d, _ = cKDTree(P[av]).query(P[T].mean(1), distance_upper_bound=R)
            hits |= target & (d < R)
print('contact faces (installed LOD0)', int(hits.sum()))
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']; fc = V[F].mean(1)
mir = cKDTree(fc).query(fc[hits] * [-1, 1, 1])[1]
hits[mir] = True
keep = np.load(sys.argv[1]).astype(bool); n0 = int(keep.sum())
keep |= hits & ~lab['lining']
np.save(sys.argv[2], keep)
print('mirrored', int(hits.sum()), 'KEEP', n0, '->', int(keep.sum()), 'by part', {int(p): int((hits & ~np.load(sys.argv[1]).astype(bool) & (lab['part'] == p)).sum()) for p in np.unique(lab['part'])})
