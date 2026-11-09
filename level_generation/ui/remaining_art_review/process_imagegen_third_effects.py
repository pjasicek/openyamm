#!/usr/bin/env python3
"""Register the large-reference imagegen spell-effect animation retries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from process_imagegen_regen import HERE, RUN, metrics, x2_resize


SHEETS = ("third-effects-swirl", "third-effects-arc", "third-effects-other")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    report = {"schema": 1, "tool": "built-in image_gen; per-cell foreground registration", "items": {}}
    for name in SHEETS:
        plan = json.loads((RUN / f"{name}.json").read_text())
        reference = HERE / plan["reference"]
        raw_path = RUN / "returns" / f"{name}.png"
        if sha256(reference) != plan["reference_sha256"]:
            raise ValueError(f"Changed reference: {name}")
        with Image.open(raw_path) as file:
            raw = file.convert("RGBA")
        sx, sy = raw.width / plan["reference_size"][0], raw.height / plan["reference_size"][1]
        for cell in plan["cells"]:
            target_id = cell["id"]
            x, y, width, height = cell["rect"]
            search = (max(0, round(x * sx) - 10), max(0, round(y * sy) - 10),
                      min(raw.width, round((x + width) * sx) + 10),
                      min(raw.height, round((y + height) * sy) + 10))
            slot = raw.crop(search)
            alpha = np.asarray(slot.getchannel("A")) >= 64
            yy, xx = np.where(alpha)
            if len(xx) < 10:
                raise ValueError(f"Imagegen returned no effect: {target_id}")
            region = (search[0] + int(xx.min()), search[1] + int(yy.min()),
                      search[0] + int(xx.max()) + 1, search[1] + int(yy.max()) + 1)
            original_path = HERE / "originals" / f"{target_id}.png"
            if sha256(original_path) != cell["original_sha256"]:
                raise ValueError(f"Changed original: {target_id}")
            with Image.open(original_path) as file:
                original = file.convert("RGBA")
            native = np.asarray(original.getchannel("A")) >= 128
            yy, xx = np.where(native)
            if not len(xx):
                raise ValueError(f"No source effect foreground: {target_id}")
            native_box = (int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1)
            region_width, region_height = region[2] - region[0], region[3] - region[1]
            native_width, native_height = native_box[2] - native_box[0], native_box[3] - native_box[1]
            if region_width < native_width * 2 or region_height < native_height * 2:
                raise ValueError(f"Below native 2x detail: {target_id}")
            fitted = x2_resize(raw.crop(region), (native_width * 2, native_height * 2))
            candidate = Image.new("RGBA", (original.width * 2, original.height * 2))
            candidate.alpha_composite(fitted, (native_box[0] * 2, native_box[1] * 2))
            geometry = metrics(x2_resize(original, candidate.size), candidate)
            destination = RUN / "third_candidates" / target_id / "candidate-2x.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            candidate.save(destination, optimize=True)
            report["items"][target_id] = {
                "status": "candidate_technical", "source_sha256": cell["source_sha256"],
                "artifact": str(destination.relative_to(HERE)), "artifact_sha256": sha256(destination),
                "method": "generated foreground fit to native occupied bounds; generated alpha retained",
                "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                "returned_region": list(region), "native_opaque_box": list(native_box),
                "sampling": [round(region_width / native_width, 3), round(region_height / native_height, 3)],
                "metrics_after_fit": geometry,
            }
    (RUN / "third_effects_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Prepared {len(report['items'])} registered effect candidates")


if __name__ == "__main__":
    main()
