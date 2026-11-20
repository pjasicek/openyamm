#!/usr/bin/env python3
"""MM9 shop balance (devdocs/mm9_rework/BALANCE_PLAN.md section 3.5): shop stock on MM6-MM8 scales.

generate_mm9_vendors.py keeps MM9's shops, profiles, prices and restock pages; for the equipment shops this module
replaces MM9's item levels and enchants:

- Shop tier by the city's chapter, at the levels of MM7's shops at the same stage (Emerald Island and Harmondale 1,
  Erathia and Tularean Forest 2, Avlee and Tatalia 3, Mount Nighon and The Pit 3-4); chapter 5, past MM7's shops,
  stocks at 5. The standard shelf stocks at the shop's treasure level, the special shelf one level higher.
- Item tiers by the tier mix of that treasure level (mm9_item_balance.RANDOM_WEIGHTS).
- Enchants as the engine rolls them (game/items/ItemEnchantRuntime.cpp): a standard bonus by the slot's weights with
  40% chance (75% at treasure level 6) and the level's power range, specials by the slot's weights among the
  rarities the level allows, at the level's weapon or equipment chance. As in MM7, the special shelf is only the higher
  treasure level: its items roll their enchants like any other (no weapon specials below level 3).
- Seeded per shop, shelf, page and slot, so the stock stays authored and reproducible.
"""
from __future__ import annotations

import csv
import dataclasses
import random
from pathlib import Path
from typing import Any, Callable

from mm9_item_balance import RANDOM_WEIGHTS

SHOP_TIER_BY_LOCATION = {
    "Sturmford": 1, "Drangheim": 2, "Guberland": 2, "Thjorgard": 3, "Frosgard": 3, "Thronheim": 3,
    "Lindisfarne": 3, "Yorwick": 4, "Arslegard": 5,
}
EQUIPMENT_PROFILES = {"Weapon", "Armor", "Mm9GeneralStore", "Mm9Apothecary"}

# ItemEnchantRuntime.cpp, by treasure level 1-6.
STANDARD_MINIMUM = (0, 1, 3, 6, 10, 15)
STANDARD_MAXIMUM = (0, 5, 8, 12, 17, 25)
STANDARD_CHANCE = (0, 40, 40, 40, 40, 75)
SPECIAL_CHANCE_EQUIPMENT = (0, 0, 10, 15, 20, 25)
SPECIAL_CHANCE_WEAPON = (0, 0, 10, 20, 30, 50)
SPECIAL_RARITIES = {3: "AB", 4: "ABC", 5: "BCD", 6: "D"}

STANDARD_GROUP = {"Armor": "Arm", "Shield": "Shld", "Helm": "Helm", "Belt": "Belt", "Cloak": "Cape",
                  "Gauntlets": "Gaunt", "Boots": "Boot", "Ring": "Ring", "Amulet": "Amul"}
SPECIAL_GROUP = {"Weapon": "W1", "Weapon1or2": "W1", "Weapon2": "W2", "Missile": "Miss", "Bow": "Miss",
                 **STANDARD_GROUP}
WEAPON_STATS = {"Weapon", "Weapon1or2", "Weapon2", "Missile", "Bow"}


@dataclasses.dataclass(frozen=True)
class EnchantRow:
    enchant_id: int
    weights: dict[str, int]
    rarity: str


def read_enchants(path: Path) -> list[EnchantRow]:
    """Rows of standard_item_enchants.txt or special_item_enchants.txt, numbered from 1 in table order."""
    with path.open(encoding="cp1252", newline="") as source:
        rows = list(csv.reader(source, delimiter="\t"))
    header_index = next(index for index, row in enumerate(rows) if row and row[0].strip() == "Bonus Stat")
    header = [cell.strip() for cell in rows[header_index]]
    result = []
    enchant_id = 0
    for row in rows[header_index + 1:]:
        if not row or not row[0].strip():
            continue
        enchant_id += 1
        padded = row + [""] * max(0, len(header) - len(row))
        weights = {name: int(padded[i]) if padded[i].strip().isdigit() else 0
                   for i, name in enumerate(header) if name in set(SPECIAL_GROUP.values())}
        rarity = padded[header.index("Lvl")].strip().upper() if "Lvl" in header else ""
        result.append(EnchantRow(enchant_id, weights, rarity))
    return result


def shop_tier(vendor: Any, location: str) -> int:
    """The shop's treasure level, or 0 for shops this module leaves to MM9 (books, libraries)."""
    if vendor.profile not in EQUIPMENT_PROFILES:
        return 0
    return SHOP_TIER_BY_LOCATION.get(location, 0)


def lane_level(tier: int, lane: str) -> int:
    return min(6, tier + (1 if lane == "special" else 0))


def tier_weights(level: int) -> dict[int, int]:
    return {tier: weights[level - 1] for tier, weights in RANDOM_WEIGHTS.items() if weights[level - 1] > 0}


def admitting_vendor(vendor: Any, tier: int) -> Any:
    """The vendor with its item-level ranges widened to the tiers its shelves' treasure levels yield."""
    standard = sorted(tier_weights(lane_level(tier, "standard")))
    special = sorted(tier_weights(lane_level(tier, "special")))
    return dataclasses.replace(vendor, standard_min=standard[0], standard_max=standard[-1],
                               special_min=special[0], special_max=special[-1])


def roll_restock(vendor: Any, lane: str, page: int, candidates: list[Any], tier: int, rolls: int,
                 admission_tier: Callable[[Any, Any], int]) -> list[Any]:
    rng = random.Random(f"mm9-vendor-stock-v3:{vendor.source_id}:{lane}:{page}")
    weights = tier_weights(lane_level(tier, lane))
    by_tier: dict[int, list[Any]] = {}
    for item in candidates:
        by_tier.setdefault(admission_tier(vendor, item), []).append(item)
    tiers = [t for t in sorted(by_tier) if t in weights]
    rolled = []
    for _ in range(rolls):
        if tiers:
            chosen = rng.choices(tiers, weights=[weights[t] for t in tiers])[0]
            rolled.append(rng.choice(by_tier[chosen]))
        else:
            rolled.append(rng.choice(candidates))
    return rolled


def roll_enchants(item: Any, vendor: Any, lane: str, page: int, slot: int, tier: int,
                  standard: list[EnchantRow], special: list[EnchantRow]) -> tuple[int, int, int]:
    """(standard id, standard power, special id) for one shelf slot."""
    level = lane_level(tier, lane)
    rng = random.Random(f"mm9-vendor-enchant-v3:{vendor.source_id}:{lane}:{page}:{slot}")
    weapon = item.equip_stat in WEAPON_STATS

    def pick_special() -> int:
        group = SPECIAL_GROUP.get(item.equip_stat)
        allowed = [row for row in special
                   if group and row.weights.get(group, 0) > 0 and row.rarity in SPECIAL_RARITIES.get(level, "")]
        if not allowed:
            return 0
        return rng.choices(allowed, weights=[row.weights[group] for row in allowed])[0].enchant_id

    def pick_standard() -> tuple[int, int]:
        group = STANDARD_GROUP.get(item.equip_stat)
        allowed = [row for row in standard if group and row.weights.get(group, 0) > 0]
        if not allowed or STANDARD_MAXIMUM[level - 1] == 0:
            return 0, 0
        row = rng.choices(allowed, weights=[r.weights[group] for r in allowed])[0]
        return row.enchant_id, rng.randint(STANDARD_MINIMUM[level - 1], STANDARD_MAXIMUM[level - 1])

    if weapon:
        chance = SPECIAL_CHANCE_WEAPON[level - 1]
        if rng.randrange(100) < chance:
            return 0, 0, pick_special()
        return 0, 0, 0
    if rng.randrange(100) < STANDARD_CHANCE[level - 1]:
        standard_id, power = pick_standard()
        if standard_id:
            return standard_id, power, 0
    if rng.randrange(100) < SPECIAL_CHANCE_EQUIPMENT[level - 1]:
        return 0, 0, pick_special()
    return 0, 0, 0
