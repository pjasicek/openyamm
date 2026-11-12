#!/usr/bin/env python3
"""Trunk weight colours of a GLB's LOD0 (follow-up m190, 2026-11-11), optionally posed.

    weight_view.py <glb> <out.png> [--clip Hit --times 0,0.2] [--yaws 0,1.57,3.14] [--cell 360] [--zoom y0,y1]

Each triangle is coloured by its corners' weights over: Pelvis grey, Spine red, Spine1 orange, Spine2 yellow,
Neck green, Head blue, clavicles magenta, upper arms cyan, everything else white.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import motion_audit  # noqa: E402
from motion_frames import view  # noqa: E402

GROUPS = [('B_Pelvis', (120, 120, 120)), ('B_Spine', (220, 40, 40)), ('B_Spine1', (240, 140, 30)),
          ('B_Spine2', (230, 220, 40)), ('B_Neck', (40, 190, 60)), ('B_Head', (50, 90, 230)),
          ('B_L_Clavicle', (210, 60, 210)), ('B_R_Clavicle', (210, 60, 210)),
          ('B_L_UpperArm', (60, 220, 220)), ('B_R_UpperArm', (60, 220, 220))]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('glb')
    p.add_argument('out')
    p.add_argument('--clip')
    p.add_argument('--times', default='0')
    p.add_argument('--yaws', default='0,1.57,3.14')
    p.add_argument('--pitch', type=float, default=0.1)
    p.add_argument('--cell', type=int, default=360)
    p.add_argument('--zoom', default='')
    a_ = p.parse_args()
    a = motion_audit.Audit(a_.glb)
    J = np.concatenate([q['joints'] for _, _, q in a.parts])
    W = np.concatenate([q['weights'] for _, _, q in a.parts])
    col = np.full((len(J), 3), 245.0)
    acc = np.zeros(len(J))
    for name, c in GROUPS:
        k = a.joint_names.index(name)
        w = (W * (J == k)).sum(1)
        col += w[:, None] * (np.array(c) - 245.0)
    tri_col = col[a.tris].mean(1)
    cells = []
    times = [float(t) for t in a_.times.split(',')]
    for t in times:
        if a_.clip:
            posed = a.pose(a_.clip, t)[0]
        else:
            posed = a.rest
        for yaw in [float(y) for y in a_.yaws.split(',')]:
            rot = view(yaw, a_.pitch)
            cam = posed @ rot.T
            if a_.zoom:
                y0, y1 = [float(x) for x in a_.zoom.split(',')]
                sel = (a.rest[:, 1] > y0) & (a.rest[:, 1] < y1)
                lo, hi = cam[sel].min(0), cam[sel].max(0)
            else:
                lo, hi = cam.min(0), cam.max(0)
            centre = (lo[:2] + hi[:2]) / 2
            span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
            cell = a_.cell
            img = Image.new('RGB', (cell, cell), (30, 30, 30))
            d = ImageDraw.Draw(img)
            A, B, C = cam[a.tris[:, 0]], cam[a.tris[:, 1]], cam[a.tris[:, 2]]
            n = np.cross(B - A, C - A)
            n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)
            shade = np.abs(n[:, 2]) * 0.6 + 0.4
            depth = (A + B + C)[:, 2]
            scale = (cell - 10) / span
            for i in np.argsort(depth):
                pts = [(cell / 2 + (x - centre[0]) * scale, cell / 2 - (y - centre[1]) * scale) for x, y, _ in
                       (A[i], B[i], C[i])]
                d.polygon(pts, fill=tuple(int(v) for v in tri_col[i] * shade[i]))
            d.text((4, 4), f'{a_.clip or "bind"} {t:.2f} yaw {yaw:.2f}', fill=(255, 255, 255))
            cells.append(img)
    sheet = Image.new('RGB', (a_.cell * len(cells), a_.cell))
    for i, im in enumerate(cells):
        sheet.paste(im, (i * a_.cell, 0))
    sheet.save(a_.out)
    print(a_.out)


if __name__ == '__main__':
    main()
