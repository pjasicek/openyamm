#!/usr/bin/env python3
"""(h04) Lowest point of a held prop (attachment GLB placed at its node) per clip, in cm above the floor, and when.
    prop_low_probe.py <body.glb> <clip>[,<clip>...] <node>=<attachment.glb>"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

glb = glb_pose.Glb(sys.argv[1])
model = glb_pose.Model(glb)
node, path = sys.argv[3].split('=', 1)
index = [n.get('name') for n in glb.json['nodes']].index(node)
pts = np.concatenate([q['positions'] for q in glb_pose.Model(glb_pose.Glb(path)).primitives])
for clip in sys.argv[2].split(','):
    T = model.clip_times(clip)[-1]
    lows = []
    for t in np.arange(0, T, 1 / 120):
        W = model.world(model.sample(clip, float(t)))
        lows.append(float((pts @ W[index, :3, :3].T + W[index, :3, 3])[:, 1].min()))
    k = int(np.argmin(lows))
    print(f'{clip:10} {node} lowest {100 * lows[k]:+.1f} cm at {k / 120 / T:.2f} of the loop')
