"""Grid of review/glbclose images: sheet.py <out.png> <cols> <label>:<spot>:<mode> ... (missing -> grey)."""
import sys, os
from PIL import Image, ImageDraw
out, cols, items = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
S = 300; rows = (len(items) + cols - 1) // cols
im = Image.new('RGB', (cols * S, rows * (S + 16)), (20, 20, 20)); dr = ImageDraw.Draw(im)
for i, it in enumerate(items):
    lab, spot, mode = it.split(':'); p = f'review/glbclose/{lab}_{spot}_{mode}.png'
    x, y = (i % cols) * S, (i // cols) * (S + 16)
    if os.path.exists(p):
        im.paste(Image.open(p).convert('RGB').resize((S, S)), (x, y + 16))
    dr.text((x + 4, y + 2), f'{lab} {spot} {mode}', fill=(255, 255, 0))
im.save(out); print(out)
