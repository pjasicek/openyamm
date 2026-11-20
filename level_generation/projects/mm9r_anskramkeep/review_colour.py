#!/usr/bin/env python3
"""Brightness and colour of a tour against MM9's, view by view (centre crop, as dungeon.sheet --brightness):

    python3 level_generation/projects/mm9r_anskramkeep/review_colour.py review/v04_original review/v04 [--views]

Hue is (r, g, b) / their mean: MM9's lightmaps average 1.118, 1.051, 0.831.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

PROJECT = Path(__file__).resolve().parent


def measure(path):
    image = Image.open(path).convert("RGB")
    w, h = image.size
    crop = np.asarray(image.crop((int(w * 0.2), int(h * 0.1), int(w * 0.8), int(h * 0.75))), dtype=np.float32)
    return crop.mean((0, 1))


folders = [PROJECT / a for a in sys.argv[1:] if not a.startswith("--")]
shots = sorted(p.name for p in folders[0].glob("*.png"))
values = [np.array([measure(folder / shot) for shot in shots]) for folder in folders]
if "--views" in sys.argv:
    for i, shot in enumerate(shots):
        print(f"{shot[:-4]:24}" + "  ".join(f"{v[i].mean():6.1f}" for v in values))
for folder, value in zip(folders, values):
    mean = value.mean(0)
    print(f"{mean.mean():6.1f}  hue {(mean / mean.mean()).round(3)}  {folder.name}")
if len(values) > 1:
    ratio = values[1].mean(1) / np.maximum(values[0].mean(1), 1)
    print(f"view ratio new / MM9: median {np.median(ratio):.2f}, 10-90 % {np.percentile(ratio, 10):.2f}-"
          f"{np.percentile(ratio, 90):.2f}")
