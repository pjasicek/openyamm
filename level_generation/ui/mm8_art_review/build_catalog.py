"""Build an offline review catalog for current MM8 UI art and MM6–MM8 NPC faces.

This reads the existing restoration ledger. It never changes acceptance or runtime art.
"""

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
import sys

from PIL import Image


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HUD = ROOT / "level_generation/ui/hud_inventory"
sys.path.insert(0, str(HUD))
from freeze_targets import rendered  # noqa: E402


def read_json(path):
    return json.loads(path.read_text())


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def web_path(path):
    return Path(os.path.relpath(path, HERE)).as_posix()


def category(target, usage):
    name = target["runtime_name"]
    treatment = target["treatment"]
    namespace = target["namespace"]
    if treatment == "npc_portrait_family" and namespace in {"engine", "worlds/mm6", "worlds/mm7", "worlds/mm8"}:
        return "NPC portraits"
    if treatment == "spell_icon_pair" and namespace == "engine":
        return "Spell icons"
    if treatment == "spellbook_page" and namespace == "engine" and any(
        row.get("kind") == "yaml" for row in target["usages"]
    ):
        return "Spellbook pages"
    if namespace == "engine" and (
        name in {"loading", "loading1", "loading2", "loading3", "loading4", "loading5", "bardata"}
        or re.fullmatch(r"ia02-\d{3}", name)
    ):
        return "Loading screens"
    if namespace == "engine" and usage.get(target["source_path"], {}).get("restoration_active"):
        if treatment == "ui_state_set" or (
            treatment == "legacy_ui_art" and re.match(r"^(bt_|but|ui-btn)", name)
        ):
            return "UI buttons"
    return None


def original_image(target):
    source = ROOT / target["source_path"]
    if sha256(source) != target["source_sha256"]:
        raise ValueError(f"Source changed: {source}")
    output = HERE / "originals" / (target["id"] + ".png")
    if not output.exists() or output.stat().st_mtime_ns < source.stat().st_mtime_ns:
        output.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as native:
            profile = target["compositing"]["profiles"][0]
            image = rendered(native, profile)
            if image.size != tuple(target["native_size"]):
                raise ValueError(f"Native size changed: {source}")
            image.save(output, optimize=True)
    return output


def candidate_list(target, state, chat, audit, provisional):
    result = []
    record = state.get("cells", {}).get(target["id"], {})
    if record.get("status") == "accepted":
        artifact = Path(record["artifact"])
        if artifact.exists():
            result.append({
                "path": artifact,
                "status": "pipeline accepted",
                "source": "current restoration checkpoint",
                "sha256": record.get("sha256"),
            })
    for cell in chat.get(target["id"], []):
        artifact = Path(cell.get("artifact") or "")
        if artifact.is_file() and artifact != Path(record.get("artifact", "")):
            result.append({
                "path": artifact,
                "status": "needs review",
                "source": cell.get("bundle", "external return"),
                "sha256": None,
            })
    for cell in audit.get(target["id"], {}).get("cells", []):
        for check in cell.get("candidate_checks", []):
            artifact = Path(check["path"])
            if artifact.is_file():
                result.append({
                    "path": artifact,
                    "status": "geometry flagged" if check["status"] == "geometry_flag" else "needs review",
                    "source": "second pass measured extraction",
                    "sha256": check.get("sha256"),
                })
    for entry in provisional.get(target["id"], []):
        if entry["source_sha256"] == target["source_sha256"]:
            if entry.get("parent_artifact"):
                parent = ROOT / entry["parent_artifact"]
                if not parent.is_file() or sha256(parent) != entry["parent_artifact_sha256"]:
                    continue
            result.append({
                "path": ROOT / entry["artifact"],
                "status": entry["status"],
                "source": entry.get("source_label", "retained generated master"),
                "sha256": entry["artifact_sha256"],
                "raw": web_path(ROOT / entry["raw"]) if entry.get("raw") else None,
            })
    checked = []
    seen = set()
    for candidate in result:
        path = candidate["path"]
        if path in seen:
            continue
        seen.add(path)
        try:
            with Image.open(path) as image:
                if image.size != tuple(target["x2_size"]):
                    continue
        except OSError:
            continue
        actual_sha256 = sha256(path)
        if candidate["sha256"] and candidate["sha256"] != actual_sha256:
            candidate["status"] = "artifact changed since recorded review"
        candidate["sha256"] = actual_sha256
        checked.append({**candidate, "path": web_path(path)})
    priority = {"approved transparent spell foreground v2": 0,
                "approved spellbook page": 0,
                "review-only transparent key cleanup": 0,
                "avatar-matched council body repair": 0, "review-only border repair": 1}
    checked.sort(key=lambda candidate: priority.get(candidate["source"], 2))
    return checked


def raw_master(target, state, audit, attempt_raw, dense_raw):
    record = state.get("cells", {}).get(target["id"], {})
    attempt_ids = [record.get("attempt")]
    for cell in audit.get(target["id"], {}).get("cells", []):
        attempt_ids.extend(cell.get("retained_attempts", []))
    for attempt_id in attempt_ids:
        raw = attempt_raw.get(attempt_id) or dense_raw.get(attempt_id)
        if raw and raw.is_file():
            return web_path(raw)
    return None


def main():
    targets = read_json(HUD / "expected_targets.json")["targets"]
    usage = {row["source_path"]: row for row in read_json(
        HUD / "review/second_pass/usage_scope.json")["files"]}
    state = read_json(HUD / "checkpoint/state.json")
    audit = {row["target_id"]: row for row in read_json(
        HUD / "review/second_pass/replacement_audit.json")["targets"]}
    provisional = defaultdict(list)
    for name in ("provisional_raw_buttons", "provisional_checkpoint", "generated_npc_candidates",
                 "generated_spell_candidates", "generated_large", "cleaned_npc_edges",
                 "council_body_repair", "cleaned_loading_key_pixels", "staged_spell_icons",
                 "staged_spellbook_pages"):
        manifest_path = HERE / name / "manifest.json"
        if manifest_path.is_file():
            for row in read_json(manifest_path)["items"]:
                provisional[row["id"]].append(row)
    chat = defaultdict(list)
    for cell in read_json(HUD / "chat_returns/inventory.json")["cells"]:
        chat[cell["cell"]].append(cell)
    attempt_raw = {row["id"]: Path(row["raw"]) for row in state.get("attempts", []) if row.get("raw")}
    dense_raw = {}
    for directory in (HUD / "dense_returns").glob("*"):
        bundle = re.sub(r"-[0-9a-f]{12}$", "", directory.name)
        for path in directory.glob("incoming/outputs/raw/S*.png"):
            dense_raw[f"dense:{bundle}:{path.stem}"] = path
    edge_unresolved_path = HERE / "cleaned_npc_edges" / "manifest.json"
    edge_unresolved = set()
    if edge_unresolved_path.is_file():
        edge_unresolved = {row["id"] for row in read_json(edge_unresolved_path).get("unresolved", [])}
    council_manifest = read_json(HERE / "council_body_repair" / "manifest.json")
    council_references = {row["id"]: {
        "id": row["reference_avatar_id"],
        "candidate_sha256": row["reference_avatar_candidate_sha256"],
    } for row in council_manifest["items"]}
    review_approvals = {}
    for name in ("review_acceptance.json", "spell_review_acceptance.json",
                 "spellbook_review_acceptance.json"):
        path = HERE / name
        if path.is_file():
            approval = read_json(path)
            for row in approval["items"]:
                if row["id"] in review_approvals:
                    raise ValueError(f"Duplicate visual approval: {row['id']}")
                review_approvals[row["id"]] = (row, approval["revision"])

    catalog = []
    for target in targets:
        group = category(target, usage)
        if not group:
            continue
        native = original_image(target)
        candidates = candidate_list(target, state, chat, audit, provisional)
        approval_entry = review_approvals.get(target["id"])
        approved, revision = approval_entry if approval_entry else (None, None)
        review_approval = None
        if approved and approved["source_sha256"] == target["source_sha256"] and any(
            candidate["sha256"] == approved["candidate_sha256"] and candidate["path"] == approved["artifact"]
            for candidate in candidates
        ):
            review_approval = {
                "candidate_sha256": approved["candidate_sha256"],
                "revision": revision,
            }
        record = state.get("cells", {}).get(target["id"], {})
        original_status = usage.get(target["source_path"], {}).get("status", "runtime selected")
        catalog.append({
            "id": target["id"],
            "name": target["runtime_name"],
            "category": group,
            "namespace": target["namespace"],
            "native_size": target["native_size"],
            "x2_size": target["x2_size"],
            "original": web_path(native),
            "source": web_path(ROOT / target["source_path"]),
            "source_sha256": target["source_sha256"],
            "candidates": candidates,
            "raw_master": raw_master(target, state, audit, attempt_raw, dense_raw) or next(
                (candidate["raw"] for candidate in candidates if candidate.get("raw")), None),
            "pipeline_status": record.get("status", "not started"),
            "usage_status": original_status,
            "usage": sorted({row.get("element") or row.get("kind", "") for row in target["usages"]})[:8],
            "quality_flags": ["purple edge needs review"] if target["id"] in edge_unresolved else [],
            "council_reference": council_references.get(target["id"]),
            "review_approval": review_approval,
        })
    catalog.sort(key=lambda row: (row["category"], row["namespace"], row["name"]))
    summary = {
        "total": len(catalog),
        "by_category": dict(Counter(row["category"] for row in catalog)),
        "with_candidate": sum(bool(row["candidates"]) for row in catalog),
        "without_candidate": sum(not row["candidates"] for row in catalog),
        "pipeline_accepted": sum(row["pipeline_status"] == "accepted" for row in catalog),
        "review_approved": sum(bool(row["review_approval"]) for row in catalog),
    }
    payload = {"summary": summary, "items": catalog}
    (HERE / "catalog.js").write_text("window.REVIEW_CATALOG = " + json.dumps(payload, separators=(",", ":")) + ";\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
