#!/usr/bin/env python3
"""Review sheets from render_review.py output: review/<id>_compare.png (native sprite | enhanced | LOD0 eye level |
LOD0 three-quarter) and review/<id>_lods.png (LOD0..2 eye level with triangle counts); prints each LOD's mean colour
and coverage versus LOD0 (the engine crossfades between neighbours). Usage: sheet.py <id> <tri0> <tri1> <tri2>"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPR = os.path.join(HERE, '..', '..', 'mm6_new_sorpigal')
sid, tris = sys.argv[1], sys.argv[2:5]
R = os.path.join(HERE, 'review')


def on_grey(im, size=360):
    im = im.convert('RGBA'); s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    bg = Image.new('RGBA', (size, size), (120, 120, 130, 255)); bg.alpha_composite(im, ((size - im.width) // 2, size - im.height))
    return bg.convert('RGB')


def crop(path):
    im = Image.open(path).convert('RGBA'); box = im.getbbox() or (0, 0, im.width, im.height)
    return im.crop(box)


tiles = [on_grey(Image.open(os.path.join(SPR, 'native', sid + '.png'))), on_grey(Image.open(os.path.join(SPR, 'enhanced', sid + '.png'))),
         on_grey(crop(os.path.join(R, f'{sid}_Plant_eye.png'))), on_grey(crop(os.path.join(R, f'{sid}_Plant_three_quarter.png')))]
sheet = Image.new('RGB', (360 * 4, 380), 'white'); d = ImageDraw.Draw(sheet)
for i, (t, label) in enumerate(zip(tiles, ('native', 'enhanced', '3D LOD0 eye', '3D LOD0 3/4'))):
    sheet.paste(t, (i * 360, 20)); d.text((i * 360 + 4, 4), label, fill='black')
sheet.save(os.path.join(R, f'{sid}_compare.png'))
names = ['Plant', 'Plant_LOD1', 'Plant_LOD2']
lod = Image.new('RGB', (360 * 3, 380), 'white'); d = ImageDraw.Draw(lod)
stats = []
for i, n in enumerate(names):
    raw = np.asarray(Image.open(os.path.join(R, f'{sid}_{n}_eye.png')).convert('RGBA')).astype(float)
    m = raw[..., 3] > 128
    stats.append((raw[m][:, :3].mean(0), m.sum()))
    lod.paste(on_grey(Image.open(os.path.join(R, f'{sid}_{n}_eye.png'))), (i * 360, 20))
    d.text((i * 360 + 4, 4), f'{n}: {tris[i]} tris', fill='black')
lod.save(os.path.join(R, f'{sid}_lods.png'))
for i, n in enumerate(names):
    print(n, 'mean', stats[i][0].round(1).tolist(), 'coverage_vs_lod0', round(stats[i][1] / stats[0][1], 3),
          'diff_vs_prev', (np.abs(stats[i][0] - stats[i - 1][0]).round(1).tolist() if i else '-'))
