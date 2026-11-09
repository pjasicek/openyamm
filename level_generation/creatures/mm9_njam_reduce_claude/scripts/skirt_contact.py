#!/usr/bin/env python3
"""Skirt faces the legs come near (skirt gate, a50: CowerLoop 0.6 -> 6.5 cm when the cut skirt's larger faces passed a crotch
vertex): skirt outer faces (part 7, not lining or cap) whose posed centroid is within R m of a leg-dominated vertex (Thigh/Calf
weight > 0.5) in any pose of every clip at HZ. Writes work/skirt_contact.npy (per GLB LOD0 face, glb_parts order).
Usage: [R=0.03 HZ=10] skirt_contact.py"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.03')); HZ = float(os.environ.get('HZ', '10'))
m = Model(Glb(str(HERE / 'before' / 'mm9_njam.glb'))); g = np.load(HERE / 'work' / 'glb_parts.npz')
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
PR = m.primitives[:3]; nf = [len(np.asarray(p['triangles']).reshape(-1, 3)) for p in PR]; off = np.cumsum([0] + nf)
leg = [i for i, n in enumerate(jn) if 'Thigh' in n or 'Calf' in n]
lv = [((np.isin(p['joints'], leg) * p['weights']).sum(1) > 0.5) for p in PR]
T1 = np.asarray(PR[1]['triangles']).reshape(-1, 3); sl = slice(off[1], off[2])
sk = (g['part'][sl] == 7) & (g['lining'][sl] == 0)
hit = np.zeros(len(T1), bool)
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        P = [x[0] for x in m.skinned_positions(m.world(m.sample(clip, t)))]
        L = np.vstack([P[k][lv[k]] for k in range(3)])
        d, _ = cKDTree(L).query(P[1][T1[sk]].mean(1), distance_upper_bound=R)
        hit[np.flatnonzero(sk)[d < R]] = True
out = np.zeros(off[-1], bool); out[sl] = hit
np.save(HERE / 'work' / 'skirt_contact.npy', out); print('SKIRT contact faces', int(hit.sum()), 'of', int(sk.sum()))
