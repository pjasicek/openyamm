"""Assemble the complete spell review page from full retained masters and approvals."""

import hashlib
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image


HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
ROOT = HERE.parents[3]
AUDIT = REVIEW / "spell_atlas_audit"
OLD = REVIEW / "spell_foreground_stage"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def web_path(path):
    return Path(os.path.relpath(path, HERE)).as_posix()


def alpha_stats(path):
    pixels = np.asarray(Image.open(path).convert("RGBA"), dtype=int)
    red, green, blue, alpha = [pixels[:, :, channel] for channel in range(4)]
    magenta = ((alpha > 32) & (red > 170) & (blue > 120) & (green < 110)
               & (red > 1.6 * green) & (blue > 1.4 * green))
    return {"transparent_fraction": round(float(np.mean(alpha < 16)), 4),
            "opaque_fraction": round(float(np.mean(alpha > 240)), 4),
            "magenta_pixel_count": int(np.count_nonzero(magenta))}


def main():
    catalog = json.loads((REVIEW / "catalog.js").read_text().split("=", 1)[1].rstrip(" ;\n"))
    originals = sorted((item for item in catalog["items"] if item["category"] == "Spell icons"),
                       key=lambda item: item["name"])
    audit = {item["id"]: item for item in json.loads((AUDIT / "manifest.json").read_text())["items"]}
    alpha = {item["id"]: item for item in json.loads((AUDIT / "alpha_candidates.json").read_text())["items"]}
    paper = {item["id"]: item for item in json.loads((AUDIT / "paper_candidates.json").read_text())["items"]}
    old = json.loads((OLD / "manifest.json").read_text())
    previous = {item["id"]: item for item in old["items"]}
    accepted_air = {item["id"]: item for item in old["items"] if item["kind"] == "existing accepted Air ink"}
    approval_path = REVIEW / "spell_review_acceptance.json"
    approval = json.loads(approval_path.read_text()) if approval_path.is_file() else None
    approved = {item["id"]: item for item in approval["items"]} if approval else {}
    if approval and (len(approval["items"]) != 222 or len(approved) != 222):
        raise ValueError("Spell approval must cover every v2 state exactly once")
    entries = []
    for item in originals:
        identity = item["id"]
        source = (REVIEW / item["original"]).resolve()
        current = (OLD / previous[identity]["current"]).resolve()
        provenance = {}
        raw = None
        prompt = None
        if identity in alpha:
            selected = alpha[identity]
            path = AUDIT / selected["path"]
            kind = "recropped transparent master"
            source_slot = audit[identity]
            raw = ROOT / source_slot["raw"]
            provenance = {"source_master_sha256": source_slot["raw_sha256"],
                          "measured_slot": source_slot["box"], "slot_sha256": source_slot["slot_sha256"],
                          "source_matte": selected["source_matte"], "master_crop": selected["crop"],
                          "shared_scale": selected["shared_scale"],
                          "fitted_size": selected["fitted_size"], "fitted_offset": selected["offset"],
                          "magenta_cleanup": selected["magenta_cleanup"]}
        elif identity in accepted_air:
            selected = accepted_air[identity]
            path = (OLD / selected["candidate"]).resolve()
            kind = "existing accepted Air ink"
            provenance = {"accepted_ink_sha256": selected["candidate_sha256"],
                          "restoration_checkpoint_sha256": selected["parent_sha256"]}
        elif identity in paper:
            selected = paper[identity]
            path = AUDIT / selected["path"]
            kind = "new transparent sheet edit"
            batch_directory = AUDIT / f"paper_batches/{selected['batch']:02d}"
            raw = batch_directory / "raw.png"
            prompt = batch_directory / "submitted_prompt.txt"
            provenance = {"source_master_sha256": audit[identity]["raw_sha256"],
                          "source_master_slot": audit[identity]["box"],
                          "reference_sha256": digest(batch_directory / "restored_reference.png"),
                          "original_reference_sha256": digest(batch_directory / "original_reference.png"),
                          "generated_sheet_sha256": selected["raw_sha256"],
                          "returned_sheet_box": selected["sheet_box"],
                          "returned_art_box": selected["art_box"],
                          "actual_sampling": selected["actual_sampling"],
                          "shared_scale": selected["shared_scale"],
                          "fitted_size": selected["fitted_size"], "fitted_offset": selected["offset"]}
        else:
            raise ValueError(f"No complete transparent master for {item['name']}")
        if not path.is_file():
            raise ValueError(f"Missing stage preview: {path}")
        with Image.open(path) as image:
            if image.size != tuple(item["x2_size"]) or image.mode != "RGBA":
                raise ValueError(f"Wrong 2x RGBA canvas: {item['name']}")
            low_alpha, high_alpha = image.getchannel("A").getextrema()
            if low_alpha != 0 or high_alpha == 0:
                raise ValueError(f"No genuine alpha: {item['name']}")
        if prompt and not prompt.is_file():
            raise ValueError(f"Missing submitted prompt: {prompt}")
        candidate_sha256 = digest(path)
        approved_item = approved.get(identity)
        if approved_item and (approved_item["source_sha256"] != item["source_sha256"]
                              or approved_item["candidate_sha256"] != candidate_sha256):
            raise ValueError(f"Spell approval no longer matches the v2 candidate: {identity}")
        entries.append({
            "id": identity, "name": item["name"], "pair": item["name"][:-1],
            "state": item["name"][-1], "native_size": item["native_size"],
            "x2_size": item["x2_size"], "source_sha256": item["source_sha256"],
            "original": web_path(source), "current": web_path(current),
            "current_sha256": digest(current), "candidate": web_path(path),
            "candidate_sha256": candidate_sha256, "kind": kind,
            "review_approval": {"decision": "approve", "revision": approval["revision"]}
            if approved_item else None,
            "raw": web_path(raw) if raw else None,
            "raw_sha256": digest(raw) if raw else None,
            "prompt": web_path(prompt) if prompt else None,
            "prompt_sha256": digest(prompt) if prompt else None,
            "alpha": alpha_stats(path), "provenance": provenance,
        })
    if len(entries) != 222 or len({entry["id"] for entry in entries}) != 222:
        raise ValueError("Stage must contain all 222 unique spell icon states")
    counts = {kind: sum(item["kind"] == kind for item in entries) for kind in
              ("recropped transparent master", "new transparent sheet edit", "existing accepted Air ink")}
    if counts != {"recropped transparent master": 152, "new transparent sheet edit": 52,
                  "existing accepted Air ink": 18}:
        raise ValueError(f"Unexpected stage mix: {counts}")
    result = {"schema": 2, "stage": "transparent spell foregrounds v2",
              "storage_key": "openyamm-transparent-spell-stage-v2-approved" if approval
              else "openyamm-transparent-spell-stage-v2", "items": entries,
              "summary": {"states": len(entries), "pairs": len(entries) // 2,
                          "new_sheet_edits": counts["new transparent sheet edit"],
                          "accepted_air_ink": counts["existing accepted Air ink"],
                          "retained": counts["recropped transparent master"],
                          "full_master_recrops": counts["recropped transparent master"]}}
    (HERE / "manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "manifest.js").write_text("window.SPELL_STAGE = " + json.dumps(result, separators=(",", ":")) + ";\n")
    print(json.dumps(result["summary"], indent=2))
    print("Saturated magenta pixels:", sum(item["alpha"]["magenta_pixel_count"] for item in entries))


if __name__ == "__main__":
    main()
