#!/usr/bin/env python3
"""Pod gait: fore-aft travel of the foot tips over Walking (stride = what a planted foot sweeps per cycle), and the
body roll of Running (the rolled ball: rotation per cycle about the lateral axis x ball circumference).
Usage: gait_measure.py <glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1]))
names = [n.get('name') for n in m.glb.json['nodes']]


def node_pos(world, name):
    return np.asarray(world[names.index(name)])[:3, 3]


for clip in ('Walking',):
    ts = np.linspace(0, m.clip_times(clip)[-1], 61)
    for tip in ('Xatip', 'Xatip01', 'Xbtip'):
        zs = np.array([node_pos(m.world(m.sample(clip, t)), tip)[2] for t in ts])  # glTF z = forward axis (-Y Blender)
        print(clip, tip, 'fore-aft travel %.3f' % (zs.max() - zs.min()))
ts = np.linspace(0, m.clip_times('Running')[-1], 61)
ang = []
for t in ts:
    w = m.world(m.sample('Running', t))
    R = np.asarray(w[names.index('XCENTER')])[:3, :3]
    ang.append(np.arctan2(R[1, 2], R[2, 2]))
ang = np.unwrap(np.array(ang))
pos = np.concatenate([p for p, _ in m.skinned_positions(m.world(m.sample('Running', 0)))])
d = pos.max(0) - pos.min(0)
print('Running roll per cycle (deg) %.1f, ball size %s' % (np.degrees(ang[-1] - ang[0]), np.round(d, 3)),
      'swing %.1f' % np.degrees(ang.max() - ang.min()))
