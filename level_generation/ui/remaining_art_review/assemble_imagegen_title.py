#!/usr/bin/env python3
"""Assemble the six overlapping imagegen title tiles at exact native 2× size."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
RUN = HERE / "imagegen_regen"
TARGET_ID = "engine--icons--title.png"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ramp(length: int, before: int, after: int) -> np.ndarray:
    values = np.ones(length, dtype=np.float32)
    if before:
        values[:before] = np.linspace(0, 1, before, dtype=np.float32)
    if after:
        values[-after:] = np.linspace(1, 0, after, dtype=np.float32)
    return values


def main() -> None:
    plan = json.loads((RUN / "plan.json").read_text())
    sheets = [sheet for sheet in plan["sheets"] if sheet["id"].startswith("title-")]
    source = HERE / "originals" / f"{TARGET_ID}.png"
    with Image.open(source) as original:
        width, height = original.size
    output = np.zeros((height * 2, width * 2, 3), dtype=np.float32)
    weight = np.zeros((height * 2, width * 2, 1), dtype=np.float32)
    tiles = []
    for sheet in sheets:
        name = sheet["id"]
        raw_path = RUN / "returns" / f"{name}.png"
        if not raw_path.is_file():
            raise FileNotFoundError(raw_path)
        cell = sheet["cells"][0]
        x, y = (coordinate * 2 for coordinate in cell["tile_origin"])
        tile_width, tile_height = (dimension * 2 for dimension in sheet["native_sheet_size"])
        with Image.open(raw_path) as raw:
            if raw.width < tile_width or raw.height < tile_height:
                raise ValueError(f"Below 2×: {name} {raw.size} versus {(tile_width, tile_height)}")
            image = raw.convert("RGB").resize((tile_width, tile_height), Image.Resampling.LANCZOS)
        array = np.asarray(image, dtype=np.float32)
        overlap_left = 60 if x else 0
        overlap_right = 60 if x + tile_width < width * 2 else 0
        overlap_top = 198 if y else 0
        overlap_bottom = 198 if y + tile_height < height * 2 else 0
        horizontal = ramp(tile_width, overlap_left, overlap_right)
        vertical = ramp(tile_height, overlap_top, overlap_bottom)
        tile_weight = (vertical[:, None] * horizontal[None, :])[:, :, None]
        output[y:y + tile_height, x:x + tile_width] += array * tile_weight
        weight[y:y + tile_height, x:x + tile_width] += tile_weight
        tiles.append({"id": name, "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                      "raw_size": list(Image.open(raw_path).size), "origin_2x": [x, y]})
    if np.any(weight == 0):
        raise ValueError("Title assembly has uncovered pixels")
    image = Image.fromarray(np.uint8(np.clip(np.rint(output / weight), 0, 255)), "RGB")
    destination = RUN / "candidates" / TARGET_ID / "candidate-2x.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)
    (RUN / "title_assembly.json").write_text(json.dumps({
        "schema": 1, "status": "candidate_technical", "source_sha256": sheets[0]["cells"][0]["source_sha256"],
        "original_sha256": sha256(source), "artifact": str(destination.relative_to(HERE)),
        "artifact_sha256": sha256(destination), "native_size": [width, height],
        "method": "six independent imagegen tiles, exact 2× resize and overlap feathering",
        "tiles": tiles,
    }, indent=2) + "\n")
    print(f"Assembled {destination} at {image.size}")


if __name__ == "__main__":
    main()
