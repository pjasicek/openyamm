#!/usr/bin/env python3
"""Native m408aa-ah (views 0 and 2) above the rendered 3D Attack frames at the matched clip times.
Usage: attack_sheet.py <frames dir> <tag> <out.png> [second tag]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
d, tag, out = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
tags = [tag] + sys.argv[4:5]
NAT = Path(__file__).resolve().parents[2] / 'mm8_m408_claude/references_native'
LET = 'abcdefgh'; MS = [0, 125, 250, 375, 500, 625, 750, 875]; CLIP = [0, .2, .4, .6, .75, .9, 1.05, 1.2]
W, H = 240, 280
rows = []
for view, native in [('front', 0), ('side', 2)]:
    rows.append(('native', [Image.open(NAT / f'm408a{l}{native}.png').convert('RGBA') for l in LET]))
    for t in tags:
        rows.append((t, [Image.open(d / f'{t}_{view}_{ms:03d}.png').convert('RGBA') for ms in MS]))
sheet = Image.new('RGB', (W * 8 + 90, H * len(rows) + 24), (24, 26, 30)); dr = ImageDraw.Draw(sheet)
for c, (l, ms, t) in enumerate(zip(LET, MS, CLIP)):
    dr.text((90 + c * W + 6, 6), f'm408a{l}  {ms} ms  ->  clip {t:.2f} s', fill=(230, 230, 230))
for r, (label, ims) in enumerate(rows):
    dr.text((6, 24 + r * H + H // 2), label, fill=(230, 230, 230))
    native = label == 'native'
    # native bitmaps share one scale: fit the tallest frame of the row, bottom aligned like the ground
    s = min(W / max(i.width for i in ims), (H - 8) / max(i.height for i in ims)) if native else None
    for c, im in enumerate(ims):
        if native:
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))))
            bg = Image.new('RGBA', (W, H), (24, 26, 30, 255)); bg.alpha_composite(im, ((W - im.width) // 2, H - 4 - im.height))
            im = bg
        else:
            im = im.resize((W, H))
        sheet.paste(im.convert('RGB'), (90 + c * W, 24 + r * H))
sheet.save(out); print('SHEET', out)
