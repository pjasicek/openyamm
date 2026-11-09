#!/usr/bin/env python3
"""MM9 ground treasure (devdocs/mm9_rework/GROUND_TREASURE_PLAN.md): how many MM6-MM8 treasure markers each rebuilt map
gets and what they roll. The rework converters place them (level_generation/projects/mm9r_common/dungeon/treasure.py)
and write them into the map's scene `spawns`, so every reconversion places them again.

A map's markers take three classes from its chest tiers (mm9_chest_balance.TIERS) and treasure level:
  - bonus (15%, at least one where the map has secrets or a boss): one tier above the chests' top where the map's
    treasure level reaches it, else the chests' top; placed only behind secrets and in boss rooms;
  - main (55%): the chests' tiers;
  - lower (30%): one tier below the chests' bottom (the chests' tiers on a map whose chests are T1).
A marker's index is the lowest one the engine remaps to exactly its class's tiers on the map's treasure level
(mm9_chest_balance.record_level_for_tiers). Each marker rolls 20% nothing, 40% gold, 40% an item, as MM6-MM8.
"""
from __future__ import annotations

import mm9_chest_balance as chests

# Markers per map (the plan's section 4: MM7's density by size, capped at 0.35 per hostile actor, adjusted for what
# each map's hints exclude; the user, 2026-11-08). Cities and the maps not listed get none.
COUNTS = {
    # act 1
    "beethoven": 24, "anskramkeep": 18, "isleofashes": 8, "sturmford": 8,
    # act 2
    "drangheim": 8, "drangheimprison": 14, "guberland": 6, "thjoradmine": 18, "tasaracademy": 8, "dookscastle": 12,
    "traininghall": 10, "thjorgard": 8, "thronheim": 8, "lindisfarne": 6, "frosgard": 8, "mountainpass": 10,
    "yanmirsfort": 20, "chasmofthedead": 28, "ruinedtemple": 8, "inventastorca": 10, "klusoshouse": 5,
    "dungeonofsecrets": 3, "verhoffinruins": 14, "lichlab": 24,
    # act 3
    "yorwick": 8, "wizardslab": 22, "connectingtunnels": 8, "bathhouse": 12, "darkpassageway": 24,
    # act 4
    "templeofhonk": 5, "1000terrors": 28,
}

BONUS_SHARE, LOWER_SHARE = 0.15, 0.30
# Maps whose lower markers take another share: 1000 Terrors' floor items are 60% T5 (its lower class) and 40% T6 (the
# user, 2026-11-09).
LOWER_SHARES = {"1000terrors": 0.60}
MARKER_RADIUS = 32          # every MM7 marker's


def available_tiers(treasure_level: int) -> list[tuple[int, int]]:
    """The tier ranges a record of level 1-6 gives on a map of this treasure level."""
    column = min(max(treasure_level + 1, 1), 7) - 1
    return sorted({row[column] for row in chests.REMAP})


def marker_tiers(stem: str) -> dict[str, tuple[int, int]]:
    """The tier range of each marker class on the map: {"bonus": ..., "main": ..., "lower": ...}."""
    low, high = chests.TIERS[stem]
    options = available_tiers(chests.map_treasure_level(stem))
    # one tier above the chests' top; else the top and one above; else the best the map's level gives up to that
    bonus = next((t for t in ((high + 1, high + 1), (high, high + 1)) if t in options), None)
    if bonus is None:
        bonus = max((t for t in options if t[1] <= high + 1), key=lambda t: (t[0] + t[1], t[1]))
    lower = (low - 1, low - 1) if low > 1 and (low - 1, low - 1) in options else (low, high)
    return {"bonus": bonus, "main": (low, high), "lower": lower}


def marker_index(stem: str, tiers: tuple[int, int]) -> int:
    """The spawn index (record level) that rolls exactly these tiers on the map."""
    return chests.record_level_for_tiers(tiers, chests.map_treasure_level(stem))


def class_counts(stem: str, count: int, has_bonus_spots: bool) -> dict[str, int]:
    """How many markers of each class the map places when it places `count`."""
    bonus = max(1, round(count * BONUS_SHARE)) if has_bonus_spots and count else 0
    lower = min(round(count * LOWER_SHARES.get(stem, LOWER_SHARE)), count - bonus)
    return {"bonus": bonus, "main": max(0, count - bonus - lower), "lower": lower}
