#!/usr/bin/env python3
"""review/overview.png: every species' x2 sprite above its LOD0 front render (no shadow maps, the engine default).
Usage: overview.py <id> ..."""
import os, sys
from PIL import Image, ImageDraw
import common
ids = sys.argv[1:]
cell = 260
sheet = Image.new('RGBA', (cell * len(ids), 2 * cell + 40), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
for k, sid in enumerate(ids):
    spec = common.load(sid)
    for row, path in enumerate((spec['sprite_path'], os.path.join(spec['work'], 'qkn_Tree_eye.png'))):
        im = Image.open(path).convert('RGBA'); im = im.crop(im.getbbox())
        s = min((cell - 10) / im.width, (cell - 10) / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        sheet.alpha_composite(im, (k * cell + (cell - im.width) // 2, 20 + row * cell + cell - im.height))
    d.text((k * cell + 4, 4), sid, fill=(0, 0, 0, 255))
sheet.convert('RGB').save(os.path.join(common.TREES, 'review', 'overview.png'))
