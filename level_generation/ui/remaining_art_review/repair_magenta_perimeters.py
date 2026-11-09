#!/usr/bin/env python3
"""Remove one-pixel magenta matte from opaque review art and flagged UI icons."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REPAIR = HERE / "magenta_perimeter"
PREFIXES = ("terra", "t_", "bt_")
REVIEWED_EDGE_IDS = {
    "engine--icons--ticon03.bmp", "engine--icons--ticon04.bmp",
    "engine--icons--tpharmon.bmp", "engine--icons--tpisl.bmp",
    "engine--icons--tpmist.bmp", "engine--icons--tpwarl.bmp",
    "worlds-mm8--icons--outside.bmp",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def saturated_magenta(rgb: np.ndarray) -> np.ndarray:
    channels = rgb.astype(np.int16)
    red, green, blue = (channels[:, :, index] for index in range(3))
    return (red > 150) & (blue > 150) & (green < 140) & (np.minimum(red, blue) - green > 70)


def perimeter(values: np.ndarray) -> np.ndarray:
    return np.concatenate((values[0, :], values[-1, :], values[1:-1, 0], values[1:-1, -1]))


def base_candidate(item: dict, old_items: dict) -> tuple[Path, str, str]:
    previous = old_items.get(item["id"])
    if previous:
        path = HERE / previous["input_artifact"]
        if sha256(path) != previous["input_sha256"]:
            raise ValueError(f"Changed input candidate: {item['id']}")
        return path, previous["input_sha256"], previous["input_origin"]
    choice = item["candidates"][0]
    path = HERE / choice["path"]
    if sha256(path) != choice["sha256"]:
        raise ValueError(f"Changed input candidate: {item['id']}")
    return path, choice["sha256"], choice["origin"]


def main() -> None:
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].strip().removesuffix(";"))
    report_path = REPAIR / "report.json"
    old_items = json.loads(report_path.read_text())["items"] if report_path.is_file() else {}
    report = {"schema": 1, "tool": "one-pixel opaque perimeter reconstruction", "items": {}}
    family_counts = Counter()
    for item in catalog["items"]:
        family = next((prefix for prefix in PREFIXES if item["name"].lower().startswith(prefix)), None)
        if item["id"] in REVIEWED_EDGE_IDS:
            family = "reviewed_edge_note"
        if family is None:
            continue
        original_path = HERE / item["original"]
        input_path, input_hash, input_origin = base_candidate(item, old_items)
        with Image.open(original_path) as file:
            original = np.asarray(file.convert("RGBA"))
        with Image.open(input_path) as file:
            candidate = np.asarray(file.convert("RGBA"))
        if candidate.shape[:2] != (item["x2_size"][1], item["x2_size"][0]):
            raise ValueError(f"Wrong input canvas: {item['id']}")
        if np.any(original[:, :, 3] != 255) or np.any(candidate[:, :, 3] != 255):
            raise ValueError(f"Expected opaque source and candidate: {item['id']}")
        source_magenta = int(saturated_magenta(original[:, :, :3]).sum())
        if source_magenta:
            raise ValueError(f"Source contains visible magenta; manual inspection needed: {item['id']}")
        if min(candidate.shape[:2]) < 4:
            raise ValueError(f"Canvas too small for perimeter repair: {item['id']}")
        before = saturated_magenta(candidate[:, :, :3])
        input_boundary_magenta = int(perimeter(before).sum())
        contrast = np.minimum(candidate[:, :, 0], candidate[:, :, 2]).astype(np.int16) \
            - candidate[:, :, 1].astype(np.int16)
        input_boundary_high_chroma = int(np.sum(perimeter(contrast) > 40))
        clean = candidate.copy()
        # Four terra frames have a few keyed pixels in the second row or
        # column. Replace those from the next fully interior pixel first.
        height, width = before.shape
        for edge_y, edge_x in np.argwhere(before):
            depth = min(edge_y, edge_x, height - 1 - edge_y, width - 1 - edge_x)
            if depth != 1:
                continue
            inside_y = 2 if edge_y == 1 else height - 3 if edge_y == height - 2 else edge_y
            inside_x = 2 if edge_x == 1 else width - 3 if edge_x == width - 2 else edge_x
            clean[edge_y, edge_x] = candidate[inside_y, inside_x]
        # Every outer-edge pixel came from the generated magenta gutter. Extend
        # the immediately adjacent artwork one pixel; do not alter interior art.
        clean[0, 1:-1] = clean[1, 1:-1]
        clean[-1, 1:-1] = clean[-2, 1:-1]
        clean[1:-1, 0] = clean[1:-1, 1]
        clean[1:-1, -1] = clean[1:-1, -2]
        clean[0, 0] = clean[1, 1]
        clean[0, -1] = clean[1, -2]
        clean[-1, 0] = clean[-2, 1]
        clean[-1, -1] = clean[-2, -2]
        after = saturated_magenta(clean[:, :, :3])
        output_boundary_magenta = int(perimeter(after).sum())
        if output_boundary_magenta:
            raise ValueError(f"Visible magenta remains on perimeter: {item['id']}")
        target_path = REPAIR / "candidates" / item["id"] / "candidate-2x.png"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(clean, "RGBA").save(target_path, optimize=True)
        report["items"][item["id"]] = {
            "status": "candidate_technical", "source_sha256": item["source_sha256"],
            "artifact": str(target_path.relative_to(HERE)), "artifact_sha256": sha256(target_path),
            "input_artifact": str(input_path.relative_to(HERE)), "input_sha256": input_hash,
            "input_origin": input_origin,
            "method": "replaced opaque one-pixel matte perimeter with adjacent generated artwork",
            "source_visible_magenta": source_magenta,
            "input_boundary_magenta": input_boundary_magenta,
            "input_boundary_high_chroma": input_boundary_high_chroma,
            "output_boundary_magenta": output_boundary_magenta,
        }
        family_counts[family] += 1
    if dict(family_counts) != {"terra": 243, "t_": 12, "bt_": 14, "reviewed_edge_note": 7}:
        raise ValueError(f"Unexpected target family counts: {family_counts}")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"repaired": len(report["items"]), "families": family_counts,
                      "input_boundary_magenta": sum(row["input_boundary_magenta"]
                                                     for row in report["items"].values()),
                      "output_boundary_magenta": 0}, indent=2))


if __name__ == "__main__":
    main()
