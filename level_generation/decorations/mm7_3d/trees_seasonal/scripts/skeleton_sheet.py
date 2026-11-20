#!/usr/bin/env python3
"""Compose work/<id>/skeleton.png: sprites (scaled so their art height = the species' height in the 512 px frame)
and the skeleton renders. Usage: skeleton_sheet.py <id> <sprite stem> [<sprite stem> ...]"""
import os, sys
import numpy as np
from PIL import Image
import common
spec = common.load(sys.argv[1]); W = spec['work']
panels = []
for stem in sys.argv[2:]:
    im = Image.open(os.path.join(common.SPRITES, stem + '.png')).convert('RGBA')
    im = im.crop(im.getbbox()); s = 512 / im.height
    im = im.resize((max(1, int(im.width * s)), 512), Image.LANCZOS)
    c = Image.new('RGBA', (512, 512)); c.alpha_composite(im, ((512 - im.width) // 2, 0)); panels.append(c)
for v in ('front', 'side'):
    panels.append(Image.open(os.path.join(W, f'skel_{v}.png')).convert('RGBA'))
sheet = Image.new('RGBA', (512 * len(panels), 512), (150, 160, 175, 255))
for k, p in enumerate(panels):
    sheet.alpha_composite(p, (512 * k, 0))
sheet.convert('RGB').save(os.path.join(W, 'skeleton.png'))
