#!/usr/bin/env python3
"""Per-frame jumps of a joint's world position: finds pops in a clip. Args: <glb> <clip> <joint> [fps]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, clip, joint = sys.argv[1:4]; fps = float(sys.argv[4]) if len(sys.argv) > 4 else 48
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]
t = m.clip_times(clip); T = np.arange(0, t[-1], 1 / fps)
i = names.index(joint)
P = np.array([m.world(m.sample(clip, x))[i][:3, 3] for x in T])
v = np.linalg.norm(np.diff(P, axis=0), axis=1) * 1000
a = np.linalg.norm(np.diff(P, 2, axis=0), axis=1) * 1000
print(clip, joint, 'speed mm/f p50', round(np.median(v), 1), 'max', round(v.max(), 1), 'acc max', round(a.max(), 1), 'at frame', int(a.argmax()) + 1, 'of', len(T))
o = np.argsort(-a)[:6]; print(sorted(o.tolist()), np.round(a[sorted(o.tolist())], 0).tolist())
