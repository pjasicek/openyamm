#!/usr/bin/env python3
"""Viewer shot specs for the face review: front close-up, 3/4 both sides, true profiles, low 3/4 from below, under the jaw, party view.
Target = Head joint + OFF (world, the clip pose). Usage: face_specs.py <glb> <prefix> <clip:sec> [ox,oy,oz]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
glb, pre, cs = sys.argv[1:4]; off = np.array([float(x) for x in (sys.argv[4] if len(sys.argv) > 4 else '0,0.035,0.07').split(',')])
HEAD = sys.argv[5] if len(sys.argv) > 5 else 'FHP Head'
m = Model(Glb(glb)); names = [n.get('name') for n in m.glb.json['nodes']]; clip, sec = cs.split(':')
w = m.world(m.sample(clip, float(sec))); t = w[names.index(HEAD)][:3, 3] + off
V = {'front': ((0, 0.03, 1), 0.42), 'q34r': ((0.75, 0.05, 0.7), 0.42), 'q34l': ((-0.75, 0.05, 0.7), 0.42), 'profl': ((1, 0.02, 0.05), 0.42),
     'profr': ((-1, 0.02, 0.05), 0.42), 'low': ((0.35, -0.7, 0.75), 0.42), 'under': ((0.0, -0.9, 0.45), 0.36), 'party': ((0.05, 0.12, 1), 2.6)}
for k, (d, dist) in V.items():
    d = np.array(d, float); d /= np.linalg.norm(d); c = t + d * dist
    print(f'{pre}_{k}:{clip}:{sec}:front:body:' + ','.join(f'{x:.3f}' for x in c) + ':' + ','.join(f'{x:.3f}' for x in t))
