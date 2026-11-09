#!/usr/bin/env python3
"""Crop viewer shots to the model (the viewer frames a 2 m creature; the drone is small): the strongest-contrast
pixels against the flat background (grid lines are faint) give the box. crop_shots.py out_dir img..."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
for f in sys.argv[2:]:
    im = Image.open(f).convert('RGB'); a = np.asarray(im).astype(int)
    bg = np.median(a[100:300, 100:300].reshape(-1, 3), 0)
    d = np.abs(a - bg).sum(-1) > 110
    d[:120] = False; d[int(a.shape[0] * 0.9):] = False
    ys, xs = np.nonzero(d)
    y0, y1 = np.percentile(ys, [0.5, 99.5]); x0, x1 = np.percentile(xs, [0.5, 99.5])
    cy, cx = (y0 + y1) / 2, (x0 + x1) / 2; h = max(y1 - y0, x1 - x0) * 0.62 + 8
    im.crop((int(cx - h), int(cy - h), int(cx + h), int(cy + h))).resize((512, 512), Image.LANCZOS).save(out / Path(f).name)
print('CROPPED', len(sys.argv) - 2)
