#!/usr/bin/env python3
"""MM9 balance report and gate (devdocs/mm9_rework/BALANCE_PLAN.md section 4).

Reads the generated MM9 world tables and checks them against the plan, then runs the engine balance probe
(tools/balance_probe_main.cpp) against MM7. Writes devdocs/mm9_rework/BALANCE_REPORT.md; with --gate, exits 1 when a
value leaves its band. Run from the repository root after building openyamm_balance_probe.
"""
from __future__ import annotations

import argparse
import csv
import re
import runpy
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mm9_item_balance as item_balance        # noqa: E402
import mm9_monster_balance as monster_balance  # noqa: E402
import mm9_vendor_balance as vendor_balance    # noqa: E402

WORLD = Path("assets_dev/worlds/mm9/data_tables")
PROTOTYPES = Path("devdocs/mm9_rework/balance_prototypes")
REPORT = Path("devdocs/mm9_rework/BALANCE_REPORT.md")
PROBE = Path("build/tools/openyamm_balance_probe")
OUT = Path("output/mm9_balance")

ITEM_TOLERANCE = 0.25        # dice steps make an exact average impossible
FIGHT_BAND = (0.7, 1.2)      # damage taken per pack against MM7's stage; a bit easier is fine (user, 2026-11-06)
KILL_TIME_MAX = 1.5          # MM9's HP is kept
TOTAL_BAND = (0.85, 1.15)    # campaign kill gold + quest gold, item drops
TOP_LEVEL_BAND = (0.75, 1.25)  # campaign level-6 drops against MM7's
STAGE_LEVEL_DELTA = 0.6      # a chapter's mean drop treasure level against its MM7 stage's
# Percentage points the common pool may raise an untyped drop's equipment share above MM6-MM8's alone: MM9 brings
# equipment and no consumables of its own.
POOL_EQUIPMENT_SHIFT = 12.0
# A family's mean damage or armour in the common pool against MM6-MM8's alone: 15%, or one point for the small values
# of low levels (MM9's helms are all armoured, MM6-MM8's include hats).
POOL_STAT_TOLERANCE = 0.15
POOL_STAT_POINTS = 1.0
POOL_FAMILIES = ("Sword 1H", "Sword 2H", "Spear", "Axe 1H", "Mace 1H", "Dagger 1H", "Bow", "Leather", "Chain", "Plate",
                 "Shield", "Helm")
# MM7 monsters left out of the stage means: the Fire Hydra (level 45, 76 kills) drops an L3 item every kill, half of
# MM7's stage-4 drops, which no other stage or world does (BALANCE_PLAN.md section 3.3).
MM7_LOOT_OUTLIERS = {"Fire Hydra"}
ENGINE_TABLES = Path("assets_dev/engine/data_tables")
MAPS = Path("assets_dev/worlds/mm9/maps")
EVENTS = Path("assets_dev/worlds/mm9/events")


def tsv(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.reader(handle, delimiter="\t"))


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.failures: list[str] = []
        self.source = "targets"

    def out(self, text: str = "") -> None:
        self.lines.append(text)

    def check(self, ok: bool, message: str) -> str:
        if not ok:
            self.failures.append(message)
        return "ok" if ok else "**out of band**"


def dice_average(text: str) -> float:
    match = re.fullmatch(r"\s*(\d+)[dD](\d+)\s*(?:\+\s*(\d+))?\s*", text or "")
    if not match:
        try:
            return float(text)
        except ValueError:
            return 0.0
    return int(match.group(1)) * (int(match.group(2)) + 1) / 2 + int(match.group(3) or 0)


def items_section(report: Report) -> None:
    rows = tsv(WORLD / "items.txt")
    columns = {name: index for index, name in enumerate(rows[0])}
    data = [row for row in rows[1:] if row and row[0].isdigit()]
    report.out("## Items")
    report.out()
    report.out("Ordinary MM9 weapons and armour against the MM6-MM8 targets of their family and tier (mm9_item_balance.py;")
    report.out(f"the top quality against tier 6), within ±{int(ITEM_TOLERANCE * 100)}% (dice steps).")
    report.out()
    report.out("| Group | Items | Mean of value / target | Outside the band |")
    report.out("| --- | --- | --- | --- |")
    groups: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for row in data:
        rare = row[columns["material"]] in {"Artifact", "Relic", "Special"}
        tier = int(row[columns["normalized_tier"]] or 0)
        if rare or not 1 <= tier <= 6:
            continue
        equip, skill = row[columns["Equip Stat"]], row[columns["Skill Group"]]
        family = item_balance.weapon_family(equip, skill, row[columns["x_mm9_source_name_type"]])
        slot = item_balance.armor_slot(equip, skill)
        if family:
            target = item_balance.weapon_target(family, tier)
            value = dice_average(row[columns["Mod1"]]) + int(row[columns["Mod2"]] or 0)
            groups[family].append((row[columns["Name"]], value / target))
        elif slot:
            target = item_balance.armor_target(slot, tier)
            if target:
                value = int(row[columns["Mod1"]] or 0) + int(row[columns["Mod2"]] or 0)
                groups[f"{slot} (armour)"].append((row[columns["Name"]], value / target))
    for group, values in sorted(groups.items()):
        # Armour keeps MM9's order within a tier, so single pieces spread around the target; the group mean is gated.
        mean = statistics.mean(ratio for _, ratio in values)
        outliers = [f"{name} {ratio:.2f}" for name, ratio in values if abs(ratio - 1) > ITEM_TOLERANCE + 0.25]
        status = report.check(abs(mean - 1) <= ITEM_TOLERANCE, f"items: {group} mean {mean:.2f}")
        report.out(f"| {group} | {len(values)} | {mean:.2f} ({status}) | {', '.join(outliers) or '-'} |")
    report.out()
    uneven = [f"{row[columns['Name']]} {row[columns['Value']]}" for row in data
              if int(row[columns["Value"]] or 0) != item_balance.round_price(int(row[columns["Value"]] or 0))]
    status = report.check(not uneven, f"items: prices not round: {', '.join(uneven[:10])}")
    report.out(f"Round prices (multiples of 5 below 100, 50 below 1,000, 100 above): {len(uneven)} items off ({status}).")
    report.out()


def monsters_section(report: Report) -> None:
    rows = [row for row in tsv(WORLD / "monster_data.txt")[3:] if row and row[0].isdigit()]
    report.out("## Monsters")
    report.out()
    combat = [row for row in rows if monster_balance.family_of(row[1]) is not None]
    slow = [row[1] for row in combat
            if int(row[3] or 0) <= 20 and row[14].isdigit() and 0 < int(row[14]) < monster_balance.LOW_LEVEL_RECOVERY_TICKS]
    spells = []
    for row in combat:
        for use, cell in ((row[24], row[25]), (row[26], row[27])):
            if use.isdigit() and cell not in {"", "0"}:
                cap = (monster_balance.CONDITION_SPELL_USE_CAP
                       if cell.split(",")[0].strip().casefold() in monster_balance.CONDITION_SPELLS
                       else monster_balance.SPELL_USE_CAP)
                if int(use) > cap:
                    spells.append(f"{row[1]} {use}%")
    no_profile = [row[1] for row in combat
                  if not any(value in {"0", "Imm"} or int(value or 0) > monster_balance.base_resistance(int(row[3] or 0))
                             for value in row[28:35])
                  and monster_balance.family_of(row[1])[0:3] != ((), (), ())]
    no_treasure = [row[1] for row in combat if row[12].strip() != "0" and int(row[6] or 0) > 0 and row[7] in {"", "0"}]
    report.out(f"{len(combat)} combat rows (the families of mm9_monster_balance.py); townsfolk, animals and named story")
    report.out("characters keep MM9's numbers.")
    report.out()
    report.out("| Rule | Rows breaking it | Status |")
    report.out("| --- | --- | --- |")
    for name, broken in (("Recovery at least 75 ticks at levels 1-20", slow), ("Spell use within the caps", spells),
                         ("A resistance profile (an immunity, strength or weakness)", no_profile),
                         ("Gold and item treasure on hostile rows with XP", no_treasure)):
        status = report.check(not broken, f"monsters: {name}: {broken[:5]}")
        report.out(f"| {name} | {', '.join(broken[:8]) or '-'} | {status} |")
    report.out()


def shops_section(report: Report) -> None:
    items = {row[0]: row for row in tsv(WORLD / "items.txt")[1:] if row and row[0].isdigit()}
    vendors = tsv(WORLD / "vendors.txt")
    location_column = vendors[0].index("location")
    location = {row[0]: row[location_column] for row in vendors[1:] if row and row[0].isdigit()}
    stock = [row for row in tsv(WORLD / "vendor_stock.txt")[1:] if row and row[0].isdigit()]
    report.out("## Shops")
    report.out()
    report.out("Equipment stock by city: item tier and standard enchant power against the shelf's treasure level")
    report.out("(mm9_vendor_balance.py).")
    report.out()
    report.out("| City | Shop tier | Mean item tier (standard / special) | Enchant power range | Status |")
    report.out("| --- | --- | --- | --- | --- |")
    by_city: dict[str, dict[str, list[tuple[int, int]]]] = defaultdict(lambda: defaultdict(list))
    for row in stock:
        item = items.get(row[4])
        if item is None or item[4] not in vendor_balance.SPECIAL_GROUP:
            continue
        lane = "special" if int(row[3]) >= 15 else "standard"
        by_city[location[row[0]]][lane].append((int(item[21] or 0), int(row[8] or 0)))
    for city, lanes in sorted(by_city.items(), key=lambda kv: vendor_balance.SHOP_TIER_BY_LOCATION.get(kv[0], 0)):
        tier = vendor_balance.SHOP_TIER_BY_LOCATION.get(city, 0)
        powers = [power for lane in lanes.values() for _, power in lane if power]
        low = vendor_balance.STANDARD_MINIMUM[max(1, tier) - 1]
        high = vendor_balance.STANDARD_MAXIMUM[min(6, tier + 1) - 1]
        ok = all(low <= power <= high for power in powers)
        means = " / ".join(f"{statistics.mean(t for t, _ in lanes[lane]):.1f}" if lanes.get(lane) else "-"
                           for lane in ("standard", "special"))
        span = f"+{min(powers)}-{max(powers)}" if powers else "-"
        report.out(f"| {city} | {tier} | {means} | {span} (allowed +{low}-{high}) | "
                   f"{report.check(ok, f'shops: {city} enchant power outside +{low}-{high}')} |")
    report.out()


def loot_values(text: str) -> tuple[float, float]:
    """(average gold, item chance 0-1) of a treasure definition such as 35%5d6+L1Bow."""
    gold = 0.0
    dice = re.search(r"(\d+)[dD](\d+)", text or "")
    if dice:
        gold = int(dice.group(1)) * (int(dice.group(2)) + 1) / 2
    chance = 0.0
    if re.search(r"[lL]\d", text or ""):
        percent = re.match(r"\s*(\d+)%", text)
        chance = (int(percent.group(1)) if percent else 100) / 100
    return gold, chance


def economy_section(report: Report, fit: dict) -> None:
    report.out("## Economy and XP")
    report.out()
    eng = {row[0]: row for row in tsv(Path("assets_dev/engine/data_tables/monster_data.txt"))[3:] if row and row[0].isdigit()}
    by_name = {}
    for row in eng.values():
        by_name.setdefault(row[1], row)
    mm9 = {row[0]: row for row in tsv(WORLD / "monster_data.txt")[3:] if row and row[0].isdigit()}
    gold7 = items7 = 0.0
    for stage in fit["mm7"].values():
        for m, n, _ in stage:
            row = by_name.get(m["name"])
            if row:
                gold, chance = loot_values(row[7])
                gold7 += n * gold
                items7 += n * chance
    groups, _ = fit["mm9_groups"](fit["DENSITY"])
    gold9 = items9 = kills9 = 0.0
    for chapter in groups.values():
        for m, n, _ in chapter:
            row = mm9.get(str(m["id"]))
            if row:
                gold, chance = loot_values(row[7])
                gold9 += n * gold
                items9 += n * chance
                kills9 += n
    quest_gold7, quest_gold9 = 450_000, 236_000   # BALANCE_PLAN.md 3.3 (MM7 one Light/Dark branch)
    total_ratio = (gold9 + quest_gold9) / (gold7 + quest_gold7)
    item_ratio = items9 / items7 if items7 else 0
    report.out("Campaign totals at the planned density, from the generated treasure fields (one kill of every placed or")
    report.out("spawned monster):")
    report.out()
    report.out("| | MM9 | MM7 | Ratio | Status |")
    report.out("| --- | --- | --- | --- | --- |")
    report.out(f"| Kills | {kills9:,.0f} | {sum(n for s in fit['mm7'].values() for _, n, _ in s):,.0f} | | |")
    report.out(f"| Kill gold + quest gold | {gold9 + quest_gold9:,.0f} | {gold7 + quest_gold7:,.0f} | {total_ratio:.2f} | "
               f"{report.check(TOTAL_BAND[0] <= total_ratio <= TOTAL_BAND[1], f'economy: gold ratio {total_ratio:.2f}')} |")
    report.out(f"| Item drops | {items9:,.0f} | {items7:,.0f} | {item_ratio:.2f} | "
               f"{report.check(TOTAL_BAND[0] <= item_ratio <= TOTAL_BAND[1], f'economy: item ratio {item_ratio:.2f}')} |")
    quests = fit["quests_from_profile"]()
    report.out()
    report.out("Quest XP per member by act (mm9_quest_xp_profile.yml; a party of five's promotions, the first tier in act 2's early maps, the second in its late ones): "
               + ", ".join(f"act {fit['STAGE_LABEL'][c]} {v:,.0f}" for c, v in quests.items()) + f"; total {sum(quests.values()):,.0f}.")
    report.out()


def treasure_level_of(text: str) -> int:
    match = re.search(r"[lL](\d)", text or "")
    return int(match.group(1)) if match else 0


def mean_level(levels: dict[int, float]) -> float:
    total = sum(levels.values())
    return sum(level * count for level, count in levels.items()) / total if total else 0.0


def loot_levels_section(report: Report, fit: dict) -> None:
    """Item drops by treasure level per chapter against MM7's stages (BALANCE_PLAN.md section 3.3)."""
    eng = {}
    for row in tsv(ENGINE_TABLES / "monster_data.txt")[3:]:
        if row and row[0].isdigit():
            eng.setdefault(row[1], row)
    mm9 = {row[0]: row for row in tsv(WORLD / "monster_data.txt")[3:] if row and row[0].isdigit()}
    stages7: dict[int, dict[int, float]] = {}
    plain7: dict[int, dict[int, float]] = {}
    for stage, entries in fit["mm7"].items():
        levels: dict[int, float] = defaultdict(float)
        plain: dict[int, float] = defaultdict(float)
        for m, n, _ in entries:
            row = eng.get(m["name"])
            if row is None or not treasure_level_of(row[7]):
                continue
            chance = loot_values(row[7])[1] * n
            levels[treasure_level_of(row[7])] += chance
            if m["name"] not in MM7_LOOT_OUTLIERS:
                plain[treasure_level_of(row[7])] += chance
        stages7[stage], plain7[stage] = levels, plain
    groups, _ = fit["mm9_groups"](fit["DENSITY"])
    chapters9: dict[int, dict[int, float]] = {}
    for chapter, entries in groups.items():
        levels = defaultdict(float)
        for m, n, _ in entries:
            row = mm9.get(str(m["id"]))
            if row is not None and treasure_level_of(row[7]):
                levels[treasure_level_of(row[7])] += loot_values(row[7])[1] * n
        chapters9[chapter] = levels
    report.out("## Drops by treasure level")
    report.out()
    report.out("Expected item drops per treasure level at the planned density: each MM9 act against MM7's stages of it")
    report.out("(the clans act as its early and late maps). The mean leaves out MM7's Fire Hydra (an L3 item on each of 76 kills).")
    report.out()
    report.out("| Act | MM9: L1 / L2 / L3 / L4 / L5 / L6 | MM7: L1 / L2 / L3 / L4 / L5 / L6 | Mean level MM9 (MM7) | Status |")
    report.out("| --- | --- | --- | --- | --- |")
    for chapter in sorted(chapters9):
        nine, seven = chapters9[chapter], stages7.get(chapter, {})
        mean9, mean7 = mean_level(nine), mean_level(plain7.get(chapter, {}))
        ok = abs(mean9 - mean7) <= STAGE_LEVEL_DELTA
        cells = [" / ".join(f"{levels.get(level, 0.0):.0f}" for level in range(1, 7)) for levels in (nine, seven)]
        report.out(f"| {fit['STAGE_LABEL'][chapter]} | {cells[0]} | {cells[1]} | {mean9:.2f} ({mean7:.2f}) | "
                   f"{report.check(ok, f'loot levels: act {fit["STAGE_LABEL"][chapter]} mean {mean9:.2f} against {mean7:.2f}')} |")
    top9 = sum(levels.get(6, 0.0) for levels in chapters9.values())
    top7 = sum(levels.get(6, 0.0) for levels in stages7.values())
    ratio = top9 / top7 if top7 else 0.0
    report.out()
    report.out(f"Level-6 drops over the campaign: {top9:.0f} against MM7's {top7:.0f} ({ratio:.2f}; story bosses, an")
    report.out(f"L6 item every kill, come on top): "
               f"{report.check(TOP_LEVEL_BAND[0] <= ratio <= TOP_LEVEL_BAND[1], f'loot levels: L6 ratio {ratio:.2f}')}.")
    report.out()


def random_weights(path: Path) -> dict[int, list[int]]:
    weights = {}
    for row in tsv(path):
        if len(row) >= 8 and row[0].strip().isdigit():
            weights[int(row[0])] = [int(value or 0) for value in row[2:8]]
    return weights


def item_rows(path: Path) -> list[list[str]]:
    rows = tsv(path)
    header = next(index for index, row in enumerate(rows) if row and row[0] == "Item #")
    return rows[header:]


def equipment_share_section(report: Report) -> None:
    """Random loot rolls from one pool of every world's items (devdocs/LOOT_POOL.md): what MM9's items change
    in it against MM6-MM8's alone."""
    def classify(rows: list[list[str]]) -> dict[int, tuple[str, float] | None]:
        """Ordinary random items: (family, damage or armour) for equipment, None for consumables."""
        columns = {name: index for index, name in enumerate(rows[0])}
        out: dict[int, tuple[str, float] | None] = {}
        for row in rows[1:]:
            if not row or not row[0].strip().isdigit() or len(row) <= columns["material"]:
                continue
            flags = row[columns["content_flags"]] if len(row) > columns["content_flags"] else ""
            if "NoRandom" in flags or row[columns["material"]] in item_balance.RARE_MATERIALS:
                continue
            equip, skill = row[columns["Equip Stat"]], row[columns["Skill Group"]]
            if equip not in item_balance.POOLED_EQUIP_STATS:
                out[int(row[0])] = None
                continue
            family = item_balance.loot_family(equip, skill, "") or equip
            family = item_balance.REFERENCE_FAMILY.get(family, family)
            dice = item_balance.parse_dice(row[columns["Mod1"]])
            mod2 = int(row[columns["Mod2"]] or 0) if row[columns["Mod2"]].lstrip("-").isdigit() else 0
            value = (item_balance.dice_average(*dice) + mod2 if dice
                     else int(row[columns["Mod1"]] or 0) + mod2 if row[columns["Mod1"]].isdigit() else 0)
            out[int(row[0])] = (family, float(value))
        return out

    engine = classify(item_rows(ENGINE_TABLES / "items.txt"))
    world = classify(item_rows(WORLD / "items.txt"))
    engine_weights = random_weights(ENGINE_TABLES / "random_items.txt")
    world_weights = random_weights(WORLD / "random_items.txt")

    def pool(parts: list[tuple[dict, dict]]) -> list[dict[str, float]]:
        """Per treasure level: total weight, equipment weight and per family its weight and weighted stat."""
        levels = [defaultdict(float) for _ in range(6)]
        for items_of, weights in parts:
            for item, vector in weights.items():
                if item not in items_of:
                    continue
                for level in range(6):
                    entry = items_of[item]
                    levels[level]["total"] += vector[level]
                    if entry is not None:
                        levels[level]["equipment"] += vector[level]
                        levels[level][entry[0]] += vector[level]
                        levels[level][entry[0] + " stat"] += vector[level] * entry[1]
        return levels

    alone = pool([(engine, engine_weights)])
    merged = pool([(engine, engine_weights), (world, world_weights)])
    mm9 = pool([(world, world_weights)])
    report.out("## Random loot pool")
    report.out()
    report.out("Random loot rolls from one pool of every world's items; MM9's weigh like MM6-MM8's items of their family")
    report.out("and tier (mm9_item_balance.py). An untyped drop is equipment this often (the rest are the potions,")
    report.out("scrolls, books, reagents, gems and wands of the merged base), MM9's share of that equipment, and the")
    report.out(f"mean of the main families in the pool against MM6-MM8's alone (within ±{int(POOL_STAT_TOLERANCE * 100)}% "
               f"or {POOL_STAT_POINTS:.0f} point).")
    report.out()
    report.out("| | L1 | L2 | L3 | L4 | L5 | L6 | Status |")
    report.out("| --- | --- | --- | --- | --- | --- | --- | --- |")
    share = [[100 * levels[level]["equipment"] / levels[level]["total"] for level in range(6)]
             for levels in (alone, merged)]
    off = [level + 1 for level in range(6) if abs(share[0][level] - share[1][level]) > POOL_EQUIPMENT_SHIFT]
    report.out("| Equipment, MM6-MM8 alone | " + " | ".join(f"{value:.0f}%" for value in share[0]) + " | |")
    report.out("| Equipment, with MM9 | " + " | ".join(f"{value:.0f}%" for value in share[1]) + " | "
               + report.check(not off, f"loot pool: equipment share off at levels {off}") + " |")
    report.out("| MM9's share of equipment | " + " | ".join(
        f"{100 * mm9[level]['equipment'] / merged[level]['equipment']:.0f}%" for level in range(6)) + " | |")
    for family in POOL_FAMILIES:
        cells, off = [], []
        for level in range(6):
            if not alone[level][family] or not merged[level][family]:
                cells.append("-")
                continue
            before = alone[level][family + " stat"] / alone[level][family]
            after = merged[level][family + " stat"] / merged[level][family]
            cells.append(f"{before:.1f} > {after:.1f}")
            if abs(after / before - 1) > POOL_STAT_TOLERANCE and abs(after - before) > POOL_STAT_POINTS:
                off.append(level + 1)
        report.out(f"| {family} | " + " | ".join(cells) + " | "
                   + report.check(not off, f"loot pool: {family} mean off at levels {off}") + " |")
    report.out()


def black_chest_section(report: Report) -> None:
    """MM9's artifacts and relics come only from black chests (BALANCE_PLAN.md section 3.8)."""
    import yaml

    rows = item_rows(WORLD / "items.txt")
    columns = {name: index for index, name in enumerate(rows[0])}
    rare = {}
    for row in rows[1:]:
        if row and row[0].isdigit() and row[columns["material"]] in {"Artifact", "Relic"}:
            rare[int(row[0])] = (row[columns["Name"]], "NoRandom" in row[columns["content_flags"]].split("|"),
                                 int(row[columns["Value"]] or 0))
    level_seven = 0
    fixed: dict[int, set[str]] = defaultdict(set)

    def placed(node, stem: str) -> None:
        # Any item placed in a scene: container fixed items, world items, carried items, searchable props.
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"item_id", "carried_item_id"} and value in rare:
                    fixed[value].add(stem)
                else:
                    placed(value, stem)
        elif isinstance(node, list):
            for value in node:
                placed(value, stem)

    for path in sorted(MAPS.glob("*.scene.yml")):
        scene = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.CSafeLoader)
        for container in scene.get("loot_containers") or []:
            level_seven += bool(container.get("random") and container.get("random_treasure_level") == 7)
        placed(scene, path.name.split(".")[0])
    for path in sorted(EVENTS.rglob("*.lua")):
        for match in re.finditer(r"giveItem\((\d+)\s*,", path.read_text(encoding="utf-8", errors="replace")):
            item = 10000 + int(match.group(1))
            if item in rare:
                fixed[item].add(path.stem)
    rollable = [item for item, (_, no_random, value) in rare.items() if not no_random and value > 0]
    loose = [rare[item][0] for item in fixed if not rare[item][1]]
    report.out("## Artifacts and relics")
    report.out()
    report.out(f"{len(rare)} MM9 artifacts and relics: {len(fixed)} with a fixed source (hand-placed or a quest reward),")
    report.out(f"{len(rollable)} rolled by the black chests' {level_seven} level-7 slots (world.yml chestArtifactsOnly; World:mm9,")
    report.out("so they roll only in MM9 and MM9 rolls no other world's).")
    report.out()
    report.out("| Rule | Breaking it | Status |")
    report.out("| --- | --- | --- |")
    report.out(f"| Fixed-source artifacts keep NoRandom (no second copy from a chest) | {', '.join(loose) or '-'} | "
               f"{report.check(not loose, f'artifacts: fixed-source items without NoRandom: {loose}')} |")
    enough = len(rollable) >= level_seven
    report.out(f"| Every level-7 slot can hold an artifact | {len(rollable)} for {level_seven} | "
               f"{report.check(enough, 'artifacts: fewer rollable artifacts than level-7 chest slots')} |")
    report.out()


def probe_section(report: Report, runs: int, fit: dict) -> None:
    report.out("## Fights (engine balance probe, bolster on)")
    report.out()
    if not PROBE.exists():
        report.out(f"{PROBE} is not built; run `cmake --build build --target openyamm_balance_probe -j25`.")
        report.check(False, "probe: not built")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(PROTOTYPES / "probe_input.py"), str(OUT / "probe_input.tsv"),
                    "--mm9-source", report.source],
                   check=True, capture_output=True)
    subprocess.run([str(PROBE), str(OUT / "probe_input.tsv"), str(OUT / "probe_report.tsv"), "--runs", str(runs),
                    "--no-mm9-changes", "--no-profiles", "--bolster"], check=True, capture_output=True)
    rows = {(row["world"], int(row["stage"])): row
            for row in csv.DictReader((OUT / "probe_report.tsv").open(), delimiter="\t")}
    report.out(f"Each MM9 act against MM7's stages of it, the open clans act as its early and late maps (fit_check.mm9_stage), {runs} fights each; the generated MM9")
    report.out("tables as they are (no probe-side changes).")
    report.out()
    report.out("| Act | Party level (MM7) | Pack (MM7) | Damage per pack vs MM7 | Kill time vs MM7 | Status |")
    label = fit["STAGE_LABEL"]
    report.out("| --- | --- | --- | --- | --- | --- |")
    for chapter in sorted(stage for world, stage in rows if world == "mm9"):
        a, b = rows[("mm7", chapter)], rows[("mm9", chapter)]
        damage = float(b["damage_share"]) / float(a["damage_share"])
        clear = float(b["clear_seconds"]) / float(a["clear_seconds"])
        ok = FIGHT_BAND[0] <= damage <= FIGHT_BAND[1] and clear <= KILL_TIME_MAX
        status = report.check(ok, f"fights: act {label[chapter]} damage x{damage:.2f}, kill time x{clear:.2f}")
        report.out(f"| {label[chapter]} | {b['party_level']} ({a['party_level']}) | {float(b['pack']):.1f} ({float(a['pack']):.1f}) "
                   f"| {damage:.2f} | {clear:.2f} | {status} |")
    report.out()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", action="store_true", help="exit 1 when a value leaves its band")
    parser.add_argument("--runs", type=int, default=8000)
    parser.add_argument("--mm9-source", choices=("targets", "scenes", "dat"), default="targets",
                        help="MM9 monsters: the rebuilt scenes grown by mm9_density_targets.yml (before the growth "
                             "is built), the scenes as they stand (the gate after it) or the original placement")
    args = parser.parse_args()
    argv = sys.argv
    sys.argv = ["fit_check", "--mm9-source", args.mm9_source]
    fit = runpy.run_path(str(PROTOTYPES / "fit_check.py"), run_name="fit")
    sys.argv = argv
    report = Report()
    report.source = args.mm9_source
    report.out("# MM9 balance report")
    report.out()
    report.out(f"MM9 monsters: `--mm9-source {args.mm9_source}`.")
    report.out()
    report.out("Generated by `tools/mm9_import_discovery/mm9_balance_report.py` from the MM9 world tables; the plan is")
    report.out("[BALANCE_PLAN.md](BALANCE_PLAN.md). Do not edit by hand.")
    report.out()
    items_section(report)
    monsters_section(report)
    shops_section(report)
    economy_section(report, fit)
    loot_levels_section(report, fit)
    equipment_share_section(report)
    black_chest_section(report)
    probe_section(report, args.runs, fit)
    report.out("## Result")
    report.out()
    report.out("All checks within their bands." if not report.failures else
               "Out of band:\n\n" + "\n".join(f"- {failure}" for failure in report.failures))
    REPORT.write_text("\n".join(report.lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}: {len(report.failures)} out of band")
    return 1 if args.gate and report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
