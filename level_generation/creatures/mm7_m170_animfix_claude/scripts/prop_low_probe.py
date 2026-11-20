#!/usr/bin/env python3
"""Lowest point of a held prop over each clip (cm above the floor) and its phase: a trident tip dragged through the
floor.  prop_low_probe.py <glb> <clip>[,<clip>...] node=prop.glb"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose, open_glb  # noqa: E402

node, path = sys.argv[3].split('=', 1)
pts = np.concatenate([p['positions'] for p in glb_pose.Model(glb_pose.Glb(path)).primitives])
glb = open_glb(sys.argv[1])
model = glb_pose.Model(glb)
index = [n['name'] for n in glb.json['nodes']].index(node)
for clip in sys.argv[2].split(','):
    T = model.clip_times(clip)[-1]
    lows = []
    for k in range(96):
        M = model.world(model.sample(clip, k * T / 96))[index]
        lows.append((pts @ M[:3, :3].T + M[:3, 3])[:, 1].min())
    k = int(np.argmin(lows))
    print(f'{clip:9} {node} lowest {100 * lows[k]:+.1f} cm at phase {k / 96:.2f}')
