#!/usr/bin/env python3
"""Phase by joints (h14): per clip, the loop phase where each ankle joint (B_<s>_Foot) is forward-most relative to the
pelvis, and its lowest-height share (stance, ankle within 2 cm of its minimum). For bodies whose skirt hem reaches the
floor, where phase_probe.py's sole vertices pick up the hem.

    joint_phase_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

glb = open_glb(sys.argv[1])
model = glb_pose.Model(glb)
idx = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
for clip in sys.argv[2].split(','):
    T = model.clip_times(clip)[-1]
    ph = np.arange(240) / 240
    W = np.array([model.world(model.sample(clip, float(p * T))) for p in ph])
    pel = W[:, idx['B_Pelvis'], :3, 3]
    out = []
    for s in 'LR':
        a = W[:, idx[f'B_{s}_Foot'], :3, 3]
        fwd = a[:, 2] - pel[:, 2]
        low = a[:, 1] <= a[:, 1].min() + 0.02
        out.append(f'{s} front {ph[np.argmax(fwd)]:.2f} stance {low.mean():.2f}')
    print(f'{clip:9} T {T:.3f}  ' + '  |  '.join(out))
