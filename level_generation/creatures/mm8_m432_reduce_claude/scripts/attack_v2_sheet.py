#!/usr/bin/env python3
"""Attack v2 review sheet: native m432Aa-Ah (views 0 and 2) against the reduced model with Attack v2 and the installed
model (old Attack), viewer shots front/left at the eight native steps -> review/attack_v2/sheet_native_new_old.png."""
from pathlib import Path
from PIL import Image, ImageDraw
P = Path(__file__).resolve().parents[1]; S = P / 'review/shots'; N = P.parent / 'mm8_m432/aligned_2x'
times = [0, 0.23, 0.46, 0.69, 0.92, 1.15, 1.37, 1.60]; W, H = 230, 280; LW = 90


def crop3d(path):
    im = Image.open(path).convert('RGB'); w, h = im.size
    return im.crop((int(w * .2), 0, int(w * .8), h)).resize((W, H))


def native(path):
    im = Image.open(path).convert('RGBA'); bg = Image.new('RGBA', im.size, (40, 44, 52, 255)); bg.alpha_composite(im)
    im = bg.convert('RGB'); s = min(W / im.width, H / im.height); im = im.resize((int(im.width * s), int(im.height * s)))
    out = Image.new('RGB', (W, H), (40, 44, 52)); out.paste(im, ((W - im.width) // 2, H - im.height)); return out


rows = [('native v0', lambda i: native(N / f'm432a{"abcdefgh"[i]}0.png')),
        ('v2 front', lambda i: crop3d(S / f'm432_a_r75_f{i}.png')),
        ('old front', lambda i: crop3d(S / f'm432_a_r100_f{i}.png')),
        ('native v2', lambda i: native(N / f'm432a{"abcdefgh"[i]}2.png')),
        ('v2 left', lambda i: crop3d(S / f'm432_a_r75_l{i}.png')),
        ('old left', lambda i: crop3d(S / f'm432_a_r100_l{i}.png'))]
sheet = Image.new('RGB', (LW + W * 8, H * len(rows)), (24, 24, 28)); d = ImageDraw.Draw(sheet)
for r, (label, get) in enumerate(rows):
    d.text((6, r * H + H // 2), label, fill=(255, 255, 255))
    for i in range(8):
        sheet.paste(get(i), (LW + i * W, r * H))
        if r == 0:
            d.text((LW + i * W + 4, 4), f'{"abcdefgh"[i]} {i * 125} ms / 3D {times[i]:.2f} s', fill=(255, 255, 0))
out = P / 'review/attack_v2/sheet_native_new_old.png'; sheet.save(out); print(out, sheet.size)
