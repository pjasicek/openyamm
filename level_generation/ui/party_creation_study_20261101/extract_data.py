#!/usr/bin/env python3
"""Extract the real party-creation data for the party creation study into data.js.

Reads the Standard tables under assets_dev/engine/data_tables/ and applies the MAW ruleset's patches the way
RulesetDefinition.h describes them (override cells, appended rows and columns, replaced tables). Mirrors the creation
rules of ClassSkillTable::getEffectiveCap / getHighestPromotionEffectiveCap /
getEffectiveStartingSkillAvailability and NewGameScreen::refreshSkillChoices so the mockups show the same caps,
fixed skills and choices as the game. Run from anywhere: python3 extract_data.py
"""

import json
import os
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TABLES = ROOT / "assets_dev/engine/data_tables"
MAW = ROOT / "assets_dev/engine/rulesets/maw"
ICONS = ROOT / "assets_dev/engine/icons_x2"
AUDIO = ROOT / "assets_dev/engine/audio"
CLASS_ICONS = ROOT / "assets_dev/engine/hud_x2/menus/classes"

MASTERY = {"-": 0, "": 0, "B": 1, "N": 1, "E": 2, "M": 3, "G": 4}
MASTERY_NAMES = {"none": 0, "normal": 1, "expert": 2, "master": 3, "grandmaster": 4}

# NewGameScreen.cpp OrderedSkillNames (creation order); MAW's four ruleset skills follow.
ORDERED_SKILLS = [
    "Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Throwing", "Mace", "Blaster", "Shield", "LeatherArmor",
    "ChainArmor", "PlateArmor", "FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic",
    "BodyMagic", "LightMagic", "DarkMagic", "DarkElfAbility", "VampireAbility", "DragonAbility", "IdentifyItem",
    "Merchant", "RepairItem", "Bodybuilding", "Meditation", "Perception", "Regeneration", "DisarmTraps", "Dodging",
    "Unarmed", "IdentifyMonster", "Armsmaster", "Stealing", "Alchemy", "Learning",
]
MAW_SKILLS = ["Cover", "ManaShield", "Enlightenment", "Retaliation"]

# Grouping used by every mockup (the game's skill sheet groups, with racial abilities split out).
SKILL_GROUPS = {
    "Weapons": ["Staff", "Sword", "Dagger", "Axe", "Spear", "Bow", "Throwing", "Mace", "Blaster", "Unarmed"],
    "Armour": ["Shield", "LeatherArmor", "ChainArmor", "PlateArmor", "Dodging", "Cover", "Retaliation", "ManaShield"],
    "Magic": ["FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "SpiritMagic", "MindMagic", "BodyMagic",
              "LightMagic", "DarkMagic"],
    "Racial": ["DarkElfAbility", "VampireAbility", "DragonAbility"],
    "Misc": ["IdentifyItem", "Merchant", "RepairItem", "Bodybuilding", "Meditation", "Perception", "Regeneration",
             "DisarmTraps", "IdentifyMonster", "Armsmaster", "Stealing", "Alchemy", "Learning", "Enlightenment"],
}

SKILL_ALIASES = {
    "thrown": "Throwing", "throwingweapon": "Throwing", "throwingweapons": "Throwing", "leather": "LeatherArmor",
    "chain": "ChainArmor", "plate": "PlateArmor", "fire": "FireMagic", "air": "AirMagic", "water": "WaterMagic",
    "earth": "EarthMagic", "spirit": "SpiritMagic", "mind": "MindMagic", "body": "BodyMagic", "light": "LightMagic",
    "dark": "DarkMagic", "darkelf": "DarkElfAbility", "vampire": "VampireAbility", "dragon": "DragonAbility",
    "iditem": "IdentifyItem", "repair": "RepairItem", "bbuilding": "Bodybuilding", "meditate": "Meditation",
    "disarm": "DisarmTraps", "disarmtrap": "DisarmTraps", "identmon": "IdentifyMonster",
}
SKILL_DISPLAY = {
    "Throwing": "Throwing", "LeatherArmor": "Leather Armor", "ChainArmor": "Chain Armor", "PlateArmor": "Plate Armor",
    "FireMagic": "Fire Magic", "AirMagic": "Air Magic", "WaterMagic": "Water Magic", "EarthMagic": "Earth Magic",
    "SpiritMagic": "Spirit Magic", "MindMagic": "Mind Magic", "BodyMagic": "Body Magic", "LightMagic": "Light Magic",
    "DarkMagic": "Dark Magic", "DarkElfAbility": "Dark Elf Ability", "VampireAbility": "Vampire Ability",
    "DragonAbility": "Dragon Ability", "IdentifyItem": "Identify Item", "RepairItem": "Repair Item",
    "Bodybuilding": "Body Building", "IdentifyMonster": "Identify Monster", "DisarmTraps": "Disarm Traps",
    "ManaShield": "Mana Shield",
}
RACIAL_ABILITY = {1: "VampireAbility", 2: "DarkElfAbility", 5: "DragonAbility"}

# MawClassRules.cpp FlatSkillBonuses / RaceResistanceTable (display data for the race card).
MAW_FLAT_SKILLS = {0: ["LeatherArmor", "ChainArmor", "PlateArmor", "Shield"], 2: ["Bow", "Spear", "Meditation"],
                   7: ["Bow", "Spear", "Meditation"], 3: ["Axe"], 4: ["Regeneration", "Mace", "Staff"],
                   8: ["Sword", "Mace", "Dagger", "LeatherArmor"], 9: ["Shield", "Bodybuilding"]}
MAW_RESIST = {2: (["Fire", "Air", "Water", "Earth"], 25, 1), 7: (["Fire", "Air", "Water", "Earth"], 25, 1),
              4: (["Water", "Earth"], 25, 1), 8: (["Air", "Earth"], 25, 1), 9: (["Mind", "Earth"], 25, 1),
              5: (["Fire"], 100, 2), 6: (["Body", "Mind"], 0, 0), 1: (["Mind"], 0, 0)}

STATS = ["Might", "Intellect", "Personality", "Endurance", "Accuracy", "Speed", "Luck"]


def key(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def read_tsv(path):
    with open(path, encoding="cp1252", errors="replace") as handle:
        return [line.rstrip("\r\n").split("\t") for line in handle]


def canonical_classes():
    source = (ROOT / "game/party/SkillData.cpp").read_text()
    block = source.split("CanonicalClassNames = {", 1)[1].split("};", 1)[0]
    return re.findall(r'"([^"]*)"', block)


CANON_CLASSES = canonical_classes()
CLASS_LOOKUP = {key(name): index for index, name in enumerate(CANON_CLASSES)}
CLASS_LOOKUP.update({"cleric2": 5, "priestoflight": 6, "priestofthelight": 6, "priestofdark": 7,
                     "priestofthedark": 7, "darkarchmage": 47})


def canon_skill(name):
    token = key(name)
    if token in SKILL_ALIASES:
        return SKILL_ALIASES[token]
    for skill in ORDERED_SKILLS + MAW_SKILLS:
        if key(skill) == token:
            return skill
    return None


def apply_override(rows, patch_path, key_column=0, header_row=0):
    """RulesetDefinition.h override: "key<TAB>column<TAB>value" cells."""
    header = rows[header_row]
    for cells in read_tsv(patch_path)[1:]:
        if len(cells) < 3:
            continue
        row_key, column, value = cells[0], cells[1], cells[2]
        if column.startswith("#"):
            column_index = int(column[1:])
        else:
            matches = [i for i, name in enumerate(header) if name == column] or \
                      [i for i, name in enumerate(header) if key(name) == key(column)]
            if not matches:
                continue
            column_index = matches[0]
        if key_column == "row":
            index = int(row_key)
            while index >= len(rows):
                rows.append([""] * len(header))
            targets = [rows[index]]
        else:
            targets = [row for row in rows[header_row + 1:] if len(row) > key_column and row[key_column] == row_key]
            if not targets:
                targets = [row for row in rows[header_row + 1:]
                           if len(row) > key_column and key(row[key_column]) == key(row_key)]
            targets = targets[:1]
        for row in targets:
            while len(row) <= column_index:
                row.append("")
            row[column_index] = value
    return rows


def apply_append(rows, path):
    rows.extend(row for row in read_tsv(path) if any(cell.strip() for cell in row))
    return rows


def apply_append_columns(rows, path):
    extra = read_tsv(path)
    names = extra[0][1:]
    by_key = {row[0]: row[1:] for row in extra[1:] if row and row[0]}
    width = len(rows[0])
    rows[0] = rows[0] + names
    for row in rows[1:]:
        row.extend([""] * (width - len(row)))
        values = by_key.get(row[0], [])
        row.extend((values + ["-"] * len(names))[:len(names)])
    return rows


def load_ruleset(maw):
    # --- class skill caps (columns are class ids by position) ---
    caps_rows = read_tsv(TABLES / "class_skills.txt")
    if maw:
        apply_override(caps_rows, MAW / "patches/class_skills.txt")
        apply_append(caps_rows, MAW / "patches/class_skills.append.txt")
        apply_append_columns(caps_rows, MAW / "patches/class_skills.columns.txt")
    class_count = len(caps_rows[0]) - 1
    caps = {class_id: {} for class_id in range(class_count)}
    for row in caps_rows[1:]:
        skill = canon_skill(row[0]) if row and row[0] else None
        if not skill:
            continue
        for class_id in range(class_count):
            cell = row[class_id + 1].strip() if class_id + 1 < len(row) else "-"
            caps[class_id][skill] = MASTERY.get(cell, 0)

    # --- class metadata ---
    extra_rows = read_tsv(TABLES / "class_extra.txt")
    if maw:
        apply_append(extra_rows, MAW / "patches/class_extra.append.txt")
    classes = {}
    for row in extra_rows[1:]:
        if len(row) < 4 or not row[0].strip().isdigit():
            continue
        class_id = int(row[0])
        if class_id >= len(CANON_CLASSES) or row[3] == "n/u":
            continue
        classes[class_id] = {"id": class_id, "canon": CANON_CLASSES[class_id], "name": row[3].strip(),
                             "kind": int(row[1]), "step": int(row[2])}
    if 48 in classes:
        classes[48]["name"] = "Peasant"

    mult_rows = read_tsv(TABLES / "class_multipliers.txt")
    if maw:
        apply_override(mult_rows, MAW / "patches/class_multipliers.txt")
        apply_append(mult_rows, MAW / "patches/class_multipliers.append.txt")
    mana_mode = {}
    for row in mult_rows[1:]:
        if len(row) >= 6 and key(row[0]) in CLASS_LOOKUP:
            token = key(row[5])
            mana_mode[CLASS_LOOKUP[key(row[0])]] = {"intellect": 1, "intelligence": 1, "personality": 2,
                                                    "mixed": 3}.get(token, 4 if token == "level" else 0)
    for class_id, entry in classes.items():
        entry["mana"] = mana_mode.get(class_id, 0)

    desc_rows = read_tsv(TABLES / "english/class.txt")
    if maw:
        apply_override(desc_rows, MAW / "patches/english/class.txt")
        if (MAW / "patches/english/class.append.txt").exists():
            apply_append(desc_rows, MAW / "patches/english/class.append.txt")
        apply_override(desc_rows, MAW / "content/class_patch.txt")
    for row in desc_rows[1:]:
        if len(row) >= 2 and key(row[0]) in CLASS_LOOKUP and CLASS_LOOKUP[key(row[0])] in classes:
            classes[CLASS_LOOKUP[key(row[0])]]["desc"] = row[1].strip().strip('"').replace("  ", " ")

    # --- starting skills ---
    start_rows = read_tsv(TABLES / "class_starting_skills.txt")
    if maw:
        apply_override(start_rows, MAW / "patches/class_starting_skills.txt")
        apply_override(start_rows, MAW / "content/class_starting_skills_patch.txt")
        apply_append(start_rows, MAW / "content/class_starting_skills_new.txt")
    start_header = [canon_skill(name) for name in start_rows[0]]
    starting = {}
    for row in start_rows[1:]:
        if not row or key(row[0]) not in CLASS_LOOKUP:
            continue
        class_id = CLASS_LOOKUP[key(row[0])]
        starting[class_id] = {start_header[i]: row[i].strip() for i in range(1, min(len(row), len(start_header)))
                              if start_header[i] and row[i].strip() in ("F", "C")}

    # --- race stats ---
    stat_rows = read_tsv(TABLES / "class_starting_stats.txt")
    if maw:
        apply_override(stat_rows, MAW / "patches/class_starting_stats.txt", key_column="row")
    stat_header = stat_rows[0]

    # --- race / class availability ---
    selection_path = MAW / "content/character_selection.yml" if maw else TABLES / "character_selection.yml"
    selection = yaml.safe_load(selection_path.read_text())
    free_selection = bool(selection.get("free_selection", False))
    races = {}
    for entry in selection["race_class_availability"]:
        race_id = entry["race_id"]
        column = next(i for i, name in enumerate(stat_header) if f"({race_id})" in name)
        stats = []
        for stat_index in range(7):
            base_text = stat_rows[1 + stat_index * 2][column]
            add_text = stat_rows[2 + stat_index * 2][column]
            base, maximum = (int(part) for part in base_text.split("/"))
            if "/" in add_text:
                add_step, dropped_step = (int(part) for part in add_text.split("/"))
            else:
                add_step = int(add_text)
                dropped_step = 1 if base > 11 else add_step
            stats.append([base, maximum, add_step, dropped_step])
        race_name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", entry["race"])
        races[race_id] = {"id": race_id, "name": race_name, "stats": stats,
                          "classes": [CLASS_LOOKUP[key(name)] for name in entry.get("classes") or []
                                      if key(name) in CLASS_LOOKUP]}

    # --- race skill rules ---
    race_skill_path = MAW / "content/race_skills.yml" if maw else TABLES / "race_skills.yml"
    race_skill_doc = yaml.safe_load(race_skill_path.read_text())
    shift_without_cap = bool(race_skill_doc.get("shift_without_class_cap", False))
    rules = []
    for rule in race_skill_doc["rules"]:
        exception = str(rule.get("exception", "none")).lower()
        exception_code = {"none": 0, "w": -5, "warrior": -5, "warriors": -5, "s": -4, "spellcaster": -4,
                          "p": -2, "ip": -3}.get(exception)
        if exception_code is None:
            exception_code = int(exception) if exception.lstrip("-").isdigit() else 0
        max_text = rule.get("max_mastery")
        rules.append({"race": rule["race_id"], "skill": canon_skill(rule["skill"]),
                      "min": MASTERY_NAMES.get(str(rule.get("min_mastery", "none")).lower(), 0),
                      "max": None if max_text is None else MASTERY_NAMES[str(max_text).lower()],
                      "add": int(rule.get("add", 0)), "exception": exception_code,
                      "kind": rule.get("class_kind")})

    def rule_applies(rule, class_id):
        info = classes.get(class_id, {"kind": 0, "mana": 0})
        if rule["kind"] is not None:
            return info["kind"] != 0 and info["kind"] == rule["kind"]
        code = rule["exception"]
        if code > 0:
            return info["kind"] != code
        if code in (-1, -2, -3):
            return info["mana"] != -code
        if code == -4:
            return info["mana"] != 0
        if code == -5:
            return info["mana"] == 0
        return True

    def effective_cap(class_id, race_id, skill):
        base = caps.get(class_id, {}).get(skill, 0)
        minimum, maximum, add = 0, None, 0
        for rule in rules:
            if rule["race"] != race_id or rule["skill"] != skill or not rule_applies(rule, class_id):
                continue
            minimum = max(minimum, rule["min"])
            if rule["max"] is not None and (maximum is None or rule["max"] < maximum):
                maximum = rule["max"]
            add = max(add, rule["add"])
        if shift_without_cap:
            shifted = base + add
            if maximum is not None:
                shifted = min(shifted, maximum)
            return max(0, min(4, max(shifted, minimum)))
        result = max(base, minimum)
        if base != 0:
            result += add
        return max(0, min(4, result))

    def promotions(class_id):
        info = classes[class_id]
        return sorted(other for other, entry in classes.items()
                      if entry["kind"] == info["kind"] and entry["step"] == info["step"] + 1 and info["kind"] != 0)

    def starting_availability(class_id, race_id, skill):
        if effective_cap(class_id, race_id, skill) == 0:
            return ""
        base = starting.get(class_id, {}).get(skill, "")
        if base:
            return base
        if caps.get(class_id, {}).get(skill, 0) == 0:
            for rule in rules:
                if rule["race"] == race_id and rule["skill"] == skill and rule["min"] > 0 and rule_applies(rule, class_id):
                    return "C"
        return ""

    skills = ORDERED_SKILLS + (MAW_SKILLS if maw else [])
    letters = "-BEMG"

    def caps_string(class_id, race_id):
        return "".join(letters[effective_cap(class_id, race_id, skill)] for skill in skills)

    # --- every race x starting class combination ---
    combos = {}
    starting_class_ids = set()
    for race_id, race in races.items():
        for class_id in race["classes"]:
            starting_class_ids.add(class_id)
    if not maw:
        starting_class_ids.update({5, 42, 4, 44})
    for race_id, race in races.items():
        offered = set(race["classes"])
        if not maw:
            offered |= {5 if c == 4 else 4 if c == 5 else 42 if c == 44 else 44 if c == 42 else c for c in offered}
        for class_id in sorted(offered):
            if class_id not in classes:
                continue
            tree, pending = [], [class_id]
            while pending:
                current = pending.pop(0)
                tree.append({"id": current, "caps": caps_string(current, race_id)})
                pending.extend(promotions(current))
            best = []
            for index, skill in enumerate(skills):
                best.append(max(letters.index(node["caps"][index]) for node in tree))
            start = []
            racial = RACIAL_ABILITY.get(race_id)
            for skill in skills:
                if skill in MAW_SKILLS:
                    start.append("-")
                    continue
                availability = starting_availability(class_id, race_id, skill)
                if racial == skill:
                    availability = "F"
                start.append(availability or "-")
            combos[f"{race_id}:{class_id}"] = {"now": tree[0]["caps"], "best": "".join(letters[b] for b in best),
                                               "start": "".join(start), "tree": tree}

    # --- race card text ---
    for race_id, race in races.items():
        lines = []
        for rule in rules:
            if rule["race"] != race_id or not rule["skill"]:
                continue
            name = SKILL_DISPLAY.get(rule["skill"], rule["skill"])
            parts = []
            if rule["min"]:
                parts.append(f"at least {['', 'Normal', 'Expert', 'Master', 'Grandmaster'][rule['min']]}")
            if rule["max"] is not None:
                parts.append("forbidden" if rule["max"] == 0 else f"at most {['', 'Normal', 'Expert', 'Master', 'Grandmaster'][rule['max']]}")
            if rule["add"]:
                parts.append(f"+{rule['add']} mastery rank")
            note = {-5: " (warrior classes)", -4: " (casters)"}.get(rule["exception"], "")
            if rule["exception"] > 0:
                note = f" (not {next((c['name'] for c in classes.values() if c['kind'] == rule['exception'] and c['step'] == 0), 'kind ' + str(rule['exception']))} line)"
            lines.append({"skill": rule["skill"], "text": f"{name}: {', '.join(parts)}{note}"})
        race["skillRules"] = lines
        notes = []
        if maw:
            if race_id in MAW_FLAT_SKILLS:
                names = [SKILL_DISPLAY.get(s, s) for s in MAW_FLAT_SKILLS[race_id]]
                notes.append(f"+3 to {', '.join(names)} (+1 per 10 skill levels)")
            if race_id in MAW_RESIST:
                elements, base, per_level = MAW_RESIST[race_id]
                notes.append(f"Immune to {', '.join(elements)} magic" if base == 0 else
                             f"{', '.join(elements)} resistance +{base}, +{per_level} per level")
            if race_id == 1:
                notes.append("Preservation at night and in dungeons")
            race["flatSkills"] = MAW_FLAT_SKILLS.get(race_id, [])
        race["notes"] = notes

    # --- portraits ---
    portrait_rows = read_tsv(TABLES / "character_data.txt")
    if maw:
        apply_override(portrait_rows, MAW / "content/character_data_patch.txt")
        apply_append(portrait_rows, MAW / "content/character_data.append.txt")
    icon_files = {name.lower() for name in os.listdir(ICONS)}
    portraits = []
    for row in portrait_rows[1:]:
        if len(row) < 24 or not row[0].strip().isdigit():
            continue
        race_id = int(row[23]) if row[23].strip().lstrip("-").isdigit() else -1
        available = row[5].strip() == "x"
        if race_id < 0 or race_id not in races or not races[race_id]["classes"]:
            continue
        if not available and not free_selection:
            continue
        image = (row[19].strip() + "01").lower() + ".png"
        if image not in icon_files:
            continue
        portraits.append({"id": int(row[0]), "race": race_id, "sex": int(row[4]), "defClass": int(row[2]),
                          "voice": int(row[3]), "img": image, "note": row[24].strip() if len(row) > 24 else "",
                          "start": available, "doll": doll_layers(row, icon_files)})

    skill_text_rows = read_tsv(TABLES / "english/skill_des.txt")
    if maw:
        apply_override(skill_text_rows, MAW / "content/skill_des_patch.txt")
        apply_append(skill_text_rows, MAW / "content/skill_des_new.txt")
    skill_text = {}
    for row in skill_text_rows[1:]:
        skill = canon_skill(row[0]) if row else None
        if skill:
            cells = [cell.strip().strip('"').replace("�", "'") for cell in row[1:6]] + [""] * 5
            skill_text[skill] = {"desc": re.sub(r"\s+", " ", cells[0]), "m": cells[1:5]}

    continents = [{"key": entry["key"], "name": entry["name"], "classIds": entry.get("available_class_ids", [])}
                  for entry in yaml.safe_load((TABLES / "character_selection.yml").read_text())["new_game_continents"]]

    return {
        "skills": skills,
        "classes": classes,
        "races": races,
        "portraits": portraits,
        "combos": combos,
        "skillText": skill_text,
        "freeSelection": free_selection,
        "continents": continents,
    }


def doll_layers(row, icon_files):
    """Creation paperdoll layers as NewGameScreen::buildCreationPreviewDollPixels composites them: background, body
    at its offset, then the open hands at the doll type's positions (logical units, icons_x2 images are 2x)."""
    def image(cell):
        name = cell.strip().lower()
        return name + ".png" if name and name not in ("none", "null") and name + ".png" in icon_files else ""

    def number(cell):
        return int(cell) if cell.strip().lstrip("-").isdigit() else 0

    return {"type": number(row[1]), "bg": image(row[8]), "body": image(row[9]), "bx": number(row[6]),
            "by": -number(row[7]), "lh": image(row[13]), "rh": image(row[17])}


def load_doll_types():
    types = {}
    for row in read_tsv(TABLES / "doll_types.txt")[1:]:
        if len(row) < 28 or not row[0].strip().isdigit():
            continue
        value = lambda cell: int(cell) if cell.strip().lstrip("-").isdigit() else 0
        # Right hand open (columns 8/9) and the left open hand position the creation doll uses (columns 18/19).
        types[int(row[0])] = {"rh": [value(row[8]), -value(row[9])], "lh": [value(row[18]), -value(row[19])]}
    return types


def load_voices():
    rows = read_tsv(TABLES / "character_voices.txt")
    header = rows[0]
    sound_names = {}
    for row in read_tsv(TABLES / "sounds.txt"):
        if len(row) >= 2 and not row[0].startswith("/") and row[1].strip().isdigit():
            sound_names[int(row[1])] = row[0].strip()
    audio_files = {name.lower(): name for name in os.listdir(AUDIO)}
    kinds = {}
    notes = {}
    categories = []
    in_lines = True
    for row in rows[1:]:
        if not row or not row[0].strip():
            in_lines = False
            continue
        if in_lines:
            categories.append(row)
        elif row[0] in ("Man", "Woman", "Dragon", "Undead Man", "Undead Woman", "Undead Dragon"):
            for index, cell in enumerate(row[1:]):
                if cell.strip() == "x":
                    kinds[index] = row[0]
        elif row[0] == "Notes":
            for index, cell in enumerate(row[1:]):
                if cell.strip():
                    notes[index] = cell.strip()
    voices = []
    for column in range(1, len(header)):
        if not header[column].strip().isdigit():
            continue
        voice_id = int(header[column])
        lines = []
        for row in categories:
            category = row[0].strip()
            if category.startswith("n/u") or column >= len(row):
                continue
            cell = row[column].strip()
            if not cell.isdigit() or int(cell) == 0:
                continue
            name = sound_names.get(int(cell))
            if name and (name.lower() + ".wav") in audio_files:
                lines.append([category, audio_files[name.lower() + ".wav"]])
        voices.append({"id": voice_id, "kind": kinds.get(column - 1, ""), "note": notes.get(column - 1, ""),
                       "lines": lines})
    return voices


def load_names():
    rows = read_tsv(TABLES / "english/pc_names.txt")
    names = {"male": [], "female": []}
    for row in rows[1:]:
        if len(row) > 1 and row[0].strip() and row[0] != "*end":
            names["male"].append(row[0].strip())
        if len(row) > 1 and row[1].strip() and row[1] != "*end":
            names["female"].append(row[1].strip())
    return {key_: values[::7][:40] for key_, values in names.items()}


def main():
    class_icons = sorted(path.stem for path in CLASS_ICONS.glob("*.png"))
    data = {
        "standard": load_ruleset(False),
        "maw": load_ruleset(True),
        "voices": load_voices(),
        "names": load_names(),
        "skillGroups": SKILL_GROUPS,
        "skillDisplay": SKILL_DISPLAY,
        "statNames": STATS,
        "classIcons": class_icons,
        "dollTypes": load_doll_types(),
    }
    text = "// Generated by extract_data.py from assets_dev/engine/data_tables and rulesets/maw. Do not edit.\n"
    text += "window.PC_DATA = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";\n"
    (HERE / "data.js").write_text(text)
    for ruleset in ("standard", "maw"):
        entry = data[ruleset]
        print(ruleset, "classes", len(entry["classes"]), "races", len(entry["races"]), "portraits",
              len(entry["portraits"]), "combos", len(entry["combos"]))
    print("voices", len(data["voices"]), "bytes", len(text))


if __name__ == "__main__":
    main()
