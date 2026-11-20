#!/usr/bin/env python3
"""MM9-vs-ours review sheets (project folder). MM9: renders of PEASANTM3.abc with each skin (references_hd/mm9/,
ref_renders.py; LithTech's left-handed numbers, so MM9's renders are the mirror image of the game actor: mirrored here so
both columns show the same handedness). Ours: review-viewer shots (review/shots/<tier>_<view>.png, run_creature_review.py).
Writes review/sheet_mm9_vs_ours.png (body: front, quarter, back, left per tier; MM9 row above ours) and
review/sheet_faces_vs_mm9.png (head: front, quarter, left, right per tier)."""
from PIL import Image, ImageDraw, ImageOps

S = 360


def tile(p, mirror=False, crop=None, fit=False):
    im = Image.open(p).convert('RGB')
    if crop:
        im = im.crop(crop)
    if fit:     # viewer shots: crop to the figure (pixels away from the flat background), 4 % margin
        import numpy as np
        a = np.asarray(im).astype(int)
        bg = a[5, a.shape[1] // 2]
        m = np.abs(a - bg).sum(-1) > 40
        m[int(a.shape[0] * 0.85):, :int(a.shape[1] * 0.4)] = False      # the viewer's label box
        ys, xs = np.nonzero(m)
        if len(xs):
            cx, cy = (xs.min() + xs.max()) // 2, (ys.min() + ys.max()) // 2
            h = int(max(xs.max() - xs.min(), ys.max() - ys.min()) * 0.54) + 4
            im = im.crop((cx - h, cy - h, cx + h, cy + h))
    if mirror:
        im = ImageOps.mirror(im)
    w, h = im.size
    k = S / max(w, h)
    im = im.resize((int(w * k), int(h * k)))
    t = Image.new('RGB', (S, S), (90, 92, 98))
    t.paste(im, ((S - im.width) // 2, (S - im.height) // 2))
    return t


def sheet(rows, out):
    W = max(len(r[1]) for r in rows) * S
    img = Image.new('RGB', (W, len(rows) * S), (40, 40, 40))
    d = ImageDraw.Draw(img)
    for i, (label, tiles) in enumerate(rows):
        for j, t in enumerate(tiles):
            img.paste(t, (j * S, i * S))
        d.text((6, i * S + 6), label, fill=(255, 255, 0))
    img.save(out)
    print('SHEET', out, img.size)


body, face = [], []
for t, T in (('a', 'A (row 52)'), ('b', 'B (row 45)')):
    # MM9 'left' camera shows the model's left side; mirrored, it matches the game actor's right side (our 'right' shot)
    body.append((f'MM9 {T}', [tile(f'references_hd/mm9/{t}_{v}.png', True, (96, 40, 672, 728))
                             for v in ('front', 'q34', 'back', 'left')]))
    body.append((f'ours {T}', [tile(f'review/shots/pm3_{t}_{v}.png', False, (308, 230, 728, 720)) for v in ('bf', 'bq', 'bb', 'br')]))
    face.append((f'MM9 {T}', [tile(f'references_hd/mm9/h{t}_{v}.png', True, (40, 0, 472, 400))
                             for v in ('front', 'q34', 'left', 'right')]))
    face.append((f'ours {T}', [tile(f'review/shots/pm3_{t}_{v}.png', False, (318, 120, 718, 520))
                               for v in ('hf', 'hq', 'hr', 'hl')]))
sheet(body, 'review/sheet_mm9_vs_ours.png')
sheet(face, 'review/sheet_faces_vs_mm9.png')
