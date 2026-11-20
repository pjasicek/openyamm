#!/usr/bin/env python3
"""Robe and belt faces the hands rest on (arm_hand_gate: the hand depth grew 0.1-0.4 cm in Fidget2, SweepFidget, Hit, Hit2
when the robe under the resting hands was decimated, with or without the hands cut): every source face of the installed
LOD0 whose posed centroid comes within R m of a posed hand vertex in any frame of the listed clips, mirrored, added to a keep
set. Usage: hand_contact.py <base keep .npy> <out .npy>   (env R, default 0.05; CLIPS)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.05'))
CLIPS = os.environ.get('CLIPS', 'Standing,Fidget,Fidget2,Hit,Hit2,AttackRanged,AttackRanged3,AttackMelee,SweepFidget,Death,Death2,Pray').split(',')
m = Model(Glb(str(HERE / 'before' / 'mm9_monk.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz'); names = [str(x) for x in g['names']]
T = np.asarray(m.primitives[0]['triangles']).reshape(-1, 3); nA = len(T)
part = g['part'][:nA]
hand_v = np.unique(T[part == names.index('hands')]); target = np.isin(part, [names.index('robe'), names.index('belt')])
hit = np.zeros(nA, bool)
for c in CLIPS:
    for t in m.clip_times(c)[::2]:
        P = np.asarray(m.skinned_positions(m.world(m.sample(c, t)))[0][0])
        d, _ = cKDTree(P[hand_v]).query(P[T].mean(1), distance_upper_bound=R)
        hit |= target & (d < R)
print('contact faces (installed Monk_A)', int(hit.sum()))
# installed faces -> mesh_in faces (Blender frame), mirrored
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
gc = g['cen'][:nA][hit][:, [0, 2, 1]] * [1, -1, 1]
gc = np.vstack([gc, gc * [-1, 1, 1]])
dist, _ = cKDTree(gc).query(V[F].mean(1))
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= dist < 0.004
np.save(sys.argv[2], keep); print('HANDCONTACT kept', n0, '->', int(keep.sum()))
