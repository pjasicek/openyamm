#!/usr/bin/env python3
"""Leftovers copy: review/<id>/flower_lods.png (LOD0..2 eye level with triangle counts); prints each LOD's mean colour
and coverage versus LOD0 (the engine crossfades between neighbours). Usage: sheet.py <id> <tri0> <tri1> <tri2>"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the leftovers batch folder
sid, tris = sys.argv[1], sys.argv[2:5]
R = os.path.join(HERE, 'review', sid)


def on_grey(im, size=360):
    im = im.convert('RGBA'); s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    bg = Image.new('RGBA', (size, size), (120, 120, 130, 255)); bg.alpha_composite(im, ((size - im.width) // 2, size - im.height))
    return bg.convert('RGB')


def crop(path):
    im = Image.open(path).convert('RGBA'); box = im.getbbox() or (0, 0, im.width, im.height)
    return im.crop(box)


names = ['Plant', 'Plant_LOD1', 'Plant_LOD2']
lod = Image.new('RGB', (360 * 3, 380), 'white'); d = ImageDraw.Draw(lod)
stats = []
for i, n in enumerate(names):
    raw = np.asarray(Image.open(os.path.join(R, f'flower_{n}_eye.png')).convert('RGBA')).astype(float)
    m = raw[..., 3] > 128
    stats.append((raw[m][:, :3].mean(0), m.sum()))
    lod.paste(on_grey(Image.open(os.path.join(R, f'flower_{n}_eye.png'))), (i * 360, 20))
    d.text((i * 360 + 4, 4), f'{n}: {tris[i]} tris', fill='black')
lod.save(os.path.join(R, 'flower_lods.png'))
for i, n in enumerate(names):
    print(n, 'mean', stats[i][0].round(1).tolist(), 'coverage_vs_lod0', round(stats[i][1] / stats[0][1], 3),
          'diff_vs_prev', (np.abs(stats[i][0] - stats[i - 1][0]).round(1).tolist() if i else '-'))
