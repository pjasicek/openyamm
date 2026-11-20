#!/usr/bin/env python3
"""
Thousand Terrors, MM9 rework: MM9's 1000TERRORS.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_1000terrors/convert.py            # build, compile, install
    python3 level_generation/projects/mm9r_1000terrors/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the exits and the seed exclusions; this file adds the outline budget (the
7 000-outline bitset: up-facing detail faces compiled invisible and drawn again at load, the Chasm of the Dead's
route), the population (props.json from ../../props/mm9_1000terrors_claude, 114 monsters) and MM9's scripted objects
as native Lua (README.md, "Scripted objects"). MM9's object messages (Trigger volumes, Door Open/CloseTriggers,
Shooters, Spawners, SpawnLoc/SpawnGeneric/SpawnNjam markers, death triggers) run through one small dispatcher in the
map Lua (`send(target, message)`), so each DAT link is carried as data, not hand-written per object.
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import dungeon  # noqa: E402
import outlines  # noqa: E402
from dungeon import content as dungeon_content, density as dungeon_density, lua  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from quest_xp import balanced_experience, experience_note  # noqa: E402

PROPS = PROJECT / "props.json"
INVISIBLE_FACE = 0x00002000
UNTOUCHABLE_FACE = 0x20000000
OUTLINE_BUDGET = 6300               # outlines.count estimate (within 2 % of the compiler on Lindisfarne and the Chasm)

# --- events, timers, hooks, groups ----------------------------------------------------------------------------------
EV_BLOCK_BASE = 300                 # + 16 * pad + button: the button puzzles' 48 blocks (ButtonPuzzle.scr)
PADS = {"ButtonTrigger": "PuzzleDoor", "ButtonTrigger0": "PuzzleDoorB", "ButtonTrigger1": "PuzzleDoorC"}
PULLS = {"Pull1": "ButtonTrigger", "Pull2": "ButtonTrigger0", "Pull3": "ButtonTrigger1"}
EV_PULL = {"Pull1": 360, "Pull2": 361, "Pull3": 362}
EV_LEVER17, EV_LIFT_LEVER, EV_LIFT_LEVER0, EV_HIDDEN_BUTTON = 363, 364, 365, 366
EV_TOMB_GATE, EV_FOYER_DOOR, EV_STAIR_GATE0 = 367, 368, 369
EV_WINMAN, EV_GENIE = 370, 371
T_POLL = 380
COG_SKULL = 1380                    # SkeletonHead's SetSprite key (evt.AimDecoration); WinMan's: cinema.COG_WINMAN
COG_STATUE = 1390                   # + k: SorceressStatue<k>'s SetSprite key (evt.PlayDecorationClip)
STATUE_ANIM = ROOT / "assets_source/worlds/mm9/models/mm9_deco_sorcererstatue_anim.glb"   # its clips (lower case)


def glb_clip_seconds(path: Path) -> dict:
    """A GLB's animations by name: their length in seconds (the latest key of their samplers)."""
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + length])
    return {a["name"]: max(gltf["accessors"][s["input"]]["max"][0] for s in a["samplers"])
            for a in gltf.get("animations", [])}
DAMAGE_HOOK, KILL_HOOK = 381, 382
GROUP_NJAM_TAUNT, GROUP_NJAM_FINAL, GROUP_CRITTERS = 1, 2, 3

# keys and items (raw MM9 numbers: keys are QBits 90000 + key, items MM9.ItemIds)
KEY_NJAM_QUEST = 108                # SpawnNjam.scr / TauntMan.scr / WinMan.scr Init: the Njam chase is on
KEY_WON = 109                       # WG_NjamCam.scr (TELP 1.3): Njam frozen
KEY_TAUNTED = 497                   # TauntMan.scr
ITEM_TOMB_KEY = 599                 # DoorLock.scr "599" on ToLowerTombGate
ITEM_STAIRS_KEY = 600               # DoorLock.scr "600; 1" on StairGate0 (taken when used)
GATE0_REACH = 300                   # a hostile monster this close to StairGate0 (native) pushes it open
CRITTER_FLY_VEL = 900.0             # 1000T_FlyingCreature_.scr :InitFlyingCreature SetStat FlyVel 900 (LT/s)
LIFT_TOUCH = 40                     # a weighted lift's touch box reaches this far past its sides (native: the party's
                                    # radius, 37, and a little: a party swimming against it touches it)
LIFT_TOUCH_DEPTH = 200              # ... and this far under its sunk top (native: a swimming party's feet hang there)
ITEM_CHESS_NOTE = 598               # BootGive.scr "598" on ChessNote0
WIN_EXPERIENCE = 234000             # WinMan.scr :OnUse


def hall_of_gods_arrival() -> tuple:
    """WinMan.scr's trip to Hall of the Gods: the rebuilt map's StartPoint0 (its scene: the review root until the
    final install, then assets_dev; the old import's hallofthegods.odm is gone, 2026-11-06), facing in yaw units."""
    import yaml
    repo = Path(__file__).resolve().parents[3]
    for root in (repo / "output/mm9_rework/assets_dev", repo / "assets_dev"):
        scene = root / "worlds/mm9/maps/hallofthegods.scene.yml"
        if scene.exists():
            starts = yaml.load(scene.read_text(), Loader=yaml.CSafeLoader)["party_start_points"]
            start = next(s for s in starts if s["source_name"] == "StartPoint0")
            x, y, z = (int(round(v)) for v in start["position"])
            return x, y, z, int(round(start["direction_degrees"] / 360 * 2048)) % 2048
    raise SystemExit("WinMan: no rebuilt hallofthegods.scene.yml")

# MM9's bodies (ABC AnimBinding extents, half sizes LT) x Scale x 2.56; kept from the rows unless listed here
CHESS_DAMAGE = 60                   # ChessBase.inc :AttackSquare (the piece slides onto the party's square)
CHESS_SLIDE_SECONDS = 2.0           # :AttackSquare MoveToPOS at half the distance a second: the slide takes 2 s
CHESS_LAST_RANK = 7                 # :PawnToQueen: a pawn that ends its attack on rank SIZEINDEX (BOARDSIZE - 1)
QUEEN_CLASS = "Terror"              # :PawnToQueen Spawn "Terror" (MONSTERS.txt's Terror, a Banshee C), HitPoints 1069
QUEEN_HIT_POINTS = 1069
MONSTERS_TXT = ROOT / "mm9/extracted/DATA/DATA/MONSTERS.txt"
GENIE_ITEMS = [2, 359, 81, 420, 86, 510, 285, 318, 71, 319, 96, 97, 320, 26, 519, 76, 87, 61, 36, 18, 41, 297, 296,
               295, 2, 56, 421, 66, 292, 291, 290, 415, 288, 287, 294, 155, 332, 518, 150, 547, 538, 333, 142, 334,
               552, 553, 554, 335, 160, 548, 346, 349, 134, 327, 133, 422, 126, 127, 530, 350, 254]   # GiveRandom.scr
# GiveRandom.scr items with no OpenYAMM item yet (tools/mm9_import_discovery/mm9_item_sources.py lists them as
# unresolved): left out of the lamp's list, and the lamp's object left out of the shared source check.
GENIE_UNRESOLVED = {420, 510, 318, 319, 320, 519, 421, 415, 332, 518, 538, 333, 334, 552, 553, 554, 335, 346, 349, 327,
                    422, 530, 350, 254}
GENIE_OBJECT = 1953
MISSILES = {"firebolt": ("Fire", "Fire"), "dragonbreath2": ("Fire", "Fire"), "lightning": ("Air", "Air")}


def mm9_class_monster_id(name: str) -> tuple[int, int]:
    """An MM9 class Spawn names (its MONSTERS.txt Monster Name without spaces) as (runtime monster id, MM9 HP)."""
    for line in MONSTERS_TXT.read_text(encoding="latin-1").splitlines()[1:]:
        fields = line.split("\t")
        if len(fields) > 8 and fields[1].replace(" ", "") == name:
            return dungeon_content.bodies.MM9_MONSTER_ID_BASE + int(fields[0]), int(fields[8])
    raise SystemExit(f"MM9 class {name}: not in {MONSTERS_TXT}")


def as_float(value) -> float:
    """A DAT float stored in an int property (ActivationCount, Type) back to its float."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


def lua_str(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def messages(properties: dict, prefix_target: str, prefix_message: str) -> list:
    out = []
    for k in range(0, 12):
        target = properties.get(f"{prefix_target}{k}")
        message = properties.get(f"{prefix_message}{k}")
        if target and message:
            out.append((str(target), str(message).lower()))
    return out


def item_sources(project, objects) -> dict:
    """content.item_sources without the genie lamp's unresolved GiveRandom list (GENIE_UNRESOLVED)."""
    from mm9_item_sources import Mm9ItemIdMap, build_mm9_item_source_manifest
    manifest = build_mm9_item_source_manifest(project.stem, objects,
                                              Mm9ItemIdMap.load(ROOT / "assets_dev/worlds/mm9/state/item_ids.yml"),
                                              SCALE)
    manifest.unresolved_item_references = [s for s in manifest.unresolved_item_references
                                           if s.source_object_index != GENIE_OBJECT]
    manifest.require_resolved_item_references()
    return manifest.scene_data()


dungeon_content.item_sources = item_sources


class ThousandTerrors(dungeon.Hooks):
    generator = "mm9r_1000terrors"
    # ACTOR lists every placed monster by DAT name for the messages (`go`) and the win's clean-up, not scripted
    # behaviour of each: pack growth copies them and adds the copies to it (dungeon/density.py)
    density_lua_directories = ("ACTOR",)
    # KIND names every placed actor too ("actor"), for send's dispatch: not scripting, and the copies need no entry (no
    # message names them). The only actors the map's messages do name are the fly-past critters (TRIGGERS' `go`,
    # FLY_LEAVE), dormant until then: they stay scripted and are never copied, so no copy needs waking or removing.
    density_lua_name_tables = ("KIND",)
    mover_events = {
        **{f"{root}{k}": (EV_BLOCK_BASE + 16 * pad + k, "click")
           for pad, root in enumerate(PADS.values()) for k in range(16)},
        **{name: (event, "click") for name, event in EV_PULL.items()},
        "Lever17": (EV_LEVER17, "click"), "LowerLever": (EV_LIFT_LEVER, "click"),
        "LowerLever0": (EV_LIFT_LEVER0, "click"), "HiddenButton1": (EV_HIDDEN_BUTTON, "click"),
        "ToLowerTombGate": (EV_TOMB_GATE, "click"), "FoyerDoorSouth": (EV_FOYER_DOOR, "click"),
        "StairGate0": (EV_STAIR_GATE0, "click"),
    }

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        self.prop_names = set()
        if PROPS.exists():
            entries = json.loads(PROPS.read_text())
            for entry in entries:
                if entry["source_name"].lower() in content.ids:
                    entry["source_name"] += "_prop"
                self.prop_names.add(entry["source_name"])
                if entry["source_name"] == "ChessNote0":
                    # MM9 drops the note 2 LT in front of the shut ToLowerTombGate: a click there meets the gate's foot
                    # first, so it lies 16 units (6 LT) further out (README, Deviations)
                    entry["y"] -= 16
            placed = project.work / "props_entities.json"
            placed.write_text(json.dumps(entries) + "\n")
            # ChessNote0 (BootGive.scr "598") is a world item (dungeon/pickups.py)
            events = {"WinMan": EV_WINMAN, "Genielamp": EV_GENIE}
            import cinematics_1000t as cinema
            cogs = {"WinMan": cinema.COG_WINMAN, "SkeletonHead": COG_SKULL,
                    **{f"SorceressStatue{k}": COG_STATUE + k for k in range(8)}}
            content.props(placed, events={k: v for k, v in events.items() if k in self.prop_names},
                          cogs={k: v for k, v in cogs.items() if k in self.prop_names})
        else:
            print("note: props.json is missing; no decorations placed")
        # Trigger volumes as boxes (native, min/max), polled in the map Lua.
        self.boxes = {}
        for o in source.objects:
            if o["class"] != "Trigger":
                continue
            p = o["properties"]
            dims = np.array(p.get("Dims") or [0, 0, 0], float)
            if not dims.any():
                continue
            centre = np.array(p["Pos"], float)
            low, high = project.native(centre - dims), project.native(centre + dims)
            self.boxes[o["name"]] = [np.minimum(low, high).round().astype(int).tolist(),
                                     np.maximum(low, high).round().astype(int).tolist()]
        self.points = {}
        for o in source.objects:
            if o["class"] in ("Shooter", "Marker", "ScriptObject", "Spawner", "Prop", "Camera") or \
                    o["class"] in project.monster_classes:
                p = o["properties"]["Pos"]
                point = project.native(p).round().astype(int)
                if o["class"] in ("Spawner", "ScriptObject", "Marker"):
                    floor = content.floor_at(p[0], p[2], p[1] + 24)
                    if floor is not None and p[1] - floor < 200:
                        point[2] = int(round(floor * SCALE - project.offset[2])) + 2
                self.points[o["name"]] = point.tolist()
        self.detail_faces(build)
        self.bright_scale(build)

    def bright_scale(self, build) -> None:
        """BLV lights carry colour x BrightScale (the Ruined Temple's route): MM9 weights each Light by it, and this map's
        dim warm and green fills (BrightScale 0.15-0.25) at full colour would wash out its blue (the DAT lightmaps'
        B/R is 2.5-4). Bake-only lights keep their authored colour: the bake weighs them by BrightScale itself. The
        profile's direct_scale makes up the level; the model lighting takes light_scale (overrides.yml)."""
        scale = {light["name"]: light["bright_scale"] for light in build.lights}
        for record in build.package.metadata["lights"]:
            s = scale.get(record["id"], 1.0)
            record["color"] = [int(round(c * s)) for c in record["color"]]
        for light in build.lights:
            if light["kept"]:
                light["colour_in_blv"] = [int(round(c * light["bright_scale"])) for c in light["colour"]]

    def detail_faces(self, build) -> None:
        """The BLV keeps at most 7 000 outlines (the 875-byte seen-lines bitset): every edge that borders a floor counts.
        Thousand Terrors has about twice that. Up-facing faces go to a TRIGGER_detail node compiled with the invisible
        flag (the outline pass skips them), smallest first, until the estimate (outlines.py) is under the budget; the
        scene draws them again at load (face_attribute_overrides) and they keep their collision (Chasm of the Dead)."""
        package = build.package
        drawn = []
        for node, entries in package.nodes.items():
            if node.startswith(("ROOM_", "STATIC_", "TRIGGER_nonsolid_")):
                drawn += [(node, i, np.asarray(e[0], float)) for i, e in enumerate(entries)]
        split = [np.asarray(e[0], float) for node, entries in package.nodes.items() if not node.startswith("MECH_")
                 for e in entries]
        before = outlines.count([d[2] for d in drawn], split)
        build.stats["outlines_estimate_all"] = before
        candidates, always = [], set()
        for node, i, p in drawn:
            n = np.cross(p, np.roll(p, -1, axis=0)).sum(axis=0).astype(float)
            nz = n[2] / max(np.linalg.norm(n), 1e-9)
            if nz < 0.45:
                continue                    # only floors (facet types 3, 4) make outlines
            if node.startswith("TRIGGER_nonsolid_"):
                # the 117 translucent water123.spr orbs over the candles (84 polygons each) and the webs: never on a map
                always.add((node, i))
                continue
            if not node.startswith("ROOM_"):
                continue
            area = 0.5 * np.linalg.norm(n)
            # steep floors (stair ramps, bevels) first, then by area: the big floors stay on the minimap
            candidates.append((0 if nz < 0.85 else 1, area, node, i))
        candidates.sort()
        chosen = 0
        lo, hi = 0, len(candidates)
        if before > OUTLINE_BUDGET:
            while lo < hi:                  # the fewest smallest faces that bring the estimate under the budget
                mid = (lo + hi) // 2
                moved = {(c[2], c[3]) for c in candidates[:mid]} | always
                if outlines.count([d[2] for d in drawn if (d[0], d[1]) not in moved], split) <= OUTLINE_BUDGET:
                    hi = mid
                else:
                    lo = mid + 1
            chosen = lo
        moved = {(c[2], c[3]) for c in candidates[:chosen]} | always
        build.stats["outline_detail_faces"] = chosen
        build.stats["outline_detail_nonsolid_faces"] = len(always)
        build.stats["outline_detail_max_area"] = round(float(candidates[chosen - 1][1])) if chosen else 0
        build.stats["outlines_estimate"] = outlines.count([d[2] for d in drawn if (d[0], d[1]) not in moved], split)
        print(f"outlines: estimate {before} -> {build.stats['outlines_estimate']}, {chosen} of {len(candidates)} "
              f"up-facing faces to TRIGGER_detail (largest {build.stats['outline_detail_max_area']})", flush=True)
        self.detail_rings = []
        for node in [n for n in package.nodes if n.startswith(("ROOM_", "TRIGGER_nonsolid_"))]:
            keep, detail = [], []
            for i, entry in enumerate(package.nodes[node]):
                (detail if (node, i) in moved else keep).append(entry)
            if not detail:
                continue
            room = node[5:] if node.startswith("ROOM_") else node[len("TRIGGER_nonsolid_"):]
            if keep or node.startswith("ROOM_"):
                package.nodes[node] = keep
            else:                           # every face of the node moved: drop it (the compiler wants no empty node)
                del package.nodes[node]
                package.room_nodes[f"room_{room}"].remove(node)
                package.metadata["surfaces"] = [s for s in package.metadata["surfaces"] if s["source_node"] != node]
            target = f"TRIGGER_detail_{room}" if node.startswith("ROOM_") else f"TRIGGER_detailns_{room}"
            package.nodes[target].extend(detail)
            self.detail_rings += [entry[0] for entry in detail]
            if target not in package.room_nodes[f"room_{room}"]:
                package.room_nodes[f"room_{room}"].append(target)
                flags = ["invisible"] if node.startswith("ROOM_") else ["invisible", "untouchable"]
                package.metadata["surfaces"].append({"id": target, "source_node": target, "flags": flags})

    def weighted_lift_lines(self, build, groups: dict) -> list[str]:
        """MM9's WeightedLift (the water hall's stepping stones): TouchToOpen, a touch starts it after MoveDelay, it sinks
        MoveDist along MoveDir at Speed (the mover: overrides.yml, `dat`), stays OpenWaitTime and rises at ClosingSpeed
        (the mover's auto-close). The touch is a polled box: its top's footprint grown by LIFT_TOUCH, from LIFT_TOUCH_DEPTH
        under its sunk top up to its resting top, so a party standing on it or swimming against it touches it."""
        lines = ["-- MM9's WeightedLift objects (the water hall's stones; TouchToOpen): a touch (standing on it, or swimming",
                 "-- against it) starts it after MoveDelay; it sinks MoveDist at Speed, waits OpenWaitTime and rises again at",
                 "-- ClosingSpeed (the mover's auto-close), carrying what stands on it. A touched lift takes no new touch until",
                 "-- it is back up (busy seconds).",
                 "local LIFTS = {"]
        for name in sorted(n for n in groups if n.startswith("WeightedLift")):
            p = build.source.properties(name)
            points = build.project.native(np.concatenate([q.points for q in build.source.polygons(name)]))
            low, high = points.min(0), points.max(0)
            drop = float(p["MoveDist"]) * SCALE
            delay = float(p.get("MoveDelay") or 0.0)
            busy = delay + float(p["MoveDist"]) / float(p["Speed"]) + float(p.get("OpenWaitTime") or 0.0) \
                + float(p["MoveDist"]) / float(p.get("ClosingSpeed") or p["Speed"])
            box = [[round(low[0] - LIFT_TOUCH), round(low[1] - LIFT_TOUCH), round(high[2] - drop - LIFT_TOUCH_DEPTH)],
                   [round(high[0] + LIFT_TOUCH), round(high[1] + LIFT_TOUCH), round(high[2] + 10)]]
            lines.append(f"    {name} = {{box = {{{{{box[0][0]}, {box[0][1]}, {box[0][2]}}}, {{{box[1][0]}, {box[1][1]}, "
                         f"{box[1][2]}}}}}, delay = {delay:g}, busy = {busy:.1f}}},")
        lines.append("}")
        return lines

    def gate0_centre(self, build) -> list:
        """StairGate0's centre (native): the middle of its faces' box."""
        points = np.concatenate([p.points for p in build.source.polygons("StairGate0")])
        return build.project.native((points.min(0) + points.max(0)) / 2).round().astype(int).tolist()

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor, self.class_monster, self.death = [], {}, {}, {}
        self.fly_leave = {}
        self.greater_on_death = []
        for o in source.objects:
            if o["class"] not in build.project.monster_classes or o["name"] not in bases:
                continue
            name, p = o["name"], o["properties"]
            group, hidden, friendly, dormant = 0, False, False, False
            if o["class"] == "NjamtheMeddler":
                # NjamTaunt.scr (NjamtheMeddler0) and NjamFreeze.scr (Njam): hidden until the map's script shows them
                group = GROUP_NJAM_TAUNT if name == "NjamtheMeddler0" else GROUP_NJAM_FINAL
                hidden, friendly = True, True
            elif o["class"] == "FlyingIcky":
                group, dormant = GROUP_CRITTERS, True     # 1000T_FlyingCreature_.scr: they wait for their Go
            record = content.actor(o, bases[name], sector_of_room, group=group, hidden=hidden, friendly=friendly,
                                   floor_query_lt=p["Pos"][1] + 40)
            if dormant:
                record["dormant"] = True
            if o["class"] == "FlyingIcky":
                # 1000T_FlyingCreature_.scr: Go flies the critter once along its marker list at FlyVel 900 LT/s and
                # :OnTraverseDone removes it at the list's last marker (RemoveObject; OnStuck RemoveMe too). The flight
                # itself is not carried (the AI wanders the stops), so it is removed after that flight's time.
                pos = record["position"]
                stops = [[pos["x"], pos["y"], pos["z"]]] + list((record.get("mm9_ai") or {}).get("path") or [])
                length = sum(float(np.linalg.norm(np.subtract(b, a))) for a, b in zip(stops, stops[1:]))
                self.fly_leave[name] = round(length / (CRITTER_FLY_VEL * SCALE), 1)
            if o["class"] == "NjamtheMeddler":
                record["immobile"] = True
            if name == "NjamtheMeddler0":
                # SpawnNjam.scr's Njam1000.scr (this placement stands in for it at the markers): Njam1000.inc :Init
                # SetPropNumber CanDamage FALSE, so no hit of any kind hurts him (the strict engine flag); he leaves on
                # SpawnNjam's 20-60 s timer (his HP threshold vanish is never reached, as in MM9)
                record["mm9_can_receive_damage"] = False
            self.actor[name] = record["actor_index"]
            self.class_monster.setdefault(o["class"], record["monster_id"])
            target = p.get("DeathTriggerTarget")
            if target:
                self.death[record["actor_index"]] = (str(target), str(p.get("DeathTriggerMessage") or "").lower())
            if o["class"] == "LesserDemon" and str(p.get("ScriptParams") or "").split()[:1] == ["1"]:
                self.greater_on_death.append(record["actor_index"])      # LesserDemon13/14: LesserDemon.scr p0 1
            out.append(record)
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        import cinematics_1000t as cinema
        # the weighted lifts (TouchToOpen) take their touch from this map's own poll (LIFTS: MoveDelay, a touch from
        # the water), not the shared TouchToOpen poll, which opens at once and reopens one a swimmer floats over
        for m in build.movers:
            if str(m["group"]).startswith("WeightedLift"):
                m["touch"] = False
        if not getattr(build, "lua_only", False):
            import pickle
            state = {"hooks": {k: v for k, v in self.__dict__.items()}, "movers": build.movers,
                     "report": build.content.report}
            (build.project.work / "lua_state.pkl").write_bytes(pickle.dumps(state))
        script = lua.Script(build, "Thousand Terrors")
        # MM9 model names with spaces ('Rotating Lever 17') are no Lua identifiers (Dook's Castle)
        script.door = {name.replace(" ", "_"): door for name, door in script.door.items()}
        script.lines[4] = "local DOORS = {" + ", ".join(f"{k} = {v}" for k, v in sorted(script.door.items())) + "}"
        script.chests()
        source, project = build.source, build.project
        doors = yaml.safe_load((build.runtime / f"{project.stem}.doors.yml").read_text()) or []
        door_faces = {d["door_id"]: d["face_ids"] for d in doors}
        rules = project.overrides["models"]
        model_group = {m: r["group"] for m, r in rules.items() if isinstance(r, dict)}
        groups = {g: ids for g, ids in script.groups.items()}
        events = {}
        for m in build.movers:
            if m["event"]:
                events[m["group"]] = m["event"]
        # Open/Close triggers of every mover model (Door, RotatingDoor, Button, Lift), by group.
        on_open, on_close = {}, {}
        for model, group in model_group.items():
            p = source.properties(model) if source.object_class(model) else {}
            on_open.setdefault(group, []).extend(messages(p, "OpenTriggerTarget", "OpenTrigger"))
            on_close.setdefault(group, []).extend(messages(p, "CloseTriggerTarget", "CloseTrigger"))
        # The objects the dispatcher knows.
        kinds = {}
        triggers = []
        for o in source.objects:
            p, name = o["properties"], o["name"]
            if o["class"] == "Trigger":
                kinds[name] = "trigger"
                triggers.append((name, self.boxes.get(name), bool(p.get("StartOn")),
                                 messages(p, "TargetName", "MessageName")))
            elif o["class"] == "Shooter":
                kinds[name] = "shooter"
            elif o["class"] == "Spawner":
                kinds[name] = "spawner"
            elif o["class"] == "ScriptObject":
                kinds[name] = "script"
        for model, group in model_group.items():
            # The lift's gears (RotatingBrush, mover spin) are no doors: a message to one must not move its group
            # (GearElevator's own Open/CloseTriggers send them toggle). lift() spins them with the lift's timing.
            kinds[model] = "spinner" if source.object_class(model) == "RotatingBrush" else "door"
        for name in self.actor:
            kinds.setdefault(name, "actor")
        skulls = {}
        for o in source.objects:
            script_name = (o["properties"].get("ScriptName") or "").lower()
            if script_name.endswith("1000t_sorcstatues.scr"):
                kinds[o["name"]] = "statue"
            elif script_name.endswith("1000t_skeletonhead.scr"):
                # 1000T_SkeletonHead.scr: ScriptParams name its two shooters (sShooterA, sShooterB)
                kinds[o["name"]] = "skull"
                skulls[o["name"]] = str(o["properties"].get("ScriptParams") or "").split()[:2]
        # Shooters: their projectile, damage, interval; the circle and skeleton-head ones fire a burst.
        shooter_lines = []
        for o in source.objects:
            if o["class"] != "Shooter":
                continue
            p = o["properties"]
            missile, damage_type = MISSILES.get(str(p.get("ProjectileName", "")).lower(), ("Fire", "Fire"))
            script_name = str(p.get("ScriptName") or "").lower()
            params = str(p.get("ScriptParams") or "").split()
            burst, target, stop = "nil", "nil", "nil"
            if "circleshooter" in script_name:      # ListMaker over markers 0..4: five shots, then its stop trigger
                burst, stop = "5", lua_str(params[5])
            elif "skheadshooter" in script_name:
                burst = params[1]
            elif "lightningshooter" in script_name:
                target = lua.point(self.points[params[0]])
            interval = as_float(p.get("ShootInterval")) or 1.0
            shooter_lines.append(f"    {name_key(o['name'])} = {{at = {lua.point(self.points[o['name']])}, missile = "
                                 f"\"{missile}\", projectile = {lua_str(str(p.get('ProjectileName') or ''))}, "
                                 f"kind = \"{damage_type}\", damage = {int(p.get('DamageAmt') or 50)}, "
                                 f"every = {max(1, round(interval * 4))}, burst = {burst}, target = {target}, "
                                 f"stop = {stop}}},")
        statue_lines = []
        for o in source.objects:
            if kinds.get(o["name"]) == "statue":
                k = int(o["name"][len("SorceressStatue"):])
                statue_lines.append(f"    {name_key(o['name'])} = {{shooter = "
                                    f"\"{str(o['properties']['ScriptParams']).split()[0]}\", cog = {COG_STATUE + k}}},")
        clip_seconds = glb_clip_seconds(STATUE_ANIM)
        # Spawns: Spawner DefaultSpawn, SpawnLoc / SpawnGeneric params, SpawnNjam markers.
        spawn_lines = []
        count_names = []
        greater_spawns = []     # LesserDemon.scr p0 1 on what they spawn (spawned_greater_on_death)
        for o in source.objects:
            p, name = o["properties"], o["name"]
            script_name = str(p.get("ScriptName") or "").lower().replace("scripts\\", "")
            what = None
            if o["class"] == "Spawner":
                what = str(p.get("DefaultSpawn") or "").split()[0] if p.get("DefaultSpawn") else None
                if script_name == "endcounttrigger.scr":
                    count_names.append(name)
            elif script_name in ("spawnloc.scr", "spawngeneric.scr"):
                params = str(p.get("ScriptParams") or "").split()
                what = params[0] if params else None
                if script_name == "spawngeneric.scr" and len(params) > 1 and params[1] == "Terrors":
                    count_names.append(name)
            if what and what in self.class_monster and spawned_greater_on_death(o):
                greater_spawns.append(name)
            if what and what in self.class_monster:
                # SpawnGeneric.scr :Onspawn2: DoClientFX g_hMyObject, GreaterDemon where the monster appears
                effect = ", effect = \"mm9:GreaterDemon\"" if script_name == "spawngeneric.scr" else ""
                spawn_lines.append(f"    {name_key(name)} = {{monster = {self.class_monster[what]}, at = "
                                   f"{lua.point(self.points[name])}{effect}}},   -- {what}")
        njam_markers = [o["name"] for o in source.objects
                        if str(o["properties"].get("ScriptName") or "").lower() == "spawnnjam.scr"]
        # Chess: the squares each static piece attacks (ChessPawn/Knight/Bishop.scr CheckPath; BoardObj<k>,
        # k = 8 z + x), as boxes over the squares.
        attackers = chess_attackers(source)
        queens = {k: pawn for pawn, squares in queening_pawns(source).items() for k in squares}
        square_boxes = []
        for k in sorted(attackers):
            c = np.array(source.properties(f"BoardObj{k}")["Pos"], float)
            low, high = project.native(c - [44, 0, 48]), project.native(c + [44, 80, 48])
            fields = ["box = {" + lua.point(np.minimum(low, high)) + ", " + lua.point(np.maximum(low, high)) + "}",
                      "pieces = {" + ", ".join(lua_str(n) for n in attackers[k]) + "}"]
            if k in queens:
                fields += [f"queen = {lua_str(queens[k])}", f"at = {lua.point(project.native(c + [0, 20, 0]))}"]
            square_boxes.append("{" + ", ".join(fields) + "}")
        self.chess_squares = sorted(attackers)
        queen_monster, queen_hp = mm9_class_monster_id(QUEEN_CLASS)
        # Button puzzle blocks: door ids and face ids per pad.
        pad_lines = []
        for pad, root in PADS.items():
            ids = [groups[f"{root}{k}"][0] for k in range(16)]
            faces = sorted({f for k in range(16) for d in groups[f"{root}{k}"] for f in door_faces[d]})
            pad_lines.append(f"    {pad} = {{doors = {{{', '.join(map(str, ids))}}}, faces = {{{', '.join(map(str, faces))}}}, "
                             f"locked = {'true' if root != 'PuzzleDoor' else 'false'}}},")
        piece_faces = ", ".join(f"{name} = {{{', '.join(map(str, faces))}}}" for name, faces in self.piece_faces.items())

        lines = [
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z + 170 >= b[1][3] and z <= b[2][3] end",
            "local function give(raw, source)",
            "    local item = MM9.ItemIds[raw]",
            "    if item ~= nil and evt.GivePartyMemberItem(math.max(0, evt.GetCurrentPlayerIndex()), item) then return true end",
            "    return MM9.giveItem(raw, source)",
            "end",
            "local function hurt(amount) evt.DamagePlayer(Players.All, const.Damage.Physical, amount) end",
            "",
            "-- Door groups (overrides.yml) by DAT model, and their MM9 Open/CloseTrigger messages.",
            "local GROUPS = {" + ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(groups.items())) + "}",
            "local MODEL_GROUP = {" + ", ".join(f"[{lua_str(m)}] = \"{g}\"" for m, g in sorted(model_group.items())) + "}",
            "local ON_OPEN = {" + ", ".join(f"{g} = {{{', '.join('{' + lua_str(t) + ', ' + lua_str(m) + '}' for t, m in v)}}}"
                                             for g, v in sorted(on_open.items()) if v) + "}",
            "local ON_CLOSE = {" + ", ".join(f"{g} = {{{', '.join('{' + lua_str(t) + ', ' + lua_str(m) + '}' for t, m in v)}}}"
                                              for g, v in sorted(on_close.items()) if v) + "}",
            "local KIND = {" + ", ".join(f"[{lua_str(n)}] = \"{k}\"" for n, k in sorted(kinds.items())) + "}",
            "local ACTOR = {" + ", ".join(f"[{lua_str(n)}] = {i}" for n, i in sorted(self.actor.items())) + "}",
            "local SHOOTERS = {", *shooter_lines, "}",
            "local STATUES = {", *statue_lines, "}",
            "local SKULLS = {" + ", ".join(f"[{lua_str(n)}] = {{cog = {COG_SKULL}, shooters = "
                                          f"{{{', '.join(lua_str(s) for s in shooters)}}}}}"
                                          for n, shooters in sorted(skulls.items())) + "}",
            "local SPAWNS = {", *spawn_lines, "}",
            "local COUNTS = {" + ", ".join(f"[{lua_str(n)}] = true" for n in count_names) + "}",
            "local DEATH = {" + ", ".join(f"[{i}] = {{{lua_str(t)}, {lua_str(m)}}}" for i, (t, m) in sorted(self.death.items()))
            + "}",
            # (getattr: a --lua rerun's lua_state.pkl from before 2026-11-06 has no list)
            "local GREATER_ON_DEATH = {" + ", ".join(f"[{i}] = true" for i in getattr(self, "greater_on_death", ()))
            + "}",
            "local GREATER_SPAWNS = {" + ", ".join(f"[{lua_str(n)}] = true" for n in greater_spawns) + "}",
            "local PADS = {", *pad_lines, "}",
            *self.weighted_lift_lines(build, groups),
            f"local PIECES = {{{piece_faces}}}",
            "local PAWN_FACES = {" + ", ".join(f"{name} = {{{', '.join(map(str, faces))}}}"
                                              for name, faces in getattr(self, "pawn_faces", {}).items()) + "}",
            "local TRIGGERS = {",
            *[f"    {{name = {lua_str(n)}, box = {('{' + lua.point(b[0]) + ', ' + lua.point(b[1]) + '}') if b else 'nil'}, "
              f"on = {'true' if on else 'false'}, msgs = {{{', '.join('{' + lua_str(t) + ', ' + lua_str(m) + '}' for t, m in msgs)}}}}},"
              for n, b, on, msgs in triggers],
            "}",
            "local TRIGGER = {}",
            "for _, t in ipairs(TRIGGERS) do TRIGGER[t.name] = t end",
            "local CHESS = {" + ", ".join(square_boxes) + "}",
            f"local NJAM_MARKERS = {{{', '.join(f'[{lua_str(n)}] = {lua.point(self.points[n])}' for n in njam_markers)}}}",
            f"local END_DEMON = {lua.point(self.points['EndDemonMarker'])}",
            f"local GATE0, GATE0_REACH = {lua.point(self.gate0_centre(build))}, {GATE0_REACH}",
            # (getattr: a --lua rerun's lua_state.pkl from before 2026-11-08 has no flight times)
            "local FLY_LEAVE = {" + ", ".join(f"[{lua_str(n)}] = {t}" for n, t in sorted(getattr(self, "fly_leave", {}).items()))
            + "}",
            "",
            "-- A scheduler on the 0.25 s poll (MM9's Wait): after(seconds, fn).",
            "local tick, tasks = 0, {}",
            "local function after(seconds, fn) table.insert(tasks, {at = tick + math.max(1, math.floor(seconds * 4 + 0.5)), fn = fn}) end",
            "-- 1000T_SorcStatues.scr: :Main2 plays fidget2 once (each statue holds its end); Go (:Start) sets bIsCasting",
            "-- (StatueCasting<name>), its shooter Go and :StartSequence: fidget2, then :Continue Taunt, then fidget2 ...",
            "-- while it casts; Stop (:TurnOff) clears it and the clip playing finishes. The clips (mm9_sorcererstatue's",
            "-- skinned copy) chain on the poll, each held until the tick after its end; the chains are runtime only, so",
            "-- map load starts them again. Its CastingSmoke (a Fire object) is not carried.",
            f"local STATUE_CLIPS = {{fidget2 = {clip_seconds['fidget2']:.3f}, taunt = {clip_seconds['taunt']:.3f}}}",
            "local statueChain = {}",
            "local function statueSequence(name, clip, chain)",
            "    if statueChain[name] ~= chain or var(\"StatueCasting\" .. name) ~= 1 then return end",
            "    evt.PlayDecorationClip(STATUES[name].cog, clip)",
            "    after(STATUE_CLIPS[clip] + 0.125, function()",
            "        statueSequence(name, clip == \"fidget2\" and \"taunt\" or \"fidget2\", chain)",
            "    end)",
            "end",
            "local function statueCasting(name)",
            "    statueChain[name] = (statueChain[name] or 0) + 1",
            "    statueSequence(name, \"fidget2\", statueChain[name])",
            "end",
            "-- A weighted lift's touch: it starts after its MoveDelay and takes no new touch until it is back up.",
            "local liftIdleAt = {}",
            "local function touchLift(name)",
            "    local lift = LIFTS[name]",
            "    liftIdleAt[name] = tick + math.floor(lift.busy * 4 + 0.5)",
            "    set(\"Touched\" .. name, var(\"Touched\" .. name) + 1)",
            "    after(lift.delay, function()",
            "        for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end",
            "    end)",
            "end",
            "local send",
            "",
            "-- Doors: MM9's Door / RotatingDoor / Button / Lift messages. A group's open state is kept in a map variable",
            "-- for the groups with Open/CloseTriggers; locks are map variables (MM9 Lock/Unlock, Locked).",
            "local function locked(group) return var(\"Lock\" .. group) == 1 end",
            "local function isOpen(group) return var(\"Open\" .. group) == 1 end",
            "local function run(list) if list then for _, m in ipairs(list) do send(m[1], m[2]) end end end",
            "local function openGroup(group)",
            "    for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Open) end",
            "    if not isOpen(group) then set(\"Open\" .. group, 1) run(ON_OPEN[group]) end",
            "end",
            "local function closeGroup(group)",
            "    for _, id in ipairs(GROUPS[group]) do evt.SetDoorState(id, DoorAction.Close) end",
            "    if isOpen(group) then set(\"Open\" .. group, 0) run(ON_CLOSE[group]) end",
            "end",
            "local function useGroup(group) if isOpen(group) then closeGroup(group) else openGroup(group) end end",
            "",
            "-- Shooters (MM9 Shooter: ProjectileName, DamageAmt, ShootInterval): on, they fire at the party (a lightning",
            "-- shooter at its marker); a burst shooter (1000T_CircleShooter.scr, 1000T_SkHeadShooter.scr) fires its count",
            "-- and stops, a circle shooter then triggers its stop trigger. A shot strikes the party in its path",
            "-- (FireMissile's strikesParty).",
            "local firing = {}",
            "local function fire(name)",
            "    local s = SHOOTERS[name]",
            "    local x, y, z = evt.GetPartyPosition()",
            "    z = z + 100",
            "    if s.target ~= nil then x, y, z = s.target[1], s.target[2], s.target[3] + 60 end",
            "    local dx, dy, dz = x - s.at[1], y - s.at[2], z - s.at[3]",
            "    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))",
            "    if s.target == nil and length > 4000 then return end",
            "    local k = math.min(64 / length, 0.33)",
            "    local shot = evt.FireMissile(s.missile, s.at[1] + dx * k, s.at[2] + dy * k, s.at[3] + dz * k, x, y, z, s.damage, s.kind, 0, 0, true)",
            "    if shot then MM9.launchSound(s.projectile, s.at[1], s.at[2], s.at[3]) end",
            "    set(\"ShotsFired\", var(\"ShotsFired\") + (shot and 1 or 0))",
            "end",
            "local function shooterOn(name)",
            "    local s = SHOOTERS[name]",
            "    if s == nil then return end",
            "    firing[name] = {next = tick, left = s.burst}",
            "end",
            "local function shooterOff(name) firing[name] = nil end",
            "",
            "-- Spawns (Spawner DefaultSpawn, SpawnLoc.scr, SpawnGeneric.scr): the monster appears at the object; EndCount.scr",
            "-- counts the end hall's spawns and, at the third, a Greater Demon appears at EndDemonMarker.",
            "local function spawn(name)",
            "    local s = SPAWNS[name]",
            "    if s == nil then return end",
            "    local _, made = evt.SummonMonstersById({monster = s.monster, x = s.at[1], y = s.at[2], z = s.at[3], radius = 48, count = 1, effect = s.effect})",
            "    set(\"Spawned\", var(\"Spawned\") + 1)",
            "    -- \"LesserDemon ScriptParams 1\" (Spawner8/13's DefaultSpawn; SpawnMgr.scr's LESSERDEMON for SpawnLoc's",
            "    -- LesserDemon): LesserDemon.scr p0 1, a Greater Demon from the body at death (the kill hook)",
            "    if GREATER_SPAWNS[name] and made ~= nil then for _, i in ipairs(made) do set(\"Greater\" .. i, 1) end end",
            "    set(\"Spawn\" .. name, var(\"Spawn\" .. name) + 1)",
            "    if COUNTS[name] then",
            "        set(\"EndCount\", var(\"EndCount\") + 1)",
            "        if var(\"EndCount\") == 3 then",
            "            -- EndDemon.scr :Main forces its spawn-in (g_bTemp = TRUE): hidden, :SpawnIn DoClientFX GreaterDemon,",
            "            -- the Spawn clip made visible, then Aware (the summon's mm9 script_params \"1\": the engine's spawn-in);",
            "            -- its :OnDeath opens the double gate Door0/Door1 before the win switch (the kill hook, EndDemon<index>)",
            "            evt.SpawnWorldEffect(\"mm9:GreaterDemon\", END_DEMON[1], END_DEMON[2], END_DEMON[3], 1)",
            "            local _, demons = evt.SummonMonstersById({monster = " + str(self.class_monster.get("GreaterDemon", 0))
            + ", x = END_DEMON[1], y = END_DEMON[2], z = END_DEMON[3], radius = 48, count = 1,"
            " mm9 = {script_params = \"1\"}})",
            "            if demons ~= nil then for _, i in ipairs(demons) do set(\"EndDemon\" .. i, 1) end end",
            "        end",
            "    end",
            "end",
            "",
            "-- Njam (SpawnNjam.scr, with key 108): at a marker he appears for 20-60 s and vanishes (one at a time).",
            "local function njamAppear(marker)",
            f"    if MM9.hasKey({KEY_NJAM_QUEST}) == 0 or MM9.hasKey({KEY_WON}) == 1 then return end",
            "    local p = NJAM_MARKERS[marker]",
            "    evt.SetMapActorPosition(ACTOR.NjamtheMeddler0, p[1], p[2], p[3])",
            "    -- Njam1000.scr: AddEnemy Player (hostile; CanDamage FALSE: njam.lua's hunt mode, no physical blow hurts him)",
            f"    evt.SetMonGroupBit({GROUP_NJAM_TAUNT}, MonsterBits.Invisible, false)",
            f"    evt.SetMonGroupBit({GROUP_NJAM_TAUNT}, MonsterBits.Hostile, true)",
            "    -- his BaseMelee + Range loop walks at the party (the placement holds him still for the taunt cinematic)",
            "    evt.SetActorImmobile(ACTOR.NjamtheMeddler0, false)",
            "    MM9.playSound(\"sounds/spells/townportal.wav\")",
            "    evt.SpawnWorldEffect(\"mm9:GreaterDemon\", p[1], p[2], p[3], 1)   -- :Onspawn2: DoClientFX g_hMyObject, GreaterDemon",
            "    set(\"NjamShown\", var(\"NjamShown\") + 1)",
            "    local shown = var(\"NjamShown\")",
            "    after(math.random(20, 60), function()",
            "        if var(\"NjamShown\") == shown then",
            "            MM9.clientFx(ACTOR.NjamtheMeddler0, \"mm9:GreaterDemon\")   -- :Vanish2: DoClientFX hNjam, GreaterDemon",
            f"            evt.SetMonGroupBit({GROUP_NJAM_TAUNT}, MonsterBits.Invisible, true)",
            f"            evt.SetMonGroupBit({GROUP_NJAM_TAUNT}, MonsterBits.Hostile, false)",
            "            evt.SetActorImmobile(ACTOR.NjamtheMeddler0, true)",
            "        end",
            "    end)",
            "end",
            "",
            "-- The button puzzles (ButtonPad.scr, ButtonPuzzle.scr): 16 blocks in a 4 x 4 wall, hidden in the ceiling",
            "-- (Main2) until the party springs the trap (SetTrap: the wall comes down, every block shut); a click pushes a",
            "-- block and its four neighbours in or out (ButtonPushed); all 16 in opens the wall for good (MoveAway); the",
            "-- pull (Reset) shuts them all. Hidden = faces invisible and untouchable (evt.SetFacetBit by face index).",
            "local function showPad(pad, shown)",
            "    for _, f in ipairs(PADS[pad].faces) do",
            f"        evt.SetFacetBit(-f, {INVISIBLE_FACE | UNTOUCHABLE_FACE}, not shown)",
            "    end",
            "end",
            "local function pressed(pad, k) return var(pad .. \"_\" .. k) == 1 end",
            "local function setBlock(pad, k, inward)",
            "    set(pad .. \"_\" .. k, inward and 1 or 0)",
            "    evt.SetDoorState(PADS[pad].doors[k + 1], inward and DoorAction.Open or DoorAction.Close)",
            "end",
            "local function resetPad(pad)",
            "    for k = 0, 15 do setBlock(pad, k, false) end",
            "end",
            "local function setTrap(pad)",
            "    if var(pad .. \"State\") ~= 0 then return end",
            "    set(pad .. \"State\", 1)",
            "    resetPad(pad)",
            "    showPad(pad, true)",
            "    MM9.playSound(\"sounds/door/stonedoorslam.wav\")",
            "end",
            "local function pushBlock(pad, k)",
            "    if var(pad .. \"State\") ~= 1 then return end",
            "    local col, row = k % 4, math.floor(k / 4)",
            "    setBlock(pad, k, not pressed(pad, k))",
            "    if col > 0 then setBlock(pad, k - 1, not pressed(pad, k - 1)) end",
            "    if col < 3 then setBlock(pad, k + 1, not pressed(pad, k + 1)) end",
            "    if row > 0 then setBlock(pad, k - 4, not pressed(pad, k - 4)) end",
            "    if row < 3 then setBlock(pad, k + 4, not pressed(pad, k + 4)) end",
            "    for j = 0, 15 do if not pressed(pad, j) then return end end",
            "    set(pad .. \"State\", 2)",
            "    MM9.playSound(\"sounds/door/doorlatch02.wav\")   -- ButtonPuzzle.scr :MoveDoor, then :EndDoor 0.8 s later",
            "    after(0.8, function()",
            "        MM9.playSound(\"sounds/door/stonedoorslide02.wav\")",
            "        showPad(pad, false)",
            "    end)",
            "end",
            "",
            "-- The dispatcher: MM9's Trigger messages (target, message), as the DAT links them.",
            "local function fireTrigger(name)",
            "    local t = TRIGGER[name]",
            "    if t == nil then return end",
            "    set(\"Fired\" .. name, var(\"Fired\" .. name) + 1)",
            "    run(t.msgs)",
            "end",
            "local function triggerOn(name)",
            "    local state = var(\"Trig\" .. name)",
            "    if state == 0 then return TRIGGER[name] ~= nil and TRIGGER[name].on end",
            "    return state == 1",
            "end",
            "send = function(target, msg)",
            "    if not MM9.receives(\"1000terrors\", target, msg, ACTOR[target]) then return end   -- a dead AI takes none",
            "    local kind = KIND[target]",
            "    if kind == \"trigger\" then",
            "        if msg == \"on\" then set(\"Trig\" .. target, 1)",
            "        elseif msg == \"off\" then set(\"Trig\" .. target, 2)",
            "        elseif msg == \"trigger\" then fireTrigger(target) end",
            "    elseif kind == \"door\" then",
            "        local group = MODEL_GROUP[target]",
            "        if msg == \"open\" then openGroup(group)",
            "        elseif msg == \"close\" then closeGroup(group)",
            "        elseif msg == \"use\" or msg == \"toggle\" then useGroup(group)",
            "        elseif msg == \"lock\" then set(\"Lock\" .. group, 1)",
            "        elseif msg == \"unlock\" then set(\"Lock\" .. group, 0) end",
            "    elseif kind == \"shooter\" then",
            "        if msg == \"on\" or msg == \"go\" then shooterOn(target) elseif msg == \"off\" or msg == \"stop\" then shooterOff(target) end",
            "    elseif kind == \"statue\" then",
            "        if msg == \"go\" then",
            "            shooterOn(STATUES[target].shooter)",
            "            set(\"StatueCasting\" .. target, 1)",
            "            statueCasting(target)",
            "        elseif msg == \"stop\" then",
            "            shooterOff(STATUES[target].shooter)",
            "            set(\"StatueCasting\" .. target, 0)",
            "        end",
            "    elseif kind == \"skull\" then",
            "        -- 1000T_SkeletonHead.scr: Go turns the skull about (:Start Rotate 0, 1, 0, 180, 180: half a turn",
            "        -- clockwise from above at 180/s, evt.AimDecoration; ignored while it turns), then :TurnOff sends both",
            "        -- shooters Go (1000T_SkHeadShooter.scr: ScriptParams' count of shots, one a second); Stop runs :TurnOff",
            "        -- at once. SkullTurns counts the half turns (aims are runtime only: map load puts it back).",
            "        if (msg == \"go\" or msg == \"stop\") and var(\"SkullTurning\" .. target) == 0 then",
            "            set(\"SkullTurning\" .. target, 1)",
            "            if msg == \"go\" then",
            "                set(\"SkullTurns\" .. target, var(\"SkullTurns\" .. target) + 1)",
            "                evt.AimDecoration(SKULLS[target].cog, -180 * var(\"SkullTurns\" .. target), 180)",
            "            end",
            "            after(msg == \"go\" and 1 or 0, function()",
            "                set(\"SkullTurning\" .. target, 0)",
            "                for _, s in ipairs(SKULLS[target].shooters) do shooterOn(s) end",
            "                set(\"SkullGo\" .. target, var(\"SkullGo\" .. target) + 1)",
            "            end)",
            "        end",
            "    elseif kind == \"spawner\" then",
            "        if msg == \"default\" or msg == \"spawn\" then spawn(target) end",
            "    elseif kind == \"script\" then",
            "        if PADS[target] ~= nil then",
            "            if msg == \"settrap\" then setTrap(target) elseif msg == \"reset\" and var(target .. \"State\") == 1 then resetPad(target) end",
            "        elseif NJAM_MARKERS[target] ~= nil then",
            "            if msg == \"spawn\" then njamAppear(target) end",
            "        elseif msg == \"spawn\" then",
            "            if not (var(\"Off\" .. target) == 1) then spawn(target) end",
            "        elseif msg == \"off\" then set(\"Off\" .. target, 1)",
            "        elseif msg == \"start\" and target == \"TauntMan\" then handlers[" + str(EV_WINMAN + 9) + "]() end",
            "    elseif kind == \"actor\" then",
            "        if msg == \"go\" and ACTOR[target] ~= nil then",
            "            evt.WakeActor(ACTOR[target])",
            "            -- 1000T_FlyingCreature_.scr :OnTraverseDone: RemoveObject at the last marker (the flight's time)",
            "            if FLY_LEAVE[target] ~= nil and var(\"Flown\" .. target) == 0 then",
            "                set(\"Flown\" .. target, 1)",
            "                after(FLY_LEAVE[target], function() MM9.removeActor(ACTOR[target]) end)",
            "            end",
            "        end",
            "    elseif target:sub(1, 10) == \"SpawnPiece\" then",
            "        if msg == \"destroy\" and PIECES[target] ~= nil then",
            "            for _, f in ipairs(PIECES[target]) do evt.SetFacetBit(-f, " + str(INVISIBLE_FACE | UNTOUCHABLE_FACE)
            + ", true) end",
            "            set(\"Destroyed\" .. target, 1)",
            "            MM9.playSound(\"sounds/events/stonecrumble.wav\")",
            "        end",
            "    elseif target == \"Rumble0\" then MM9.playSound(\"sounds/events/rubblecrash.wav\")",
            "    end",
            "end",
            "",
            "-- Plates (ShooterPlate, FireballPlate, FoyerShooterPlate): a trigger toggles the plate down; it rises after its",
            "-- CloseWaitTime and its CloseTriggers turn the shooters off and the trigger on again.",
        ]
        plate_waits = {}
        for model, group in model_group.items():
            if group.startswith(("ShooterPlate", "FireballPlate", "FoyerShooterPlate")):
                plate_waits[group] = float(source.properties(model).get("CloseWaitTime") or 3.0)
        lines += [
            "local PLATE_WAIT = {" + ", ".join(f"{g} = {w}" for g, w in sorted(plate_waits.items())) + "}",
            "local plainOpen = openGroup",
            "openGroup = function(group)",
            "    plainOpen(group)",
            "    if PLATE_WAIT[group] ~= nil then after(PLATE_WAIT[group], function() closeGroup(group) end) end",
            "end",
            "",
        ]
        # Click events of the plain doors (no lock, no messages): a toggle as the shared scaffolding does.
        own = set(self.mover_events)
        lines.append("-- Doors: a click toggles a group (MM9 Use); locked groups say so (MM9 LockJiggle).")
        clicks = sorted({(m["event"], m["group"]) for m in build.movers if m["event"] and m["group"] not in own})
        for event, group in clicks:
            lines.append(f"handlers[{event}] = function() if locked(\"{group}\") then evt.StatusText(\"Locked\") return end "
                         f"if ON_OPEN.{group} or ON_CLOSE.{group} then useGroup(\"{group}\") else "
                         + " ".join(f"evt.SetDoorState({d}, DoorAction.Trigger)" for d in groups[group]) + " end end"
                         f"   -- {group}")
            script.registrations.append((event, "Door", "Door", "event"))
        lines += [
            "",
            "-- Button puzzle blocks (ButtonPuzzle.scr :UseMe -> ButtonPad.scr :Button<k>), pulls (Pull1-3: Reset).",
        ]
        for pad_index, (pad, root) in enumerate(PADS.items()):
            for k in range(16):
                event = EV_BLOCK_BASE + 16 * pad_index + k
                lines.append(f"handlers[{event}] = function() pushBlock(\"{pad}\", {k}) end   -- {root}{k}")
                script.registrations.append((event, "Puzzle block", "Block", "event"))
        for pull, pad in PULLS.items():
            lines.append(f"handlers[{EV_PULL[pull]}] = function() useGroup(\"{pull}\") after(1, function() closeGroup(\"{pull}\") end) end"
                         f"   -- {pull}: OpenTrigger0 {pad} Reset")
            script.registrations.append((EV_PULL[pull], "Pull", "Lever", "event"))
        tomb_item = ITEM_TOMB_KEY
        gate0 = source.properties("StairGate0")
        gate0_wait = float(gate0.get("CloseWaitTime") or 0.0)
        # open (MoveDist at Speed, LT) plus the wait plus the close (MoveDist at ClosingSpeed): shut again after this
        gate0_shut = round(float(gate0["MoveDist"]) / float(gate0["Speed"]) + gate0_wait
                           + float(gate0["MoveDist"]) / float(gate0.get("ClosingSpeed") or gate0["Speed"]), 1)
        lines += [
            "",
            "-- Rotating Lever 17 (OpenTrigger0 TrapDoor1 open): the trap doors drop into the water pit; Levers 16/18 name",
            "-- 'Upper Chomper 1/2', which the DAT does not have (they only swing).",
            f"handlers[{EV_LEVER17}] = function() useGroup(\"Lever17\") end",
            "-- The gear elevator (LowerLever, LowerLever0: Open/CloseTrigger GearElevator toggle; Lift 912 LT up). Its",
            "-- gears (ElevatorGear1/2, RotatingBrush AttachTo GearElevator: they ride the lift) spin while it moves: the",
            "-- levers toggle them on, the lift's Open/CloseTriggers reverse them and turn them off as it arrives (912 LT",
            "-- at 200 LT/s).",
            "local function lift()",
            "    useGroup(\"GearElevator\")",
            "    MM9.playSound(\"sounds/door/elestart.wav\")",
            "    for _, gear in ipairs({DOORS.ElevatorGear1, DOORS.ElevatorGear2}) do evt.SpinMover(gear, \"on\") end",
            "    after(912 / 200, function()",
            "        for _, gear in ipairs({DOORS.ElevatorGear1, DOORS.ElevatorGear2}) do",
            "            evt.SpinMover(gear, \"reverse\"); evt.SpinMover(gear, \"off\")",
            "        end",
            "    end)",
            "end",
            f"handlers[{EV_LIFT_LEVER}] = function() for _, id in ipairs(GROUPS.LowerLever) do evt.SetDoorState(id, DoorAction.Trigger) end lift() end",
            f"handlers[{EV_LIFT_LEVER0}] = function() for _, id in ipairs(GROUPS.LowerLever0) do evt.SetDoorState(id, DoorAction.Trigger) end lift() end",
            "-- HiddenButton1 (Button, OpenTriggers: lock itself, TreasureDoor and TreasureDoor0 open).",
            f"handlers[{EV_HIDDEN_BUTTON}] = function() if not locked(\"HiddenButton1\") then openGroup(\"HiddenButton1\") end end",
            f"-- ToLowerTombGate (DoorLock.scr \"599\"): opens for a party with item {tomb_item}. The gate has no Open or",
            "-- CloseTriggers and shuts by itself (CloseWaitTime), so a click toggles the gate itself, not the script's open",
            "-- flag (which its auto-close never cleared: a click after it shut did nothing).",
            f"handlers[{EV_TOMB_GATE}] = function()",
            f"    if MM9.hasItem({tomb_item}, \"1000terrors:DoorLock\") == 1 or MM9.hasItem({tomb_item}, \"1000terrors:DoorLock\") == true then",
            "        for _, id in ipairs(GROUPS.ToLowerTombGate) do evt.SetDoorState(id, DoorAction.Trigger) end",
            "    else evt.StatusText(\"Locked\") end",
            "end",
            f"-- StairGate0 (Door, PushOpen, AITriggerable, CloseWaitTime {gate0_wait:g}; DoorLock.scr \"{ITEM_STAIRS_KEY}; 1\"):",
            f"-- DoorLock's :OnUse, with the stairs key ({ITEM_STAIRS_KEY}, TreasureChest5) in the packs, unlocks the gate and",
            "-- takes the key (bTakeKey), then exits FALSE: the door's own use goes on. The DAT leaves the gate unlocked, so a",
            "-- use opens it with or without the key. MM9's monsters push it open (AITriggerable): the poll opens it for a",
            "-- hostile monster beside it (on the landing, or south of it once StairGate is open). The gate shuts by itself",
            "-- (its CloseWaitTime), so a use always opens it and its open flag clears when it has shut again.",
            "local gate0Opens = 0",
            "local function openGate0()",
            "    for _, id in ipairs(GROUPS.StairGate0) do evt.SetDoorState(id, DoorAction.Open) end",
            "    set(\"OpenStairGate0\", 1)",
            "    gate0Opens = gate0Opens + 1",
            "    local this = gate0Opens",
            f"    after({gate0_shut:g}, function() if gate0Opens == this then set(\"OpenStairGate0\", 0) end end)",
            "end",
            f"handlers[{EV_STAIR_GATE0}] = function()",
            f"    if MM9.hasItem({ITEM_STAIRS_KEY}, \"1000terrors:DoorLock\") == 1 then MM9.takeItem({ITEM_STAIRS_KEY}, \"1000terrors:DoorLock\") end",
            "    openGate0()",
            "end",
            f"-- FoyerDoorSouth1/2 (WinMan.scr :Init, TELP): shut and locked until the party holds key {KEY_NJAM_QUEST}.",
            f"handlers[{EV_FOYER_DOOR}] = function()",
            f"    if MM9.hasKey({KEY_NJAM_QUEST}) == 0 then evt.StatusText(\"Locked\") return end",
            "    for _, id in ipairs(GROUPS.FoyerDoorSouth) do evt.SetDoorState(id, DoorAction.Trigger) end",
            "end",
            "",
            # WinMan.scr :OnUse: the cinematic njam_freeze_win (cinematics_1000t.py: its steps carry the experience, the
            # removals, key 109 and the change of level)
            *cinema.win_handler(EV_WINMAN, f"{balanced_experience(WIN_EXPERIENCE, KEY_WON, 'winman.scr', 'OnUse')}"
                                f"{experience_note(WIN_EXPERIENCE, KEY_WON, 'winman.scr', 'OnUse')}",
                                cinema.switch_min_y(cinema.Frame(PROJECT)), cinema.Frame(PROJECT),
                                cinema.Objects.load(project.stem)),
            "",
            "-- The genie lamp (GiveRandom.scr, once): gold 100-1000, experience 100-1000, an item of its list, healing",
            "-- 100-1000 or (as MM9's GiveAttribute 1-2) experience again; TriggerSmokeOn is only smoke.",
            "local GENIE_ITEMS = {" + ", ".join(str(i) for i in GENIE_ITEMS if i not in GENIE_UNRESOLVED) + "}",
            f"handlers[{EV_GENIE}] = function()",
            "    if var(\"GenieUsed\") == 1 then return end",
            "    set(\"GenieUsed\", 1)",
            "    local roll = math.random(0, 4)",
            "    if roll == 0 then MM9.giveGold(math.random(100, 1000))",
            "    elseif roll == 2 then give(GENIE_ITEMS[math.random(1, #GENIE_ITEMS)], \"1000terrors:GiveRandom\")",
            "    elseif roll == 3 then AddValue(HP, math.random(100, 1000))",
            "    else MM9.giveExperience(math.random(100, 1000)) end",
            "    MM9.playSound(\"sounds/magic/windup10.wav\")",
            "end",
            "",
            f"-- TauntMan.scr (Trigger19 Start; key {KEY_NJAM_QUEST} without {KEY_TAUNTED}): the cinematic "
            f"{cinema.TAUNT_ID} (cinematics_1000t.py:",
            f"-- key {KEY_TAUNTED}, Door0, Njam's walk to TauntMarker and his vanishing).",
            f"handlers[{EV_WINMAN + 9}] = function()",
            f"    if MM9.hasKey({KEY_NJAM_QUEST}) == 0 or MM9.hasKey({KEY_TAUNTED}) == 1 then return end",
            f"    MM9Cinematic.start(\"{cinema.TAUNT_ID}\")",
            "end",
            "",
            "-- Monsters' DeathTriggerTarget (GreaterDemon1 -> Spawner8, Oculus7 -> TP5, LesserDemon13/14 -> TP4 ...).",
            f"handlers[{KILL_HOOK}] = function(context)",
            "    local d = context.actorIndex ~= nil and DEATH[context.actorIndex] or nil",
            "    if d ~= nil then send(d[1], d[2]) end",
            "    -- EndDemon.scr :OnDeath (lines 25-33): sDoorA Open (declared Door1, then Door0): the double gate before the",
            "    -- win switch, both leaves",
            "    if context.actorIndex ~= nil and var(\"EndDemon\" .. context.actorIndex) == 1 then",
            "        set(\"EndDemon\" .. context.actorIndex, 0)",
            "        set(\"EndDemonDead\", 1)",
            "        openGroup(\"Door0\")",
            "        openGroup(\"Door1\")",
            "    end",
            "    -- LesserDemon.scr p0 1 (the placed LesserDemon13/14, and the spawned \"LesserDemon ScriptParams 1\" spawn()",
            "    -- marks): :OnDeathDone spawns a Greater Demon at the body (sSpawnCmd \"GreaterDemon ScriptParams 1\": it",
            "    -- spawns in, the summon's mm9 script_params).",
            "    if context.actorIndex ~= nil and (GREATER_ON_DEATH[context.actorIndex]",
            "            or var(\"Greater\" .. context.actorIndex) == 1) then",
            "        set(\"Greater\" .. context.actorIndex, 0)",
            "        local x, y, z = evt.GetMapActorPosition(context.actorIndex)",
            "        if x ~= nil then evt.SummonMonstersById({monster = " + str(self.class_monster.get("GreaterDemon", 0))
            + ", x = x, y = y, z = z, radius = 32, count = 1, mm9 = {script_params = \"1\"}, "
            "effect = \"mm9:GreaterDemon\"}) end   -- GreaterDemon.scr :SpawnIn: DoClientFX GreaterDemon",
            "    end",
            "end",
            "",
            "-- ChessBase.inc :PawnToQueen: a pawn whose attack ends on the last rank (ChessPiece1 from square 51) becomes a",
            f"-- Terror at that square once its slide is done ({CHESS_SLIDE_SECONDS:g} s): the piece is gone (RemoveObject), the "
            f"Terror (HitPoints {QUEEN_HIT_POINTS}, its fireblue",
            "-- effect) is the party's enemy. The other pieces stay on their squares here (MM9 slides each onto the square it",
            "-- attacks), so the pawn on square 35 never reaches the last rank; a square only a queened pawn attacked is safe.",
            "local queening = {}",
            "local function chessAttacked(c)",
            "    for _, piece in ipairs(c.pieces) do if var(\"Queened\" .. piece) == 0 then return true end end",
            "    return false",
            "end",
            "local function hidePawn(pawn)",
            f"    for _, f in ipairs(PAWN_FACES[pawn] or {{}}) do evt.SetFacetBit(-f, {INVISIBLE_FACE | UNTOUCHABLE_FACE}, true) end",
            "end",
            "local function queen(c)",
            "    if c.queen == nil or var(\"Queened\" .. c.queen) == 1 or queening[c.queen] then return end",
            "    queening[c.queen] = true",
            f"    after({CHESS_SLIDE_SECONDS}, function()",
            "        set(\"Queened\" .. c.queen, 1)",
            "        hidePawn(c.queen)",
            f"        evt.SummonMonstersById({{monster = {queen_monster}, x = c.at[1], y = c.at[2], z = c.at[3], radius = 64, "
            f"count = 1, hpScale = {QUEEN_HIT_POINTS / queen_hp:.4f}}})",
            "        evt.SpawnWorldEffect(\"mm9:fireblue\", c.at[1], c.at[2], c.at[3], 1)",
            "    end)",
            "end",
            "",
            "-- The poll (four times a second): MM9's Trigger volumes (any part of the party in the box; StartOn, on/off",
            "-- messages), the chess squares, the shooters and the scheduled waits.",
            "local inside, onSquare = {}, false",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    tick = tick + 1",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for _, t in ipairs(TRIGGERS) do",
            "        if t.box ~= nil then",
            "            local now = inBox(t.box, x, y, z)",
            "            if now and not inside[t.name] and triggerOn(t.name) then fireTrigger(t.name) end",
            "            inside[t.name] = now",
            "        end",
            "    end",
            "    for name, lift in pairs(LIFTS) do",
            "        if inBox(lift.box, x, y, z) and tick >= (liftIdleAt[name] or 0) then touchLift(name) end",
            "    end",
            "    local square = nil",
            "    for _, c in ipairs(CHESS) do if inBox(c.box, x, y, z) and chessAttacked(c) then square = c end end",
            "    if square ~= nil and not onSquare then",
            "        MM9.playSound(\"sounds/door/doorslidestone.wav\")",
            f"        hurt({CHESS_DAMAGE})",
            "        set(\"ChessHits\", var(\"ChessHits\") + 1)",
            "        queen(square)",
            "        MM9Cinematic.chessCapture(square)   -- ChessBase.inc :StartCamera (cinematics_1000t.py)",
            "    end",
            "    onSquare = square ~= nil",
            "    if tick % 4 == 0 and not isOpen(\"StairGate0\") then     -- every actor, the spawned ones too",
            "        local scan = 0   -- not `index`: pack growth's Lua scan (density.py) takes every `index` for one",
            "        while true do",
            "            local ax, ay, az = evt.GetMapActorPosition(scan)",
            "            if ax == nil then break end",
            "            -- south of the gates a monster reaches StairGate0 only through an open StairGate",
            "            if math.abs(ax - GATE0[1]) < GATE0_REACH and math.abs(ay - GATE0[2]) < GATE0_REACH",
            "                    and math.abs(az - GATE0[3]) < GATE0_REACH and (ay > GATE0[2] or isOpen(\"StairGate\"))",
            "                    and evt.IsMapActorHostile(scan) then",
            "                openGate0()",
            "                set(\"Gate0ByMonster\", 1)",
            "                break",
            "            end",
            "            scan = scan + 1",
            "        end",
            "    end",
            "    for name, f in pairs(firing) do",
            "        if tick >= f.next then",
            "            fire(name)",
            "            f.next = tick + SHOOTERS[name].every",
            "            if f.left ~= nil then",
            "                f.left = f.left - 1",
            "                if f.left <= 0 then",
            "                    firing[name] = nil",
            "                    if SHOOTERS[name].stop ~= nil then fireTrigger(SHOOTERS[name].stop) end",
            "                end",
            "            end",
            "        end",
            "    end",
            "    local due = {}",
            "    for i = #tasks, 1, -1 do if tasks[i].at <= tick then table.insert(due, tasks[i].fn) table.remove(tasks, i) end end",
            "    for _, fn in ipairs(due) do fn() end",
            "end",
            "",
            "-- Map load: locks (Locked doors, the B and C puzzle walls), the puzzle walls hidden until their trap, destroyed",
            "-- statues gone, Njam's triggers only with key 108 (SpawnNjam.scr :Init), the taken scroll, the poll.",
            "handlers[1] = function()",
            "    if var(\"Loaded\") == 0 then",
            "        set(\"Loaded\", 1)",
            "        set(\"LockToLowerTombGate\", 0)",
            "        for _, g in ipairs({" + ", ".join(f'"{root}{k}"' for root in ("PuzzleDoorB", "PuzzleDoorC")
                                              for k in range(16)) + "}) do set(\"Lock\" .. g, 1) end",
            "    end",
            "    -- StairGate (Door: no PushOpen, no lock in the DAT): no use opens it, only LesserDemon0's DeathTriggerTarget",
            "    -- (StairGate open); the lock answers a click as MM9's LockJiggle (the death's open ignores it)",
            "    if not isOpen(\"StairGate\") then set(\"LockStairGate\", 1) end",
            "    for pad, _ in pairs(PADS) do showPad(pad, var(pad .. \"State\") == 1) end",
            "    for pawn, _ in pairs(PAWN_FACES) do if var(\"Queened\" .. pawn) == 1 then hidePawn(pawn) end end",
            "    for name, skull in pairs(SKULLS) do evt.AimDecoration(skull.cog, -180 * var(\"SkullTurns\" .. name)) end",
            "    for name, statue in pairs(STATUES) do",
            "        if var(\"StatueCasting\" .. name) == 1 then statueCasting(name) else evt.PlayDecorationClip(statue.cog, \"fidget2\") end",
            "    end",
            f"    if var(\"WinWheel\") == 2 then evt.PlayDecorationClip({cinema.COG_WINMAN}, \"down\", \"end\") end",
            "    for name, faces in pairs(PIECES) do",
            f"        if var(\"Destroyed\" .. name) == 1 then for _, f in ipairs(faces) do evt.SetFacetBit(-f, {INVISIBLE_FACE | UNTOUCHABLE_FACE}, true) end end",
            "    end",
            f"    local njam = MM9.hasKey({KEY_NJAM_QUEST}) == 1",
            "    for marker, _ in pairs(NJAM_MARKERS) do end",
            "    for _, t in ipairs({\"TriggerNjam0\", \"TriggerNjam1\", \"TriggerNjam2\", \"TriggerNjam3\", \"TriggerNjam4\", "
            "\"TriggerNjam6\", \"TriggerNjam7\"}) do set(\"Trig\" .. t, njam and 1 or 2) end",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "end",
        ]
        script.add(lines, (1, "Map load", None), (T_POLL, "Poll", None, "timer"),
                   (EV_LEVER17, "Lever", "Lever"), (EV_LIFT_LEVER, "Lever", "Lever"), (EV_LIFT_LEVER0, "Lever", "Lever"),
                   (EV_HIDDEN_BUTTON, "Button", "Button"), (EV_TOMB_GATE, "Gate", "Gate"),
                   (EV_STAIR_GATE0, "Gate", "Gate"), (EV_FOYER_DOOR, "Door", "Door"),
                   (EV_WINMAN, "Switch", "Switch"), (EV_GENIE, "Genie lamp", "Lamp"),
                   (EV_WINMAN + 9, "Taunt", None))
        script.hooks += [f'RegisterMonsterKilledHook({KILL_HOOK}, "Death triggers", handlers[{KILL_HOOK}])']
        # MM9's cutscenes (cinematics_1000t.py): the map Lua's block, and 1000terrors.cinematics.yml with its sounds
        scenes = cinema.scenes(self.actor, self.points, hall_of_gods_arrival())
        cinema.install(scenes)
        return script.finish(on_load=[1]) + cinema.lua_block(scenes)

    def scene(self, build, scene: dict) -> None:
        # MM9's WeightedLift moves what is in its way (a Lift's physics): rising under a party that swims over it, it
        # lifts the party onto its top (MM9's way out of the pool); the plain linear rule (no ReopenOnContact) holds
        lifts = {m["door_id"]: m for m in build.movers if str(m["group"]).startswith("WeightedLift")}
        for door in scene["initial_state"]["doors"]:
            if door["door_id"] in lifts:
                door.setdefault("mover", {"easing": "linear", "carry": False})["bodies"] = "push"
        # MM9 places two monsters on the stones (Eye2 on WeightedLift6, Orbus8 on the dais' WeightedLift15):
        # the floor snap reads static floors only and dropped them to the pool's bed; they stand on the stone's top
        for actor in scene["initial_state"]["actors"]:
            p = actor["position"]
            for m in lifts.values():
                (x0, y0, _), (x1, y1, z1) = m["box"]
                if x0 <= p["x"] <= x1 and y0 <= p["y"] <= y1 and p["z"] < z1 - 8:
                    p["z"] = int(round(z1))
                    build.stats["actors_on_weighted_lifts"] = build.stats.get("actors_on_weighted_lifts", 0) + 1
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], np.int64)

        def key(points) -> tuple:
            return tuple(sorted(tuple(int(round(c)) for c in p) for p in points))

        ids = {}
        for f in blv["faces"]:
            ids.setdefault(key(vertices[np.asarray(f["vertex_indices"])]), []).append(f)
        details = [f for ring in self.detail_rings for f in ids.get(key(ring), [])]
        scene["initial_state"].setdefault("face_attribute_overrides", []).extend(
            {"face_index": f["index"], "legacy_attributes": int(f["attributes"]) & ~INVISIBLE_FACE} for f in details)
        build.stats["detail_faces_restored"] = len(details)
        # MM9's translucent non-solid brushes: the candle orbs (WorldObject Alpha 0.4, water123.spr) and the webs (0.7)
        alias = {e["source_texture"].split("\\")[-1].lower(): e["alias"] for e in build.source.aliases.values()
                 if "alias" in e}
        for texture, opacity in (("water123.spr", 0.4), ("web3.dtx", 0.7)):
            name = alias.get(texture)
            faces = sorted(f["index"] for f in blv["faces"] if name and f["texture_name"] == name and not f["is_portal"])
            if faces:
                scene.setdefault("translucent_faces", []).append(
                    {"faces": faces, "opacity": opacity, "tint": [1.0, 1.0, 1.0], "two_sided": True})
            build.stats[f"translucent_{texture}"] = len(faces)
        # The demon statues SpawnTrigger0-3 destroy (DestructableBrush SpawnPiece0-3): their compiled faces by box, hidden
        # by the map Lua (evt.SetFacetBit with the face index) when MM9 destroys them.
        self.piece_faces = {}
        for name in ("SpawnPiece0", "SpawnPiece1", "SpawnPiece2", "SpawnPiece3"):
            native = build.project.native(np.array(build.source.models[name].points, float))
            low, high = native.min(0) - 2, native.max(0) + 2
            self.piece_faces[name] = [f["index"] for f in blv["faces"] if not f["is_portal"] and f["index"] > 0
                                      and np.all((vertices[np.asarray(f["vertex_indices"])] >= low) & (vertices[np.asarray(f["vertex_indices"])] <= high))]
        build.stats["spawn_piece_faces"] = sum(len(v) for v in self.piece_faces.values())
        # The pawns that can queen (queening_pawns): their compiled faces by box, hidden when the pawn becomes a Terror.
        self.pawn_faces = {}
        for name in queening_pawns(build.source):
            native = build.project.native(np.array(build.source.models[name].points, float))
            low, high = native.min(0) - 2, native.max(0) + 2
            self.pawn_faces[name] = [f["index"] for f in blv["faces"] if not f["is_portal"] and f["index"] > 0
                                     and np.all((vertices[np.asarray(f["vertex_indices"])] >= low) & (vertices[np.asarray(f["vertex_indices"])] <= high))]
        build.stats["queening_pawn_faces"] = {name: len(faces) for name, faces in self.pawn_faces.items()}

    def report(self, build) -> dict:
        return {"scripted": {"actors": self.actor, "boxes": self.boxes, "points": self.points,
                             "chess_squares": self.chess_squares, "pieces": self.piece_faces,
                             "death": {str(i): list(v) for i, v in sorted(self.death.items())}}}


def spawned_greater_on_death(o: dict) -> bool:
    """Whether what the object spawns runs LesserDemon.scr with p0 1: a Spawner whose DefaultSpawn is "LesserDemon
    ScriptParams 1" (Spawner8, Spawner13), or a SpawnLoc.scr of LesserDemon (SpawnMgr.scr spawns its LESSERDEMON,
    "LesserDemon ScriptParams 1", for that class)."""
    p = o["properties"]
    script_name = str(p.get("ScriptName") or "").lower().replace("scripts\\", "")
    if o["class"] == "Spawner":
        words = str(p.get("DefaultSpawn") or "").replace(";", " ").split()
        return words[:1] == ["LesserDemon"] and any(words[k:k + 2] == ["ScriptParams", "1"] for k in range(len(words)))
    return script_name == "spawnloc.scr" and str(p.get("ScriptParams") or "").split()[:1] == ["LesserDemon"]


def chess_pieces(source) -> list:
    """The pieces (ChessPawn/Knight/Bishop.scr): (DAT name, kind, x, z) of each one's square (ScriptParams p3, k = 8 z
    + x)."""
    out = []
    for o in source.objects:
        script_name = str(o["properties"].get("ScriptName") or "").lower()
        kind = next((k for k in ("pawn", "knight", "bishop") if f"chess{k}" in script_name), None)
        if kind is not None:
            location = int(str(o["properties"]["ScriptParams"]).split()[3])
            out.append((o["name"], kind, location % 8, location // 8))
    return out


def piece_cells(kind: str, x: int, z: int) -> list:
    """The squares a piece attacks from (x, z) (its CheckPath)."""
    if kind == "pawn":
        cells = [(x - 1, z + 1), (x + 1, z + 1)]
    elif kind == "knight":
        cells = [(x + dx, z + dz) for dx, dz in ((1, 2), (-1, 2), (1, -2), (-1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1))]
    else:
        cells = [(x + d * sx, z + d * sz) for d in range(1, 8) for sx in (1, -1) for sz in (1, -1)]
    return [8 * cz + cx for cx, cz in cells if 0 <= cx < 8 and 0 <= cz < 8]


def chess_attackers(source) -> dict:
    """Square k -> the pieces that attack it from their DAT squares."""
    out = {}
    for name, kind, x, z in chess_pieces(source):
        for k in piece_cells(kind, x, z):
            out.setdefault(k, []).append(name)
    return out


def queening_pawns(source) -> dict:
    """The pawns whose attack from their DAT square ends on the last rank (ChessBase.inc :PawnToQueen): name -> those
    squares."""
    out = {}
    for name, kind, x, z in chess_pieces(source):
        squares = [k for k in piece_cells(kind, x, z) if k // 8 == CHESS_LAST_RANK] if kind == "pawn" else []
        if squares:
            out[name] = squares
    return out


def name_key(name: str) -> str:
    return name if name.isidentifier() else f"[{lua_str(name)}]"


def lua_only() -> int:
    """Regenerate and install only the map Lua from the last build's state (work/lua_state.pkl): fast iteration on the
    scripts. The BLV, scene and doors stay as built."""
    import pickle
    from types import SimpleNamespace
    from dungeon.source import Project, Source
    import review_root
    state = pickle.loads((PROJECT / "work/lua_state.pkl").read_bytes())
    hooks = ThousandTerrors()
    hooks.__dict__.update(state["hooks"])
    project = Project.load(PROJECT)
    build = SimpleNamespace(project=project, source=Source(project), movers=state["movers"], hooks=hooks,
                            content=SimpleNamespace(report=state["report"]), runtime=project.work / "runtime",
                            lua_only=True)
    text = hooks.map_script(build)
    # the last build's pack growth copies (work/density.json) in ACTOR, as the build added them
    grown = json.loads((project.work / "density.json").read_text()) if (project.work / "density.json").exists() else {}
    text = dungeon_density.add_to_directories(text, hooks.density_lua_directories,
                                              [c for pack in grown.get("packs", []) for c in pack["copies"]])
    (build.runtime / f"{project.stem}.lua").write_text(text)
    review_root.install_file(Path("worlds/mm9/events/maps") / f"{project.stem}.lua", build.runtime / f"{project.stem}.lua")
    print("installed", project.stem + ".lua", len(text.splitlines()), "lines")
    return 0


if __name__ == "__main__":
    if "--lua" in sys.argv:
        sys.exit(lua_only())
    sys.exit(dungeon.main(PROJECT, ThousandTerrors()))
