#!/usr/bin/env python3
"""Six frames of every clip per tier from viewer shots (s<tier>_<clip>_<k>.png). Writes review/sheet_strips_<tier>.png"""
import json, os
from PIL import Image, ImageDraw
m = json.load(open('review/viewer/manifest.json')); cl = list(m['clips']); S = 170
for t in 'abc':
    sh = Image.new('RGB', (S * 6, S * len(cl)), (40, 40, 40))
    for r, c in enumerate(cl):
        for k in range(6):
            p = f'review/shots/s{t}_{c}_{k}.png'
            if not os.path.exists(p): continue
            im = Image.open(p).convert('RGB'); w, h = im.size; im = im.crop(((w - h) // 2, 0, (w + h) // 2, h)).resize((S, S))
            if k == 0: ImageDraw.Draw(im).text((3, 3), c, fill=(255, 255, 0))
            sh.paste(im, (k * S, r * S))
    sh.save(f'review/sheet_strips_{t}.png')
