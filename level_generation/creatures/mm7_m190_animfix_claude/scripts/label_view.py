#!/usr/bin/env python3
"""Bind-pose views of LOD0 coloured by a per-vertex label array (follow-up m190).
    label_view.py <glb> <labels.npy> <out.png> [--yaws 0,1.57,3.14] [--ymin 0.6]"""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit  # noqa
from motion_frames import view  # noqa
PAL = np.array([(200, 200, 200), (220, 40, 40), (40, 190, 60), (50, 90, 230), (230, 220, 40), (210, 60, 210),
                (60, 220, 220), (240, 140, 30), (120, 120, 120), (255, 255, 255)], float)
p = argparse.ArgumentParser(); p.add_argument('glb'); p.add_argument('labels'); p.add_argument('out')
p.add_argument('--yaws', default='0,1.57,3.14,4.71'); p.add_argument('--ymin', type=float, default=0.55)
p.add_argument('--cell', type=int, default=420)
a_ = p.parse_args()
a = motion_audit.Audit(a_.glb)
lab = np.load(a_.labels)
if lab.dtype.kind == 'f':
    col = PAL[0] + np.clip(lab, 0, 1)[:, None] * (PAL[1] - PAL[0])
else:
    col = PAL[lab % len(PAL)]
tc = col[a.tris].mean(1)
keep = a.rest[a.tris].mean(1)[:, 1] > a_.ymin
cells = []
for yaw in [float(y) for y in a_.yaws.split(',')]:
    cam = a.rest @ view(yaw, 0.1).T
    sel = a.rest[:, 1] > a_.ymin
    lo, hi = cam[sel].min(0), cam[sel].max(0)
    c0 = (lo[:2] + hi[:2]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
    cell = a_.cell; img = Image.new('RGB', (cell, cell), (30, 30, 30)); d = ImageDraw.Draw(img)
    A, B, C = (cam[a.tris[:, k]] for k in range(3))
    n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
    sh = np.abs(n[:, 2]) * 0.6 + 0.4; dep = (A + B + C)[:, 2]; s = (cell - 10) / span
    for i in np.argsort(dep):
        if not keep[i]:
            continue
        d.polygon([(cell / 2 + (x - c0[0]) * s, cell / 2 - (y - c0[1]) * s) for x, y, _ in (A[i], B[i], C[i])],
                  fill=tuple(int(v) for v in tc[i] * sh[i]))
    d.text((4, 4), f'yaw {yaw:.2f}', fill=(255, 255, 255)); cells.append(img)
sh_ = Image.new('RGB', (a_.cell * len(cells), a_.cell))
for i, im in enumerate(cells):
    sh_.paste(im, (i * a_.cell, 0))
sh_.save(a_.out); print(a_.out)
