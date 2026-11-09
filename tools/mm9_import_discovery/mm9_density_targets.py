#!/usr/bin/env python3
"""MM9 density targets for the map rebuild (devdocs/mm9_rework/BALANCE_PLAN.md section 3.6).

Writes tools/mm9_import_discovery/mm9_density_targets.yml from the rebuilt maps as they stand before growth
(assets_dev/worlds/mm9/maps/<stem>.scene.yml, initial_state.actors). The file is the frozen baseline: the rework
converters (level_generation/projects/mm9r_<project>) read it and add `add` monsters to each pack; this script refuses
to overwrite it unless --force, so growth is never applied on top of grown maps.

Counting rule (counted_actor): a placed actor counts when its MM9 monster row belongs to a combat family of
mm9_monster_balance.py, it is not a civilian or an NPC (npc_id 0), it is hostile (hostility_type not 0; the Temple of
Honk's Honks, placed non-hostile until the story turns them, count), it is not a passive scripted actor
(mm9_ai.profile.passive), it is not a swimmer on an outdoor map (modifiers.yml `movement: swim`, the Jellyspore family
and the Sea Monsters: outdoors they stay in the sea and lakes, where the party need not fight them; in a dungeon's pools
and channels they count; the user, 2026-11-07) and its level is below 150 (Njam, the Dragon King). Packs: counted actors within 1,200 units of
each other (single linkage, height counted twice). A pack's target is floor(size x the chapter factor), capped by the
room check (at most a third of the free space where its roomiest member stands: 16 rays to the walls, 1,536 units at
most); the map's remainder up to round(count x factor) goes one monster at a time to the packs with room left, largest
fraction first, then the roomiest.
"""
from __future__ import annotations

import argparse
import functools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "util"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from map_export import parse_blv_file  # noqa: E402
from mm9_monster_balance import family_of  # noqa: E402

MAPS = ROOT / "assets_dev/worlds/mm9/maps"
MONSTERS = ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"
MODIFIERS = ROOT / "assets_dev/worlds/mm9/modifiers.yml"
ANCHORS = ROOT / "level_generation/projects/mm9r_common/density_anchors.json"
OUTPUT = Path(__file__).resolve().with_name("mm9_density_targets.yml")

# The story's acts (the user, 2026-11-07): 1 the prologue; 2 uniting the clans, an open act (the six Jarls' twelve
# mainline quests, both promotions and the side quests on the way: Yanmir's Fort is Tryggva's, Klusos's House, the
# Dungeon of Secrets, Verhoffin Ruins and the Lich Lab are second-tier promotions); 3 the war (the war council to
# Arslegard's gate); 4 the finale. The key is still called a chapter in the targets file.
CHAPTER_MAPS = {
    1: "isleofashes sturmford sturmfordcity beethoven anskramkeep",
    2: "drangheim drangheimprison drangheimcity guberland guberlandcity thjoradmine tasaracademy "
       "thjorgard thjorgardcity thronheim thronheimcity frosgard frosgardcity mountainpass lindisfarne "
       "lindisfarnemonastery chasmofthedead ruinedtemple inventastorca thearena dookscastle "
       "yanmirsfort klusoshouse traininghall dungeonofsecrets verhoffinruins lichlab",
    3: "yorwick wizardslab connectingtunnels darkpassageway bathhouse greatgate",
    4: "templeofhonk 1000terrors arslegardcity dragonstadium hallofthegods afterworld",
}
# Growth per act. Act 1 grows 1.9x so its packs reach MM7's start (3.3 against 3.1; 1.4 until 2026-11-07, which read
# 0.45x MM7's damage once the outdoor swimmers stopped counting); act 2 1.4x, except the maps of the first chapter
# draft's chapter 2 (MAP_FACTOR: unchanged, the user 2026-11-06: their level 6-20 monsters are MM9's strongest against
# MM7's, +10% read 1.19-1.24x); the war 2.3x, the finale 5x (BALANCE_PLAN.md 3.6).
FACTOR = {1: 1.9, 2: 1.4, 3: 2.3, 4: 5.0}
# The clans act's early maps: the Jarls next to Sturmford (Drangheim, Guberland, Thjorad Mine, Ta'Sar Academy), where a
# party starts it; the rest of the act (Thjorgard, Thronheim, Frosgard, Lindisfarne and their dungeons) comes after.
CLANS_EARLY_MAPS = set("drangheim drangheimprison drangheimcity guberland guberlandcity thjoradmine tasaracademy".split())
MAP_FACTOR = {stem: 1.0 for stem in CLANS_EARLY_MAPS}
# The user's per-map calls (2026-11-09): Thjorad Mine grows as the rest of the act, 1.4x (an early map, but its
# tunnels are made for crowds; MAW adds more); the Tomb of a Thousand Terrors grows 2x, not the finale's 5x, which
# piled ten times its monsters into its open halls.
MAP_FACTOR.update({"thjoradmine": 1.4, "1000terrors": 2.0})
# The clans act's optional promotion and side dungeons with MM9's strongest monsters of the act (levels 33-79): Klusos's
# House (Assassin), Verhoffin Ruins (Mage), the Lich Lab (Lich), the Training Hall. A party takes them last, at the top of
# the act or after the war council; the balance report measures them at the war's party level (fit_check.mm9_stage).
CLANS_LATE_DUNGEONS = set("klusoshouse verhoffinruins lichlab traininghall".split())
# The user's exceptions (2026-11-06): a scripted dungeon whose guards sleep until woken gets no extra monsters; the
# Temple of Honk's scripted congregation takes what fits.
NO_GROWTH = {"klusoshouse"}
# The outdoor maps (the outdoor-BLV converter's, level_generation/projects/mm9r_<map>_blv): swimmers there do not count.
OUTDOOR_MAPS = {"afterworld", "bootcamp", "drangheim", "frosgard", "guberland", "isleofashes", "lindisfarne",
                "mountainpass", "sturmford", "thjorgard", "thronheim", "yorwick"}
HOSTILE_WHEN_PLACED_NON_HOSTILE = {"templeofhonk"}
LINK, CELL_RAYS, RAY_CAP, ROOM_SHARE, MAX_PACK = 1200.0, 16, 1536.0, 1 / 3, 12


def monster_rows() -> dict[int, tuple[str, int]]:
    rows = {}
    for line in MONSTERS.read_text(encoding="utf-8", errors="replace").splitlines()[3:]:
        cells = line.split("\t")
        if len(cells) > 3 and cells[0].isdigit() and cells[3].strip().lstrip("-").isdigit():
            rows[int(cells[0])] = (cells[1], int(cells[3]))
    return rows


@functools.cache
def swimmer_rows() -> frozenset[int]:
    """The monster rows that move in water (modifiers.yml: an mm9_ai entry with movement swim)."""
    swimmers = set()
    for key, entries in (yaml.safe_load(MODIFIERS.read_text(encoding="utf-8")).get("monsters") or {}).items():
        if not any(isinstance(entry, dict) and (entry.get("mm9_ai") or {}).get("movement") == "swim"
                   for entry in entries or []):
            continue
        first, _, last = str(key).partition("-")
        swimmers.update(range(int(first), int(last or first) + 1))
    return frozenset(swimmers)


def counted_actor(actor: dict, rows: dict[int, tuple[str, int]], stem: str) -> bool:
    """Whether a placed actor counts toward a map's density (the module docstring's rule)."""
    monster_id = int(actor.get("monster_info_id", 0))
    row = rows.get(monster_id)
    if row is None or family_of(row[0]) is None or row[1] >= 150:
        return False
    if stem in OUTDOOR_MAPS and monster_id in swimmer_rows():
        return False
    if actor.get("mm9_civilian") or actor.get("npc_id"):
        return False
    if actor.get("hostility_type", 4) == 0 and stem not in HOSTILE_WHEN_PLACED_NON_HOSTILE:
        return False
    return not ((actor.get("mm9_ai") or {}).get("profile") or {}).get("passive")


def wall_segments(q: dict) -> np.ndarray:
    vertices = q["vertices"]
    rows = []
    for face in q["faces"]:
        if face["facet_type"] != 1 or face["is_portal"]:
            continue
        points = [(vertices[i]["x"], vertices[i]["y"], vertices[i]["z"]) for i in face["vertex_indices"]]
        heights = [p[2] for p in points]
        for a, b in zip(points, points[1:] + points[:1]):
            if (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > 4:
                rows.append((a[0], a[1], b[0], b[1], min(heights), max(heights)))
    return np.array(rows, dtype=float).T if rows else np.zeros((6, 0))


def free_space(walls: np.ndarray, x: float, y: float, z: float) -> float:
    x1, y1, x2, y2, zmin, zmax = walls
    keep = ((zmin <= z + 64) & (zmax >= z + 64) & (np.minimum(x1, x2) < x + RAY_CAP)
            & (np.maximum(x1, x2) > x - RAY_CAP) & (np.minimum(y1, y2) < y + RAY_CAP)
            & (np.maximum(y1, y2) > y - RAY_CAP))
    ax, ay, bx, by = x1[keep], y1[keep], x2[keep], y2[keep]
    distances = []
    for k in range(CELL_RAYS):
        angle = 2 * math.pi * k / CELL_RAYS
        dx, dy = math.cos(angle), math.sin(angle)
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((ax - x) * ey - (ay - y) * ex) / den
            u = ((ax - x) * dy - (ay - y) * dx) / den
        hit = (np.abs(den) > 1e-9) & (t > 1) & (u >= 0) & (u <= 1)
        distances.append(float(min(RAY_CAP, t[hit].min())) if hit.any() else RAY_CAP)
    step = math.sin(2 * math.pi / CELL_RAYS)
    return sum(0.5 * distances[k] * distances[(k + 1) % CELL_RAYS] * step for k in range(CELL_RAYS))


def packs_of(actors: list[dict]) -> list[list[dict]]:
    parent = list(range(len(actors)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, a in enumerate(actors):
        for j in range(i + 1, len(actors)):
            b = actors[j]
            pa, pb = a["position"], b["position"]
            if ((pa["x"] - pb["x"]) ** 2 + (pa["y"] - pb["y"]) ** 2
                    + (2 * (pa["z"] - pb["z"])) ** 2) <= LINK * LINK:
                parent[find(i)] = find(j)
    groups: dict[int, list[dict]] = defaultdict(list)
    for i, actor in enumerate(actors):
        groups[find(i)].append(actor)
    return sorted(groups.values(), key=lambda pack: min(a["actor_index"] for a in pack))


def baseline_actor_count(stem: str) -> int | None:
    """The map's actors before growth: the converter appends its copies after them and lists them in the project's
    work/content.json (copy_of); None when the map has no project in the density anchors."""
    anchors = json.loads(ANCHORS.read_text(encoding="utf-8"))["maps"].get(stem)
    if anchors is None:
        return None
    content = json.loads((ROOT / "level_generation/projects" / anchors["project"] / "work/content.json")
                         .read_text(encoding="utf-8"))["actors"]
    return sum(1 for actor in content if "copy_of" not in actor)


def map_targets(stem: str, chapter: int, rows: dict[int, tuple[str, int]], baseline: int | None = None) -> dict:
    scene = yaml.load((MAPS / f"{stem}.scene.yml").read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
    placed = (scene.get("initial_state") or {}).get("actors") or []
    if baseline is not None:
        placed = placed[:baseline]
    actors = [a for a in placed if counted_actor(a, rows, stem)]
    factor = 1.0 if stem in NO_GROWTH else MAP_FACTOR.get(stem, FACTOR[chapter])
    walls = wall_segments(parse_blv_file(MAPS / f"{stem}.blv")["payload"]) if (MAPS / f"{stem}.blv").exists() \
        else np.zeros((6, 0))
    entries = []
    for pack in packs_of(actors):
        radius = max(int(a.get("radius", 40)) for a in pack)
        space = max(free_space(walls, a["position"]["x"], a["position"]["y"], a["position"]["z"]) for a in pack)
        capacity = max(len(pack), min(MAX_PACK, int(ROOM_SHARE * space / (2 * radius + 128) ** 2)))
        exact = len(pack) * factor
        target = min(capacity, max(len(pack), math.floor(exact)))
        entries.append({"actors": sorted(a["actor_index"] for a in pack), "size": len(pack), "target": target,
                        "capacity": capacity, "fraction": exact - math.floor(exact),
                        "monsters": sorted({rows[int(a["monster_info_id"])][0] for a in pack})})
    wanted = round(len(actors) * factor)
    # The map's remainder goes one monster at a time to the open packs with the largest fraction, then the most room.
    shortfall = wanted - sum(entry["target"] for entry in entries)
    while shortfall > 0:
        open_entries = [entry for entry in entries if entry["target"] < entry["capacity"]]
        if not open_entries:
            break
        best = max(open_entries, key=lambda entry: (entry["fraction"], entry["capacity"] - entry["target"]))
        best["target"] += 1
        best["fraction"] -= 1.0
        shortfall -= 1
    for entry in entries:
        del entry["fraction"]
        entry["add"] = entry["target"] - entry["size"]
    total = sum(entry["target"] for entry in entries)
    note = ("no growth (user)" if stem in NO_GROWTH else
            f"room for {total} of {wanted}" if total < wanted else "")
    return {"chapter": chapter, "factor": factor, "counted_today": len(actors), "target_total": total,
            "wanted_total": wanted, "mean_pack_today": round(len(actors) / len(entries), 2) if entries else 0,
            "mean_pack_target": round(total / len(entries), 2) if entries else 0, "note": note, "packs": entries}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="overwrite the frozen baseline")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--maps", nargs="+", metavar="STEM",
                        help="re-freeze only these maps, from their actors before growth (the scene's first actors, "
                             "the project's work/content.json without its copies); the others keep their entries")
    args = parser.parse_args()
    if args.output.exists() and not args.force:
        print(f"{args.output} exists (the frozen pre-growth baseline); pass --force to rebuild it from the scenes")
        return 1
    rows = monster_rows()
    chapter_of = {stem: chapter for chapter, stems in CHAPTER_MAPS.items() for stem in stems.split()}
    if args.maps:
        maps = yaml.safe_load(args.output.read_text(encoding="utf-8"))["maps"]
        for stem in args.maps:
            maps[stem] = map_targets(stem, chapter_of[stem], rows, baseline_actor_count(stem))
    else:
        maps = {}
        for chapter, stems in CHAPTER_MAPS.items():
            for stem in stems.split():
                if (MAPS / f"{stem}.scene.yml").exists():
                    maps[stem] = map_targets(stem, chapter, rows)
    header = (
        "# MM9 density targets (devdocs/mm9_rework/BALANCE_PLAN.md section 3.6), generated by mm9_density_targets.py\n"
        "# from the rebuilt maps before growth; the frozen baseline. Per map: chapter, factor, counted_today (the\n"
        "# counting rule in the script's docstring and counted_actor()), target_total, and per pack its placed actor\n"
        "# indices, size, target, capacity (room check) and `add`, the monsters to add next to it (copies of the pack's\n"
        "# own monsters). Bootcamp has no chapter and is not listed.\n")
    data = {"format_version": 1, "factors": FACTOR, "no_growth": sorted(NO_GROWTH),
            "counted_when_placed_non_hostile": sorted(HOSTILE_WHEN_PLACED_NON_HOSTILE), "maps": maps}
    args.output.write_text(header + yaml.safe_dump(data, sort_keys=False, width=120), encoding="utf-8")
    for stem, entry in maps.items():
        if args.maps and stem not in args.maps:
            continue
        print(f"ch{entry['chapter']} {stem:22} {entry['counted_today']:4} -> {entry['target_total']:4} "
              f"(wanted {entry['wanted_total']}) packs {len(entry['packs']):3} mean {entry['mean_pack_today']} -> "
              f"{entry['mean_pack_target']} {entry['note']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
