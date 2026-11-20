#!/usr/bin/env python3
"""Bad triangles (motion_audit rule) of one clip, with the beard and braids hidden or shown, several yaws.
    bad_view.py <glb> <clip> <out.png> --times 1.0,1.2 [--yaws 0,1.57,3.14] [--hide-beard work/labels.npz]
                [--region spine] [--zoom y0,y1] [--cell 330]
Red: bad in any region; magenta: bad and in --region."""
import argparse, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit  # noqa
from motion_frames import view  # noqa
p = argparse.ArgumentParser(); p.add_argument('glb'); p.add_argument('clip'); p.add_argument('out')
p.add_argument('--times', default='0'); p.add_argument('--yaws', default='0,1.57,3.14')
p.add_argument('--hide-beard'); p.add_argument('--region'); p.add_argument('--cell', type=int, default=330)
p.add_argument('--zoom', default='0.6,1.25')
a_ = p.parse_args()
a = motion_audit.Audit(a_.glb)
hide = np.zeros(len(a.tris), bool)
if a_.hide_beard:
    lab = np.load(a_.hide_beard)
    hide = lab['b'][a.tris].mean(1) > 0.5
reg = motion_audit.REGIONS.index(a_.region) if a_.region else -1
y0, y1 = [float(v) for v in a_.zoom.split(',')]
cells = []
for t in [float(v) for v in a_.times.split(',')]:
    posed, scale, pal, w = a.pose(a_.clip, t)
    s1, s2, fold, live = a.deformation(posed, scale, pal)
    bad = live & ((s1 > motion_audit.STRETCH) | (s2 < motion_audit.SQUASH) | fold)
    for yaw in [float(v) for v in a_.yaws.split(',')]:
        cam = posed @ view(yaw, 0.1).T
        sel = (a.rest[:, 1] > y0) & (a.rest[:, 1] < y1)
        lo, hi = cam[sel].min(0), cam[sel].max(0)
        c0 = (lo[:2] + hi[:2]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
        cell = a_.cell; img = Image.new('RGB', (cell, cell), (236, 236, 232)); d = ImageDraw.Draw(img)
        A, B, C = (cam[a.tris[:, k]] for k in range(3))
        n = np.cross(B - A, C - A); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
        sh = np.abs(n[:, 2]) * 0.7 + 0.25; dep = (A + B + C)[:, 2]; s = (cell - 10) / span
        for i in np.argsort(dep):
            if hide[i]:
                continue
            g = 255 * sh[i]
            col = (g, g * .95, g * .88)
            if bad[i]:
                col = (g, g * .2, g * .9) if a.tri_region[i] == reg else (g, g * .3, g * .3)
            d.polygon([(cell / 2 + (x - c0[0]) * s, cell / 2 - (y - c0[1]) * s) for x, y, _ in (A[i], B[i], C[i])],
                      fill=tuple(int(v) for v in col))
        d.text((4, 4), f'{a_.clip} {t:.2f} yaw {yaw:.2f}', fill=(0, 0, 0)); cells.append(img)
sheet = Image.new('RGB', (a_.cell * len(cells), a_.cell))
for i, im in enumerate(cells):
    sheet.paste(im, (i * a_.cell, 0))
sheet.save(a_.out); print(a_.out)
