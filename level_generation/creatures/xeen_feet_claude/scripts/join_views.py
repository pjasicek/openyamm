#!/usr/bin/env python3
"""Join review/<prefix>_{front,side,top,quarter,under,oside}.png into review/<prefix>_sheet.png (and delete them)."""
import os, sys
from PIL import Image
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for prefix in sys.argv[1:]:
    ps = [os.path.join(here, 'review', f'{prefix}_{k}.png') for k in ('front', 'side', 'top', 'quarter', 'under', 'oside')]
    ims = [Image.open(p) for p in ps]; w, h = ims[0].size
    S = Image.new('RGB', (w * 3, h * 2))
    for i, im in enumerate(ims):
        S.paste(im, ((i % 3) * w, (i // 3) * h))
    S.save(os.path.join(here, 'review', f'{prefix}_sheet.png'))
    for p in ps: os.remove(p)
