#!/usr/bin/env python3
"""Viewer shot sheets (review/shots/<tier>_{inst,red}/): faces (f0 front close-up, f1 3/4, f2 profile, f3 low 3/4,
f4 party) as installed | reduced | difference x4 per tier, and body (b0-b5) installed | reduced per tier.
-> review/sheet_faces_viewer.png, review/sheet_body_viewer.png"""
import numpy as np
from PIL import Image, ImageDraw
S, H = 400, 295
def load(t, k, n):
    return Image.open(f'review/shots/{t}_{k}/{n}.png').convert('RGB')
def crop(im):   # the whole viewer canvas, scaled
    return im.resize((S, H))
faces = ['f0', 'f1', 'f2', 'f3', 'f4']; body = ['b0', 'b1', 'b2', 'b3', 'b4', 'b5']
for name, shots, diff in (('faces', faces, True), ('body', body, False)):
    cols = 3 if diff else 2
    sheet = Image.new('RGB', (S * cols * 3, (H + 16) * len(shots)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for ti, t in enumerate('abc'):
        for r, n in enumerate(shots):
            a, b = crop(load(t, 'inst', n)), crop(load(t, 'red', n)); x0 = ti * cols * S; y = r * (H + 16)
            sheet.paste(a, (x0, y + 16)); sheet.paste(b, (x0 + S, y + 16))
            d.text((x0 + 4, y + 2), f'{t} {n} installed', fill=(240, 230, 140)); d.text((x0 + S + 4, y + 2), f'{t} {n} reduced', fill=(240, 230, 140))
            if diff:
                df = np.abs(np.asarray(a, int) - np.asarray(b, int)).max(2)
                sheet.paste(Image.fromarray(np.clip(df * 4, 0, 255).astype(np.uint8)).convert('RGB'), (x0 + 2 * S, y + 16))
                d.text((x0 + 2 * S + 4, y + 2), f'diff x4 (px>8: {int((df > 8).sum())})', fill=(240, 230, 140))
    sheet.save(f'review/sheet_{name}_viewer.png'); print('SHEET', name, sheet.size)
