#!/usr/bin/env python3
"""Build six unconfirmed UI/icon slices from fitted, hash-bound review art."""

from __future__ import annotations

import hashlib
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageDraw


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / "level_generation/ui/hud_inventory"
MM8_REVIEW = ROOT / "level_generation/ui/mm8_art_review"
sys.path.insert(0, str(HUD))
from freeze_targets import rendered  # noqa: E402


CATEGORIES = {
    "inventory_items": "Inventory items",
    "ui_animation_family": "UI animation frames",
    "ui_frame_or_panel": "Frames and panels",
    "ui_state_set": "Button and control states",
    "ui_background": "UI backgrounds and loading images",
    "legacy_ui_art": "Other referenced UI art",
}
EXPECTED_COUNTS = {
    "inventory_items": 770,
    "ui_animation_family": 473,
    "ui_frame_or_panel": 20,
    "ui_state_set": 75,
    "ui_background": 87,
    "legacy_ui_art": 293,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def browser_path(path: Path) -> str:
    return Path(os.path.relpath(path, HERE)).as_posix()


def source_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path if path.is_file() else None


def originals(target: dict) -> Path:
    source = ROOT / target["source_path"]
    if sha256(source) != target["source_sha256"]:
        raise ValueError(f"Changed native source: {source}")
    output = HERE / "originals" / (target["id"] + ".png")
    if not output.is_file() or output.stat().st_mtime_ns < source.stat().st_mtime_ns:
        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as native:
            image = rendered(native, target["compositing"]["profiles"][0])
            if image.size != tuple(target["native_size"]):
                raise ValueError(f"Changed native dimensions: {source}")
            image.save(output, optimize=True)
    return output


def candidate_options(target: dict, audit: dict, chat: list[dict], decision: dict | None,
                      extraction: dict | None, imagegen: dict | None, hglas: dict | None,
                      repair: dict | None, perimeter: dict | None, flagged: dict | None,
                      world_master: dict | None, obsolete_hashes: set[str]) -> list[dict]:
    requested = []
    local = []
    replaced_hashes = set(obsolete_hashes)
    if flagged and flagged.get("status") == "candidate_technical" \
            and flagged.get("source_sha256") == target["source_sha256"]:
        if flagged["input_sha256"] != flagged["artifact_sha256"]:
            replaced_hashes.add(flagged["input_sha256"])
        local.append((str(HERE / flagged["artifact"]), flagged["artifact_sha256"],
                      flagged["origin"], "new candidate after user flag; art pending review",
                      f"{flagged['method']}; replaces {flagged['input_sha256'][:12]}."))
    if perimeter and perimeter.get("status") == "candidate_technical" \
            and perimeter.get("source_sha256") == target["source_sha256"]:
        replaced_hashes.add(perimeter["input_sha256"])
        local.append((str(HERE / perimeter["artifact"]), perimeter["artifact_sha256"],
                      perimeter["input_origin"], "fitted 2×; magenta perimeter cleaned; art pending review",
                      f"{perimeter['method']}; input {perimeter['input_sha256'][:12]}."))
    if imagegen and imagegen.get("status") == "candidate_technical" \
            and imagegen.get("source_sha256") == target["source_sha256"]:
        method = imagegen.get("method", "")
        origin = "Native geometry redraw" if method.startswith(("smooth vector", "preserved intentional")) \
            else "Imagegen restoration"
        local.append((str(HERE / imagegen["artifact"]), imagegen["artifact_sha256"], origin,
                      "fitted 2×; art pending review", imagegen.get("method", "imagegen sheet extraction")))
    if repair and repair.get("status") == "candidate_technical" \
            and repair.get("source_sha256") == target["source_sha256"]:
        local.append((str(HERE / repair["artifact"]), repair["artifact_sha256"],
                      repair.get("origin", "Local visual repair"), "fitted 2×; art pending review",
                      f"{repair['method']}; input master {repair['master_sha256'][:12]}."))
    if hglas and hglas.get("status") == "candidate_technical" \
            and hglas.get("source_sha256") == target["source_sha256"]:
        local.append((str(HERE / hglas["artifact"]), hglas["artifact_sha256"],
                      "Transparent hourglass master", "fitted 2×; art pending review",
                      f"Foreground extracted from {hglas['master']}; "
                      f"master {hglas['master_sha256'][:12]}."))
    if extraction and extraction.get("status") == "candidate_technical":
        local.append((str(HERE / extraction["artifact"]), extraction["artifact_sha256"],
                      "Measured retained-sheet extraction", "technical crop checked; art pending review",
                      f"Raw sampling {extraction['sampling'][0]:.2f}× by {extraction['sampling'][1]:.2f}×; "
                      f"{extraction['method']}; raw {extraction['raw_sha256'][:12]}."))
    requested.extend(local)
    if decision and decision.get("source_sha256") == target["source_sha256"]:
        requested.append((decision.get("candidate"), decision.get("candidate_sha256"),
                          "Second-pass selection", decision.get("status", "needs_review"),
                          decision.get("observation", "")))
    for cell in audit.get("cells", []):
        for check in cell.get("candidate_checks", []):
            requested.append((check["path"], check.get("sha256"), "Measured extraction",
                              check.get("status", "needs_review"), ""))
    for row in chat:
        requested.append((row.get("artifact"), row.get("worker_review", {}).get("candidate_sha256"),
                          row.get("bundle", "External return"), row.get("status", "review_pending"),
                          row.get("notes", "")))
    if world_master and world_master.get("candidate"):
        approved = world_master["approved_world"]
        requested.insert(0, (str(HERE / world_master["candidate"]), world_master["candidate_sha256"],
                             "Approved world sprite master", "user approved ground-master reuse",
                             f"Same native drawing as {world_master['native_match']['sprite_name']}; "
                             f"{world_master['fit_method']}; world master {approved['sha256'][:12]}."))

    result = []
    seen = set()
    for name, recorded_hash, origin, status, note in requested:
        path = source_path(name)
        if path is None:
            continue
        try:
            with Image.open(path) as image:
                if image.size != tuple(target["x2_size"]):
                    continue
        except OSError:
            continue
        actual_hash = sha256(path)
        if actual_hash in seen or actual_hash in replaced_hashes \
                or (recorded_hash and recorded_hash != actual_hash):
            continue
        seen.add(actual_hash)
        result.append({
            "path": browser_path(path),
            "sha256": actual_hash,
            "origin": origin,
            "status": status,
            "note": note,
            **({"kind": "approved_world_master"} if origin == "Approved world sprite master" else {}),
        })
    return result


def accepted_artwork(targets_by_id: dict, checkpoint: dict) -> dict[str, dict]:
    """Find hash-bound restorations that were approved before this review."""
    result = {}
    for target_id, row in checkpoint["cells"].items():
        if row.get("status") == "accepted" and target_id in targets_by_id:
            result[target_id] = {
                "path": source_path(row.get("artifact")), "sha256": row.get("sha256"),
                "approval": "restoration checkpoint",
            }
    for name in ("review_acceptance.json", "spell_review_acceptance.json",
                 "spellbook_review_acceptance.json"):
        for row in read_json(MM8_REVIEW / name)["items"]:
            target_id = row["id"]
            if target_id in targets_by_id and row["source_sha256"] == targets_by_id[target_id]["source_sha256"]:
                result[target_id] = {
                    "path": source_path(str(MM8_REVIEW / row["artifact"])),
                    "sha256": row["candidate_sha256"], "approval": "MM8 art review",
                }
    with (HUD / "hud_context_review/acceptance/hud_icons.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            target_id = "engine--icons--" + Path(row["native_file"]).name
            if target_id in targets_by_id and row["native_sha256"] == targets_by_id[target_id]["source_sha256"]:
                result[target_id] = {
                    "path": source_path(row["x2_review_png"]),
                    "sha256": row["x2_sha256"], "approval": "HUD visual signoff",
                }
    valid = {}
    for target_id, row in result.items():
        path = row["path"]
        if path is None or sha256(path) != row["sha256"]:
            continue
        with Image.open(path) as image:
            if image.size != tuple(targets_by_id[target_id]["x2_size"]):
                continue
        valid[target_id] = row
    return valid


def displayed_native_hash(target: dict, cache: dict) -> str:
    target_id = target["id"]
    if target_id not in cache:
        with Image.open(ROOT / target["source_path"]) as native:
            image = rendered(native, target["compositing"]["profiles"][0]).convert("RGBA")
            cache[target_id] = hashlib.sha256(image.tobytes()).hexdigest()
    return cache[target_id]


def accepted_duplicate(target: dict, donors: list[str], targets_by_id: dict,
                       approved: dict, displayed_hashes: dict) -> dict | None:
    for donor_id in sorted(donors):
        if donor_id == target["id"]:
            continue
        donor = targets_by_id[donor_id]
        if (donor["native_size"] != target["native_size"]
                or donor["x2_size"] != target["x2_size"]
                or donor.get("placement") != target.get("placement")):
            continue
        if displayed_native_hash(donor, displayed_hashes) != displayed_native_hash(target, displayed_hashes):
            continue
        artwork = approved[donor_id]
        return {
            "donor_id": donor_id,
            "path": browser_path(artwork["path"]),
            "sha256": artwork["sha256"],
            "approval": artwork["approval"],
            "match": "identical native bytes" if donor["source_sha256"] == target["source_sha256"]
                     else "identical rendered native pixels",
        }
    return None


def dense_attempts() -> dict[str, dict]:
    result = {}
    for directory in (HUD / "dense_returns").glob("*"):
        manifest = directory / "incoming/manifest.json"
        if not manifest.is_file():
            continue
        bundle = read_json(manifest)["bundle_id"]
        for raw in (directory / "incoming/outputs/raw").glob("S*.png"):
            layout = HUD / "chat_bundles/dense64_20260916" / bundle / "sheets" / raw.stem / "layout.json"
            result[f"dense:{bundle}:{raw.stem}"] = {
                "raw": raw,
                "layout": layout if layout.is_file() else None,
            }
    return result


def raw_choice(target: dict, audit: dict, decision: dict | None, state: dict,
               attempts: dict, dense: dict) -> dict | None:
    ids = []
    current = state.get("attempt")
    if current:
        ids.append(current)
    if decision and decision.get("attempt"):
        ids.append(decision["attempt"])
    for cell in audit.get("cells", []):
        ids.extend(reversed(cell.get("retained_attempts", [])))
    found = []
    for attempt_id in dict.fromkeys(ids):
        if attempt_id in dense:
            info = dense[attempt_id]
            if info["raw"].is_file():
                found.append({"path": info["raw"], "layout": info["layout"], "id": attempt_id})
            continue
        attempt = attempts.get(attempt_id, {})
        path = source_path(attempt.get("raw"))
        if path is None:
            continue
        payload_path = source_path(attempt.get("payload"))
        layout = read_json(payload_path).get("execution_layout") if payload_path else None
        found.append({"path": path, "layout": layout, "id": attempt_id})
    if decision:
        path = source_path(decision.get("raw"))
        if path and not any(item["path"] == path for item in found):
            found.append({"path": path, "layout": None, "id": "second-pass raw"})
    if not found:
        return None
    return next((item for item in found if item["layout"]), found[0])


def projected_rect(target_id: str, layout: dict | Path | None, raw_size: tuple[int, int]) -> list[int] | None:
    if layout is None:
        return None
    if isinstance(layout, Path):
        layout = read_json(layout)
        canvas_size = layout.get("reference_size")
        cells = {cell["id"]: cell["reference_rect"] for cell in layout.get("cells", [])}
    else:
        canvas_size = layout.get("canvas_size")
        cells = layout.get("cell_rects", {})
    rect = cells.get(target_id)
    if not canvas_size or not rect:
        return None
    scale_x = raw_size[0] / canvas_size[0]
    scale_y = raw_size[1] / canvas_size[1]
    return [round(rect[0] * scale_x), round(rect[1] * scale_y),
            max(1, round(rect[2] * scale_x)), max(1, round(rect[3] * scale_y))]


def raw_locator(target: dict, raw: dict | None) -> dict | None:
    if raw is None:
        return None
    path = raw["path"]
    output = HERE / "raw_locators" / (target["id"] + ".webp")
    with Image.open(path) as source:
        rect = projected_rect(target["id"], raw["layout"], source.size)
        if rect:
            x, y, width, height = rect
            margin = max(16, round(max(width, height) * 0.22))
            box = (max(0, x - margin), max(0, y - margin),
                   min(source.width, x + width + margin), min(source.height, y + height + margin))
        else:
            box = (0, 0, source.width, source.height)
        if box[2] <= box[0] or box[3] <= box[1]:
            return {"master": browser_path(path), "preview": None, "attempt": raw["id"]}
        if not output.is_file() or output.stat().st_mtime_ns < path.stat().st_mtime_ns:
            image = source.convert("RGB").crop(box)
            if rect:
                draw = ImageDraw.Draw(image)
                boundary = (x - box[0], y - box[1], x + width - box[0], y + height - box[1])
                draw.rectangle(boundary, outline="#7ef4cf", width=max(2, image.width // 200))
            if max(image.size) > 640:
                image.thumbnail((640, 640), Image.Resampling.LANCZOS)
            output.parent.mkdir(parents=True, exist_ok=True)
            image.save(output, format="WEBP", quality=82, method=4)
    return {
        "master": browser_path(path),
        "preview": browser_path(output) if output.is_file() else None,
        "attempt": raw["id"],
        "projected": bool(rect),
    }


def main() -> None:
    targets = read_json(HUD / "expected_targets.json")["targets"]
    targets_by_id = {target["id"]: target for target in targets}
    scope = {row["source_path"]: row for row in read_json(
        HUD / "review/second_pass/usage_scope.json")["files"]}
    checkpoint = read_json(HUD / "checkpoint/state.json")
    approved = accepted_artwork(targets_by_id, checkpoint)
    donors_by_pixels = defaultdict(list)
    for donor_id in approved:
        donors_by_pixels[targets_by_id[donor_id]["native_rgba_sha256"]].append(donor_id)
    displayed_hashes = {}
    audit = {row["target_id"]: row for row in read_json(
        HUD / "review/second_pass/replacement_audit.json")["targets"]}
    chat = defaultdict(list)
    for row in read_json(HUD / "chat_returns/inventory.json")["cells"]:
        chat[row["cell"]].append(row)
    decisions_dir = HUD / "review/second_pass/decisions"
    decisions = {path.name[:-5]: read_json(path) for path in decisions_dir.glob("*.json")}
    extraction_path = HERE / "extracted_retained/report.json"
    extraction = read_json(extraction_path)["items"] if extraction_path.is_file() else {}
    fallback_path = HERE / "restored_fallback/manifest.json"
    old_fallback = read_json(fallback_path)["items"] if fallback_path.is_file() else {}
    imagegen_dir = HERE / "imagegen_regen"
    imagegen = {}
    for name in ("report.json", "component_report.json", "edge_component_report.json",
                 "retry_report.json", "potion_report.json",
                 "cape_report.json",
                 "special_report.json", "third_report.json",
                 "third_effects_report.json", "palette_report.json", "tail_report.json"):
        for target_id, row in read_json(imagegen_dir / name)["items"].items():
            if row.get("status") == "candidate_technical":
                imagegen[target_id] = row
    imagegen["engine--icons--title.png"] = read_json(imagegen_dir / "title_assembly.json")
    if set(imagegen) != set(old_fallback):
        raise ValueError(f"Imagegen coverage differs from old fallback slice: "
                         f"missing {set(old_fallback) - set(imagegen)}, extra {set(imagegen) - set(old_fallback)}")
    hglas_path = HERE / "hglas_alpha/report.json"
    hglas = read_json(hglas_path)["items"] if hglas_path.is_file() else {}
    repair_path = HERE / "local_repairs/report.json"
    repairs = read_json(repair_path)["items"] if repair_path.is_file() else {}
    perimeter_path = HERE / "magenta_perimeter/report.json"
    perimeter = read_json(perimeter_path)["items"] if perimeter_path.is_file() else {}
    world_links = read_json(HERE / "review_repairs/world_item_links/report.json")["items"]
    kept_sequences = read_json(HERE / "review_repairs/full_sequences/report.json")["items"]
    remaining_sequences = read_json(HERE / "review_repairs/remaining_sequences/report.json")["items"]
    stabilized_idle = read_json(HERE / "review_repairs/remaining_sequences/stabilization_report.json")["items"]
    if not set(stabilized_idle).issubset(remaining_sequences):
        raise ValueError("Idle animation stabilization has unknown frames")
    remaining_sequences.update(stabilized_idle)
    locked_idle = read_json(HERE / "review_repairs/remaining_sequences/idle_core_report.json")["items"]
    if not set(locked_idle).issubset(remaining_sequences):
        raise ValueError("Locked idle animation has unknown frames")
    remaining_sequences.update(locked_idle)
    remaining_sequences = {target_id: row for target_id, row in remaining_sequences.items()
                           if target_id != "engine--icons--sp21a10.bmp"}
    if set(kept_sequences) & set(remaining_sequences) or len(remaining_sequences) != 141:
        raise ValueError("Effect sequence candidates changed")
    sequence_repairs = {**kept_sequences, **remaining_sequences}
    flagged = {}
    for name in ("component_reuse_report.json", "effect_report.json", "inventory_regen_report.json",
                 "spill_report.json", "ui_regen_report.json"):
        path = HERE / "review_repairs" / name
        if path.is_file():
            flagged.update(read_json(path)["items"])
    flagged.update(sequence_repairs)
    flagged.update(read_json(HERE / "review_repairs/shared_world_primary_report.json")["items"])
    user_flags = {target_id: row["candidate_sha256"] for target_id, row in
                  read_json(HERE / "user_review_2026-09-24.json")["decisions"].items()
                  if row["decision"] == "flag" and row.get("candidate_sha256")}
    attempts = {row["id"]: row for row in checkpoint.get("attempts", [])}
    dense = dense_attempts()
    signed_hud = set((HUD / "hud_context_review/acceptance/hud_icon_names.txt").read_text().splitlines())
    signed_prior = set()
    for name in ("review_acceptance.json", "spell_review_acceptance.json",
                 "spellbook_review_acceptance.json"):
        signed_prior.update(row["id"] for row in read_json(MM8_REVIEW / name)["items"])
    families = {}
    for job in read_json(HUD / "jobs.json")["jobs"]:
        for member in job["members"]:
            families[member["id"]] = job["family"][-1]

    selected = [target for target in targets if target["treatment"] in CATEGORIES
                and scope.get(target["source_path"], {}).get("restoration_active")
                and target["id"] not in signed_prior
                and not (target["namespace"] == "engine"
                         and Path(target["source_path"]).name in signed_hud)
                and checkpoint["cells"].get(target["id"], {}).get("status") != "accepted"]
    counts = Counter(target["treatment"] for target in selected)
    if dict(counts) != EXPECTED_COUNTS:
        raise ValueError(f"Review scope changed: {dict(counts)} != {EXPECTED_COUNTS}")
    if len({target["id"] for target in selected}) != len(selected):
        raise ValueError("Duplicate target IDs")

    catalog = []
    for index, target in enumerate(selected, 1):
        target_id = target["id"]
        source = ROOT / target["source_path"]
        decision = decisions.get(target_id)
        options = candidate_options(target, audit.get(target_id, {}), chat[target_id], decision,
                                    extraction.get(target_id), imagegen.get(target_id), hglas.get(target_id),
                                    repairs.get(target_id), perimeter.get(target_id), flagged.get(target_id),
                                    world_links.get(target_id), {user_flags[target_id]} if target_id in user_flags else set())
        duplicate = accepted_duplicate(target, donors_by_pixels[target["native_rgba_sha256"]],
                                       targets_by_id, approved, displayed_hashes)
        if duplicate and duplicate["sha256"] not in {option["sha256"] for option in options}:
            options.append({
                "path": duplicate["path"], "sha256": duplicate["sha256"],
                "origin": "Approved identical original: " + duplicate["donor_id"],
                "status": "approved donor; this target still needs review",
                "note": "Reuse candidate from " + duplicate["approval"] + ". " + duplicate["match"] + ".",
                "kind": "accepted_duplicate",
            })
        raw = raw_choice(target, audit.get(target_id, {}), decision,
                         checkpoint["cells"].get(target_id, {}), attempts, dense)
        locator = raw_locator(target, raw) if not options else None
        catalog.append({
            "id": target_id,
            "name": target["runtime_name"],
            "category": CATEGORIES[target["treatment"]],
            "treatment": target["treatment"],
            "namespace": target["namespace"],
            "family": families.get(target_id) or re.sub(r"\d+$", "", target["runtime_name"]),
            "native_size": target["native_size"],
            "x2_size": target["x2_size"],
            "source_sha256": target["source_sha256"],
            "original": browser_path(originals(target)),
            "source": browser_path(source),
            "candidates": options,
            "imagegen_slice": target_id in imagegen,
            "review_repair": target_id in flagged,
            "sequence_repair": target_id in sequence_repairs,
            "world_master": ({
                "sprite_name": world_links[target_id]["native_match"]["sprite_name"],
                "reuse_status": world_links[target_id]["reuse_status"],
                "source_rgb_correlation": world_links[target_id]["native_match"]["rgb_correlation"],
                "world_path": browser_path(ROOT / world_links[target_id]["approved_world"]["path"])
                              if world_links[target_id].get("approved_world") else None,
                "world_sha256": world_links[target_id]["approved_world"]["sha256"]
                                if world_links[target_id].get("approved_world") else None,
                "candidate_sha256": world_links[target_id].get("candidate_sha256"),
            } if world_links.get(target_id, {}).get("native_match") else None),
            "accepted_duplicate": duplicate,
            "raw": locator or ({"master": browser_path(raw["path"]), "attempt": raw["id"]} if raw else None),
            "pipeline_status": checkpoint["cells"].get(target_id, {}).get("status", "unaccepted"),
            "existing_status": decision.get("status") if decision else None,
            "existing_note": decision.get("observation", "") if decision else "",
        })
        if index % 250 == 0:
            print(f"Prepared {index}/{len(selected)}")
    pending_donors = defaultdict(list)
    for item in catalog:
        if item["candidates"]:
            pending_donors[targets_by_id[item["id"]]["native_rgba_sha256"]].append(item)
    for item in catalog:
        if item["candidates"]:
            continue
        target = targets_by_id[item["id"]]
        for donor in pending_donors[target["native_rgba_sha256"]]:
            donor_target = targets_by_id[donor["id"]]
            if (donor["id"] == item["id"] or donor_target["native_size"] != target["native_size"]
                    or donor_target["x2_size"] != target["x2_size"]
                    or donor_target.get("placement") != target.get("placement")
                    or displayed_native_hash(donor_target, displayed_hashes)
                    != displayed_native_hash(target, displayed_hashes)):
                continue
            option = donor["candidates"][0]
            item["candidates"].append({
                "path": option["path"], "sha256": option["sha256"],
                "origin": "Same original as " + donor["id"],
                "status": "pending donor; destination review required",
                "note": "Identical rendered native pixels, x2 canvas and placement. "
                        "Review the donor once, then verify this destination's consumer contract.",
                "kind": "pending_duplicate",
                "donor_id": donor["id"],
            })
            break
    catalog.sort(key=lambda row: (list(CATEGORIES).index(row["treatment"]),
                                  not bool(row["candidates"]), row["family"], row["name"]))
    pending_by_pixels = defaultdict(list)
    for item in catalog:
        pending_by_pixels[targets_by_id[item["id"]]["native_rgba_sha256"]].append(item)
    pending_groups = []
    for pixel_hash, members in pending_by_pixels.items():
        canonical = members[0]["id"]
        if len(members) > 1:
            pending_groups.append({
                "native_rgba_sha256": pixel_hash,
                "source_sha256": members[0]["source_sha256"],
                "canonical_id": canonical,
                "members": [item["id"] for item in members],
                "with_individual_candidate": [item["id"] for item in members if item["candidates"]],
            })
        for item in members:
            item["duplicate_group_id"] = canonical
            item["review_siblings"] = [other["id"] for other in members if other is not item]
    accepted_matches = [{
        "target_id": item["id"], "source_sha256": item["source_sha256"],
        "native_rgba_sha256": targets_by_id[item["id"]]["native_rgba_sha256"],
        **item["accepted_duplicate"],
    } for item in catalog if item["accepted_duplicate"]]
    summary = {
        "total": len(catalog),
        "by_category": {CATEGORIES[key]: counts[key] for key in CATEGORIES},
        "with_candidate": sum(bool(item["candidates"]) for item in catalog),
        "imagegen_slice_candidates": sum(item["imagegen_slice"] and bool(item["candidates"]) for item in catalog),
        "individual_candidates": sum(any(option.get("kind") not in ("accepted_duplicate", "pending_duplicate")
                                         for option in item["candidates"]) for item in catalog),
        "accepted_reuse_candidates": len(accepted_matches),
        "pending_reuse_candidates": sum(any(option.get("kind") == "pending_duplicate"
                                             for option in item["candidates"]) for item in catalog),
        "raw_only": sum(not item["candidates"] and bool(item["raw"]) for item in catalog),
        "no_return": sum(not item["candidates"] and not item["raw"] for item in catalog),
        "pending_duplicate_groups": len(pending_groups),
        "pending_duplicate_targets": sum(len(group["members"]) for group in pending_groups),
    }
    (HERE / "duplicate_report.json").write_text(json.dumps({
        "summary": {
            "accepted_original_matches": len(accepted_matches),
            "pending_duplicate_groups": len(pending_groups),
            "pending_duplicate_targets": sum(len(group["members"]) for group in pending_groups),
            "redundant_pending_review_slots": sum(len(group["members"]) - 1 for group in pending_groups),
        },
        "accepted_matches": accepted_matches,
        "pending_groups": sorted(pending_groups, key=lambda group: group["canonical_id"]),
    }, indent=2) + "\n")
    output = HERE / "catalog.js"
    output.write_text("window.REMAINING_ART_CATALOG = " + json.dumps(
        {"schema": 1, "summary": summary, "items": catalog}, separators=(",", ":")) + ";\n")
    # Superseded previews generated by an earlier version of this same builder.
    for preview in (HERE / "raw_locators").glob("*.png"):
        preview.unlink()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
