#!/usr/bin/env python3
"""
Frosgard City's boat routes: the review root's `worlds/mm9/data_tables/transport_routes.txt` rows whose destination is
this map (the docks' boats of Sea's Fang, The Flying Bird and NPC 257's ship: mm9:transport/18/wednesday,
144/friday, 257/sunday) name `frosgardcity.odm`, which the BLV install removes from the review root: the game then
refuses the whole table at every start ("destination map reference is unresolved"). This rewrites those rows to the
BLV: `frosgardcity.blv`, the arrival at StartPoint0 as built (on the pier, facing 90 - ry), under the review tables
lock. Frosgard City is the first converted city that is a boat destination; the shared converter has no transport
writer (map-local, called by convert.py after each install).

    python3 level_generation/projects/mm9r_frosgardcity/transport.py      # apply to the review root now
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import review_root  # noqa: E402
from dungeon import tables  # noqa: E402

RELATIVE = "worlds/mm9/data_tables/transport_routes.txt"
MAP_ID = "world.mm9.map.frosgardcity"
START = "StartPoint0"


def rewrite(text: str, arrival: list, facing: float) -> tuple[str, int]:
    lines = text.split("\n")
    header = lines[0].rstrip("\r").split("\t")
    col = {name: k for k, name in enumerate(header)}
    changed = 0
    for k, line in enumerate(lines[1:], start=1):
        ending = "\r" if line.endswith("\r") else ""
        cells = line.rstrip("\r").split("\t")
        if len(cells) <= col["FacingYawUnits"] or cells[col["DestinationMap"]] != MAP_ID:
            continue
        if cells[col["DestinationStartPoint"]] != START:
            raise SystemExit(f"transport row {cells[0]}: start {cells[col['DestinationStartPoint']]} not handled")
        cells[col["DestinationMapFile"]] = "frosgardcity.blv"
        cells[col["ArrivalX"]], cells[col["ArrivalY"]], cells[col["ArrivalZ"]] = (str(int(v)) for v in arrival)
        cells[col["FacingDegrees"]] = str(facing)
        cells[col["FacingYawUnits"]] = str(int(round(facing / 360.0 * 2048)) % 2048)
        new = "\t".join(cells) + ending
        if new != line:
            lines[k] = new
            changed += 1
    return "\n".join(lines), changed


def apply(starts: list) -> int:
    start = next(s for s in starts if s["name"] == START)
    with tables.locked("review_tables.lock"):
        current = "\n".join(tables.read_lines(review_root.mirror_path(RELATIVE)))
        text, changed = rewrite(current, start["position"], start["direction_degrees"])
        if text != current:
            review_root.install(RELATIVE, text.encode())
    return changed


def main() -> int:
    report = json.loads((PROJECT / "work/build_report.json").read_text())
    print("transport rows rewritten:", apply(report["starts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
