#!/usr/bin/env python3
"""Build an offline, read-only HUD composition review from current restoration evidence."""

from __future__ import annotations

import json
import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from PIL import Image


ROOT = Path(__file__).resolve().parents[4]
WORK = ROOT / "level_generation/ui/hud_inventory"
OUT = Path(__file__).resolve().parent
LAYOUTS = ROOT / "assets_dev/engine/ui/gameplay"
SECOND_PASS = WORK / "review/second_pass"
NATIVE = OUT / "native"
RESTORED = OUT / "restored_display"
ALPHA_REPAIR = OUT / "alpha_repair"
OPAQUE_EDGE_REPAIR = OUT / "opaque_edge_repair"
TARGETED_REPAIRS = OUT / "targeted_repairs"
BUTTON_TRIPLETS = OUT / "button_triplets"

EXTRA_HUD_NAMES = {
    "basebar_ender", "divbar", "ib_spelico", "manar", "manay", "mhp_bg", "mhp_capl", "mhp_capr",
    "mhp_grn", "mhp_red", "mhp_yel", "statbl", "statg", "statr", "staty",
    "pc01-01", "pc02-01", "pc03-01", "pc04-01", "npc0499", "npc1500", "npc1581", "item015",
}


def relative(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def browser_path(path: Path) -> str:
    return Path(__import__("os").path.relpath(path.resolve(), OUT)).as_posix()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def existing_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path if path.is_file() else None


def parse_layouts() -> tuple[dict, dict[str, list]]:
    layouts = {}
    uses = defaultdict(list)

    def walk(element: dict, layout: str) -> None:
        asset = element.get("asset") or {}
        if isinstance(asset, str):
            asset = {"default": asset}
        for state, name in asset.items():
            if isinstance(name, str) and name:
                uses[name.lower()].append({"layout": layout, "element": element["id"], "state": state})
        for child in element.get("children") or []:
            walk(child, layout)

    for path in sorted(LAYOUTS.glob("*.yml")):
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict) or "elements" not in data:
            continue
        layouts[path.stem] = {"screen": data.get("screen", path.stem), "elements": data["elements"]}
        for element in data["elements"]:
            walk(element, path.stem)
    return layouts, uses


def source_png(source: Path, name: str, destination: Path) -> tuple[int, int]:
    with Image.open(source) as input_image:
        indexed = input_image.mode == "P"
        rgba = input_image.convert("RGBA")
        pixels = rgba.load()
        index_pixels = input_image.load() if indexed else None
        for y in range(rgba.height):
            for x in range(rgba.width):
                r, g, b, a = pixels[x, y]
                key = (r >= 248 and g <= 8 and b >= 248) or (r <= 8 and g >= 248 and b >= 248)
                if name.startswith(("mapdir", "micon")):
                    key = key or (r <= 8 and g <= 8 and b <= 8)
                if name.startswith(("item", "6item", "7item")) and indexed:
                    key = key or index_pixels[x, y] == 0
                if key:
                    pixels[x, y] = (r, g, b, 0)
        destination.parent.mkdir(parents=True, exist_ok=True)
        rgba.save(destination, optimize=True)
        return rgba.size


def pick_candidate(
    target: str, name: str, size: tuple[int, int], native_path: Path, staged: dict, decisions: dict,
    audited: dict, repairs: dict, edge_repairs: dict, targeted_repairs: dict, button_repairs: dict,
) -> dict:
    choices = []
    accepted = staged.get(target)
    if accepted:
        choices.append((accepted.get("artifact"), "staged", None))
    decision = decisions.get(target)
    if decision:
        choices.append((decision.get("candidate"), decision.get("status", "review candidate"), decision))
    for candidate in audited.get(target, []):
        choices.append((candidate, "extracted candidate", None))

    seen = set()
    for value, status, decision_record in choices:
        path = existing_path(value)
        if not path or path in seen:
            continue
        seen.add(path)
        try:
            with Image.open(path) as image:
                actual = image.size
        except (OSError, ValueError):
            continue
        result = {
            "original": browser_path(path), "status": status, "size": actual,
            "exact_x2": actual == (size[0] * 2, size[1] * 2),
        }
        if decision_record:
            result["decision"] = browser_path(SECOND_PASS / "decisions" / (target + ".json"))
            result["observation"] = decision_record.get("observation", "")
            result["next_action"] = decision_record.get("next_action", "")
        if result["exact_x2"]:
            display_path = RESTORED / (target.rsplit(".", 1)[0] + ".png")
            source_png(path, name, display_path)
            result["image"] = browser_path(display_path)
            targeted = targeted_repairs.get(target)
            if targeted and targeted.get("status") == "imagegen_true_alpha_review_required":
                output = TARGETED_REPAIRS / targeted["output"]
                master = TARGETED_REPAIRS / targeted["master"]
                if (output.is_file() and master.is_file()
                        and sha256(path) == targeted.get("source_candidate_sha256")
                        and sha256(native_path) == targeted.get("native_sha256")
                        and sha256(output) == targeted.get("output_sha256")
                        and sha256(master) == targeted.get("master_sha256")):
                    with Image.open(output) as clean:
                        if clean.size == actual and clean.mode == "RGBA":
                            result["keyed_image"] = result["image"]
                            result["image"] = browser_path(output)
                            result["imagegen_repair"] = {
                                "status": "unapproved imagegen true-alpha review candidate",
                                "silhouette_iou": targeted["silhouette_iou"],
                                "method": targeted["method"],
                                "master": browser_path(master),
                                "comparison": browser_path(TARGETED_REPAIRS / "manafrm-comparison.png"),
                            }
            repair = repairs.get(target)
            if not result.get("imagegen_repair") and repair and repair.get("status") == "alpha_repaired_review_required":
                output = OUT / repair["output"]
                if (output.is_file() and sha256(path) == repair.get("source_sha256")
                        and sha256(native_path) == repair.get("native_sha256")
                        and sha256(output) == repair.get("output_sha256")):
                    with Image.open(output) as clean:
                        if clean.size == actual and clean.mode == "RGBA":
                            result["keyed_image"] = result["image"]
                            result["image"] = browser_path(output)
                            result["alpha_repair"] = {
                                "status": "unapproved true-alpha review candidate",
                                "source_matte_on_native_clear_pct": repair["source_matte_on_native_clear_pct"],
                                "current": repair["current"], "repaired": repair["repaired"],
                                "method": "local spatial matte extraction and RGB unmixing",
                            }
            edge_repair = edge_repairs.get(target)
            if not result.get("imagegen_repair") and not result.get("alpha_repair") and edge_repair:
                output = OUT / edge_repair["output"]
                if (output.is_file() and sha256(path) == edge_repair.get("source_sha256")
                        and sha256(native_path) == edge_repair.get("native_sha256")
                        and sha256(output) == edge_repair.get("output_sha256")):
                    with Image.open(output) as clean:
                        if clean.size == actual and clean.mode == "RGBA":
                            result["keyed_image"] = result["image"]
                            result["image"] = browser_path(output)
                            result["opaque_edge_repair"] = {
                                "status": "unapproved opaque edge color repair",
                                "changed_pixels": edge_repair["changed_pixels"],
                                "changed_pct": edge_repair["changed_pct"],
                                "edge_chroma_before": edge_repair["edge_chroma_before"],
                                "edge_chroma_after": edge_repair["edge_chroma_after"],
                                "method": "native-guided outer-edge color replacement; alpha unchanged",
                            }
            button_repair = button_repairs.get(target)
            if button_repair:
                output = OUT / button_repair["output"]
                current = OUT / result["image"]
                if (output.is_file() and current.is_file()
                        and sha256(path) == button_repair.get("source_sha256")
                        and sha256(native_path) == button_repair.get("native_preview_sha256")
                        and sha256(current) == button_repair.get("current_sha256")
                        and sha256(output) == button_repair.get("output_sha256")):
                    with Image.open(output) as clean:
                        if clean.size == actual and clean.mode == "RGBA" and clean.getextrema()[3] == (255, 255):
                            result["keyed_image"] = result.get("keyed_image", result["image"])
                            previous = result["image"]
                            result["image"] = browser_path(output)
                            result["button_triplet_repair"] = {
                                "status": "unapproved imagegen state-family review candidate",
                                "previous": previous,
                                "master": "button_triplets/imagegen_master_v2.png",
                                "contact": "button_triplets/fitted_contact_v2.png",
                                "method": "one 21-state imagegen sheet, measured crops, exact-x2 resize",
                            }
            return result
    return {"image": None, "status": "no exact-x2 extraction", "size": None, "exact_x2": False}


def first_raw(cell: dict, attempts: dict) -> Path | None:
    for attempt_id in cell.get("attempts") or []:
        path = existing_path(attempts.get(attempt_id))
        if path:
            return path
    for historical in cell.get("historical") or []:
        record = historical.get("record") or {}
        path = existing_path(record.get("raw_path"))
        if path:
            return path
    return None


def main() -> None:
    layouts, uses = parse_layouts()
    inventory = json.loads((WORK / "inventory.json").read_text())
    by_name = {asset["name"].lower(): asset for asset in inventory["assets"]}
    selected = set(uses)
    for asset in inventory["assets"]:
        groups = set(asset.get("groups", []))
        name = asset["name"].lower()
        if groups.intersection({"hud_animation_table", "journal_animation_family", "minimap_symbol_family"}):
            selected.add(name)
        if name in EXTRA_HUD_NAMES:
            selected.add(name)

    state = json.loads((WORK / "checkpoint/state.json").read_text())
    attempts = {attempt["id"]: attempt.get("raw") for attempt in state["attempts"]}
    review_inventory = json.loads((SECOND_PASS / "inventory.json").read_text())
    cells = {cell["cell_id"]: cell for cell in review_inventory["cells"]}
    decisions = {}
    for path in (SECOND_PASS / "decisions").glob("*.json"):
        decision = json.loads(path.read_text())
        decisions[decision.get("target_id", path.stem)] = decision
    audit = json.loads((SECOND_PASS / "replacement_audit.json").read_text())
    audited = defaultdict(list)
    for target in audit["targets"]:
        for cell in target.get("cells", []):
            for check in cell.get("candidate_checks", []):
                if check.get("exact_x2"):
                    audited[target["target_id"]].append(check["path"])
    repair_file = ALPHA_REPAIR / "manifest.json"
    repairs = {}
    if repair_file.is_file():
        repairs = {record["target"]: record for record in json.loads(repair_file.read_text())["records"]}
    edge_repair_file = OPAQUE_EDGE_REPAIR / "manifest.json"
    edge_repairs = {}
    if edge_repair_file.is_file():
        edge_repairs = {record["target"]: record for record in json.loads(edge_repair_file.read_text())["records"]}
    targeted_repairs = {}
    mana_report = TARGETED_REPAIRS / "manafrm-report.json"
    if mana_report.is_file():
        repair = json.loads(mana_report.read_text())
        targeted_repairs[repair["target"]] = repair
    button_repairs = {}
    button_report = BUTTON_TRIPLETS / "review_manifest.json"
    if button_report.is_file():
        report = json.loads(button_report.read_text())
        master = BUTTON_TRIPLETS / report["master"]
        prompt = BUTTON_TRIPLETS / report["prompt"]
        source_manifest = BUTTON_TRIPLETS / "source_manifest.json"
        if (master.is_file() and prompt.is_file() and source_manifest.is_file()
                and sha256(master) == report.get("master_sha256")
                and sha256(prompt) == report.get("prompt_sha256")
                and sha256(source_manifest) == report.get("source_manifest_sha256")):
            button_repairs = {record["target"]: record for record in report["records"]}

    assets = {}
    counts = Counter()
    for name in sorted(selected):
        asset = by_name.get(name)
        files = asset.get("files", []) if asset else []
        files = sorted(files, key=lambda item: (not item["path"].startswith("assets_dev/engine/"), item["path"]))
        file = next((item for item in files if (ROOT / item["path"]).is_file()), None)
        if file is None:
            generated = name == "minimap"
            assets[name] = {"name": name, "uses": uses.get(name, []), "missing": True, "generated": generated}
            counts["generated_content" if generated else "missing_source"] += 1
            continue

        source = ROOT / file["path"]
        target = file["path"].removeprefix("assets_dev/").replace("worlds/", "worlds-").replace("/", "--")
        native_path = NATIVE / (target.rsplit(".", 1)[0] + ".png")
        native_size = source_png(source, name, native_path)
        candidate = pick_candidate(target, name, native_size, native_path,
                                   state["staged_targets"], decisions, audited, repairs, edge_repairs, targeted_repairs,
                                   button_repairs)
        cell = cells.get(target, {})
        raw = first_raw(cell, attempts)
        if not candidate["image"]:
            candidate["status"] = "raw return only — not fitted" if raw else "native fallback"
        record = {
            "name": asset["name"], "target": target, "source": relative(source),
            "native": browser_path(native_path), "native_size": native_size,
            "restored": candidate, "uses": uses.get(name, []), "groups": asset.get("groups", []),
            "screens": asset.get("screens", []), "second_pass": cell.get("second_pass_status", ""),
            "disposition": cell.get("disposition", ""), "raw": browser_path(raw) if raw else None,
            "alternates": [item["path"] for item in files[1:]],
        }
        assets[name] = record
        counts["with_exact_x2" if candidate["image"] else "native_fallback"] += 1
        if raw and not candidate["image"]:
            counts["raw_only"] += 1
        if candidate["status"] == "staged":
            counts["staged"] += 1
        if candidate.get("alpha_repair"):
            counts["alpha_repaired_review"] += 1
        if candidate.get("opaque_edge_repair"):
            counts["opaque_edge_repaired_review"] += 1
        if candidate.get("imagegen_repair"):
            counts["imagegen_repaired_review"] += 1
        if candidate.get("button_triplet_repair"):
            counts["button_triplet_repaired_review"] += 1

    data = {"layouts": layouts, "assets": assets, "counts": counts, "generated_from": {
        "layouts": "assets_dev/engine/ui/gameplay/*.yml", "inventory": "level_generation/ui/hud_inventory/inventory.json",
        "restoration": "level_generation/ui/hud_inventory/review/second_pass and checkpoint/state.json",
    }}
    (OUT / "data.js").write_text("window.HUD_REVIEW_DATA = " + json.dumps(data, separators=(",", ":")) + ";\n")
    with (OUT / "coverage.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["name", "target", "source", "exact_x2", "candidate_status", "alpha_repaired_review",
                         "opaque_edge_repaired_review", "imagegen_repaired_review",
                         "button_triplet_repaired_review", "second_pass", "uses"])
        for name, record in assets.items():
            writer.writerow([
                name, record.get("target", ""), record.get("source", ""),
                bool(record.get("restored", {}).get("image")),
                record.get("restored", {}).get("status", "missing source"),
                bool(record.get("restored", {}).get("alpha_repair")),
                bool(record.get("restored", {}).get("opaque_edge_repair")),
                bool(record.get("restored", {}).get("imagegen_repair")),
                bool(record.get("restored", {}).get("button_triplet_repair")),
                record.get("second_pass", ""),
                "; ".join(use["layout"] + ":" + use["element"] + ":" + use["state"]
                          for use in record.get("uses", [])),
            ])
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
