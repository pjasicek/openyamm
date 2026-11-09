#!/usr/bin/env python3
"""Review sheets: review/glbclose/sheet_<mode>.png (source | reduced per spot, from the GLBs) and review/lods_sheet.png
(source and reduced LOD0-3, Standing three-quarter and Attack frame 12). Usage: review_sheets.py"""
from PIL import Image, ImageDraw
S = 260
spots = ['top', 'front', 'back', 'rim_front', 'walk', 'attack_up', 'knob', 'cast_swell', 'dead', 'fidget']
for mode in ('tex', 'clay'):
    cols = 5; W = 2 * S + 8; rows = (len(spots) + cols - 1) // cols
    sh = Image.new('RGB', (W * cols, rows * (S + 18)), (20, 20, 20)); d = ImageDraw.Draw(sh)
    for k, spot in enumerate(spots):
        x0, y0 = (k % cols) * W, (k // cols) * (S + 18); d.text((x0 + 4, y0 + 3), f'{spot}: source | reduced', fill=(255, 230, 120))
        for j, l in enumerate(('source', 'reduced')):
            sh.paste(Image.open(f'review/glbclose/{l}_{spot}_{mode}.png').convert('RGB').resize((S, S)), (x0 + j * S, y0 + 18))
    sh.save(f'review/glbclose/sheet_{mode}.png')
tris = {'src': [4662, 2330, 838, 273], 'red': [3904, 1952, 702, 232]}
sh = Image.new('RGB', (S * 8, 2 * (S + 18)), (20, 20, 20)); d = ImageDraw.Draw(sh)
for r, lab in enumerate(('src', 'red')):
    for lv in range(4):
        for k, view in enumerate(('q34', 'attack')):
            x, y = (lv * 2 + k) * S, r * (S + 18)
            d.text((x + 4, y + 3), f"{'source' if lab == 'src' else 'reduced'} LOD{lv} {tris[lab][lv]} {view}", fill=(255, 230, 120))
            sh.paste(Image.open(f'review/lods/{lab}_{lv}_{view}.png').convert('RGB').resize((S, S)), (x, y + 18))
sh.save('review/lods_sheet.png'); print('SHEETS done')
