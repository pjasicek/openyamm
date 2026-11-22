#!/usr/bin/env python3
"""Build the Xeen guide website from the Xeen world package.

Reads assets_dev/worlds/xeen (maps and scenes, map events, the source files of towns, quests and monsters, the
generated data tables, journal maps, item icons) and writes a static site to output/xeen_site in the MM9 guide's
format: the same web front end (tools/mm9_site/web), the same `window.GUIDE` data shape and the MM9 generator's shared
parts (monsters, items, story and FAQ loaders, screenshots, portraits). Indoor maps get floor plans drawn from their
BLV geometry by tools/maw_site/dungeon_plans.py. See tools/xeen_site/README.md.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORLD = ROOT / "assets_dev/worlds/xeen"
ENGINE = ROOT / "assets_dev/engine"
SOURCE = WORLD / "source"
CONFIG = HERE / "site_config.yml"
STORY = HERE / "story"
FAQ = HERE / "faq"
SHOTS = ROOT / "output/xeen_site_shots"
PORTRAITS = ROOT / "output/xeen_site_monsters"
MM9_WEB = ROOT / "tools/mm9_site/web"

# The MM9 generator is the shared module (loaded by path: both scripts are called build_site.py).
_spec = importlib.util.spec_from_file_location("mm9_site_build", ROOT / "tools/mm9_site/build_site.py")
mm9 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mm9)

sys.path.insert(0, str(ROOT / "tools/maw_site"))
sys.path.insert(0, str(ROOT / "tools"))
import dungeon_plans  # noqa: E402
import teachers as maw_teachers  # noqa: E402
import trainer_places  # noqa: E402

# Both modules look maps up by world; the Xeen guide reads only the Xeen world.
dungeon_plans.WORLD_IDS = ("xeen",)
trainer_places.WORLD_IDS = ("xeen",)

read_tsv, read_rows, to_int, pretty_name = mm9.read_tsv, mm9.read_rows, mm9.to_int, mm9.pretty_name

# An outdoor journal map spans -32768..32768 in x and y, north up (MapPresentation defaults).
OUTDOOR_HALF = 32768
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
ACTS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
SCHOOLS = mm9.SCHOOLS
MASTERY_RANK = {"Expert": 4, "Master": 7, "Grandmaster": 10}
MASTERY_SLOT = {"Expert": 0, "Master": 1, "Grandmaster": 2}

HOUSE_KINDS = {
    "weapon_shop": ("vendor", "Weapon shop", "Weapon"), "armor_shop": ("vendor", "Armour shop", "Armor"),
    "magic_shop": ("vendor", "Magic shop", "Magic"), "alchemist": ("vendor", "Alchemist", "Alchemist"),
    "temple": ("service", "Temple", "Temple"), "tavern": ("service", "Tavern", "Tavern"),
    "bank": ("service", "Bank", "Bank"), "training": ("service", "Training hall", "Training"),
    "town_hall": ("service", "Town hall", "Town hall"), "inn": ("service", "Adventurer's Inn", "Inn"),
    "stables": ("transport", "Stables", "Stables"), "boats": ("transport", "Boats", "Boats"),
    "mirror": ("mirror", "Mirror", "Mirror"), "residence": ("house", "Home", "Home"),
    "throne": ("house", "Throne room", "Throne room"),
}


def load_yaml(path: Path):
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        return json.loads(text)
    return yaml.load(text, Loader=yaml.CSafeLoader)


def stem_of(key: str) -> str:
    """A map key of the sources (X1, XD-07, DD-10A) to the map id (xeen_x1, xeen_xd07, xeen_dd10a)."""
    return "xeen_" + key.lower().replace("-", "")


def unescape(text: str) -> str:
    return text.replace('\\"', '"').replace("\\n", " ").replace("\\\\", "\\")


# ---------------------------------------------------------------------------------------------------------------------
# Sources


def load_quest_sources(skip: set[str]) -> dict[str, dict]:
    quests = {}
    for path in sorted((SOURCE / "quests").glob("*.yml")):
        if path.stem in skip:
            continue
        data = yaml.safe_load(path.read_text())
        data["_stem"] = path.stem
        quests[path.stem] = data
    return quests


def qbit_names(quests: dict[str, dict]) -> dict[str, dict]:
    """`<quest>.<qbit>` (A3's names, as Xeen.isSet takes them) -> {id, quest, journal, note}."""
    names = {}
    for stem, quest in quests.items():
        for name, bit in (quest.get("qbits") or {}).items():
            if isinstance(bit, dict):
                names[f"{stem}.{name}"] = {"id": bit.get("id"), "quest": stem, "journal": bit.get("journal", ""),
                                           "note": bit.get("note", "")}
    return names


def hook_sources() -> dict[str, dict]:
    """Every hook of the quest and NPC source files by its full name (`<file stem>.<hook>`), with its player text."""
    hooks = {}
    files = sorted(glob.glob(str(SOURCE / "quests/*.yml"))) + sorted(glob.glob(str(SOURCE / "npcs/**/*.yml"),
                                                                             recursive=True))
    for name in files:
        data = yaml.safe_load(Path(name).read_text())
        if not isinstance(data, dict):
            continue
        for key, hook in (data.get("hooks") or {}).items():
            hooks[f"{Path(name).stem}.{key}"] = hook
    return hooks


def hook_text(hook: dict) -> str:
    """What the player reads when the hook fires: its text, or the text of its last (unconditional) state."""
    if hook.get("text"):
        return hook["text"]
    states = hook.get("states") or []
    for state in reversed(states):
        if state.get("text"):
            return state["text"]
    return ""


def load_towns() -> tuple[dict, dict, dict, dict]:
    """Town files: houses by id, NPCs by id, arrivals by key (-> map, place) and the map of each file."""
    houses, npcs, arrivals = {}, {}, {}
    file_town = {}
    for path in sorted((SOURCE / "towns").glob("*.yml")):
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict) or "stem" not in data:
            continue
        map_id = data["stem"].rsplit(".", 1)[0]
        file_town[path.stem] = data.get("town", "")
        for key, arrival in (data.get("arrivals") or {}).items():
            arrivals[key] = {"map": map_id, "place": (arrival or {}).get("place", "")}
        for house in data.get("houses") or []:
            house = dict(house)
            house["map"] = map_id
            house["town"] = house.get("town") or data.get("town", "")
            houses[house["id"]] = house
        for npc in data.get("npcs") or []:
            npc = dict(npc)
            npc["file_map"] = map_id
            npc["town"] = data.get("town", "")
            npcs[npc["id"]] = npc
    for house in houses.values():
        for npc_id in [house.get("owner")] + list(house.get("residents") or []):
            if npc_id in npcs and house.get("kind") != "mirror":
                npcs[npc_id].setdefault("houses", []).append(house["id"])
    return houses, npcs, arrivals, file_town


def house_rules() -> dict[str, dict[int, tuple[int, int]]]:
    """Engine house_rules.txt: section name -> row index -> (standard quality, special quality)."""
    sections: dict[str, dict[int, tuple[int, int]]] = {}
    current = None
    for row in read_rows(ENGINE / "data_tables/house_rules.txt")[1:]:
        if not row or not row[0].strip():
            continue
        if not row[0].strip().isdigit():
            current = row[0].strip()
            sections[current] = {}
            continue
        if current is not None and len(row) > 6:
            sections[current][int(row[0])] = (to_int(row[1]), to_int(row[6]) if row[6].strip() else to_int(row[1]))
    return sections


def house_table() -> dict[int, dict]:
    rows = {}
    for row in read_rows(WORLD / "data_tables/house_data.txt")[2:]:
        if len(row) > 12 and row[0].strip().isdigit():
            rows[int(row[0])] = {"index": to_int(row[1]), "type": row[2], "val": float(row[12] or 0) if
                                 re.match(r"^[\d.]+$", row[12].strip() or "x") else 0.0}
    return rows


LUA_START = re.compile(r'^RegisterEvent\((\d+),\s*(?:"((?:[^"\\]|\\.)*)"|nil)', re.M)
TAG_RE = re.compile(r"^-- evt:(\S+)\s*$")
MOVE_RE = re.compile(r'evt\.MoveToMap\(([^"]*?)"([^"]+\.(?:blv|odm))"', re.I)
TEXT_RE = re.compile(r'evt\.(?:StatusText|SimpleMessage|SetMessage)\("((?:[^"\\]|\\.)*)"')
HOOK_RE = re.compile(r'XeenQuests\.hook\("([^"]+)"\)')


def parse_events(map_id: str) -> dict[int, dict]:
    """Each RegisterEvent of the map's script: name, the Map Studio tag above it, and what its body does."""
    path = WORLD / "events/maps" / f"{map_id}.lua"
    if not path.exists():
        return {}
    source = path.read_text(encoding="utf-8", errors="replace")
    starts = [(m.start(), int(m.group(1)), unescape(m.group(2) or "")) for m in LUA_START.finditer(source)]
    events: dict[int, dict] = {}
    for index, (start, event, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(source)
        body = source[start:end]
        before = source[:start].rstrip().rsplit("\n", 1)[-1]
        tag_match = TAG_RE.match(before.strip())
        entry = events.setdefault(event, {"name": "", "tag": "", "houses": [], "moves": [], "chests": [],
                                          "hooks": [], "texts": [], "body": ""})
        entry["name"] = entry["name"] or name.strip()
        entry["tag"] = entry["tag"] or (tag_match.group(1) if tag_match else "")
        entry["body"] += body
        entry["houses"] += [int(h) for h in re.findall(r"evt\.EnterHouse\((\d+)\)", body)]
        for move in MOVE_RE.finditer(body):
            args = [a.strip() for a in move.group(1).split(",") if a.strip()]
            entry["moves"].append({"map": move.group(2).lower().rsplit(".", 1)[0], "args": args})
        entry["chests"] += [int(c) for c in re.findall(r"evt\.OpenChest\((\d+)\)", body)]
        entry["hooks"] += HOOK_RE.findall(body)
        entry["texts"] += [unescape(t) for t in TEXT_RE.findall(body)]
    return events


def parse_lua_table(text: str, name: str) -> str:
    match = re.search(re.escape(name) + r" = \{(.*?)\n\}", text, re.S)
    return match.group(1) if match else ""


def hook_targets() -> dict[str, str]:
    """Quest hooks that move the party to another map (events/common/xeen_quests.lua): hook name -> map id. A hook
    calls evt.MoveToMap, or Xeen.toPlane(<element>) (Xeen.PlaneArrivals)."""
    common = (WORLD / "events/common/xeen_common.lua").read_text(encoding="utf-8")
    planes = dict(re.findall(r'(\w+) = \{[^}]*"(xeen_\w+)\.blv"\}', parse_lua_table(common, "Xeen.PlaneArrivals")))
    text = (WORLD / "events/common/xeen_quests.lua").read_text(encoding="utf-8")
    starts = [(m.start(), m.group(1)) for m in re.finditer(r'^XeenQuests\.hooks\["([^"]+)"\] = \{', text, re.M)]
    targets = {}
    for index, (start, name) in enumerate(starts):
        body = text[start:starts[index + 1][0] if index + 1 < len(starts) else len(text)]
        move = MOVE_RE.search(body)
        plane = re.search(r'Xeen\.toPlane\("(\w+)"\)', body)
        if plane and plane.group(1) in planes:
            targets[name] = planes[plane.group(1)]
        elif move:
            targets[name] = move.group(2).lower().rsplit(".", 1)[0]
    return targets


def load_common() -> dict:
    """Promotions, pyramids and stages from events/common/xeen_common.lua."""
    text = (WORLD / "events/common/xeen_common.lua").read_text(encoding="utf-8")
    promotions = {}
    for key, body in re.findall(r"^\s*(\w+) = \{([^}]*)\},", parse_lua_table(text, "Xeen.Promotions"), re.M):
        promotions[key] = [[pretty_name(a), pretty_name(b)] for a, b in re.findall(r'(\w+) = "(\w+)"', body)]
    pyramids = {key: {"opens": opens, "to": to} for key, opens, to in
                re.findall(r'(\w+) = \{opens = "([^"]+)", to = "(\w+)"\}', parse_lua_table(text, "Xeen.Pyramids"))}
    arrivals = {key: target for key, target in
                re.findall(r'(\w+) = \{[^}]*"(xeen_\w+)\.(?:odm|blv)"\}', parse_lua_table(text, "Xeen.PyramidArrivals"))}
    return {"promotions": promotions, "pyramids": pyramids, "pyramid_arrivals": arrivals}


CLASS_NAMES = {"WarriorMage": "Warrior Mage", "GreatDruid": "Great Druid", "PriestLight": "Priest of Light",
               "PriestDark": "Priest of Dark", "RangerLord": "Ranger Lord", "MasterArcher": "Master Archer",
               "ArchDruid": "Arch Druid", "ArchMage": "Arch Mage", "BlackKnight": "Black Knight",
               "BountyHunter": "Bounty Hunter", "MinotaurLord": "Minotaur Lord", "WarTroll": "War Troll",
               "GreatWyrm": "Great Wyrm", "DarkElf": "Dark Elf"}


def class_name(key: str) -> str:
    return CLASS_NAMES.get(key, key)


# ---------------------------------------------------------------------------------------------------------------------
# Map images


def polygon_area(points) -> float:
    return abs(sum(points[i][0] * points[i - 1][1] - points[i - 1][0] * points[i][1] for i in range(len(points)))) / 2


def storey_bands(stem: str) -> list[tuple[float, float]] | None:
    """The storeys of an indoor map whose levels lie over one another (towers, castles with cellars): z bands, lowest
    first. The levels are the floor heights that carry at least 4 % of the floor area, a new storey wherever two such
    heights are 320 or more apart; stairs and slopes between them join the storey below. None: one plan suffices (one
    level, or levels side by side)."""
    payload = dungeon_plans.load(stem)
    floors = []
    for face in payload["faces"]:
        if face["facet_type"] in dungeon_plans.FLOORS and dungeon_plans.drawn(face):
            points = dungeon_plans.face_points(payload, face)
            if len(points) >= 3:
                floors.append((sum(q[2] for q in points) / len(points), polygon_area(points), points))
    total = sum(f[1] for f in floors) or 1.0
    bins: Counter = Counter()
    for z, area, _ in floors:
        bins[round(z / 64) * 64] += area
    levels = sorted(z for z, area in bins.items() if area >= total * 0.04)
    groups = [[levels[0]]] if levels else []
    for z in levels[1:]:
        if z - groups[-1][-1] >= 320:
            groups.append([z])
        else:
            groups[-1].append(z)
    if len(groups) < 2:
        return None
    cuts = [(groups[i][-1] + groups[i + 1][0]) / 2 for i in range(len(groups) - 1)]
    bands = list(zip([-1e9] + cuts, cuts + [1e9]))
    # Only split when storeys cover each other: rasterise each band's floors on a 128-unit grid.
    xs = [q[0] for _, _, pts in floors for q in pts]
    ys = [q[1] for _, _, pts in floors for q in pts]
    min_x, min_y = min(xs), min(ys)
    size = (int((max(xs) - min_x) / 128) + 2, int((max(ys) - min_y) / 128) + 2)
    masks = []
    for low, high in bands:
        mask = Image.new("1", size, 0)
        draw = ImageDraw.Draw(mask)
        for z, _, pts in floors:
            if low <= z < high:
                draw.polygon([((q[0] - min_x) / 128, (q[1] - min_y) / 128) for q in pts], fill=1)
        masks.append(set(i for i, v in enumerate(mask.getdata()) if v))
    overlapping = any(len(masks[i] & masks[j]) > 0.15 * min(len(masks[i]), len(masks[j]))
                      for i in range(len(masks)) for j in range(i + 1, len(masks)) if masks[i] and masks[j])
    return bands if overlapping else None


def render_storey(stem: str, band: tuple[float, float] | None, png: Path) -> dict | None:
    """dungeon_plans.render_plan for one storey: faces of other storeys are hidden (marked invisible) while it draws."""
    payload = dungeon_plans.load(stem)
    original = payload["faces"]
    if band is not None:
        low, high = band
        faces = []
        for face in original:
            points = dungeon_plans.face_points(payload, face)
            z = (sum(q[2] for q in points) / len(points) if face["facet_type"] in dungeon_plans.FLOORS else
                 min(q[2] for q in points)) if points else 0
            if not (low - 32 <= z < high):
                face = dict(face, attributes=face["attributes"] | dungeon_plans.INVISIBLE)
            faces.append(face)
        payload["faces"] = faces
    try:
        return dungeon_plans.render_plan(stem, png)
    finally:
        payload["faces"] = original


def load_presentations(maps_yml: list[dict], out: Path) -> dict[str, dict]:
    """Surface maps use their journal map (icons_x2/<stem>.png); every other map a floor plan drawn from its BLV, one
    per storey where storeys lie over one another. Each floor carries its own bounds and z band."""
    result = {}
    folder = out / "img/maps"
    folder.mkdir(parents=True, exist_ok=True)
    for entry in maps_yml:
        stem = entry["stem"]
        map_id = stem.rsplit(".", 1)[0]
        journal = WORLD / "icons_x2" / f"{map_id}.png"
        floors = []
        if stem.endswith(".odm") and journal.exists():
            floors.append((Image.open(journal).convert("RGB"), [-OUTDOOR_HALF, OUTDOOR_HALF, -OUTDOOR_HALF,
                                                                   OUTDOOR_HALF], None))
        else:
            bands = storey_bands(stem) or [None]
            for index, band in enumerate(bands):
                png = out.parent / "xeen_site_work/plans" / f"{map_id}_{index}.png"
                plan = render_storey(stem, band, png)
                if plan is None:
                    continue
                min_x, min_y, max_x, max_y = plan["bounds"]
                floors.append((Image.open(png).convert("RGB"), [min_x, max_x, min_y, max_y], band))
        if not floors:
            print(f"warning: no plan for {stem}", file=sys.stderr)
            continue
        presentation = {"bounds": floors[0][1], "flipU": False, "flipV": True, "floors": []}
        for index, (image, bounds, band) in enumerate(floors):
            image.thumbnail((1400, 1400))
            name = f"{map_id}.webp" if len(floors) == 1 else f"{map_id}_{index}.webp"
            image.save(folder / name, "WEBP", quality=84, method=5)
            floor = {"w": image.width, "h": image.height, "img": f"img/maps/{name}", "bounds": bounds}
            if band is not None:
                floor["minZ"], floor["maxZ"] = band[0], band[1]
            presentation["floors"].append(floor)
        # The thumbnail: the biggest storey.
        biggest = max(floors, key=lambda f: f[0].width * f[0].height)[0].copy()
        biggest.thumbnail((320, 320))
        biggest.save(folder / f"{map_id}_thumb.webp", "WEBP", quality=80)
        presentation["thumb"] = f"img/maps/{map_id}_thumb.webp"
        presentation["floorNames"] = (["Map"] if len(floors) == 1 else
                                      [f"Level {i + 1}" for i in range(len(floors))])
        result[map_id] = presentation
        print(f"image {map_id}: {len(floors)} floor(s)", file=sys.stderr)
    return result


def place_point(presentation: dict, x: float, y: float, z: float | None) -> tuple[float, float, int]:
    """A point's (u, v) on its floor's image and the floor's index (by the floor's z band)."""
    index = 0
    floors = presentation["floors"]
    if z is not None and len(floors) > 1:
        for i, floor in enumerate(floors):
            if floor.get("minZ", -1e9) - 32 <= z < floor.get("maxZ", 1e9) - 32 or i == len(floors) - 1:
                index = i
                break
    bounds = floors[index].get("bounds", presentation["bounds"])
    u, v = mm9.to_uv({"bounds": bounds, "flipU": False, "flipV": True}, x, y)
    return u, v, index


# ---------------------------------------------------------------------------------------------------------------------
# Text helpers


def condition_text(name: str, qnames: dict, quest_titles: dict) -> str:
    """A qbit name (`m3.done`, `q-c5.done`, `m19.stage2`) or number in words for the reader."""
    if name is None or name == "" or name == 0:
        return ""
    name = str(name)
    entry = qnames.get(name)
    if entry is None and name.isdigit():
        entry = next((e for e in qnames.values() if str(e["id"]) == name), None)
    if entry is None:
        return name
    title = quest_titles.get(entry["quest"], entry["quest"].upper())
    bit = name.split(".", 1)[1] if "." in name else ""
    if bit == "done":
        return f"after {title}"
    if bit.startswith("stage") and bit[5:].isdigit():
        return f"{title}, stage {bit[5:]}"
    return f"{title} ({pretty_name(bit).lower()})" if bit else title


def reward_text(rewards: dict | None) -> str:
    if not rewards:
        return ""
    parts = []
    xp, gold = rewards.get("xp"), rewards.get("gold")
    if xp:
        parts.append(f"{xp:,} XP" if isinstance(xp, int) else f"{xp} XP")
    if gold:
        if isinstance(gold, int):
            parts.append(f"{gold:,} gold" if gold > 0 else f"costs {-gold:,} gold")
        else:
            parts.append(f"{gold} gold")
    for key in ("items", "award", "awards", "promotion", "stats"):
        if rewards.get(key):
            label = {"award": "award", "awards": "awards", "promotion": "promotion", "stats": ""}.get(key, "")
            parts.append((label + ": " if label else "") + str(rewards[key]))
    text = "; ".join(parts)
    # The quest files' notes are for the lanes: no asides about the scripts, item rows or identifiers (D-76).
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\s*\([^()]*\)", lambda m: "" if DEV_WORDING_RE.search(m.group(0)) else m.group(0), text)
        text = re.sub(r"\s*\([^()]*$", lambda m: "" if DEV_WORDING_RE.search(m.group(0)) else m.group(0), text)
    text = re.sub(r"(?<=[A-Za-z]) \d{5}\b", "", text)
    return re.sub(r"\b[a-z]+(?:_[a-z]+)+\b", lambda m: m.group(0).replace("_", " ").capitalize(), text)


MAP_KEY_RE = re.compile(r"\b(?:XD|DD|FD)-\d{2}[A-C]?\b|\b[XDP]\d\b")
MAP_NAMES: dict[str, str] = {}  # map key (X1, XD-07) -> name, filled by main()


def map_names_in(text: str) -> str:
    """Map keys of the design documents (XD-16, D5) in a text for players: the maps' names."""
    return MAP_KEY_RE.sub(lambda m: MAP_NAMES.get(m.group(0), m.group(0)), text)


def clean_where(text: str) -> str:
    """A hook's `where` is written for the map lanes: its first clause only, without asides, identifiers or the
    lanes' notes (D-76). A clause that speaks of answers or the scripts is dropped whole."""
    text = re.sub(r"`[^`]*`", "", text or "")
    previous = None
    while previous != text:  # asides, innermost first: "(the map's prompt; 'X' calls this hook)"
        previous, text = text, re.sub(r"\s*\([^()]*\)", "", text)
    text = re.sub(r"\s*\(.*$", "", text).replace(")", "")
    text = re.split(r";|:\s| — |\. ", text)[0]
    text = re.sub(r"(?:'s)? entrance:\w+", "", text)
    text = re.sub(r",? as [\w.]*_[\w.]*\b.*$|,? as (?:the|its) [\w' ]+$", "", text)
    text = re.sub(r",[^,]*(?:\b[a-z0-9]+_[a-z0-9_]+\b|\b[\w-]+\.[a-z]\w*\b)[^,]*", "", text)
    text = re.sub(r"\s*\b(?:after|before|until|while|once|unless|with|without|on|by)?\s*"
                  r"\b(?:m\d+|q-[cdf]\d+|t\d-[a-z]+|x\d-[a-z]+|[a-z]{1,2}\d+)\.[a-z]\w*", "", text)
    # The lanes' storey numbers (L1, L2) are not the guide's storeys (Entry, Up 1): the point's storey shows instead.
    text = re.sub(r"^L\d[,:]?\s+(?:the\s+)?|\bL\d's\s+(?:the\s+)?", "the ", text)
    text = re.sub(r"\s+on L\d\b", "", text)
    text = re.sub(r"\bL(\d)\b", r"level \1", text)
    text = re.sub(r"\b(?:the )?(?:map|source)'s ", "the ", text)
    text = map_names_in(re.sub(r"\s+", " ", text).strip().rstrip(".;,:")).replace("s's ", "s' ")
    if re.search(r"\banswers?\b|\bcalls?\b|\bhook\b|\bqbit|\bbit \d|^level \d$", text, re.I):
        return ""
    return text[:1].upper() + text[1:] if text else ""


# Developer wording that no point of a guide may carry (D-76): the scripts' words, identifiers, sources and notes.
DEV_WORDING_RE = re.compile(r"(?<!off )\b(?:this|the|its|states|answer|quest|map's|lamp) hooks?\b(?!,? nailed)|"
                            r"\bhook(?:'s|s)? (?:text|calls|name|fires|returns|line)\b|\bhook\(|\b(?:m\d+|q-[cdft]\d+|[a-z]{1,2}\d+)\.[a-z]\w*|calls this|\b[a-z0-9]+_[a-z0-9_]+\b|\bthe source\b|\bthe map's\b|\bqbits?\b|"
                            r"\bevents? \d+|\bpoi\b|\bD-\d+\b|\bA\d\b|scenario|playthrough|quest file|\.lua\b|"
                            r"\bplayer bit\b|\bmap variable", re.I)
YES_NO = {"yes", "y", "no", "n"}
ASK_RE = re.compile(r'evt\.AskQuestion\([^"]*"((?:[^"\\]|\\.)*)",\s*\{([^}]*)\}')


def event_questions(body: str) -> tuple[list[str], set[str]]:
    """The prompts an event asks that want a typed answer (not yes or no), and their answers."""
    prompts, answers = [], set()
    for ask in ASK_RE.finditer(body):
        prompt, listed = ask.groups()
        options = {unescape(a).strip().strip('"').lower() for a in re.findall(r'"((?:[^"\\]|\\.)*)"', listed)}
        if options and not options <= YES_NO:
            prompt = unescape(prompt).strip()
            shown = TEXT_RE.findall(body[:ask.start()])
            if len(prompt) < 20 and shown:  # "Answer?" after the question itself
                before = unescape(shown[-1]).strip()
                prompt = before + ("" if before[-1:] in ".?!:\"" else ".") + " " + prompt
            prompts.append(prompt)
            answers |= options
    return prompts, answers


PUZZLE_CALL_RE = re.compile(r'Xeen\.(genieLamp|pyramidNiche|pharaohSafe|alamarSundial|toll|merchantRiddle|tribbleDoor|'
                            r'vowelessBook|vowelessThrone)\(([^)]*)\)')
LUA_STRING = r'"((?:[^"\\]|\\.)*)"'


def puzzle_calls(body: str, common: str) -> tuple[list[str], list[str], set[str]]:
    """The puzzle pieces of xeen_common.lua an event calls (genie lamps, the pyramid's niches, sundials, the vowelless
    books, merchants, tolls): the hooks they run, the prompt they ask and its answers, from the function's table."""
    hooks, prompts, answers = [], [], set()
    for function, args in PUZZLE_CALL_RE.findall(body):
        start = common.find(f"function Xeen.{function}(")
        end = common.find("\nfunction ", start + 1)
        code = common[start:end if end > 0 else len(common)]
        first = (args.split(",")[0].strip() if args.strip() else "")
        key = first.strip('"') if first.startswith('"') else None
        index = int(first) if first.isdigit() else None
        entry = ""
        for table in dict.fromkeys(re.findall(r"Xeen\.([A-Z]\w+)\[", code)) if (key or index) else []:
            text = parse_lua_table(common, f"Xeen.{table}")
            if key:
                match = re.search(rf"(?m)^(\s+){re.escape(key)} = (.*?)(?=^\1\w+ = |\Z)", text, re.S) or \
                    re.search(rf'(?m)^\s+\{{(.*\bkey = "{re.escape(key)}".*)\}},?\s*$', text)
                entry = match.group(match.lastindex) if match else entry
            elif index:
                rows = re.findall(r"(?m)^\s+\{(.*)\},?\s*$", text)
                entry = rows[index - 1] if index <= len(rows) else entry
            if entry:
                break
        if not entry:
            table = re.search(r"Xeen\.([A-Z]\w+)\.question", code)
            entry = common[common.find(f"Xeen.{table.group(1)} = "):].split("\n", 1)[0] if table else ""
        hooks += [h for h in re.findall(LUA_STRING, entry) if re.fullmatch(r"[\w-]+\.\w+", h)]
        hooks += [prefix + key for prefix in re.findall(r'"([\w-]+\.\w*_)" \.\. key', code)] if key else []
        if key:
            hooks += re.findall(rf'key == "{re.escape(key)}" then\s+XeenQuests\.hook\("([^"]+)"\)', code)
        question = re.search(r"question = " + LUA_STRING, entry)
        if question is None and "kind" in code:
            kind = re.search(r'kind = "(\w+)"', entry)
            kinds = parse_lua_table(common, "Xeen.GenieKinds")
            block = re.search(rf"(?m)^\s+{kind.group(1) if kind else 'wish'} = \{{(.*?)^\s+\}},", kinds, re.S)
            question = re.search(r"question = " + LUA_STRING, block.group(1)) if block else None
        if question:
            prompts.append(unescape(question.group(1)))
        for name in ("answer", "number", "word", "vowels"):
            answers |= {a.lower() for a in re.findall(rf"\b{name} = " + LUA_STRING, entry)}
        listed = re.search(r"answers = \{([^{}]*)\}", entry)
        answers |= {a.lower() for a in re.findall(LUA_STRING, listed.group(1))} if listed else set()
    return hooks, prompts, answers


def ask_text(prompt: str) -> str:
    """A prompt for a point's detail: 'asks "Password?"', or 'Sky Bandits ask "Pay us ..."' for a speaker's line."""
    speaker = re.fullmatch(r'([A-Z][\w\' ]{2,40}): "(.*?)"?', prompt.strip(), re.S)
    if speaker:
        who, line = speaker.groups()
        return f"{who} {'ask' if who.endswith('s') and not who.endswith('ss') else 'asks'} \u201c{line.strip()}\u201d"
    return f"asks \u201c{prompt.strip().strip(chr(34))}\u201d"


def unconditional_hooks(body: str) -> list[str]:
    """The hooks an event runs on every click (not inside an `if` of its body: an outcome such as "the ninth lid
    drops shut" is not what the point shows). A hook in an `if`'s condition runs on every click too."""
    plain = re.sub(r"if continueStep == \d+ then.*?return\s+end", "", body, flags=re.S)
    plain = re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: m.group(0) if m.group(0).count(".") == 1 and
                   re.fullmatch(r'"[\w-]+\.\w+"', m.group(0)) else '""', plain)
    found = []
    for call in HOOK_RE.finditer(plain):
        before = plain[:call.start()]
        tokens = re.findall(r"\b(if|for|while|function|then|do|end)\b", before)
        depth, pending_if = 0, False
        for token in tokens:
            if token in ("if", "for", "while", "function"):
                depth += 1
                pending_if = token == "if"
            elif token in ("then", "do"):
                pending_if = False
            elif token == "end":
                depth -= 1
        if depth <= 1 or (depth == 2 and pending_if):
            found.append(call.group(1))
    return found


def main_hooks(body: str) -> list[str]:
    """The hooks an event calls on its click, not those of its answer branches (`if continueStep == 2 ...`)."""
    plain = re.sub(r"if continueStep == \d+ then.*?return\s+end", "", body, flags=re.S)
    return HOOK_RE.findall(plain)


def answer_forms(options) -> set[str]:
    """Answers as the guide compares them: lower case, without end stops or a leading article."""
    return {re.sub(r"^(?:the|a|an) ", "", a.strip().strip('"').strip(" .").lower()) for a in options} - {""}


def says(answer: str, text: str) -> bool:
    return bool(re.search(r"(?<!\w)" + re.escape(answer) + r"(?!\w)", text, re.I))


def map_secrets(map_data: dict, answers: dict[tuple[str, str], set[str]]) -> set[str]:
    """The answers of a map's prompts that no other point may spell out (a note under a pillow, a prisoner's tip):
    five letters or more, and not a word the map's own names use (Ellinger, Witch, Earth Zone)."""
    names = " ".join([map_data["name"]] + [p["n"] for p in map_data["pois"]])
    found = set()
    for (map_id, _), listed in answers.items():
        if map_id == map_data["id"]:
            found |= {a for a in listed if len(a) >= 5 and not says(a, names)}
    return found


def hide_answers(guide_maps: list[dict], answers: dict[tuple[str, str], set[str]]) -> None:
    """A clue that spells out an answer (the thieves' memo, the registry plaque) keeps its text up to the clause that
    gives the answer away; the answer stays in the quest's walkthrough (D-76)."""
    for map_data in guide_maps:
        secrets = map_secrets(map_data, answers)
        for poi in map_data["pois"]:
            text = poi.get("d", "")
            hits = [m.start() for a in secrets for m in re.finditer(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text,
                                                                     re.I)]
            if not hits:
                continue
            cut = max([m.end() for m in re.finditer(r"[.!?:;](?:\s|$)", text[:min(hits)])] or [0])
            kept = text[:cut].strip()
            if kept.count('"') % 2:  # the cut fell inside a quotation: keep what came before it
                kept = kept[:kept.rfind('"')].strip()
            kept = re.sub(r"\s*(?:that )?reads?:?$|[:;,]$", "", kept).strip()
            if kept:
                poi["d"] = kept + ("" if kept[-1] in ".!?" else ".")
            else:
                poi.pop("d", None)


def says_solution(phrase: str, text: str) -> bool:
    """A declared solution phrase in a text: whole words, in any case; a piece of three letters or fewer ("FI", "THE")
    only as written, since it is a common word in lower case."""
    flags = 0 if len(phrase) <= 3 else re.I
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, flags))


def declared_solutions(guide_maps: list[dict], declared: dict) -> dict[tuple[str, str | None], list[str]]:
    """extra_pois.yml `solutions` (D-79): (map, None) -> phrases no point of the map may say, (map, point) -> pieces
    only that point may not say (two-letter syllables would match everywhere map-wide)."""
    points = {m["id"]: {p["id"] for p in m["pois"]} for m in guide_maps}
    found: dict[tuple[str, str | None], list[str]] = {}
    for map_id, entries in (declared or {}).items():
        if map_id not in points:
            raise SystemExit(f"extra_pois.yml solutions: no map {map_id}")
        for key, phrases in entries.items():
            for poi_id in ([None] if key == "map" else str(key).split(",")):
                if poi_id is not None and poi_id not in points[map_id]:
                    raise SystemExit(f"extra_pois.yml solutions: {map_id} has no point {poi_id}")
                found.setdefault((map_id, poi_id), []).extend(str(p) for p in phrases)
    return found


def developer_wording(guide_maps: list[dict], answers: dict[tuple[str, str], set[str]],
                      solutions: dict[tuple[str, str | None], list[str]]) -> list[str]:
    """Every point whose name or detail carries developer wording, the answer of a prompt (D-76) or a declared
    solution of its map (D-79)."""
    faults = []
    for map_data in guide_maps:
        secrets = map_secrets(map_data, answers)
        for poi in map_data["pois"]:
            phrases = solutions.get((map_data["id"], None), []) + solutions.get((map_data["id"], poi["id"]), [])
            for field in ("n", "d"):
                text = poi.get(field, "")
                hit = DEV_WORDING_RE.search(text)
                own = {a for a in answers.get((map_data["id"], poi["id"]), ()) if len(a) > 2}
                said = [a for a in own | (secrets if field == "d" else set()) if says(a, text)]
                said += [s for s in phrases if says_solution(s, text)]
                if hit or said:
                    faults.append(f"{map_data['id']} {poi['id']} {field}: {hit.group(0) if hit else said[0]!r}: "
                                  f"{text[:160]}")
    return faults


GENERIC_NAMES = {"chest", "sign", "door", "button", "lever", "box", "barrel", "statue", "crate", "book", "stone",
                 "panel", "plaque", "altar", "table", "desk", "skull", "pedestal", "switch", "bed", "throne", "cage"}

SIGN_RE = re.compile(r"sign|signpost|plaque|notice|board|grave|tomb|stone|statue|inscription|plinth|crag|boulder|"
                     r"wall|bones|post|marker|monument", re.I)
BONUS_RE = re.compile(r"well|fountain|shrine|altar|spring|pool|cask|barrel|throne|font|water|tonic|orchard|tree",
                      re.I)
LEVER_RE = re.compile(r"lever|switch|button|wheel|crank|valve|winch|chain|rope|bell|gong|plate|mechanism|lock|"
                      r"pedestal|niche|sundial|dial|panel|torch|brazier", re.I)
DULL_RE = re.compile(r"\s*(?:Nothing(?: here| happens)?|There is nothing|Click\. Nothing|The [\w ]+ is (?:empty|bolted)|"
                     r"You find nothing)", re.I)
STAT_RE = re.compile(r"\+\s?\d+|until (?:you )?rest|cure|heal|resist|permanent|age", re.I)


# ---------------------------------------------------------------------------------------------------------------------
# Main


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=ROOT / "output/xeen_site")
    parser.add_argument("--skip-images", action="store_true", help="reuse map and icon images already in --out")
    args = parser.parse_args()
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    config = yaml.safe_load(CONFIG.read_text())
    hand_points = yaml.safe_load((HERE / "extra_pois.yml").read_text()) or {}
    poi_types = config["poi_types"]

    maps_yml = yaml.safe_load((SOURCE / "maps.yml").read_text())["maps"]
    map_entry = {m["stem"].rsplit(".", 1)[0]: m for m in maps_yml}
    names = {map_id: m["name"] for map_id, m in map_entry.items()}
    MAP_NAMES.update({m["key"]: m["name"] for m in maps_yml})
    quest_src = load_quest_sources(set(config.get("skip_quests", [])))
    qnames = qbit_names(quest_src)
    quest_titles = {stem: q.get("title", stem) for stem, q in quest_src.items()}
    cond = lambda name: condition_text(name, qnames, quest_titles)  # noqa: E731
    houses, npcs, arrivals, _ = load_towns()
    hdata = house_table()
    rules = house_rules()
    hooks_all = load_yaml(WORLD / "data_tables/quest_hooks.yml")
    hook_texts = hook_sources()
    hook_moves = hook_targets()
    common = load_common()
    plan = yaml.safe_load((SOURCE / "towns/teachers_plan.yml").read_text())
    monsters = mm9.load_monsters(WORLD, "Xeen")
    map_stats = {row[2].strip().lower().rsplit(".", 1)[0]: row for row in read_rows(WORLD / "data_tables/map_stats.txt")
                 if len(row) > 27 and row[0].strip().isdigit()}
    family_rows: dict[str, list[int]] = defaultdict(list)
    for monster in monsters.values():
        if monster["family"]:
            family_rows[monster["family"]].append(monster["id"])
    # Item names (the engine's and Xeen's tables), and the quest of each item a map gives as a chest item or a ground
    # item (D-90: the hook records it in `map_gives`; nothing hands it over).
    item_names = {to_int(r["Item #"]): r["Name"] for table in (ENGINE, WORLD)
                  for r in read_tsv(table / "data_tables/items.txt", 1) if to_int(r["Item #"])}
    given_by: dict[tuple[str, int], str] = {}
    for hook in hooks_all.values():
        for item in ((hook or {}).get("map_gives") or {}).values():
            if hook.get("quest") and hook.get("map"):
                given_by[(stem_of(hook["map"]), int(item["id"]))] = hook["quest"].lower()

    # Which quest each NPC talks in, and who promotes.
    npc_quests: dict[int, set[str]] = defaultdict(set)
    promoters: dict[str, list[tuple[str, object]]] = defaultdict(list)  # key -> [("npc", id) | ("hook", name)]

    def walk_promote(node, owner):
        if isinstance(node, dict):
            if "promote" in node and isinstance(node["promote"], str):
                if owner not in promoters[node["promote"]]:
                    promoters[node["promote"]].append(owner)
            for value in node.values():
                walk_promote(value, owner)
        elif isinstance(node, list):
            for value in node:
                walk_promote(value, owner)

    for stem, quest in quest_src.items():
        for npc_id, block in (quest.get("npcs") or {}).items():
            npc_quests[int(npc_id)].add(stem)
            walk_promote(block, ("npc", int(npc_id)))
        for hook_name, hook in (quest.get("hooks") or {}).items():
            walk_promote(hook, ("hook", f"{stem}.{hook_name}"))
    promote_quest = {}
    for key, entry in config["promotions"].items():
        for owner in promoters.get(key, []):
            promote_quest.setdefault(owner, set()).update(entry["quests"])

    # Teacher places of the plan: (skill, mastery) -> place.
    place_of = {}
    for skill, places in plan["offers"].items():
        for mastery, place in zip(("Expert", "Master", "Grandmaster"), places):
            place_of[(skill.lower(), mastery)] = place
    for extra in plan.get("extra") or []:
        place_of[(extra["skill"].lower(), extra["mastery"].capitalize(), "extra")] = extra["place"]

    if args.skip_images and (out / "data/presentations.json").exists():
        presentations = json.loads((out / "data/presentations.json").read_text())
    else:
        presentations = load_presentations(maps_yml, out)
        (out / "data").mkdir(exist_ok=True)
        (out / "data/presentations.json").write_text(json.dumps(presentations))

    # -----------------------------------------------------------------------------------------------------------------
    # Map pass

    maps_out = []
    common_lua = (WORLD / "events/common/xeen_common.lua").read_text(encoding="utf-8")
    point_answers: dict[tuple[str, str], set[str]] = {}  # (map, point) -> the answers of the prompts it asks
    npc_locations: dict[int, list[dict]] = defaultdict(list)
    hook_locations: dict[str, list[dict]] = defaultdict(list)
    house_locations: dict[int, list[dict]] = defaultdict(list)
    monster_maps: dict[int, Counter] = defaultdict(Counter)
    exits_between: dict[tuple[str, str], dict] = {}
    entered_from: dict[str, list[str]] = defaultdict(list)

    for entry in maps_yml:
        stem = entry["stem"]
        map_id = stem.rsplit(".", 1)[0]
        presentation = presentations.get(map_id)
        if presentation is None:
            continue
        outdoor = stem.endswith(".odm")
        scene = load_yaml(WORLD / "maps" / f"{map_id}.scene.yml")
        events = parse_events(map_id)
        for event_id, data in events.items():
            # Puzzle pieces of the common script name their hooks and prompts in its tables.
            hooks, prompts, answers = puzzle_calls(data["body"], common_lua)
            data["hooks"] = list(dict.fromkeys(hooks + data["hooks"]))
            data["asks"] = event_questions(data["body"])[0] + prompts
            own = " ".join([data["name"]] + [names.get(m["map"], "") for m in data["moves"]] +
                           [names.get(hook_moves.get(h, ""), "") for h in data["hooks"]]).lower()
            point_answers[(map_id, f"e{event_id}")] = {a for a in answer_forms(event_questions(data["body"])[1] |
                                                                           answers) if a not in own}
        if outdoor:
            points = {e: [(x, y, 0.0) for x, y in pts] for e, pts in trainer_places.outdoor_event_points(stem).items()}
        else:
            points = dungeon_plans.indoor_event_points(stem)
        pois: list[dict] = []
        counters: Counter = Counter()

        cur = {"z": None}  # the height of the thing being placed (indoors: its floor)
        exit_spots: list[tuple[str, int, float, float, dict]] = []
        mirror_spots: list[tuple[str, int, float, float]] = []

        def add_exit(x, y, target, label, detail, poi_id, quests=None) -> dict:
            """An exit, or the exit to the same map already marked within 1,024 units on the same storey (a pit's or a
            gate's many faces, each with its own event)."""
            floor = place_point(presentation, x, y, cur["z"])[2]
            for t, f, ex, ey, poi in exit_spots:
                if t == target and f == floor and abs(ex - x) < 1024 and abs(ey - y) < 1024:
                    poi["quests"] = sorted(set(poi.get("quests", [])) | set(quests or []))
                    if not poi["quests"]:
                        del poi["quests"]
                    return poi
            poi = add("exit", x, y, label, detail, poi_id=poi_id, map=target, quests=quests or [])
            exit_spots.append((target, floor, x, y, poi))
            return poi

        def add(kind, x, y, label, detail="", poi_id=None, z=None, **extra):
            counters[kind] += 1
            u, v, floor = place_point(presentation, x, y, cur["z"] if z is None else z)
            poi = {"id": poi_id or f"{kind[:2]}{counters[kind]}", "t": kind, "u": u, "v": v, "f": floor, "n": label}
            if detail and re.sub(r"^the ", "", detail.strip(" .").lower()) != re.sub(r"^the ", "", label.strip(" .").lower()):
                poi["d"] = detail
            poi.update({k: val for k, val in extra.items() if val})
            pois.append(poi)
            return poi

        def npc_roles(npc_id: int) -> tuple[str, list[str], dict]:
            """The marker type, role lines and links of a person."""
            npc = npcs.get(npc_id, {})
            kind, roles, links = "npc", [], {}
            teaches = npc.get("teaches") or []
            if teaches:
                kind = "teacher"
                roles.append("Teaches " + ", ".join(f"{t['skill']} {t['mastery'].capitalize()}" +
                                                    (f" (opens {cond(t['opens'])})" if t.get("opens") else "")
                                                    for t in teaches))
            promos = [key for key, owners in promoters.items() if ("npc", npc_id) in owners]
            if promos:
                kind = "promoter"
                links["promo"] = promos[0]
                roles.append("Promotes " + "; ".join(", ".join(f"{class_name(a)} to {class_name(b)}"
                                                                for a, b in common["promotions"].get(p, []))
                                                     for p in promos))
            quests_here = sorted(npc_quests.get(npc_id, set()))
            if quests_here:
                links["quests"] = quests_here
                if kind == "npc":
                    kind = "quest"
            return kind, roles, links

        def person_label(npc_id: int) -> str:
            npc = npcs.get(npc_id, {})
            return npc.get("name", f"NPC {npc_id}")

        def hook_detail(data: dict) -> str:
            """What a hooked event shows the player: the text of its click's first hook that has one (else that
            hook's place) and the prompts it asks."""
            text = ""
            for hook_name in dict.fromkeys(unconditional_hooks(data["body"])):
                text = hook_text(hook_texts.get(hook_name, {})) or ""
                if text:
                    break
            if not text:
                for hook_name in dict.fromkeys(main_hooks(data["body"]) or data["hooks"]):
                    text = clean_where((hooks_all.get(hook_name) or {}).get("where", ""))
                    if text:
                        break
            asks = "; ".join(ask_text(p) for p in data.get("asks", []))
            if asks:  # a typed prompt: the point shows the prompt, its outcomes stay in the walkthrough
                return asks[:1].upper() + asks[1:]
            return unescape(text).strip()

        seen_houses: set[int] = set()
        renamed: dict[str, tuple[str, str]] = {}  # point id -> (the event's own name, detail) for hook-named points
        # A dungeon's chests are its loot containers (placed below with their treasure level), not their events.
        containers = {c.get("container_id") for c in scene.get("loot_containers", []) or []}
        for event_id in sorted(events):
            data = events[event_id]
            hits = points.get(event_id)
            if not hits:
                continue
            x = sum(p[0] for p in hits) / len(hits)
            y = sum(p[1] for p in hits) / len(hits)
            cur["z"] = None if outdoor else min(p[2] for p in hits)
            name = data["name"] or pretty_name(data["tag"].split(":")[-1])
            name = name[:1].upper() + name[1:]
            texts = [t for t in dict.fromkeys(data["texts"]) if t]
            made = False
            # Houses: shops, guilds, services, homes; the people inside decide the marker.
            for house_id in dict.fromkeys(data["houses"]):
                house = houses.get(house_id)
                if house is None or house_id in seen_houses:
                    continue
                seen_houses.add(house_id)
                kind, label, _ = HOUSE_KINDS.get(house["kind"], ("house", "House", "House"))
                if house["kind"].endswith("_guild"):
                    kind, label = "guild", pretty_name(house["kind"]).replace(" guild", " Guild")
                people = [n for n in [house.get("owner")] + list(house.get("residents") or []) if n in npcs]
                lines = [label + (f" in {house['town']}" if house.get("town") else "")]
                links: dict = {"house": house_id}
                quests_here: set[str] = set()
                for npc_id in people:
                    pkind, roles, plinks = npc_roles(npc_id)
                    npc = npcs[npc_id]
                    who = npc["name"] + (f", {npc['title']}" if npc.get("title") else "")
                    lines.append(who + (": " + "; ".join(roles) if roles else ""))
                    quests_here |= set(plinks.get("quests", []))
                    if pkind == "promoter":
                        kind, links["promo"] = "promoter", plinks["promo"]
                    elif pkind == "teacher" and kind in ("house", "service", "vendor", "guild") and kind != "promoter":
                        kind = "teacher" if kind == "house" else kind
                    elif pkind == "quest" and kind == "house":
                        kind = "quest"
                if house.get("hook"):
                    quests_here.add(house["hook"].split(".")[0])
                if house.get("opens"):
                    lines.append(f"Opens {cond(house['opens'])}")
                if house.get("guild"):
                    lines.append(f"Sells the first {house['guild'].get('spells')} spells of its school")
                if house.get("training"):
                    lines.append(f"Trains to level {house['training'].get('cap')}")
                for route in house.get("routes") or []:
                    to = arrivals.get(route["to"], {})
                    when = "/".join(d.capitalize() for d in route.get("days", []))
                    lines.append(f"To {to.get('place') or names.get(to.get('map'), route['to'])}: {when}, "
                                 f"{route.get('travel_days')} d" + (f" ({cond(route['qbit'])})" if route.get("qbit")
                                                                     else ""))
                # A home is shown by the people in it (the house's own name stays in the detail).
                display = house["name"]
                if house["kind"] in ("residence", "throne") and people:
                    display = " and ".join(npcs[n]["name"] for n in people[:2]) + (" and others" if len(people) > 2
                                                                                   else "")
                    lines[0] = house["name"] + (f" in {house['town']}" if house.get("town") else "")
                links["people"] = [npcs[n]["name"] for n in people]
                poi = add(kind, x, y, display, "; ".join(lines), poi_id=f"h{house_id}",
                          quests=sorted(quests_here), **{k: v for k, v in links.items() if k != "quests"})
                if house["kind"] == "mirror":
                    poi["t"] = "mirror"
                house_locations[house_id].append({"map": map_id, "poi": poi["id"], "name": poi["n"]})
                for npc_id in people:
                    npc_locations[npc_id].append({"map": map_id, "poi": poi["id"], "name": npcs[npc_id]["name"]})
                made = True
            if made:
                continue
            # A person spoken to through a map object (Ellinger in his study, Valio in his bed, a booth window).
            spoken = [int(n) for n in re.findall(r"evt\.SpeakNPC\((\d+)\)", data["body"]) if int(n) in npcs]
            if spoken and not any(loc["map"] == map_id for loc in npc_locations.get(spoken[0], [])):
                npc_id = spoken[0]
                kind, roles, links = npc_roles(npc_id)
                npc = npcs[npc_id]
                # The object keeps its name ("Cage", "Booth window") when it has one; the person is in `people`.
                label = name if name and name.lower() not in npc["name"].lower() else npc["name"]
                detail = "; ".join(filter(None, [npc["name"] if label != npc["name"] else "", npc.get("title", ""),
                                                 "; ".join(roles)]))
                poi = add(kind, x, y, label, detail, poi_id=f"e{event_id}", people=[npc["name"]], **links)
                npc_locations[npc_id].append({"map": map_id, "poi": poi["id"], "name": npc["name"]})
                continue
            # A way into another map that a quest hook guards (the Witch Tower's door): an exit tagged with the quest.
            leads = [m["map"] for m in data["moves"] if m["map"] != map_id and m["map"] in map_entry]
            leads += [hook_moves[h] for h in data["hooks"] if hook_moves.get(h, map_id) != map_id
                      and hook_moves[h] in map_entry]
            if leads and data["hooks"]:
                target = leads[0]
                hook_quests = sorted({((hooks_all.get(h) or {}).get("quest") or "").lower() for h in data["hooks"]}
                                     & set(quest_src))
                gate = hook_detail(data)
                poi = add_exit(x, y, target, names.get(target, target), "; ".join(dict.fromkeys(filter(None, [
                    name if name.lower() != names.get(target, target).lower() else "", gate]))), f"e{event_id}",
                    hook_quests)
                for hook_name in data["hooks"]:
                    hook_locations[hook_name].append({"map": map_id, "poi": poi["id"], "name": poi["n"]})
                exits_between.setdefault((map_id, target), {"from": map_id, "to": target, "days": 0})
                entered_from[target].append(map_id)
                continue
            # Quest hooks: objectives, wells and shrines. One point per event: its detail is what the player reads
            # on the click (the hook's text, or the hook's place) and the prompt it asks; the answer stays in the
            # quest's walkthrough (D-76).
            hook_pois = []
            detail = hook_detail(data)
            for hook_name in dict.fromkeys(data["hooks"]):
                hook = hooks_all.get(hook_name) or {}
                source = hook_texts.get(hook_name, {})
                quest = (hook.get("quest") or "").lower() or None
                text = hook_text(source)
                daily = "usedToday" in json.dumps(source) or "markToday" in json.dumps(source)
                bonus = bool(BONUS_RE.search(name) or BONUS_RE.search(hook_name)) and (daily or STAT_RE.search(text))
                kind = "bonus" if bonus and not quest else "objective"
                if not quest and kind == "objective" and not text:
                    continue
                if hook_pois:
                    # One event, several hooks (a quest's step and its later-member promotion): one point.
                    poi = hook_pois[0]
                    if quest and quest in quest_src and quest not in poi.get("quests", []):
                        poi["quests"] = poi.get("quests", []) + [quest]
                    if kind == "bonus" and poi["t"] == "objective" and not poi.get("quests"):
                        poi["t"] = "bonus"
                    hook_locations[hook_name].append({"map": map_id, "poi": poi["id"], "name": poi["n"]})
                    continue
                label = name
                place = clean_where(hook.get("where", ""))
                secret = point_answers.get((map_id, f"e{event_id}"), set())
                if any(re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", place, re.I) for a in secret if len(a) > 2):
                    place = ""  # the place would say the answer ("the door before Ellinger's study")
                if name.lower() in GENERIC_NAMES and place:
                    # "Chest" says little: the hook's place names it ("The vault chest with the tiara").
                    if len(place) <= 64 and not place.startswith(("The same", "Each ", "Any ")):
                        label = place
                full = "; ".join(filter(None, [detail, "once a day" if daily and bonus else ""]))
                poi = add(kind, x, y, label, full, poi_id=f"e{event_id}",
                          quests=[quest] if quest and quest in quest_src else [])
                if label != name:
                    renamed[poi["id"]] = (name, full)
                hook_locations[hook_name].append({"map": map_id, "poi": poi["id"], "name": poi["n"]})
                for owner_hook in [("hook", hook_name)]:
                    promos = [k for k, owners in promoters.items() if owner_hook in owners]
                    if promos:
                        poi["t"], poi["promo"] = "promoter", promos[0]
                hook_pois.append(poi)
            if hook_pois:
                continue
            body = data["body"]
            if "Xeen.useMirror" in body:
                # One point per mirror: its glass, frame, posts and sill each carry the same event (D7's Olympus).
                floor = place_point(presentation, x, y, cur["z"])[2]
                label = name or "Mirror"
                if not any(n == label and f == floor and abs(mx - x) < 1024 and abs(my - y) < 1024
                           for n, f, mx, my in mirror_spots):
                    add("mirror", x, y, label, "Touch it to travel to another town's mirror of this side "
                        "(the towns whose mirrors you have touched)", poi_id=f"e{event_id}")
                    mirror_spots.append((label, floor, x, y))
                continue
            pyramid = re.search(r'Xeen\.travelPyramid\("(\w+)"\)', body)
            if pyramid:
                p = common["pyramids"].get(pyramid.group(1), {})
                target = common["pyramid_arrivals"].get(p.get("to", ""), "")
                add("transport", x, y, "Travel pyramid", f"To {names.get(target, target)}; opens {cond(p.get('opens'))}",
                    poi_id=f"e{event_id}", map=target)
                if target:
                    exits_between.setdefault((map_id, target), {"from": map_id, "to": target, "days": 0,
                                                                "via": "pyramid"})
                continue
            other = [m for m in data["moves"] if m["map"] != map_id and m["map"] in map_entry]
            same = [m for m in data["moves"] if m["map"] == map_id]
            if other:
                target = other[0]["map"]
                label = names.get(target, target)
                detail = name if name and name.lower() != label.lower() else ""
                add_exit(x, y, target, label, detail, f"e{event_id}")
                exits_between.setdefault((map_id, target), {"from": map_id, "to": target, "days": 0})
                entered_from[target].append(map_id)
                continue
            if same:
                add("teleporter", x, y, name or "Teleporter", texts[0] if texts else "", poi_id=f"e{event_id}")
                continue
            if data["chests"] and set(data["chests"]) <= containers:
                continue
            if data["chests"]:
                add("chest", x, y, name or "Chest", "", poi_id=f"e{event_id}")
                continue
            if "Xeen.usedToday" in body or "markToday" in body:
                add("bonus", x, y, name, "; ".join(texts[-2:]) + "; once a day", poi_id=f"e{event_id}")
                continue
            tag = data["tag"]
            if "obelisk" in (name + tag).lower():
                add("hint", x, y, name, texts[0] if texts else "", poi_id=f"e{event_id}")
                continue
            if tag.startswith("hint:"):
                add("hint", x, y, name, texts[0] if texts else "", poi_id=f"e{event_id}")
                continue
            if BONUS_RE.search(name) and texts and STAT_RE.search(" ".join(texts)):
                add("bonus", x, y, name, "; ".join(texts[:2]), poi_id=f"e{event_id}")
                continue
            if LEVER_RE.search(name + " " + tag) and ("SetDoorState" in body or "SetFacetBit" in body or
                                                      "SetTexture" in body):
                add("lever", x, y, name, texts[0] if texts else "", poi_id=f"e{event_id}")
                continue
            if "SetDoorState" in body and not texts:
                add("door", x, y, name or "Door", "", poi_id=f"e{event_id}")
                continue
            if texts and (SIGN_RE.search(name + " " + tag) or tag.startswith("thing:") or tag.startswith("name:")):
                if tag.startswith("name:") or tag.startswith("part:"):
                    continue
                add("sign", x, y, name, texts[0][:400], poi_id=f"e{event_id}")
                continue
            if "SetDoorState" in body:
                add("door", x, y, name or "Door", texts[0] if texts else "", poi_id=f"e{event_id}")
                continue
            # Other named things the party clicks: dials, talking skulls, gongs, safes, pads (puzzle pieces).
            if name and (texts or data["asks"]) and not tag.startswith(("name:", "door:", "building:")) and \
                    not (texts and not data["asks"] and all(DULL_RE.match(t) for t in texts)):
                lever = bool(LEVER_RE.search(name + " " + tag))
                asks = "; ".join(ask_text(p) for p in data["asks"])
                detail = asks[:1].upper() + asks[1:] if asks else "" if lever else texts[0][:400]
                add("lever" if lever else "sign", x, y, name, detail, poi_id=f"e{event_id}")

        def item_list(ids: list[int]) -> str:
            counted = Counter(ids)
            return ", ".join((f"{n} × " if n > 1 else "") + item_names.get(i, f"item {i}") for i, n in counted.items())

        def quest_point_at(x, y, quests: list[str]) -> dict | None:
            """The quest point of an event on the same spot (a chest's own click: the rack, the desk, the cabinet)."""
            u, v, floor = place_point(presentation, x, y, cur["z"])
            for poi in pois:
                if poi["t"] == "objective" and poi["f"] == floor and set(poi.get("quests", [])) & set(quests) and \
                        abs(poi["u"] - u) < 0.004 and abs(poi["v"] - v) < 0.004:
                    return poi
            return None

        # BLV containers carry their treasure level and the items placed in them (D-90: quest finds are chest items).
        for chest in scene.get("loot_containers", []) or []:
            pos = chest["position"]
            level = chest.get("random_treasure_level", 0)
            label = (chest.get("presentation") or "chest").capitalize() + (f" L{level}" if level else "")
            fixed = [int(i["item_id"]) for i in chest.get("fixed_items") or [] if i.get("item_id")]
            quests = sorted({given_by[(map_id, i)] for i in fixed if (map_id, i) in given_by} & set(quest_src))
            details = []
            if chest.get("gold"):
                details.append(f"{chest['gold']} gold")
            if level:
                details.append(f"treasure level {level}")
            cur["z"] = pos["z"]
            detail = ", ".join(details)
            if fixed:
                detail = f"Holds {item_list(fixed)}" + (f"; {detail}" if detail else "")
            twin = quest_point_at(pos["x"], pos["y"], quests) if quests else None
            if twin is not None:  # one pin: the quest point says what the chest holds
                kind_name = (chest.get("presentation") or "chest").lower()
                twin["d"] = f"A {kind_name} holding {item_list(fixed)}" + \
                    (f" ({', '.join(details)})" if details else "") + (f". {twin['d']}" if twin.get("d") else "")
                continue
            add("chest", pos["x"], pos["y"], label, detail, poi_id=f"c{chest['container_id']}", lvl=level,
                quests=quests)

        # Items lying on the ground (sprite objects carrying an item): quest finds since D-90, and loose loot.
        for index, thing in enumerate((scene.get("initial_state") or {}).get("sprite_objects") or []):
            raw = str(thing.get("raw_containing_item_hex") or "")
            item_id = int.from_bytes(bytes.fromhex(raw[:8]), "little", signed=True) if len(raw) >= 8 else 0
            if item_id <= 0:
                continue
            pos = thing["position"]
            cur["z"] = None if outdoor else pos["z"]
            quest = given_by.get((map_id, item_id))
            name = item_names.get(item_id, f"item {item_id}")
            if quest in quest_src:
                add("objective", pos["x"], pos["y"], name, "Lies on the ground", poi_id=f"g{index}", quests=[quest])
            else:
                add("chest", pos["x"], pos["y"], name, "Lies on the ground", poi_id=f"g{index}")

        # Actors: placed people and monsters.
        for actor in scene["initial_state"].get("actors", []):
            pos = actor["position"]
            cur["z"] = None if outdoor else pos["z"]
            npc_id = actor.get("npc_id") or 0
            if npc_id and npc_id in npcs:
                kind, roles, links = npc_roles(npc_id)
                npc = npcs[npc_id]
                detail = "; ".join(filter(None, [npc.get("title", ""), "; ".join(roles)]))
                poi = add(kind, pos["x"], pos["y"], npc["name"], detail, poi_id=f"a{actor['actor_index']}", **links)
                npc_locations[npc_id].append({"map": map_id, "poi": poi["id"], "name": npc["name"]})
                continue
            monster = monsters.get(actor.get("monster_info_id")) or monsters.get(actor.get("monster_id"))
            if monster is None or npc_id:
                continue
            monster_maps[monster["id"]][map_id] += 1
            add("monster", pos["x"], pos["y"], monster["name"], f"Level {monster['level']}, {monster['hp']} HP",
                poi_id=f"a{actor['actor_index']}", mon=monster["id"])

        # Outdoor spawn points: groups of a map_stats family (slot 1-3), any tier.
        stats = map_stats.get(map_id)
        for spawn in scene.get("spawns", []) or []:
            if spawn.get("type_id") != 3 or stats is None:
                continue
            index = spawn.get("index", 1)
            slot = (index - 1) % 3 if index <= 3 else (index - 4) // 3
            tier = None if index <= 3 else "ABC"[(index - 4) % 3]
            picture = stats[16 + slot * 4].strip()
            family = re.sub(r"^Xeen ", "", picture)
            rows = sorted(family_rows.get(family, []))
            if not rows:
                continue
            chosen = [r for r in rows if monsters[r]["tier"] == tier] if tier else rows[:3]
            for row in chosen:
                monster_maps[row][map_id] += 1
            first = monsters[chosen[0]]
            pos = spawn["position"]
            add("monster", pos["x"], pos["y"], f"{family} group" + (f" ({tier})" if tier else ""),
                f"Spawn point: {', '.join(monsters[r]['name'] for r in chosen)}; levels "
                f"{min(monsters[r]['level'] for r in chosen)}-{max(monsters[r]['level'] for r in chosen)}",
                poi_id=f"s{spawn['spawn_index']}", mon=first["id"])

        # The four edges of a surface map.
        if outdoor:
            for edge, (u, v) in (("north", (0.5, 0.012)), ("south", (0.5, 0.988)), ("west", (0.012, 0.5)),
                                 ("east", (0.988, 0.5))):
                # An edge may lead to two maps by its spans (X4's south edge: west half to X3, east half to X2).
                spans = (entry.get("edge_spans") or {}).get(edge)
                target_key = (entry.get("neighbours") or {}).get(edge)
                if not spans:
                    spans = [{"from": -OUTDOOR_HALF, "to": OUTDOOR_HALF, "map": target_key}] if target_key else []
                for index, span in enumerate(spans):
                    target = stem_of(span["map"])
                    days = travel_days(map_id, target) or travel_days(target, map_id)
                    middle = (span["from"] + span["to"]) / 2 / (2 * OUTDOOR_HALF) + 0.5  # along the edge, 0..1
                    eu, ev = (middle, v) if edge in ("north", "south") else (u, 1 - middle)
                    part = "" if len(spans) == 1 else (" (west half)" if middle < 0.5 else " (east half)") \
                        if edge in ("north", "south") else (" (south half)" if middle < 0.5 else " (north half)")
                    pois.append({"id": f"edge{edge}{index if len(spans) > 1 else ''}", "t": "exit", "u": round(eu, 4),
                                 "v": round(ev, 4), "f": 0, "n": names.get(target, target),
                                 "d": f"Walk off the {edge} edge{part}" + (f": {days} days of travel" if days else ""),
                                 "map": target})
                    exits_between[(map_id, target)] = {"from": map_id, "to": target, "days": days}

        # Two points named alike by their hooks ("The second cage ...") say nothing apart: back to the event's names.
        labels = Counter(p["n"] for p in pois if p["id"] in renamed)
        for poi in pois:
            if poi["id"] in renamed and labels[poi["n"]] > 1:
                poi["n"], poi["d"] = renamed[poi["id"]]
        # The hand-kept points (extra_pois.yml): renames of generic points, and pieces the scripts do not name.
        for poi_id, change in (hand_points.get("rename", {}).get(map_id) or {}).items():
            match = [p for p in pois if p["id"] == poi_id]
            if not match:
                raise SystemExit(f"extra_pois.yml: {map_id} has no point {poi_id}")
            match[0].update({k: v for k, v in change.items() if k in ("n", "d", "t", "quests")})
        for item in hand_points.get("add", {}).get(map_id) or []:
            cur["z"] = None if outdoor else item.get("z")
            add(item["t"], item["x"], item["y"], item["n"], item.get("d", ""), poi_id=item["id"],
                quests=item.get("quests", []))
        for poi in pois:
            if poi["t"] not in poi_types:
                raise SystemExit(f"unknown POI type {poi['t']}")
        kind = {"odm": "outdoor", "open_air_blv": "outdoor"}.get(entry["kind"], "dungeon")
        if entry.get("role") in ("sky",):
            kind = "sky"
        elif entry.get("role") in ("plane", "finale"):
            kind = "plane"
        elif "town" in (entry.get("role") or "") and kind == "dungeon":
            kind = "town"
        # Storeys are named from the arrival's: Entry, Up 1, Down 1 ...; a map opens on the arrival's storey.
        starts = scene.get("party_start_points") or []
        if len(presentation["floors"]) > 1 and starts:
            entry_floor = place_point(presentation, 0, 0, starts[0]["position"][2])[2]
            presentation = dict(presentation, defaultFloor=entry_floor, floorNames=[
                "Entry" if i == entry_floor else f"Up {i - entry_floor}" if i > entry_floor else f"Down {entry_floor - i}"
                for i in range(len(presentation["floors"]))])
        maps_out.append({"id": map_id, "name": names[map_id], "kind": kind, "region": "", "face": entry.get("face"),
                         "act": entry.get("act"), "party": entry.get("party"), **presentation, "pois": pois})
        print(f"{map_id}: {len(pois)} points", file=sys.stderr)

    # Regions: the config's surface, sky and plane maps; dungeons join the map that leads into them.
    region_by_hub = {r["hub"]: r for r in config["regions"]}
    region_of = {}
    for region in config["regions"]:
        for map_id in [region["hub"]] + region.get("maps", []):
            region_of[map_id] = region["id"]
    region_of.update(config.get("region_of", {}))
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
    for region in config["regions"]:
        members = [m["id"] for m in maps_out if region_of.get(m["id"]) == region["id"]]
        members.sort(key=lambda m: (m != region["hub"], map_entry[m].get("kind") != "odm", names[m]))
        regions.append({k: v for k, v in region.items() if k != "maps"} | {"maps": members})
    unplaced = [m["id"] for m in maps_out if m["id"] not in region_of]
    if unplaced:
        print(f"maps without a region: {unplaced}", file=sys.stderr)
        regions.append({"id": "other", "name": "Elsewhere", "hub": unplaced[0], "pos": [4.3, 4.7],
                        "face": "Other", "maps": unplaced})
        for m in unplaced:
            region_of[m] = "other"
    for map_data in maps_out:
        map_data["region"] = region_of.get(map_data["id"], "")
    region_name = {r["id"]: r["name"] for r in regions}

    # -----------------------------------------------------------------------------------------------------------------
    # Quests

    quests: dict[str, dict] = {}
    for stem, src in quest_src.items():
        kind = src.get("kind")
        cat = "main" if kind == "main" else "promotion" if kind == "promotion" else "side"
        stages = [{"qbit": bit["id"], "text": bit["journal"]} for bit in (src.get("qbits") or {}).values()
                  if isinstance(bit, dict) and bit.get("journal")]
        quest = {"id": stem, "title": src.get("title", stem), "src": src.get("id"), "cat": cat,
                 "stages": stages or [{"qbit": 0, "text": ""}], "givers": [], "handoffs": [], "steps": [],
                 "act": ACTS.get(str(src.get("act")), 0), "srcLevel": src.get("level")}
        if cat == "main":
            quest["chapter"] = quest["act"]
        giver = src.get("giver")
        if isinstance(giver, int):
            quest["givers"] = list(npc_locations.get(giver, []))
            if not quest["givers"] and giver in npcs:
                quest["giverText"] = npcs[giver]["name"] + " (not placed on a map)"
        if src.get("giver_name"):
            text = map_names_in(src["giver_name"].strip().strip("()"))
            quest["giverText"] = text[:1].upper() + text[1:]
        for npc_id in (src.get("npcs") or {}):
            if npc_id != giver:
                quest["handoffs"] += [loc for loc in npc_locations.get(int(npc_id), []) if loc not in quest["handoffs"]]
        reward = reward_text(src.get("rewards"))
        if reward:
            quest["reward"] = reward
        quests[stem] = quest
    for map_data in maps_out:
        for poi in map_data["pois"]:
            for key in poi.get("quests", []):
                if key in quests and poi["t"] in ("objective", "chest", "bonus", "exit", "lever", "promoter"):
                    quests[key]["steps"].append({"map": map_data["id"], "poi": poi["id"], "name": poi["n"]})
    promotions = []
    for key, entry in config["promotions"].items():
        lines = common["promotions"].get(key, [])
        at = []
        for owner in promoters.get(key, []):
            at += npc_locations.get(owner[1], []) if owner[0] == "npc" else hook_locations.get(owner[1], [])
        unique_at = []
        for a in at:
            if a not in unique_at:
                unique_at.append(a)
        promo_quests = [q for q in entry["quests"] if q in quests]
        title = " / ".join(dict.fromkeys(class_name(b) for _, b in lines))
        promotions.append({"key": key, "to": title, "from": " / ".join(dict.fromkeys(class_name(a) for a, _ in lines)),
                           "path": entry["path"], "classes": [[class_name(a), class_name(b)] for a, b in lines],
                           "quests": promo_quests, "at": unique_at,
                           "note": f"{entry['path']} promotion" + (": " + ", ".join(quests[q]["title"]
                                                                                    for q in promo_quests)
                                                                   if promo_quests else "")})
        for q in promo_quests:
            quests[q]["promo"] = title
    for map_data in maps_out:
        for poi in map_data["pois"]:
            if poi.get("promo"):
                poi["promo"] = next((p["to"] for p in promotions if p["key"] == poi["promo"]), poi["promo"])

    story, walkthroughs = mm9.load_story(quests, maps_out, {"poi_types": poi_types}, STORY,
                                         ["act1.yml", "act2.yml", "act3.yml", "act4.yml", "act5.yml", "act6.yml"]) \
        if STORY.is_dir() else ([], {})
    for chapter in story:
        chapter["title"] = next((c["name"] for c in config["chapters"] if c["id"] == chapter["id"]), chapter["title"])
    mm9.quest_levels(quests, walkthroughs, maps_out, monsters, {"quest_level_maps": {}})
    for quest in quests.values():
        if quest.get("srcLevel"):
            level = quest.get("level") or {"lo": quest["srcLevel"], "hi": quest["srcLevel"], "maps": []}
            level["rec"] = quest["srcLevel"]
            quest["level"] = level
        quest.pop("srcLevel", None)

    # -----------------------------------------------------------------------------------------------------------------
    # Teachers, shops, services

    teachers = []
    for npc_id, npc in sorted(npcs.items()):
        for offer in npc.get("teaches") or []:
            mastery = offer["mastery"].capitalize()
            mastery = "Grandmaster" if mastery.startswith("Grand") else mastery
            canonical = maw_teachers.canonical_skill(offer["skill"])
            place_key = place_of.get((offer["skill"].lower(), mastery))
            place = plan["places"].get(place_key, {}) if place_key else {}
            if place_key and npc.get("file_map") != stem_of(place.get("map", "")):
                extra = place_of.get((offer["skill"].lower(), mastery, "extra"))
                place = plan["places"].get(extra, place)
            when = []
            if offer.get("opens"):
                when.append(f"lesson opens {cond(offer['opens'])}")
            for house_id in npc.get("houses", []):
                if houses[house_id].get("opens"):
                    when.append(f"house opens {cond(houses[house_id]['opens'])}")
            if place.get("when") and not when:
                when.append(place["when"])
            needs = f"{offer['skill']} {MASTERY_RANK[mastery]}"
            extra_need = maw_teachers.EXTRA_REQUIREMENTS.get((canonical, mastery))
            teachers.append({
                "skill": offer["skill"], "skills": offer["skill"], "mastery": mastery,
                "name": npc["name"] + (f", {npc['title']}" if npc.get("title") else ""),
                "region": place.get("town") or npc.get("town") or names.get(npc["file_map"], ""),
                "rank": MASTERY_RANK[mastery], "gold": maw_teachers.default_price(canonical, MASTERY_SLOT[mastery]),
                "gated": bool(when), "when": "; ".join(when) + (f"; also {extra_need}" if extra_need else ""),
                "act": place.get("act", ""), "level": place.get("level", ""),
                "at": [{"map": a["map"], "poi": a["poi"]} for a in npc_locations.get(npc_id, [])],
            })

    vendors, services, spellbooks = [], [], {}
    item_rows = {to_int(r["Item #"]): r for r in read_tsv(ENGINE / "data_tables/items.txt", 1)}
    for house_id, house in sorted(houses.items()):
        kind = house["kind"]
        at = [{"map": a["map"], "poi": a["poi"], "name": a["name"]} for a in house_locations.get(house_id, [])]
        row = hdata.get(house_id, {})
        price = row.get("val") or house.get("price") or 1
        region = house.get("town") or names.get(house["map"], "")
        owner = npcs.get(house.get("owner"), {}).get("name", "")
        opens = cond(house["opens"]) if house.get("opens") else ""
        if kind in ("weapon_shop", "armor_shop", "magic_shop", "alchemist") or kind.endswith("_guild"):
            vtype = HOUSE_KINDS[kind][2] if kind in HOUSE_KINDS else pretty_name(kind).replace(" guild", " Guild")
            section = {"weapon_shop": "Weapon shops", "armor_shop": "Armor shops", "magic_shop": "Magic shops",
                       "alchemist": "Alchemist shops"}.get(kind)
            treasure = []
            if section:
                rows_for = next((v for k, v in rules.items() if k.lower().startswith(section.lower())), {})
                quality = rows_for.get(row.get("index"))
                if quality is None and house.get("shop"):
                    quality = (house["shop"].get("quality", 0), house["shop"].get("quality", 0) + 1)
                treasure = list(quality) if quality else []
            sells = {"weapon_shop": "weapons", "armor_shop": "armour", "magic_shop": "wands, rings, amulets, magic "
                     "items", "alchemist": "potions and reagents"}.get(kind, "")
            if kind.endswith("_guild"):
                school = kind.split("_")[0].capitalize()
                count = (house.get("guild") or {}).get("spells", 0)
                sells = f"{school} Magic spellbooks 1-{count}"
                base = SCHOOLS.index(school) * 11
                for n in range(1, count + 1):
                    spell = base + n
                    item = item_rows.get(399 + spell, {})
                    book = spellbooks.setdefault(spell, {
                        "spell": spell, "name": item.get("Name", f"Spell {spell}"), "school": school,
                        "mastery": "Normal" if n <= 4 else "Expert" if n <= 7 else "Master" if n <= 10 else
                        "Grandmaster", "value": to_int(item.get("Value", "0")), "shops": []})
                    book["shops"].append({"id": house_id, "pages": 1, "of": 1})
            vendors.append({"id": house_id, "name": house["name"], "type": vtype, "region": region,
                            "treasure": treasure, "tiers": [], "enchanted": 0, "price": price, "restock": 0,
                            "pages": 1, "perPage": 0,
                            "sells": "; ".join(filter(None, [sells, f"owner {owner}" if owner else "",
                                                            f"opens {opens}" if opens else ""])),
                            "at": at})
        elif kind in ("temple", "tavern", "bank", "training", "town_hall", "inn", "stables", "boats"):
            services.append({"name": house["name"], "type": HOUSE_KINDS[kind][1], "region": region,
                             "trainMax": (house.get("training") or {}).get("cap", 0),
                             "learn": [f"opens {opens}"] if opens else [], "at": at})

    # -----------------------------------------------------------------------------------------------------------------
    # Travel

    schedules = []
    for house_id, house in sorted(houses.items()):
        for route in house.get("routes") or []:
            to = arrivals.get(route["to"])
            if not to:
                continue
            boat = house["kind"] == "boats"
            row = hdata.get(house_id, {})
            fare = max(1, round((50 if boat else 25) * (row.get("val") or 1)))
            for day in route.get("days", []):
                schedules.append({
                    "vessel": house["name"], "kind": "Boat" if boat else "Coach", "from": house["map"],
                    "at": [{"map": a["map"], "poi": a["poi"]} for a in house_locations.get(house_id, [])],
                    "to": to["map"], "toPlace": to.get("place", ""), "day": DAYS[DAY_KEYS.index(day)],
                    "days": route.get("travel_days", 0), "price": fare, "gated": bool(route.get("qbit")),
                    "gate": cond(route.get("qbit")) if route.get("qbit") else "",
                })
    mirrors = load_yaml(WORLD / "data_tables/mirrors.yml")
    extras = []
    mirror_rows = []
    for face, rows in mirrors.items():
        for mirror in rows:
            at = house_locations.get(mirror["id"], [])
            mirror_rows.append({"from": mirror["map"].rsplit(".", 1)[0], "to": "", "label": mirror["town"],
                                "note": f"{face.capitalize()}; " + "; ".join(filter(None, [
                                    "after Castle Kalindra's stage 4"
                                    if face == "darkside" else "",
                                    f"lit {cond(mirror['opens'])}" if mirror.get("opens") else
                                    ("" if face == "darkside" else "lit from the start")])),
                                "at": at[:1]})
    extras.append({"title": "Mirrors", "intro": "Each town has a mirror. Touch a mirror to add its town; then any mirror "
                   "of the same side takes you to every town whose mirror you have touched. Touching a mirror also "
                   "unlocks that town for Town Portal. Darkside's mirrors wake when Castle Kalindra is whole; a "
                   "cursed town's mirror stays dark until the town is freed.",
                   "rows": mirror_rows})
    pyramid_rows = []
    for key, pyramid in common["pyramids"].items():
        source_map = common["pyramid_arrivals"].get(key, "")
        target = common["pyramid_arrivals"].get(pyramid["to"], "")
        at = [{"map": m["id"], "poi": p["id"]} for m in maps_out if m["id"] == source_map for p in m["pois"]
              if p["n"] == "Travel pyramid"]
        pyramid_rows.append({"from": source_map, "to": target, "label": "Travel pyramid",
                             "note": f"opens {cond(pyramid['opens'])}", "at": at[:1]})
    extras.append({"title": "Travel pyramids", "intro": "The pyramids join Cloudside and Darkside. Before the party "
                   "holds the right to pass, a pyramid only says that the moons are not aligned.",
                   "rows": pyramid_rows})
    tp = yaml.safe_load((SOURCE / "towns/town_portal.yml").read_text())
    tp_rows = []
    for page in tp["pages"]:
        for dest in page["destinations"]:
            tp_rows.append({"from": stem_of(dest["map"]), "to": "", "label": dest["town"],
                            "note": f"{page['label']}; unlocked by touching the town's mirror", "at": []})
    extras.append({"title": "Town Portal", "intro": "Town Portal shows one page per side: the side you stand on. A "
                   "town is on it once you have touched its mirror.", "rows": tp_rows})
    links = list(exits_between.values())
    # The world map's lines between regions: walking edges with their days, and one line per other pair of regions a
    # dungeon passage, a fall from the sky or a pyramid joins ("via <map>").
    kind_of = {m["id"]: m["kind"] for m in maps_out}
    world_links: dict[tuple[str, str], dict] = {}
    for link in links:
        a, b = region_of.get(link["from"]), region_of.get(link["to"])
        if not a or not b or a == b:
            continue
        key = tuple(sorted((a, b)))
        if link["days"]:
            world_links[key] = {"a": key[0], "b": key[1], "days": link["days"], "label": f"{link['days']} d"}
            continue
        if key in world_links:
            continue
        # Passages are many; only the pyramids are labelled (the lines say a way exists, the Exits of a map say where).
        label = "pyramid" if link.get("via") == "pyramid" else ""
        world_links[key] = {"a": key[0], "b": key[1], "days": 0, "label": label, "passage": True}

    data = {
        "generated": "",
        "site": config["site"],
        "poiTypes": poi_types,
        "regions": regions,
        "chapters": config["chapters"],
        "maps": maps_out,
        "quests": sorted(quests.values(), key=lambda q: ({"main": 0, "side": 1, "promotion": 2}[q["cat"]], q["act"],
                                                         q["srcLevel"] if "srcLevel" in q else
                                                         (q.get("level") or {}).get("rec", 0), q["title"])),
        "teachers": teachers,
        "vendors": vendors,
        "spellbooks": sorted(spellbooks.values(), key=lambda b: b["spell"]),
        "services": services,
        "promotions": promotions,
        "story": story,
        "walkthroughs": walkthroughs,
        "faq": mm9.load_faq(FAQ) if (FAQ / "faq.yml").exists() else [],
        "travel": {"links": links, "schedules": schedules, "extras": extras,
                   "worldLinks": list(world_links.values())},
        "monsters": mm9.attach_portraits(build_monsters(monsters, monster_maps), out, args.skip_images,
                                         set(config.get("monster_portrait_exclude", [])), PORTRAITS),
        **mm9.build_items(out, args.skip_images, WORLD,
                          [WORLD / "icons_x2", ENGINE / "icons_x2"] +
                          [ROOT / f"assets_dev/worlds/{w}/icons_x2" for w in ("mm8", "mm7", "mm6")]),
    }
    mm9.attach_shots(maps_out, out, args.skip_images, set(config.get("shot_exclude", [])), SHOTS)
    for region in data["regions"]:
        region["name"] = region_name[region["id"]]
    # Point names and details are for players: no developer wording, no answer of a prompt (D-76), no solution (D-79).
    hide_answers(maps_out, point_answers)
    # Links to points carry the point's name as it was made: refresh them after the hand renames.
    current = {(m["id"], poi["id"]): poi["n"] for m in maps_out for poi in m["pois"]}

    def refresh(node):
        if isinstance(node, dict):
            if {"map", "poi", "name"} <= node.keys() and (node["map"], node["poi"]) in current:
                node["name"] = current[(node["map"], node["poi"])]
            for value in node.values():
                refresh(value)
        elif isinstance(node, list):
            for value in node:
                refresh(value)

    refresh(data)
    faults = developer_wording(maps_out, point_answers, declared_solutions(maps_out, hand_points.get("solutions")))
    faults += [f"quest {q['id']} reward: {q['reward'][:160]}" for q in data["quests"]
               if DEV_WORDING_RE.search(q.get("reward", ""))]
    if faults:
        print("\n".join(faults), file=sys.stderr)
        raise SystemExit(f"{len(faults)} point names or details carry developer wording, answers (D-76) or solutions "
                         f"(D-79); fix the generator or extra_pois.yml")
    write_site(out, data)
    return 0


def travel_days(a: str, b: str) -> int:
    rows = read_rows(WORLD / "data_tables/outdoor_travels.txt")
    for row in rows[1:]:
        if row and row[0].strip().lower() == f"{a}.odm":
            for i in range(1, 12, 3):
                if i + 2 < len(row) and row[i].strip().lower() == f"{b}.odm":
                    return to_int(row[i + 2])
    return 0


def build_monsters(monsters: dict[int, dict], monster_maps: dict[int, Counter]) -> list[dict]:
    out = []
    for monster_id, counts in monster_maps.items():
        monster = dict(monsters[monster_id])
        monster["maps"] = [{"map": m, "count": c} for m, c in counts.most_common()]
        out.append(monster)
    return sorted(out, key=lambda m: (m["level"], m["name"]))


def write_site(out: Path, data: dict) -> None:
    (out / "data").mkdir(exist_ok=True)
    (out / "data/guide.js").write_text("window.GUIDE = " + json.dumps(data, separators=(",", ":")) + ";\n")
    for path in MM9_WEB.iterdir():
        if path.is_file() and path.name != "page.html":
            shutil.copy2(path, out / path.name)
    page = (HERE / "web/page.html").read_text(encoding="utf-8")
    shutil.copy2(HERE / "web/page.html", out / "page.html")
    (out / "index.html").write_text('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
                                    '<meta name="viewport" content="width=device-width, initial-scale=1, '
                                    'viewport-fit=cover">\n</head>\n<body>\n' + page + "</body>\n</html>\n",
                                    encoding="utf-8")
    for folder, target in ((STORY / "img", "img/story"), (FAQ / "img", "img/faq")):
        if folder.is_dir():
            shutil.copytree(folder, out / target, dirs_exist_ok=True)
    size = (out / "data/guide.js").stat().st_size
    print(f"wrote {out} (guide.js {size // 1024} KB, {sum(len(m['pois']) for m in data['maps'])} points)",
          file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
