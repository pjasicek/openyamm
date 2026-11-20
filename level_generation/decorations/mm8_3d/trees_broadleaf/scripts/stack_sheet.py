#!/usr/bin/env python3
"""review/<id>/sheet.png = compare.png (sprite | LOD0 front | three-quarter | side) above lod_consistency.png.
Usage: stack_sheet.py <id>"""
import os
from PIL import Image
import common
R = common.load()['review']
top = Image.open(os.path.join(R, 'compare.png')).convert('RGB')
bottom = Image.open(os.path.join(R, 'lod_consistency.png')).convert('RGB')
w = max(top.width, bottom.width)
sheet = Image.new('RGB', (w, top.height + bottom.height), (150, 160, 175))
sheet.paste(top, (0, 0)); sheet.paste(bottom, (0, top.height))
sheet.save(os.path.join(R, 'sheet.png'))
print('SHEET', os.path.join(R, 'sheet.png'))
