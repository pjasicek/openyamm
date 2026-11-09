#!/usr/bin/env python3
"""Hair/head silhouette overlay (finishing round 2026-11-04, coordinator note "fit the hair to MM9's silhouette (overlay)"): MM9's
head outline (review/hair_overlay/mm9_*.png from head_sil.py; the side view mirrored: the raw conversion is the mirror image)
drawn in cyan over ours (ours_*.png), same ortho scale; front aligned on the crown top and the head's centre line, side on the
crown top and the back of the head. Only the part above the ear tips is compared (braids and shoulders differ by design).
Prints the crown width at 2/4/6/8 cm below the top for both. Writes review/hair_overlay/overlay.png."""
import numpy as np
from PIL import Image, ImageOps, ImageDraw
from scipy import ndimage
D = 'review/hair_overlay/'
out = []; px = 0.5 / 600
for v in ('front', 'side'):
    a = Image.open(D + f'mm9_{v}.png').convert('RGBA'); b = Image.open(D + f'ours_{v}.png').convert('RGBA')
    if v == 'side':
        a = ImageOps.mirror(a)
    A = np.asarray(a)[..., 3] > 128; B = np.asarray(b)[..., 3] > 128
    def top(M): return np.nonzero(M.any(1))[0][0]
    ta, tb = top(A), top(B)
    def ref_x(M, t):
        band = M[t + 10:t + 60]; xs = np.nonzero(band.any(0))[0]
        return (xs[0] + xs[-1]) / 2 if v == 'front' else xs[-1] if False else xs[0]
    dy = tb - ta; dx = int(round(ref_x(B, tb) - ref_x(A, ta)))
    A2 = np.roll(np.roll(A, dy, 0), dx, 1)
    edge = A2 & ~ndimage.binary_erosion(A2, iterations=2)
    im = np.asarray(b.convert('RGB')).copy(); im[edge] = (0, 255, 255)
    t = tb; rows = []
    for cm in (2, 4, 6, 8):
        y = t + int(cm / 100 / px)
        wa = A2[y].sum() * px * 100; wb = B[y].sum() * px * 100
        rows.append(f'{cm} cm: MM9 {wa:.1f} ours {wb:.1f} cm')
    print('HAIROVERLAY', v, '; '.join(rows))
    I = Image.fromarray(im); ImageDraw.Draw(I).text((8, 8), f'{v}: MM9 outline cyan', fill=(255, 255, 0)); out.append(I)
s = Image.new('RGB', (1200, 600)); s.paste(out[0], (0, 0)); s.paste(out[1], (600, 0)); s.save(D + 'overlay.png')
