#!/usr/bin/env python3
"""review/<id>/sheet.png = compare.png above lod_consistency.png (scaled to a common width). Usage: stack_sheet.py <id>"""
import os
from PIL import Image
import common
R = common.load()['review']
top = Image.open(os.path.join(R, 'compare.png')).convert('RGB')
low = Image.open(os.path.join(R, 'lod_consistency.png')).convert('RGB')
w = max(top.width, low.width)
top = top.resize((w, int(top.height * w / top.width)), Image.LANCZOS)
low = low.resize((w, int(low.height * w / low.width)), Image.LANCZOS)
sheet = Image.new('RGB', (w, top.height + low.height), (150, 160, 175))
sheet.paste(top, (0, 0)); sheet.paste(low, (0, top.height))
sheet.save(os.path.join(R, 'sheet.png'))
print('SHEET', os.path.join(R, 'sheet.png'))
