#!/usr/bin/env python3
"""Record and stage all PC portrait spell effects approved by the user."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE = HERE / "staged_approved_effects"
ACCEPTANCE = HERE / "effect_acceptance.json"
BROWSER = HERE / "effect_acceptance.js"
SUPPLEMENT = "engine--icons--sp21a10.bmp"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_assignment(path: Path) -> dict:
    return json.loads(path.read_text().split("=", 1)[1].strip().removesuffix(";"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="audit the existing stage and ledger")
    args = parser.parse_args()
    catalog = read_assignment(HERE / "catalog.js")
    by_id = {item["id"]: item for item in catalog["items"]}
    sequences = read_assignment(HERE / "pc_effect_sequences/sequences.js")["sequences"]
    frames = {frame["id"]: {**frame, "sequence": group["family"]}
              for group in sequences for frame in group["frames"]}
    effect_ids = set(json.loads((HERE / "review_acceptance.json").read_text())["pending_effect_ids"])
    if len(effect_ids) != 177 or len(frames) != 174 or set(frames) - effect_ids != {SUPPLEMENT}:
        raise ValueError("The approved spell effect inventory changed")
    supplement = frames[SUPPLEMENT]
    by_id[SUPPLEMENT] = {
        "source": "../../../assets_dev/engine/icons/sp21a10.bmp",
        "source_sha256": supplement["source_sha256"], "native_size": supplement["native_size"],
        "x2_size": [side * 2 for side in supplement["native_size"]],
        "candidates": [{"path": "pc_effect_sequences/" + supplement["candidate"],
                        "sha256": supplement["candidate_sha256"]}],
    }
    historical = json.loads((HERE / "review_repairs/four_kept_effect_acceptance.json").read_text())
    rows = []
    staged = []
    for target_id in sorted(effect_ids | {SUPPLEMENT}):
        item = by_id[target_id]
        candidate = item["candidates"][0]
        frame = frames.get(target_id)
        source = (HERE / item["source"]).resolve()
        artwork = (HERE / candidate["path"]).resolve()
        relative = source.relative_to(ROOT / "assets_dev")
        if relative.parent.name != "icons" or relative.suffix.lower() != ".bmp":
            raise ValueError(f"Unexpected native effect source: {source}")
        destination = STAGE / relative.parent.parent / "icons_x2" / (relative.stem.lower() + ".png")
        review_source = (HERE / "pc_effect_sequences" / frame["original"]).resolve() \
            if target_id == SUPPLEMENT else source
        if digest(review_source) != item["source_sha256"] or digest(artwork) != candidate["sha256"]:
            raise ValueError(f"Approved candidate changed: {target_id}")
        if frame and (HERE / "pc_effect_sequences" / frame["candidate"]).resolve() != artwork:
            raise ValueError(f"Animation viewer candidate differs: {target_id}")
        with Image.open(artwork) as image:
            if image.mode != "RGBA" or list(image.size) != item["x2_size"] \
                    or item["x2_size"] != [side * 2 for side in item["native_size"]]:
                raise ValueError(f"Invalid kept 2x effect frame: {target_id}")
        if destination.exists():
            if digest(destination) != candidate["sha256"]:
                raise ValueError(f"Staged effect frame changed: {target_id}")
        elif args.verify:
            raise ValueError(f"Missing staged effect frame: {target_id}")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(artwork, destination)
            destination.chmod(0o644)
        rows.append({"id": target_id, "sequence": frame["sequence"] if frame else None,
                     "frame_index": frame["number"] if frame else None, "decision": "approve",
                     "source_sha256": item["source_sha256"],
                     "candidate": candidate["path"], "candidate_sha256": candidate["sha256"],
                     "artifact": destination.relative_to(HERE).as_posix()})
        if target_id == SUPPLEMENT:
            rows[-1]["source_reference"] = review_source.relative_to(ROOT).as_posix()
            rows[-1]["native_source_sha256"] = digest(source)
        staged.append({"id": target_id, "native_source": source.relative_to(ROOT).as_posix(),
                       "source_sha256": digest(source),
                       "artifact": destination.relative_to(ROOT).as_posix(),
                       "artifact_sha256": candidate["sha256"], "x2_size": item["x2_size"]})
    current = {row["id"]: row for row in rows}
    for previous in historical["items"]:
        if current[previous["id"]] != previous:
            raise ValueError(f"Previously accepted effect changed: {previous['id']}")
    if {path for path in STAGE.rglob("*.png")} != {ROOT / row["artifact"] for row in staged}:
        raise ValueError("Unlisted or missing staged effect frame")
    revision = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:16]
    acceptance = {"schema": 1, "kind": "visual_review_acceptance", "revision": revision,
                  "scope": "all_pc_spell_effects",
                  "approval_date": "2026-09-24",
                  "approval_basis": "Explicit user approval: OK whatever accept it including all the other spell effects, ledger it",
                  "previous_revision": historical["revision"],
                  "approved_sequences": sorted(group["family"] for group in sequences),
                  "approved_catalog_count": len(effect_ids), "supplemental_count": 1,
                  "standalone_count": len(effect_ids - set(frames)), "pending_effect_count": 0,
                  "approved_count": len(rows), "items": rows}
    manifest = {"schema": 1, "kind": "staged_approved_pc_effect_sequences", "revision": revision,
                "count": len(staged), "items": staged}
    browser = {"schema": 1, "revision": revision,
               "decisions": {row["id"]: {"decision": "approve", "reasons": [], "note": "",
                                       "candidate_index": 0,
                                       "candidate_sha256": row["candidate_sha256"],
                                       "source_sha256": row["source_sha256"]} for row in rows}}
    browser_text = "window.KEPT_EFFECT_ACCEPTANCE = " + json.dumps(browser, separators=(",", ":")) + ";\n"
    if args.verify:
        if json.loads(ACCEPTANCE.read_text()) != acceptance \
                or json.loads((STAGE / "manifest.json").read_text()) != manifest \
                or BROWSER.read_text() != browser_text:
            raise ValueError("Effect acceptance ledger or stage changed")
    else:
        ACCEPTANCE.write_text(json.dumps(acceptance, indent=2) + "\n")
        (STAGE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        BROWSER.write_text(browser_text)
    print(json.dumps({"approved_sequences": acceptance["approved_sequences"], "approved_frames": len(rows),
                      "revision": revision}, indent=2))


if __name__ == "__main__":
    main()
