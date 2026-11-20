#!/usr/bin/env python3
"""Viewer shots installed (top) vs reduced (bottom) per tier -> review/sheet_viewer_<t>.png"""
from pathlib import Path
from PIL import Image, ImageDraw
H = Path(__file__).resolve().parents[1] / 'review'
SH = ['st_front', 'st_q', 'st_back', 'walk_q', 'atk_q', 'death_q', 'head_front', 'head_q']
for t in 'abc':
    ims = [[Image.open(H / f'shots_{t}_{m}' / f'{s}.png').convert('RGB') for s in SH] for m in ('installed', 'mp85')]
    W = 360; h = int(ims[0][0].height * W / ims[0][0].width)
    sheet = Image.new('RGB', (W * len(SH), 2 * h + 40), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    d.text((6, 4), f'tier {t.upper()}: installed 12,599 (top) vs reduced mp85 11,445 (bottom), review viewer', fill=(240, 240, 240))
    for r, row in enumerate(ims):
        for c, im in enumerate(row):
            sheet.paste(im.resize((W, h)), (c * W, 20 + r * (h + 20)))
            if r == 1:
                d.text((c * W + 6, 20 + h + 4), SH[c], fill=(240, 220, 120))
    sheet.save(H / f'sheet_viewer_{t}.png'); print('sheet', t)
