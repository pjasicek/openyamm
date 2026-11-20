#!/usr/bin/env python3
"""Build the PC effect playback catalog from the game's icon animation table."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = HERE.parents[3]
TABLE = ROOT / "assets_dev/engine/data_tables/icon_frame_data.txt"
HUD = ROOT / "level_generation/ui/hud_inventory/hud_context_review"
REMAINING = REVIEW / "review_repairs/remaining_sequences"
KEPT = {"sp05e", "spell14e", "spell36e", "spell68e"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def browser_path(path: Path) -> str:
    return os.path.relpath(path, HERE).replace(os.sep, "/")


def family_name(texture: str) -> str:
    patterns = (r"((?:sp|spell)\d+e)\d+", r"(sp\d+a)\d+", r"(sp\d+h)[a-z]",
                r"(sp\d+)-\d+", r"(sptext\d+)[a-z]")
    for pattern in patterns:
        match = re.fullmatch(pattern, texture, re.IGNORECASE)
        if match:
            return match.group(1).lower()
    raise ValueError(f"Unrecognized PC effect frame name: {texture}")


def animation_groups() -> list[dict]:
    groups = []
    current = []
    for line in TABLE.read_text().splitlines():
        if line.startswith("//") or line.startswith("AnimationName"):
            continue
        parts = line.split("\t")
        if len(parts) < 6:
            continue
        animation, texture, frame_ticks, _, _, flags = parts[:6]
        if "First" in flags:
            if current:
                raise ValueError(f"Unterminated icon animation before {animation}")
            current = []
        if not current and "First" not in flags:
            raise ValueError(f"Orphan icon frame: {animation}")
        current.append({"animation": animation, "texture": texture or animation,
                        "ticks": int(frame_ticks)})
        if "HasMore" not in flags:
            if len(current) > 1 and all(frame["texture"].lower().startswith("sp") for frame in current):
                groups.append({"animation": current[0]["animation"],
                               "family": family_name(current[0]["texture"]), "frames": current})
            current = []
    if current:
        raise ValueError("Unterminated final icon animation")
    return groups


def hud_first_frame() -> dict:
    manifest = json.loads((HUD / "alpha_repair/manifest.json").read_text())
    record = next(row for row in manifest["records"] if row["target"] == "engine--icons--sp21a10.bmp")
    regenerated = json.loads((REMAINING / "report.json").read_text())["items"][record["target"]]
    stabilized = json.loads((REMAINING / "stabilization_report.json").read_text())["items"]
    regenerated = stabilized.get(record["target"], regenerated)
    locked = json.loads((REMAINING / "idle_core_report.json").read_text())["items"]
    regenerated = locked.get(record["target"], regenerated)
    original = HUD / record["native_path"]
    candidate = REVIEW / regenerated["artifact"]
    if digest(original) != record["native_sha256"] or digest(original) != regenerated["source_sha256"] \
            or digest(candidate) != regenerated["artifact_sha256"]:
        raise ValueError("The HUD first frame has changed")
    return {"id": record["target"], "original": browser_path(original),
            "candidate": browser_path(candidate),
            "source_sha256": regenerated["source_sha256"],
            "candidate_sha256": regenerated["artifact_sha256"],
            "native_size": [side // 2 for side in record["size"]],
            "candidate_origin": "Whole-sequence imagegen restoration",
            "review": "../review_repairs/remaining_sequences/first_frame.html",
            "status": "hud_pending"}


def main() -> None:
    catalog = json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].strip().removesuffix(";"))
    by_id = {item["id"]: item for item in catalog["items"]}
    acceptance = json.loads((REVIEW / "effect_acceptance.json").read_text())
    accepted = {row["id"]: row for row in acceptance["items"]}
    idle_families = set(json.loads((REMAINING / "idle_core_report.json").read_text())["families"])
    hud_frame = hud_first_frame()
    groups = animation_groups()
    seen = set()
    for group in groups:
        frames = []
        for ordinal, frame in enumerate(group["frames"], 1):
            texture = frame["texture"]
            target_id = f"engine--icons--{texture.lower()}.bmp"
            if target_id in seen:
                raise ValueError(f"Duplicate animation frame: {target_id}")
            seen.add(target_id)
            if target_id == hud_frame["id"]:
                entry = {**hud_frame, "name": texture, "number": ordinal, "ticks": frame["ticks"]}
            else:
                item = by_id.get(target_id)
                if item is None:
                    raise ValueError(f"Missing review frame: {target_id}")
                candidate = item["candidates"][0]
                original = REVIEW / item["original"]
                restored = REVIEW / candidate["path"]
                if digest(restored) != candidate["sha256"]:
                    raise ValueError(f"Changed review candidate: {target_id}")
                entry = {"id": target_id, "name": texture, "number": ordinal,
                         "ticks": frame["ticks"], "original": browser_path(original),
                         "candidate": browser_path(restored), "native_size": item["native_size"],
                         "candidate_origin": candidate["origin"],
                         "review": "../index.html?item=" + target_id,
                         "status": "remaining_review",
                         "kept_approved": group["family"] in KEPT,
                         "full_sequence_repair": bool(item.get("sequence_repair"))}
            approval = accepted.get(target_id)
            candidate_hash = digest(HERE / entry["candidate"])
            source_hash = entry.get("source_sha256") or by_id[target_id]["source_sha256"]
            entry["approved"] = bool(approval and approval["candidate_sha256"] == candidate_hash
                                     and approval["source_sha256"] == source_hash)
            if entry["approved"]:
                entry["status"] = "approved"
            with Image.open(HERE / entry["original"]) as image:
                if image.size != tuple(entry["native_size"]):
                    raise ValueError(f"Wrong native size: {target_id}: {image.size}")
            with Image.open(HERE / entry["candidate"]) as image:
                expected = tuple(2 * side for side in entry["native_size"])
                if image.size != expected:
                    raise ValueError(f"Wrong 2x size: {target_id}: {image.size} != {expected}")
            frames.append(entry)
        sizes = {tuple(frame["native_size"]) for frame in frames}
        if len(sizes) != 1:
            raise ValueError(f"Mixed frame canvases within {group['family']}: {sizes}")
        group["frames"] = frames
        group["native_size"] = list(sizes.pop())
        group["idle_core_locked"] = group["family"] in idle_families
        boxes = []
        for frame in frames:
            with Image.open(HERE / frame["original"]) as image:
                box = image.convert("RGBA").getchannel("A").getbbox()
            if box is None:
                raise ValueError(f"Empty native effect frame: {frame['id']}")
            boxes.append(box)
        envelope = [min(box[0] for box in boxes), min(box[1] for box in boxes),
                    max(box[2] for box in boxes), max(box[3] for box in boxes)]
        group["native_envelope"] = envelope
        group["guide_center"] = [(envelope[0] + envelope[2]) / 2,
                                 (envelope[1] + envelope[3]) / 2]
        group["guide_shape"] = "rect" if group["family"] in {"sp96h", "sptext01"} else "oval"
    if len(groups) != 22 or sum(len(group["frames"]) for group in groups) != 174:
        raise ValueError("PC effect sequence inventory changed; inspect the animation table")
    payload = {"schema": 1, "table": browser_path(TABLE),
               "summary": {"sequences": len(groups), "frames": len(seen),
                           "kept_approved_sequences": len(KEPT),
                           "approved_sequences": sum(all(frame["approved"] for frame in group["frames"])
                                                     for group in groups),
                           "approved_frames": sum(frame["approved"] for group in groups for frame in group["frames"]),
                           "supplemental_frames": 1,
                           "hud_pending_frames": sum(frame["status"] == "hud_pending"
                                                     for group in groups for frame in group["frames"])},
               "sequences": groups}
    (HERE / "sequences.js").write_text("window.PC_EFFECT_SEQUENCES = " +
                                       json.dumps(payload, separators=(",", ":")) + ";\n")
    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
