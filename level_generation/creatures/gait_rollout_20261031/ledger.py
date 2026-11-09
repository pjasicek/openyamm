#!/usr/bin/env python3
"""Ledger of the 2026-10-31 gait rollout: every installed 3D actor model of MM6-MM8 whose walk/run/sprint fails the
gait gate's window (Standard wandering and chasing, MAW chasing; claude_shared/postprocess/gait_gate.py), with the
facts a work package needs. Writes ledger.json and prints a table.

    python3 level_generation/creatures/gait_rollout_20261031/ledger.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / "claude_shared/postprocess"))
sys.path.insert(0, str(HERE.parent / "claude_shared/floor"))
import gait_audit  # noqa: E402
import glb_pose  # noqa: E402

FOOT = ("foot", "toe", "ankle", "hoof", "paw", "tarsus")


def body(path):
    """footless / biped / multi-legged from the rig's foot joints (stride_audit.FOOT names)."""
    glb = glb_pose.Glb(ROOT / "assets_source" / path)
    names = [node.get("name", "").lower() for node in glb.json["nodes"]]
    feet = [name for name in names if any(part in name for part in FOOT) and "toe" not in name
            and "end" not in name]
    if not feet:
        return "footless", 0
    return ("biped" if len(feet) <= 2 else "multi-legged"), len(feet)


def main():
    low, high = gait_audit.WINDOW
    models = {}
    for world in ("mm6", "mm7", "mm8"):
        standard = {r["descriptor"]: r for r in gait_audit.audit(world, None)}
        maw = {r["descriptor"]: r for r in gait_audit.audit(world, None, ruleset="maw")}
        for name, result in standard.items():
            key = f"{world}/{Path(result['model']).name}"
            entry = models.setdefault(key, {"world": world, "model": result["model"], "descriptors": [],
                                            "problems": [], "walk": result["walk_speed"],
                                            "run": result["run_speed"], "sprint": result["sprint_speed"]})
            entry["descriptors"].append(name)
            other = maw[name]
            rows = [("standard wander", result["rows"][0]), ("standard chase", result["rows"][1]),
                    ("maw chase", other["rows"][1])]
            if not result["flagged"] and not other["flagged"]:
                continue
            for label, row in rows:
                rate = row["rate"] * row["slide"]
                if not low <= rate <= high:
                    entry["problems"].append(f"{name}: {label} {row['clip']} x{rate:.2f} at {row['speed']}")
    flagged = {key: entry for key, entry in models.items() if entry["problems"]}
    for key, entry in flagged.items():
        entry["body"], entry["feet"] = body(entry["model"])
        entry["projects"] = sorted(p.parent.name for p in (HERE.parent).glob("*/README.md")
                                   if Path(entry["model"]).name in p.read_text(errors="ignore"))
    (HERE / "ledger.json").write_text(json.dumps(flagged, indent=1))
    by = defaultdict(int)
    for key, entry in sorted(flagged.items()):
        by[entry["body"]] += 1
        print(f"{key:24} {entry['body']:12} {len(entry['problems']):2} problems  e.g. {entry['problems'][0]}")
    print(f"\n{len(flagged)} models: " + ", ".join(f"{k} {v}" for k, v in by.items()))


if __name__ == "__main__":
    main()
