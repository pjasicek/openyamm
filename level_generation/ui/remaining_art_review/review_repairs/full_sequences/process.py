#!/usr/bin/env python3
"""Extract whole-sequence imagegen returns into exact 2x review canvases."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
SELECTED = {"sp05e": "sp05e.png", "spell14e": "spell14e-v2.png",
            "spell36e": "spell36e-v2.png", "spell68e": "spell68e-v2.png"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cleaned_cell(image: Image.Image) -> tuple[Image.Image, list[int]]:
    pixels = np.asarray(image.convert("RGBA")).copy()
    alpha = pixels[:, :, 3].astype(np.int16)
    core = Image.fromarray(np.uint8(alpha >= 64) * 255)
    box = core.getbbox()
    if box is None:
        raise ValueError("Empty generated animation frame")
    if box[0] < 8 or box[1] < 8 or box[2] > image.width - 8 or box[3] > image.height - 8:
        raise ValueError(f"Generated frame touches cell gutter: {box} in {image.size}")
    # The low-alpha outer mist is not part of the source sprite, and expands
    # the crop into neighboring sheet cells. Preserve smooth 2x edge alpha.
    pixels[:, :, 3] = np.uint8(np.clip((alpha - 24) * (255 / 231), 0, 255))
    box = [max(0, box[0] - 2), max(0, box[1] - 2),
           min(image.width, box[2] + 2), min(image.height, box[3] + 2)]
    return Image.fromarray(pixels, "RGBA").crop(tuple(box)), box


def main() -> None:
    jobs = json.loads((HERE / "jobs.json").read_text())["jobs"]
    catalog = json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].rstrip(";\n"))
    by_id = {item["id"]: item for item in catalog["items"]}
    output_dir = HERE / "candidates"
    output_dir.mkdir(parents=True, exist_ok=True)
    report = {}
    preview = {}
    for group, filename in SELECTED.items():
        raw_path = HERE / "returns" / filename
        raw_sha256 = digest(raw_path)
        with Image.open(raw_path) as source:
            raw = source.convert("RGBA")
        if raw.width < 1000 or raw.height < 700:
            raise ValueError(f"Insufficient generated resolution: {raw_path}: {raw.size}")
        native_boxes = []
        for frame in jobs[group]["frames"]:
            item = by_id[frame["id"]]
            native = Image.open(REVIEW / item["original"]).convert("RGBA")
            box = native.getchannel("A").getbbox()
            if not box:
                raise ValueError(f"Empty native frame: {frame['id']}")
            native_boxes.append(box)
        # The legacy atlas stores every phase on the same 59x79 canvas. Sparse
        # phases have smaller occupied boxes; fitting those independently made
        # their oval size and anchor jump during playback. All eight use the
        # complete sequence's native oval envelope instead.
        oval_box = [min(box[0] for box in native_boxes), min(box[1] for box in native_boxes),
                    max(box[2] for box in native_boxes), max(box[3] for box in native_boxes)]
        target_box = [value * 2 for value in oval_box]
        frames = []
        for index, frame in enumerate(jobs[group]["frames"]):
            item = by_id[frame["id"]]
            native_box = native_boxes[index]
            x0 = round((index % 4) * raw.width / 4)
            x1 = round((index % 4 + 1) * raw.width / 4)
            y0 = round((index // 4) * raw.height / 2)
            y1 = round((index // 4 + 1) * raw.height / 2)
            extracted, returned_box = cleaned_cell(raw.crop((x0, y0, x1, y1)))
            width = target_box[2] - target_box[0]
            height = target_box[3] - target_box[1]
            if extracted.width < width * 1.8 or extracted.height < height * 1.8:
                raise ValueError(f"Imagegen sampling below restoration budget: {frame['id']}")
            fitted = extracted.resize((width, height), Image.Resampling.LANCZOS)
            candidate = Image.new("RGBA", tuple(item["x2_size"]))
            candidate.paste(fitted, (target_box[0], target_box[1]))
            artifact = output_dir / f"{frame['id']}.png"
            candidate.save(artifact, optimize=True)
            row = {
                "status": "candidate_technical", "source_sha256": item["source_sha256"],
                "input_sha256": frame["previous_candidate_sha256"],
                "artifact": str(artifact.relative_to(REVIEW)), "artifact_sha256": digest(artifact),
                "origin": "Imagegen restoration",
                "method": "complete eight-frame sequence regenerated together; alpha fitted to shared native oval envelope",
                "raw": str(raw_path.relative_to(REVIEW)), "raw_sha256": raw_sha256,
                "returned_region": [x0 + returned_box[0], y0 + returned_box[1],
                                    x0 + returned_box[2], y0 + returned_box[3]],
                "native_opaque_box": list(native_box),
                "sequence_oval_box_2x": target_box,
                "sequence_oval_center_2x": [(target_box[0] + target_box[2]) / 2,
                                             (target_box[1] + target_box[3]) / 2],
                "sampling": [round(extracted.width / width, 3), round(extracted.height / height, 3)],
                "sequence": group, "frame_index": index + 1,
            }
            report[frame["id"]] = row
            frames.append({"name": frame["name"], "original": item["original"],
                           "previous": frame["previous_candidate"], "new": row["artifact"]})
        preview[group] = frames
    (HERE / "report.json").write_text(json.dumps({"schema": 1, "items": report}, indent=2) + "\n")
    (HERE / "preview.js").write_text("window.SEQUENCE_PREVIEW = " +
                                     json.dumps(preview, separators=(",", ":")) + ";\n")
    print(json.dumps({"sequences": len(preview), "frames": len(report),
                      "minimum_sampling": min(min(row["sampling"]) for row in report.values())}, indent=2))


if __name__ == "__main__":
    main()
