"""Publish the explicitly approved spellbook browser revision; never regenerate art.

Use --apply to update the live ledger/index after all scope and artifact checks.
Deployment uses the repository's current-index deploy_icons.py command afterward.
"""

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
import yaml
from PIL import Image


OUT = Path(__file__).resolve().parent
HUD = OUT.parent
ROOT = HUD.parents[2]
REVISION = "e1c5265ae12b808b"
REVIEW = HUD / "spellbook_fixup_review/revisions" / REVISION
CURRENT = HUD / "accepted_icons.json"
METHOD = "user_approved_spellbook_fixup_20260927"
EXPECTED_MIGRATIONS = {
    "sbf10b": ([304, 248], [308, 248]),
    "sba05b": ([252, 274], [250, 274]),
    "sbe03b": ([268, 296], [266, 296]),
    "sbe08b": ([262, 266], [260, 266]),
    "sbm11b": ([288, 304], [284, 304]),
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


def bindings(review):
    result = []
    for school in review["schools"]:
        result.append((school["id"], "page", "default", school["installed"], school["proposed"], school["rect"]))
        for state in ["default", "pressed"]:
            button = school["button"]
            result.append((button["id"], "school", state, button["states"][state],
                           button["proposedStates"][state], button["rect"]))
        for spell in school["spells"]:
            normal = spell.get("opacityTrial", {}).get("normal", spell["proposedNormal"])
            highlighted = spell.get("opacityTrial", {}).get("highlighted", spell["canonical"])
            for state, art in [("default", normal), ("highlighted", highlighted)]:
                result.append((spell["id"], "spell", state, spell["states"][state], art, spell["rect"]))
    assert len(result) == 258
    return result


def prepare(queue):
    review = read(REVIEW / "manifest.json")
    assert review["revision"] == REVISION
    for evidence in ["browser_checks.json", "asset_checks.json"]:
        report = read(REVIEW / "evidence" / evidence)
        assert report["result"] == "PASS" and report["revision"] == REVISION
    assert sha(CURRENT) == queue.state["accepted_icon_index"]["sha256"]
    previous = read(CURRENT)
    assert previous["count"] == len(previous["records"]) == 9920
    layout_path = ROOT / review["sourceLayout"]
    assert sha(layout_path) == review["sources"][review["sourceLayout"]]
    elements = {element["id"]: element for element in yaml.safe_load(layout_path.read_text())["elements"][0]["children"]}
    authority = {
        "schema": "openyamm-icon-revision-authority-v1", "method": METHOD,
        "instruction": 'OK so "accept", ledger etc. your work - replace the latest accepted ones '
                       '(spellbooks, spell icons, spell pages icons) with these ones we have in the browser. '
                       'also put it to the engine/icons_x2 afterward.',
        "scope": {"book_pages": 12, "spell_pairs": 111, "spell_states": 222, "school_bookmark_states": 24},
        "review_revision": REVISION, "review_manifest": str((REVIEW / "manifest.json").relative_to(ROOT)),
        "review_manifest_sha256": sha(REVIEW / "manifest.json"),
        "selected_view": "Proposed artwork with restored Air strength",
        "publication": "Exact reviewed PNG bytes; no regeneration, recolouring, resampling or new image generation",
        "canvas_policy": "Five normal-state exports adopt their highlighted partner's reviewed canvas. "
                         "Native source contracts remain historical; all YAML draw and hit rectangles are unchanged.",
        "evidence": {str((REVIEW / "evidence" / name).relative_to(ROOT)): sha(REVIEW / "evidence" / name)
                     for name in ["browser_checks.json", "asset_checks.json", "review.png"]},
    }
    immutable(OUT / "authority.json", authority)
    records, cells, migrations = {}, {}, {}
    for element_id, kind, state, original, selected, rect in bindings(review):
        name = Path(original["path"]).stem
        target = "engine--icons--" + name + ".bmp"
        assert target not in records, target
        prior = previous["records"][target]
        contract = queue.targets[target]
        assert len(queue.target_cells[target]) == 1, target
        cell = queue.target_cells[target][0]
        assert queue.accepted(cell), cell
        assert queue.state["staged_targets"][target]["sha256"] == prior["sha256"]
        assert sha(prior["artifact"]) == prior["sha256"]
        assert prior["source_sha256"] == contract["source_sha256"]
        assert prior["runtime_output_path"] == "assets_dev/engine/icons_x2/" + name + ".png"
        assert sha(ROOT / prior["runtime_output_path"]) == prior["sha256"], "Runtime differs from latest approval: " + target
        assert sha(REVIEW / original["path"]) == original["sha256"]
        assert elements[element_id]["asset"][state].lower() == name
        assert elements[element_id]["width"] == rect["width"] and elements[element_id]["height"] == rect["height"]
        selected_path = REVIEW / selected["path"]
        assert sha(selected_path) == selected["sha256"]
        with Image.open(selected_path) as image:
            assert image.format == "PNG" and image.mode == "RGBA", target
            size = list(image.size)
        migration = None
        if size != contract["x2_size"]:
            assert name in EXPECTED_MIGRATIONS and kind == "spell" and state == "default", target
            assert (contract["x2_size"], size) == EXPECTED_MIGRATIONS[name]
            assert {usage["element"] for usage in contract["usages"]} == {element_id}
            migration = {
                "target": target, "source_native_size": contract["native_size"],
                "previous_export_size": contract["x2_size"], "approved_export_size": size,
                "paired_highlighted_asset": elements[element_id]["asset"]["highlighted"].lower(),
                "element": element_id, "unchanged_logical_draw_rect": rect,
                "reason": "Both states use identical geometry and sampling, exactly as approved in the browser.",
            }
            migrations[target] = migration
        destination = OUT / "accepted/engine/icons_x2" / (name + ".png")
        copy_verified(selected_path, destination, selected["sha256"])
        record = {
            "target": target, "artifact": str(destination), "sha256": selected["sha256"],
            "source": prior["source"], "source_sha256": prior["source_sha256"],
            "source_native_size": contract["native_size"], "x2_size": size,
            "runtime_output_path": prior["runtime_output_path"],
            "previous_artifact": prior["artifact"], "previous_sha256": prior["sha256"],
            "reviewed_artifact": str(selected_path), "review_manifest": str(REVIEW / "manifest.json"),
            "review_revision": REVISION, "review_target": element_id, "kind": kind, "state": state,
            "authority": str(OUT / "authority.json"), "acceptance": "explicit_user_browser_revision_approval",
            "logical_draw_rect": rect, "placement_changes": False, "canvas_migration": migration,
        }
        receipt = OUT / "receipts" / (target + ".json")
        immutable(receipt, record)
        records[target] = record
        cells[cell] = {"artifact": str(destination), "sha256": selected["sha256"], "receipt": str(receipt)}
    assert len(migrations) == 5
    immutable(OUT / "canvas_migrations.json", {
        "schema": "openyamm-approved-export-canvas-migration-v1", "review_revision": REVISION,
        "native_contract_manifest": str((HUD / "expected_targets.json").relative_to(ROOT)),
        "native_contract_sha256": sha(HUD / "expected_targets.json"), "records": migrations,
    })
    for school in review["schools"]:
        for spell in school["spells"]:
            pair = []
            for state in ["default", "highlighted"]:
                target = "engine--icons--" + Path(spell["states"][state]["path"]).stem + ".bmp"
                pair.append(np.asarray(Image.open(records[target]["artifact"])))
            assert pair[0].shape == pair[1].shape and np.array_equal(pair[0][:, :, 3], pair[1][:, :, 3])
    summary = {"targets": 258, "book_pages": 12, "spell_pairs": 111, "school_bookmark_states": 24,
               "changed_runtime_images": sum(record["sha256"] != record["previous_sha256"] for record in records.values()),
               "canvas_migrations": 5, "air_pairs_with_restored_opacity": 9,
               "previous_index_sha256": sha(CURRENT), "review_revision": REVISION}
    return records, cells, previous, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with (HUD / "checkpoint/state.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        queue = Queue()
        if (OUT / "accepted.json").exists():
            accepted = read(OUT / "accepted.json")
            current = read(CURRENT)["records"]
            for target, record in accepted["records"].items():
                assert current[target] == record, "Revision was superseded; deploy only the current accepted index"
                assert queue.state["staged_targets"][target]["sha256"] == record["sha256"]
                assert all(queue.accepted(cell) for cell in queue.target_cells[target])
            print("Already accepted. Use deploy_icons.py to verify or deploy the current index.")
            return
        records, cells, previous, summary = prepare(queue)
        immutable(OUT / "prepared.json", {"records": records, "cells": cells, "summary": summary})
        if not args.apply:
            print(json.dumps({"prepared": True, **summary}, indent=2))
            return
        copy_verified(queue.state_path, OUT / "checkpoint.before.json", sha(queue.state_path))
        copy_verified(CURRENT, OUT / "previous_accepted_index.json", sha(CURRENT))
        preserved_paths = [ROOT / "assets_dev/engine/ui/gameplay/spellbook.yml",
                           ROOT / "assets_dev/engine/data_tables/item_visuals.txt",
                           HUD / "expected_targets.json", HUD / "jobs.json"]
        preserved = {str(path.relative_to(ROOT)): sha(path) for path in preserved_paths}
        old_cells = copy.deepcopy(queue.state["cells"])
        for cell, new in cells.items():
            receipt = Path(new["receipt"])
            queue.state["cells"][cell] = {
                "status": "accepted", "artifact": new["artifact"], "sha256": new["sha256"],
                "acceptance_method": METHOD, "layout_sha256": queue.layout_hash(cell), "dependency_cells": {},
                "evidence_hashes": {str(receipt): sha(receipt), str(OUT / "authority.json"): sha(OUT / "authority.json")},
                "review": {"authority": str(OUT / "authority.json"), "decision": str(receipt),
                           "notes": "Exact accepted browser revision, including restored Air strength and shared bookmarks."},
            }
        frozen = []
        for cell, record in queue.state["cells"].items():
            if cell in cells:
                continue
            for dependency, expected in list(record.get("dependency_cells", {}).items()):
                if dependency not in cells or cells[dependency]["sha256"] == expected:
                    continue
                old = old_cells[dependency]
                assert old["sha256"] == expected and sha(old["artifact"]) == expected
                snapshot = {"cell": dependency, "sha256": expected, "artifact": old["artifact"],
                            "reason": "Preserve the exact reference version used by the earlier accepted drawing"}
                record.setdefault("reference_revision_history", []).append(snapshot)
                record.setdefault("evidence_hashes", {})[old["artifact"]] = expected
                del record["dependency_cells"][dependency]
                frozen.append({"dependent": cell, **snapshot})
        for target, record in records.items():
            contract = queue.targets[target]
            receipt = OUT / "receipts" / (target + ".json")
            target_cells = {cell: queue.state["cells"][cell]["sha256"] for cell in queue.target_cells[target]}
            queue.state["staged_targets"][target] = {
                "target": target, "source_path": contract["source_path"], "source_sha256": record["source_sha256"],
                "artifact": record["artifact"], "sha256": record["sha256"],
                "native_size": contract["native_size"], "x2_size": record["x2_size"],
                "canvas_migration": record["canvas_migration"], "runtime_output_path": record["runtime_output_path"],
                "cells": target_cells, "status": "accepted_staged",
                "evidence_hashes": {str(receipt): sha(receipt), str(OUT / "authority.json"): sha(OUT / "authority.json")},
                "review": {"authority": str(OUT / "authority.json"), "decision": str(receipt)},
            }
            queue.state["reconstructed_targets"][target] = {
                "target": target, "path": record["artifact"], "sha256": record["sha256"],
                "size": record["x2_size"], "cells": target_cells, "status": "accepted_full_canvas",
            }
            if target in queue.state.get("restoration_inventory", {}):
                queue.state["restoration_inventory"][target].update(
                    status="accepted", canonical_artifact=record["artifact"], canonical_sha256=record["sha256"],
                    acceptance_receipt=str(receipt))
        assert all(queue.accepted(cell) for cell in cells)
        assert all(queue.accepted(record["dependent"]) for record in frozen)
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
        assert all(sha(ROOT / path) == expected for path, expected in preserved.items())
        accepted = {"schema": "openyamm-accepted-spellbook-revision-v1", "records": records, "summary": summary,
                    "authority": str(OUT / "authority.json"), "published_at": publication["updated_at"],
                    "preserved": preserved, "reference_revision_migrations": frozen,
                    "canonical_index_sha256": sha(CURRENT), "ledger_sha256": sha(queue.state_path)}
        save(OUT / "accepted.json", accepted)
        print(json.dumps({"accepted": True, **summary}, indent=2))


if __name__ == "__main__":
    main()
