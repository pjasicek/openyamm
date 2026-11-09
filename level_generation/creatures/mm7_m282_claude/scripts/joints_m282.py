#!/usr/bin/env python3
"""Medusa joints (python3) -> work/joints.json, from work/axial.json (harmonic.py) and slice measurements on
work/step1_mesh.npz (forward -Y, up +Z, character left +X; numbers read from measure.py / slice tables).
- Serpent centreline: the harmonic band centroids from the rattle tip to the pelvis, smoothed (moving average over
  ~15 cm of arc, then Chaikin), the ground part held at its own radius above the floor, resampled every SEG m.
  Root = the joint at the bend (the column's lowest forward point); tail joints run back from it, column joints up.
- Human upper body (slice tables, mirrored symmetric): pelvis at the column top, lumbar, chest, neck base, skull base,
  crown; clavicle, shoulder, elbow (where the upper arm, close to the ribs, meets the out-angled forearm), wrist (hand
  piece junction)."""
import json
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
SEG = 0.10
A = np.array(json.load(open(P / 'work' / 'axial.json'))['u_c_r'])
d = np.load(P / 'work' / 'step1_mesh.npz'); co, pv = d['co'], d['piece']
PELVIS = np.array([0.0, 0.13, 0.92])
# serpent points up to the pelvis level
k = np.argmax((A[:, 3] > 0.85) & (A[:, 0] > 0.6))
pts, rad = A[:k, 1:4], A[:k, 4]
W = 15
pad = lambda a: np.concatenate([np.repeat(a[:1], W // 2, 0), a, np.repeat(a[-1:], W // 2, 0)])
ker = np.ones(W) / W
pts = np.stack([np.convolve(pad(pts[:, i]), ker, 'valid') for i in range(3)], 1)
rad = np.convolve(pad(rad), ker, 'valid')
pts = np.vstack([pts, PELVIS]); rad = np.append(rad, 0.17)
for _ in range(3):
    p2, r2 = [pts[0]], [rad[0]]
    for a, b, ra, rb in zip(pts[:-1], pts[1:], rad[:-1], rad[1:]):
        p2 += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]; r2 += [0.75 * ra + 0.25 * rb, 0.25 * ra + 0.75 * rb]
    p2.append(pts[-1]); r2.append(rad[-1]); pts, rad = np.array(p2), np.array(r2)
arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
n = int(round(arc[-1] / SEG))
s = np.linspace(0, arc[-1], n + 1)
J = np.stack([np.interp(s, arc, pts[:, i]) for i in range(3)], 1)
R = np.interp(s, arc, rad)
# radius from the mesh: median distance of nearby skin vertices to the centreline point
skin = co[pv == 0]
for i, j in enumerate(J):
    dd = np.linalg.norm(skin - j, axis=1)
    near = dd[dd < 0.25]
    R[i] = float(np.clip(np.percentile(near, 15) if len(near) else R[i], 0.02, 0.2))
R[0] = 0.02
# the tail lies on the floor: centre at its radius (measured z can wobble)
ground = J[:, 2] < 0.3
J[ground, 2] = np.maximum(J[ground, 2], R[ground] * 0.95)
root = int(np.argmin(J[:, 1] + 10 * np.maximum(J[:, 2] - 0.35, 0)))      # forward-most low point = the bend
J[-1] = PELVIS
H = {
    'Pelvis': [0.0, 0.13, 0.92], 'Spine1': [0.0, 0.12, 1.03], 'Spine2': [0.0, 0.16, 1.18], 'Neck': [0.0, 0.225, 1.44],
    'Head': [0.0, 0.215, 1.535], 'HeadTop': [0.0, 0.2, 1.74],
}
for s_, sg in (('L', 1), ('R', -1)):
    H['Clavicle_' + s_] = [sg * 0.035, 0.225, 1.405]
    H['UpperArm_' + s_] = [sg * 0.155, 0.245, 1.37]
    H['ForeArm_' + s_] = [sg * 0.226, 0.245, 1.14]
    H['Hand_' + s_] = [sg * 0.438, 0.150, 0.898]
out = {'axial': J.round(5).tolist(), 'radius': R.round(4).tolist(), 'root': root, 'human': H}
(P / 'work' / 'joints.json').write_text(json.dumps(out, indent=1))
print('AXIAL length %.3f joints %d root %d at %s' % (arc[-1], len(J), root, np.round(J[root], 3)))
for i in range(0, len(J), 3):
    print('  J%02d %s r %.3f' % (i, np.round(J[i], 3), R[i]))
flat = {f'A{i:02d}': J[i].tolist() for i in range(0, len(J), 2)}; flat.update(H)
(P / 'work' / 'joints_plot.json').write_text(json.dumps({'joints': flat}))
