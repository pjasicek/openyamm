#!/usr/bin/env python3
"""Assemble review sheets for a prop: native sprite | enhanced sprite | LOD0 (sprite_compare.png), LOD0..3 with triangle
counts (lods.png), LOD0 turntable (turntable.png); print mean lit colour of the opaque pixels of sprite and render.
Usage: review_sheet.py <prop> <sprite_stem> [tri counts...]"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAT = os.path.join(HERE, '..', 'mm6_new_sorpigal')
prop, stem, *tris = sys.argv[1:]
R = os.path.join(HERE, prop, 'review')


def crop(im):
    im = im.convert('RGBA'); bb = im.getchannel('A').point(lambda a: 255 if a > 8 else 0).getbbox()
    return im.crop(bb) if bb else im


def fit(im, w, h):
    im = crop(im); im.thumbnail((w, h), Image.LANCZOS); return im


def mean(im):
    a = np.asarray(im.convert('RGBA'), np.float32) / 255; m = a[..., 3] > 0.5
    return (a[..., :3][m].mean(0) * 255).round(1), float(np.median(a[..., :3][m].max(1) * 255))


def sheet(items, path, W=300, H=300):
    s = Image.new('RGB', (W * len(items), H + 22), (52, 56, 52)); d = ImageDraw.Draw(s)
    for i, (label, im) in enumerate(items):
        im = fit(im, W - 10, H - 10); s.paste(im, (i * W + (W - im.width) // 2, 22 + H - 5 - im.height), im)
        d.text((i * W + 6, 5), label, fill=(255, 255, 255))
    s.save(path); print('SHEET', path)


native = Image.open(os.path.join(NAT, 'native', stem + '.png'))
enh = Image.open(os.path.join(NAT, 'enhanced', stem + '.png'))
lod0 = Image.open(os.path.join(R, 'render_lod0.png'))
sheet([('native ' + stem, native), ('enhanced ' + stem, enh), ('3D LOD0 (Eevee)', lod0)], os.path.join(R, 'sprite_compare.png'))
sheet([(f'LOD{i}' + (f'  {tris[i]} tris' if i < len(tris) else ''), Image.open(os.path.join(R, f'render_lod{i}.png')))
       for i in range(4)], os.path.join(R, 'lods.png'))
sheet([(f'yaw +{y}', Image.open(os.path.join(R, f'render_yaw{y:03d}.png'))) for y in (0, 90, 180, 270)],
      os.path.join(R, 'turntable.png'))
for label, im in (('native', native), ('enhanced', enh), ('render', lod0)):
    print('MEAN', label, *mean(im))
