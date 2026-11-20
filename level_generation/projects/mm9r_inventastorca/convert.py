#!/usr/bin/env python3
"""
Inventa Storca, MM9 rework: MM9's INVENTASTORCA.dat (the old library under Thronheim) as a native BLV on the shared
dungeon converter (../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_inventastorca/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_inventastorca/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules and archway cuts; this file adds the library's water (the flooded cavern under the
west walkways and the well beside the lower library, wading floors: no diving yet), its population (props.json from
../../props/mm9_inventastorca_claude, the touch triggers as pads, 39 actors, the perception hints) and its scripted
objects as native Lua, each citing its .scr or its DAT trigger wiring (README.md, "Scripted objects"):
- the Orbs of Linking (Orb.scr) and the two letters (BookLetter.scr);
- the dead adventurers (GreenParty.scr), the dying one and the Lich King who kills him (IS_DyingNpc.scr,
  IS_KillingLich.scr; SpookTrigger5 and DoubleDoorL9's OpenTrigger);
- the spook sounds (Spook.scr), the scurrying basilisks (ScurryCreature.scr), the ickies in the cave shaft
  (IS_ficky.scr, IS_fickyflock.scr), the bust-outs (KingKong.scr on BustOutLich0 and BustOutLichKing0);
- the falling bookcases (FallingBookcaseSwitch -> FBR1..5 -> FallingBookcase1..6), the secret switches and panels,
  the breakable walls (DestructableBrush0-3), the dressers, drawers and the trapdoor over Ladder5.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import review_root  # noqa: E402
from dungeon import lua, tables, water  # noqa: E402
from dungeon.geometry import Polygon, clip  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from dungeon.destructibles import CLICK_EVENT_BASE  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402

PROPS = PROJECT / "props.json"

# --- Water -----------------------------------------------------------------------------------------------------------
# MM9's BlueWater volumes (ShowSurface 1, Sprites\Water\Ocean3.spr, SurfaceAlpha 0.85). BlueWater1 fills the cavern
# under the west walkways to LT -576; BlueWater0 is the well in the niche west of the lower library (its top -640, the
# niche floor's height; the native surface lies 2 LT under the floor so only the well's hole shows it); BlueWater2 is
# the flooded channel between them, wholly under rock (no surface). The surfaces are non-solid and swum (the shared
# water rule, 2026-11-06); with overrides.yml `map: {swim: false}` wading floors and the swim pad below.
WATER_TEXTURE = "sprites\\water\\ocean3.spr"
WATER_SURFACES = {"BlueWater1": None, "BlueWater0": -642.0}       # model -> surface LT y (None: the volume's top)
WATER_ALIAS = "OCEA8LH6KA"
LIQUIDS = """
  - id: ocean_mm9_inventastorca
    kind: water
    color: [52, 84, 96]
    applies_to: [face]
    worlds: [mm9]
    depth: shallow
    match:
      texture_names: [ocea8lh6ka]
"""

# --- Events, timers, cogs, groups ------------------------------------------------------------------------------------
EV_LOAD = 1
EV_DD9 = 120                        # DoubleDoor9: its OpenTrigger sets the Lich King on the dying adventurer
EV_FURNITURE = 130                  # 130 + k: dresser k, drawers, desk drawers, the trapdoor, the wall book (FURNITURE)
EV_BOOKCASES = 170                  # FallingBookcaseSwitch: the domino
EV_SECRET1 = 171                    # SecretSwitch1 (on FallingBookcase4): SecretPanel1 over the chests
EV_SECRET = 172                     # SecretSwitch: SecretPanel (TreasureBag1's niche)
EV_SECRET0 = 173                    # SecretSwitch0: SecretPanel0 (TreasureBag0's niche)
EV_FALSE_SWITCH = 174               # the book switches riding the bookcases: they do nothing in MM9 either
EV_BREAK = 180                      # 180 + k: DestructableBrush k (k 0-3) broken (its destroyed event)
EV_BUSTOUT = {"BustOutTrigger0": 190, "BustOutTrigger1": 191}
EV_SCURRY = {"ScurryTrigger0": 192, "ScurryTrigger1": 193}
EV_BIRDS = {"BirdTrigg0": 194, "BirdTrigg1": 195}
EV_SPOOK = {f"SpookTrigger{k}": 196 + k for k in range(6)}         # 196..201
EV_SWIM = 202                       # the cavern's water: the party swims out to the well
EV_SCURRY_HIDDEN = 203              # 203 + k: ScurryBasilisk k reached HideMarker0 (its RunTo's Disappear)
EV_ORB = 210                        # 210 + k: Prop0..Prop6 (Orb.scr)
EV_LETTER = {"Prop7": 220, "Prop8": 221}                          # BookLetter.scr
T_DOMINO, T_SPOOK, T_HINTS = 250, 251, 252
COG_HINT = 320
G_LK, G_DUDE, G_BUST0, G_BUST1, G_SCURRY0, G_SCURRY1, G_BROOD, G_SKYBIRD = 10, 11, 12, 13, 14, 15, 16, 17

ITEM_ORB = 252                      # Orb.scr: giveitem 252 (a world item, dungeon/pickups.py)
RELATION_HOSTILE = 2

# BookLetter.scr DoLetter <ScriptParams p0>: MM9's BOOK AND SCROLL TEXT.csv rows 494 and 495.
LETTER_ROWS = {"Prop7": 494, "Prop8": 495}

# Furniture clicks: group -> what the click also does to a perception hint (the brush's Open/CloseTriggers).
FURNITURE = [*(f"Dresser{k}" for k in range(1, 9)), *(f"Drawer{k}" for k in range(1, 17)),
             "DeskDrawer", "DeskDrawer0", "LadderDoor", "FalseSwitch4"]
FURNITURE_HINTS = {"DeskDrawer": "PerceptionBrush8", "DeskDrawer0": "PerceptionBrush7", "LadderDoor": "PerceptionBrush9"}

# The bookcase domino (FallingBookcaseSwitch, FBR1..5, FallingBookcase1..6, MM9's own Open/Trigger wiring): relay k
# swings 37 degrees at 40 a second (0.93 s), then starts bookcase k (attached to it, so it turns with the relay) and
# relay k + 1. Native: bookcase k is one rotating mover turning both swings (relay + its own) at a speed that ends with
# MM9's, started (k - 1) seconds after the switch; bookcase 6 has no relay. The book switches ride their bookcase.
DOMINO = {f"FallingBookcase{k}": f"FBR{k}" for k in range(1, 6)}
RIDERS = {"FalseSwitch1": "FallingBookcase1", "FallingBookcaseSwitch": "FallingBookcase1",
          "FalseSwitch2": "FallingBookcase2", "FalseSwitch3": "FallingBookcase3", "SecretSwitch1": "FallingBookcase4",
          "FalseSwitch5": "FallingBookcase5", "FalseSwitch6": "FallingBookcase6"}
BOOKCASE_GROUPS = {k: [f"FallingBookcase{k}"] + [r for r, b in RIDERS.items() if b == f"FallingBookcase{k}"]
                   for k in range(1, 7)}

# Breakable walls (DestructableBrush, DeathTriggerTarget): the hint each break turns off.
BREAKABLE = {0: "PerceptionBrush0", 1: "PerceptionBrush1", 2: "PerceptionBrush3", 3: "PerceptionBrush2"}

# A perception glow covers the thing it marks, and interact picks it first: a click on the glow runs that thing's event
# (a breakable wall's: its shared click, CLICK_EVENT_BASE + its DAT index, place_perception_hints).
HINT_CLICKS = {"PerceptionBrush4": EV_SECRET,
               "PerceptionBrush5": EV_SECRET0, "PerceptionBrush5Level10": EV_SECRET1,
               "PerceptionBrush7": EV_FURNITURE + FURNITURE.index("DeskDrawer0"),
               "PerceptionBrush8": EV_FURNITURE + FURNITURE.index("DeskDrawer"),
               "PerceptionBrush9": EV_FURNITURE + FURNITURE.index("LadderDoor")}

# Spook.scr's ten sounds (InitStrings); lichkingTaunt and gopherwince are not in the MM9 audio import (skipped).
SPOOK_SOUNDS = ["door/doorcreak02.wav", "ambient/birds/owl02.wav", "ambient/thunder/thunder distant02.wav",
                "events/rockscrumblingloop.wav", "events/woodcreak1.wav", "ambient/insects/cricket.wav",
                "pickupitems/shield/metal01.wav", "events/shatterpotterybig02.wav"]

# Monster bodies: MM9's (dungeon/bodies.py): the row's, or the row's model at the DAT's own Scale (the Lich Kings 1.2,
# the sky Icky 3, the scurrying Basilisks 0.2), which replaces the row's Scale.
# Classes with no MM9 monster row (WealthyTownGuard1/2: the dead adventurers and the dying one): rows by model.
GUARD_ROWS = {"models\\guard.abc": 9111, "models\\highwayman.abc": 9101}
DEAD = {"DeadLich0", "DeadBandit0", "DeadBandit2", "DeadBandit3", "DeadBandit4", "DeadGreenPartyGuy0",
        "DeadGreenPartyGuy1", "DeadGreenPartyGuy2", "DeadGreenPartyGuy3"}            # GreenParty.scr: Die at launch
FLIERS = {"AirBorneIcky"}


def lua_string(text: str) -> str:
    return json.dumps(text)


def letter_text(row: int) -> tuple[str, str]:
    import csv
    path = ROOT / "mm9/extracted/DATA/DATA/BOOK AND SCROLL TEXT.csv"
    for cells in csv.reader(path.open(encoding="latin-1")):
        if cells and cells[0].strip() == str(row):
            return cells[1].strip(), cells[2].strip()
    raise SystemExit(f"letter row {row} not found")


def water_polygon(points_xz, y: float, texture: str, alias: dict, model: str) -> Polygon:
    """A horizontal solid face over a ring of (x, z) points, front upward, one texel per LT (Beethoven's surface)."""
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    mapping = (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0]))
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture, mapping, 0x1081, model, "static")
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, mapping, 0x1081, model,
                          "static")
    polygon.notes.update(width=alias["width"], height=alias["height"])
    return polygon


class InventaStorca(dungeon.Hooks):
    generator = "mm9r_inventastorca"
    own_water_surfaces = ("BlueWater0", "BlueWater1", "BlueWater2")   # edit_polygons builds them; the channel has none
    mover_events = {
        "DoubleDoor9": (EV_DD9, "click"),
        **{group: (EV_FURNITURE + k, "click") for k, group in enumerate(FURNITURE)},
        "FallingBookcaseSwitch": (EV_BOOKCASES, "click"), "SecretSwitch1": (EV_SECRET1, "click"),
        "SecretSwitch": (EV_SECRET, "click"), "SecretSwitch0": (EV_SECRET0, "click"),
        **{f"FalseSwitch{k}": (EV_FALSE_SWITCH, "click") for k in (1, 2, 3, 5, 6)},
    }

    def destructible_events(self, build) -> dict:
        """The breakable walls' deaths (DeathTrigger: their hint off; dungeon/destructibles.py `break`)."""
        return {f"DestructableBrush{k}": (EV_BREAK + k, 0) for k in BREAKABLE}

    # --- source edits before the voxels --------------------------------------------------------------------------
    def extra_seeds(self, build) -> list:
        """Called before the movers are built: folds each relay's swing into its bookcase and hangs the book switches
        on their bookcase's swing (see DOMINO, RIDERS)."""
        source = build.source
        if not getattr(source, "_domino_patched", False):
            for bookcase, relay in DOMINO.items():
                p, r = source.properties(bookcase), source.properties(relay)
                total = float(np.asarray(p["RotationAngles"])[0]) + float(np.asarray(r["RotationAngles"])[0])
                seconds = float(np.asarray(r["RotationAngles"])[0]) / float(r["Speed"]) + \
                    float(np.asarray(p["RotationAngles"])[0]) / float(p["Speed"])
                p["RotationAngles"] = [total, 0.0, 0.0]
                p["Speed"] = round(total / seconds, 2)
            for rider, bookcase in RIDERS.items():
                p, b = source.properties(rider), source.properties(bookcase)
                for key in ("RotationPoint", "RotationAngles", "Speed", "Waveform"):
                    p[key] = b.get(key)
                p.pop("ReopenOnContact", None)
                p.pop("ClosingSpeed", None)
            source._domino_patched = True
        # The shared classifier skips every model named Ladder* as a ladder volume; LadderDoor is the trapdoor over
        # Ladder5's hole (a linear Door): it takes its rule from overrides.yml here.
        if "LadderDoor" in build.plan["skipped"]:
            del build.plan["skipped"]["LadderDoor"]
            build.plan["movers"]["LadderDoor"] = build.project.overrides["models"]["LadderDoor"]
        return super().extra_seeds(build)

    def edit_polygons(self, build, polygons: list) -> list:
        """The water surfaces: each volume's top face as a solid wading floor (WATER_SURFACES)."""
        source = build.source
        # The cave shaft's floor (one stonewallrough polygon at LT -640, x -400..64, z -512..0) runs under the wall to
        # the lower hall: its edge under the hall's wall face sees the hall as much as its open part sees the cave, and
        # the whole floor went to the hall's sector, so a party in the cave was drawn from the hall. Split off the strip
        # under the wall (z < -500).
        edited = []
        for polygon in polygons:
            low, high = polygon.points.min(0), polygon.points.max(0)
            if polygon.normal[1] > 0.9 and abs(low[1] + 640) < 1 and low[0] < -390 and high[0] > 60 and low[2] < -510 \
                    and high[2] > -10:
                front, back = clip(polygon, np.array([0.0, 0.0, 1.0]), -500.0, "cave_floor")
                edited += [part for part in (front, back) if part is not None]
                self.cave_floor_split = True
            else:
                edited.append(polygon)
        polygons[:] = edited
        alias = source.aliases[WATER_TEXTURE]
        self.water = {}
        for model, y in WATER_SURFACES.items():
            points = np.array(source.models[model].points, float)
            (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
            top = float(points[:, 1].max()) if y is None else y
            polygons.append(water_polygon([(x0, z0), (x0, z1), (x1, z1), (x1, z0)], top, WATER_TEXTURE, alias, model))
            self.water[model] = {"box": [x0, z0, x1, z1], "y": top}
        return polygons

    # --- population ------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        self.orbs = [o["name"] for o in source.objects if "orb.scr" in str(o["properties"].get("ScriptName", "")).lower()]
        self.orbs.sort(key=lambda n: int(n[4:]))
        if PROPS.exists():
            events = {name: EV_ORB + k for k, name in enumerate(self.orbs)}
            events.update(EV_LETTER)
            # MM9 names two benches 'Bench' and two tables 'Table': the second of a name takes its object index.
            entries, seen = json.loads(PROPS.read_text()), set()
            for entry in entries:
                if entry["source_name"].lower() in seen:
                    entry["source_name"] = f"{entry['source_name']}_{entry['source_object']}"
                seen.add(entry["source_name"].lower())
            unique = build.project.work / "props_unique.json"
            unique.write_text(json.dumps(entries, indent=0))
            content.props(unique, events=events)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        for name, event in [*EV_BUSTOUT.items(), *EV_SCURRY.items(), *EV_BIRDS.items(), *EV_SPOOK.items()]:
            p = source.properties(name)
            content.pad(name, p["Pos"], p["Dims"], event)
        if not water.swimming(build.project):
            self.swim_pad(build)        # the stand-in for MM9's swim (overrides.yml `map: {swim: false}` only)
        self.place_perception_hints(build)
        self.points = {}
        for name in ("HideMarker0",):
            self.points[name] = self.foot(build, source.properties(name)["Pos"])
        x0, z0, x1, z1 = self.water["BlueWater0"]["box"]
        # The well's way out: the niche floor beside the well's hole (east of it).
        self.points["WellShore"] = self.foot(build, (-960.0, -620.0, -1196.0))
        self.points["BustOut1Floor"] = self.foot(build, (-1632.0, -320.0, -2768.0))

    def foot(self, build, point) -> list:
        floor = build.content.floor_at(point[0], point[2], point[1] + 16)
        if floor is None:
            raise SystemExit(f"no floor under {point}")
        return build.project.native([point[0], floor, point[2]]).round().astype(int).tolist()

    def swim_pad(self, build) -> None:
        """The cavern's water as a pressure plate 3 over the surface: a party that falls in from the walkways swims
        out (MM9: through BlueWater2 and up the well; here moved to the well's shore)."""
        project, package = build.project, build.package
        x0, z0, x1, z1 = self.water["BlueWater1"]["box"]
        y = self.water["BlueWater1"]["y"]
        corners = [project.native([x, y, z]) for x, z in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]
        points = np.round(np.array(corners)).astype(int) + np.array([0, 0, 3])
        if np.cross(points[1] - points[0], points[2] - points[0])[2] < 0:
            points = points[::-1]
        node = "TRIGGER_CavernWater"
        package.add_raw(node, points, package.marker_material())
        owner = build.content.owner(np.array([-2100.0, y + 20, -950.0]))
        package.room_nodes[owner].append(node)
        package.metadata["surfaces"].append({"id": "CavernWater", "source_node": node, "flags": ["invisible"],
                                             "trigger": {"event_id": EV_SWIM, "type": "pressure_plate"}})
        build.content.report["pads"].append({"anchor": "CavernWater", "event": EV_SWIM, "room": owner,
                                             "z": int(points[0][2])})

    def place_perception_hints(self, build) -> None:
        """Each PerceptionBrush's Perception.spr polygons as untouchable faces with a cog (Drangheim Prison's route):
        the map script shows them to a party whose Perception reaches the brush's PerceptionValue (8; 10 for
        PerceptionBrush5Level10) until the secret they mark is found."""
        package, source = build.package, build.source
        self.hints = {}                 # brush name -> (cog, difficulty)
        self.hint_faces = 0
        difficulties = perception_difficulties_by_model_name(source.world)
        names = sorted(difficulties)
        for k, lower in enumerate(names):
            name = next(model for model in source.models if model.lower() == lower)
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                rooms = build.content.rooms
                room = room_id(_side_room(rooms, polygon, 1) or _side_room(rooms, polygon, -1)
                               or rooms.owner(polygon.points.mean(0)))
                node = f"TRIGGER_perception_{name}_{i}"
                if not package.add_polygon(node, polygon, build.stats):
                    self.hint_degenerate = getattr(self, "hint_degenerate", 0) + 1
                    continue
                package.room_nodes[room].append(node)
                surface = {"id": node[8:], "source_node": node, "flags": ["untouchable"], "cog_number": COG_HINT + k}
                clicks = dict(HINT_CLICKS, **{hint: CLICK_EVENT_BASE + source.by_name[f"destructablebrush{k}"]["index"]
                                              for k, hint in BREAKABLE.items()})
                if name in clicks:              # the glow lies over the secret: a click on it is a click on the secret
                    surface["trigger"] = {"event_id": clicks[name], "type": "click"}
                package.metadata["surfaces"].append(surface)
                self.hint_faces += 1
            self.hints[name] = (COG_HINT + k, int(round(difficulties[lower])))

    # --- actors ----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor = [], {}
        for o in source.objects:
            if o["class"] not in build.project.monster_classes:
                continue
            name, p = o["name"], o["properties"]
            model = str(p.get("Filename", "")).lower()
            base = bases.get(name)
            if base is None:            # WealthyTownGuard1/2: MM9 has no monster row; the Guard or Bandit row by model
                row = GUARD_ROWS[model]
                base = {"name": "Guard" if row == 9111 else "Bandit", "attributes": 0, "hp": 1, "hostility_type": 0,
                        "monster_info_id": row, "monster_id": row, "radius": 38, "height": 184, "move_speed": 0}
                content.report["omitted"] = [e for e in content.report["omitted"] if e["anchor"] != name]
            script = str(p.get("ScriptName", "")).lower()
            group, hidden, friendly, changes = 0, False, False, {}
            dormant, immobile = False, False
            if name in DEAD:
                changes["hp"] = 0
                friendly = True
            elif name == "GreenPartyDude0":                 # IS_DyingNpc.scr: a dying adventurer
                group, friendly, immobile = G_DUDE, True, True
                changes["hp"] = 1
            elif name == "LKToKillGreenParty0":             # IS_KillingLich.scr: waits for its Kill trigger
                group, friendly, dormant = G_LK, True, True
            elif name in ("BustOutLich0", "BustOutLich1"):  # KingKong.scr: behind DestructableBrush4 until ForceBreak
                group, dormant = G_BUST0, True
            elif name in ("BustOutLichKing0", "BustOutSkeleton0", "BustOutSkeleton1"):
                group, hidden, dormant = G_BUST1, True, True      # over DestructableBrush5 until ForceFall
            elif "scurrycreature" in script:                 # ScurryCreature.scr: no fight, runs off to hide
                group = G_SCURRY0 if p["Pos"][2] > -1200 else G_SCURRY1
                friendly = True
            elif "is_fickyflock" in script:                  # IS_fickyflock.scr: inactive until scattered
                group, friendly = G_BROOD, True
            elif "is_ficky.scr" in script:                   # IS_ficky.scr: circles the shaft's top
                group, friendly = G_SKYBIRD, True
            query = p["Pos"][1] + 24
            if o["class"] in FLIERS:
                query = p["Pos"][1] + 24
            record = content.actor(o, base, sector_of_room, group=group, hidden=hidden, friendly=friendly,
                                   floor_query_lt=query, **changes)
            if o["class"] in FLIERS:                          # fliers keep their DAT height (their centre)
                floor_z = record["position"]["z"]
                record["position"]["z"] = max(floor_z, int(round(p["Pos"][1] * SCALE)) - 64)
            record.update(placed_body(record["monster_id"], p))
            if dormant:
                record["dormant"] = True
            if immobile:
                record["immobile"] = True
            record["mm9_source_object_index"] = o["index"]
            self.actor[name] = record["actor_index"]
            out.append(record)
        return out

    # --- map script ------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Inventa Storca")
        actor, points = self.actor, self.points
        groups = {g: ids for g, ids in script.groups.items()}
        script.lines += [
            "local GROUPS = {" + ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(groups.items()))
            + "}",
            "local function trigger(group) for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Trigger) end end",
            "local function openGroup(group) for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Open) end end",
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "",
        ]
        script.doors()
        script.chests()
        hint_cogs = {name: cog for name, (cog, _) in self.hints.items()}
        lines = [
            "-- The PerceptionBrushes (MM9's red outlines of secrets): shown to a party whose Perception reaches the",
            "-- brush's PerceptionValue, until the secret is found (each brush's Off trigger: a broken wall, an open",
            "-- drawer or panel; the drawers and the trapdoor show theirs again when shut). On load and every 3 s.",
            "local HINTS = {" + ", ".join(f"{name} = {{cog = {cog}, value = {value}}}"
                                          for name, (cog, value) in sorted(self.hints.items())) + "}",
            "local function hintOff(name, off) set(\"HintOff\" .. name, off and 1 or 0); set(\"HintsShown\", -1) end",
            "local function updateHints()",
            "    local skill = 0",
            "    for value = 1, 60 do if evt.CheckSkill(29, 0, value) then skill = value else break end end",
            "    set(\"HintSkill\", skill)",
            "    local key = skill",
            "    for name, _ in pairs(HINTS) do key = key * 2 + var(\"HintOff\" .. name) end",
            "    if var(\"HintsShown\") == key then return end",
            "    set(\"HintsShown\", key)",
            "    for name, hint in pairs(HINTS) do",
            "        evt.SetFacetBit(hint.cog, FacetBits.Invisible, skill < hint.value or var(\"HintOff\" .. name) == 1)",
            "    end",
            "end",
            f"handlers[{T_HINTS}] = updateHints",
            "",
            "-- Furniture (dressers, drawers, desk drawers, the trapdoor over Ladder5, the book on the wall): a click opens",
            "-- or shuts it; the desk drawers and the trapdoor carry a perception hint (their Open/CloseTriggers).",
        ]
        script.add([], (T_HINTS, "Perception hints", None, "timer"))
        for k, group in enumerate(FURNITURE):
            event = EV_FURNITURE + k
            hint = FURNITURE_HINTS.get(group)
            body = f"trigger(\"{group}\")"
            if hint:
                body += (f"; hintOff(\"{hint}\", var(\"Open{group}\") == 0); set(\"Open{group}\", 1 - var(\"Open{group}\"));"
                         " updateHints()")
            lines.append(f"handlers[{event}] = function() {body} end   -- {group}")
            script.add([], (event, "Drawer" if "Drawer" in group else "Door", "Open"))
        # Bookcases.
        domino = []
        for k in range(1, 7):
            domino.append("{" + ", ".join(f"\"{m}\"" for m in BOOKCASE_GROUPS[k]) + "}")
        lines += [
            "",
            "-- The falling bookcases (FallingBookcaseSwitch's OpenTriggers: FBR1 toggle, itself locked, PerceptionBrush5Level10",
            "-- off; FBR k's OpenTriggers: FallingBookcase k and FBR k+1): one bookcase a second topples into the next, its",
            "-- book switches with it; the last falls flat across the aisle (FallingBookcase6, its OpenTrigger: AITrk100 off).",
            "local DOMINO = {" + ", ".join(domino) + "}",
            "local function topple(k)",
            "    for _, name in ipairs(DOMINO[k]) do evt.SetDoorState(DOORS[name], DoorAction.Open) end",
            "    evt.PlaySoundName(\"events/woodcreak1.wav\", 0, 0, 0)",
            "end",
            f"handlers[{EV_BOOKCASES}] = function()   -- FallingBookcaseSwitch",
            "    if var(\"Domino\") ~= 0 then return end",
            "    set(\"Domino\", 1)",
            "    hintOff(\"PerceptionBrush5Level10\", true); updateHints()",
            "    topple(1)",
            f"    arm({T_DOMINO}, 1)",
            "end",
            f"handlers[{T_DOMINO}] = function()",
            f"    if not fired({T_DOMINO}) then return end",
            "    local k = var(\"Domino\") + 1",
            "    if k > 6 then return end",
            "    set(\"Domino\", k)",
            "    topple(k)",
            "    if k == 6 then evt.PlaySoundName(\"events/metalbreak01.wav\", 0, 0, 0) else "
            f"arm({T_DOMINO}, 1) end",
            "end",
            f"handlers[{EV_FALSE_SWITCH}] = function() end   -- FalseSwitch1-3, 5, 6: a book that does nothing",
            "",
            "-- The secret switches (their OpenTriggers: the panel opens, the switch locks, the hint goes).",
            f"handlers[{EV_SECRET1}] = function()   -- SecretSwitch1 on FallingBookcase4 -> SecretPanel1 over Chest1/Chest2",
            "    if var(\"Secret1\") == 1 then return end",
            "    set(\"Secret1\", 1)",
            "    open(\"SecretPanel1\"); hintOff(\"PerceptionBrush5Level10\", true); hintOff(\"PerceptionBrush10\", true)",
            "    updateHints()",
            "end",
            f"handlers[{EV_SECRET}] = function()   -- SecretSwitch -> SecretPanel (TreasureBag1's niche)",
            "    if var(\"Secret\") == 1 then return end",
            "    set(\"Secret\", 1)",
            "    open(\"SecretSwitch\"); open(\"SecretPanel\"); hintOff(\"PerceptionBrush4\", true); updateHints()",
            "end",
            f"handlers[{EV_SECRET0}] = function()   -- SecretSwitch0 -> SecretPanel0 (TreasureBag0's niche)",
            "    if var(\"Secret0\") == 1 then return end",
            "    set(\"Secret0\", 1)",
            "    open(\"SecretSwitch0\"); open(\"SecretPanel0\"); hintOff(\"PerceptionBrush5\", true); updateHints()",
            "end",
            "",
            "-- The breakable walls (DestructableBrush0-3, scene destructibles: MM9's party smashes them, a click still does;",
            "-- DeathTrigger: the hint off, DestructableBrush2's through 'Tom Needed A Trigger1'): each one's destroyed event.",
        ]
        script.add([], (EV_BOOKCASES, "Book", "Book"), (T_DOMINO, "Bookcases", None, "timer"),
                   (EV_FALSE_SWITCH, "Book", "Book"), (EV_SECRET1, "Book", "Book"), (EV_SECRET, "Book", "Book"),
                   (EV_SECRET0, "Book", "Book"))
        for k, hint in BREAKABLE.items():
            lines += [f"handlers[{EV_BREAK + k}] = function()   -- DestructableBrush{k} broken",
                      f"    set(\"Broken{k}\", 1)",
                      f"    hintOff(\"{hint}\", true); updateHints()",
                      "end"]
            script.add([], (EV_BREAK + k, "Cracked wall", None))
        # Bust-outs.
        bx, by, bz = points["BustOut1Floor"]
        fallers = ["BustOutLichKing0", "BustOutSkeleton0", "BustOutSkeleton1"]
        lines += [
            "",
            "-- KingKong.scr: BustOutTrigger0 sends BustOutLich0 through its cage wall (ForceBreak: DestructableBrush4,",
            "-- rock_crush.wav) and the caged pair attack; BustOutTrigger1 drops BustOutLichKing0 and its two skeletons",
            "-- through the ceiling (ForceFall: DestructableBrush5 destroyed). Native: both are scene destructibles broken",
            "-- here; the three appear on the floor under the hole, and each wakes and hunts the party.",
            f"handlers[{EV_BUSTOUT['BustOutTrigger0']}] = function()",
            "    if var(\"BustOut0\") == 1 then return end",
            "    set(\"BustOut0\", 1)",
            "    -- BustOutLich0 breaks its own cage (ForceBreak): killed in it, it takes none and the wall stands.",
            "    -- :RushCage roars where it stands (dragonredrattack3.wav), :BreakCage swings hattack1 (LICH.abc's",
            "    -- Hattack1 is the model's attack_melee2).",
            f"    if MM9.receives(\"inventastorca\", \"BustOutLich0\", \"ForceBreak\", {actor['BustOutLich0']}) then",
            f"        local x, y, z = evt.GetMapActorPosition({actor['BustOutLich0']})",
            "        if x ~= nil then",
            "            evt.PlaySoundName(\"animsounds/dragonredrattack3.wav\", math.floor(x), math.floor(y), "
            "math.floor(z))",
            "        end",
            f"        evt.DestroyDestructible({build.source.by_name['destructablebrush4']['index']})",
            "        evt.PlaySoundName(\"events/rock_crush.wav\", 0, 0, 0)",
            f"        evt.PlayActorClip({actor['BustOutLich0']}, \"attack_melee2\")   -- PlayAnim hattack1",
            "    end",
            f"    evt.WakeGroup({G_BUST0})",
            "end",
            f"handlers[{EV_BUSTOUT['BustOutTrigger1']}] = function()",
            "    if var(\"BustOut1\") == 1 then return end",
            "    set(\"BustOut1\", 1)",
            f"    evt.DestroyDestructible({build.source.by_name['destructablebrush5']['index']})",
            "    evt.PlaySoundName(\"events/rock_crush.wav\", 0, 0, 0)",
        ]
        for k, name in enumerate(fallers):
            dx = (k - 1) * 90
            lines += [f"    evt.SetMapActorPosition({actor[name]}, {bx + dx}, {by}, {bz})",
                      f"    evt.SetMonsterBit({actor[name]}, ActorAttribute.Invisible, 0)"]
        lines += [f"    evt.WakeGroup({G_BUST1})", "end"]
        script.add([], *[(event, name, None) for name, event in EV_BUSTOUT.items()])
        # Scurry, birds.
        lines += [
            "",
            "-- ScurryCreature.scr: the small basilisks run to HideMarker0 at six times their speed and vanish (Hide:",
            "-- :GoHide's RunTo, then RemoveObject). Here they run at their own run speed; a load sends the ones still",
            "-- running again.",
            f"local HIDE = {{{', '.join(str(v) for v in self.points['HideMarker0'])}}}",
            "local function scurry(actorIndex)",
            "    if not evt.MoveActorTo(actorIndex, HIDE[1], HIDE[2], HIDE[3], "
            f"{EV_SCURRY_HIDDEN} + actorIndex - {actor['ScurryBasilisk0']}, true) then MM9.removeActor(actorIndex) end",
            "end",
        ]
        scurriers = sorted((n for n in actor if n.startswith("ScurryBasilisk")), key=lambda n: int(n[-1]))
        if [actor[n] for n in scurriers] != list(range(actor[scurriers[0]], actor[scurriers[0]] + len(scurriers))):
            raise SystemExit("the scurrying basilisks are not consecutive actors")
        for k, n in enumerate(scurriers):
            lines.append(f"handlers[{EV_SCURRY_HIDDEN + k}] = function() MM9.removeActor({actor[n]}) end"
                         f"   -- {n} hidden")
            script.add([], (EV_SCURRY_HIDDEN + k, f"{n} hidden", None))
        for name, event in EV_SCURRY.items():
            group = G_SCURRY0 if name.endswith("0") else G_SCURRY1
            members = [n for n in actor if n.startswith("ScurryBasilisk") and (int(n[-1]) < 3) == (group == G_SCURRY0)]
            lines += [f"handlers[{event}] = function()   -- {name}",
                      f"    if var(\"{name}\") == 1 then return end",
                      f"    set(\"{name}\", 1)",
                      "    evt.PlaySoundName(\"animsounds/dragonredhop.wav\", 0, 0, 0)",
                      # Hide (:GoHide, then RemoveObject): a dead basilisk takes none, its corpse stays
                      *[f"    if MM9.receives(\"inventastorca\", \"{n}\", \"Hide\", {actor[n]}) then "
                        f"scurry({actor[n]}) end" for n in members],
                      "end"]
            script.add([], (event, name, None))
        brood = [n for n in actor if n.startswith("BrettBird")]
        lines += [
            "-- IS_ficky.scr / IS_fickyflock.scr: either BirdTrigg scatters the five ickies resting in the cave shaft;",
            "-- they fly up to the FlockM markers and vanish (Die). Here they are gone with their flapping. The scatter",
            "-- goes to BirdIntheSky0, which sends each of the five its go: a dead one takes none (MM9.receives).",
            "local function scatter()",
            "    if var(\"Scattered\") == 1 then return end",
            "    set(\"Scattered\", 1)",
            f"    if not MM9.receives(\"inventastorca\", \"BirdIntheSky0\", \"scatter\", {actor['BirdIntheSky0']}) "
            "then return end",
            "    evt.PlaySoundName(\"events/woodcreak1.wav\", 0, 0, 0)",
            *[f"    if MM9.receives(\"inventastorca\", \"{n}\", \"go\", {actor[n]}) then "
              f"MM9.removeActor({actor[n]}) end" for n in brood],
            "end",
        ]
        for name, event in EV_BIRDS.items():
            lines.append(f"handlers[{event}] = scatter   -- {name}")
            script.add([], (event, name, None))
        # Dying adventurer.
        lines += [
            "",
            "-- IS_KillingLich.scr / IS_DyingNpc.scr: SpookTrigger5 or opening DoubleDoor9 sends the Kill trigger; the Lich",
            "-- King deals the dying adventurer (GreenPartyDude0) the killing blow, then attacks the party. Native: the two",
            "-- become enemies, and the Lich King turns hostile and moves; the adventurer is on his last hit point (the",
            "-- scene's 1, which the load-time bolster fills up), so the first blow kills him.",
            "-- A dead Lich King takes no Kill (MM9.receives): the adventurer lives on.",
            f"local function lastHitPoint() if MM9.actorAlive({actor['GreenPartyDude0']}) then "
            f"evt.SetMapActorHp({actor['GreenPartyDude0']}, 1) end end",
            "local function lichKills()",
            "    if var(\"LichKills\") == 1 then return end",
            "    if not MM9.receives(\"inventastorca\", \"LKToKillGreenParty0\", \"Kill\", "
            f"{actor['LKToKillGreenParty0']}) then return end",
            "    set(\"LichKills\", 1)",
            "    lastHitPoint()",
            "    evt.SetMonsterRelation(9207, 9111, " + str(RELATION_HOSTILE) + ")",
            "    evt.SetMonsterRelation(9111, 9207, " + str(RELATION_HOSTILE) + ")",
            f"    evt.SetMonGroupBit({G_LK}, MonsterBits.Hostile, true)",
            f"    evt.WakeGroup({G_LK})",
            "end",
            f"handlers[{EV_DD9}] = function() trigger(\"DoubleDoor9\"); lichKills() end   -- DoubleDoor9",
        ]
        script.add([], (EV_DD9, "Door", "Door"))
        # Spook.
        sounds = ", ".join(lua_string(s) for s in SPOOK_SOUNDS)
        lines += [
            "",
            "-- Spook.scr (SpookObject): SpookTrigger0-4 play one of its sounds once each; it also plays one every 2-8",
            "-- minutes (StartPlayLoop). SpookTrigger5 sends the Lich King's Kill trigger instead.",
            f"local SPOOK = {{{sounds}}}",
            "local function spook() evt.PlaySoundName(SPOOK[evt.RandomBetween(1, #SPOOK, 1)], 0, 0, 0) end",
        ]
        for name, event in EV_SPOOK.items():
            action = "lichKills()" if name == "SpookTrigger5" else "spook()"
            lines.append(f"handlers[{event}] = function() if var(\"{name}\") == 0 then set(\"{name}\", 1); {action} end end"
                         f"   -- {name}")
            script.add([], (event, name, None))
        lines += [
            f"handlers[{T_SPOOK}] = function()",
            f"    if not fired({T_SPOOK}) then return end",
            "    spook()",
            f"    arm({T_SPOOK}, evt.RandomBetween(120, 480, 1))",
            "end",
        ]
        script.add([], (T_SPOOK, "Spook", None, "timer"))
        # Water: swum (the shared water rule, 2026-11-06: down the cavern, through BlueWater2 and up the well, as MM9);
        # with overrides.yml `map: {swim: false}` the stand-in below.
        sx, sy, sz = points["WellShore"]
        lines += [] if water.swimming(build.project) else [
            "",
            "-- The flooded cavern (BlueWater1): MM9's party swims; it leaves through the flooded channel (BlueWater2) and up",
            "-- the well (BlueWater0) beside the lower library. Diving is not built: a party that falls from the walkways onto",
            "-- the water is moved to the well's shore.",
            f"handlers[{EV_SWIM}] = function()",
            "    set(\"Swam\", var(\"Swam\") + 1)",
            "    evt.StatusText(\"You swim down through the flooded passage and come up in the well.\")",
            f"    evt.MoveToMap({sx}, {sy}, {sz + 4}, 0, 0, 0, 0, 0, \"\")",
            "end",
        ]
        if not water.swimming(build.project):
            script.add([], (EV_SWIM, "Water", None))
        # Orbs and letters.
        # The orbs are world items (dungeon/pickups.py: item 252, hidden once key 337 is held); their pickup event
        # plays Orb.scr's quest sound.
        lines += ["", "-- Orb.scr: an Orb of Linking taken (a world item) plays the quest sound."]
        for k, name in enumerate(self.orbs):
            lines.append(f"handlers[{EV_ORB + k}] = function() MM9.playSound(\"sounds/events/quest.wav\") end   -- {name}")
            script.add([], (EV_ORB + k, "Orb of Linking", None))
        lines.append("-- BookLetter.scr (Prop7, Prop8: ScriptParams '<row> Letter'): DoLetter shows MM9's text, bookopen.wav.")
        for name, event in EV_LETTER.items():
            title, text = letter_text(LETTER_ROWS[name])
            lines.append(f"handlers[{event}] = function() evt.PlaySoundName(\"events/bookopen.wav\", 0, 0, 0); "
                         f"evt.SimpleMessage({lua_string(title + chr(10) + chr(10) + text)}) end   -- {name}")
            script.add([], (event, "Scroll", "Read"))
        # Load.
        lines += [
            "",
            "handlers[1] = function()   -- map load",
            "    if var(\"LichKills\") == 1 then",
            "        evt.SetMonsterRelation(9207, 9111, " + str(RELATION_HOSTILE) + ")",
            "        evt.SetMonsterRelation(9111, 9207, " + str(RELATION_HOSTILE) + ")",
            "        lastHitPoint()",
            "    end",
            *[f"    if var(\"{name}\") == 1 and MM9.actorAlive({actor[n]}) then scurry({actor[n]}) end"
              for name in EV_SCURRY
              for n in sorted(actor) if n.startswith("ScurryBasilisk") and (int(n[-1]) < 3) == name.endswith("0")],
            f"    if var(\"Armed{T_SPOOK}\") == 0 then arm({T_SPOOK}, evt.RandomBetween(120, 480, 1)) end",
            "    set(\"HintsShown\", -1)",
            "    updateHints()",
            "end",
        ]
        script.add(lines, (EV_LOAD, "Map load", None))
        return script.finish(on_load=[EV_LOAD])

    # --- scene -----------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """The perception hints at their brushes' Alpha, drawn from both sides (faces.yml lists static nodes only: the
        faces are found in the compiled BLV by texture); the water's frames and liquid entry in the review root."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        alias = build.source.aliases["sprites\\perception.spr"]["alias"].lower()
        hints = sorted(f["index"] for f in blv["faces"] if str(f.get("texture_name", "")).lower() == alias)
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        scene.setdefault("translucent_faces", []).append(
            {"faces": hints, "opacity": 0.35, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        if build.project.install:
            self.install_frames(build, "sprites\\perception.spr")
            self.install_water_frames()
            install_liquids()

    def install_frames(self, build, texture: str) -> None:
        """An MM9 .spr as a texture frame sequence in the review root's table (Drangheim Prison's install_frames)."""
        entry = build.source.aliases[texture]
        frames = [entry["alias"]] + [frame["alias"] for frame in entry["animation_frames"][1:]]
        self.write_frames(frames)

    def install_water_frames(self) -> None:
        """Ocean3.spr's 20 frames (15 fps; the old import's aliases in another MM9 map's alias table)."""
        import yaml
        text = (ROOT / "assets_editor_dev/worlds/mm9/maps/verhoffinruins.material_aliases.yml").read_text()
        entry = next(e for e in yaml.safe_load(text)["textures"] if e["alias"] == WATER_ALIAS)
        frames = [entry["alias"]] + [frame["alias"] for frame in entry["animation_frames"][1:]]
        self.write_frames(frames)

    @staticmethod
    def write_frames(frames: list[str]) -> None:
        flags = {(True, True): "0x3\tHasMore,First", (False, True): "0x1\tHasMore", (False, False): "0x0\t"}
        relative = "engine/data_tables/texture_frame_data.txt"
        with tables.locked("review_tables.lock"):
            text = review_root.mirror_path(relative).read_text()
            if f"\n{frames[0]}\t" in text:
                return
            rows = [f"{name}\t0\t1\t{len(frames) if i == 0 else 0}\t{flags[i == 0, i < len(frames) - 1]}"
                    for i, name in enumerate(frames)]
            review_root.install(relative, (text.rstrip("\n") + "\n" + "\n".join(rows) + "\n").encode())

    def report(self, build) -> dict:
        return {"scripted": {"actors": self.actor, "orbs": self.orbs, "points": self.points,
                             "hints": {k: list(v) for k, v in self.hints.items()},
                             "water": self.water}}


def install_liquids() -> None:
    """The water's liquid entry in the review root's liquid table (shared, under the tables lock, added once)."""
    with tables.locked("review_tables.lock"):
        path = review_root.mirror_path("engine/liquids/liquids.yml")
        text = path.read_text()
        blocks = re.split(r"(?m)^(?=  - id: )", text)
        kept = "".join(b for b in blocks if not re.match(r"  - id: ocean_mm9_inventastorca\n", b)).rstrip("\n") + "\n"
        if kept + LIQUIDS != text:
            review_root.install("engine/liquids/liquids.yml", (kept + LIQUIDS).encode())


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, InventaStorca()))
