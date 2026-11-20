#!/usr/bin/env python3
"""
Thronheim City, MM9 rework: MM9's THRONHEIMCITY.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_thronheimcity/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_thronheimcity/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the glass and the city settings (roof line, cuts); this file adds the city's
population (props.json from ../../props/mm9_thronheimcity_claude, the townsfolk with their RUDE dialogues, the Honk
missionaries, the guards, Kira and Yrsa, the Desert Terror in its cell) and the scripted objects as native Lua
(citylua.py), each citing its .scr (README.md, "Scripted objects"; behaviour spec: work/scr_spec.md).
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
from city.hooks import CityHooks  # noqa: E402
from dungeon.bodies import mm9_bodies  # noqa: E402
from dungeon.geometry import clip  # noqa: E402
from dungeon.source import ROOT  # noqa: E402
from mm9_ai_placement import townsperson_walks  # noqa: E402
from mm9_monster_bodies import native_body  # noqa: E402
from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402
import council  # noqa: E402
import rude_props  # noqa: E402
import cutscenes  # noqa: E402
import review_root  # noqa: E402

PROPS = PROJECT / "props.json"
# Sven's council model (Sven_ARG.ABC) carries his chair; the HD Sven sits on one placed here: the other Jarls' chairs
# stand 35-41 units behind them along their row (Tryggva's Prop15: -41, 0), so the same offset from SvenProp, his yaw.
SVEN_CHAIR = {"from": "Prop15", "name": "SvenChair", "offset": (-40.0, 0.0)}
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/thronheimcity.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"

FALLBACK_ROW = 367                  # stand-in peasant row (Peasant Human2 MaleA) for objects the old import left out
GUARD_CLASS, GUARD_ROW = "PoorTownGuard1", 9107       # MM9 107 Town Guard (L20)
BADASS_CLASS = "DesertTerror"
PEACEFUL_ALLY = 118                 # a peasant family's monster type: lends peaceful relations (Hall of the Gods)
# Dialogue actors the DAT gives no NPCNbr/DoRude (only their scripts open the RUDE): Honkies.scr's params, DoRude.scr's
# 278, ARG_Yrsa.scr's RUDE 1.
SCRIPT_RUDE = {"CommonerHumanMaleA1": 271, "CommonerHumanFemaleA0": 279, "CommonerHumanFemaleA1": 272,
               "Lt. Dain": 278, "YrsatheTroll0": 1}
HONKS = ("CommonerHumanMaleA1", "CommonerHumanFemaleA0", "CommonerHumanFemaleA1")
# Honkies.scr :Init: AttachProp HonkPamphlet.ABC on the Honk's `pamphlet` socket (scene held_items); its :Main runs
# BaseWanderInit, so each walks the DAT's wander (WanderON) like a townsperson.
HONK_PAMPHLET = {"model": "worlds/mm9/models/mm9_item_honkpamphlet.glb", "node": "Socket_pamphlet"}
STAGE_TOP_LT = 900                  # the Argument cinema's stage under the city (not built): Kira's stage copy stands there
EXTRA_GUARD_AT = "GuardSpawn1"      # Thronheimcity_BadAss.scr :GetExtraGuard spawns one guard here 6 s into the breakout
FLOOR_SPLIT_AREA_LT2 = 20000        # floors at least this big are cut at the walls standing on them (split_floors_at_walls)
WALL_MIN_HEIGHT_LT = 48
WALL_FOOT_LT = 16
(GROUP_TOWNSFOLK, GROUP_GUARDS, GROUP_BADASS, GROUP_EXTRA_GUARD, GROUP_HONKS) = 1, 2, 3, 4, 5


def float_property(value) -> float:
    """A float MM9 stores in an int property (NPCNbr 1131479040 = 241.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


class ThronheimCity(CityHooks):
    generator = "mm9r_thronheimcity"
    mover_events = citylua.MOVER_EVENTS

    # --- geometry ---------------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        return self.split_floors_at_walls(super().edit_polygons(build, polygons), build)

    def split_floors_at_walls(self, polygons: list, build) -> list:
        """MM9 lays one sidewalk or ground polygon under a house front and on into the house: the shared converter
        splits a face only where a second room holds 15 % of its samples, so the strip outside the wall went to the
        house's sector and the street drew sky there (review v02, s12_centre_west_lane: a pale strip along the inn's
        front). Each large flat floor is cut at the plane of every wall (48 LT or taller, any horizontal direction)
        that stands on it (its foot at most 16 LT over the floor, or below it) and crosses it; a cut splits only the pieces the wall's length reaches (Klusos House's
        split_at_walls, for floors). The pieces under the walls see no air and are dropped; the rest lie in one room."""
        walls = []
        for p in polygons:
            n = p.normal
            if p.role == "static" and abs(n[1]) < 0.01 and np.ptp(p.points[:, 1]) >= WALL_MIN_HEIGHT_LT:
                horizontal = np.array([n[0], 0.0, n[2]]) / np.hypot(n[0], n[2])
                along = np.array([-horizontal[2], 0.0, horizontal[0]])
                span = p.points @ along
                walls.append((horizontal, float(horizontal @ p.points[0]), float(p.points[:, 1].min()),
                              along, float(span.min()), float(span.max()), p.points.min(0), p.points.max(0)))
        lows = np.array([w[6] for w in walls])
        highs = np.array([w[7] for w in walls])
        # a wall stands on the floor when it reaches from at most WALL_FOOT_LT over the floor (a house's wall often
        # starts at its own floor, a few LT over the street's) to at least WALL_MIN_HEIGHT_LT over it
        out, splits = [], 0
        for polygon in polygons:
            if polygon.role != "static" or polygon.normal[1] < 0.999 or polygon.area < FLOOR_SPLIT_AREA_LT2:
                out.append(polygon)
                continue
            low, high = polygon.points.min(0), polygon.points.max(0)
            height = float(polygon.points[0, 1])
            near = np.nonzero((lows[:, 0] < high[0] - 2) & (highs[:, 0] > low[0] + 2) & (lows[:, 2] < high[2] - 2)
                              & (highs[:, 2] > low[2] + 2) & (lows[:, 1] <= height + WALL_FOOT_LT)
                            & (highs[:, 1] >= height + WALL_MIN_HEIGHT_LT))[0]
            planes = sorted({(tuple(np.round(walls[i][0], 4)), round(walls[i][1], 1), i) for i in near},
                            key=lambda t: t[:2])
            pieces, seen = [polygon], set()
            for normal_key, distance, i in planes:
                if (normal_key, distance) in seen:
                    continue
                seen.add((normal_key, distance))
                normal, _, _, along, a0, a1, _, _ = walls[i]
                cut = []
                for piece in pieces:
                    span = piece.points @ along
                    if a0 < span.max() - 4 and a1 > span.min() + 4:
                        front, back = clip(piece, normal, distance, f"floorwall_{normal_key}_{distance}")
                        cut += [part for part in (front, back) if part is not None]
                    else:
                        cut.append(piece)
                pieces = cut
            splits += len(pieces) - 1
            out += pieces
        build.stats["floor_splits_at_walls"] = splits
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        if PROPS.exists():
            # the council's posed Jarls are actors (actors(), rude_props.py); Sven's chair is added (SVEN_CHAIR)
            entries = json.loads(PROPS.read_text())
            sven = next(e for e in entries if e["source_name"] == "SvenProp")
            chair = dict(next(e for e in entries if e["source_name"] == SVEN_CHAIR["from"]))
            chair.update(source_name=SVEN_CHAIR["name"], source_object=None, x=sven["x"] + SVEN_CHAIR["offset"][0],
                         y=sven["y"] + SVEN_CHAIR["offset"][1], yaw_degrees=sven["yaw_degrees"])
            props = build.project.work / "props_council.json"
            props.write_text(json.dumps(entries + [chair], indent=1) + "\n")
            build.content.props(props, events=citylua.prop_events(build), cogs=citylua.prop_cogs(build),
                                skip={name for name, _ in citylua.posed_people(build)})
        else:
            print("note: props.json is missing; no decorations or chests placed")
        self.points = citylua.marker_points(build)

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """Every person of the DAT (the cinema's stage actors excepted: overrides.yml): the old import's NPC records
        (row, name, RUDE dialogue) where it placed them, MM9's body (the object's model's initial dims x its Scale).
        Townsfolk, shopkeepers, Kira and the guards are friendly and stand where MM9 placed them; the Honk
        missionaries keep MM9's Honk row (friendly, a peasant's relations); Yrsa starts hidden (she appears after the
        war council); the Desert Terror stands in its cell, friendly until the breakout makes its group hostile; one
        extra guard waits hidden at GuardSpawn1 for the breakout."""
        content, source = build.content, build.source
        old = {a["mm9_source_object_index"]: a for a in
               yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]
               if "mm9_source_object_index" in a}
        names = read_mm9_npc_names(NPC_NAMES)
        bodies = mm9_bodies()
        out, self.actor, self.objects, self.rude = [], {}, {}, {}
        self.sleeping_guards = []
        for o in source.objects:
            if o["class"] not in build.project.monster_classes or o["properties"]["Pos"][1] < STAGE_TOP_LT:
                continue
            name, p = o["name"], o["properties"]
            record = old.get(o["index"])
            if record is not None:
                rude = int(record.get("mm9_rude_id") or 0)
                base = {key: record[key] for key in ("name", "attributes", "hp", "hostility_type", "monster_info_id",
                                                     "monster_id", "radius", "height", "move_speed")}
            else:
                rude = mm9_npc_rude_id({key: p.get(key) for key in ("DoRude", "ScriptName", "GreetingSound",
                                                                      "NPCNbr")})
                base = {"name": names.get(rude, name), "attributes": 0, "hp": 20, "hostility_type": 0,
                        "monster_info_id": FALLBACK_ROW, "monster_id": FALLBACK_ROW, "radius": 43, "height": 120,
                        "move_speed": 0}
            rude = SCRIPT_RUDE.get(name, rude)
            if rude and name in SCRIPT_RUDE:
                base["name"] = names.get(rude, base["name"])
            group, hidden = GROUP_TOWNSFOLK, False
            if o["class"] == GUARD_CLASS:
                base["monster_id"] = base["monster_info_id"] = GUARD_ROW
                group = GROUP_GUARDS
            elif o["class"] == BADASS_CLASS:
                group = GROUP_BADASS
            elif name in HONKS:
                group = GROUP_HONKS
            if name == "YrsatheTroll0":
                hidden = True                      # DAT Visible 0: ARG_Yrsa.scr shows her after the war council
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                height, radius = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
                base["height"], base["radius"] = height, radius
            actor = content.actor(o, base, sector_of_room, group=group, friendly=True, hidden=hidden,
                                  floor_query_lt=p["Pos"][1] + 24)
            if o["class"] == BADASS_CLASS:
                # Friendly (no hostile or aggressor bit) but with the row's engagement type, so the breakout's
                # evt.SetMonGroupBit(Hostile) makes it fight (Dook's Castle's guards).
                actor["hostility_type"] = base["hostility_type"]
            else:
                actor["ally"] = PEACEFUL_ALLY      # MM9 rows of monster families (Honk, Swordsman...) talk, not fight
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = not townsperson_walks(actor.get("mm9_ai") or {})
            if name in HONKS:
                actor["held_items"] = [dict(HONK_PAMPHLET)]
                actor["immobile"] = (actor.get("mm9_ai") or {}).get("wander") not in ("aimless", "path")
            if o["class"] == GUARD_CLASS and str(p.get("ScriptParams") or "").split()[:1] != ["GetBadAss"]:
                # Thronheimcity_Guard.scr :Main without GetBadAss: DisableWandering, GotoSleep (LoopAnim Sleep, no
                # OnFoundTarget): asleep at its post until :OpenEyes (the breakout's GetExtraGuard, Guard1 only: the
                # map's evt.WakeActor) or a hit (PoliceMan.inc OnDamage takes the attacker).
                ai = actor.setdefault("mm9_ai", {})
                for key in ("wander", "path", "path_random", "path_stops", "wander_leash", "wander_wait",
                            "wander_time"):
                    ai.pop(key, None)
                ai["dormant"] = {"until": "trigger", "pose": "sleep"}
                actor["dormant"] = True
                actor["immobile"] = False
                self.sleeping_guards.append(name)
            self.actor[name], self.objects[name], self.rude[name] = actor["actor_index"], o["index"], rude
            out.append(actor)
        # The breakout's extra guard (GuardSpawn1's DefaultSpawn, PoorTownGuard1 "GetBadAss"): hidden until then.
        spawn = source.by_name[EXTRA_GUARD_AT.lower()]
        guard_base = {"name": "Town Guard", "attributes": 0, "hp": 100, "hostility_type": 0,
                      "monster_info_id": GUARD_ROW, "monster_id": GUARD_ROW, "radius": 38, "height": 184,
                      "move_speed": 0}
        guard_object = {"name": "ExtraGuard", "class": GUARD_CLASS, "index": spawn["index"],
                        "properties": dict(spawn["properties"])}
        actor = content.actor(guard_object, guard_base, sector_of_room, group=GROUP_EXTRA_GUARD, friendly=True,
                              hidden=True, floor_query_lt=spawn["properties"]["Pos"][1] + 24)
        actor["ally"] = PEACEFUL_ALLY
        self.actor["ExtraGuard"] = actor["actor_index"]
        out.append(actor)
        # The council's six Jarls (PropAnim "Sit" RUDEProps) as actors on their HD models, seated where MM9 draws
        # them (../mm9r_common/rude_props.py); councilProps() in the map Lua shows them, the load starts their pose.
        self.posed = {}
        self.council_feet = {}
        roles = {prop: role for role, prop in council.POSED_JARLS.items()}
        for name, entry in citylua.posed_people(build):
            o = source.objects[entry["source_object"]]
            assert o["index"] == entry["source_object"], name
            actor = rude_props.actor(content, o, entry, sector_of_room, names, GROUP_TOWNSFOLK, bodies)
            actor["ally"] = PEACEFUL_ALLY
            self.actor[name], self.objects[name], self.rude[name] = (actor["actor_index"], o["index"],
                                                                    actor.get("mm9_rude_id", 0))
            self.posed[name] = rude_props.load_lines(actor)
            if name in roles:
                self.council_feet[roles[name]] = [actor["position"][k] for k in ("x", "y", "z")]
            out.append(rude_props.finish(actor))
        # Kira's stage actor (council.py): moved from MM9's stage under the city into Kira's hall, hidden until the
        # council_argument cinematic; a plain immobile friendly actor of her MM9 row (no AI profile: she only acts).
        for role, stage_object, row, title in council.stage_actor_objects(source.by_name):
            if role in council.POSED_JARLS:
                continue
            base = {"name": title, "attributes": 0, "hp": 20, "hostility_type": 0, "monster_info_id": 9000 + row,
                    "monster_id": 9000 + row, "radius": 31, "height": 174, "move_speed": 0}
            actor = content.actor(stage_object, base, sector_of_room, group=GROUP_TOWNSFOLK, friendly=True,
                                  hidden=True, floor_query_lt=stage_object["properties"]["Pos"][1] + 24)
            for key in ("mm9_ai", "dormant", "mm9_civilian"):
                actor.pop(key, None)
            actor["ally"] = PEACEFUL_ALLY
            actor["immobile"] = True
            actor["mm9_source_object_index"] = stage_object["index"]
            self.actor[stage_object["name"]] = actor["actor_index"]
            self.council_feet[role] = [actor["position"][k] for k in ("x", "y", "z")]
            out.append(actor)
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        posed = {role: self.posed[prop] for role, prop in council.POSED_JARLS.items()}
        self.scenes = council.scenes(citylua.council_actors(self), self.council_feet, citylua.prop_cogs(build), posed)
        return citylua.map_script(self, build) + cutscenes.lua_block(self.scenes)

    def report(self, build) -> dict:
        return dict(super().report(build), scripted={"actors": self.actor, "objects": self.objects,
                                                     "rude": self.rude})


if __name__ == "__main__":
    hooks = ThronheimCity()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        # The war council's cinematic (council.py) beside the map, and the sounds it and Yrsa's appearance need
        print(f"cinematics installed: {cutscenes.install(council.STEM, hooks.scenes)}")
        print(f"council sounds installed: {council.install_sounds(review_root) or 'none'}")
    sys.exit(code)
