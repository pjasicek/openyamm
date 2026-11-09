#!/usr/bin/env python3
"""Recover complete separated inventory objects from dense imagegen sheets.

The nominal cell rectangles can clip an object after imagegen expands or shifts
it. For sheets with exactly one disconnected object per cell, assign whole
components in reading order, measure nominal crop loss, and fit the generated
object to its native occupied bounds without copying the native alpha mask.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label

from process_imagegen_regen import HERE, RUN, metrics, x2_resize


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(raw: Image.Image) -> tuple[np.ndarray, list[dict]]:
    indexed, count = label(np.asarray(raw.getchannel("A")) >= 16)
    found = []
    for index in range(1, count + 1):
        yy, xx = np.where(indexed == index)
        if len(xx) < 100:
            continue
        found.append({"label": index, "area": len(xx),
                      "box": (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1),
                      "center": (float(xx.mean()), float(yy.mean()))})
    return indexed, found


def main() -> None:
    plan = json.loads((RUN / "plan.json").read_text())
    first = json.loads((RUN / "report.json").read_text())["items"]
    report = {"schema": 1, "tool": "built-in image_gen; complete-component inventory extraction",
              "sheets": {}, "items": {}}
    for sheet in plan["sheets"]:
        if not sheet["id"].startswith("small_alpha-inventory_items"):
            continue
        raw_path = RUN / "returns" / f"{sheet['id']}.png"
        with Image.open(raw_path) as file:
            raw = file.convert("RGBA")
        indexed, objects = components(raw)
        missing_potion = sheet["id"] == "small_alpha-inventory_items-003" and len(objects) == 35
        if len(objects) != len(sheet["cells"]) and not missing_potion:
            report["sheets"][sheet["id"]] = {
                "status": "not_one_component_per_cell", "cells": len(sheet["cells"]),
                "components": len(objects),
            }
            continue
        rows = [sorted((cell for cell in sheet["cells"] if cell["rect"][1] == y),
                       key=lambda cell: cell["rect"][0])
                for y in sorted({cell["rect"][1] for cell in sheet["cells"]})]
        objects.sort(key=lambda item: item["center"][1])
        assigned = []
        position = 0
        for row_index, row in enumerate(rows):
            count = 9 if missing_potion and row_index == 3 else len(row)
            row_objects = sorted(objects[position:position + count], key=lambda item: item["center"][0])
            if missing_potion and row_index == 3:
                # Imagegen omitted one of these ten near-identical potion states.
                # A dedicated enlarged reference supplies all ten separately.
                position += count
                continue
            assigned.extend(zip(row, row_objects))
            position += count
        if position != len(objects):
            raise ValueError(f"Unassigned returned components: {sheet['id']}")
        sx = raw.width / sheet["native_sheet_size"][0]
        sy = raw.height / sheet["native_sheet_size"][1]
        changed = 0
        for cell, obj in assigned:
            target_id = cell["id"]
            x, y, width, height = cell["rect"]
            expected = (round(x * sx), round(y * sy), round((x + width) * sx),
                        round((y + height) * sy))
            nominal = indexed[expected[1]:expected[3], expected[0]:expected[2]]
            kept = int(np.sum(nominal == obj["label"]))
            coverage = kept / obj["area"]
            visible_in_crop = int(np.sum(nominal != 0))
            foreign = (visible_in_crop - kept) / max(1, visible_in_crop)
            record = {"status": "nominal_crop_complete", "source_sha256": cell["source_sha256"],
                      "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                      "returned_region": list(obj["box"]), "nominal_region": list(expected),
                      "component_coverage_in_nominal_crop": round(coverage, 4),
                      "foreign_component_fraction_in_nominal_crop": round(foreign, 4)}
            if coverage >= 0.97 and foreign <= 0.02:
                report["items"][target_id] = record
                continue
            original_path = HERE / "originals" / f"{target_id}.png"
            if sha256(original_path) != cell["original_sha256"]:
                raise ValueError(f"Changed original: {target_id}")
            with Image.open(original_path) as file:
                original = file.convert("RGBA")
            native = np.asarray(original.getchannel("A")) >= 128
            yy, xx = np.where(native)
            if not len(xx):
                raise ValueError(f"Missing native foreground: {target_id}")
            native_box = (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)
            box = obj["box"]
            nw, nh = native_box[2] - native_box[0], native_box[3] - native_box[1]
            rw, rh = box[2] - box[0], box[3] - box[1]
            aspect_ratio = (rw / rh) / (nw / nh)
            sampling = [round(rw / nw, 3), round(rh / nh, 3)]
            record.update({"native_opaque_box": list(native_box), "sampling": sampling,
                           "aspect_ratio_returned_over_native": round(aspect_ratio, 4)})
            if min(sampling) < 2 or not 0.65 <= aspect_ratio <= 1.50:
                record["status"] = "hold_component_geometry"
                report["items"][target_id] = record
                continue
            component = raw.crop(box)
            local = indexed[box[1]:box[3], box[0]:box[2]] == obj["label"]
            alpha = np.asarray(component.getchannel("A")).copy()
            alpha[~local] = 0
            component.putalpha(Image.fromarray(alpha, "L"))
            fitted = x2_resize(component, (nw * 2, nh * 2))
            candidate = Image.new("RGBA", (original.width * 2, original.height * 2))
            candidate.alpha_composite(fitted, (native_box[0] * 2, native_box[1] * 2))
            destination = RUN / "component_candidates" / target_id / "candidate-2x.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            candidate.save(destination, optimize=True)
            record.update({"status": "candidate_technical", "artifact": str(destination.relative_to(HERE)),
                           "artifact_sha256": sha256(destination),
                           "method": "whole returned component fit to native occupied bounds; generated alpha retained",
                           "metrics_after_fit": metrics(x2_resize(original, candidate.size), candidate)})
            report["items"][target_id] = record
            changed += 1
        report["sheets"][sheet["id"]] = {"status": "processed", "cells": len(sheet["cells"]),
                                          "assigned_cells": len(assigned), "corrected_crops": changed,
                                          "dedicated_potion_retry": missing_potion}
    (RUN / "component_report.json").write_text(json.dumps(report, indent=2) + "\n")
    totals = {status: sum(item["status"] == status for item in report["items"].values())
              for status in sorted({item["status"] for item in report["items"].values()})}
    print(json.dumps({"sheets": report["sheets"], "items": totals}, indent=2))


if __name__ == "__main__":
    main()
