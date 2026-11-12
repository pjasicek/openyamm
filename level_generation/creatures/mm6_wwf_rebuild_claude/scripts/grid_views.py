#!/usr/bin/env python3
"""Front (x,z) and side (y,z) flat views of work/placed.npz with a 5 cm grid (labels every 10 cm), optional points
(json file of name -> [x,y,z]) drawn as red dots. Usage: grid_views.py <out.png> [points.json] [x0,x1,z0,z1]"""
import sys, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import motion_frames
import os; D = np.load(os.environ.get('NPZ', HERE / 'work/placed.npz')); B, T = D['co'], D['tri']
pts = json.load(open(sys.argv[2])) if len(sys.argv) > 2 and sys.argv[2] != '-' else {}
win = [float(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
cells = []
for yaw, ax in ((0, 0), (1.57, 1)):
    cam = np.stack([B[:, 0], B[:, 2], B[:, 1]], 1) @ motion_frames.view(yaw, 0).T
    if win:
        c = np.array([(win[0] + win[1]) / 2 * (1 if ax == 0 else 0) , (win[2] + win[3]) / 2]); span = max(win[1] - win[0], win[3] - win[2])
        if ax == 1: c[0] = (cam[:, 0].min() + cam[:, 0].max()) / 2 if False else c[0]
    else:
        lo, hi = cam.min(0), cam.max(0); c = (lo[:2] + hi[:2]) / 2; span = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
    N = 900; img = motion_frames.draw(cam, T, None, c, span, N); d = ImageDraw.Draw(img); sc = (N - 10) / span
    for g in np.arange(-2, 2, 0.05):
        X = N / 2 + (g - c[0]) * sc; Y = N / 2 - (g - c[1]) * sc
        col = (120, 160, 255) if abs(g * 10 - round(g * 10)) < 1e-6 else (205, 220, 255)
        d.line([(X, 0), (X, N)], fill=col); d.line([(0, Y), (N, Y)], fill=col)
        if abs(g * 10 - round(g * 10)) < 1e-6:
            d.text((X + 2, 2), f'{g:.1f}', fill=(0, 0, 160)); d.text((2, Y + 1), f'{g:.1f}', fill=(0, 0, 160))
    for nm, p in pts.items():
        q = np.array([p[0], p[2], p[1]]) @ motion_frames.view(yaw, 0).T
        X, Y = N / 2 + (q[0] - c[0]) * sc, N / 2 - (q[1] - c[1]) * sc
        d.ellipse([X - 4, Y - 4, X + 4, Y + 4], fill=(255, 0, 0)); d.text((X + 5, Y - 5), nm.split()[-1], fill=(200, 0, 0))
    d.text((N - 120, N - 14), 'front x' if ax == 0 else 'side: -y right?', fill=(0, 0, 0))
    cells.append(img)
sh = Image.new('RGB', (1800, 900)); sh.paste(cells[0], (0, 0)); sh.paste(cells[1], (900, 0)); sh.save(sys.argv[1]); print(sys.argv[1])
