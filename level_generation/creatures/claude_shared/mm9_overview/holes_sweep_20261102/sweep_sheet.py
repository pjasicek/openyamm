#!/usr/bin/env python3
"""Contact sheet of the see-through sweep (2026-11-02): one row per body, its worst gate shot per cloth zone (sleeves,
boots, trousers, torso, collar; head listed separately: beard sheets and eyes), holes in yellow, views into an opening in
red, on a flat grey silhouette, cropped on the holes; the row label gives the zone maxima (pixels of 4 mm, any view /
party view 20 deg down).
Usage (this folder): sweep_sheet.py <out png> <body> [...]   (reads <body>/see_through.json and its shots)"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
out, bodies = sys.argv[1], sys.argv[2:]
CELL, LW, COLS = 230, 330, 5
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)
    small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
except OSError:
    font = small = ImageFont.load_default()
CLOTH = ('sleeve', 'boot', 'trousers', 'torso', 'collar')
rows = []
for b in bodies:
    d = json.load(open(HERE / b / 'see_through.json'))
    summ = d['summary']
    shots = sorted(d['shots'], key=lambda s: -s['hole_px'])
    pick, seen = [], set()
    for s in shots:
        z = s['zone'].split(' ')[0]
        if z in CLOTH and s['zone'] not in seen and s['hole_px'] >= 3:
            seen.add(s['zone']); pick.append(s)
    lines = [f'{b}  ({len(d["clips"])} clips, every {d["step"]}th frame)']
    for z, s in sorted(summ.items(), key=lambda kv: -kv[1]['hole_max']):
        if s['hole_max'] < 3 or z == 'none':
            continue
        e = s.get('hole_max_by_elev', {})
        lines.append(f'{z}: {s["hole_max"]} px ({e.get("0", "?")}/{e.get("20", "?")}) '
                     f'{s["worst"][0]} f{s["worst"][1]} {s["worst"][2]}; {s["clips_with_holes"]} clips')
    rows.append((lines, pick[:COLS]))
H = 30 + CELL * len(rows)
sheet = Image.new('RGB', (LW + CELL * COLS, H), (24, 24, 28))
dr = ImageDraw.Draw(sheet)
dr.text((6, 6), 'See-through sweep 2026-11-02 (mm9_peasantdm2_claude/scripts/see_through_gate.py; render only): '
        'yellow = background through cloth, red = view into an opening; px = 4 mm pixels, (level / party 20 deg)',
        fill=(255, 220, 120), font=font)
for j, (lines, pick) in enumerate(rows):
    y = 30 + j * CELL
    dr.line([(0, y), (sheet.size[0], y)], fill=(70, 70, 70))
    for k, t in enumerate(lines[:14]):
        dr.text((6, y + 6 + 15 * k), t, fill=(230, 230, 230) if k == 0 else (190, 190, 190), font=font if k == 0 else small)
    for i, s in enumerate(pick):
        im = Image.open(s['png']).convert('RGB')
        a = np.asarray(im)
        ys, xs = np.nonzero((a[..., 0] > 240) & (a[..., 1] > 190) & (a[..., 1] < 240) & (a[..., 2] < 40))
        if len(ys):                       # crop on the holes (square, at least 140 px, 50 px around them)
            cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
            half = max(70, (max(np.ptp(xs), np.ptp(ys)) + 100) / 2)
            im = im.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half)))
        im = im.resize((CELL - 18, CELL - 18), Image.NEAREST)
        x = LW + i * CELL
        sheet.paste(im, (x + (CELL - im.size[0]) // 2, y + 16))
        dr.text((x + 4, y + 2), f'{s["zone"]} {s["clip"]} f{s["frame30"]} {s["view"]}: {s["hole_px"]}', fill=(255, 255, 0),
                font=small)
sheet.save(out)
print('SWEEP_SHEET', out, sheet.size)
