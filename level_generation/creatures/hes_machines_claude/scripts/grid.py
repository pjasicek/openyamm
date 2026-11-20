"""Contact sheet: python3 grid.py <out.png> <columns> <image>... (each image scaled to 400 px high, labelled)."""
import sys
from PIL import Image, ImageDraw
out, cols, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = []
for p in paths:
    im = Image.open(p).convert('RGB'); im = im.resize((int(im.width * 400 / im.height), 400))
    ImageDraw.Draw(im).text((6, 6), p.split('/')[-1], fill=(255, 255, 0)); ims.append(im)
w = max(i.width for i in ims); rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (w * cols, 400 * rows), (40, 40, 40))
for k, im in enumerate(ims):
    sheet.paste(im, ((k % cols) * w, (k // cols) * 400))
sheet.save(out)
