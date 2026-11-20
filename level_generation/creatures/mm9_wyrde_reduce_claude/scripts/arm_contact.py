#!/usr/bin/env python3
"""Cloth faces the arms come close to in any pose (contact keep set, after the Clan Soldier's hands-on-body sets): the installed
GLB posed over every clip at HZ; for each mantle / dress / skirt face (not on an arm) the smallest distance from its centroid and
corners to any arm vertex (sleeve and hand vertices dominated by UpperArm, Forearm, the half-joint helpers or the hand). Faces
within R m in some pose -> work/arm_contact.npy (bool per GLB face, glb_parts order). Usage: arm_contact.py [R] [HZ]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.02; HZ = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
m = Model(Glb(str(HERE / 'before' / 'mm9_wyrde.glb'))); names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part']
pr = m.primitives[0]; T = pr['triangles']; nb = len(T)
dom = np.array([jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))])
armk = ('UpperArm', 'Forearm', 'Hand', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
armv = np.flatnonzero([any(k in d for k in armk) for d in dom])
armface = np.isin(T, armv).any(1)
cand = np.flatnonzero(np.isin(part[:nb], (1, 2, 4)) & ~armface)
best = np.full(len(cand), 9.0)
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        X = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
        tree = cKDTree(X[armv])
        pts = np.concatenate([X[T[cand]], X[T[cand]].mean(1, keepdims=True)], 1)       # (f, 4, 3)
        d = tree.query(pts.reshape(-1, 3))[0].reshape(-1, 4).min(1)
        best = np.minimum(best, d)
hit = np.zeros(len(part), bool); hit[cand[best < R]] = True
print('arm vertices', len(armv), 'candidate cloth faces', len(cand), f'within {R} m in some pose', int(hit.sum()),
      'by part', {int(p): int((hit & (part == p)).sum()) for p in (1, 2, 4)})
np.save(HERE / 'work' / 'arm_contact.npy', hit)
