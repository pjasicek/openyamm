#!/usr/bin/env python3
"""MAW in MM9: check the single source of MM9's MAW numbers and derive what is made from it.

assets_dev/engine/rulesets/maw/worlds/mm9/balance.yml is the only file edited by hand (devdocs/maw/MM9_BALANCE_DESIGN.md).
This tool
  - checks it against MM9's maps, monsters and quest bits (every map with a band, bands in order, story bands on MM9
    quest bits, completion exclusions naming real monsters),
  - writes item_bases.yml beside it: a MAW base item for each of MM9's ordinary weapons and armour, by the rule in
    balance.yml `items` (MM9's quality on MAW's rungs; the slot's MAW armour; a strength above 1 where the MM9 piece
    outdoes its nearest MM6-MM8 peer),
  - and with --review, a Markdown page for testers: each map's stage, band, story bands and monsters, and each item;
    with --levels also MAW's whole map table, every installed world's maps with their levels under each progression as
    the game computes them (`ruleset maplevels`, run headless through tools/maw/maw_map_levels.scenario.yml), the
    continents side by side and MM9's route checked stage by stage.

  python3 tools/maw/mm9_balance.py [--review output/maw_mm9_review.md [--levels]] [--check]

--check only checks (and fails when item_bases.yml is not what balance.yml gives).
"""

import argparse
import csv
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAW = ROOT / "assets_dev/engine/rulesets/maw"
WORLD = ROOT / "assets_dev/worlds/mm9"
BALANCE = MAW / "worlds/mm9/balance.yml"
ITEM_BASES = MAW / "worlds/mm9/item_bases.yml"

STAGES = ["tutorial", "act1", "early_clans", "clans", "late_side", "war", "finale", "arena"]
# The stages MM9's story walks in order (late side dungeons and the Arena are optional).
STORY_STAGES = ["tutorial", "act1", "early_clans", "clans", "war", "finale"]
CONTINENTS = {1: "Jadame (MM8)", 2: "Antagarich (MM7)", 3: "Enroth (MM6)", 5: "Chedian (MM9)"}
LEVELS_SCENARIO = ROOT / "tools/maw/maw_map_levels.scenario.yml"
LEVELS_TABLE = ROOT / "output/maw_map_levels.tsv"
MONSTERS_TABLE = ROOT / "output/maw_map_monsters.tsv"
WEAPONS = {"Weapon", "Weapon2", "Weapon1or2", "Missile"}
# MM9's ordinary equipment (import_mm9_items.py): artifacts, set pieces and Bootcamp's gear come after it.
ORDINARY = range(10002, 10165)


def fail(errors):
    for error in errors:
        print("error: " + error, file=sys.stderr)
    sys.exit(1)


def read_items(path):
    with open(path, encoding="utf-8", errors="replace") as file:
        rows = list(csv.reader(file, delimiter="\t"))
    header_index = next(i for i, row in enumerate(rows) if row and row[0] == "Item #")
    header = rows[header_index]
    return {int(row[0]): dict(zip(header, row)) for row in rows[header_index + 1:] if row and row[0].strip().isdigit()}


def read_monsters():
    monsters = {}
    with open(WORLD / "data_tables/monster_data.txt", encoding="utf-8", errors="replace") as file:
        for row in csv.reader(file, delimiter="\t"):
            if row and row[0].isdigit():
                monsters[int(row[0])] = {"name": row[1], "picture": row[2], "level": int(row[3] or 0)}
    return monsters


def excluded(exclusions, monster_id, monster):
    for value in exclusions:
        text = str(value)
        if text.isdigit() and int(text) == monster_id:
            return True
        picture = monster["picture"]
        family = len(picture) == len(text) + 2 and picture.startswith(text) and picture[len(text)] == " "
        if text in (monster["name"], picture) or family:
            return True
    return False


def encounter_pictures():
    """MM9's maps' encounter pictures in the engine's map table (Mon1-3 Pic), by file name."""
    pictures = {}
    with open(ROOT / "assets_dev/engine/data_tables/map_stats.txt", encoding="utf-8", errors="replace") as file:
        for row in csv.reader(file, delimiter="\t"):
            if len(row) > 24 and row[0].isdigit() and 9000 <= int(row[0]) < 10000:
                pictures[row[2].lower()] = [row[i] for i in (16, 20, 24) if row[i] and row[i] != "0"]
    return pictures


def placed_families(name, entry, file_exclusions, monsters):
    """The hostile families a map's scene places (counted toward clearing), by picture stem, and the totals."""
    scene = json.load(open(WORLD / "maps" / (name[:-4] + ".scene.yml")))
    placed = counted = 0
    families = {}
    for actor in scene["initial_state"]["actors"]:
        monster = monsters.get(actor.get("monster_id", 0))
        if monster is None or actor.get("mm9_civilian") or actor.get("mm9_guard"):
            continue
        placed += 1
        if excluded(file_exclusions + (entry.get("completion_exclude") or []), actor["monster_id"], monster):
            continue
        counted += 1
        family = re.sub(r" [ABC]$", "", monster["picture"])
        families[family] = families.get(family, 0) + 1
    return families, placed, counted


def scene_check(actors) -> str:
    """The scene's actors as a pack reserve was made against them (mm9_pack_reserve.py, IndoorSceneYml.cpp)."""
    value = 0xcbf29ce484222325
    for actor in actors:
        position = actor["position"]
        for byte in f"{actor['monster_id']},{position['x']},{position['y']},{position['z']};".encode():
            value ^= byte
            value = (value * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return f"{value:016x}"


def pack_reserves(balance):
    """Each map's pack reserve (rulesets/maw/maps/<stem>_zz_maw.scene.yml): its size, the monsters it was made for,
    and whether the installed scene is still the one it was placed against."""
    reserves = {}
    for name in balance["maps"]:
        path = MAW / "maps" / (name[:-4] + "_zz_maw.scene.yml")
        if not path.exists():
            continue
        reserve = (yaml.load(path.read_text(), Loader=yaml.CSafeLoader).get("initial_state") or {}).get("pack_reserve")
        if not reserve:
            continue
        actors = json.load(open(WORLD / "maps" / (name[:-4] + ".scene.yml")))["initial_state"]["actors"]
        fresh = reserve["scene_actors"] == len(actors) and reserve["scene_check"] == scene_check(actors)
        reserves[name] = {"copies": len(reserve["actors"]), "monsters": reserve["monsters"], "fresh": fresh,
                          "reach": 1 + len(reserve["actors"]) / max(1, reserve["monsters"])}
    return reserves


def check_maps(balance, monsters):
    errors = []
    maps = balance.get("maps") or {}
    world_maps = sorted(path.name.lower() for path in (WORLD / "maps").glob("*.blv"))
    for name in world_maps:
        if name not in maps:
            errors.append(f"{name} has no entry")
    pictures = {picture for monster in monsters.values() for picture in
                (monster["picture"], re.sub(r" [ABC]$", "", monster["picture"]))}
    for name, entry in maps.items():
        if name not in world_maps:
            errors.append(f"{name} is no MM9 map")
        for native in entry.get("natives") or []:
            if native not in pictures:
                errors.append(f"{name}: native {native!r} is no MM9 family")
        if entry.get("stage") not in STAGES:
            errors.append(f"{name}: stage must be one of {', '.join(STAGES)}")
        bands = [entry.get("band")] + [story.get("band") for story in entry.get("story_bands") or []]
        for band in bands:
            if not (isinstance(band, list) and len(band) == 3 and band[0] <= band[1] <= band[2] and band[0] >= 1):
                errors.append(f"{name}: a band must be [low, mid, high], rising from 1")
        for story in entry.get("story_bands") or []:
            if not 90000 <= int(story.get("qbit", 0)) <= 99999:
                errors.append(f"{name}: story band quest bit {story.get('qbit')} is no MM9 quest bit (90000-99999)")
    for name, reserve in pack_reserves(balance).items():
        if not reserve["fresh"]:
            errors.append(f"{name}: its pack reserve was made for another scene (run tools/maw/mm9_pack_reserve.py "
                          f"{name[:-4]})")
    for value in list(balance.get("completion_exclude") or []) + [
            value for entry in maps.values() for value in entry.get("completion_exclude") or []]:
        if not any(excluded([value], monster_id, monster) for monster_id, monster in monsters.items()):
            errors.append(f"completion_exclude {value!r} names no MM9 monster")
    return errors


# --- items ---------------------------------------------------------------------------------------------------------

def dice(text):
    match = re.match(r"(\d+)[dD](\d+)", text or "")
    return (int(match.group(1)), int(match.group(2))) if match else None


def average_damage(entry):
    rolled = dice(entry["Mod1"])
    return rolled[0] * (rolled[1] + 1) / 2 + int(entry["Mod2"] or 0) if rolled else 0


def armor_value(entry):
    return int(entry["Mod1"] or 0) + int(entry["Mod2"] or 0)


def slot(entry):
    equip, skill, kind = entry["Equip Stat"], entry["Skill Group"], entry["Not identified name"]
    if equip == "Armor":
        return skill
    if equip == "Helm":
        return "Hat" if kind in ("Hat", "Crown") else "Helm"
    return equip


def derive_bases(balance):
    rules = balance.get("items") or {}
    rungs = {int(quality): float(rung) for quality, rung in (rules.get("rung_by_quality") or {}).items()}
    strength_rule = rules.get("strength") or {}
    best_strength = float(strength_rule.get("best", 1.10))
    top_strength = float(strength_rule.get("best_at_top_quality", 1.15))
    overrides = {int(item_id): value for item_id, value in (rules.get("overrides") or {}).items()}

    engine = read_items(ROOT / "assets_dev/engine/data_tables/items.txt")
    mm9 = read_items(WORLD / "data_tables/items.txt")
    maw_bases = yaml.safe_load(open(MAW / "data/items.yml"))["bases"]

    # MAW's armour by slot and rung (mean of its MM6-MM8 bases) and each slot's reference (the family tops).
    ladder_values, references = {}, {}
    for item_id, base in maw_bases.items():
        entry = engine[item_id]
        if entry["Equip Stat"] in WEAPONS:
            continue
        ladder_values.setdefault((slot(entry), base[0]), []).append(base[3])
        references.setdefault(slot(entry), []).append(base[4])
    ladder = {key: round(statistics.mean(values)) for key, values in ladder_values.items()}
    reference = {key: round(statistics.mean(values)) for key, values in references.items()}

    def ladder_at(slot_name, rung):
        if (slot_name, rung) in ladder:
            return ladder[(slot_name, rung)]
        lower = max(r for (s, r) in ladder if s == slot_name and r < rung)
        upper = min(r for (s, r) in ladder if s == slot_name and r > rung)
        low, high = ladder[(slot_name, lower)], ladder[(slot_name, upper)]
        return round(low + (high - low) * (rung - lower) / (upper - lower))

    ordinary = {item_id: entry for item_id, entry in mm9.items()
                if item_id in ORDINARY and entry["Equip Stat"] in WEAPONS | {
                    "Armor", "Shield", "Helm", "Belt", "Cloak", "Gauntlets", "Boots", "Ring", "Amulet"}}
    groups = {}
    for entry in ordinary.values():
        if entry["Equip Stat"] not in WEAPONS:
            groups.setdefault((slot(entry), entry["normalized_tier"]), []).append(armor_value(entry))

    def nearest_peer(entry, rung, two_handed, armor_class):
        best = None
        equip, skill = entry["Equip Stat"], entry["Skill Group"]
        for item_id, base in maw_bases.items():
            peer = engine[item_id]
            if equip in WEAPONS:
                if skill == "Throwing":
                    fits = peer["Equip Stat"] == "Weapon" and peer["Skill Group"] == (
                        "Axe" if "Axe" in entry["Not identified name"] else "Dagger")
                else:
                    fits = (peer["Skill Group"] in ((skill, "Club") if skill == "Mace" else (skill,))
                            and bool(base[2]) == two_handed
                            and (peer["Equip Stat"] == "Missile") == (equip == "Missile"))
                key = (abs(base[0] - rung), abs(average_damage(peer) - average_damage(entry)))
            else:
                fits = slot(peer) == slot(entry)
                key = (abs(base[0] - rung), abs(base[3] - armor_class))
            if fits and (best is None or key < best[0]):
                best = (key, item_id)
        return best[1]

    # The strongest MM9 piece of each kind and quality (by its own damage or armour; the first id on a tie) is the
    # one a step ahead of its MM6-MM8 peers. Kinds with a single piece at that quality (rings, amulets) have none.
    def kind(entry):
        return (slot(entry) if entry["Equip Stat"] not in WEAPONS
                else f"{entry['Skill Group']} {entry['Equip Stat']}", entry["normalized_tier"])

    members = {}
    for item_id in sorted(ordinary):
        entry = ordinary[item_id]
        if slot(entry) not in ("Ring", "Amulet"):
            value = average_damage(entry) if entry["Equip Stat"] in WEAPONS else armor_value(entry)
            members.setdefault(kind(entry), []).append((value, -item_id))
    best_in_group = {group: -max(values)[1] for group, values in members.items() if len(values) > 1}

    bases = {}
    for item_id in sorted(ordinary):
        entry = ordinary[item_id]
        rung = rungs[int(entry["normalized_tier"])]
        equip = entry["Equip Stat"]
        two_handed = equip == "Weapon2"
        if equip in WEAPONS:
            dice_count, armor_class, reference_class = dice(entry["Mod1"])[0], 0, 0
        else:
            dice_count = 0
            slot_name = slot(entry)
            if slot_name in ("Ring", "Amulet"):
                armor_class = reference_class = 0
            else:
                mean = statistics.mean(groups[(slot_name, entry["normalized_tier"])])
                reference_class = reference[slot_name]
                share = armor_value(entry) / mean if mean else 1
                armor_class = min(reference_class, max(1, round(ladder_at(slot_name, rung) * share)))
        peer_id = nearest_peer(entry, rung, two_handed, armor_class)
        peer = engine[peer_id]
        if equip in WEAPONS:
            ratio = average_damage(entry) / max(average_damage(peer), 1)
        else:
            ratio = armor_value(entry) / max(armor_value(peer), 1) if armor_value(peer) else 1
        strength = 1.0
        if best_in_group.get(kind(entry)) == item_id:
            strength = top_strength if int(entry["normalized_tier"]) == max(rungs) else best_strength
        base = {"rung": rung, "dice": dice_count, "two_handed": int(two_handed), "ac": armor_class,
                "reference_ac": reference_class, "strength": strength}
        base.update(overrides.get(item_id, {}))
        bases[item_id] = {"base": base, "name": entry["Name"], "slot": slot(entry) if equip not in WEAPONS else
                          f"{entry['Skill Group']} {'2H' if two_handed else '1H'}", "quality": entry["normalized_tier"],
                          "peer": f"{peer_id} {peer['Name']}", "ratio": ratio}
    return bases


def item_bases_text(bases, version):
    lines = [
        "# Generated by tools/maw/mm9_balance.py from balance.yml (version " + str(version) + "); do not edit.",
        "# MAW base items of MM9's ordinary weapons and armour: [rung, dice, two-handed, AC, reference AC, strength].",
        "bases:",
    ]
    for item_id, info in bases.items():
        base = info["base"]
        values = [f"{base['rung']:g}", str(base["dice"]), str(base["two_handed"]), str(base["ac"]),
                  str(base["reference_ac"]), f"{base['strength']:g}"]
        lines.append(f"  {item_id}: [{', '.join(values)}]  # {info['name']}, quality {info['quality']}; peer {info['peer']}")
    return "\n".join(lines) + "\n"


# --- review --------------------------------------------------------------------------------------------------------

def native_warnings(balance, monsters):
    """Maps whose natives (balance.yml `natives`, else the map table's encounter pictures) miss what their scenes
    place: a native family with no monster there, or a placed family of a fifth or more of the map left out."""
    warnings = []
    tables = encounter_pictures()
    file_exclusions = balance.get("completion_exclude") or []
    for name, entry in balance["maps"].items():
        families, _, counted = placed_families(name, entry, file_exclusions, monsters)
        if counted == 0:
            continue
        natives = entry.get("natives") or tables.get(name, [])
        for native in natives:
            if families.get(native, 0) == 0:
                warnings.append(f"{name}: native {native} places no monster")
        tiered = {re.sub(r" [ABC]$", "", monster["picture"]) for monster in monsters.values()
                  if re.search(r" [ABC]$", monster["picture"])}
        for family, count in families.items():
            # Only tiered families can be natives; townsfolk, animals and named uniques never are.
            if family in tiered and family not in natives and count * 5 >= counted:
                warnings.append(f"{name}: {family} ({count} of {counted}) is not native")
    return warnings


def review_text(balance, monsters, bases):
    maps = balance["maps"]
    tables = encounter_pictures()
    file_exclusions = balance.get("completion_exclude") or []
    lines = [f"# MAW in MM9: balance review (version {balance['version']})", "",
             "Generated by tools/maw/mm9_balance.py from rulesets/maw/worlds/mm9/balance.yml. Quote the version in a "
             "report.", "", "## Maps", "",
             "| Map | Stage | Band | Natives | Story bands | Starter | Madness | Monsters (counted / placed) | "
             "Density reserve | Families |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    reserves = pack_reserves(balance)
    for stage in STAGES:
        for name, entry in maps.items():
            if entry["stage"] != stage:
                continue
            families, placed, counted = placed_families(name, entry, file_exclusions, monsters)
            natives = ", ".join(n.replace("MM9 ", "") for n in entry.get("natives") or tables.get(name, []))
            stories = ", ".join(f"{story['band']} at {story['qbit']}" for story in entry.get("story_bands") or [])
            starter = "yes" if entry.get("horizontal_starter") else ""
            top = ", ".join(f"{family.replace('MM9 ', '')} {count}"
                            for family, count in sorted(families.items(), key=lambda kv: -kv[1])[:4])
            reserve = reserves.get(name)
            density = f"{reserve['copies']} copies, to x{reserve['reach']:.2f}" if reserve else ""
            lines.append(f"| {name} | {stage} | {entry['band']} | {natives} | {stories} | {starter} | "
                         f"{entry.get('madness_level', '')} | {counted} / {placed} | {density} | {top} |")
    warnings = native_warnings(balance, monsters)
    if warnings:
        lines += ["", "## Natives to check", ""] + [f"- {warning}" for warning in warnings]
    lines += ["", "## Items", "", "| Id | Name | Kind | Quality | Base | Peer | Own / peer |", "|---|---|---|---|---|---|---|"]
    for item_id, info in bases.items():
        base = info["base"]
        text = f"[{base['rung']:g}, {base['dice']}, {base['two_handed']}, {base['ac']}, {base['reference_ac']}, {base['strength']:g}]"
        lines.append(f"| {item_id} | {info['name']} | {info['slot']} | {info['quality']} | {text} | {info['peer']} | "
                     f"{info['ratio']:.2f} |")
    return "\n".join(lines) + "\n"


def engine_map_levels():
    """MAW's map table as the game computes it: runs `ruleset maplevels` in a headless MAW game."""
    binary = ROOT / "build/game/openyamm"
    LEVELS_TABLE.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([str(binary), "--headless-run-scenario", str(LEVELS_SCENARIO), "--scenario-no-color"],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0 or not LEVELS_TABLE.exists():
        fail([f"{LEVELS_SCENARIO.relative_to(ROOT)} failed:\n" + result.stdout[-2000:] + result.stderr[-2000:]])
    with open(LEVELS_TABLE, encoding="utf-8") as file:
        rows = list(csv.DictReader(file, delimiter="\t"))
    for row in rows:
        for key in ("continent", "madness_level", "free", "free_banked", "horizontal", "madness"):
            row[key] = int(float(row[key]))
    return rows


def mm68_encounters():
    """MM6-MM8 maps' monsters at MAW's group sizes, by file name: placed hostile actors plus each encounter spawn
    point's mean group (the map table's Mon1-3 counts with MAW's patch; Hard and Hell raise a group's top by one
    when it is 3 or less, Nightmare its bottom to 2 and its top by one), as MawMonsterRules::adjustMapEncounters."""
    rows = {}
    with open(ROOT / "assets_dev/engine/data_tables/map_stats.txt", encoding="latin-1") as file:
        for row in list(csv.reader(file, delimiter="\t"))[3:]:
            if len(row) > 27 and row[2].strip():
                rows[row[2].strip().lower()] = row
    with open(MAW / "patches/map_stats.txt") as file:
        for line in file.read().splitlines()[1:]:
            fields = line.split("\t")
            if len(fields) == 3 and fields[1] in ("#19", "#23", "#27"):
                for row in rows.values():
                    if row[0].strip() == fields[0]:
                        row[int(fields[1][1:])] = fields[2]

    def span(text):
        text = text.strip()
        if "-" in text:
            low, high = text.split("-")
            return int(low), int(high)
        return (int(text), int(text)) if text.isdigit() else (0, 0)

    counts = {}
    for world in ("mm6", "mm7", "mm8"):
        for path in sorted((ROOT / f"assets_dev/worlds/{world}/maps").glob("*.scene.yml")):
            stem = path.name[:-len(".scene.yml")]
            if "_" in stem:
                continue
            text = path.read_text()
            scene = json.loads(text) if text.lstrip().startswith("{") else yaml.load(text, Loader=yaml.CSafeLoader)
            name = stem + (".odm" if str(scene.get("kind", "")).startswith("outdoor") else ".blv")
            row = rows.get(name)
            if row is None:
                continue
            groups = [span(row[19]), span(row[23]), span(row[27])]
            placed = sum(1 for a in (scene.get("initial_state") or {}).get("actors") or [] if a.get("hostility_type"))
            result = {}
            for mode in ("maw", "nightmare"):
                total = placed
                for spawn in scene.get("spawns") or []:
                    index = spawn.get("index", 0)
                    slot = index if 1 <= index <= 3 else ((index - 4) % 3 + 1 if 4 <= index <= 12 else 0)
                    if spawn.get("type_id") != 3 or not slot:
                        continue
                    low, high = groups[slot - 1]
                    if mode == "nightmare" and high > 1:
                        low, high = max(low, 2), high + 1
                    total += (low + high) / 2
                result[mode] = round(total)
            counts[name] = result
    return counts


def mm9_encounters(balance):
    """MM9 maps' monsters at MAW and Nightmare: the scene's hostile actors, then the pack reserve up to the factor."""
    density = (balance.get("density") or {}).get("difficulty") or {}
    counts = {}
    for name in balance["maps"]:
        actors = json.load(open(WORLD / "maps" / (name[:-4] + ".scene.yml")))["initial_state"]["actors"]
        placed = sum(1 for a in actors if a.get("hostility_type") and not a.get("mm9_civilian") and not a.get("mm9_guard"))
        path = MAW / "maps" / (name[:-4] + "_zz_maw.scene.yml")
        reserve = []
        if path.exists():
            node = (yaml.load(path.read_text(), Loader=yaml.CSafeLoader).get("initial_state") or {}).get("pack_reserve")
            reserve = [entry["from_factor"] for entry in (node or {}).get("actors") or []]
        own = float(balance["maps"][name].get("density", 1.0))
        counts[name] = {mode: placed + sum(1 for f in reserve if f <= float(density.get(mode, 1.0)) * own + 1e-6)
                        for mode in ("maw", "nightmare")}
    return counts


def encounters_text(balance, levels):
    """Each MM9 story map beside the two MM6-MM8 maps whose level (free progression, nothing banked) is nearest."""
    if not MONSTERS_TABLE.exists():
        return ""
    with open(MONSTERS_TABLE, encoding="utf-8") as file:
        monsters = list(csv.DictReader(file, delimiter="\t"))
    families = {}
    for row in monsters:
        if row["tier"] == "2":
            families.setdefault(row["map"], []).append(
                f"{row['family'].replace('MM9 ', '')} L{row['level']} {row['hp']} HP {float(row['attack_damage']):.0f} dmg")
    mm9_counts, other_counts = mm9_encounters(balance), mm68_encounters()
    fought = [row for row in levels if row["free"] > 0]
    others = [row for row in fought if row["continent"] in (1, 2, 3)]
    lines = ["", "### Comparable encounters (a fresh party on each continent)", "",
             "Each MM9 story map beside the two MM6-MM8 maps nearest its level in free progression with nothing banked "
             "elsewhere: the map's level, its monsters at MAW and at Nightmare (MM9: the scene and the pack reserve to "
             "the factor; MM6-MM8: placed actors and each spawn point's mean group), and its native B families' level, "
             "hit points and attack damage as MAW makes them. Written by `ruleset mapmonsters`.", "",
             "| Map | Level | Monsters MAW / Nightmare | B families |", "|---|---|---|---|"]
    for stage in STORY_STAGES:
        for name, entry in balance["maps"].items():
            mine = next((row for row in fought if row["map"] == name), None)
            if entry["stage"] != stage or mine is None:
                continue
            counts = mm9_counts.get(name, {})
            lines.append(f"| **{name}** ({stage}) | {mine['free']} | {counts.get('maw', '')} / {counts.get('nightmare', '')} | "
                         f"{'; '.join(families.get(name, []))} |")
            for other in sorted(others, key=lambda row: abs(row["free"] - mine["free"]))[:2]:
                c = other_counts.get(other["map"], {})
                lines.append(f"| &nbsp;&nbsp;{other['map']} {other['name']} ({CONTINENTS[other['continent']]}) | "
                             f"{other['free']} | {c.get('maw', '')} / {c.get('nightmare', '')} | "
                             f"{'; '.join(families.get(other['map'], []))} |")
    return "\n".join(lines) + "\n"


def levels_text(balance, rows):
    maps = balance["maps"]
    fought = [row for row in rows if row["free"] > 0]
    lines = ["", "## MAW's map table, all continents", "",
             "Each map's level as the journal's Progress tab counts it (its native families' B levels): free progression "
             "with no levels banked elsewhere and with 50, horizontal progression, Beyond Madness. Maps without native "
             "families (cities, scripted fights) are left out. Written by `ruleset maplevels`.", "",
             "| Continent | Maps | Free (no banks) | Horizontal | Beyond Madness |", "|---|---|---|---|---|"]
    for continent, label in CONTINENTS.items():
        own = [row for row in fought if row["continent"] == continent]
        if own:
            span = lambda key: f"{min(r[key] for r in own)}-{max(r[key] for r in own)}"
            lines.append(f"| {label} | {len(own)} | {span('free')} | {span('horizontal')} | {span('madness')} |")

    # MM9's story in order: a story stage's maps should not sit below the stage before it.
    lines += ["", "### MM9's route, stage by stage (horizontal)", "", "| Stage | Maps | Free | Horizontal |", "|---|---|---|---|"]
    warnings = []
    by_file = {row["map"]: row for row in fought}
    previous = None
    for stage in STAGES:
        own = [by_file[name] for name, entry in maps.items() if entry["stage"] == stage and name in by_file]
        if not own:
            continue
        lines.append(f"| {stage} | {', '.join(r['map'][:-4] for r in sorted(own, key=lambda r: r['horizontal']))} | "
                     f"{min(r['free'] for r in own)}-{max(r['free'] for r in own)} | "
                     f"{min(r['horizontal'] for r in own)}-{max(r['horizontal'] for r in own)} |")
        if stage in STORY_STAGES:
            if previous is not None:
                floor = statistics.mean(r["horizontal"] for r in previous)
                warnings += [f"{r['map']} ({stage}, horizontal {r['horizontal']}) sits below the previous story "
                             f"stage's mean ({floor:.0f})" for r in own if r["horizontal"] < floor]
            previous = own
    if warnings:
        lines += ["", "Route to check:", ""] + [f"- {warning}" for warning in warnings]

    lines += ["", "### Every map by horizontal level", "",
              "| Horizontal | Free | Free (50 banked) | Beyond Madness | Map | Continent | Band | MM9 stage |",
              "|---|---|---|---|---|---|---|---|"]
    for row in sorted(fought, key=lambda r: (r["horizontal"], r["free"])):
        stage = maps.get(row["map"], {}).get("stage", "")
        band = f"[{float(row['low']):g}, {float(row['mid']):g}, {float(row['high']):g}]"
        lines.append(f"| {row['horizontal']} | {row['free']} | {row['free_banked']} | {row['madness']} | "
                     f"{row['map']} {row['name']} | {CONTINENTS.get(row['continent'], row['continent'])} | {band} | "
                     f"{stage} |")
    return "\n".join(lines) + "\n", warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--review", type=Path, help="write the testers' review page (Markdown) here")
    parser.add_argument("--check", action="store_true", help="only check; fail when item_bases.yml is stale")
    parser.add_argument("--levels", action="store_true",
                        help="with --review: add MAW's whole map table, computed by the game (needs build/game/openyamm)")
    arguments = parser.parse_args()

    balance = yaml.safe_load(open(BALANCE))
    monsters = read_monsters()
    errors = check_maps(balance, monsters)
    if errors:
        fail(errors)

    for warning in native_warnings(balance, monsters):
        print("natives: " + warning)

    bases = derive_bases(balance)
    text = item_bases_text(bases, balance["version"])
    if arguments.check:
        if not ITEM_BASES.exists() or ITEM_BASES.read_text() != text:
            fail([f"{ITEM_BASES.relative_to(ROOT)} is not what balance.yml gives: run tools/maw/mm9_balance.py"])
    else:
        ITEM_BASES.write_text(text)
        stronger = sum(1 for info in bases.values() if info["base"]["strength"] > 1)
        print(f"{ITEM_BASES.relative_to(ROOT)}: {len(bases)} bases, {stronger} stronger than their peers")

    if arguments.review:
        arguments.review.parent.mkdir(parents=True, exist_ok=True)
        text = review_text(balance, monsters, bases)
        if arguments.levels:
            map_levels = engine_map_levels()
            levels, warnings = levels_text(balance, map_levels)
            text += levels + encounters_text(balance, map_levels)
            for warning in warnings:
                print("route: " + warning)
        arguments.review.write_text(text)
        print(f"review: {arguments.review}")
    print(f"balance.yml version {balance['version']}: {len(balance['maps'])} maps checked")


if __name__ == "__main__":
    main()
