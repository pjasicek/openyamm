#!/usr/bin/env python3
"""Measure the blow of an attack clip: the halberd's blade head (the attachment's farthest vertex from the grip along the shaft,
on Xbase) per 1/120 s; impact = fastest motion of the blade head while it moves forward (toward the target, -Z of the model is
its front in glTF here: the actor faces glTF +Z? both are printed). Args: <body glb> <halberd glb> <clip> [joint]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
body, hal, clip = sys.argv[1:4]; joint = sys.argv[4] if len(sys.argv) > 4 else 'Xbase'
m = Model(Glb(Path(body))); h = Glb(Path(hal)); hp = h.json['meshes'][0]['primitives'][0]
P = h.accessor(hp['attributes']['POSITION']).astype(float)
tip = P[np.argmax(np.linalg.norm(P, axis=1))]
names = [n.get('name') for n in m.glb.json['nodes']] if hasattr(m, 'glb') else [n.get('name') for n in Glb(Path(body)).json['nodes']]
ji = names.index(joint)
t0, t1 = 0.0, max(m.clip_times(clip))
ts = np.arange(t0, t1 + 1e-6, 1 / 120); pts = []
for t in ts:
    w = m.world(m.sample(clip, t)); pts.append((w[ji] @ np.r_[tip, 1])[:3])
pts = np.array(pts); v = np.gradient(pts, ts, axis=0); sp = np.linalg.norm(v, axis=1)
k = int(np.argmax(sp)); fwd = v[:, 2]
print('BLOW', clip, 'peak blade speed %.2f m/s at %.3f s' % (sp[k], ts[k]), 'clip %.3f s' % t1, 'z-velocity there %.2f' % fwd[k],
      'tip height there %.2f' % pts[k, 1], 'top-3 times', np.round(ts[np.argsort(-sp)[:3]], 3).tolist())
