#!/usr/bin/env python3
"""Review sheets from viewer shots (review/shots/<tier>_<name>.png) and the MM9 reference renders (references_hd/mm9/).
Writes review/sheet_mm9_vs_ours.png, review/sheet_tiers.png, review/sheet_face.png. Project folder."""
import numpy as np
from PIL import Image, ImageDraw


def fig(path, pad=20):
    im = Image.open(path).convert('RGB')
    if 'review/shots/' in path:            # viewer shots: fixed frame (the floor grid defeats the background test)
        return im.crop((300, 140, 736, 752)) if '_r' in path.rsplit('/', 1)[1][7:] else im.crop((230, 90, 806, 752))
    a = np.asarray(im).astype(int)
    bg = a[min(a.shape[0] - 1, 40), 5]
    m = np.abs(a - bg).sum(-1) > 45
    m[:30] = False; m[-40:] = False
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        return im
    return im.crop((max(xs.min() - pad, 0), max(ys.min() - pad, 0), min(xs.max() + pad, im.width), min(ys.max() + pad, im.height)))


def grid(rows, labels, out, cw=300, ch=420):
    sheet = Image.new('RGB', (cw * max(len(r) for r in rows) + 150, ch * len(rows)), (35, 35, 35))
    d = ImageDraw.Draw(sheet)
    for r, (row, lab) in enumerate(zip(rows, labels)):
        d.text((6, r * ch + ch // 2), lab, fill=(255, 255, 255))
        for c, im in enumerate(row):
            im = im.copy(); im.thumbnail((cw, ch))
            sheet.paste(im, (150 + c * cw + (cw - im.width) // 2, r * ch + (ch - im.height) // 2))
    sheet.save(out)


R, S = 'references_hd/mm9/', 'review/shots/'
grid([[fig(R + f'{t}_{v}.png') for v in ('q34', 'front', 'left', 'back')] if k == 'mm9' else
      [fig(S + f'phom1_{t}_{v}.png') for v in ('r1', 'r0', 'r3', 'r2')]
      for t in 'ab' for k in ('mm9', 'ours')],
     ['MM9 rows 57/60 (HOM1a)', 'ours phom1_a', 'MM9 row 58 (HOM1b)', 'ours phom1_b'], 'review/sheet_mm9_vs_ours.png')
grid([[fig(S + f'phom1_{t}_{v}.png') for v in ('r0', 'r1', 'r3', 'r2', 'ar', 'ft')] for t in 'ab'],
     ['phom1_a (57, 60)', 'phom1_b (58)'], 'review/sheet_tiers.png')
grid([[fig(R + f'head_{t}_{v}.png', 5) for v in ('front', 'q34', 'left', 'back')] if k == 'mm9' else
      [fig(S + f'phom1_{t}_{v}.png', 5) for v in ('hf', 'hq', 'hl', 'hb')]
      for t in 'ab' for k in ('mm9', 'ours')],
     ['MM9 head (HOM1a)', 'ours phom1_a', 'MM9 head (HOM1b)', 'ours phom1_b'], 'review/sheet_face.png', 380, 380)
print('sheets written')
