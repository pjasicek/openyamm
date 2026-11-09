#!/usr/bin/env python3
"""MM9 (Blender render of the true-handed source) over ours (viewer shots), seven clip extremes, three tiers. Project folder."""
from PIL import Image, ImageDraw
M = ['q', 'w', 'x', 'y', 'h', 'k', 'd']  # ours: Standing, Walking, AttackMelee, AttackMelee2, Hit, Block, Dead
C = 300
W = Image.new('RGB', (C * 7, C * 6), (40, 40, 44)); d = ImageDraw.Draw(W)
for r, t in enumerate('abc'):
    for i, k in enumerate(M):
        a = Image.open(f'review/mm9/{t}_{i}.png').convert('RGB').resize((C, C), Image.LANCZOS)
        b = Image.open(f'review/final/t{t}_{k}.png').convert('RGB'); w, h = b.size
        b = b.crop(((w - h) // 2, 0, (w + h) // 2, h)).resize((C, C), Image.LANCZOS)
        W.paste(a, (i * C, r * 2 * C)); W.paste(b, (i * C, (r * 2 + 1) * C))
    d.text((6, r * 2 * C + 4), f'MM9 tier {t}', fill=(255, 240, 120)); d.text((6, (r * 2 + 1) * C + 4), f'ours tier {t}', fill=(255, 240, 120))
W.save('review/sheet_mm9_vs_ours.png')
