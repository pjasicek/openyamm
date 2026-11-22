#!/usr/bin/env python3
"""texsheet.py <out.jpg> <name> ...: a contact sheet of shipped x4 texture masters (or the xeen world's), labelled."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys, glob, os
from PIL import Image, ImageDraw
R = _REPO_ROOT
out = sys.argv[1]; names = sys.argv[2:]
cell = 200; cols = 6
ims = []
for n in names:
    c = glob.glob(f'{R}/level_generation/textures_x4/masters/*/{n}.png') + glob.glob(f'{R}/assets_dev/worlds/*/textures_x2/{n}.png') + glob.glob(f'{R}/assets_dev/worlds/*/textures/{n}.png') + glob.glob(f'{R}/assets_dev/worlds/*/bitmaps/{n}.png')
    if not c:
        im = Image.new('RGB', (cell, cell), (60, 0, 60)); w, h = 0, 0
    else:
        im0 = Image.open(c[0]).convert('RGB'); w, h = im0.size
        im = im0.resize((cell, cell))
    d = ImageDraw.Draw(im); d.rectangle([0, 0, cell, 14], fill=(0, 0, 0)); d.text((2, 1), f'{n} {w}x{h}', fill=(255, 255, 0))
    ims.append(im)
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (cell * cols, cell * rows))
for i, im in enumerate(ims):
    s.paste(im, ((i % cols) * cell, (i // cols) * cell))
s.save(out, quality=85)
