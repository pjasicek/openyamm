"""Publish the explicitly approved transparent PC portraits without changing their pixels."""

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
REVIEW = HUD / "pc_transparent_regen_20260927"
CURRENT = HUD / "accepted_icons.json"
METHOD = "user_approved_transparent_pc_portraits_20260927"
APPROVED_MANIFEST_SHA256 = "8f0305c8921224901832cae20c153d0e43c6ad78334439895e9f56a8613ec11b"
sys.path.insert(0, str(HUD))
from queue import Queue, save


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable(path, value):
    if path.exists():
        assert read(path) == value, "Immutable receipt differs: " + str(path)
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


def prepare(queue):
    assert sha(REVIEW / "manifest.json") == APPROVED_MANIFEST_SHA256, "Approved selection changed"
    manifest = read(REVIEW / "manifest.json")
    catalogue = read(REVIEW / "catalogue.json")
    audit = read(REVIEW / "audit.json")
    browser = read(REVIEW / "browser-check.json")
    assert manifest["candidate_frames"] == manifest["expected_frames"] == audit["audited_frames"] == 4032
    assert manifest["native_family_count"] == len(manifest["families"]) == 72
    assert manifest["counts"] == {"reviewed": 144}
    assert audit["technical_checks_pass"] and audit["all_sheets_reviewed"] and not audit["errors"]
    assert not audit["pending_sheets"] and browser["result"] == "PASS" and not browser["errors"]
    assert browser["candidate_frames"] == 4032
    assert sha(CURRENT) == queue.state["accepted_icon_index"]["sha256"]
    previous = read(CURRENT)
    assert previous["count"] == len(previous["records"]) == 9920
    by_runtime = {r["runtime_output_path"]: (target, r) for target, r in previous["records"].items()}
    native = {f["name"]: f for family in catalogue["families"] for f in family["frames"]}
    jobs = {job["id"]: job for job in catalogue["jobs"]}
    snapshots = ["manifest.json", "catalogue.json", "scope_audit.json", "audit.json", "browser-check.json",
                 "browser.png", "index.html", "viewer.js", "run.py", "audit.py", "README.md"]
    for name in snapshots:
        copy_verified(REVIEW / name, OUT / "review_before" / name, sha(REVIEW / name))
    sheet_evidence = {}
    for job_id, job in jobs.items():
        folder = REVIEW / job["path"]
        state = read(folder / "state.json")
        assert state["status"] == "reviewed" and state["visual_review"]["decision"] == "pass", job_id
        assert not state["flagged_frames"], job_id
        attempt = folder / state["attempt"]
        report = read(attempt / "report.json")
        assert sha(attempt / "raw.png") == state["raw_sha256"] == report["raw_sha256"], job_id
        assert sha(attempt / "prompt.txt") == state["prompt_sha256"], job_id
        assert sha(folder / "reference.png") == state["reference_sha256"], job_id
        assert [f["number"] for f in report["frames"]] == job["frames"], job_id
        for path in [folder / "state.json", attempt / "report.json"]:
            copy_verified(path, OUT / "review_before/sheets" / job_id / path.name, sha(path))
        sheet_evidence[job_id] = {
            "raw": str(attempt / "raw.png"), "raw_sha256": state["raw_sha256"],
            "prompt": str(attempt / "prompt.txt"), "prompt_sha256": state["prompt_sha256"],
            "reference": str(folder / "reference.png"), "reference_sha256": state["reference_sha256"],
            "report": str(OUT / "review_before/sheets" / job_id / "report.json"),
            "report_sha256": sha(attempt / "report.json"),
            "scope_change": state.get("scope_change"),
        }
    authority = {
        "schema": "openyamm-icon-revision-authority-v1", "method": METHOD,
        "instruction": 'OK this is good I like it, accept it, replace it as accepted "solution" and put it all to icons_2x',
        "earlier_scope_instruction": 'use "less" injury there then',
        "scope": {"families": 72, "portraits": 4032, "sheets": 144},
        "selected_view": "Aligned transparent portraits with default global offset [0, 0]",
        "publication": "Exact reviewed 118x158 RGBA PNG bytes; no new image processing or generation",
        "runtime_root": "assets_dev/engine/icons_x2",
        "approved_manifest_sha256": APPROVED_MANIFEST_SHA256,
        "review_snapshot": str((OUT / "review_before").relative_to(ROOT)),
        "evidence_hashes": {str(OUT / "review_before" / name): sha(OUT / "review_before" / name)
                            for name in snapshots},
        "sheets": sheet_evidence,
    }
    immutable(OUT / "authority.json", authority)
    records = {}
    for family in manifest["families"]:
        assert [f["number"] for f in family["frames"]] == list(range(1, 57)), family["id"]
        seed_hash = family["frames"][0]["sha256"]
        for frame in family["frames"]:
            original = native[frame["name"]]
            target, prior = by_runtime[original["runtime_path"]]
            contract = queue.targets[target]
            assert target not in records and len(queue.target_cells[target]) == 1, target
            assert prior["sha256"] == original["accepted_sha256"], target
            assert sha(prior["artifact"]) == sha(ROOT / prior["runtime_output_path"]) == prior["sha256"], target
            assert prior["source_sha256"] == original["source_sha256"] == contract["source_sha256"], target
            assert sha(ROOT / original["source"]) == original["source_sha256"], target
            assert prior["x2_size"] == contract["x2_size"] == [118, 158], target
            assert contract["native_size"] == [59, 79], target
            assert queue.state["staged_targets"][target]["sha256"] == prior["sha256"], target
            assert all(queue.accepted(cell) for cell in queue.target_cells[target]), target
            source = REVIEW / frame["candidate"]
            assert not frame["issues"] and sha(source) == frame["sha256"], target
            with Image.open(source) as image:
                assert image.format == "PNG" and image.mode == "RGBA" and image.size == (118, 158), target
                alpha = np.asarray(image.getchannel("A"))
                assert int(alpha.max()) >= 240 and float(np.mean(alpha == 0)) >= .08, target
            runtime = "assets_dev/engine/icons_x2/" + frame["name"]
            assert runtime == prior["runtime_output_path"] and frame["name"] == frame["name"].lower(), target
            destination = OUT / "accepted/engine/icons_x2" / frame["name"]
            copy_verified(source, destination, frame["sha256"])
            record = {
                "target": target, "artifact": str(destination), "sha256": frame["sha256"],
                "source": prior["source"], "source_archive": original["source"],
                "source_sha256": original["source_sha256"], "source_native_size": [59, 79], "x2_size": [118, 158],
                "runtime_output_path": runtime, "previous_artifact": prior["artifact"],
                "previous_sha256": prior["sha256"], "reviewed_artifact": str(source),
                "authority": str(OUT / "authority.json"), "acceptance": "explicit_user_review_approval",
                "family": family["id"], "frame": frame["number"], "sheet": family["id"] + "_" + frame["sheet"],
                "family_seed_sha256": seed_hash, "global_offset": [0, 0], "canvas_migration": None,
                "alpha_policy": "Imagegen alpha preserved; transparent backing replaces the prior opaque panel",
            }
            immutable(OUT / "receipts" / (target + ".json"), record)
            records[target] = record
    cells = {cell for target in records for cell in queue.target_cells[target]}
    assert len(records) == len(cells) == 4032
    assert not any(cells.intersection(r.get("dependency_cells", {}))
                   for cell, r in queue.state["cells"].items() if cell not in cells), "External dependency found"
    return records, previous


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with (HUD / "checkpoint/state.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        queue = Queue()
        if (OUT / "accepted.json").exists():
            current = read(CURRENT)
            for target, record in read(OUT / "accepted.json")["records"].items():
                assert current["records"][target] == record, "Revision superseded; use the current index"
                assert all(queue.accepted(cell) for cell in queue.target_cells[target]), target
            print("Already accepted. Use deploy_icons.py to verify or deploy the current index.")
            return
        records, previous = prepare(queue)
        summary = {"families": 72, "targets": len(records), "accepted_cells_updated": 4032,
                   "changed_runtime_images": sum(r["sha256"] != r["previous_sha256"] for r in records.values()),
                   "canvas_migrations": 0, "global_offset": [0, 0], "previous_index_sha256": sha(CURRENT)}
        immutable(OUT / "prepared.json", {"records": records, "summary": summary})
        if not args.apply:
            print(json.dumps({"prepared": True, **summary}, indent=2))
            return
        copy_verified(queue.state_path, OUT / "checkpoint.before.json", sha(queue.state_path))
        copy_verified(CURRENT, OUT / "previous_accepted_index.json", sha(CURRENT))
        preserved_paths = [HUD / "expected_targets.json", HUD / "jobs.json",
                           HUD / "finalization_20260926/placements.json",
                           ROOT / "assets_dev/engine/data_tables/item_visuals.txt",
                           ROOT / "assets_dev/engine/data_tables/character_data.txt",
                           ROOT / "assets_dev/engine/icon_packages.txt"]
        preserved = {str(p.relative_to(ROOT)): sha(p) for p in preserved_paths}
        for target, record in records.items():
            receipt = OUT / "receipts" / (target + ".json")
            evidence = {str(receipt): sha(receipt), str(OUT / "authority.json"): sha(OUT / "authority.json")}
            review = {"authority": str(OUT / "authority.json"), "decision": str(receipt),
                      "notes": "User accepted the complete aligned transparent portrait set from the browser."}
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
                "native_size": [59, 79], "x2_size": [118, 158], "runtime_output_path": record["runtime_output_path"],
                "cells": target_cells, "status": "accepted_staged", "evidence_hashes": evidence, "review": review,
            }
            queue.state["reconstructed_targets"][target] = {
                "target": target, "path": record["artifact"], "sha256": record["sha256"],
                "size": [118, 158], "cells": target_cells, "status": "accepted_full_canvas",
            }
            if target in queue.state.get("restoration_inventory", {}):
                queue.state["restoration_inventory"][target].update(
                    status="accepted", canonical_artifact=record["artifact"], canonical_sha256=record["sha256"],
                    acceptance_receipt=str(receipt))
        assert all(queue.accepted(cell) for target in records for cell in queue.target_cells[target])
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
        save(OUT / "accepted.json", {
            "schema": "openyamm-accepted-pc-portrait-revision-v1", "records": records, "summary": summary,
            "authority": str(OUT / "authority.json"), "published_at": publication["updated_at"],
            "preserved": preserved, "canonical_index_sha256": sha(CURRENT), "ledger_sha256": sha(queue.state_path),
        })
        print(json.dumps({"accepted": True, **summary}, indent=2))


if __name__ == "__main__":
    main()
