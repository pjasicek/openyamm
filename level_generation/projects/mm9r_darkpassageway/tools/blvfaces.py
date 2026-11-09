#!/usr/bin/env python3
"""Horizontal BLV faces under a native point: tools/blvfaces.py x y zlo zhi (native)"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM')
from util.map_export import parse_blv_file
b = parse_blv_file(Path(__file__).resolve().parents[1] / 'work/runtime/darkpassageway.blv')['payload']
V = np.array([[v['x'], v['y'], v['z']] for v in b['vertices']], float)
x, y, zlo, zhi = map(float, sys.argv[1:5])
for f in b['faces']:
    pts = V[f['vertex_indices']]
    if len(pts) < 3 or not (pts[:, 0].min() <= x <= pts[:, 0].max() and pts[:, 1].min() <= y <= pts[:, 1].max()):
        continue
    z = pts[:, 2].mean()
    if zlo <= z <= zhi:
        print(f['index'], 'room', f['room_number'], 'z', round(z), 'dz', round(np.ptp(pts[:, 2])), f.get('texture_name'), 'portal' if f['is_portal'] else '')
