#!/usr/bin/env python3
"""
Real MM9 screenshots (devdocs/mm9_rework/overnight/real_mm9/<stem>_real_*.png, YouTube frames) against our captures of
the same views (2026-10-31 re-light to real shots; Klusos House's real_compare.py generalised).

Crops: the real shot's 3D view is x 20-78 %, y 5-88 % (without the portraits and the minimap). Assumed: MM9 draws the
full 4:3 frame at 90 degrees across (tan 1.0 x 0.75); ours is 16:9 at a 60 degree vertical field (tan 1.026 x 0.577).
A real-frame fraction maps to ours by angle (`ours_frac`), so the same box is x 20.8-77.3 %, y 0-99.4 % of our frame,
the HUD inside it masked (the party frame, the status line, the top bar). Bands: the box's upper, middle and lower
thirds in the real frame (y 5-32.7, 32.7-60.3, 60.3-88 %), mapped the same way. Luma is Rec. 709 on the 8-bit values.

    python3 level_generation/projects/mm9r_common/real_shots.py measure IMAGE [--real]
    python3 level_generation/projects/mm9r_common/real_shots.py sheet OUT.jpg REAL1=DIR_OR_PNG,DIR_OR_PNG ... \
        [--labels before,after] [--views name1,name2,...]

`sheet` rows: one per real shot, given as `<real png>` and the matching shot of each of our folders (a folder takes the
first PNG whose name contains the row's view name from --views, in order).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
REAL_DIR = ROOT / "devdocs/mm9_rework/overnight/real_mm9"
WEIGHTS = np.array([0.2126, 0.7152, 0.0722])
TILE = (560, 330)


REAL_BOX = (0.20, 0.78, 0.05, 0.88)
BANDS = {"upper": (0.05, 0.327), "middle": (0.327, 0.603), "lower": (0.603, 0.88)}


def ours_frac(rx: float, ry: float) -> tuple[float, float]:
    """A real (4:3, 90 degrees across) frame fraction as the same view direction in our 16:9, 60 degree frame."""
    return 0.5 + (rx - 0.5) * 1.0 / 1.0261, 0.5 + (ry - 0.5) * 0.75 / 0.5774


def hud_keep(h: int, w: int) -> np.ndarray:
    keep = np.ones((h, w), bool)
    keep[int(h * 0.78):, int(w * 0.39):int(w * 0.61)] = False                 # party frame
    keep[int(h * 0.70):int(h * 0.78), int(w * 0.33):int(w * 0.67)] = False    # status line
    keep[:int(h * 0.06), :int(w * 0.32)] = False                              # top bar
    return keep


def box_pixels(path: Path, real: bool, box=REAL_BOX) -> np.ndarray:
    """The pixels of a real-frame box (x0, x1, y0, y1) in the real shot, or of the same view directions in ours."""
    a = np.asarray(Image.open(path).convert("RGB"), float)
    h, w = a.shape[:2]
    x0, x1, y0, y1 = box
    if not real:
        (x0, y0), (x1, y1) = ours_frac(x0, y0), ours_frac(x1, y1)
    x0, x1 = max(0, int(w * x0)), min(w, int(w * x1))
    y0, y1 = max(0, int(h * y0)), min(h, int(h * y1))
    if real:
        return a[y0:y1, x0:x1].reshape(-1, 3)
    return a[y0:y1, x0:x1][hud_keep(h, w)[y0:y1, x0:x1]]


def crop_pixels(path: Path, real: bool) -> np.ndarray:
    return box_pixels(path, real)


def measure(path: Path, real: bool) -> tuple[float, np.ndarray]:
    rgb = crop_pixels(path, real).mean(0)
    return float(rgb @ WEIGHTS), rgb


def stats(path: Path, real: bool, extra: dict | None = None) -> dict:
    """Mean and median luma, mean RGB of the box, and the means of its thirds (and of any extra real-frame boxes)."""
    px = crop_pixels(path, real)
    luma = px @ WEIGHTS
    rgb = px.mean(0)
    out = {"luma": round(float(rgb @ WEIGHTS), 1), "median": round(float(np.median(luma)), 1),
           "rgb": [int(round(v)) for v in rgb]}
    for name, (y0, y1) in BANDS.items():
        part = box_pixels(path, real, (REAL_BOX[0], REAL_BOX[1], y0, y1))
        out[name] = round(float(part.mean(0) @ WEIGHTS), 1) if len(part) else None
    for name, box in (extra or {}).items():
        part = box_pixels(path, real, box)
        out[name] = round(float(part.mean(0) @ WEIGHTS), 1) if len(part) else None
        out[name + "_rgb"] = [int(round(v)) for v in part.mean(0)] if len(part) else None
    return out


def describe(luma: float, rgb: np.ndarray) -> str:
    r, g, b = rgb
    return f"luma {luma:5.1f} RGB ({r:.0f},{g:.0f},{b:.0f}) B/R {b / max(r, 1e-3):.2f} G/R {g / max(r, 1e-3):.2f}"


def find_shot(folder: Path, view: str) -> Path:
    if folder.is_file():
        return folder
    matches = sorted(p for p in folder.glob("*.png") if view in p.stem)
    if not matches:
        raise SystemExit(f"no shot {view} in {folder}")
    return matches[0]


def sheet(out: Path, rows: list[tuple[Path, list[Path]]], labels: list[str]) -> None:
    columns = 1 + max(len(r[1]) for r in rows)
    image = Image.new("RGB", (TILE[0] * columns, (TILE[1] + 34) * len(rows)), (12, 12, 16))
    draw = ImageDraw.Draw(image)
    for row, (real, ours) in enumerate(rows):
        luma, rgb = measure(real, True)
        cells = [(real, True, f"REAL {real.stem.split('_real_')[-1]}", luma)]
        cells += [(p, False, labels[k] if k < len(labels) else p.parent.name, None) for k, p in enumerate(ours)]
        for col, (path, is_real, label, _) in enumerate(cells):
            l2, c2 = measure(path, is_real)
            text = f"{label}: {describe(l2, c2)}" + ("" if is_real else f"  x{l2 / luma:.2f}")
            y = row * (TILE[1] + 34)
            image.paste(Image.open(path).convert("RGB").resize(TILE), (col * TILE[0], y + 34))
            draw.text((col * TILE[0] + 4, y + 3), text[:80], fill=(235, 235, 235))
            draw.text((col * TILE[0] + 4, y + 17), path.name[:80], fill=(160, 160, 160))
            print(f"{real.stem:40s} {label:10s} {describe(l2, c2)}" + ("" if is_real else f" x{l2 / luma:.2f}"))
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, quality=88)
    print(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    m = sub.add_parser("measure")
    m.add_argument("images", nargs="+", type=Path)
    m.add_argument("--real", action="store_true")
    s = sub.add_parser("sheet")
    s.add_argument("out", type=Path)
    s.add_argument("rows", nargs="+", help="REAL.png=OURS1,OURS2 (folders or PNGs)")
    s.add_argument("--labels", default="")
    s.add_argument("--views", default="")
    args = ap.parse_args()
    if args.command == "measure":
        for path in args.images:
            print(f"{path.name:44s} {describe(*measure(path, args.real))}")
        return 0
    views = args.views.split(",") if args.views else []
    rows = []
    for k, spec in enumerate(args.rows):
        real, ours = spec.split("=", 1)
        real_path = Path(real) if Path(real).exists() else REAL_DIR / real
        view = views[k] if k < len(views) else ""
        rows.append((real_path, [find_shot(Path(p), view) for p in ours.split(",")]))
    sheet(args.out, rows, [x for x in args.labels.split(",") if x])
    return 0


if __name__ == "__main__":
    sys.exit(main())
