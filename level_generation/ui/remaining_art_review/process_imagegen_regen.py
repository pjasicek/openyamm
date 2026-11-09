#!/usr/bin/env python3
"""Register and conservatively extract returned imagegen sheets for review.

No candidate is accepted here. Technical holds remain in the report and are
excluded from the review catalog until a corrected imagegen return is supplied.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label


HERE = Path(__file__).resolve().parent
RUN = HERE / "imagegen_regen"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def x2_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGBA")
    return image.convert("RGBa").resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def rectangular_region(image: Image.Image, expected: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
    """Find the actual opaque frame enclosed by generated magenta gutters."""
    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    magenta = (rgb[:, :, 0] > 150) & (rgb[:, :, 2] > 150) & (rgb[:, :, 1] < 115)
    magenta &= (rgb[:, :, 0] - rgb[:, :, 1] > 115) & (rgb[:, :, 2] - rgb[:, :, 1] > 115)
    occupied, count = label(~magenta)
    cx = min(image.width - 1, (expected[0] + expected[2]) // 2)
    cy = min(image.height - 1, (expected[1] + expected[3]) // 2)
    component = occupied[cy, cx]
    if component == 0 or count == 0:
        return None
    yy, xx = np.where(occupied == component)
    if len(xx) < 0.5 * (expected[2] - expected[0]) * (expected[3] - expected[1]):
        return None
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def metrics(original: Image.Image, candidate: Image.Image) -> dict:
    result = {}
    for threshold in (16, 128):
        first = np.asarray(original.getchannel("A")) >= threshold
        second = np.asarray(candidate.getchannel("A")) >= threshold
        union = int(np.logical_or(first, second).sum())
        intersection = int(np.logical_and(first, second).sum())
        result[f"iou_{threshold}"] = round(intersection / union, 4) if union else 1.0
        bounds = []
        centroids = []
        for mask in (first, second):
            yy, xx = np.where(mask)
            bounds.append([int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1]
                          if len(xx) else None)
            centroids.append([round(float(xx.mean()), 2), round(float(yy.mean()), 2)] if len(xx) else None)
        result[f"bounds_delta_{threshold}"] = [bounds[1][axis] - bounds[0][axis] for axis in range(4)] \
            if all(bounds) else None
        result[f"centroid_delta_{threshold}"] = [round(centroids[1][axis] - centroids[0][axis], 2)
                                                    for axis in range(2)] if all(centroids) else None
    return result


def process_sheet(sheet: dict, returns_dir: str = "returns", candidates_dir: str = "candidates") -> dict:
    name = sheet["id"]
    raw_path = RUN / returns_dir / f"{name}.png"
    if not raw_path.is_file():
        return {"id": name, "status": "awaiting_imagegen_return", "items": {}}
    raw = Image.open(raw_path)
    native_width, native_height = sheet["native_sheet_size"]
    sx, sy = raw.width / native_width, raw.height / native_height
    role = sheet["role"]
    record = {"id": name, "status": "processed", "raw": str(raw_path.relative_to(HERE)),
              "raw_sha256": digest(raw_path), "raw_size": list(raw.size),
              "sampling": [round(sx, 4), round(sy, 4)], "items": {}}
    if sx < 2 or sy < 2:
        record["status"] = "hold_sampling_below_x2"
        return record
    if role == "title_tile":
        record["status"] = "hold_title_assembly_pending"
        return record

    for cell in sheet["cells"]:
        target_id = cell["id"]
        x, y, width, height = cell["rect"]
        expected = (round(x * sx), round(y * sy), round((x + width) * sx), round((y + height) * sy))
        original = Image.open(HERE / "originals" / f"{target_id}.png").convert("RGBA")
        if digest(HERE / "originals" / f"{target_id}.png") != cell["original_sha256"]:
            raise ValueError(f"Original changed: {target_id}")
        if original.size != (width, height):
            raise ValueError(f"Native size changed: {target_id}")
        if role == "opaque":
            actual = rectangular_region(raw, expected)
            if actual is None:
                status = "hold_opaque_frame_not_found"
                region = expected
            else:
                dw = abs((actual[2] - actual[0]) - (expected[2] - expected[0]))
                dh = abs((actual[3] - actual[1]) - (expected[3] - expected[1]))
                status = "candidate_technical" if dw <= 0.08 * width * sx and dh <= 0.08 * height * sy \
                    else "hold_frame_geometry"
                region = actual
        else:
            region = expected
            status = "candidate_technical"
        crop = raw.crop(region).convert("RGBA")
        if role == "alpha":
            alpha = np.asarray(crop.getchannel("A"))
            if alpha.min() == 255:
                status = "hold_alpha_missing"
        else:
            crop.putalpha(Image.new("L", crop.size, 255))
        candidate = x2_resize(crop, (width * 2, height * 2))
        comparison = metrics(x2_resize(original, candidate.size), candidate) if role == "alpha" else {}
        if role == "alpha" and comparison["bounds_delta_128"] is None:
            status = "hold_empty_foreground"
        # Large shifts and missing subject area need a new imagegen return.
        if role == "alpha" and comparison["bounds_delta_128"] is not None:
            if max(abs(delta) for delta in comparison["bounds_delta_128"]) > max(8, 0.12 * max(candidate.size)):
                status = "hold_subject_registration"
            elif comparison["iou_128"] < 0.55 and original.getchannel("A").getbbox() is not None:
                status = "hold_subject_shape"
        destination = RUN / candidates_dir / target_id / "candidate-2x.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        candidate.save(destination, optimize=True)
        record["items"][target_id] = {
            "status": status, "source_sha256": cell["source_sha256"],
            "artifact": str(destination.relative_to(HERE)), "artifact_sha256": digest(destination),
            "region": list(region), "expected_region": list(expected), "metrics": comparison,
        }
    return record


def main() -> None:
    plan = json.loads((RUN / "plan.json").read_text())
    report = {"schema": 1, "tool": "built-in image_gen", "sheets": {}, "items": {}}
    for sheet in plan["sheets"]:
        record = process_sheet(sheet)
        report["sheets"][sheet["id"]] = {key: value for key, value in record.items() if key != "items"}
        report["items"].update(record["items"])
    (RUN / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    counts = {}
    for item in report["items"].values():
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print(json.dumps({"returned_sheets": sum(s["status"] != "awaiting_imagegen_return"
                                              for s in report["sheets"].values()),
                      "candidate_counts": counts}, indent=2))


if __name__ == "__main__":
    main()
