#!/usr/bin/env python3
"""A labelled grid of one review folder's PNGs: montage.py <folder> <out.jpg> [columns] [width]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

folder, out = Path(sys.argv[1]), Path(sys.argv[2])
columns = int(sys.argv[3]) if len(sys.argv) > 3 else 3
width = int(sys.argv[4]) if len(sys.argv) > 4 else 640
files = sorted(folder.glob("*.png"))
first = Image.open(files[0])
height = int(width * first.height / first.width)
rows = (len(files) + columns - 1) // columns
sheet = Image.new("RGB", (columns * width, rows * height), (20, 20, 20))
draw = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    x, y = i % columns * width, i // columns * height
    sheet.paste(Image.open(f).convert("RGB").resize((width, height)), (x, y))
    draw.rectangle([x, y, x + 220, y + 16], fill=(0, 0, 0))
    draw.text((x + 4, y + 2), f.stem, fill=(255, 255, 0))
sheet.save(out, quality=85)
print(out, sheet.size)
