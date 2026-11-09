#!/usr/bin/env python3
"""Where the staff axis passes through the right fist (mm9_greenman): for some clip keys, the fist centre (mean of the
vertices weighted mostly to the R finger bones' first two segments and the R hand bone's front half) and the staff axis
(vertices weighted to Bone01: principal axis), the perpendicular offset of the axis from the fist centre, expressed in the
R hand bone's frame (what staff_follow.py --offset takes, but the opposite sign), and the staff radius there.
Usage: grip_probe.py <glb> [clip@t ...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(Path(sys.argv[1]))); d = m.glb.json
names = [n.get('name') for n in d['nodes']]
specs = sys.argv[2:] or ['Standing@0', 'Walking@0.5', 'Fidget@1.5']
P0 = m.primitives
for spec in specs:
    clip, t = spec.split('@')
    W = m.world(m.sample(clip, float(t)))
    posed = m.skinned_positions(W)
    pts, dom = [], []
    for pr, (p, _) in zip(P0, posed):
        if not pr['skinned']:
            continue
        jn = [names[m.joints[j]] for j in pr['joints'][np.arange(len(p)), np.argmax(pr['weights'], 1)]]
        pts.append(p); dom += jn
    pts = np.concatenate(pts); dom = np.array(dom)
    st = pts[dom == 'Bone01']; c = st.mean(0); ax = np.linalg.svd(st - c)[2][0]
    fin = np.isin(dom, [f'Bip01 R {f}{k}' for f in ('Index', 'Middle', 'Ring', 'Pinky') for k in (1, 2)])
    fist = pts[fin].mean(0)
    foot = c + ax * ((fist - c) @ ax)
    off = fist - foot
    near = st[np.abs((st - foot) @ ax) < 0.05]
    rad = np.median(np.linalg.norm(near - foot - np.outer((near - foot) @ ax, ax), axis=1))
    hi = names.index('Bip01 R Hand'); R = W[hi][:3, :3]; R = R / np.linalg.norm(R, axis=0)
    print('GRIP', spec, 'axis->fist offset (m, world) %s |%.3f| in hand frame %s staff radius %.3f' % (np.round(off, 3), np.linalg.norm(off), np.round(R.T @ off, 3), rad))
