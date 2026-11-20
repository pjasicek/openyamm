#!/usr/bin/env python3
"""Review sheet for one species (after build.sh): review/<id>/sheet.png = row 1: native x2 sprite | LOD0 front (eye
level) | three-quarter | side (Eevee, sun + sky, with shadows) | LOD0 front without shadow maps (engine default), with
mean colour and luminance 5/50/95 percentiles; below it lod_consistency.png (every LOD at a common size and at its
in-game size, no shadow maps). Usage: review_sheet.py <id>"""
import os, subprocess
import numpy as np
from PIL import Image, ImageDraw
import common
spec = common.load(); W = spec['work']; R = spec['review']
subprocess.run(['python3', os.path.join(common.TREES, 'scripts', 'quick.py'), spec['id']], check=True,
               stdout=subprocess.DEVNULL)


def stats(im):
    x = np.asarray(im).astype(float); m = x[..., 3] > 128; l = x[..., :3] @ [0.3, 0.59, 0.11]
    return x[m][:, :3].mean(0).round(0).astype(int).tolist(), np.percentile(l[m], [5, 50, 95]).round(0).astype(int).tolist()


files = [spec['sprite_path']] + [os.path.join(W, f) for f in ('qk_Tree_eye.png', 'qk_Tree_three_quarter.png',
                                                               'qk_Tree_side.png', 'qkn_Tree_eye.png')]
labels = [f"{spec['sprite']} sprite (x2)", 'LOD0 front', 'LOD0 three-quarter', 'LOD0 side', 'LOD0 front, no shadow maps']
ims = [Image.open(f).convert('RGBA') for f in files]
ims = [i.crop(i.getbbox()) for i in ims]
ims = [i.resize((int(i.width * 520 / i.height), 520), Image.LANCZOS) for i in ims]
lods = Image.open(os.path.join(R, 'lod_consistency.png')).convert('RGBA')
cell = max(max(i.width for i in ims), 300) + 12
width = max(cell * len(ims), lods.width)
sheet = Image.new('RGBA', (width, 580 + lods.height), (150, 160, 175, 255)); d = ImageDraw.Draw(sheet)
for k, (im, label) in enumerate(zip(ims, labels)):
    x = k * cell
    sheet.alpha_composite(im, (x + (cell - im.width) // 2, 50))
    d.text((x + 4, 4), label, fill=(0, 0, 0, 255)); d.text((x + 4, 20), f'{stats(im)}', fill=(0, 0, 0, 255))
sheet.alpha_composite(lods, (0, 580))
sheet.convert('RGB').save(os.path.join(R, 'sheet.png'))
print('SHEET', os.path.join(R, 'sheet.png'))
