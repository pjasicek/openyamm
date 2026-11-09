#!/usr/bin/env python3
"""Repack held imagegen cells into regular, generously separated retry sheets."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
RUN = HERE / "imagegen_regen"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def group_key(sheet: dict, cell: dict) -> tuple[str, str]:
    name = sheet["id"]
    if name.startswith("small_alpha-inventory_items"):
        width, height = cell["rect"][2:]
        size = "small" if max(width, height) <= 80 else "medium" if max(width, height) <= 140 else "large"
        return "inventory", size
    if name.startswith("small_alpha-legacy_ui_art"):
        return "effects", "small"
    if name.startswith("small_opaque"):
        return "opaque_controls", "mixed"
    return "other", "mixed"


def pack_group(cells: list[dict], kind: str) -> list[dict]:
    sheets = []
    while cells:
        for count in range(min(16, len(cells)), 0, -1):
            batch = cells[:count]
            max_width = max(item["width"] for item in batch)
            max_height = max(item["height"] for item in batch)
            columns = min(4, math.ceil(math.sqrt(count)))
            rows = math.ceil(count / columns)
            width = columns * (max_width + 20) + 12
            height = rows * (max_height + 20) + 12
            if width <= 540 and height <= 540:
                break
        else:
            raise ValueError(f"Cannot fit {cells[0]['id']}")
        canvas = Image.new("RGBA", (width, height), (255, 0, 255, 255))
        output_cells = []
        for index, item in enumerate(batch):
            column, row = index % columns, index // columns
            x = 16 + column * (max_width + 20) + (max_width - item["width"]) // 2
            y = 16 + row * (max_height + 20) + (max_height - item["height"]) // 2
            original_path = HERE / "originals" / f"{item['id']}.png"
            original = Image.open(original_path).convert("RGBA")
            canvas.alpha_composite(original, (x, y))
            output_cells.append({
                "id": item["id"], "rect": [x, y, item["width"], item["height"]],
                "source_sha256": item["source_sha256"], "original_sha256": sha256(original_path),
            })
        sheets.append({"role": kind, "native_sheet_size": list(canvas.size), "cells": output_cells,
                       "reference_image": canvas})
        del cells[:count]
    return sheets


def main() -> None:
    plan = json.loads((RUN / "plan.json").read_text())
    report = json.loads((RUN / "report.json").read_text())
    originals = {cell["id"]: (sheet, cell) for sheet in plan["sheets"] for cell in sheet["cells"]}
    groups: dict[tuple[str, str], list[dict]] = {}
    for target_id, item in report["items"].items():
        if item["status"] == "candidate_technical":
            continue
        sheet, cell = originals[target_id]
        if not sheet["id"].startswith(("small_alpha", "small_opaque")):
            continue
        width, height = cell["rect"][2:]
        groups.setdefault(group_key(sheet, cell), []).append({
            "id": target_id, "width": width, "height": height,
            "source_sha256": cell["source_sha256"],
        })
    folder = RUN / "retry_references"
    folder.mkdir(exist_ok=True)
    new_sheets = []
    for (family, size), cells in sorted(groups.items()):
        cells.sort(key=lambda item: (max(item["width"], item["height"]), item["id"]), reverse=True)
        kind = "opaque" if family == "opaque_controls" else "alpha"
        for index, sheet in enumerate(pack_group(cells, kind), 1):
            name = f"retry-{family}-{size}-{index:03d}"
            reference = folder / f"{name}.png"
            sheet.pop("reference_image").save(reference, optimize=True)
            sheet.update({"id": name, "reference": str(reference.relative_to(HERE)),
                          "reference_sha256": sha256(reference)})
            new_sheets.append(sheet)
    (RUN / "retry_plan.json").write_text(json.dumps({"schema": 1, "sheets": new_sheets}, indent=2) + "\n")
    print(json.dumps({"sheets": len(new_sheets), "targets": sum(len(sheet["cells"]) for sheet in new_sheets),
                      "groups": {str(key): len(value) for key, value in groups.items()}}, indent=2))


if __name__ == "__main__":
    main()
