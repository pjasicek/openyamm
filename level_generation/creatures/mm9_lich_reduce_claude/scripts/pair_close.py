#!/usr/bin/env python3
"""review/close/<inst|red>_<tier>/c*.png -> review/sheet_close_<tag>_<tier>.png (installed row over reduced row)."""
import sys
from PIL import Image, ImageDraw
tag = sys.argv[1]; names = ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7']
LB = dict(c0='hands front', c1='right hand 3/4', c2='Walking robe back', c3='robe front', c4='Fidget2 sleeves 3/4', c5='boots',
          c6='AttackRanged shoulders back', c7='Running robe side')
W = 500; H = int(W * 1060 / 1440)
for t in 'ab':
    for half, nl in ((1, names[:4]), (2, names[4:])):
        sh = Image.new('RGB', (W * 4, (H + 20) * 2), (25, 25, 25)); d = ImageDraw.Draw(sh)
        for j, k in enumerate(('inst', 'red')):
            for i, s in enumerate(nl):
                sh.paste(Image.open(f'review/close/{k}_{t}/{s}.png').convert('RGB').resize((W, H)), (i * W, j * (H + 20) + 20))
                d.text((i * W + 4, j * (H + 20) + 4), f'{t} {"installed" if k == "inst" else tag} {LB[s]}', fill=(255, 220, 120))
        sh.save(f'review/sheet_close_{tag}_{t}_{half}.png')
