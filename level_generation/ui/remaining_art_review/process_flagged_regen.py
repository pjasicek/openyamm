#!/usr/bin/env python3
"""Fit padded user-flag repair sheets to the original 2x sprite placements."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import find_objects, label

from process_imagegen_regen import x2_resize


HERE = Path(__file__).resolve().parent
RUN = HERE / "review_repairs"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def foreground_box(image: Image.Image, largest_component: bool = False) -> tuple[int, int, int, int]:
    alpha = np.asarray(image.getchannel("A")) >= 64
    if largest_component:
        labels, count = label(alpha)
        parts = [(int((labels[region] == index).sum()), index, region)
                 for index, region in enumerate(find_objects(labels), 1) if region is not None]
        if not count or not parts:
            raise ValueError("No generated foreground")
        _, index, region = max(parts, key=lambda part: part[0])
        alpha = np.zeros_like(alpha)
        alpha[region] = labels[region] == index
    yy, xx = np.where(alpha)
    if len(xx) < 10:
        raise ValueError("No generated foreground")
    return int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1


def process(plan_file: str, report_file: str, candidates_dir: str) -> int:
    jobs = json.loads((RUN / plan_file).read_text())["jobs"]
    report = {"schema": 1, "tool": "built-in image_gen; padded cell registration to original occupied bounds",
              "items": {}}
    for name, job in jobs.items():
        ref = HERE / job["reference"]
        if sha256(ref) != job["reference_sha256"]:
            raise ValueError(f"Changed original reference: {name}")
        raw_path = RUN / "returns" / ("status-gems-smooth.png" if name == "status-gems" else f"{name}.png")
        with Image.open(raw_path) as file:
            raw = file.convert("RGBA")
        sx = raw.width / job["reference_size"][0]
        sy = raw.height / job["reference_size"][1]
        for cell in job["cells"]:
            target_id = cell["id"]
            x, y, width, height = cell["slot"]
            left = round(x * sx)
            top = round(y * sy)
            right = round((x + width) * sx)
            bottom = round((y + height) * sy)
            if target_id == "engine--icons--item302.bmp":
                right += 30  # The complete telescope crosses the nominal sheet divider.
            slot = raw.crop((left, top, right, bottom))
            box = foreground_box(slot, target_id in {
                "engine--icons--item302.bmp", "engine--icons--item309.bmp"})
            region = (left + box[0], top + box[1], left + box[2], top + box[3])
            original_path = HERE / "originals" / f"{target_id}.png"
            if sha256(original_path) != cell["original_sha256"]:
                raise ValueError(f"Changed native rendering: {target_id}")
            with Image.open(original_path) as file:
                original = file.convert("RGBA")
            native_box = foreground_box(original)
            native_size = (native_box[2] - native_box[0], native_box[3] - native_box[1])
            returned_size = (region[2] - region[0], region[3] - region[1])
            if returned_size[0] < native_size[0] * 2 or returned_size[1] < native_size[1] * 2:
                raise ValueError(f"Generated sampling below native 2x: {target_id}")
            fitted = x2_resize(raw.crop(region), (native_size[0] * 2, native_size[1] * 2))
            candidate = Image.new("RGBA", (original.width * 2, original.height * 2))
            candidate.alpha_composite(fitted, (native_box[0] * 2, native_box[1] * 2))
            destination = RUN / candidates_dir / target_id / "candidate-2x.png"
            destination.parent.mkdir(parents=True, exist_ok=True)
            candidate.save(destination, optimize=True)
            report["items"][target_id] = {
                "status": "candidate_technical", "source_sha256": cell["source_sha256"],
                "input_sha256": cell["input_sha256"], "artifact": str(destination.relative_to(HERE)),
                "artifact_sha256": sha256(destination), "origin": "Imagegen restoration",
                "method": "padded source-sheet imagegen; whole generated foreground fitted to native occupied bounds",
                "raw": str(raw_path.relative_to(HERE)), "raw_sha256": sha256(raw_path),
                "returned_region": list(region), "native_opaque_box": list(native_box),
                "sampling": [round(returned_size[0] / native_size[0], 3),
                             round(returned_size[1] / native_size[1], 3)],
            }
    (RUN / report_file).write_text(json.dumps(report, indent=2) + "\n")
    return len(report["items"])


def main() -> None:
    effects = process("effect_jobs.json", "effect_report.json", "effect_candidates")
    inventory = process("inventory_jobs.json", "inventory_regen_report.json", "inventory_candidates")
    print(f"Prepared {effects} effects and {inventory} inventory/UI candidates")


if __name__ == "__main__":
    main()
