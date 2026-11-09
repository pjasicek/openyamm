#!/usr/bin/env python3
"""Contact sheet: sheet.py out.png cols img1 img2 ... (labels = file stems)."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
out, cols, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ims = [Image.open(f).convert('RGB') for f in files]
W = max(i.size[0] for i in ims); H = max(i.size[1] for i in ims)
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGB', (W * cols, H * rows), (40, 40, 40)); d = ImageDraw.Draw(s)
for k, (im, f) in enumerate(zip(ims, files)):
    x, y = (k % cols) * W, (k // cols) * H
    s.paste(im, (x, y)); d.text((x + 6, y + 4), Path(f).stem, fill=(255, 40, 40))
s.save(out); print(out, s.size)
