#!/usr/bin/env python3
"""Forward thigh swing per clip (deg, hip-to-knee against the pelvis's rest frame, from hanging): max and min per side,
and the knee's highest point above the floor (m).  thigh_probe.py <glb> <clip,clip>"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_gait  # noqa: E402

P = compose_gait.Body(sys.argv[1])
joints = list(P.model.joints)
ibm = P.model.inverse_binds[joints.index(P.idx['B_Pelvis'])]
for clip in sys.argv[2].split(','):
    T = P.clip_length(clip)
    _, worlds = P.clip_world(clip, np.arange(60) / 60 * T)
    out = []
    for s in 'LR':
        a, knee = [], []
        for W in worlds:
            Minv = np.linalg.inv(W[P.idx['B_Pelvis']] @ ibm)[:3, :3]
            d = Minv @ (W[P.idx[f'B_{s}_Calf']][:3, 3] - W[P.idx[f'B_{s}_Thigh']][:3, 3])
            a.append(np.degrees(np.arctan2(d[2], -d[1])))
            knee.append(W[P.idx[f'B_{s}_Calf']][1, 3])
        out.append(f'{s} {min(a):+6.1f}..{max(a):+6.1f} knee max {max(knee):.2f}')
    print(f'{clip:9s} thigh ' + '  |  '.join(out))
