#!/usr/bin/env python3
"""MM9 chest balance (devdocs/mm9_rework/BALANCE_PLAN.md section 3.8), applied by the rework converters;
`stem` is the map, kept for map-specific exceptions.

balance_loot_containers(stem, containers) rewrites a map's scene loot containers in place:
  - a black chest's random slot (BlackChest model, random) becomes one level-7 record: a random artifact or relic the
    party has not found; with none left, gold and a level-6 item (world.yml chestArtifactsOnly). Black chests with only
    fixed items keep them.
  - an ordinary random container with level 0 (MM9's "unset", which the engine fills with nothing) takes its map's most
    common level among the other ordinary random containers (1 if there are none);
  - every other ordinary random container holds RECORDS random records (random_records), each rolling 1-5 times like
    an MM6-MM8 chest slot: MM7's average chest (1,194 random records in 406 chests). A chest holds what an MM7 chest
    holds; MM9's fewer chests are not compensated (the user, 2026-11-06). balance_prototypes/chests.py --planned
    measures it.
  - on a map in TIERS, an ordinary random container's items are of those tiers: its record level is raised to the
    lowest one the engine remaps to exactly that tier range on the map's treasure level (the user, 2026-11-08: Ta'Sar
    Academy's chests gave T2 items and Yanmir's Fort's T3 and T1). A map whose treasure level cannot give its tiers
    takes one that can in MAP_TREASURE_LEVEL, which the converters write into its map_stats row (dungeon/tables.py).
"""
from __future__ import annotations

from pathlib import Path

ARTIFACT_LEVEL = 7
RECORDS = 3

# The item tiers [lowest, highest] of the ordinary random containers per map, by act (the user, 2026-11-08: act 2's;
# the other acts' follow them, about one tier above MM9's own levels, from the act's first places to its last).
TIERS = {
    # act 1 (the Isle of Ashes, the first map, only the worst items: the user, 2026-11-09)
    "isleofashes": (1, 1), "sturmford": (1, 2), "beethoven": (2, 2), "anskramkeep": (2, 2),
    # act 2
    "drangheim": (2, 3), "drangheimprison": (2, 3), "guberland": (2, 3),
    "dookscastle": (3, 3), "traininghall": (3, 3), "thjorgard": (3, 3), "thronheim": (3, 3), "thronheimcity": (3, 3),
    "lindisfarne": (3, 3), "frosgard": (3, 4), "mountainpass": (3, 4),
    "thjoradmine": (3, 3), "klusoshouse": (3, 3), "dungeonofsecrets": (3, 3),
    "tasaracademy": (3, 4), "inventastorca": (3, 4),
    "yanmirsfort": (4, 4), "chasmofthedead": (4, 4), "ruinedtemple": (4, 4),
    "lichlab": (4, 5), "verhoffinruins": (4, 5),
    # act 3
    "yorwick": (4, 5), "wizardslab": (5, 5), "connectingtunnels": (5, 5), "bathhouse": (5, 5),
    "darkpassageway": (5, 6),
    # act 4
    "templeofhonk": (5, 6), "1000terrors": (6, 6),
}

# Single containers whose tiers differ from their map's (map, DAT object name): Verhoffin Ruins' first chest, forward
# and to the right of the start, which a level-1 party reaches without being seen (the user, 2026-11-08).
# 1000 Terrors' seven ordinary chests are half T5, half T6 (the user, 2026-11-09): its treasure level 6 has no record of
# T5-T6, so the four nearest the start (in plan) give T5 and the other three keep the map's T6.
CONTAINER_TIERS = {
    ("verhoffinruins", "TreasureChest3"): (4, 4),
    ("1000terrors", "TreasureChest0"): (5, 5), ("1000terrors", "TreasureChest1"): (5, 5),
    ("1000terrors", "TreasureChest8"): (5, 5), ("1000terrors", "TreasureChest12"): (5, 5),
}

# Map treasure levels (map_stats 0-6) replacing the original row's where its level cannot give the map's TIERS: a
# level-0 map remaps every record to T1, a level-1 map to T1-T2. The map's monster drops and floor treasure remap
# against it too.
MAP_TREASURE_LEVEL = {
    "isleofashes": 1, "sturmford": 1, "beethoven": 1, "anskramkeep": 1,
    "drangheim": 2, "drangheimprison": 2, "thronheimcity": 2, "lindisfarne": 2,
    "guberland": 2, "klusoshouse": 2,
}

# Map disarm difficulties (map_stats Lock 0-20; a party disarms a chest trap with Disarm Traps of twice it) replacing the
# original row's where it is out of step with the map's place: Beethoven, a chapter-1 sewer whose traps are MM6-MM8's
# weakest (1 d20), had Lock 10, so no early party could disarm a chest and every one went off (the user, 2026-11-09).
# MM6-MM8's 1-d20 dungeons have Lock 0-2.
MAP_DISARM_DIFFICULTY = {
    "beethoven": 2,
}
MAP_STATS_LOCK_COLUMN = 9

# The map treasure levels the converters install (dungeon/tables.py takes each map's map_stats row from here).
ORIGINAL_MAP_STATS = Path(__file__).resolve().parents[2] / "level_generation/projects/mm9r_common/original_tables" \
    / "map_stats.txt"
MAP_STATS_TREASURE_COLUMN = 11

# The engine's chest remap (game/gameplay/ChestRuntime.cpp, remapTreasureLevelRange, MM6-MM8's): the item tiers
# [lowest, highest] a record of level 1-7 (row) gives on a map of normalized treasure level 1-7 (column; the map_stats
# level + 1).
REMAP = [
    [(1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1), (1, 1)],
    [(1, 1), (1, 2), (2, 2), (2, 2), (2, 2), (2, 2), (2, 2)],
    [(1, 2), (2, 2), (2, 3), (3, 3), (3, 3), (3, 3), (3, 3)],
    [(2, 2), (2, 2), (3, 3), (3, 4), (4, 4), (4, 4), (4, 4)],
    [(2, 2), (2, 2), (3, 4), (4, 4), (4, 5), (5, 5), (5, 5)],
    [(2, 2), (2, 2), (4, 4), (4, 5), (5, 5), (5, 6), (6, 6)],
]


def map_treasure_level(stem: str) -> int:
    """The map's treasure level (0-6): MAP_TREASURE_LEVEL's, else the original map_stats row's (by its old `.odm` or
    `.blv` name)."""
    if stem in MAP_TREASURE_LEVEL:
        return MAP_TREASURE_LEVEL[stem]
    for line in ORIGINAL_MAP_STATS.read_text(encoding="latin-1").splitlines():
        cells = line.split("\t")
        if len(cells) > MAP_STATS_TREASURE_COLUMN and cells[2].lower().rsplit(".", 1)[0] == stem:
            return int(cells[MAP_STATS_TREASURE_COLUMN])
    raise SystemExit(f"{ORIGINAL_MAP_STATS} has no row for {stem}")


def record_level_for_tiers(tiers: tuple[int, int], treasure_level: int) -> int:
    """The lowest record level (1-6) whose items are exactly of these tiers on a map of this treasure level."""
    column = min(max(treasure_level + 1, 1), 7) - 1
    for level, row in enumerate(REMAP, 1):
        if row[column] == tuple(tiers):
            return level
    raise SystemExit(f"no record level gives tiers {tiers} on treasure level {treasure_level}")


def is_black_chest(container: dict) -> bool:
    return "blackchest" in str(container.get("source_model", "")).replace("\\", "/").lower()


def is_random(container: dict) -> bool:
    return bool(container.get("random") or container.get("ai_drop")) and not container.get("gold_only") \
        and not container.get("random_item_pool")


def balance_loot_containers(stem: str, containers: list[dict]) -> list[dict]:
    ordinary = [c for c in containers if is_random(c) and not is_black_chest(c)]
    levels = [int(c.get("random_treasure_level") or 0) for c in ordinary]
    levels = [level for level in levels if level > 0]
    fill = max(sorted(set(levels)), key=levels.count) if levels else 1
    floor = record_level_for_tiers(TIERS[stem], map_treasure_level(stem)) if stem in TIERS else 0
    for container in containers:
        if not is_random(container):
            continue
        if is_black_chest(container):
            container["random_treasure_level"] = ARTIFACT_LEVEL
            container["random_records"] = 1
            continue
        if int(container.get("random_treasure_level") or 0) == 0:
            container["random_treasure_level"] = fill
        if (stem, container.get("source_name")) in CONTAINER_TIERS:
            container["random_treasure_level"] = record_level_for_tiers(
                CONTAINER_TIERS[stem, container["source_name"]], map_treasure_level(stem))
        else:
            container["random_treasure_level"] = max(int(container["random_treasure_level"]), floor)
        container["random_records"] = RECORDS
    return containers
