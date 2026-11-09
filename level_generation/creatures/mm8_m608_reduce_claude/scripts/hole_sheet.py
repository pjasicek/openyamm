#!/usr/bin/env python3
"""review/hole renders -> review/hole/sheet_<label>.png (rows pose, columns arms/noarms x view). Usage: hole_sheet.py <label>"""
import itertools, sys
from PIL import Image, ImageDraw
lab = sys.argv[1]; poses = ['stand', 'attack', 'hit']; S = 240
cols = list(itertools.product(['arms', 'noarms'], ['back', 'backside', 'top']))
im = Image.new('RGB', (S * len(cols), S * len(poses))); dr = ImageDraw.Draw(im)
for r, p in enumerate(poses):
    for c, (a, v) in enumerate(cols):
        im.paste(Image.open(f'review/hole/{lab}_{p}_{a}_{v}.png').convert('RGB').resize((S, S)), (c * S, r * S)); dr.text((c * S + 3, r * S + 3), f'{lab} {p} {a} {v}', fill=(255, 255, 0))
im.save(f'review/hole/sheet_{lab}.png'); print(f'review/hole/sheet_{lab}.png')
