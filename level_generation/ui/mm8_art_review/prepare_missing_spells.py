"""Prepare paired native-reference sheets for missing MM8 spell icon states."""

import json
from pathlib import Path

from PIL import Image

from extract_raw_buttons import read_catalog


HERE = Path(__file__).resolve().parent


def main():
    catalog = read_catalog()
    missing = [row for row in catalog["items"] if row["category"] == "Spell icons" and not row["candidates"]]
    by_pair = {}
    for item in missing:
        by_pair.setdefault(item["name"][:-1], {})[item["name"][-1]] = item
    pairs = []
    for name, states in sorted(by_pair.items()):
        if set(states) != {"a", "b"}:
            raise ValueError(f"Incomplete spell state pair: {name}")
        pairs.append((states["a"], states["b"]))
    for start in range(0, len(pairs), 2):
        group = pairs[start:start + 2]
        cells = [item for pair in group for item in pair]
        max_width = max(item["native_size"][0] for item in cells)
        max_height = max(item["native_size"][1] for item in cells)
        width = 2 * (max_width + 4) * 2
        height = len(group) * (max_height + 4) * 2
        reference = Image.new("RGBA", (width, height), (35, 29, 26, 255))
        layout = []
        for index, item in enumerate(cells):
            x = ((index % 2) * (max_width + 4) + 2) * 2
            y = ((index // 2) * (max_height + 4) + 2) * 2
            with Image.open(HERE / item["original"]) as original:
                enlarged = original.convert("RGBA").resize(tuple(item["x2_size"]), Image.Resampling.NEAREST)
                reference.alpha_composite(enlarged, (x, y))
            layout.append({"id": item["id"], "source_sha256": item["source_sha256"],
                           "reference_rect": [x, y, *item["x2_size"]], "x2_size": item["x2_size"]})
        target = HERE / "missing_spell_sheets" / f"pair_sheet_{start // 2 + 1:02d}"
        target.mkdir(parents=True, exist_ok=True)
        reference.save(target / "reference.png", optimize=True)
        (target / "layout.json").write_text(json.dumps({
            "schema": 1, "reference_size": [width, height], "cells": layout,
            "pairs": [pair[0]["name"][:-1] for pair in group],
        }, indent=2) + "\n")
        (target / "prompt.txt").write_text(
            "Use case: precise-object-edit. Asset type: OpenYAMM MM8 spellbook illustration restoration sheet. "
            f"The reference has {len(group)} colored/sepia spell-state pairs, one pair per row in a fixed "
            "two-column grid. Restore each complete canvas faithfully at high resolution. Preserve its own "
            "parchment, glyphs, drawing, ink density, lighting, palette, state color relationship, exact "
            "framing and original bounds. Keep pair members as the same drawing in colored and sepia states. "
            "Keep every distinctive figure, symbol and spell effect; do not add words, symbols, page borders, "
            "new paper rectangles or extra artwork. Preserve slot order, dark gutters, row heights and sheet "
            f"aspect ratio. Output one complete sheet at least {width}x{height}.\n"
        )
        print(target.name, [pair[0]["name"][:-1] for pair in group], reference.size)


if __name__ == "__main__":
    main()
