#!/usr/bin/env python3
"""Mean brightness and hue (centre crop) of a calibration tour against the same views of the MM9 original:
python3 level_generation/projects/mm9r_thjoradmine/calib.py <folder>"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

review = Path(__file__).resolve().parent / "review"


def crop(path):
    a = np.asarray(Image.open(path).convert("RGB"), float)
    h, w = a.shape[:2]
    return a[h // 5:h * 3 // 4, w // 5:w * 4 // 5].reshape(-1, 3).mean(0)


rows = []
for path in sorted((review / sys.argv[1]).glob("*.png")):
    original = next((review / (sys.argv[2] if len(sys.argv) > 2 else "v02_original")).glob(f"*-{path.stem.split('-', 1)[1]}.png"), None)
    a, b = crop(original), crop(path)
    rows.append((a, b))
    print(f"{path.stem[3:]:22} MM9 {a.mean():5.1f} {a.round()}  BLV {b.mean():5.1f} {b.round()}")
rows = np.array(rows)
print("means", rows[:, 0].mean().round(1), rows[:, 1].mean().round(1))
