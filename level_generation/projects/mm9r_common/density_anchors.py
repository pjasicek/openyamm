#!/usr/bin/env python3
"""
The balance session's density targets (tools/mm9_import_discovery/mm9_density_targets.yml, openyamm-95,
BALANCE_PLAN.md 3.6) as the converter's pack growth reads them: the targets name pack members by the actor_index of
the scenes installed on 2026-11-06 (the frozen pre-growth baseline); a conversion that grows packs renumbers nothing
it keeps, but to stay safe the members are frozen here as their DAT object names (the converter's `anchor`, from each
project's work/content.json of that same baseline conversion, checked 1:1 against the installed scenes).

    python3 level_generation/projects/mm9r_common/density_anchors.py      # writes density_anchors.json (once)
    python3 level_generation/projects/mm9r_common/density_anchors.py --maps STEM...   # after a --maps re-freeze

Run it only while the installed scenes are the baseline (before the first grown conversion); it refuses to overwrite
its output without --force, as the target file does.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
TARGETS = REPO / "tools/mm9_import_discovery/mm9_density_targets.yml"
OUTPUT = Path(__file__).resolve().parent / "density_anchors.json"


def refresh_maps(stems: list[str]) -> int:
    """Re-pin the members of these maps' packs after their targets were re-frozen (mm9_density_targets.py --maps):
    the anchors of the project's baseline actors (work/content.json without the converter's copies), checked 1:1
    against the installed scene's first actors."""
    targets = yaml.safe_load(TARGETS.read_text())
    out = json.loads(OUTPUT.read_text())
    for stem in stems:
        entry, project = targets["maps"][stem], REPO / "level_generation/projects" / out["maps"][stem]["project"]
        content = [a for a in json.loads((project / "work/content.json").read_text())["actors"] if "copy_of" not in a]
        scene = yaml.load((REPO / f"assets_dev/worlds/mm9/maps/{stem}.scene.yml").read_text(),
                          Loader=yaml.CSafeLoader)["initial_state"]["actors"]
        assert all(a["actor_index"] == s["actor_index"] and a["monster_id"] == s["monster_id"]
                   for a, s in zip(content, scene)), stem
        anchors = {a["actor_index"]: a["anchor"] for a in content}
        out["maps"][stem].update(chapter=entry.get("chapter"), factor=entry.get("factor"), packs=[
            {"members": [anchors[i] for i in pack["actors"]], "add": int(pack.get("add", 0)),
             "target": pack.get("target"), "capacity": pack.get("capacity")}
            for pack in entry.get("packs", []) if int(pack.get("add", 0)) > 0])
    OUTPUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"re-pinned {len(stems)} maps in {OUTPUT.name}")
    return 0


def main(argv: list[str]) -> int:
    if "--maps" in argv:
        return refresh_maps(argv[argv.index("--maps") + 1:])
    if OUTPUT.exists() and "--force" not in argv:
        raise SystemExit(f"{OUTPUT.name} exists (the frozen baseline); pass --force to rebuild it")
    targets = yaml.safe_load(TARGETS.read_text())
    stems = {}
    for overrides in sorted(REPO.glob("level_generation/projects/mm9r_*/overrides.yml")):
        stem = (yaml.safe_load(overrides.read_text()).get("map") or {}).get("stem")
        if stem:
            stems.setdefault(stem, overrides.parent)
    out = {"format_version": 1, "targets": str(TARGETS.relative_to(REPO)), "maps": {}}
    for stem, entry in targets["maps"].items():
        project = stems[stem]
        content = json.loads((project / "work/content.json").read_text())["actors"]
        scene = yaml.load((REPO / f"assets_editor_dev/worlds/mm9/maps/{stem}.scene.yml").read_text(),
                          Loader=yaml.CSafeLoader)["initial_state"]["actors"]
        assert len(content) == len(scene) and all(
            a["actor_index"] == s["actor_index"] and a["monster_id"] == s["monster_id"] for a, s in zip(content, scene)), stem
        anchors = {a["actor_index"]: a["anchor"] for a in content}
        out["maps"][stem] = {
            "project": project.name, "chapter": entry.get("chapter"), "factor": entry.get("factor"),
            "packs": [{"members": [anchors[i] for i in pack["actors"]], "add": int(pack.get("add", 0)),
                       "target": pack.get("target"), "capacity": pack.get("capacity")}
                      for pack in entry.get("packs", []) if int(pack.get("add", 0)) > 0],
        }
    OUTPUT.write_text(json.dumps(out, indent=1) + "\n")
    total = sum(p["add"] for m in out["maps"].values() for p in m["packs"])
    print(f"wrote {OUTPUT.name}: {len(out['maps'])} maps, {total} monsters to add")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
