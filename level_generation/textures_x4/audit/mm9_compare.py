#!/usr/bin/env python3
"""Native | x4 side-by-side sheets from two tour output roots: mm9_compare.py NATIVE_ROOT X4_ROOT OUT_DIR [MAP...]."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

native_root, x4_root, out = (Path(a) for a in sys.argv[1:4])
maps = sys.argv[4:] or sorted(p.name for p in native_root.iterdir() if p.is_dir())
out.mkdir(parents=True, exist_ok=True)
for name in maps:
    pairs = [(n, x4_root / name / n.name) for n in sorted((native_root / name).glob('[0-9]*.png'))]
    pairs = [(a, b) for a, b in pairs if b.exists()]
    if not pairs:
        continue
    width, height = 800, 450
    sheet = Image.new('RGB', (2 * width, len(pairs) * (height + 18)), (25, 25, 25))
    draw = ImageDraw.Draw(sheet)
    for row, (a, b) in enumerate(pairs):
        y = row * (height + 18)
        draw.text((4, y + 2), f'{a.stem}: native 1x (left) | x4 (right)', fill=(255, 255, 0))
        for column, path in enumerate((a, b)):
            sheet.paste(Image.open(path).convert('RGB').resize((width, height), Image.LANCZOS), (column * width, y + 18))
    sheet.save(out / f'{name}.jpg', quality=88)
    print(out / f'{name}.jpg')
