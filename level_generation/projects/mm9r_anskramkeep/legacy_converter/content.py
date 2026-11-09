"""
Anskram Keep's population and scripts for convert.py: the props, torches and chests as BLV decoration entities
(props.json, from level_generation/props/mm9_anskramkeep_claude), the Imp gates' fires, MM9's touch triggers as
invisible pressure-plate pads, the 47 monsters as placed actors, the chests' loot records, and the map Lua that
wires MM9's plates, crushers, levers, gate, cages, Imp gates and the Giant Imp with native events. Every entity,
pad, mover and actor keeps its DAT object name as its anchor (work/content.json lists them). See README.md.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

import convert
import review_root
from convert import ROOT, SCALE, native

PROJECT = Path(__file__).resolve().parent
PROPS = PROJECT / "props.json"
OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/anskramkeep.scene.yml"

CHEST_EVENT = 41                    # chest k (loot container k) opens with event CHEST_EVENT + k
FIRE_COG = 200                      # the Imp gate fire k is evt.SetSprite key FIRE_COG + k
IMP_MONSTER = 9079                  # MM9 "Imp" (AK_ImpGate.scr params "Imp 5 ...": five Imps per gate)
IMPS_PER_GATE = 5
GATE_GROUP = 60                     # actors summoned by Imp gate k are in group GATE_GROUP + k
GROUPS = {"GiantImp": 51, "GiantImpGuard0": 52, "GiantImpGuard1": 52,
          "BustOutNagate0": 53, "BustOutNagate1": 53, "BustOutNagate2": 53,
          "BustOutIcky0": 54, "BustOutIcky1": 54, "BustOutIcky2": 54}
HIDDEN = {"GiantImp", "GiantImpGuard0", "GiantImpGuard1"}      # MM9 scripts clear FLAG_VISIBLE until "appear"
FRIENDLY = {"GiantImpGuard0", "GiantImpGuard1"}                # AK_GiantImpGuard.scr: AddFriend Player
INVISIBLE_BIT, AGGRESSOR_BIT = 0x00010000, 0x00080000
# The Giant Imp waits in the pit under the four Floordoor slabs (not built: README); it appears on the hall floor.
FLOOR_QUERY_LT = {"GiantImp": -150.0}

# Mover groups with events: (event, trigger type). Plates fire when stepped on, the rest on a click.
MOVER_EVENTS = {
    "ShooterPlate5": (60, "pressure_plate"), "ShooterPlate6": (61, "pressure_plate"),
    "ShooterPlate7": (62, "pressure_plate"), "ShooterPlate8": (63, "pressure_plate"),
    "ShooterPlate9": (64, "pressure_plate"), "ShooterPlate10": (65, "pressure_plate"),
    "CeilingCrushPlate1": (66, "pressure_plate"), "CeilingCrushPlate2": (67, "pressure_plate"),
    "CeilingCrushPlate3": (68, "pressure_plate"),
    "PivotTreasurePanel1": (70, "click"),
    "SwitchLever0": (71, "click"), "PanelLever": (72, "click"), "Switch0": (73, "click"), "Switch1": (74, "click"),
    # The pivot traps: stepping on the cross's floor springs it (MM9: PivotWallTrapTrigger on that half), the hatch
    # opens on a click from the ladder, the button in the niche springs the trap too.
    "PivotWallTrap1": (77, "pressure_plate"), "PivotWallTrap2": (78, "pressure_plate"),
    "PivotWallTrap3": (79, "pressure_plate"),
    "TrapExitDoor1": (80, "click"), "TrapExitDoor2": (81, "click"), "TrapExitDoor3": (82, "click"),
    "PivotButton1": (83, "click"), "PivotButton2": (84, "click"), "PivotButton3": (85, "click"),
}
# The spike pits under the traps: MM9 PropDamagers (20 per second): a pad on the pit floor.
SPIKE_PADS = {"Spikes14": 86, "Spikes16": 87, "Spikes17": 88}
SPIKE_DAMAGE = 20
SPIKE_HALF_LT = (40.0, 16.0, 40.0)
TRAP_CYCLE_SECONDS = 8              # opens in 0.9 s, waits 5 s, closes in 1.8 s; then it is armed again
# MM9 trigger volumes (DAT Trigger objects) as pressure-plate pads: name -> event. The handler is chosen by the
# trigger's first target (TargetName1).
PAD_EVENTS = {"TriggerNagateBust": 75, "TriggerIckyBust": 76, "TriggerGiantImp": 90}
GATE_TRIGGER_EVENT = 170            # TriggerClosetGate* and TriggerBarrackGate*: 170, 171, ... in DAT order
KILL_HOOK_EVENT = 95                # runs on every monster kill (the Imp gates' next Imp)
# Timers: 150-161 (plate resets, crusher strikes and rises).
# Shooter plates: plate -> (shooter, damage): MM9 Door OpenTrigger0 "on" of a Shooter (FireBolt, DamageAmt).
SHOOTERS = {"ShooterPlate5": "Shooter5", "ShooterPlate6": "Shooter6", "ShooterPlate7": "Shooter7",
            "ShooterPlate8": "Shooter8", "ShooterPlate9": "CeilingShooter1", "ShooterPlate10": "CeilingShooter0"}
CRUSHERS = {"CeilingCrushPlate1": "CeilingCrush1", "CeilingCrushPlate2": "CeilingCrush2",
            "CeilingCrushPlate3": "CeilingCrush3"}
CRUSH_DAMAGE = 20                   # MM9 PropDamager Spikes18-20 under the crushers: DamagePerSecond 20
GAME_SECONDS_PER_SECOND = 30        # map timers run on game time: 30 game seconds per real second
PAD_LIFT = 3                        # a trigger pad stands this far over its floor, so it is the floor the party stands on


def lt_from_native(point) -> np.ndarray:
    x, y, z = point
    return np.array([x / SCALE, z / SCALE, y / SCALE], float)


def decoration_ids() -> dict:
    """Decoration list ids by name from the review root's tables as the engine merges them (engine rows, then the MM9
    world's contribution, game/content/WorldDecorations.cpp)."""
    world = yaml.safe_load(review_root.mirror_path("worlds/mm9/world.yml").read_text())
    tables = ["engine/data_tables/decoration_data.txt"] + [
        "worlds/mm9/" + c["path"] for c in world.get("tableContributions", []) if c.get("table") == "decorations"]
    ids = {}
    for table in tables:
        for cells in (line.split("\t") for line in review_root.mirror_path(table).read_text(encoding="latin-1")
                      .splitlines()):
            if len(cells) > 1 and cells[0].strip().isdigit():
                ids[cells[1].strip().lower()] = int(cells[0]) - 1
    return ids


class Content:
    def __init__(self, source, polygons, package, rooms, grid):
        self.source, self.polygons, self.package, self.rooms, self.grid = source, polygons, package, rooms, grid
        self.ids = decoration_ids()
        self.report = {"decorations": [], "pads": [], "actors": [], "chests": [], "gates": []}
        self.floors = [p for p in polygons if p.normal[1] >= 0.7 and p.role == "static"]
        self.floor_low = np.array([p.points.min(0)[[0, 2]] for p in self.floors])
        self.floor_high = np.array([p.points.max(0)[[0, 2]] for p in self.floors])
        self.gates = []                 # Imp gate k: {spawner, fire, position}
        self.gate_triggers = {}         # event -> gate index

    # --- Decorations -----------------------------------------------------------------------------------------------
    def entity(self, anchor: str, decoration: str, position, facing: float, primary: int = 0, secondary: int = 0):
        name = decoration.lower()
        if name not in self.ids:
            raise SystemExit(f"decoration {name} has no row in the review root's tables (run the props tables.py)")
        if anchor.lower() in self.ids:
            raise SystemExit(f"entity {anchor} would resolve as the decoration of that name")
        node = f"DECOR_{anchor}"
        position = np.asarray(position, float)
        self.package.marker(node, position, next(iter(self.package.materials)))
        owner = convert.owner_room(self.rooms, self.grid, lt_from_native(position + [0, 0, 24]))
        self.package.room_nodes[owner].append(node)
        record = {"id": anchor, "kind": "decoration", "source_node": node, "decoration_list_id": self.ids[name],
                  "event_id_primary": primary, "event_id_secondary": secondary}
        if int(round(facing)) % 360:
            record["facing"] = int(round(facing)) % 360
        self.package.metadata["entities"].append(record)
        self.report["decorations"].append({"anchor": anchor, "decoration": name, "room": owner,
                                           "position": [int(round(v)) for v in position], "event": secondary,
                                           "cog": primary})

    def decorations(self, loot: list[dict]):
        """props.json entries (props, torches, barrels, bone piles, chests) and the Imp gate fires."""
        chest_index = {record["source_object_index"]: record["container_id"] for record in loot}
        for entry in json.loads(PROPS.read_text()):
            secondary = 0
            if entry["kind"] == "chest":
                secondary = CHEST_EVENT + chest_index[entry["source_object"]]
            self.entity(entry["source_name"], entry["decoration"], (entry["x"], entry["y"], entry["z"]),
                        entry["yaw_degrees"], secondary=secondary)
        # The spike pits under the traps stand on their pit floors (MM9 PropDamager Spikes14/16/17, scale 1.3).
        for name in SPIKE_PADS:
            pos = self.source.by_name[name.lower()]["properties"]["Pos"]
            self.entity(name, "mm9_spikepit", native([pos[0], self.floor_at(pos[0], pos[2], pos[1]), pos[2]]), 0)
        spawners = {o["name"]: o for o in self.source.objects if o["class"] == "Fish"
                    and str(o["properties"].get("ScriptName", "")).lower().endswith("ak_impgate.scr")}
        for name in sorted(spawners, key=lambda n: int(n[len("ImpGateSpawner"):])):
            params = spawners[name]["properties"]["ScriptParams"].split()        # "Imp 5 killed ImpGateFire0"
            fire = self.source.by_name[params[3].lower()]
            spawn = spawners[name]["properties"]["Pos"]
            spawn_floor = self.floor_at(spawn[0], spawn[2], spawn[1] + 40)
            # MM9's fire burns in the sealed alcove behind the gate (floor 112 below the hall; not built): it stands
            # on the hall floor at the gate's mouth, the farthest point toward it that is still on that floor.
            pos = fire["properties"]["Pos"]
            for t in (0.8, 0.6, 0.4, 0.2, 0.0):
                x, z = spawn[0] + t * (pos[0] - spawn[0]), spawn[2] + t * (pos[2] - spawn[2])
                floor = self.floor_at(x, z, spawn[1] + 40)
                if floor is not None and abs(floor - spawn_floor) < 0.5:
                    break
            k = len(self.gates)
            self.entity(fire["name"], "mm9_gatefire", native([x, floor, z]), 0, primary=FIRE_COG + k)
            self.gates.append({"spawner": name, "fire": fire["name"], "count": int(params[1]),
                               "position": native([spawn[0], spawn_floor, spawn[2]]).round().astype(int).tolist()})
        self.report["gates"] = self.gates

    # --- Floors and pads -------------------------------------------------------------------------------------------
    def floor_at(self, x, z, y_from):
        near = np.nonzero((self.floor_low[:, 0] <= x) & (x <= self.floor_high[:, 0]) & (self.floor_low[:, 1] <= z)
                          & (z <= self.floor_high[:, 1]))[0]
        return convert.floor_below([self.floors[i] for i in near], (x, y_from, z))

    def pads(self):
        """Each MM9 touch trigger becomes an invisible pressure-plate face PAD_LIFT units over the floor under it: the
        trigger's footprint (Dims are half extents), shrunk until every sample over it stands on the same floor
        in the same room (so it never pokes through a wall)."""
        gate_index = {g["spawner"]: k for k, g in enumerate(self.gates)}
        triggers = [o for o in self.source.objects if o["class"] == "Trigger"]
        for o in triggers:
            p = o["properties"]
            target = str(p.get("TargetName1", ""))
            if o["name"] in PAD_EVENTS:
                event = PAD_EVENTS[o["name"]]
            elif target.startswith("ImpGateSpawner"):
                event = GATE_TRIGGER_EVENT + len(self.gate_triggers)
                self.gate_triggers[event] = gate_index[target]
            else:
                continue                # plate triggers: the plates themselves are pressure plates (MOVER_EVENTS)
            self.pad(o["name"], p["Pos"], p["Dims"], event)
        for name, event in SPIKE_PADS.items():
            self.pad(name, self.source.by_name[name.lower()]["properties"]["Pos"], SPIKE_HALF_LT, event)

    def fits(self, x0, z0, hx, hz, centre_floor, owner) -> bool:
        for sx in np.linspace(-1, 1, 7):
            for sz in np.linspace(-1, 1, 7):
                x, z = x0 + sx * hx, z0 + sz * hz
                floor = self.floor_at(x, z, centre_floor + 40)
                if floor is None or abs(floor - centre_floor) > 0.5 or convert.owner_room(
                        self.rooms, self.grid, np.array([x, floor + 20, z])) != owner:
                    return False
        return True

    def pad(self, name, pos, dims, event):
        """A trigger in a doorway (the barrack gates' triggers stand in their door frames) straddles two rooms: its
        pad moves to one side of the doorway (half its size off centre) when the centred one does not fit."""
        px, y0, pz = pos
        centre_floor = self.floor_at(px, pz, y0 + dims[1])
        found = None
        for shrink in (1.0, 0.85, 0.7, 0.55, 0.4, 0.3, 0.2):
            hx, hz = dims[0] * shrink, dims[2] * shrink
            for dx, dz in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                x0, z0 = px + dx * dims[0] * 0.5, pz + dz * dims[2] * 0.5
                owner = convert.owner_room(self.rooms, self.grid, np.array([x0, centre_floor + 20, z0]))
                if self.fits(x0, z0, hx, hz, centre_floor, owner):
                    found = (x0, z0, hx, hz, owner)
                    break
            if found:
                break
        if found is None:
            raise SystemExit(f"trigger {name}: no floor under it")
        x0, z0, hx, hz, owner = found
        corners = [native([x0 + sx * hx, centre_floor, z0 + sz * hz]) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        points = np.round(np.array(corners)).astype(int) + np.array([0, 0, PAD_LIFT])
        normal = np.cross(points[1] - points[0], points[2] - points[0])
        if normal[2] < 0:
            points = points[::-1]
        node = f"TRIGGER_{name}"
        self.package.add_raw(node, points, next(iter(self.package.materials)))
        self.package.room_nodes[owner].append(node)
        self.package.metadata["surfaces"].append({"id": name, "source_node": node, "flags": ["invisible"],
                                                  "trigger": {"event_id": event, "type": "pressure_plate"}})
        centre = points.mean(0).round().astype(int).tolist()
        self.report["pads"].append({"anchor": name, "event": event, "room": owner, "centre": centre,
                                    "size": [round(2 * hx * SCALE), round(2 * hz * SCALE)],
                                    "z": int(points[0][2])})

    # --- Actors and chests -----------------------------------------------------------------------------------------
    def actors(self, sector_of_room: dict) -> list[dict]:
        """The old scene's MM9 actor records (monster rows with the MM9 family pictures), at their DAT positions on
        the floor, with the scripted ones grouped, hidden or friendly."""
        old = yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["actors"]
        by_object = {self.source.objects[a["mm9_source_object_index"]]["name"]: a for a in old}
        out = []
        for o in self.source.objects:
            if o["class"] not in convert.MONSTER_CLASSES:
                continue
            a = by_object[o["name"]]
            p = o["properties"]
            floor = self.floor_at(p["Pos"][0], p["Pos"][2], FLOOR_QUERY_LT.get(o["name"], p["Pos"][1]))
            position = native([p["Pos"][0], floor, p["Pos"][2]]).round().astype(int)
            position[2] += 1
            room = convert.owner_room(self.rooms, self.grid, np.array([p["Pos"][0], floor + 20, p["Pos"][2]]))
            from transcode_mm9_dat_to_odm import lt_rotation_to_openyamm_yaw_degrees
            yaw = lt_rotation_to_openyamm_yaw_degrees(p.get("Rotation", [0, 0, 0, 0]))
            attributes = a["attributes"]
            hostility = a["hostility_type"]
            if o["name"] in HIDDEN:
                attributes |= INVISIBLE_BIT
            if o["name"] in FRIENDLY:
                attributes &= ~AGGRESSOR_BIT
                hostility = 0
            scale = float(p.get("Scale", 1.0))
            hp, radius, height = a["hp"], a["radius"], a["height"]
            if o["name"] == "GiantImp":          # AK_GiantImp.scr: SetStat HitPoints 100; the DAT Scale 2
                hp, radius, height = 100, int(radius * scale), int(height * scale)
            out.append({"actor_index": len(out), "name": a["name"], "npc_id": 0, "attributes": attributes,
                        "hp": hp, "hostility_type": hostility, "monster_info_id": a["monster_info_id"],
                        "monster_id": a["monster_id"], "radius": radius, "height": height,
                        "move_speed": a["move_speed"],
                        "position": {k: int(v) for k, v in zip(("x", "y", "z"), position)},
                        "initial_yaw_units": int(round(yaw % 360 / 360 * 2048)) % 2048, "immobile": False,
                        "sprite_ids": [0, 0, 0, 0], "sector_id": sector_of_room[room], "current_action_animation": 0,
                        "carried_item_id": 0, "group": GROUPS.get(o["name"], 0), "ally": 0,
                        "unique_name_index": 0})
            self.report["actors"].append({"actor_index": out[-1]["actor_index"], "anchor": o["name"],
                                          "class": o["class"], "monster_id": a["monster_id"], "room": room,
                                          "group": out[-1]["group"], "hidden": o["name"] in HIDDEN,
                                          "friendly": o["name"] in FRIENDLY})
        return out

    def loot(self) -> list[dict]:
        """The old scene's chest records (treasure type and level, trap level, repopulate), in this map's frame (the
        same frame: no offset), container k in their old order."""
        out = []
        for record in yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["loot_containers"]:
            record = dict(record)
            record.pop("world_visual", None)
            out.append(record)
            self.report["chests"].append({"container_id": record["container_id"], "anchor": record["source_name"],
                                          "event": CHEST_EVENT + record["container_id"],
                                          "treasure_level": record["random_treasure_level"],
                                          "trap_level": record["trap_level"]})
        return out


# --- Lua ----------------------------------------------------------------------------------------------------------

def lua_point(point) -> str:
    return "{" + ", ".join(str(int(round(v))) for v in point) + "}"


def map_script(movers: list[dict], content: Content, source) -> str:
    door = {m["node"][5:]: m["door_id"] for m in movers}
    groups = defaultdict(list)
    for m in movers:
        groups[m["group"]].append(m["door_id"])
    obj = {o["name"]: o["properties"] for o in source.objects}
    timer = 150
    lines = [
        "-- Anskram Keep, MM9 rework (level_generation/projects/mm9r_anskramkeep/convert.py writes this file).",
        "-- MM9's doors, plates, crushers, levers, gate, cages, Imp gates and Giant Imp as native events; every",
        "-- door, pad and decoration is named by its DAT object (see work/content.json and README.md).",
        "local handlers = {}",
        "local DOORS = {" + ", ".join(f"{k} = {v}" for k, v in sorted(door.items())) + "}",
        "local function open(name) evt.SetDoorState(DOORS[name], DoorAction.Open) end",
        "local function close(name) evt.SetDoorState(DOORS[name], DoorAction.Close) end",
        "local function var(name) return evt.GetMapVar(name, 0) end",
        "local function set(name, value) evt.SetMapVar(name, value) end",
        "local function hidden(group, state) evt.SetMonGroupBit(group, MonsterBits.Invisible, state) end",
        "local function seconds(n) return n * " + str(GAME_SECONDS_PER_SECOND) + " end",
        "-- A Shooter sits inside its wall or ceiling: the bolt starts a third of the way from it to the party's",
        "-- chest (at least 64 units out), inside the room.",
        "local function shoot(sx, sy, sz, damage)",
        "    local x, y, z = evt.GetPartyPosition()",
        "    z = z + 100",
        "    local dx, dy, dz = x - sx, y - sy, z - sz",
        "    local length = math.max(1, math.sqrt(dx * dx + dy * dy + dz * dz))",
        "    local k = math.max(64 / length, 0.33)",
        "    local fired = evt.FireMissile(\"Fire\", sx + dx * k, sy + dy * k, sz + dz * k, x, y, z, damage, \"Fire\", 0)",
        "    set(\"ShotsFired\", var(\"ShotsFired\") + (fired and 1 or 0))",
        "end",
        "",
    ]
    opened = ", ".join(f"[{CHEST_EVENT + c['container_id']}] = {{{c['container_id']}}}" for c in content.report["chests"])
    lines.append(f"SetMapMetadata({{onLoad = {{1}}, onLeave = {{}}, timers = {{}}, openedChestIds = {{{opened}}}}})")
    lines.append("")
    registrations = []

    lines.append("-- Doors: each MM9 door group opens and closes on a click (the gate's leaves open only by its switches).")
    door_events = sorted({(m["event"], m["group"]) for m in movers if m["event"] and m["group"] not in MOVER_EVENTS})
    for event, group in door_events:
        calls = " ".join(f"evt.SetDoorState({d}, DoorAction.Trigger)" for d in groups[group])
        lines.append(f"handlers[{event}] = function() {calls} end   -- {group}")
        registrations.append((event, "Door", "Door"))
    lines.append("")

    lines.append("-- Chests (MM9 TreasureChest objects; loot records in the scene).")
    for c in content.report["chests"]:
        lines.append(f"handlers[{c['event']}] = function() evt.OpenChest({c['container_id']}) end   -- {c['anchor']}")
        registrations.append((c["event"], "Chest", "Chest"))
    lines.append("")

    lines.append("-- Shooter plates: the plate sinks and its Shooter fires a fire bolt at the party (MM9 FireBolt, "
                 "DamageAmt); the plate rises after 3 s (CloseWaitTime).")
    for plate, shooter in SHOOTERS.items():
        event = MOVER_EVENTS[plate][0]
        reset = timer
        timer += 1
        sp = obj[shooter]
        origin = native(sp["Pos"])
        damage = int(round(float(sp.get("DamageAmt", 5))))
        lines += [f"handlers[{event}] = function()   -- {plate} -> {shooter}",
                  f"    if var(\"{plate}\") == 1 then return end",
                  f"    set(\"{plate}\", 1)",
                  f"    open(\"{plate}\")",
                  f"    shoot({', '.join(str(int(round(v))) for v in origin)}, {damage})",
                  f"    evt.StartTimer({reset}, seconds(3))",
                  "end",
                  f"handlers[{reset}] = function() evt.StopTimer({reset}); close(\"{plate}\"); set(\"{plate}\", 0) end"]
        registrations.append((event, plate, plate))
        registrations.append((reset, f"{plate} reset", None))
    lines.append("")

    lines.append(f"-- Ceiling crushers: the plate sinks, the crusher drops (MM9 Speed 300, MoveDist 176), its spikes hurt "
                 f"a party under it ({CRUSH_DAMAGE}, MM9 Spikes18-20), and it rises after 3 s.")
    for plate, crusher in CRUSHERS.items():
        event = MOVER_EVENTS[plate][0]
        hit, rise = timer, timer + 1
        timer += 2
        model = np.array(source.models[crusher].points)
        low, high = native(model.min(0)), native(model.max(0))
        x0, x1 = sorted((low[0], high[0]))
        y0, y1 = sorted((low[1], high[1]))
        lines += [f"handlers[{event}] = function()   -- {plate} -> {crusher}",
                  f"    if var(\"{crusher}\") == 1 then return end",
                  f"    set(\"{crusher}\", 1)",
                  f"    open(\"{plate}\")",
                  f"    open(\"{crusher}\")",
                  f"    evt.StartTimer({hit}, seconds(0.7))",
                  "end",
                  f"handlers[{hit}] = function()",
                  f"    evt.StopTimer({hit})",
                  f"    if var(\"{crusher}\") ~= 1 then return end",
                  "    local x, y = evt.GetPartyPosition()",
                  f"    if x >= {int(x0) - 40} and x <= {int(x1) + 40} and y >= {int(y0) - 40} and y <= {int(y1) + 40} "
                  f"then evt.DamagePlayer(Players.All, const.Damage.Physical, {CRUSH_DAMAGE}); "
                  f"set(\"CrushHits\", var(\"CrushHits\") + 1) end",
                  f"    evt.StartTimer({rise}, seconds(2.3))",
                  "end",
                  f"handlers[{rise}] = function() evt.StopTimer({rise}); close(\"{crusher}\"); close(\"{plate}\"); "
                  f"set(\"{crusher}\", 0) end"]
        registrations += [(event, plate, plate), (hit, f"{crusher} strike", None), (rise, f"{crusher} rise", None)]
    lines.append("")

    lines += ["-- The treasure panel beside PivotWallTrap1 slides up (MM9 Sticky, PushOpen) to show TreasureChest1.",
              f"handlers[70] = function() open(\"PivotTreasurePanel1\") end"]
    lines.append("")
    lines.append("-- Pivot traps: the cross turns 90 degrees and tips the party into the pit; MM9's CloseWaitTime turns it back")
    lines.append("-- (the mover's auto-close), then it is armed again. A ladder climbs to the hatch beside it.")
    for k in (1, 2, 3):
        trap, button, hatch = f"PivotWallTrap{k}", f"PivotButton{k}", f"TrapExitDoor{k}"
        event = MOVER_EVENTS[trap][0]
        reset = timer
        timer += 1
        lines += [f"handlers[{event}] = function()   -- {trap}",
                  f"    if var(\"{trap}\") == 1 then return end",
                  f"    set(\"{trap}\", 1)",
                  f"    open(\"{trap}\")",
                  f"    open(\"{button}\")",
                  f"    evt.StartTimer({reset}, seconds({TRAP_CYCLE_SECONDS}))",
                  "end",
                  f"handlers[{reset}] = function() evt.StopTimer({reset}); close(\"{button}\"); set(\"{trap}\", 0) end",
                  f"handlers[{MOVER_EVENTS[button][0]}] = function() handlers[{event}]() end   -- {button}",
                  f"handlers[{MOVER_EVENTS[hatch][0]}] = function() open(\"{hatch}\") end   -- {hatch}"]
        registrations += [(event, trap, None), (reset, f"{trap} reset", None), (MOVER_EVENTS[button][0], button, button),
                          (MOVER_EVENTS[hatch][0], hatch, "Hatch")]
    for name, event in SPIKE_PADS.items():
        lines.append(f"handlers[{event}] = function() evt.DamagePlayer(Players.All, const.Damage.Physical, "
                     f"{SPIKE_DAMAGE}); set(\"SpikeHits\", var(\"SpikeHits\") + 1) end   -- {name}")
        registrations.append((event, name, None))
    registrations.append((70, "Panel", "Panel"))
    lines += ["",
              "-- The gate is an airlock: the outer leaves stand apart (built shut, starting open) and the inner ones shut.",
              "-- SwitchLever0 slides LeverPanel and LeverPanel0 aside, PanelLever unlocks Switch0 and Switch1, and either",
              "-- switch shuts the outer gate and opens the inner one (MM9: one after the other), or the reverse.",
              "handlers[71] = function()",
              "    if var(\"SwitchLever0\") == 1 then return end",
              "    set(\"SwitchLever0\", 1)",
              "    open(\"SwitchLever0\"); open(\"LeverPanel\"); open(\"LeverPanel0\")",
              "end",
              "handlers[72] = function()",
              "    if var(\"PanelLever\") == 1 then return end",
              "    set(\"PanelLever\", 1)",
              "    open(\"PanelLever\")",
              "end",
              "local function gateSwitch(name)",
              "    if var(\"PanelLever\") == 0 then evt.StatusText(\"The switch is locked.\") return end",
              "    if var(\"Gate\") == 0 then",
              "        set(\"Gate\", 1)",
              "        open(\"Switch0\"); open(\"Switch1\")",
              "        close(\"Outerdoor0\"); close(\"Outerdoor1\"); open(\"Innerdoor0\"); open(\"Innerdoor1\")",
              "    else",
              "        set(\"Gate\", 0)",
              "        close(\"Switch0\"); close(\"Switch1\")",
              "        open(\"Outerdoor0\"); open(\"Outerdoor1\"); close(\"Innerdoor0\"); close(\"Innerdoor1\")",
              "    end",
              "end",
              "handlers[73] = function() gateSwitch(\"Switch0\") end",
              "handlers[74] = function() gateSwitch(\"Switch1\") end",
              ""]
    registrations += [(71, "Lever", "Lever"), (72, "Lever", "Lever"), (73, "Switch", "Switch"), (74, "Switch", "Switch")]

    lines += ["-- The cages: stepping near them breaks the walls (CritterBreakOut0/1 sink into the floor and wall) and the",
              "-- caged Nagate Hatchlings and Airborne Ickies (KingKong.scr) come out.",
              "handlers[75] = function() if var(\"TriggerNagateBust\") == 0 then set(\"TriggerNagateBust\", 1); "
              "open(\"CritterBreakOut0\") end end",
              "handlers[76] = function() if var(\"TriggerIckyBust\") == 0 then set(\"TriggerIckyBust\", 1); "
              "open(\"CritterBreakOut1\") end end",
              ""]
    registrations += [(75, "TriggerNagateBust", None), (76, "TriggerIckyBust", None)]

    lines += [f"-- The Imp gates (AK_ImpGate.scr on ImpGateSpawner0-7): a touch trigger starts its gate; it sends "
              f"{IMPS_PER_GATE} Imps one",
              "-- after another, each when the last is dead; then its fire goes out. When all eight are out, the Giant Imp",
              "-- (AK_GiantImp.scr) and its two guards (AK_GiantImpGuard.scr, friends of the party) appear when the party",
              "-- crosses TriggerGiantImp in the north hall. Gate states: 0 waiting, 1 sending, 2 done.",
              "local GATES = {"]
    for k, gate in enumerate(content.gates):
        lines.append(f"    [{k}] = {{position = {lua_point(gate['position'])}, count = {gate['count']}}},   "
                     f"-- {gate['spawner']}, {gate['fire']}")
    lines += ["}",
              "local function sendImp(k)",
              "    local gate = GATES[k]",
              f"    local sent = evt.SummonMonstersById({{monster = {IMP_MONSTER}, x = gate.position[1], "
              f"y = gate.position[2], z = gate.position[3], radius = 64, group = {GATE_GROUP} + k, count = 1}})",
              "    set(\"ImpsSummoned\", var(\"ImpsSummoned\") + sent)",
              "    set(\"ImpGateSent\" .. k, var(\"ImpGateSent\" .. k) + 1)",
              "end",
              "local function startGate(k)",
              "    if var(\"ImpGate\" .. k) ~= 0 then return end",
              "    set(\"ImpGate\" .. k, 1)",
              "    sendImp(k)",
              "end"]
    for event, k in sorted(content.gate_triggers.items()):
        anchor = next(p["anchor"] for p in content.report["pads"] if p["event"] == event)
        lines.append(f"handlers[{event}] = function() startGate({k}) end   -- {anchor} -> {content.gates[k]['spawner']}")
        registrations.append((event, anchor, None))
    lines += [f"handlers[{KILL_HOOK_EVENT}] = function()   -- any monster killed",
              f"    for k = 0, {len(content.gates) - 1} do",
              f"        if var(\"ImpGate\" .. k) == 1 and evt.CheckMonstersKilled(ActorKillCheck.Group, {GATE_GROUP} + k, 0, "
              "false) then",
              "            if var(\"ImpGateSent\" .. k) < GATES[k].count then",
              "                sendImp(k)",
              "            else",
              "                set(\"ImpGate\" .. k, 2)",
              f"                evt.SetSprite({FIRE_COG} + k, false)",
              "                set(\"ImpGatesDone\", var(\"ImpGatesDone\") + 1)",
              "            end",
              "        end",
              "    end",
              "end",
              "handlers[90] = function()   -- TriggerGiantImp",
              f"    if var(\"GiantImp\") == 1 or var(\"ImpGatesDone\") < {len(content.gates)} then return end",
              "    set(\"GiantImp\", 1)",
              "    hidden(51, false)",
              "    hidden(52, false)",
              "end",
              "handlers[1] = function()   -- map load: fires of the finished gates stay out",
              f"    for k = 0, {len(content.gates) - 1} do",
              f"        if var(\"ImpGate\" .. k) == 2 then evt.SetSprite({FIRE_COG} + k, false) end",
              "    end",
              "end",
              ""]
    registrations.append((90, "TriggerGiantImp", None))

    for event, title, hint in registrations:
        if title.endswith(("reset", "strike", "rise")):
            lines.append(f'RegisterMapTimerEvent({event}, seconds(3), handlers[{event}], "{title}", "", seconds(3))')
        elif hint:
            lines.append(f'RegisterEvent({event}, "{title}", handlers[{event}], "{hint}")')
        else:
            lines.append(f'RegisterEvent({event}, "{title}", handlers[{event}])')
    lines.append(f'RegisterMonsterKilledHook({KILL_HOOK_EVENT}, "Imp gates", handlers[{KILL_HOOK_EVENT}])')
    lines.append('RegisterEvent(1, "Map load", handlers[1])')
    return "\n".join(lines) + "\n"
