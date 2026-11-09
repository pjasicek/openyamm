#!/usr/bin/env python3
"""
Prop lighting, old path against model_lighting (the 2026-10-31 re-light): the same bake and views rendered both ways.
The pixels that differ between the two runs are the props and actors (walls take the same lightmap). Per view: the
luma of those pixels in the capture, old path and model-lighting shots, and each relative to its own whole view (a prop
x1.0 is as bright as the view round it). The capture (old import) is too bright overall, so the relative numbers are
the comparison; MM9 itself draws props as bright as the walls or brighter (MM9_RENDER_LIGHTING_RE.md, Models).

    python3 level_generation/projects/mm9r_common/relight_props.py CAPTURE_DIR OLD_DIR MODEL_DIR [--threshold 6]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import binary_opening

LUMA = np.array([0.2126, 0.7152, 0.0722])


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), float) @ LUMA


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", type=Path)
    ap.add_argument("old", type=Path)
    ap.add_argument("model", type=Path)
    ap.add_argument("--threshold", type=float, default=6)
    ap.add_argument("--min-pixels", type=int, default=1500)
    args = ap.parse_args()
    print(f"{'view':28s} {'pixels':>7s} | {'capture':>7s} {'old':>6s} {'model':>6s} | relative to view: "
          f"{'capture':>7s} {'old':>6s} {'model':>6s}")
    rel = []
    for path in sorted(args.old.glob("*.png")):
        if not (args.model / path.name).exists():
            continue
        old, model = load(path), load(args.model / path.name)
        mask = binary_opening(np.abs(old - model) > args.threshold, iterations=2)
        if mask.sum() < args.min_pixels:
            continue
        cap = load(args.capture / path.name) if (args.capture / path.name).exists() else None
        values = []
        for image in (cap, old, model):
            if image is None or image.shape != old.shape:
                values.append((float("nan"), float("nan")))
                continue
            values.append((image[mask].mean(), image[mask].mean() / max(image.mean(), 1e-6)))
        rel.append([v[1] for v in values])
        print(f"{path.stem:28s} {int(mask.sum()):7d} | " + " ".join(f"{v[0]:7.1f}" for v in values) + " | "
              + "                  " + " ".join(f"{v[1]:7.2f}" for v in values))
    if rel:
        rel = np.array(rel)
        print(f"median relative brightness of the changed pixels: capture {np.nanmedian(rel[:, 0]):.2f}, "
              f"old path {np.nanmedian(rel[:, 1]):.2f}, model lighting {np.nanmedian(rel[:, 2]):.2f} "
              f"({len(rel)} views)")
        print(f"views with props under x0.6 of their view: old {int((rel[:, 1] < 0.6).sum())}, "
              f"model {int((rel[:, 2] < 0.6).sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
