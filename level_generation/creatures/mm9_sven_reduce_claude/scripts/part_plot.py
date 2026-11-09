"""Face-centroid dots by part (front x-y, side z-y, front = +z right) above YLO, drawn with PIL: review/parts_plot[_<tag>].png;
kept faces of work/glb_sets_<tag>.npz in black. usage: part_plot.py [tag] [ylo]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parents[1]
g = np.load(HERE / 'work' / 'glb_parts.npz'); cen = g['cen']; part = g['part']
tag = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '-' else None
keep = np.load(HERE / 'work' / f'glb_sets_{tag}.npz')['keep'] if tag else np.zeros(len(part), bool)
ylo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
sel = cen[:, 1] > ylo; S = 1400 / max(np.ptp(cen[sel, 1]), 0.5)
PAL = [(230, 25, 75), (60, 180, 75), (255, 225, 25), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
       (240, 50, 230), (210, 245, 60), (250, 190, 212), (0, 128, 128), (170, 110, 40), (128, 0, 0), (128, 128, 0)]
parts = list(np.unique(part)); col = {p: PAL[i % len(PAL)] for i, p in enumerate(parts)}
W = int(S * 1.0) + 40; H = int(S * np.ptp(cen[sel, 1])) + 60
im = Image.new('RGB', (2 * W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
y0 = cen[sel, 1].max()
for side, (i, cx) in enumerate(((0, W // 2), (2, W + W // 2))):
    for f in np.flatnonzero(sel):
        x = cx + cen[f, i] * S; y = 30 + (y0 - cen[f, 1]) * S
        c = (0, 0, 0) if keep[f] else col[part[f]]
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=c)
for k, p in enumerate(parts):
    d.rectangle([10, 10 + 18 * k, 24, 24 + 18 * k], fill=col[p]); d.text((30, 10 + 18 * k), f'part {p}', fill=(0, 0, 0))
out = HERE / 'review' / (f'parts_plot_{tag}.png' if tag else 'parts_plot.png'); out.parent.mkdir(exist_ok=True); im.save(out); print(out, im.size)
