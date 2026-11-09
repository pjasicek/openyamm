#!/usr/bin/env python3
"""Real MM9 screenshots of Klusos House against a tour of the same views (make_real_tour.py): central-crop means
(x 18-82 %, y 15-90 %: the orchestrator's crop), luma (Rec. 709) and RGB, b/r, and a side-by-side sheet.

    python3 level_generation/projects/mm9r_klusoshouse/real_compare.py <tour name> [<tour name> ...]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parent
REAL = PROJECT.parents[2] / "devdocs/mm9_rework/overnight/real_mm9"
TILE = (640, 460)


def crop_mean(path):
    a = np.asarray(Image.open(path).convert("RGB"), float)
    h, w = a.shape[:2]
    rgb = a[int(h * 0.15):int(h * 0.90), int(w * 0.18):int(w * 0.82)].reshape(-1, 3).mean(0)
    return rgb @ np.array([0.2126, 0.7152, 0.0722]), rgb


def main():
    tours = sys.argv[1:] or ["real01"]
    reals = sorted(REAL.glob("klusoshouse_real_*.png"))
    sheet = Image.new("RGB", (TILE[0] * (1 + len(tours)), (TILE[1] + 20) * len(reals)), (12, 12, 16))
    draw = ImageDraw.Draw(sheet)
    for row, real in enumerate(reals):
        number = real.stem.split("_")[2]
        luma, rgb = crop_mean(real)
        line = [f"{number}: real {luma:5.1f} {rgb.round().astype(int)} b/r {rgb[2] / rgb[0]:.2f}"]
        cells = [(real, f"real MM9 {number}  luma {luma:.1f}")]
        for name in tours:
            ours = next((PROJECT / "review" / name).glob(f"0{number}-*.png"))
            l2, c2 = crop_mean(ours)
            line.append(f"{name} {l2:5.1f} {c2.round().astype(int)} b/r {c2[2] / c2[0]:.2f} x{l2 / luma:.2f}")
            cells.append((ours, f"{name}  luma {l2:.1f} (x{l2 / luma:.2f})"))
        print(" | ".join(line))
        for col, (path, label) in enumerate(cells):
            sheet.paste(Image.open(path).convert("RGB").resize(TILE), (col * TILE[0], row * (TILE[1] + 20) + 20))
            draw.text((col * TILE[0] + 4, row * (TILE[1] + 20) + 4), label, fill=(230, 230, 230))
    out = PROJECT / "review" / f"real_vs_{'_'.join(tours)}.jpg"
    sheet.save(out, quality=88)
    print(out)


if __name__ == "__main__":
    main()
