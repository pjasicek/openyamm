#!/usr/bin/env python3
"""Prepare complete native PC effect sequences, preserving the four approved sheets."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
PLAYER = REVIEW / "pc_effect_sequences"
APPROVED = {"sp05e", "spell14e", "spell36e", "spell68e"}
CELL = (300, 380)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_assignment(path: Path) -> dict:
    return json.loads(path.read_text().split("=", 1)[1].strip().removesuffix(";"))


def make_sheet(frames: list[dict], columns: int, path: Path) -> str:
    rows = (len(frames) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * CELL[0], rows * CELL[1]), (255, 0, 255))
    for index, frame in enumerate(frames):
        with Image.open(PLAYER / frame["original"]) as image:
            native = image.convert("RGBA")
        enlarged = native.resize((native.width * 4, native.height * 4), Image.Resampling.NEAREST)
        x = (index % columns) * CELL[0] + (CELL[0] - enlarged.width) // 2
        y = (index // columns) * CELL[1] + (CELL[1] - enlarged.height) // 2
        sheet.paste(enlarged, (x, y), enlarged)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)
    return digest(path)


def main() -> None:
    player = read_assignment(PLAYER / "sequences.js")
    catalog = read_assignment(REVIEW / "catalog.js")
    by_id = {item["id"]: item for item in catalog["items"]}
    existing_path = HERE / "jobs.json"
    existing = json.loads(existing_path.read_text())["jobs"] if existing_path.is_file() else {}
    jobs = {}
    for group in player["sequences"]:
        family = group["family"]
        if family in APPROVED:
            continue
        original_frames = group["frames"]
        native_boxes = []
        frames = []
        for index, frame in enumerate(original_frames, 1):
            target_id = frame["id"]
            with Image.open(PLAYER / frame["original"]) as native_image:
                native = native_image.convert("RGBA")
            if list(native.size) != group["native_size"]:
                raise ValueError(f"Native canvas changed: {target_id}")
            box = native.getchannel("A").getbbox()
            if not box:
                raise ValueError(f"Empty native effect frame: {target_id}")
            native_boxes.append(box)
            item = by_id.get(target_id)
            if item:
                source_sha = item["source_sha256"]
                prior_candidate = item["candidates"][0]
            elif target_id == "engine--icons--sp21a10.bmp":
                source_sha = digest((PLAYER / frame["original"]).resolve())
                prior_candidate = {"path": os.path.relpath((PLAYER / frame["candidate"]).resolve(), REVIEW),
                                   "sha256": digest((PLAYER / frame["candidate"]).resolve())}
            else:
                raise ValueError(f"Uncatalogued frame outside HUD first frame: {target_id}")
            old = next((entry for entry in existing.get(family, {}).get("frames", [])
                        if entry["id"] == target_id), None)
            if old and old["source_sha256"] != source_sha:
                raise ValueError(f"Native source changed after preparation: {target_id}")
            frames.append({
                "id": target_id, "name": frame["name"], "number": index, "ticks": frame["ticks"],
                "original": frame["original"], "original_sha256": digest(PLAYER / frame["original"]),
                "source_sha256": source_sha, "native_size": list(native.size), "native_box": list(box),
                "previous_candidate": old["previous_candidate"] if old else prior_candidate["path"],
                "previous_candidate_sha256": old["previous_candidate_sha256"] if old else prior_candidate["sha256"],
            })
        envelope = [min(box[0] for box in native_boxes), min(box[1] for box in native_boxes),
                    max(box[2] for box in native_boxes), max(box[3] for box in native_boxes)]
        native_center = [(envelope[0] + envelope[2]) / 2, (envelope[1] + envelope[3]) / 2]
        canvas_center = [group["native_size"][0] / 2, group["native_size"][1] / 2]
        columns = 4 if len(frames) in (8, 12) else 3 if len(frames) == 6 else 2
        reference = HERE / "references" / f"{family}.png"
        reference_hash = make_sheet(frames, columns, reference)
        outputs = [{"name": family, "frame_numbers": list(range(1, len(frames) + 1)),
                    "reference": reference.relative_to(REVIEW).as_posix(),
                    "reference_sha256": reference_hash, "columns": columns}]
        if len(frames) == 12:
            outputs = []
            for start, length in ((0, 6), (6, 3), (9, 3)):
                part = frames[start:start + length]
                part_name = f"{family}-{start + 1:02d}-{start + len(part):02d}"
                part_reference = HERE / "references" / f"{part_name}.png"
                part_hash = make_sheet(part, 3, part_reference)
                outputs.append({"name": part_name, "frame_numbers": list(range(start + 1, start + len(part) + 1)),
                                "reference": part_reference.relative_to(REVIEW).as_posix(),
                                "reference_sha256": part_hash, "columns": 3,
                                "full_reference": reference.relative_to(REVIEW).as_posix(),
                                "full_reference_sha256": reference_hash})
        jobs[family] = {"family": family, "animation": group["animation"], "native_size": group["native_size"],
                        "native_envelope": envelope, "native_envelope_center": native_center,
                        "canvas_center": canvas_center, "frames": frames,
                        "full_reference": reference.relative_to(REVIEW).as_posix(),
                        "full_reference_sha256": reference_hash, "outputs": outputs}
    if len(jobs) != 18 or sum(len(job["frames"]) for job in jobs.values()) != 142:
        raise ValueError("Remaining sequence scope changed")
    result = {"schema": 1, "kind": "remaining_pc_effect_sequences", "kept_approved": sorted(APPROVED),
              "jobs": jobs}
    existing_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"sequences": len(jobs), "frames": sum(len(job["frames"]) for job in jobs.values()),
                      "imagegen_outputs": sum(len(job["outputs"]) for job in jobs.values()),
                      "centers": {name: job["native_envelope_center"] for name, job in jobs.items()}}, indent=2))


if __name__ == "__main__":
    main()
