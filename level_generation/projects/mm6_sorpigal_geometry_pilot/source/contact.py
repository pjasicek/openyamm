"""Contact sheets of a capture folder for picking views: python3 source/contact.py <folder> <out_prefix>"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

folder, prefix = Path(sys.argv[1]), sys.argv[2]
shots = sorted(folder.glob('*.png'))
w, h, cols = 400, 225, 4
for part in range(0, len(shots), 24):
    group = shots[part:part + 24]
    sheet = Image.new('RGB', (w * cols, h * ((len(group) + cols - 1) // cols)))
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(group):
        x, y = (i % cols) * w, (i // cols) * h
        sheet.paste(Image.open(path).convert('RGB').resize((w, h)), (x, y))
        draw.rectangle([x, y, x + 8 + 7 * len(path.stem), y + 14], fill=(0, 0, 0))
        draw.text((x + 3, y + 1), path.stem, fill=(255, 255, 0))
    sheet.save(f'{prefix}_{part // 24}.jpg', quality=80)
