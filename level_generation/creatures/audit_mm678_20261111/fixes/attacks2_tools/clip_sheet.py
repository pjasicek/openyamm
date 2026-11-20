#!/usr/bin/env python3
"""Clip frames on a FIXED camera, one row per view, floor line drawn (attacks-2 stream, 2026-11-11).

    clip_sheet.py <glb> <clip> <out.png> [--frames 10 | --times 0,0.3] [--yaws 0,1.57] [--pitch 0.15] [--cell 220]
                  [--highlight] [--label text]

Unlike motion_frames.py (which recentres every frame), the framing covers the whole clip, so root motion, lunges and
reach read as they play. Several GLBs can be compared by stacking sheets (--label marks the row).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
import motion_audit  # noqa: E402
from motion_frames import draw, view  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('glb')
    p.add_argument('clip')
    p.add_argument('out')
    p.add_argument('--frames', type=int, default=10)
    p.add_argument('--times')
    p.add_argument('--yaws', default='0,1.5708')
    p.add_argument('--pitch', type=float, default=0.15)
    p.add_argument('--cell', type=int, default=220)
    p.add_argument('--highlight', action='store_true')
    p.add_argument('--label', default='')
    a = p.parse_args()
    au = motion_audit.Audit(a.glb)
    times = au.model.clip_times(a.clip)
    picks = [float(t) for t in a.times.split(',')] if a.times else list(np.linspace(times[0], times[-1], a.frames))
    poses = []
    for t in picks:
        posed, scale, palette, world = au.pose(a.clip, t)
        bad = None
        if a.highlight:
            s1, s2, fold, live = au.deformation(posed, scale, palette)
            bad = live & ((s1 > motion_audit.STRETCH) | (s2 < motion_audit.SQUASH) | fold)
        poses.append((posed, bad))
    rows = []
    for yaw in [float(y) for y in a.yaws.split(',')]:
        rot = view(yaw, a.pitch)
        cams = [posed @ rot.T for posed, _ in poses]
        allp = np.concatenate(cams)
        lo, hi = allp.min(axis=0), allp.max(axis=0)
        centre = (lo[:2] + hi[:2]) / 2
        span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
        row = []
        for t, cam, (_, bad) in zip(picks, cams, poses):
            img = draw(cam, au.tris, bad, centre, span, a.cell)
            d = ImageDraw.Draw(img)
            floor = (np.array([0.0, 0.0, 0.0]) @ rot.T)[1]
            scale = (a.cell - 10) / span
            y = a.cell / 2 - (floor - centre[1]) * scale
            d.line([(0, y), (a.cell, y)], fill=(80, 140, 220))
            d.text((4, 4), f'{a.label} {a.clip} {t:.2f}s', fill=(0, 0, 0))
            row.append(img)
        rows.append(row)
    sheet = Image.new('RGB', (a.cell * len(picks), a.cell * len(rows)), (255, 255, 255))
    for r, row in enumerate(rows):
        for i, img in enumerate(row):
            sheet.paste(img, (i * a.cell, r * a.cell))
    sheet.save(a.out)
    print(a.out)


if __name__ == '__main__':
    main()
