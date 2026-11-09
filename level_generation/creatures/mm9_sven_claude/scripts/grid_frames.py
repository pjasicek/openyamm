#!/usr/bin/env python3
"""Grid sheet from a glb_frames.py .list: one row per clip, its frames side by side (all views of each frame), tiles
scaled to CELL px. Run right after glb_frames.py (it reuses /tmp tile paths). Args: <glb_frames out png> <grid png> [cell]"""
import sys
from collections import OrderedDict
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]; C = int(sys.argv[3]) if len(sys.argv) > 3 else 220
rows = OrderedDict()
for l in open(src + '.list').read().splitlines():
    p = l.split('\t'); rows.setdefault(p[0].split(':')[0], []).append((p[0], p[1:]))
ncol = max(sum(len(f) for _, f in r) for r in rows.values())
sheet = Image.new('RGB', (C * ncol, C * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(sheet)
for i, (clip, items) in enumerate(rows.items()):
    j = 0
    for label, files in items:
        for f in files:
            sheet.paste(Image.open(f).convert('RGB').resize((C, C)), (j * C, i * C)); j += 1
        d.text(((j - len(files)) * C + 4, i * C + 4), label, fill=(255, 255, 0))
sheet.save(out); print('GRID', out, sheet.size)
