#!/usr/bin/env python3
"""Head (Xhead joint) height over the fly loop, MM9 own vs before vs after, world units (model x 100), from
work/jaw/fly_series.json (root_series.py). Writes review/fly_head_height_20261030.png. Two panels: Walking, Running."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parents[2]
d = json.load(open(HERE / 'work/jaw/fly_series.json'))
SER = [('mm9', 'MM9 own fly loop (no floor pass)', (27, 175, 122), (10, 6)), ('before', 'before: per-key raise (bob)', (235, 104, 52), None),
       ('after', 'after: MM9 motion + one constant lift', (42, 120, 214), None)]
W, H, PAD = 1500, 620, 70
img = Image.new('RGB', (W, H), (252, 252, 251)); dr = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 16); small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
except OSError:
    font = small = ImageFont.load_default()
ink, muted, grid = (40, 40, 38), (110, 110, 104), (226, 226, 222)
ys = [r[1] * 100 for lab, *_ in SER for clip in ('Walking', 'Running') for r in d[lab][clip]]
y0, y1 = (min(ys) // 50) * 50 - 25, (max(ys) // 50 + 1) * 50 + 25
dr.text((PAD, 14), 'Dragon King fly loop: head height over one loop (world units, floor = 0)', fill=ink, font=font)
pw = (W - 3 * PAD) // 2
for k, clip in enumerate(('Walking', 'Running')):
    x0 = PAD + k * (pw + PAD); top, bot = 60, H - 90
    fx = lambda t, T: x0 + t / T * pw
    fy = lambda v: bot - (v - y0) / (y1 - y0) * (bot - top)
    for g in range(int(y0), int(y1) + 1, 50):
        dr.line([(x0, fy(g)), (x0 + pw, fy(g))], fill=grid); dr.text((x0 - 50, fy(g) - 8), f'{g}', fill=muted, font=small)
    T = max(r[0] for r in d['after'][clip])
    for t in range(0, int(T * 10) + 1, 2):
        dr.text((fx(t / 10, T) - 8, bot + 6), f'{t / 10:.1f}', fill=muted, font=small)
    dr.text((x0 + pw // 2 - 60, bot + 26), f'{clip} time (s)', fill=muted, font=small)
    for lab, name, col, dash in SER:
        pts = [(fx(r[0] * T / max(rr[0] for rr in d[lab][clip]), T), fy(r[1] * 100)) for r in d[lab][clip]]
        if dash:
            for i in range(0, len(pts) - 1, 2):
                dr.line(pts[i:i + 2], fill=col, width=2)
        else:
            dr.line(pts, fill=col, width=2)
        rng = (max(r[1] for r in d[lab][clip]) - min(r[1] for r in d[lab][clip])) * 100
        dr.text((pts[-1][0] - 150, pts[-1][1] - 22), f'range {rng:.0f}', fill=ink, font=small)
    dr.text((x0, 38), clip, fill=ink, font=font)
lx = PAD
for lab, name, col, dash in SER:
    dr.line([(lx, H - 40), (lx + 30, H - 40)], fill=col, width=3); dr.text((lx + 38, H - 48), name, fill=ink, font=small); lx += 470
img.save(HERE / 'review' / 'fly_head_height_20261030.png')
print('PLOT written')
