#!/usr/bin/env python3
"""Prepare source-only, padded imagegen sheets for user-flagged UI art."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
RUN = HERE / "review_repairs"
GROUPS = {
    "portraits": ("7item266", "7item267"),
    "inventory-a": ("item198", "item302", "item309", "item159"),
    "inventory-b": ("item160", "item165", "7item127", "item144"),
    "inventory-c": ("7item206", "7item083", "7item065", "6mace7"),
    "status-gems": ("statbl", "statg", "statr", "staty"),
    "review-notes": ("tp_regna", "7item134", "amulet1"),
    "spill-regens": ("item245", "6ring12"),
}
CELL = (300, 380)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].strip().removesuffix(";"))
    by_name = {item["name"]: item for item in catalog["items"]}
    review = json.loads((HERE / "user_review_2026-09-24.json").read_text())["decisions"]
    prior_path = RUN / "inventory_jobs.json"
    prior = {cell["id"]: cell for job in json.loads(prior_path.read_text())["jobs"].values()
             for cell in job["cells"]} if prior_path.is_file() else {}
    jobs = {"schema": 1, "jobs": {}}
    for name, members in GROUPS.items():
        sheet = Image.new("RGBA", (CELL[0] * len(members), CELL[1]), (255, 0, 255, 255))
        cells = []
        for index, member in enumerate(members):
            item = by_name[member]
            target_id = item["id"]
            decision = review[target_id]
            previous = prior.get(target_id)
            if previous and previous["source_sha256"] != item["source_sha256"]:
                raise ValueError(f"Changed native source: {target_id}")
            if decision["decision"] == "flag" and not previous:
                assert decision["candidate_sha256"] == item["candidates"][0]["sha256"]
            source = HERE / item["original"]
            with Image.open(source) as file:
                original = file.convert("RGBA")
            scale = min(4 if name != "status-gems" else 8,
                        (CELL[0] - 64) / original.width, (CELL[1] - 64) / original.height)
            size = (round(original.width * scale), round(original.height * scale))
            expanded = original.resize(size, Image.Resampling.NEAREST)
            px = index * CELL[0] + (CELL[0] - size[0]) // 2
            py = (CELL[1] - size[1]) // 2
            sheet.alpha_composite(expanded, (px, py))
            cells.append({
                "id": target_id, "slot": [index * CELL[0], 0, *CELL],
                "source_sha256": item["source_sha256"],
                "input_sha256": previous["input_sha256"] if previous else item["candidates"][0]["sha256"],
                "input_origin": previous["input_origin"] if previous else item["candidates"][0]["origin"],
                "original_sha256": sha256(source),
            })
        destination = RUN / "references" / f"{name}.png"
        destination.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(destination, optimize=True)
        jobs["jobs"][name] = {
            "reference": str(destination.relative_to(HERE)), "reference_sha256": sha256(destination),
            "reference_size": list(sheet.size), "cells": cells,
        }
    (RUN / "inventory_jobs.json").write_text(json.dumps(jobs, indent=2) + "\n")
    print(f"Prepared {sum(len(job['cells']) for job in jobs['jobs'].values())} sources on {len(GROUPS)} sheets")


if __name__ == "__main__":
    main()
