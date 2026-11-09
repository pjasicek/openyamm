#!/usr/bin/env python3
"""
Hall of the Gods, MM9 rework: MM9's HALLOFTHEGODS.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_hallofthegods/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_hallofthegods/convert.py --plan     # rooms only: work/rooms*.png

The hall is an open colonnaded temple inside MM9's skymarker box, floating over the Arslegaard sky box's clouds.
overrides.yml holds the model rules and the stained glass; this file adds the sky box faces, the population
(props.json from ../../props/mm9_hallofthegods_claude, the gods and the Wyrdes) and MM9's scripted objects as native
Lua, each citing its .scr (README.md, "Scripted objects"):
- Krohn on his throne (NPC335.scr :StopNjam): key 108 without 191 gives Njam's Key (576), key 191, 218 000 experience;
- Skraelos (NPC336.scr, ScriptParams Hall: :Teleport, :sixfires, :Failure): key 101 without 102 sends the party to the
  Afterworld (key 379); key 103 without 189: key 189 and 52 000 experience; key 392 takes keys 379-392 and sends the
  party back to the Afterworld;
- Fre (NPC337.scr :GoldenHonk): key 346 without 347 takes the Golden Honk (369) for 10 000 gold, 80 000 experience;
- the Great Honk (NPC377.scr): a click opens RUDE 377; it wanders (BaseWander.inc);
- the bill of sale on the bench (BookLetter.scr "480 Letter 1");
- the end of the game (WinMan.scr Part2, WG_NPC334/335/336.scr): with key 109 and without the Writ of Fate (394) the
  cinematic gods_epilogue plays (cinematics_hall.py: the gods and the Wyrdes gather round Hanndl, the WG_Scene7Cam
  shots and the voices), then the Writ of Fate is given and Krohn is back on his throne (DoHighScore: the world's
  completion on key 109).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from dungeon import lua, tables  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402

import numpy as np  # noqa: E402
import yaml  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

SKY_MODEL = "Snow"                  # MM9's DemoSkyWorldModel: the Arslegaard sky box (a 256 LT double-walled cube)
PROPS = PROJECT / "props.json"
LETTERS = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
ACTOR_TXT = ROOT / "mm9/extracted/DATA/DATA/ACTOR.txt"
NPC_REPLACEMENTS = ROOT / "tools/mm9_import_discovery/mm9_npc_legacy_replacements.tsv"
DESCRIPTORS = ROOT / "assets_dev/engine/data_tables/monster_descriptors.txt"

EV_LETTER = 76                       # Prop3: BookLetter.scr "480 Letter 1"
LETTER_ID = 480
GROUP_CINEMA, GROUP_KROHN = 1, 2
# DAT object -> (NPC replacement class: the old importer's MM9 NPC table, RUDE id or 0, cinema actor)
NPCS = {
    "Krohn0": ("Krohn", 335, False),             # NPC335.scr, NPCNbr 335: on the throne
    "Skraelos": ("Skraelos", 336, False),        # NPC336.scr, ScriptParams Hall, NPCNbr 336
    "Fre": ("Fre", 337, False),                  # NPC337.scr, NPCNbr 337
    "Hanndl": ("Hanndl", 0, True),               # WG_NPC334.scr: hidden until the cinema
    "Krohn": ("Krohn", 0, True),                 # WG_NPC335.scr
    "Skraelos0": ("Skraelos", 0, True),          # WG_NPC336.scr
    "WyrdeoftheKnowing0": ("WyrdeoftheKnowing", 0, True),             # hidden by WG_NPC334.scr :Loop
    "WyrdeoftheKnown0": ("WyrdeoftheKnown", 0, True),
    "WyrdeoftheKnown1": ("WyrdeoftheUnknown", 0, True),             # class WyrdeoftheUnknown
}
# MM9's bodies (ABC AnimBinding extents, half sizes LT, x the DAT Scale x 2.56): the DAT model of each object
# (Krohn.abc 20 x 54, Lich.abc 10 x 35, goose.abc 10 x 16 for TheGreatHonk.abc which MM9 does not ship,
# wyrd_old.abc 12 x 34, wyrd_mature/young.abc 12 x 30 for the Wyrde classes' missing ABCs).
BODIES = {"models\\krohn.abc": (20, 54), "models\\lich.abc": (10, 35), "models\\thegreathonk.abc": (10, 16),
          "models\\wyrdeoftheknown.abc": (12, 34), "models\\wyrdeoftheknowing.abc": (12, 30)}
BODY_BY_NAME = {"WyrdeoftheKnown1": (12, 30)}    # the Unknown (wyrd_young.abc) in a Known class object

# keys and items (raw MM9 numbers: keys are QBits 90000 + key, items MM9.ItemIds)
KEY_TAMUR, KEY_NJAM_DONE, ITEM_NJAM_KEY = 108, 191, 576            # NPC335.scr :StopNjam
KEY_SENT, KEY_BACK, KEY_ARRIVED = 101, 102, 379                    # NPC336.scr :Teleport
KEY_FIRES_DONE, KEY_FIRES_REWARD = 103, 189                        # NPC336.scr :sixfires
KEY_FAILED = 392                                                   # NPC336.scr :Failure (takes 379-392)
KEY_HONK_FOUND, KEY_HONK_DONE, ITEM_GOLDEN_HONK = 346, 347, 369    # NPC337.scr :GoldenHonk
KEY_NJAM_BEATEN, ITEM_WRIT = 109, 394                              # WinMan.scr :Init, :End
AFTERWORLD = "afterworld.blv"   # the rebuilt Afterworld (mm9r_afterworld_blv)
PEACEFUL_ALLY = (352 - 1) // 3 + 1   # monster type of row 352 (Peasant Human1 FemaleB A): neutral to the party
GREAT_HONK_ROW = 9262                # worlds/mm9 monster_data.txt: MM9 262 The Great Honk (the replacement table has none)


def rude_exit_event(index: int) -> int:
    """game/mm9/Mm9RudeDialogue.h: the event a dialogue with actor object `index` runs when it closes."""
    return 50000 + index


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "") + '"'


def letter(number: int) -> tuple[str, str]:
    with open(LETTERS, newline="", encoding="latin-1") as stream:
        for row in csv.reader(stream):
            if row and row[0].strip() == str(number):
                return row[1].strip(), row[2].replace("\r", "").strip()
    raise SystemExit(f"letter {number}: not in {LETTERS}")


def npc_rows() -> dict:
    sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
    from transcode_mm9_dat_to_odm import read_mm9_npc_replacements
    return read_mm9_npc_replacements(ACTOR_TXT, NPC_REPLACEMENTS, DESCRIPTORS)


class HallOfTheGods(dungeon.Hooks):
    generator = "mm9r_hallofthegods"

    # --- geometry -------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        """The six skymarker faces (MM9 draws its Arslegaard sky box through them: the hall floats over a sea of
        clouds under a blue sky with the sun overhead) take the sky box's own six textures, one tile per face. Each
        skymarker face takes the texture and the texel axes of the Snow model's inner face with the same normal,
        carried over by the per-axis scale between the two boxes, so the clouds lie the way MM9's camera sees them;
        the sky is drawn at the box walls (a few thousand LT away) instead of at infinity. The bake shows them at
        their texture brightness (an emitter with `display`, profile mm9_hallofthegods.yml)."""
        sky = [p for p in build.source.polygons(SKY_MODEL)]
        snow_low = np.min([p.points.min(0) for p in sky], axis=0) + 4      # the inner shell: 4 LT inside the outer
        snow_high = np.max([p.points.max(0) for p in sky], axis=0) - 4
        inner = [p for p in sky if np.all(p.points.min(0) >= snow_low - 0.5) and np.all(p.points.max(0) <= snow_high + 0.5)]
        centre_snow = (snow_low + snow_high) / 2
        markers = [p for p in polygons if "skymarker" in p.texture.lower()]
        walls_low = np.array([min(p.points[:, a].min() for p in markers if abs(p.normal[a]) > 0.9) for a in range(3)])
        walls_high = np.array([max(p.points[:, a].max() for p in markers if abs(p.normal[a]) > 0.9) for a in range(3)])
        centre_big = (walls_low + walls_high) / 2
        k = (snow_high - snow_low) / (walls_high - walls_low)
        self.sky_faces = {}
        for polygon in markers:
            n = polygon.normal
            # the inner Snow face facing the same way (toward the box centre)
            match = max(inner, key=lambda q: float(np.dot(q.normal, n)))
            if float(np.dot(match.normal, n)) < 0.99:
                raise SystemExit(f"sky face {n}: no Snow face with that normal")
            origin, u, v = (np.asarray(a, float) for a in match.mapping)
            polygon.texture = match.texture
            polygon.notes.update(width=match.notes["width"], height=match.notes["height"])
            polygon.mapping = (centre_big + (origin - centre_snow) / k, u * k, v * k)
            self.sky_faces[match.texture.split("\\")[-1]] = [round(float(c), 2) for c in n]
        return polygons

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        if PROPS.exists():
            build.content.props(PROPS, events={"Prop3": EV_LETTER})
        else:
            print("note: props.json is missing; no decorations placed")
        report = build.content.report["omitted"]
        report += [
            {"anchor": "WinMan", "class": "ScriptObject",
             "reason": "WinMan.scr Part2 (the end-game cinema manager, parked outside the hall): the map Lua (README)"},
            {"anchor": "WG_Scene7Cam1-11", "class": "Camera",
             "reason": "the cinema's cameras: no scripted camera in the engine (README, Deviations)"},
            {"anchor": "HanndlMarker", "class": "Marker", "reason": "Hanndl's cinema mark: his place in the cinema (Lua)"},
            {"anchor": "Scene7MK1", "class": "Marker", "reason": "WG_Scene7Cam1's pan target (cinema camera)"},
            {"anchor": "DragonAzure0/1", "class": "DragonAzure",
             "reason": "no MONSTERS.txt row, and MM9 ships no DragonAzure.abc model: nothing to show"},
            {"anchor": "AmbientSound0-22", "class": "AmbientSound", "reason": "ambient sound: a later pass"},
        ]
        p = build.source.properties("HanndlMarker")["Pos"]
        floor = build.content.floor_at(p[0], p[2], p[1] + 24)
        self.hanndl_mark = build.project.native([p[0], floor, p[2]]).round().astype(int) + np.array([0, 0, 1])

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        rows = npc_rows()
        out, self.actor, self.object, self.cinema = [], {}, {}, []
        for o in source.objects:
            name, p = o["name"], o["properties"]
            if name in NPCS:
                klass, rude, cinema = NPCS[name]
                row = rows[klass]
                base = {"name": row.role, "attributes": 0, "hp": max(row.hit_points, 1), "hostility_type": 0,
                        "monster_info_id": row.legacy_actor_id, "monster_id": row.legacy_actor_id,
                        "radius": row.radius, "height": row.height, "move_speed": 0}
            elif name == "TheGreatHonk0":    # MM9 monster row 9262 (The Great Honk, "God's Pet"); NPC377.scr: DoRude 377
                rude, cinema = 377, False
                base = {"name": "The Great Honk", "attributes": 0, "hp": 1800, "hostility_type": 0,
                        "monster_info_id": GREAT_HONK_ROW, "monster_id": GREAT_HONK_ROW, "radius": 38, "height": 82,
                        "move_speed": 384}
            else:
                continue
            half, tall = BODY_BY_NAME.get(name) or BODIES[str(p.get("Filename", "")).lower()]
            scale = float(p.get("Scale", 1.0) or 1.0)
            group = GROUP_CINEMA if cinema else GROUP_KROHN if name == "Krohn0" else 0
            actor = content.actor(o, base, sector_of_room, group=group, hidden=cinema, friendly=True,
                                  floor_query_lt=p["Pos"][1] + 24,
                                  radius=int(round(half * scale * SCALE)), height=int(round(2 * tall * scale * SCALE)))
            actor["mm9_source_object_index"] = o["index"]
            # The gods' picture rows (565 KnightPlate, 568 BLich, 555 Guard C) are hostile to the party by the monster
            # relation table even with the aggressor bit clear: they take the relations of the peasant family of
            # Fre's row 352 (ally = monster type, GameplayActorService::relationMonsterId), as MM9's gods are friends.
            actor["ally"] = PEACEFUL_ALLY
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = name != "TheGreatHonk0"            # the Great Honk wanders (BaseWander.inc)
            self.actor[name], self.object[name] = actor["actor_index"], o["index"]
            if name == "Hanndl":
                self.hanndl_start = [actor["position"][k] for k in ("x", "y", "z")]   # the cinematic's walk start
            if cinema:
                self.cinema.append(name)
            out.append(actor)
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        import cinematics_hall as cinema
        import cutscenes
        script = lua.Script(build, "Hall of the Gods")
        script.doors()
        script.chests()
        arrival = self.afterworld_arrival(build)
        objects = self.object
        title, text = letter(LETTER_ID)
        lines = [
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            "local function questSound() MM9.playSound(\"events/quest.wav\") end   -- MM9 quest.wav: the shared quest sound",
            "-- ExitTrigger0 (Afterworld, StartPoint0): MM9's scripts trigger it (`trigger ExitTrigger0 trigger`); the volume",
            "-- stands in the air beyond the hall's east end, out of reach. The move goes to its arrival.",
            "local function toAfterworld()",
            f"    set(\"ToAfterworld\", var(\"ToAfterworld\") + 1)",
            f"    evt.MoveToMap({arrival[0]}, {arrival[1]}, {arrival[2]}, {arrival[3]}, 0, 0, 0, 1, \"{AFTERWORLD}\")",
            "end",
            "",
            f"-- Krohn (NPC335.scr :OnRude :StopNjam): key {KEY_TAMUR} (Tamur spoken to) without {KEY_NJAM_DONE}: Njam's Key "
            f"({ITEM_NJAM_KEY}), key {KEY_NJAM_DONE},",
            "-- 218000 experience and the quest sound.",
            f"handlers[{rude_exit_event(objects['Krohn0'])}] = function()   -- Krohn0",
            f"    if MM9.hasKey({KEY_NJAM_DONE}) == 0 and MM9.hasKey({KEY_TAMUR}) == 1 then",
            f"        give({ITEM_NJAM_KEY}, \"NPC335.scr:StopNjam\")",
            f"        MM9.giveKey({KEY_NJAM_DONE})",
            f"        {experience_lua(218000, KEY_NJAM_DONE)}",
            "        questSound()",
            "    end",
            "end",
            "",
            "-- Skraelos (NPC336.scr :OnRude with ScriptParams Hall): :Teleport (key 101 without 102: key 379 and off to the",
            "-- Afterworld), :sixfires (key 103 without 189: key 189, 52000 experience, the quest sound), :Failure (key 392:",
            "-- keys 379-392 taken, back to the Afterworld). The six fires' scenes (:Guilt ... :Rebirth, keys 380-390) run",
            "-- against the Afterworld's objects and are carried there (README).",
            f"handlers[{rude_exit_event(objects['Skraelos'])}] = function()   -- Skraelos",
            "    local away = false",
            f"    if MM9.hasKey({KEY_BACK}) == 0 and MM9.hasKey({KEY_SENT}) == 1 then",
            f"        MM9.giveKey({KEY_ARRIVED})",
            "        away = true",
            "    end",
            f"    if MM9.hasKey({KEY_FIRES_REWARD}) == 0 and MM9.hasKey({KEY_FIRES_DONE}) == 1 then",
            f"        MM9.giveKey({KEY_FIRES_REWARD})",
            f"        {experience_lua(52000, KEY_FIRES_REWARD)}",
            "        questSound()",
            "    end",
            f"    if MM9.hasKey({KEY_FAILED}) == 1 then",
            f"        for key = {KEY_ARRIVED}, {KEY_FAILED} do MM9.takeKey(key) end",
            "        away = true",
            "    end",
            "    if away then toAfterworld() end",
            "end",
            "",
            f"-- Fre (NPC337.scr :OnRude :GoldenHonk): key {KEY_HONK_FOUND} without {KEY_HONK_DONE}: 10000 gold, 80000 "
            f"experience, the quest sound,",
            f"-- the Golden Honk ({ITEM_GOLDEN_HONK}) taken, key {KEY_HONK_DONE}.",
            f"handlers[{rude_exit_event(objects['Fre'])}] = function()   -- Fre",
            f"    if MM9.hasKey({KEY_HONK_DONE}) == 0 and MM9.hasKey({KEY_HONK_FOUND}) == 1 then",
            "        MM9.giveGold(10000)",
            f"        {experience_lua(80000, KEY_HONK_DONE)}",
            "        questSound()",
            f"        MM9.takeItem({ITEM_GOLDEN_HONK}, \"NPC337.scr:GoldenHonk\")",
            f"        MM9.giveKey({KEY_HONK_DONE})",
            "    end",
            "end",
            "",
            f"-- The bill of sale on the bench (Prop3: BookLetter.scr \"{LETTER_ID} Letter 1\": DoLetter {LETTER_ID}).",
            f"handlers[{EV_LETTER}] = function() evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end",
            "",
            "-- The end of the game (WinMan.scr ScriptParams Part2 :Init): with key 109 (Njam beaten) and without the Writ of",
            "-- Fate (394), :OnKrohn starts the cinema: :StartPart2 shows Hanndl, Krohn and Skraelos (WG_NPC334/335/336.scr",
            "-- :OnStart; Hanndl's shows the three Wyrdes) and hides Krohn0 (:Loop); Hanndl walks to HanndlMarker and the",
            "-- gods talk. :End gives the Writ of Fate; :Release hides the cinema's gods again and puts Krohn0 back.",
            "-- The cinematic gods_epilogue (cinematics_hall.py) plays it; DoHighScore is the world's completion (key 109).",
            "local function cinemaShown(on)",
            f"    evt.SetMonGroupBit({GROUP_CINEMA}, MonsterBits.Invisible, not on)",
            f"    evt.SetMonGroupBit({GROUP_KROHN}, MonsterBits.Invisible, on)",
            "end",
            "",
            *cinema.LOAD_LUA,
            "",
        ]
        script.add(lines, (rude_exit_event(objects["Krohn0"]), "Krohn", None),
                   (rude_exit_event(objects["Skraelos"]), "Skraelos", None),
                   (rude_exit_event(objects["Fre"]), "Fre", None),
                   (EV_LETTER, "Letter", "Letter"), (1, "Map load", None))
        # WinMan.scr Part2's cutscene (cinematics_hall.py): the map Lua's block and hallofthegods.cinematics.yml
        scenes = cinema.scenes(self.actor, self.hanndl_mark, self.hanndl_start)
        cinema.install(scenes)
        return script.finish(on_load=[1]) + cutscenes.lua_block(scenes)

    def afterworld_arrival(self, build) -> tuple:
        """ExitTrigger0's arrival: the rebuilt Afterworld's StartPoint0 (its BLV frame and floor, from its scene:
        the isle review root until the final install, then assets_dev) and its facing in yaw units."""
        for root in (ROOT / "output/mm9_rework/isleofashes_blv_root", ROOT / "assets_dev"):
            scene = root / "worlds/mm9/maps/afterworld.scene.yml"
            if scene.exists():
                starts = yaml.load(scene.read_text(), Loader=yaml.CSafeLoader)["party_start_points"]
                start = next(s for s in starts if s["source_name"] == "StartPoint0")
                x, y, z = (int(round(v)) for v in start["position"])
                return x, y, z, int(round(start["direction_degrees"] / 360 * 2048)) % 2048
        raise SystemExit("ExitTrigger0: no rebuilt afterworld.scene.yml")


    def scene(self, build, scene: dict) -> None:
        """MM9's water surfaces drawn by the liquid shader."""
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)

    def report(self, build) -> dict:
        return {"sky_faces": getattr(self, "sky_faces", {}),
                "hanndl_mark": [int(v) for v in self.hanndl_mark],
                "scripted": {"actors": self.actor, "objects": self.object, "cinema": self.cinema}}


GATE_ROW = "mm9:transition/hallofthegods/142"     # ExitTriggerHall, the gate's shimmer to Arslegard City
GATE_HALF_X = 48                     # native: MM9's 4 LT box tested against its player's box (radius about 15 LT)


def transitions_text(project, polygons, current_text, facings=None):
    """The shared writer (dungeon.tables.transitions_text), then ExitTriggerHall's volume made reachable: MM9's box
    (Dims 4 x 64 x 32 LT round LT y 72) starts 8 LT over the porch floor and is 4 LT thick, tested against MM9's
    player box; the native exit tests the party's centre (Training Hall's lesson), so the row reaches down to the floor
    and is GATE_HALF_X deep along x. Applied here because overrides.yml `exits` can only lower a box's bottom, not
    deepen it."""
    text, changes = _shared_transitions_text(project, polygons, current_text, facings)
    lines = text.split("\n")
    header = lines[0].split("\t")
    column = {name: i for i, name in enumerate(header)}
    for k, line in enumerate(lines):
        cells = line.split("\t")
        if cells[0] != GATE_ROW:
            continue
        top = 72 * SCALE + 64 * SCALE              # the DAT box's top (LT y 72 + Dims y 64)
        cells[column["CenterZ"]] = str(int(round(top / 2)))
        cells[column["HalfExtentZ"]] = str(int(round(top / 2)))
        cells[column["HalfExtentX"]] = str(GATE_HALF_X)
        lines[k] = "\t".join(cells)
    return "\n".join(lines), changes


_shared_transitions_text = tables.transitions_text
tables.transitions_text = transitions_text


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, HallOfTheGods()))
