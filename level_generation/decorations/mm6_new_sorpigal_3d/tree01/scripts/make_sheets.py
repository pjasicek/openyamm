#!/usr/bin/env python3
"""Review sheets from render_review.py output (work/fin_*): review/tree01_compare.png (native sprite | LOD0 eye level |
LOD0 three-quarter) and review/tree01_lods.png (LOD0..LOD3, same camera and scale, triangle counts)."""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, R = os.path.join(HERE, 'work'), os.path.join(HERE, 'review')
counts = [int(x) for x in sys.argv[1].split(',')]
BG = (150, 160, 172, 255)


def strip(images, labels, out):
    w = sum(i.width for i in images); s = Image.new('RGBA', (w, 580), BG); d = ImageDraw.Draw(s); x = 0
    for img, label in zip(images, labels):
        s.alpha_composite(img, (x, 40)); d.text((x + 8, 12), label, fill=(20, 20, 20, 255)); x += img.width
    s.convert('RGB').save(out); print('SHEET', out)


sp = Image.open(os.path.join(HERE, '..', '..', 'mm6_new_sorpigal', 'enhanced', '6tree01.png')).convert('RGBA')
sp = sp.resize((int(sp.width * 540 / sp.height), 540))
strip([sp, Image.open(os.path.join(W, 'fin_Tree_eye.png')), Image.open(os.path.join(W, 'fin_Tree_three_quarter.png'))],
      ['native 6tree01 (upscaled)', 'LOD0 eye level', 'LOD0 three-quarter, raised'], os.path.join(R, 'tree01_compare.png'))
names = ['Tree', 'Tree_LOD1', 'Tree_LOD2', 'Tree_LOD3']
strip([Image.open(os.path.join(W, f'fin_{n}_eye.png')) for n in names],
      [f'LOD{i}: {c} triangles' + (' (impostor)' if i == 3 else '') for i, c in enumerate(counts)],
      os.path.join(R, 'tree01_lods.png'))
