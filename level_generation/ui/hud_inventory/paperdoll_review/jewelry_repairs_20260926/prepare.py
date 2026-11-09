"""Publish two artwork repairs and scoped jewelry sizing, preserving the captured review."""
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
HERE = OUT.parent
sys.path.insert(0, str(HERE))
from prepare_raw_candidates import cleaned_crop, sheet_kind
from scan_magenta import measure, classify


def read(path):
    return json.loads(path.read_text())


def js(path):
    return json.loads(path.read_text().split("=", 1)[1].strip().removesuffix(";"))


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fit_complete(image, size, margin=1):
    alpha = np.asarray(image.getchannel("A"))
    bounds = Image.fromarray((alpha > 24).astype("uint8") * 255).getbbox()
    assert bounds
    subject = image.crop(bounds)
    scale = min((size[0] - margin * 2) / subject.width, (size[1] - margin * 2) / subject.height)
    dims = [max(1, round(subject.width * scale)), max(1, round(subject.height * scale))]
    reduced = subject.convert("RGBa").resize(dims, Image.Resampling.LANCZOS).convert("RGBA")
    output = Image.new("RGBA", size)
    output.alpha_composite(reduced, ((size[0] - dims[0]) // 2, (size[1] - dims[1]) // 2))
    return output, {"master_subject_bounds": bounds, "draw_size_2x": dims, "destination_canvas": size}


def main():
    catalog = js(HERE / "catalog.js")
    previous = js(OUT / "previous_review.js")
    snapshot = read(OUT / "browser_state.original.json")
    decisions = json.loads(snapshot["storage"]["openyamm-paperdoll-context-review-v1"])
    placements = json.loads(snapshot["storage"]["openyamm-paperdoll-placement-v1"])
    ledger_hash = digest(HERE.parent / "checkpoint/state.json")
    assert len(decisions) == 1260 and len(placements) == 728
    repairs = {}
    scans = []
    for name in ("item150", "ring1"):
        asset = catalog["assets"][name]
        old_path = HERE / unquote(asset["candidate"])
        assert digest(old_path) == asset["candidateHash"]
        if name == "item150":
            master_path = OUT / "generated/item150-raw.png"
            master = Image.open(master_path).convert("RGBA")
            assert master.getchannel("A").getextrema()[0] == 0
            operation = {"method": "imagegen_silver_material_correction", "prompt": "generated/item150-prompt.txt",
                         "preserved": "Emerald stones/insets and fine gold trim; corrected broad metal to silver."}
        else:
            master_path = HERE.parent / "chat_bundles/dense64_20260916/dense64_inventory_001/outputs/raw/S001.png"
            raw = Image.open(master_path).convert("RGBA")
            # Actual complete subject, including the pearl above the former y=415 crop.
            bounds = (40, 370, 280, 550)
            master, matte, issues = cleaned_crop(raw.crop(bounds), sheet_kind(raw), False,
                                                {"preserve_thin_lines": True, "background_distance": .08})
            assert not issues
            master.save(OUT / "generated/ring1-recovered-master.png")
            operation = {"method": "complete_retained_master_reextraction", "raw_search_box": bounds,
                         "old_crop": [65, 415, 249, 526], "matte": matte,
                         "note": "Complete pearl, side tips and lower band recovered; no new ring generation."}
        size = [n * 2 for n in asset["size"]]
        image, fitting = fit_complete(master, size)
        path = OUT / "repaired" / (asset["id"] + ".png")
        image.save(path)
        native = Image.open(HERE / asset["native"]).convert("RGBA")
        metrics, native_metrics = measure(image), measure(native)
        spill = classify(metrics, native_metrics)
        assert spill == "no_spill_detected", (name, spill)
        operation.update(fitting)
        operation.update({"master": str(master_path), "master_sha256": digest(master_path)})
        repair = {"target": asset["id"], "name": name, "path": str(path.relative_to(HERE)),
                  "sha256": digest(path), "source_hash": asset["sourceHash"], "old_sha256": asset["candidateHash"],
                  "old_path": asset["candidate"], "note": decisions[asset["id"]].get("note", ""),
                  "operations": [operation], "categories": ["material" if name == "item150" else "crop"],
                  "changed": True, "unresolved": [], "status": "repair_candidate_needs_review",
                  "previously_approved": decisions[asset["id"]]["decision"] == "approve",
                  "placement_compatible_hashes": [asset["candidateHash"], digest(path)],
                  "review_baseline_at": snapshot["captured_at"], "pass_id": "20260926_jewelry_repairs"}
        repairs[asset["id"]] = repair
        scans.append({"target": asset["id"], "name": name, "candidate_hash": digest(path),
                      "source_hash": asset["sourceHash"], "path": repair["path"], "selected": True,
                      "status": spill, "metrics": metrics, "native_metrics": native_metrics})
    write(OUT / "repairs.json", repairs)
    write(OUT / "magenta_scan.json", {"records": scans})

    # Capture and stage exactly what the user accepted, including versions now replaced for review.
    staged = {}
    new_files = 0
    assets = {asset["id"]: asset for asset in catalog["assets"].values()}
    (OUT / "staged-accepted").mkdir(exist_ok=True)
    for target, decision in decisions.items():
        asset = assets[target]
        assert asset["sourceHash"] == decision["source_hash"]
        choices = [{"path": asset["candidate"], "sha256": asset["candidateHash"]}] + asset["preparedAlternatives"]
        choices += previous.get("history", {}).get(target, [])
        if target in previous["repairs"]:
            choices.append(previous["repairs"][target])
        chosen = next(choice for choice in choices if choice["sha256"] == decision["candidate_hash"])
        source = HERE / unquote(chosen["path"].split("?")[0])
        assert digest(source) == decision["candidate_hash"]
        record = {"target": target, "name": asset["name"], "decision": decision,
                  "reviewed_path": chosen["path"], "reviewed_sha256": decision["candidate_hash"],
                  "source_hash": asset["sourceHash"]}
        if decision["decision"] == "approve":
            retained = previous["staged"].get(target, {})
            if retained.get("staged_path") and retained["reviewed_sha256"] == decision["candidate_hash"]:
                destination = HERE / retained["staged_path"]
            else:
                destination = OUT / "staged-accepted" / (target + ".png")
                shutil.copyfile(source, destination)
                new_files += 1
            assert digest(destination) == decision["candidate_hash"]
            record["staged_path"] = str(destination.relative_to(HERE))
        staged[target] = record
    write(OUT / "stage_manifest.json", {"staging_only": True, "ledger_modified": False, "records": staged})
    write(OUT / "placements.json", {"schema": "openyamm-paperdoll-placement-v1", "placements": placements})
    write(OUT / "review.original.json", {"decisions": decisions, "placements": placements,
                                         "exported_at": snapshot["captured_at"], "runtime_tables_modified": False})
    with (OUT / "placement_proposals.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["key", "item_id", "doll_type", "slot", "base_x", "base_y", "delta_x", "delta_y"])
        for key, record in placements.items():
            writer.writerow([key, record["item_id"], record.get("doll_type"), record.get("slot"),
                             *record["base"], *record["delta"]])
    previous.update({"id": "20260926_jewelry_repairs", "import_revision": 1,
                     "decisions": decisions, "placements": placements, "staged": staged,
                     "new_targets": sorted(repairs)})
    previous["repairs"].update(repairs)
    previous["magenta_scan"]["records"] += scans
    (OUT / "review.js").write_text("window.PAPERDOLL_REPAIR_PASS = " + json.dumps(previous) + ";\n")

    # One image per source-equivalent family remains authoritative for both consumers.
    fit = js(HERE / "jewelry_inventory_20260926/inventory_fit.js")
    # Scale about the existing center, preserving all manual x/y deltas. The gauntlet's 60px height leaves
    # room inside its 64px opening at the user's already accepted (-2,-7) offset.
    scales = {"gontlet3": 60 / 81, "ring6": 32 / 40, "ring10": 32 / 42, "ring1": 32 / 40, "item150": 32 / 34}
    fits = {record["item_id"]: record for record in fit["records"]}
    for record in fit["records"]:
        representative = fits[record["representative_item_id"]]
        if representative["icon"] in scales:
            record["overlay_scale"] = scales[representative["icon"]]
        repair = repairs.get(record["target"])
        if repair:
            record["previous_candidate"] = record["candidate"]
            record["previous_candidate_hash"] = record["candidate_hash"]
            record["candidate"] = repair["path"]
            record["candidate_hash"] = repair["sha256"]
        decision = decisions.get(record["target"])
        if decision:
            record["review_status"] = "replacement_needs_review" if repair else decision["decision"]
            record["note"] = decision.get("note", "")
    for group in fit["groups"]:
        representative = fits[group["representative_item_id"]]
        group.update({"shared_candidate": representative["candidate"],
                      "shared_candidate_hash": representative["candidate_hash"],
                      "review_status": representative["review_status"]})
    fit.update({"captured_at": snapshot["captured_at"], "artwork_modified": True,
                "browser_snapshot_sha256": digest(OUT / "browser_state.original.json"),
                "overlay_policy": "Scoped uniform scaling about the existing image center; original panels and manual deltas unchanged."})
    fit["group_summary"]["review"] = dict(Counter(g["review_status"] for g in fit["groups"]))
    for stat, summary in fit["summary"].items():
        summary["review"] = dict(Counter(record["review_status"] for record in fit["records"]
                                        if record["stat"] == stat))
    write(OUT / "inventory_fit.json", fit)
    (OUT / "inventory_fit.js").write_text("window.PAPERDOLL_INVENTORY_FIT = " + json.dumps(fit) + ";\n")
    for filename in ("inventory_fit.csv", "items_table_proposals.csv"):
        shutil.copyfile(HERE / "jewelry_inventory_20260926" / filename, OUT / filename)
    with (OUT / "shared_image_proposals.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["item_id", "name", "icon", "representative_item_id", "shared_candidate",
                         "shared_candidate_hash", "inventory_scale", "jewelry_overlay_scale", "consumers"])
        for record in fit["records"]:
            representative = fits[record["representative_item_id"]]
            writer.writerow([record["item_id"], record["name"], record["icon"], representative["item_id"],
                             representative["candidate"], representative["candidate_hash"], record["draw_scale"],
                             record.get("overlay_scale", 1), "inventory|jewelry_overlay"])
    assert digest(HERE.parent / "checkpoint/state.json") == ledger_hash
    report = {"result": "PASS", "new_artwork": len(repairs), "overlay_size_groups": len(scales),
              "saved_decisions": len(decisions), "staged_approvals": sum("staged_path" in r for r in staged.values()),
              "new_staged_files": new_files, "saved_placements": len(placements), "ledger_sha256": ledger_hash,
              "ledger_unchanged": True, "new_acceptances": 0}
    write(OUT / "validation.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
