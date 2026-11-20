#!/usr/bin/env python3
"""Right (or left) arm directions in the chest frame at clip times: arm_info.py <glb> <clip> <t,t,...> [side]"""
import sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'level_generation/creatures/claude_shared/floor'))
import glb_pose  # noqa: E402
from arm_aim import ortho, unit  # noqa: E402
g = glb_pose.Glb(sys.argv[1]); m = glb_pose.Model(g)
names = [n['name'] for n in g.json['nodes']]; I = {n: i for i, n in enumerate(names)}
s = sys.argv[4] if len(sys.argv) > 4 else 'R'
C0 = ortho(m.world(m.sample('Standing', 0))[I['B_Spine2']][:3, :3])
for t in [float(x) for x in sys.argv[3].split(',')]:
    W = m.world(m.sample(sys.argv[2], t))
    Rb = ortho(W[I['B_Spine2']][:3, :3]) @ C0.T
    p = lambda b: W[I[b]][:3, 3]
    sh, el, wr, nk = p(f'B_{s}_UpperArm'), p(f'B_{s}_Forearm'), p(f'B_{s}_Hand'), p('B_Neck')
    H = ortho(W[I[f'B_{s}_Hand']][:3, :3])
    ax = ' '.join(f'{k}{np.round(Rb.T @ H[:, i], 2)}' for i, k in enumerate('xyz'))
    fa, ua = unit(wr - el), unit(el - sh)
    bend = np.degrees(np.arccos(np.clip(fa @ ua, -1, 1)))
    print(f't={t:.2f} ua {np.round(Rb.T @ ua, 2)} fa {np.round(Rb.T @ fa, 2)} bend {bend:4.0f} '
          f'elbow {np.round(Rb.T @ (el - nk), 2)} wrist {np.round(Rb.T @ (wr - nk), 2)} hand {ax}')
