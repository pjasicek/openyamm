#!/usr/bin/env python3
"""Per-view brightness (centre crop, the shared sheet's) of tour folders and their ratio to the first (MM9 original).
Usage: tools/brightness.py <original folder> <folder> [...]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image


def value(path):
    image = Image.open(path).convert("RGB")
    w, h = image.size
    crop = image.crop((int(w * 0.2), int(h * 0.1), int(w * 0.8), int(h * 0.75)))
    return float(np.asarray(crop, dtype=np.float32).mean())


folders = [Path(a) for a in sys.argv[1:]]
names = sorted(p.name for p in folders[0].glob("*.png"))
rows = []
for name in names:
    vals = [value(f / name) if (f / name).exists() else float("nan") for f in folders]
    rows.append(vals)
    print(f"{name[:-4]:32s}" + " ".join(f"{v:6.1f}" for v in vals) + "   " + " ".join(f"{v / vals[0]:5.2f}" for v in vals[1:]))
means = np.nanmean(np.array(rows), 0)
print(f"{'MEAN':32s}" + " ".join(f"{v:6.1f}" for v in means) + "   " + " ".join(f"{v / means[0]:5.2f}" for v in means[1:]))
for k, f in enumerate(folders[1:], 1):
    off = [names[i][:-4] for i, r in enumerate(rows) if abs(r[k] / r[0] - 1) > 0.10]
    print(f.name, "views off by > 10 %:", len(off), "of", len(rows))
