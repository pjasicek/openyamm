#!/usr/bin/env python3
"""Record this review's approved non-effect art and stage its exact 2x files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE = HERE / "staged_approved"
ACCEPTANCE = HERE / "review_acceptance.json"
WORLD_NAME = "7obj263_p9.png"
SPECIAL_ID = "engine--icons--7item263.bmp"
EXPECTED_TOTAL = 1718
EXPECTED_PENDING = 177
EXPECTED_ACCEPTED = 1541
EXPECTED_WORLD_REUSE = 138


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def read_assignment(path: Path) -> dict:
    return json.loads(path.read_text().split("=", 1)[1].strip().removesuffix(";"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def checked_copy(source: Path, destination: Path, expected_hash: str, verify: bool) -> None:
    if digest(source) != expected_hash:
        raise ValueError(f"Approved input changed: {source}")
    if destination.exists():
        if digest(destination) != expected_hash:
            raise ValueError(f"Staged output changed: {destination}")
    elif verify:
        raise ValueError(f"Staged output is missing: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    if not verify:
        destination.chmod(0o644)
    if digest(destination) != expected_hash:
        raise ValueError(f"Staged output differs from approval: {destination}")


def pending_ids(catalog: dict) -> set[str]:
    sequence = read_assignment(HERE / "pc_effect_sequences/sequences.js")
    pending = {frame["id"] for group in sequence["sequences"] for frame in group["frames"]
               if frame["id"] != "engine--icons--sp21a10.bmp"}
    if len(pending) != 173:
        raise ValueError(f"Changed referenced PC effect sequence set: {len(pending)}")
    by_id = {item["id"]: item for item in catalog["items"]}
    if not pending.issubset(by_id):
        raise ValueError("Referenced PC effect sequence is missing from the review")
    # Three more single-frame effects occur in icon_frame_data.txt. spell1 is an
    # unreferenced spell-labelled image; hold it with the same separate review.
    standalone = {item["id"] for item in catalog["items"]
                  if item["name"].lower().startswith(("sp", "spell"))
                  and not item["name"].lower().startswith("spear")}
    pending |= standalone
    if len(pending) != EXPECTED_PENDING:
        raise ValueError(f"Changed PC effect review boundary: {len(pending)}")
    return pending


def target_path(item: dict) -> Path:
    source = (HERE / item["source"]).resolve()
    relative = source.relative_to(ROOT / "assets_dev")
    if relative.parent.name != "icons" or relative.suffix.lower() not in (".bmp", ".png", ".pcx"):
        raise ValueError(f"Unexpected native icon path: {source}")
    return STAGE / relative.parent.parent / "icons_x2" / (relative.stem.lower() + ".png")


def special_world_image(candidate: Path, world_size: tuple[int, int], offset: tuple[int, int]) -> Image.Image:
    with Image.open(candidate) as image:
        if image.mode != "RGBA" or image.size != (142, 250):
            raise ValueError("7item263 approved inventory image changed dimensions or mode")
        if offset[0] < 0 or offset[1] < 0 or offset[0] + image.width > world_size[0] \
                or offset[1] + image.height > world_size[1]:
            raise ValueError("7item263 does not fit its ground canvas")
        result = Image.new("RGBA", world_size)
        result.paste(image, offset)
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true", help="audit an existing stage and ledger")
    args = parser.parse_args()

    catalog = read_assignment(HERE / "catalog.js")
    items = catalog["items"]
    if len(items) != EXPECTED_TOTAL or len({item["id"] for item in items}) != EXPECTED_TOTAL:
        raise ValueError("Review catalog changed")
    pending = pending_ids(catalog)
    approved = [item for item in items if item["id"] not in pending]
    if len(approved) != EXPECTED_ACCEPTED:
        raise ValueError("Approval count changed")
    approved_ids = {item["id"] for item in approved}
    if SPECIAL_ID not in approved_ids:
        raise ValueError("The 7item263 exception is missing")
    if sum(item["candidates"][0].get("kind") == "approved_world_master" for item in approved) \
            != EXPECTED_WORLD_REUSE:
        raise ValueError("Approved ground master reuse set changed")

    approval_rows = []
    stage_rows = []
    categories = Counter()
    for item in approved:
        candidate = item["candidates"][0]
        source = (HERE / item["source"]).resolve()
        image = (HERE / candidate["path"]).resolve()
        destination = target_path(item)
        if digest(source) != item["source_sha256"] or digest(image) != candidate["sha256"]:
            raise ValueError(f"Source or candidate changed: {item['id']}")
        with Image.open(image) as restored:
            if restored.mode not in ("RGB", "RGBA") or list(restored.size) != item["x2_size"] \
                    or item["x2_size"] != [size * 2 for size in item["native_size"]]:
                raise ValueError(f"Invalid exact 2x PNG: {item['id']}")
        checked_copy(image, destination, candidate["sha256"], args.verify)
        categories[item["category"]] += 1
        approval_rows.append({
            "id": item["id"], "category": item["category"], "decision": "approve",
            "source_sha256": item["source_sha256"], "candidate_sha256": candidate["sha256"],
            "candidate": candidate["path"], "artifact": destination.relative_to(HERE).as_posix(),
            "provenance": candidate["origin"],
        })
        stage_rows.append({
            "id": item["id"], "native_source": source.relative_to(ROOT).as_posix(),
            "source_sha256": item["source_sha256"],
            "artifact": destination.relative_to(ROOT).as_posix(),
            "artifact_sha256": candidate["sha256"], "x2_size": item["x2_size"],
        })

    # The one reverse binding uses the selected inventory artwork as the world
    # object's foreground, placed at the native drawing's world offset.
    report = json.loads((HERE / "review_repairs/world_item_links/report.json").read_text())
    link = report["items"][SPECIAL_ID]
    native = link["native_match"]
    offset = (2 * (native["world_box"][0] - native["inventory_box"][0]),
              2 * (native["world_box"][1] - native["inventory_box"][1]))
    if native["sprite_name"] != "7obj263" or native["palette_id"] != 9 or offset != (42, 6):
        raise ValueError("The special inventory/world placement changed")
    old_plan = json.loads((ROOT / "level_generation/sprites/restoration_jobs/runs/remaining_review_20260923/"
                           "approved-installation-plan.json").read_text())
    old_binding = next(row for row in old_plan["bindings"] if row["file"] == WORLD_NAME)
    world_destination = STAGE / "engine/decorations_x2" / WORLD_NAME
    image = (HERE / next(item for item in approved if item["id"] == SPECIAL_ID)["candidates"][0]["path"]).resolve()
    new_world = special_world_image(image, tuple(side * 2 for side in old_binding["logical_size"]), offset)
    if args.verify:
        if not world_destination.is_file():
            raise ValueError("The staged 7obj263 world image is missing")
        with Image.open(world_destination) as staged_world:
            if staged_world.mode != "RGBA" or staged_world.size != new_world.size \
                    or staged_world.tobytes() != new_world.tobytes():
                raise ValueError("The staged 7obj263 world pixels changed")
    else:
        world_destination.parent.mkdir(parents=True, exist_ok=True)
        if world_destination.is_file():
            with Image.open(world_destination) as staged_world:
                if staged_world.mode != "RGBA" or staged_world.size != new_world.size \
                        or staged_world.tobytes() != new_world.tobytes():
                    raise ValueError("An existing 7obj263 world stage differs from the selected inventory art")
        else:
            new_world.save(world_destination, optimize=True)
        world_destination.chmod(0o644)
    world_hash = digest(world_destination)
    expected_pngs = {ROOT / row["artifact"] for row in stage_rows} | {world_destination}
    actual_pngs = set(STAGE.rglob("*.png"))
    if len(expected_pngs) != EXPECTED_ACCEPTED + 1 or actual_pngs != expected_pngs:
        raise ValueError("Staging tree has missing, duplicate, or unlisted PNGs")
    world_override = {
        "binding_file": WORLD_NAME, "binding_name": "7obj263", "palette_id": 9,
        "previous_sha256": old_binding["sha256"], "artifact": world_destination.relative_to(ROOT).as_posix(),
        "artifact_sha256": world_hash, "inventory_target": SPECIAL_ID,
        "inventory_candidate_sha256": next(row["candidate_sha256"] for row in approval_rows if row["id"] == SPECIAL_ID),
        "placement_2x": list(offset), "x2_size": list(new_world.size),
    }
    revision = hashlib.sha256(json.dumps(approval_rows, sort_keys=True).encode()).hexdigest()[:16]
    acceptance = {
        "schema": 1, "kind": "visual_review_acceptance", "revision": revision,
        "scope": "remaining_ui_art_except_sp_spell_effects", "catalog_total": len(items),
        "accepted_count": len(approved), "pending_effect_count": len(pending),
        "pending_effect_ids": sorted(pending), "by_category": dict(categories),
        "approved_world_master_inventory_count": EXPECTED_WORLD_REUSE,
        "items": approval_rows,
    }
    manifest = {
        "schema": 1, "kind": "staged_remaining_ui_art", "revision": revision,
        "count": len(stage_rows), "items": stage_rows, "world_override": world_override,
    }
    browser = {"schema": 1, "revision": revision, "pending_effect_ids": sorted(pending),
               "decisions": {row["id"]: {"decision": "approve", "reasons": [], "note": "",
                                        "candidate_index": 0, "candidate_sha256": row["candidate_sha256"],
                                        "source_sha256": row["source_sha256"]} for row in approval_rows}}
    browser_text = "window.REMAINING_ART_ACCEPTANCE = " + json.dumps(browser, separators=(",", ":")) + ";\n"
    if args.verify:
        if json.loads(ACCEPTANCE.read_text()) != acceptance \
                or json.loads((STAGE / "manifest.json").read_text()) != manifest \
                or (HERE / "acceptance.js").read_text() != browser_text:
            raise ValueError("Acceptance ledger or browser data differs from the staged artwork")
    else:
        write_json(ACCEPTANCE, acceptance)
        write_json(STAGE / "manifest.json", manifest)
        (HERE / "acceptance.js").write_text(browser_text)
    print(json.dumps({"accepted": len(approved), "pending_effects": len(pending),
                      "ground_master_inventory": EXPECTED_WORLD_REUSE, "revision": revision,
                      "world_override_sha256": world_hash, "by_category": dict(categories)}, indent=2))


if __name__ == "__main__":
    main()
