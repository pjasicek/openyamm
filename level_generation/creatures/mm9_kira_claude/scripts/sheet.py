"""Paste images in a row (or grid with COLS=n). Args: out img1 img2 ..."""
import sys, os
from PIL import Image
out, ims = sys.argv[1], [Image.open(p).convert('RGB') for p in sys.argv[2:]]
cols = int(os.environ.get('COLS', len(ims))); rows = (len(ims) + cols - 1) // cols
w, h = ims[0].size
o = Image.new('RGB', (w * cols, h * rows), (60, 60, 60))
for i, im in enumerate(ims): o.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
o.save(out); print('SHEET', out, o.size)
