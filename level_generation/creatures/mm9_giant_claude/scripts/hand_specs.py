#!/usr/bin/env python3
"""Viewer shot specs for the grip close-ups (third pass): both hands from the front, below and the outside, framed on the grip point (the
fist's hole on the shaft, work/hand_poses.json), and the mallet's head and grip run. Usage: hand_specs.py <glb> <prefix> <clip:seconds> ...
[--mallet]"""
import sys, json
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
HERE = Path(__file__).resolve().parents[1]
glb, pre = sys.argv[1:3]; args = [a for a in sys.argv[3:] if not a.startswith('--')]
m = Model(Glb(glb)); d = m.glb.json; names = [n.get('name') for n in d['nodes']]
P = json.load(open(HERE / 'work' / 'hand_poses.json')); B2G = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0.]])
lift = np.array(d['nodes'][names.index('MM9_Rig')].get('translation', [0, 0, 0])); W0 = m.world({})
iH = {S: names.index(f'Bip01 {S} Hand') for S in 'RL'}; iX = names.index('Xhammer')
loc = {'R': (np.linalg.inv(W0[iH['R']]) @ np.r_[B2G @ np.array(P['holeR']['G_turned_world']) + lift, 1])[:3],
       'L': (np.linalg.inv(W0[iH['L']]) @ np.r_[B2G @ np.array(P['holeL']['G_world']) + lift, 1])[:3]}
VIEWS = {'front': (0, 0.15, 1), 'below': (0, -1, 0.3)}
def spec(name, clip, sec, p, o, dist):
    o = np.array(o, float); o = o / np.linalg.norm(o) * dist
    return f'{name}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in p + o) + ':' + ','.join(f'{x:.3f}' for x in p)
out = []
for k, cs in enumerate(args):
    clip, sec = cs.split(':'); w = m.world(m.sample(clip, float(sec)))
    for S in 'RL':
        g = (w[iH[S]] @ np.r_[loc[S], 1])[:3]
        views = dict(VIEWS); views['side'] = (-1 if S == 'R' else 1, 0.15, 0.2)
        for v, o in views.items(): out.append(spec(f'{pre}{k:02d}{S}{v}', clip, sec, g, o, 0.62))
if '--mallet' in sys.argv:
    w = m.world(m.sample('Standing', 0.0)); X = w[iX]
    head = (X @ np.r_[0, -0.19, 0, 1])[:3]; grip = (X @ np.r_[0, 0.55, 0, 1])[:3]
    out += [spec(f'{pre}M_head_q', 'Standing', 0.0, head, (0.6, 0.35, 1), 1.1), spec(f'{pre}M_head_end', 'Standing', 0.0, head, (1, 0.2, 0.15), 0.9),
            spec(f'{pre}M_head_top', 'Standing', 0.0, head, (0.2, 1, 0.5), 1.0), spec(f'{pre}M_whole', 'Standing', 0.0, (head + (X @ np.r_[0, 0.6, 0, 1])[:3]) / 2, (0.3, 0.2, 1), 2.6),
            spec(f'{pre}M_grip', 'Standing', 0.0, grip, (0.2, 0.3, 1), 0.9)]
print(' '.join(out))
