#!/usr/bin/env python3
"""Full body vs MM9 sheet (finishing round 2026-11-04): per tier one row of MM9's renders (review/mm9/<tier>_{front,q34,left,back},
raw conversion = mirror image, flipped here to game handedness) and one row of our viewer shots
(review/shots/<tier>_<rev>_{body,body34,side,back}). Args: <out png> <rev>"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
sys.path.insert(0, 'scripts/from_dm2')
out, rev = sys.argv[1], sys.argv[2]


def crop_fig(im, pad=24):
    a = np.asarray(im.convert('RGB')).astype(int); h, w, _ = a.shape
    bg = np.median(a[h // 5:2 * h // 5, w // 50:w // 12].reshape(-1, 3), 0)
    d = np.abs(a - bg).sum(-1); d[int(h * 0.88):, :int(w * 0.4)] = 0; d[int(h * 0.985):] = 0; d[:int(h * 0.06)] = 0; d[:, :int(w * 0.02)] = 0
    ys, xs = np.nonzero(d > 60)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    s = max(y1 - y0, x1 - x0) // 2 + pad; cy = (y0 + y1) // 2; cx = (x0 + x1) // 2
    return im.crop((cx - s, cy - s, cx + s, cy + s))


W = 340
rows = []
for t in ('phof1_a', 'phof1_b', 'phof2_c'):
    k = t.replace('_', '')
    mm = [crop_fig(ImageOps.mirror(Image.open(f'review/mm9/{k}_{v}.png').convert('RGB'))) for v in ('front', 'q34', 'left', 'back')]
    ours = [crop_fig(Image.open(f'review/shots/{t}_{rev}_{v}.png').convert('RGB')) for v in ('body', 'body34', 'side', 'back')]
    rows.append((f'{t} MM9', mm)); rows.append((f'{t} ours ({rev})', ours))
s = Image.new('RGB', (W * 4, W * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(s)
for r, (lab, ims) in enumerate(rows):
    for c, im in enumerate(ims):
        s.paste(im.resize((W, W), Image.LANCZOS), (c * W, r * W))
    d.text((6, r * W + 6), lab, fill=(255, 255, 0))
s.save(out); print('BODYSHEET', out, s.size)
