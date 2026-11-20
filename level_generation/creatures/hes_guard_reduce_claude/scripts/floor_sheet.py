#!/usr/bin/env python3
"""review/floor/before_after.png from floor_view.py renders (work/floorcheck/<label>_<shot>_<view>.png)."""
from PIL import Image, ImageDraw
shots = ['Death1.0', 'Death1.6', 'Death2.4', 'Death3.43', 'Dead0.5']; W, H = 360, 225
sh = Image.new('RGB', (W * 5, (H + 18) * 4), (20, 20, 20)); d = ImageDraw.Draw(sh)
for r, (lab, view) in enumerate([('before', 'side'), ('after', 'side'), ('before', 'front'), ('after', 'front')]):
    for c, s in enumerate(shots):
        x, y = c * W, r * (H + 18)
        sh.paste(Image.open(f'work/floorcheck/{lab}_{s}_{view}.png').convert('RGB').resize((W, H)), (x, y + 18))
        d.text((x + 3, y + 3), f'{lab} {s} {view}', fill=(255, 230, 120))
sh.save('review/floor/before_after.png'); print('FLOORSHEET', sh.size)
