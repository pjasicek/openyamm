#!/usr/bin/env python3
"""Best staff position in the right fist (mm9_greenman): at several clip keys the hand's vertices (dominant joint the R
hand or an R finger) and the staff axis (principal axis of the Bone01 vertices) are taken into the R hand bone's frame
(the staff is rigid there); a shift of the axis perpendicular to itself is searched on a grid (LIM, 2 mm) round GUESS,
minimising the worst penetration of hand vertices into a cylinder of radius R round the shifted axis over all keys.
Prints the shift in the hand frame (add it to staff_follow.py --offset). Usage: [GUESS=x,y,z] grip_solve.py <unmirrored glb> <R> clip@t ..."""
import os, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); R0 = float(sys.argv[2]); names = [n.get('name') for n in m.glb.json['nodes']]
LIM = float(os.environ.get('LIM', '0.04'))
GUESS = np.array([float(x) for x in os.environ.get('GUESS', '0,0,0').split(',')])
keys = ('R Hand', 'R Thumb', 'R Index', 'R Middle', 'R Ring', 'R Pinky')
data = []
for spec in sys.argv[3:]:
    clip, t = spec.split('@'); W = m.world(m.sample(clip, float(t))); posed = m.skinned_positions(W)
    pts, dom = [], []
    for pr, (p, _) in zip(m.primitives, posed):
        if not pr['skinned']: continue
        pts.append(p); dom += [names[m.joints[j]] for j in pr['joints'][np.arange(len(p)), np.argmax(pr['weights'], 1)]]
    pts = np.concatenate(pts); dom = np.array(dom)
    hi = names.index('Bip01 R Hand'); M = W[hi]; Rm = M[:3, :3] / np.linalg.norm(M[:3, :3], axis=0); o = M[:3, 3]
    st = (pts[dom == 'Bone01'] - o) @ Rm; c = st.mean(0); ax = np.linalg.svd(st - c)[2][0]
    hv = (pts[np.array([any(k in d for k in keys) for d in dom])] - o) @ Rm
    data.append((hv, c, ax))
hv0, c0, ax0 = data[0]
e1 = np.cross(ax0, [1.0, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(ax0, e1)
g = np.arange(-LIM, LIM + 1e-6, 0.002)
best = (9, None)
for a in g:
    for b in g:
        s = GUESS + e1 * a + e2 * b
        worst = 0
        for hv, c, ax in data:
            rel = hv - c - s; rel -= np.outer(rel @ ax, ax)
            worst = max(worst, R0 - np.linalg.norm(rel, axis=1).min())
        if worst < best[0]:
            best = (worst, s)
worst0 = max(R0 - np.linalg.norm((hv - c) - np.outer((hv - c) @ ax, ax), axis=1).min() for hv, c, ax in data)
print('GRIPSOLVE R %.3f worst penetration %.3f m (current %.3f) shift hand frame %s' % (R0, best[0], worst0, np.round(best[1], 3)))
