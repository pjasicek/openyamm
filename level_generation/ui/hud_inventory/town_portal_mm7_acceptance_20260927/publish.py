"""Publish the explicitly approved MM7 Town Portal artwork, without regenerating it."""

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
REVIEW = HUD / "town_portal_fixup_review/mm7"
CURRENT = HUD / "accepted_icons.json"
METHOD = "user_approved_mm7_town_portal_20260927"
APPROVED = {
    "antagrich": "279aa0b79797f3346814b39e5bc2c421f9d64f30253aca1f302b1292087845e7",
    "tpharmon": "2c036fc9895a34de435acd2745b5174546a2afb0f53eddc810f9400525f575bb",
    "tpavli": "bf331e5ec0b4f35c5715a775027d0bc8c8d3751fcf378ed8a1cd00241603c473",
    "tpwarl": "edc81571ab6e98821dba21ca57b38cd75cd6bda7264cf8c180bb430dbf9f7d70",
    "tpisl": "9cc4dee98217621547d7c79e73ade2ac9935f211dda7f6ae6abaca8c367f6ea1",
    "tpheav": "b38c1421694b66cb0c68c52cd6c178817fd03ce9125c01953527e92b0abc017f",
    "tpdeja": "dbd78056195b99580b677d04de91a9eb6ff1e7a2c0f4e43b57c06d917cd2517d"
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
    map_manifest = read(REVIEW / "attempt_01/manifest.json")
    buttons = read(REVIEW / "buttons_v1/manifest.json")
    evidence = read(REVIEW / "buttons_v1/browser_validation.json")
    assert buttons["validation"]["result"] == evidence["result"] == "PASS"
    assert buttons["background"]["sha256"] == map_manifest["export"]["sha256"] == APPROVED["antagrich"]
    assert evidence["destinations"] == 6
    for key in ["exactExportedPatchPixels", "unchangedSurroundingMap", "exactHoverReset",
                "logicalHitAreas", "keyboardFocusAndClick"]:
        assert evidence[key], key
    referenced = map_manifest["inputs"] + evidence["captures"] + [evidence["contactSheet"]]
    referenced += [map_manifest[key] for key in ["raw", "export", "input_record", "prompt", "tool_args",
                                               "generation", "validation"]]
    referenced += [buttons[key] for key in ["background", "placementSource", "layoutSource", "recipeSource"]]
    for item in referenced:
        assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
    assert buttons["background"]["path"] == map_manifest["export"]["path"]
    assert buttons["recipe"]["generationUsed"] is False
    selected = {"antagrich": {
        "path": ROOT / map_manifest["export"]["path"], "kind": "background", "state": "default",
        "rect": {"x": 0, "y": 0, "width": 640, "height": 480},
    }}
    with Image.open(selected["antagrich"]["path"]) as image:
        assert image.mode == "RGB" and image.size == (1280, 960)
        background = np.asarray(image)
    for item in buttons["records"]:
        name = item["id"]
        assert item["exports"]["hover"]["sha256"] == APPROVED[name]
        for export in item["exports"].values():
            assert sha(ROOT / export["path"]) == export["sha256"], export["path"]
        assert sha(ROOT / item["originalSource"]["path"]) == item["originalSource"]["sha256"]
        mask_path = ROOT / item["exports"]["masks"]["path"]
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
    assert (REVIEW / data["versions"]["candidate"]["background"]) == selected["antagrich"]["path"]
    assert data["versions"]["candidate"]["hoverKey"] == "hover"
    assert {i["id"]: (REVIEW / i["hover"], i["rect"]) for i in data["destinations"]} == {
        name: (item["path"], item["rect"]) for name, item in selected.items() if name != "antagrich"}
    for item in read(REVIEW / "buttons_v1/browser_validation.json")["viewerFiles"]:
        assert sha(ROOT / item["path"]) == item["sha256"], "Viewer changed since button review"
    for filename in ["index.html", "review.js", "data.js", "README.md",
                     "buttons_v1/README.md", "buttons_v1/browser_validation.json"]:
        copy_verified(REVIEW / filename, OUT / "review_before" / filename, sha(REVIEW / filename))
    provenance_paths = [REVIEW / "prepare_buttons.py", OUT / "publish.py",
                        ROOT / queue.state["input_reconciliation"]["path"]]
    provenance_paths += sorted((REVIEW / "attempt_01").rglob("*.json"))
    provenance_paths += sorted((REVIEW / "attempt_01").rglob("*.png"))
    provenance_paths += [REVIEW / "attempt_01/prompt.txt"]
    provenance_paths += sorted((REVIEW / "buttons_v1").rglob("*.json"))
    provenance_paths += sorted((REVIEW / "buttons_v1").rglob("*.png"))
    snapshots = [p for p in (OUT / "review_before").rglob("*") if p.is_file()]
    authority = {
        "schema": "openyamm-icon-revision-authority-v1", "method": METHOD,
        "instruction": "OK accept it and put it to icons_x2",
        "scope": {"world": "mm7", "backgrounds": 1, "destination_hover_buttons": 6},
        "selected_view": "Regenerated MM7 map with six matching destination highlights from the browser review",
        "approved_sha256": APPROVED, "publication": "Exact reviewed PNG bytes; no image processing or generation",
        "review_snapshot": str((OUT / "review_before").relative_to(ROOT)),
        "evidence_hashes": {str(p): sha(p) for p in provenance_paths + snapshots},
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
            assert sha(REVIEW / "attempt_01/inputs/current.png") == prior["sha256"]
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
            "review_manifest": str(REVIEW / "buttons_v1/manifest.json"),
            "acceptance": "explicit_user_review_approval", "world": "mm7",
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
                           HUD / "expected_targets.json", HUD / "jobs.json",
                           ROOT / "assets_dev/engine/data_tables/chest_data.txt",
                           ROOT / "assets_dev/engine/ui/gameplay/character.yml",
                           ROOT / "assets_dev/engine/ui/gameplay/chest.yml"]
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
