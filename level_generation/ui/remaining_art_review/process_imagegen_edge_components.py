#!/usr/bin/env python3
"""Recover complete imagegen components that overran their nominal cell crop."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from process_imagegen_components import components
from process_imagegen_regen import HERE, RUN, metrics, x2_resize


TARGETS = (
    "engine--icons--pc07lwp1.bmp",
    "engine--icons--sp71e20.bmp", "engine--icons--sp71e30.bmp",
    "engine--icons--sp71e40.bmp", "engine--icons--sp71e50.bmp",
    "engine--icons--sp71e60.bmp", "engine--icons--sp71e70.bmp",
    "engine--icons--sp77e60.bmp", "engine--icons--sp77e70.bmp",
    "engine--icons--edge_top.bmp",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sheets = json.loads((RUN / "plan.json").read_text())["sheets"]
    first = json.loads((RUN / "report.json").read_text())["items"]
    by_id = {cell["id"]: (sheet, cell) for sheet in sheets for cell in sheet["cells"]}
    report = {"schema": 1, "tool": "built-in image_gen; complete-component overflow extraction",
              "items": {}}
    raw_cache = {}
    for target_id in TARGETS:
        sheet, cell = by_id[target_id]
        if sheet["id"] not in raw_cache:
            raw_path = RUN / "returns" / f"{sheet['id']}.png"
            with Image.open(raw_path) as file:
                raw = file.convert("RGBA")
            indexed, found = components(raw)
            raw_cache[sheet["id"]] = (raw_path, raw, indexed, found)
        raw_path, raw, indexed, found = raw_cache[sheet["id"]]
        x, y, width, height = cell["rect"]
        sx = raw.width / sheet["native_sheet_size"][0]
        sy = raw.height / sheet["native_sheet_size"][1]
        nominal = (round(x * sx), round(y * sy), round((x + width) * sx),
                   round((y + height) * sy))
        matches = [obj for obj in found if nominal[0] <= obj["center"][0] < nominal[2]
                   and nominal[1] <= obj["center"][1] < nominal[3]
                   and obj["area"] >= 1000]
        if len(matches) != 1:
            raise ValueError(f"Expected one large component in {target_id}, found {len(matches)}")
        obj = matches[0]
        kept = int(np.sum(indexed[nominal[1]:nominal[3], nominal[0]:nominal[2]] == obj["label"]))
        coverage = kept / obj["area"]
        if not 0.90 <= coverage < 0.97:
            raise ValueError(f"Unexpected nominal component coverage: {target_id}: {coverage:.3f}")
        original_path = HERE / "originals" / f"{target_id}.png"
        if sha256(original_path) != cell["original_sha256"]:
            raise ValueError(f"Changed original: {target_id}")
        with Image.open(original_path) as file:
            original = file.convert("RGBA")
        yy, xx = np.where(np.asarray(original.getchannel("A")) >= 128)
        native_box = (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)
        box = obj["box"]
        nw, nh = native_box[2] - native_box[0], native_box[3] - native_box[1]
        rw, rh = box[2] - box[0], box[3] - box[1]
        sampling = [round(rw / nw, 3), round(rh / nh, 3)]
        aspect_ratio = (rw / rh) / (nw / nh)
        if min(sampling) < 2 or not 0.80 <= aspect_ratio <= 1.20:
            raise ValueError(f"Changed component proportions: {target_id}: {aspect_ratio:.3f}")
        component = raw.crop(box)
        local = indexed[box[1]:box[3], box[0]:box[2]] == obj["label"]
        alpha = np.asarray(component.getchannel("A")).copy()
        alpha[~local] = 0
        component.putalpha(Image.fromarray(alpha, "L"))
        fitted = x2_resize(component, (nw * 2, nh * 2))
        candidate = Image.new("RGBA", (original.width * 2, original.height * 2))
        candidate.alpha_composite(fitted, (native_box[0] * 2, native_box[1] * 2))
        destination = RUN / "edge_component_candidates" / target_id / "candidate-2x.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        candidate.save(destination, optimize=True)
        report["items"][target_id] = {
            "status": "candidate_technical", "source_sha256": first[target_id]["source_sha256"],
            "artifact": str(destination.relative_to(HERE)), "artifact_sha256": sha256(destination),
            "method": "whole imagegen component fit to native occupied bounds; generated alpha retained",
            "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
            "returned_region": list(box), "nominal_region": list(nominal),
            "component_coverage_in_nominal_crop": round(coverage, 4),
            "native_opaque_box": list(native_box), "sampling": sampling,
            "aspect_ratio_returned_over_native": round(aspect_ratio, 4),
            "metrics_after_fit": metrics(x2_resize(original, candidate.size), candidate),
        }
    (RUN / "edge_component_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {len(report['items'])} whole-component imagegen crop repairs")


if __name__ == "__main__":
    main()
