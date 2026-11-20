#!/usr/bin/env python3
"""Measure alpha and magenta evidence for the user's HUD flags without changing artwork."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
FLAGS = HERE / "user_flags_20260923.json"


def pixels(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGBA"), dtype=np.uint8)


def measure_asset(asset: dict) -> dict:
    candidate = asset["restored"]
    row = {
        "target": asset["target"], "name": asset["name"],
        "candidate_status": candidate["status"], "second_pass": asset.get("second_pass", ""),
        "native_size": "x".join(map(str, asset["native_size"])),
        "raw_available": bool(asset.get("raw")), "candidate_image": candidate.get("original", ""),
        "native_transparent_pct": "", "candidate_transparent_pct": "",
        "candidate_opacity_on_native_clear_pct": "", "opaque_magenta_pct": "", "category": "",
    }
    if not candidate.get("image"):
        row["category"] = "raw_only_or_unfitted" if asset.get("raw") else "no_candidate"
        return row

    native = pixels(HERE / asset["native"])
    restored = pixels(HERE / (candidate.get("keyed_image") or candidate["image"]))
    expected_clear = np.repeat(np.repeat(native[:, :, 3] < 128, 2, axis=0), 2, axis=1)
    candidate_clear = restored[:, :, 3] < 128
    alpha = restored[:, :, 3] >= 128
    red = restored[:, :, 0].astype(np.int16)
    green = restored[:, :, 1].astype(np.int16)
    blue = restored[:, :, 2].astype(np.int16)
    high_chroma = (np.minimum(red, blue) - green >= 90) & (red >= 150) & (blue >= 150)
    opaque_magenta = alpha & high_chroma
    native_clear_count = int(expected_clear.sum())
    opacity_on_clear = int((expected_clear & alpha).sum())
    row["native_transparent_pct"] = round(100 * float((native[:, :, 3] < 128).mean()), 2)
    row["candidate_transparent_pct"] = round(100 * float(candidate_clear.mean()), 2)
    row["candidate_opacity_on_native_clear_pct"] = round(
        100 * opacity_on_clear / native_clear_count, 2) if native_clear_count else 0
    row["opaque_magenta_pct"] = round(100 * float(opaque_magenta.mean()), 2)

    if native_clear_count and opacity_on_clear / native_clear_count > 0.1:
        row["category"] = "wrong_or_missing_alpha"
    elif float(opaque_magenta.mean()) > 0.01:
        row["category"] = "magenta_contamination_check"
    else:
        row["category"] = "visual_geometry_or_fine_edge_review"
    return row


def measure_visible_asset(asset: dict, flagged: bool) -> dict:
    candidate = asset["restored"]
    displayed = pixels(HERE / candidate["image"])
    rgb = displayed[:, :, :3]
    opaque = displayed[:, :, 3] >= 128
    near_key = (rgb[:, :, 0] >= 220) & (rgb[:, :, 2] >= 220) & (rgb[:, :, 1] <= 40) & opaque
    repair = ("imagegen_button_triplets" if candidate.get("button_triplet_repair") else
              "imagegen_true_alpha" if candidate.get("imagegen_repair") else
              "magenta_matte_true_alpha" if candidate.get("alpha_repair") else
              "opaque_outer_edge_color" if candidate.get("opaque_edge_repair") else "none")
    return {"target": asset["target"], "name": asset["name"], "user_flagged": flagged,
            "repair": repair, "candidate_status": candidate["status"],
            "display_image": candidate["image"], "display_size": "x".join(map(str, candidate["size"])),
            "visible_near_key_pink_pct": round(100 * float(near_key.mean()), 4),
            "display_transparent_pct": round(100 * float((~opaque).mean()), 3)}


def main() -> None:
    flags = json.loads(FLAGS.read_text())
    data_js = (HERE / "data.js").read_text()
    data = json.loads(data_js.removeprefix("window.HUD_REVIEW_DATA = ").removesuffix(";\n"))
    by_target = {asset.get("target"): asset for asset in data["assets"].values() if asset.get("target")}
    rows = []
    summary = Counter()

    for target in flags["targets"]:
        asset = by_target.get(target)
        if asset is None:
            rows.append({"target": target, "category": "not_in_browser"})
            summary["not_in_browser"] += 1
            continue

        row = {"note": flags.get("notes", {}).get(target, ""), **measure_asset(asset)}
        summary[row["category"]] += 1
        rows.append(row)

    with (HERE / "user_flag_audit.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (HERE / "user_flag_audit_summary.json").write_text(json.dumps({
        "flag_count": len(flags["targets"]), "categories": summary,
        "note": "Metrics nominate checks; they do not approve or reject artwork. Magenta materials can be intentional.",
    }, indent=2) + "\n")
    all_rows = [measure_asset(asset) for asset in by_target.values() if asset["restored"].get("image")]
    all_rows.sort(key=lambda item: (
        -float(item["candidate_opacity_on_native_clear_pct"]), -float(item["opaque_magenta_pct"])))
    with (HERE / "all_candidate_alpha_audit.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    attention = [item for item in all_rows if item["category"] != "visual_geometry_or_fine_edge_review"]
    (HERE / "all_candidate_alpha_summary.json").write_text(json.dumps({
        "candidate_count": len(all_rows), "attention_count": len(attention),
        "categories": Counter(item["category"] for item in all_rows),
        "note": "Heuristic attention only; original alpha, intended purple art, internal geometry and full-scene fit need review.",
    }, indent=2) + "\n")
    flag_set = set(flags["targets"])
    visible_rows = [measure_visible_asset(asset, asset["target"] in flag_set)
                    for asset in by_target.values() if asset["restored"].get("image")]
    visible_rows.sort(key=lambda item: item["target"])
    with (HERE / "post_repair_audit.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(visible_rows[0]))
        writer.writeheader()
        writer.writerows(visible_rows)
    visible_summary = {
        "exact_x2_count": len(visible_rows),
        "repair_counts": Counter(row["repair"] for row in visible_rows),
        "user_flagged_with_exact_x2": sum(row["user_flagged"] for row in visible_rows),
        "user_flagged_with_review_repair": sum(row["user_flagged"] and row["repair"] != "none"
                                                 for row in visible_rows),
        "visible_near_key_pink_over_0_03_pct": sum(row["visible_near_key_pink_pct"] > .03
                                                     for row in visible_rows),
        "note": "All displayed x2 images scanned. Chroma scan and deterministic repairs do not approve artwork.",
    }
    (HERE / "post_repair_summary.json").write_text(json.dumps(visible_summary, indent=2) + "\n")
    pilot_dir = HERE / "diagnostic_alpha"
    pilots = {}
    if (pilot_dir / "measurements.json").is_file():
        for pilot in json.loads((pilot_dir / "measurements.json").read_text()):
            name = pilot["name"].lower()
            image = pilot_dir / (name + "-matte-pilot.png")
            comparison = pilot_dir / (name + "-comparison.png")
            current = by_target.get(pilot["target"], {}).get("restored", {}).get("original")
            source = HERE / current if current else None
            matches = bool(source and source.is_file() and pilot.get("source_sha256") ==
                           hashlib.sha256(source.read_bytes()).hexdigest())
            if image.is_file() and comparison.is_file() and matches:
                pilots[pilot["target"]] = {
                    "image": "diagnostic_alpha/" + image.name,
                    "comparison": "diagnostic_alpha/" + comparison.name,
                    "measurements": pilot["pilot"],
                    "visual_note": pilot.get("visual_note", ""),
                }
    audit_data = {
        "flagged": flags["targets"],
        "flag_notes": flags.get("notes", {}),
        "by_target": {item["target"]: item for item in all_rows},
        "pilots": pilots,
        "note": "Automated alpha checks nominate inspection only; pilots are unapproved.",
    }
    (HERE / "audit.js").write_text("window.HUD_REVIEW_AUDIT = " + json.dumps(audit_data, separators=(",", ":")) + ";\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
