#!/usr/bin/env python3
"""MM9 map scripts edited only where they are installed (AGENTS.md, "MM9 map Lua").

Every assets_dev/worlds/mm9/events/maps/<stem>.lua is written by its map's converter (level_generation/projects/
mm9r_<map>*/convert.py, citylua.py, regionlua.py, ...), which installs it into the map's review root; promotion
(output/mm9_rework/promotion_*/promote.py) copies it from there to assets_dev. A fix belongs in the converter, installed
into both. For each map this compares the installed script with

- its own review root (output/mm9_rework/isleofashes_blv_root for the regions, Bootcamp and the Afterworld,
  output/mm9_rework/assets_dev for the rest, as promote.py has them): a difference is an edit in one place only (lost
  on the next promotion or conversion) or a conversion not installed in both;
- the converter's last installing build (level_generation/projects/mm9r_*/work/runtime/<stem>.lua): informational, a
  scratch build writes elsewhere.

    python3 tools/mm9_import_discovery/check_mm9_map_lua.py            # exit 1 when a map differs from its root

Whether a converter still writes the installed script, exactly:
    python3 level_generation/projects/mm9r_<map>/convert.py --scratch /tmp/<dir>
    diff assets_dev/worlds/mm9/events/maps/<stem>.lua /tmp/<dir>/runtime/<stem>.lua
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLED = ROOT / "assets_dev/worlds/mm9/events/maps"
ROOT_A = ROOT / "output/mm9_rework/assets_dev"
ROOT_B = ROOT / "output/mm9_rework/isleofashes_blv_root"
# promote.py's B_MAPS: the maps converted into the Isle of Ashes BLV root
B_MAPS = set("afterworld lindisfarne thronheim frosgard bootcamp mountainpass guberland drangheim thjorgard sturmford "
             "isleofashes yorwick".split())
PROJECTS = ROOT / "level_generation/projects"


def stamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")


def main() -> int:
    scripts = sorted(INSTALLED.glob("*.lua"))
    differing = 0
    for script in scripts:
        stem = script.stem
        data = script.read_bytes()
        own = (ROOT_B if stem in B_MAPS else ROOT_A) / "worlds/mm9/events/maps" / script.name
        builds = sorted(PROJECTS.glob(f"mm9r_*/work/runtime/{script.name}"))
        own_ok = own.is_file() and own.read_bytes() == data
        build_notes = [f"{b.parents[2].name} {'same' if b.read_bytes() == data else 'differs'} ({stamp(b)})"
                       for b in builds]
        if own_ok:
            continue
        differing += 1
        own_note = f"{own.parents[4].name} {stamp(own)}" if own.is_file() else f"{own.parents[4].name} missing"
        print(f"{stem}: installed {stamp(script)}, its review root {own_note}; last builds: "
              + (", ".join(build_notes) or "none"))
    print(f"{differing} of {len(scripts)} MM9 map scripts differ from their own review root")
    return 1 if differing else 0


if __name__ == "__main__":
    sys.exit(main())
