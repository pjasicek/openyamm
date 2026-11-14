#!/usr/bin/env python3
"""Review sheets of the in-game captures (README.md, "In-game checks"): one per template, rows the plain template (t0),
low (t1), mid (t2), high (t3), legendary (t4) and our ground model, columns idle and mid-swing (the bow: drawing; the
shield: raised block) outdoors in daylight and in the dim dungeon. Usage: make_sheets.py <tag> [template ...] [--cell W]
(default every template captured under the tag, cells 800 wide); writes review/<template>_tiers.jpg."""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
args = sys.argv[1:]
W = 800
if '--cell' in args:
    W = int(args[args.index('--cell') + 1])
    del args[args.index('--cell'):args.index('--cell') + 2]
tag, names = args[0], args[1:]
H = W * 9 // 16
root = os.path.join(PROJECT, 'ingame', tag)
if not names:
    names = sorted({f.rpartition('_')[0] for f in os.listdir(root)})
ROWS = [('t0', 'template'), ('t1', 'low'), ('t2', 'mid'), ('t3', 'high'), ('t4', 'legendary'), ('ours', 'our model')]
COLS = [('outdoor', 'idle'), ('outdoor', 'swing'), ('indoor', 'idle'), ('indoor', 'swing')]
for name in names:
    sheet = Image.new('RGB', (W * len(COLS), H * len(ROWS)), (20, 20, 20))
    draw = ImageDraw.Draw(sheet)
    for r, (row, label) in enumerate(ROWS):
        for c, (place, shot) in enumerate(COLS):
            path = os.path.join(root, f'{name}_{place}', f'{row}_{shot}.png')
            if os.path.exists(path):
                sheet.paste(Image.open(path).convert('RGB').resize((W, H), Image.LANCZOS), (c * W, r * H))
            draw.text((c * W + 8, r * H + H // 4), f'{label} - {place} {shot}', fill=(255, 255, 0))
    out = os.path.join(PROJECT, 'review', f'{name}_tiers.jpg')
    sheet.save(out, quality=88)
    print(out)
