#!/usr/bin/env python3
"""Prepare complete eight-frame native references for coherent spell effect restoration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
GROUPS = {
    "sp05e": [f"sp05e{index}0" for index in range(1, 9)],
    "spell14e": [f"spell14e{index}" for index in range(1, 9)],
    "spell36e": [f"spell36e{index}" for index in range(1, 9)],
    "spell68e": [f"spell68e{index}" for index in range(1, 9)],
}
CELL = (300, 380)
SHEET = (CELL[0] * 4, CELL[1] * 2)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    catalog = json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].rstrip(";\n"))
    by_name = {item["name"]: item for item in catalog["items"]}
    existing_path = HERE / "jobs.json"
    existing = json.loads(existing_path.read_text())["jobs"] if existing_path.is_file() else {}
    prior_frames = {frame["id"]: frame for job in existing.values() for frame in job["frames"]}
    references = HERE / "references"
    references.mkdir(parents=True, exist_ok=True)
    jobs = {}
    for group, names in GROUPS.items():
        sheet = Image.new("RGB", SHEET, (255, 0, 255))
        frames = []
        for index, name in enumerate(names):
            item = by_name[name]
            source = REVIEW / item["original"]
            with Image.open(source) as image:
                native = image.convert("RGBA")
            if native.size != (59, 79):
                raise ValueError(f"Unexpected frame canvas: {name}: {native.size}")
            enlarged = native.resize((236, 316), Image.Resampling.NEAREST)
            x = (index % 4) * CELL[0] + (CELL[0] - enlarged.width) // 2
            y = (index // 4) * CELL[1] + (CELL[1] - enlarged.height) // 2
            sheet.paste(enlarged, (x, y), enlarged)
            prior = prior_frames.get(item["id"], {})
            if prior and prior["source_sha256"] != item["source_sha256"]:
                raise ValueError(f"Native source changed since sequence preparation: {name}")
            frames.append({
                "id": item["id"],
                "name": name,
                "slot": [(index % 4) * CELL[0], (index // 4) * CELL[1], *CELL],
                "source_sha256": item["source_sha256"],
                "original_sha256": digest(source),
                "previous_candidate_sha256": prior.get("previous_candidate_sha256",
                                                       item["candidates"][0]["sha256"]),
                "previous_candidate": prior.get("previous_candidate", item["candidates"][0]["path"]),
            })
        reference = references / f"{group}.png"
        sheet.save(reference, optimize=True)
        jobs[group] = {
            "reference": str(reference.relative_to(REVIEW)),
            "reference_sha256": digest(reference),
            "reference_size": list(SHEET),
            "frames": frames,
        }
    (HERE / "jobs.json").write_text(json.dumps({"schema": 1, "jobs": jobs}, indent=2) + "\n")


if __name__ == "__main__":
    main()
