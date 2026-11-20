#!/usr/bin/env python3
"""Review pages of a tour: pairs (MM9 original | native) in pages of 12 pairs, which fit one look.

    python3 level_generation/projects/mm9r_bathhouse/pages.py <native folder> <original folder> [page ...]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

TILE = (480, 270)
review = Path(__file__).resolve().parent / "review"
a, b = review / sys.argv[1], review / sys.argv[2]
names = sorted(p.name for p in a.glob("*.png"))
for page in range(0, (len(names) + 11) // 12):
    chunk = names[page * 12:page * 12 + 12]
    sheet = Image.new("RGB", (TILE[0] * 4, (TILE[1] + 16) * 6), (12, 12, 16))
    draw = ImageDraw.Draw(sheet)
    for k, name in enumerate(chunk):
        row, column = k // 2 // 3 * 0 + k // 2, k % 2
        for side, folder in enumerate((b, a)):
            x, y = (column * 2 + side) * TILE[0], row // 1 * (TILE[1] + 16)
            path = folder / name
            if path.exists():
                sheet.paste(Image.open(path).convert("RGB").resize(TILE), (x, y + 16))
            draw.text((x + 4, y + 2), ("MM9 " if side == 0 else "BLV ") + name[:-4], fill=(255, 255, 255))
    out = review / f"pages_{sys.argv[1]}_{page + 1:02d}.jpg"
    sheet.save(out, quality=85)
    print(out)
