#!/usr/bin/env python3
"""Highest 'lowest skin point' over a clip (cm): how far every foot leaves the floor, the floor audit's walking rule
(a walking-role clip must keep a foot within the tolerance: max(2.5 world units, 1 % of the standing height)).
    flight_probe.py <glb> <clip>[,<clip>...] [scale]"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gaitlib import glb_pose  # noqa: E402

model = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
scale = float(sys.argv[3]) if len(sys.argv) > 3 else None
for clip in sys.argv[2].split(','):
    T = model.clip_times(clip)[-1]
    lows = [model.skinned_positions(model.world(model.sample(clip, k * T / 96)))[0][0][:, 1].min() for k in range(96)]
    hi = max(lows)
    extra = f'  world {hi * scale:+.2f}' if scale else ''
    print(f'{clip:9} highest lowest point {100 * hi:+.2f} cm at {np.argmax(lows) / 96:.2f}{extra}')
