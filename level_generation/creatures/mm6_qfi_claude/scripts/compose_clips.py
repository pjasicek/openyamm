#!/usr/bin/env python3
"""Compose review/clips/frames.json into review/clips/<action>.png (front row over three-quarter row)."""
import json
from pathlib import Path
from PIL import Image
P = Path(__file__).resolve().parents[1]
d = json.loads((P / 'review' / 'clips' / 'frames.json').read_text())
n = d['frames']
for name, files in d['actions'].items():
    im0 = Image.open(next(iter(files.values())))
    w, h = im0.size
    sheet = Image.new('RGB', (w * n, h * 2), (200, 200, 200))
    for key, path in files.items():
        i, view = key.split('_', 1)
        sheet.paste(Image.open(path).convert('RGB'), (w * int(i), 0 if view in ('front', 'three_quarter') and key.endswith(('front',)) or view == d.get('top', 'three_quarter') else h))
    sheet.save(P / 'review' / 'clips' / f'{name}.png')
    print('wrote', name)
