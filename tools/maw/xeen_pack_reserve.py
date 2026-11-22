#!/usr/bin/env python3
"""MAW's density in the World of Xeen: each indoor map's pack reserve (devdocs/maw/XEEN_SUPPORT.md section 4).

Most of Xeen's 69 indoor maps place every monster as a scene actor (Map Studio's builds, no spawn points), so MAW's
group sizes cannot grow them. As MM9's (tools/maw/mm9_pack_reserve.py), each gets a MAW overlay,
assets_dev/engine/rulesets/maw/maps/<stem>_zz_maw.scene.yml, `initial_state.pack_reserve`: copies of its monsters
beside them, by the MM9 converter's placement and the shared rules of tools/maw/pack_reserve.py (crowds, the
arrivals' leeway), for up to the map's highest density factor (balance.yml `density`, Beyond Madness 2.0).

What is Xeen's here:
- Packs: the map's monsters in clusters (within 700 units, one sector); Xeen has no density targets.
- Monsters: actors of a hostile Xeen row (the table's Hst above 0, or placed aggressive) that are not people (npc id)
  and not left out of the clearing (balance.yml `completion_exclude`: the octopods).
- Never copied (besides the converter's rules: identities, actors hidden at the start, actors the map's Lua or
  cinematics name): bosses (source/monsters.yml `bosses`) and actors whose name the map's Lua quotes. A pack of only
  those gives its share to the map's other packs.
- Scripted groups take copies: Xeen's Lua addresses a group only as a whole (evt.SetMonGroupBit to hide, show or calm
  it, group kill checks), and a copy keeps its member's group, so it hides, shows, calms and must be killed with it
  (MM9's `reserve_lua_groups` for every group; a member hidden at the start is still never copied).
- Arrivals kept clear: the scene's start points, every evt.MoveToMap onto the map (any Xeen script, and the map's own
  in-map teleports), the scripts' arrival tables ({x, y, z, yaw, "<map>"}), the data tables' landings (`map` with
  `at`, transport_locations.txt) and balance.yml `arrivals`.
- Not given a reserve: the arena, the finale and the towns (SKIP), and the maps with spawn points (MM6-MM8's
  monster spawns in the BLV, 15 of Cloudside's dungeons): MAW's group sizes grow their spawned groups by difficulty,
  and their placed actors stay as they are, as on MAW's own MM6-MM8 dungeons.

A map rebuilt since its reserve was made does not use it (the game says so) and `xeen_balance.py --check` fails:
map lanes run this tool again after a rebuild.

    python3 tools/maw/xeen_pack_reserve.py [stems ...]       # every indoor Xeen map when none are given
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_reserve as core  # noqa: E402
from pack_reserve import ROOT, density, parse_blv_file  # noqa: E402
import xeen_balance  # noqa: E402

WORLD = ROOT / "assets_dev/worlds/xeen"
MAPS = WORLD / "maps"
EVENTS = WORLD / "events"
BALANCE = yaml.safe_load(xeen_balance.BALANCE.read_text())
MARKER = "tools/maw/xeen_pack_reserve.py writes this file"
INVISIBLE, AGGRESSOR = 0x00010000, 0x00080000
# Maps where copies make no sense.
SKIP = {
    "xeen_xd20": "the Warzone: an arena whose fighters are drawn by tier (MAW's arena rules)",
    "xeen_p5": "the finale (Clouds of the Ancients)",
    "xeen_xd17": "Shangri-La, a hidden town without monsters",
    "xeen_dd25": "Bosco's Hall, a town without monsters",
}


def monster_rows() -> dict[int, dict]:
    rows = {}
    for row in xeen_balance.table_rows(WORLD / "data_tables/monster_data.txt"):
        rows[int(row[0])] = {"name": row[1], "picture": row[2].strip(), "level": int(row[3] or 0),
                             "hostile": int(row[12] or 0) > 0 if row[12].strip().isdigit() else False}
    return rows


ROWS = monster_rows()


def boss_rows() -> set[int]:
    """Every boss row of source/monsters.yml (each family's `bosses`)."""
    source = yaml.load((WORLD / "source/monsters.yml").read_text(), Loader=yaml.CSafeLoader)
    found = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "bosses" and isinstance(value, list):
                    found.update(int(boss["id"]) for boss in value if isinstance(boss, dict) and "id" in boss)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(source)
    return found


BOSSES = boss_rows()


def left_out(map_file: str, row: int) -> bool:
    exclusions = list(BALANCE.get("completion_exclude") or []) + list(
        core.map_entry(BALANCE, map_file).get("completion_exclude") or [])
    monster = ROWS.get(row)
    return bool(monster) and xeen_balance.excluded(exclusions, row, monster)


def is_monster(map_file: str, actor: dict) -> bool:
    """A monster of the map's density: a hostile Xeen row, no person, not left out of the clearing."""
    row = int(actor.get("monster_info_id") or 0)
    monster = ROWS.get(row)
    if not actor.get("monster_id") or monster is None or actor.get("npc_id"):
        return False
    hostile = monster["hostile"] or bool(int(actor.get("attributes", 0)) & AGGRESSOR)
    return hostile and not left_out(map_file, row)


class XeenReferences(density.References):
    """The converter's References without a DAT world or Lua groups (module docstring): bosses and actors whose name
    the map's Lua quotes."""

    def __init__(self, script: str, cinematics, bosses: set[str], names: dict[str, str]):
        super().__init__(lua_names=density.lua_strings(script), scene_indices=density.cinematic_actors(cinematics))
        self.bosses, self.names = bosses, names

    def reason(self, anchor):
        if anchor in self.bosses:
            return "boss"
        name = self.names.get(anchor, "").lower()
        if name and name in self.lua_names:
            return "named by the map Lua"
        return None


def liquid_textures(blv: dict, scene: dict) -> set[str]:
    """The map's face textures that the engine draws as a liquid (engine/liquids/liquids.yml entries for every world
    or for Xeen, by name or prefix)."""
    table = yaml.safe_load((ROOT / "assets_dev/engine/liquids/liquids.yml").read_text())
    names, prefixes = set(), []
    for liquid in table["liquids"]:
        if liquid.get("worlds") and "xeen" not in liquid["worlds"]:
            continue
        match = liquid.get("match") or {}
        names |= {name.lower() for name in match.get("texture_names") or []}
        prefixes += [prefix.lower() for prefix in match.get("texture_prefixes") or []]
    textures = {str(face["texture_name"]).lower() for face in blv["faces"]}
    textures |= {str(o["texture_name"]).lower() for o in (scene.get("initial_state") or {}).get(
        "face_attribute_overrides") or [] if o.get("texture_name")}
    return {texture for texture in textures if texture in names or any(texture.startswith(p) for p in prefixes)}


def scripts() -> dict[Path, str]:
    return {path: path.read_text() for path in sorted(EVENTS.rglob("*.lua"))}


SCRIPTS = scripts()


def landings(node, map_file: str, spots: list) -> None:
    """The data tables' landings on the map: any mapping with `map` the map's file and `at` [x, y, z]."""
    if isinstance(node, dict):
        if str(node.get("map", "")).lower() == map_file and isinstance(node.get("at"), list) and len(node["at"]) >= 3:
            spots.append(tuple(int(value) for value in node["at"][:3]))
        for value in node.values():
            landings(value, map_file, spots)
    elif isinstance(node, list):
        for value in node:
            landings(value, map_file, spots)


def arrivals_of(stem: str, scene: dict) -> list[tuple]:
    map_file = f"{stem}.blv"
    spots = [tuple(point["position"]) for point in scene.get("party_start_points") or []]
    name = re.escape(map_file)
    to_map = re.compile(r'evt\.MoveToMap\((-?\d+), (-?\d+), (-?\d+),[^)]*"' + name + '"')
    table = re.compile(r'\{\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*-?\d+,\s*"' + name + '"')
    in_map = re.compile(r"evt\.MoveToMap\((-?\d+), (-?\d+), (-?\d+), -?\d+, -?\d+, -?\d+, -?\d+, -?\d+\)")
    for path, text in SCRIPTS.items():
        for pattern in (to_map, table) + ((in_map,) if path.stem == stem else ()):
            spots += [tuple(int(value) for value in match.groups()) for match in pattern.finditer(text)]
    for path in sorted((WORLD / "data_tables").glob("*.yml")):
        landings(yaml.load(path.read_text(), Loader=yaml.CSafeLoader), map_file, spots)
    with open(WORLD / "data_tables/transport_locations.txt", encoding="utf-8", errors="replace") as file:
        for row in csv.reader(file, delimiter="\t"):
            if len(row) > 12 and row[1].strip().lower() == map_file:
                spots.append((int(row[10]), int(row[11]), int(row[12])))
    spots += [tuple(spot) for spot in core.map_entry(BALANCE, map_file).get("arrivals") or []]
    return spots


def reserve(stem: str) -> tuple[dict | None, str]:
    map_file = f"{stem}.blv"
    if stem in SKIP:
        return None, SKIP[stem]
    blv = parse_blv_file(MAPS / map_file)["payload"]
    if blv["spawn_count"]:
        return None, f"{blv['spawn_count']} spawn points: MAW's group sizes grow them"
    scene = yaml.load((MAPS / f"{stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    actors = scene["initial_state"]["actors"]
    if any(actor["actor_index"] != index for index, actor in enumerate(actors)):
        return None, "the scene's actor indices are not its order"
    top = core.highest_factor(BALANCE, map_file)
    anchors = {f"xeen_actor_{actor['actor_index']}": actor["actor_index"] for actor in actors}
    anchor_of = {index: anchor for anchor, index in anchors.items()}
    monsters = [actor["actor_index"] for actor in actors if is_monster(map_file, actor)]
    if not monsters:
        return None, "no monsters"
    packs = core.pack_sizes([{"members": [anchor_of[index] for index in cluster]}
                             for cluster in core.scene_clusters(actors, monsters)],
                            lambda pack: len(pack["members"]), top)

    world = core.CrowdedWorld(blv, scene, liquid_textures(blv, scene))
    lua_path = EVENTS / "maps" / f"{stem}.lua"
    lua = lua_path.read_text() if lua_path.is_file() else ""
    cinematics_path = MAPS / f"{stem}.cinematics.yml"
    cinematics = yaml.load(cinematics_path.read_text(), Loader=yaml.CSafeLoader) if cinematics_path.is_file() else None
    references = XeenReferences(
        lua, cinematics, {anchor_of[a["actor_index"]] for a in actors if int(a.get("monster_info_id") or 0) in BOSSES},
        {anchor_of[a["actor_index"]]: str(a.get("name") or "") for a in actors})
    copies, result = density.grow(stem, actors, anchors, packs, world, density.lua_actor_indices(lua), None,
                                  references, core.arrival_zones(arrivals_of(stem, scene)))
    pack_reserve, note = core.ranked_reserve(actors, copies, result, len(monsters), top)
    skipped = {}
    for pack in result["packs"]:
        for why in pack["skipped"].values():
            skipped[why] = skipped.get(why, 0) + 1
    if skipped:
        note += f"; not copied: {skipped}"
    return pack_reserve, note


def write(stem: str, pack_reserve: dict) -> Path:
    return core.write(stem, pack_reserve, [
        f"# MAW's pack reserve for Xeen's {stem} ({MARKER}; do not edit): copies of its",
        "# monsters for MAW's denser difficulties, by rising from_factor (devdocs/maw/XEEN_SUPPORT.md section 4)."])


def indoor_stems() -> list[str]:
    return sorted(path.stem for path in MAPS.glob("*.blv"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stems", nargs="*")
    arguments = parser.parse_args(argv)
    stems = arguments.stems or indoor_stems()
    for stem in stems:
        if not (MAPS / f"{stem}.blv").is_file():
            raise SystemExit(f"{stem}: no indoor Xeen map")
        pack_reserve, note = reserve(stem)
        if pack_reserve is None or not pack_reserve["actors"]:
            core.remove_written(stem, MARKER)
            print(f"{stem:14} no reserve: {note}")
            continue
        path = write(stem, pack_reserve)
        print(f"{stem:14} {note} -> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
