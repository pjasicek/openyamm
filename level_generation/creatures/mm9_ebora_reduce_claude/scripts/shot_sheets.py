"""Side-by-side sheets from review/shots/<tier>_{inst,red}/: per tier group, rows = shots, columns = installed | reduced |
pixel difference (x4) for the face shots. -> review/sheet_faces_<tiers>.png, review/sheet_body_<tiers>.png"""
import sys
import numpy as np
from PIL import Image, ImageDraw
S = 'review/shots'
def pair(t, shot, w):
    a = Image.open(f'{S}/{t}_inst/{shot}.png').convert('RGB'); b = Image.open(f'{S}/{t}_red/{shot}.png').convert('RGB')
    d = np.clip(np.abs(np.asarray(a, int) - np.asarray(b, int)).sum(-1) * 4, 0, 255).astype(np.uint8)
    h = int(a.height * w / a.width)
    return [x.resize((w, h)) for x in (a, b, Image.fromarray(d).convert('RGB'))], h, int((np.abs(np.asarray(a, int) - np.asarray(b, int)).sum(-1) > 24).sum())
for kind, shots, w, cols in (('faces', ['f0', 'f1', 'f2', 'f3', 'f4'], 300, 3), ('body', ['b0', 'b1', 'b2', 'b3', 'b4'], 300, 2)):
    for group in (['eb', 's1'], ['s2', 's3', 's4']):
        rows = [(t, s) for t in group for s in shots]
        _, h, _ = pair(group[0], shots[0], w)
        sheet = Image.new('RGB', (w * cols * len(shots) // len(shots) * 1, 1)); 
        sheet = Image.new('RGB', (w * cols * 1, (h + 16) * len(rows)), (20, 20, 20)); d = ImageDraw.Draw(sheet)
        for i, (t, s) in enumerate(rows):
            ims, h, n = pair(t, s, w)
            for j in range(cols):
                sheet.paste(ims[j], (j * w, i * (h + 16) + 16))
            d.text((4, i * (h + 16) + 2), f'{t} {s}: installed | reduced' + (f' | diff x4 ({n} px > 24)' if cols == 3 else ''), fill=(240, 230, 140))
        sheet.save(f'review/sheet_{kind}_{"_".join(group)}.png'); print('SHEET', kind, group)
