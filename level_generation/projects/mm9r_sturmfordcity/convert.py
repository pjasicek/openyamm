#!/usr/bin/env python3
"""
Sturmford City, MM9 rework: MM9's STURMFORDCITY.dat as a native BLV open to the sky, on the shared dungeon converter
(../mm9r_common/dungeon) and its city extension (../mm9r_common/city, ../mm9r_common/CITY_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_sturmfordcity/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_sturmfordcity/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules, the glass and the city settings (roof line, hand cuts); this file adds the
city's population (props.json from ../../props/mm9_sturmfordcity_claude, the well's water, the NPCs with their RUDE
dialogues, the guard and the animals) and the scripted objects as native Lua (citylua.py), each citing its .scr
(README.md, "Scripted objects").
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np
import yaml

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(PROJECT))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from city import structure  # noqa: E402
from city.hooks import CityHooks  # noqa: E402
from dungeon.bodies import mm9_bodies  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from mm9_ai_placement import townsperson_walks  # noqa: E402
from mm9_monster_bodies import native_body  # noqa: E402
from transcode_mm9_dat_to_odm import mm9_npc_rude_id, read_mm9_npc_names  # noqa: E402

import citylua  # noqa: E402
import rude_props  # noqa: E402

PROPS = PROJECT / "props.json"
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/sturmfordcity.scene.yml"
NPC_NAMES = ROOT / "mm9/extracted/RUDE/RUDE/NPCNAME.rude"
WELL_MODEL = "Wellwater"
WELL_TEXTURE = "sprites\\water\\water125.spr"
WELL_LADDER = "Ladder7"

# NPC rows for objects the old import did not place (the RUDEProps: peasant models in a pose, MM9's talking props):
# the stand-in peasant row 367 (Peasant Human2 MaleA) as Drangheim Prison's prisoners. Animals: MM9's own cat row,
# the old import's dog row (MM9 has no dog row).
RUDEPROP_ROW = 367
ANIMAL_ROWS = {"Cat": 9294, "Dog": 469}
GUARD_CLASS = "PoorTownGuard1"
GUARD_ROW = 9107                    # MM9 107 Town Guard (L20): MM9's PoorTownGuard1 (Sturmguard.scr)
GUARD_RUDE = 425
# The pieces of MM9's prop models our HD bodies lack, as held items (scene held_items): Ercc's cup (cup01 of MM9's
# Props/Ercc.ABC, which our Ercc, drawn with the townsman body, lacks; the townsman's Socket_Cup is cup01's frame).
# Tryggva (RUDEProp0, PeasantMS2.ABC) has no cup piece and TryggvaSpeech.scr attaches none.
POSED_ITEMS = {"RUDEProp1": [{"model": "worlds/mm9/models/mm9_item_erccup.glb", "node": "Socket_Cup"}]}
GROUP_TOWNSFOLK, GROUP_GUARDS, GROUP_ANIMALS = 1, 2, 3
# Chedian's dimensional travel pedestal (not MM9's; the user, 2026-11-09): MAW's teleporter, the ped06 pedestal under
# the dec57 orb 160 units up (engine/rulesets/maw/maps/oute3_zz_maw.scene.yml), on the lawn east of the south sewer
# hatch, native units. A Dimension Door to Chedian lands the party 224 units east of it, facing it
# (game/gameplay/GameplayPartyOverlayInputController.cpp, resolveDimensionDoorLanding).
PEDESTAL = (1529, 54, 19702)
PEDESTAL_ORB_LIFT = 160


def float_property(value) -> float:
    """A float MM9 stores in an int property (RUDENPCId 1113849856 = 57.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value or 0)


class SturmfordCity(CityHooks):
    generator = "mm9r_sturmfordcity"
    own_water_surfaces = (WELL_MODEL,)      # well() builds its surface (no shared drawn_surfaces face)
    mover_events = citylua.MOVER_EVENTS

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content = build.content
        if PROPS.exists():
            content.props(PROPS, events=citylua.prop_events(build), cogs=citylua.prop_cogs(build),
                          skip={name for name, _ in citylua.posed_people(build)})
        else:
            print("note: props.json is missing; no decorations or chests placed")
        self.well(build)
        self.pedestal(build)
        self.points = citylua.marker_points(build)

    def pedestal(self, build) -> None:
        """The dimensional travel pedestal and its orb: a click on either opens the dimensional travel (citylua.py)."""
        x, y, z = PEDESTAL
        event = citylua.EV_DIMENSIONAL_TRAVEL
        build.content.entity("DimensionalTravelPedestal", "ped06", (x, y, z), 0, secondary=event)
        build.content.entity("DimensionalTravelOrb", "dec57", (x, y, z + PEDESTAL_ORB_LIFT), 0, secondary=event)

    def well(self, build) -> None:
        """The well's water: the top face of MM9's Wellwater volume (BlueWater, ShowSurface, SurfaceAlpha 0.8,
        water125.spr) as an untouchable face, drawn by the liquid shader (../mm9r_common/liquids.py)."""
        project, package = build.project, build.package
        points = np.array(build.source.models[WELL_MODEL].points, float)
        top = points[:, 1].max()
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        ring = np.array([[x0, top, z0], [x0, top, z1], [x1, top, z1], [x1, top, z0]])
        native = np.round(project.native(ring)).astype(np.int64)
        if np.cross(native[1] - native[0], native[2] - native[0])[2] < 0:
            native, ring = native[::-1], ring[::-1]
        key = package.material(WELL_TEXTURE)[0]
        node = f"TRIGGER_water_{WELL_MODEL}"
        package.nodes[node].append((native, ring[:, [0, 2]] - ring[:, [0, 2]].min(0), key))
        room = build.content.owner(np.array([(x0 + x1) / 2, top - 4, (z0 + z1) / 2]))
        package.room_nodes[room].append(node)
        package.metadata["surfaces"].append({"id": WELL_MODEL, "source_node": node, "flags": ["untouchable"]})
        build.content.report["water"] = {"model": WELL_MODEL, "room": room, "z": int(native[0][2])}

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        """Every person and animal of the DAT: the old import's NPC records (row, name, RUDE dialogue) where it placed
        them, MM9's body (the object's model's initial dims x its Scale, ABC extents), RUDE ids from the object
        (NPCNbr, a NPC<n>.scr, the greeting; RUDEProps: RUDENPCId). All friendly; the animals and the townsfolk on
        MM9's own wander without a script of their own (mm9_ai_placement.townsperson_walks) walk, every other
        townsperson stands where MM9 placed it."""
        content, source = build.content, build.source
        old = {a["mm9_source_object_index"]: a for a in
               yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]}
        names = read_mm9_npc_names(NPC_NAMES)
        bodies = mm9_bodies()
        out, self.actor, self.objects, self.rude = [], {}, {}, {}
        for o in source.objects:
            if o["class"] not in build.project.monster_classes:
                continue
            name, p = o["name"], o["properties"]
            record = old.get(o["index"])
            if o["class"] == "RUDEProp":
                rude = int(round(float_property(p.get("RUDENPCId"))))
                base = {"name": names.get(rude, name), "attributes": 0, "hp": 20, "hostility_type": 0,
                        "monster_info_id": RUDEPROP_ROW, "monster_id": RUDEPROP_ROW, "radius": 43, "height": 120,
                        "move_speed": 0}
            elif record is not None:
                rude = int(record.get("mm9_rude_id") or 0)
                base = {key: record[key] for key in ("name", "attributes", "hp", "hostility_type", "monster_info_id",
                                                     "monster_id", "radius", "height", "move_speed")}
            else:
                rude = mm9_npc_rude_id({key: p.get(key) for key in ("DoRude", "ScriptName", "GreetingSound",
                                                                      "NPCNbr")})
                base = {"name": names.get(rude, name), "attributes": 0, "hp": 20, "hostility_type": 0,
                        "monster_info_id": RUDEPROP_ROW, "monster_id": RUDEPROP_ROW, "radius": 43, "height": 120,
                        "move_speed": 0}
            group = GROUP_TOWNSFOLK
            if o["class"] in ANIMAL_ROWS:
                base["monster_id"] = base["monster_info_id"] = ANIMAL_ROWS[o["class"]]
                group = GROUP_ANIMALS
            elif o["class"] == GUARD_CLASS:
                base["monster_id"] = base["monster_info_id"] = GUARD_ROW
                group = GROUP_GUARDS
                rude = GUARD_RUDE           # Sturmguard.scr :OnUse: DoRude 425 (the DAT gives him no dialogue)
            extents = bodies.model_extents(str(p.get("Filename", "")))
            if extents is not None:
                height, radius = native_body(extents[1], float(p.get("Scale", 1.0) or 1.0))
                base["height"], base["radius"] = height, radius
            actor = content.actor(o, base, sector_of_room, group=group, friendly=True,
                                  floor_query_lt=p["Pos"][1] + 24)
            actor["mm9_source_object_index"] = o["index"]
            if rude:
                actor["mm9_rude_id"] = rude
            actor["immobile"] = group != GROUP_ANIMALS and not townsperson_walks(actor.get("mm9_ai") or {})
            self.actor[name], self.objects[name], self.rude[name] = actor["actor_index"], o["index"], rude
            out.append(actor)
        # MM9's posed people (RUDEProps: the innkeeper, the drinkers, Ludwig, Bjarni, Ercc) as actors looping their
        # pose on the HD townsfolk bodies (../mm9r_common/rude_props.py); their pose and facing come from the map Lua
        self.posed = {}
        for name, entry in citylua.posed_people(build):
            o = source.objects[entry["source_object"]]
            assert o["index"] == entry["source_object"], name
            actor = rude_props.actor(content, o, entry, sector_of_room, names, GROUP_TOWNSFOLK, bodies)
            if name in POSED_ITEMS:
                actor["held_items"] = POSED_ITEMS[name]
            self.actor[name], self.objects[name], self.rude[name] = (actor["actor_index"], o["index"],
                                                                    actor.get("mm9_rude_id", 0))
            self.posed[name] = rude_props.load_lines(actor)
            out.append(rude_props.finish(actor))
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        return citylua.map_script(self, build)

    def scene(self, build, scene: dict) -> None:
        super().scene(build, scene)
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        alias = build.source.aliases[WELL_TEXTURE]["alias"].lower()
        water = sorted(f["index"] for f in blv["faces"] if str(f.get("texture_name", "")).lower() == alias)
        if water:
            scene.setdefault("translucent_faces", []).append(
                {"faces": water, "opacity": 0.8, "tint": [1.0, 1.0, 1.0], "two_sided": False})
        liquids.apply(build, scene)
        # The well's rope (Ladder7) hangs to MM9's water (7 148 LT); the bags lie on the bottom 200 LT under it (MM9:
        # the party dives). The well is swum (the shared water rule: Wellwater in the scene's water_volumes); the rope
        # reaches down to the bottom, so a party under water or at the surface takes it and climbs out
        # (scenario_well.yml).
        for ladder in scene.get("ladders", []):
            if ladder["id"] == WELL_LADDER:
                x, y, z = ladder["bottom"]
                lt = build.project.lt_from_native((x, y, z))
                floor = build.content.floor_at(lt[0], lt[2], lt[1])
                if floor is not None:
                    ladder["bottom"][2] = round(floor * SCALE - build.project.offset[2] + 1, 2)
                    build.content.report["well_ladder_bottom"] = ladder["bottom"]

    def report(self, build) -> dict:
        return dict(super().report(build), scripted={"actors": self.actor, "objects": self.objects,
                                                     "rude": self.rude})


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, SturmfordCity()))
