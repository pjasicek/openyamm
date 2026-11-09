#!/usr/bin/env python3
"""Record the exact HUD review approval scope and check native-to-x2 runtime contracts."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = HERE.parents[4]
EXPECTED = ROOT / "level_generation/ui/hud_inventory/expected_targets.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def repair_kind(restored):
    kinds = []
    for key, label in (
        ("button_triplet_repair", "regenerated U/H/D button"),
        ("imagegen_repair", "regenerated mana frame"),
        ("alpha_repair", "true-alpha matte repair"),
        ("opaque_edge_repair", "opaque edge color repair"),
    ):
        if restored.get(key):
            kinds.append(label)
    return "; ".join(kinds) or "existing x2 candidate"


def main():
    browser = json.loads((REVIEW / "data.js").read_text().removeprefix("window.HUD_REVIEW_DATA = ").removesuffix(";\n"))
    expected = {record["id"]: record for record in json.loads(EXPECTED.read_text())["targets"]}
    exact = [asset for asset in browser["assets"].values() if asset.get("restored", {}).get("exact_x2")]
    rows = []
    destinations = set()
    for asset in sorted(exact, key=lambda item: item["target"]):
        target = asset["target"]
        frozen = expected.get(target)
        if frozen is None:
            raise ValueError(f"Missing frozen target: {target}")
        native = ROOT / asset["source"]
        candidate = (REVIEW / asset["restored"]["image"]).resolve()
        if not candidate.is_relative_to(REVIEW) or not native.is_file() or not candidate.is_file():
            raise ValueError(f"Missing or unexpected icon path: {target}")
        if asset["source"] != frozen["source_path"] or sha256(native) != frozen["source_sha256"]:
            raise ValueError(f"Native source differs from frozen target: {target}")
        with Image.open(native) as native_image, Image.open(candidate) as x2_image:
            native_image.load()
            x2_image.load()
            native_size = native_image.size
            x2_size = x2_image.size
            if (x2_image.format != "PNG" or x2_image.mode != "RGBA"
                    or x2_size != (native_size[0] * 2, native_size[1] * 2)
                    or list(native_size) != frozen["native_size"]
                    or list(x2_size) != frozen["x2_size"]
                    or list(native_size) != asset["native_size"]
                    or list(x2_size) != asset["restored"]["size"]):
                raise ValueError(f"Native-to-x2 canvas or format mismatch: {target}: {native_size} -> {x2_size}")
        destination = frozen["runtime_output_path"]
        if not destination.startswith("assets_dev/engine/icons_x2/") or not destination.endswith(".png"):
            raise ValueError(f"Unexpected runtime icon destination: {target}: {destination}")
        if destination in destinations:
            raise ValueError(f"Duplicate runtime icon destination: {destination}")
        destinations.add(destination)
        rows.append({
            "name": asset["name"],
            "native_file": asset["source"],
            "native_width": native_size[0],
            "native_height": native_size[1],
            "x2_width": x2_size[0],
            "x2_height": x2_size[1],
            "x2_review_png": candidate.relative_to(ROOT).as_posix(),
            "runtime_destination": destination,
            "native_sha256": frozen["source_sha256"],
            "x2_sha256": sha256(candidate),
            "review_status": asset["restored"]["status"],
            "review_treatment": repair_kind(asset["restored"]),
            "used_in_layouts": "; ".join(sorted({use["layout"] for use in asset.get("uses", [])})),
            "installed_at_runtime_path": (ROOT / destination).is_file(),
        })
    if len(rows) != browser["counts"]["with_exact_x2"]:
        raise ValueError("Browser exact-x2 count changed during the audit")
    fields = list(rows[0])
    with (HERE / "hud_icons.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (HERE / "hud_icon_names.txt").write_text("\n".join(Path(row["native_file"]).name for row in rows) + "\n")
    fallbacks = sorted(
        Path(asset["source"]).name for asset in browser["assets"].values()
        if asset.get("source") and not asset.get("restored", {}).get("exact_x2")
    )
    if len(fallbacks) != browser["counts"]["native_fallback"]:
        raise ValueError("Browser native-fallback count changed during the audit")
    (HERE / "native_fallback_names.txt").write_text("\n".join(fallbacks) + "\n")
    summary = {
        "schema": "openyamm-hud-acceptance-scope-v1",
        "scope": "exact-x2 images displayed by hud_context_review after the user's HUD visual signoff",
        "browser_data_sha256": sha256(REVIEW / "data.js"),
        "expected_targets_sha256": sha256(EXPECTED),
        "listed_icons": len(rows),
        "native_fallbacks_outside_scope": len(fallbacks),
        "generated_content_outside_scope": browser["counts"]["generated_content"],
        "all_native_dimensions_doubled": True,
        "all_source_hashes_match_frozen_targets": True,
        "all_x2_files_decode_as_rgba_png": True,
        "unique_runtime_destinations": len(destinations),
        "currently_installed_at_runtime_path": sum(row["installed_at_runtime_path"] for row in rows),
        "source_review_statuses": Counter(row["review_status"] for row in rows),
        "review_treatments": Counter(row["review_treatment"] for row in rows),
        "known_unrepaired_second_pass_notes": [
            row["name"] for row in rows
            if row["review_status"] == "needs_repair"
            and "regenerated mana frame" not in row["review_treatment"]
        ],
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
