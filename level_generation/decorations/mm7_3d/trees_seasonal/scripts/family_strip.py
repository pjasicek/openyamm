#!/usr/bin/env python3
"""One family's x2 sprites at full size side by side (work/sprites_<first>.png) for planning. Usage: family_strip.py a b c"""
import os, sys
from PIL import Image
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X2 = os.path.join(HERE, '..', '..', '..', '..', 'assets_legacy', 'decorations_x2_20261016')
ims = [Image.open(os.path.join(X2, n + '.png')).convert('RGBA') for n in sys.argv[1:]]
sheet = Image.new('RGBA', (sum(i.width for i in ims), max(i.height for i in ims)), (128, 128, 128, 255))
x = 0
for im in ims:
    sheet.alpha_composite(im, (x, sheet.height - im.height)); x += im.width
sheet.convert('RGB').save(os.path.join(HERE, 'work', f'sprites_{sys.argv[1]}.png'))
