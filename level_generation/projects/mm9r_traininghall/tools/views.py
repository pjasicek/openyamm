#!/usr/bin/env python3
"""Per-view centre-crop brightness and mean RGB of tour folders (the sheet's crop: 20-80 % across, 10-75 % down).
Usage: views.py <folder> [<folder>...]  (the first is the reference: ratio columns against it)"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def stats(path):
    image = Image.open(path).convert("RGB")
    w, h = image.size
    a = np.asarray(image.crop((int(w * 0.2), int(h * 0.1), int(w * 0.8), int(h * 0.75))), dtype=np.float32)
    return a.mean(), a.reshape(-1, 3).mean(0)


folders = [Path(f) for f in sys.argv[1:]]
names = sorted(p.name for p in folders[0].glob("*.png"))
totals = [[] for _ in folders]
for name in names:
    row = [stats(f / name) if (f / name).exists() else (float("nan"), np.zeros(3)) for f in folders]
    for t, r in zip(totals, row):
        t.append(r[0])
    ref = row[0][0]
    cells = "  ".join(f"{m:5.1f} ({'/'.join(str(int(v)) for v in rgb)}) x{m / ref:4.2f}" for m, rgb in row)
    print(f"{name[:26]:26s} {cells}")
print("mean", "  ".join(f"{np.nanmean(t):5.1f}" for t in totals))
