#!/usr/bin/env python3
"""
Ta'Sar Academy, MM9 rework: MM9's TASARACADEMY.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_tasaracademy/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_tasaracademy/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the archway cuts, the pit's portal and the ladders; this file adds the population
(props.json from ../../props/mm9_tasaracademy_claude, the pit's spikes, the guards, students, animals and Dagrells) and
MM9's scripted objects as native Lua, each citing its .scr (README.md, "Scripted objects"):
- the library puzzle (TaSarBook.scr, TaSarTable.scr): the four textbooks (items 435-438) back on their tables, in
  order, unlock the library's secret door (keys 9501-9504, 9516-9520);
- the Book of Rules (BookOfRules.scr, the podium's PropTrigger.scr): item 391 and Ludwig's quest keys 59 / 166;
- the rotating bookcase and its book buttons, the two wall switches and their secret doors, the cracked wall
  (DestructableBrush), the trap doors over the spike pit (PitDoorTrigger1, PropDamager Spikes1);
- the chalices (TaSarChalice.scr), the skill books (SkillBook.scr), the letters (BookLetter.scr), the crate that hides
  a Dagrell (Trigger4, DestructableProp0), the sparring students (TaSarTeacher.scr, TaSarStudent.scr, Trigger0-3);
- the PerceptionBrushes (Perception 10).

MM9's Trigger volumes are boxes polled four times a second (as Verhoffin Ruins' and the Chasm's): they fire on any
part of the party in their box.
"""

from __future__ import annotations

import csv
import struct
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.destructibles import CLICK_EVENT_BASE  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.source import ROOT, SCALE, yaw_degrees  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"

# --- Events, timers, cogs, groups ------------------------------------------------------------------------------------
EV_LOAD = 1
EV_LIBRARY_DOOR, EV_BOOK_BUTTON, EV_SWITCH, EV_SWITCH1, EV_CRACK = 200, 201, 202, 203, 204
EV_CRACK_HIT = 205                  # "door crack" damaged: its DamageTrigger destroys "door crack 2" (EV_CRACK: broken)
CRACK, CRACK2 = "door crack", "door crack 2"
EV_CHALICE_RIGHT, EV_CHALICE = 210, 211
EV_RULES = 270
T_POLL, T_HINTS, T_BUTTON = 150, 151, 152
COG_CRATE = 440
COG_BOOK = 400                                     # textbook k (BOOKS order): COG_BOOK + k
COG_HINT = 450                                     # PerceptionBrush k: COG_HINT + k
GROUP_STUDENTS, GROUP_DOOKS, GROUP_CRATE = 1, 2, 3

# TaSarTable.scr: the tables by Location (ItemInit): their book, the key for it and the key that frees the next book.
LOCATIONS = ["Offense", "Strategy", "Defense", "Intelligence"]
TABLE_BOOK = {"Offense": 435, "Strategy": 436, "Defense": 437, "Intelligence": 438}
TABLE_KEY = {"Offense": 9501, "Strategy": 9502, "Defense": 9503, "Intelligence": 9504}
TABLE_PLACED_KEY = {"Offense": 9517, "Strategy": 9518, "Defense": 9519, "Intelligence": 9520}
TABLES = {"Prop164": "Offense", "Prop166": "Strategy", "Prop163": "Defense", "Prop168": "Defense",
          "Prop165": "Intelligence", "Prop167": "Start"}
EV_TABLE = {name: 220 + k for k, name in enumerate(TABLES)}
# TaSarBook.scr :KeyInit: book item -> its table's key (taken on pick-up) and the key that must stand first.
BOOK_KEY = {435: 9501, 436: 9502, 437: 9503, 438: 9504}
BOOK_NEEDS = {435: 0, 436: 9517, 437: 9518, 438: 9519}
KEY_LIBRARY_DONE = 9516
BOOKS = [f"{location}{item}" for location in ("Start", *LOCATIONS) for item in (435, 436, 437, 438)]
EV_BOOK = {name: 230 + k for k, name in enumerate(BOOKS)}
# BookLetter.scr objects: DAT name -> letter number (ScriptParams p0); the podium (Prop159, PropTrigger.scr "Prop160
# Use") reads its book.
LETTER_OBJECTS = ["Prop160", "Brazier48", "Prop4", "Prop2", "Prop96", "Prop174", "Prop175", "Prop177", "Prop178",
                  "Prop179"]
EV_LETTER = {name: 260 + k for k, name in enumerate(LETTER_OBJECTS)}
EV_LETTER["Prop159"] = EV_LETTER["Prop160"]
CHALICES = ["Prop145", "Prop146", "Prop147", "Prop148", "Prop149", "Prop150", "Prop151", "Prop152"]
KEY_CHALICE = 9500                                 # TaSarChalice.scr: givekey 9500, GiveAttribute 0 10 0 288000
CHALICE_MIGHT = 10
# BookOfRules.scr: Ludwig's quest (key 57) ends with key 59; without it key 166. Item 391, 5000 experience.
KEY_LUDWIG, KEY_RULES_QUEST, KEY_RULES_FREE, ITEM_RULES, EXP_RULES = 57, 59, 166, 391, 5000

HINTS = ["PerceptionBrush0", "PerceptionBrush1", "PerceptionBrush2", "PerceptionBrush3", "PerceptionBrush4"]
PERCEPTION_SKILL = 29                              # evt.CheckSkill's id: the party's best Perception value
PERCEPTION_OPACITY = 0.5                           # the brushes' Alpha
HINT_EVENTS = {"PerceptionBrush4": EV_BOOK_BUTTON}     # PerceptionBrush3 (the crack's): its click (place_hints)
TOUCH_TRIGGERS = ["PitDoorTrigger1", "Trigger0", "Trigger1", "Trigger2", "Trigger3", "Trigger4"]
PARTY_REACH = 32                                   # native: MM9's touch fires on any part of the party
SPIKE_DAMAGE = 40                                  # Spikes1: DamagePerSecond 40, OneTimeDamage
UNTOUCHABLE = 0x20000000
SKY_TEXELS_PER_LT = 0.2                            # the skylights' sky04: one tile about 2 500 LT wide (Verhoffin's)

# MM9's bodies (ABC AnimBinding half extents x Scale x 2.56; animals by their mean half width): radius, height native.
BODIES = {"Guard": (38, 184), "GuardCaptain": (38, 184), "HalfOrcCaptain": (38, 195), "Dagrell": (64, 148),
          "Cow": (64, 133), "Pig": (26, 36), "Goat": (44, 87)}
CRATE_DAGRELL_SCALE = 0.75                         # DestructableProp0 SpawnObject "Dagrell Scale 0.75"
# The animals' MM9 rows (worlds/mm9 monster_data.txt: Move Med, AI Wimp, Hst 0; their 3D models are in actors.yml); the
# shared replacement table has none, so their base records are written here (as Drangheim Prison's ANIMAL_ROWS).
ANIMAL_ROWS = {"Cow": (9267, "Cow", 384), "Goat": (9268, "Goat", 384), "Pig": (9271, "Pig", 307)}


def as_float(value) -> float:
    """A DAT float stored in an int property (PerceptionValue 1092616192 = 10.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value)


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


class TasarAcademy(dungeon.Hooks):
    generator = "mm9r_tasaracademy"
    mover_events = {"LibraryDoor": (EV_LIBRARY_DOOR, "click"), "BookButtonFront1": (EV_BOOK_BUTTON, "click"),
                    "BookButtonBack1": (EV_BOOK_BUTTON, "click"), "Switch": (EV_SWITCH, "click"),
                    "Switch1": (EV_SWITCH1, "click")}

    def destructible_events(self, build) -> dict:
        """The cracked wall (dungeon/destructibles.py `break`): its death and its damage."""
        return {CRACK: (EV_CRACK, EV_CRACK_HIT)}

    # --- geometry -----------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        """The two skylights (the arena's open roof, the library's lantern; MM9's skymarker sky box): sky04 stretched
        so one tile spans about 2 500 LT, as Verhoffin Ruins' core; the bake's sky emitter (profile `emitters`)."""
        for polygon in polygons:
            if "skymarker" in polygon.texture.lower():
                origin = np.asarray(polygon.mapping[0], float)
                n = polygon.normal
                if abs(n[1]) > 0.7:          # a ceiling: across x and z
                    u, v = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
                else:                        # a wall: along its horizontal tangent and down
                    u = np.cross([0.0, 1.0, 0.0], n)
                    u /= np.linalg.norm(u)
                    v = np.array([0.0, -1.0, 0.0])
                polygon.mapping = (origin, u * SKY_TEXELS_PER_LT, v * SKY_TEXELS_PER_LT)
        return polygons

    # --- population ---------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        # the skill books and the Book of Rules are world items (dungeon/pickups.py); the book's pickup runs EV_RULES
        events = {**EV_TABLE, **EV_BOOK, **EV_LETTER, "BookRules": EV_RULES,
                  "Prop151": EV_CHALICE_RIGHT, **{name: EV_CHALICE for name in CHALICES if name != "Prop151"}}
        cogs = {**{name: COG_BOOK + k for k, name in enumerate(BOOKS)}, "DestructableProp0": COG_CRATE}
        self.placed = set()
        if PROPS.exists():
            import json
            self.placed = {entry["source_name"] for entry in json.loads(PROPS.read_text())}
            content.props(PROPS, events=events, cogs=cogs)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        missing = sorted(set(events) - self.placed)
        if PROPS.exists() and missing:
            print("note: scripted objects without a placement:", missing)
        # The spike pit under the trap doors (PropDamager Spikes1, MoveToFloor): Anskram's spikepit on the pit floor.
        if "Spikes1" not in self.placed:
            p = source.properties("Spikes1")
            floor = content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 8)
            floor = -256.0 if floor is None else floor
            content.entity("Spikes1", "mm9_spikepit", project.native([p["Pos"][0], floor, p["Pos"][2]]),
                           yaw_degrees(p.get("Rotation")))
        self.scale_lights(build)
        self.place_perception_hints(build)
        self.boxes = {name: self.box(build, name) for name in TOUCH_TRIGGERS}
        # the spikes' damage: the pit's floor under the trap doors (x 432-560, z -2064..-1936 LT, floor -256)
        self.boxes["Spikes"] = self.lt_box(build, (432, -260, -2064), (560, -200, -1936))

    def scale_lights(self, build) -> None:
        """MM9 weights each Light by its BrightScale (here the braziers' orange 0.7, the white fills 0.2-0.5 over
        radii of 300-450 LT); the shared converter writes the colour as authored, which makes the fills as strong as
        the braziers (the Ruined Temple's lesson). The BLV lights carry colour x BrightScale; the profile's
        direct_scale makes up the level. Bake-only lights keep their authored colour (lighting.py applies their
        BrightScale itself)."""
        scale = {light["name"]: light["bright_scale"] for light in build.lights}
        for record in build.package.metadata["lights"]:
            record["color"] = [int(round(c * scale.get(record["id"], 1.0))) for c in record["color"]]

    def lt_box(self, build, low, high) -> list:
        a, b = build.project.native(np.array(low, float)), build.project.native(np.array(high, float))
        return [np.minimum(a, b).round().astype(int).tolist(), np.maximum(a, b).round().astype(int).tolist()]

    def box(self, build, name) -> list:
        """A Trigger's box in native units (Pos +- Dims), widened by the party's reach in x and y."""
        p = build.source.properties(name)
        pos, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
        low, high = self.lt_box(build, pos - dims, pos + dims)
        return [[low[0] - PARTY_REACH, low[1] - PARTY_REACH, low[2]],
                [high[0] + PARTY_REACH, high[1] + PARTY_REACH, high[2]]]

    def place_perception_hints(self, build) -> None:
        """MM9's PerceptionBrushes (the two secret doors, the trap doors, the cracked wall, the bookcase's button): their
        Perception polygons as untouchable translucent faces with a cog, shown by the map script to a party with
        Perception 10 (PerceptionValue)."""
        package, source = build.package, build.source
        self.hints, self.hint_faces, self.hint_value = {}, 0, 0
        for k, name in enumerate(HINTS):
            self.hint_value = max(self.hint_value, int(round(as_float(source.properties(name)["PerceptionValue"]))))
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                rooms = build.content.rooms
                room = room_id(_side_room(rooms, polygon, 1) or _side_room(rooms, polygon, -1)
                               or rooms.owner(polygon.points.mean(0)))
                node = f"TRIGGER_perception_{name}_{i}"
                package.add_polygon(node, polygon, build.stats)
                package.room_nodes[room].append(node)
                surface = {"id": node[8:], "source_node": node, "flags": ["untouchable"], "cog_number": COG_HINT + k}
                clicks = dict(HINT_EVENTS, PerceptionBrush3=CLICK_EVENT_BASE + source.by_name[CRACK]["index"])
                if name in clicks:          # a hint box round a clickable thing takes its click
                    surface["trigger"] = {"event_id": clicks[name], "type": "click"}
                package.metadata["surfaces"].append(surface)
                self.hint_faces += 1
            self.hints[name] = COG_HINT + k
        self.perception_textures = sorted({p.texture.lower() for name in HINTS for p in source.polygons(name)
                                           if "perception" in p.texture.lower()})

    # --- actors -------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor = [], {}
        for o in source.objects:
            if o["class"] in ANIMAL_ROWS:
                row, title, speed = ANIMAL_ROWS[o["class"]]
                bases[o["name"]] = {"name": title, "attributes": 0, "hp": 4, "hostility_type": 0, "monster_info_id": row,
                                    "monster_id": row, "radius": 0, "height": 0, "move_speed": speed}
                content.report["omitted"] = [e for e in content.report["omitted"] if e["anchor"] != o["name"]]
        for o in source.objects:
            if o["class"] not in build.project.monster_classes or o["name"] not in bases:
                continue
            name, p = o["name"], o["properties"]
            radius, height = BODIES[o["class"]]
            scale = float(p.get("Scale", 1.0) or 1.0)
            script = str(p.get("ScriptName") or "").lower()
            group = GROUP_STUDENTS if "tasarstudent" in script and o["class"] == "Guard" else \
                GROUP_DOOKS if "tasarstudent" in script else 0
            # Guards, students, the teacher and Dook's captains are hostile to the party, as in MM9: their scripts
            # (Guardbase.scr's baseMelee, TaSarStudent/Teacher/GuardDuty.scr) have no hostility include, so MM9's
            # default makes them enemies, and their rows' Hostility 4 says so (the Hostility Group column is not read
            # by MM9's AI). The farm animals keep their rows' Hostility 0 (FarmAnimal.inc: they flee, never attack).
            actor = content.actor(o, bases[name], sector_of_room, group=group,
                                  floor_query_lt=p["Pos"][1] + 24,
                                  radius=int(round(radius * scale)), height=int(round(height * scale)))
            self.actor[name] = actor["actor_index"]
            out.append(actor)
        # The Dagrell in the crate (DestructableProp0 SpawnObject "Dagrell Scale 0.75"): hidden at the crate until
        # Trigger4 smashes it.
        crate = source.properties("DestructableProp0")
        dagrell = next(o for o in source.objects if o["class"] == "Dagrell")
        fake = {"name": "CrateDagrell", "class": "Dagrell",
                "properties": {"Pos": crate["Pos"], "Rotation": crate.get("Rotation"), "Scale": CRATE_DAGRELL_SCALE}}
        radius, height = BODIES["Dagrell"]
        # Dagrell0 is MM9's CacheOnly model cache for that spawn (never placed itself): its row is the template
        template = content.monster_bases(cache_only=True)[dagrell["name"]]
        actor = content.actor(fake, template, sector_of_room, group=GROUP_CRATE, hidden=True,
                              floor_query_lt=crate["Pos"][1] + 24, radius=int(round(radius * CRATE_DAGRELL_SCALE)),
                              height=int(round(height * CRATE_DAGRELL_SCALE)))
        self.actor["CrateDagrell"] = actor["actor_index"]
        out.append(actor)
        self.monster_ids = {o["class"]: bases[o["name"]]["monster_id"] for o in source.objects if o["name"] in bases}
        return out

    # --- map script ---------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Ta'Sar Academy")
        boxes = self.boxes
        script.lines += [
            "local GROUPS = {" + ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}"
                                           for g, ids in sorted(script.groups.items())) + "}",
            "local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end",
            "local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end",
            "local function toggleGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end end",
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z + 170 >= b[1][3] and z <= b[2][3] end",
            "local function hurt(amount, kind) evt.DamagePlayer(Players.All, kind or const.Damage.Physical, amount) end",
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            f"local BOX = {{{', '.join(f'{k} = {{{lua.point(v[0])}, {lua.point(v[1])}}}' for k, v in sorted(boxes.items()))}}}",
            "",
        ]
        script.doors()
        script.chests()
        lines, registrations = self.script_library(build)
        lines += self.script_mechanisms(build)
        registrations += [(EV_BOOK_BUTTON, "Book", "Book"), (EV_SWITCH, "Switch", "Switch"),
                          (EV_SWITCH1, "Switch", "Switch"), (EV_CRACK, "Cracked wall", None),
                          (EV_CRACK_HIT, "Cracked wall", None)]
        more, more_registrations = self.script_objects(build)
        lines += more
        registrations += more_registrations
        lines += self.script_hints()
        lines += self.script_volumes()
        registrations += [(timer, title, None, "timer") for timer, title in (
            (T_POLL, "Trigger volumes"), (T_HINTS, "Perception hints"), (T_BUTTON, "Book button"))]
        lines += [
            "",
            "handlers[1] = function()   -- map load: the scripts' Init (TaSarBook.scr :Init, BookOfRules.scr :Main,",
            "                           -- the crate, the sparring)",
            "    if var(\"Init\") == 0 then",
            "        set(\"Init\", 1)",
            "        for _, item in ipairs({435, 436, 437, 438}) do set(\"AtStart\" .. item, 1) end",
            "    end",
            "    showBooks()",
            f"    if var(\"CrateBroken\") == 1 then evt.SetSprite({COG_CRATE}, false) end",
            "    if var(\"Sparring\") == 1 then sparringRelations() end",
            f"    if MM9.hasKey({KEY_LIBRARY_DONE}) == 1 then openGroup(\"LibraryDoor\") end",
            "    set(\"PerceptionHints\", 0)",
            "    updateHints()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "end",
        ]
        script.add(lines, *registrations, (1, "Map load", None))
        return script.finish(on_load=[1])

    def script_library(self, build) -> tuple[list[str], list]:
        """The library puzzle (TaSarBook.scr, TaSarTable.scr), the Book of Rules (BookOfRules.scr, PropTrigger.scr)."""
        books = ", ".join(f"\"{name}\"" for name in BOOKS)
        lines = [
            "",
            "-- The library puzzle. TaSarBook.scr: the four textbooks (items 435-438) lie on the Start table; a book is taken",
            "-- (:OnUse) when the key for the book before it is held (:KeyCheck: 436 needs 9517, 437 9518, 438 9519) and its",
            "-- own table's key is not (:PlacedBook), and only until the library is solved (key 9516). TaSarTable.scr :OnUse:",
            "-- a table given its own book gives its two keys (Offense 435: 9501, 9517; Strategy 436: 9502, 9518; Defense",
            "-- 437: 9503, 9519; Intelligence 438: 9504, 9520) and takes every textbook the party carries, showing each on",
            "-- itself (\"<Location><item>\"); :CheckAllKeys: with 9501-9504 key 9516, and the library's door opens.",
            f"local BOOKS = {{{books}}}",
            f"local BOOK_KEY = {{[435] = 9501, [436] = 9502, [437] = 9503, [438] = 9504}}",
            f"local BOOK_NEEDS = {{[435] = 0, [436] = 9517, [437] = 9518, [438] = 9519}}",
            "local function showBooks()",
            "    for k, name in ipairs(BOOKS) do",
            "        local location, item = string.match(name, \"^(%a+)(%d+)$\")",
            f"        evt.SetSprite({COG_BOOK} + k - 1, var(\"At\" .. location .. item) == 1)",
            "    end",
            "end",
            "local function takeBook(location, item)",
            "    if var(\"At\" .. location .. item) ~= 1 then return end",
            "    local needs = BOOK_NEEDS[item]",
            "    if needs ~= 0 and MM9.hasKey(needs) == 0 then return end",
            "    if MM9.hasKey(BOOK_KEY[item]) == 1 then return end",
            f"    if MM9.hasKey({KEY_LIBRARY_DONE}) == 1 then return end",
            "    set(\"At\" .. location .. item, 0)",
            "    showBooks()",
            f"    give(item, \"tasaracademy:\" .. location .. item)",
            "end",
            "local function placeBooks(location, book, key, placedKey)",
            f"    if book ~= 0 and MM9.hasItem(book, \"tasaracademy:table\") == 1 then MM9.giveKey(key); MM9.giveKey(placedKey) end",
            "    for item = 435, 438 do",
            "        if MM9.hasItem(item, \"tasaracademy:table\") == 1 then",
            "            MM9.takeItem(item, \"tasaracademy:table\")",
            "            set(\"At\" .. location .. item, 1)",
            "        end",
            "    end",
            "    showBooks()",
            f"    if MM9.hasKey(9501) == 1 and MM9.hasKey(9502) == 1 and MM9.hasKey(9503) == 1 and MM9.hasKey(9504) == 1",
            f"            and MM9.hasKey({KEY_LIBRARY_DONE}) == 0 then",
            f"        MM9.giveKey({KEY_LIBRARY_DONE})",
            "        evt.PlaySoundName(\"door/door01open.wav\", 0, 0, 0)",
            "        openGroup(\"LibraryDoor\")",
            "    end",
            "end",
        ]
        registrations = []
        for name, location in TABLES.items():
            book, key, placed = (0, 0, 0) if location == "Start" else (TABLE_BOOK[location], TABLE_KEY[location],
                                                                          TABLE_PLACED_KEY[location])
            lines.append(f"handlers[{EV_TABLE[name]}] = function() placeBooks(\"{location}\", {book}, {key}, {placed}) end"
                         f"   -- {name}, TaSarTable.scr \"{location}\"")
            registrations.append((EV_TABLE[name], "Table", "Table"))
        for name in BOOKS:
            location, item = name[:-3], int(name[-3:])
            lines.append(f"handlers[{EV_BOOK[name]}] = function() takeBook(\"{location}\", {item}) end"
                         f"   -- {name}, TaSarBook.scr \"{item} {location}\"")
            registrations.append((EV_BOOK[name], "Textbook", "Book"))
        lines += [
            "",
            f"-- The library's secret door (LibraryDoor, Locked): only :CheckAllKeys opens it (unlock, use, lock: it stays open).",
            f"handlers[{EV_LIBRARY_DOOR}] = function()",
            f"    if MM9.hasKey({KEY_LIBRARY_DONE}) == 0 then evt.StatusText(\"The door is locked.\") end",
            "end",
            "",
            f"-- The Book of Rules (BookOfRules.scr :Onuse): a world item ({ITEM_RULES}, hidden with key {KEY_RULES_QUEST} or "
            f"{KEY_RULES_FREE}); its pickup gives {EXP_RULES} experience, the quest sound and key {KEY_RULES_QUEST} on "
            f"Ludwig's errand (key {KEY_LUDWIG}), else key {KEY_RULES_FREE}.",
            f"handlers[{EV_RULES}] = function()",
            f"    if MM9.hasKey({KEY_RULES_QUEST}) == 1 or MM9.hasKey({KEY_RULES_FREE}) == 1 then return end",
            f"    MM9.giveKey(MM9.hasKey({KEY_LUDWIG}) == 1 and {KEY_RULES_QUEST} or {KEY_RULES_FREE})",
            f"    {experience_lua(EXP_RULES, KEY_RULES_QUEST)}",
            "    MM9.playSound(\"sounds/events/quest.wav\")",
            "end",
        ]
        registrations.append((EV_RULES, "Book of Rules", "Book"))
        registrations.append((EV_LIBRARY_DOOR, "Door", "Door"))
        return lines, registrations

    def script_mechanisms(self, build) -> list[str]:
        return [
            "",
            "-- The rotating bookcase (RotatingBookcase1): either book button (BookButtonFront1, its DoubleDoor",
            "-- BookButtonBack1) presses in and swings the bookcase (OpenTrigger toggle); the bookcase's Open/CloseTriggers",
            "-- release the buttons. Pressed while it swings, nothing (the buttons are locked).",
            f"handlers[{EV_BOOK_BUTTON}] = function()",
            "    if var(\"ButtonDown\") == 1 then return end",
            "    set(\"ButtonDown\", 1)",
            "    openGroup(\"BookButtonFront1\"); openGroup(\"BookButtonBack1\")",
            "    toggleGroup(\"RotatingBookcase1\")",
            "    set(\"BookcaseTurns\", var(\"BookcaseTurns\") + 1)",
            f"    evt.StartTimer({T_BUTTON}, seconds(5.5))",
            "end",
            f"handlers[{T_BUTTON}] = function()",
            f"    evt.StopTimer({T_BUTTON})",
            "    if var(\"ButtonDown\") ~= 1 then return end",
            "    set(\"ButtonDown\", 0)",
            "    closeGroup(\"BookButtonFront1\"); closeGroup(\"BookButtonBack1\")",
            "end",
            "",
            "-- The wall switches (Switch, Switch1; StartOpen): each click swings the switch and its secret door (SecretDoor1,",
            "-- SecretDoor0: Open/CloseTriggers toggle), which shuts again after 7 s (CloseWaitTime); the hint goes",
            "-- (PerceptionBrush1, PerceptionBrush0 off). MM9 locks Switch1 after its second swing; not carried (README).",
            f"handlers[{EV_SWITCH}] = function()",
            "    toggleGroup(\"Switch\"); openGroup(\"SecretDoor1\")",
            "    set(\"FoundPerceptionBrush1\", 1); set(\"PerceptionHints\", 0); updateHints()",
            "end",
            f"handlers[{EV_SWITCH1}] = function()",
            "    toggleGroup(\"Switch1\"); openGroup(\"SecretDoor0\")",
            "    set(\"FoundPerceptionBrush0\", 1); set(\"PerceptionHints\", 0); updateHints()",
            "end",
            "",
            "-- The cracked wall between the pit's tunnel and the library (\"door crack\", DestructableBrush, 25 hit points:",
            "-- its DamageTrigger destroys \"door crack 2\", its DeathTrigger turns PerceptionBrush3 off): scene destructibles;",
            "-- weapons break it as in MM9, a click still does (the shared click's killing blow).",
            f"handlers[{EV_CRACK_HIT}] = function() evt.DestroyDestructible({build.source.by_name[CRACK2]['index']}) end",
            f"handlers[{EV_CRACK}] = function()   -- broken",
            "    set(\"CrackBroken\", 1)",
            f"    evt.DestroyDestructible({build.source.by_name[CRACK2]['index']})",
            "    evt.PlaySoundName(\"events/rockfall.wav\", 0, 0, 0)",
            "    set(\"PerceptionHints\", 0); updateHints()",
            "end",
        ]

    def script_objects(self, build) -> tuple[list[str], list]:
        """The chalices, the skill books, the letters, the crate, the sparring."""
        source = build.source
        lines = [
            "",
            f"-- The chalices (TaSarChalice.scr): the right one (Prop151, \"Right\") gives the active character {CHALICE_MIGHT}",
            f"-- Might for a while (GiveAttribute 0 10 0 288000: MM9's stat 0 = Might) and key {KEY_CHALICE}; here once",
            "-- per character (MM9 has no guard; a temporary bonus until rest). The others do nothing (\";damage player\").",
            f"handlers[{EV_CHALICE_RIGHT}] = function()",
            "    local who = math.max(0, evt.GetCurrentPlayerIndex())",
            "    if var(\"Chalice\" .. who) == 1 then evt.StatusText(\"Refreshing!\") return end",
            "    set(\"Chalice\" .. who, 1)",
            f"    AddValue(MightBonus, {CHALICE_MIGHT})",
            f"    MM9.giveKey({KEY_CHALICE})",
            f"    evt.StatusText(\"+{CHALICE_MIGHT} Might (Temporary)\")",
            "end",
            f"handlers[{EV_CHALICE}] = function() end",
        ]
        registrations = [(EV_CHALICE_RIGHT, "Chalice", "Chalice"), (EV_CHALICE, "Chalice", "Chalice")]
        lines += ["", "-- Letters and books (BookLetter.scr: DoLetter <p0>; the podium Prop159 reads its book Prop160 by"
                  " PropTrigger.scr \"Prop160 Use\")."]
        for name in LETTER_OBJECTS:
            number = int(source.properties(name)["ScriptParams"].split()[0])
            title, text = letter(number)
            lines.append(f"handlers[{EV_LETTER[name]}] = function() evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) "
                         f"end   -- {name}, BookLetter.scr \"{source.properties(name)['ScriptParams'].strip()}\"")
            registrations.append((EV_LETTER[name], title, "Read"))
        dooks = self.monster_ids.get("HalfOrcCaptain", 0)
        guards = sorted({self.monster_ids[c] for c in ("Guard", "GuardCaptain") if c in self.monster_ids})
        relations = "; ".join(f"evt.SetMonsterRelation({g}, {dooks}, 2); evt.SetMonsterRelation({dooks}, {g}, 2)"
                              for g in guards)
        lines += [
            "",
            "-- The sparring (Trigger0-3 in the arena's mouths: GuardCaptain0 'Fight'; TaSarTeacher.scr :OnSpawn sends",
            "-- 'Hate' to Student0-3 and DooksGuardCaptain0/1; TaSarStudent.scr :OnHate AddEnemy: the students' enemy",
            "-- is \"DooksGuardCaptain\", the captains' \"Guard\"). Native: the Guard rows and the Half Orc Captain row",
            "-- become enemies of each other as well as of the party.",
            f"function sparringRelations() {relations} end",
            "-- A dead teacher takes no 'Fight' (MM9.receives): nobody is told to hate, the sparring never starts.",
            "local function sparring()",
            "    if var(\"Sparring\") == 1 then return end",
            f"    if not MM9.receives(\"tasaracademy\", \"GuardCaptain0\", \"Fight\", {self.actor['GuardCaptain0']}) then return end",
            "    set(\"Sparring\", 1)",
            "    sparringRelations()",
            "end",
            "",
            "-- The crate in the store room (Trigger4: DestructableProp0 'Destroy'; its SpawnObject \"Dagrell Scale 0.75\"):",
            "-- the crate is smashed and a small Dagrell comes out of it.",
            "local function smashCrate()",
            "    if var(\"CrateBroken\") == 1 then return end",
            "    set(\"CrateBroken\", 1)",
            f"    evt.SetSprite({COG_CRATE}, false)",
            "    evt.PlaySoundName(\"events/crate_smash.wav\", 0, 0, 0)",
            f"    evt.SetMonGroupBit({GROUP_CRATE}, MonsterBits.Invisible, false)",
            f"    evt.SetMonGroupBit({GROUP_CRATE}, MonsterBits.Hostile, true)",
            "end",
        ]
        return lines, registrations

    def script_hints(self) -> list[str]:
        hints = ", ".join(f"{name} = {cog}" for name, cog in self.hints.items())
        return [
            "",
            f"-- The PerceptionBrushes (Perception {self.hint_value}): the secret doors (0, 1), the trap doors (2), the cracked",
            "-- wall (3), the bookcase's button (4) show to a party with the Perception for them; the secret doors' go once",
            "-- found (their switches turn them off), the crack's once broken. Checked on load and every 3 s.",
            f"local function perceptive() return evt.CheckSkill({PERCEPTION_SKILL}, 0, {self.hint_value}) end",
            f"local HINTS = {{{hints}}}",
            "function updateHints()",
            "    local want = perceptive() and 2 or 1",
            "    if var(\"PerceptionHints\") == want then return end",
            "    set(\"PerceptionHints\", want)",
            "    for name, cog in pairs(HINTS) do",
            "        local gone = var(\"Found\" .. name) == 1 or (name == \"PerceptionBrush3\" and var(\"CrackBroken\") == 1)",
            "        evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or gone)",
            "    end",
            "end",
            f"handlers[{T_HINTS}] = updateHints",
        ]

    def script_volumes(self) -> list[str]:
        return [
            "",
            "-- The trap doors (PitDoorTrigger1: PitDoorRight1 toggle, its DoubleDoor PitDoorLeft1; CloseWaitTime 1, the",
            "-- leaves' CloseTrigger turns the trigger on again) and the spikes under them (Spikes1: 40 once on landing).",
            "local function trapDoors()",
            "    openGroup(\"PitDoor\")",
            "    evt.PlaySoundName(\"door/door01open.wav\", 0, 0, 0)",
            "    set(\"PitTrips\", var(\"PitTrips\") + 1)",
            "end",
            "",
            "-- MM9's Trigger volumes, polled four times a second: each fires once on entry (the trap re-arms).",
            "local VOLUMES = {",
            "    {name = \"PitDoorTrigger1\", run = trapDoors, rearm = true},",
            "    {name = \"Trigger0\", run = sparring}, {name = \"Trigger1\", run = sparring},",
            "    {name = \"Trigger2\", run = sparring}, {name = \"Trigger3\", run = sparring},",
            "    {name = \"Trigger4\", run = smashCrate},",
            "    {name = \"Spikes\", run = function()",
            f"        hurt({SPIKE_DAMAGE}); set(\"SpikeHits\", var(\"SpikeHits\") + 1) end, rearm = true}},",
            "}",
            "local inside, polls = {}, 0",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    local x, y, z = evt.GetPartyPosition()",
            "    polls = polls + 1",
            "    for _, v in ipairs(VOLUMES) do",
            "        local now = inBox(BOX[v.name], x, y, z)",
            "        if now and not inside[v.name] and var(\"Done\" .. v.name) == 0 then",
            "            if not v.rearm then set(\"Done\" .. v.name, 1) end",
            "            v.run()",
            "        end",
            "        inside[v.name] = now",
            "    end",
            f"    if polls % 12 == 0 then updateHints() end",
            "end",
        ]

    def scene(self, build, scene: dict) -> None:
        """The perception hints: translucent, two-sided."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]

        def faces_of(texture: str) -> list[int]:
            alias = build.source.aliases[texture.lower()]["alias"].lower()
            return sorted(f["index"] for f in blv["faces"] if str(f.get("texture_name", "")).lower() == alias)

        hints = sorted({i for t in self.perception_textures for i in faces_of(t)})
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        scene.setdefault("translucent_faces", []).append(
            {"faces": hints, "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0], "two_sided": True})

    def report(self, build) -> dict:
        return {"scripted": {"actors": self.actor, "boxes": self.boxes, "hints": self.hints}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, TasarAcademy()))
