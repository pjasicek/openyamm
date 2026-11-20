#!/usr/bin/env python3
"""Viewer shot specs with free cameras round a joint (glTF metres), for claude_shared/texpass_viewer_shots.py:
prints name:clip:time:front:body:cx,cy,cz:tx,ty,tz per shot. Joint positions from export/mm6_wwf.glb (joints the
installed and the new GLB share, so before/after cameras are identical)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp
g = gp.Glb(Path(__file__).resolve().parents[1] / 'export/mm6_wwf.glb'); m = gp.Model(g)
names = [n.get('name') for n in g.json['nodes']]
SHOTS = [  # name, clip, time, joint, camera direction (x model left, y up, z front), distance, target offset
    ('stand_front', 'Standing', 0.0, 'Bip01 Pelvis', (0, 0.1, 1), 2.6, (0, 0.0, 0)),
    ('stand_quarter', 'Standing', 0.0, 'Bip01 Pelvis', (-0.7, 0.15, 1), 2.6, (0, 0.0, 0)),
    ('stand_side', 'Standing', 0.0, 'Bip01 Pelvis', (-1, 0.1, 0), 2.6, (0, 0.0, 0)),
    ('stand_back', 'Standing', 0.0, 'Bip01 Pelvis', (0.3, 0.15, -1), 2.6, (0, 0.0, 0)),
    ('head_front', 'Standing', 0.0, 'Bip01 Head', (0, 0.05, 1), 0.75, (0, 0.05, 0.1)),
    ('head_quarter', 'Standing', 0.0, 'Bip01 Head', (-0.8, 0.1, 1), 0.75, (0, 0.05, 0.1)),
    ('hand_R', 'Standing', 0.0, 'Bip01 R Hand', (-0.6, 0.2, 1), 0.5, (0, -0.06, 0.03)),
    ('hand_L', 'Standing', 0.0, 'Bip01 L Hand', (0.6, 0.2, 1), 0.5, (0, -0.06, 0.03)),
    ('attack_wind', 'Attack', 0.28, 'Bip01 Pelvis', (-0.6, 0.15, 1), 2.8, (0, 0.1, 0)),
    ('attack_hit', 'Attack', 0.456, 'Bip01 Pelvis', (-0.6, 0.15, 1), 2.8, (0, 0.1, 0)),
    ('attack_rake', 'Attack', 0.5625, 'Bip01 Pelvis', (-0.3, 0.1, 1), 1.6, (0, -0.1, 0)),   # follow-up: claws past the shorts
    ('walk', 'Walking', 0.2, 'Bip01 Pelvis', (-1, 0.1, 0.3), 2.6, (0, 0.0, 0)),
    ('hit', 'Hit', 0.2, 'Bip01 Pelvis', (-0.6, 0.15, 1), 2.6, (0, 0.0, 0)),
    ('corpse', 'Dead', 0.0, 'Bip01 Pelvis', (0.6, 0.8, 1), 2.6, (0, 0, 0)),
]
want = set(sys.argv[1:])
for name, clip, t, joint, d, dist, off in SHOTS:
    if want and name not in want:
        continue
    w = m.world(m.sample(clip, t)); p = w[names.index(joint)][:3, 3] + np.array(off)
    d = np.array(d, float); d /= np.linalg.norm(d); c = p + d * dist
    print(f'{name}:{clip}:{t}:front:body:{c[0]:.4f},{c[1]:.4f},{c[2]:.4f}:{p[0]:.4f},{p[1]:.4f},{p[2]:.4f}')
