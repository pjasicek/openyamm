#!/usr/bin/env python3
"""
Chasm of the Dead, MM9 rework: MM9's CHASMOFTHEDEAD.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon).

    python3 level_generation/projects/mm9r_chasmofthedead/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_chasmofthedead/convert.py --plan     # rooms and plans only

overrides.yml holds the model rules and the archway cuts; this file adds the population (props.json from
../../props/mm9_chasmofthedead_claude, 171 monsters) and MM9's traps and scripts as native Lua (README.md, "Scripted
objects"): the shooter plates and hidden shooters (Shooter objects, Door plates, RotatingDoor shutters), the closing
walls, the spike wave, the ceiling crushers, the pendulums, the acid grate, the mummies (MummyAwaken.scr), the buried
zombies (AutoResurrect.Scr), the apparitions (Chasm_GhostSpawner.scr, ghost.scr), the Lich Instructions
(LichInstructions.scr) and the Crona Kiga (CronaKiga.scr), the dais shooter (OffRailTrigger.scr).

MM9's Trigger volumes are boxes polled four times a second: they fire on any part of the party in their box as MM9's
do, and need no level floor, which the canyon does not have.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon import rotation  # noqa: E402
from dungeon.rotation import rotate_lt  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from quest_xp import experience_lua  # noqa: E402

PROPS = PROJECT / "props.json"

# --- Events, timers, groups ---------------------------------------------------------------------------------------
SHOOTER_PLATES = {"ShooterPlate1": "Shooter1", "ShooterPlate2": "CeilingShooter1", "ShooterPlate3": "CeilingShooter3",
                  "ShooterPlate4": "CeilingShooter2", "ShooterPlate5": "Shooter2", "ShooterPlate6": "Shooter2",
                  "ShooterPlate7": "Shooter2", "ShooterPlate8": "Shooter3", "ShooterPlate9": "Shooter3",
                  "ShooterPlate10": "Shooter3"}
EV_SHOOTER_PLATE = {name: 200 + k for k, name in enumerate(SHOOTER_PLATES)}
HIDDEN_PLATES = {"HSP1": ("SD1", "SD2"), "HSP2": ("SD3", "SD4"), "HSP6": ("SD6",), "HSP7": ("SD7",)}
HIDDEN_SHOOTER = {"SD1": "HS1", "SD2": "HS2", "SD3": "HS3", "SD4": "HS4", "SD6": "HS6", "SD7": "HS7"}
EV_HIDDEN_PLATE = {name: 220 + k for k, name in enumerate(HIDDEN_PLATES)}
EV_CLOSING_WALLS, EV_SPIKE_PLATE, EV_PANEL, EV_PENDULUM, EV_CRONA = 230, 231, 232, 233, 235
CRUSHERS = {"CeilingCrushPlate3": "CeilingCrush3", "CeilingCrushPlate4": "CeilingCrush4"}
EV_CRUSHER = {"CeilingCrushPlate3": 236, "CeilingCrushPlate4": 237}
EV_DAIS, EV_TRAP, EV_HATCH, EV_BUTTON, EV_PIT_WEST = 238, 239, 240, 241, 242
TRAP_CYCLE_SECONDS = 8               # 0.9 s over, 5 s open, 1.8 s back (PivotWallTrap1: 100, CloseWaitTime 5, 50)
PENDULUM_TRIGGERS = ("PendulumTrigger1", "PendulumTrigger2")
T_POLL = 300
T_SHOOTER_PLATE = {name: 301 + k for k, name in enumerate(SHOOTER_PLATES)}
T_HIDDEN_PLATE = {name: 320 + k for k, name in enumerate(HIDDEN_PLATES)}
T_WALLS_HIT, T_WALLS_OPEN, T_WAVE, T_PENDULUM_HIT, T_PENDULUM_UP = 330, 331, 332, 333, 334
T_GRATE_SHUT, T_TRAP_RESET, T_CARRY = 335, 340, 341
T_CRUSH = {"CeilingCrushPlate3": (336, 337), "CeilingCrushPlate4": (338, 339)}
DAMAGE_HOOK, KILL_HOOK = 96, 97
ZOMBIE_GROUPS = {"Trigger2": 60, "Trigger3": 61, "Trigger4": 62, "Trigger5": 63, "Trigger6": 64}
GROUP_GHOSTS = 90

APPARITION = 9139                    # MM9 monster row Apparition (ghost.scr's Spawn "Apparition")
ITEM_INSTRUCTIONS, KEY_INSTRUCTIONS = 447, 296      # LichInstructions.scr
ITEM_CRONA, KEY_CRONA_QUEST, KEY_LUDWIG, KEY_CRONA_FOUND, CRONA_EXPERIENCE = 390, 48, 46, 169, 10000      # CronaKiga.scr
BOLT_DAMAGE, DAIS_DAMAGE, CRUSH_DAMAGE, WALL_DAMAGE, SPIKE_DAMAGE, PENDULUM_DAMAGE, ACID_DAMAGE = 20, 35, 20, 20, 10, 30, 10
PIT_SPIKE_DAMAGE = 20                # Spikes2: 20 a second to whoever stands on it
ACID_SECONDS = 3                     # the third second in the acid lifts the party out: it swims in the pit (the shared
#                                     water rule), but the rim is 102 over the surface, past the surface jump (59)
WAVE_STEP = 0.16                     # a row rises 96 LT at 600: the next starts when it is up
PENDULUMS = ("Pendulum1", "Pendulum2")
DETAIL_STEEP, DETAIL_NARROW = 0.5, 26      # detail_faces(): normal z under this, or under this wide (native units)
INVISIBLE_FACE = 0x00002000
SKY_TEXELS_PER_LT = 0.2              # the canyon's sky face: sky04 stretched to about two repeats along the chasm


class Chasm(dungeon.Hooks):
    generator = "mm9r_chasmofthedead"
    own_water_surfaces = ("BlueWater1", "Acid0")      # surface() builds them (no drawn_surfaces); BlueWater0 is H2OSurface's
    mover_events = {**{name: (event, "pressure_plate") for name, event in EV_SHOOTER_PLATE.items()},
                    **{name: (event, "pressure_plate") for name, event in EV_HIDDEN_PLATE.items()},
                    **{name: (event, "pressure_plate") for name, event in EV_CRUSHER.items()},
                    "CWPlate1": (EV_CLOSING_WALLS, "pressure_plate"),
                    "SpikeRowPlate1": (EV_SPIKE_PLATE, "pressure_plate"),
                    "PivotTreasurePanel1": (EV_PANEL, "click"), "PivotWallTrap1": (EV_TRAP, "pressure_plate"),
                    "TrapExitDoor1": (EV_HATCH, "click"), "PivotButton1": (EV_BUTTON, "click")}

    def extra_seeds(self, build) -> list:
        # The pendulums (RotatingDoor with an object yaw, the only ones in MM9): their points are authored un-yawed and
        # their RotationAngles are about the object's own axes, turned here about their pivots; the swing's axis with them.
        polygons = build.source.polygons
        axis_y = np.array([0.0, 1.0, 0.0])

        def turned(model_name):
            found = polygons(model_name)
            if model_name not in PENDULUMS:
                return found
            properties = build.source.properties(model_name)
            pivot = np.asarray(properties["RotationPoint"], float)
            degrees = float(np.degrees(properties["Rotation"][1]))
            out = []
            for p in found:
                origin, u, v = p.mapping
                mapping = (rotate_lt(np.asarray(origin, float)[None], pivot, axis_y, degrees)[0],
                           rotate_lt(np.asarray(u, float)[None], np.zeros(3), axis_y, degrees)[0],
                           rotate_lt(np.asarray(v, float)[None], np.zeros(3), axis_y, degrees)[0])
                out.append(Polygon(rotate_lt(p.points, pivot, axis_y, degrees), p.keys, p.texture, mapping, p.flags,
                                   p.model, p.role, notes=dict(p.notes)))
            return out

        original_rotation = rotation.lt_rotation

        def object_rotation(properties):
            axis, degrees = original_rotation(properties)
            yaw = float((properties.get("Rotation") or [0, 0])[1])
            return (rotate_lt(axis[None], np.zeros(3), axis_y, float(np.degrees(yaw)))[0] if yaw else axis), degrees

        rotation.lt_rotation = object_rotation
        build.source.polygons = turned
        return super().extra_seeds(build)

    def edit_polygons(self, build, polygons) -> list:
        """The sky face over the chasm (MM9 draws a static sky box through it): one tile about 2 500 LT wide, not a
        repeating tile every 200 (the bake's sky emitter stays an ordinary textured face: IndoorSky faces cannot be)."""
        for polygon in polygons:
            if "skymarker" in polygon.texture.lower():
                origin = np.asarray(polygon.mapping[0], float)
                polygon.mapping = (origin, np.array([SKY_TEXELS_PER_LT, 0.0, 0.0]), np.array([0.0, 0.0, SKY_TEXELS_PER_LT]))
        return polygons

    # --- population -------------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source, project = build.content, build.source, build.project
        if PROPS.exists():
            # An entity named like a decoration resolves as that decoration (playbook): MM9's Urn2 and the like.
            entries = json.loads(PROPS.read_text())
            for entry in entries:
                if entry["source_name"].lower() in content.ids:
                    entry["source_name"] += "_prop"
            placed = build.project.work / "props_entities.json"
            placed.write_text(json.dumps(entries) + "\n")
            # the Lich Instructions and the Crona Kiga are world items (dungeon/pickups.py); the Crona Kiga's pickup
            # runs EV_CRONA
            content.props(placed, events={"CronaKiga": EV_CRONA})
        # MM9's non-solid movers: the spike rows and the pendulums pass through the party, which takes the damage.
        untouchable = {"SpikeRow%d" % k for k in range(1, 15)} | set(PENDULUMS)
        for mover in build.movers:
            if mover["group"] in untouchable and not mover["invisible"]:
                build.package.metadata["surfaces"].append({"id": mover["node"][5:], "source_node": mover["node"],
                                                           "flags": ["untouchable"]})
        # Trigger volumes.
        self.boxes = {}
        for o in source.objects:
            if o["class"] != "Trigger" or o["name"] == "CKTrigger":
                continue
            p = o["properties"]
            centre = np.array(p["Pos"], float)
            if p.get("MoveToFloor"):        # MM9 drops these boxes onto the floor under them (the ledge's apparitions)
                floor = content.floor_at(centre[0], centre[2], centre[1])
                if floor is not None:
                    centre[1] = floor + p["Dims"][1]
            low = project.native(centre - np.array(p["Dims"]))
            high = project.native(centre + np.array(p["Dims"]))
            self.boxes[o["name"]] = [np.minimum(low, high).round().astype(int).tolist(),
                                     np.maximum(low, high).round().astype(int).tolist()]
        self.points = {}
        for o in source.objects:
            if o["class"] == "Shooter" or o["class"] == "Marker":
                self.points[o["name"]] = project.native(o["properties"]["Pos"]).round().astype(int).tolist()
        # OffRailTrigger.scr's shooter stands over the dais of the Lich Instructions: the footing MM9's rails leave out.
        shooter = source.properties("Shooter0")["Pos"]
        content.pad("ShooterDais", (shooter[0], shooter[1] - 40, shooter[2]), (60, 80, 60), EV_DAIS)
        # The pit's west half, under the alcove (MM9's HidingPlace Hide0 stands there): convert.py's stand-in for the
        # cross's quarter turn into the alcove, which no MM9 trigger can reach (README, "Deviations").
        hide = source.properties("Hide0")["Pos"]
        content.pad("PivotPitWest", hide, (40, 40, 40), EV_PIT_WEST)
        # Spikes2 on the pit floor (the crushers' and walls' spikes move: decorations do not, README).
        spikes = source.properties("Spikes2")["Pos"]
        pit_floor = content.floor_at(spikes[0], spikes[2], spikes[1])
        content.entity("Spikes2", "mm9_spikepit", project.native([spikes[0], pit_floor, spikes[2]]), 0)
        self.water_faces, self.water_rings = [], []
        self.surface(build, "H2OSurface", "water:pool")
        self.surface(build, "BlueWater1", "water:pool")
        self.surface(build, "Acid0", "water:acid")
        self.detail_faces(build)

    def detail_faces(self, build) -> None:
        """The BLV keeps at most 7 000 outlines (the 875-byte seen-lines bitset) and the Chasm has about 8 000: every
        up-facing face counts, however small. The up-facing bevels of its columns and the narrow trim ledges of its
        walls add nothing to the map's plan, so they go to a TRIGGER_detail node compiled with the invisible flag, which
        the outline pass skips, and scene() gives them their drawn attributes back at load (they keep their collision)."""
        package = build.package
        self.detail_rings = []
        for node in [n for n in package.nodes if n.startswith("ROOM_")]:
            keep, detail = [], []
            for entry in package.nodes[node]:
                p = np.asarray(entry[0], float)
                n = np.cross(p[1] - p[0], p[2] - p[0]).astype(float)
                nz = n[2] / max(np.linalg.norm(n), 1e-9)
                wide = min(np.ptp(p[:, 0]), np.ptp(p[:, 1]))
                (detail if nz > 0.05 and (nz < DETAIL_STEEP or wide <= DETAIL_NARROW) else keep).append(entry)
            if not detail:
                continue
            package.nodes[node] = keep
            target = f"TRIGGER_detail_{node[5:]}"
            package.nodes[target].extend(detail)
            self.detail_rings += [entry[0] for entry in detail]
            package.room_nodes[f"room_{node[5:]}"].append(target)
            package.metadata["surfaces"].append({"id": target, "source_node": target, "flags": ["invisible"]})

    def surface(self, build, model_name, texture):
        """A liquid volume's top face (MM9 ShowSurface; H2OSurface is the channel's) as an untouchable face."""
        project, package = build.project, build.package
        points = np.array(build.source.models[model_name].points, float)
        top = points[:, 1].max()
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        ring = np.array([[x0, top, z0], [x0, top, z1], [x1, top, z1], [x1, top, z0]])
        native = np.round(project.native(ring)).astype(np.int64)
        if np.cross(native[1] - native[0], native[2] - native[0])[2] < 0:
            native, ring = native[::-1], ring[::-1]
        key = package.material(texture)[0]
        node = f"TRIGGER_water_{model_name}"
        package.nodes[node].append((native, ring[:, [0, 2]] - ring[:, [0, 2]].min(0), key))
        room = build.content.owner(np.array([(x0 + x1) / 2, top - 4, (z0 + z1) / 2]))
        package.room_nodes[room].append(node)
        package.metadata["surfaces"].append({"id": model_name, "source_node": node, "flags": ["untouchable"]})
        self.water_faces.append(node)
        self.water_rings.append(native)

    def scene(self, build, scene: dict) -> None:
        """MM9 draws its liquid surfaces at SurfaceAlpha 0.7: translucent faces over the channel, pool and pit."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], np.int64)

        def key(points) -> tuple:
            return tuple(sorted(tuple(int(round(c)) for c in p) for p in points))

        ids = {}
        for f in blv["faces"]:
            ids.setdefault(key(vertices[f["vertex_indices"]]), []).append(f)
        # The compiler reports no TRIGGER_ nodes: their faces are found by their vertices.
        details = [f for ring in self.detail_rings for f in ids[key(ring)]]
        water = [f["index"] for ring in self.water_rings for f in ids[key(ring)]]
        scene["initial_state"].setdefault("face_attribute_overrides", []).extend(
            {"face_index": f["index"], "legacy_attributes": int(f["attributes"]) & ~INVISIBLE_FACE} for f in details)
        build.stats["detail_faces"] = len(details)
        if water:
            scene.setdefault("translucent_faces", []).append(
                {"faces": sorted(water), "opacity": 0.7, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)

    # --- actors ---------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        buried = {}
        for trigger, group in ZOMBIE_GROUPS.items():
            for n in range(1, 11):
                target = source.properties(trigger).get(f"TargetName{n}", "")
                if target and source.properties(trigger).get(f"MessageName{n}") == "RESURRECT":
                    buried[target.lower()] = group
        buried["dripper35"] = ZOMBIE_GROUPS["Trigger4"]      # Trigger4 names Dripper33 twice: a slip for Dripper35
        self.mummies = {}
        out = []
        for o in source.objects:
            if o["class"] not in build.project.monster_classes or o["name"] not in bases:
                continue
            name, base, p = o["name"], bases[o["name"]], o["properties"]
            script = (p.get("ScriptName") or "").lower()
            group, hidden = 0, False
            if "autoresurrect" in script:
                group, hidden = buried[name.lower()], True
            record = content.actor(o, base, sector_of_room, group=group, hidden=hidden,
                                   floor_query_lt=p["Pos"][1] + 40)
            if "mummyawaken" in script:
                # MummyAwaken.scr: stands in its coffin until an awaken, or a hit (the engine wakes a hit resting
                # actor); p0 1: the next one wakes at this one's death, 0: at once.
                record["dormant"] = True
                words = str(p.get("ScriptParams") or "").split()
                self.mummies[name] = {"index": record["actor_index"], "on_death": bool(words and words[0] == "1"),
                                      "next": words[1] if len(words) > 1 else None}
            out.append(record)
        return out

    # --- map script -----------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Chasm of the Dead")
        group_doors = {g: ids for g, ids in script.groups.items()}
        script.lines += [
            "local GROUPS = {" + ", ".join(f"{g} = {{{', '.join(map(str, ids))}}}" for g, ids in sorted(group_doors.items()))
            + "}",
            "local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) "
            "end end",
            "local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, "
            "DoorAction.Close) end end",
            "local function arm(timer, delay) set(\"Armed\" .. timer, 1); evt.StartTimer(timer, seconds(delay)) end",
            "local function fired(timer)",
            "    evt.StopTimer(timer)",
            "    if var(\"Armed\" .. timer) ~= 1 then return false end",
            "    set(\"Armed\" .. timer, 0)",
            "    return true",
            "end",
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z + 170 >= b[1][3] and z <= b[2][3] end",
            "local function near(b)",
            "    local x, y, z = evt.GetPartyPosition()",
            "    return inBox(b, x, y, z)",
            "end",
            "-- A Shooter sits in its wall or ceiling: the bolt starts a third of the way to the party's chest and",
            "-- strikes the party in its path (FireMissile's strikesParty); `projectile` is its MM9 ProjectileName (the",
            "-- launch sound).",
            "local function shoot(sx, sy, sz, damage, kind, projectile)",
            "    local x, y, z = evt.GetPartyPosition()",
            "    z = z + 100",
            "    local dx, dy, dz = x - sx, y - sy, z - sz",
            "    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))",
            "    local k = math.max(64 / length, 0.33)",
            "    local shot = evt.FireMissile(\"Fire\", sx + dx * k, sy + dy * k, sz + dz * k, x, y, z, damage, kind, 0, 0, "
            "true)",
            "    if shot then MM9.launchSound(projectile, sx, sy, sz) end",
            "    set(\"ShotsFired\", var(\"ShotsFired\") + (shot and 1 or 0))",
            "end",
            "local function hurt(amount) evt.DamagePlayer(Players.All, const.Damage.Physical, amount) end",
            "",
        ]
        script.doors()
        script.chests()
        lines = []
        pos = self.points
        # Shooter plates.
        lines.append("-- Shooter plates (MM9 Door + Trigger): the plate sinks, its Shooter fires one FireBolt "
                     f"(DamageAmt {BOLT_DAMAGE}) and the plate rises after 1 s (CloseWaitTime).")
        for plate, shooter in SHOOTER_PLATES.items():
            event, reset = EV_SHOOTER_PLATE[plate], T_SHOOTER_PLATE[plate]
            lines += [f"handlers[{event}] = function()   -- {plate} -> {shooter}",
                      f"    if var(\"{plate}\") == 1 then return end",
                      f"    set(\"{plate}\", 1)",
                      f"    openGroup(\"{plate}\")",
                      f"    shoot({', '.join(map(str, pos[shooter]))}, {BOLT_DAMAGE}, \"Fire\", \"FireBolt\")",
                      f"    arm({reset}, 1.1)",
                      "end",
                      f"handlers[{reset}] = function()",
                      f"    if not fired({reset}) then return end",
                      f"    closeGroup(\"{plate}\")",
                      f"    set(\"{plate}\", 0)",
                      "end"]
            script.add([], (event, plate, None), (reset, f"{plate} reset", None, "timer"))
        # Hidden shooters.
        lines += ["",
                  "-- Hidden shooters (HSP plates, SDU/SDL shutters, HS shooters): the plate sinks, the shutters open, a "
                  "bolt comes out, and they shut after 1 s (CloseWaitTime; MM9's flaps swing apart: here they slide).",
                  ]
        for plate, shutters in HIDDEN_PLATES.items():
            event, reset = EV_HIDDEN_PLATE[plate], T_HIDDEN_PLATE[plate]
            shots = [f"    openGroup(\"{s}\"); shoot({', '.join(map(str, pos[HIDDEN_SHOOTER[s]]))}, {BOLT_DAMAGE}, "
                     f"\"Fire\", \"FireBolt\")" for s in shutters]
            lines += [f"handlers[{event}] = function()   -- {plate}",
                      f"    if var(\"{plate}\") == 1 then return end",
                      f"    set(\"{plate}\", 1)",
                      f"    openGroup(\"{plate}\")",
                      *shots,
                      f"    arm({reset}, 1.3)",
                      "end",
                      f"handlers[{reset}] = function()",
                      f"    if not fired({reset}) then return end",
                      *[f"    closeGroup(\"{s}\")" for s in shutters],
                      f"    closeGroup(\"{plate}\")",
                      f"    set(\"{plate}\", 0)",
                      "end"]
            script.add([], (event, plate, None), (reset, f"{plate} reset", None, "timer"))
        # Closing walls.
        walls = build.project.native(np.array([[-5136, 616, 7328], [-4784, 760, 7520]], float))
        wall_box = [np.minimum(walls[0], walls[1]).round().astype(int).tolist(),
                    np.maximum(walls[0], walls[1]).round().astype(int).tolist()]
        lines += ["",
                  "-- The closing walls (TriggerCWPlate1, CWR1/L1, CWR2/L2: Door 80 LT at 300, DoDamage; Spikes3-8 on "
                  "them): the plate sinks, both pairs slam in, whoever stands between is hurt; 3 s later they draw back.",
                  f"local WALL_BOX = {{{lua.point(wall_box[0])}, {lua.point(wall_box[1])}}}",
                  f"handlers[{EV_CLOSING_WALLS}] = function()   -- CWPlate1",
                  "    if var(\"ClosingWalls\") == 1 then return end",
                  "    set(\"ClosingWalls\", 1)",
                  "    openGroup(\"CWPlate1\")",
                  "    openGroup(\"CWR1\"); openGroup(\"CWL1\"); openGroup(\"CWR2\"); openGroup(\"CWL2\")",
                  f"    arm({T_WALLS_HIT}, 0.3)",
                  "end",
                  f"handlers[{T_WALLS_HIT}] = function()",
                  f"    if not fired({T_WALLS_HIT}) then return end",
                  f"    if near(WALL_BOX) then hurt({WALL_DAMAGE}); set(\"WallHits\", var(\"WallHits\") + 1) end",
                  f"    arm({T_WALLS_OPEN}, 3)",
                  "end",
                  f"handlers[{T_WALLS_OPEN}] = function()",
                  f"    if not fired({T_WALLS_OPEN}) then return end",
                  "    closeGroup(\"CWR1\"); closeGroup(\"CWL1\"); closeGroup(\"CWR2\"); closeGroup(\"CWL2\")",
                  "    closeGroup(\"CWPlate1\")",
                  "    set(\"ClosingWalls\", 0)",
                  "end"]
        script.add([], (EV_CLOSING_WALLS, "CWPlate1", None), (T_WALLS_HIT, "Walls strike", None, "timer"),
                   (T_WALLS_OPEN, "Walls open", None, "timer"))
        # The spike wave.
        rows = [build.project.native(np.array(build.source.models[f"SpikeRow{k}"].points, float)) for k in range(1, 15)]
        row_x = [int(round(r[:, 0].mean())) for r in rows]
        y0, y1 = int(rows[0][:, 1].min()), int(rows[0][:, 1].max())
        lines += ["",
                  "-- The spike wave (SpikeRowTrigger1, SpikeRowPlate1, SpikeRow1-14: Door, Solid 0, 96 LT up at 600, "
                  "back at 100; each row's open toggles the next and the last): a wave runs the length of the stair.",
                  f"local ROW_X = {{{', '.join(map(str, row_x))}}}",
                  f"handlers[{EV_SPIKE_PLATE}] = function()   -- SpikeRowPlate1",
                  "    if var(\"SpikeWave\") ~= 0 then return end",
                  "    set(\"SpikeWave\", 1)",
                  "    openGroup(\"SpikeRowPlate1\")",
                  f"    evt.StartTimer({T_WAVE}, seconds({WAVE_STEP}))",
                  "end",
                  f"handlers[{T_WAVE}] = function()",
                  "    local k = var(\"SpikeWave\")",
                  f"    evt.StopTimer({T_WAVE})",
                  "    if k == 0 then return end",
                  "    if k > 1 then closeGroup(\"SpikeRow\" .. (k - 1)) end",
                  "    if k > 14 then",
                  "        closeGroup(\"SpikeRowPlate1\")",
                  "        set(\"SpikeWave\", 0)",
                  "        return",
                  "    end",
                  "    openGroup(\"SpikeRow\" .. k)",
                  "    local x, y = evt.GetPartyPosition()",
                  f"    if math.abs(x - ROW_X[k]) <= 70 and y >= {y0 - 30} and y <= {y1 + 30} then",
                  f"        hurt({SPIKE_DAMAGE}); set(\"SpikeHits\", var(\"SpikeHits\") + 1)",
                  "    end",
                  "    set(\"SpikeWave\", k + 1)",
                  f"    evt.StartTimer({T_WAVE}, seconds({WAVE_STEP}))",
                  "end"]
        script.add([], (EV_SPIKE_PLATE, "SpikeRowPlate1", None), (T_WAVE, "Spike wave", None, "timer"))
        # Crushers.
        lines += ["",
                  "-- Ceiling crushers (CeilingCrushPlate, CeilingCrush: Lift 160 LT down at 500, back at 100 after 3 s; "
                  f"Spikes5/6 20 a second): the plate sinks, the ceiling drops, a party under it takes {CRUSH_DAMAGE}."]
        for plate, crusher in CRUSHERS.items():
            hit, rise = T_CRUSH[plate]
            points = build.project.native(np.array(build.source.models[crusher].points, float))
            low, high = points.min(0).round().astype(int), points.max(0).round().astype(int)
            lines += [f"handlers[{EV_CRUSHER[plate]}] = function()   -- {plate} -> {crusher}",
                      f"    if var(\"{crusher}\") == 1 then return end",
                      f"    set(\"{crusher}\", 1)",
                      f"    openGroup(\"{plate}\"); openGroup(\"{crusher}\")",
                      f"    arm({hit}, 0.35)",
                      "end",
                      f"handlers[{hit}] = function()",
                      f"    if not fired({hit}) then return end",
                      "    local x, y = evt.GetPartyPosition()",
                      f"    if x >= {low[0] - 40} and x <= {high[0] + 40} and y >= {low[1] - 40} and y <= {high[1] + 40} then",
                      f"        hurt({CRUSH_DAMAGE}); set(\"CrushHits\", var(\"CrushHits\") + 1)",
                      "    end",
                      f"    arm({rise}, 3)",
                      "end",
                      f"handlers[{rise}] = function()",
                      f"    if not fired({rise}) then return end",
                      f"    closeGroup(\"{crusher}\"); closeGroup(\"{plate}\")",
                      f"    set(\"{crusher}\", 0)",
                      "end"]
            script.add([], (EV_CRUSHER[plate], plate, None), (hit, f"{crusher} strike", None, "timer"),
                       (rise, f"{crusher} rise", None, "timer"))
        # Pendulums.
        pend = self.boxes[PENDULUM_TRIGGERS[0]], self.boxes[PENDULUM_TRIGGERS[1]]
        band = [np.minimum(pend[0][0], pend[1][0]).tolist(), np.maximum(pend[0][1], pend[1][1]).tolist()]
        lines += ["",
                  "-- The pendulums (PendulumTrigger1/2, Pendulum1/2: RotatingDoor, 210 degrees at 100, 30 a second): "
                  "a touch swings both blades through the corridor; the next touch swings them back (Sticky).",
                  f"local PENDULUM_BOX = {{{lua.point(band[0])}, {lua.point(band[1])}}}",
                  "local function swing()",
                  "    if var(\"Pendulum\") == 1 then return end",
                  "    set(\"Pendulum\", 1)",
                  "    for _, name in ipairs({\"Pendulum1\", \"Pendulum2\"}) do",
                  "        for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end",
                  "    end",
                  f"    arm({T_PENDULUM_HIT}, 1.0)",
                  "end",
                  f"handlers[{T_PENDULUM_HIT}] = function()",
                  f"    if not fired({T_PENDULUM_HIT}) then return end",
                  f"    if near(PENDULUM_BOX) then hurt({PENDULUM_DAMAGE}); set(\"PendulumHits\", var(\"PendulumHits\") + 1) end",
                  f"    arm({T_PENDULUM_UP}, 1.2)",
                  "end",
                  f"handlers[{T_PENDULUM_UP}] = function()",
                  f"    if not fired({T_PENDULUM_UP}) then return end",
                  "    set(\"Pendulum\", 0)",
                  "end",
                  f"handlers[{EV_PENDULUM}] = function() swing() end"]
        script.add([], (EV_PENDULUM, "Pendulum", None), (T_PENDULUM_HIT, "Pendulum strike", None, "timer"),
                   (T_PENDULUM_UP, "Pendulum rises", None, "timer"))
        # Treasure panel.
        lines += ["",
                  "-- PivotTreasurePanel1 (PushOpen, Sticky): a click slides it up and shows TreasureChest1.",
                  f"handlers[{EV_PANEL}] = function() openGroup(\"PivotTreasurePanel1\") end"]
        script.add([], (EV_PANEL, "Panel", "Panel"))
        lines += ["",
                  "-- The pivot trap (PivotWallTrap1, its trigger on the corridor half, PivotButton1 in the alcove): the "
                  "cross turns 90 degrees and tips the party into the spike pit; it turns back itself (the mover's "
                  "auto-close) and arms again. The ladder climbs to TrapExitDoor1, a hatch opened by a click.",
                  f"handlers[{EV_TRAP}] = function()",
                  "    if var(\"PivotTrap\") == 1 then return end",
                  "    set(\"PivotTrap\", 1)",
                  "    openGroup(\"PivotWallTrap1\"); openGroup(\"PivotButton1\")",
                  f"    arm({T_TRAP_RESET}, {TRAP_CYCLE_SECONDS})",
                  "end",
                  f"handlers[{T_TRAP_RESET}] = function()",
                  f"    if not fired({T_TRAP_RESET}) then return end",
                  "    closeGroup(\"PivotButton1\")",
                  "    set(\"PivotTrap\", 0)",
                  "end",
                  "-- MM9's cross is a revolving wall: its quarter turn would carry a party from the pit's west half up into "
                  "the alcove and from the alcove out to the corridor, but its trigger stands on the corridor half and "
                  "the button in the alcove, so no party could ever get in. The pit's west half springs the trap and the "
                  "turn carries the party up; the button in the alcove turns it back out.",
                  f"local CARRY_ALCOVE = {lua.point(build.project.native([830, -1726, -1776]))}",
                  f"local CARRY_CORRIDOR = {lua.point(build.project.native([1000, -1726, -1776]))}",
                  "local function carry(to)",
                  "    set(\"CarryTo\", to)",
                  f"    arm({T_CARRY}, 0.9)",
                  "end",
                  f"handlers[{T_CARRY}] = function()",
                  f"    if not fired({T_CARRY}) then return end",
                  "    local p = var(\"CarryTo\") == 1 and CARRY_ALCOVE or CARRY_CORRIDOR",
                  "    set(\"Carried\", var(\"Carried\") + 1)",
                  "    evt.MoveToMap(p[1], p[2], p[3], 0, 0, 0, 0, 0)",
                  "end",
                  f"handlers[{EV_PIT_WEST}] = function()",
                  f"    if var(\"PivotTrap\") == 1 then return end",
                  f"    handlers[{EV_TRAP}]()",
                  "    carry(1)",
                  "end",
                  f"handlers[{EV_BUTTON}] = function()   -- PivotButton1",
                  "    if var(\"PivotTrap\") == 1 then return end",
                  f"    handlers[{EV_TRAP}]()",
                  "    carry(2)",
                  "end",
                  f"handlers[{EV_HATCH}] = function() openGroup(\"TrapExitDoor1\") end   -- TrapExitDoor1"]
        script.add([], (EV_TRAP, "Pivot trap", None), (T_TRAP_RESET, "Pivot trap reset", None, "timer"),
                   (T_CARRY, "Pivot carry", None, "timer"), (EV_PIT_WEST, "Pit west", None), (EV_BUTTON, "PivotButton1", "Button"), (EV_HATCH, "TrapExitDoor1", "Hatch"))
        # Mummies.
        names = self.mummies
        rows_lua = ", ".join(f"[{m['index']}] = {{name = \"{name}\", "
                             f"next = {names[m['next']]['index'] if m['next'] in names else 'nil'}, "
                             f"onDeath = {'true' if m['on_death'] else 'false'}}}" for name, m in names.items())
        lines += ["",
                  "-- The mummies (MummyAwaken.scr): they stand in their coffins (dormant) until an awaken message or a "
                  "hit; each then wakes the next, at once or at its death (ScriptParams p0). A dead mummy takes no",
                  "-- awaken (MM9.receives) and its OnDamage does not fire: a blow that kills a dormant one wakes",
                  "-- nothing, so a hit wakes at the next poll, if the mummy lived through it; its OnDeath sends the",
                  "-- next one's awaken with p0 1 only (OnDeath DoNothing with p0 0).",
                  f"local MUMMIES = {{{rows_lua}}}",
                  "local function wake(index)",
                  "    if var(\"Mummy\" .. index) == 1 then return end",
                  "    if not MM9.receives(\"chasmofthedead\", MUMMIES[index].name, \"awaken\", index) then return end",
                  "    set(\"Mummy\" .. index, 1)",
                  "    set(\"MummiesAwake\", var(\"MummiesAwake\") + 1)",
                  "    evt.WakeActor(index)",
                  "    local m = MUMMIES[index]",
                  "    if m.next ~= nil and not m.onDeath then wake(m.next) end",
                  "end",
                  "local mummiesHit = {}",
                  f"handlers[{DAMAGE_HOOK}] = function(context)",
                  "    if MUMMIES[context.actorIndex] then mummiesHit[context.actorIndex] = true end",
                  "end",
                  f"handlers[{KILL_HOOK}] = function(context)",
                  "    local m = MUMMIES[context.actorIndex]",
                  "    if m ~= nil and m.next ~= nil and m.onDeath then wake(m.next) end",
                  "end"]
        script.hooks += [f'RegisterMonsterDamageHook({DAMAGE_HOOK}, "Mummy wakes", handlers[{DAMAGE_HOOK}])',
                         f'RegisterMonsterKilledHook({KILL_HOOK}, "Mummy chain", handlers[{KILL_HOOK}])']
        # Volumes.
        source = build.source

        def awaken(trigger):
            return [names[source.properties(trigger)[f"TargetName{n}"]]["index"] for n in range(1, 5)
                    if source.properties(trigger).get(f"MessageName{n}") == "awaken"]

        marker_names = [f"Apparition{k}" for k in range(13)]
        markers = ", ".join(lua.point(pos[n]) for n in marker_names)
        entries = []
        for trigger in ("Trigger0", "Trigger1", "Trigger7"):
            entries.append((trigger, "wakeAll({" + ", ".join(map(str, awaken(trigger))) + "})"))
        for trigger, group in ZOMBIE_GROUPS.items():
            call = f"rise({group})"
            if trigger == "Trigger5":
                call += "; set(\"Trigger6On\", 1)"
            entries.append((trigger, call))
        for k in range(13, 26):
            entries.append((f"Apparition{k}", "spawnGhost()"))
        entries.append(("GratetrapTrigger0", "grate()"))
        entries += [(name, "swing()") for name in PENDULUM_TRIGGERS]
        rearm = {"GratetrapTrigger0", *PENDULUM_TRIGGERS}
        volume_lua = ",\n".join(
            f"    {{name = \"{name}\", box = {{{lua.point(self.boxes[name][0])}, {lua.point(self.boxes[name][1])}}}, "
            f"rearm = {'true' if name in rearm else 'false'}, run = function() {call} end}}" for name, call in entries)
        grate = self.boxes["GratetrapTrigger0"]
        pit = build.project.native(np.array([[2712, -2344, 6376], [2856, -2120, 6520]], float))
        pit_box = [pit.min(0).round().astype(int).tolist(), pit.max(0).round().astype(int).tolist()]
        spikes = build.source.properties("Spikes2")["Pos"]
        spike_box = build.project.native(np.array([[spikes[0] - 70, spikes[1] - 70, spikes[2] - 70],
                                                   [spikes[0] + 70, spikes[1] + 40, spikes[2] + 70]], float))
        spike_box = [spike_box.min(0).round().astype(int).tolist(), spike_box.max(0).round().astype(int).tolist()]
        rim_floor = build.content.floor_at(2620, 6448, -1950)      # the corridor beside the pit
        rim = build.project.native([2620, rim_floor, 6448]).round().astype(int).tolist()
        rim[2] += 1
        dais = build.source.properties("LichInstructions")["Pos"]
        lines += ["",
                  "-- MM9's Trigger volumes: awaken lists, the buried zombies (AutoResurrect.Scr: hidden under the floor "
                  "until their RESURRECT), the apparitions (Chasm_GhostSpawner.scr: each touched trigger makes the next "
                  "of the thirteen markers spawn an Apparition, ghost.scr; then the spawner stops), the acid grate.",
                  "local function wakeAll(list) for _, index in ipairs(list) do wake(index) end end",
                  "local function rise(group)",
                  "    evt.SetMonGroupBit(group, MonsterBits.Invisible, false)",
                  "    set(\"ZombiesRisen\", var(\"ZombiesRisen\") + 1)",
                  "end",
                  f"local MARKERS = {{{markers}}}",
                  "local function spawnGhost()",
                  "    local k = var(\"GhostsSpawned\") + 1",
                  "    if k > #MARKERS then return end",
                  "    set(\"GhostsSpawned\", k)",
                  "    local p = MARKERS[k]",
                  f"    evt.SummonMonstersById({{monster = {APPARITION}, x = p[1], y = p[2], z = p[3], radius = 32, "
                  f"group = {GROUP_GHOSTS}, count = 1, effect = \"mm9:fireblue\"}})   "
                  "-- :SpawnCreature: DoClientFX hDummy, SPELL_BLUEFIRE",
                  "end",
                  "local function grate()",
                  "    if var(\"GrateOpen\") == 1 then return end",
                  "    set(\"GrateOpen\", 1)",
                  "    openGroup(\"Gratetrap0\")",
                  f"    arm({T_GRATE_SHUT}, 5.5)",
                  "end",
                  f"handlers[{T_GRATE_SHUT}] = function()",
                  f"    if not fired({T_GRATE_SHUT}) then return end",
                  "    closeGroup(\"Gratetrap0\")",
                  "    set(\"GrateOpen\", 0)",
                  "end",
                  f"local ACID_BOX = {{{lua.point(pit_box[0])}, {lua.point(pit_box[1])}}}",
                  f"local RIM = {lua.point(rim)}",
                  "local VOLUMES = {",
                  volume_lua,
                  "}",
                  f"local SPIKE_BOX = {{{lua.point(spike_box[0])}, {lua.point(spike_box[1])}}}",
                  "local inside, polls = {}, 0",
                  f"handlers[{T_POLL}] = function()",
                  f"    evt.StartTimer({T_POLL}, seconds(0.25))",
                  "    for index in pairs(mummiesHit) do   -- OnDamage WakeUp, for a mummy that lived through the blow",
                  "        mummiesHit[index] = nil",
                  "        if MM9.actorAlive(index) then wake(index) end",
                  "    end",
                  "    local x, y, z = evt.GetPartyPosition()",
                  "    polls = polls + 1",
                  "    for _, v in ipairs(VOLUMES) do",
                  "        local armed = var(\"Done\" .. v.name) == 0",
                  "        if v.name == \"Trigger6\" and var(\"Trigger6On\") == 0 then armed = false end",
                  "        local now = inBox(v.box, x, y, z)",
                  "        if armed and now and not inside[v.name] then",
                  "            if not v.rearm then set(\"Done\" .. v.name, 1) end",
                  "            v.run()",
                  "        end",
                  "        inside[v.name] = now",
                  "    end",
                  "    if polls % 4 == 0 and inBox(SPIKE_BOX, x, y, z) then",
                  f"        hurt({PIT_SPIKE_DAMAGE}); set(\"PitSpikeHits\", var(\"PitSpikeHits\") + 1)",
                  "    end",
                  "    if inBox(ACID_BOX, x, y, z) and z < " + str(int(pit_box[1][2]) - 60) + " then",
                  f"        if polls % 4 == 0 then",
                  f"            evt.DamagePlayer(Players.All, const.Damage.Water, {ACID_DAMAGE})",
                  "            set(\"AcidSeconds\", var(\"AcidSeconds\") + 1)",
                  f"            if var(\"AcidSeconds\") % {ACID_SECONDS} == 0 then",
                  "                evt.StatusText(\"You claw your way out of the acid.\")",
                  "                set(\"AcidLifts\", var(\"AcidLifts\") + 1)",
                  "                evt.MoveToMap(RIM[1], RIM[2], RIM[3], 0, 0, 0, 0, 0)",
                  "            end",
                  "        end",
                  "    end",
                  "end"]
        script.add([], (T_POLL, "Trigger volumes", None, "timer"), (T_GRATE_SHUT, "Grate shuts", None, "timer"))
        # Quest objects.
        lines += ["",
                  "-- The quest objects are world items (dungeon/pickups.py): the Lich Instructions (447) give key 296;",
                  "-- the Crona Kiga's (390) pickup runs CronaKiga.scr's use.",
                  f"local CK = {{{', '.join(map(str, [names['PetrifiedMummy16']['index']]))}}}",
                  f"handlers[{EV_CRONA}] = function()   -- CronaKiga.scr, picked up (its CKTrigger awakens PetrifiedMummy16)",
                  "    wakeAll(CK)",
                  f"    if MM9.hasKey({KEY_CRONA_QUEST}) == 1 or MM9.hasKey({KEY_CRONA_FOUND}) == 1 then return end",
                  f"    if MM9.hasKey({KEY_LUDWIG}) == 1 then MM9.giveKey({KEY_CRONA_QUEST}) else MM9.giveKey({KEY_CRONA_FOUND}) end",
                  f"    {experience_lua(CRONA_EXPERIENCE, KEY_CRONA_QUEST)}",
                  "    MM9.playSound(\"sounds/events/quest.wav\")",
                  "end",
                  "",
                  "-- Shooter0 (OffRailTrigger.scr, PurpleThingy, DamageAmt 35): fires once at a party that leaves MM9's AI "
                  "rails; the map's only off-rail footing is the dais under it, a one-shot pad here.",
                  f"handlers[{EV_DAIS}] = function()",
                  "    if var(\"DaisShot\") == 1 then return end",
                  "    set(\"DaisShot\", 1)",
                  f"    shoot({', '.join(map(str, pos['Shooter0']))}, {DAIS_DAMAGE}, \"Dark\", \"PurpleThingy\")",
                  "end"]
        script.add([], (EV_CRONA, "Crona Kiga", None),
                   (EV_DAIS, "Dais shooter", None))
        # Load.
        lines += ["",
                  "handlers[1] = function()   -- map load: taken objects stay gone, the volumes start polling",
                  f"    evt.StartTimer({T_POLL}, seconds(0.25))",
                  "end"]
        script.add(lines, (1, "Map load", None))
        return script.finish(on_load=[1])

    def report(self, build) -> dict:
        return {"scripted": {"boxes": self.boxes, "points": self.points,
                             "mummies": self.mummies, "water": self.water_faces}}


if __name__ == "__main__":
    sys.exit(dungeon.main(PROJECT, Chasm()))
