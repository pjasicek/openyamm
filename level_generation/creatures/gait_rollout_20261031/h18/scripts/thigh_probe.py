"""Thigh flexion (deg, hip->knee from straight down, forward positive) and knee height range per clip and side.
    thigh_probe.py <glb> <clip,clip>"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

glb = open_glb(sys.argv[1])
M = glb_pose.Model(glb)
I = {n['name']: i for i, n in enumerate(glb.json['nodes'])}
for clip in sys.argv[2].split(','):
    T = M.clip_times(clip)[-1]
    W = np.array([M.world(M.sample(clip, t)) for t in np.linspace(0, T, 60, endpoint=False)])
    out = []
    for s in 'LR':
        d = W[:, I[f'B_{s}_Calf'], :3, 3] - W[:, I[f'B_{s}_Thigh'], :3, 3]
        a = np.degrees(np.arctan2(d[:, 2], -d[:, 1]))
        k = W[:, I[f'B_{s}_Calf'], 1, 3]
        out.append(f'{s} flex {a.min():+.0f}..{a.max():+.0f} knee {k.min():.2f}..{k.max():.2f}')
    print(f'{clip:9s}', '  '.join(out))
