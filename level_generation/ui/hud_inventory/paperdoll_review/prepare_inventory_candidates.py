"""Prepare retained weapon/shield inventory art for the equipment browser, without accepting it."""

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

from PIL import Image, ImageDraw

from prepare_raw_candidates import HERE, INVENTORY, ROOT, catalog, digest, process_attempt, queue_module, read
import registration


OUT = HERE / "inventory_prepared"
STATS = {"Weapon", "Weapon1or2", "Weapon2", "Missile", "Shield", "WeaponW"}
RECIPE = "retained-inventory-extraction-v4-thin-lines"


def dense_attempt(identifier, output=OUT):
    _, bundle, sheet_id = identifier.split(":")
    folder = INVENTORY / "chat_bundles/dense64_20260916" / bundle
    manifest_path = folder / "manifest.json"
    manifest = read(manifest_path)
    sheet = next(entry for entry in manifest["sheets"] if entry["id"] == sheet_id)
    receipt_path = folder / "outputs/progress.json"
    receipt = read(receipt_path)["sheets"][sheet_id]
    layout_path = folder / sheet["layout"]
    assert digest(layout_path) == sheet["layout_sha256"]
    assert digest(folder / sheet["reference"]) == sheet["reference_sha256"]
    assert digest(folder / receipt["submitted_prompt_path"]) == receipt["submitted_prompt_sha256"]
    layout = read(layout_path)
    payload = {
        "selected_cells": sheet["cells"],
        "execution_layout": {"canvas_size": layout["reference_size"],
                             "cell_rects": {cell["id"]: cell["reference_rect"] for cell in layout["cells"]}},
        "provenance": "Measured reference rectangles from retained Dense64 layout; no new submission",
        "evidence_hashes": {str(path): digest(path) for path in (
            manifest_path, receipt_path, layout_path, folder / sheet["reference"],
            folder / receipt["submitted_prompt_path"])},
    }
    payload_path = output / "layouts" / (bundle + "__" + sheet_id + ".json")
    payload_path.parent.mkdir(exist_ok=True)
    payload_path.write_text(json.dumps(payload, indent=2) + "\n")
    return {"raw": str(folder / receipt["raw_path"]), "sha256": receipt["raw_sha256"],
            "payload": str(payload_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=["weapons", "jewelry"], default="weapons")
    arguments = parser.parse_args()
    output = OUT if arguments.group == "weapons" else HERE / "jewelry_prepared"
    stats = STATS if arguments.group == "weapons" else {"Gauntlets", "Amulet", "Ring"}
    output.mkdir(exist_ok=True)
    data = catalog()
    queue = queue_module.Queue()
    state_hash = digest(queue.state_path)
    audit = {entry["target_id"]: entry for entry in
             read(INVENTORY / "review/second_pass/replacement_audit.json")["targets"]}
    inventory = {entry["cell_id"]: entry for entry in
                 read(INVENTORY / "review/second_pass/inventory.json")["cells"]}
    names = sorted({item["icon"] for item in data["items"] if item["stat"] in stats and item["icon"]})
    assert len(names) == (332 if arguments.group == "weapons" else 79), "Equipment scope changed"
    existing = {}
    requested = set()
    for name in names:
        asset = data["assets"][name]
        if asset.get("candidate") and f"{output.name}/" not in asset["candidate"]:
            existing[asset["id"]] = asset
        else:
            requested.add(asset["id"])
    attempts = {entry["id"]: entry for entry in queue.state["attempts"]}
    by_attempt = defaultdict(set)
    donors = {}
    required = set()

    def collect(cell):
        if cell in required or cell in existing:
            return
        required.add(cell)
        raw_ids = list(dict.fromkeys(attempt for part in audit[cell]["cells"]
                                    for attempt in part["retained_attempts"]))
        if raw_ids:
            for identifier in raw_ids:
                by_attempt[identifier].add(cell)
        else:
            donor = inventory[cell].get("donor")
            if not donor:
                raise ValueError(f"Neither retained raw nor exact-source donor: {cell}")
            donors[cell] = donor
            collect(donor)

    for cell in sorted(requested):
        collect(cell)
    prepared = defaultdict(list)
    for i, (identifier, cells) in enumerate(sorted(by_attempt.items()), 1):
        attempt = dense_attempt(identifier, output) if identifier.startswith("dense:") else attempts[identifier]
        results = process_attempt(identifier, sorted(cells), attempt, queue, output,
                                  matte_options={"preserve_thin_lines": True, "background_distance": .08})
        for cell, option in results.items():
            option["payload"] = attempt["payload"]
            option["payload_sha256"] = digest(Path(attempt["payload"]))
            assert "empty_extraction" not in option["issues"], f"Empty extraction: {cell}"
            assert "opaque_or_unknown_raw_backing" not in option["issues"], f"Unresolved matte: {cell}"
            prepared[cell].append(option)
        print(f"Prepared sheet {i}/{len(by_attempt)}: {identifier} ({len(cells)} icons)", flush=True)
    for options in prepared.values():
        options.sort(key=lambda option: ("raw_canvas_aspect_changed" in option["issues"],
                                        "insufficient_raw_sampling" in option["issues"],
                                        len(option["registration_flags"]), -min(option["actual_sampling"])))

    def materialize(cell):
        if prepared[cell]:
            return prepared[cell][0]
        if cell in existing:
            asset = existing[cell]
            path = (HERE / unquote(asset["candidate"])).resolve()
            assert digest(path) == asset["candidateHash"]
            return {"path": str(path), "sha256": digest(path), "raw": str(path), "raw_sha256": digest(path),
                    "attempt": "retained-candidate:" + cell, "raw_rect": [0, 0, *Image.open(path).size],
                    "actual_sampling": [2, 2], "issues": [], "registration_flags": {}}
        donor = donors[cell]
        member = queue.members[cell][1]
        donor_member = queue.members[donor][1]
        target = queue.targets[member["target"]]
        donor_target = queue.targets[donor_member["target"]]
        for key in ("source_sha256", "source_rect", "export_region"):
            assert member[key] == donor_member[key], f"Incompatible donor: {cell} ({key})"
        assert target["compositing"] == donor_target["compositing"], cell
        assert digest(ROOT / member["source_path"]) == member["source_sha256"]
        source = materialize(donor)
        path = output / (cell + "__reuse.png")
        shutil.copyfile(source["path"], path)
        measurement = registration.measurements(member, target, path)
        flags = {profile: report["failures"] for profile, report in measurement["profiles"].items()
                 if report["failures"]}
        option = {**source, "cell_id": cell, "attempt": "reuse:" + donor, "path": str(path.resolve()),
                  "sha256": digest(path), "source_sha256": member["source_sha256"],
                  "x2_size": target["x2_size"], "matte": {"method": "exact_native_donor_reuse"},
                  "operation": "Exact-source donor candidate copied onto identical destination canvas.",
                  "issues": sorted(set(source["issues"] + ["reuse_destination_review"] +
                                       (["registration_guard_flag"] if flags else []))),
                  "registration_flags": flags, "visual_approval": False, "reuse_of": donor}
        prepared[cell].append(option)
        return option

    records = []
    for cell in sorted(requested):
        option = materialize(cell)
        member = queue.members[cell][1]
        target = queue.targets[member["target"]]
        records.append({"target_id": cell, "name": target["runtime_name"].lower(), "family": "inventory_items",
                        "selected": option["attempt"], "alternatives": prepared[cell],
                        "status": "prepared_for_visual_review"})
    report = {"schema": "openyamm-inventory-prepared-v1", "recipe": RECIPE, "targets": records,
              "summary": {"scope": len(names), "previous_candidates": len(existing), "prepared": len(records),
                          "raw_extracted": sum(record["target_id"] not in donors for record in records),
                          "donor_copies": sum(record["target_id"] in donors for record in records),
                          "retained_sheets": len(by_attempt),
                          "issues": dict(Counter(issue for record in records
                                                 for issue in record["alternatives"][0]["issues"]))},
              "checkpoint_sha256": state_hash,
              "note": "Prepared candidates only: no generation, canonical acceptance, or runtime installation."}
    assert digest(queue.state_path) == state_hash, "Checkpoint changed during preparation; inspect concurrent work"
    (output / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    # Compact labeled pages for extraction review; retain full-size candidates separately.
    for start in range(0, len(records), 40):
        subset = records[start:start + 40]
        contact = Image.new("RGB", (1200, 1200), (36, 46, 50))
        draw = ImageDraw.Draw(contact)
        for i, record in enumerate(subset):
            option = next(o for o in record["alternatives"] if o["attempt"] == record["selected"])
            with Image.open(option["path"]) as opened:
                im = opened.copy()
            im.thumbnail((138, 210), Image.Resampling.LANCZOS)
            x, y = (i % 8) * 150, (i // 8) * 240
            contact.paste(im, (x + (150 - im.width) // 2, y + 20), im)
            draw.text((x + 3, y + 3), record["name"], fill="white")
        contact.save(output / f"contact_{start // 40 + 1:02}.jpg", quality=92)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
