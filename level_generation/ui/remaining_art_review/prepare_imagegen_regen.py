#!/usr/bin/env python3
"""Prepare source-bound imagegen sheets for the former ESRGAN review slice.

This script only prepares references. A sheet becomes a review candidate only
after its returned master is registered, inspected, and extracted separately.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "imagegen_regen"
PADDING = 6
MAX_SIDE = 520
MAX_CELLS = 36
MAGENTA = (255, 0, 255, 255)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def catalog_items() -> list[dict]:
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].strip().removesuffix(";"))
    return [item for item in catalog["items"] if item["candidates"]
            and item["candidates"][0]["origin"] == "Native-geometry Real-ESRGAN repair"]


def source(item: dict) -> Image.Image:
    path = HERE / item["original"]
    image = Image.open(path).convert("RGBA")
    if image.size != tuple(item["native_size"]):
        raise ValueError(f"Native size changed: {item['id']}")
    return image


def kind(item: dict) -> str:
    image = source(item)
    if item["id"] == "engine--icons--title.png":
        return "tiled_title"
    if item["native_size"] == [444, 108] and item["name"].startswith("terra"):
        return "terra"
    if image.width * image.height > 80000 or max(image.size) > 500:
        return "large_alpha" if image.getchannel("A").getextrema() != (255, 255) else "large_opaque"
    return "small_alpha" if image.getchannel("A").getextrema() != (255, 255) else "small_opaque"


def packed(items: list[dict]) -> list[tuple[list[dict], list[dict], tuple[int, int]]]:
    """Shelf-pack nearby source identities into small sheets with hard gutters."""
    sheets = []
    current = []
    cells = []
    x = PADDING
    y = PADDING
    row_height = 0
    used_width = 0

    def flush() -> None:
        nonlocal current, cells, x, y, row_height, used_width
        if current:
            width = used_width + PADDING
            height = y + row_height + PADDING
            width = max(width, (height + 1) // 2)
            height = max(height, (width + 1) // 2)
            if width > MAX_SIDE or height > MAX_SIDE:
                raise ValueError(f"Cannot fit prepared sheet: {width}x{height}")
            sheets.append((current, cells, (width, height)))
        current, cells = [], []
        x, y, row_height, used_width = PADDING, PADDING, 0, 0

    for item in items:
        width, height = item["native_size"]
        if width + 2 * PADDING > MAX_SIDE or height + 2 * PADDING > MAX_SIDE:
            raise ValueError(f"Individual source exceeds small-sheet canvas: {item['id']}")
        if x + width + PADDING > MAX_SIDE:
            x = PADDING
            y += row_height + 2 * PADDING
            row_height = 0
        if y + height + PADDING > MAX_SIDE or len(current) >= MAX_CELLS:
            flush()
        current.append(item)
        cells.append({"id": item["id"], "rect": [x, y, width, height],
                      "source_sha256": item["source_sha256"], "original_sha256": digest(HERE / item["original"])})
        used_width = max(used_width, x + width)
        row_height = max(row_height, height)
        x += width + 2 * PADDING
    flush()
    return sheets


def make_sheet(name: str, items: list[dict], cells: list[dict], size: tuple[int, int], role: str) -> dict:
    native = Image.new("RGBA", size, MAGENTA)
    for item, cell in zip(items, cells):
        image = source(item)
        if role == "opaque":
            if image.getchannel("A").getextrema() != (255, 255):
                raise ValueError(f"Transparent source on opaque sheet: {item['id']}")
            native.paste(image, cell["rect"][:2])
        else:
            native.alpha_composite(image, cell["rect"][:2])
    path = OUTPUT / "references" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    native.resize((size[0] * 2, size[1] * 2), Image.Resampling.NEAREST).save(path)
    return {"id": name, "role": role, "reference": str(path.relative_to(HERE)),
            "reference_sha256": digest(path), "native_sheet_size": list(size),
            "reference_size": [size[0] * 2, size[1] * 2], "cells": cells,
            "status": "prepared_only"}


def main() -> None:
    items = catalog_items()
    if len(items) != 590:
        raise ValueError(f"Expected 590 former ESRGAN primary targets, found {len(items)}")
    by_kind = defaultdict(list)
    for item in items:
        by_kind[kind(item)].append(item)
    sheets = []
    for role in ("small_alpha", "small_opaque"):
        for category in sorted({item["treatment"] for item in by_kind[role]}):
            group = sorted((item for item in by_kind[role] if item["treatment"] == category),
                           key=lambda item: (item["family"], item["id"]))
            for number, (members, cells, size) in enumerate(packed(group), 1):
                name = f"{role}-{category}-{number:03d}"
                sheets.append(make_sheet(name, members, cells, size,
                                         "alpha" if role == "small_alpha" else "opaque"))
    terra = sorted(by_kind["terra"], key=lambda item: item["id"])
    for offset in range(0, len(terra), 6):
        group = terra[offset:offset + 6]
        cells = [{"id": item["id"], "rect": [6, 6 + index * 120, 444, 108],
                  "source_sha256": item["source_sha256"],
                  "original_sha256": digest(HERE / item["original"])}
                 for index, item in enumerate(group)]
        height = len(group) * 120
        sheets.append(make_sheet(f"terra-{offset // 6 + 1:03d}", group, cells,
                                 (456, max(228, height)), "opaque"))
    for role in ("large_alpha", "large_opaque"):
        for number, item in enumerate(sorted(by_kind[role], key=lambda row: row["id"]), 1):
            width, height = item["native_size"]
            cell = {"id": item["id"], "rect": [6, 6, width, height],
                    "source_sha256": item["source_sha256"],
                    "original_sha256": digest(HERE / item["original"])}
            sheet_width, sheet_height = width + 12, height + 12
            sheet_width = max(sheet_width, (sheet_height + 1) // 2)
            sheet_height = max(sheet_height, (sheet_width + 1) // 2)
            sheets.append(make_sheet(f"{role}-{number:03d}", [item], [cell],
                                     (sheet_width, sheet_height),
                                     "alpha" if role == "large_alpha" else "opaque"))
    if len(by_kind["tiled_title"]) != 1:
        raise ValueError("Expected one oversized title image")
    title = by_kind["tiled_title"][0]
    image = source(title)
    # Overlapping original-coordinate tiles give imagegen enough context for
    # seam checks and allow a true 2x final canvas after registration.
    for row, top in enumerate((0, 421), 1):
        for column, left in enumerate((0, 554, 1108), 1):
            width = min(584, image.width - left)
            height = min(520, image.height - top)
            if width < 520 or height < 400:
                raise ValueError("Title tiling left an undersized terminal tile")
            tile = image.crop((left, top, left + width, top + height))
            name = f"title-r{row}c{column}"
            path = OUTPUT / "references" / f"{name}.png"
            tile.resize((width * 2, height * 2), Image.Resampling.NEAREST).save(path)
            sheets.append({"id": name, "role": "title_tile", "reference": str(path.relative_to(HERE)),
                           "reference_sha256": digest(path), "native_sheet_size": [width, height],
                           "reference_size": [width * 2, height * 2],
                           "cells": [{"id": title["id"], "rect": [0, 0, width, height],
                                      "source_sha256": title["source_sha256"],
                                      "original_sha256": digest(HERE / title["original"]),
                                      "tile_origin": [left, top]}], "status": "prepared_only"})
    manifest = {"schema": 1, "tool": "built-in image_gen", "target_count": len(items),
                "sheet_count": len(sheets), "sheets": sheets}
    (OUTPUT / "plan.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"targets": len(items), "sheets": len(sheets),
                      "by_kind": {key: len(value) for key, value in by_kind.items()},
                      "by_role": {key: sum(sheet["role"] == key for sheet in sheets)
                                  for key in {sheet["role"] for sheet in sheets}}}, indent=2))


if __name__ == "__main__":
    main()
