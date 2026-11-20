#!/usr/bin/env python3
"""Spec lines for viewer frame strips: every clip at N evenly spaced times, a wide 3/4 camera following the pelvis. Args: <glb> <n> [clips]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); n = int(sys.argv[2]); want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
names = [x.get('name') for x in m.glb.json['nodes']]; pel = names.index('Bip01 Pelvis')
for a in m.glb.json['animations']:
    c = a['name']
    if want and c not in want: continue
    d = m.clip_times(c)[-1]
    for k in range(n):
        t = d * k / (n - 1)
        p = m.world(m.sample(c, t))[pel][:3, 3]
        print(f'{c}_{k:02d}:{c}:{t:.3f}:front:body:{p[0] - 1.9:.3f},1.75,{p[2] + 2.5:.3f}:{p[0]:.3f},0.8,{p[2]:.3f}')
