"""Extract batch-edited spell foregrounds at measured returned gutters.

This creates review previews only. A sheet with weak gutters or too little
native sampling fails instead of silently clipping or borrowing a neighbor.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from prepare import occupancy, split_axis


HERE = Path(__file__).resolve().parent
SUPERSEDED_PAIRS = {"sba04", "sba11"}  # Their full magenta masters retain glyphs; the paper-edit input did not.


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def content_bounds(image):
    pixels = np.asarray(image.convert("RGBA")).copy()
    labels, count = ndimage.label(pixels[:, :, 3] > 12)
    if count:
        sizes = np.bincount(labels.ravel())
        keep = (labels == 0) | (sizes[labels] >= 6)
        pixels[:, :, 3][~keep] = 0
    image = Image.fromarray(pixels, "RGBA")
    rows, columns = np.nonzero(pixels[:, :, 3] > 32)
    if len(rows) == 0:
        raise ValueError("Edited spell cell is empty")
    box = [max(0, int(columns.min()) - 3), max(0, int(rows.min()) - 3),
           min(image.width, int(columns.max()) + 4), min(image.height, int(rows.max()) + 4)]
    return image.crop(box), box


def main():
    batch_index = json.loads((HERE / "paper_batches.json").read_text())["batches"]
    output = HERE / "paper_candidates"
    output.mkdir(exist_ok=True)
    results = []
    failures = []
    for batch in batch_index:
        directory = HERE / f"paper_batches/{batch['batch']:02d}"
        raw_path = directory / "raw.png"
        if not raw_path.is_file():
            continue
        layout = json.loads((directory / "layout.json").read_text())
        with Image.open(raw_path) as raw:
            if raw.mode != "RGBA" or raw.getchannel("A").getextrema() != (0, 255):
                failures.append({"batch": batch["batch"], "reason": "return lacks true RGBA alpha"})
                continue
            occupied, _ = occupancy(raw)
            xs, x_splits = split_axis(occupied, 2, "x")
            ys, y_splits = split_axis(occupied, len(layout["pairs"]), "y")
            weak = [entry for entry in x_splits + y_splits if entry["occupied_fraction"] > 0.01]
            if weak:
                failures.append({"batch": batch["batch"], "reason": "weak gutter", "splits": weak})
                continue
            cells = {}
            for index, cell in enumerate(layout["cells"]):
                col, row = index % 2, index // 2
                sheet_box = [xs[col], ys[row], xs[col + 1], ys[row + 1]]
                panel, art_box = content_bounds(raw.crop(sheet_box))
                cells[cell["name"]] = (cell, panel, sheet_box, art_box)
            for pair in layout["pairs"]:
                if pair in SUPERSEDED_PAIRS:
                    continue
                a, b = cells[pair + "a"], cells[pair + "b"]
                pair_width = max(a[1].width, b[1].width)
                pair_height = max(a[1].height, b[1].height)
                target_width = min(a[0]["x2_size"][0], b[0]["x2_size"][0])
                target_height = min(a[0]["x2_size"][1], b[0]["x2_size"][1])
                scale = min(1, (target_width - 4) / pair_width, (target_height - 4) / pair_height)
                for cell, panel, sheet_box, art_box in (a, b):
                    target_size = cell["x2_size"]
                    native_size = [value / 2 for value in target_size]
                    sampling = [panel.width / native_size[0], panel.height / native_size[1]]
                    if min(sampling) < 2:
                        failures.append({"batch": batch["batch"], "name": cell["name"],
                                         "reason": "raw foreground below 2 generated pixels/native pixel",
                                         "sampling": sampling})
                        continue
                    size = [round(panel.width * scale), round(panel.height * scale)]
                    fitted = panel.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")
                    canvas = Image.new("RGBA", target_size)
                    offset = [(canvas.width - fitted.width) // 2, (canvas.height - fitted.height) // 2]
                    canvas.alpha_composite(fitted, tuple(offset))
                    target = output / (cell["id"] + ".png")
                    canvas.save(target, optimize=True)
                    results.append({"id": cell["id"], "name": cell["name"], "pair": pair,
                                    "state": cell["state"], "batch": batch["batch"],
                                    "path": "paper_candidates/" + target.name, "sha256": digest(target),
                                    "raw": str(raw_path.relative_to(HERE)), "raw_sha256": digest(raw_path),
                                    "sheet_box": sheet_box, "art_box": art_box,
                                    "actual_sampling": [round(value, 3) for value in sampling],
                                    "shared_scale": round(scale, 6), "fitted_size": size,
                                    "offset": offset, "x2_size": target_size})
    report = {"schema": 1, "description": "measured transparent paper-edit crops; all require visual review",
              "states": len(results), "batches": len({r["batch"] for r in results}),
              "items": results, "failures": failures}
    (HERE / "paper_candidates.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"states": report["states"], "batches": report["batches"],
                      "failures": failures}, indent=2))


if __name__ == "__main__":
    main()
