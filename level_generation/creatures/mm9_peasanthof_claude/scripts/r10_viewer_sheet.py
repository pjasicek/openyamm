#!/usr/bin/env python3
"""Viewer before/after sheet (user review r10, 2026-11-04): per tier two rows (r9, r10) of review-viewer shots (Standing 0 s,
head focus): front close-up (the user's view, zoomed 2x) with the face midline (the mirror axis that best matches the eyes and nose
band of the r9 shot), the same with her left half mirrored onto her right, 3/4, both profiles (left shot when present).
Args: <out png> <tier> ..."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageOps
T = 400
def axis(im):
    a = np.asarray(im.convert('L'), float); h, w = a.shape; band = a[int(h * 0.30):int(h * 0.55)]
    best = None
    for c in range(int(w * 0.42), int(w * 0.58)):
        k = min(c, w - c) - 2
        e = np.mean(np.abs(band[:, c - k:c] - band[:, c + 1:c + 1 + k][:, ::-1]))
        if best is None or e < best[0]: best = (e, c)
    return best[1]
rows = []
for tier in sys.argv[2:]:
    c0 = None
    for rev in ('r9', 'r10'):
        sh = lambda v: Image.open(f'review/shots/{tier}_{rev}_{v}.png').convert('RGB')
        f = sh('hfront').crop((400, 150, 700, 450)).resize((T, T), Image.LANCZOS)
        if c0 is None: c0 = axis(f)
        m = f.copy(); k = min(c0, T - c0); m.paste(ImageOps.mirror(f.crop((c0, 0, c0 + k, T))), (c0 - k, 0))
        fl = f.copy(); ImageDraw.Draw(fl).line([(c0, 0), (c0, T)], fill=(255, 0, 0))
        others = []
        for v in ('hq34', 'hprof', 'hleft'):
            try: others.append(sh(v).crop((268, 40, 768, 540)).resize((T, T), Image.LANCZOS))
            except FileNotFoundError: others.append(Image.new('RGB', (T, T), (40, 40, 40)))
        rows.append((f'{tier} {rev}', [fl, m] + others))
labels = ['front x2 + midline', 'her left mirrored', '3/4', 'right profile', 'left profile']
s = Image.new('RGB', (T * len(labels), T * len(rows)), (40, 40, 40)); d = ImageDraw.Draw(s)
for r, (name, ims) in enumerate(rows):
    for c, im in enumerate(ims):
        s.paste(im, (c * T, r * T)); d.text((c * T + 5, r * T + 5), f'{name} {labels[c]}', fill=(255, 255, 0))
s.save(sys.argv[1]); print('R10VIEWERSHEET', sys.argv[1], s.size)
