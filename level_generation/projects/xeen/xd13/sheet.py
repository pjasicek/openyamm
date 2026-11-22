"""Contact sheet of a tour folder: sheet.py <folder> <out.jpg> [first] [last] (labelled, 3 per row)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
src = Path(sys.argv[1]); out = sys.argv[2]
files = sorted(src.glob('*.png'))
if len(sys.argv) > 4:
    files = files[int(sys.argv[3]):int(sys.argv[4])]
W, H, C = 640, 400, 3
rows = (len(files) + C - 1) // C
sheet = Image.new('RGB', (W * C, (H + 20) * rows), (30, 30, 30))
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).convert('RGB'); im.thumbnail((W, H))
    x, y = (i % C) * W, (i // C) * (H + 20)
    sheet.paste(im, (x, y)); d.text((x + 4, y + H + 3), f.stem, fill=(255, 255, 0))
sheet.save(out, quality=85)
