#!/usr/bin/env python3
"""Bind the selected imagegen returns to their references and submitted prompts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parents[1]
CURTAIN_STYLE = (
    " Image 3 shows the newly restored first six frames as a style reference only. "
    "Produce exactly the three target frames from Image 2 in its row order, matching Image 3's crimson "
    "fabric texture, fold structure, lighting, and transparent gutters. Preserve each target frame's "
    "descending lower-edge contour and coverage. Do not combine phases or repeat any phase."
)
FIERY_PROMPT = (
    "Use case: precise-object-edit. Asset type: OpenYAMM 2D PC portrait spell-effect animation. "
    "Image 1 is the authoritative original EIGHT-frame sequence in a 4-column by 2-row sheet, row-major "
    "order. Restore ALL EIGHT phases together as a single coherent, smooth, detailed painted 2D sequence "
    "of fiery orange-gold magical arcs and sparks. The left arc grows into a hollow glowing ring and then "
    "recedes; preserve the exact phase progression, empty central holes, dark orange structure, sparse "
    "first and last phases, and warm gold highlights. The flat magenta in Image 1 is only a transparency "
    "key, not part of the artwork. Deliver a genuine RGBA transparent 4x2 sprite sheet. Keep each "
    "distinct complete effect inside its equal cell, with at least 30 pixels of transparent space on "
    "every side and between rows; no crossing into neighboring cells and no cropped arc or spark. Use "
    "one consistent scale, texture, palette and lighting for all frames. No grid, labels, text, black "
    "background, checkerboard, solid filled discs, invented symbols, or extra objects."
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    submissions = json.loads((HERE / "submissions.json").read_text())["submissions"]
    source_records = json.loads((HERE / "report.json").read_text())["sources"]
    if len(submissions) != 20 or set(source_records) != {row["name"] for row in submissions}:
        raise ValueError("Selected imagegen output set changed")
    rows = []
    for submitted in submissions:
        name = submitted["name"]
        source = source_records[name]
        if digest(REVIEW / source["path"]) != source["sha256"]:
            raise ValueError(f"Changed imagegen return: {name}")
        for path, expected in zip(submitted["references"], submitted["reference_hashes"]):
            if digest(REVIEW / path) != expected:
                raise ValueError(f"Changed imagegen reference: {name}: {path}")
        prompt = FIERY_PROMPT if name == "spell03e" else submitted["prompt"]
        references = [{"path": path, "sha256": sha} for path, sha in
                      zip(submitted["references"], submitted["reference_hashes"])]
        if name in {"sp96h-07-09", "sp96h-10-12"}:
            prompt += CURTAIN_STYLE
            style = HERE / "returns/sp96h-01-06.png"
            references.append({"path": style.relative_to(REVIEW).as_posix(), "sha256": digest(style),
                               "role": "style_only"})
        rows.append({"name": name, "family": submitted["family"],
                     "frame_numbers": submitted["frame_numbers"], "prompt": prompt,
                     "references": references, "return": source})
    superseded = HERE / "returns/sp96h-07-12.png"
    result = {"schema": 1, "tool": "image_gen.imagegen", "selected_outputs": rows,
              "superseded_outputs": [{"path": superseded.relative_to(REVIEW).as_posix(),
                                      "sha256": digest(superseded),
                                      "reason": "Three of six frames undersampled their final 2x placement; "
                                                "replaced by two three-frame returns."}]}
    (HERE / "generation_log.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Recorded {len(rows)} selected imagegen returns")


if __name__ == "__main__":
    main()
