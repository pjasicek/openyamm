"""Tile PNGs into one sheet: sheet.py out.png cols img1 img2 ... (labels = file stems)."""
import sys
from PIL import Image, ImageDraw
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGBA') for f in files]
w = max(i.width for i in ims); h = max(i.height for i in ims)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGBA', (w * cols, (h + 18) * rows), (70, 70, 78, 255))
d = ImageDraw.Draw(sheet)
for k, (im, f) in enumerate(zip(ims, files)):
    x, y = (k % cols) * w, (k // cols) * (h + 18)
    sheet.alpha_composite(im, (x, y + 18))
    d.text((x + 4, y + 3), f.rsplit('/', 1)[-1].rsplit('.', 1)[0], fill=(255, 255, 255, 255))
sheet.convert('RGB').save(out)
