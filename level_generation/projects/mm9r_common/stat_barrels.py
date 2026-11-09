#!/usr/bin/env python3
"""
MM9's stat barrels on the remade maps, MM6 style (user, 2026-11-04): only DAT objects of class `Barrel` (MM9's
drinkable barrels, MM9_BARREL_INTEGRATION_GOAL.md) can be drunk from, and they show MM6's barrel with its liquid
overlay by state (engine/models/decoration_overlays.yml `bigbarel`; Global.lua events 268-275 by the hint "barrel",
game/gameplay/InteractiveDecorationRules.cpp). Every other MM9 decoration row is a plain decoration.

The props projects' tables.py gave MM9 rows the hints "barrel", "keg", "bucket", "cauldron" and "campfire", which the
engine reads as MMerge's interactive decorations: any barrel, keg or bucket on a shelf was drinkable and hearth logs
gave food. `--apply` writes into assets_dev (temporary file, then rename: the files are hard-linked into the review
roots, which need review_root.refresh() afterwards):

  - worlds/mm9/data_tables/decoration_data.txt: those hints on MM9 rows become NEUTRAL_HINTS; the stat barrel rows
    (STAT_ROWS, hint "barrel") added at the next free numbers;
  - worlds/mm9/rendering/sprite_frame_data_world_decorations.yml: a 'pending' sprite per stat row;
  - worlds/mm9/models/indoor_decorations.yml: the stat rows' bindings (MM6's barrel at MM9's barrel height);
  - worlds/mm9/models/decoration_overlays.yml (written here): the stat rows' liquids, the bigbarel overlays.

The dungeon converter places class `Barrel` props on the stat row of their scale (stat_decoration(), used by
dungeon/content.py); the remade maps are converted again afterwards. The props projects' HINTS use the neutral hints.

    python3 level_generation/projects/mm9r_common/stat_barrels.py            # dry run: what would change
    python3 level_generation/projects/mm9r_common/stat_barrels.py --apply
"""

from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORLD = ROOT / "assets_dev/worlds/mm9"
DECORATIONS = WORLD / "data_tables/decoration_data.txt"
SPRITES = WORLD / "rendering/sprite_frame_data_world_decorations.yml"
BINDINGS = WORLD / "models/indoor_decorations.yml"
OVERLAYS = WORLD / "models/decoration_overlays.yml"
ROW_RANGE = (2001, 2999)            # world.yml idRanges decorations
SPRITE_RANGE = (24801, 26999)

# Hints the engine reads as interactive families (InteractiveDecorationRules.cpp classifyFamily) -> plain ones.
NEUTRAL_HINTS = {"barrel": "wooden barrel", "keg": "beer keg", "bucket": "wooden bucket", "cauldron": "iron cauldron",
                 "campfire": "burning logs"}

BARREL_MODEL = "engine/models/mm6_deco_barrel.glb"
# Stat rows: name -> (height, collision radius). Heights are MM9's own barrel rows' (mm9_barrel03 122.9, its x100
# variant 81.9); MM6's barrel is 0.70 wide for 0.871 tall, so the radius is 0.40 x height.
STAT_ROWS = {"mm9_statbarrel": (122.9, 49), "mm9_statbarrel_x100": (81.9, 33)}
# The decoration a class Barrel prop had (props.json) -> its stat row.
STAT_FOR = {"mm9_barrel03": "mm9_statbarrel", "mm9_barrel": "mm9_statbarrel",
            "mm9_barrel03_x100": "mm9_statbarrel_x100", "mm9_barrel_x100": "mm9_statbarrel_x100"}
LIQUIDS = ["red", "yellow", "blue", "orange", "green", "purple", "white"]


def stat_decoration(entry: dict) -> str:
    """The decoration a props.json entry is placed with: a class Barrel prop on a barrel model takes its stat row
    (other Barrel-class models, Boot Camp's suit of armour, stay as they are and are not drinkable)."""
    if entry.get("class") == "Barrel":
        return STAT_FOR.get(entry["decoration"].lower(), entry["decoration"])
    return entry["decoration"]


def write(path: Path, text: str) -> None:
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".")
    with os.fdopen(fd, "w", encoding="latin-1" if path.suffix == ".txt" else "utf-8", newline="") as handle:
        handle.write(text)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def plan():
    lines = DECORATIONS.read_text(encoding="latin-1").split("\n")
    names, numbers, sprite_ids, hints = set(), [], [], []
    for index, line in enumerate(lines):
        cells = line.split("\t")
        if len(cells) < 13 or not cells[0].strip().isdigit():
            continue
        number = int(cells[0])
        if not ROW_RANGE[0] <= number <= ROW_RANGE[1]:
            continue
        names.add(cells[1].strip().lower())
        numbers.append(number)
        sprite_ids.append(int(cells[12]))
        hint = cells[2].strip().lower()
        if hint in NEUTRAL_HINTS and cells[1].strip().lower() not in STAT_ROWS:
            cells[2] = NEUTRAL_HINTS[hint]
            hints.append((cells[1], hint, cells[2]))
            lines[index] = "\t".join(cells)
    added = []
    number, sprite = max(numbers), max(sprite_ids)
    for name, (height, radius) in STAT_ROWS.items():
        if name in names:
            continue
        number, sprite = number + 1, sprite + 1
        assert number <= ROW_RANGE[1] and sprite <= SPRITE_RANGE[1]
        added.append((number, name, height, radius, sprite))
    return lines, hints, added


def apply(lines, added) -> None:
    trailing = lines[-1] == ""
    body = lines[:-1] if trailing else lines
    for number, name, height, radius, sprite in added:
        body.append("\t".join([str(number), name, "barrel", "0", str(radius), str(int(round(height))), "0", "0", "0",
                               "0", "0", "0", str(sprite), "-"]))
    write(DECORATIONS, "\n".join(body) + ("\n" if trailing else ""))

    sprites = SPRITES.read_text()
    bindings = BINDINGS.read_text()
    for number, name, height, radius, sprite in added:
        if f'sprite_name: "{name}"' not in sprites:
            sprites = sprites.rstrip("\n") + (f"\n  - sprite_id: {sprite}\n    sprite_name: \"{name}\"\n    frames:\n"
                                              f"      - texture_name: \"pending\"\n        frame_length_raw: 0\n"
                                              f"        flags: [First]\n        scale: 1.0\n")
    for name, (height, radius) in STAT_ROWS.items():
        if not re.search(rf"^  - name: {name}$", bindings, re.M):
            bindings = bindings.rstrip("\n") + (f"\n  - name: {name}\n    model: {BARREL_MODEL}\n"
                                                f"    height: {height}\n")
    write(SPRITES, sprites)
    write(BINDINGS, bindings)

    text = ["# The MM9 world's decoration overlays (extends engine/models/decoration_overlays.yml; see its header).",
            "# Written by level_generation/projects/mm9r_common/stat_barrels.py: MM9's stat barrels (class Barrel) are",
            "# MM6's barrel with bigbarel's liquids by state (empty, then red Might, yellow Accuracy, blue Personality,",
            "# orange Intellect, green Endurance, purple Speed and white Luck; Global.lua events 268-275).",
            "overlays:"]
    for name in STAT_ROWS:
        text += [f"  - name: {name}", "    states:", "      - null"]
        text += [f"      - engine/models/mm6_deco_barrel_liquid_{colour}.glb" for colour in LIQUIDS]
    write(OVERLAYS, "\n".join(text) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args()
    lines, hints, added = plan()
    for name, old, new in hints:
        print(f"hint {name}: {old} -> {new}")
    for number, name, height, radius, sprite in added:
        print(f"row {number} {name}: height {height}, radius {radius}, sprite {sprite}")
    if arguments.apply:
        apply(lines, added)
        print("written")


if __name__ == "__main__":
    main()
