#!/usr/bin/env python3
"""
Training Hall, MM9 rework: MM9's TRAININGHALL.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_traininghall/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_traininghall/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules; this file adds the hall's population (props.json from
../../props/mm9_traininghall_claude, the Fire objects' flames, the perception hints, the water surfaces, the ladders)
and its scripted objects as native Lua, each citing what it reproduces (README.md, "Scripted objects"):
- the lobby chandelier (dropsequence, cracktrigger1-5, droptrigger, DestructableBrush6, Door "drop");
- the lobby ghouls (TH_LobbyGhouls.scr; TriggerLobbyGhouls, TriggerGhoulsAttack, TriggerShutDoor, the dragon door);
- the joust (d2lever, Trigger2/3, dummy2door) and the Mean Trellborg who launches it (TH_MeanTrellborg.scr,
  TriggerTrellborgOn0/1, Off0/1);
- the second horse (d4lever0, dummy4door, dummy4guide) breaking the wooden wall (upperbreak1/2, lowerbreak1/2,
  woodexplosion, Trigger8/9, PerceptionBrush1);
- the archery range (TH_TargetMgr.scr, TH_TargetRing.scr, target1-4, the 16 rings, TriggerTargetsOn/Off);
- the crate round the Blackbox (DestructableBrush0-5, DestructableBrush8, crateopentrigger, PerceptionBrush2-8);
- the hall's end (TrainingEnter.scr on TrainingTrigger: the bar DestructableBrush12, key 301, ExitTrigger0);
- the pole room's beams (Pusher0-2, MM9 Looping doors); the locked reset levers.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from dungeon import lua, water  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.rotation import grabs_at_top  # noqa: E402
from dungeon.source import LT_INVISIBLE, ROOT, SCALE  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"
PERCEPTION_TEXTURE = "sprites\\perception.spr"
PERCEPTION_COG = 300                # PerceptionBrush<k>: cog PERCEPTION_COG + k
PERCEPTION_SKILL = 29               # evt.CheckSkill's id: the party's best Perception
PERCEPTION_OPACITY = 0.5            # the brushes' Alpha here (the texture's own alpha on top)
PARTY_HEIGHT_LT = 68                # the native party (170 units) in LT, with a little room

# --- Events, cogs, timers ----------------------------------------------------------------------------------------------
EV_LOAD = 1
EV = {"d2lever": 201, "d4lever0": 202, "resetlever1": 203, "resetlever2": 204, "resetlever3": 205, "resetlever4": 206}
BOARDS = {f"DestructableBrush{k}": 210 + k for k in range(6)}          # the crate's small boards
BOARDS["DestructableBrush8"] = 216                                     # its back board (crateopentrigger)
BOARD_HINTS = {f"DestructableBrush{k}": f"PerceptionBrush{k + 2}" for k in range(6)}
BOARD_HINTS["DestructableBrush8"] = "PerceptionBrush8"
EV_BAR = 220                                                           # DestructableBrush12, the bar on the end door
EV_DROPBAR = 221                                                       # DestructableBrush6's death: the chandelier falls
WALL = ("woodexplosion", "upperbreak1", "lowerbreak1", "upperbreak2", "lowerbreak2")   # the horse's wooden wall
# The archery range (TH_TargetMgr.scr "target 1 4"; TH_TargetRing.scr "<ring index> <prize>"): ring -> (target, prize).
RINGS = {"Rank8000a": (1, 8000), "Rank4000a": (1, 4000), "Rank2000a": (1, 2000), "Rank1000a": (1, 1000),
         "Rank4000b": (2, 4000), "Rank2000b": (2, 2000), "Rank1000b": (2, 1000), "Rank0750b": (2, 750),
         "Rank2000c": (3, 2000), "Rank1000c": (3, 1000), "Rank0750c": (3, 750), "Rank0500c": (3, 500),
         "Rank1000d": (4, 1000), "Rank0750d": (4, 750), "Rank0500d": (4, 500), "Rank0250d": (4, 250)}
EV_RINGS = {name: 230 + k for k, name in enumerate(RINGS)}
KEY_WON = 7009                      # TH_TargetRing.scr: key 7009 + target index, once per target
KEY_TRAINED = 301                   # TrainingEnter.scr :OnBreak
KILL_HOOK = 96
T_POLL, T_HINTS, T_PUSH, T_JOUST, T_CRASH, T_DROP, T_DROP2, T_LEVER2, T_LEVER4, T_WHEELS2 = range(400, 410)
# MM9's Trigger volumes polled four times a second (any part of the party in the box: it grows by the party radius).
VOLUMES = ["dropsequence", "TriggerLobbyGhouls", "TriggerGhoulsAttack", "TriggerShutDoor", "TriggerTargetsOn",
           "TriggerTargetsOff", "TriggerTrellborgOn0", "TriggerTrellborgOn1", "TriggerTrellborgOff0",
           "TriggerTrellborgOff1", "TriggerOrcTraining", "TriggerOrcsStop", "TriggerGossipOn", "TriggerGossipOff",
           "TriggerBoxOrcsOn", "TriggerBoxOrcsOff"]
# The training scenes (TH_TrainingOrcs.scr, TH_TrainingOrcCommander.scr, TH_TrainingOrcObserver.scr,
# TH_OrcsGossip.scr, TH_JoustTrellborg.scr, TH_LookOutTrellborg.scr, TH_MeanTrellborg.scr): each actor's chain of
# PlayAnims and walks as a routine (scene mm9_ai.routines; devdocs/mm9_rework/monster_ai/MM9_AMBIENT_ANIMATION.md
# section 4 item 9), run while the party is in its part of the hall: the trigger volume that sends its actors Train or
# Go starts it (map var = 1, evt.SetActorRoutine), the one that sends Stop ends it. scene var -> (routine, the
# volume that starts it, the one that stops it, the DAT objects).
SCENES = {"OrcTraining": ("train", "TriggerOrcTraining", "TriggerOrcsStop",
                          ["TrainingObserver", "OrcStudent0", "OrcStudent1", "OrcStudent2", "OrcStudent3",
                           "TrainingCommander"]),
          "Gossip": ("gossip", "TriggerGossipOn", "TriggerGossipOff", ["OrcGossipLead", "OrcGossipFollow"]),
          "BoxOrcs": ("train", "TriggerBoxOrcsOn", "TriggerBoxOrcsOff", ["BoxOrc0", "BoxOrc1"]),
          "Jousting": ("joust", None, None, ["LookOutTrellborg", "WitnessTrellborg", "JoustVictimTrellborg"])}
# TH_TrainingOrcs.scr :ParadiddleStart .. :Left2: Taunt, then the drill R L R R L R L L.
DRILL = ["Taunt", "HAttack1", "HAttack2", "HAttack1", "HAttack1", "HAttack2", "HAttack1", "HAttack2", "HAttack2"]
COMMANDS = ["Stand", "Fidget2", "Stand", "Taunt"]           # TH_TrainingOrcCommander.scr :StartTraining .. :CommandTwo
OBSERVER_WAIT = 2.0                 # TH_TrainingOrcObserver.scr / TH_LookOutTrellborg.scr :Relax: Wait 0, 2
MEAN_CLIPS = ["Stand", "Fidget3", "Fidget1", "Taunt"]       # TH_MeanTrellborg.scr :AnimationA .. :AnimationD
HOLD = [3600.0, 3600.0]             # a routine's last wait: it stands until the map script switches it
# dropsequence (50 x 4 x 50 at 544 LT) is touched by MM9's party standing on the chandelier (top 464); the native
# party (66 LT) does not reach 540: its box reaches down to the chandelier's top; so does TriggerLobbyGhouls' (514-614 LT
# on the chain over it).
VOLUME_LOW_LT = {"dropsequence": 464, "TriggerLobbyGhouls": 464}
# ... and both cover the whole wheel (radius 144 LT): the native party lands anywhere on it, MM9's falls down the chain.
VOLUME_HALF_XZ_LT = {"dropsequence": 144, "TriggerLobbyGhouls": 144}
GHOULS = {"GhoulInSauna0": "Ghoul1Marker4", "GhoulInSauna1": "Ghoul1Marker3"}   # TH_LobbyGhouls.scr: the last marker
WATER_POLES_LT = 202.0              # BlueWater0's surface (the pole room) is 200 LT: 2 LT up, off the voxel centres (a face
#                                     on a voxel centre reads as having no air in front and is dropped)
WATER_POOL_LT = -2.0                # BlueWater1's surface (the lobby pool)
WATER_TILE = 64.0
# The Fire objects (no model in MM9: a particle fire, FireScale 1, on the hall's fire bowls and stands): the Anskram
# gate fire's flames without a light (their MM9 Light objects light them), at a third of its size.
FIRE_DECORATION = "mm9_gatefire_x33"
# The pole room (Ladder4-14): the iron poles (WorldObject8-18, 4 x 4 LT) climbed from any side; each strip ends a
# party height under the beam or platform it hangs from, whose top is where a climber steps off (MM9's LadderBlocker
# caps). pole -> (WorldObject, exit LT point).
POLES = {"Ladder4": ("WorldObject8", (-120, 1345, 1256)), "Ladder5": ("WorldObject9", (232, 1345, 870)),
         "Ladder6": ("WorldObject10", (8, 1065, 760)), "Ladder7": ("WorldObject11", (8, 1081, 1048)),
         "Ladder8": ("WorldObject12", (-190, 849, 1016)), "Ladder9": ("WorldObject13", (136, 737, 1144)),
         "Ladder10": ("WorldObject14", (180, 937, 1000)), "Ladder11": ("WorldObject15", (-190, 625, 824)),
         "Ladder12": ("WorldObject16", (8, 625, 1240)), "Ladder13": ("WorldObject17", (190, 481, 984)),
         "Ladder14": ("WorldObject18", (8, 737, 920))}
POLE_REACH = 60.0                   # native units in front of a pole a body may stand and grab it
# The bar on the end door: an invisible slab across the door's recess (the MM9 ExitTrigger0 starts off and only
# TrainingEnter.scr :OnBreak turns it on) moves away with the bar.
# Zone gains on the light colours (LT boxes, RGB), fitted to MM9's DAT lightmaps (hue_vs_lightmaps.py, 16-sample
# drafts): the joust hall and the cross corridor before it came out at 0.67-0.71 of MM9's lightmaps and too neutral
# (their big 0.4-0.5 fills); the pole room's blue (the "lava lights" under the water) at 0.76 of MM9's blue.
LIGHT_GAINS = [((-840, -290, -2060, 840, -30, -1020), (2.0, 1.9, 1.7)),
               ((-840, -290, -1020, 840, -30, -60), (1.65, 1.6, 1.5)),
               ((-300, 0, 650, 340, 1500, 1350), (1.0, 1.0, 1.35))]
CHANDELIER_TOP_LT = 424.0          # the spokes' top: the invisible floor over the wheel (extra_seeds)
BAR_SLAB_LT = {"z": -1346.0, "x": (-90.0, 90.0), "y": (0.0, 130.0)}
# Light colours: MM9 weights each Light by its BrightScale (0.15-0.9 here); the BLV lights carry colour x BrightScale
# (Ruined Temple lesson), the bake profile's direct_scale makes up the level.


def in_air(polygons: list, x: float, y: float, z: float) -> bool:
    """Whether (x, y, z) LT lies in air: the first polygon straight above faces down at it (Dook's Castle's)."""
    best, facing = None, False
    for polygon in polygons:
        low, high = polygon.bounds
        if not (low[0] <= x <= high[0] and low[2] <= z <= high[2]) or high[1] < y:
            continue
        n = polygon.normal
        if abs(n[1]) < 1e-6:
            continue
        hit = y + float(np.dot(polygon.points[0] - np.array([x, y, z]), n)) / n[1]
        if hit < y or (best is not None and hit >= best):
            continue
        ring = polygon.points[:, [0, 2]]
        edges = np.roll(ring, -1, axis=0) - ring
        cross = edges[:, 0] * (z - ring[:, 1]) - edges[:, 1] * (x - ring[:, 0])
        if (cross >= -1e-6).all() or (cross <= 1e-6).all():
            best, facing = hit, n[1] < 0
    return best is not None and facing


def flat(points_xz, y: float, template: Polygon, texture: str, notes: dict, model: str, role: str, flags: int):
    """A horizontal face over a ring of (x, z) points, front upward, mapped one texel per LT."""
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture,
                      (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), flags, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, polygon.mapping, flags,
                          model, role)
    polygon.notes.update(notes)
    return polygon


def lua_point(p) -> str:
    return lua.point(p)


class TrainingHall(dungeon.Hooks):
    generator = "mm9r_traininghall"
    own_water_surfaces = ("BlueWater0", "BlueWater1")     # edit_polygons builds both surfaces (no drawn_surfaces)
    mover_events = {**{name: (event, "click") for name, event in EV.items()},
                    **{name: (event, "click") for name, event in EV_RINGS.items()}}

    def destructible_events(self, build) -> dict:
        """The crate's boards, the end door's bar and the chandelier's bar (`motion: break`: scene destructibles that
        weapons break; the boards and the end bar also by a click): their deaths run the old click handlers."""
        events = {board: (event, 0) for board, event in BOARDS.items()}
        events["DestructableBrush12"] = (EV_BAR, 0)
        events["DestructableBrush6"] = (EV_DROPBAR, 0)
        return events

    # --- before the voxels and movers ---------------------------------------------------------------------------
    def extra_seeds(self, build) -> list:
        """Two changes to the DAT objects before the movers are built: each target ring takes its target's swing
        (TH_TargetRing.scr rings are WorldObjects drawn on the target; MM9 lowers the target with them on it), and the
        bar on the end door carries an invisible slab across the door's recess (the gate of ExitTrigger0)."""
        source = build.source
        keys = ("RotationPoint", "RotationAngles", "Speed", "ClosingSpeed", "CloseWaitTime", "Sticky", "Waveform",
                "ReopenOnContact", "OpenAway")
        for ring, (target, _) in RINGS.items():
            target_properties = source.by_name[f"target{target}"]["properties"]
            properties = source.by_name[ring.lower()]["properties"]
            for key in keys:
                if key in target_properties:
                    properties[key] = target_properties[key]
        template = next(p for p in source.polygons("InvisibleBrush2") if p.role == "invisible")
        original = source.polygons

        def polygons(name):
            out = original(name)
            if name in RINGS:
                # MM9's rings are invisible hit shells (Invisible flag) over the target's painted rings. Native
                # missiles pass Invisible faces, so the shells are built as ordinary faces and drawn fully transparent
                # (scene translucent_faces, opacity 0): an arrow or a spell striking a ring hits its shell.
                return [Polygon(p.points, p.keys, p.texture, p.mapping, p.flags & ~LT_INVISIBLE, p.model, "static",
                                notes=dict(p.notes)) if "invisible.dtx" not in p.texture.lower() else p for p in out]
            if name == "drop":
                # The chandelier's wheel: a rim (384-416 LT) and spokes (424) MM9's party box stands on; the native
                # party (a 37-unit cylinder) falls between them. An invisible floor over the wheel (radius 144 LT,
                # at the spokes' top) rides the chandelier, so the party lands on it and falls with it.
                ring = [(144.0 * math.cos(a), CHANDELIER_TOP_LT, 144.0 * math.sin(a))
                        for a in np.linspace(0.0, 2.0 * math.pi, 16, endpoint=False)]
                points = np.array(ring, float)
                polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], template.texture, template.mapping,
                                  template.flags, name, "invisible", notes=dict(template.notes))
                if polygon.normal[1] < 0:
                    points = points[::-1]
                    polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], template.texture,
                                      template.mapping, template.flags, name, "invisible", notes=dict(template.notes))
                return out + [polygon]
            if name != "DestructableBrush12":
                return out
            z, (x0, x1), (y0, y1) = BAR_SLAB_LT["z"], BAR_SLAB_LT["x"], BAR_SLAB_LT["y"]
            for ring in ([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)],
                         [(x0, y0, z), (x0, y1, z), (x1, y1, z), (x1, y0, z)]):
                points = np.array(ring, float)
                polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], template.texture, template.mapping,
                                  template.flags, name, "invisible", notes=dict(template.notes))
                out = out + [polygon]
            return out
        source.polygons = polygons
        return super().extra_seeds(build)

    def edit_polygons(self, build, polygons: list) -> list:
        """The two water volumes' surfaces (MM9 BlueWater1, the lobby pool, Ocean4.spr at SurfaceAlpha 0.5; BlueWater0,
        the pole room, water123 at 0.9) as non-solid translucent faces over the air of the volume's top (64 LT tiles). The
        lobby pool is 10 LT deep over its bed (-12): the party wades in it. The pole room's is 104 LT deep: the party
        swims and dives in it (the shared water rule, dungeon/water.py; its bed, sealed before, is built), and climbs out
        on the poles as MM9's does. With overrides.yml `map: {swim: false}` its surface is the old solid wading face."""
        source = build.source
        template = next(p for p in source.polygons("InvisibleBrush2") if p.role == "invisible")
        for polygon in polygons:
            polygon.bounds = (polygon.points.min(0), polygon.points.max(0))
        out = list(polygons)
        self.water_faces = {}
        for model, y, texture in (("BlueWater0", WATER_POLES_LT, "water:poles"), ("BlueWater1", WATER_POOL_LT,
                                                                                    "water:pool")):
            points = np.array(source.models[model].points, float)
            (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
            alias = source.aliases[texture]
            count = 0
            for row in np.arange(z0, z1, WATER_TILE):
                run = None
                for column in np.arange(x0, x1 + WATER_TILE, WATER_TILE):
                    # A tile is wet when most of its samples are in air (the poles' invisible prisms stand in some
                    # of them: those keep their water; a tile mostly in the wall is left out).
                    wet = column < x1 and sum(in_air(polygons, min(column + u * WATER_TILE, x1 - 0.5), y + 1,
                                                     min(row + v * WATER_TILE, z1 - 0.5))
                                              for u in (0.05, 0.5, 0.95) for v in (0.05, 0.5, 0.95)) >= 5
                    if wet and run is None:
                        run = column
                    elif not wet and run is not None:
                        top = min(row + WATER_TILE, z1)
                        ring = [(run, row), (run, top), (column, top), (column, row)]
                        # The lobby pool (10 LT deep): a non-solid surface over its bed, which the party wades. The
                        # pole room's (104 LT): non-solid, swum (the shared water rule); without it a solid surface
                        # the party stands on (the volume under it sealed and not built).
                        role = "static" if model == "BlueWater0" and not water.swimming(build.project) else "nonsolid"
                        out.append(flat(ring, y, template, texture, {"width": alias["width"],
                                                                     "height": alias["height"]},
                                        model, role, 0x1089 if role == "static" else 0x1088))
                        count += 1
                        run = None
            self.water_faces[model] = count
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        self.scale_lights(build)
        self.raise_lava_lights(build)
        content.props(PROPS)
        for o in source.objects:
            if o["class"] == "Fire":
                content.entity(o["name"], FIRE_DECORATION, project.native(o["properties"]["Pos"]), 0)
        self.place_perception_hints(build)
        # Rings and boards are struck by missiles too (MM9 OnDamage / DestructableBrush): the face fires its event
        # when an arrow or spell hits it (FaceAttribute TriggerByObject) as well as on a click. The rings are MM9's
        # invisible hit shells over the target's painted rings (Invisible flag on every polygon): their `_INV` part.
        struck = set(RINGS)
        for surface in build.package.metadata["surfaces"]:
            if surface["id"].removesuffix("_INV") in struck and "trigger" in surface:
                surface["flags"] = list(surface.get("flags", [])) + ["trigger_object"]
        # The horses' wheels go back with the horse (MM9's ClosingSpeed 200 LT/s).
        for mechanism in build.package.metadata["mechanisms"]:
            if mechanism["id"].startswith("d2w"):
                mechanism["door"]["close_speed"] = int(round(200 * SCALE))
        self.boxes = {}
        for name in VOLUMES:
            p = source.properties(name)
            centre, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
            if name in VOLUME_HALF_XZ_LT:
                dims[0] = dims[2] = VOLUME_HALF_XZ_LT[name]
            low, high = centre - dims, centre + dims
            if name in VOLUME_LOW_LT:
                low[1] = VOLUME_LOW_LT[name]
            low, high = project.native(low), project.native(high)
            self.boxes[name] = [np.minimum(low, high).round().astype(int).tolist(),
                                np.maximum(low, high).round().astype(int).tolist()]
        # The lobby ghouls' perch (TH_LobbyGhouls.scr's last marker, on WO_GhoulPlatform) and where they land when
        # they drop (the pole room's water surface under the platform).
        self.ghoul_points = {}
        for ghoul, marker in GHOULS.items():
            m = source.properties(marker)["Pos"]
            floor = content.floor_at(m[0], m[2], m[1] + 8)
            self.ghoul_points[ghoul] = (project.native([m[0], floor, m[2]]).round().astype(int).tolist(),
                                        project.native([m[0], WATER_POLES_LT, m[2] - 24]).round().astype(int).tolist())

    def scale_lights(self, build) -> None:
        """BLV light colour = MM9 colour x BrightScale x the zone gain (LIGHT_GAINS, fitted to MM9's DAT lightmaps with
        hue_vs_lightmaps.py: README, Baked lighting)."""
        gains = {}
        for light in build.lights:
            x, y, z = light["position_lt"]
            gain = np.ones(3)
            for (x0, y0, z0, x1, y1, z1), rgb in LIGHT_GAINS:
                if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1:
                    gain = np.array(rgb, float)
            gains[light["name"]] = gain * light["bright_scale"]
        for record in build.package.metadata["lights"]:
            factor = gains.get(record["id"], np.ones(3))
            record["color"] = [int(min(255, round(c * f))) for c, f in zip(record["color"], factor)]
        for light in build.lights:
            light["colour_in_blv"] = [int(min(255, round(c * f))) for c, f in zip(light["colour"], gains[light["name"]])]
        # The bake-only lights (over the four-per-point cap) take the same colour x BrightScale; their strength is then
        # the typical kept light's (the shared bake writes alpha = BrightScale / median of the kept lights, which
        # weighed the big 0.5 fills of the crate and training rooms twice as much as the kept lights).
        kept = sorted(light["bright_scale"] for light in build.lights if light["kept"])
        typical = kept[len(kept) // 2] if kept else 1.0
        for light in build.lights:
            if not light["kept"]:
                light["mm9_colour"], light["mm9_bright_scale"] = light["colour"], light["bright_scale"]
                light["colour"] = light["colour_in_blv"]
                light["bright_scale"] = typical

    def raise_lava_lights(self, build) -> None:
        """MM9's four 'lava light' DirLights point straight up from under the pole room's water (128 LT, the surface at
        200): MM9 lights the room blue through it, our solid wading surface blocks them in the bake. Each becomes a
        bake-only point light just over the surface (colour x BrightScale, the pole room's blue gain), added to the
        bake's extra lights (work/lights.json)."""
        typical = sorted(l["bright_scale"] for l in build.lights if l["kept"])
        typical = typical[len(typical) // 2] if typical else 1.0
        for o in build.source.objects:
            if o["class"] != "DirLight" or not o["name"].startswith("lava light"):
                continue
            p = o["properties"]
            lt = [p["Pos"][0], WATER_POLES_LT + 8.0, p["Pos"][2]]
            colour = [int(min(255, round(c * float(p["BrightScale"]) * g)))
                      for c, g in zip(p["InnerColor"], LIGHT_GAINS[2][1])]
            build.lights.append({"name": f"{o['name']} (raised)", "position_lt": lt,
                                 "position": [int(round(v)) for v in build.project.native(lt)],
                                 "radius": int(round(float(p["LightRadius"]) * SCALE * 0.5)), "colour": colour,
                                 "bright_scale": typical, "kept": False, "reason": "a floor point already under four lights",
                                 "note": "convert.py: MM9 DirLight under the water, raised over the surface"})

    def place_perception_hints(self, build) -> None:
        """Each PerceptionBrush's visible polygons (MM9's Perception.spr) as untouchable translucent faces with a cog,
        in the room of the air beside them, drawn from both sides (Drangheim Prison's and the Ruined Temple's route)."""
        package, source = build.package, build.source
        self.hints, self.hint_difficulty, self.hint_faces = {}, {}, 0
        difficulties = perception_difficulties_by_model_name(source.world)
        for lower in sorted(difficulties, key=lambda n: int(n[len("perceptionbrush"):])):
            k = int(lower[len("perceptionbrush"):])
            name = next(model for model in source.models if model.lower() == lower)
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                rooms = build.content.rooms
                room = room_id(_side_room(rooms, polygon, 1) or _side_room(rooms, polygon, -1)
                               or rooms.owner(polygon.points.mean(0)))
                node = f"TRIGGER_perception_{name}_{i}"
                package.add_polygon(node, polygon, build.stats)
                package.room_nodes[room].append(node)
                surface = {"id": node[8:], "source_node": node, "flags": ["untouchable"],
                           "cog_number": PERCEPTION_COG + k}
                # A visible hint stands in front of its board and takes the click (and the missile): it breaks the
                # board it marks, as a hit on the board would.
                board = next((b for b, h in BOARD_HINTS.items() if h == name), None)
                if board is not None:
                    surface["flags"] = ["untouchable", "trigger_object"]
                    surface["trigger"] = {"event_id": BOARDS[board], "type": "click"}
                package.metadata["surfaces"].append(surface)
                self.hint_faces += 1
            self.hints[name] = PERCEPTION_COG + k
            self.hint_difficulty[PERCEPTION_COG + k] = difficulties[lower]

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor_index, self.moved_actors = [], {}, {}
        for o in source.objects:
            if o["name"] not in bases:
                continue
            base, p = bases[o["name"]], o["properties"]
            changes = placed_body(base["monster_id"], p)        # MM9's body: the row's, or at the DAT's own Scale
            if content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 24) is None:
                # Ghoul4 stands on a seam of the cave floor's triangles: the nearest point with a floor under it.
                for dx, dz in ((8, 0), (-8, 0), (0, 8), (0, -8), (16, 0), (-16, 0), (0, 16), (0, -16)):
                    if content.floor_at(p["Pos"][0] + dx, p["Pos"][2] + dz, p["Pos"][1] + 24) is not None:
                        moved = [p["Pos"][0] + dx, p["Pos"][1], p["Pos"][2] + dz]
                        o = dict(o, properties=dict(p, Pos=moved))
                        p = o["properties"]
                        self.moved_actors[o["name"]] = [dx, dz]
                        break
            record = content.actor(o, base, sector_of_room, floor_query_lt=p["Pos"][1] + 24, **changes)
            self.actor_index[o["name"]] = record["actor_index"]
            out.append(record)
        records = {name: out[index] for name, index in self.actor_index.items()}
        for name, routines in self.training_routines(build, records).items():
            records[name].setdefault("mm9_ai", {})["routines"] = routines
        return out

    def training_routines(self, build, records: dict) -> dict:
        """The scenes' routines (SCENES) by DAT object, from each object's script and ScriptParams."""
        source, content, project = build.source, build.content, build.project

        def foot(name: str) -> list:
            pos = source.properties(name)["Pos"]
            floor = content.floor_at(pos[0], pos[2], pos[1] + 24)
            if floor is None:
                raise SystemExit(f"{name}: no floor under it")
            return project.native([pos[0], floor, pos[2]]).round().astype(int).tolist()

        def toward(at: list, name: str) -> float:
            x, y, _ = project.native(source.properties(name)["Pos"])
            return round(math.degrees(math.atan2(y - at[1], x - at[0])) % 360.0, 1)

        out = {}
        for name, record in records.items():
            o = source.by_name[name.lower()]
            script = str(o["properties"].get("ScriptName") or "").lower().replace("scripts\\", "")
            params = str(o["properties"].get("ScriptParams") or "").split()
            seconds = lua.model_clip_seconds(record["monster_id"])

            def clip(anim: str) -> dict:
                role = {"stand": "standing", "fidget1": "fidget", "hattack1": "attack_melee"}.get(anim.lower())
                role = role or ("attack2" if anim.lower() == "hattack2" else anim.lower())
                if role not in seconds:
                    raise SystemExit(f"{name}: {anim} ({role}) is not a clip of monster {record['monster_id']}")
                return {"clip": role, "seconds": math.floor(seconds[role] * 100) / 100}

            face = {"face": round(record["initial_yaw_units"] / 2048 * 360.0, 1)}
            if script == "th_trainingorcs.scr":
                out[name] = {"train": [face, *map(clip, DRILL)]}
            elif script == "th_trainingorccommander.scr":
                out[name] = {"train": [face, *map(clip, COMMANDS)]}
            elif script == "th_orcsgossip.scr":
                out[name] = {"gossip": [face, *map(clip, params[:6])]}
            elif script == "th_trainingorcobserver.scr":         # p0, p1 markers, p2 the commander it faces
                a, b = foot(params[0]), foot(params[1])
                out[name] = {"train": [{"walk": a}, {"face": toward(a, params[2])}, {"wait": [OBSERVER_WAIT] * 2},
                                       clip("Fidget1"),
                                       {"walk": b}, {"face": toward(b, params[2])}, {"wait": [OBSERVER_WAIT] * 2},
                                       clip("Fidget1")]}
            elif script == "th_jousttrellborg.scr":               # p0-p3 clips, p4 its marker (WalkTo 3)
                out[name] = {"joust": [{"walk": foot(params[4])}, face, *map(clip, params[:4])]}
            elif script == "th_lookouttrellborg.scr":             # p0, p1 markers; at p0 it watches p3, at p1 p2
                a, b = foot(params[0]), foot(params[1])
                look = [clip("Stand"), clip("Fidget1"), clip("Stand")]
                out[name] = {"joust": [{"walk": a}, {"face": toward(a, params[3])}, {"wait": [OBSERVER_WAIT] * 2},
                                       *look,
                                       {"walk": b}, {"face": toward(b, params[2])}, {"wait": [OBSERVER_WAIT] * 2},
                                       *look]}
            elif script == "th_meantrellborg.scr":                # p0 the switch, p1 the Trellborg it launches at
                at = record["position"]
                at = [at["x"], at["y"], at["z"]]
                self.mean_lead = round(sum(clip(anim)["seconds"] for anim in MEAN_CLIPS), 2)
                out[name] = {"launch": [*map(clip, MEAN_CLIPS), {"face": toward(at, params[1])}, {"wait": HOLD}],
                             "reset": [{"face": toward(at, params[0])}, {"wait": HOLD}]}
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Training Hall")
        index = {o["name"]: o["index"] for o in build.source.objects}
        script.doors()
        script.chests()
        lines = script.lines
        hint = self.hints
        groups = ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(script.groups.items()))
        lines += [
            "-- Mover groups (each MM9 model's mechanism and its invisible collision part move together).",
            f"local GROUPS = {{{groups}}}",
            "local function openG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Open) end end",
            "local function closeG(g) for _, d in ipairs(GROUPS[g]) do evt.SetDoorState(d, DoorAction.Close) end end",
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "local function sound(name) evt.PlaySoundName(name, 0, 0, 0) end",
            "local function inBox(b, x, y, z) return x >= b[1][1] - 37 and x <= b[2][1] + 37 and y >= b[1][2] - 37 "
            "and y <= b[2][2] + 37 and z + 170 >= b[1][3] and z <= b[2][3] end",
            "local function hintOff(cog) set(\"HintOff\" .. cog, 1); evt.SetFacetBit(cog, FacetBits.Invisible, true) end",
            "",
            "-- The lobby chandelier (dropsequence -> cracktrigger1-5 -> droptrigger destroys DestructableBrush6, whose death",
            "-- opens Door \"drop\": 432 LT down at 750 LT/s, Sticky). The party standing on it hears each trigger's",
            "-- ActivationSound as it fires (MM9's SendDelays: dropsequence 0, cracktrigger1 0.5, 2-3 0.35, 4 0.25, 5 1.25,",
            "-- droptrigger 1.0 s): the wood creaks and cracks, the bar shatters and the chandelier falls into the pool.",
            "local CRACKS = {{0.5, \"events/woodwood02.wav\"}, {0.35, \"events/woodwood03.wav\"}, "
            "{0.35, \"events/shatterwood01.wav\"}, {0.25, \"events/shatterwood02.wav\"}}",
            "local function creak()",
            "    if var(\"DropDone\") == 1 or var(\"DropCrack\") > 0 then return end",
            "    sound(\"ambient/woodcreak2.wav\")   -- dropsequence",
            "    sound(\"events/woodwood01.wav\")   -- cracktrigger1",
            "    set(\"DropCrack\", 1)",
            f"    arm({T_DROP}, CRACKS[1][1])",
            "end",
            f"handlers[{T_DROP}] = function()   -- cracktrigger2-5",
            f"    if not fired({T_DROP}) then return end",
            "    local k = var(\"DropCrack\")",
            "    sound(CRACKS[k][2])",
            "    set(\"DropCrack\", k + 1)",
            f"    if CRACKS[k + 1] then arm({T_DROP}, CRACKS[k + 1][1]) else arm({T_DROP2}, 1.25 + 1.0) end",
            "end",
            f"handlers[{T_DROP2}] = function()",
            f"    if not fired({T_DROP2}) then return end",
            f"    evt.DestroyDestructible({index['DestructableBrush6']})   -- droptrigger: DestructableBrush6 destroy",
            "end",
            "-- DestructableBrush6's death (droptrigger's destroy, or 100 HP of weapon damage) opens \"drop\".",
            f"handlers[{EV_DROPBAR}] = function()",
            "    if var(\"DropDone\") == 1 then return end",
            "    set(\"DropDone\", 1)",
            "    openG(\"drop\")",
            f"    hintOff({hint['PerceptionBrush0']})   -- Door drop OpenTrigger: \"drop perception\" off",
            "end",
            "",
            "-- The lobby ghouls (TH_LobbyGhouls.scr): TriggerLobbyGhouls sends them up the stairs into the pole room and",
            "-- onto WO_GhoulPlatform over its entrance (MM9 runs them along Ghoul*Marker0-2 and sets them on the last",
            "-- marker) and uses the dragon door; TriggerGhoulsAttack drops them in front of the party and uses the door;",
            "-- TriggerShutDoor uses it once more. A dead ghoul takes neither Go nor Drop (MM9.receives): it stays where it",
            "-- fell. Drop makes the platform non-solid (DropGhouls: ClearFlag WO_GhoulPlatform), so whatever is perched on",
            "-- it falls once any living ghoul takes it.",
        ]
        ghouls = []
        for name, (perch, landing) in self.ghoul_points.items():
            ghouls.append(f"{{name = \"{name}\", actor = {self.actor_index[name]}, perch = {lua_point(perch)}, "
                          f"land = {lua_point(landing)}}}")
        lines += [
            f"local GHOULS = {{{', '.join(ghouls)}}}",
            "local function ghoulsUp()",
            "    set(\"GhoulsUp\", 1)",
            "    for _, g in ipairs(GHOULS) do",
            "        if MM9.receives(\"traininghall\", g.name, \"Go\", g.actor) then",
            "            set(\"Perched\" .. g.name, 1)",
            "            evt.SetMapActorPosition(g.actor, g.perch[1], g.perch[2], g.perch[3])",
            "        end",
            "    end",
            "    openG(\"dragonroomdoor\")",
            "end",
            "local function ghoulsDrop()",
            "    if var(\"GhoulsUp\") ~= 1 then return end",
            "    set(\"GhoulsDropped\", 1)",
            "    local drops = false",
            "    for _, g in ipairs(GHOULS) do",
            "        if MM9.receives(\"traininghall\", g.name, \"Drop\", g.actor) then drops = true end",
            "    end",
            "    for _, g in ipairs(GHOULS) do",
            "        if drops and var(\"Perched\" .. g.name) == 1 then",
            "            set(\"Perched\" .. g.name, 0)",
            "            evt.SetMapActorPosition(g.actor, g.land[1], g.land[2], g.land[3])",
            "        end",
            "    end",
            "    closeG(\"dragonroomdoor\")",
            "end",
            "",
            "-- The joust (d2lever, Switch: open -> Trigger2 turns the wheels and opens dummy2door, the horse rides 1190 LT",
            "-- east at 1250 LT/s; close -> Trigger3 and dummy2door back at 200 LT/s). A click on the lever does it, and so",
            "-- does the Mean Trellborg (TH_MeanTrellborg.scr) while the party is down at the lanes (TriggerTrellborgOn0/1",
            "-- 'Go', Off0/1 'Stop'): stand, two fidgets and a taunt (routine \"launch\": MEAN_LEAD s), pull, he turns to",
            "-- the Trellborg the horse rides at, pulls it back facing the lever (dummy2door 'Switch', routine \"reset\"), and",
            "-- when it is back ('Throw') he starts again.",
            "-- The horse's wheels (d2w1-4, RotatingBrush: mover spin) turn while it rides: Trigger2 sends them on and",
            "-- reverse, Trigger3 reverse and on; dummy2door's Open/CloseTriggers (TriggerHorseGo) send off on arrival (out",
            "-- 1190 LT at 1250 LT/s, back at 200 LT/s). The second horse's wheels (d4w1-4) never turn in MM9: Trigger7",
            "-- sends them on and Trigger6 off in the same moment.",
            "local WHEELS2 = {" + ", ".join(f"DOORS.d2w{k}" for k in range(1, 5)) + "}",
            "local function wheels2(...) for _, w in ipairs(WHEELS2) do for _, m in ipairs({...}) do evt.SpinMover(w, m) end end end",
            "local function lever2(pull)",
            "    if pull then openG(\"d2lever\"); openG(\"Horse2\"); openG(\"Horse2Wheels\"); set(\"Horse2Out\", 1)",
            "    else closeG(\"d2lever\"); closeG(\"Horse2\"); closeG(\"Horse2Wheels\"); set(\"Horse2Out\", 0) end",
            "    if pull then wheels2(\"on\", \"reverse\") else wheels2(\"reverse\", \"on\") end",
            f"    arm({T_WHEELS2}, pull and 1190 / 1250 or 1190 / 200)",
            "    sound(\"events/gears01.wav\")",
            "end",
            f"handlers[{T_WHEELS2}] = function() if fired({T_WHEELS2}) then wheels2(\"off\") end end   -- TriggerHorseGo",
            f"handlers[{EV['d2lever']}] = function() lever2(var(\"Horse2Out\") == 0) end",
            "",
            "-- The training scenes (SCENES in convert.py): while the party is in its part of the hall, each actor runs its",
            "-- MM9 script's chain of clips and walks (its scene routine, runtime only: set again on load); the drill, the",
            "-- commanders' orders, the observers' pacing, the gossip, the jousters' and the lookout's watch.",
            "local SCENES = {",
            *[f"    {scene} = {{routine = \"{routine}\", actors = {{{', '.join(str(self.actor_index[n]) for n in names)}}}}},"
              for scene, (routine, _, _, names) in SCENES.items()],
            "}",
            "local function scene(name, on)",
            "    set(name, on and 1 or 0)",
            "    for _, a in ipairs(SCENES[name].actors) do evt.SetActorRoutine(a, on and SCENES[name].routine or nil) end",
            "end",
            f"local MEAN, MEAN_LEAD = {self.actor_index['MeanTrellborg']}, {self.mean_lead:g}",
            "local function meanLaunch() evt.SetActorRoutine(MEAN, \"launch\"); arm(" + str(T_JOUST) + ", MEAN_LEAD) end",
            f"handlers[{T_JOUST}] = function()",
            f"    if not fired({T_JOUST}) then return end",
            "    if var(\"Jousting\") ~= 1 or var(\"MeanDead\") == 1 then return end",
            "    if var(\"JoustThrow\") == 1 then           -- the horse is back ('Throw'): :CheckStart",
            "        set(\"JoustThrow\", 0); meanLaunch()",
            "    elseif var(\"Horse2Out\") == 0 then        -- :LaunchHorse",
            "        lever2(true); set(\"Launches\", var(\"Launches\") + 1)",
            f"        arm({T_JOUST}, 1.5)",
            "    else                                      -- :ResetSwitch",
            "        lever2(false); evt.SetActorRoutine(MEAN, \"reset\"); set(\"JoustThrow\", 1)",
            f"        arm({T_JOUST}, 1190 / 200)",
            "    end",
            "end",
            "local function joust(on)",
            "    scene(\"Jousting\", on)",
            "    set(\"JoustThrow\", 0)",
            "    if on then meanLaunch() else evt.SetActorRoutine(MEAN, nil) end",
            "end",
            f"handlers[{KILL_HOOK}] = function(context) if context.actorIndex == MEAN then set(\"MeanDead\", 1) end end",
            "",
            "-- The second horse (d4lever0, Switch: open -> dummy4guide and dummy4door open; dummy4door rides 2000 LT east",
            "-- through the wooden wall: woodexplosion, PerceptionBrush1 off, and dummy4guide's upperbreak1 -> Trigger8 ->",
            "-- lowerbreak1, upperbreak2, Trigger9 -> lowerbreak2: the wall is gone and the debris room behind it is open).",
            "-- Close: the guide goes back and dummy4door locks where it stands (MM9).",
            f"handlers[{EV['d4lever0']}] = function()",
            "    sound(\"events/gears01.wav\")",
            "    if var(\"Lever4Open\") == 1 then",
            "        set(\"Lever4Open\", 0); closeG(\"d4lever0\"); closeG(\"Horse4Guide\")",
            "        return",
            "    end",
            "    set(\"Lever4Open\", 1); openG(\"d4lever0\"); openG(\"Horse4Guide\")",
            "    if var(\"WallBroken\") == 1 then return end",
            "    openG(\"Horse4\"); openG(\"Horse4Wheels\")",
            f"    hintOff({hint['PerceptionBrush1']})",
            f"    arm({T_CRASH}, 1.1)",
            "end",
            f"handlers[{T_CRASH}] = function()",
            f"    if not fired({T_CRASH}) then return end",
            "    set(\"WallBroken\", 1)",
            "    sound(\"weapons/eqhammerimpact.wav\")",
            "    for _, k in ipairs({" + ", ".join(str(build.source.by_name[f"exsound{k}"]["index"]) for k in range(4))
            + "}) do set(\"AmbientSound\" .. k, 1) end   -- upper/lowerbreak1-2 DamageTriggers: exsound0-3 on",
            "    for _, id in ipairs({" + ", ".join(str(index[name]) for name in WALL) + "}) do "
            "evt.DestroyDestructible(id) end   -- the wall's TriggerDestroyOnly pieces",
            "end",
            "",
            "-- The reset levers by the range (RotatingDoor, MM9 Locked: nothing in the map unlocks them).",
        ]
        for k in range(1, 5):
            lines.append(f"handlers[{EV[f'resetlever{k}']}] = function() evt.StatusText(\"The lever is locked.\") end")
        lines += [
            "",
            "-- The crate round the Blackbox (DestructableBrush0-5, 25 HP, each turns its PerceptionBrush2-7 off; the back",
            "-- board DestructableBrush8, 100 HP: crateopentrigger turns PerceptionBrush8 off): scene destructibles that",
            "-- weapons break (a click on a board: the shared killing blow; a click or missile on its hint: this event).",
            "local function breakBoard(board, id, cog)",
            "    if var(\"Broken\" .. board) == 1 then return end",
            "    set(\"Broken\" .. board, 1)",
            "    evt.DestroyDestructible(id); hintOff(cog)",
            "end",
        ]
        for board, event in BOARDS.items():
            lines.append(f"handlers[{event}] = function() breakBoard(\"{board}\", {index[board]}, "
                         f"{hint[BOARD_HINTS[board]]}) end")
        lines += [
            "",
            "-- The hall's end (TrainingEnter.scr \"TrainingHall\" on TrainingTrigger): breaking the bar on the end door",
            f"-- (DestructableBrush12, 1 HP) gives key {KEY_TRAINED}, +5 Might and +5 Intellect (GiveAttribute 0 5 1, 1 5 1: the",
            "-- active member, as the Ruined Temple reads it), 20000 experience and the quest sound, and turns ExitTrigger0",
            "-- on: here the bar's invisible slab across the door's recess goes with it. With the key, the map loads with",
            "-- the bar gone (:Init RemoveObject).",
            f"handlers[{EV_BAR}] = function()",
            "    if var(\"BarBroken\") == 1 then return end",
            "    set(\"BarBroken\", 1)",
            f"    evt.DestroyDestructible({index['DestructableBrush12']})",
            f"    if MM9.hasKey({KEY_TRAINED}) == 0 then",
            f"        MM9.giveKey({KEY_TRAINED})",
            "        AddValue(BaseMight, 5)",
            "        AddValue(BaseIntellect, 5)",
            f"        {experience_lua(20000, KEY_TRAINED)}",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            "    end",
            "end",
            "",
            "-- The archery range (TH_TargetMgr.scr, TH_TargetRing.scr). The four targets stand at load; passing",
            "-- TriggerTargetsOff (StartOn) lays them flat ('closeall' -> LowerTargets: each target opens), TriggerTargetsOn",
            "-- stands them up again ('openall'); each re-arms the other. A ring hit by a missile (or a click) rings the bell,",
            f"-- pays its prize in gold once per target (key {KEY_WON} + target) and lays its target flat for good (open, lock).",
        ]
        targets = {}
        for ring, (target, _) in RINGS.items():
            targets.setdefault(target, []).append(ring)
        lines.append("local TARGETS = {" + ", ".join(
            f"[{t}] = {{\"target{t}\", " + ", ".join(f"\"{r}\"" for r in rings) + "}" for t, rings in targets.items())
            + "}")
        lines += [
            "local function setTarget(t, down)",
            "    if var(\"TargetLocked\" .. t) == 1 then return end",
            "    for _, g in ipairs(TARGETS[t]) do if down then openG(g) else closeG(g) end end",
            "end",
            "local function hitRing(t, prize)",
            "    if var(\"TargetLocked\" .. t) == 1 or var(\"TargetsDown\") == 1 then return end",
            "    set(\"RingHits\", var(\"RingHits\") + 1)",
            f"    if MM9.hasKey({KEY_WON} + t) == 0 then",
            f"        MM9.giveKey({KEY_WON} + t)",
            "        MM9.giveGold(prize)",
            "        set(\"Prize\" .. t, prize)",
            "        sound(\"events/gold01.wav\")",
            "    end",
            "    sound(\"events/hand bell.wav\")",
            "    setTarget(t, true)",
            "    set(\"TargetLocked\" .. t, 1)",
            "end",
        ]
        for ring, (target, prize) in RINGS.items():
            lines.append(f"handlers[{EV_RINGS[ring]}] = function() hitRing({target}, {prize}) end   -- {ring}")
        lines += [
            "",
            "-- The pole room's beams (Pusher0-2: MM9 Doors with Looping, 130-150 LT at 40 LT/s, MoveDelay 2, OpenWaitTime 3,",
            "-- CloseWaitTime 2): out, wait, back, wait, for ever, sweeping their beams.",
        ]
        pushers = []
        for name in ("Pusher0", "Pusher1", "Pusher2"):
            p = build.source.properties(name)
            travel = float(p["MoveDist"]) / float(p["Speed"])
            pushers.append((name, travel, float(p.get("OpenWaitTime", 3.0)), float(p.get("CloseWaitTime", 2.0)),
                            float(p.get("MoveDelay", 0.0))))
        lines.append("local PUSHERS = {" + ", ".join(
            f"{{name = \"{n}\", out = {d:g}, back = {d + w_open + d:g}, cycle = {d + w_open + d + w_close:g}, "
            f"delay = {delay:g}}}" for n, d, w_open, w_close, delay in pushers) + "}")
        lines += [
            f"handlers[{T_PUSH}] = function()",
            f"    evt.StartTimer({T_PUSH}, seconds(0.25))",
            "    local tick = var(\"PushTick\") + 1",
            "    set(\"PushTick\", tick)",
            "    for _, p in ipairs(PUSHERS) do",
            "        local t = (tick * 0.25 - p.delay) % p.cycle",
            "        if t < 0.25 then openG(p.name) elseif t >= p.out + (p.back - 2 * p.out) and t < p.out + (p.back - 2 * "
            "p.out) + 0.25 then closeG(p.name) end",
            "    end",
            "end",
            "",
        ]
        boxes = self.boxes
        runs = {
            "dropsequence": ("true", "creak()", False),
            "TriggerLobbyGhouls": ("true", "ghoulsUp()", False),
            "TriggerGhoulsAttack": ("true", "ghoulsDrop()", False),
            "TriggerShutDoor": ("var(\"GhoulsDropped\") == 1", "closeG(\"dragonroomdoor\")", False),
            "TriggerTargetsOff": ("var(\"TargetsDown\") == 0",
                                  "set(\"TargetsDown\", 1); for t = 1, 4 do setTarget(t, true) end", True),
            "TriggerTargetsOn": ("var(\"TargetsDown\") == 1",
                                 "set(\"TargetsDown\", 0); for t = 1, 4 do setTarget(t, false) end", True),
            "TriggerTrellborgOn0": ("var(\"Jousting\") == 0", "joust(true)", True),
            "TriggerTrellborgOn1": ("var(\"Jousting\") == 0", "joust(true)", True),
            "TriggerTrellborgOff0": ("var(\"Jousting\") == 1", "joust(false)", True),
            "TriggerTrellborgOff1": ("var(\"Jousting\") == 1", "joust(false)", True),
            **{start: (f"var(\"{name}\") == 0", f"scene(\"{name}\", true)", True)
               for name, (_, start, _, _) in SCENES.items() if start},
            **{stop: (f"var(\"{name}\") == 1", f"scene(\"{name}\", false)", True)
               for name, (_, _, stop, _) in SCENES.items() if stop},
        }
        volume_lua = ",\n".join(
            f"    {{name = \"{name}\", box = {{{lua.point(boxes[name][0])}, {lua.point(boxes[name][1])}}}, "
            f"again = {'true' if runs[name][2] else 'false'}, "
            f"armed = function() return {runs[name][0]} end, run = function() {runs[name][1]} end}}"
            for name in VOLUMES)
        lines += [
            "-- MM9's Trigger volumes, polled four times a second. The one-shot ones fire once (MM9 turns them off); the",
            "-- paired on/off ones fire whenever their state allows (MM9's mutual On/Off messages) and the party has left",
            "-- the box since.",
            "local VOLUMES = {",
            volume_lua,
            "}",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    local x, y, z = evt.GetPartyPosition()",
            "    for _, v in ipairs(VOLUMES) do",
            "        local inside = inBox(v.box, x, y, z)",
            "        if inside and var(\"In\" .. v.name) == 0 and var(\"Done\" .. v.name) == 0 and v.armed() then",
            "            if not v.again then set(\"Done\" .. v.name, 1) end",
            "            v.run()",
            "        end",
            "        set(\"In\" .. v.name, inside and 1 or 0)",
            "    end",
            "end",
            "",
            "-- The PerceptionBrushes: the red glow shows to a party whose Perception reaches the brush's PerceptionValue",
            "-- (12: the chandelier's bar, the wooden wall; 17: the crate's boards) unless MM9's wiring switched it off.",
            "local HINTS = {" + ", ".join(f"[{cog}] = {value}" for cog, value in sorted(self.hint_difficulty.items())) + "}",
            "local function updateHints()",
            "    for cog, value in pairs(HINTS) do",
            "        local want = evt.CheckSkill(" + str(PERCEPTION_SKILL) + ", 0, value) and 2 or 1",
            "        if var(\"Hint\" .. cog) ~= want or var(\"HintOff\" .. cog) == 1 then",
            "            set(\"Hint\" .. cog, want)",
            "            evt.SetFacetBit(cog, FacetBits.Invisible, want == 1 or var(\"HintOff\" .. cog) == 1)",
            "        end",
            "    end",
            "end",
            f"handlers[{T_HINTS}] = updateHints",
            f"handlers[{EV_LOAD}] = function()   -- map load: what MM9 saves stays as it was left",
            "    for cog, _ in pairs(HINTS) do set(\"Hint\" .. cog, 0) end",
            "    updateHints()",
            f"    if MM9.hasKey({KEY_TRAINED}) == 1 and var(\"BarBroken\") == 0 then set(\"BarBroken\", 1); "
            f"evt.DestroyDestructible({index['DestructableBrush12']}) end",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            f"    evt.StartTimer({T_PUSH}, seconds(0.25))",
            "    -- the scenes' routines are runtime only: those under way when the game was saved start again",
            *[f"    if var(\"{name}\") == 1 then " + ("joust(true)" if name == "Jousting" else f"scene(\"{name}\", true)")
              + " end" for name in SCENES],
            "end",
            "",
        ]
        script.add([], *[(EV[name], "Lever", "Lever") for name in EV],
                   *[(event, "Board", "Board") for event in BOARDS.values()], (EV_BAR, "Bar", "Bar"),
                   (EV_DROPBAR, "Chandelier bar", None),
                   *[(event, "Target", "Target") for event in EV_RINGS.values()],
                   (T_POLL, "Trigger volumes", None, "timer"), (T_HINTS, "Perception hints", None, "timer"),
                   (T_PUSH, "Pole room beams", None, "timer"),
                   *[(t, "Timer", None, "timer") for t in (T_JOUST, T_CRASH, T_DROP, T_DROP2, T_WHEELS2)],
                   (EV_LOAD, "Map load", None))
        script.hooks += [f'RegisterMonsterKilledHook({KILL_HOOK}, "Mean Trellborg killed", handlers[{KILL_HOOK}])']
        return script.finish(on_load=[EV_LOAD])

    # --- scene ------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """The ladders (the chain, the lobby's steel ladders, the pole room's poles), the water surfaces and the
        perception hints as translucent faces (found in the compiled BLV by texture)."""
        scene["ladders"] = self.ladders(build)
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        aliases = build.source.aliases
        by_texture = {aliases[PERCEPTION_TEXTURE]["alias"].lower(): "hints",
                      aliases["water:pool"]["alias"].lower(): "pool", aliases["water:poles"]["alias"].lower(): "poles"}
        found = {"hints": [], "pool": [], "poles": []}
        for face in blv["faces"]:
            kind = by_texture.get(str(face.get("texture_name", "")).lower())
            if kind and not face["is_portal"]:
                found[kind].append(face["index"])
        if len(found["hints"]) != self.hint_faces:
            raise SystemExit(f"{len(found['hints'])} perception faces in the BLV, {self.hint_faces} polygons")
        entries = scene.setdefault("translucent_faces", [])
        entries.append({"faces": sorted(found["hints"]), "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0],
                        "two_sided": True})
        # MM9's visible water: SurfaceAlpha x the sprite's alpha (BlueWater1 0.5, BlueWater0 0.9), seen from above.
        entries.append({"faces": sorted(found["pool"]), "opacity": 0.5, "tint": [1.0, 1.0, 1.0], "two_sided": False})
        entries.append({"faces": sorted(found["poles"]), "opacity": 0.9, "tint": [1.0, 1.0, 1.0], "two_sided": False})
        door_faces = {door["door_id"]: door["face_ids"] for door in scene["initial_state"]["doors"]}
        shells = sorted(f for mover in build.movers if mover["group"] in RINGS and not mover["invisible"]
                        for f in door_faces[mover["door_id"]])
        entries.append({"faces": shells, "opacity": 0.0, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        build.stats["ring_shell_faces"] = len(shells)
        build.stats["translucent_faces"] = sum(len(e["faces"]) for e in entries)
        build.stats["water_faces"] = {"pool": len(found["pool"]), "poles": len(found["poles"])}
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)

    def ladders(self, build) -> list[dict]:
        """Ladder records (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md) in native units from LT points."""
        project, models = build.project, build.source.models
        out = []

        def record(name, surface_lt, bottom_y, top_y, facing_xz, width_lt, reach, exit_lt, in_air=False):
            bottom = project.native([surface_lt[0], bottom_y, surface_lt[1]])
            top = project.native([surface_lt[0], top_y, surface_lt[1]])
            out.append({"id": name, "bottom": [round(float(v), 2) for v in bottom],
                        "top": [round(float(v), 2) for v in top],
                        "facing_degrees": round(math.degrees(math.atan2(facing_xz[1], facing_xz[0])) % 360.0, 2),
                        "width": round(width_lt * SCALE, 2), "reach": reach,
                        "top_exit": [round(float(v), 2) for v in project.native(exit_lt)]})
            if in_air:
                out[-1]["grab_in_air"] = True
            elif grabs_at_top(out[-1]):
                # the chain and the steel ladders are taken at the top too; the poles only by a jump (grab_in_air)
                out[-1]["grab_at_top"] = True

        sides = ((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0))
        # The chain the chandelier hangs on (MM9 Ladder "Chain Ladder", 32 x 32 LT from the chandelier to the roof
        # room's ceiling): from the roof room's floor (640) at the hole's rim down onto the chandelier (464); a climber
        # going up steps off on the roof floor north of the hole.
        for k, (fx, fz) in enumerate(sides):
            record(f"ChainLadder_{k}", (-fx * 16.0, -fz * 16.0), CHANDELIER_TOP_LT, 700.0, (fx, fz), 32.0, 140.0,
                   (0.0, 641.0, 100.0))
        # The lobby's two steel ladders (Ladder0/1: rungs on the outer diagonal face of a post in the south corners)
        # up to the crow's nests at 432 (TreasureChest1 on the west one).
        for name, sx in (("Ladder0", -1.0), ("Ladder1", 1.0)):
            facing = (-sx * math.sqrt(0.5), math.sqrt(0.5))
            surface = (sx * 289.0, -289.0)
            record(name, surface, 0.0, 432.0 - PARTY_HEIGHT_LT, facing, 20.0, 60.0, (sx * 256.0, 433.0, -256.0))
        # The pole room's poles, four sides each.
        for name, (pole, exit_lt) in POLES.items():
            points = np.array(models[pole].points, float)
            low, high = points.min(0), points.max(0)
            cx, cz = (low[0] + high[0]) / 2, (low[2] + high[2]) / 2
            bottom = max(float(low[1]), WATER_POLES_LT)
            top = min(float(high[1]), exit_lt[1] - 16.0) - PARTY_HEIGHT_LT
            # MM9 wraps each pole in an invisible octagonal prism 16 LT round (the poles' collision): the climber
            # holds on at its faces. The poles hang in the air over the water: MM9's party jumps from a beam or a
            # pole to the next; `grab_in_air` (engine, 2026-10-30) lets a jumping or falling party take hold.
            for k, (fx, fz) in enumerate(sides):
                record(f"{name}_{k}", (cx - fx * 16.0, cz - fz * 16.0), bottom, top, (fx, fz), 40.0, POLE_REACH,
                       exit_lt, in_air=True)
        return out

    def report(self, build) -> dict:
        return {"scripted": {"boxes": getattr(self, "boxes", {}), "hints": getattr(self, "hints", {}),
                             "actors": getattr(self, "actor_index", {}), "ghouls": getattr(self, "ghoul_points", {}),
                             "water_faces": getattr(self, "water_faces", {}),
                             "moved_actors": getattr(self, "moved_actors", {})}}


def grow_exits(transitions_text):
    """ExitTrigger1 (16 LT thick in the roof room's east wall, a painted door: x 152-184 LT) is touched by MM9's party
    box against the wall; the native exit tests the party's centre, which the wall keeps 14.5 LT (its radius) off it.
    The row's box reaches EXIT_GROW_LT further into the room (map-local: the shared writer keeps MM9's box)."""
    def wrapped(project, polygons, current_text, facings=None):
        text, changes = transitions_text(project, polygons, current_text, facings)
        lines = text.split("\n")
        header = next(line for line in lines if line.startswith("CanonicalId") or "\tSourceMapFile\t" in line)
        column = {name: i for i, name in enumerate(header.split("\t"))}
        for k, line in enumerate(lines):
            cells = line.split("\t")
            if len(cells) < len(column) or cells[column["SourceMapFile"]] != project.map:
                continue
            grow = EXIT_GROW_LT.get(cells[column["SourceName"]])
            if grow is None:
                continue
            for axis, amount in zip("XYZ", grow):          # native axes: a negative amount grows toward -axis
                if amount:
                    centre, half = float(cells[column[f"Center{axis}"]]), float(cells[column[f"HalfExtent{axis}"]])
                    low, high = centre - half, centre + half
                    low, high = (low + amount * SCALE, high) if amount < 0 else (low, high + amount * SCALE)
                    cells[column[f"Center{axis}"]] = str(int(round((low + high) / 2)))
                    cells[column[f"HalfExtent{axis}"]] = str(int(round((high - low) / 2)))
            lines[k] = "\t".join(cells)
        return "\n".join(lines), changes
    return wrapped


EXIT_GROW_LT = {"ExitTrigger1": (-24, 0, 0)}


if __name__ == "__main__":
    from dungeon import tables
    tables.transitions_text = grow_exits(tables.transitions_text)
    sys.exit(dungeon.main(PROJECT, TrainingHall()))
