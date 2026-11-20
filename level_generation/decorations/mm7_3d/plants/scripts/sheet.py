#!/usr/bin/env python3
"""Review sheet from review.py output: review/<id>/sheet.png = native x2 sprite | LOD0 front | three-quarter | side
| LOD0 | LOD1 | LOD2 (front, same scale, with triangle counts). Prints the sprite's mean colour next to LOD0's
front and each level's mean colour and coverage against the previous level. Usage: sheet.py <id> <tris0> ..."""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REVIEW, SPECS, SPRITES

sid, tris = sys.argv[1], sys.argv[2:]
R = os.path.join(REVIEW, sid)
SPRITE = os.path.join(SPRITES, SPECS[sid][0])
T = 360


def tile(im, scale_ref=None, bg=(128, 136, 150)):
    im = im.convert('RGBA'); box = im.getbbox() or (0, 0, im.width, im.height)
    if scale_ref is None:
        im = im.crop(box); s = T * 0.94 / max(im.size)
    else:
        s = scale_ref
        im = im.crop((0, box[1], im.width, im.height))
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    canvas = Image.new('RGBA', (T, T), bg + (255,)); canvas.alpha_composite(im, ((T - im.width) // 2, T - im.height - 6))
    return canvas.convert('RGB')


def stats(path):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(float); m = a[..., 3] > 128
    return a[m][:, :3].mean(0), m.sum()


views = ['front', 'three_quarter', 'side']
levels = sorted(glob.glob(os.path.join(R, 'level*.png')))
images = [Image.open(SPRITE)] + [Image.open(os.path.join(R, f'lod0_{v}.png')) for v in views]
labels = ['native ' + os.path.basename(SPRITE)] + ['LOD0 ' + v.replace('_', '-') for v in views]
tiles = [tile(im) for im in images]
# the levels at one common scale (that of LOD0)
ref = Image.open(levels[0]).convert('RGBA'); box = ref.getbbox()
s = T * 0.94 / max(box[2] - box[0], box[3] - box[1])
for i, p in enumerate(levels):
    tiles.append(tile(Image.open(p), s)); labels.append(f'LOD{i}: {tris[i] if i < len(tris) else "?"} tris')
sheet = Image.new('RGB', (T * len(tiles), T + 20), 'white'); d = ImageDraw.Draw(sheet)
for i, (im, label) in enumerate(zip(tiles, labels)):
    sheet.paste(im, (i * T, 20)); d.text((i * T + 6, 4), label, fill='black')
sheet.save(os.path.join(R, 'sheet.png')); print('SHEET', os.path.join(R, 'sheet.png'))
sprite = np.asarray(Image.open(SPRITE).convert('RGBA')).astype(float)
print('sprite mean', sprite[sprite[..., 3] > 128][:, :3].mean(0).round(1).tolist(), 'LOD0 front mean',
      stats(os.path.join(R, 'lod0_front.png'))[0].round(1).tolist())
st = [stats(p) for p in levels]
for i, (mean, cov) in enumerate(st):
    print(f'LOD{i}', 'mean', mean.round(1).tolist(),
          'diff_vs_prev', np.abs(mean - st[i - 1][0]).round(1).tolist() if i else '-',
          'coverage_vs_prev', round(cov / st[i - 1][1], 3) if i else '-')
