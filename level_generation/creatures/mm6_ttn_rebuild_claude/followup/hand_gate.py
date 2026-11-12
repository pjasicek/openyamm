#!/usr/bin/env python3
"""Finger interpenetration of the Titan's hands over whole clips (follow-up 2026-11-11), with fist_solve.py's part
split and signed depth test: per clip and side the worst distal-part depth into another finger (cm) and into the palm,
at the viewer's 48 fps. Usage: hand_gate.py <glb> [clips,...]"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fist_solve as fs
import json
glb = sys.argv[1]; signs = json.load(open(Path(__file__).resolve().parents[1] / 'work/splice_v1.json'))['spread_signs']
for side in ('Left', 'Right'):
    h = fs.Hand(glb, side, signs)
    clips = sys.argv[2].split(',') if len(sys.argv) > 2 else list(h.m.clips)
    for clip in clips:
        dur = max(h.m.clip_times(clip)); worst_f = (0, 0, ''); worst_h = (0, 0, '')
        for t in np.arange(0, dur + 1e-6, 1 / 48):
            w = h.m.world(h.m.sample(clip, float(t))); pal = w[h.m.joints] @ h.m.inverse_binds
            X = np.einsum('vij,vj->vi', np.einsum('vk,vkij->vij', h.W, pal[h.J]), h.P)[:, :3]
            parts = {k: np.where(h.part == k)[0] for k in range(6)}; faces = {k: np.where(h.face_part == k)[0] for k in range(6)}
            for a in range(1, 6):
                for b in range(6):
                    if a == b:
                        continue
                    pa = parts[a][h.distal[parts[a]]]; fb = faces[b] if b == 0 else faces[b][h.face_distal[faces[b]]]
                    if not len(pa) or not len(fb):
                        continue
                    d = float(h.depth(X[pa], X, fb)[0].max()) * 100
                    key = f'{"HTIMRP"[a]}{"HTIMRP"[b]}'
                    if b == 0 and d > worst_h[0]:
                        worst_h = (round(d, 2), round(float(t), 3), key)
                    if b > 0 and d > worst_f[0]:
                        worst_f = (round(d, 2), round(float(t), 3), key)
        print(f'{side:5s} {clip:10s} finger-finger {worst_f}  finger-palm {worst_h}')
