#!/usr/bin/env python3
"""Contact sheet of a capture folder's PNGs (three across, half size). Usage: sheet.py <dir> [columns]"""
import sys
from pathlib import Path

from PIL import Image

folder = Path(sys.argv[1])
cols = int(sys.argv[2]) if len(sys.argv) > 2 else 3
files = sorted(folder.glob('*.png'))
images = [Image.open(f).convert('RGB') for f in files]
w, h = images[0].size
W, H = w // 2, h // 2
sheet = Image.new('RGB', (W * cols, H * ((len(images) + cols - 1) // cols)))
for i, im in enumerate(images):
    sheet.paste(im.resize((W, H)), ((i % cols) * W, (i // cols) * H))
sheet.save(folder / 'sheet.jpg', quality=85)
print(folder / 'sheet.jpg', [f.name for f in files])
