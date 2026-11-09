#!/usr/bin/env python3
"""Contact sheet of viewer shots cropped to the creature (non-background bounding box, padded).
crop_sheet.py <out.png> <columns> <png> [<png> ...]"""
import sys
import numpy as np
from PIL import Image

ims = []
for p in sys.argv[3:]:
    im = Image.open(p).convert('RGB'); a = np.asarray(im).astype(int)
    bg = a[5, a.shape[1] // 2]
    body = (np.abs(a - bg).sum(2) > 90); m = 0.06
    body[:int(a.shape[0] * m)] = False; body[int(a.shape[0] * 0.88):] = False
    body[:, :int(a.shape[1] * m)] = False; body[:, int(a.shape[1] * (1 - m)):] = False
    ys, xs = np.nonzero(body)
    ims.append((im, xs.min(), ys.min(), xs.max(), ys.max()))
w = max(x1 - x0 for _, x0, _, x1, _ in ims) + 40; h = max(y1 - y0 for _, _, y0, _, y1 in ims) + 40
cells = []
for im, x0, y0, x1, y1 in ims:
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    cells.append(im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)))
cols = int(sys.argv[2])
sheet = Image.new('RGB', (w * cols, h * ((len(cells) + cols - 1) // cols)))
for k, c in enumerate(cells):
    sheet.paste(c, ((k % cols) * w, (k // cols) * h))
sheet.save(sys.argv[1]); print(sheet.size)
