#!/usr/bin/env python3
"""
Dark Passageway, MM9 rework: MM9's DARKPASSAGEWAY.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_darkpassageway/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_darkpassageway/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules; this file adds the passage's population (props.json from
../../props/mm9_darkpassageway_claude, the perception hints, the water surfaces, the ladders, the actors) and its
scripted objects as native Lua, each citing what it reproduces (README.md, "Scripted objects"):
- the bridge puzzle (DarkP_bridgepuzzle.scr, DarkP_initMyStuff.inc, DarkP_RaisingSwitch.scr, DarkP_RaisingBridge.scr,
  DarkP_BridgeReset.scr; Bridge0-4, SwitchCreature0-3/5, TeleportDoor0);
- the teleporters (Teleporter class: Teleporter0/1, Lake, Mountain, Desert, Forest);
- the canyon (DarkP_CanyonSwitch.scr on SwitchCreature4, the banshee eyes BansheeAEye0-7, CanyonDoorL0/R0,
  TriggerBansheeOff0; MagicCarpet.scr on ElevatorObj);
- the forest ambush (TriggerDoor0, TriggerAttack0, DarkP_Warrior.scr, DarkP_NPCDie.scr, ForestDoor0, TeleportDoor1 by
  the warrior's DeathTriggerTarget);
- the painting (Painting, DoubleDoorL40/R40, PerceptionBrush1);
- the mirror puzzle in the desert (PassageMirror.scr, PassageLaser.scr, PassageGemstone.scr, DP_CageMonster.scr:
  Mirror0-3, Gemstone, Door1-6, CageTerror0-5, DesertDoor0);
- Njam's cameo (Trigger1, SpawnNjamCameo.scr, NjamCameo.scr);
- the spike trap (SpikeTrigger1, SpikeDoor1-4, Spikes1 PropDamager);
- the ocean (SeaMonsterFemale0's DeathTriggerTarget breaks DB_TeleporterCage0) and the tube room's dive;
- the exit room (ExitTrigger0-3, ExitRiser, ExitRamp, Switch -> ExitReset);
- the Wyrde of the Unknown (NPC338.scr :OnRude, the flame cage FlameCage and FlameDamage, ExitPoint to Guberland);
- the scroll (Givetake.scr "483 false 1" on Prop38): a world item (../mm9r_common/dungeon/pickups.py).
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
from dungeon.source import ROOT, SCALE, facing_degrees  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from transcode_mm9_dat_to_odm import perception_difficulties_by_model_name  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"
PERCEPTION_TEXTURE = "sprites\\perception.spr"
PERCEPTION_COG = 300                # PerceptionBrush<k>: cog PERCEPTION_COG + k
PERCEPTION_SKILL = 29               # evt.CheckSkill's id: the party's best Perception
PERCEPTION_OPACITY = 0.5

# --- Events, cogs, timers ----------------------------------------------------------------------------------------------
EV_LOAD = 1
EV_SWITCH = {"SwitchCreature0": 201, "SwitchCreature1": 202, "SwitchCreature2": 203, "SwitchCreature3": 204}
EV_RESET_STATUE = 205               # SwitchCreature5 (DarkP_BridgeReset.scr)
EV_CANYON_STATUE = 206              # SwitchCreature4 (DarkP_CanyonSwitch.scr)
EV_CARPET = 207                     # ElevatorObj (MagicCarpet.scr)
EV_PAINTING = 208
EV_MIRROR = {f"Mirror{k}": 210 + k for k in range(4)}
EV_GEMSTONE = 215
EV_SWITCH_EXIT = 217                # the exit room's Switch (-> ExitReset)
EV_TELEPORT_DOOR1 = 218             # TeleportDoor1: locked until the Colloidal Warrior dies
EV_LOCKED = {"CanyonDoor": 219, "ForestDoor0": 220, "TeleportDoor0": 221, "DesertDoor0": 222}
HINT_TARGET = {"PerceptionBrush0": "MountainForestDoor", "PerceptionBrush1": "Painting",
               "PerceptionBrush2": "TrapRoomDoor2", "PerceptionBrush3": "ForestDoor0"}
# The four puzzle statues stand on the bridges and ride them (DarkP_RaisingSwitch.scr clears DontFollowStandingOn);
# decorations do not move natively: each statue has a copy at the bridge's other pose, and the map shows the one
# matching its bridge (cogs STATUE_COG + 2 k: the DAT pose, + 2 k + 1: the other).
STATUE_COG = 410
# The desert's mirrors are decorations (mirrors.json, written by the props project's mirror_source.py from Mirror0-3,
# whose overrides.yml rule is skip) so the map can turn them: cog MIRROR_COG + k, evt.AimDecoration.
MIRROR_COG = 420
MIRRORS_JSON = PROJECT / "mirrors.json"
MIRROR_TURN_SPEED = 180             # degrees a second (PassageMirror.scr :Rotate: Rotate 0,1,0, 10, 180)
STATUE_BRIDGE = {"SwitchCreature0": 0, "SwitchCreature1": 1, "SwitchCreature2": 2, "SwitchCreature3": 3}
COG_RESET_STATUE = 418              # SwitchCreature5's SetSprite key (evt.PlayDecorationClip)
COG_CANYON_STATUE = 419             # SwitchCreature4's
COG_NJAM = 401
KILL_HOOK = 96
T_POLL, T_HINTS, T_EYES, T_CARPET, T_CAGES, T_NJAM, T_WARRIOR, T_FLAME, T_CANYON = range(400, 409)
T_STATUE = 430                      # + k: the end of statue k's clip (SWITCH_STATUES)

# The ice statues are animated decorations (mm9_deco_<prop>_anim.glb: the creature's clips, lower case). The puzzle's
# (DarkP_RaisingSwitch.scr "PuzzleManager0 Hit<X> <type>", DarkP_BridgeReset.scr): (letter or None for the reset, the
# clip at start, held: PlayAnim ..., StopHere; the clip of a Use, whose end triggers the manager). MM9 starts the
# banshee on awareAir and the skeleton warrior (DarkP_CanyonSwitch.scr) on CastSpell, which BANSHEE.abc and
# SKELETONWARRIOR.abc lack: those stand at rest (their build pose) until used.
SWITCH_STATUES = {"SwitchCreature0": ("A", "fidget1", "fidget1"), "SwitchCreature1": ("B", "fidget1", "fidget1"),
                  "SwitchCreature2": ("C", "fidget1", "fidget1"), "SwitchCreature3": ("D", "awareair", "fidgetair1"),
                  "SwitchCreature5": (None, "fidget1", "fidget1")}
CANYON_START = "castspell"
# DarkP_CanyonSwitch.scr :OnUse, :AnimateA-C: the clips in turn, and the banshee eyes each clip's end wakes.
CANYON_CLIPS = [("hattack2", (0, 1)), ("taunt", (2, 3)), ("rattack1", (6, 7)), ("fidget1", (4, 5))]
STATUE_MODELS = ROOT / "assets_source/worlds/mm9/models"


def statue_clips(prop: str) -> dict:
    """An ice statue's clips by name (lower case): their length in seconds (the latest key of their samplers)."""
    import json
    import struct
    data = (STATUE_MODELS / f"mm9_deco_{prop}_anim.glb").read_bytes()
    size = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + size])
    return {a["name"]: max(gltf["accessors"][s["input"]]["max"][0] for s in a["samplers"])
            for a in gltf.get("animations", [])}
KEY_SCROLL_ITEM = 483               # Givetake.scr "483 false 1"
ITEM_FATE = 396                     # NPC338.scr: hasitem 396 -> key 188, 146 000 experience
KEY_ACTIVATED, KEY_MET, KEY_ITEM_BACK = 476, 187, 188
RUDE_WYRDE = 338

# The bridge puzzle (DarkP_initMyStuff.inc): the state is a 5-bit number, bit (4 - k) set when bridge k is down; the
# four statues map a state to the next (aA..aD, sparse arrays; the rest are 0 and never reached). Start 14, solved 0
# (sequence ADCBDCBA).
PUZZLE_START = 14
PUZZLE = {
    "A": {0: 0, 1: 5, 5: 14, 9: 21, 14: 22, 17: 0, 19: 22, 21: 14, 22: 14, 23: 14, 25: 9, 26: 5, 29: 1, 30: 1, 31: 9},
    "B": {0: 0, 1: 9, 5: 30, 9: 23, 14: 5, 17: 9, 19: 31, 21: 5, 22: 1, 23: 1, 25: 17, 26: 23, 29: 23, 30: 9, 31: 23},
    "C": {0: 0, 1: 23, 5: 1, 9: 22, 14: 23, 17: 5, 19: 23, 21: 19, 22: 30, 23: 9, 25: 5, 26: 31, 29: 25, 30: 5, 31: 21},
    "D": {0: 0, 1: 30, 5: 22, 9: 26, 14: 30, 17: 23, 19: 30, 21: 9, 22: 21, 23: 22, 25: 23, 26: 9, 29: 30, 30: 23, 31: 29},
}
SWITCH_LETTER = {"SwitchCreature0": "A", "SwitchCreature1": "B", "SwitchCreature2": "C", "SwitchCreature3": "D"}
BRIDGE_BUILT_UP = {0: True, 1: False, 2: False, 3: False, 4: True}   # the DAT pose of each bridge (DarkP_RaisingBridge.scr p2)

# The mirrors (PassageMirror.scr "<angle> <next> <beam>"): a click turns a mirror 10 degrees (counter + 1 mod 36); the
# gemstone's light passes a mirror to the next when its counter is the target angle / 10.
MIRRORS = {"Mirror0": (330, "Mirror1"), "Mirror1": (10, "Mirror2"), "Mirror2": (340, "Mirror3"), "Mirror3": (50, "Gemstone")}
CAGES = {"CageTerror0": "Door1", "CageTerror1": "Door2", "CageTerror2": "Door3", "CageTerror3": "Door4",
         "CageTerror4": "Door5", "CageTerror5": "Door6"}

TELEPORTERS = {"Teleporter0": "Teleporter1", "LakeTeleporter": "LakeArrival", "MountainTeleporter": "MountainArrival",
               "DesertTeleporter": "DesertArrival", "ForestTeleporter": "ForestArrival"}
EYES = [f"BansheeAEye{k}" for _, pair in CANYON_CLIPS for k in pair]   # in the order they wake
EYE_DAMAGE = 5                      # Shooter DamageAmt (ProjectileName KBYellowLine, ShootInterval 1)

# Water (README "Water"). (model, wading surface LT, texture, opacity). overrides.yml `map: {swim: true}` (2026-11-06,
# devdocs/mm9_rework/MM9_WATER_SWIMMING_DESIGN.md): MM9's volumes (the scene's `water_volumes`, the shared build's
# dungeon/water.py; TubeRoomWater, the flooded tube, carries MM9's current, 90 LT/s down) swum and dived in, the tiles
# non-solid at each volume's own top (MM9's), the sea monsters swimmers in their water, no dive box. Without it the
# tiles are wading floors at these heights (the ocean's 12 LT over MM9's: the party steps onto the island) and the dive
# box stands in for the swim.
WATER = [("BlueWater0", -598.0, "water:lake", 0.4), ("TubeRoomWater0", -382.0, "water:tube", 0.7),
         ("Ocean", -1300.0, "water:ocean", 0.95)]
WATER_TILE = 32.0
SWIM_VOLUMES = ("BlueWater0", "TubeRoomWater0", "TubeRoomWater", "Ocean")
SEA_MONSTER_WATER = {"SeaMonsterMale": "TubeRoomWater0", "SeaMonsterFemale": "Ocean"}
# The flooded tube runs east under the tube room (PhysicsBSP, ceiling -576, floor -736 LT) into a shaft (x -3792..-3696,
# z -8480..-8368) whose bottom is the ocean hall's sky: Terrain4's down-facing starfield polygon at -977 LT, which MM9's
# party passes from behind. With swimming it is non-solid (still drawn from the hall): the party swims down the tube
# and shaft and drops into the ocean, and the shaft's air is the hall's room (the engine crosses rooms at portals only).
SHAFT_SKY = ("Terrain4", (-3800.0, -8490.0), (-3690.0, -8360.0), (-980.0, -970.0))   # model, x z low, x z high, y
# The shaft's open bottom: the engine holds a body whose eye leaves a volume through its bottom as at a surface (it
# stops at TubeRoomWater's bottom, -968 LT, over the hall's air), so a box at the bottom (SHAFT_EXIT_LT: the shaft's
# footprint, from 80 LT under the volume's bottom to 8 over it) moves the party straight down under the hall's sky
# (SHAFT_DROP_LT), and it falls into the ocean: the swim down the tube and the shaft is real, only the last step out of
# the water is a move (README "Water"; an engine item: leaving a volume through its bottom).
SHAFT_EXIT_LT = ((-3792.0, -1048.0, -8480.0), (-3696.0, -960.0, -8368.0))
SHAFT_DROP_LT = (-3744.0, -1050.0, -8424.0)
# The tube room's dive (without swimming): the water runs from the tube room down a submerged tube and a shaft into
# the ocean hall (MM9 swims it). The party wading at the tube's mouth dives: it comes up on the ocean under the shaft.
DIVE_BOX_LT = ((-4200.0, -420.0, -8560.0), (-4096.0, -300.0, -8336.0))
DIVE_ARRIVAL_LT = (-3752.0, -1300.0, -8424.0)
# The flame cage round the exit (FlameCage, Door: 128 LT down at 15 when the Wyrde activates it): an invisible slab ring
# riding the cage keeps the party off ExitPoint (StartOn 0 in MM9; NPC338.scr :activate turns it on).
# The magic carpet's column (README: Deviations): MM9's carpet drifts the way the party faces as it rises; native
# movers do not carry the party sideways, so the carpet sits in the pit's corner under the statue's ledge (moved
# CARPET_SHIFT_LT from its DAT spot) and rises straight up to the ledge's height (12 LT); an invisible plank at that
# height bridges the last 90 LT to the ledge.
# Deviation (2026-11-08, the user's decision): the path's crouch slot into the tube room. MM9's party crouched through
# it (123 high); there is no crouch on land, so its ceiling is raised to give the party room (README Deviations).
# Native x range, y range, the ceiling's height and the raised one; every PhysicsBSP vertex there at that height moves.
CROUCH_SLOT = ((-13271.0, -13107.0), (-21627.0, -20972.0), -573.0, -470.0)
CARPET_SHIFT_LT = (476.0, 524.0)
# Lowered by this much (and its lift lengthened to match, overrides.yml move_lt) so a party that fell into the pit
# jumps onto it: its top was 123-144 over the pit floor, over the party's jump (90); now 46-67 (2026-11-09).
CARPET_DROP_LT = 30.0
CARPET_PLANK_LT = ((-7730.0, 12.0, -6730.0), (-7630.0, 12.0, -6630.0))
EXIT_SLAB_LT = {"x": (150.0, 234.0), "y": (-224.0, -100.0), "z": (2438.0, 2522.0)}
FIRE_DAMAGE = 10                    # FlameDamage PoisonGas: Damage 10 (per second)
SPIKE_DAMAGE = 100                  # Spikes1 PropDamager: DamagePerSecond 100, OneTimeDamage
NJAM_ROW = 9261                     # Njam the Meddler
WYRDE_ROW = 338                     # Peasant Elf Female C (the old importer's NPC 338 body: an elf woman)
GUARD_ROW = 9111                    # MM9 Guard A (the adventurer, MM9 guard.abc; WealthyTownGuard1 as on Guberland and Inventa)
VOLUMES = ["SpikeTrigger1", "TriggerDoor0", "TriggerAttack0", "TriggerBansheeOff0", "Trigger1", "ExitTrigger0",
           "ExitTrigger1", "ExitTrigger2", "ExitTrigger3"]
# Light colours: MM9 weights each Light by its BrightScale (0.1-1.0 here): BLV colour = colour x BrightScale, times the
# zone gain of LIGHT_GAINS (LT boxes x0, y0, z0, x1, y1, z1 -> RGB), fitted to MM9's DAT lightmaps with
# ../mm9r_common/hue_vs_lightmaps.py and hue_zones.py (README: Baked lighting).
# Fitted on the 16-sample draft (bounce 1, ambient 0.3): zone mean ours / MM9 per channel after the ambient floor.
# The player light's stand-in (README: Baked lighting). MM9 lights the passage's corridors only with its player light
# (WorldProperties PlayerLightOn), which leaves their lightmaps at 0.001-0.02; the native map has no player light, so
# matched exactly they render black. Each room below gets a sector minimum light level (against the map's `ambient` 30),
# which the bake turns into an ambient floor of max(0.18, (31 - level) / 31 x 0.97) x the profile's ambient_scale
# (0.16): level 0 about 0.16 (the unlit corridors), 8 about 0.12 (the canyon with its pit, the start room and the lake),
# 15 about 0.08 (the tube room, the ocean, the trap corridor). Revert: ROOM_LEVELS = [] and ambient_scale 0.2.
ROOM_LEVELS = [
    *[(point, 0) for point in ((-7646, -450, -4305), (-7548, -450, -4060), (-7344, -100, -8608), (-6272, -100, -7700),
                               (-3072, -250, -7000), (-2048, -300, -500), (-6016, -100, -4300), (-7728, -100, -8592),
                               (-7548, -350, -3950), (-1840, -100, -1150), (-5320, -200, -7000), (-6016, 50, -3700),
                               (-5000, 50, -3200))],
    *[(point, 8) for point in ((-8000, -400, -7500), (-7420, 50, 500))],
    *[(point, 15) for point in ((-4500, -300, -8300), (-2944, -1250, -8380), (-2176, -100, -1900))],
]
LIGHT_GAINS: list = [
    ((-8600, -1200, -3900, -6100, 0, -512), (1.0, 2.0, 2.1)),        # the lake: MM9's pure blue, twice ours
    ((-9400, -2600, -8450, -7300, 700, -6350), (1.3, 1.3, 1.3)),     # the canyon
    ((-7600, -300, -8800, -6000, 300, -7600), (0.25, 0.25, 0.25)),   # the mountain room and corridor: MM9 0.012
    ((-6400, -500, -4400, -3900, 600, -2800), (0.45, 0.45, 0.45)),   # the path's north part: MM9 0.018
    ((-5300, -1000, -8800, -3600, 300, -7700), (1.4, 1.4, 1.5)),     # the tube room
    ((-4100, -1700, -9300, -1900, -900, -7600), (1.6, 1.6, 1.5)),    # the ocean hall
    ((-2400, -400, -2080, -1700, 100, -600), (1.7, 1.7, 1.8)),       # the spike-trap corridor
    ((-2300, -500, -600, -1700, 0, 1050), (0.65, 0.65, 0.65)),       # the exit room
    ((-2100, -300, 1050, -500, 1000, 2900), (1.45, 1.45, 1.45)),     # the curved corridor
    ((-500, -300, 2150, 300, 600, 2900), (2.6, 2.2, 2.2)),           # the Wyrde's room: MM9's warm 0.33 / 0.22
]


def njam_speed() -> int:
    """Njam's row speed (monster_data.txt Spd): the cameo walks."""
    table = ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"
    for line in table.read_text(encoding="latin-1").splitlines():
        cells = line.split("\t")
        if cells[0] == str(NJAM_ROW):
            return int(cells[13])
    raise SystemExit(f"monster_data.txt has no row {NJAM_ROW}")


def swimming(build) -> bool:
    """MM9's water volumes, swum in (the shared rule, dungeon/water.py `swimming`; module constants, "Water")."""
    return water.swimming(build.project)


def volume_top_lt(source, model: str) -> float:
    """A liquid volume's top (LT y): its brush's highest up-facing polygon (dungeon/water.py pieces)."""
    return max(piece["top"] for piece in water.pieces_lt(source.models[model]))


class AirTest:
    """Whether a LT point lies in air: the first polygon straight above faces down at it (Dook's Castle's test),
    with the polygons' xz bounds as arrays for speed."""
    def __init__(self, polygons):
        self.polygons = [p for p in polygons if abs(p.normal[1]) > 1e-6]
        self.low = np.array([p.points.min(0) for p in self.polygons])
        self.high = np.array([p.points.max(0) for p in self.polygons])

    def __call__(self, x, y, z) -> bool:
        idx = np.nonzero((self.low[:, 0] <= x) & (x <= self.high[:, 0]) & (self.low[:, 2] <= z) & (z <= self.high[:, 2])
                         & (self.high[:, 1] >= y))[0]
        best, facing = None, False
        for i in idx:
            polygon = self.polygons[i]
            n = polygon.normal
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


def raise_crouch_slot(project, polygons: list) -> None:
    """CROUCH_SLOT: the slot's ceiling vertices (and the walls' ends that share them) raised, in place."""
    (x0, x1), (y0, y1), ceiling, raised = CROUCH_SLOT
    moved = 0
    for polygon in polygons:
        if polygon.model != "PhysicsBSP":
            continue
        native = project.native(polygon.points)
        hit = ((np.abs(native[:, 2] - ceiling) < 1.0) & (native[:, 0] > x0 - 1.0) & (native[:, 0] < x1 + 1.0)
               & (native[:, 1] > y0 - 1.0) & (native[:, 1] < y1 + 1.0))
        if not hit.any():
            continue
        points = polygon.points.copy()
        for index in np.flatnonzero(hit):
            points[index] = project.lt_from_native((native[index, 0], native[index, 1], raised))
            polygon.keys[index] = tuple(np.round(points[index], 1))
            moved += 1
        polygon.points = points
    if moved == 0:
        raise SystemExit("the crouch slot's ceiling was not found (CROUCH_SLOT)")


def box_polygons(low, high, template: Polygon, model: str, role: str = "invisible") -> list:
    """The six faces of an axis-aligned LT box, facing out, with the template's texture and flags."""
    (x0, y0, z0), (x1, y1, z1) = low, high
    corners = {"x0": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
               "x1": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
               "y0": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
               "y1": [(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)],
               "z0": [(x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)],
               "z1": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]}
    centre = np.array([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    out = []
    for ring in corners.values():
        points = np.array(ring, float)
        polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], template.texture, template.mapping,
                          template.flags, model, role, notes=dict(template.notes))
        if np.dot(polygon.normal, points.mean(0) - centre) < 0:
            points = points[::-1]
            polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], template.texture, template.mapping,
                              template.flags, model, role, notes=dict(template.notes))
        out.append(polygon)
    return out


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


class DarkPassageway(dungeon.Hooks):
    generator = "mm9r_darkpassageway"
    mover_events = {"ElevatorObj": (EV_CARPET, "click"), "Painting": (EV_PAINTING, "click"),
                    "Switch": (EV_SWITCH_EXIT, "click"), "TeleportDoor1": (EV_TELEPORT_DOOR1, "click"),
                    **{name: (event, "click") for name, event in EV_LOCKED.items()}}

    # --- before the voxels and movers ---------------------------------------------------------------------------
    def extra_seeds(self, build) -> list:
        """The flame cage carries an invisible slab ring round ExitPoint (the exit's gate: it sinks with the cage)."""
        source = build.source
        template = next(p for p in source.polygons("WorldObject4") if p.role == "invisible")
        original = source.polygons

        def polygons(name):
            out = original(name)
            if name == "ElevatorObj":
                shift = np.array([CARPET_SHIFT_LT[0], -CARPET_DROP_LT, CARPET_SHIFT_LT[1]])
                return [Polygon(p.points + shift, p.keys, p.texture, (p.mapping[0] + shift,) + tuple(p.mapping[1:]),
                                p.flags, p.model, p.role, notes=dict(p.notes)) for p in out]
            if name != "FlameCage":
                return out
            box = EXIT_SLAB_LT
            return out + box_polygons((box["x"][0], box["y"][0], box["z"][0]), (box["x"][1], box["y"][1], box["z"][1]),
                                      template, name)
        source.polygons = polygons
        return super().extra_seeds(build)

    def edit_polygons(self, build, polygons: list) -> list:
        """The three water volumes' surfaces as tiles over the air at the surface (32 LT): solid wading faces, or
        with `swim: true` non-solid surfaces at the volumes' own tops (README "Water"). Liquid faces (scene hook)."""
        source = build.source
        template = next(p for p in source.polygons("WorldObject4") if p.role == "invisible")
        raise_crouch_slot(build.project, polygons)
        air = AirTest(polygons)
        out = list(polygons)
        (x0, y, z0), (x1, _, z1) = CARPET_PLANK_LT
        out.append(flat([(x0, z0), (x0, z1), (x1, z1), (x1, z0)], y, template, template.texture, dict(template.notes),
                        "CarpetPlank", "invisible", template.flags))
        self.water_faces = {}
        swim = swimming(build)
        if swim:
            model, low, high, (y0, y1) = SHAFT_SKY
            sky = [p for p in out if p.model == model and p.normal[1] < -0.99 and y0 < p.points[:, 1].mean() < y1
                   and (low <= p.points[:, [0, 2]].mean(0)).all() and (p.points[:, [0, 2]].mean(0) <= high).all()]
            if len(sky) != 1:
                raise SystemExit(f"the shaft's sky polygon: {len(sky)} found")
            sky[0].role = "nonsolid"
        for model, y, texture, _ in WATER:
            if swim:
                y = volume_top_lt(source, model)
            points = np.array(source.models[model].points, float)
            (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
            alias = source.aliases[texture]
            count = 0
            for row in np.arange(z0, z1, WATER_TILE):
                run = None
                for column in np.arange(x0, x1 + WATER_TILE, WATER_TILE):
                    wet = column < x1 and sum(air(min(column + u * WATER_TILE, x1 - 0.5), y + 1,
                                                  min(row + v * WATER_TILE, z1 - 0.5))
                                              for u in (0.05, 0.5, 0.95) for v in (0.05, 0.5, 0.95)) >= 5
                    if wet and run is None:
                        run = column
                    elif not wet and run is not None:
                        top = min(row + WATER_TILE, z1)
                        ring = [(run, row), (run, top), (column, top), (column, row)]
                        out.append(flat(ring, y, template, texture, {"width": alias["width"], "height": alias["height"]},
                                        model, "nonsolid" if swim else "static", 0x1089))
                        count += 1
                        run = None
            self.water_faces[model] = count
        return out

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        self.scale_lights(build)
        events = {**{name: event for name, event in EV_SWITCH.items()}, "SwitchCreature5": EV_RESET_STATUE,
                  "SwitchCreature4": EV_CANYON_STATUE, "Gemstone": EV_GEMSTONE}
        # the scroll Prop38 (Givetake.scr) is a world item (dungeon/pickups.py: item 483)
        cogs = {**{name: STATUE_COG + 2 * k for name, k in STATUE_BRIDGE.items()},
                "SwitchCreature5": COG_RESET_STATUE, "SwitchCreature4": COG_CANYON_STATUE}
        self.statue_clips = {}
        if PROPS.exists():
            content.props(PROPS, events=events, cogs=cogs)
            import json
            for entry in json.loads(PROPS.read_text()):
                if entry["source_name"] in SWITCH_STATUES or entry["source_name"] == "SwitchCreature4":
                    self.statue_clips[entry["source_name"]] = statue_clips(entry["prop"])
                k = STATUE_BRIDGE.get(entry["source_name"])
                if k is None:
                    continue
                shift = (-160.0 if BRIDGE_BUILT_UP[k] else 160.0) * SCALE
                content.entity(f"{entry['source_name']}_Moved", entry["decoration"],
                               (entry["x"], entry["y"], entry["z"] + shift), entry["yaw_degrees"],
                               primary=STATUE_COG + 2 * k + 1, secondary=events[entry["source_name"]])
        import json
        for entry in json.loads(MIRRORS_JSON.read_text()):
            k = int(entry["source_name"][len("Mirror"):])
            content.entity(entry["source_name"], entry["decoration"], (entry["x"], entry["y"], entry["z"]),
                           entry["yaw_degrees"], primary=MIRROR_COG + k, secondary=EV_MIRROR[entry["source_name"]])
        self.place_perception_hints(build)
        levels = {content.owner(np.array(point, float)): level for point, level in ROOM_LEVELS}
        self.room_ambient = levels
        write = build.package.write

        def write_with_levels(*args, **kwargs):
            for room in build.package.metadata["rooms"]:
                if room["id"] in levels:
                    room["min_ambient_light_level"] = levels[room["id"]]
            return write(*args, **kwargs)
        build.package.write = write_with_levels
        self.boxes = {}
        for name in VOLUMES + list(TELEPORTERS) + ["FlameDamage"]:
            p = source.properties(name)
            dims = np.array(p.get("Dims") or [0, 0, 0], float)
            if name == "FlameDamage":
                points = np.array(source.models["FlameDamage"].points, float)
                low, high = points.min(0), points.max(0)
            else:
                centre = np.array(p["Pos"], float)
                low, high = centre - dims, centre + dims
            low, high = project.native(low), project.native(high)
            self.boxes[name] = [np.minimum(low, high).round().astype(int).tolist(),
                                np.maximum(low, high).round().astype(int).tolist()]
        low, high = project.native(DIVE_BOX_LT[0]), project.native(DIVE_BOX_LT[1])
        self.boxes["Dive"] = [np.minimum(low, high).round().astype(int).tolist(),
                              np.maximum(low, high).round().astype(int).tolist()]
        low, high = project.native(SHAFT_EXIT_LT[0]), project.native(SHAFT_EXIT_LT[1])
        self.boxes["ShaftExit"] = [np.minimum(low, high).round().astype(int).tolist(),
                                   np.maximum(low, high).round().astype(int).tolist()]
        self.shaft_drop = project.native(SHAFT_DROP_LT).round().astype(int).tolist()
        # Teleport arrivals: on the floor under the arrival object, facing as it does (UseRotation).
        self.arrivals = {}
        for name, arrival in TELEPORTERS.items():
            p = source.properties(arrival)
            floor = content.floor_at(p["Pos"][0], p["Pos"][2], p["Pos"][1] + 20)
            point = project.native([p["Pos"][0], floor, p["Pos"][2]]).round().astype(int).tolist()
            point[2] += 2
            self.arrivals[name] = (point, int(round(facing_degrees(p.get("Rotation")) / 360 * 2048)) % 2048)
        floor = content.floor_at(DIVE_ARRIVAL_LT[0], DIVE_ARRIVAL_LT[2], DIVE_ARRIVAL_LT[1] + 20)
        dive = project.native([DIVE_ARRIVAL_LT[0], floor, DIVE_ARRIVAL_LT[2]]).round().astype(int).tolist()
        self.dive_arrival = [dive[0], dive[1], dive[2] + 2]
        # The banshee eyes (Shooters) and the light beams' points (mirrors, gemstone, GemLight0).
        self.eyes = {name: project.native(source.properties(name)["Pos"]).round().astype(int).tolist() for name in EYES}
        self.beam_points = {name: project.native(source.properties(name)["Pos"]).round().astype(int).tolist()
                            for name in ["GemLight0", "Gemstone", *MIRRORS, "BeamReceiver1"]}
        self.mirror_facing = {}
        for name in MIRRORS:
            # The direction its counter 0 sends the light: the object's own facing (its DAT Rotation yaw; LithTech's
            # forward is (sin yaw, 0, cos yaw), native (x, z) -> angle 90 - yaw), which PassageLaser.scr's GetFaceDir
            # reads; PassageMirror.scr turns it clockwise 10 degrees a click. Not its glass: the DAT keeps the brush in
            # world space, the glass of all four facing the same way, and the targets (330, 10, 340, 50) aim the light
            # at the next mirror (and Mirror3's at BeamReceiver1) only from these facings (0, 180, 0, 180).
            yaw = math.degrees(float(source.properties(name)["Rotation"][1]))
            self.mirror_facing[name] = 90.0 - yaw

    def scale_lights(self, build) -> None:
        """BLV light colour = MM9 colour x BrightScale (Ruined Temple lesson); the bake-only lights the same, with the
        typical kept light's strength (Training Hall lesson)."""
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
        kept = sorted(light["bright_scale"] for light in build.lights if light["kept"])
        typical = kept[len(kept) // 2] if kept else 1.0
        for light in build.lights:
            light["colour_in_blv"] = [int(min(255, round(c * f))) for c, f in zip(light["colour"], gains[light["name"]])]
            if not light["kept"]:
                light["mm9_colour"], light["mm9_bright_scale"] = light["colour"], light["bright_scale"]
                light["colour"] = light["colour_in_blv"]
                light["bright_scale"] = typical

    def place_perception_hints(self, build) -> None:
        """Each PerceptionBrush's visible polygons (Perception.spr) as untouchable translucent faces with a cog
        (Training Hall's route)."""
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
                # A hint stands in front of what it marks and takes the click (Training Hall lesson): it runs the
                # marked door's (or the painting's) click event.
                group = HINT_TARGET.get(name)
                event = next((mv["event"] for mv in build.movers if mv["group"] == group and mv.get("event")), 0)
                if event:
                    surface["trigger"] = {"event_id": event, "type": "click"}
                package.metadata["surfaces"].append(surface)
                self.hint_faces += 1
            self.hints[name] = PERCEPTION_COG + k
            self.hint_difficulty[PERCEPTION_COG + k] = difficulties[lower]

    # --- actors -----------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor_index, self.placement_notes = [], {}, {}
        for o in source.objects:
            name, p = o["name"], o["properties"]
            if o["class"] not in build.project.monster_classes:
                continue
            base = bases.get(name)
            friendly, changes = False, {}
            if o["class"] == "WyrdeoftheKnown":
                base = {"name": "Wyrde of the Unknown", "attributes": 0, "hp": 100, "hostility_type": 0,
                        "monster_info_id": WYRDE_ROW, "monster_id": WYRDE_ROW, "radius": 40, "height": 180,
                        "move_speed": 0}
                friendly = True
            elif o["class"] == "WealthyTownGuard1":
                base = {"name": "Adventurer", "attributes": 0, "hp": 60, "hostility_type": 0,
                        "monster_info_id": GUARD_ROW, "monster_id": GUARD_ROW, "radius": 40, "height": 180,
                        "move_speed": 0}
                friendly = True
            if base is None:
                continue
            if not friendly:
                changes = placed_body(base["monster_id"], p)    # MM9's body: the row's, or at the DAT's own Scale
            query = p["Pos"][1] + 24
            if name in ("Specter9", "Specter10"):
                query = 40.0                         # inside the ramp's slab: on the ramp above
                self.placement_notes[name] = "on the ramp over the slab MM9 hides them in"
            if o["class"] in SEA_MONSTER_WATER and swimming(build):
                query = None                         # the bed under MM9's position (the room's sector)
            elif o["class"] in SEA_MONSTER_WATER:
                surface = next(y for model, y, _, _ in WATER
                               if model == ("TubeRoomWater0" if o["class"] == "SeaMonsterMale" else "Ocean"))
                query = surface + 40
                self.placement_notes[name] = "on the water surface (no swimming)"
            if p.get("Gravity") and p["Pos"][1] > 0:
                self.placement_notes[name] = "MM9 drops it from y 64 onto the floor under it"
            record = content.actor(o, base, sector_of_room, floor_query_lt=query, friendly=friendly, **changes)
            if o["class"] in SEA_MONSTER_WATER and swimming(build):
                # a swimmer: content.actor floats it at MM9's box centre in its volume (water.swimmer_foot)
                self.placement_notes[name] = f"a swimmer in {SEA_MONSTER_WATER[o['class']]} (box centre at MM9's)"
            record["mm9_source_object_index"] = o["index"]
            if o["class"] == "WyrdeoftheKnown":
                record["mm9_rude_id"] = RUDE_WYRDE
                record["immobile"] = True
            if o["class"] == "WealthyTownGuard1":
                record["immobile"] = True
            if name in CAGES or name == "ColloidalWarrior0":
                record["dormant"] = True             # DP_CageMonster.scr waits for 'go'; DarkP_Warrior.scr for HitNpc
            self.actor_index[name] = record["actor_index"]
            out.append(record)
        # Njam the Meddler's cameo (SpawnNjamCameo.scr on SpawnNjam0): hidden until Trigger1 spawns him.
        njam = source.by_name["spawnnjam0"]
        njam_base = {"name": "Njam the Meddler", "attributes": 0, "hp": 6600, "hostility_type": 0,
                     "monster_info_id": NJAM_ROW, "monster_id": NJAM_ROW, "radius": 40, "height": 180,
                     "move_speed": njam_speed()}
        record = content.actor(njam, njam_base, sector_of_room, hidden=True, friendly=True,
                               floor_query_lt=njam["properties"]["Pos"][1] + 24)
        # SpawnNjamCameo.scr spawns him with NjamCameo.scr: his behaviour's cameo mode (worlds/mm9/behaviors/njam.lua)
        # and MM9's wander; he stands until the map's Lua shows him (evt.SetActorImmobile)
        record["mm9_ai"] = content.mm9_ai({"ScriptName": "scripts\\NjamCameo.scr"}, NJAM_ROW - 9000)
        record["immobile"] = True
        self.actor_index["Njam"] = record["actor_index"]
        out.append(record)
        return out

    # --- map script -------------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Dark Passageway")
        script.doors()
        script.chests()
        lines = script.lines
        hint, actor = self.hints, self.actor_index
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
            "and y <= b[2][2] + 37 and z + 170 >= b[1][3] and z <= b[2][3] + 37 end",
            "local function hintOff(cog) set(\"HintOff\" .. cog, 1); evt.SetFacetBit(cog, FacetBits.Invisible, true) end",
            "local function locked() evt.StatusText(\"The door is locked.\") end",
            "",
        ]
        # --- the bridge puzzle
        tables = []
        for letter in "ABCD":
            tables.append(f"{letter} = {{" + ", ".join(f"[{k}] = {v}" for k, v in sorted(PUZZLE[letter].items())) + "}")
        lines += [
            "-- The bridge puzzle (DarkP_bridgepuzzle.scr, DarkP_initMyStuff.inc: 'Sequence to completion - ADCBDCBA').",
            "-- The state is a 5-bit number, bit (4 - k) set while bridge k is down; each statue (DarkP_RaisingSwitch.scr",
            "-- \"PuzzleManager0 Hit<X>\") maps the state through its table and the bridges whose bit changed move",
            "-- (DarkP_RaisingBridge.scr: 160 LT between their markers at 180 LT/s). State 0 (every bridge up) solves it:",
            "-- the statues stop and TeleportDoor0 unlocks and opens. The terror statue (DarkP_BridgeReset.scr) resets it.",
            f"local PUZZLE = {{{', '.join(tables)}}}",
            "local BUILT_UP = {" + ", ".join("true" if BRIDGE_BUILT_UP[k] else "false" for k in range(5)) + "}",
            "local function puzzleState() if var(\"PuzzleSet\") == 0 then return " + str(PUZZLE_START) + " end "
            "return var(\"Puzzle\") end",
            "local function placeBridges(state)",
            "    for k = 0, 4 do",
            "        local down = math.floor(state / 2 ^ (4 - k)) % 2 == 1",
            "        -- bridges 0 and 4 are built up (open = down), 1-3 built down (open = up)",
            "        local moved = down == BUILT_UP[k + 1]",
            "        if moved then openG(\"Bridge\" .. k) else closeG(\"Bridge\" .. k) end",
            f"        if k < 4 then evt.SetSprite({STATUE_COG} + 2 * k, not moved); evt.SetSprite({STATUE_COG} + 2 * k + 1, moved) end",
            "    end",
            "end",
            "local function setPuzzle(state)",
            "    local old = puzzleState()",
            "    set(\"PuzzleSet\", 1); set(\"Puzzle\", state)",
            "    if old ~= state then sound(\"spells/eshield.wav\") end",
            "    placeBridges(state)",
            "    if state == 0 and var(\"PuzzleSolved\") == 0 then",
            "        set(\"PuzzleSolved\", 1)",
            "        openG(\"TeleportDoor0\")",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            "    end",
            "end",
        ]
        statues = []
        for k, (name, (letter, start, use)) in enumerate(SWITCH_STATUES.items()):
            clips = self.statue_clips[name]
            assert use in clips, f"{name}: no {use} clip"
            cogs = [STATUE_COG + 2 * STATUE_BRIDGE[name], STATUE_COG + 2 * STATUE_BRIDGE[name] + 1] \
                if name in STATUE_BRIDGE else [COG_RESET_STATUE]
            fields = [f"cogs = {{{', '.join(map(str, cogs))}}}", f"hit = \"{letter}\"" if letter else None,
                      f"start = \"{start}\"" if start in clips else None, f"use = \"{use}\"",
                      f"seconds = {clips[use]:.3f}"]
            statues.append(f"    [{k}] = {{{', '.join(f for f in fields if f)}}},   -- {name}")
        lines += [
            "-- The statues (animated decorations; each puzzle statue and its moved twin play together): at start",
            "-- PlayAnim fidget1 (the banshee awareAir, which BANSHEE.abc lacks: it stands at rest), its end held; a Use",
            "-- plays fidget1 (the banshee FidgetAir1) with EnchantItem.wav, and only the clip's end (PlayAnim's callback",
            "-- :TriggerScrObj) tells the manager: Hit<X>, or Reset for the terror (DarkP_BridgeReset.scr). A click while",
            "-- the clip plays is ignored (MM9 restarts it, still one trigger). The solved puzzle's Stop removes the Use.",
            "local STATUES = {",
            *statues,
            "}",
            "local function showStatue(k)   -- the pose it holds: the end of the last clip it played",
            "    local s = STATUES[k]",
            "    local clip = var(\"StatueUsed\" .. k) == 1 and s.use or s.start",
            "    if clip then for _, cog in ipairs(s.cogs) do evt.PlayDecorationClip(cog, clip, \"end\") end end",
            "end",
            "local function useStatue(k)   -- :MoveMe",
            "    if var(\"PuzzleSolved\") == 1 or var(\"StatueBusy\" .. k) == 1 then return end",
            "    local s = STATUES[k]",
            "    set(\"StatueBusy\" .. k, 1); set(\"StatueUsed\" .. k, 1)",
            "    for _, cog in ipairs(s.cogs) do evt.PlayDecorationClip(cog, s.use) end",
            "    sound(\"spells/EnchantItem.wav\")",
            f"    arm({T_STATUE} + k, s.seconds)",
            "end",
            "local function statueDone(k)   -- :TriggerScrObj",
            "    set(\"StatueBusy\" .. k, 0)",
            "    if var(\"PuzzleSolved\") == 1 then return end",
            "    local s = STATUES[k]",
            f"    setPuzzle(s.hit and (PUZZLE[s.hit][puzzleState()] or 0) or {PUZZLE_START})",
            "end",
        ]
        for k, name in enumerate(SWITCH_STATUES):
            event = EV_SWITCH.get(name, EV_RESET_STATUE)
            lines += [f"handlers[{event}] = function() useStatue({k}) end   -- {name}",
                      f"handlers[{T_STATUE + k}] = function() if fired({T_STATUE + k}) then statueDone({k}) end end"]
        lines += [
            f"handlers[{EV_LOCKED['TeleportDoor0']}] = function()   -- TeleportDoor0: Locked until the puzzle is solved",
            "    if var(\"PuzzleSolved\") == 0 or var(\"TeleportDoor0Locked\") == 1 then locked() return end",
            "    openG(\"TeleportDoor0\")",
            "end",
            "",
        ]
        # --- teleporters
        arrivals = ", ".join(f"{name} = {{{lua.point(p)}, {yaw}}}" for name, (p, yaw) in self.arrivals.items())
        lines += [
            "-- The teleporters (MM9 Teleporter objects, TouchNotify: the party walking into the box goes to its",
            "-- TeleportDestination, facing the arrival's way, UseRotation).",
            f"local ARRIVALS = {{{arrivals}}}",
            "local function teleport(name)",
            "    local a = ARRIVALS[name]",
            "    set(\"Teleported\", var(\"Teleported\") + 1); set(\"LastTeleport\" .. name, var(\"LastTeleport\" .. name) + 1)",
            "    sound(\"magic/teleport.wav\")",
            "    evt.MoveToMap(a[1][1], a[1][2], a[1][3], a[2], 0, 0, 0, 0)",
            "end",
            "",
        ]
        # --- canyon
        eyes = ", ".join(f"{lua.point(self.eyes[name])}" for name in EYES)
        canyon = self.statue_clips["SwitchCreature4"]
        steps = ", ".join(f"{{\"{clip}\", {canyon[clip]:.3f}}}" for clip, _ in CANYON_CLIPS)
        lines += [
            "-- The canyon (DarkP_CanyonSwitch.scr on the ice statue SwitchCreature4, an animated decoration): a click",
            "-- plays Hattack2, Taunt, Rattack1 and Fidget1 in turn, each with EnchantItem.wav; each clip's end wakes a",
            "-- pair of the banshee statues' eyes (BansheeAEye0/1, 2/3, 6/7, then 4/5: Shooters, KBYellowLine, 5 damage,",
            "-- one shot a second at the party), the last one stops the statue (holding Fidget1's end), removes its Use",
            "-- and unlocks and opens the canyon doors (CanyonDoorL0/R0). At start it plays CastSpell, which",
            "-- SKELETONWARRIOR.abc lacks: it stands at rest. TriggerBansheeOff0 by the mountain teleporter turns every",
            "-- eye off. An eye's shot strikes the party in its path (FireMissile's strikesParty).",
            f"local EYES = {{{eyes}}}   -- in the order they wake",
            f"local CANYON = {{{steps}}}",
            "local function shoot(e)",
            "    local x, y, z = evt.GetPartyPosition()",
            "    z = z + 100",
            "    local dx, dy, dz = x - e[1], y - e[2], z - e[3]",
            "    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))",
            "    if length > 6000 then return end",
            "    local k = math.max(64 / length, 0.05)",
            f"    local shot = evt.FireMissile(\"Fire\", e[1] + dx * k, e[2] + dy * k, e[3] + dz * k, x, y, z, {EYE_DAMAGE}, \"Energy\", 0, 0, true)",
            "    if shot then MM9.launchSound(\"KBYellowLine\", e[1], e[2], e[3]) end",
            "    set(\"EyeShots\", var(\"EyeShots\") + (shot and 1 or 0))",
            "end",
            f"handlers[{T_EYES}] = function()",
            f"    evt.StartTimer({T_EYES}, seconds(1))",
            "    local on = var(\"EyesOn\")",
            "    if var(\"EyesOff\") == 1 or on == 0 then return end",
            "    for k = 1, math.min(on, 8) do shoot(EYES[k]) end",
            "end",
            "local function canyonClip(step)   -- :OnUse, :AnimateA-C",
            "    set(\"CanyonStep\", step)",
            "    sound(\"spells/EnchantItem.wav\")",
            f"    evt.PlayDecorationClip({COG_CANYON_STATUE}, CANYON[step][1])",
            f"    arm({T_CANYON}, CANYON[step][2])",
            "end",
            "local function canyonOpen()   -- :Stop, :CanyonDoors",
            "    set(\"EyesOn\", 8); set(\"CanyonOpen\", 1); openG(\"CanyonDoor\")",
            "end",
            f"handlers[{T_CANYON}] = function()   -- a clip's end: a pair of eyes wakes, then the next clip",
            f"    if not fired({T_CANYON}) then return end",
            "    set(\"EyesOn\", math.min(8, var(\"EyesOn\") + 2))",
            "    if var(\"CanyonStep\") < #CANYON then canyonClip(var(\"CanyonStep\") + 1) else canyonOpen() end",
            "end",
            f"handlers[{EV_CANYON_STATUE}] = function()   -- SwitchCreature4 :OnUse",
            "    if var(\"CanyonUsed\") == 1 then return end",
            "    set(\"CanyonUsed\", 1)",
            "    canyonClip(1)",
            "end",
            f"handlers[{EV_LOCKED['CanyonDoor']}] = function()   -- CanyonDoorL0/R0: Locked until the statue's call",
            "    if var(\"CanyonOpen\") == 0 then locked() return end",
            "    openG(\"CanyonDoor\")",
            "end",
            "",
            "-- The magic carpet (MagicCarpet.scr \"0\" on ElevatorObj, at the bottom of the canyon's pit): a click lifts it",
            "-- at 500 LT/s; MM9 also drifts it the way the party faces (800 LT/s) and drops it back when it reaches y 0",
            "-- or sticks. Native: a lift straight up to y 0 (README: Deviations); 8 s at the top, then it sinks back.",
            f"handlers[{EV_CARPET}] = function()",
            "    if var(\"CarpetUp\") == 1 then return end",
            "    set(\"CarpetUp\", 1); set(\"CarpetRides\", var(\"CarpetRides\") + 1)",
            "    openG(\"ElevatorObj\")",
            f"    arm({T_CARPET}, 2500 / 500 + 8)",
            "end",
            f"handlers[{T_CARPET}] = function()",
            f"    if not fired({T_CARPET}) then return end",
            "    sound(\"default.wav\")",
            "    closeG(\"ElevatorObj\"); set(\"CarpetUp\", 0)",
            "end",
            "",
        ]
        # --- forest
        lines += [
            "-- The forest ambush: TriggerDoor0 unlocks ForestDoor0 (AutoTrigger: it opens as the party comes); in the forest",
            "-- TriggerAttack0 slams and locks it behind the party, and the Colloidal Warrior (DarkP_Warrior.scr :HitNpc)",
            "-- strikes the adventurer down (DarkP_NPCDie.scr) and turns on the party. Its death unlocks TeleportDoor1",
            "-- (DeathTriggerTarget); opening TeleportDoor1 locks TeleportDoor0 (its OpenTrigger).",
            f"local WARRIOR, ADVENTURER = {actor['ColloidalWarrior0']}, {actor['NPCAdventurer0']}",
            f"handlers[{T_WARRIOR}] = function()",
            f"    if not fired({T_WARRIOR}) then return end",
            "    -- TriggerAttack0's HitNpc: a warrior killed before the ambush takes none (the adventurer lives), and a",
            "    -- dead adventurer takes no Destroy (MM9.receives)",
            "    if not MM9.receives(\"darkpassageway\", \"ColloidalWarrior0\", \"HitNpc\", WARRIOR) then return end",
            "    sound(\"weapons/swordhit01.wav\")",
            "    if MM9.receives(\"darkpassageway\", \"NPCAdventurer0\", \"destroy\", ADVENTURER) then",
            "        MM9.removeActor(ADVENTURER); set(\"AdventurerDead\", 1)",
            "    end",
            "    evt.WakeActor(WARRIOR)",
            "end",
            f"handlers[{EV_LOCKED['ForestDoor0']}] = function()",
            "    if var(\"ForestUnlocked\") == 0 or var(\"ForestLocked\") == 1 then locked() return end",
            "    openG(\"ForestDoor0\")",
            "end",
            f"handlers[{EV_TELEPORT_DOOR1}] = function()   -- TeleportDoor1: Locked until the warrior dies",
            "    if var(\"WarriorDead\") == 0 then locked() return end",
            "    openG(\"TeleportDoor1\"); set(\"TeleportDoor0Locked\", 1)",
            "end",
            f"handlers[{KILL_HOOK}] = function(context)",
            "    if context.monsterId == WARRIOR or context.actorIndex == WARRIOR then set(\"WarriorDead\", 1) end",
            f"    if context.monsterId == {actor['SeaMonsterFemale0']} or context.actorIndex == {actor['SeaMonsterFemale0']} then",
            "        set(\"CageBroken\", 1); openG(\"DB_TeleporterCage0\"); sound(\"events/clap01.wav\")",
            "    end",
            "end",
            "",
        ]
        # --- painting
        lines += [
            "-- The painting (RotatingDoor, 90 about y; its OpenTriggers open DoubleDoorL40 (and R40 with it), lock it",
            "-- and turn PerceptionBrush1 off): the hidden room with TreasureChest0-2 behind it.",
            f"handlers[{EV_PAINTING}] = function()",
            "    if var(\"PaintingOpen\") == 1 then return end",
            "    set(\"PaintingOpen\", 1)",
            "    openG(\"Painting\"); openG(\"DoubleDoor40\")",
            f"    hintOff({hint['PerceptionBrush1']})",
            "end",
            "",
        ]
        # --- mirrors
        mirror_rows = []
        for name, (angle, nxt) in MIRRORS.items():
            mirror_rows.append(f"{{name = \"{name}\", target = {angle // 10}, at = {lua.point(self.beam_points[name])}, "
                               f"next = {lua.point(self.beam_points[nxt])}, facing = {self.mirror_facing[name]:.1f}}}")
        cages = ", ".join(f"{{name = \"{c}\", actor = {actor[c]}, door = \"{d}\"}}" for c, d in CAGES.items())
        lines += [
            "-- The mirror puzzle in the desert (PassageMirror.scr \"<angle> <next> <beam>\", PassageLaser.scr,",
            "-- PassageGemstone.scr \"CageTerror 0 5\"): a click on a mirror turns it 10 degrees clockwise (its counter + 1,",
            "-- mod 36). A click on the gemstone shines its light (GemLight0) at Mirror0; a mirror whose counter is its",
            "-- target angle / 10 passes it on to the next, the last to BeamReceiver1, and the gemstone then releases the",
            "-- six cage terrors (their cage doors Door1-6 unlock and open, they come out after the door's open time) and",
            "-- opens",
            "-- DesertDoor0. Each mirror is a decoration (cog MIRROR_COG + k) turned by evt.AimDecoration, 10 degrees a",
            "-- click at MM9's 180 degrees a second: MirrorTurns<k> counts every click (the aim keeps turning the same way",
            "-- past a full turn), and the map's load puts each back at its angle (decoration aims are not saved).",
            f"local MIRRORS = {{{', '.join(mirror_rows)}}}",
            f"local GEM_LIGHT = {lua.point(self.beam_points['GemLight0'])}",
            f"local CAGES = {{{cages}}}",
            "local function mirrorCount(k) return var(\"Mirror\" .. k) end",
            f"local function aimMirror(k, speed) evt.AimDecoration({MIRROR_COG} + k - 1, -10 * var(\"MirrorTurns\" .. k), speed) end",
            "local function beamFrom(k)",
            "    local m = MIRRORS[k]",
            "    local a = math.rad(m.facing - mirrorCount(k) * 10)",
            "    return {m.at[1] + math.cos(a) * 3000, m.at[2] + math.sin(a) * 3000, m.at[3]}",
            "end",
            "local function release()",
            "    if var(\"CagesOpen\") == 1 then return end",
            "    set(\"CagesOpen\", 1)",
            "    sound(\"spells/enchantitem.wav\"); sound(\"door/doorslidestone.wav\")",
            "    -- each terror's go (DP_CageMonster.scr :OpenCage unlocks and opens its own door): a dead one takes none",
            "    for _, c in ipairs(CAGES) do",
            "        if MM9.receives(\"darkpassageway\", c.name, \"go\", c.actor) then openG(c.door) end",
            "    end",
            "    openG(\"DesertDoor0\")",
            f"    arm({T_CAGES}, 192 / 60)",
            "end",
            f"handlers[{T_CAGES}] = function()   -- DP_CageMonster.scr :LeaveCage after the door's open time",
            f"    if not fired({T_CAGES}) then return end",
            "    for _, c in ipairs(CAGES) do evt.WakeActor(c.actor) end",
            "end",
            f"handlers[{EV_GEMSTONE}] = function()   -- Gemstone :ShineLight",
            "    set(\"Shines\", var(\"Shines\") + 1)",
            "    sound(\"spells/enchantitem.wav\")",
            "    local from = GEM_LIGHT",
            "    for k = 1, 4 do",
            "        local m = MIRRORS[k]",
            "        evt.Beam(\"PassageBeam\" .. k, \"openyamm:fx/arc_beam\", from[1], from[2], from[3], m.at[1], m.at[2], m.at[3], 1.5)",
            "        -- PassageMirror.scr :GiveFocus: a mirror turned 70-290 degrees from its facing sends no light on",
            "        local count = mirrorCount(k)",
            "        if count > 6 and count < 30 then return end",
            "        if count ~= m.target then",
            "            local to = beamFrom(k)",
            "            evt.Beam(\"PassageBeamLost\", \"openyamm:fx/arc_beam\", m.at[1], m.at[2], m.at[3], to[1], to[2], to[3], 1.5)",
            "            return",
            "        end",
            "        from = m.at",
            "    end",
            f"    local g = {lua.point(self.beam_points['BeamReceiver1'])}   -- Mirror3's light ends at BeamReceiver1",
            "    evt.Beam(\"PassageBeam5\", \"openyamm:fx/arc_beam\", from[1], from[2], from[3], g[1], g[2], g[3], 1.5)",
            "    release()",
            "end",
        ]
        for k, name in enumerate(MIRRORS):
            lines.append(f"handlers[{EV_MIRROR[name]}] = function()   -- {name} :Rotate")
            lines.append(f"    set(\"Mirror{k + 1}\", (var(\"Mirror{k + 1}\") + 1) % 36)")
            lines.append(f"    set(\"MirrorTurns{k + 1}\", var(\"MirrorTurns{k + 1}\") + 1)")
            lines.append(f"    aimMirror({k + 1}, {MIRROR_TURN_SPEED})")
            lines.append("    sound(\"door/doorslidestone.wav\")")
            lines.append(f"    evt.StatusText(tr(\"The mirror turns ({{degrees}} degrees).\", "
                         f"{{degrees = var(\"Mirror{k + 1}\") * 10}}))")
            lines.append("end")
        lines += [
            f"handlers[{EV_LOCKED['DesertDoor0']}] = function()   -- DesertDoor0: Locked until the gemstone's light",
            "    if var(\"CagesOpen\") == 0 then locked() return end",
            "    openG(\"DesertDoor0\")",
            "end",
            "",
            "-- Njam the Meddler's cameo (Trigger1 -> SpawnNjam0 Spawn: SpawnNjamCameo.scr): a second later the effect and",
            "-- Windup10 at the spawner (:Onspawn2), two more and he appears with the town portal sound (:Appear) and walks",
            "-- (NjamCameo.scr: BaseWanderForceStartUp), 10-20 s later he goes (:Vanish2: his behaviour's departure,",
            "-- worlds/mm9/behaviors/njam.lua cameo). A hit sends him away at once (NjamCameo.scr OnDamage: the behaviour).",
            f"local NJAM = {actor['Njam']}",
            f"handlers[{T_NJAM}] = function()",
            f"    if not fired({T_NJAM}) then return end",
            "    local stage = var(\"NjamStage\")",
            "    if stage == 1 then",
            "        set(\"NjamStage\", 2)",
            "        MM9.clientFx(NJAM, \"mm9:GreaterDemon\"); sound(\"magic/windup10.wav\")",
            f"        arm({T_NJAM}, 2)",
            "    elseif stage == 2 then",
            "        set(\"NjamStage\", 3); set(\"NjamShown\", 1)",
            "        sound(\"spells/TownPortal.wav\")",
            "        evt.SetMonsterBit(NJAM, MonsterBits.Invisible, false)",
            "        evt.SetActorImmobile(NJAM, false)",
            f"        arm({T_NJAM}, evt.RandomBetween(10, 20))",
            "    elseif stage == 3 then",
            "        set(\"NjamStage\", 4)",
            "        if MM9.actorAlive(NJAM) then evt.TriggerActor(NJAM, \"vanish\") end",
            "    end",
            "end",
            "",
            "-- The exit room (ExitTrigger0-3, four boxes at the room's corners, each turning the next on: 2 -> 0 -> 1 -> 3;",
            "-- the last, on the riser, unlocks and raises ExitRiser 228 LT and runs out ExitRamp to the upper door; the",
            "-- Switch (StartOpen, -> ExitReset) puts it all back: ExitTrigger2 on, the others off, riser down and locked).",
            "local function exitStep(k)",
            "    if var(\"ExitOn\" .. k) ~= 1 then return end",
            "    if k == 2 then set(\"ExitOn0\", 1); set(\"ExitOn3\", 0)",
            "    elseif k == 0 then set(\"ExitOn1\", 1); set(\"ExitOn2\", 0); set(\"ExitOn3\", 0)",
            "    elseif k == 1 then set(\"ExitOn3\", 1); set(\"ExitOn2\", 0); set(\"ExitOn1\", 0)",
            "    elseif k == 3 then",
            "        set(\"ExitOn0\", 0); set(\"ExitOn1\", 0); set(\"ExitOn2\", 0); set(\"ExitOn3\", 0)",
            "        set(\"RiserUp\", 1); openG(\"ExitRiser\"); openG(\"ExitRamp\")",
            f"        set(\"AmbientSound{build.source.by_name['magic elevator sound']['index']}\", 1)"
            "   -- ExitTrigger3: the magic elevator sound on",
            "        sound(\"magic/windup10.wav\")",
            "    end",
            "    sound(\"spells/enchantitem.wav\")",
            "end",
            "local function exitReset()",
            "    set(\"ExitOn0\", 0); set(\"ExitOn1\", 0); set(\"ExitOn2\", 1); set(\"ExitOn3\", 0)",
            "    set(\"RiserUp\", 0); closeG(\"ExitRiser\"); closeG(\"ExitRamp\")",
            f"    set(\"AmbientSound{build.source.by_name['magic elevator sound']['index']}\", 2)"
            "   -- ExitRiser's CloseTrigger0: off",
            "end",
            f"handlers[{EV_SWITCH_EXIT}] = function()   -- Switch -> ExitReset",
            "    for _, d in ipairs(GROUPS.Switch) do evt.SetDoorState(d, DoorAction.Trigger) end",
            "    set(\"Resets\", var(\"Resets\") + 1)",
            "    exitReset()",
            "end",
            "",
            "-- The Wyrde of the Unknown (NPC338.scr :OnRude on RUDE 338's exit): with key 476 the flame cage opens and the",
            "-- exit is on (:activate); with item 396 and no key 188, key 188 and 146 000 experience; the first talk (no key",
            "-- 187) gives keys 476 and 187, 92 000 experience, the quest sound and :activate. FlameCage sinks 128 LT at 15;",
            "-- its invisible slab ring round ExitPoint goes with it; FlameDamage (PoisonGas, 10) burns until then.",
            "local function activate()",
            "    if var(\"CageOpen\") == 1 then return end",
            "    set(\"CageOpen\", 1); openG(\"FlameCage\")",
            "end",
            f"handlers[{50000 + build.source.by_name['wyrdeoftheunknown0']['index']}] = function()   -- WyrdeoftheUnknown0",
            f"    if MM9.hasKey({KEY_ACTIVATED}) == 1 then activate() end",
            f"    if MM9.hasKey({KEY_ITEM_BACK}) == 0 and MM9.hasItem({ITEM_FATE}) == 1 then",
            f"        MM9.giveKey({KEY_ITEM_BACK}); {experience_lua(146000, KEY_ITEM_BACK)}",
            "    end",
            f"    if MM9.hasKey({KEY_MET}) == 0 then",
            f"        MM9.giveKey({KEY_ACTIVATED}); MM9.giveKey({KEY_MET}); {experience_lua(92000, KEY_MET)}",
            "        activate()",
            "        MM9.playSound(\"sounds/events/quest.wav\")",
            "    end",
            "end",
            f"handlers[{T_FLAME}] = function() end",
            "",
        ]
        boxes = self.boxes
        runs = {
            "SpikeTrigger1": ("var(\"SpikesOpen\") == 0", "set(\"SpikesOpen\", 1); for k = 1, 4 do openG(\"SpikeDoor\" .. k) end; "
                              "sound(\"door/doormetal_open02.wav\")", False),
            "TriggerDoor0": ("true", "set(\"ForestUnlocked\", 1); openG(\"ForestDoor0\")", False),
            "TriggerAttack0": ("true", "closeG(\"ForestDoor0\"); set(\"ForestLocked\", 1); "
                               f"arm({T_WARRIOR}, 1.5); sound(\"door/doorslammetal01.wav\")", False),
            "TriggerBansheeOff0": ("true", "set(\"EyesOff\", 1)", False),
            # SpawnNjam0's Spawn (SpawnNjamCameo.scr :Onspawn: wait 1 -> :Onspawn2), where Njam waits hidden
            "Trigger1": ("true", f"set(\"NjamStage\", 1); arm({T_NJAM}, 1)", False),
            "ExitTrigger0": ("var(\"ExitOn0\") == 1", "exitStep(0)", True),
            "ExitTrigger1": ("var(\"ExitOn1\") == 1", "exitStep(1)", True),
            "ExitTrigger2": ("var(\"ExitOn2\") == 1", "exitStep(2)", True),
            "ExitTrigger3": ("var(\"ExitOn3\") == 1", "exitStep(3)", True),
            **{name: ("true", f"teleport(\"{name}\")", True) for name in TELEPORTERS},
            "Dive": ("true", "set(\"Dives\", var(\"Dives\") + 1); evt.StatusText(\"You dive down the flooded tube.\"); "
                     f"evt.MoveToMap({self.dive_arrival[0]}, {self.dive_arrival[1]}, {self.dive_arrival[2]}, 0, 0, 0, 0, 0)",
                     True),
            "ShaftExit": ("true", "set(\"ShaftDrops\", var(\"ShaftDrops\") + 1); "
                          f"evt.MoveToMap({self.shaft_drop[0]}, {self.shaft_drop[1]}, {self.shaft_drop[2]}, 0, 0, 0, 0, 0)",
                          True),
        }
        # with swimming the party swims the tube and the shaft (no dive box); the shaft's bottom is a move (SHAFT_EXIT_LT)
        names = VOLUMES + list(TELEPORTERS) + (["ShaftExit"] if swimming(build) else ["Dive"])
        volume_lua = ",\n".join(
            f"    {{name = \"{name}\", box = {{{lua.point(boxes[name][0])}, {lua.point(boxes[name][1])}}}, "
            f"again = {'true' if runs[name][2] else 'false'}, "
            f"armed = function() return {runs[name][0]} end, run = function() {runs[name][1]} end}}"
            for name in names)
        lines += [
            "-- MM9's Trigger and Teleporter volumes, polled four times a second (any part of the party in the box). One-shot",
            "-- ones fire once; the others whenever their state allows and the party has left the box since.",
            "local VOLUMES = {",
            volume_lua,
            "}",
            f"local FLAME = {{{lua.point(boxes['FlameDamage'][0])}, {lua.point(boxes['FlameDamage'][1])}}}",
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
            "    -- FlameDamage (PoisonGas, Damage 10 a second) until the cage is open; the spike pit once (Spikes1, 100)",
            "    if var(\"CageOpen\") == 0 and inBox(FLAME, x, y, z) then",
            "        set(\"FlameTicks\", var(\"FlameTicks\") + 1)",
            "        if var(\"FlameTicks\") % 4 == 0 then evt.DamagePlayer(Players.All, const.Damage.Fire, "
            f"{FIRE_DAMAGE}) end",
            "    end",
            "end",
            "",
            "-- The PerceptionBrushes: the red glow shows to a party whose Perception reaches the brush's PerceptionValue",
            "-- unless MM9's wiring switched it off (the painting's PerceptionBrush1).",
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
            "    if var(\"ExitInit\") == 0 then set(\"ExitInit\", 1); set(\"ExitOn2\", 1) end",
            f"    for k = 0, {len(SWITCH_STATUES) - 1} do",
            "        -- a save taken while a statue's clip played: the manager hears it now",
            f"        if var(\"StatueBusy\" .. k) == 1 then set(\"Armed\" .. ({T_STATUE} + k), 0); statueDone(k) end",
            "        showStatue(k)",
            "    end",
            "    placeBridges(puzzleState())",
            f"    if var(\"CanyonUsed\") == 1 and var(\"CanyonOpen\") == 0 then set(\"Armed{T_CANYON}\", 0); canyonOpen() end",
            f"    if var(\"CanyonOpen\") == 1 then evt.PlayDecorationClip({COG_CANYON_STATUE}, CANYON[#CANYON][1], \"end\") "
            + (f"else evt.PlayDecorationClip({COG_CANYON_STATUE}, \"{CANYON_START}\", \"end\") "
               if CANYON_START in self.statue_clips["SwitchCreature4"] else "") + "end",
            "    for k = 1, 4 do aimMirror(k, 0) end",
            "    if var(\"PuzzleSolved\") == 1 then openG(\"TeleportDoor0\") end",
            "    if var(\"NjamShown\") == 1 then MM9.removeActor(NJAM)",
            f"    elseif var(\"NjamStage\") == 2 then set(\"NjamStage\", 1); arm({T_NJAM}, 1) end   -- saved mid-spawn",
            "    if var(\"AdventurerDead\") == 1 then MM9.removeActor(ADVENTURER) end",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            f"    evt.StartTimer({T_EYES}, seconds(1))",
            "end",
            "",
        ]
        script.add([], *[(event, "Statue", "Statue") for event in EV_SWITCH.values()],
                   (EV_RESET_STATUE, "Statue", "Statue"), (EV_CANYON_STATUE, "Statue", "Statue"),
                   (EV_CARPET, "Magic carpet", "Carpet"), (EV_PAINTING, "Painting", "Painting"),
                   *[(event, "Mirror", "Mirror") for event in EV_MIRROR.values()], (EV_GEMSTONE, "Gemstone", "Gemstone"),
(EV_SWITCH_EXIT, "Switch", "Switch"),
                   (EV_TELEPORT_DOOR1, "Door", "Door"), *[(event, "Door", "Door") for event in EV_LOCKED.values()],
                   (50000 + build.source.by_name["wyrdeoftheunknown0"]["index"], "Wyrde of the Unknown", None),
                   (T_POLL, "Trigger volumes", None, "timer"), (T_HINTS, "Perception hints", None, "timer"),
                   (T_EYES, "Banshee eyes", None, "timer"),
                   *[(t, "Timer", None, "timer") for t in (T_CARPET, T_CAGES, T_NJAM, T_WARRIOR, T_FLAME, T_CANYON)],
                   *[(T_STATUE + k, f"{name}'s clip ends", None, "timer") for k, name in enumerate(SWITCH_STATUES)],
                   (EV_LOAD, "Map load", None))
        script.hooks += [f'RegisterMonsterKilledHook({KILL_HOOK}, "Dark Passageway kills", handlers[{KILL_HOOK}])']
        return script.finish(on_load=[EV_LOAD])

    # --- scene ------------------------------------------------------------------------------------------------------
    def scene(self, build, scene: dict) -> None:
        """The ladders, the water surfaces and the perception hints as translucent faces (found in the compiled BLV by
        texture)."""
        scene["ladders"] = self.ladders(build)
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        aliases = build.source.aliases
        by_texture = {aliases[PERCEPTION_TEXTURE]["alias"].lower(): "hints"}
        for model, _, texture, _ in WATER:
            by_texture[aliases[texture]["alias"].lower()] = texture
        found = {kind: [] for kind in by_texture.values()}
        for face in blv["faces"]:
            kind = by_texture.get(str(face.get("texture_name", "")).lower())
            if kind and not face["is_portal"]:
                found[kind].append(face["index"])
        if len(found["hints"]) != self.hint_faces:
            raise SystemExit(f"{len(found['hints'])} perception faces in the BLV, {self.hint_faces} polygons")
        entries = scene.setdefault("translucent_faces", [])
        entries.append({"faces": sorted(found["hints"]), "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0],
                        "two_sided": True})
        for _, _, texture, opacity in WATER:
            if found[texture]:
                entries.append({"faces": sorted(found[texture]), "opacity": opacity, "tint": [1.0, 1.0, 1.0],
                                "two_sided": False})
        build.stats["translucent_faces"] = sum(len(e["faces"]) for e in entries)
        build.stats["water_faces"] = {texture: len(found[texture]) for _, _, texture, _ in WATER}
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)
        if swimming(build):
            self.water_volumes(build, scene)

    def water_volumes(self, build, scene: dict) -> None:
        """The scene's `water_volumes` (written by the shared build): the lake, the tube room, the flooded tube (its
        current) and the ocean. The room and bed gates are the shared build's (`water_checks`, build_report.json)."""
        volumes = scene.get("water_volumes", [])
        if sorted(v["id"] for v in volumes) != sorted(SWIM_VOLUMES):
            raise SystemExit(f"water volumes: {[v['id'] for v in volumes]}, expected {SWIM_VOLUMES}")

    def ladders(self, build) -> list[dict]:
        """Ladder records (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md) in native units from LT points: Ladder5 from
        Bridge0's deck up to the start corridor (rungs WorldObject10 on the corridor's end wall), Ladder1 out of the lake
        onto Bridge0's east side (from the water with swimming), Ladder0 out of the spike pit onto the corridor north
        of it."""
        project = build.project
        out = []

        def record(name, surface_lt, bottom_y, top_y, facing_xz, width_lt, reach, exit_lt):
            bottom = project.native([surface_lt[0], bottom_y, surface_lt[1]])
            top = project.native([surface_lt[0], top_y, surface_lt[1]])
            out.append({"id": name, "bottom": [round(float(v), 2) for v in bottom],
                        "top": [round(float(v), 2) for v in top],
                        "facing_degrees": round(math.degrees(math.atan2(facing_xz[1], facing_xz[0])) % 360.0, 2),
                        "width": round(width_lt * SCALE, 2), "reach": reach,
                        "top_exit": [round(float(v), 2) for v in project.native(exit_lt)]})
            if grabs_at_top(out[-1]):
                out[-1]["grab_at_top"] = True

        record("Ladder5", (-7438.0, -530.0), -478.0, -4.0, (0.0, 1.0), 40.0, 80.0, (-7438.0, 1.0, -470.0))
        # Ladder1 rises out of the lake: with swimming its foot reaches 60 LT under the surface, where the feet of a party
        # swimming at it are (the engine grabs a ladder from 24 under its bottom; MM9's brush overlaps the body)
        bottom = volume_top_lt(build.source, "BlueWater0") - 60.0 if swimming(build) else -598.0
        record("Ladder1", (-7366.0, -568.0), bottom, -496.0, (-1.0, 0.0), 70.0, 80.0, (-7420.0, -478.0, -568.0))
        record("Ladder0", (-2180.0, -1216.0), -302.0, -144.0, (0.0, 1.0), 170.0, 80.0, (-2180.0, -127.0, -1150.0))
        return out

    def report(self, build) -> dict:
        return {"scripted": {"boxes": getattr(self, "boxes", {}), "hints": getattr(self, "hints", {}),
                             "actors": getattr(self, "actor_index", {}), "arrivals": getattr(self, "arrivals", {}),
                             "water_faces": getattr(self, "water_faces", {}),
                             "placement_notes": getattr(self, "placement_notes", {}),
                             "room_ambient": getattr(self, "room_ambient", {})}}


def grow_exits(transitions_text):
    """ExitPoint (30 LT half extents) stands on the water barrel (Prop36, MM9's swirling exit): the native exit tests
    the party's centre, which the barrel's body keeps outside MM9's box. The row's box reaches EXIT_GROW_LT further
    toward the room (map-local: the shared writer keeps MM9's box)."""
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


EXIT_GROW_LT = {"ExitPoint": (-40, 0, -12)}   # x toward the room; z down to the floor (the box stands 2 LT over it)


if __name__ == "__main__":
    from dungeon import tables
    tables.transitions_text = grow_exits(tables.transitions_text)
    sys.exit(dungeon.main(PROJECT, DarkPassageway()))
