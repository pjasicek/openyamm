#!/usr/bin/env python3
"""Full orientation of the head and paw bones, ours against the MM9 clip at the same time (every clip, 48 fps): the angle
of the relative rotation in degrees, max per clip. Bones are compared in world space, so the root (floor pass) and any rest
change are taken out only through the rotation. Usage: orientation_gate.py <ours.glb> <mm9.glb> <bones comma> role=clip ..."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
ours, mm9 = Model(Glb(sys.argv[1])), Model(Glb(sys.argv[2]))
bones = sys.argv[3].split(',')
roles = dict(a.split('=') for a in sys.argv[4:])
na = [n.get('name') for n in ours.glb.json['nodes']]
nb = [n.get('name') for n in mm9.glb.json['nodes']]


def rot(M):
    R = np.asarray(M)[:3, :3]
    return R / np.linalg.norm(R, axis=0)


def rest_rel(model, names, b):
    return rot(model.world({})[names.index(b)])


for role, clip in roles.items():
    Ta, Tb = ours.clip_times(role)[-1], mm9.clip_times(clip)[-1]
    res = {b: 0.0 for b in bones}
    for t in np.arange(0, Ta, 1 / 48):
        wa = ours.world(ours.sample(role, float(t)))
        wb = mm9.world(mm9.sample(clip, float(t) * Tb / Ta))
        for b in bones:
            # world orientation of the bone relative to its own rest: the same turn in both
            ra = rot(wa[na.index(b)]) @ rest_rel(ours, na, b).T
            rb = rot(wb[nb.index(b)]) @ rest_rel(mm9, nb, b).T
            c = (np.trace(ra.T @ rb) - 1) / 2
            res[b] = max(res[b], float(np.degrees(np.arccos(np.clip(c, -1, 1)))))
    print(role, {k: round(v, 1) for k, v in res.items()})
