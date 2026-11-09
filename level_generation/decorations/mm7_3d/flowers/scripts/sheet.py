#!/usr/bin/env python3
"""Review sheet review/<id>_sheet.png: row 1 the restored x2 sprite | LOD0 front | three-quarter | top, the sprite and
the front render at the same metres per pixel; row 2 LOD0 | LOD1 | LOD2 front with triangle counts. Prints the mean
colour of flower and foliage pixels (common.flower_mask) in the sprite and the front render, and each LOD's coverage
and mean colour against LOD0. --grade multiplies the atlas grading gains (work/<atlas>/grade.json) by the damped
sprite/render ratio of each group (only the atlas's own species grades it). Usage: sheet.py <id> [--grade]"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import HERE, UNITS, atlas_of, dims, flower_mask, sprite_path, work

SID = sys.argv[1]
W, H = dims(SID)
R = os.path.join(HERE, 'review')
TILE = 420
STATS = os.path.join(work(SID), 'stats.txt')
tris = open(STATS).read().split() if os.path.exists(STATS) else ['?'] * 4


def load(path):
    return Image.open(path).convert('RGBA')


front = load(os.path.join(R, f'{SID}_Plant_front.png'))
render_ppm = front.width / (max(W, H) * 1.25)
sprite = load(sprite_path(SID))
sprite_ppm = 2 * UNITS
k = render_ppm / sprite_ppm
sprite_scaled = sprite.resize((max(1, int(sprite.width * k)), max(1, int(sprite.height * k))), Image.LANCZOS)


def tile(im, bottom=True):
    box = im.getbbox() or (0, 0, im.width, im.height)
    im = im.crop(box)
    return im


crops = [tile(sprite_scaled), tile(front), tile(load(os.path.join(R, f'{SID}_Plant_three_quarter.png'))),
         tile(load(os.path.join(R, f'{SID}_Plant_top.png')))]
s = min(TILE / max(max(c.width, c.height) for c in crops[:2]), 1.0)


def place(im, factor, label):
    im = im.resize((max(1, int(im.width * factor)), max(1, int(im.height * factor))), Image.LANCZOS)
    bg = Image.new('RGBA', (TILE, TILE), (128, 128, 136, 255))
    bg.alpha_composite(im, ((TILE - im.width) // 2, TILE - im.height - 6 if im.height < TILE - 6 else 0))
    d = ImageDraw.Draw(bg)
    d.text((6, 6), label, fill=(255, 255, 255, 255))
    return bg.convert('RGB')


labels = ['native x2 sprite', 'LOD0 front', 'LOD0 three-quarter', 'LOD0 top']
tiles = [place(c, s if i < 2 else min(TILE / max(c.width, c.height), 1.0), l)
         for i, (c, l) in enumerate(zip(crops, labels))]
lod_imgs = [load(os.path.join(R, f'{SID}_{n}_front.png')) for n in ('Plant', 'Plant_LOD1', 'Plant_LOD2')]
lod_tiles = [place(tile(im), s, f'{n}: {t} tris') for im, n, t in zip(lod_imgs, ('LOD0', 'LOD1', 'LOD2'), tris[:3])]
sheet = Image.new('RGB', (TILE * 4 + 30, TILE * 2 + 50), 'white')
d = ImageDraw.Draw(sheet)
size_mb = int(tris[3]) / 1e6 if tris[3] != '?' else 0
d.text((6, 4), f'{SID}  mm7_deco_{SID}.glb  {W:.2f} x {H:.2f} m  file {size_mb:.2f} MB',
       fill='black')
for i, t in enumerate(tiles):
    sheet.paste(t, (i * (TILE + 10), 20))
for i, t in enumerate(lod_tiles):
    sheet.paste(t, (i * (TILE + 10), TILE + 40))
sheet.save(os.path.join(R, f'{SID}_sheet.png'))


def groups(im):
    a = np.asarray(im).astype(float) / 255
    m = a[..., 3] > 0.5
    rgb = a[m][:, :3]
    fm = flower_mask(SID, rgb)
    return rgb.mean(0), rgb[fm].mean(0) if fm.any() else rgb.mean(0), rgb[~fm].mean(0), fm.mean(), m.sum()


sp, rn = groups(sprite), groups(front)
fmt = lambda v: (np.asarray(v) * 255).round().astype(int).tolist()
print(f'{SID} sprite all {fmt(sp[0])} flower {fmt(sp[1])} foliage {fmt(sp[2])} flower% {sp[3]:.2f}')
print(f'{SID} render all {fmt(rn[0])} flower {fmt(rn[1])} foliage {fmt(rn[2])} flower% {rn[3]:.2f}')
base = groups(lod_imgs[0])
for n, im in zip(('LOD1', 'LOD2'), lod_imgs[1:]):
    g = groups(im)
    print(f'{SID} {n} coverage {g[4] / base[4]:.3f} mean diff {fmt(np.abs(g[0] - base[0]))}')
if '--grade' in sys.argv and atlas_of(SID) == SID and not os.environ.get('FLOWERS_CPU'):   # Eevee renders only
    path = os.path.join(work(SID), 'grade.json')
    gains = json.load(open(path)) if os.path.exists(path) else {}
    for name, i in (('flower', 1), ('foliage', 2)):
        ratio = np.clip((sp[i] / np.maximum(rn[i], 1e-3)) ** 0.85, 0.7, 1.45)
        if name == 'flower':     # brightness only (the painted hue is kept), capped: bright petals clip
            ratio = np.full(3, np.clip(float(np.mean(ratio)), 0.8, 1.15))
        total = np.array(gains.get(name, [1, 1, 1])) * ratio
        if name == 'flower':
            total = np.clip(total, 0.75, 1.25)
        gains[name] = total.round(3).tolist()
    json.dump(gains, open(path, 'w'))
    print('GRADE', SID, gains)
