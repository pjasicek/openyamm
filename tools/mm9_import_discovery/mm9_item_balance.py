#!/usr/bin/env python3
"""MM9 item balance profile v2 (devdocs/mm9_rework/BALANCE_PLAN.md section 3.4): MM9 equipment on MM6-MM8 scales.

import_mm9_items.py keeps reading MM9's own numbers (MASTERITEMLIST.csv, mm9_item_effects.yml) and passes them through
here, so the source stays MM9's and every change is a rule with a name the item row records.

MM9's five ordinary qualities stand on MM6-MM8's six tiers as tiers 1-4 and 6 (reference_tier): its top quality is
its only ordinary equipment of treasure level 6, so it matches MM6-MM8's top pieces (Lionheart Sword, Noble Plate).

- Ordinary weapons: each item keeps its dice at qualities 1-2; the die grows one size at quality 3 and again at 5; the
  flat bonus (attack and damage) brings the average to the MM6-MM8 median of the family and tier. Dice whose average
  is far above the target lose die size first, so no tier-1 weapon hits like a tier-3 one. The price is the MM6-MM8
  price of that average damage in the family (EngineReference.weapon_price).
- Ordinary armour: the slot's MM6-MM8 median armour value for the tier, scaled by the item's MM9 value against its
  tier group so MM9's order within a slot stays (Quilted below Padded Leather). The price follows the armour value on
  the slot's MM6-MM8 price curve.
- Belts, rings and amulets cost the MM6-MM8 median of their kind and tier.
- Artifacts, relics and set pieces: weapons get a flat bonus up to an artifact average; armour value is capped per slot;
  regeneration is MM6-MM8's 1 HP/s; a few items are retuned to the MM7 effect budget (PER_ITEM_EFFECTS).
- Random loot rolls from one pool of every world's items (devdocs/LOOT_POOL.md), so an MM9 item weighs what
  an MM6-MM8 item of its family and tier weighs at each treasure level (random_items.txt; EngineReference.weights).
- Prices are round like MM6-MM8's: multiples of 5 below 100, of 50 below 1,000, of 100 above (round_price).
"""
from __future__ import annotations

import copy
import statistics
from dataclasses import dataclass, field
from typing import Any

PROFILE = "mm9_balance_v2"

# Average damage, flat bonus included, MM6-MM8 medians by family and tier (balance_prototypes/cmp.py, 2026-11-05).
WEAPON_TARGETS: dict[str, list[float]] = {
    "Sword 1H": [4.7, 6.4, 9.6, 13.4, 17.8, 20.3],
    "Sword 2H": [10.0, 12.5, 15.0, 20.0, 24.0, 27.0],
    "Dagger 1H": [2.2, 3.5, 5.5, 7.9, 9.5, 12.0],
    "Axe 1H": [4.5, 7.0, 9.8, 12.8, 16.2, 19.0],
    "Axe 2H": [10.5, 12.5, 14.5, 18.5, 25.0, 27.2],
    "Spear": [6.5, 7.9, 11.9, 16.1, 19.1, 23.5],
    # Halberds stay two-handed and follow the two-handed axes, a step above the one-or-two-handed spears.
    "Spear 2H": [10.5, 12.5, 14.5, 18.5, 25.0, 27.2],
    "Mace 1H": [4.5, 6.2, 8.8, 12.4, 16.0, 18.3],
    # MM6-MM8 have no two-handed maces; MM9's (Thjorad) follow the two-handed axes.
    "Mace 2H": [10.5, 12.5, 14.5, 18.5, 25.0, 27.2],
    "Staff 2H": [4.0, 5.5, 7.5, 10.0, 12.0, 13.5],
    "Bow": [5.2, 7.6, 10.1, 13.4, 17.2, 17.8],
}
# Dice may run this far over the target before they lose die size.
DICE_OVERSHOOT = 1.25

# Armour value (base + bonus), MM6-MM8 medians by slot and tier, smoothed where a median dips. Helms count only
# pieces with armour (hats and crowns have none). Plate tier 4 is the geometric mean of tiers 3 and 5: its median (21,
# the entry plate of MM6 and MM7) is no better than tier 4 chain. MM6-MM8 have no tier 1 shields, boots or gauntlets;
# MM9's take a step below tier 2 (the lowest MM6-MM8 pieces: 2-3 shields, 1 boots and gloves), not MM9's own values.
ARMOR_TARGETS: dict[str, list[float | None]] = {
    "Leather": [3, 4.5, 7, 10, 16, 24],
    "Chain": [None, 7, 12, 20, 28, 39],
    "Plate": [None, None, 18, 26, 38, 59],
    "Shield": [3, 5.5, 10, 14.5, 16.5, 18.5],
    "Helm": [1, 3, 6, 9, 12.5, 15],
    "Boots": [1, 1.5, 4.5, 8, 11, 14],
    "Gauntlets": [1, 1.5, 4.5, 8, 12, 15],
}
# MM9 has no ordinary quality 6: its top quality is its only ordinary equipment of treasure level 6 and stands for
# MM6-MM8's tier 6 (reference_tier).
TOP_ORDINARY_TIER = 5
# Families MM6-MM8 lack, priced and weighted as their nearest MM6-MM8 family: halberds as MM6-MM8's spears (halberds
# among them), two-handed maces as two-handed axes.
REFERENCE_FAMILY = {"Spear 2H": "Spear", "Mace 2H": "Axe 2H"}

# MM6-MM8 price by armour value, (armour, price) anchors per slot: their ordinary armour prices lie on these lines.
ARMOR_PRICE_CURVES: dict[str, tuple[tuple[int, int], ...]] = {
    "Leather": ((3, 100), (10, 450), (18, 850), (27, 1300)),
    "Chain": ((6, 300), (30, 1500), (42, 2100)),
    "Plate": ((18, 750), (22, 1100), (38, 2000), (64, 3800)),
    "Shield": ((2, 25), (4, 100), (22, 1000)),
    "Helm": ((1, 10), (3, 100), (10, 650), (15, 1050)),
    "Boots": ((1, 10), (3, 100), (10, 650), (15, 1050)),
    "Gauntlets": ((1, 10), (3, 100), (10, 650), (15, 1050)),
}

# Artifacts, relics and set pieces.
RARE_WEAPON_AVERAGE = {"1H": 24.0, "2H": 30.0, "Missile": 20.0}
RARE_WEAPON_FLAT = (5, 18)
RARE_ARMOR_CAP = {"Plate": 75, "Chain": 50, "Leather": 32, "Shield": 32, "Helm": 15, "Boots": 15, "Gauntlets": 15}
REGENERATION_PER_SECOND = 1.0
# Per-item effect changes against the MM7 effect budget (stat point 1, +1 skill 3, all resistances +10 = 21).
PER_ITEM_EFFECTS: dict[int, dict[str, Any]] = {
    181: {"melee_attack": 20, "melee_damage": 15},              # Integris: a top weapon, not +35/+35
    209: {"luck": 30},                                          # Weregild: weekly gold and luck for its party drain
    215: {"school_skill_bonus": 3},                             # Pendant of the Spheres: +3 per school, not +5
    216: {"might": 15, "accuracy": 15, "all_resistances": 10},  # Fizbin of Misfortune: an upside to its curse
    # The weak ones raised into the MM6-MM8 artifact curve (OY-589, 2026-11-13): artifacts about +40 in stats or a
    # +20 pair with a perk, relics more with a real drawback (Glomenthal +40 Might, Havoc +70/+70 and -20 AC).
    179: {"speed": 40, "accuracy": 40, "max_sp": -50},          # Jorhgamesh: a warlord's relic; MM9's -50 SP drawback
    182: {"endurance": 30},                                     # Bloodaxe: Sven, who died of old age
    183: {"skill_bonuses": {"Axe": 6, "Armsmaster": 6}},        # Sygnir: MM9's Blade skill is Axe for an axe
    184: {"skill_bonuses": {"Bow": 5}, "recovery_reduction_ticks": 20},  # Everstrike: Longseeker's bow and speed
    186: {"weapon_damage": 5},                                  # Tillhygge: damage for its disease flag to carry
    190: {"might": 50},                                         # Formanir: Krohn's spear
    191: {"might": 40},                                         # Einherjar: a relic, more than a vampiric artifact
    194: {"might": 40, "endurance": 20},                        # Blutterbunger: a barroom brawler's club
    198: {"speed": 30, "might": 20},                            # Spencer's Obedience: a general's club
    199: {"might": 50},                                         # Mjulnir: the Hammer of the Gods, for a massive warrior
    200: {"intellect": 30, "personality": 30},                  # Igdrasine: Igrassa's gift, MM9's "+10 to Magic"
    201: {"speed": 30},                                         # Poltergeist: it weighs nearly nothing
    206: {"accuracy": -20, "luck": 40, "skill_bonuses": {"DisarmTraps": 10}},  # Laet'ax: a thief's slippery gloves
    207: {"endurance": 30},                                     # Arrowfoe: more than missile armour
    214: {"personality": 30},                                   # Mountbatten: the sages' peace and happiness
    218: {"max_health": 100, "endurance": 30, "max_sp": -20},   # Fre's Heart: Vita's goddess, a healer's relic
}
# Set pieces whose base armour MM9 leaves at nothing.
SET_PIECE_ARMOR_BONUS = {221: 4, 223: 4}                        # Prize Skullcap, Prize Shield

# The tier mix of a treasure level for shop stock (mm9_vendor_balance.py), the common MM6-MM8 pattern of each tier.
# Tier 5, MM9's top ordinary quality, weighs like MM6-MM8's top pieces (Royal Leather, Golden Plate): mostly levels 5
# and 6. Random loot takes its weights per family and tier from MM6-MM8's items instead (EngineReference.weights).
RANDOM_WEIGHTS = {
    1: (8, 2, 0, 0, 0, 0),
    2: (0, 10, 5, 2, 0, 0),
    3: (0, 5, 7, 3, 0, 0),
    4: (0, 0, 5, 7, 3, 0),
    5: (0, 0, 0, 2, 7, 10),
    6: (0, 0, 0, 0, 0, 5),
}

# Weapons, armour and jewellery (ItemGenerator.cpp isPooledEquipment): the equipment of random loot. Potions, scrolls,
# books, reagents, gems and wands come from the merged base and roll beside it.
POOLED_EQUIP_STATS = {"Weapon", "Weapon2", "Weapon1or2", "Missile", "Armor", "Shield", "Helm", "Belt", "Cloak",
                      "Gauntlets", "Boots", "Ring", "Amulet"}
RARE_MATERIALS = {"Artifact", "Relic", "Special"}


def parse_dice(text: str) -> tuple[int, int] | None:
    parts = text.lower().split("d")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return None
    return int(parts[0]), int(parts[1])


def dice_average(count: int, sides: int) -> float:
    return count * (sides + 1) / 2


def weapon_family(equip_stat: str, skill: str, subtype: str) -> str | None:
    subtype = subtype.casefold()
    if equip_stat == "Missile":
        if skill == "Bow":
            return "Bow"
        return "Axe 1H" if "axe" in subtype else "Dagger 1H"
    two_handed = equip_stat == "Weapon2"
    if skill == "Spear":
        return "Spear 2H" if "halberd" in subtype else "Spear"
    if skill == "Staff":
        return "Staff 2H"
    if skill in {"Sword", "Axe", "Mace"}:
        return f"{skill} {'2H' if two_handed else '1H'}"
    if skill == "Dagger":
        return "Dagger 1H"
    return None


def reference_tier(tier: int) -> int:
    """The MM6-MM8 tier an MM9 quality stands for: qualities 1-4 as they are, the top quality as tier 6."""
    return 6 if tier == TOP_ORDINARY_TIER else tier


def weapon_target(family: str, tier: int) -> float:
    return WEAPON_TARGETS[family][reference_tier(tier) - 1]


def ordinary_weapon(family: str, tier: int, dice: tuple[int, int]) -> tuple[str, str, str]:
    """(mod1, mod2, rule) for an ordinary weapon of an MM9 quality 1-5."""
    target = weapon_target(family, tier)
    count, sides = dice
    sides += (1 if tier >= 3 else 0) + (1 if tier >= 5 else 0)
    while sides > 2 and dice_average(count, sides) > target * DICE_OVERSHOOT:
        sides -= 1
    flat = max(0, round(target - dice_average(count, sides)))
    return f"{count}d{sides}", str(flat), f"weapon_ladder:{family.replace(' ', '')}"


def round_price(value: float) -> int:
    """A shop price as MM6-MM8 write them: 45, 550, 1200."""
    if value <= 0:
        return 0
    step = 5 if value < 100 else 50 if value < 1000 else 100
    return max(step, int(value / step + 0.5) * step)


def armor_target(slot: str, tier: int) -> float | None:
    """The armour value an ordinary piece of the slot and MM9 quality aims at."""
    if not 1 <= tier <= TOP_ORDINARY_TIER:
        return None
    return ARMOR_TARGETS[slot][reference_tier(tier) - 1]


def armor_price(slot: str, armor_value: int) -> int:
    """The MM6-MM8 price of an ordinary piece of the slot with this armour value, rounded."""
    curve = ARMOR_PRICE_CURVES[slot]
    index = 1
    while index < len(curve) - 1 and armor_value > curve[index][0]:
        index += 1
    (low_value, low_price), (high_value, high_price) = curve[index - 1], curve[index]
    price = low_price + (armor_value - low_value) * (high_price - low_price) / (high_value - low_value)
    return round_price(max(curve[0][1], price))


def ordinary_armor(slot: str, tier: int, base: int, source_value: int, group_mean: float) -> tuple[str, str, str]:
    """(mod1, mod2, rule): the armour value scaled to the slot's tier target, keeping the base in mod1."""
    target = armor_target(slot, tier)
    if target is None:
        return str(base), str(source_value), "armor_source_kept"
    scale = (base + source_value) / group_mean if group_mean > 0 else 1.0
    total = max(base, round(target * scale))
    return str(base), str(total - base), f"armor_ladder:{slot}"


def rare_weapon(hand: str, dice: tuple[int, int]) -> tuple[str, str, str]:
    count, sides = dice
    low, high = RARE_WEAPON_FLAT
    flat = max(low, min(high, round(RARE_WEAPON_AVERAGE[hand] - dice_average(count, sides))))
    return f"{count}d{sides}", str(flat), f"rare_weapon:{hand}"


def rare_armor(slot: str, raw_id: int, base: int, bonus: int) -> tuple[str, str, str]:
    bonus += SET_PIECE_ARMOR_BONUS.get(raw_id, 0)
    cap = RARE_ARMOR_CAP.get(slot)
    if cap is not None and base + bonus > cap:
        return str(base), str(cap - base), f"rare_armor_cap:{slot}"
    rule = "set_piece_armor" if raw_id in SET_PIECE_ARMOR_BONUS else "rare_armor_kept"
    return str(base), str(bonus), rule


def armor_slot(equip_stat: str, skill: str) -> str | None:
    if equip_stat == "Armor":
        return skill if skill in {"Leather", "Chain", "Plate"} else None
    return {"Shield": "Shield", "Helm": "Helm", "Boots": "Boots", "Gauntlets": "Gauntlets"}.get(equip_stat)


def loot_family(equip_stat: str, skill: str, subtype: str) -> str | None:
    """The family an item weighs and is priced in: weapon family, armour slot, or belt, ring, amulet or cloak."""
    if equip_stat in {"Weapon", "Weapon2", "Weapon1or2", "Missile"}:
        if equip_stat == "Missile" and skill not in {"Bow", "Throwing"}:
            return None                     # MM6-MM8's blasters
        return weapon_family(equip_stat, skill, subtype)
    slot = armor_slot(equip_stat, skill)
    if slot:
        return slot
    return equip_stat if equip_stat in {"Belt", "Ring", "Amulet", "Cloak"} else None


def isotonic_curve(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """The non-decreasing least-squares fit of (x, y) points (pool adjacent violators), one knot per distinct x."""
    by_x: dict[float, list[float]] = {}
    for x, y in points:
        by_x.setdefault(x, []).append(y)
    blocks: list[list[float]] = []      # sum of x, sum of y, count
    for x in sorted(by_x):
        ys = by_x[x]
        blocks.append([x * len(ys), sum(ys), len(ys)])
        while len(blocks) > 1 and blocks[-2][1] / blocks[-2][2] > blocks[-1][1] / blocks[-1][2]:
            last = blocks.pop()
            blocks[-1] = [a + b for a, b in zip(blocks[-1], last)]
    return [(sx / n, sy / n) for sx, sy, n in blocks]


def curve_value(curve: list[tuple[float, float]], x: float) -> float:
    """The curve at x, linear between knots and along the last segment beyond them; flat below the first."""
    if x <= curve[0][0] or len(curve) == 1:
        return curve[0][1]
    index = 1
    while index < len(curve) - 1 and x > curve[index][0]:
        index += 1
    (x0, y0), (x1, y1) = curve[index - 1], curve[index]
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def engine_tier(weights: list[int]) -> int:
    """An MM6-MM8 item's tier: its weighted mean treasure level, rounded (balance_prototypes/cmp.py)."""
    return round(sum((level + 1) * weight for level, weight in enumerate(weights)) / sum(weights))


@dataclass
class EngineReference:
    """MM6-MM8's ordinary random equipment (engine items.txt and random_items.txt) by family and tier."""
    weight_vectors: dict[tuple[str, int], list[list[int]]] = field(default_factory=dict)
    damage_prices: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    tier_prices: dict[tuple[str, int], list[int]] = field(default_factory=dict)

    @classmethod
    def from_tables(cls, item_rows: list[list[str]], random_rows: list[list[str]]) -> "EngineReference":
        header = next(row for row in item_rows if row and row[0] == "Item #")
        columns = {name: index for index, name in enumerate(header)}

        def cell(row: list[str], name: str) -> str:
            # Rows end early when their trailing columns (package, flags) are empty.
            return row[columns[name]] if len(row) > columns[name] else ""

        weights = {int(row[0]): [int(value or 0) for value in row[2:8]]
                   for row in random_rows if len(row) >= 8 and row[0].strip().isdigit()}
        reference = cls()
        for row in item_rows:
            if not row or not row[0].strip().isdigit() or int(row[0]) not in weights:
                continue
            vector = weights[int(row[0])]
            if (sum(vector) == 0 or cell(row, "material") in RARE_MATERIALS
                    or "NoRandom" in cell(row, "content_flags").split("|")):
                continue
            equip_stat, skill = cell(row, "Equip Stat"), cell(row, "Skill Group")
            family = loot_family(equip_stat, skill, "")
            if family is None:
                continue
            tier = engine_tier(vector)
            price = int(cell(row, "Value") or 0)
            reference.weight_vectors.setdefault((family, tier), []).append(vector)
            reference.tier_prices.setdefault((family, tier), []).append(price)
            dice = parse_dice(cell(row, "Mod1"))
            if family in WEAPON_TARGETS and dice:
                average = dice_average(*dice) + int(cell(row, "Mod2") or 0)
                reference.damage_prices.setdefault(family, []).append((average, price))
        return reference

    def weights(self, family: str, tier: int) -> list[int]:
        """The mean treasure-level weights of MM6-MM8's items of the family and MM9 quality, or of the family's
        nearest tier where MM6-MM8 have none of it (they start boots, gauntlets, shields, belts, rings and amulets
        at tier 2, so MM9's tier 1 pieces drop where MM6-MM8's lowest ones do)."""
        family = REFERENCE_FAMILY.get(family, family)
        target = reference_tier(tier)
        tiers = sorted((abs(other - target), -other) for other_family, other in self.weight_vectors
                       if other_family == family)
        if not tiers:
            raise ValueError(f"MM6-MM8 have no {family} to weigh MM9's quality {tier}")
        vectors = self.weight_vectors[(family, -tiers[0][1])]
        return [round(statistics.mean(vector[level] for vector in vectors)) for level in range(6)]

    def weapon_price(self, family: str, average_damage: float) -> int:
        """The MM6-MM8 price of a weapon of the family with this average damage, on their monotone price curve."""
        points = self.damage_prices.get(REFERENCE_FAMILY.get(family, family))
        if not points:
            raise ValueError(f"MM6-MM8 have no priced {family} weapons")
        return round_price(curve_value(isotonic_curve(points), average_damage))

    def tier_price(self, family: str, tier: int) -> int | None:
        """The median MM6-MM8 price of the family (belts, rings, amulets) at the MM9 quality's tier; below the
        family's lowest MM6-MM8 tier, that tier's cheapest piece."""
        target = reference_tier(tier)
        tiers = sorted(other for other_family, other in self.tier_prices if other_family == family)
        if not tiers:
            return None
        if target in tiers:
            return round_price(statistics.median(self.tier_prices[(family, target)]))
        if target < tiers[0]:
            return round_price(min(self.tier_prices[(family, tiers[0])]))
        nearest = min(tiers, key=lambda other: abs(other - target))
        return round_price(statistics.median(self.tier_prices[(family, nearest)]))


def balance_rows(rows: list[list[str]], columns: dict[str, int], reference: EngineReference) -> None:
    """Rewrite mod1/mod2 and prices of the item rows in place and append the rule to their balance-profile column."""
    def cell(row: list[str], name: str) -> str:
        return row[columns[name]]

    # MM9's armour value means per slot and tier, so scaling keeps each item's place in its group.
    groups: dict[tuple[str, int], list[int]] = {}
    for row in rows:
        slot = armor_slot(cell(row, "Equip Stat"), cell(row, "Skill Group"))
        rare = cell(row, "material") in {"Artifact", "Relic", "Special"}
        if slot and not rare:
            tier = int(cell(row, "normalized_tier") or 0)
            groups.setdefault((slot, tier), []).append(int(cell(row, "Mod1") or 0) + int(cell(row, "Mod2") or 0))

    for row in rows:
        equip_stat = cell(row, "Equip Stat")
        skill = cell(row, "Skill Group")
        tier = int(cell(row, "normalized_tier") or 0)
        rare = cell(row, "material") in {"Artifact", "Relic", "Special"}
        raw_id = int(cell(row, "x_mm9_raw_item_id") or 0)
        result: tuple[str, str, str] | None = None
        dice = parse_dice(cell(row, "Mod1"))
        family = weapon_family(equip_stat, skill, cell(row, "x_mm9_source_name_type"))
        slot = armor_slot(equip_stat, skill)

        if family and dice:
            if rare:
                hand = "Missile" if equip_stat == "Missile" else "2H" if equip_stat == "Weapon2" else "1H"
                result = rare_weapon(hand, dice)
            elif 1 <= tier <= 6:
                result = ordinary_weapon(family, tier, dice)
        elif slot:
            base, bonus = int(cell(row, "Mod1") or 0), int(cell(row, "Mod2") or 0)
            if rare:
                result = rare_armor(slot, raw_id, base, bonus)
            else:
                values = groups.get((slot, tier), [base + bonus])
                result = ordinary_armor(slot, tier, base, bonus, sum(values) / len(values))

        if family == "Spear" and not rare:
            row[columns["Equip Stat"]] = "Weapon1or2"   # MM6-MM8 spears are one-or-two-handed; halberds stay two-handed

        rule = "unchanged"
        if result is not None:
            row[columns["Mod1"]], row[columns["Mod2"]], rule = result
            if slot and not rare and rule.startswith("armor_ladder"):
                armor_value = int(row[columns["Mod1"]]) + int(row[columns["Mod2"]])
                row[columns["Value"]] = str(armor_price(slot, armor_value))
                rule += "+armor_price"
            elif family and not rare and rule.startswith("weapon_ladder"):
                count, sides = parse_dice(row[columns["Mod1"]]) or (0, 0)
                average = dice_average(count, sides) + int(row[columns["Mod2"]] or 0)
                row[columns["Value"]] = str(reference.weapon_price(family, average))
                rule += "+weapon_price"
        elif not rare and equip_stat in {"Belt", "Ring", "Amulet"} and 1 <= tier <= TOP_ORDINARY_TIER:
            price = reference.tier_price(equip_stat, tier)
            if price is not None:
                row[columns["Value"]] = str(price)
                rule = "tier_price"
        profile_column = columns["x_mm9_balance_profile"]
        row[profile_column] = f"{PROFILE}:{rule}|{row[profile_column]}"


def balance_effect(raw_id: int, definition: dict[str, Any]) -> dict[str, Any]:
    """An item's or set's authored MM9 effect with the v2 changes."""
    result = copy.deepcopy(definition)
    if "health_regen_per_second" in result:
        result["health_regen_per_second"] = max(REGENERATION_PER_SECOND, float(result["health_regen_per_second"]))
    for key, value in PER_ITEM_EFFECTS.get(raw_id, {}).items():
        if key == "school_skill_bonus":
            result["skill_bonuses"] = {name: value if name.endswith("Magic") else amount
                                       for name, amount in result.get("skill_bonuses", {}).items()}
        else:
            result[key] = value
    return result


def random_item_rows(rows: list[list[str]], columns: dict[str, int], reference: EngineReference) -> list[list[str]]:
    """random_items.txt rows for MM9's ordinary equipment: the weights of MM6-MM8's items of its family and tier."""
    out = []
    for row in rows:
        flags = row[columns["content_flags"]].split("|")
        tier = int(row[columns["normalized_tier"]] or 0)
        rare = row[columns["material"]] in RARE_MATERIALS
        if rare or "NoRandom" in flags or "Quest" in flags or not 1 <= tier <= TOP_ORDINARY_TIER:
            continue
        if row[columns["Equip Stat"]] not in POOLED_EQUIP_STATS:
            continue
        family = loot_family(row[columns["Equip Stat"]], row[columns["Skill Group"]],
                             row[columns["x_mm9_source_name_type"]])
        if family is None:
            raise ValueError(f"MM9 item {row[0]} ({row[columns['Name']]}) has no loot family")
        weights = reference.weights(family, tier)
        out.append([row[0], row[columns["Pic File"]], *map(str, weights), row[columns["Name"]]])
    return out
