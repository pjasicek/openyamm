#!/usr/bin/env python3
"""Fit third-pass imagegen inventory sprites from enlarged reference sheets.

The returned independent objects are registered to their native opaque bounds.
No native alpha mask is copied onto the restored artwork.
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


def components(image: Image.Image) -> list[dict]:
    alpha = np.asarray(image.getchannel("A")) >= 16
    indexed, count = label(alpha)
    result = []
    for index in range(1, count + 1):
        yy, xx = np.where(indexed == index)
        if len(xx) < 100:
            continue
        result.append({"index": index, "area": len(xx),
                       "box": (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1),
                       "center": (float(xx.mean()), float(yy.mean()))})
    return result


def main() -> None:
    first = json.loads((RUN / "report.json").read_text())["items"]
    report = {"schema": 1, "tool": "built-in image_gen; component-to-native-bounds fitting", "items": {}}
    for name, plan_file in (("third-inventory-keys", "third_inventory_plan.json"),
                            ("third-inventory-fragments", "third_fragments_plan.json")):
        plan = json.loads((RUN / plan_file).read_text())
        reference = HERE / plan["reference"]
        raw_path = RUN / "returns" / f"{name}.png"
        if sha256(reference) != plan["reference_sha256"]:
            raise ValueError(f"Changed reference: {reference}")
        with Image.open(raw_path) as file:
            raw = file.convert("RGBA")
        sx, sy = raw.width / plan["reference_size"][0], raw.height / plan["reference_size"][1]
        available = components(raw)
        if len(available) != len(plan["cells"]):
            raise ValueError(f"Expected {len(plan['cells'])} objects, found {len(available)}: {name}")
        for cell in plan["cells"]:
            target_id = cell["id"]
            x, y, width, height = cell["rect"]
            center = ((x + width / 2) * sx, (y + height / 2) * sy)
            chosen = min(available, key=lambda item: ((item["center"][0] - center[0]) / raw.width) ** 2
                         + ((item["center"][1] - center[1]) / raw.height) ** 2)
            available.remove(chosen)
            original_path = HERE / "originals" / f"{target_id}.png"
            if sha256(original_path) != cell["original_sha256"]:
                raise ValueError(f"Changed original: {target_id}")
            with Image.open(original_path) as source:
                original = source.convert("RGBA")
            opaque = np.asarray(original.getchannel("A")) >= 128
            yy, xx = np.where(opaque)
            native_box = (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)
            box = chosen["box"]
            aspect_native = (native_box[2] - native_box[0]) / (native_box[3] - native_box[1])
            aspect_returned = (box[2] - box[0]) / (box[3] - box[1])
            if abs(aspect_returned / aspect_native - 1) > 0.18:
                raise ValueError(f"Changed sprite proportions: {target_id}, {aspect_native}, {aspect_returned}")
            crop = raw.crop(box)
            fitted = x2_resize(crop, ((native_box[2] - native_box[0]) * 2,
                                      (native_box[3] - native_box[1]) * 2))
            candidate = Image.new("RGBA", (original.width * 2, original.height * 2))
            candidate.alpha_composite(fitted, (native_box[0] * 2, native_box[1] * 2))
            geometry = metrics(x2_resize(original, candidate.size), candidate)
            destination = RUN / "third_candidates" / target_id / "candidate-2x.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            candidate.save(destination, optimize=True)
            report["items"][target_id] = {
                "status": "candidate_technical", "source_sha256": first[target_id]["source_sha256"],
                "artifact": str(destination.relative_to(HERE)), "artifact_sha256": sha256(destination),
                "method": "imagegen component fitted to native opaque bounding box; generated alpha retained",
                "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                "returned_region": list(box), "native_opaque_box": list(native_box),
                "sampling": [round((box[2] - box[0]) / (native_box[2] - native_box[0]), 3),
                             round((box[3] - box[1]) / (native_box[3] - native_box[1]), 3)],
                "metrics_after_fit": geometry,
            }
    (RUN / "third_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {len(report['items'])} fitted third-pass imagegen candidates")


if __name__ == "__main__":
    main()
