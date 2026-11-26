#!/usr/bin/env python3
"""Build the MM6 (Enroth), MM7 (Antagarich) and MM8 (Jadame) guide websites from the merged engine tables and the
MM6-MM8 world packages, as OpenYAMM plays them under the Standard (MMMerge) ruleset.

    python3 tools/mm678_site/build_site.py [--world mm6|mm7|mm8|all] [--skip-images]

Each book is written to output/<world>_site in the MM9 guide's format: the same web front end (tools/mm9_site/web),
the same `window.GUIDE` data shape and the MM9 generator's shared parts (monsters, story and FAQ loaders, quest levels,
screenshots, portraits, the item icon atlas). Outdoor maps use their journal map (icons_x2/<stem>); indoor maps get
floor plans drawn from their BLV geometry by tools/maw_site/dungeon_plans.py, one per storey where storeys lie over one
another (the Xeen guide's split). See tools/mm678_site/README.md.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
# Hand-written walkthroughs and FAQ, one folder per book: story/<world>/*.yml (main story, side quests and promotions
# in the MM9 guide's story format, read in file-name order) and faq/<world>/faq.yml; pictures in their img/ folders.
STORY = HERE / "story"
FAQ = HERE / "faq"
ENGINE = ROOT / "assets_dev/engine"
TABLES = ENGINE / "data_tables"
WORLDS = ROOT / "assets_dev/worlds"
CONFIG = HERE / "site_config.yml"
MM9_WEB = ROOT / "tools/mm9_site/web"
MAW_PLANS = ROOT / "output/maw_site/work/plans"  # the MAW guide's single-storey plans, reused as a cache


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# The MM9 generator is the shared module; the Xeen generator brings the storey split of indoor plans and the point
# placement on them (both scripts are called build_site.py, so they are loaded by path).
mm9 = load_module("mm9_site_build", ROOT / "tools/mm9_site/build_site.py")
xeen = load_module("xeen_site_build", ROOT / "tools/xeen_site/build_site.py")

sys.path.insert(0, str(ROOT / "tools/maw_site"))
sys.path.insert(0, str(ROOT / "tools"))
import dungeon_plans  # noqa: E402
import maw_tables  # noqa: E402
import teachers as maw_teachers  # noqa: E402
import trainer_places  # noqa: E402
import world_maps  # noqa: E402

# Loading the Xeen generator pointed both modules at the Xeen world; this guide reads MM6-MM8.
dungeon_plans.WORLD_IDS = ("mm6", "mm7", "mm8")
trainer_places.WORLD_IDS = ("mm6", "mm7", "mm8")

to_int, pretty_name = mm9.to_int, mm9.pretty_name
read_rows = maw_tables.read_rows  # the engine's tab-separated parser (quoted cells may span lines)

CONTINENT = {"mm6": "Enroth", "mm7": "Antagarich", "mm8": "Jadame"}
OUTDOOR_HALF = 32768
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SCHOOLS = mm9.SCHOOLS
SPELLS_PER_SCHOOL = 11
STANDARD_LEVEL = maw_teachers.STANDARD_LEVEL
MASTERY_SLOT = maw_teachers.MASTERY_INDEX

# house_data.txt type -> (marker type, what the house is, shop or service type for the tables)
HAND_POINTS = HERE / "extra_pois.yml"

HOUSE_TYPES = {
    "Weapon Shop": ("vendor", "Weapon shop", "Weapon"), "Armor Shop": ("vendor", "Armour shop", "Armor"),
    "Magic Shop": ("vendor", "Magic shop", "Magic"), "Alchemist": ("vendor", "Alchemist", "Alchemist"),
    "General Store": ("vendor", "General store", "General"), "Spell Shop": ("guild", "Spell shop", "Spell shop"),
    "Temple": ("service", "Temple", "Temple"), "Tavern": ("service", "Tavern", "Tavern"),
    "Bank": ("service", "Bank", "Bank"), "Training": ("service", "Training hall", "Training hall"),
    "Town Hall": ("service", "Town hall", "Town hall"), "Circus": ("service", "Circus", "Circus"),
    "The Adventurer's Inn": ("service", "Adventurer's Inn", "Adventurer's Inn"),
    "Boats": ("transport", "Boats", "Boats"), "Stables": ("transport", "Stables", "Stables"),
    "Throne": ("house", "Throne room", ""), "Castle Entrance": ("exit", "Castle", ""),
    "Dungeon Ent": ("exit", "Entrance", ""), "Seer": ("house", "Seer", ""), "Jail": ("house", "Jail", ""),
    "House": ("house", "Home", ""),
}
GUILD_SCHOOLS = {
    "Fire Guild": [0], "Air Guild": [1], "Water Guild": [2], "Earth Guild": [3], "Spirit Guild": [4],
    "Mind Guild": [5], "Body Guild": [6], "Light Guild": [7], "Dark Guild": [8], "Elemental Guild": [0, 1, 2, 3],
    "Self Guild": [4, 5, 6], "Spell Shop": list(range(9)),
}
# HouseTable.cpp deriveOfferedSkillsForHouseType: the skills a house teaches (Learn) when its row names none.
HOUSE_LEARN = {
    "Magic Shop": ["IdentifyItem", "RepairItem"], "Alchemist": ["Alchemy", "IdentifyMonster"],
    "Elemental Guild": ["FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "Learning"],
    "Spell Shop": ["FireMagic", "AirMagic", "WaterMagic", "EarthMagic", "Learning"],
    "Fire Guild": ["FireMagic", "Learning"], "Air Guild": ["AirMagic", "Learning"],
    "Water Guild": ["WaterMagic", "Learning"], "Earth Guild": ["EarthMagic", "Learning"],
    "Self Guild": ["SpiritMagic", "MindMagic", "BodyMagic", "Meditation"],
    "Spirit Guild": ["SpiritMagic", "Meditation"], "Mind Guild": ["MindMagic", "Meditation"],
    "Body Guild": ["BodyMagic", "Meditation"],
    "Thieves guild": ["Dagger", "Merchant", "IdentifyItem", "Perception", "DisarmTraps"],
    "Merc Guild": ["Unarmed", "Dodging", "Armsmaster", "DisarmTraps"], "Light Guild": ["LightMagic"],
    "Dark Guild": ["DarkMagic"], "Temple": ["Unarmed", "Dodging", "Regeneration", "Merchant"],
    "Tavern": ["Stealing", "DisarmTraps", "Perception"], "Training": ["Armsmaster", "Bodybuilding"],
}
# HouseTable.cpp skillForStockItemType: weapon and armour shops teach the skills of the item types they stock.
STOCK_SKILLS = {23: "Sword", 24: "Dagger", 25: "Axe", 26: "Spear", 27: "Bow", 28: "Mace", 30: "Staff",
                31: "LeatherArmor", 32: "ChainArmor", 33: "PlateArmor", 34: "Shield"}
STOCK_SECTIONS = {"Weapon Shop": "Weapon shops", "Armor Shop": "Armor shops", "Magic Shop": "Magic shops",
                  "Alchemist": "Alchem shops"}

# Map script events: one entry per RegisterEvent (and the MMMerge overlays' Replace/Append of the same id).
EVENT_START = re.compile(r'^(RegisterEvent|ReplaceMapEvent|AppendMapEvent|RegisterNoOpEvent)\((\d+),\s*'
                         r'(?:"((?:[^"\\]|\\.)*)"|nil|function)', re.M)
GLOBAL_START = re.compile(r'^[ \t]*(RegisterGlobalEvent|ReplaceGlobalEvent|AppendGlobalEvent)\((\d+)', re.M)
TOP_LINE = re.compile(r"^(?!end\b)[A-Za-z_]", re.M)
ACTION_LINE = trainer_places.ACTION_LINE
LEARNED_LINE = re.compile(r'^\s*\[(\d+)\] = \{ autonote = \d+, effect = "((?:[^"\\]|\\.)*)" \},?$', re.M)
MOVE_RE = re.compile(r'evt\.MoveToMap\(([^)"]*?)(?:"([^"]+\.(?:blv|odm))")?\)', re.I)
TEXT_RE = re.compile(r'evt\.(?:StatusText|SimpleMessage|SetMessage)\("((?:[^"\\]|\\.)*)"')
AUTONOTE_RE = re.compile(r"SetAutonote\(\d+\)\s*--\s*(.+)$", re.M)
QSET_RE = re.compile(r"\bSetQBit\(QBit\((\d+)\)\)")
QCLEAR_RE = re.compile(r"\bClearQBit\(QBit\((\d+)\)\)")
QCHECK_RE = re.compile(r"\bIsQBitSet\(QBit\((\d+)\)\)")
GIVE_RE = re.compile(r"AddValue\(InventoryItem\((\d+)\)")
NEED_RE = re.compile(r"\b(?:HasItem|RemoveItem)\((\d+)\)")
TOPIC_RE = re.compile(r"evt\.SetNPCTopic\((\d+),\s*(\d+),\s*(\d+)\)")
SPEAK_RE = re.compile(r"evt\.SpeakNPC\((\d+)\)")
MOVE_NPC_RE = re.compile(r"evt\.MoveNPC\((\d+),\s*(\d+)\)")
XP_RE = re.compile(r"AddValue\(Experience,\s*(\d+)\)")
GOLD_RE = re.compile(r"AddValue\(Gold,\s*(\d+)\)")
DULL_TEXT = re.compile(r"^(?:Refreshing!?|You pray at the shrine\.?|Nothing (?:here|happens)\.?|Empty|"
                       r"The door is locked\.?|Locked\.?|It won't budge!?|Tree|You pick an apple\.|"
                       r"(?:There are no items|You (?:see|found) nothing) "
                       r"(?:that interest you|of interest|useful)\.?)$", re.I)
SIGN_NAME = re.compile(r"sign|plaque|notice|grave|tomb|inscription|plinth|monument|statue|marker|scroll|book|"
                       r"lectern|letter|note|tablet|stone|altar", re.I)
DEV_WORDING_RE = xeen.DEV_WORDING_RE
# teachers.py's display names carry MAW's renames (Learning shows as Ascension under MAW); Standard keeps the base.
MAW_SKILL_NAMES = maw_tables.ruleset().get("skillNames") or {}


def skill_name(canonical: str) -> str:
    return canonical if canonical in MAW_SKILL_NAMES else maw_teachers.skill_name(canonical)


def unescape(text: str) -> str:
    return text.replace('\\"', '"').replace("\\n", " ").replace("\\\\", "\\").strip()


def numbered(name: str) -> list[list[str]]:
    return [[c.strip() for c in row] for row in read_rows(TABLES / name) if row and row[0].strip().isdigit()]


def clean_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.replace("�", "'")).strip()
    return text[:1].upper() + text[1:] if text else text


# ---------------------------------------------------------------------------------------------------------------------
# Script readers


def split_blocks(source: str, start_re: re.Pattern) -> list[tuple[re.Match, str]]:
    """Each match of start_re with its body: up to the next top-level statement."""
    tops = [m.start() for m in TOP_LINE.finditer(source)] + [len(source)]
    blocks = []
    for match in start_re.finditer(source):
        end = next(t for t in tops if t > match.end())
        blocks.append((match, source[match.start():end]))
    return blocks


def body_facts(body: str) -> dict:
    return {
        "set": {int(b) for b in QSET_RE.findall(body)},
        "clear": {int(b) for b in QCLEAR_RE.findall(body)},
        "check": {int(b) for b in QCHECK_RE.findall(body)},
        "gives": {int(i) for i in GIVE_RE.findall(body)},
        "needs": {int(i) for i in NEED_RE.findall(body)},
        "xp": [int(x) for x in XP_RE.findall(body)],
        "gold": [int(x) for x in GOLD_RE.findall(body)],
    }


def map_scripts(world: str, stem: str) -> list[Path]:
    """The map's base script, then its overlays (MMMerge supplements and numbered variants)."""
    return sorted(world_maps.script_paths(world, stem), key=lambda p: (p.stem != stem, p.stem))


def parse_map_events(world: str, stem: str) -> dict[int, dict]:
    events: dict[int, dict] = {}

    def entry(event_id: int) -> dict:
        return events.setdefault(event_id, {"id": event_id, "name": "", "kind": "", "target": "", "effect": "",
                                            "body": "", "houses": [], "moves": [], "chests": [], "texts": [],
                                            "notes": [], "speak": [], "move_npc": []})

    for path in map_scripts(world, stem):
        source = path.read_text(encoding="utf-8", errors="replace")
        for match in ACTION_LINE.finditer(source):
            data = entry(int(match.group(1)))
            data["kind"] = data["kind"] or match.group(2)
            target = re.search(r'targetMap = "([^"]+)"', match.group(3))
            if target and not data["target"]:
                data["target"] = target.group(1).lower()
        for match in LEARNED_LINE.finditer(source):
            entry(int(match.group(1)))["effect"] = unescape(match.group(2))
        for match, body in split_blocks(source, EVENT_START):
            data = entry(int(match.group(2)))
            name = unescape(match.group(3) or "")
            if match.group(1) == "ReplaceMapEvent":
                data["body"] = body + "\n-- replaced:\n" + data["body"]  # the analysis keeps both (quest bits)
                data["name"] = name or data["name"]
            else:
                data["body"] += body
                data["name"] = data["name"] or name
    for data in events.values():
        body = data["body"]
        data["houses"] = list(dict.fromkeys(int(h) for h in re.findall(r"evt\.EnterHouse\((\d+)\)", body)))
        for move in MOVE_RE.finditer(body):
            args = [a.strip() for a in move.group(1).split(",") if a.strip()]
            data["moves"].append({"map": (move.group(2) or "").lower(), "args": args})
        data["chests"] = list(dict.fromkeys(int(c) for c in re.findall(r"evt\.OpenChest\((\d+)\)", body)))
        data["texts"] = [clean_sentence(unescape(t)) for t in TEXT_RE.findall(body)]
        data["notes"] = [n.strip() for n in AUTONOTE_RE.findall(body)]
        data["speak"] = [int(n) for n in SPEAK_RE.findall(body)]
        data["move_npc"] = [(int(n), int(h)) for n, h in MOVE_NPC_RE.findall(body)]
        data.update(body_facts(body))
    return events


def global_sources() -> list[Path]:
    """Engine Global.lua and its supplements, then the three worlds' global overlays (MMMerge, MM8 promotions)."""
    paths = [ENGINE / "events/Global.lua"] + sorted(p for p in (ENGINE / "events").glob("Global_*.lua"))
    for other in ("mm6", "mm7", "mm8"):
        paths += sorted((WORLDS / other / "events").glob("Global*.lua"))
    return paths


def parse_global_events() -> dict[int, dict]:
    """Every NPC topic event (engine Global.lua and the worlds' overlays): its body facts, by topic id."""
    events: dict[int, dict] = {}
    topic_changes: list[tuple[int, int, int]] = []
    for path in global_sources():
        source = path.read_text(encoding="utf-8", errors="replace")
        topic_changes += [(int(n), int(s), int(t)) for n, s, t in TOPIC_RE.findall(source)]
        for match, body in split_blocks(source, GLOBAL_START):
            data = events.setdefault(int(match.group(2)), {"body": ""})
            data["body"] += "\n" + body
    for data in events.values():
        data.update(body_facts(data["body"]))
        data["topics"] = [(int(n), int(s), int(t)) for n, s, t in TOPIC_RE.findall(data["body"])]
        data["promotes"] = "SetValue(ClassId" in data["body"]
    return events, topic_changes


# ---------------------------------------------------------------------------------------------------------------------
# Tables


def load_npcs() -> dict[int, dict]:
    """npc.txt: name, title, house (2D Location) and topic slots (columns 10-15, as NpcDialogTable reads them)."""
    npcs = {}
    for row in numbered("npc.txt"):
        row = row + [""] * (18 - len(row))
        if not row[1] or row[1] in ("Boob", "0"):
            continue
        npcs[int(row[0])] = {"id": int(row[0]), "name": row[1].replace("_", " "), "house": to_int(row[6]),
                             "topics": [to_int(c) for c in row[10:16] if to_int(c)],
                             "title": row[17] if row[17] not in ("0", "") else ""}
    return npcs


def load_houses() -> dict[int, dict]:
    houses = {}
    for row in numbered("house_data.txt"):
        row = row + [""] * (26 - len(row))
        try:
            val = float(row[12]) if row[12] else 0.0
        except ValueError:
            val = 0.0
        houses[int(row[0])] = {"id": int(row[0]), "index": to_int(row[1]), "type": row[2], "map": to_int(row[3]),
                               "name": row[5], "owner": row[6], "title": row[7], "val": val,
                               "train_max": to_int(row[17]), "open": to_int(row[18]), "close": to_int(row[19]),
                               "skills": row[24]}
    return houses


def load_house_rules() -> dict[str, dict[int, list[int]]]:
    sections: dict[str, dict[int, list[int]]] = {}
    current = None
    for row in read_rows(TABLES / "house_rules.txt")[1:]:
        if not row or not row[0].strip():
            continue
        if not row[0].strip().isdigit():
            current = row[0].strip()
            sections[current] = {}
            continue
        if current is not None:
            sections[current][int(row[0])] = [to_int(c, -1) if c.strip() else -1 for c in row]
    return sections


def rule_row(rules: dict, section: str, house: dict) -> list[int] | None:
    """HouseTable.cpp houseRuleId: the house's type index, else its map id."""
    rule_id = house["index"] or house["map"]
    return (rules.get(section) or {}).get(rule_id)


def load_transport() -> tuple[dict[int, list[int]], dict[int, dict]]:
    index = {}
    for row in read_rows(TABLES / "transport_index.txt")[1:]:
        if row and row[0].strip().isdigit():
            index[int(row[0])] = [to_int(c, -1) for c in row[1:] if c.strip()]
    locations = {}
    for row in read_rows(TABLES / "transport_locations.txt")[1:]:
        if row and row[0].strip().isdigit():
            row = row + [""] * (16 - len(row))
            locations[int(row[0])] = {"map": row[1].strip().lower(), "days": [DAYS[i] for i in range(7)
                                                                              if row[2 + i].strip().lower() == "x"],
                                      "travel": to_int(row[9]), "qbit": to_int(row[14]), "name": row[15].strip()}
    return index, locations


def load_monster_table() -> tuple[dict[int, dict], dict[str, int]]:
    """monster_data.txt rows with family and tier from the picture ("Lizardmen Warrior A"), and the descriptor ids by
    internal name ("BGoblin A") that map_stats' encounter slots name."""
    monsters = mm9.load_monsters(ENGINE, "")
    for row in read_rows(TABLES / "monster_data.txt"):
        if len(row) > 3 and row[0].strip().isdigit() and int(row[0]) in monsters:
            match = re.match(r"(.*\S)\s+([ABC])$", row[2].strip())
            monster = monsters[int(row[0])]
            monster["family"], monster["tier"] = (match.group(1), match.group(2)) if match else ("", "")
            monster["picture"] = row[2].strip()
            monster["name"] = monster["name"].replace("_", " ")
    descriptors = {}
    for row in read_rows(TABLES / "monster_descriptors.txt"):
        if len(row) > 1 and row[0].strip().isdigit():
            descriptors.setdefault(row[1].strip().lower(), int(row[0]))
    # A family is named after its first tier (the picture names are internal: "BGoblin", "PeasantF2").
    first = {}
    for monster in sorted(monsters.values(), key=lambda m: (m["tier"] or "Z", m["id"])):
        if monster["family"]:
            first.setdefault(monster["family"], monster["name"])
    for monster in monsters.values():
        monster["family_key"] = monster["family"]
        if monster["family"]:
            monster["family"] = first[monster["family"]]
    return monsters, descriptors


def item_table() -> dict[int, dict]:
    items = {}
    for row in read_rows(TABLES / "items.txt"):
        if len(row) > 8 and row[0].strip().isdigit():
            row = row + [""] * (21 - len(row))
            items[int(row[0])] = {"id": int(row[0]), "pic": row[1], "name": row[2], "value": to_int(row[3]),
                                  "equip": row[4], "skill": row[5], "mod1": row[6], "mod2": row[7],
                                  "material": row[8], "desc": row[16], "flags": row[20]}
    return items


def load_quest_notes() -> dict[int, dict]:
    notes = {}
    for row in read_rows(TABLES / "english/quests.txt")[1:]:
        if row and row[0].strip().isdigit():
            row = row + [""] * (7 - len(row))
            notes[int(row[0])] = {"bit": int(row[0]), "text": clean_sentence(row[1]), "notes": row[2].strip(),
                                  "owner": row[3].strip()}
    return notes


# ---------------------------------------------------------------------------------------------------------------------
# Map images


def plan_storeys(file_name: str, stem: str, work: Path, skip_images: bool) -> list[tuple[Path, list[float], tuple]]:
    """An indoor map's floor plans: one per storey where storeys lie over one another (the Xeen guide's split), else
    one plan (the MAW guide's, reused when it already drew it). (png, bounds [min_x, max_x, min_y, max_y], z band)."""
    meta = work / f"{stem}.json"
    if skip_images and meta.exists():
        cached = json.loads(meta.read_text())
        if all((work / f["png"]).exists() for f in cached):
            return [(work / f["png"], f["bounds"], tuple(f["band"]) if f["band"] else None) for f in cached]
    bands = xeen.storey_bands(file_name) or [None]
    floors = []
    for index, band in enumerate(bands):
        png = work / (f"{stem}.png" if band is None else f"{stem}_{index}.png")
        plan = None
        if band is None and (MAW_PLANS / f"{stem}.json").exists() and (MAW_PLANS / f"{stem}.png").exists():
            plan = json.loads((MAW_PLANS / f"{stem}.json").read_text())
            shutil.copy2(MAW_PLANS / f"{stem}.png", png)
        if plan is None:
            plan = xeen.render_storey(file_name, band, png)
        if plan is None:
            continue
        min_x, min_y, max_x, max_y = plan["bounds"]
        floors.append((png, [min_x, max_x, min_y, max_y], band))
    meta.write_text(json.dumps([{"png": p.name, "bounds": b, "band": list(band) if band else None}
                                for p, b, band in floors]))
    return floors


def load_presentation(record: dict, out: Path, work: Path, skip_images: bool) -> dict | None:
    stem = record["id"]
    folder = out / "img/maps"
    folder.mkdir(parents=True, exist_ok=True)
    floors = []
    if record["kind"] == "outdoor":
        source = world_maps.outdoor_image(record)
        if source is None:
            return None
        floors.append((source, [-OUTDOOR_HALF, OUTDOOR_HALF, -OUTDOOR_HALF, OUTDOOR_HALF], None))
    else:
        floors = plan_storeys(record["file"], stem, work, skip_images)
    if not floors:
        return None
    # The map's bounds cover every storey (each floor carries its own bounds for its image).
    presentation = {"bounds": [min(f[1][0] for f in floors), max(f[1][1] for f in floors),
                               min(f[1][2] for f in floors), max(f[1][3] for f in floors)],
                    "flipU": False, "flipV": True, "floors": []}
    biggest = None
    for index, (source, bounds, band) in enumerate(floors):
        name = f"{stem}.webp" if len(floors) == 1 else f"{stem}_{index}.webp"
        target = folder / name
        if skip_images and target.exists():
            with Image.open(target) as image:
                size = image.size
        else:
            with Image.open(source) as image:
                image = image.convert("RGB")
                image.thumbnail((1400, 1400))
                image.save(target, "WEBP", quality=84, method=5)
                size = image.size
        floor = {"w": size[0], "h": size[1], "img": f"img/maps/{name}", "bounds": bounds}
        if band is not None:
            floor["minZ"], floor["maxZ"] = band[0], band[1]
        presentation["floors"].append(floor)
        if biggest is None or size[0] * size[1] > biggest[1]:
            biggest = (source, size[0] * size[1])
    thumb = folder / f"{stem}_thumb.webp"
    if not (skip_images and thumb.exists()):
        with Image.open(biggest[0]) as image:
            image = image.convert("RGB")
            image.thumbnail((320, 320))
            image.save(thumb, "WEBP", quality=80)
    presentation["thumb"] = f"img/maps/{stem}_thumb.webp"
    presentation["floorNames"] = ["Map"] if len(floors) == 1 else [f"Level {i + 1}" for i in range(len(floors))]
    return presentation


# ---------------------------------------------------------------------------------------------------------------------
# Shared data (all three books read the same engine tables and NPC topic events)


class Shared:
    def __init__(self):
        self.records = world_maps.load_maps()  # map file -> record (id, file, name, world, kind, num)
        self.by_num = {r["num"]: r for r in self.records.values()}
        self.travels = world_maps.load_travels()
        self.npcs = load_npcs()
        self.houses = load_houses()
        self.rules = load_house_rules()
        self.transport_index, self.transport_locations = load_transport()
        self.monsters, _ = load_monster_table()
        self.by_picture = {m["picture"].lower(): m["id"] for m in self.monsters.values() if m.get("picture")}
        self.items = item_table()
        self.notes = load_quest_notes()
        self.globals, topic_changes = parse_global_events()
        self.teacher_topics = maw_teachers.load_topics()
        self.map_stats = {row[2].lower(): row + [""] * (30 - len(row)) for row in numbered("map_stats.txt")}
        # Every topic an NPC can show: its npc.txt slots, the topics any script sets on it and MMMerge's Enroth
        # grandmaster topics (with the quest bit that holds one back).
        self.topics_of: dict[int, set[int]] = defaultdict(set)
        self.gated_topic: dict[tuple[int, int], int] = {}
        for npc in self.npcs.values():
            self.topics_of[npc["id"]].update(npc["topics"])
        changes = list(topic_changes)
        self.arrivals: dict[str, list[tuple[str, int]]] = defaultdict(list)  # map file -> (source stem, arrival z)
        # Every quest bit some script sets: a journal line no script sets never shows in a Standard game.
        self.set_bits: set[int] = {b for data in self.globals.values() for b in data["set"]}
        self.npc_houses: dict[int, set[int]] = defaultdict(set)  # NPCs a script moves into a house
        for world in ("mm6", "mm7", "mm8"):
            for path in sorted((WORLDS / world / "events/maps").glob("*.lua")):
                source = path.read_text(encoding="utf-8", errors="replace")
                changes += [(int(n), int(s), int(t)) for n, s, t in TOPIC_RE.findall(source)]
                self.set_bits |= {int(b) for b in QSET_RE.findall(source)}
                for move in MOVE_RE.finditer(source):
                    args = [a.strip() for a in move.group(1).split(",") if a.strip()]
                    if move.group(2) and len(args) >= 3 and re.fullmatch(r"-?\d+", args[2]):
                        self.arrivals[move.group(2).lower()].append((path.stem.split("_")[0], int(args[2])))
                for npc_id, house in MOVE_NPC_RE.findall(source):
                    if int(house):
                        self.npc_houses[int(npc_id)].add(int(house))
        for data in self.globals.values():
            for npc_id, house in MOVE_NPC_RE.findall(data["body"]):
                if int(house):
                    self.npc_houses[int(npc_id)].add(int(house))
        for npc_id, _, topic in changes:
            if topic:
                self.topics_of[npc_id].add(topic)
        for entry in maw_teachers.scripted_topics():
            self.topics_of[entry["npc"]].add(entry["topic"])
            if entry["qbit"]:
                self.gated_topic[(entry["npc"], entry["topic"])] = entry["qbit"]
        for npc in self.npcs.values():
            if npc["house"]:
                self.npc_houses[npc["id"]].add(npc["house"])
        self.house_people: dict[int, list[int]] = defaultdict(list)
        for npc_id, houses in sorted(self.npc_houses.items()):
            for house in sorted(houses):
                if npc_id in self.npcs:
                    self.house_people[house].append(npc_id)

    def world_of_house(self, house: dict) -> str:
        record = self.by_num.get(house["map"])
        return record["world"] if record else ""

    def topic_facts(self, npc_id: int) -> dict:
        """What an NPC's topics do: quest bits set, cleared and checked, items needed and given."""
        facts = {"set": set(), "clear": set(), "check": set(), "needs": set(), "gives": set(), "promotes": False}
        for topic in self.topics_of.get(npc_id, ()):
            data = self.globals.get(topic)
            if data is None:
                continue
            for key in ("set", "clear", "check", "needs", "gives"):
                facts[key] |= data[key]
            facts["promotes"] = facts["promotes"] or data["promotes"]
        return facts


def cluster_hits(hits: list[tuple], reach: float = 2048) -> list[list[tuple]]:
    """Hits (x, y[, z]) grouped by nearness: a hit joins the group of any hit within `reach` units; largest first."""
    groups: list[list[tuple]] = []
    for hit in hits:
        near = [g for g in groups if any(abs(hit[0] - h[0]) < reach and abs(hit[1] - h[1]) < reach for h in g)]
        merged = [hit] + [h for g in near for h in g]
        groups = [g for g in groups if g not in near] + [merged]
    return sorted(groups, key=len, reverse=True)


def overlay_event_points(world: str, stem: str, file_name: str, outdoor: bool,
                         scene: dict) -> dict[int, list[tuple[float, float, float]]]:
    """Event positions the map's scene overlays add (`<stem>_<name>.scene.yml`: MMMerge's dimensional travel
    pedestals, the courtyard water of Castle Harmondale): outdoor overlays place entities, indoor scenes and their
    overlays give faces an event (`face_attribute_overrides` with `cog_triggered`)."""
    result: dict[int, list[tuple[float, float, float]]] = defaultdict(list)
    scenes = [scene] + [yaml.load(p.read_text(), Loader=yaml.CSafeLoader)
                        for p in sorted((WORLDS / world / "maps").glob(f"{stem}_*.scene.yml"))]
    payload = None if outdoor else dungeon_plans.load(file_name)
    for data in scenes:
        for entity in ((data or {}).get("authored_content") or {}).get("entities") or []:
            position = entity.get("position") or {}
            for key in ("event_id_primary", "event_id_secondary"):
                if entity.get(key) and "x" in position:
                    result[entity[key]].append((position["x"], position["y"], position.get("z", 0)))
        if payload is None:
            continue
        for face in ((data or {}).get("initial_state") or {}).get("face_attribute_overrides") or []:
            event = face.get("cog_triggered") or 0
            if event and face.get("face_index", -1) < len(payload["faces"]):
                points = dungeon_plans.face_points(payload, payload["faces"][face["face_index"]])
                if points:
                    result[event].append(tuple(sum(p[i] for p in points) / len(points) for i in range(3)))
    return result


def chest_contents(scene: dict) -> dict[int, dict]:
    """A map's chests (the scene's initial chests): fixed items and random items by treasure level. Each 36-byte slot
    starts with the item id; a negative id is a random item of that treasure level."""
    result = {}
    for chest in (scene.get("initial_state") or {}).get("chests") or []:
        raw = bytes.fromhex(chest.get("raw_items_hex") or "")
        ids = [int.from_bytes(raw[i:i + 4], "little", signed=True) for i in range(0, len(raw) - 3, 36)]
        result[chest["chest_index"]] = {"fixed": [i for i in ids if i > 0], "levels": [-i for i in ids if i < 0]}
    return result


# ---------------------------------------------------------------------------------------------------------------------
# One book


def item_name(shared: Shared, item_id: int) -> str:
    """An item's name, or "" for the table's placeholders ("_potion/reagent", "0")."""
    name = shared.items.get(item_id, {}).get("name", "").strip()
    return "" if not name or name == "0" or name.startswith("_") else name


def item_list(shared: Shared, ids) -> str:
    counted = Counter(i for i in ids if item_name(shared, i))
    return ", ".join((f"{n} × " if n > 1 else "") + item_name(shared, i) for i, n in counted.items())


def bonus_detail(data: dict) -> str:
    """What a well, fountain, shrine or barrel does: the learned-effect line, else its autonote, else its texts."""
    if data["effect"]:
        return clean_sentence(data["effect"]).rstrip(".")
    if data["notes"]:
        return clean_sentence(data["notes"][0]).rstrip(".")
    texts = [t for t in dict.fromkeys(data["texts"]) if not DULL_TEXT.match(t)]
    return "; ".join(t.rstrip(".") for t in texts[:3])


def build_book(world: str, out: Path, skip_images: bool, config: dict, shared: Shared) -> dict:
    book = config["books"][world]
    poi_types = config["poi_types"]
    continent = CONTINENT[world]
    work = ROOT / f"output/{world}_site_work/plans"
    work.mkdir(parents=True, exist_ok=True)
    records = {f: r for f, r in shared.records.items() if r["world"] == world}
    file_of = {r["id"]: f for f, r in records.items()}
    names = {r["id"]: r["name"] for r in records.values()}
    skip_maps = set(book.get("skip_maps") or [])
    npcs = shared.npcs
    items = shared.items

    # Quests of this continent: quests.txt rows owned by it with a journal text.
    quest_bits = {bit: note for bit, note in shared.notes.items()
                  if note["owner"] == continent and note["text"] and note["text"] != "0"
                  and bit not in set(book.get("skip_quests") or [])}
    stage_of = {int(sub): int(main) for main, subs in (book.get("stages_of") or {}).items() for sub in subs}
    never_set = sorted(bit for bit in quest_bits if bit not in shared.set_bits and bit not in stage_of
                       and bit not in (book.get("giver_text") or {}))
    if never_set:
        print(f"{world}: journal lines no script sets, left out: {never_set}", file=sys.stderr)
    for bit in never_set:
        del quest_bits[bit]

    def quest_key(bit: int) -> str | None:
        bit = stage_of.get(bit, bit)
        return f"q{bit}" if bit in quest_bits else None

    # Promotions (tools/maw_site/promotions.yml, Standard ruleset: the MAW-only fields are not read).
    promo_file = yaml.safe_load((ROOT / "tools/maw_site/promotions.yml").read_text())["quests"]
    promo_entries = [p for p in promo_file if p["continent"] == continent]
    promoter_npcs: dict[int, list[dict]] = defaultdict(list)
    for entry in promo_entries:
        promoter_npcs[entry["npc"]].append(entry)
    promo_quest_bits = {p["quest"] for p in promo_entries}

    # NPC roles: teacher, promoter, quest giver.
    def npc_roles(npc_id: int) -> tuple[str, list[str], dict]:
        kind, roles, links = "npc", [], {}
        taught = [shared.teacher_topics[t] for t in sorted(shared.topics_of.get(npc_id, ()))
                  if t in shared.teacher_topics]
        if taught:
            kind = "teacher"
            roles.append("Teaches " + ", ".join(dict.fromkeys(
                f"{skill_name(t['skill'])} {t['mastery']}" for t in taught)))
        if npc_id in promoter_npcs:
            kind = "promoter"
            links["promo"] = promoter_npcs[npc_id][0]["id"]
            roles.append("Promotes " + "; ".join(dict.fromkeys(
                ", ".join(f"{a} to {b}" for a, b in p["promotes"].items()) for p in promoter_npcs[npc_id])))
        facts = shared.topic_facts(npc_id)
        quests_here = sorted({quest_key(b) for b in facts["set"] | facts["clear"] | facts["check"]} - {None},
                             key=lambda k: int(k[1:]))
        if quests_here:
            links["quests"] = quests_here
            if kind == "npc":
                kind = "quest"
        return kind, roles, links

    def npc_label(npc_id: int) -> str:
        npc = npcs.get(npc_id, {})
        return npc.get("name", f"NPC {npc_id}")

    # Items a quest's closing topic asks for, and the helper bits it checks (a rescued person following the party):
    # an item on the floor or in a chest, or an event setting the bit, is a step of that quest.
    item_quests: dict[int, set[str]] = defaultdict(set)
    helper_quests: dict[int, set[str]] = defaultdict(set)
    for data in shared.globals.values():
        for bit in data["clear"] | data["check"]:
            key = quest_key(bit)
            if key:
                for item in data["needs"]:
                    item_quests[item].add(key)
                for helper in data["check"] if bit in data["clear"] else ():
                    if helper not in quest_bits and helper not in stage_of:
                        helper_quests[helper].add(key)
    # A topic that takes several quests' items (the Emerald Island judge): each item goes to the quest whose journal
    # line names it, when one does.
    for item, row in shared.items.items():  # quest items only map scripts take (the Oracle's memory crystals)
        if item not in item_quests and row["equip"] in ("N / A", "Mscroll") and item_name(shared, item):
            item_quests[item] = set()
    for item, keys in list(item_quests.items()):
        words = re.sub(r"\s*\(.*?\)", "", item_name(shared, item)).lower()
        named = {f"q{b}" for b, note in quest_bits.items() if b not in stage_of and len(words) >= 4 and
                 re.search(r"\b" + re.escape(words) + r"\b", note["text"].lower())}
        if named and (len(keys) > 1 or not keys & named):
            item_quests[item] = named
        if not item_quests[item]:
            del item_quests[item]
    hand = (yaml.safe_load(HAND_POINTS.read_text()) or {}).get(world) or {} if HAND_POINTS.exists() else {}

    maps_out = []
    npc_locations: dict[int, list[dict]] = defaultdict(list)
    house_locations: dict[int, list[dict]] = defaultdict(list)
    monster_maps: dict[int, Counter] = defaultdict(Counter)
    exits_between: dict[tuple[str, str], dict] = {}
    entered_from: dict[str, list[str]] = defaultdict(list)
    quest_points: dict[str, list[dict]] = defaultdict(list)  # quest key -> [{map, poi, name}]
    item_points: dict[int, list[tuple[dict, dict]]] = defaultdict(list)  # item -> [(map, poi)] that give or hold it
    setting_points: dict[str, list[dict]] = defaultdict(list)  # quest -> map points whose event sets its bit
    bit_points: dict[int, list[tuple[str, dict]]] = defaultdict(list)  # any bit -> map points whose event sets it
    unplaced_setters: dict[str, list[str]] = defaultdict(list)  # quest -> who starts it by an event with no place
    found_by: Counter = Counter()  # what the generic rules found, for the build's summary
    edge_records = {f: r for f, r in shared.records.items()}

    for file_name, record in sorted(records.items(), key=lambda item: item[1]["num"]):
        stem = record["id"]
        if stem in skip_maps:
            continue
        presentation = load_presentation(record, out, work, skip_images)
        if presentation is None:
            print(f"warning: no image for {file_name}", file=sys.stderr)
            continue
        outdoor = record["kind"] == "outdoor"
        scene_path = WORLDS / world / "maps" / f"{stem}.scene.yml"
        scene = yaml.load(scene_path.read_text(), Loader=yaml.CSafeLoader) if scene_path.exists() else {}
        events = parse_map_events(world, stem)
        if outdoor:
            points = {e: [(x, y, 0.0) for x, y in pts] for e, pts in trainer_places.outdoor_event_points(
                file_name).items()}
        else:
            points = dungeon_plans.indoor_event_points(file_name)
        added = overlay_event_points(world, stem, file_name, outdoor, scene)
        for event_id, spots in added.items():
            if event_id not in points:
                points[event_id] = spots
        found_by["overlay events"] += sum(1 for e in added if e in events and added[e] == points.get(e))
        chests = chest_contents(scene)
        house_moves = {}
        for data in events.values():
            for move in data["moves"]:
                target = shared.records.get(move["map"])
                if target and target["world"] == world and target["id"] != stem:
                    entered_from[target["id"]].append(stem)  # placed or not: a way in for the regions
                if len(move["args"]) > 6 and move["args"][6].isdigit() and int(move["args"][6]) and move["map"]:
                    house_moves[int(move["args"][6])] = move["map"]
        pois: list[dict] = []
        counters: Counter = Counter()
        cur = {"z": None}
        exit_spots: list[tuple[str, int, float, float, dict]] = []

        def add(kind, x, y, label, detail="", poi_id=None, **extra) -> dict:
            counters[kind] += 1
            u, v, floor = xeen.place_point(presentation, x, y, cur["z"])
            poi = {"id": poi_id or f"{kind[:2]}{counters[kind]}", "t": kind, "u": u, "v": v, "f": floor,
                   "n": label}
            if detail and re.sub(r"^the ", "", detail.strip(" .").lower()) != \
                    re.sub(r"^the ", "", label.strip(" .").lower()):
                poi["d"] = detail
            poi.update({k: val for k, val in extra.items() if val})
            pois.append(poi)
            return poi

        def add_exit(x, y, target_file, detail, poi_id) -> dict:
            """An exit, or the exit to the same map already marked within 1,024 units on the same storey."""
            target = shared.records[target_file]
            floor = xeen.place_point(presentation, x, y, cur["z"])[2]
            for t, f, ex, ey, poi in exit_spots:
                if t == target["id"] and f == floor and abs(ex - x) < 1024 and abs(ey - y) < 1024:
                    return poi
            poi = add("exit", x, y, target["name"], detail, poi_id=poi_id, map=target["id"])
            exit_spots.append((target["id"], floor, x, y, poi))
            if target["world"] == world:
                exits_between.setdefault((stem, target["id"]), {"from": stem, "to": target["id"], "days": 0})
                entered_from[target["id"]].append(stem)
            return poi

        def tag_quests(poi: dict, data: dict) -> None:
            """The quests whose bits the event sets, clears or checks."""
            keys = sorted(({quest_key(b) for b in data["set"] | data["clear"] | data["check"]} - {None}) |
                          {k for b in data["set"] for k in helper_quests.get(b, ())}, key=lambda k: int(k[1:]))
            if keys:
                poi["quests"] = sorted(set(poi.get("quests", [])) | set(keys), key=lambda k: int(k[1:]))
            for bit in data["set"]:
                key = quest_key(bit)
                if key:
                    setting_points[key].append({"map": stem, "poi": poi["id"], "name": poi["n"]})
                bit_points[bit].append((stem, poi))
            for item in data["gives"]:
                item_points[item].append((stem, poi))

        def place_person(npc_id: int, x, y, poi_id: str, label: str | None = None, z=None) -> dict:
            kind, roles, links = npc_roles(npc_id)
            npc = npcs[npc_id]
            detail = "; ".join(filter(None, [npc["title"], "; ".join(roles)]))
            poi = add(kind, x, y, label or npc["name"], detail, poi_id=poi_id, people=[npc["name"]],
                      **{k: v for k, v in links.items()})
            npc_locations[npc_id].append({"map": stem, "poi": poi["id"], "name": npc["name"]})
            return poi

        seen_houses: set[int] = set()
        spread: dict[int, list[list[tuple]]] = {}
        for event_id in sorted(events):
            data = events[event_id]
            hits = points.get(event_id)
            if not hits:
                # A timer or arrival event that starts a quest (a messenger who finds the party): who and where.
                speaker = next((npcs[n]["name"] for n in data["speak"] if n in npcs), "")
                for bit in data["set"]:
                    if quest_key(bit):
                        unplaced_setters[quest_key(bit)].append(f"{speaker or 'On arrival'} ({record['name']})")
                continue
            # Faces and entities far apart carrying one event (two doors of one lock, a castle's two gates) are each
            # a point: the first group places the event's point, the others copy it after the classification.
            groups = cluster_hits(hits)
            hits = groups[0]
            if len(groups) > 1:
                spread[event_id] = groups[1:]
            x = sum(p[0] for p in hits) / len(hits)
            y = sum(p[1] for p in hits) / len(hits)
            cur["z"] = None if outdoor else min(p[2] for p in hits)
            name = data["name"]
            # Houses: shops, guilds, services, homes, castles and dungeon entrances; the people inside decide a
            # home's marker.
            made = None
            for house_id in data["houses"]:
                house = shared.houses.get(house_id)
                if house is None or house_id in seen_houses:
                    continue
                seen_houses.add(house_id)
                kind, label, _ = HOUSE_TYPES.get(house["type"], ("house", "", ""))
                if "guild" in house["type"].lower():
                    kind, label = "guild", house["type"].replace("guild", "Guild")
                people = [n for n in shared.house_people.get(house_id, []) if n in npcs]
                people = [n for i, n in enumerate(people) if npcs[n]["name"] not in
                          {npcs[m]["name"] for m in people[:i]}]  # one person listed twice (two npc.txt rows)
                if kind == "exit":
                    target = house_moves.get(house_id) or next((m["map"] for m in data["moves"]
                                                                if m["map"] and m["map"] != file_name), "")
                    if target in shared.records:
                        poi = add_exit(x, y, target, house["name"] if house["name"] != shared.records[target]["name"]
                                       else "", f"h{house_id}")
                        house_locations[house_id].append({"map": stem, "poi": poi["id"], "name": poi["n"]})
                        tag_quests(poi, data)
                        made = poi
                        continue
                    kind = "house"
                lines = [label] if label else []
                links: dict = {"house": house_id}
                quests_here: set[str] = set()
                for npc_id in people:
                    pkind, roles, plinks = npc_roles(npc_id)
                    npc = npcs[npc_id]
                    who = npc["name"] + (f", {npc['title']}" if npc["title"] else "")
                    lines.append(who + (": " + "; ".join(roles) if roles else ""))
                    quests_here |= set(plinks.get("quests", []))
                    if pkind == "promoter":
                        kind, links["promo"] = "promoter", plinks["promo"]
                    elif pkind == "teacher" and kind == "house":
                        kind = "teacher"
                    elif pkind == "quest" and kind == "house":
                        kind = "quest"
                display = house["name"] if house["name"] not in ("", "House", "0") else ""
                if house["type"] == "Throne" and people:  # a throne room is shown by who sits in it
                    display = ""
                if not display:
                    display = (" and ".join(npcs[n]["name"] for n in people[:2]) + (" and others" if len(people) > 2
                                                                                    else "")) or "Home"
                if house["type"] == "Training":
                    row = rule_row(shared.rules, "Training halls", house)
                    cap = row[1] if row and len(row) > 1 and row[1] > 0 else house["train_max"]
                    if cap:
                        lines.append(f"Trains to level {cap}")
                links["people"] = [npcs[n]["name"] for n in people]
                poi = add(kind, x, y, display, "; ".join(lines), poi_id=f"h{house_id}",
                          quests=sorted(quests_here, key=lambda k: int(k[1:])),
                          **{k: v for k, v in links.items() if v})
                house_locations[house_id].append({"map": stem, "poi": poi["id"], "name": poi["n"]})
                for npc_id in people:
                    npc_locations[npc_id].append({"map": stem, "poi": poi["id"], "name": npcs[npc_id]["name"]})
                tag_quests(poi, data)
                made = poi
            if made is not None:
                continue
            # Ways to other maps, and teleporters within the map.
            other = [m for m in data["moves"] if m["map"] and m["map"] != file_name and m["map"] in shared.records]
            same = [m for m in data["moves"] if not m["map"] or m["map"] == file_name]
            spoken = [n for n in data["speak"] if n in npcs]
            if re.search(r"dimension", name, re.I):  # MMMerge's travel between the continents
                found_by["dimensional travel"] += 1
                poi = add("transport", x, y, "Dimensional travel pedestal" if outdoor else "Dimensional travel",
                          "Travel to the dimensional travel pedestals of the other continents", poi_id=f"e{event_id}")
                continue
            if other:
                target = other[0]["map"]
                label = shared.records[target]["name"]
                poi = add_exit(x, y, target, name if name and name.lower() != label.lower() else "",
                               f"e{event_id}")
                tag_quests(poi, data)
                # A person who speaks at the door (Archibald at Clanker's Laboratory) is met here.
                for npc_id in spoken:
                    if not any(loc["map"] == stem for loc in npc_locations.get(npc_id, [])):
                        poi["people"] = poi.get("people", []) + [npcs[npc_id]["name"]]
                        npc_locations[npc_id].append({"map": stem, "poi": poi["id"], "name": poi["n"]})
                continue
            # A person spoken to through a map object (a cage, a bed, a statue).
            if spoken and not any(loc["map"] == stem for loc in npc_locations.get(spoken[0], [])):
                label = name if name and name.lower() not in npcs[spoken[0]]["name"].lower() else None
                poi = place_person(spoken[0], x, y, f"e{event_id}", label)
                tag_quests(poi, data)
                continue
            if same and data["kind"] not in ("well", "fountain", "shrine"):
                poi = add("teleporter", x, y, name if name and len(name) >= 3 else "Teleporter", "",
                          poi_id=f"e{event_id}")
                tag_quests(poi, data)
                continue
            kind = data["kind"]
            if kind in ("well", "fountain", "shrine", "boost") or (name and re.search(
                    r"\b(?:well|fountain|shrine|altar|barrel|cauldron|pool|keg)\b", name, re.I) and bonus_detail(data)):
                label = name or kind.capitalize()
                poi = add("bonus", x, y, label, bonus_detail(data), poi_id=f"e{event_id}")
                tag_quests(poi, data)
                continue
            if kind == "obelisk" or (name and "obelisk" in name.lower()):
                poi = add("hint", x, y, name or "Obelisk", "Touching it shows a fragment of a message and notes it in "
                          "the autonotes; all the obelisks' fragments together reveal a secret", poi_id=f"e{event_id}")
                continue
            if data["chests"]:
                fixed, levels = [], []
                for chest_index in data["chests"]:
                    contents = chests.get(chest_index, {"fixed": [], "levels": []})
                    fixed += contents["fixed"]
                    levels += contents["levels"]
                level = max(levels) if levels else 0
                label = (name if name and name.lower() not in ("chest", "") else "Chest") + \
                    (f" L{level}" if level else "")
                wanted = [i for i in dict.fromkeys(fixed) if item_quests.get(i) and item_name(shared, i)]
                if wanted:  # a chest holding a quest's item is named after it, so a walkthrough can point at it
                    label += f" ({item_list(shared, wanted)})"
                    found_by["chests named after a quest item"] += 1
                parts = []
                if fixed:
                    parts.append(f"Holds {item_list(shared, fixed)}")
                if levels:
                    parts.append(f"random treasure up to level {level}")
                poi = add("chest", x, y, label, "; ".join(parts), poi_id=f"e{event_id}", lvl=level)
                for item in fixed:
                    item_points[item].append((stem, poi))
                tag_quests(poi, data)
                continue
            quest_related = bool({quest_key(b) for b in data["set"] | data["clear"] | data["check"]} - {None}) or \
                any(helper_quests.get(b) for b in data["set"])
            texts = [t for t in dict.fromkeys(data["texts"]) if not DULL_TEXT.match(t)]
            if kind in ("use_lever", "use_switch", "press_button", "use_pedestal", "use_elevator") or \
                    (name and re.search(r"lever|switch|button|wheel|crank|pedestal", name, re.I)):
                poi = add("lever", x, y, name or pretty_name(kind.replace("use_", "").replace("press_", "")),
                          texts[0][:200] if texts and len(texts[0]) < 200 else "", poi_id=f"e{event_id}")
                tag_quests(poi, data)
                continue
            if quest_related or data["gives"] & set(items) and any(
                    "quest" in (items[i]["desc"] or "").lower() for i in data["gives"] if i in items):
                given = [item_name(shared, i) for i in sorted(data["gives"]) if item_name(shared, i)]
                label = name or (given[0] if given else (texts[0] if texts and len(texts[0]) <= 40 else "Quest spot"))
                needed = [item_name(shared, i) for i in sorted(data["needs"]) if item_name(shared, i)]
                detail = "; ".join(filter(None, [f"Gives {', '.join(given)}" if given else "",
                                                 f"Needs {', '.join(needed)}" if needed else "",
                                                 texts[0][:300] if texts and texts[0] != label else ""]))
                poi = add("objective", x, y, label, detail, poi_id=f"e{event_id}")
                tag_quests(poi, data)
                continue
            keys = [i for i in sorted(data["needs"]) if item_name(shared, i)]
            door = kind == "open_door" or "SetDoorState" in data["body"]
            if keys:
                # A door, altar or tower that asks for an item: a quest's step when a quest wants the item there.
                found_by["events asking for an item"] += 1
                wanted = sorted({k for i in keys for k in item_quests.get(i, ())}, key=lambda k: int(k[1:]))
                label = name if name and len(name) >= 3 else "Locked door" if door else "Quest spot"
                detail = "; ".join(filter(None, [f"Needs {item_list(shared, keys)}", texts[0][:200] if texts else ""]))
                poi = add("objective" if wanted else "door" if door else "lever", x, y, label, detail,
                          poi_id=f"e{event_id}", quests=wanted)
                tag_quests(poi, data)
                continue
            if door and name.lower().rstrip(".") == "door" and texts:
                found_by["doors with a message"] += 1
                add("door", x, y, name.rstrip("."), texts[0][:200], poi_id=f"e{event_id}")
                continue
            if kind == "open_door" or "SetDoorState" in data["body"]:
                # A named thing that opens a way (a strange rock, a torch, a picture) is a mechanism; a named door a
                # door; nameless doors and lettered ones are left out.
                if name and len(name) >= 3 and name.lower().rstrip(".") not in ("door", "the door will not budge"):
                    door = re.search(r"door|gate|cell|portcullis|wall|entry", name, re.I)
                    add("door" if door else "lever", x, y, name, texts[0][:200] if texts else "",
                        poi_id=f"e{event_id}")
                continue
            if texts and (kind == "read" or name and SIGN_NAME.search(name)):
                add("sign", x, y, name or "Sign", texts[0][:400] if texts else "", poi_id=f"e{event_id}")
                continue
            if data["gives"] and name:
                given = [item_name(shared, i) for i in sorted(data["gives"]) if item_name(shared, i)]
                poi = add("chest", x, y, name, f"Gives {', '.join(given)}" if given else "", poi_id=f"e{event_id}")
                tag_quests(poi, data)
                continue
            # Any other clickable thing that says something (a panel, a terminal, a tree with a riddle, a cannon).
            if texts and (name and len(name) >= 3 or kind in ("generic_event", "read", "boost")):
                found_by["events with a message"] += 1
                label = name if name and len(name) >= 3 else texts[0] if len(texts[0]) <= 40 else "Inscription"
                mechanism = re.search(r"panel|terminal|console|cannon|crystal|switch|button|lever|wheel|valve|"
                                      r"control|machine|lift|elevator", label, re.I)
                poi = add("lever" if mechanism else "sign", x, y, label, texts[0][:400] if texts[0] != label else
                          "; ".join(texts[1:2])[:400], poi_id=f"e{event_id}")
                tag_quests(poi, data)

        # Actors: placed people and monsters; outdoor and indoor spawn points by map_stats' encounter slots.
        for actor in (scene.get("initial_state") or {}).get("actors") or []:
            pos = actor["position"]
            cur["z"] = None if outdoor else pos["z"]
            npc_id = actor.get("npc_id") or 0
            if npc_id and npc_id in npcs:
                place_person(npc_id, pos["x"], pos["y"], f"a{actor['actor_index']}")
                continue
            monster = shared.monsters.get(actor.get("monster_info_id"))
            if monster is None or npc_id or re.search(r"peasant", monster.get("picture", ""), re.I):
                continue
            monster_maps[monster["id"]][stem] += 1
            poi = add("monster", pos["x"], pos["y"], monster["name"], f"Level {monster['level']}, {monster['hp']} HP",
                      poi_id=f"a{actor['actor_index']}", mon=monster["id"])
            carried = actor.get("carried_item_id") or 0
            if carried > 0:
                item_points[carried].append((stem, poi))
                poi["d"] += f"; carries {items.get(carried, {}).get('name', 'an item')}"
        # Items lying on the floor (sprite objects carrying an item): a quest's item is its objective, other gear and
        # letters are loot, reagents, potions, ore and gold piles are pickups (hidden by default).
        for index, thing in enumerate((scene.get("initial_state") or {}).get("sprite_objects") or []):
            raw = str(thing.get("raw_containing_item_hex") or "")
            item_id = int.from_bytes(bytes.fromhex(raw[:8]), "little", signed=True) if len(raw) >= 8 else 0
            label = item_name(shared, item_id) if item_id > 0 else ""
            if not label:
                continue
            pos = thing["position"]
            cur["z"] = None if outdoor else pos["z"]
            equip = items[item_id]["equip"]
            consumable = equip in ("Reagent", "Herb", "Bottle", "Ore", "Gem", "Gold", "Sscroll")
            wanted = [] if consumable else sorted(item_quests.get(item_id, ()), key=lambda k: int(k[1:]))
            kind = "objective" if wanted else "pickup" if consumable else "loot"
            found_by[f"items on the floor ({kind})"] += 1
            poi = add(kind, pos["x"], pos["y"], label, "Lies on the floor", poi_id=f"g{index}", quests=wanted)
            item_points[item_id].append((stem, poi))
        stats = shared.map_stats.get(file_name)
        for spawn in scene.get("spawns") or []:
            if spawn.get("type_id") != 3 or stats is None:
                continue
            index = spawn.get("index", 1)
            slot = (index - 1) % 3 if index <= 3 else (index - 4) // 3
            if slot > 2:
                continue
            tier = None if index <= 3 else "ABC"[(index - 4) % 3]
            picture = stats[16 + slot * 4].strip()
            if not picture or picture == "0" or re.search(r"peasant", picture, re.I):
                continue
            chosen = [shared.by_picture[f"{picture} {t}".lower()] for t in (tier or "ABC")
                      if f"{picture} {t}".lower() in shared.by_picture]
            if not chosen:
                continue
            for monster_id in chosen:
                monster_maps[monster_id][stem] += 1
            first = shared.monsters[chosen[0]]
            pos = spawn["position"]
            cur["z"] = None if outdoor else pos["z"]
            group = first["family"] or first["name"]
            add("monster", pos["x"], pos["y"], f"{group} group" + (f" ({tier})" if tier else ""),
                f"Spawn point: {', '.join(dict.fromkeys(shared.monsters[m]['name'] for m in chosen))}; level "
                f"{min(shared.monsters[m]['level'] for m in chosen)}" +
                (f"-{max(shared.monsters[m]['level'] for m in chosen)}" if len(chosen) > 1 else ""),
                poi_id=f"s{spawn['spawn_index']}", mon=first["id"])

        # The four edges of an outdoor map (outdoor_travels.txt).
        if outdoor:
            for edge in world_maps.edge_markers(record, edge_records, shared.travels):
                edge["f"] = 0
                pois.append(edge)
                days = to_int(re.sub(r"\D", "", edge["d"].split(":")[-1])) if ":" in edge["d"] else 0
                exits_between[(stem, edge["map"])] = {"from": stem, "to": edge["map"], "days": days}

        # Levers and doors sharing a name are numbered in reading order (storey, north to south, west to east), so a
        # walkthrough can point at each ("Button 3").
        groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for poi in pois:
            if poi["t"] in ("lever", "door"):
                groups[(poi["t"], poi["n"])].append(poi)
        for group in groups.values():
            if len(group) > 1:
                found_by["numbered levers and doors"] += len(group)
                for number, poi in enumerate(sorted(group, key=lambda p: (p["f"], round(p["v"], 2), p["u"])), 1):
                    poi["n"] = f"{poi['n']} {number}"
        # The hand-kept points (extra_pois.yml): renames of generated points and things no rule finds.
        for poi_id, change in ((hand.get("rename") or {}).get(stem) or {}).items():
            match = [p for p in pois if p["id"] == poi_id]
            if not match:
                raise SystemExit(f"extra_pois.yml: {world} {stem} has no point {poi_id}")
            match[0].update({k: v for k, v in change.items() if k in ("n", "d", "t", "quests")})
        for item in (hand.get("add") or {}).get(stem) or []:
            cur["z"] = None if outdoor else item.get("z")
            add(item["t"], item["x"], item["y"], item["n"], item.get("d", ""), poi_id=item["id"],
                quests=item.get("quests", []))
            found_by["hand-kept points"] += 1
        # Second places of one event take its final name (after the numbering and the hand renames).
        for event_id, others in spread.items():
            original = next((p for p in pois if p["id"] == f"e{event_id}"), None)
            if original is None or original["t"] in ("exit",):
                continue
            for number, group in enumerate(others, 2):
                cur["z"] = None if outdoor else min(p[2] for p in group)
                u, v, floor = xeen.place_point(presentation, sum(p[0] for p in group) / len(group),
                                               sum(p[1] for p in group) / len(group), cur["z"])
                pois.append(dict(original, id=f"e{event_id}-{number}", u=u, v=v, f=floor))
                found_by["second places of one event"] += 1
        for poi in pois:
            if poi["t"] not in poi_types:
                raise SystemExit(f"unknown POI type {poi['t']}")
        kind = "outdoor" if outdoor else ("castle" if re.search(r"\bCastle\b|Palace|Manor|Estate", record["name"])
                                           else "dungeon")
        # Storeys are named from the arrival's (the way in from an outdoor map first): Entry, Up 1, Down 1 ...; the
        # map opens on the arrival's storey.
        ways_in = sorted(shared.arrivals.get(file_name, []), key=lambda a: (
            shared.records.get(a[0] + ".odm") is None, a[0] == stem))
        if len(presentation["floors"]) > 1 and ways_in:
            entry_floor = xeen.place_point(presentation, 0, 0, ways_in[0][1])[2]
            presentation = dict(presentation, defaultFloor=entry_floor, floorNames=[
                "Entry" if i == entry_floor else f"Up {i - entry_floor}" if i > entry_floor else
                f"Down {entry_floor - i}" for i in range(len(presentation["floors"]))])
        maps_out.append({"id": stem, "name": record["name"], "kind": kind, "region": "", **presentation,
                         "pois": pois})
        print(f"{world} {stem}: {len(pois)} points", file=sys.stderr)

    print(f"{world} generic rules: " + ", ".join(f"{k} {v}" for k, v in sorted(found_by.items())), file=sys.stderr)
    return finish_book(world, out, skip_images, config, shared, book, maps_out, quest_bits, stage_of, quest_key,
                       promo_entries, npc_locations, house_locations, monster_maps, exits_between, entered_from,
                       item_points, setting_points, bit_points, unplaced_setters, npc_roles, item_quests)


def money(value: int) -> str:
    return f"{value:,}"


def notes_giver(notes: str) -> str:
    """The quest table's "Given by X in Y." when it reads as player text (no area numbers, bits or NPC ids)."""
    match = re.match(r"\s*Given (?:and taken )?by ([^.;]+?)\s*(?:\.|$)", notes or "")
    if not match:
        return ""
    text = match.group(1).strip()
    if re.search(r"\d|\barea\b|qbit|\bnpc\b|\bw\d|[A-Z]{4,}|\?|along with|event", text, re.I):
        return ""
    return text[:1].upper() + text[1:]


def quest_title(text: str) -> str:
    """A journal line's first sentence without its way back ("... and return to Lord Newton in Mist")."""
    title = text.split(". ")[0].rstrip(".")
    match = re.search(r",? (?:and|then) (?:return|report|come back|bring (?:it|them|him|her) back)\b", title)
    if match and len(title[:match.start()].split()) >= 4:
        title = title[:match.start()]
    return title


def gate_text(book: dict, quests: dict, quest_key, qbit: int) -> str:
    """A route's or a lesson's condition in words: the quest it follows, else site_config.yml's `gate_text`."""
    text = (book.get("gate_text") or {}).get(qbit)
    if text:
        return text
    key = quest_key(qbit)
    return f"after {quests[key]['title']}" if key in quests else "later in the story"


def finish_book(world, out, skip_images, config, shared, book, maps_out, quest_bits, stage_of, quest_key,
                promo_entries, npc_locations, house_locations, monster_maps, exits_between, entered_from, item_points,
                setting_points, bit_points, unplaced_setters, npc_roles, item_quests) -> dict:
    poi_types = config["poi_types"]
    names = {m["id"]: m["name"] for m in maps_out}
    npcs = shared.npcs
    map_ids = set(names)

    # Regions: one per outdoor map (site_config.yml places them); dungeons join the map that leads into them.
    region_of = {}
    for region in book["regions"]:
        for map_id in [region["hub"]] + region.get("maps", []):
            region_of[map_id] = region["id"]
    region_of.update(book.get("region_of") or {})
    for house_id, house in shared.houses.items():  # maps reached only by coach or boat (the arenas)
        if house["type"] in ("Stables", "Boats") and house_locations.get(house_id):
            row = rule_row(shared.rules, house["type"], house)
            for location_id in (row[1:] if row else shared.transport_index.get(house_id, [])):
                location = shared.transport_locations.get(location_id)
                target = shared.records.get(location["map"]) if location else None
                if target and target["id"] in names:
                    entered_from[target["id"]].append(house_locations[house_id][0]["map"])
    changed = True
    while changed:
        changed = False
        for map_data in maps_out:
            if map_data["id"] in region_of:
                continue
            for source in entered_from.get(map_data["id"], []):
                if source in region_of:
                    region_of[map_data["id"]] = region_of[source]
                    changed = True
                    break
    regions = []
    for region in book["regions"]:
        members = [m["id"] for m in maps_out if region_of.get(m["id"]) == region["id"]]
        members.sort(key=lambda m: (m != region["hub"], names[m]))
        if members:
            regions.append({k: v for k, v in region.items() if k != "maps"} | {"maps": members})
    unplaced = [m["id"] for m in maps_out if m["id"] not in region_of]
    if unplaced:
        print(f"{world}: maps without a region: {unplaced}", file=sys.stderr)
        regions.append({"id": "other", "name": "Elsewhere", "hub": unplaced[0], "pos": book.get("other_pos", [5, 3]),
                        "maps": unplaced})
        for m in unplaced:
            region_of[m] = "other"
    for map_data in maps_out:
        map_data["region"] = region_of.get(map_data["id"], "")
    region_name = {r["id"]: r["name"] for r in regions}

    def region_label(map_id: str) -> str:
        return region_name.get(region_of.get(map_id, ""), names.get(map_id, ""))

    # -----------------------------------------------------------------------------------------------------------------
    # Quests

    chapter_of = {}
    for chapter in book.get("chapters") or []:
        for bit in chapter.get("quests", []):
            chapter_of[int(bit)] = chapter["id"]
    promo_bits = {b: p for p in promo_entries for b in [p["quest"]] + list(p.get("also") or [])}
    turn_ins: dict[int, list[dict]] = defaultdict(list)  # bit -> topic events that clear or check it
    for data in shared.globals.values():
        for bit in data["clear"] | data["check"]:
            turn_ins[bit].append(data)
    # NPCs that check many quests, or check quests but never set or close one (seers, heralds), give hints: they do
    # not take part in a quest.
    def checked_quests(npc_id: int) -> int:
        return len({quest_key(b) for b in shared.topic_facts(npc_id)["check"]} - {None})

    quests: dict[str, dict] = {}
    for bit, note in sorted(quest_bits.items()):
        if bit in stage_of:
            continue
        key = f"q{bit}"
        bits = [bit] + sorted(b for b, main in stage_of.items() if main == bit and b in quest_bits)
        stages = [{"qbit": b, "text": quest_bits[b]["text"]} for b in bits]
        cat = "promotion" if bit in promo_bits else "main" if bit in chapter_of else "side"
        quest = {"id": key, "title": book.get("titles", {}).get(bit) or quest_title(note["text"]),
                 "stages": stages, "givers": [], "handoffs": [], "steps": [], "cat": cat}
        if cat == "main":
            quest["chapter"] = chapter_of[bit]
        givers, handoffs = [], []
        for npc_id in sorted(npcs):
            facts = shared.topic_facts(npc_id)
            if not npc_locations.get(npc_id):
                continue
            if set(bits) & facts["set"]:
                givers += [loc for loc in npc_locations[npc_id] if loc not in givers]
            elif set(bits) & facts["clear"] or set(bits) & facts["check"] and checked_quests(npc_id) <= 6 and \
                    {quest_key(b) for b in facts["set"] | facts["clear"]} - {None}:
                handoffs += [loc for loc in npc_locations[npc_id] if loc not in handoffs]
        quest["givers"] = givers
        quest["handoffs"] = [h for h in handoffs if h not in givers]
        if not givers:
            text = (book.get("giver_text") or {}).get(bit) or notes_giver(note["notes"])
            spots = setting_points.get(key, [])
            if not (book.get("giver_text") or {}).get(bit):
                unplaced_npcs = [n["name"] for n in npcs.values() if set(bits) & shared.topic_facts(n["id"])["set"]]
                if spots:
                    text = f"{spots[0]['name']} ({names.get(spots[0]['map'], '')})"
                elif unplaced_setters.get(key):
                    text = unplaced_setters[key][0]
                elif unplaced_npcs:
                    text = unplaced_npcs[0]
            if text:
                quest["giverText"] = text
        # Reward: what the topics that clear the bit hand out.
        xp = max([x for data in turn_ins.get(bit, []) if bit in data["clear"] for x in data["xp"]] or [0])
        gold = max([g for data in turn_ins.get(bit, []) if bit in data["clear"] for g in data["gold"]] or [0])
        reward = "; ".join(filter(None, [f"{money(xp)} XP" if xp else "", f"{money(gold)} gold" if gold else ""]))
        if reward:
            quest["reward"] = reward
        # Quest items: what the turn-in topics ask for; the map points that give or hold them are steps.
        closing = [data for b in bits for data in turn_ins.get(b, []) if b in data["clear"]]
        quest["_items"] = sorted({i for data in closing for i in data["needs"]})
        # Helper bits the turn-in checks (a rescued person following the party, a deed done): the map points that
        # set them are the quest's steps.
        quest["_bits"] = sorted({b for data in closing for b in data["check"]} - set(quest_bits) - set(bits))
        quests[key] = quest
    for map_data in maps_out:
        for poi in map_data["pois"]:
            for key in poi.get("quests", []):
                if key in quests and poi["t"] in ("objective", "chest", "bonus", "exit", "lever", "teleporter", "door",
                                                  "hint", "sign"):
                    step = {"map": map_data["id"], "poi": poi["id"], "name": poi["n"]}
                    if step not in quests[key]["steps"]:
                        quests[key]["steps"].append(step)
    for quest in quests.values():
        found = [p for item in quest.pop("_items") if len(item_points.get(item, [])) <= 4
                 and quest["id"] in item_quests.get(item, {quest["id"]}) for p in item_points.get(item, [])]
        found += [p for bit in quest.pop("_bits") if len(bit_points.get(bit, [])) <= 8 for p in bit_points.get(bit, [])]
        for map_id, poi in found:
            step = {"map": map_id, "poi": poi["id"], "name": poi["n"]}
            if step not in quest["steps"]:
                quest["steps"].append(step)
                if quest["id"] not in poi.get("quests", []):
                    poi["quests"] = poi.get("quests", []) + [quest["id"]]

    # Promotions (tools/maw_site/promotions.yml): the promoter's places, the class lines, the task.
    promotions = []
    for entry in promo_entries:
        at = []
        for loc in npc_locations.get(entry["npc"], []):
            if entry.get("map") and loc["map"] != Path(entry["map"]).stem and any(
                    l["map"] == Path(entry["map"]).stem for l in npc_locations[entry["npc"]]):
                continue
            if loc not in at:
                at.append(loc)
        lines = [[a, b] for a, b in entry["promotes"].items()]
        title = " / ".join(dict.fromkeys(b for _, b in lines))
        key = f"q{entry['quest']}"
        quest = quests.get(key)
        note = entry.get("task") or (quest["stages"][0]["text"] if quest else "")
        keys = [k for k in [key] + [f"q{b}" for b in entry.get("also") or []] if k in quests]
        item = {"key": entry["id"], "to": title, "from": " / ".join(dict.fromkeys(a for a, _ in lines)),
                "classes": lines, "quests": keys, "at": at, "note": clean_sentence(note)}
        if entry.get("path"):
            item["path"] = entry["path"]
        promotions.append(item)
        for other in keys[1:]:
            quests[other].update(promo=title, cat="promotion", **({"path": entry["path"]} if entry.get("path") else {}))
            quests[other].pop("chapter", None)
        if quest:
            quest["promo"] = title
            quest["cat"] = "promotion"
            quest.pop("chapter", None)
            if entry.get("path"):
                quest["path"] = entry["path"]
    for bit, path in (book.get("paths") or {}).items():  # side quests only one of MM7's paths offers
        if f"q{bit}" in quests:
            quests[f"q{bit}"]["path"] = path
    promo_title = {p["key"]: p["to"] for p in promotions}
    for map_data in maps_out:
        for poi in map_data["pois"]:
            if poi.get("promo"):
                poi["promo"] = promo_title.get(poi["promo"], poi["promo"])

    # Exits to another continent's map (MMMerge's links between the worlds): the guide names the map; the other book
    # holds its page (`xmap`, for a front end that links across books).
    for map_data in maps_out:
        for poi in map_data["pois"]:
            if poi.get("map") and poi["map"] not in map_ids:
                target = next((r for r in shared.records.values() if r["id"] == poi["map"]), None)
                poi["xmap"] = {"book": target["world"] if target else "", "map": poi.pop("map")}
                where = f"In {CONTINENT.get(target['world'], 'another world')}" if target else ""
                poi["d"] = "; ".join(filter(None, [poi.get("d", ""), where]))

    monsters = shared.monsters
    story_dir = STORY / world
    story, walkthroughs = mm9.load_story(quests, maps_out, {"poi_types": poi_types}, story_dir,
                                         sorted(p.name for p in story_dir.glob("*.yml"))) \
        if story_dir.is_dir() else ([], {})
    for chapter in story:
        chapter["title"] = next((c["name"] for c in book.get("chapters") or [] if c["id"] == chapter["id"]),
                                chapter["title"])
    mm9.quest_levels(quests, walkthroughs, maps_out, monsters, {"quest_level_maps": {}})

    # -----------------------------------------------------------------------------------------------------------------
    # Teachers

    teachers = []
    for npc_id, npc in sorted(npcs.items()):
        taught = [(t, shared.teacher_topics[t]) for t in sorted(shared.topics_of.get(npc_id, ()))
                  if t in shared.teacher_topics]
        locs = npc_locations.get(npc_id, [])
        if not taught or not locs:
            continue
        for topic_id, topic in taught:
            canonical, mastery = topic["skill"], topic["mastery"]
            slot = MASTERY_SLOT[mastery]
            when = []
            qbit = shared.gated_topic.get((npc_id, topic_id))
            if qbit:
                when.append(maw_teachers.QUEST_NOTES.get(qbit) or gate_text(book, quests, quest_key, qbit))
            extra = maw_teachers.EXTRA_REQUIREMENTS.get((canonical, mastery))
            if extra:
                when.append(f"also {extra}")
            teachers.append({
                "skill": skill_name(canonical), "skills": skill_name(canonical),
                "mastery": mastery, "name": npc["name"] + (f", {npc['title']}" if npc["title"] else ""),
                "region": region_label(locs[0]["map"]),
                "rank": max(STANDARD_LEVEL[slot], topic["required"]),
                "gold": topic["gold"] or maw_teachers.default_price(canonical, slot),
                "gated": bool(qbit), "when": "; ".join(when),
                "at": [{"map": a["map"], "poi": a["poi"]} for a in locs],
            })

    # -----------------------------------------------------------------------------------------------------------------
    # Shops, guilds, services

    vendors, services, spellbooks = [], [], {}
    book_items = {}
    for item in shared.items.values():
        match = re.fullmatch(r"S(\d+)", item["mod1"])
        if item["equip"] == "Book" and match and f"World:{world}" in item["flags"]:
            book_items.setdefault(int(match.group(1)), item)
    for house_id, house in sorted(shared.houses.items()):
        at = [{"map": a["map"], "poi": a["poi"], "name": a["name"]} for a in house_locations.get(house_id, [])]
        if not at:
            continue
        htype = house["type"]
        region = region_label(at[0]["map"])
        learn_skills = [s for s in re.split(r"\s*,\s*", house["skills"]) if s and s != "none" and s != "0"] \
            if house["skills"] and house["skills"] != "0" else list(HOUSE_LEARN.get(htype, []))
        if htype in STOCK_SECTIONS:
            standard = rule_row(shared.rules, f"{STOCK_SECTIONS[htype]} Standart", house)
            special = rule_row(shared.rules, f"{STOCK_SECTIONS[htype]} Special", house)
            treasure = [standard[1] if standard else 0, special[1] if special else 0]
            types = [t for row in (standard, special) if row for t in row[2:] if t > 0]
            if htype in ("Weapon Shop", "Armor Shop") and not learn_skills:
                learn_skills = list(dict.fromkeys(STOCK_SKILLS[t] for t in types if t in STOCK_SKILLS))
            sells = {"Weapon Shop": "weapons", "Armor Shop": "armour, shields, helms, boots, gloves",
                     "Magic Shop": "wands, rings, amulets and magic items",
                     "Alchemist": "potions, reagents and bottles"}[htype]
            stock_skills = [skill_name(STOCK_SKILLS[t]) for t in dict.fromkeys(types) if t in STOCK_SKILLS]
            if stock_skills:
                sells += " (" + ", ".join(dict.fromkeys(stock_skills)) + ")"
            vendors.append({"id": house_id, "name": house["name"], "type": HOUSE_TYPES[htype][2], "region": region,
                            "treasure": treasure, "tiers": [], "enchanted": 0, "price": house["val"], "restock": 0,
                            "pages": 1, "perPage": 0, "sells": sells, "at": at})
        elif htype in GUILD_SCHOOLS:
            row = rule_row(shared.rules, "Spellbook shops", house)
            top = max(0, min(row[1] if row and len(row) > 1 else 0, SPELLS_PER_SCHOOL))
            schools = GUILD_SCHOOLS[htype]
            for school in schools:
                for n in range(1, top + 1):
                    spell = school * SPELLS_PER_SCHOOL + n
                    item = book_items.get(spell)
                    if item is None:
                        continue
                    entry = spellbooks.setdefault(spell, {
                        "spell": spell, "name": item["name"], "school": SCHOOLS[school],
                        "mastery": "Normal" if n <= 4 else "Expert" if n <= 7 else "Master" if n <= 10 else
                        "Grandmaster", "value": item["value"], "shops": []})
                    entry["shops"].append({"id": house_id, "pages": 1, "of": 1})
            sells = (", ".join(f"{SCHOOLS[s]}" for s in schools) + f" Magic spellbooks 1-{top}") if top else ""
            vendors.append({"id": house_id, "name": house["name"], "type": HOUSE_TYPES.get(htype, ("", "", "Guild"))[2]
                            if htype == "Spell Shop" else htype.replace("guild", "Guild"), "region": region,
                            "treasure": [], "tiers": [], "enchanted": 0, "price": house["val"], "restock": 0,
                            "pages": 1, "perPage": 0, "sells": sells, "at": at})
        elif htype in ("Temple", "Tavern", "Bank", "Training", "Town Hall", "Circus", "The Adventurer's Inn",
                       "Stables", "Boats", "Thieves guild", "Merc Guild"):
            train = 0
            if htype == "Training":
                row = rule_row(shared.rules, "Training halls", house)
                train = row[1] if row and len(row) > 1 and row[1] > 0 else house["train_max"]
            services.append({"id": house_id, "name": house["name"],
                             "type": HOUSE_TYPES[htype][2] if htype in HOUSE_TYPES else htype.replace("guild", "Guild"),
                             "region": region, "trainMax": train,
                             "learn": [skill_name(s) for s in learn_skills], "at": at})
        for skill in learn_skills:
            teachers.append({"name": house["name"], "skill": skill_name(skill),
                             "skills": skill_name(skill), "mastery": "Learn", "rank": 0, "gold": 0,
                             "region": region, "gated": False,
                             "venue": HOUSE_TYPES.get(htype, ("", htype.replace("guild", "Guild"), ""))[1] or htype,
                             "at": [{"map": a["map"], "poi": a["poi"]} for a in at]})

    # -----------------------------------------------------------------------------------------------------------------
    # Travel

    schedules = []
    file_to_id = {f: r["id"] for f, r in shared.records.items()}
    for house_id, house in sorted(shared.houses.items()):
        if house["type"] not in ("Stables", "Boats") or not house_locations.get(house_id):
            continue
        row = rule_row(shared.rules, house["type"], house)
        location_ids = row[1:] if row else shared.transport_index.get(house_id, [])
        boat = house["type"] == "Boats"
        fare = max(1, round((50 if boat else 25) * (house["val"] or 1)))
        at = [{"map": a["map"], "poi": a["poi"]} for a in house_locations[house_id]]
        for location_id in dict.fromkeys(location_ids):
            location = shared.transport_locations.get(location_id)
            if location is None or location_id < 0:
                continue
            target = file_to_id.get(location["map"])
            if target not in map_ids:
                continue
            gate = ""
            if location["qbit"]:
                gate = gate_text(book, quests, quest_key, location["qbit"])
            for day in location["days"]:
                schedules.append({"vessel": house["name"], "kind": "Boat" if boat else "Coach",
                                  "from": house_locations[house_id][0]["map"], "at": at, "to": target,
                                  "toPlace": location["name"], "day": day, "days": location["travel"],
                                  "price": fare, "gated": bool(location["qbit"]), "gate": gate})
    links = [l for l in exits_between.values() if l["to"] in map_ids]
    world_links: dict[tuple[str, str], dict] = {}
    for link in links:
        a, b = region_of.get(link["from"]), region_of.get(link["to"])
        if not a or not b or a == b:
            continue
        pair = tuple(sorted((a, b)))
        if link["days"]:
            world_links[pair] = {"a": pair[0], "b": pair[1], "days": link["days"], "label": f"{link['days']} d"}
        elif pair not in world_links:
            world_links[pair] = {"a": pair[0], "b": pair[1], "days": 0, "label": "", "passage": True}

    # -----------------------------------------------------------------------------------------------------------------
    # Bestiary, items, site

    monster_list = mm9.build_monsters(monsters, monster_maps)
    for monster in monster_list:
        monster.pop("picture", None)
        monster.pop("family_key", None)
    monster_list = mm9.attach_portraits(monster_list, out, skip_images, set(book.get("monster_portrait_exclude", [])),
                                        ROOT / f"output/{world}_site_monsters")
    mm9.attach_shots(maps_out, out, skip_images, set(book.get("shot_exclude", [])), ROOT / f"output/{world}_site_shots")

    data = {
        "generated": "",
        "site": book["site"],
        "poiTypes": poi_types,
        "regions": regions,
        "chapters": [{"id": c["id"], "name": c["name"]} for c in book.get("chapters") or []],
        "maps": maps_out,
        "quests": sorted(quests.values(), key=lambda q: ({"main": 0, "side": 1, "promotion": 2}[q["cat"]],
                                                         q.get("chapter", 0), (q.get("level") or {}).get("rec", 0),
                                                         q["title"])),
        "teachers": teachers,
        "vendors": vendors,
        "spellbooks": sorted(spellbooks.values(), key=lambda b: b["spell"]),
        "services": services,
        "promotions": promotions,
        "story": story,
        "walkthroughs": walkthroughs,
        "faq": mm9.load_faq(FAQ / world) if (FAQ / world / "faq.yml").exists() else [],
        "travel": {"links": links, "schedules": schedules, "extras": [], "worldLinks": list(world_links.values())},
        "monsters": monster_list,
    }
    return data


# ---------------------------------------------------------------------------------------------------------------------
# Items: the engine's items.txt (the same catalogue for the three books)

EQUIP_CATEGORY = dict(mm9.EQUIP_CATEGORY, Cloak="armor", WeaponW="weapons", Book="books", Sscroll="scrolls",
                      Mscroll="readables", Bottle="potions", Reagent="potions", Herb="potions", Gem="gems",
                      Ore="gems")
# The MM9 guide's categories, its skill books being MM6-MM8's spellbooks, with scrolls, potions and gems added.
ITEM_CATEGORIES = [(c, {"books": "Spellbooks"}.get(c, n)) for c, n in mm9.ITEM_CATEGORIES if c != "sets"]
ITEM_CATEGORIES[ITEM_CATEGORIES.index(("books", "Spellbooks")) + 1:1] = [
    ("scrolls", "Spell scrolls"), ("potions", "Potions and reagents"), ("gems", "Gems and ore")]


def build_items(shared: Shared, out: Path, skip_images: bool) -> dict:
    """Every named item of the merged table (placeholders and blanks left out), its icon from the engine's or the
    MM6-MM8 worlds' icons_x2; artifacts and relics by their material, quest items by their description."""
    icon_dirs = [ENGINE / "icons_x2"] + [WORLDS / w / "icons_x2" for w in ("mm8", "mm7", "mm6")]
    icons: list[Path] = []
    icon_cell: dict[str, int] = {}
    result = []
    for item_id, row in sorted(shared.items.items()):
        name = row["name"].strip()
        if not item_id or not name or name == "0" or name.startswith("_") or row["pic"] in ("", "null", "0") or \
                row["equip"] == "Gold":
            continue
        equip = row["equip"]
        desc = mm9.clean_quoted(row["desc"]).replace("�", "'")
        world_flag = re.search(r"World:(mm\d)", row["flags"])
        if row["material"] in ("Artifact", "Relic"):
            category = "artifacts"
        elif equip in EQUIP_CATEGORY:
            category = EQUIP_CATEGORY[equip]
        elif desc.lower().startswith("quest item") or equip == "N / A" and row["value"] == 0:
            category = "quest"
        else:
            category = "misc"
        if category == "misc" and equip in ("N / A", "0", "") and "quest" in desc.lower():
            category = "quest"
        pic = row["pic"].lower()
        if pic not in icon_cell:
            path = next((d / f"{pic}.png" for d in icon_dirs if (d / f"{pic}.png").exists()), None)
            icon_cell[pic] = -1
            if path is not None:
                icon_cell[pic] = len(icons)
                icons.append(path)
        result.append({
            "id": item_id, "name": name, "cat": category, "equip": equip if equip not in ("0", "") else "",
            "skill": row["skill"] if row["skill"] not in ("Misc", "0") else "",
            "mod1": row["mod1"] if row["mod1"] not in ("0", "") and not re.fullmatch(r"S\d+", row["mod1"]) else "",
            "mod2": row["mod2"] if row["mod2"] not in ("0", "") and equip not in ("Book", "Sscroll") else "",
            "value": row["value"], "tier": 0,
            "rarity": row["material"] if row["material"] in ("Artifact", "Relic") else "",
            "set": "", "desc": desc, "flags": [], "classes": world_flag.group(1).upper() if world_flag else "",
            "icon": icon_cell[pic], "fx": [],
        })
    atlas = out / "img/items.webp"
    listing = out.parent / f"{out.name}_work/items_atlas.json"  # its icons: a changed list redraws it
    names = [str(p.relative_to(ROOT)) for p in icons]
    if not skip_images or not atlas.exists() or not listing.exists() or json.loads(listing.read_text()) != names:
        mm9.write_icon_atlas(icons, atlas)
        listing.parent.mkdir(parents=True, exist_ok=True)
        listing.write_text(json.dumps(names))
    return {
        "iconAtlas": {"src": "img/items.webp", "cell": mm9.ICON_CELL, "cols": mm9.ICON_COLUMNS,
                      "rows": (len(icons) + mm9.ICON_COLUMNS - 1) // mm9.ICON_COLUMNS},
        "itemCategories": [{"id": c, "name": n} for c, n in ITEM_CATEGORIES],
        "items": result,
        "sets": [],
        "enchants": mm9.load_enchants(),
    }


# ---------------------------------------------------------------------------------------------------------------------
# Checks and output


def developer_wording(data: dict) -> list[str]:
    """Point names and details, quest titles, rewards and giver texts are for players (the Xeen guide's D-76 rule)."""
    faults = []
    for map_data in data["maps"]:
        for poi in map_data["pois"]:
            for field in ("n", "d"):
                hit = DEV_WORDING_RE.search(poi.get(field, ""))
                if hit:
                    faults.append(f"{map_data['id']} {poi['id']} {field}: {hit.group(0)!r}: {poi[field][:120]}")
    for quest in data["quests"]:
        for field in ("title", "reward", "giverText"):
            hit = DEV_WORDING_RE.search(quest.get(field, ""))
            if hit:
                faults.append(f"quest {quest['id']} {field}: {hit.group(0)!r}: {quest[field][:120]}")
    return faults


def check_references(data: dict) -> list[str]:
    """Every map, point, quest and region a part of the data names exists."""
    maps = {m["id"]: {p["id"] for p in m["pois"]} for m in data["maps"]}
    quests = {q["id"] for q in data["quests"]}
    faults = []

    def ref(where: str, node: dict) -> None:
        if node["map"] not in maps:
            faults.append(f"{where}: no map {node['map']}")
        elif "poi" in node and node["poi"] not in maps[node["map"]]:
            faults.append(f"{where}: no point {node['map']}/{node['poi']}")

    for q in data["quests"]:
        for key in ("givers", "handoffs", "steps"):
            for node in q[key]:
                ref(f"quest {q['id']} {key}", node)
    for group in ("teachers", "vendors", "services", "promotions"):
        for entry in data[group]:
            for node in entry["at"]:
                ref(f"{group} {entry.get('name', entry.get('to'))}", node)
    for p in data["promotions"]:
        faults += [f"promotion {p['to']}: no quest {k}" for k in p["quests"] if k not in quests]
    for s in data["travel"]["schedules"]:
        for node in s["at"]:
            ref(f"schedule {s['vessel']}", node)
        if s["to"] not in maps:
            faults.append(f"schedule {s['vessel']}: no map {s['to']}")
    for link in data["travel"]["links"]:
        if link["from"] not in maps or link["to"] not in maps:
            faults.append(f"link {link}")
    regions = {r["id"] for r in data["regions"]}
    for r in data["regions"]:
        faults += [f"region {r['id']}: no map {m}" for m in r["maps"] + [r["hub"]] if m not in maps]
    for link in data["travel"]["worldLinks"]:
        if link["a"] not in regions or link["b"] not in regions:
            faults.append(f"world link {link}")
    for m in data["maps"]:
        for poi in m["pois"]:
            if poi.get("map") and poi["map"] not in maps and poi["t"] == "exit":
                pass  # an exit to another world's map (the guide names it; it has no page here)
            faults += [f"{m['id']} {poi['id']}: no quest {k}" for k in poi.get("quests", []) if k not in quests]
            if poi.get("mon") and poi["mon"] not in {x["id"] for x in data["monsters"]} and poi["t"] == "monster":
                pass  # livestock without attacks are left out of the bestiary
    for m in data["maps"]:
        ids = Counter(p["id"] for p in m["pois"])
        faults += [f"{m['id']}: point id {i} used {n} times" for i, n in ids.items() if n > 1]
    chapters = {c["id"] for c in data["chapters"]}
    faults += [f"quest {q['id']}: no chapter {q.get('chapter')}" for q in data["quests"]
               if q["cat"] == "main" and q.get("chapter") not in chapters]
    return faults


def write_site(out: Path, world: str, data: dict, title: str) -> None:
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "data/guide.js").write_text("window.GUIDE = " + json.dumps(data, separators=(",", ":")) + ";\n")
    for path in MM9_WEB.iterdir():
        if path.is_file() and path.name != "page.html":
            shutil.copy2(path, out / path.name)
    page = (MM9_WEB / "page.html").read_text(encoding="utf-8")
    page = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", page)
    brand = title.rsplit(" ", 1)
    page = re.sub(r'(<a class="brand[^"]*" href="#home">)[^<]*<span>[^<]*</span>',
                  lambda m: f"{m.group(1)}{brand[0]} <span>{brand[1]}</span>", page)
    (out / "page.html").write_text(page, encoding="utf-8")
    (out / "index.html").write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                                    '<meta name="viewport" content="width=device-width, initial-scale=1, '
                                    'viewport-fit=cover">\n</head>\n<body>\n' + page + "</body>\n</html>\n",
                                    encoding="utf-8")
    size = (out / "data/guide.js").stat().st_size
    print(f"wrote {out} (guide.js {size // 1024} KB, {sum(len(m['pois']) for m in data['maps'])} points)",
          file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--world", choices=["mm6", "mm7", "mm8", "all"], default="all")
    parser.add_argument("--skip-images", action="store_true", help="reuse map plans, map and icon images")
    args = parser.parse_args()
    config = yaml.safe_load(CONFIG.read_text())
    shared = Shared()
    worlds = ["mm6", "mm7", "mm8"] if args.world == "all" else [args.world]
    failed = []
    for world in worlds:
        out = ROOT / f"output/{world}_site"
        out.mkdir(parents=True, exist_ok=True)
        data = build_book(world, out, args.skip_images, config, shared)
        data.update(build_items(shared, out, args.skip_images))
        faults = developer_wording(data) + check_references(data)
        if faults:
            print("\n".join(faults[:60]), file=sys.stderr)
            failed.append(f"{world}: {len(faults)} faults")
        write_site(out, world, data, config["books"][world]["site"]["title"])
        for folder, target in ((STORY / world / "img", "img/story"), (FAQ / world / "img", "img/faq")):
            if folder.is_dir():
                shutil.copytree(folder, out / target, dirs_exist_ok=True)
        counts = Counter(q["cat"] for q in data["quests"])
        print(f"{world}: {len(data['maps'])} maps, {sum(len(m['pois']) for m in data['maps'])} points, quests "
              f"{counts['main']} main / {counts['side']} side / {counts['promotion']} promotion, "
              f"{sum(1 for t in data['teachers'] if t['mastery'] != 'Learn')} lessons, {len(data['vendors'])} shops "
              f"and guilds, {len(data['services'])} services, {len(data['monsters'])} monsters, "
              f"{len(data['items'])} items", file=sys.stderr)
    if failed:
        raise SystemExit("; ".join(failed) + ": fix the generator or site_config.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
