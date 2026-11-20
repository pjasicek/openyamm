"""Audit jewelry coverage and stage inventory-only footprints without changing accepted art."""

import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUT = HERE / "jewelry_inventory_20260926"
STATS = {"Gauntlets", "Amulet", "Ring"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slots(pixels):
    return max(1, min(14, 1 + (max(14, pixels) - 14) // 32))


def main():
    data = json.loads((HERE / "catalog.js").read_text().split("=", 1)[1].strip().removesuffix(";"))
    table = ROOT / "assets_dev/engine/data_tables/items.txt"
    rows = list(csv.reader(io.StringIO(table.read_text(encoding="cp1252")), delimiter="\t"))
    definitions = {int(r[0]): r for r in rows if r and r[0].isdigit() and len(r) > 4 and r[4] in STATS}
    items = [item for item in data["items"] if item["stat"] in STATS]
    assert set(definitions) == {item["id"] for item in items}, "Browser omits source table items"
    snapshot = json.loads((OUT / "browser_state.original.json").read_text())
    decisions = json.loads(snapshot["storage"]["openyamm-paperdoll-context-review-v1"])
    choices = json.loads(snapshot["storage"]["openyamm-paperdoll-context-review-attempt-v1"])
    placements = json.loads(snapshot["storage"]["openyamm-paperdoll-placement-v1"])
    records = []
    shared = defaultdict(list)
    for item in items:
        asset = data["assets"][item["icon"]]
        selected = next((option for option in asset["preparedAlternatives"]
                         if option["attempt"] == choices.get(asset["id"])), None)
        candidate = selected["path"] if selected else asset["candidate"]
        candidate_hash = selected["sha256"] if selected else asset["candidateHash"]
        path = HERE / unquote(candidate)
        assert digest(path) == candidate_hash
        width, height = asset["size"]
        with Image.open(path) as image:
            assert image.mode == "RGBA" and image.size == (width * 2, height * 2)
            assert image.getchannel("A").getbbox()
        current = [slots(width), slots(height)]
        row = definitions[item["id"]]
        with Image.open(HERE / unquote(asset["native"])) as original:
            rgba = original.convert("RGBA")
            pixels = bytearray(rgba.tobytes())
            for offset in range(0, len(pixels), 4):
                if pixels[offset + 3] == 0:
                    pixels[offset:offset + 3] = b"\0\0\0"
            visual_hash = hashlib.sha256(bytes(pixels)).hexdigest()
        if len(row) > 30 and row[29].isdigit() and row[30].isdigit() and int(row[29]) and int(row[30]):
            current = [max(1, min(14, int(row[29]))), max(1, min(9, int(row[30])))]
        target = [1, 1 if item["stat"] == "Ring" else
                  2 if item["stat"] == "Gauntlets" else min(2, current[1])]
        scale = min(1.0, target[0] * 32 / width, target[1] * 32 / height)
        # Bound the full canvas, not only alpha, so tips/edges and future matte fixes cannot cross a cell.
        draw_size = [width * scale, height * scale]
        assert draw_size[0] <= target[0] * 32 + 1e-9 and draw_size[1] <= target[1] * 32 + 1e-9
        decision = decisions.get(asset["id"])
        status = "canonical" if asset["candidateStatus"] in {"accepted", "hud_approved"} else "unreviewed"
        if decision:
            placement = decision.get("placement")
            saved = placements.get(placement["key"]) if placement else None
            same_placement = not placement or placement["delta"] == (saved["delta"] if saved else [0, 0])
            status = decision["decision"] if decision["source_hash"] == asset["sourceHash"] and \
                decision["candidate_hash"] == candidate_hash and same_placement else "stale"
        records.append({"item_id": item["id"], "name": item["name"], "icon": item["icon"],
                        "stat": item["stat"], "target": asset["id"], "source_hash": asset["sourceHash"],
                        "native_size": asset["size"], "current_cells": current, "cells": target,
                        "cell_size": 32, "draw_scale": scale, "draw_size": draw_size,
                        "candidate": candidate, "candidate_hash": candidate_hash,
                        "material": row[8], "native_visual_sha256": visual_hash,
                        "review_status": status, "note": decision.get("note", "") if decision else ""})
        shared[(item["stat"], width, height, visual_hash)].append(records[-1])
    assert len(records) == 79
    groups = []
    for key, members in shared.items():
        # Numeric materials are normal-tier items. Keep artifact/relic/special aliases under that normal image.
        representative = min(members, key=lambda r: (not r["material"].isdigit(), r["item_id"]))
        group_id = f"{key[0].lower()}:{key[3][:16]}"
        for member in members:
            assert member["cells"] == representative["cells"]
            member["shared_group"] = group_id
            member["representative_item_id"] = representative["item_id"]
        flags = [r for r in members if r["review_status"] == "flag"]
        group_status = "flag" if flags else representative["review_status"]
        groups.append({"id": group_id, "classification": "exact_native_image_aliases" if len(members) > 1 else "unique_image",
                       "representative_item_id": representative["item_id"], "representative_target": representative["target"],
                       "shared_candidate": representative["candidate"], "shared_candidate_hash": representative["candidate_hash"],
                       "review_status": group_status, "members": [r["item_id"] for r in members],
                       "different_restored_candidates": len({r["candidate_hash"] for r in members}) > 1})
    summary = {stat: {"total": sum(r["stat"] == stat for r in records),
                      "review": dict(Counter(r["review_status"] for r in records if r["stat"] == stat)),
                      "cells": dict(Counter("x".join(map(str, r["cells"])) for r in records if r["stat"] == stat))}
               for stat in sorted(STATS)}
    changed = [r for r in records if r["cells"] != r["current_cells"]]
    report = {"schema": "openyamm-jewelry-inventory-fit-v1", "staging_only": True,
              "captured_at": snapshot["captured_at"], "cell_size": 32, "summary": summary,
              "policy": "Inventory only: center full native canvas, shrink uniformly to assigned cells, never enlarge.",
              "runtime_tables_modified": False, "artwork_modified": False,
              "table_sha256": digest(table), "ledger_sha256": digest(HERE.parent / "checkpoint/state.json"),
              "browser_snapshot_sha256": digest(OUT / "browser_state.original.json"),
              "records": records, "changed_footprints": len(changed), "groups": groups,
              "group_summary": {"items": len(records), "distinct_images": len(groups),
                                "duplicate_items": len(records) - len(groups),
                                "alias_families": sum(len(g["members"]) > 1 for g in groups),
                                "divergent_restorations": sum(g["different_restored_candidates"] for g in groups),
                                "review": dict(Counter(g["review_status"] for g in groups))}}
    (OUT / "inventory_fit.json").write_text(json.dumps(report, indent=2) + "\n")
    (OUT / "inventory_fit.js").write_text("window.PAPERDOLL_INVENTORY_FIT = " + json.dumps(report) + ";\n")
    fields = ["item_id", "icon", "name", "old_inventory_width", "old_inventory_height",
              "inventory_width", "inventory_height", "draw_scale", "source_hash"]
    for filename, subset in [("inventory_fit.csv", records), ("items_table_proposals.csv", changed)]:
        with (OUT / filename).open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for record in subset:
                writer.writerow({key: record[key] for key in ("item_id", "icon", "name", "draw_scale", "source_hash")} |
                                dict(zip(fields[3:7], record["current_cells"] + record["cells"])))
    with (OUT / "shared_image_proposals.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["item_id", "name", "icon", "representative_item_id", "representative_target",
                         "shared_candidate", "shared_candidate_hash", "previous_candidate_hash", "consumers"])
        by_id = {g["id"]: g for g in groups}
        for record in records:
            group = by_id[record["shared_group"]]
            writer.writerow([record["item_id"], record["name"], record["icon"], group["representative_item_id"],
                             group["representative_target"], group["shared_candidate"], group["shared_candidate_hash"],
                             record["candidate_hash"], "inventory|jewelry_overlay"])
    print(json.dumps({"summary": summary, "changed_footprints": len(changed),
                      "uniformly_reduced": sum(r["draw_scale"] < 1 for r in records),
                      "group_summary": report["group_summary"]}, indent=2))


if __name__ == "__main__":
    main()
