#!/usr/bin/env python3
"""Codex input sheets per skin: references_hd/mm9_views_<s>.png (q34, front, left, back, right of the raw MM9
conversion), mm9_head_views_<s>.png (front, left profile, q34, right profile, back) and mm9_skin_x4_<s>.png."""
from PIL import Image, ImageDraw
import sys
skins = sys.argv[1:] or [f'pdf{n}{t}' for n in '1234' for t in 'ab']
for s in skins:
    ims = [Image.open(f'review/mm9/{s}_{v}.png').convert('RGB').crop((134, 0, 634, 768)) for v in ('q34', 'front', 'left', 'back', 'right')]
    sh = Image.new('RGB', (500 * 5, 768), (107, 107, 107))
    for i, im in enumerate(ims):
        sh.paste(im, (i * 500, 0))
    sh.save(f'references_hd/mm9_views_{s}.png')
    ims = [Image.open(f'review/mm9_head/{s}_{v}.png').convert('RGB') for v in ('front', 'left', 'q34', 'right', 'back')]
    sh = Image.new('RGB', (768 * 5, 768), (107, 107, 107))
    for i, im in enumerate(ims):
        sh.paste(im, (i * 768, 0))
    sh.resize((768 * 5 // 2, 384)).save(f'references_hd/mm9_head_views_{s}.png')
    sk = Image.open(f'source/mm9/skins/{s}.png').convert('RGB')
    sk.resize((sk.width * 4, sk.height * 4), Image.NEAREST if False else Image.BICUBIC).save(f'references_hd/mm9_skin_x4_{s}.png')
    print('SHEET', s, sk.size)
