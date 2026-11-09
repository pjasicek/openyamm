#!/usr/bin/env python3
"""Join review/clips/<label>_<clip>_NN.png into one row per clip. Usage: sheet.py <label> <out.png> [clips]"""
import sys, glob, re
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[1]; label, out = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(str(P / 'review/clips' / f'{label}_*_*.png')))
rows = {}
for f in files:
    m = re.match(rf'{label}_(.+)_(\d\d)\.png', Path(f).name)
    if m and (len(sys.argv) < 4 or m.group(1) in sys.argv[3].split(',')):
        rows.setdefault(m.group(1), []).append(f)
w, h = Image.open(files[0]).size; cols = max(len(v) for v in rows.values())
im = Image.new('RGB', (cols * w + 90, len(rows) * h), (30, 30, 34)); d = ImageDraw.Draw(im)
for r, (clip, fs) in enumerate(rows.items()):
    d.text((4, r * h + 8), clip, fill=(255, 220, 120))
    for c, f in enumerate(fs):
        im.paste(Image.open(f).convert('RGB'), (90 + c * w, r * h))
im.save(P / out); print(im.size)
