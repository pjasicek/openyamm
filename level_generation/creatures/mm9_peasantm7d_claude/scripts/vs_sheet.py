#!/usr/bin/env python3
"""MM9 vs ours sheet: per row label=<mm9 prefix>=<our tiles dir>; MM9 renders <prefix>_{front,q34,back}.png (ref_renders.py, the
raw LithTech model: a mirror image of the game's actor) then our glb_frames.py tiles 0_0..0_2 (front, q34, back).
Usage: vs_sheet.py <out png> <label>=<mm9 prefix>=<tiles dir> ..."""
import sys
from PIL import Image, ImageDraw, ImageOps
H = 520
rows = []
for a in sys.argv[2:]:
    lab, pre, tiles = a.split('=')
    ims = []
    for v in ('front', 'q34', 'back'):
        im = Image.open(f'{pre}_{v}.png').convert('RGB'); bb = ImageOps.invert(im.convert('L').point(lambda x: 255 if abs(x - 107) < 3 else 0)).getbbox()
        im = im.crop(bb) if bb else im
        ims.append(im)
    for k in range(3):
        im = Image.open(f'{tiles}/0_{k}.png').convert('RGB'); ims.append(im)
    ims = [i.resize((max(1, int(i.width * H / i.height)), H)) for i in ims]
    rows.append((lab, ims))
W = max(sum(i.width for i in r) + 20 * 6 for _, r in rows)
out = Image.new('RGB', (W, (H + 30) * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(out)
for j, (lab, ims) in enumerate(rows):
    x = 0; y = j * (H + 30)
    d.text((5, y + 5), lab + ' | MM9 (raw, mirrored): front, q34, back | ours: front, q34, back', fill=(255, 255, 0))
    for i in ims:
        out.paste(i, (x, y + 30)); x += i.width + 20
out.save(sys.argv[1]); print('VS', sys.argv[1], out.size)
