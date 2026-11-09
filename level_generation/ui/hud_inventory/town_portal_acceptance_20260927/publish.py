"""Publish the explicitly approved MM6 Town Portal artwork, without regenerating it."""

import argparse
import copy
import fcntl
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image


OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
REVIEW = HUD / "town_portal_fixup_review"
CURRENT = HUD / "accepted_icons.json"
METHOD = "user_approved_mm6_town_portal_20260927"
APPROVED = {
    "tpenroth": "7cec0d669f96a73c76a87f605b8673ac108bc7f14e1ff1e7c0f9769e81d7d4ba",
    "tpblckshr": "40aa56e76e2fdfba8a6b1b79e2c12e3c7df6fd779bbf078012057c9a52b82cb3",
    "tpfrhvn": "32cfd191f1043b72d876f80ea8b6aaed663d7d34c3c9c5861282ce1ff857ffba",
    "tpmist": "765459468df6990d9925b39dac85e203c76c97565770965c0ead58f36671c00b",
    "tpsorpig": "2b87173288a2378a254a392b0e6422f4981cadfa33ebe107e023f8dad0e7bd63",
    "tpslvrcv": "dfc22e69ed4d46a6f80b436feb9e5d42b0a9234a8522e13b59bbc33bae14e235",
    "tpwhtc": "ccb7a7d8e2c2fe8e5be746803cd5225c90a085387ab668c8146caec15e602381",
}
sys.path.insert(0, str(HUD))
from queue import Queue, save


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable(path, value):
    if path.exists():
        assert read(path) == value, "Immutable receipt changed: " + str(path)
    else:
        save(path, value)


def copy_verified(source, destination, expected):
    assert sha(source) == expected, source
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert sha(destination) == expected, destination
    else:
        shutil.copyfile(source, destination)
    destination.chmod(0o644)


def check_review():
    map_manifest = read(REVIEW / "mm6/creature_fixup_v3/manifest.json")
    buttons = read(REVIEW / "mm6/buttons_v1/manifest.json")
    evidence = read(REVIEW / "validation.json")
    assert map_manifest["validation"]["result"] == buttons["validation"]["result"] == evidence["result"] == "PASS"
    assert evidence["map_export_sha256"] == map_manifest["export"]["sha256"] == APPROVED["tpenroth"]
    assert evidence["browser"]["hover_states_checked"] == 24
    browser = evidence["browser"]["evidence"]
    assert sha(REVIEW / browser["path"]) == browser["sha256"]
    for item in map_manifest["inputs"] + [map_manifest["master"], map_manifest["export"], buttons["placementSource"]]:
        assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
    assert buttons["background"] == map_manifest["export"]
    selected = {"tpenroth": {
        "path": ROOT / map_manifest["export"]["path"], "kind": "background", "state": "default",
        "rect": {"x": 0, "y": 0, "width": 640, "height": 480},
    }}
    with Image.open(selected["tpenroth"]["path"]) as image:
        assert image.mode == "RGB" and image.size == (1280, 960)
        background = np.asarray(image)
    for item in buttons["records"]:
        name = item["id"]
        assert item["hoverSha256"] == APPROVED[name]
        for field, digest in [("hover", "hoverSha256"), ("default", "defaultSha256")]:
            assert sha(REVIEW / item[field]) == item[digest], name
        mask_path = REVIEW / "mm6/buttons_v1/masks" / (name + ".png")
        assert sha(mask_path) == item["maskSha256"]
        normal = np.asarray(Image.open(REVIEW / item["default"]))
        hover = np.asarray(Image.open(REVIEW / item["hover"]))
        mask = np.asarray(Image.open(mask_path))
        x0, y0, x1, y1 = item["cropBoxX2"]
        r = item["rect"]
        assert [x0, y0, x1, y1] == [2 * r["x"], 2 * r["y"],
                                         2 * (r["x"] + r["width"]), 2 * (r["y"] + r["height"])]
        assert np.array_equal(normal, background[y0:y1, x0:x1])
        assert hover.shape == normal.shape == (2 * r["height"], 2 * r["width"], 3)
        delta = np.any(normal != hover, axis=2)
        assert delta.any() and not np.any(delta & (mask == 0))
        assert not delta[:4].any() and not delta[-4:].any()
        assert not delta[:, :4].any() and not delta[:, -4:].any()
        selected[name] = {"path": REVIEW / item["hover"], "kind": "destination", "state": "highlighted",
                          "rect": r, "label": item["label"], "crop_box_x2": item["cropBoxX2"]}
    assert set(selected) == set(APPROVED)
    return selected, buttons


def prepare(queue):
    selected, buttons = check_review()
    assert sha(CURRENT) == queue.state["accepted_icon_index"]["sha256"]
    previous = read(CURRENT)
    assert previous["count"] == len(previous["records"]) == 9920
    data = json.loads((REVIEW / "data.js").read_text().split(" = ", 1)[1].removesuffix(";\n"))
    assert (REVIEW / data["versions"]["candidate"]["background"]) == selected["tpenroth"]["path"]
    assert data["versions"]["candidate"]["hoverKey"] == "hover"
    assert {i["id"]: (REVIEW / i["hover"], i["rect"]) for i in data["destinations"]} == {
        name: (item["path"], item["rect"]) for name, item in selected.items() if name != "tpenroth"}
    for filename in ["index.html", "review.js", "data.js", "README.md", "validation.json"]:
        copy_verified(REVIEW / filename, OUT / "review_before" / filename, sha(REVIEW / filename))
    provenance_paths = [
        REVIEW / "mm6/creature_fixup_v3/manifest.json", REVIEW / "mm6/buttons_v1/manifest.json",
        REVIEW / "mm6/creature_fixup_v3/master.png", REVIEW / "mm6/creature_fixup_v3/terrain.png",
        REVIEW / "mm6/creature_fixup_v3/gargoyle.png", REVIEW / "mm6/creature_fixup_v3/gargoyle_mask.png",
        REVIEW / "mm6/creature_fixup_v3/terrain_repair_mask.png", REVIEW / "mm6/creature_fixup_v3/browser.png",
        REVIEW / "prepare_buttons.py", REVIEW / "mm6/prepare_creature_fixup.py",
        REVIEW / "mm6/prepare_gargoyle.py", REVIEW / "mm6/prepare_ground.py",
    ]
    provenance_paths += [REVIEW / f"mm6/attempt_{i:02d}" / name
                         for i in range(1, 8) for name in ["tool_args.json", "prompt.txt", "raw.png"]]
    provenance_paths += [REVIEW / f"mm6/attempt_{i:02d}/manifest.json" for i in [1, 2, 3, 5, 6, 7]]
    provenance_paths.append(REVIEW / "mm6/attempt_04/input.json")
    authority = {
        "schema": "openyamm-icon-revision-authority-v1", "method": METHOD,
        "instruction": "this is good, accept it and replace it in icons_x2",
        "scope": {"world": "mm6", "backgrounds": 1, "destination_hover_buttons": 6},
        "selected_view": "Revised map with repaired sharp terrain and registered destination highlights",
        "approved_sha256": APPROVED, "publication": "Exact reviewed PNG bytes; no image processing or generation",
        "review_snapshot": str((OUT / "review_before").relative_to(ROOT)),
        "evidence_hashes": {str(p): sha(p) for p in provenance_paths + list((OUT / "review_before").iterdir())},
    }
    immutable(OUT / "authority.json", authority)
    records = {}
    prior_buttons = {item["id"]: item["previousAcceptance"] for item in buttons["records"]}
    cells = set()
    for name, selected_item in selected.items():
        target = "engine--icons--" + name + ".bmp"
        prior = previous["records"][target]
        contract = queue.targets[target]
        assert len(queue.target_cells[target]) == 1
        cells.update(queue.target_cells[target])
        assert all(queue.accepted(cell) for cell in queue.target_cells[target])
        assert queue.state["staged_targets"][target]["sha256"] == prior["sha256"]
        assert sha(prior["artifact"]) == prior["sha256"]
        assert prior["source_sha256"] == contract["source_sha256"]
        assert prior["runtime_output_path"] == "assets_dev/engine/icons_x2/" + name + ".png"
        assert sha(ROOT / prior["runtime_output_path"]) == prior["sha256"], "Runtime differs from approval: " + target
        if name in prior_buttons:
            assert prior == prior_buttons[name], "Review predecessor changed: " + target
        else:
            assert sha(REVIEW / "mm6/attempt_01/inputs/previous.png") == prior["sha256"]
        source = selected_item["path"]
        with Image.open(source) as image:
            assert image.format == "PNG" and image.mode == "RGB"
            assert list(image.size) == contract["x2_size"] == prior["x2_size"]
        destination = OUT / "accepted/engine/icons_x2" / (name + ".png")
        copy_verified(source, destination, APPROVED[name])
        record = {
            "target": target, "artifact": str(destination), "sha256": APPROVED[name],
            "source": prior["source"], "source_sha256": prior["source_sha256"],
            "source_native_size": contract["native_size"], "x2_size": contract["x2_size"],
            "runtime_output_path": prior["runtime_output_path"],
            "previous_artifact": prior["artifact"], "previous_sha256": prior["sha256"],
            "reviewed_artifact": str(source), "authority": str(OUT / "authority.json"),
            "review_manifest": str(REVIEW / "mm6/buttons_v1/manifest.json"),
            "acceptance": "explicit_user_review_approval", "world": "mm6",
            "kind": selected_item["kind"], "state": selected_item["state"],
            "logical_draw_rect": selected_item["rect"], "placement_changes": False, "canvas_migration": None,
        }
        immutable(OUT / "receipts" / (target + ".json"), record)
        records[target] = record
    assert not any(cells.intersection(r.get("dependency_cells", {}))
                   for cell, r in queue.state["cells"].items() if cell not in cells), "Unexpected external dependency"
    return records, previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with (HUD / "checkpoint/state.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        queue = Queue()
        if (OUT / "accepted.json").exists():
            for target, record in read(OUT / "accepted.json")["records"].items():
                assert read(CURRENT)["records"][target] == record, "Revision superseded; use the current index"
                assert all(queue.accepted(cell) for cell in queue.target_cells[target])
            print("Already accepted. Use deploy_icons.py to verify or deploy the current index.")
            return
        records, previous = prepare(queue)
        summary = {"targets": 7, "backgrounds": 1, "hover_buttons": 6,
                   "changed_runtime_images": sum(r["sha256"] != r["previous_sha256"] for r in records.values()),
                   "previous_index_sha256": sha(CURRENT), "canvas_migrations": 0}
        immutable(OUT / "prepared.json", {"records": records, "summary": summary})
        if not args.apply:
            print(json.dumps({"prepared": True, **summary}, indent=2))
            return
        copy_verified(queue.state_path, OUT / "checkpoint.before.json", sha(queue.state_path))
        copy_verified(CURRENT, OUT / "previous_accepted_index.json", sha(CURRENT))
        preserved_paths = [ROOT / "assets_dev/engine/ui/gameplay/town_portal.yml",
                           ROOT / "assets_dev/engine/data_tables/town_portal_switch.txt",
                           HUD / "expected_targets.json", HUD / "jobs.json"]
        preserved = {str(p.relative_to(ROOT)): sha(p) for p in preserved_paths}
        for target, record in records.items():
            receipt = OUT / "receipts" / (target + ".json")
            evidence = {str(receipt): sha(receipt), str(OUT / "authority.json"): sha(OUT / "authority.json")}
            review = {"authority": str(OUT / "authority.json"), "decision": str(receipt)}
            target_cells = {cell: record["sha256"] for cell in queue.target_cells[target]}
            for cell in target_cells:
                queue.state["cells"][cell] = {
                    "status": "accepted", "artifact": record["artifact"], "sha256": record["sha256"],
                    "acceptance_method": METHOD, "layout_sha256": queue.layout_hash(cell),
                    "dependency_cells": {}, "evidence_hashes": evidence, "review": review,
                }
            queue.state["staged_targets"][target] = {
                "target": target, "source_path": queue.targets[target]["source_path"],
                "source_sha256": record["source_sha256"], "artifact": record["artifact"], "sha256": record["sha256"],
                "native_size": record["source_native_size"], "x2_size": record["x2_size"],
                "canvas_migration": None, "runtime_output_path": record["runtime_output_path"],
                "cells": target_cells, "status": "accepted_staged", "evidence_hashes": evidence, "review": review,
            }
            queue.state["reconstructed_targets"][target] = {
                "target": target, "path": record["artifact"], "sha256": record["sha256"],
                "size": record["x2_size"], "cells": target_cells, "status": "accepted_full_canvas",
            }
            if target in queue.state.get("restoration_inventory", {}):
                queue.state["restoration_inventory"][target].update(
                    status="accepted", canonical_artifact=record["artifact"], canonical_sha256=record["sha256"],
                    acceptance_receipt=str(receipt))
            assert all(queue.accepted(cell) for cell in target_cells)
        current = copy.deepcopy(previous["records"])
        current.update(records)
        publication = {"schema": "openyamm-current-accepted-icons-v1", "count": len(current), "records": current,
                       "latest_revision": str((OUT / "accepted.json").relative_to(ROOT)),
                       "updated_at": datetime.now(timezone.utc).isoformat()}
        save(CURRENT, publication)
        queue.state["accepted_icon_index"] = {"path": str(CURRENT.relative_to(ROOT)), "sha256": sha(CURRENT),
                                              "targets": len(current)}
        save(queue.state_path, queue.state)
        save(queue.storage_root() / "exports/manifest.json", {"targets": list(queue.state["staged_targets"].values())})
        assert all(sha(ROOT / p) == expected for p, expected in preserved.items())
        save(OUT / "accepted.json", {
            "schema": "openyamm-accepted-town-portal-revision-v1", "records": records, "summary": summary,
            "authority": str(OUT / "authority.json"), "published_at": publication["updated_at"],
            "preserved": preserved, "canonical_index_sha256": sha(CURRENT), "ledger_sha256": sha(queue.state_path),
        })
        print(json.dumps({"accepted": True, **summary}, indent=2))


if __name__ == "__main__":
    main()
