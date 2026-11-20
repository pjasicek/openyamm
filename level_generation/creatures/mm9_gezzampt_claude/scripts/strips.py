#!/usr/bin/env python3
"""Spec lines for viewer frame strips: every clip at N evenly spaced times, wide 3/4 camera. Args: <glb> <n> [clips]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
m = Model(Glb(sys.argv[1])); n = int(sys.argv[2]); want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
pre = sys.argv[4] if len(sys.argv) > 4 else 'st'
for a in m.glb.json['animations']:
    c = a['name']; d = m.clip_times(c)[-1]
    if want and c not in want: continue
    for k in range(n):
        t = d * k / (n - 1)
        print(f'{pre}_{c}_{k:02d}:{c}:{t:.3f}:front:body:-2.6,2.0,4.0:0,1.1,0')
