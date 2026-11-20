"""Pack full retained paper-backed spell masters for batched alpha editing.

Every cell has the same measured canvas, generous gutters, and its native
original in an identically registered second sheet. No native art is upscaled
to make the detailed master reference.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
BATCHES = [
    ["sbb01", "sbb02", "sbb04", "sbb06"],
    ["sbb03", "sbb05", "sbb09"],
    ["sbb07", "sbb08", "sbb10", "sbb11"],
    ["sba04", "sba11", "sbe11", "sbm06"],
    ["sbl01", "sbl07", "sbl10", "sbw02"],
    ["sbl04", "sbl05", "sbdk03"],
    ["sbs11", "sbw07", "sbw04", "sbw05"],
    ["sbm11", "sbs01"],
]
GUTTER = 32


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paper_bounds(image, kind):
    rgb = np.asarray(image.convert("RGB"), dtype=int)
    if kind == "magenta matte and paper":
        mask = ~((rgb[:, :, 0] > 165) & (rgb[:, :, 2] > 145) & (rgb[:, :, 1] < 115))
    elif kind == "dark gutter and paper":
        mask = (rgb[:, :, 0] * 3 + rgb[:, :, 1] * 6 + rgb[:, :, 2]) / 10 > 65
        mask = ndimage.binary_closing(mask, iterations=2)
    else:
        raise ValueError(f"Not a paper-backed sheet: {kind}")
    labels, count = ndimage.label(mask)
    if count == 0:
        raise ValueError("Paper panel is empty")
    areas = np.bincount(labels.ravel())
    areas[0] = 0
    rows, columns = np.nonzero(labels == np.argmax(areas))
    return [int(columns.min()), int(rows.min()), int(columns.max()) + 1, int(rows.max()) + 1]


def main():
    frozen = HERE / "paper_batches.json"
    if frozen.is_file():
        plans = json.loads(frozen.read_text())["batches"]
        for plan in plans:
            directory = HERE / f"paper_batches/{plan['batch']:02d}"
            layout = json.loads((directory / "layout.json").read_text())
            if digest(directory / "restored_reference.png") != layout["restored_reference_sha256"]:
                raise ValueError(f"Frozen restored reference changed: {directory}")
            if digest(directory / "original_reference.png") != layout["original_reference_sha256"]:
                raise ValueError(f"Frozen native reference changed: {directory}")
            if not (directory / "raw.png").is_file():
                raise ValueError(f"Frozen batch is missing its return: {directory}")
        print(f"Verified {len(plans)} frozen paper-edit batches; references are unchanged")
        return
    audit = json.loads((HERE / "manifest.json").read_text())
    items = {item["name"]: item for item in audit["items"]}
    paper_pairs = {item["pair"] for item in audit["items"] if item["matte_kind"] != "native alpha"}
    assigned = [pair for group in BATCHES for pair in group]
    if set(assigned) != paper_pairs or len(assigned) != len(paper_pairs):
        raise ValueError("Paper batch list must cover every paper-backed pair exactly once")
    panel_root = HERE / "paper_panels"
    panel_root.mkdir(exist_ok=True)
    plans = []
    for number, pairs in enumerate(BATCHES, 1):
        states = [items[pair + state] for pair in pairs for state in "ab"]
        cell_width = max(item["x2_size"][0] for item in states)
        cell_height = max(item["x2_size"][1] for item in states)
        width = cell_width * 2 + GUTTER * 3
        height = cell_height * len(pairs) + GUTTER * (len(pairs) + 1)
        if width * height > 1_360_000:
            raise ValueError(f"Paper reference exceeds 1.36 MP budget: {number} {width}x{height}")
        master_sheet = Image.new("RGB", (width, height), "#28272b")
        native_sheet = Image.new("RGB", (width, height), "#28272b")
        cells = []
        for index, item in enumerate(states):
            raw = Image.open(HERE / item["slot"]).convert("RGB")
            box = paper_bounds(raw, item["matte_kind"])
            panel = raw.crop(box)
            target_size = tuple(item["x2_size"])
            native = Image.open(REVIEW / item["original"].removeprefix("../")).convert("RGBA")
            if native.size != tuple(item["native_size"]):
                raise ValueError(f"Native source changed: {item['name']}")
            # This is a detailed generated master reduced to the exact 2x canvas.
            detailed = panel.resize(target_size, Image.Resampling.LANCZOS)
            panel_path = panel_root / (item["id"] + ".png")
            detailed.save(panel_path, optimize=True)
            native = native.resize(target_size, Image.Resampling.NEAREST)
            col, row = index % 2, index // 2
            x = GUTTER + col * (cell_width + GUTTER) + (cell_width - target_size[0]) // 2
            y = GUTTER + row * (cell_height + GUTTER) + (cell_height - target_size[1]) // 2
            master_sheet.paste(detailed, (x, y))
            native_sheet.paste(native, (x, y), native)
            cells.append({"id": item["id"], "name": item["name"], "state": item["state"],
                          "source_sha256": item["source_sha256"], "slot_sha256": item["slot_sha256"],
                          "panel_rect_in_slot": box, "panel_size": list(panel.size),
                          "x2_size": item["x2_size"], "rect": [x, y, *target_size],
                          "master_panel": "../../paper_panels/" + panel_path.name,
                          "master_panel_sha256": digest(panel_path)})
        directory = HERE / "paper_batches" / f"{number:02d}"
        directory.mkdir(parents=True, exist_ok=True)
        master_path = directory / "restored_reference.png"
        native_path = directory / "original_reference.png"
        master_sheet.save(master_path, optimize=True)
        native_sheet.save(native_path, optimize=True)
        prompt = (
            "Edit the RESTORED spell-art sheet into a true RGBA transparent-foreground sheet. "
            "The other sheet contains the matching native ORIGINALS in exactly the same cell grid and order; "
            "use those originals as the binding reference for subject identity, all glyph counts/shapes/positions "
            "and complete canvas bounds. Restore the existing detailed drawing and glyphs from the restored "
            "sheet; remove only the parchment/background within every cell. Keep all figures, complete extremities, "
            "smoke, glow, fine hatch marks, and every detached glyph. Do not crop, enlarge, recenter, invent glyphs, "
            "or move content between cells. Each row is a color/sepia pair. Keep the paired states matched and their "
            "own colors. Keep the dark gutters empty and transparent. Return one complete grid PNG with true alpha, "
            "not a painted checkerboard. Preserve the complete rectangular cell grid and its generous gutters. "
            f"This sheet has {len(pairs)} rows and 2 columns, from top to bottom: {', '.join(pairs)}."
        )
        prompt_path = directory / "prompt.txt"
        prompt_path.write_text(prompt + "\n")
        layout = {"schema": 1, "pairs": pairs, "reference_size": [width, height],
                  "cell_size": [cell_width, cell_height], "gutter": GUTTER,
                  "restored_reference_sha256": digest(master_path),
                  "original_reference_sha256": digest(native_path),
                  "prompt_sha256": digest(prompt_path), "cells": cells}
        (directory / "layout.json").write_text(json.dumps(layout, indent=2) + "\n")
        plans.append({"batch": number, "pairs": pairs, "size": [width, height],
                      "megapixels": round(width * height / 1_000_000, 3),
                      "reference": str(master_path.relative_to(HERE)),
                      "original_reference": str(native_path.relative_to(HERE)),
                      "layout": str((directory / "layout.json").relative_to(HERE)),
                      "prompt": str(prompt_path.relative_to(HERE))})
    (HERE / "paper_batches.json").write_text(json.dumps({"schema": 1, "batches": plans}, indent=2) + "\n")
    for plan in plans:
        print(plan["batch"], ",".join(plan["pairs"]), plan["size"], plan["megapixels"])


if __name__ == "__main__":
    main()
