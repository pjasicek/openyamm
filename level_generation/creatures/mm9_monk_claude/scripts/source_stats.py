#!/usr/bin/env python3
"""MM9 source facts: joints with weight, rest positions, per-joint weight share. Args: <glb>"""
import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
g = Glb(sys.argv[1]); m = Model(g)
j = g.json; names = [n.get('name') for n in j['nodes']]
w = m.world({})
sk = j['skins'][0]['joints']
print('skins', len(j['skins']), 'joints', len(sk))
print({k: len(v) for k, v in j.items() if isinstance(v, list)})
for i in sk[:]:
    p = w[i][:3, 3]; print(f"{names[i]:20s} {p[0]:+.3f} {p[1]:+.3f} {p[2]:+.3f}")
