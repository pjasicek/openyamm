#!/usr/bin/env python3
"""Extract full-sequence imagegen returns to native-aligned exact 2x frames."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
PLAYER = REVIEW / "pc_effect_sequences"
ALPHA_FLOOR = 48
ENDPOINT_FADE = {"sp25e": {1: 0.5, 8: 0.5}, "sp71e": {1: 0.5, 8: 0.5}}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_region(raw: Image.Image, index: int, columns: int, rows: int) -> tuple[Image.Image, list[int]]:
    x0 = round((index % columns) * raw.width / columns)
    x1 = round((index % columns + 1) * raw.width / columns)
    y0 = round((index // columns) * raw.height / rows)
    y1 = round((index // columns + 1) * raw.height / rows)
    return raw.crop((x0, y0, x1, y1)), [x0, y0, x1, y1]


def clean_alpha(cell: Image.Image, minimum_component_area: int = 0) -> tuple[Image.Image, list[int], list[int]]:
    pixels = np.asarray(cell.convert("RGBA")).copy()
    alpha = pixels[:, :, 3].astype(np.int16)
    red = pixels[:, :, 0].astype(np.int16)
    green = pixels[:, :, 1].astype(np.int16)
    blue = pixels[:, :, 2].astype(np.int16)
    key_spill = (red >= 215) & (blue >= 200) & (green <= 75) \
        & (np.minimum(red, blue) - green >= 140)
    alpha[key_spill] = 0
    if minimum_component_area:
        labels, _ = ndimage.label(alpha >= 64)
        areas = np.bincount(labels.ravel())
        alpha[(labels > 0) & (areas[labels] < minimum_component_area)] = 0
    core = Image.fromarray(np.uint8(alpha >= 64) * 255)
    box = core.getbbox()
    if box is None:
        raise ValueError("Imagegen cell has no visible effect artwork")
    insets = [box[0], box[1], cell.width - box[2], cell.height - box[3]]
    if min(insets) < 8:
        raise ValueError(f"Generated art approaches a cell boundary: {insets}")
    alpha = np.clip((alpha - ALPHA_FLOOR) * (255.0 / (255 - ALPHA_FLOOR)), 0, 255).astype(np.uint8)
    pixels[:, :, 3] = alpha
    expanded = [max(0, box[0] - 2), max(0, box[1] - 2),
                min(cell.width, box[2] + 2), min(cell.height, box[3] + 2)]
    return Image.fromarray(pixels, "RGBA").crop(tuple(expanded)), expanded, insets


def make_candidate(extracted: Image.Image, native_box: list[int], native_size: list[int],
                   fade: float, frame_id: str) -> tuple[Image.Image, list[int], list[float]]:
    target_box = [edge * 2 for edge in native_box]
    target_size = (target_box[2] - target_box[0], target_box[3] - target_box[1])
    sampling = [round(extracted.width / target_size[0], 3),
                round(extracted.height / target_size[1], 3)]
    if min(sampling) < 2.0:
        raise ValueError(f"Raw master undersamples {frame_id}: {sampling}")
    fitted = extracted.resize(target_size, Image.Resampling.LANCZOS)
    if fade < 1.0:
        fitted.putalpha(fitted.getchannel("A").point(lambda alpha: round(alpha * fade)))
    canvas = Image.new("RGBA", (native_size[0] * 2, native_size[1] * 2))
    canvas.paste(fitted, tuple(target_box[:2]))
    return canvas, target_box, sampling


def main() -> None:
    jobs = json.loads((HERE / "jobs.json").read_text())["jobs"]
    submission = json.loads((HERE / "submissions.json").read_text())
    submitted = {row["name"]: row for row in submission["submissions"]}
    candidates_dir = HERE / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    rows = {}
    preview = {}
    source_records = {}
    for family, job in jobs.items():
        frames = job["frames"]
        family_preview = []
        for output in job["outputs"]:
            name = output["name"]
            submission_row = submitted[name]
            for reference, expected in zip(submission_row["references"], submission_row["reference_hashes"]):
                if digest(REVIEW / reference) != expected:
                    raise ValueError(f"Changed imagegen reference: {name}: {reference}")
            source = HERE / "returns" / f"{name}.png"
            if not source.is_file():
                raise ValueError(f"Missing whole-sequence imagegen return: {source}")
            with Image.open(source) as image:
                if image.mode != "RGBA":
                    raise ValueError(f"Raw sheet lacks delivered alpha: {source}")
                raw = image.copy()
            count = len(output["frame_numbers"])
            columns = output["columns"]
            rows_in_sheet = (count + columns - 1) // columns
            source_records[name] = {"path": source.relative_to(REVIEW).as_posix(),
                                    "sha256": digest(source), "size": list(raw.size),
                                    "frame_numbers": output["frame_numbers"]}
            for local_index, number in enumerate(output["frame_numbers"]):
                frame = frames[number - 1]
                original = PLAYER / frame["original"]
                if digest(original) != frame["original_sha256"]:
                    raise ValueError(f"Changed native frame: {frame['id']}")
                cell, cell_region = frame_region(raw, local_index, columns, rows_in_sheet)
                minimum_component_area = 8 if family == "sp109" else 0
                extracted, extracted_region, insets = clean_alpha(cell, minimum_component_area)
                fade = ENDPOINT_FADE.get(family, {}).get(number, 1.0)
                candidate, placed, sampling = make_candidate(extracted, frame["native_box"],
                                                               frame["native_size"], fade, frame["id"])
                artifact = candidates_dir / f"{frame['id']}.png"
                candidate.save(artifact, optimize=True)
                if candidate.getchannel("A").getbbox() is None:
                    raise ValueError(f"Blank fitted frame: {frame['id']}")
                row = {"status": "candidate_technical", "sequence": family, "frame_index": number,
                       "source_sha256": frame["source_sha256"],
                       "input_sha256": frame["previous_candidate_sha256"],
                       "artifact": artifact.relative_to(REVIEW).as_posix(),
                       "artifact_sha256": digest(artifact), "origin": "Imagegen restoration",
                       "method": "complete sequence generated together; raw cell fitted to its native phase bounds",
                       "raw": source.relative_to(REVIEW).as_posix(), "raw_sha256": digest(source),
                       "raw_cell": cell_region, "returned_region": [cell_region[0] + extracted_region[0],
                                                               cell_region[1] + extracted_region[1],
                                                               cell_region[0] + extracted_region[2],
                                                               cell_region[1] + extracted_region[3]],
                       "raw_core_insets": insets, "native_opaque_box": frame["native_box"],
                       "native_envelope": job["native_envelope"],
                       "sequence_oval_center_2x": [value * 2 for value in job["native_envelope_center"]],
                       "placed_box_2x": placed, "sampling": sampling,
                       "alpha_floor": ALPHA_FLOOR, "alpha_scale": fade,
                       "minimum_component_area": minimum_component_area}
                rows[frame["id"]] = row
                family_preview.append({"name": frame["name"], "original": frame["original"],
                                       "previous": frame["previous_candidate"],
                                       "new": row["artifact"], "number": number})
        family_preview.sort(key=lambda row: row["number"])
        if [row["number"] for row in family_preview] != list(range(1, len(frames) + 1)):
            raise ValueError(f"Incomplete sequence: {family}")
        preview[family] = family_preview
    if len(rows) != 142 or len(preview) != 18:
        raise ValueError("Incomplete remaining effect sequence extraction")
    (HERE / "report.json").write_text(json.dumps({"schema": 1, "kind": "remaining_pc_effect_sequence_candidates",
                                                  "sources": source_records, "items": rows}, indent=2) + "\n")
    (HERE / "preview.js").write_text("window.REMAINING_SEQUENCE_PREVIEW = " +
                                       json.dumps(preview, separators=(",", ":")) + ";\n")
    print(json.dumps({"sequences": len(preview), "frames": len(rows),
                      "minimum_sampling": min(min(row["sampling"]) for row in rows.values()),
                      "minimum_core_inset": min(min(row["raw_core_insets"]) for row in rows.values())}, indent=2))


if __name__ == "__main__":
    main()
