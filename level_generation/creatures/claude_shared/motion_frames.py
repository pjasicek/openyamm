#!/usr/bin/env python3
"""Flat-shaded frames of a creature GLB clip, optionally zoomed on one joint (MM6-MM8 audit, 2026-11-11).

    motion_frames.py <glb> <clip> <out.png> [--frames 8] [--times 0.5,0.9] [--joint LeftHand] [--zoom 0.25]
                     [--yaw 0] [--pitch 0.2] [--cell 260] [--highlight]

Poses LOD0 with motion_audit.Audit (no Blender), renders each frame in painter's order from a camera at --yaw (radians
about +Y; 0 looks at the model's front along -Z... the model's own facing varies, so try 0, 1.57, 3.14) and --pitch.
--joint centres every frame on that joint and frames a window of --zoom x H. --highlight paints triangles that
motion_audit counts as bad (stretch, squash or fold) red, so a number can be checked against the picture.
"""
import argparse
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import motion_audit  # noqa: E402


def view(yaw, pitch):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return rx @ ry


def draw(points, tris, bad, centre, span, cell, light=np.array([0.4, 0.7, 0.6])):
    a, b, c = points[tris[:, 0]], points[tris[:, 1]], points[tris[:, 2]]
    n = np.cross(b - a, c - a)
    length = np.linalg.norm(n, axis=1)
    keep = length > 1e-14
    n = n / np.maximum(length[:, None], 1e-20)
    shade = np.clip(np.abs(n @ (light / np.linalg.norm(light))), 0, 1) * 0.75 + 0.2
    depth = (a + b + c)[:, 2] / 3
    scale = (cell - 10) / span
    img = Image.new('RGB', (cell, cell), (236, 236, 232))
    d = ImageDraw.Draw(img)
    for i in np.argsort(depth):
        if not keep[i]:
            continue
        pts = [(cell / 2 + (x - centre[0]) * scale, cell / 2 - (y - centre[1]) * scale) for x, y, _ in
               (a[i], b[i], c[i])]
        g = int(255 * shade[i])
        d.polygon(pts, fill=(g, int(g * 0.3), int(g * 0.3)) if bad is not None and bad[i] else
                  (g, int(g * 0.95), int(g * 0.88)))
    return img


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('glb')
    p.add_argument('clip')
    p.add_argument('out')
    p.add_argument('--frames', type=int, default=8)
    p.add_argument('--times')
    p.add_argument('--joint')
    p.add_argument('--zoom', type=float, default=0.3)
    p.add_argument('--yaw', type=float, default=0.0)
    p.add_argument('--pitch', type=float, default=0.15)
    p.add_argument('--cell', type=int, default=260)
    p.add_argument('--highlight', action='store_true')
    args = p.parse_args()
    a = motion_audit.Audit(args.glb)
    times = a.model.clip_times(args.clip)
    picks = [float(t) for t in args.times.split(',')] if args.times else \
        list(np.linspace(times[0], times[-1], args.frames))
    rot = view(args.yaw, args.pitch)
    joint = None
    if args.joint:
        joint = a.model.joints[a.joint_names.index(args.joint)]
    cells = []
    for t in picks:
        posed, scale, palette, world = a.pose(args.clip, t)
        bad = None
        if args.highlight:
            s1, s2, fold, live = a.deformation(posed, scale, palette)
            bad = live & ((s1 > motion_audit.STRETCH) | (s2 < motion_audit.SQUASH) | fold)
        cam = posed @ rot.T
        if joint is not None:
            centre = (world[joint][:3, 3] @ rot.T)[:2]
            span = args.zoom * a.height
        else:
            lo, hi = cam.min(axis=0), cam.max(axis=0)
            centre = (lo[:2] + hi[:2]) / 2
            span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
        img = draw(cam, a.tris, bad, centre, span, args.cell)
        ImageDraw.Draw(img).text((4, 4), f'{args.clip} {t:.2f}s', fill=(0, 0, 0))
        cells.append(img)
    sheet = Image.new('RGB', (args.cell * len(cells), args.cell), (255, 255, 255))
    for i, img in enumerate(cells):
        sheet.paste(img, (i * args.cell, 0))
    sheet.save(args.out)
    print(args.out)


if __name__ == '__main__':
    main()
