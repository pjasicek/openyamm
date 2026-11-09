#!/usr/bin/env python3
"""Review sheets from the viewer shots (review/shots/) and the MM9 renders (review/mm9/, ref_renders.py of the raw
conversion, which is the mirror image of the game actor): review/sheet_mm9_vs_ours.png and review/sheet_tiers.png."""
from PIL import Image, ImageDraw
import numpy as np


def crop_fig(im, pad=30):
    a = np.asarray(im.convert('RGB')).astype(int); h, w, _ = a.shape
    bg = np.median(a[:h // 3, :w // 6].reshape(-1, 3), 0)
    d = np.abs(a - bg).sum(-1); d[int(h * 0.85):] = 0
    ys, xs = np.nonzero(d > 60)
    cx = np.median(xs); m = np.abs(xs - cx) < w * 0.3; ys, xs = ys[m], xs[m]
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    s = max(y1 - y0, x1 - x0) // 2 + pad; cy = (y0 + y1) // 2; cx = (x0 + x1) // 2
    return im.crop((cx - s, cy - s, cx + s, cy + s))


def fit(im, w, h):
    im = im.convert('RGB'); bg = Image.new('RGB', (w, h), (110, 110, 110))
    im = im.resize((w, int(im.height * w / im.width))) if im.width / im.height > w / h else im.resize((int(im.width * h / im.height), h))
    bg.paste(im, ((w - im.width) // 2, (h - im.height) // 2)); return bg


W, H = 360, 420
rows = []
for t in 'ab':
    mm = [Image.open(f'review/mm9/pdm1{t}_{v}.png').crop((150, 60, 618, 740)) for v in ('front', 'q34', 'left', 'back')]
    ours = [crop_fig(Image.open(f'review/shots/pdm1_{t}_{v}.png')) for v in ('front', 'quarter', 'left', 'back')]
    rows.append(('MM9 ' + t.upper() + ' (raw conversion: mirror image)', mm)); rows.append(('ours ' + t.upper(), ours))
s = Image.new('RGB', (W * 4, H * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(s)
for r, (lab, ims) in enumerate(rows):
    for c, im in enumerate(ims):
        s.paste(fit(im, W, H), (c * W, r * H))
    d.text((8, r * H + 8), lab, fill=(255, 255, 0))
s.save('review/sheet_mm9_vs_ours.png')
s = Image.new('RGB', (W * 4, H * 2), (40, 40, 40)); d = ImageDraw.Draw(s)
for r, t in enumerate('ab'):
    for c, v in enumerate(('front', 'quarter', 'headfront', 'headquarter')):
        im = Image.open(f'review/shots/pdm1_{t}_{v}.png')
        s.paste(fit(crop_fig(im) if 'head' not in v else im, W, H), (c * W, r * H))
    d.text((8, r * H + 8), f'tier pdm1_{t}', fill=(255, 255, 0))
s.save('review/sheet_tiers.png')
print('SHEETS done')
