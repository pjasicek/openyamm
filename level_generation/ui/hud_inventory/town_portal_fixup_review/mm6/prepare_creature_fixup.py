#!/usr/bin/env python3
"""Keep the approved map and composite only its two generated creature repairs."""

import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUT = HERE / "creature_fixup"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def region_mask(size, box, feather):
    x0, y0, x1, y1 = box
    yy, xx = np.mgrid[:size[1], :size[0]]
    distance = np.minimum.reduce([xx - x0, x1 - 1 - xx, yy - y0, y1 - 1 - yy])
    value = np.clip(distance / feather, 0, 1)
    value = value * value * (3 - 2 * value)
    return Image.fromarray(np.rint(value * 255).astype(np.uint8))


def main():
    if (HERE.parents[1] / "town_portal_acceptance_20260927/accepted.json").exists():
        raise SystemExit("This revision is accepted; create a new revision before preparing new artwork.")
    OUT.mkdir(exist_ok=True)
    original = Image.open(HERE / "attempt_01/raw.png").convert("RGB")
    first_edit = Image.open(HERE / "attempt_02/raw.png").convert("RGB")
    reduced = Image.open(HERE / "attempt_03/raw.png").convert("RGB")
    assert original.size == first_edit.size == reduced.size == (1448, 1086)

    # Use only the cleaned ground beneath the smaller figure from the focused AI repair.
    # The Kreegan itself remains exactly the user-requested reduced figure from attempt 03.
    cleanup = Image.open(HERE / "attempt_04/raw.png").convert("RGB")
    cleanup = cleanup.resize((116, 127), Image.Resampling.LANCZOS)
    cleanup_canvas = reduced.copy()
    cleanup_canvas.paste(cleanup, (177, 322))
    cleanup_mask = region_mask(original.size, (202, 427, 270, 446), 4)
    cleaned = Image.composite(cleanup_canvas, reduced, cleanup_mask)
    cleanup_mask.save(OUT / "cleanup_mask.png")

    regions = [
        {"name": "Kreegan", "box": [188, 333, 285, 445], "feather": 5,
         "source": "attempt_03/raw.png", "cleanup": "attempt_04/raw.png"},
        {"name": "Titan", "box": [390, 795, 459, 941], "feather": 7,
         "source": "attempt_02/raw.png"},
    ]
    result = original.copy()
    for region, source in zip(regions, [cleaned, first_edit]):
        mask = region_mask(original.size, region["box"], region["feather"])
        mask.save(OUT / (region["name"].lower() + "_mask.png"))
        result = Image.composite(source, result, mask)
    master = OUT / "master.png"
    result.save(master)
    export = OUT / "tpenroth.png"
    subprocess.run([
        "magick", str(master), "-filter", "Lanczos", "-resize", "1280x960",
        "-define", "png:color-type=2", str(export),
    ], check=True)

    before = np.asarray(Image.open(HERE / "attempt_01/tpenroth.png").convert("RGB"))
    after = np.asarray(Image.open(export).convert("RGB"))
    changed = np.any(before != after, axis=2)
    allowed = np.zeros(changed.shape, dtype=bool)
    for region in regions:
        x0, y0, x1, y1 = region["box"]
        box = [int(x0 * 1280 / 1448) - 4, int(y0 * 960 / 1086) - 4,
               int(x1 * 1280 / 1448) + 5, int(y1 * 960 / 1086) + 5]
        region["export_change_bounds"] = box
        allowed[box[1]:box[3], box[0]:box[2]] = True
    assert not np.any(changed & ~allowed), "Pixels changed outside the two local repairs"
    inputs = [HERE / f"attempt_{i:02}/raw.png" for i in range(1, 5)]
    inputs.append(HERE / "attempt_01/tpenroth.png")
    manifest = {
        "schema": 1, "target": "engine--icons--tpenroth.bmp", "status": "review_candidate",
        "logical_size": [640, 480], "export_size": [1280, 960],
        "background_approved_by_user": True, "accepted_in_ledger": False, "installed": False,
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in inputs],
        "master": {"path": str(master.relative_to(ROOT)), "sha256": digest(master), "size": list(result.size)},
        "export": {"path": str(export.relative_to(ROOT)), "sha256": digest(export)},
        "regions": regions,
        "processing": "Two feathered local generated patches over the approved original master; "
                      "only the tiny stray lettering repair is taken from attempt 04. "
                      "Full-canvas ImageMagick Lanczos downsample to x2.",
        "validation": {"result": "PASS", "changed_pixels": int(changed.sum()),
                       "all_other_map_pixels_identical": True, "opaque_rgb": True},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest["validation"], indent=2))


if __name__ == "__main__":
    main()
