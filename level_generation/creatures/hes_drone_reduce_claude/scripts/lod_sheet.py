#!/usr/bin/env python3
"""review/lods/lod_sheet.png: source and reduced LOD0-3 from lod_views.py (q34, second clip, head, hand)."""
from PIL import Image, ImageDraw
S = 260; views = ['q34', 'attack', 'head', 'hand']
sh = Image.new('RGB', (S * 8, (S + 20) * 4), (20, 20, 20)); d = ImageDraw.Draw(sh)
for r, lab in enumerate(['source', 'reduced']):
    for lvl in range(4):
        for j, v in enumerate(views):
            x = (lvl * 2 + (j % 2)) * S; y = (r * 2 + (j // 2)) * (S + 20)
            sh.paste(Image.open(f'review/lods/{lab}_{lvl}_{v}.png').convert('RGB').resize((S, S)), (x, y + 20))
            d.text((x + 3, y + 3), f'{lab} LOD{lvl} {v}', fill=(255, 230, 120))
sh.save('review/lods/lod_sheet.png'); print('LODSHEET', sh.size)
