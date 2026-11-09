"""Prepare bounded native-reference sheets for missing NPC portrait candidates."""

import json
from pathlib import Path

from PIL import Image

from extract_raw_buttons import read_catalog


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def create_sheet(name, items, columns, rows, native_cell, transparent):
    cell_width, cell_height = native_cell
    width = columns * (cell_width + 4) * 2
    height = rows * (cell_height + 4) * 2
    background = (255, 0, 255, 255) if transparent else (31, 35, 37, 255)
    reference = Image.new("RGBA", (width, height), background)
    layout = []
    for index, item in enumerate(items):
        column, row = index % columns, index // columns
        x = (column * (cell_width + 4) + 2) * 2
        y = (row * (cell_height + 4) + 2) * 2
        with Image.open(HERE / item["original"]) as original:
            enlarged = original.convert("RGBA").resize(tuple(item["x2_size"]), Image.Resampling.NEAREST)
            if transparent:
                reference.alpha_composite(enlarged, (x, y))
            else:
                reference.paste(enlarged, (x, y))
        layout.append({"id": item["id"], "source_sha256": item["source_sha256"],
                       "reference_rect": [x, y, *item["x2_size"]], "x2_size": item["x2_size"]})
    target = HERE / "missing_npc_sheets" / name
    target.mkdir(parents=True, exist_ok=True)
    reference.save(target / "reference.png", optimize=True)
    (target / "layout.json").write_text(json.dumps({
        "schema": 1, "name": name, "reference_size": [width, height],
        "columns": columns, "rows": rows, "cells": layout,
    }, indent=2) + "\n")
    prompt = (
        "Use case: precise-object-edit. Asset type: OpenYAMM NPC dialogue portrait restoration sheet.\n"
        "The attached image is the exact source sheet. Reconstruct each portrait as a polished, faithful "
        "high-resolution painted game portrait while keeping every distinct person's face, age, ethnicity, "
        "expression, headwear, clothes, original background and framing. Preserve the complete grid, slot "
        "order, rectangular borders, sizes and gutters exactly. No new people or objects, no labels, no text. "
        "Do not blend identities between slots. Remove enlarged source pixels by painting natural material, "
        "hair and facial detail. Keep the original subdued fantasy palette and lighting. Output a single "
        "sheet with the same aspect ratio and at least the input resolution."
    )
    if transparent:
        prompt += (" Keep the magenta outer sheet gutters flat #FF00FF. Preserve the shape, position "
                   "and transparent regions of each irregular portrait cutout; do not add a new panel behind it.")
    (target / "prompt.txt").write_text(prompt + "\n")
    print(name, len(items), reference.size)


def main():
    catalog = read_catalog()
    missing = [item for item in catalog["items"] if item["category"] == "NPC portraits" and not item["candidates"]]
    opaque = [item for item in missing if item["native_size"] == [63, 73]]
    other = [item for item in missing if item["native_size"] != [63, 73]]
    for index in range(0, len(opaque), 48):
        batch = opaque[index:index + 48]
        create_sheet(f"opaque_{index // 48 + 1:02d}", batch, 6, 8, (63, 73), False)
    if other:
        size = (max(item["native_size"][0] for item in other),
                max(item["native_size"][1] for item in other))
        create_sheet("cutouts_01", other, 4, 3, size, True)


if __name__ == "__main__":
    main()
