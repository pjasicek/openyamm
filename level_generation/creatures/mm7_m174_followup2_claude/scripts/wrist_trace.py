#!/usr/bin/env python3
"""Per-frame wrist swing and twist (hand against forearm, relative to Standing; as attack_tools/wrist_probe.py) and
the forearm's roll about its own axis against Standing: wrist_trace.py <glb> <clip> [side] [fps]"""
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/audit_mm678_20261111/fixes/attack_tools'))
import donor_attack as da  # noqa: E402

T = da.Skeleton(sys.argv[1])
clip = sys.argv[2]
s = sys.argv[3] if len(sys.argv) > 3 else 'R'
fps = float(sys.argv[4]) if len(sys.argv) > 4 else 24
_, W0 = T.world('Standing', 0.0)
f, h = T.idx[f'B_{s}_Forearm'], T.idx[f'B_{s}_Hand']
rel0 = da.rot_of(W0[f]).T @ da.rot_of(W0[h])
axis = da.unit(da.rot_of(W0[f]).T @ (W0[h, :3, 3] - W0[f, :3, 3]))
L = T.model.clip_times(clip)[-1]
for t in np.arange(0, L + 1e-6, 1 / fps):
    _, W = T.world(clip, t)
    d = (da.rot_of(W[f]).T @ da.rot_of(W[h])) @ rel0.T
    tw = math.degrees(da.twist_about(da.glb_pose.matrix_quaternion(d), axis))
    sr = d @ da.axis_angle(axis, -math.radians(tw))
    sw = math.degrees(math.acos(np.clip((np.trace(sr) - 1) / 2, -1, 1)))
    print(f't={t:.3f} swing {sw:5.1f} twist {tw:6.1f}')
