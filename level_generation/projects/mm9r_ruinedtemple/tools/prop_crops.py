#!/usr/bin/env python3
"""Prop crop mean luminance (Rec. 709 luma of the crop's mean RGB) in tour folders, as Thjorad Mine's
model_lighting_props.txt: the MM9 capture first, then the native variants (ratios to the capture).
Usage: prop_crops.py <capture> <variant>... (folders with the same view names)"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

# view -> [(label, (x0, y0, x1, y1) as fractions of the frame)]
CROPS = {
    "e03_lower_hall": [("banner left", (0.23, 0.10, 0.32, 0.55)), ("banner right", (0.67, 0.10, 0.77, 0.55))],
    "t03_lamp": [("genie lamp", (0.44, 0.52, 0.52, 0.60))],
    "s05_chest_room": [("chests", (0.22, 0.69, 0.75, 0.75))],
    "s06_hiddendoor3": [("crate", (0.64, 0.70, 0.83, 0.95)), ("barrel", (0.0, 0.74, 0.07, 0.95))],
    "n03_pews": [("pews right", (0.72, 0.58, 0.98, 0.80)), ("pews left", (0.0, 0.60, 0.28, 0.80))],
    "n04_podium": [("podium box", (0.37, 0.40, 0.48, 0.55))],
    "c03_crypt_hall": [("banner", (0.0, 0.10, 0.11, 0.60)), ("sarcophagus", (0.20, 0.55, 0.58, 0.72))],
}


def luma(folder, view, box):
    path = next(Path(folder).glob(f"*-{view}.png"))
    image = Image.open(path).convert("RGB")
    w, h = image.size
    a = np.asarray(image.crop((int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h))), float)
    r, g, b = a.reshape(-1, 3).mean(0)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


folders = sys.argv[1:]
print("prop crop mean luminance: " + " | ".join(Path(f).name for f in folders) + " (ratios to the first)")
for view, crops in CROPS.items():
    for label, box in crops:
        values = [luma(f, view, box) for f in folders]
        cells = [f"{values[0]:6.1f}"] + [f"{v:6.1f} (x{v / values[0]:.2f})" for v in values[1:]]
        print(f"{view[:12]:12} {label:13} " + " | ".join(cells))
