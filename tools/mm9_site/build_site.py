#!/usr/bin/env python3
"""Build the MM9 guide website from the MM9 world package.

Reads assets_dev/worlds/mm9 (scenes, map events, data tables, quest notes, minimaps, item icons), the raw MM9 DAT
object dumps in assets_editor_dev/worlds/mm9/maps and the engine's shared tables, and writes a static site to
output/mm9_site: the web files from tools/mm9_site/web, data/guide.js with everything the pages show, minimap and
icon images. Open output/mm9_site/index.html directly or serve the folder. See tools/mm9_site/README.md.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / "assets_dev/worlds/mm9"
ENGINE = ROOT / "assets_dev/engine"
RAW_OBJECTS = ROOT / "assets_editor_dev/worlds/mm9/maps"
WEB = Path(__file__).resolve().parent / "web"
CONFIG = Path(__file__).resolve().parent / "site_config.yml"

sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
import promote_mm9_map_images as mapimages  # noqa: E402

SCALE = mapimages.MM9_TO_OPENYAMM_SCALE

csv.field_size_limit(1 << 24)


# ---------------------------------------------------------------------------------------------------------------------
# Small readers


def read_tsv(path: Path, skip: int = 0) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    rows = rows[skip:]
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:] if any(cell.strip() for cell in row)]


def read_rows(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", errors="replace", newline="") as handle:
        return list(csv.reader(handle, delimiter="\t"))


def to_int(text: str, default: int = 0) -> int:
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return default


def float_bits(value: str) -> float:
    """MM9 stores some float properties as the int of their bits (1084227584 is 5.0)."""
    number = to_int(value)
    return struct.unpack("<f", struct.pack("<I", number & 0xFFFFFFFF))[0]


def clean_quoted(text: str) -> str:
    return text.strip().strip('"').replace("~", "\n").strip()


# ---------------------------------------------------------------------------------------------------------------------
# Raw DAT objects (assets_editor_dev/worlds/mm9/maps/<map>.raw_objects.yml); a line scanner, PyYAML is far too slow.

RAW_CLASSES = {
    "Switch", "Button", "PerceptionBrush", "Teleporter", "WellMMIX", "Cauldron", "Cookpot", "Clover", "StatStone",
    "Barrel", "Shooter", "DamageBrush", "PropDamager", "ExitTrigger", "ScriptObject",
}
RAW_PROPS = {"Name", "Pos", "TeleportDestination", "PerceptionValue", "DestinationWorld"}


def scan_raw_objects(map_id: str) -> tuple[dict[int, dict], dict[str, tuple]]:
    """The objects of RAW_CLASSES by DAT index, and every object's world position by its name (lower case)."""
    path = RAW_OBJECTS / f"{map_id}.raw_objects.yml"
    objects: dict[int, dict] = {}
    every: list[dict] = []
    if not path.exists():
        return objects, {}, {}, {}
    index = -1
    current: dict = {}
    prop = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("  - object_index:"):
                index = int(line.split(":", 1)[1])
            elif line.startswith("    name: "):
                cls = line[10:].strip().strip('"')
                current = {"cls": cls, "index": index}
                every.append(current)
                if cls in RAW_CLASSES:
                    objects[index] = current
            elif line.startswith("      - name: "):
                prop = line[14:].strip().strip('"')
            elif prop in RAW_PROPS and line.startswith("        value_json: "):
                if current["cls"] in RAW_CLASSES or prop in ("Name", "Pos"):
                    current[prop] = json.loads(json.loads(line[20:]))
                prop = None
    positions = {}
    by_index = {}
    indices = {}
    for record in every:
        pos = record.get("Pos")
        if pos:
            record["world"] = (pos[0] * SCALE, pos[2] * SCALE, pos[1] * SCALE)
            by_index[record["index"]] = record["world"]
            if record.get("Name"):
                positions.setdefault(record["Name"].lower(), record["world"])
                indices.setdefault(record["Name"].lower(), record["index"])
    return objects, positions, by_index, indices


def frame_offset(scene: dict, by_index: dict[int, tuple]) -> tuple[float, float, float]:
    """The rebuilt map's offset from MM9's DAT frame (scene = DAT + offset): the median over actors and containers
    found in both. Several converters moved a map whole (Connecting Tunnels by -17000, Thronheim by 33607)."""
    deltas = []
    for actor in scene["initial_state"]["actors"]:
        world = by_index.get(actor.get("mm9_source_object_index"))
        if world:
            pos = actor["position"]
            deltas.append((pos["x"] - world[0], pos["y"] - world[1], pos["z"] - world[2]))
    for chest in scene.get("loot_containers", []):
        world = by_index.get(chest.get("source_object_index"))
        if world:
            pos = chest["position"]
            deltas.append((pos["x"] - world[0], pos["y"] - world[1], pos["z"] - world[2]))
    if not deltas:
        return 0.0, 0.0, 0.0
    middle = lambda values: sorted(values)[len(values) // 2]  # noqa: E731
    return tuple(round(middle([d[i] for d in deltas]) / 64) * 64 for i in range(3))


# ---------------------------------------------------------------------------------------------------------------------
# Map presentation: bounds, flips and floor images (the game's catalog, or MM9's DAT header for the rest)


def load_presentations(map_ids: list[str], out_dir: Path) -> dict[str, dict]:
    catalog = yaml.safe_load((WORLD / "ui/maps/catalog.yml").read_text())
    by_map = {entry["map"]: entry for entry in catalog["maps"]}
    dat_root = ROOT / "mm9/extracted/WORLDS/WORLDS"
    result = {}
    (out_dir / "img/maps").mkdir(parents=True, exist_ok=True)
    for map_id in map_ids:
        entry = by_map.get(map_id)
        if entry:
            bounds = entry["world_bounds"]
            presentation = {
                "frame": "scene",
                "bounds": [bounds["min_x"], bounds["max_x"], bounds["min_y"], bounds["max_y"]],
                "flipU": entry.get("flip_u", False),
                "flipV": entry.get("flip_v", False),
                "floors": [
                    {
                        "src": Path(v["texture"]).stem,
                        "minZ": v.get("minimum_z"),
                        "maxZ": v.get("maximum_z"),
                    }
                    for v in entry["variants"]
                ],
            }
        else:
            dat_files = [p for p in dat_root.glob("*.dat") if p.stem.lower() == map_id]
            if not dat_files:
                continue
            min_x, max_x, min_y, max_y = mapimages.read_dat_horizontal_bounds(dat_files[0], SCALE)
            exterior = map_id in mapimages.EXTERIOR_MAPS
            floors = []
            for variant in mapimages.FLOOR_VARIANTS.get(map_id, (mapimages.ImageVariant(""),)):
                band = lambda y: None if y is None else (y - mapimages.PLAYER_HALF_HEIGHT_LT) * SCALE  # noqa: E731
                floors.append({
                    "src": (map_id + variant.suffix).lower(),
                    "minZ": band(variant.minimum_source_y),
                    "maxZ": band(variant.maximum_source_y),
                })
            presentation = {
                "bounds": [min_x, max_x, min_y, max_y],
                "flipU": exterior,
                "flipV": not exterior,
                "floors": floors,
            }
        for index, floor in enumerate(presentation["floors"]):
            source = WORLD / "ui/maps" / f"{floor['src']}.pcx"
            image = Image.open(source).convert("RGB")
            floor["w"], floor["h"] = image.size
            name = f"{floor['src']}.webp"
            image.save(out_dir / "img/maps" / name, "WEBP", quality=84, method=5)
            floor["img"] = f"img/maps/{name}"
            if index == 0:
                thumb = image.copy()
                thumb.thumbnail((320, 320))
                thumb.save(out_dir / "img/maps" / f"{map_id}_thumb.webp", "WEBP", quality=80)
                presentation["thumb"] = f"img/maps/{map_id}_thumb.webp"
            del floor["src"]
        presentation["floorNames"] = floor_names(len(presentation["floors"]))
        result[map_id] = presentation
    return result


def floor_names(count: int) -> list[str]:
    if count == 1:
        return ["Map"]
    # MM9's floor images run from the top band (A) down; the last image covers everything else.
    return [f"Level {chr(ord('A') + i)}" for i in range(count)]


def to_uv(presentation: dict, x: float, y: float) -> tuple[float, float]:
    min_x, max_x, min_y, max_y = presentation["bounds"]
    u = (x - min_x) / max(max_x - min_x, 1e-6)
    v = (y - min_y) / max(max_y - min_y, 1e-6)
    if presentation["flipU"]:
        u = 1.0 - u
    if presentation["flipV"]:
        v = 1.0 - v
    return round(min(max(u, 0.0), 1.0), 5), round(min(max(v, 0.0), 1.0), 5)


def floor_of(presentation: dict, z: float) -> int:
    floors = presentation["floors"]
    for index, floor in enumerate(floors):
        low, high = floor.get("minZ"), floor.get("maxZ")
        if low is None and high is None:
            return index
        if (low is None or z > low) and (high is None or z <= high):
            return index
    return len(floors) - 1


# ---------------------------------------------------------------------------------------------------------------------
# Tables


def load_monsters() -> dict[int, dict]:
    rows = read_rows(WORLD / "data_tables/monster_data.txt")
    monsters = {}
    resist_names = ["Fire", "Air", "Water", "Earth", "Mind", "Spirit", "Body", "Light", "Dark", "Phys"]
    for row in rows[4:]:
        if len(row) < 38 or not row[0].strip().isdigit():
            continue
        monster_id = int(row[0])
        attacks = []
        if row[17] and row[17] != "0":
            attacks.append({"type": row[17], "dmg": row[18], "missile": row[19] if row[19] != "0" else ""})
        if row[21] and row[21] != "0":
            attacks.append({"type": row[21], "dmg": row[22], "missile": row[23] if row[23] != "0" else "",
                            "chance": to_int(row[20])})
        spells = [s for s in (row[25], row[27]) if s and s != "0"]
        # The picture names a family and its tier ("MM9 Skeleton B"); a numbered one ("MM9 252 Forad Darre") is unique.
        family_match = re.match(r"MM9 (\D.*?) ([ABC])$", row[2].strip())
        monsters[monster_id] = {
            "id": monster_id,
            "name": row[1].strip(),
            "family": family_match.group(1) if family_match else "",
            "tier": family_match.group(2) if family_match else "",
            "level": to_int(row[3]),
            "hp": to_int(row[4]),
            "ac": to_int(row[5]),
            "xp": to_int(row[6]),
            "treasure": parse_treasure(row[7]),
            "fly": row[9].strip().upper() == "Y",
            "move": row[10].strip(),
            "ai": row[11].strip(),
            "speed": to_int(row[13]),
            "recovery": to_int(row[14]),
            "attacks": attacks,
            "spells": [{"spell": s, "chance": to_int(c)} for s, c in zip((row[25], row[27]), (row[24], row[26]))
                       if s and s != "0"] if spells else [],
            "resist": {name: row[28 + i].strip() for i, name in enumerate(resist_names)},
            "special": row[38].strip() if len(row) > 38 and row[38].strip() not in ("", "0") else "",
        }
    return monsters


TREASURE_RE = re.compile(r"^(?:(\d+)%)?(?:(\d+[dD]\d+(?:\+\d+)?))?(?:\+?L(\d))?([A-Za-z]*)$")


def parse_treasure(text: str) -> dict | None:
    text = text.strip()
    if not text or text == "0":
        return None
    match = TREASURE_RE.match(text)
    if not match:
        return {"raw": text}
    chance, gold, level, kind = match.groups()
    return {
        "gold": gold.lower() if gold else "",
        "chance": int(chance) if chance else (100 if level else 0),
        "level": int(level) if level else 0,
        "kind": kind or "Any",
    }


def load_map_names() -> dict[str, str]:
    names = {}
    for row in read_rows(ENGINE / "data_tables/map_stats.txt"):
        if len(row) > 2 and row[2].endswith(".blv") and "mm9" in row:
            names[row[2][:-4].lower()] = row[1].strip()
    return names


def load_class_promotions() -> dict[str, list[list[str]]]:
    """MM9.Promotions (events/common/mm9_common.lua): the MM6-MM8 classes each MM9 promotion quest promotes."""
    text = (WORLD / "events/common/mm9_common.lua").read_text(encoding="utf-8")
    block = re.search(r"MM9\.Promotions = \{(.*?)\n\}", text, re.S).group(1)
    result = {}
    for name, body in re.findall(r"(\w+) = \{([^}]*)\}", block):
        result[name] = [[pretty_name(a), pretty_name(b)] for a, b in re.findall(r'(\w+) = "(\w+)"', body)]
    return result


# ---------------------------------------------------------------------------------------------------------------------
# Map events (assets_dev/worlds/mm9/events/maps/<map>.lua): door names and bonus props


DOORS_RE = re.compile(r"local DOORS = \{(.*?)\}\s*$", re.M)
BONUS_RE = re.compile(r"MM9\.use(Well|Cauldron|Cookpot|Clover)\((\d+)((?:,\s*[-\d.]+)*)")
BONUS_STATS = ["Might", "Magic", "Endurance", "Accuracy", "Speed", "Luck"]
BONUS_SCHOOLS = ["Elemental", "Dark", "Light", "Spirit", "Physical"]


def load_map_events(map_id: str) -> tuple[dict[int, str], dict[int, str]]:
    path = WORLD / "events/maps" / f"{map_id}.lua"
    if not path.exists():
        return {}, {}
    text = path.read_text(encoding="utf-8", errors="replace")
    door_names: dict[int, str] = {}
    match = DOORS_RE.search(text)
    if match:
        for name, door_id in re.findall(r"([A-Za-z_][\w]*)\s*=\s*(\d+)", match.group(1)):
            door_names[int(door_id)] = name
        for name, door_id in re.findall(r'\["([^"]+)"\]\s*=\s*(\d+)', match.group(1)):
            door_names[int(door_id)] = name
    bonus: dict[int, str] = {}
    for kind, index, rest in BONUS_RE.findall(text):
        args = [float(a) for a in rest.replace(" ", "").split(",") if a]
        bonus[int(index)] = describe_bonus(kind, args)
    return door_names, bonus


def describe_bonus(kind: str, args: list[float]) -> str:
    def school(i: float) -> str:
        return BONUS_SCHOOLS[int(i)] if 0 <= int(i) < len(BONUS_SCHOOLS) else "?"

    if kind == "Well" and len(args) >= 5:
        stat, stat_type, amount, seconds, per_day = args[:5]
        amount = int(amount)
        if stat == 0:
            effect = f"+{amount} HP"
        elif stat == 1:
            effect = f"+{amount} SP"
        elif stat == 2:
            name = BONUS_STATS[int(stat_type)] if 0 <= int(stat_type) < len(BONUS_STATS) else "?"
            effect = f"+{amount} {name} " + ("permanent, party, once" if seconds == 0 else "temporary")
        else:
            effect = f"+{amount} {school(stat_type)} resistance" + (" permanent" if seconds == 0 else " temporary")
        return f"Well: {effect}; {int(per_day)}/day"
    if kind == "Cauldron" and len(args) >= 2:
        return f"Cauldron: +{int(args[1])} {school(args[0])} resistance, party, once"
    if kind == "Cookpot" and len(args) >= 4:
        return f"Cook pot: +{int(args[2])} {school(args[1])} resistance temporary; {int(args[0])}% poison; " \
               f"{int(args[3])}/day"
    if kind == "Clover":
        return "Four-leaf clover (item), once"
    return kind


DOOR_KINDS = [
    (re.compile(r"lever|switch|button|pull|crank|wheel", re.I), "lever"),
    (re.compile(r"secret|hidden|fake|false", re.I), "secret"),
    (re.compile(r"trap|crush|shooter|spike|blade|saw|axe", re.I), "trap"),
    (re.compile(r"puzzle|piece|block|square|organ|key", re.I), "lever"),
    (re.compile(r"drawer|cabinet|lid|book", re.I), None),
]


def door_kind(name: str) -> str | None:
    for pattern, kind in DOOR_KINDS:
        if pattern.search(name):
            return kind
    return "door"


HINT_RADIUS = 300.0
NPC_RADIUS = 60.0  # a quest step's DAT object this close to a placed NPC is that NPC's script  # a perception glow this close to a door, lever, trap or secret belongs to it


def pretty_name(name: str) -> str:
    name = re.sub(r"(\d+)$", r" \1", name)
    name = re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Za-z])", " ", name)
    return name.replace("_", " ").strip()


# ---------------------------------------------------------------------------------------------------------------------
# Quest steps in the map events: each handler names its DAT object and the quest keys and items it checks or gives


HANDLER_RE = re.compile(r"^handlers\[(\d+)\] = function\(\)(.*)$")
REGISTER_RE = re.compile(r'^RegisterEvent\((\d+), "([^"]*)"')
KEY_RE = re.compile(r"(?:MM9\.giveKey|MM9\.hasKey|MM9\.takeKey|\bhas|\breward)\((\d+)")
GIVE_RE = re.compile(r"(?:MM9\.giveItem|\bgive)\((\d+)")
NEED_RE = re.compile(r"(?:MM9\.hasItem|MM9\.takeItem|evt\.RemovePartyMemberItem\([^,]+,\s*MM9\.ItemIds\[)\(?(\d+)")
XP_RE = re.compile(r"(?:MM9\.giveExperience\((\d+)\)|\breward\(\d+,\s*(\d+))")
SOURCE_RE = re.compile(r'"[a-z0-9]+:([A-Za-z_][\w ]*?)"')
RUDE_RE = re.compile(r"RUDE (\d+)|openRude\((\d+)\)")
WORD_RE = re.compile(r"[A-Za-z_][\w]*")


def parse_handlers(map_id: str) -> list[dict]:
    path = WORLD / "events/maps" / f"{map_id}.lua"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    labels = {}
    for line in lines:
        match = REGISTER_RE.match(line)
        if match:
            labels[int(match.group(1))] = match.group(2)
    handlers = []
    i = 0
    while i < len(lines):
        match = HANDLER_RE.match(lines[i])
        if not match:
            i += 1
            continue
        comments = []
        j = i - 1
        while j >= 0 and lines[j].startswith("--"):
            comments.insert(0, lines[j][2:])
            j -= 1
        first_code, _, first_comment = match.group(2).partition("--")
        body = [first_code]
        tail = [first_comment]
        if not re.search(r"\bend\s*$", first_code.strip()):
            i += 1
            while i < len(lines) and lines[i] != "end":
                code, _, comment = lines[i].partition("--")
                body.append(code)
                tail.append(comment)
                i += 1
        i += 1
        code = "\n".join(body)
        trailing = " ".join(tail)
        if "evt.OpenChest" in code or int(match.group(1)) == 1 or labels.get(int(match.group(1))) in (
                "Map load", "Shared objects"):
            continue
        xp = sum(int(a or b) for a, b in XP_RE.findall(code))
        rude = next((int(a or b) for a, b in RUDE_RE.findall(trailing + " " + " ".join(comments) + code)), None)
        names = SOURCE_RE.findall(code) + WORD_RE.findall(trailing) + WORD_RE.findall(" ".join(comments))
        handlers.append({
            "id": int(match.group(1)),
            "label": labels.get(int(match.group(1)), ""),
            "keys": {90000 + int(k) for k in KEY_RE.findall(code)},
            "gives": [int(x) for x in GIVE_RE.findall(code)],
            "needs": [int(x) for x in NEED_RE.findall(code)],
            "xp": xp,
            "rude": rude,
            "names": names,
        })
    return handlers


LATE_MAPS = {"afterworld", "hallofthegods"}


def add_rude_givers(quests: dict, quest_of_qbit: dict, rude_locations: dict, maps_out: list[dict]) -> None:
    """Givers and report-to NPCs from the dialogue itself: a RUDE row granting a key that shows a journal note offers
    that quest; one granting a key that hides it closes it. Covers NPCs without generated quest interactions."""
    stages = yaml.safe_load((WORLD / "state/quest_interactions.yml").read_text())["journal_stages"]
    shows, hides = defaultdict(set), defaultdict(set)
    for stage in stages:
        quest = quest_of_qbit.get(stage["entry_qbit"])
        if quest:
            for qbit in stage["required_qbits"]:
                shows[qbit].add(quest)
            for qbit in stage["forbidden_qbits"]:
                hides[qbit].add(quest)
    pois = {(m["id"], p["id"]): p for m in maps_out for p in m["pois"]}
    proposals: dict[str, list] = defaultdict(list)
    for path in (WORLD / "dialogue/rude").glob("NPC*.rude"):
        rude = to_int(path.stem[3:])
        if rude >= 997 or rude not in rude_locations:
            continue
        offered, closed = set(), set()
        for row in csv.reader(path.open(encoding="utf-8", errors="replace")):
            for cell in row[15:25]:
                key = to_int(cell)
                if key > 0:
                    qbit = 90000 + key
                    if len(shows.get(qbit, ())) <= 2:
                        offered |= shows.get(qbit, set())
                    if len(hides.get(qbit, ())) <= 2:
                        closed |= hides.get(qbit, set())
        # The Jarls stand again in the Afterworld and as war-council props in Thronheim: their quests are given where
        # they live, so later copies and props do not count while an actor elsewhere exists.
        places = [(m, p) for m, p in rude_locations[rude] if m not in LATE_MAPS]
        actors = [(m, p) for m, p in places if not p.startswith("r")]
        places = actors or places
        for key in offered | closed:
            proposals[key].append((rude, "givers" if key in offered else "handoffs", places))
    # A key many NPCs grant is a shared topic, not the quest's start: keep a quest's proposals only from a few NPCs.
    for key, entries in proposals.items():
        if len({rude for rude, _, _ in entries}) > 3:
            continue
        for rude, role, places in entries:
            for map_id, poi_id in places:
                poi = pois[(map_id, poi_id)]
                entry = {"map": map_id, "poi": poi_id, "name": poi["n"]}
                if entry not in quests[key][role]:
                    quests[key][role].append(entry)
                poi["quests"] = sorted(set(poi.get("quests", [])) | {key})
                if poi["t"] == "npc":
                    poi["t"] = "quest"


def key_quest_index(quest_of_qbit: dict[int, str], interactions: list[dict]) -> dict[int, set[str]]:
    """Quest keys (qbits) to the quests whose journal entries they show or hide. Journal entry numbers share the key
    range (entry 100 is a note, key 100 a flag), so the entries themselves are not keys."""
    stages = yaml.safe_load((WORLD / "state/quest_interactions.yml").read_text())["journal_stages"]
    index: dict[int, set[str]] = defaultdict(set)
    for stage in stages:
        quest = quest_of_qbit.get(stage["entry_qbit"])
        if quest:
            for qbit in [*stage["required_qbits"], *stage["forbidden_qbits"]]:
                index[qbit].add(quest)
    for interaction in interactions:
        linked = {quest_of_qbit[q] for q in interaction.get("journal_entries", []) if q in quest_of_qbit}
        for qbit in interaction.get("effects", {}).get("granted_qbits", []):
            index[qbit] |= linked
    # A key that gates many journal entries is a chapter or world state, not one quest's step.
    return {qbit: quests for qbit, quests in index.items() if len(quests) <= 3}


# ---------------------------------------------------------------------------------------------------------------------
# Build


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "output/mm9_site")
    parser.add_argument("--skip-images", action="store_true", help="reuse map and icon images already in --out")
    args = parser.parse_args()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(CONFIG.read_text())
    extra = yaml.safe_load((Path(__file__).resolve().parent / "extra_pois.yml").read_text())

    map_ids = sorted(p.name.split(".")[0] for p in (WORLD / "maps").glob("*.scene.yml"))
    names = load_map_names()
    monsters = load_monsters()
    tables = WORLD / "data_tables"
    trainers = read_tsv(tables / "skill_trainers.txt")
    racial = load_racial_trainers()
    racial_by_rude = {t["rude"]: t for t in racial["trainers"]}
    npc_names = load_npc_names()
    vendors = read_tsv(tables / "vendors.txt")
    stock = load_stock()
    tier_of = {to_int(r["Item #"]): to_int(r.get("normalized_tier", "0")) for r in read_tsv(tables / "items.txt")}
    services = read_tsv(tables / "service_venues.txt")
    routes = read_tsv(tables / "transport_routes.txt")
    transitions = read_tsv(tables / "map_transitions.txt")
    hirelings = read_tsv(tables / "hirelings.txt")
    promotions = config["promotions"]
    class_lines = load_class_promotions()
    for promotion in promotions:
        promotion["classes"] = class_lines.get(promotion["to"].lower(), [])
    promotion_by_rude = {p["rude"]: p for p in promotions if p.get("rude")}
    interactions = yaml.safe_load((WORLD / "state/quest_interactions.yml").read_text())["interactions"]

    if args.skip_images and (out / "data/presentations.json").exists():
        presentations = json.loads((out / "data/presentations.json").read_text())
    else:
        presentations = load_presentations(map_ids, out)
        (out / "data").mkdir(exist_ok=True)
        (out / "data/presentations.json").write_text(json.dumps(presentations))

    catalog_maps = {e["map"] for e in yaml.safe_load((WORLD / "ui/maps/catalog.yml").read_text())["maps"]}
    for map_id, presentation in presentations.items():
        presentation["frame"] = "scene" if map_id in catalog_maps else "dat"

    region_of = {}
    for region in config["regions"]:
        for map_id in region["maps"]:
            region_of[map_id] = region["id"]

    vendor_by_rude = {to_int(v["source_vendor_id"]): v for v in vendors}
    service_by_rude = {to_int(s["source_service_id"]): s for s in services}
    trainers_by_rude: dict[int, list[dict]] = defaultdict(list)
    for row in trainers:
        trainers_by_rude[to_int(row["RudeId"])].append(row)
    routes_by_rude: dict[int, list[dict]] = defaultdict(list)
    for row in routes:
        routes_by_rude[to_int(row["DockNpcId"])].append(row)
    hireling_by_rude = {to_int(h["rude_id"]): h for h in hirelings}

    # Quests: stages grouped by their headline.
    quest_rows = read_tsv(tables / "english/quests_overlay.txt")
    quests: dict[str, dict] = {}
    quest_of_qbit: dict[int, str] = {}
    for row in quest_rows:
        qbit = to_int(row["Q Bit"])
        text = clean_quoted(row["Quest Note Text"])
        title, _, body = text.partition("\n")
        title = title.strip().rstrip(".")
        key = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        key = config.get("quest_merge", {}).get(key, key)
        quest = quests.setdefault(key, {"id": key, "title": title, "stages": [], "givers": [], "handoffs": []})
        quest["stages"].append({"qbit": qbit, "text": body.strip()})
        quest_of_qbit[qbit] = key

    # Quest steps from every map's events: keys to quests, then quest items to the quests of the keys they go with.
    key_quests = key_quest_index(quest_of_qbit, interactions)
    item_rows = read_tsv(tables / "items.txt")
    raw_items = {to_int(r["x_mm9_raw_item_id"]): r for r in item_rows if r.get("x_mm9_raw_item_id")}
    quest_item = {raw for raw, r in raw_items.items() if "Quest" in r.get("content_flags", "")}
    handlers_by_map = {map_id: parse_handlers(map_id) for map_id in map_ids}
    item_quests: dict[int, set[str]] = defaultdict(set)
    for handlers in handlers_by_map.values():
        for handler in handlers:
            linked = set().union(*(key_quests.get(k, set()) for k in handler["keys"]))
            for raw in handler["gives"] + handler["needs"]:
                if raw in quest_item:
                    item_quests[raw] |= linked
    item_name = lambda raw: raw_items[raw]["Name"] if raw in raw_items else f"item {raw}"  # noqa: E731

    # Map pass: POIs.
    maps_out = []
    unplaced_steps: list[dict] = []
    actor_lookup: dict[tuple[str, int], dict] = {}
    rude_locations: dict[int, list[tuple[str, str]]] = defaultdict(list)
    monster_maps: dict[int, Counter] = defaultdict(Counter)
    poi_types = config["poi_types"]

    for map_id in map_ids:
        presentation = presentations.get(map_id)
        if presentation is None:
            print(f"warning: no map image for {map_id}", file=sys.stderr)
            continue
        scene = json.loads((WORLD / "maps" / f"{map_id}.scene.yml").read_text())
        state = scene["initial_state"]
        raw, positions, by_index, name_index = scan_raw_objects(map_id)
        # Everything in the rebuilt map's frame; the image's bounds are in that frame for catalog maps (refitted to the
        # rebuilt geometry) and in MM9's DAT frame for the rest.
        ox, oy, oz = frame_offset(scene, by_index)
        shift = lambda w: (w[0] + ox, w[1] + oy, w[2] + oz)  # noqa: E731
        for record in raw.values():
            if record.get("world"):
                record["world"] = shift(record["world"])
        positions = {name: shift(w) for name, w in positions.items()}
        image_offset = (0.0, 0.0, 0.0) if presentation.get("frame") == "scene" else (ox, oy, oz)
        door_names, bonus_texts = load_map_events(map_id)
        pois: list[dict] = []
        counters: Counter = Counter()

        def add(kind: str, x: float, y: float, z: float, label: str, detail: str = "", poi_id: str | None = None,
                **extra) -> dict:
            counters[kind] += 1
            u, v = to_uv(presentation, x - image_offset[0], y - image_offset[1])
            poi = {"id": poi_id or f"{kind[:2]}{counters[kind]}", "t": kind, "u": u, "v": v,
                   "f": floor_of(presentation, z - image_offset[2]), "n": label, "x_": x, "y_": y}
            if detail:
                poi["d"] = detail
            poi.update({k: val for k, val in extra.items() if val})
            pois.append(poi)
            return poi

        # Actors: NPCs by their RUDE roles, monsters by their table row.
        for actor in state["actors"]:
            pos = actor["position"]
            rude = actor.get("mm9_rude_id")
            monster = monsters.get(actor.get("monster_id", 0))
            civilian = actor.get("mm9_civilian", False)
            if rude is None and not civilian and monster is not None:
                monster_maps[monster["id"]][map_id] += 1
                add("monster", pos["x"], pos["y"], pos["z"], monster["name"],
                    f"Level {monster['level']}, {monster['hp']} HP", poi_id=f"a{actor['actor_index']}",
                    mon=monster["id"])
                continue
            if rude is None and not actor.get("name"):
                continue
            roles = []
            kind = "npc"
            links: dict = {}
            name = actor.get("name") or pretty_name(actor.get("mm9_source_name", "NPC"))
            if rude in trainers_by_rude:
                rows = trainers_by_rude[rude]
                skills = sorted({r["Mm9Skill"] for r in rows})
                roles.append("Teaches " + ", ".join(
                    f"{s} ({'/'.join(r['TargetMastery'] for r in rows if r['Mm9Skill'] == s)})" for s in skills))
                kind = "teacher"
            if rude in racial_by_rude:
                roles.append(f"Teaches racial abilities (up to {racial_by_rude[rude]['mastery']})")
                kind = "teacher" if kind == "npc" else kind
            promotion = promotion_by_rude.get(rude)
            if promotion:
                roles.append(f"Promotes {promotion['from']} to {promotion['to']}")
                kind = "promoter"
                links["promo"] = promotion["to"]
            if rude in vendor_by_rude:
                vendor = vendor_by_rude[rude]
                summary = stock_summary(stock[to_int(vendor["vendor_id"])], tier_of)
                if summary["treasure"]:
                    sells = f"treasure level {summary['treasure'][0]}, special {summary['treasure'][1]}"
                else:
                    tiers = summary["tiers"]
                    sells = f"item tiers {tiers[0]}-{tiers[1]}" if tiers else "no stock"
                roles.append(f"{vendor['name']} ({vendor['source_type']}, {sells}, prices x{vendor['merchant_base']})")
                kind = "vendor"
                links["vendor"] = to_int(vendor["vendor_id"])
            if rude in service_by_rude:
                service = service_by_rude[rude]
                roles.append(f"{service['name']} ({service['service_type']})")
                if kind == "npc":
                    kind = "service"
                links["service"] = to_int(service["service_id"])
            if rude in routes_by_rude:
                dock = routes_by_rude[rude][0]
                roles.append(f"{dock['DockName']}: {dock['ServiceClassification']}")
                kind = "transport" if kind in ("npc", "service") else kind
                links["dock"] = rude
            if rude in hireling_by_rude:
                hireling = hireling_by_rude[rude]
                roles.append(f"Hireling, level {hireling['level']}, fee {hireling['hire_fee']}")
                if kind == "npc":
                    kind = "hireling"
            poi = add(kind, pos["x"], pos["y"], pos["z"], name, "; ".join(roles), poi_id=f"a{actor['actor_index']}",
                      **links)
            actor_lookup[(map_id, actor.get("mm9_source_object_index", -1))] = poi
            if rude is not None:
                rude_locations[rude].append((map_id, poi["id"]))
                poi["rude"] = rude

        # Containers and searchables.
        for chest in scene.get("loot_containers", []):
            pos = chest["position"]
            level = chest.get("random_treasure_level", 0)
            kind_name = {"chest": "Chest", "treasure_bag": "Treasure bag"}.get(chest.get("kind"), "Container")
            if chest.get("source_class") == "TreasureChest" and "black" in chest.get("source_name", "").lower():
                kind_name = "Black chest"
            details = []
            if level:
                details.append(f"treasure level {level}")
            if chest.get("gold_only"):
                details.append("gold only")
            contents = [f["raw_mm9_item_id"] for f in chest.get("fixed_items", [])]
            if contents:
                details.append("contains " + ", ".join(item_name(raw) for raw in contents))
            if chest.get("trap_level"):
                details.append(f"trap {chest['trap_level']}")
            label = kind_name + (f" L{level}" if level else "")
            linked = sorted(set().union(*(item_quests.get(raw, set()) for raw in contents)))
            add("chest" if chest.get("kind") == "chest" else "loot", pos["x"], pos["y"], pos["z"], label,
                ", ".join(details), lvl=level, quests=linked)
        for prop in scene.get("searchable_loot_props", []):
            pos = prop["position"]
            hazard = prop.get("hazard") or {}
            detail = f"search: treasure level {prop.get('random_treasure_level', 0)}"
            if hazard:
                detail += f"; {hazard.get('chance')}% {hazard.get('condition')}"
            add("loot", pos["x"], pos["y"], pos["z"], pretty_name(prop.get("kind", "pile")).capitalize(), detail)
        for destructible in scene.get("destructibles", []):
            x, y, z = destructible["center"]
            add("breakable", x, y, z, pretty_name(destructible.get("name", "Breakable")),
                f"{destructible.get('hp', 1)} HP")
        for ladder in scene.get("ladders", []):
            x, y, z = ladder["bottom"]
            add("ladder", x, y, z, "Ladder", f"height {round(ladder['top'][2] - z)}")

        # Doors and mechanisms, named by the map's events.
        raw_names = {r.get("Name") for r in raw.values()}
        mechanisms: list[tuple[float, float, float, dict]] = []
        perception_hints: list[tuple[float, float, float]] = []
        for door in state["doors"]:
            xs, ys, zs = door.get("x_offsets") or [], door.get("y_offsets") or [], door.get("z_offsets") or []
            if not xs:
                continue
            name = door_names.get(door["door_id"], "Door")
            kind = door_kind(name)
            if kind is None or name in raw_names:
                continue
            centre = (sum(xs) / len(xs), sum(ys) / len(ys), min(zs))
            poi = add(kind, *centre, pretty_name(name),
                      {"lever": "mechanism", "secret": "hidden door", "trap": "trap", "door": ""}[kind])
            mechanisms.append((*centre, poi))

        # Raw DAT objects the scene does not list.
        for index, obj in sorted(raw.items()):
            world = obj.get("world")
            if not world:
                continue
            cls, name = obj["cls"], obj.get("Name", obj["cls"])
            if cls in ("Switch", "Button"):
                poi = add("secret" if "hidden" in name.lower() else "lever", *world, pretty_name(name),
                          "hidden button" if "hidden" in name.lower() else "switch")
                mechanisms.append((*world, poi))
            elif cls == "PerceptionBrush":
                perception_hints.append(world)
            elif cls == "Teleporter":
                destination = obj.get("TeleportDestination")
                if destination:
                    add("teleporter", *world, pretty_name(name), f"to {pretty_name(destination)}")
            elif cls in ("WellMMIX", "Cauldron", "Cookpot", "Clover"):
                label = {"WellMMIX": "Well", "Cauldron": "Cauldron", "Cookpot": "Cook pot", "Clover": "Clover"}[cls]
                add("bonus", *world, label, bonus_texts.get(index, ""))
            elif cls == "StatStone":
                add("bonus", *world, "Stat stone", "")
            elif cls == "Barrel":
                add("bonus", *world, "Stat barrel", "random colour: red Might, blue Magic, green Endurance, "
                    "yellow Accuracy, purple Speed, white Luck")
            elif cls == "ScriptObject" and name == "PromoTrigger":
                for promotion in promotions:
                    if promotion.get("map") == map_id:
                        add("promoter", *world, f"{promotion['to']} promotion", promotion.get("note", ""),
                            promo=promotion["to"])
            elif cls in ("Shooter", "DamageBrush", "PropDamager"):
                poi = add("trap", *world, pretty_name(name), {"Shooter": "shooter", "DamageBrush": "damage zone",
                                                               "PropDamager": "spikes"}[cls])
                mechanisms.append((*world, poi))

        # MM9's PerceptionBrushes glow for a party with enough Perception over something to use: in towns nearly
        # always an openable door. A glow on a door says nothing new; on a trap, lever or secret it is noted there;
        # a glow on nothing we mark stays a hint of its own.
        for x, y, z in perception_hints:
            near = min(mechanisms, key=lambda m: (m[0] - x) ** 2 + (m[1] - y) ** 2, default=None)
            if near is not None and (near[0] - x) ** 2 + (near[1] - y) ** 2 < HINT_RADIUS ** 2:
                poi = near[3]
                if poi["t"] != "door" and "Perception" not in poi.get("d", ""):
                    poi["d"] = (poi.get("d", "") + "; " if poi.get("d") else "") + "Perception reveals it"
                continue
            add("hint", x, y, z, "Perception hint", "glows for a party with enough Perception: something to find "
                "or use here")

        # Exits.
        for row in transitions:
            if row["SourceMapFile"] != f"{map_id}.blv":
                continue
            dest = row["DestinationMapFile"][:-4]
            days = to_int(row["TravelDays"])
            centre = raw.get(to_int(row["SourceObjectIndex"]), {}).get("world") or (
                float(row["CenterX"]), float(row["CenterY"]), float(row["CenterZ"]))
            add("exit", *centre,
                "To " + names.get(dest, dest), f"{days} day(s) travel" if days > 0 else "", map=dest)

        # Quest steps: the map's handlers that check or give quest keys or quest items, at their DAT object.
        by_rude = {p["rude"]: p for p in pois if "rude" in p}
        # NPCs the scripts talk through that are props, not actors, in the rebuilt map (Jarl Bjarni in Sturmford).
        for handler in handlers_by_map[map_id]:
            rude = handler["rude"]
            if rude is None or rude in by_rude:
                continue
            name = next((n for n in handler["names"] if n.lower() in positions), None)
            if name is None:
                continue
            label = config.get("npc_names", {}).get(rude) or pretty_name(name)
            if re.match(r"(RUDEProp|Commoner|Shopkeeper|Town|Prop)", name):
                label = "Townsperson"
            poi = add("quest", *positions[name.lower()], label, "", poi_id=f"r{rude}")
            poi["rude"] = rude
            by_rude[rude] = poi
            actor_lookup[(map_id, name_index[name.lower()])] = poi
            rude_locations[rude].append((map_id, poi["id"]))
        objectives: dict[str, dict] = {}
        for handler in handlers_by_map[map_id]:
            linked = set().union(*(key_quests.get(k, set()) for k in handler["keys"]),
                                 *(item_quests.get(raw, set()) for raw in handler["gives"] + handler["needs"]))
            if not linked:
                continue
            if handler["rude"] is not None:
                npc = by_rude.get(handler["rude"])
                if npc is not None:
                    npc["quests"] = sorted(set(npc.get("quests", [])) | linked)
                    if npc["t"] == "npc":
                        npc["t"] = "quest"
                continue
            name = next((n for n in handler["names"] if n.lower() in positions), None)
            if name is None:
                unplaced_steps.append({"map": map_id, "label": handler["label"] or "Event", "quests": sorted(linked)})
                continue
            parts = []
            needs = [item_name(r) for r in handler["needs"] if r in raw_items]
            gives = [item_name(r) for r in handler["gives"] if r in raw_items]
            if needs:
                parts.append("needs " + ", ".join(dict.fromkeys(needs)))
            if gives:
                parts.append("gives " + ", ".join(dict.fromkeys(gives)))
            if handler["xp"]:
                parts.append(f"{handler['xp']:,} XP")
            x, y, z = positions[name.lower()]
            # A step scripted on an NPC belongs to that NPC's marker: the same MM9 object, or an NPC right beside it.
            npc = actor_lookup.get((map_id, name_index.get(name.lower(), -1))) or next(
                (p for p in pois if "rude" in p and abs(p["x_"] - x) < NPC_RADIUS and abs(p["y_"] - y) < NPC_RADIUS),
                None)
            if npc is not None:
                npc["quests"] = sorted(set(npc.get("quests", [])) | linked)
                if parts and "; ".join(parts) not in npc.get("d", ""):
                    npc["d"] = "; ".join(filter(None, [npc.get("d", ""), "; ".join(parts)]))
                if npc["t"] == "npc":
                    npc["t"] = "quest"
                continue
            poi = objectives.get(name.lower())
            if poi is None:
                label = handler["label"]
                if not label or label.islower() or label.startswith("Trigger") or label == "Event":
                    label = "Quest event" if name.lower().startswith(("trigger", "killed")) or not label \
                        else pretty_name(label).capitalize()
                poi = add("objective", x, y, z, label, "; ".join(parts))
                objectives[name.lower()] = poi
            elif parts and "; ".join(parts) not in poi.get("d", ""):
                poi["d"] = "; ".join(filter(None, [poi.get("d", ""), "; ".join(parts)]))
            poi["quests"] = sorted(set(poi.get("quests", [])) | linked)

        # Hand-listed quest props and puzzle pieces (extra_pois.yml), at their DAT objects.
        for entry in extra["points"]:
            if entry["map"] != map_id:
                continue
            # objects by DAT name, or by DAT index (an int)
            found = [shift(by_index[o]) if isinstance(o, int) else positions[o.lower()] for o in entry["objects"]
                     if (o in by_index if isinstance(o, int) else o.lower() in positions)]
            if not found:
                print(f"extra_pois: {map_id} {entry['label']}: none of {entry['objects']} found", file=sys.stderr)
                continue
            centre = tuple(sum(c[i] for c in found) / len(found) for i in range(3))
            # a map event on the same objects already made the point (its label): the entry places and describes it
            poi = next((p for p in objectives.values() if p["n"] == entry["label"]), None)
            if poi is not None:
                pois.remove(poi)
                entry = {**entry, "quests": sorted(set(poi.get("quests", [])) | set(entry.get("quests", [])))}
            add(entry["type"], *centre, entry["label"], entry.get("detail", ""), quests=entry.get("quests", []))
        for rename in extra["renames"]:
            if rename["map"] == map_id:
                for poi in list(pois):
                    if poi["id"] == rename.get("id") or ("match" in rename and re.search(rename["match"], poi["n"])):
                        if rename.get("drop"):
                            pois.remove(poi)
                            continue
                        if rename.get("label"):
                            poi["n"] = rename["label"]
                        if rename.get("quests"):
                            poi["quests"] = sorted(set(poi.get("quests", [])) | set(rename["quests"]))
                            if poi["t"] == "npc":
                                poi["t"] = "quest"

        for poi in pois:
            del poi["x_"], poi["y_"]
            if poi["t"] not in poi_types:
                raise SystemExit(f"unknown POI type {poi['t']}")
        maps_out.append({
            "id": map_id,
            "name": names.get(map_id, pretty_name(map_id)),
            "kind": config["map_kinds"].get(map_id, "dungeon"),
            "region": region_of.get(map_id, ""),
            **presentation,
            "pois": pois,
        })
        print(f"{map_id}: {len(pois)} points", file=sys.stderr)

    # Quests: givers and turn-ins from the bound RUDE interactions.
    for interaction in interactions:
        bound = []
        for binding in interaction.get("bindings", []):
            # by the MM9 object: the rebuilt scenes renumbered their actors
            poi = actor_lookup.get((binding["map_id"], binding["source_object_index"]))
            if poi:
                bound.append({"map": binding["map_id"], "poi": poi["id"], "name": poi["n"]})
        for qbit in interaction.get("journal_entries", []):
            key = quest_of_qbit.get(qbit)
            if not key:
                continue
            target = quests[key]["givers" if "offer" in interaction["roles"] else "handoffs"]
            for entry in bound:
                if entry not in target:
                    target.append(entry)
                poi = next(p for m in maps_out if m["id"] == entry["map"] for p in m["pois"] if p["id"] == entry["poi"])
                poi.setdefault("quests", [])
                if key not in poi["quests"]:
                    poi["quests"].append(key)
                if poi["t"] == "npc":
                    poi["t"] = "quest"

    add_rude_givers(quests, quest_of_qbit, rude_locations, maps_out)
    for quest in quests.values():
        quest["steps"] = []
    for map_data in maps_out:
        for poi in map_data["pois"]:
            if poi["t"] in ("objective", "chest", "loot") and poi.get("quests"):
                for key in poi["quests"]:
                    quests[key]["steps"].append({"map": map_data["id"], "poi": poi["id"], "name": poi["n"]})
    for step in unplaced_steps:
        for key in step["quests"]:
            entry = {"map": step["map"], "poi": "", "name": step["label"]}
            if entry not in quests[key]["steps"]:
                quests[key]["steps"].append(entry)
    classify_quests(quests, config)
    attach_shots(maps_out, out, args.skip_images, set(config.get("shot_exclude", [])))
    for promotion in promotions:
        promotion["at"] = [{"map": m["id"], "poi": p["id"], "name": p["n"]} for m in maps_out for p in m["pois"]
                           if p["t"] == "promoter" and p.get("promo") == promotion["to"]]

    story = load_story(quests, maps_out, config)
    quest_levels(quests, story[1], maps_out, monsters, config)
    data = {
        "generated": "",
        "poiTypes": poi_types,
        "regions": config["regions"],
        "chapters": config["chapters"],
        "maps": maps_out,
        "quests": sorted(quests.values(), key=lambda q: (q["cat"], q.get("chapter", 99), q["stages"][0]["qbit"])),
        "teachers": build_teachers(trainers, services, vendors, rude_locations, names)
        + build_racial_teachers(racial, services, trainers, rude_locations, npc_names),
        "vendors": build_vendors(vendors, rude_locations, stock, tier_of),
        "spellbooks": build_spellbooks(stock),
        "services": build_services(services, rude_locations),
        "promotions": promotions,
        **dict(zip(("story", "walkthroughs"), story)),
        "faq": load_faq(),
        "travel": build_travel(transitions, routes, names, rude_locations),
        "monsters": attach_portraits(build_monsters(monsters, monster_maps), out, args.skip_images,
                                     set(config.get("monster_portrait_exclude", []))),
        **build_items(out, args.skip_images),
    }

    (out / "data").mkdir(exist_ok=True)
    (out / "data/guide.js").write_text("window.GUIDE = " + json.dumps(data, separators=(",", ":")) + ";\n")
    for path in WEB.iterdir():
        if path.is_file() and path.name != "page.html":
            shutil.copy2(path, out / path.name)
    # page.html is the body of the page: published as is (the artifact host adds the document skeleton) and wrapped
    # into index.html for local viewing.
    page = (WEB / "page.html").read_text(encoding="utf-8")
    shutil.copy2(WEB / "page.html", out / "page.html")
    (out / "index.html").write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                                    '<meta name="viewport" content="width=device-width, initial-scale=1, '
                                    'viewport-fit=cover">\n</head>\n<body>\n' + page + "</body>\n</html>\n",
                                    encoding="utf-8")
    if (STORY / "img").is_dir():
        shutil.copytree(STORY / "img", out / "img/story", dirs_exist_ok=True)
    if (FAQ / "img").is_dir():
        shutil.copytree(FAQ / "img", out / "img/faq", dirs_exist_ok=True)
    shutil.rmtree(out / "img/items", ignore_errors=True)
    size = (out / "data/guide.js").stat().st_size
    print(f"wrote {out} (guide.js {size // 1024} KB, {sum(len(m['pois']) for m in maps_out)} points)",
          file=sys.stderr)
    return 0


SHOTS = ROOT / "output/mm9_site_shots"


def shot_is_usable(image: Image.Image, npc: bool) -> bool:
    """Reject captures that missed the scene: a flat frame, or for an NPC a frame whose middle is open sky (the camera
    landed outside the geometry)."""
    width, height = image.size
    middle = image.crop((int(width * .3), int(height * .3), int(width * .7), int(height * .72))).convert("RGB")
    middle = middle.resize((80, 42))
    raw = middle.tobytes()
    pixels = [tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)]
    grey = [sum(p) / 3 for p in pixels]
    mean = sum(grey) / len(grey)
    spread = (sum((g - mean) ** 2 for g in grey) / len(grey)) ** .5
    if spread < (10 if npc else 3):
        return False
    if npc:
        sky = sum(1 for r, g, b in pixels if b > 150 and b > r + 25 and b >= g)
        if sky > len(pixels) * .45:
            return False
    return True


def attach_shots(maps_out: list[dict], out: Path, skip_images: bool, exclude: set[str]) -> None:
    """In-game captures from capture_shots.py: the map's arrival view and its key NPCs, as img/shots/*.webp."""
    target = out / "img/shots"
    target.mkdir(parents=True, exist_ok=True)
    rejected = []
    for map_data in maps_out:
        folder = SHOTS / map_data["id"]
        if not folder.is_dir():
            continue
        pois = {p["id"]: p for p in map_data["pois"]}
        for png in sorted(folder.glob("*.png")):
            name = png.stem.split("-", 1)[1]
            rel = f"img/shots/{map_data['id']}-{name}.webp"
            if f"{map_data['id']}-{name}" in exclude:
                (out / rel).unlink(missing_ok=True)
                continue
            if not (skip_images and (out / rel).exists()):
                image = Image.open(png).convert("RGB")
                if not shot_is_usable(image, name != "arrival"):
                    rejected.append(f"{map_data['id']}/{png.name}")
                    (out / rel).unlink(missing_ok=True)
                    continue
                image.thumbnail((1280, 1280))
                image.save(out / rel, "WEBP", quality=80, method=5)
            if not (out / rel).exists():
                continue
            if name == "arrival":
                map_data["shot"] = rel
            elif name in pois:
                pois[name]["shot"] = rel
    if rejected:
        print("rejected shots: " + ", ".join(rejected), file=sys.stderr)


STORY = Path(__file__).resolve().parent / "story"
FAQ = Path(__file__).resolve().parent / "faq"


def load_faq() -> list[dict]:
    """The hand-written questions and answers (faq/faq.yml); figures from faq/img (faq_figures.py draws them)."""
    entries = yaml.safe_load((FAQ / "faq.yml").read_text())["questions"]
    for entry in entries:
        for figure in entry.get("figures", []):
            if not (FAQ / "img" / figure["img"]).is_file():
                raise SystemExit(f"faq {entry['id']}: missing figure faq/img/{figure['img']}")
            figure["img"] = f"img/faq/{figure['img']}"
    return entries


def load_story(quests: dict[str, dict], maps_out: list[dict], config: dict) -> tuple[list[dict], dict]:
    """The hand-written walkthroughs (story/*.yml, see story/BRIEF.md and BRIEF_SIDE.md): main-story chapters merged
    by id with sections in file order, and a walkthrough entry per quest (chapter entries and flat `quests:` lists).
    Quest ids, maps, marker types, NPCs and points are checked against the generated data and resolved to points."""
    maps = {m["id"]: m for m in maps_out}
    types = set(config["poi_types"])

    def find(ref: dict, where: str) -> dict | None:
        name = ref.get("npc") or ref.get("name")
        poi = next((p for p in maps.get(ref["map"], {}).get("pois", []) if p["n"] == name), None)
        if poi is None:
            print(f"story {where}: {ref} not found", file=sys.stderr)
            return None
        return {"map": ref["map"], "poi": poi["id"], "name": poi["n"]}

    def check(entry: dict, where: str, giver: dict | None) -> None:
        if entry["quest"] not in quests:
            raise SystemExit(f"story {where}: unknown quest {entry['quest']}")
        for view in entry.get("maps", []):
            if view["map"] not in maps:
                raise SystemExit(f"story {where}: unknown map {view['map']}")
            unknown = set(view.get("show", [])) - types
            if unknown:
                raise SystemExit(f"story {where}: unknown marker types {sorted(unknown)}")
        for figure in entry.get("figures", []):
            # story/img/<name>: a picture beside the steps (story_figures.py draws the annotated ones)
            if not (STORY / "img" / figure["img"]).is_file():
                raise SystemExit(f"story {where}: missing figure story/img/{figure['img']}")
            figure["img"] = f"img/story/{figure['img']}"
        for key in ("from", "to"):
            if entry.get(key):
                entry[key] = find(entry[key], where)
        if giver and not entry.get("from"):
            entry["from"] = giver
        entry["points"] = [ref for ref in (find(r, where) for r in entry.get("points", [])) if ref]

    chapters: dict[int, dict] = {}
    walkthroughs: dict[str, dict] = {}
    order = ["prologue_ch1a.yml", "ch1b.yml", "ch1c_ch2.yml", "ch3_5.yml"]
    files = sorted(STORY.glob("*.yml"), key=lambda path: (order.index(path.name) if path.name in order else 99, path.name))
    for path in files:
        data = yaml.safe_load(path.read_text()) or {}
        for chapter in data.get("chapters", []):
            merged = chapters.setdefault(chapter["id"], {"id": chapter["id"], "title": chapter.get("title", ""),
                                                         "intro": "", "sections": []})
            merged["intro"] = merged["intro"] or chapter.get("intro", "")
            merged["title"] = merged["title"] or chapter.get("title", "")
            for section in chapter.get("sections", []):
                giver = section.get("giver")
                if giver:
                    resolved = find(giver, path.name)
                    if resolved is None:
                        section.pop("giver")
                    else:
                        giver["poi"] = resolved["poi"]
                for entry in section.get("quests", []):
                    check(entry, path.name, find(giver, path.name) if section.get("giver") else None)
                    walkthroughs[entry["quest"]] = entry
                merged["sections"].append(section)
        for entry in data.get("quests", []):
            check(entry, path.name, None)
            walkthroughs[entry["quest"]] = entry
    return [chapters[k] for k in sorted(chapters)], walkthroughs


def quest_levels(quests: dict, walkthroughs: dict, maps_out: list[dict], monsters: dict, config: dict) -> None:
    """A recommended party level per quest: the hardest map its work is on, rated by the median level of its ordinary
    (family) monsters, with that map's 10th-90th percentile range. The maps are the walkthrough's own when it names
    any, else the quest's points; towns count only when nothing else does. `quest_level_maps` in the config overrides."""
    by_map = {}
    for map_data in maps_out:
        levels = [monsters[p["mon"]]["level"] for p in map_data["pois"]
                  if p["t"] == "monster" and p.get("mon") in monsters and monsters[p["mon"]].get("family")]
        by_map[map_data["id"]] = sorted(levels)
    kinds = {m["id"]: m["kind"] for m in maps_out}
    tagged: dict[str, set] = defaultdict(set)
    for map_data in maps_out:
        for p in map_data["pois"]:
            for key in p.get("quests", []):
                tagged[key].add(map_data["id"])
    pick = lambda levels, q: levels[min(len(levels) - 1, int(q * len(levels)))]  # noqa: E731
    for key, quest in quests.items():
        entry = walkthroughs.get(key, {})
        overrides = config.get("quest_level_maps", {})
        if key in overrides:
            work = set(overrides[key])
        else:
            work = {v["map"] for v in entry.get("maps", [])} or (set(tagged[key]) | {s["map"] for s in quest["steps"]})
        rated = [m for m in work if len(by_map.get(m, [])) >= 3]
        fights = [m for m in rated if kinds.get(m) != "city"] or rated
        if not fights:
            continue
        hardest = max(fights, key=lambda m: pick(by_map[m], 0.5))
        levels = by_map[hardest]
        quest["level"] = {"rec": pick(levels, 0.5), "lo": pick(levels, 0.1), "hi": pick(levels, 0.9), "maps": [hardest]}


def classify_quests(quests: dict[str, dict], config: dict) -> None:
    overrides = config.get("quest_categories", {})
    chapters = config["chapters"]
    for quest in quests.values():
        first = quest["stages"][0]["qbit"]
        quest["stages"].sort(key=lambda s: s["qbit"])
        category = overrides.get(quest["id"])
        if category is None:
            category = "main" if first < config["main_story_below_qbit"] else "side"
        quest["cat"] = category
        if category == "main":
            for chapter in chapters:
                if chapter["from"] <= first <= chapter["to"]:
                    quest["chapter"] = chapter["id"]
        for promotion in config["promotions"]:
            if quest["id"] in promotion["quests"]:
                quest["cat"] = "promotion"
                quest["promo"] = promotion["to"]
    known = set(quests)
    for promotion in config["promotions"]:
        for key in promotion["quests"]:
            if key not in known:
                raise SystemExit(f"promotion {promotion['to']}: no quest note headed {key}")


def locations(rude: int, rude_locations: dict) -> list[dict]:
    return [{"map": m, "poi": p} for m, p in rude_locations.get(rude, [])]


def build_teachers(trainers, services, vendors, rude_locations, names) -> list[dict]:
    """The MM9 trainers' Expert to Grandmaster lessons, then the Learn lessons of the venues (`learn_skills`): the
    services' (taverns, temples, training halls) and the shops' (vendors.txt), each with its venue type."""
    out = []
    for row in trainers:
        rude = to_int(row["RudeId"])
        out.append({
            "name": row["SourceDisplayNames"],
            "skill": row["Mm9Skill"],
            "skills": ", ".join(pretty_name(skill) for skill in row["SharedSkills"].split("|")),
            "mastery": row["TargetMastery"],
            "rank": to_int(row["RequiredSkillRank"]),
            "gold": to_int(row["RequiredGold"]),
            "region": row["ExpectedRegion"],
            "gated": bool(row["RequiredRawKeys"]),
            "at": locations(rude, rude_locations),
        })
    venues = [(s, to_int(s["source_service_id"]), s["service_type"]) for s in services]
    venues += [(v, to_int(v["source_vendor_id"]), v["source_type"]) for v in vendors]
    for venue, rude, kind in venues:
        for skill in (s for s in venue.get("learn_skills", "").split("|") if s):
            out.append({
                "name": venue["name"],
                "skill": pretty_name(skill),
                "skills": pretty_name(skill),
                "mastery": "Learn",
                "rank": 0,
                "gold": 0,
                "region": venue["location"],
                "gated": False,
                "venue": kind,
                "at": locations(rude, rude_locations),
            })
    return out


# MM6-MM8 spell schools by spell number (eleven each), and the spellbooks' masteries (mm9_spellbooks.py).
SCHOOLS = ("Fire", "Air", "Water", "Earth", "Spirit", "Mind", "Body", "Light", "Dark")
BOOK_MASTERIES = ("Normal", "Expert", "Master", "Grandmaster")
# The racial lessons' skill rank by mastery, as the MM9 trainers' (skill_trainers.txt RequiredSkillRank).
MASTERY_RANK = {"Expert": 4, "Master": 7, "Grandmaster": 10}


def load_stock() -> dict[int, dict]:
    """The shops' authored stock by vendor id: generate_mm9_vendors.py's audit (state/vendor_stock_audit.yml, JSON),
    each shelf ("lane") with its treasure level and its slots by restock page. A shop shows one page per restock."""
    audit = json.loads((WORLD / "state/vendor_stock_audit.yml").read_text())
    return {v["vendor_id"]: v for v in audit["vendors"]}


def stock_summary(shop: dict, tier_of: dict[int, int]) -> dict:
    """What a shop really stocks: the treasure level of its two shelves (equipment shops; books and libraries keep
    MM9's lists), the item tiers on them, the share of enchanted items and its restock pages."""
    lanes = shop["lanes"]
    slots = [slot for lane in lanes.values() for slot in lane["slots"]]
    tiers = sorted({tier_of.get(slot["item_id"], 0) for slot in slots} - {0})
    enchanted = sum(1 for slot in slots
                    if slot["runtime_mapping"]["standard_enchant_id"] or slot["runtime_mapping"]["special_enchant_id"])
    levels = [lanes[lane].get("stock_treasure_level") for lane in ("standard", "special") if lane in lanes]
    return {
        "treasure": levels if all(levels) else [],
        "tiers": [tiers[0], tiers[-1]] if tiers else [],
        "enchanted": round(100 * enchanted / len(slots)) if slots else 0,
        "pages": max(lane["page_count"] for lane in lanes.values()),
        "perPage": round(len(slots) / max(lane["page_count"] for lane in lanes.values())),
    }


def build_vendors(vendors, rude_locations, stock: dict[int, dict], tier_of: dict[int, int]) -> list[dict]:
    return [{
        "id": to_int(v["vendor_id"]),
        "name": v["name"],
        "region": v["location"],
        "type": v["source_type"],
        "sells": v["merchandise"],
        "price": float(v["merchant_base"]),
        "restock": to_int(v["restock_days"]),
        "identify": v["can_identify"] == "1",
        "repair": v["can_repair"] == "1",
        **stock_summary(stock[to_int(v["vendor_id"])], tier_of),
        "at": locations(to_int(v["source_vendor_id"]), rude_locations),
    } for v in vendors]


def build_spellbooks(stock: dict[int, dict]) -> list[dict]:
    """Every spellbook with the shops that sell it: on how many of each shop's restock pages it is (all of them: on
    every restock)."""
    books = {}
    for row in read_tsv(WORLD / "data_tables/items.txt"):
        if row["Equip Stat"] != "Book" or not row["Mod1"].startswith("S"):
            continue
        spell = to_int(row["Mod1"][1:])
        mastery = row.get("x_mm9_import_status", "").removeprefix("generated_spellbook:").capitalize()
        books[to_int(row["Item #"])] = {
            "id": to_int(row["Item #"]),
            "name": row["Name"],
            "spell": spell,
            "school": SCHOOLS[(spell - 1) // 11],
            "mastery": mastery if mastery in BOOK_MASTERIES else "",
            "value": to_int(row["Value"]),
            "shops": [],
        }
    for shop in stock.values():
        if shop["profile"] != "Spellbook":
            continue
        pages: dict[int, set[int]] = defaultdict(set)
        for lane in shop["lanes"].values():
            for slot in lane["slots"]:
                pages[slot["item_id"]].add(slot["page"])
        total = max(lane["page_count"] for lane in shop["lanes"].values())
        for item_id, item_pages in pages.items():
            if item_id in books:
                books[item_id]["shops"].append({"id": shop["vendor_id"], "pages": len(item_pages), "of": total})
    return sorted(books.values(), key=lambda book: book["spell"])


def load_npc_names() -> dict[int, str]:
    """The RUDE dialogues' NPC names (dialogue/rude/NPCNAME.rude: id, quoted name)."""
    with (WORLD / "dialogue/rude/NPCNAME.rude").open(encoding="utf-8", errors="replace", newline="") as handle:
        return {to_int(row[0]): row[1].strip() for row in csv.reader(handle) if len(row) > 1 and row[0].isdigit()}


def load_racial_trainers() -> dict:
    """The racial-ability trainers (dialogue/racial_trainers.yml): every training hall's keeper and a Yorwick
    grandmaster teach each member their own race's ability, up to the trainer's mastery."""
    path = WORLD / "dialogue/racial_trainers.yml"
    return yaml.safe_load(path.read_text()) if path.exists() else {"skills": [], "trainers": []}


def build_racial_teachers(racial: dict, services, trainers, rude_locations, npc_names) -> list[dict]:
    region_by_rude = {to_int(s["source_service_id"]): s["location"] for s in services}
    region_by_rude.update({to_int(t["RudeId"]): t["ExpectedRegion"] for t in trainers})
    skills = ", ".join(pretty_name(skill) for skill in racial["skills"])
    out = []
    for trainer in racial["trainers"]:
        rude = trainer["rude"]
        top = list(MASTERY_RANK).index(trainer["mastery"]) + 1
        for mastery in list(MASTERY_RANK)[:top]:
            out.append({
                "name": npc_names.get(rude, f"NPC {rude}"),
                "skill": "Racial ability",
                "skills": skills,
                "mastery": mastery,
                "rank": MASTERY_RANK[mastery],
                "gold": 0,
                "region": region_by_rude.get(rude, ""),
                "gated": False,
                "racial": True,
                "at": locations(rude, rude_locations),
            })
    return out


def build_services(services, rude_locations) -> list[dict]:
    return [{
        "id": to_int(s["service_id"]),
        "name": s["name"],
        "region": s["location"],
        "type": s["service_type"],
        "trainMax": to_int(s["training_max_level"]),
        "learn": [pretty_name(x) for x in s.get("learn_skills", "").split("|") if x],
        "at": locations(to_int(s["source_service_id"]), rude_locations),
    } for s in services]


def build_travel(transitions, routes, names, rude_locations) -> dict:
    links = []
    for row in transitions:
        source = row["SourceMapFile"][:-4]
        dest = row["DestinationMapFile"][:-4]
        days = to_int(row["TravelDays"])
        links.append({"from": source, "to": dest, "days": max(days, 0)})
    unique = {}
    for link in links:
        key = (link["from"], link["to"])
        if key not in unique or link["days"] < unique[key]["days"]:
            unique[key] = link
    schedules = []
    for row in routes:
        rude = to_int(row["DockNpcId"])
        located = locations(rude, rude_locations)
        schedules.append({
            "vessel": row["DockName"],
            "kind": row["ServiceClassification"],
            "from": located[0]["map"] if located else "",
            "at": located,
            "to": row["DestinationMapFile"][:-4],
            "day": row["AvailableWeekday"],
            "days": to_int(row["TravelDays"]),
            "price": to_int(row["BasePrice"]),
            "gated": bool(row["RequiredRawKeys"]),
        })
    return {"links": list(unique.values()), "schedules": schedules}


PORTRAITS = ROOT / "output/mm9_site_monsters"


def attach_portraits(monster_list: list[dict], out: Path, skip_images: bool, exclude: set[int]) -> list[dict]:
    """capture_monsters.py's arena portraits as img/monsters/<id>.webp."""
    target = out / "img/monsters"
    target.mkdir(parents=True, exist_ok=True)
    for monster in monster_list:
        source = PORTRAITS / f"{monster['id']}.png"
        rel = f"img/monsters/{monster['id']}.webp"
        if monster["id"] in exclude or not source.exists():
            (out / rel).unlink(missing_ok=True)
            continue
        if not (skip_images and (out / rel).exists()):
            image = Image.open(source).convert("RGB")
            image.thumbnail((640, 640))
            image.save(out / rel, "WEBP", quality=82, method=5)
        monster["img"] = rel
    return monster_list


def build_monsters(monsters: dict[int, dict], monster_maps: dict[int, Counter]) -> list[dict]:
    out = []
    for monster_id, counts in monster_maps.items():
        monster = dict(monsters[monster_id])
        if all(not re.search(r"[1-9]", a["dmg"]) for a in monster["attacks"]) and not monster["spells"]:
            continue  # livestock and fish: no damage, nothing to fight
        monster["maps"] = [{"map": m, "count": c} for m, c in counts.most_common()]
        out.append(monster)
    return sorted(out, key=lambda m: (m["level"], m["name"]))


# ---------------------------------------------------------------------------------------------------------------------
# Items


ITEM_CATEGORIES = [
    ("artifacts", "Artifacts and relics"),
    ("sets", "Set items"),
    ("weapons", "Weapons"),
    ("armor", "Body armor"),
    ("shields", "Shields"),
    ("helms", "Helms"),
    ("gauntlets", "Gauntlets"),
    ("boots", "Boots"),
    ("belts", "Belts"),
    ("rings", "Rings"),
    ("amulets", "Amulets"),
    ("books", "Skill books"),
    ("quest", "Quest items"),
    ("readables", "Letters and books"),
    ("misc", "Other"),
]
EQUIP_CATEGORY = {
    "Weapon": "weapons", "Weapon2": "weapons", "Weapon1or2": "weapons", "Missile": "weapons", "Armor": "armor",
    "Shield": "shields", "Helm": "helms", "Gauntlets": "gauntlets", "Boots": "boots", "Belt": "belts",
    "Ring": "rings", "Amulet": "amulets", "LearnSkill": "books",
}
EFFECT_LABELS = {
    "might": "Might", "intellect": "Intellect", "personality": "Personality", "endurance": "Endurance",
    "speed": "Speed", "accuracy": "Accuracy", "luck": "Luck", "max_health": "Hit points", "max_sp": "Spell points",
    "armor_class": "Armor class", "melee_attack": "Melee attack", "ranged_attack": "Ranged attack",
    "melee_damage": "Melee damage", "ranged_damage": "Ranged damage", "all_resistances": "All resistances",
    "fire_resistance": "Fire res.", "air_resistance": "Air res.", "water_resistance": "Water res.",
    "earth_resistance": "Earth res.", "mind_resistance": "Mind res.", "body_resistance": "Body res.",
    "spirit_resistance": "Spirit res.", "weapon_damage": "Weapon damage",
    "recovery_reduction_ticks": "Recovery time -", "health_regen_per_second": "HP regen/s",
    "spell_regen_per_second": "SP regen/s",
}


def effect_lines(row: dict) -> list[str]:
    lines = []
    for key, label in EFFECT_LABELS.items():
        value = (row.get(key) or "").strip()
        if value and value != "0":
            sign = "" if value.startswith("-") or label.endswith("-") else "+"
            lines.append(f"{label}{'' if label.endswith('-') else ' '}{sign}{value}")
    for bonus in (row.get("skill_bonuses") or "").split("|"):
        if bonus:
            skill, _, amount = bonus.partition(":")
            lines.append(f"{pretty_name(skill)} +{amount}")
    flags = (row.get("effect_flags") or "").strip()
    if flags:
        lines.extend(pretty_name(f) for f in flags.split("|") if f)
    return lines


def build_items(out: Path, skip_images: bool) -> dict:
    rows = read_tsv(WORLD / "data_tables/items.txt")
    effects = {to_int(r["item_id"]): r for r in read_tsv(WORLD / "data_tables/item_effects.txt")}
    sets = read_tsv(WORLD / "data_tables/item_sets.txt")
    icon_dir = WORLD / "icons_x2"
    icons: list[Path] = []
    items = []
    for row in rows:
        item_id = to_int(row["Item #"])
        equip = row["Equip Stat"]
        material = row["material"]
        flags = row.get("content_flags", "")
        if material in ("Artifact", "Relic"):
            category = "artifacts"
        elif row.get("set_id"):
            category = "sets"
        elif equip in EQUIP_CATEGORY:
            category = EQUIP_CATEGORY[equip]
        elif "Readable" in flags:
            category = "readables"
        elif "Quest" in flags:
            category = "quest"
        else:
            category = "misc"
        icon = icon_dir / f"{row['Pic File']}.png"
        icon_cell = -1
        if icon.exists():
            icon_cell = len(icons)
            icons.append(icon)
        item = {
            "id": item_id,
            "name": row["Name"],
            "cat": category,
            "equip": equip,
            "skill": row["Skill Group"] if row["Skill Group"] != "Misc" else "",
            "mod1": row["Mod1"] if row["Mod1"] != "0" else "",
            "mod2": row["Mod2"] if row["Mod2"] != "0" else "",
            "value": to_int(row["Value"]),
            "tier": to_int(row.get("normalized_tier", "0")),
            "rarity": material if material in ("Artifact", "Relic", "Special") else "",
            "set": row.get("set_id", "").split("/")[-1],
            "desc": clean_quoted(row.get("Notes", "")),
            "flags": [f for f in flags.split("|") if f],
            "classes": row.get("x_mm9_source_restrictions", ""),
            "icon": icon_cell,
            "fx": effect_lines(effects.get(item_id, {})),
        }
        items.append(item)
    set_list = []
    for row in sets:
        set_id = row["set_id"].split("/")[-1]
        set_list.append({
            "id": set_id,
            "name": set_id.capitalize(),
            "pieces": to_int(row["required_piece_count"]),
            "fx": effect_lines(row),
            "items": [i["id"] for i in items if i["set"] == set_id],
        })
    if not skip_images or not (out / "img/items.webp").exists():
        write_icon_atlas(icons, out / "img/items.webp")
    return {
        "iconAtlas": {"src": "img/items.webp", "cell": ICON_CELL, "cols": ICON_COLUMNS,
                      "rows": (len(icons) + ICON_COLUMNS - 1) // ICON_COLUMNS},
        "itemCategories": [{"id": c, "name": n} for c, n in ITEM_CATEGORIES],
        "items": items,
        "sets": set_list,
        "enchants": load_enchants(),
    }


ICON_CELL = 80
ICON_COLUMNS = 20


def write_icon_atlas(icons: list[Path], path: Path) -> None:
    """All item icons in one image: each fitted into an ICON_CELL square, row-major, ICON_COLUMNS wide."""
    rows = (len(icons) + ICON_COLUMNS - 1) // ICON_COLUMNS
    atlas = Image.new("RGBA", (ICON_COLUMNS * ICON_CELL, max(rows, 1) * ICON_CELL), (0, 0, 0, 0))
    for index, icon_path in enumerate(icons):
        icon = Image.open(icon_path).convert("RGBA")
        icon.thumbnail((ICON_CELL - 4, ICON_CELL - 4), Image.LANCZOS)
        x = (index % ICON_COLUMNS) * ICON_CELL + (ICON_CELL - icon.width) // 2
        y = (index // ICON_COLUMNS) * ICON_CELL + (ICON_CELL - icon.height) // 2
        atlas.alpha_composite(icon, (x, y))
    path.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(path, "WEBP", quality=90, method=5)


def load_enchants() -> dict:
    standard = []
    rows = read_rows(ENGINE / "data_tables/standard_item_enchants.txt")
    slots = ["Armor", "Shield", "Helm", "Belt", "Cape", "Gauntlets", "Boots", "Ring", "Amulet"]
    for row in rows[3:]:
        if len(row) < 11 or not row[0].strip() or not row[1].strip():
            continue
        standard.append({"stat": row[0].strip(), "suffix": row[1].strip(),
                         "slots": [s for s, w in zip(slots, row[2:11]) if w.strip() not in ("", "0")]})
    special = []
    rows = read_rows(ENGINE / "data_tables/special_item_enchants.txt")
    slots = ["Weapon 1H", "Weapon 2H", "Missile", "Armor", "Shield", "Helm", "Belt", "Cape", "Gauntlets", "Boots",
             "Ring", "Amulet"]
    for row in rows[3:]:
        if len(row) < 17 or not row[0].strip() or not row[1].strip():
            continue
        special.append({"bonus": row[0].strip(), "name": row[1].strip(),
                        "slots": [s for s, w in zip(slots, row[2:14]) if w.strip() not in ("", "0")],
                        "value": row[14].strip(), "level": row[15].strip(), "desc": row[16].strip() if len(row) > 16
                        else ""})
    return {"standard": standard, "special": special}


if __name__ == "__main__":
    raise SystemExit(main())
