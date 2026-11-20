"""Contact sheet: sheet.py <out png> <columns> <cell px> <image>... (label = file stem)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

out, cols, cell = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
paths = sys.argv[4:]
rows = (len(paths) + cols - 1) // cols
sheet = Image.new('RGB', (cols * cell, rows * (cell + 18)), (24, 26, 30))
draw = ImageDraw.Draw(sheet)
for i, p in enumerate(paths):
    img = Image.open(p).convert('RGB')
    img.thumbnail((cell, cell))
    x, y = (i % cols) * cell, (i // cols) * (cell + 18)
    sheet.paste(img, (x + (cell - img.width) // 2, y + 18))
    draw.text((x + 4, y + 3), Path(p).stem, fill=(230, 230, 230))
sheet.save(out)
print('SHEET', out, sheet.size)
