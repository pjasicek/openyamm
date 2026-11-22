#!/usr/bin/env python3
"""Join images into a labelled grid: grid.py out.png cols img1 img2 ... (labels = file stems)."""
import sys, os
from PIL import Image, ImageDraw
out, cols, paths = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(p).convert('RGB') for p in paths]
w = max(i.width for i in ims); h = max(i.height for i in ims)
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (w * cols, (h + 16) * rows), (255, 255, 255)); d = ImageDraw.Draw(S)
for k, (p, im) in enumerate(zip(paths, ims)):
    x, y = (k % cols) * w, (k // cols) * (h + 16)
    S.paste(im, (x, y + 16)); d.text((x + 4, y + 2), os.path.splitext(os.path.basename(p))[0], fill=(0, 0, 0))
S.save(out)
