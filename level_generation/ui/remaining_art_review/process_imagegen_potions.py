#!/usr/bin/env python3
"""Fit the ten separately generated potion states to their native icon canvases."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from process_imagegen_components import components
from process_imagegen_regen import HERE, RUN, metrics, x2_resize


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    first = json.loads((RUN / "report.json").read_text())["items"]
    report = {"schema": 1, "tool": "built-in image_gen; isolated potion component extraction",
              "sheets": {}, "items": {}}
    for name in ("third-potions-189-193", "third-potions-194-198"):
        plan = json.loads((RUN / f"{name}.json").read_text())
        reference = HERE / plan["reference"]
        raw_path = RUN / "returns" / f"{name}.png"
        if sha256(reference) != plan["reference_sha256"]:
            raise ValueError(f"Changed reference: {reference}")
        with Image.open(raw_path) as file:
            raw = file.convert("RGBA")
        indexed, found = components(raw)
        if len(found) != len(plan["cells"]):
            raise ValueError(f"Expected five separate bottles in {name}, found {len(found)}")
        found.sort(key=lambda entry: entry["center"][0])
        report["sheets"][name] = {"reference": plan["reference"],
                                   "reference_sha256": plan["reference_sha256"],
                                   "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                                   "raw_size": list(raw.size), "components": len(found)}
        for cell, obj in zip(plan["cells"], found):
            target_id = cell["id"]
            original_path = HERE / "originals" / f"{target_id}.png"
            if sha256(original_path) != cell["original_sha256"]:
                raise ValueError(f"Changed original: {target_id}")
            with Image.open(original_path) as file:
                original = file.convert("RGBA")
            native_mask = np.asarray(original.getchannel("A")) >= 128
            yy, xx = np.where(native_mask)
            if len(xx) == 0:
                raise ValueError(f"Empty native potion: {target_id}")
            native_box = (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)
            box = obj["box"]
            nw, nh = native_box[2] - native_box[0], native_box[3] - native_box[1]
            rw, rh = box[2] - box[0], box[3] - box[1]
            aspect_ratio = (rw / rh) / (nw / nh)
            sampling = [round(rw / nw, 3), round(rh / nh, 3)]
            if min(sampling) < 2 or not 0.80 <= aspect_ratio <= 1.20:
                raise ValueError(f"Changed potion proportions: {target_id}, {aspect_ratio:.3f}")
            component = raw.crop(box)
            local = indexed[box[1]:box[3], box[0]:box[2]] == obj["label"]
            alpha = np.asarray(component.getchannel("A")).copy()
            alpha[~local] = 0
            component.putalpha(Image.fromarray(alpha, "L"))
            fitted = x2_resize(component, (nw * 2, nh * 2))
            candidate = Image.new("RGBA", (original.width * 2, original.height * 2))
            candidate.alpha_composite(fitted, (native_box[0] * 2, native_box[1] * 2))
            destination = RUN / "potion_candidates" / target_id / "candidate-2x.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            candidate.save(destination, optimize=True)
            report["items"][target_id] = {
                "status": "candidate_technical", "source_sha256": first[target_id]["source_sha256"],
                "artifact": str(destination.relative_to(HERE)), "artifact_sha256": sha256(destination),
                "method": "isolated imagegen bottle fitted to native occupied bounds; generated alpha retained",
                "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                "returned_region": list(box), "native_opaque_box": list(native_box),
                "sampling": sampling, "aspect_ratio_returned_over_native": round(aspect_ratio, 4),
                "metrics_after_fit": metrics(x2_resize(original, candidate.size), candidate),
            }
    if len(report["items"]) != 10:
        raise ValueError("Did not prepare all ten potion states")
    (RUN / "potion_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {len(report['items'])} separate imagegen potion candidates")


if __name__ == "__main__":
    main()
