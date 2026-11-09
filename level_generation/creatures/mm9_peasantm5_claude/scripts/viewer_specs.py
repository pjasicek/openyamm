#!/usr/bin/env python3
"""Shot specs for mm8_m424_claude/scripts/viewer_shots.mjs around both hands (sleeve acceptance, 2026-10-30): for each
clip:seconds the camera looks at the mid point of the hands from the front, 3/4 from above (both sides) and from
below, in viewer (glTF, Y-up) metres, plus a close view of each cuff from below. Prints one spec per line.
Usage: viewer_specs.py <glb> <hand token: "FHP" | "Bip01"> <prefix> <clip:seconds> [...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model

glb, tok, prefix, items = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
model = Model(Glb(glb))
names = [n.get('name') for n in model.glb.json['nodes']]
for it in items:
    clip, sec = it.split(':')
    world = model.world(model.sample(clip, float(sec)))
    hand = {s: world[names.index(f'{tok} {s} Hand')][:3, 3] for s in 'LR'}
    mid = (hand['L'] + hand['R']) / 2
    # the viewer turns nothing: GLB +Z is the front
    for view, off in (('front', (0, 0.05, 1.5)), ('aboveL', (0.8, 0.95, 1.05)), ('aboveR', (-0.8, 0.95, 1.05)),
                      ('below', (0, -0.65, 1.2))):
        cam = mid + np.array(off)
        print(f'{prefix}_{clip}_{view}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in cam) + ':'
              + ','.join(f'{x:.3f}' for x in mid))
    for s in 'LR':
        c = hand[s] + np.array((0.0, -0.35, 0.65))
        print(f'{prefix}_{clip}_cuff{s}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in c) + ':'
              + ','.join(f'{x:.3f}' for x in hand[s]))
