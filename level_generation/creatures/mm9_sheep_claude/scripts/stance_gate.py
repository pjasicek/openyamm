#!/usr/bin/env python3
"""Stance at Standing from the bones: yaw (+ = toward +x, the sheep's left) and roll of chosen joints' forward/up
vectors relative to the bind pose, ours against MM9's untouched stand. Usage: stance_gate.py <our glb> <mm9 glb>"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
BONES = ['XCENTER', 'Xback', 'Xneck', 'Xheadpiv', 'Xffoot01', 'Xffoot', 'Xbfoot01', 'Xbfoot']


def row(path, clip):
    m = Model(Glb(path)); names = [n.get('name') for n in m.glb.json['nodes']]
    B = m.world({})
    T = m.clip_times(clip)[-1]
    out = {}
    for t in np.linspace(0, T, 14):
        W = m.world(m.sample(clip, t))
        for b in BONES:
            i = names.index(b)
            Rb = B[i][:3, :3] / np.linalg.norm(B[i][:3, :3], axis=0)
            Rw = W[i][:3, :3] / np.linalg.norm(W[i][:3, :3], axis=0)
            R = Rw @ Rb.T
            f = R @ [0, 0, 1]; u = R @ [0, 1, 0]
            out.setdefault(b, []).append((np.degrees(np.arctan2(f[0], f[2])), np.degrees(np.arctan2(u[0], u[1])), W[i][0, 3]))
    return {b: np.array(v) for b, v in out.items()}


o, m = row(sys.argv[1], 'Standing'), row(sys.argv[2], 'stand')
for b in BONES:
    print(f'{b:10s} yaw ours {o[b][:, 0].min():+6.1f}..{o[b][:, 0].max():+6.1f} mm9 {m[b][:, 0].min():+6.1f}..{m[b][:, 0].max():+6.1f} | '
          f'roll ours {o[b][:, 1].min():+6.1f}..{o[b][:, 1].max():+6.1f} mm9 {m[b][:, 1].min():+6.1f}..{m[b][:, 1].max():+6.1f} | '
          f'x ours {o[b][:, 2].mean():+.3f} mm9 {m[b][:, 2].mean():+.3f}')
