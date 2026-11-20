#!/usr/bin/env python3
"""Skirt faces the thighs press through (the chart-guarded cut of the skirt raised skirt_gate.py's Death from 7.5 to 8.2 cm, at
any skirt ratio up to 0.7; the skirt kept whole gives 7.5 again but costs 650 triangles): every outer skirt face (part 7, not
lining) whose posed centroid comes within R m of a posed leg vertex (Thigh/Calf-dominated) in any frame (24 fps) of CLIPS, mirrored
across x, is added to the keep set (its lining twin follows in mpqem.py). Usage: skirt_contact.py <base keep .npy> <out .npy>"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.03')); CLIPS = os.environ.get('CLIPS', 'Death,Death2,Dead,DeadStatic,Dead2,Running,Cower').split(',')
m = Model(Glb(str(HERE / 'before' / 'mm9_clansoldier.glb'))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
PR = [p for p in m.primitives if p['node'] == m.primitives[0]['node']][:4]
off = np.cumsum([0] + [len(p['positions']) for p in PR])
T = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(PR, off)])
dom = np.concatenate([np.array([jn[p['joints'][v][np.argmax(p['weights'][v])]] for v in range(len(p['positions']))]) for p in PR])
lab = np.load(HERE / 'work' / 'face_labels.npz'); target = (lab['part'] == 7) & ~lab['lining'].astype(bool)
leg = np.flatnonzero([('Thigh' in d or 'Calf' in d) for d in dom])
hits = np.zeros(len(T), bool)
for c in CLIPS:
    for t in np.arange(0, m.clip_times(c)[-1] + 1e-6, 1 / 24):
        P = np.vstack([sp[0] for sp in m.skinned_positions(m.world(m.sample(c, float(t))))[:4]])
        d, _ = cKDTree(P[leg]).query(P[T].mean(1), distance_upper_bound=R)
        hits |= target & (d < R)
d = np.load(HERE / 'work' / 'mesh_in.npz'); fc = d['verts'][d['faces']].mean(1)
hits[cKDTree(fc).query(fc[hits] * [-1, 1, 1])[1]] = True
keep = np.load(sys.argv[1]).astype(bool); n0 = int(keep.sum()); keep |= hits; np.save(sys.argv[2], keep)
print('skirt contact', int(hits.sum()), 'of', int(target.sum()), 'KEEP', n0, '->', int(keep.sum()))
