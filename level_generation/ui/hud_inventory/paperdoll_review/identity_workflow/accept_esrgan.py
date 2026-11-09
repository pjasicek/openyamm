"""Import the user's explicit 2026-09-24 acceptance of native-based ESRGAN dolls.

This is a scoped acceptance migration, not fabricated imagegen visual-review evidence.
It preserves other checkpoint entries and never installs runtime assets.
"""

import argparse
import fcntl
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
INVENTORY = REVIEW.parent
ROOT = HERE.parents[4]
BASELINE = HERE / "esrgan_baseline"
ACCEPTANCE = HERE / "esrgan_acceptance_20260924"
METHOD = "user_accepted_native_realesrgan"
PART_FIELDS = ("body", "leftClosed", "leftHold", "leftOpen", "rightFingers", "rightOpen", "rightHold")
sys.path.insert(0, str(INVENTORY))
from queue import Queue, digest, save  # noqa: E402


def validate(queue):
    data = json.loads((REVIEW / "catalog.js").read_text().split(" = ", 1)[1].removesuffix(";\n"))
    manifest = json.loads((BASELINE / "manifest.json").read_text())
    names = {person[field] for person in data["characters"] for field in PART_FIELDS
             if person[field] and person[field] in data["assets"]}
    assert names == set(manifest["items"]), "Baseline does not cover all available body/limb references"
    assert len(names) == 466, "Acceptance scope changed; review explicitly"
    for key, path in (
        ("runner_sha256", ROOT / "tools/upscaling/realesrgan-ncnn-vulkan"),
        ("model_param_sha256", ROOT / "tools/upscaling/models/realesrgan-x4plus.param"),
        ("model_bin_sha256", ROOT / "tools/upscaling/models/realesrgan-x4plus.bin"),
    ):
        assert digest(path) == manifest[key], f"Inference provenance changed: {path}"
    records = {}
    for name in sorted(names):
        asset = data["assets"][name]
        record = manifest["items"][name]
        cell = asset["id"]
        member = queue.members[cell][1]
        target = queue.targets[member["target"]]
        assert target["treatment"] == "paperdoll_parts"
        assert queue.target_cells[target["id"]] == [cell], "Expected a complete single-cell sprite"
        assert cell not in queue.state.get("user_excluded_targets", {})
        assert digest(ROOT / asset["source"]) == asset["sourceHash"] == record["source_sha256"]
        native_path = REVIEW / unquote(asset["native"])
        assert digest(native_path) == record["native_preview_sha256"]
        for key in ("input_rgb", "raw_bordered_x4", "master_rgb_x4", "candidate_x2"):
            assert digest(BASELINE / record[key]) == record[key + "_sha256"], f"Changed {name}: {key}"
        artifact = BASELINE / record["candidate_x2"]
        with Image.open(artifact) as image, Image.open(native_path) as native:
            assert image.mode == "RGBA"
            assert list(image.size) == target["x2_size"] == member["export_region"][2:]
            assert image.size == (native.width * 2, native.height * 2)
            alpha = np.asarray(image.getchannel("A"))
            native_alpha = np.asarray(native.getchannel("A").resize(image.size, Image.Resampling.NEAREST))
            assert alpha.any()
            outside = int(np.count_nonzero((alpha > 0) & (native_alpha == 0)))
            assert outside == 0, f"Outside native silhouette: {name}"
        previous = queue.state["cells"].get(cell)
        assert previous is None or (previous.get("acceptance_method") == METHOD
                                   and previous["sha256"] == record["candidate_x2_sha256"]), cell
        records[cell] = {"name": name, "source": asset["source"], "source_sha256": asset["sourceHash"],
                         "artifact": str(artifact), "sha256": digest(artifact), "size": target["x2_size"],
                         "outside_native_pixels": outside}
    return data, manifest, records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Record the already-authorized user decision")
    args = parser.parse_args()
    with (INVENTORY / "checkpoint/state.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        queue = Queue()
        data, manifest, records = validate(queue)
        if not args.apply:
            print(json.dumps({"validated": len(records), "already_accepted": sum(queue.accepted(c) for c in records)}))
            return
        if all(queue.accepted(c) for c in records):
            print("All 466 ESRGAN bodies and limbs are already accepted; unchanged.")
            return
        ACCEPTANCE.mkdir(exist_ok=True)
        decision_path = ACCEPTANCE / "decision.json"
        assert not decision_path.exists(), "Existing incomplete acceptance: inspect before retrying"
        decision = {
            "schema": "openyamm-paperdoll-user-acceptance-v1", "date": "2026-09-24",
            "status": "accepted", "method": METHOD, "authority": "Explicit user instruction in this session",
            "user_instruction": "I want to use/accept the real-esrgan for ALL the paperdolls + all their limbs. "
                                "This is going to be my decision, restoring it to faithful way would be way "
                                "too much work above my budget. It can stay as good to-be-done work for the future.",
            "scope": "All 75 available doll bodies and 391 limb/hand sprites in the retained baseline",
            "quality_policy": "User accepts native-based ESRGAN improvement; painted restoration is deferred.",
            "placement": "Original logical canvases, table offsets, cut lines and draw order are unchanged.",
            "not_included": ["Equipment", "Avatar portraits", "Separate backgrounds", "Head/beard metadata",
                             "Missing original art", "Runtime installation"],
            "checkpoint_before_sha256": digest(queue.state_path),
            "source_manifest_sha256": digest(BASELINE / "manifest.json"),
            "placement_source_hashes": {path: digest(ROOT / path) for path in data["sources"].values()},
            "artifacts": records,
        }
        save(decision_path, decision)
        shutil.copy2(BASELINE / "manifest.json", ACCEPTANCE / "baseline_manifest.json")
        # Frozen evidence avoids invalidating acceptance when a comparison viewer is rebuilt.
        evidence = {str(path): digest(path) for path in (decision_path, ACCEPTANCE / "baseline_manifest.json")}
        destination = queue.storage_root() / "accepted/paperdoll_esrgan_20260924"
        destination.mkdir(parents=True, exist_ok=True)
        for cell, record in records.items():
            output = destination / (cell + ".png")
            if output.exists():
                assert digest(output) == record["sha256"], f"Conflicting accepted file: {output}"
            else:
                shutil.copy2(record["artifact"], output)
            queue.state["cells"][cell] = {
                "status": "accepted", "artifact": str(output), "sha256": record["sha256"],
                "acceptance_method": METHOD,
                "review": {"authority": "explicit_user_acceptance", "decision": str(decision_path),
                           "notes": decision["quality_policy"]},
                "evidence_hashes": evidence, "dependency_cells": {}, "layout_sha256": queue.layout_hash(cell),
            }
        save(queue.state_path, queue.state)
        assert all(queue.accepted(cell) for cell in records)
        print(json.dumps({"accepted": len(records), "decision": str(decision_path), "installed": False}, indent=2))


if __name__ == "__main__":
    main()
