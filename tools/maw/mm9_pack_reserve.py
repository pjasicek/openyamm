#!/usr/bin/env python3
"""MAW's density in MM9: each map's pack reserve, extra copies of its packs' members for MAW's harder difficulties.

MM9's maps have no spawn points, so MAW's group sizes (1-3 to 3-6 by difficulty) cannot act on them; its monsters are
scene actors, their packs already grown by the converter (level_generation/projects/mm9r_common/dungeon/density.py).
This tool runs that same placement (every rule of it: floor, sector, walls, doors and movers, ladders, event faces,
water, pod launchers, forced arrivals, scripted members left alone) on each installed map, beside the actors it already
has, for up to MAX_FACTOR times its monsters, and writes the copies as the map's MAW overlay,
assets_dev/engine/rulesets/maw/maps/<stem>_zz_maw.scene.yml, `initial_state.pack_reserve`:

- `actors`: the copies, by rising `from_factor`: a difficulty whose density factor (balance.yml `density`) reaches it
  adds the copy at a map's first fill and each refill (MonsterRules::packDensityFactor, MapDeltaData::packReserve).
  The copies of all packs are interleaved by each pack's share, and the k-th copy's factor is 1 + k / N (N the map's
  hostile monsters), so a factor f adds (f - 1) x N of them, as far as the reserve goes.
- `scene_actors`, `scene_check`: the scene they were placed against (FNV-1a 64 of "monster_id,x,y,z;" per actor). A
  map rebuilt since does not use its reserve (the game says so) until this tool runs again; mm9_balance.py --check
  finds such reserves.

The reserve is MAW's: Standard games never read it, and the converters never write it.

    python3 tools/maw/mm9_pack_reserve.py [stems ...]        # every map with packs when none are given
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "level_generation/projects/mm9r_common"))
import density_dry_check as dry  # noqa: E402
from density_dry_check import density, parse_blv_file, Project, Source  # noqa: E402

OVERLAYS = ROOT / "assets_dev/engine/rulesets/maw/maps"
TARGETS = yaml.load((ROOT / json.loads(density.ANCHORS.read_text())["targets"]).read_text(), Loader=yaml.CSafeLoader)
BALANCE = yaml.safe_load((ROOT / "assets_dev/engine/rulesets/maw/worlds/mm9/balance.yml").read_text())


def monster_pictures() -> dict[int, tuple[str, str]]:
    pictures = {}
    for line in (ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt").read_text(errors="replace").splitlines():
        fields = line.split("\t")
        if fields and fields[0].isdigit():
            pictures[int(fields[0])] = (fields[1], fields[2])
    return pictures


PICTURES = monster_pictures()


def left_out(stem: str, monster_id: int) -> bool:
    """A monster balance.yml leaves out of the map's clearing (the sea's guards): never copied, never counted."""
    exclusions = list(BALANCE.get("completion_exclude") or []) + list(
        ((BALANCE.get("maps") or {}).get(f"{stem}.blv") or {}).get("completion_exclude") or [])
    name, picture = PICTURES.get(monster_id, ("", ""))
    for value in map(str, exclusions):
        family = len(picture) == len(value) + 2 and picture.startswith(value) and picture[len(value)] == " "
        if value == str(monster_id) or value in (name, picture) or family:
            return True
    return False
# The largest factor a reserve is made for: the map's highest (its `density` times the file's highest difficulty or
# challenge factor), at most MAX_FACTOR.
MAX_FACTOR = 8.0
# Maps whose Lua counts the placed actors (Yanmir's Fort's PLACED: an actor past them is a summoned bug).
SKIP = {"yanmirsfort": "its Lua takes every actor past the scene's for a summoned bug (PLACED)"}
# No crowds (the user, 2026-11-09: never ten monsters in a few steps): a copy is refused where CROWD_MAX monsters,
# placed or copied, already stand within CROWD_RADIUS (height counted double).
CROWD_RADIUS, CROWD_MAX = 400.0, 6
# Leeway where the party arrives (a map's start points, the spots other maps and teleports put it): no copy within
# ARRIVAL_RADIUS of one, so a party is never dropped into a crowd with no room to move (the user, 2026-11-09).
ARRIVAL_RADIUS = 1500.0
# Monsters standing apart from every pack (the targets' packs cover only part of a map) form packs of their own:
# those within CLUSTER_DISTANCE of each other, in one sector.
CLUSTER_DISTANCE = 700.0


class CrowdedWorld(density.World):
    """The converter's placement with the crowd rule on top: a spot is refused when CROWD_MAX monsters already stand
    within CROWD_RADIUS of it, or when one of those already has CROWD_MAX others that near (so copies cannot ring a
    monster either). The neighbour counts follow the placed actors as grow() appends them."""

    def __init__(self, *arguments):
        super().__init__(*arguments)
        self.positions, self.counts, self.seen = [], [], 0

    @staticmethod
    def near(a, b) -> bool:
        dx, dy, dz = a[0] - b[0], a[1] - b[1], (a[2] - b[2]) * 2
        return dx * dx + dy * dy + dz * dz <= CROWD_RADIUS * CROWD_RADIUS

    def follow(self, placed_actors) -> None:
        for actor in placed_actors[self.seen:]:
            self.seen += 1
            if not actor.get("monster_id") or actor.get("mm9_civilian") or actor.get("mm9_guard"):
                continue
            position = actor["position"]
            spot = (position["x"], position["y"], position["z"])
            count = 0
            for index, other in enumerate(self.positions):
                if self.near(spot, other):
                    self.counts[index] += 1
                    count += 1
            self.positions.append(spot)
            self.counts.append(count)

    def check(self, member, body, x, y, placed_actors):
        spot, reason = super().check(member, body, x, y, placed_actors)
        if spot is None:
            return spot, reason
        self.follow(placed_actors)
        near = [index for index, other in enumerate(self.positions) if self.near(spot, other)]
        if len(near) >= CROWD_MAX or any(self.counts[index] >= CROWD_MAX for index in near):
            return None, "crowded"
        return spot, reason


def arrivals_of(stem: str, scene: dict) -> list[dict]:
    """Where the party arrives on the map, each a spot no copy may stand near (grow's forced arrivals, quota 0)."""
    spots = [tuple(point["position"]) for point in scene.get("party_start_points") or []]
    for line in (ROOT / "assets_dev/worlds/mm9/data_tables/map_transitions.txt").read_text().splitlines()[1:]:
        fields = line.split("\t")
        if len(fields) > 18 and fields[13].lower() == f"{stem}.blv":
            spots.append((int(fields[16]), int(fields[17]), int(fields[18])))
    for path in dry.EVENTS.glob("*.lua"):
        for match in re.finditer(r'evt\.MoveToMap\((-?\d+), (-?\d+), (-?\d+),[^)]*"' + re.escape(stem) + r'\.blv"',
                                 path.read_text()):
            spots.append(tuple(int(value) for value in match.groups()))
    own = ((BALANCE.get("maps") or {}).get(f"{stem}.blv") or {}).get("arrivals") or []
    spots += [tuple(spot) for spot in own]
    return [{"name": f"arrival{index}", "at": list(spot), "radius": ARRIVAL_RADIUS, "copies": 0}
            for index, spot in enumerate(dict.fromkeys(spots))]


def scene_clusters(actors: list[dict], free: list[int]) -> list[list[int]]:
    """The actor indices `free` grouped: within CLUSTER_DISTANCE (height counted double) and in one sector."""
    parent = {index: index for index in free}

    def root(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for i, a in enumerate(free):
        for b in free[i + 1:]:
            pa, pb = actors[a]["position"], actors[b]["position"]
            dx, dy, dz = pa["x"] - pb["x"], pa["y"] - pb["y"], (pa["z"] - pb["z"]) * 2
            if actors[a].get("sector_id") == actors[b].get("sector_id") \
                    and dx * dx + dy * dy + dz * dz <= CLUSTER_DISTANCE * CLUSTER_DISTANCE:
                parent[root(a)] = root(b)
    clusters: dict[int, list[int]] = {}
    for index in free:
        clusters.setdefault(root(index), []).append(index)
    return list(clusters.values())


def scene_check(actors: list[dict]) -> str:
    value = 0xcbf29ce484222325
    for actor in actors:
        position = actor["position"]
        for byte in f"{actor['monster_id']},{position['x']},{position['y']},{position['z']};".encode():
            value ^= byte
            value = (value * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def lua_groups(stem: str) -> set[int]:
    """balance.yml `reserve_lua_groups`: groups the map's Lua turns or wakes only as a whole (the Honks)."""
    return set(((BALANCE.get("maps") or {}).get(f"{stem}.blv") or {}).get("reserve_lua_groups") or [])


def is_monster(stem: str, actor: dict) -> bool:
    """A monster of the map's density: hostile, or of a group that turns hostile as a whole; not townsfolk, guards,
    animals or what balance.yml leaves out of the clearing."""
    return bool(actor.get("monster_id")) and not actor.get("mm9_civilian") and not actor.get("mm9_guard") \
        and (int(actor.get("hostility_type", 0)) != 0 or actor.get("group") in lua_groups(stem)) \
        and not left_out(stem, int(actor["monster_id"]))


def monsters_of(stem: str, actors: list[dict]) -> int:
    return sum(1 for a in actors if is_monster(stem, a))


def highest_factor(stem: str) -> float:
    """The highest density factor the map can have (balance.yml `density`, the map's own times the file's highest)."""
    density = BALANCE.get("density") or {}
    factors = list((density.get("difficulty") or {}).values()) + list((density.get("challenge") or {}).values())
    own = float(((BALANCE.get("maps") or {}).get(f"{stem}.blv") or {}).get("density", 1.0))
    return min(MAX_FACTOR, own * max(factors or [1.0]))


def reserve(stem: str, entry: dict) -> tuple[dict | None, str]:
    project = ROOT / "level_generation/projects" / entry["project"]
    top = highest_factor(stem)
    overrides = yaml.safe_load((project / "overrides.yml").read_text()) or {}
    if not (overrides.get("map") or {}).get("density", True):
        return None, "growth off for the map"
    if stem in SKIP:
        return None, SKIP[stem]
    scene = yaml.load((dry.MAPS / f"{stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    actors = scene["initial_state"]["actors"]
    content = json.loads((project / "work/content.json").read_text())["actors"]
    members = [a for a in content if "copy_of" not in a]
    copies_of = Counter(a["copy_of"] for a in content if "copy_of" in a)
    rows = {a["actor_index"]: a["monster_id"] for a in content}
    if len(content) != len(actors) or any(rows.get(s["actor_index"]) != s["monster_id"] for s in actors):
        return None, "work/content.json does not match the installed scene (convert the map again first)"
    anchors = {a["anchor"]: a["actor_index"] for a in members}

    # The packs: the grown maps' (density_anchors.json, by DAT name), else the targets' (by the actor indices of the
    # ungrown scene, density targets `packs`), each member checked against the monster the targets name.
    source_packs = density.map_packs(stem)
    if not source_packs:
        by_index = {a["actor_index"]: a["anchor"] for a in members}
        for pack in (TARGETS["maps"].get(stem) or {}).get("packs") or []:
            names = set(pack.get("monsters") or [])
            anchors_of = [by_index[i] for i in pack["actors"]
                          if i in by_index and i < len(actors) and actors[i].get("name") in names]
            if anchors_of:
                source_packs.append({"members": anchors_of})
    # The monsters no pack holds, in packs of their own (scene_clusters).
    in_packs = {anchors[anchor] for pack in source_packs for anchor in pack["members"] if anchor in anchors}
    copy_indices = {a["actor_index"] for a in content if "copy_of" in a}
    by_index = {a["actor_index"]: a["anchor"] for a in members}
    free = [a["actor_index"] for a in actors
            if a["actor_index"] in by_index and a["actor_index"] not in in_packs and a["actor_index"] not in copy_indices
            and is_monster(stem, a)]
    source_packs += [{"members": [by_index[index] for index in cluster]} for cluster in scene_clusters(actors, free)]
    packs = []
    for pack in source_packs:
        kept = [anchor for anchor in pack["members"]
                if anchor not in anchors or not left_out(stem, int(actors[anchors[anchor]]["monster_id"]))]
        if not kept:
            continue
        pack = dict(pack, members=kept)
        grown = sum(1 + copies_of[anchor] for anchor in pack["members"] if anchor in anchors)
        add = round(grown * (top - 1))
        # Room for its own copies and as many again, so the copies of packs that cannot grow (scripted members) find
        # a place with the others.
        packs.append({"members": pack["members"], "add": add, "capacity": grown + 2 * add})

    world = CrowdedWorld(parse_blv_file(dry.MAPS / f"{stem}.blv")["payload"], scene, density.liquid_textures())
    directories = density.lua_name_tables(dry.project_hooks(project))
    lua = (dry.EVENTS / f"{stem}.lua").read_text()
    cinematics_path = dry.MAPS / f"{stem}.cinematics.yml"
    cinematics = yaml.load(cinematics_path.read_text(), Loader=yaml.CSafeLoader) if cinematics_path.is_file() else None
    references = density.References.of(Source(Project.load(project, install=False)), lua, directories, cinematics)
    # Groups the map's Lua only turns hostile or wakes as a whole may take copies: they turn with the group
    # (balance.yml `reserve_lua_groups`: the Temple of Honk's Honks).
    # Their members' MM9 script is that group's (the Honks' HonkHostility.inc), so it does not hold them back either.
    groups = lua_groups(stem)
    references.lua_groups -= groups
    for anchor, index in anchors.items():
        key = anchor.lower()
        if actors[index].get("group") in groups and key in references.dat:
            cls, properties = references.dat[key]
            references.dat[key] = (cls, dict(properties, ScriptName=""))
    arrivals = list((overrides.get("map") or {}).get("density_arrivals") or ()) + arrivals_of(stem, scene)
    copies, result = density.grow(stem, actors, anchors, packs, world, density.lua_actor_indices(lua, directories),
                                  None, references, arrivals)

    # Interleave the packs' copies by each pack's share, then number them map-wide.
    by_index = {c["actor_index"]: c for c in copies}
    ranked = []
    for order, pack in enumerate(result["packs"]):
        grown = max(1, pack["capacity"] - pack["wanted"])
        for k, placed in enumerate(pack["copies"], start=1):
            ranked.append((k / grown, order, by_index[placed["actor_index"]]))
    ranked.sort(key=lambda item: (item[0], item[1]))
    monsters = max(1, monsters_of(stem, actors))
    entries = [{"from_factor": round(1 + (rank + 1) / monsters, 4), "actor": record}
               for rank, (_, _, record) in enumerate(ranked)]
    summary = result["summary"]
    reach = 1 + len(entries) / monsters
    note = (f"{len(entries)} of {summary['wanted_adds']} copies placed for {monsters} monsters: up to x{reach:.2f}"
            + (f" ({summary['unplaced_reasons']})" if summary["unplaced_adds"] else ""))
    return {"scene_actors": len(actors), "scene_check": scene_check(actors), "max_factor": top,
            "monsters": monsters, "actors": entries}, note


def write(stem: str, pack_reserve: dict) -> Path:
    path = OVERLAYS / f"{stem}_zz_maw.scene.yml"
    lines = [
        f"# MAW's pack reserve for MM9's {stem} (tools/maw/mm9_pack_reserve.py writes this file; do not edit): copies of",
        "# its packs' members for MAW's denser difficulties, by rising from_factor (devdocs/maw/MM9_BALANCE_DESIGN.md).",
        "format_version: 1",
        "kind: indoor_scene_overlay",
        "initial_state:",
        "  pack_reserve:",
        f"    scene_actors: {pack_reserve['scene_actors']}",
        f"    scene_check: \"{pack_reserve['scene_check']}\"",
        f"    max_factor: {pack_reserve['max_factor']}",
        f"    monsters: {pack_reserve['monsters']}",
        "    actors:",
    ]
    lines += [f"      - {json.dumps(entry, separators=(',', ':'))}" for entry in pack_reserve["actors"]]
    path.write_text("\n".join(lines) + "\n")
    return path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stems", nargs="*")
    arguments = parser.parse_args(argv)
    maps = json.loads(density.ANCHORS.read_text())["maps"]
    stems = arguments.stems or list(maps)
    for stem in stems:
        if stem not in maps:
            raise SystemExit(f"{stem}: not in {density.ANCHORS.name}")
        pack_reserve, note = reserve(stem, maps[stem])
        if pack_reserve is None or not pack_reserve["actors"]:
            # A reserve this tool wrote before goes: the map has none now.
            stale = OVERLAYS / f"{stem}_zz_maw.scene.yml"
            if stale.exists() and "tools/maw/mm9_pack_reserve.py writes this file" in stale.read_text()[:300]:
                stale.unlink()
            print(f"{stem:22} no reserve: {note}")
            continue
        path = write(stem, pack_reserve)
        print(f"{stem:22} {note} -> {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
