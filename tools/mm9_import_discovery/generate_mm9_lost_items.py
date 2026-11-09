#!/usr/bin/env python3
"""Write worlds/mm9/dialogue/lost_items.yml: the items Hjordisa the Hag (RUDE 132, Guberland) gives back to a party
that lost them (devdocs/mm9_rework/PLACED_ITEMS_PLAN.md section 4).

The items are every item an MM9 script checks or takes: `hasitem` / `takeitem` in the original SCR scripts, and
`MM9.hasItem` / `MM9.takeItem` in the converted map scripts (which also cover the items a script's parameters name,
such as DoorLock.scr's key). The engine (game/mm9/Mm9RudeDialogue.cpp) gives back the first of them the party has
owned, holds nowhere now and has not handed in (`MM9.takeItem` records the hand-in, mm9_common.lua).

    python3 tools/mm9_import_discovery/generate_mm9_lost_items.py
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "mm9/extracted/SCRIPTS/SCRIPTS"
MAP_LUA = ROOT / "assets_dev/worlds/mm9/events/maps"
ITEM_IDS = ROOT / "assets_dev/worlds/mm9/state/item_ids.yml"
OUTPUT = ROOT / "assets_dev/worlds/mm9/dialogue/lost_items.yml"
KEEPERS = [132]             # Hjordisa the Hag, in her Guberland cave

SCR_ITEM = re.compile(r"^\s*(hasitem|takeitem)\s*,?\s*(\d+)", re.IGNORECASE)
LUA_ITEM = re.compile(r"MM9\.(hasItem|takeItem)\((\d+)")


def checked_items() -> set[int]:
    items = set()
    for path in SCRIPTS.iterdir():
        if path.suffix.lower() in (".scr", ".inc"):
            for line in path.read_text(errors="replace").splitlines():
                match = SCR_ITEM.match(line.split(";")[0])
                if match:
                    items.add(int(match.group(2)))
    for path in MAP_LUA.glob("*.lua"):
        items.update(int(match.group(2)) for match in LUA_ITEM.finditer(path.read_text()))
    return items


def main() -> int:
    mapping = {int(m["raw_mm9_id"]): int(m["item_id"])
               for m in yaml.load(ITEM_IDS.read_text(), Loader=yaml.CSafeLoader)["mappings"]}
    items = sorted(checked_items())
    missing = [raw for raw in items if raw not in mapping]
    rows = "\n".join(f"  - {{raw: {raw}, item_id: {mapping[raw]}}}" for raw in items if raw in mapping)
    OUTPUT.write_text(
        "# Hjordisa the Hag's lost items (devdocs/mm9_rework/PLACED_ITEMS_PLAN.md section 4). Written by\n"
        "# tools/mm9_import_discovery/generate_mm9_lost_items.py; do not edit by hand. Read by the RUDE dialogue table\n"
        "# (game/mm9/Mm9RudeDialogue.cpp loadLostItemsText): the keepers' first page offers \"We've lost something.\",\n"
        "# which gives back the first item here the party has owned, holds nowhere now and has not handed in\n"
        "# (the named global MM9.HandedIn.<raw>, set by mm9_common.lua MM9.takeItem through evt.SetGlobalVar).\n"
        "format_version: 1\n"
        f"keepers: [{', '.join(map(str, KEEPERS))}]\n"
        "items:\n" + rows + "\n")
    print(f"{OUTPUT.relative_to(ROOT)}: {len(items) - len(missing)} items"
          + (f"; not in the item table: {missing}" if missing else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
