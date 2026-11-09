#!/usr/bin/env python3
from PIL import Image, ImageDraw
C = 330
rows = [('MM9 A', ['review/mm9/t1_front_0', 'review/mm9/t1_back_0', 'review/mm9/t1_quarter_0'] ), ('ours A', ['review/shots/sa_front', 'review/shots/sa_back', 'review/shots/sa_quarter']),
        ('MM9 B', ['review/mm9/t2_front_0', 'review/mm9/t2_back_0', 'review/mm9/t2_quarter_0']), ('ours B', ['review/shots/sb_front', 'review/shots/sb_back', 'review/shots/sb_quarter']),
        ('MM9 C', ['review/mm9/t3_front_0', 'review/mm9/t3_back_0', 'review/mm9/t3_quarter_0']), ('ours C', ['review/shots/sc_front', 'review/shots/sc_back', 'review/shots/sc_quarter'])]
s = Image.new('RGB', (6 * C, 3 * C), (30, 30, 34)); d = ImageDraw.Draw(s)
for r in range(3):
    for j in range(2):
        lab, fs = rows[r * 2 + j]
        for k, f in enumerate(fs):
            im = Image.open(f + '.png').convert('RGB')
            w, h = im.size; q = min(w, h); im = im.crop(((w - q) // 2, (h - q) // 2, (w + q) // 2, (h + q) // 2)).resize((C, C), Image.LANCZOS)
            x = (k * 2 + j) * C; s.paste(im, (x, r * C)); d.text((x + 6, r * C + 4), lab, fill=(255, 240, 120))
s.save('review/mm9_vs_ours_tiers.png')
s = Image.new('RGB', (8 * C, 2 * C), (30, 30, 34)); d = ImageDraw.Draw(s)
for k in range(8):
    for j, f in enumerate((f'review/mm9/clip_quarter_{k}', f'review/shots/k{k}')):
        im = Image.open(f + '.png').convert('RGB'); w, h = im.size; q = min(w, h)
        im = im.crop(((w - q) // 2, (h - q) // 2, (w + q) // 2, (h + q) // 2)).resize((C, C), Image.LANCZOS); s.paste(im, (k * C, j * C))
s.save('review/mm9_vs_ours_clips.png')
