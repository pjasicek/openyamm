#!/usr/bin/env python3
"""Stack view_spot.py renders (rows src/cand, columns x y z q) into <prefix>_sheet.png. Usage: spot_sheet.py <prefix>"""
import sys
from PIL import Image
pre = sys.argv[1]
ims = [[Image.open(f'{pre}_{d}_{n}.png').convert('RGB') for d in 'xyzq'] for n in ('src', 'cand')]
W = ims[0][0].width; sh = Image.new('RGB', (W * 4, W * 2))
for r, row in enumerate(ims):
    for c, im in enumerate(row):
        sh.paste(im, (c * W, r * W))
sh.save(f'{pre}_sheet.png')
