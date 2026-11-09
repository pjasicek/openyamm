#!/usr/bin/env python3
"""Before/after face sheet (user review r10, 2026-11-04): per tier two rows (before, after) of head_closeups.py tiles rendered with
views front,q34,q34r,rside,low34,party; the front tile gets the face midline in red (the mirror axis that best matches the eyes and
nose band of the BEFORE front tile, rows 30-55 %; the same x on both rows) and a mirrored copy of its lower half beside it, so
a lopsided jaw shows as a mismatch. Args: <out png> <tier>=<before png>,<after png> ..."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
out = sys.argv[1]
T = 300
def tiles(png):
    return [Image.open(f).convert('RGB') for f in open(png + '.list').read().splitlines()[0].split('\t')[1:]]
def axis(im):
    a = np.asarray(im.convert('L'), float); h, w = a.shape; band = a[int(h * 0.30):int(h * 0.55)]
    best = None
    for c in range(int(w * 0.42), int(w * 0.58)):
        k = min(c, w - c) - 2
        e = np.mean(np.abs(band[:, c - k:c] - band[:, c + 1:c + 1 + k][:, ::-1]))
        if best is None or e < best[0]: best = (e, c)
    return best[1]
rows = []
for spec in sys.argv[2:]:
    tier, pngs = spec.split('='); b, a = pngs.split(',')
    tb, ta = tiles(b), tiles(a); c = axis(tb[0])
    for lab, ts in (('before', tb), ('after', ta)):
        f = ts[0].copy(); w, h = f.size
        # mirrored half: her left half (image right of the axis) mirrored onto the image left, for the jaw comparison
        m = f.copy(); k = min(c, w - c)
        right = f.crop((c, 0, c + k, h)); m.paste(ImageOps.mirror(right), (c - k, 0))
        d = ImageDraw.Draw(f); d.line([(c, 0), (c, h)], fill=(255, 0, 0), width=1)
        ims = [f, m] + ts[1:6]
        rows.append((f'{tier} {lab}', [im.resize((T, T), Image.LANCZOS) for im in ims]))
labels = ['front + midline', 'front, her left mirrored', '3/4', '3/4 other side', 'profile', 'low 3/4', 'party']
s = Image.new('RGB', (T * len(labels), T * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(s)
for r, (name, ims) in enumerate(rows):
    for col, im in enumerate(ims):
        s.paste(im, (col * T, r * T)); d.text((col * T + 5, r * T + 5), f'{name} {labels[col]}', fill=(255, 255, 0))
s.save(out); print('R10SHEET', out, s.size)
