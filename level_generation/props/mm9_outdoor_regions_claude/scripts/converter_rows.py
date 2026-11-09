#!/usr/bin/env python3
"""The decoration rows the shared converter's MM9 object rules place (FINAL_REBUILD_WORK.md phase 3):

- the flat letter (scrollflat.py builds the model; dungeon/content.py `flat_letter`): `mm9_scrollflat`, plus
  `mm9_scrollflat_xNNN` for every other scale an upright letter lying flat in MM9 uses (BookLetter.scr bDown 1 on a
  props.json entry of the upright `mm9_scroll`, any map). Rows as mm9_scroll's (hint, no collision); binding height =
  the flat GLB's height (work/scrollflat_meta.json height_units) x scale;
- the always-on fires' flames (dungeon/objects.py `fire_decoration`): `mm9_gatefire_xNNN` at FireScale / 12 of the gate
  fire (any map's always-on Fire), rows as mm9_gatefire_x8's (unlit), binding height 130.7 x NNN / 100.

Appends only, refuses a name the engine has, and
writes each file as a new file renamed over the old one (the review mirror hard-links assets_dev; refresh it after).
Run under the decorations lock, so the next free row is read inside it:

    flock -x level_generation/projects/mm9r_common/locks/mm9_decorations.lock \
        python3 level_generation/props/mm9_outdoor_regions_claude/scripts/converter_rows.py [--apply]

"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
WORLD = REPO / "assets_dev/worlds/mm9"
DECORATIONS = WORLD / "data_tables/decoration_data.txt"
SPRITES = WORLD / "rendering/sprite_frame_data_world_decorations.yml"
BINDINGS = WORLD / "models/indoor_decorations.yml"
ENGINE_DECORATIONS = REPO / "assets_dev/engine/data_tables/decoration_data.txt"
SPRITE_RANGE2 = (26001, 26999)
MODEL = "worlds/mm9/models/mm9_deco_scrollflat.glb"
FIRE_MODEL = "worlds/mm9/models/mm9_deco_gatefire.glb"
GATE_FIRE_HEIGHT = 130.7            # mm9_gatefire's binding height (Anskram's ImpGateFire, FireScale 12)
UPRIGHT = re.compile(r"^mm9_scroll(_x(\d+))?$")
sys.path.insert(0, str(REPO / "tools/mm9_import_discovery"))


def flat_scales() -> set:
    """The scales (x 100) of every upright letter with bDown 1 in any map's props.json."""
    from transcode_mm9_dat_to_odm import read_dat_world
    scales = set()
    for path in sorted((REPO / "level_generation/projects").glob("mm9r_*/props.json")):
        entries = json.loads(path.read_text())
        letters = [e for e in entries if UPRIGHT.match(e.get("decoration", ""))]
        if not letters:
            continue
        stem = path.parent.name[len("mm9r_"):].removesuffix("_blv")
        objects = read_dat_world(REPO / f"mm9/extracted/WORLDS/WORLDS/{stem.upper()}.dat").objects
        for e in letters:
            p = {x.name: x.value for x in objects[int(e["source_object"])].properties}
            tokens = str(p.get("ScriptParams") or "").split()
            if "bookletter" in str(p.get("ScriptName") or "").lower() and len(tokens) > 2 and tokens[2] == "1":
                match = UPRIGHT.match(e["decoration"])
                scales.add(int(match.group(2)) if match.group(2) else 100)
    return scales


def fire_rows() -> set:
    """The gate fire rows (names) every always-on Fire of any map takes (dungeon/objects.py)."""
    from transcode_mm9_dat_to_odm import read_dat_world
    sys.path.insert(0, str(REPO / "level_generation/projects/mm9r_common"))
    from dungeon.objects import always_on_fires, fire_decoration
    names = set()
    for dat in sorted((REPO / "mm9/extracted/WORLDS/WORLDS").glob("*.dat")):
        world = read_dat_world(dat)

        class Source:
            objects = []
        for index, o in enumerate(world.objects):
            properties = {x.name: x.value for x in o.properties}
            Source.objects.append({"index": index, "class": o.name, "name": str(properties.get("Name", "")),
                                   "properties": properties})
        names |= {fire_decoration(o["properties"]) for o in always_on_fires(Source)}
    return names


def write(path: Path, text: str) -> None:
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    with os.fdopen(handle, "wb") as stream:
        stream.write(text.encode("latin-1"))
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def main() -> int:
    height = json.loads((HERE / "work/scrollflat_meta.json").read_text())["height_units"]
    rows = [line.split("\t") for line in DECORATIONS.read_text(encoding="latin-1").splitlines()
            if line.split("\t")[0].strip().isdigit()]
    names = {r[1].strip().lower() for r in rows}
    engine = {line.split("\t")[1].strip().lower() for line in ENGINE_DECORATIONS.read_text(encoding="latin-1")
              .splitlines() if line.split("\t")[0].strip().isdigit()}
    upright = next(r for r in rows if r[1].strip().lower() == "mm9_scroll")
    declared = yaml.safe_load((WORLD / "world.yml").read_text())["idRanges"]["decorations"]
    sprites = (yaml.load(SPRITES.read_text(), Loader=yaml.CSafeLoader) or {}).get("sprites") or []
    next_id = max(int(r[0]) for r in rows) + 1
    next_sprite = max([s["sprite_id"] + len(s["frames"]) for s in sprites] + [SPRITE_RANGE2[0]])
    bound = {b["name"].lower() for b in (yaml.safe_load(BINDINGS.read_text()) or {}).get("decorations") or []}
    new_rows, new_sprites, new_bindings = [], [], []
    gate = next(r for r in rows if r[1].strip().lower() == "mm9_gatefire_x8")
    wanted = [("mm9_scrollflat" if scale == 100 else f"mm9_scrollflat_x{scale}", upright, MODEL, height * scale / 100)
              for scale in sorted(flat_scales(), key=lambda s: (s != 100, s))]
    wanted += [(name, gate, FIRE_MODEL, GATE_FIRE_HEIGHT * int(name.rsplit("_x", 1)[1]) / 100)
               for name in sorted(fire_rows()) if "_x" in name]
    for name, template, model, binding_height in wanted:
        if name in engine:
            sys.exit(f"{name} is an engine decoration: nothing written")
        if name in names:
            continue
        if not declared["begin"] <= next_id <= declared["end"] or not next_sprite <= SPRITE_RANGE2[1]:
            sys.exit(f"{name}: row {next_id} or sprite {next_sprite} out of range")
        cells = list(template)
        cells[0], cells[1], cells[12] = str(next_id), name, str(next_sprite)
        new_rows.append("\t".join(cells) + "\n")
        new_sprites.append(f"  - sprite_id: {next_sprite}\n    sprite_name: \"{name}\"\n    frames:\n"
                           f"      - texture_name: \"pending\"\n        frame_length_raw: 0\n"
                           f"        flags: [First]\n        scale: 1.0\n")
        if name not in bound:
            new_bindings.append(f"  - name: {name}\n    model: {model}\n    height: {round(binding_height, 1)}\n"
                                f"    yaw: facing\n")
        next_id, next_sprite = next_id + 1, next_sprite + 1
    if new_bindings:
        new_bindings.insert(0, "  # --- MM9 shared object rules (level_generation/props/mm9_outdoor_regions_claude/scripts/"
                               "converter_rows.py) ---\n")
    print("".join(new_rows + new_bindings) or "nothing to add")
    if "--apply" not in sys.argv:
        print("dry run; --apply appends")
        return 0
    for path, text in ((DECORATIONS, new_rows), (SPRITES, new_sprites), (BINDINGS, new_bindings)):
        if text:
            current = path.read_text(encoding="latin-1")
            write(path, current + ("" if current.endswith("\n") else "\n") + "".join(text))
            print("APPENDED", path.relative_to(REPO), len(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
