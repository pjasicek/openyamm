#!/usr/bin/env python3
"""Viewer close-up specs of the right hand on the staff (2026-11-01): per clip:time, four cameras on the fist (mean of the R Hand and finger
joints) from the front (+z, the actor faces +z in the exported GLB), below, outside (the actor's right, -x) and the palm side (the hand's
palm normal in that pose, plus front and down, at 0.4 of the distance, so the camera stays out of the torso and coat). Viewer frame = export frame.
Usage: grip_specs.py <export glb> <prefix> <dist m> clip:t ... ; prints name:clip:t:front:body:cam:target per shot"""
import sys, json
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
glb, pre, dist = sys.argv[1], sys.argv[2], float(sys.argv[3])
m = Model(Glb(glb)); nn = [n['name'] for n in m.glb.json['nodes']]; jn = [nn[j] for j in m.joints]
GR = json.load(open('work/rig.json'))['grip']
n = np.array(GR['palm_side'], float); n = np.array([n[0], n[2], -n[1]]) * [-1, 1, 1]                  # Blender raw -> glTF, mirrored
Wb = np.linalg.inv(m.inverse_binds[jn.index('Bip01 R Hand')]); n_loc = Wb[:3, :3].T @ n
for k, ct in enumerate(sys.argv[4:]):
    clip, t = ct.split(':'); t = float(t); T = m.clip_times(clip)[-1]; t = min(t, T)
    w = m.world(m.sample(clip, t))
    pts = [w[nn.index('Bip01 R Hand')][:3, 3]] + [w[nn.index(f'Bip01 R {f}{i}')][:3, 3] for f in ('Index', 'Middle', 'Ring', 'Pinky', 'Thumb') for i in (1, 2)]
    c = np.mean(pts, 0); nw = w[nn.index('Bip01 R Hand')][:3, :3] @ n_loc; nw /= np.linalg.norm(nw)
    fr = np.array([0, 0, 1.0]); pal = nw + fr + np.array([0, -1.0, 0]); pal /= np.linalg.norm(pal)
    views = dict(front=fr, below=np.array([0, -1, 0.15]), outside=np.array([-1, 0, 0.2]), palm=pal)
    for v, d in views.items():
        d = d / np.linalg.norm(d); cam = c + d * (dist * 0.4 if v == 'palm' else dist)
        print(f'{pre}{k}{v}:{clip}:{t:.3f}:front:body:' + ','.join(f'{x:.3f}' for x in cam) + ':' + ','.join(f'{x:.3f}' for x in c))
