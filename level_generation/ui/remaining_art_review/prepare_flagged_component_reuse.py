#!/usr/bin/env python3
"""Select complete imagegen inventory objects where a later retry was flagged as clipped."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    review = json.loads((HERE / "user_review_2026-09-24.json").read_text())["decisions"]
    catalog = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].strip().removesuffix(";"))
    by_id = {item["id"]: item for item in catalog["items"]}
    components = json.loads((HERE / "imagegen_regen/component_report.json").read_text())["items"]
    existing_path = HERE / "review_repairs/component_reuse_report.json"
    existing = json.loads(existing_path.read_text())["items"] if existing_path.is_file() else {}
    report = {"schema": 1, "method": "reuse of whole-object first-pass imagegen extraction after user crop flag",
              "items": {}}
    for target_id, decision in review.items():
        if decision["decision"] != "flag" or "crop / placement" not in decision["reasons"]:
            continue
        extracted = components.get(target_id)
        if not extracted or extracted["status"] != "candidate_technical":
            continue
        item = by_id[target_id]
        prior = item["candidates"][0]
        previous = existing.get(target_id)
        input_hash = previous["input_sha256"] if previous else prior["sha256"]
        if decision["candidate_sha256"] != input_hash:
            raise ValueError(f"Flagged candidate changed before repair: {target_id}")
        path = HERE / extracted["artifact"]
        if sha256(path) != extracted["artifact_sha256"]:
            raise ValueError(f"Changed whole-object candidate: {target_id}")
        with Image.open(path) as image:
            if list(image.size) != item["x2_size"]:
                raise ValueError(f"Wrong repaired canvas: {target_id}")
        report["items"][target_id] = {
            "status": "candidate_technical", "source_sha256": item["source_sha256"],
            "input_sha256": input_hash, "artifact": extracted["artifact"],
            "artifact_sha256": extracted["artifact_sha256"],
            "origin": previous["origin"] if previous else prior["origin"],
            "method": "complete connected imagegen object fitted to native occupied bounds; generated alpha retained",
            "raw": extracted["raw"], "raw_sha256": extracted["raw_sha256"],
            "component_coverage_in_old_nominal_crop": extracted["component_coverage_in_nominal_crop"],
        }
    if len(report["items"]) != 32:
        raise ValueError(f"Expected 32 cropped inventory retries, found {len(report['items'])}")
    destination = HERE / "review_repairs/component_reuse_report.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Selected {len(report['items'])} complete imagegen inventory objects for re-review")


if __name__ == "__main__":
    main()
