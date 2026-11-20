#!/usr/bin/env python3
"""Axe-head path of a clip (glTF model space, 120 Hz): position, speed and the world head yaw, plus the times the head
crosses the body's centre line (x = 0) in front of him. Usage: oh_path.py <glb> [clip] [t0 t1]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gltf_pose import Pose, qrot  # noqa: E402
glb = sys.argv[1]; clip = sys.argv[2] if len(sys.argv) > 2 else 'Attack'
p = Pose(glb); c = p.clip(clip); i = p.idx; end = max(float(v[0][-1]) for ch in c.values() for v in ch.values())
t0, t1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0, end)
ts = np.arange(0, end + 1e-6, 1 / 120); H = []; yaw = []
for t in ts:
    P, Q = p.world(p.local(c, t)); H.append(P[i['Axe']] + qrot(Q[i['Axe']], np.array([0, 1.05, 0])))
    hd = qrot(Q[i['B_Head']], np.array([1.0, 0, 0])); yaw.append(np.degrees(np.arctan2(hd[0], hd[2])))
H = np.array(H); v = np.r_[0, np.linalg.norm(np.diff(H, axis=0), axis=1) * 120]
for k in np.where(np.sign(H[1:, 0]) != np.sign(H[:-1, 0]))[0]:
    if H[k, 2] > 0.3:
        print(f'crosses the centre line at {ts[k]:.3f}-{ts[k + 1]:.3f} s: height {H[k, 1]:.2f} m, {H[k, 2]:.2f} m in front, {v[k + 1]:.1f} m/s')
print(f'peak head speed {v.max():.1f} m/s at {ts[v.argmax()]:.3f} s; world head yaw {min(yaw):.1f}..{max(yaw):.1f} deg')
for k in range(0, len(ts), 2):
    if t0 <= ts[k] <= t1:
        print(f'{ts[k]:.3f} {H[k].round(2)} {v[k]:5.1f}')
