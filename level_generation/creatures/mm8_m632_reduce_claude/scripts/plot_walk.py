#!/usr/bin/env python3
"""Walking head and pelvis height per viewer frame (48 fps), before vs after the fixes, plus the left elbow's travel
per frame (the swivel spikes), drawn with PIL -> review/walk/walk_bob_plot.png. Usage: plot_walk.py <before.glb> <after.glb>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent)); from anim_fk import Clip  # noqa: E402
series = []
for glb in sys.argv[1:3]:
    c = Clip(Path(glb), 'Walking'); t = c.times; f = np.arange(0, round(t[-1] * 48) + 1)
    hp = {b: np.interp(f / 48, t, c.world(b)[:, 1, 3]) * 100 for b in ('B_Head', 'B_Pelvis')}
    e = c.world('B_L_Forearm')[:, :3, 3]; e48 = np.stack([np.interp(f / 48, t, e[:, k]) for k in range(3)], 1)
    series.append((hp, np.concatenate([[np.nan], np.linalg.norm(np.diff(e48, axis=0), axis=1) * 1000])))
n = len(f) - 1; W, H, M = 1100, 820, 70
img = Image.new('RGB', (W, H), (250, 250, 250)); d = ImageDraw.Draw(img); cols = [(150, 150, 150), (30, 110, 220)]
X = lambda i: M + (W - 2 * M) * i / n
panels = [([s[0]['B_Head'] for s in series] + [s[0]['B_Pelvis'] for s in series], 40, 470, 'head (upper) and pelvis (lower) height, cm'),
          ([s[1] for s in series], 530, 780, 'left elbow travel per frame, mm (swivel spikes)')]
for p, (curves, y0, y1, title) in enumerate(panels):
    allv = np.concatenate([c[~np.isnan(c)] for c in curves]); lo, hi = allv.min(), allv.max(); pad = (hi - lo) * .06; lo -= pad; hi += pad
    Y = lambda v: y1 - (y1 - y0) * (v - lo) / (hi - lo)
    d.rectangle([M, y0, W - M, y1], outline=(0, 0, 0)); d.text((M + 6, y0 + 4), title, fill=(0, 0, 0))
    for k in range(6):
        v = lo + (hi - lo) * k / 5; d.text((6, Y(v) - 6), f'{v:.1f}', fill=(0, 0, 0)); d.line([M, Y(v), W - M, Y(v)], fill=(225, 225, 225))
    for fr in range(0, n + 1, 2):
        d.line([X(fr), y1, X(fr), y1 + 4], fill=(0, 0, 0)); d.text((X(fr) - 5, y1 + 6), str(fr), fill=(0, 0, 0))
    for ci, cv in enumerate(curves):
        col = cols[ci % 2]; pts = [(X(i), Y(v)) for i, v in enumerate(cv) if not np.isnan(v)]
        d.line(pts, fill=col, width=2)
        for x, y in pts:
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=col)
d.text((W - 330, 10), 'grey: installed (before)   blue: fixed', fill=(0, 0, 0))
d.text((M, H - 22), 'MM8 Dark Dwarf Walking, viewer frame (48 fps)', fill=(0, 0, 0))
out = Path(__file__).resolve().parents[1] / 'review/walk'; out.mkdir(parents=True, exist_ok=True)
img.save(out / 'walk_bob_plot.png'); print('PLOT', out / 'walk_bob_plot.png')
