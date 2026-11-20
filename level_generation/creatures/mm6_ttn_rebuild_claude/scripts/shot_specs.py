#!/usr/bin/env python3
"""Viewer shot specs with free cameras round a joint (glTF metres), for claude_shared/texpass_viewer_shots.py:
prints name:clip:time:front:body:cx,cy,cz:tx,ty,tz per shot. Joint positions from export/mm6_ttn.glb (joints the
installed and the new GLB share, so before/after cameras are identical)."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
import glb_pose as gp
g = gp.Glb(Path(__file__).resolve().parents[1] / 'export/mm6_ttn.glb'); m = gp.Model(g)
names = [n.get('name') for n in g.json['nodes']]
SHOTS = [  # name, clip, time, joint, camera direction (x right of model?, y up, z front), distance, target offset
    ('stand_full', 'Standing', 0.0, 'Hips', (0, 0.1, 1), 2.6, (0, 0.0, 0)),
    ('stand_hand_L', 'Standing', 0.0, 'LeftHand', (0.8, 0.1, 1), 0.42, (0, -0.07, 0)),
    ('stand_hand_R', 'Standing', 0.0, 'RightHand', (-0.8, 0.1, 1), 0.42, (0, -0.07, 0)),
    ('walk_hand_R', 'WalkHeavy', 0.4, 'RightHand', (-0.8, 0.2, 1), 0.45, (0, -0.06, 0)),
    ('cast_gather', 'Cast', 0.7, 'Spine', (-0.6, 0.15, 1), 1.5, (0, -0.1, 0)),
    ('cast_claw_L', 'Cast', 0.7, 'LeftHand', (0.5, 0.3, 1), 0.45, (0, 0, 0)),
    ('cast_push', 'Cast', 0.95, 'Spine', (-0.6, 0.15, 1), 1.6, (0, -0.1, 0.2)),
    ('cast_push_hands', 'Cast', 0.95, 'Spine', (0.0, 0.1, 1), 0.9, (0, -0.05, 0.42)),
    ('cast_push_side', 'Cast', 0.95, 'RightHand', (-1, 0.2, 0.3), 0.5, (0, 0, 0)),
    ('cast_rec_175', 'Cast', 1.75, 'Spine', (0.7, 0.1, 1), 1.6, (0, -0.15, 0)),
    ('cast_rec_195', 'Cast', 1.95, 'Spine', (0.7, 0.1, 1), 1.6, (0, -0.15, 0)),
    ('cast_rec_205', 'Cast', 2.05, 'Spine', (0.7, 0.1, 1), 1.6, (0, -0.15, 0)),
    ('fidget_fist_L', 'Fidget', 0.34, 'LeftHand', (0.8, 0.1, 1), 0.42, (0, -0.06, 0)),
    ('fidget_fist_R', 'Fidget', 0.34, 'RightHand', (-0.8, 0.1, 1), 0.42, (0, -0.06, 0)),
    ('hit_head', 'Hit', 0.35, 'Head', (-0.4, 0.2, 1), 0.8, (0, 0, 0)),
    ('ranged_thrust', 'Ranged', 0.85, 'RightHand', (-0.6, 0.2, 1), 0.6, (0, 0, 0)),
    ('death_end', 'Dead', 0.0, 'Hips', (0.6, 0.6, 1), 2.4, (0, 0, 0)),
]
want = set(sys.argv[1:])
for name, clip, t, joint, d, dist, off in SHOTS:
    if want and name not in want:
        continue
    w = m.world(m.sample(clip, t)); p = w[names.index(joint)][:3, 3] + np.array(off)
    d = np.array(d, float); d /= np.linalg.norm(d); c = p + d * dist
    print(f'{name}:{clip}:{t}:front:body:{c[0]:.4f},{c[1]:.4f},{c[2]:.4f}:{p[0]:.4f},{p[1]:.4f},{p[2]:.4f}')
