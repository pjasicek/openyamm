#!/usr/bin/env python3
"""review/compare_20261016/<id>.png: the sheet's top row before the 2026-10-16 quality pass (review/before_20261016/)
over the current sheet (both rows). Usage: before_after.py <id> [...]"""
import os, sys
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sid in sys.argv[1:]:
    before = Image.open(os.path.join(HERE, 'review', 'before_20261016', f'{sid}_sheet.png')).convert('RGB')
    after = Image.open(os.path.join(HERE, 'review', f'{sid}_sheet.png')).convert('RGB')
    top = before.crop((0, 0, before.width, 440))
    out = Image.new('RGB', (after.width, 440 + after.height + 20), 'white')
    out.paste(top, (0, 0))
    out.paste(after, (0, 460))
    d = ImageDraw.Draw(out)
    d.text((900, 4), 'BEFORE (2026-10-16 morning)', fill='red')
    d.text((900, 464), 'AFTER (quality pass)', fill='green')
    out.save(os.path.join(HERE, 'review', 'compare_20261016', f'{sid}.png'))
