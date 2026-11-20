#!/usr/bin/env python3
"""glb_close.py renders -> side-by-side sheet: per spot one row installed | candidate (textured), installed | candidate
(clay), and |difference| x4 of the textured pair. Usage: close_sheet.py <instlabel> <candlabel> <out.png> <spot,...> [size]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
A, B, out, spots = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
W = int(sys.argv[5]) if len(sys.argv) > 5 else 300
D = 'review/glbclose'
cols = 5
sh = Image.new('RGB', (cols * W, len(spots) * (W + 16)), (25, 25, 25)); d = ImageDraw.Draw(sh)
for r, s in enumerate(spots):
    y = r * (W + 16)
    ims = [Image.open(f'{D}/{x}_{s}_{m}.png').convert('RGB') for m in ('tex', 'clay') for x in (A, B)]
    diff = np.abs(np.asarray(ims[0], float) - np.asarray(ims[1], float)).max(-1)
    ims.append(Image.fromarray(np.clip(diff * 4, 0, 255).astype(np.uint8)).convert('RGB'))
    labels = [f'{A} tex', f'{B} tex', f'{A} clay', f'{B} clay', f'|diff|x4 >8: {(diff > 8).mean() * 100:.1f}%']
    for j, (im, lb) in enumerate(zip(ims, labels)):
        sh.paste(im.resize((W, W)), (j * W, y + 16)); d.text((j * W + 3, y + 2), f'{s}: {lb}', fill=(255, 220, 120))
sh.save(out); print('SHEET', out)
