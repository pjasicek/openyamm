#!/usr/bin/env python3
"""Per sample of a clip: each foot's lowest vertex height (cm) and its forward velocity (m/s, glTF -Z... reported along
the clip's mean backward direction of planted feet), to see where the stride measurement takes swing frames.
    foot_track.py <glb> <clip> [samples]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared/floor'))
import glb_pose  # noqa: E402

glb = glb_pose.Glb(sys.argv[1]); M = glb_pose.Model(glb); clip = sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 30
names = [x.get('name', '') for x in glb.json['nodes']]
pr = M.primitives[0]
dom = np.array([names[M.joints[j]] for j in pr['joints'][np.arange(len(pr['joints'])), pr['weights'].argmax(1)]])
side = {s: np.array([d.startswith(f'B_{s}_Foot') or d.startswith(f'B_{s}_Toe') for d in dom]) for s in 'LR'}
T = M.clip_times(clip)[-1]
ts = np.linspace(0, T, n + 1)
P = [M.skinned_positions(M.world(M.sample(clip, t)))[0][0] for t in ts]
for s in 'LR':
    rows = []
    for k in range(n):
        a, b = P[k][side[s]], P[k + 1][side[s]]
        low = a[:, 1].min()
        sel = a[:, 1] < low + .01
        v = ((b[sel] - a[sel]) / (T / n)).mean(0)
        rows.append(f'{low * 100:5.1f}/{v[2]:+5.2f}')
    print(s, ' '.join(rows))
