#!/usr/bin/env python3
"""Review sheets from review.py output: review/<id>/compare.png (native sprite | LOD0 front | three-quarter | back)
and review/<id>/lods.png (every LOD from the front, same scale, with triangle counts). Prints each LOD's mean colour
and coverage against LOD0 and the previous level (the engine crossfades neighbours), and the sprite's mean colour
next to LOD0's front. Usage: sheet.py <id> <tris0> <tris1> ..."""
import glob, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sid, tris = sys.argv[1], sys.argv[2:]
R = os.path.join(HERE, 'review', sid)
SPRITE = sorted(glob.glob(os.path.join(REPO, 'assets_dev', 'engine', 'decorations_x2', sid + '_p*.png')))[0]
T = 400


def tile(im, bg=(128, 136, 150)):
    im = im.convert('RGBA'); box = im.getbbox() or (0, 0, im.width, im.height); im = im.crop(box)
    s = T * 0.94 / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    canvas = Image.new('RGBA', (T, T), bg + (255,)); canvas.alpha_composite(im, ((T - im.width) // 2, T - im.height - 6))
    return canvas.convert('RGB')


def stats(path):
    a = np.asarray(Image.open(path).convert('RGBA')).astype(float); m = a[..., 3] > 128
    return a[m][:, :3].mean(0), m.sum()


def row(images, labels, out):
    sheet = Image.new('RGB', (T * len(images), T + 20), 'white'); d = ImageDraw.Draw(sheet)
    for i, (im, label) in enumerate(zip(images, labels)):
        sheet.paste(tile(im), (i * T, 20)); d.text((i * T + 6, 4), label, fill='black')
    sheet.save(out); print('SHEET', out)


views = ['front', 'three_quarter', 'back']
row([Image.open(SPRITE)] + [Image.open(os.path.join(R, f'lod0_{v}.png')) for v in views],
    ['native ' + os.path.basename(SPRITE)] + ['LOD0 ' + v.replace('_', '-') for v in views], os.path.join(R, 'compare.png'))
levels = sorted(glob.glob(os.path.join(R, 'level*.png')))
row([Image.open(p) for p in levels], [f'LOD{i}: {tris[i] if i < len(tris) else "?"} tris' for i in range(len(levels))],
    os.path.join(R, 'lods.png'))
st = [stats(p) for p in levels]
sprite = np.asarray(Image.open(SPRITE).convert('RGBA')).astype(float)
print('sprite mean', sprite[sprite[..., 3] > 128][:, :3].mean(0).round(1).tolist(), 'LOD0 front mean',
      stats(os.path.join(R, 'lod0_front.png'))[0].round(1).tolist())
for i, (mean, cov) in enumerate(st):
    print(f'LOD{i}', 'mean', mean.round(1).tolist(), 'coverage_vs_lod0', round(cov / st[0][1], 3),
          'diff_vs_prev', np.abs(mean - st[i - 1][0]).round(1).tolist() if i else '-',
          'coverage_vs_prev', round(cov / st[i - 1][1], 3) if i else '-')
