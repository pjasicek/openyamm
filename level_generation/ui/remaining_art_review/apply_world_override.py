#!/usr/bin/env python3
"""Install the approved 7item263 foreground into its existing ground-sprite binding."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
WORLD = ROOT / "assets_dev/engine/decorations_x2"
STAGE_MANIFEST = HERE / "staged_approved/manifest.json"
ACCEPTANCE = HERE / "review_acceptance.json"
ORIGINAL_PLAN = ROOT / "level_generation/sprites/restoration_jobs/runs/remaining_review_20260923/" \
    "approved-installation-plan.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    stage = json.loads(STAGE_MANIFEST.read_text())
    acceptance = json.loads(ACCEPTANCE.read_text())
    original = json.loads(ORIGINAL_PLAN.read_text())
    live_path = WORLD / "manifest.json"
    live = json.loads(live_path.read_text())
    override = stage["world_override"]
    file = override["binding_file"]
    target = WORLD / file
    staged = ROOT / override["artifact"]
    old = next(row for row in original["bindings"] if row["file"] == file)
    binding = next(row for row in live["bindings"] if row["file"] == file)
    inventory = next(row for row in acceptance["items"] if row["id"] == override["inventory_target"])
    if stage["revision"] != acceptance["revision"] or file != "7obj263_p9.png" \
            or old["sha256"] != override["previous_sha256"] \
            or inventory["candidate_sha256"] != override["inventory_candidate_sha256"] \
            or binding["name"] != override["binding_name"] or binding["palette_id"] != override["palette_id"] \
            or binding["asset"] != old["asset"] or binding["logical_size"] != old["logical_size"] \
            or override["placement_2x"] != [42, 6] or override["x2_size"] != [256, 256]:
        raise ValueError("7obj263 approval or binding changed")
    if digest(staged) != override["artifact_sha256"]:
        raise ValueError("Staged 7obj263 image changed")
    with Image.open(staged) as image:
        if image.mode != "RGBA" or list(image.size) != override["x2_size"]:
            raise ValueError("Staged 7obj263 image has the wrong canvas")

    marker = {
        "binding_file": file,
        "previous_sha256": old["sha256"],
        "artifact_sha256": override["artifact_sha256"],
        "approval_revision": acceptance["revision"],
        "stage_manifest": STAGE_MANIFEST.relative_to(ROOT).as_posix(),
        "inventory_target": override["inventory_target"],
    }
    if args.verify:
        if digest(target) != override["artifact_sha256"] or binding["sha256"] != override["artifact_sha256"] \
                or live.get("post_approval_overrides") != [marker]:
            raise ValueError("The installed 7obj263 override differs from the approved stage")
        print("Verified installed 7obj263 inventory-to-ground override")
        return

    prior_markers = live.get("post_approval_overrides", [])
    if digest(target) not in (old["sha256"], override["artifact_sha256"]) \
            or binding["sha256"] not in (old["sha256"], override["artifact_sha256"]) \
            or len(prior_markers) > 1 \
            or any(row["binding_file"] != file or row["previous_sha256"] != old["sha256"]
                   or row["artifact_sha256"] != override["artifact_sha256"]
                   or row["inventory_target"] != override["inventory_target"] for row in prior_markers):
        raise ValueError("Installed 7obj263 is neither the prior approved image nor this override")
    if digest(target) != override["artifact_sha256"]:
        shutil.copyfile(staged, target)
    target.chmod(0o644)
    binding["sha256"] = override["artifact_sha256"]
    live["post_approval_overrides"] = [marker]
    write_json(live_path, live)
    print("Installed approved 7item263 art into the 7obj263 ground-sprite binding")
    main_verify = json.loads(live_path.read_text())
    if main_verify["post_approval_overrides"] != [marker] or digest(target) != override["artifact_sha256"]:
        raise ValueError("The 7obj263 installation did not verify")


if __name__ == "__main__":
    main()
