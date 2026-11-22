"""MAW's pack reserves, the part every world shares (devdocs/maw/MM9_BALANCE_DESIGN.md section 4,
devdocs/maw/XEEN_SUPPORT.md section 4).

A world whose dungeons place every monster as a scene actor (no spawn points) cannot grow by MAW's group sizes. Its
pack reserve is a MAW scene overlay, assets_dev/engine/rulesets/maw/maps/<stem>_zz_maw.scene.yml,
`initial_state.pack_reserve`: copies of the map's packs' members placed beside them by the MM9 converter's placement
(level_generation/projects/mm9r_common/dungeon/density.py: floor, sector, walls, doors and movers, ladders, event
faces, water, scripted members left alone) with the crowd rule and the arrivals' leeway below, for up to the map's
highest density factor. A difficulty whose factor (balance.yml `density`) reaches an entry's `from_factor` adds it at
a map's first fill and each refill (MonsterRules::packDensityFactor, MapDeltaData::packReserve). `scene_actors` and
`scene_check` name the scene it was placed against: a map rebuilt since does not use its reserve until its world's
tool runs again, and the world's balance check fails.

Each world has its own front end for what differs (where its packs and scripting come from, which actors are its
monsters, where the party arrives): tools/maw/mm9_pack_reserve.py and tools/maw/xeen_pack_reserve.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "level_generation/projects/mm9r_common"))
from density_dry_check import density, parse_blv_file  # noqa: E402,F401

OVERLAYS = ROOT / "assets_dev/engine/rulesets/maw/maps"
# The largest factor a reserve is made for: the map's highest (its `density` times the file's highest difficulty or
# challenge factor), at most MAX_FACTOR.
MAX_FACTOR = 8.0
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


def arrival_zones(spots) -> list[dict]:
    """grow()'s forced arrivals (quota 0) round each spot the party arrives at, without repeats."""
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
    """FNV-1a 64 of "monster_id,x,y,z;" per scene actor (IndoorSceneYml.cpp checks the same)."""
    value = 0xcbf29ce484222325
    for actor in actors:
        position = actor["position"]
        for byte in f"{actor['monster_id']},{position['x']},{position['y']},{position['z']};".encode():
            value ^= byte
            value = (value * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def map_entry(balance: dict, map_file: str) -> dict:
    return (balance.get("maps") or {}).get(map_file) or {}


def lua_groups(balance: dict, map_file: str) -> set[int]:
    """balance.yml `reserve_lua_groups`: groups the map's Lua turns or wakes only as a whole (MM9's Honks)."""
    return set(map_entry(balance, map_file).get("reserve_lua_groups") or [])


def highest_factor(balance: dict, map_file: str) -> float:
    """The highest density factor the map can have (balance.yml `density`, the map's own times the file's highest)."""
    density_block = balance.get("density") or {}
    factors = list((density_block.get("difficulty") or {}).values()) + list(
        (density_block.get("challenge") or {}).values())
    own = float(map_entry(balance, map_file).get("density", 1.0))
    return min(MAX_FACTOR, own * max(factors or [1.0]))


def pack_sizes(packs: list[dict], grown_of, top: float) -> list[dict]:
    """Each pack's wanted copies for factor `top` (its grown size x (top - 1)) and its room: its own copies and as
    many again, so the copies of packs that cannot grow (scripted members) find a place with the others."""
    out = []
    for pack in packs:
        grown = grown_of(pack)
        add = round(grown * (top - 1))
        out.append({"members": pack["members"], "add": add, "capacity": grown + 2 * add})
    return out


def ranked_reserve(actors: list[dict], copies: list[dict], result: dict, monsters: int, top: float) -> tuple[dict,
                                                                                                              str]:
    """The reserve from grow()'s copies: the packs' copies interleaved by each pack's share and numbered map-wide, the
    k-th copy's factor 1 + k / N (N the map's monsters), so a factor f adds (f - 1) x N of them."""
    by_index = {c["actor_index"]: c for c in copies}
    ranked = []
    for order, pack in enumerate(result["packs"]):
        grown = max(1, pack["capacity"] - pack["wanted"])
        for k, placed in enumerate(pack["copies"], start=1):
            ranked.append((k / grown, order, by_index[placed["actor_index"]]))
    ranked.sort(key=lambda item: (item[0], item[1]))
    monsters = max(1, monsters)
    entries = [{"from_factor": round(1 + (rank + 1) / monsters, 4), "actor": record}
               for rank, (_, _, record) in enumerate(ranked)]
    summary = result["summary"]
    reach = 1 + len(entries) / monsters
    note = (f"{len(entries)} of {summary['wanted_adds']} copies placed for {monsters} monsters: up to x{reach:.2f}"
            + (f" ({summary['unplaced_reasons']})" if summary["unplaced_adds"] else ""))
    return {"scene_actors": len(actors), "scene_check": scene_check(actors), "max_factor": top,
            "monsters": monsters, "actors": entries}, note


def write(stem: str, pack_reserve: dict, header: list[str]) -> Path:
    """The overlay: `header` (comment lines naming the tool that writes it), then the reserve."""
    path = OVERLAYS / f"{stem}_zz_maw.scene.yml"
    lines = header + [
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


def remove_written(stem: str, marker: str) -> None:
    """A reserve the world's tool wrote before (its header names `marker`) goes: the map has none now."""
    stale = OVERLAYS / f"{stem}_zz_maw.scene.yml"
    if stale.exists() and marker in stale.read_text()[:300]:
        stale.unlink()


def reserve_state(stem: str, actors: list[dict]) -> dict | None:
    """The map's installed reserve against its scene's actors: copies, monsters, reach and whether the scene is still
    the one it was placed against (None: no reserve)."""
    path = OVERLAYS / f"{stem}_zz_maw.scene.yml"
    if not path.exists():
        return None
    reserve = (yaml.load(path.read_text(), Loader=yaml.CSafeLoader).get("initial_state") or {}).get("pack_reserve")
    if not reserve:
        return None
    fresh = reserve["scene_actors"] == len(actors) and reserve["scene_check"] == scene_check(actors)
    return {"copies": len(reserve["actors"]), "monsters": reserve["monsters"], "fresh": fresh,
            "reach": 1 + len(reserve["actors"]) / max(1, reserve["monsters"])}
