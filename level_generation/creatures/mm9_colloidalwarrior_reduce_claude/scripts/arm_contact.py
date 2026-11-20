#!/usr/bin/env python3
"""Body faces the forearms and hands touch (arm_hand_gate: AttackMelee2 R forearm depth 0.4 -> 1.0 cm when the belly
under it was decimated, candidate e79): every installed LOD0 face (both sets) not on an arm whose posed centroid comes
within R m of a posed forearm/hand/finger vertex in any 2nd frame of every clip; mapped to work/mesh_in.npz faces by rest
centroid and added to a keep set. Usage: arm_contact.py <base keep .npy> <out .npy>   (env R, default 0.03)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.03'))
m = Model(Glb(str(HERE / 'before' / 'mm9_colloidalwarrior.glb')))
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
ARM = ('Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
prims = [k for k, p in enumerate(m.primitives) if p['node'] == m.primitives[0]['node'] and p['skinned']][:2]
off = np.cumsum([0] + [len(m.primitives[k]['positions']) for k in prims])
T = np.vstack([np.asarray(m.primitives[k]['triangles']).reshape(-1, 3) + off[i] for i, k in enumerate(prims)])
dom = np.concatenate([[jn[m.primitives[k]['joints'][v][np.argmax(m.primitives[k]['weights'][v])]] for v in range(len(m.primitives[k]['positions']))] for k in prims])
arm = np.array([any(a in x for a in ARM) for x in dom])
target = ~arm[T].any(1); hit = np.zeros(len(T), bool)
for c in m.clips:
    for t in m.clip_times(c)[::2]:
        sp = m.skinned_positions(m.world(m.sample(c, t)))
        P = np.concatenate([np.asarray(sp[k][0]) for k in prims])
        d, _ = cKDTree(P[arm]).query(P[T].mean(1), distance_upper_bound=R)
        hit |= target & (d < R)
print('contact faces (installed)', int(hit.sum()))
rest = np.concatenate([np.asarray(m.primitives[k]['positions']) for k in prims])
d = np.load(HERE / 'work' / 'mesh_in.npz'); V, F = d['verts'], d['faces']
gc = rest[T[hit]].mean(1)[:, [0, 2, 1]] * [1, -1, 1]
gc[:, 2] += V[:, 2].min() - rest[:, 1].min()   # the mesh sits under the rig: Blender mesh-local z = glTF y - 1.013
dist, _ = cKDTree(gc).query(V[F].mean(1))
keep = np.load(sys.argv[1]).copy(); n0 = int(keep.sum()); keep |= dist < 0.004
np.save(sys.argv[2], keep); print('ARMCONTACT kept', n0, '->', int(keep.sum()))
