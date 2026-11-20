"""Build a file://-friendly paperdoll review catalog from the live game tables."""

import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import yaml
from PIL import Image


HERE = Path(__file__).resolve().parent
INVENTORY = HERE.parent
ROOT = HERE.parents[3]
TABLES = ROOT / "assets_dev/engine/data_tables"
sys.path.insert(0, str(INVENTORY))
from native_sources import native_source
from freeze_targets import rendered  # noqa: E402


VISIBLE_STATS = {
    "Weapon", "Weapon2", "Weapon1or2", "WeaponW", "Shield", "Missile",
    "Armor", "Helm", "Belt", "Boots", "Cloak", "Gauntlets", "Amulet", "Ring",
}
BODY_STATS = {"Armor", "Helm", "Belt", "Boots", "Cloak", "Gauntlets"}
LAYER_IDS = {
    "CharacterDollBowSlot", "CharacterDollCloakSlot", "CharacterDollBody",
    "CharacterDollRightHand", "CharacterDollLeftHand", "CharacterDollArmorSlot",
    "CharacterDollBootsSlot", "CharacterDollHelmetSlot", "CharacterDollBeltSlot",
    "CharacterDollRightHandSlot", "CharacterDollLeftHandSlot",
    "CharacterDollRightHandFingers",
}


def table_rows(name):
    with (TABLES / name).open(encoding="cp1252", newline="") as file:
        return list(csv.reader(file, delimiter="\t"))


def number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def asset_name(value):
    name = value.strip().lower()
    return "" if name in {"", "none", "null"} else name


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def browser_path(path):
    relative = os.path.relpath(path, HERE)
    return "/".join(quote(part) for part in Path(relative).parts)


def source_path(target):
    return native_source(target["source_path"])


def characters():
    output = []
    for row in table_rows("character_data.txt")[1:]:
        if len(row) < 24 or not row[0].isdigit():
            continue
        output.append({
            "id": number(row[0]),
            "type": number(row[1]),
            "sex": number(row[4]),
            "start": row[5].strip().lower() == "x",
            "bodyX": number(row[6]),
            "bodyY": -number(row[7]),
            "background": asset_name(row[8]),
            "body": asset_name(row[9]),
            "head": asset_name(row[10]),
            "leftClosed": asset_name(row[11]),
            "leftHold": asset_name(row[12]),
            "leftOpen": asset_name(row[13]),
            "rightFingers": asset_name(row[14]),
            "rightOpen": asset_name(row[17]),
            "rightHold": asset_name(row[18]),
            "facePrefix": row[19].strip(),
            "portrait": asset_name((row[19].strip() or f"pc{number(row[0]):02d}-") + "01"),
            "race": number(row[23]),
            "notes": row[24].strip() if len(row) > 24 else "",
        })
    return output


def doll_types():
    names = [
        "rightOpenX", "rightOpenY", "rightClosedX", "rightClosedY",
        "rightFingersX", "rightFingersY", "leftClosedX", "leftClosedY",
        "leftOpenX", "leftOpenY", "leftFingersX", "leftFingersY",
        "offHandOffsetX", "offHandOffsetY", "mainHandOffsetX", "mainHandOffsetY",
        "bowOffsetX", "bowOffsetY", "shieldX", "shieldY",
    ]
    output = {}
    for row in table_rows("doll_types.txt")[1:]:
        if len(row) < 28 or not row[0].isdigit():
            continue
        entry = {"id": number(row[0]), "can": {
            name: row[index].strip().lower() == "x"
            for index, name in enumerate(("bow", "armor", "helm", "belt", "boots", "cloak", "weapon"), 1)
        }}
        for index, name in enumerate(names):
            value = number(row[8 + index])
            entry[name] = -value if index % 2 else value
        output[entry["id"]] = entry
    return output


def items(extra_icons):
    output = []
    for row in table_rows("items.txt")[2:]:
        if len(row) < 16 or not row[0].isdigit() or (row[4] not in VISIBLE_STATS
                                                     and asset_name(row[1]) not in extra_icons):
            continue
        output.append({
            "id": number(row[0]), "icon": asset_name(row[1]), "name": row[2].strip(),
            "stat": row[4], "skill": row[5].strip(), "equipX": number(row[14]),
            "equipY": number(row[15]),
        })
    return output


def complex_pictures():
    output = {}
    for row in table_rows("complex_item_pictures.txt")[2:]:
        if len(row) < 4 or not row[0].isdigit() or not row[1].isdigit():
            continue
        output[number(row[1])] = [
            [number(row[column]) if column < len(row) else 0,
             number(row[column + 1]) if column + 1 < len(row) else 0]
            for column in range(4, 16, 2)
        ]
    return output


def layout():
    document = yaml.safe_load((ROOT / "assets_dev/engine/ui/gameplay/character.yml").read_text())
    panel = None

    def find_panel(nodes):
        nonlocal panel
        for node in nodes:
            if node["id"] == "CharacterDollPanel":
                panel = node
                return
            find_panel(node.get("children", []))

    find_panel(document["elements"])
    if panel is None:
        raise ValueError("CharacterDollPanel missing from character.yml")
    layers = []
    jewelry = {}

    def collect(nodes, inherited_z):
        for node in nodes:
            z = node.get("z_index", inherited_z)
            if node["id"] in LAYER_IDS:
                layers.append({"id": node["id"], "z": z, "order": len(layers)})
            if node["id"] == "CharacterDollJewelryOverlayPanel":
                jewelry["width"] = node["width"]
                jewelry["height"] = node["height"]
                jewelry["background"] = asset_name(node["asset"]["default"])
                for slot in node.get("children", []):
                    jewelry[slot["id"]] = {
                        "x": slot.get("offset_x", 0) + panel["width"] - node["width"],
                        "y": slot.get("offset_y", 0),
                        "width": slot.get("width", 0), "height": slot.get("height", 0),
                    }
            collect(node.get("children", []), z)

    collect(panel.get("children", []), panel.get("z_index", 0))
    layers.sort(key=lambda entry: (entry["z"], entry["order"]))
    return {"width": panel["width"], "height": panel["height"], "layers": layers, "jewelry": jewelry}


def main():
    all_targets = json.loads((INVENTORY / "expected_targets.json").read_text())["targets"]
    targets = {target["id"]: target for target in all_targets}
    icons = {target["runtime_name"].lower(): target for target in all_targets if target["namespace"] == "engine"}
    usage = {
        entry["source_path"]: entry
        for entry in json.loads((INVENTORY / "review/second_pass/usage_scope.json").read_text())["files"]
    }
    checkpoint = json.loads((INVENTORY / "checkpoint/state.json").read_text())["cells"]
    audit = {
        entry["target_id"]: entry
        for entry in json.loads((INVENTORY / "review/second_pass/replacement_audit.json").read_text())["targets"]
    }
    prepared_path = HERE / "raw_prepared/manifest.json"
    prepared = {
        entry["target_id"]: entry for entry in json.loads(prepared_path.read_text())["targets"]
    } if prepared_path.is_file() else {}
    for folder in ("inventory_prepared", "jewelry_prepared"):
        inventory_path = HERE / folder / "manifest.json"
        if not inventory_path.is_file():
            continue
        for entry in json.loads(inventory_path.read_text())["targets"]:
            if entry["target_id"] in prepared:
                raise ValueError(f"Duplicate prepared target: {entry['target_id']}")
            prepared[entry["target_id"]] = entry
    new_path = HERE / "new_returns/manifest.json"
    if new_path.is_file():
        for entry in json.loads(new_path.read_text())["targets"]:
            if not prepared.get(entry["target_id"], {}).get("alternatives"):
                prepared[entry["target_id"]] = entry
    repair_path = HERE / "edge_repaired/manifest.json"
    edge_repairs = {
        entry["target_id"]: entry for entry in json.loads(repair_path.read_text())["targets"]
    } if repair_path.is_file() else {}
    hud_approved = {}
    with (INVENTORY / "hud_context_review/acceptance/hud_icons.csv").open(newline="") as file:
        for row in csv.DictReader(file):
            hud_approved[row["native_file"].lower()] = row

    people = characters()
    types = doll_types()
    equipment_targets = [
        target for target in all_targets
        if target["namespace"] == "engine"
        and target["treatment"] in {"paperdoll_parts", "fitted_equipment_variants"}
    ]
    extra_icons = {
        match.group(1)
        for target in equipment_targets if target["treatment"] == "fitted_equipment_variants"
        if (match := re.fullmatch(r"(.*)v[1-5][ab]?", target["runtime_name"].lower()))
    }
    item_rows = items(extra_icons)
    points = complex_pictures()
    names = {target["runtime_name"].lower() for target in equipment_targets}
    names.update(name for person in people for name in (
        person["background"], person["body"], person["head"], person["leftClosed"], person["leftHold"],
        person["leftOpen"], person["rightFingers"], person["rightOpen"], person["rightHold"],
        person["portrait"]
    ) if name)
    names.update(item["icon"] for item in item_rows if item["icon"])
    names.add("backhand")

    old_manifest_path = HERE / "native_manifest.json"
    old_manifest = json.loads(old_manifest_path.read_text()) if old_manifest_path.exists() else {}
    new_manifest = {}
    native_dir = HERE / "native"
    native_dir.mkdir(exist_ok=True)
    assets = {}
    counts = Counter()
    missing = []

    for name in sorted(names):
        target = icons.get(name)
        if target is None:
            missing.append(name)
            continue
        source = source_path(target)
        if not source.is_file():
            raise FileNotFoundError(source)
        if file_hash(source) != target["source_sha256"]:
            raise ValueError(f"Frozen source changed: {source}")
        profile = "item" if target["treatment"] in {"inventory_items", "fitted_equipment_variants"} else "hud"
        if profile not in target["compositing"]["profiles"]:
            profile = target["compositing"]["profiles"][0]
        native_file = native_dir / (target["id"] + ".png")
        signature = f"{target['source_sha256']}:{profile}"
        if old_manifest.get(target["id"]) != signature or not native_file.is_file():
            with Image.open(source) as image:
                native = rendered(image, profile)
                if list(native.size) != target["native_size"]:
                    raise ValueError(f"Native dimensions changed: {source}")
                native.save(native_file, optimize=True)
            counts["native_written"] += 1
        new_manifest[target["id"]] = signature

        candidate_path = None
        expected_candidate_hash = None
        candidate_status = None
        candidate_flag = None
        prepared_alternatives = []
        cell = checkpoint.get(target["id"], {})
        if cell.get("status") == "accepted" and cell.get("artifact"):
            candidate_path = Path(cell["artifact"])
            expected_candidate_hash = cell.get("sha256")
            candidate_status = "accepted"
        elif target["source_path"].lower() in hud_approved:
            hud_row = hud_approved[target["source_path"].lower()]
            candidate_path = ROOT / hud_row["x2_review_png"]
            expected_candidate_hash = hud_row["x2_sha256"]
            candidate_status = "hud_approved"
        else:
            for part in audit.get(target["id"], {}).get("cells", []):
                for check in part.get("candidate_checks", []):
                    if check.get("exact_x2"):
                        candidate_path = Path(check["path"])
                        expected_candidate_hash = check.get("sha256")
                        candidate_status = "candidate"
                        candidate_flag = check.get("status")
                        break
                if candidate_path:
                    break
        if candidate_path is None and target["id"] in prepared:
            raw_record = prepared[target["id"]]
            for option in raw_record["alternatives"]:
                path = Path(option["path"])
                if not path.is_file() or file_hash(path) != option["sha256"]:
                    raise ValueError(f"Prepared candidate changed: {path}")
                if option["source_sha256"] != target["source_sha256"]:
                    raise ValueError(f"Prepared candidate source changed: {path}")
                raw_path = Path(option["raw"])
                if not raw_path.is_file() or file_hash(raw_path) != option["raw_sha256"]:
                    raise ValueError(f"Prepared raw sheet changed: {raw_path}")
                with Image.open(path) as image:
                    if list(image.size) != target["x2_size"]:
                        raise ValueError(f"Prepared candidate is not exact x2: {path}")
                prepared_alternatives.append({
                    "attempt": option["attempt"], "path": browser_path(path), "sha256": option["sha256"],
                    "raw": browser_path(raw_path), "rawRect": option["raw_rect"],
                    "sampling": option["actual_sampling"], "issues": option["issues"],
                    "matte": option["matte"]["method"], "operation": option["operation"],
                    "registrationFlags": option["registration_flags"],
                    "reuseOf": option.get("reuse_of"),
                })
            if prepared_alternatives:
                selected = next((option for option in prepared_alternatives
                                 if option["attempt"] == raw_record["selected"]), prepared_alternatives[0])
                candidate_path = Path(next(option["path"] for option in raw_record["alternatives"]
                                           if option["attempt"] == selected["attempt"]))
                expected_candidate_hash = selected["sha256"]
                candidate_status = "new_prepared" if raw_record.get("kind") == "new_generation" else "raw_prepared"
                candidate_flag = ", ".join(selected["issues"]) or "extracted_for_visual_review"
        if candidate_status == "candidate" and target["id"] in edge_repairs:
            repair = edge_repairs[target["id"]]
            original = Path(repair["original"])
            repaired = Path(repair["prepared"])
            if (candidate_path.resolve() != original.resolve() or
                    expected_candidate_hash != repair["original_sha256"] or
                    repair["source_sha256"] != target["source_sha256"] or
                    not repaired.is_file() or file_hash(repaired) != repair["prepared_sha256"] or
                    repair["size"] != target["x2_size"]):
                raise ValueError(f"Audited border repair changed: {target['id']}")
            original_url = browser_path(original)
            repaired_url = browser_path(repaired)
            common = {"raw": original_url, "rawRect": [0, 0, *repair["size"]], "sampling": [2, 2],
                      "registrationFlags": {}, "reuseOf": None}
            prepared_alternatives = [
                {**common, "attempt": "audited-original", "path": original_url,
                 "sha256": repair["original_sha256"], "issues": ["opaque_magenta_edge_detected"],
                 "matte": "audited_original", "operation": "Unaltered audited candidate"},
                {**common, "attempt": "border-repair", "path": repaired_url,
                 "sha256": repair["prepared_sha256"], "issues": ["opaque_magenta_edge_repaired"],
                 "matte": "opaque_edge_copy", "operation": "One-pixel border repair: " + ", ".join(repair["edges"])},
            ]
            candidate_path = repaired
            expected_candidate_hash = repair["prepared_sha256"]
            candidate_status = "border_repaired"
            candidate_flag = "Opaque magenta sheet border repaired: " + ", ".join(repair["edges"])
        candidate = None
        candidate_hash = None
        if candidate_path is not None:
            if not candidate_path.is_file():
                raise FileNotFoundError(candidate_path)
            with Image.open(candidate_path) as image:
                if list(image.size) != target["x2_size"]:
                    raise ValueError(f"Candidate is not exact x2: {candidate_path}")
            candidate = browser_path(candidate_path)
            candidate_hash = file_hash(candidate_path)
            if expected_candidate_hash and candidate_hash != expected_candidate_hash:
                raise ValueError(f"Candidate hash changed: {candidate_path}")
            counts[candidate_status] += 1
        attempts = sum(len(part.get("retained_attempts", [])) for part in audit.get(target["id"], {}).get("cells", []))
        assets[name] = {
            "id": target["id"], "name": name, "treatment": target["treatment"],
            "source": target["source_path"], "sourceHash": target["source_sha256"],
            "size": target["native_size"], "native": browser_path(native_file),
            "candidate": candidate, "candidateHash": candidate_hash,
            "candidateStatus": candidate_status, "candidateFlag": candidate_flag,
            "acceptanceMethod": cell.get("acceptance_method") if candidate_status == "accepted" else None,
            "preparedAlternatives": prepared_alternatives,
            "attempts": attempts,
            "active": usage.get(target["source_path"], {}).get("restoration_active", False),
            "usageStatus": usage.get(target["source_path"], {}).get("status", "not_audited"),
        }

    review_targets = [
        {"id": target["id"], "name": target["runtime_name"].lower(),
         "treatment": target["treatment"],
         "active": usage.get(target["source_path"], {}).get("restoration_active", False)}
        for target in equipment_targets
    ]
    character_assets = {
        name for person in people for name in (
            person["background"], person["body"], person["head"], person["leftClosed"],
            person["leftHold"], person["leftOpen"], person["rightFingers"],
            person["rightOpen"], person["rightHold"]
        ) if name
    }
    rendered_character_assets = {
        name for person in people for name in (
            person["background"], person["body"], person["leftClosed"],
            person["leftHold"], person["leftOpen"], person["rightFingers"],
            person["rightOpen"], person["rightHold"]
        ) if name
    }
    item_icons = {item["icon"] for item in item_rows}
    items_by_icon = {}
    for item in item_rows:
        items_by_icon.setdefault(item["icon"], []).append(item)
    doll_can_key = {
        "Armor": "armor", "Helm": "helm", "Belt": "belt",
        "Boots": "boots", "Cloak": "cloak",
    }

    def resolver_selects(target_name, item, type_id):
        slot = item["stat"]
        if slot not in BODY_STATS or type_id >= 5:
            return False
        can_key = doll_can_key.get(slot)
        if can_key and not types[type_id]["can"][can_key]:
            return False
        variant = 1 if slot == "Cloak" and type_id in {2, 3} else type_id + 1
        suffix = f"v{variant}"
        for has_main in (False, True):
            candidates = ([suffix, suffix + "a"] if has_main else [suffix + "a", suffix]) if slot == "Armor" else (
                [suffix + "a"] if slot == "Cloak" else [suffix]
            )
            selected = next((item["icon"] + variant_name for variant_name in candidates
                             if item["icon"] + variant_name in icons), item["icon"])
            if selected == target_name:
                return True
        return False

    for target in review_targets:
        name = target["name"]
        if target["treatment"] == "paperdoll_parts":
            target["resolverSelected"] = name in rendered_character_assets
            if not target["active"]:
                continue
            if name not in character_assets:
                raise ValueError(f"Active doll part has no character context: {name}")
        else:
            match = re.fullmatch(r"(.*)v([1-5])[ab]?", name)
            target["resolverSelected"] = bool(match) and any(
                resolver_selects(name, item, int(match.group(2)) - 1)
                for item in items_by_icon.get(match.group(1), [])
            )
            if not target["active"]:
                continue
            if match is None or match.group(1) not in item_icons or not any(
                person["type"] == int(match.group(2)) - 1 for person in people
            ):
                raise ValueError(f"Active fitted variant has no item/doll context: {name}")
    document = {
        "schema": "openyamm-paperdoll-review-v1",
        "sources": {
            "characterData": "assets_dev/engine/data_tables/character_data.txt",
            "dollTypes": "assets_dev/engine/data_tables/doll_types.txt",
            "items": "assets_dev/engine/data_tables/items.txt",
            "complexPictures": "assets_dev/engine/data_tables/complex_item_pictures.txt",
            "layout": "assets_dev/engine/ui/gameplay/character.yml",
        },
        "characters": people, "types": types, "items": item_rows, "complex": points,
        "layout": layout(), "assets": assets, "reviewTargets": review_targets,
        "missingNames": missing,
    }
    (HERE / "catalog.js").write_text(
        "window.PAPERDOLL_REVIEW_DATA = " + json.dumps(document, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )
    old = set(old_manifest) - set(new_manifest)
    for target_id in old:
        (native_dir / (target_id + ".png")).unlink(missing_ok=True)
    old_manifest_path.write_text(json.dumps(new_manifest, indent=2) + "\n")
    print(json.dumps({
        "characters": len(people), "items": len(item_rows), "review_targets": len(review_targets),
        "active_pending_targets": sum(t["active"] and assets[t["name"]]["candidateStatus"] not in {"accepted", "hud_approved"}
                                      for t in review_targets),
        "active_pending_resolver_selected": sum(
            t["active"] and t["resolverSelected"]
            and assets[t["name"]]["candidateStatus"] not in {"accepted", "hud_approved"}
            for t in review_targets
        ),
        "assets": len(assets), "missing_names": missing, "counts": counts,
    }, indent=2))


if __name__ == "__main__":
    main()
