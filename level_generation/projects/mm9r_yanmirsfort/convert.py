#!/usr/bin/env python3
"""
Yanmir's Fort, MM9 rework: MM9's YANMIRSFORT.dat as a native BLV on the shared dungeon converter
(../mm9r_common/dungeon, ../mm9r_common/DUNGEON_PLAYBOOK.md).

    python3 level_generation/projects/mm9r_yanmirsfort/convert.py            # build, compile, install (review root)
    python3 level_generation/projects/mm9r_yanmirsfort/convert.py --plan     # rooms only: work/rooms*.png

overrides.yml holds the model rules (the double doors, the cages, the teleporter doors, the secret wall, the trap's
supports and floors), the seed exclusions and the exits; this file adds the population (props.json from
../../props/mm9_yanmirsfort_claude, the monsters with MM9's bodies, the children) and MM9's scripted objects as native
Lua, each citing its .scr (README.md, "Scripted objects"):
- Yanmir (YanmirBase.scr): immune to all damage (Reset: CanDamage FALSE), asleep until the party walks into
  SquishTrigger0/1 ("Squish" -> Begin); YanmirTrap.scr: six wooden supports under the trap hall (DestructableBrush0-5,
  their PerceptionBrushes 2-7) broken arm TriggerYanmirTrap; Yanmir walking into it (TimeToDie) brings the hall's floor
  down (YF_ExplodingFloor.scr, YF_FallingFloor.scr, Planks0, Xbeams0), gives the quest key 69 (on key 68) or 173 and
  8 000 experience, and he falls to the end of the world (Yanmir_EndOfWorld.scr removes him; a party that falls goes to
  Frosgard City, PlayerExit "FallingStart");
- the Forest Giants (YanmirHidden.scr): hidden while Yanmir lives, there from the next load after his fall;
- Yanmir's key (YanmirKey.scr): item 570 and key 7001, which unlock the teleporter doors and the children's cages;
- the children (YanmirChild.scr): with key 7001 a click sends a child to the teleporter (TPS2); they call for help
  (RolloverText 200/201) the first time the party comes near;
- the secret wall (Secretdoor: OpenTrigger "lock", it stays open; PerceptionBrush0);
- the spawners: Trigger6-10 and the deaths of nine Yetis (DeathTriggerTarget Spawner0-5) send a Yeti (Spawner6 a
  Thrall) from their spawner; YanmirFort_BugSpawn.scr: an Ice Lobbercicle killed near Respawn0-3 comes back there 10-15
  minutes later, out of the party's sight.

MM9's Trigger volumes are boxes polled four times a second (Verhoffin Ruins', the Chasm's and Ta'Sar's route).
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import numpy as np

PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
import dungeon  # noqa: E402
import liquids  # noqa: E402
from dungeon import lua  # noqa: E402
from dungeon.geometry import Polygon  # noqa: E402
from dungeon.package import room_id  # noqa: E402
from dungeon.rooms import _side_room  # noqa: E402
from dungeon.source import ROOT, SCALE  # noqa: E402
from dungeon.bodies import placed_body  # noqa: E402
from quest_xp import balanced_experience  # noqa: E402
import cutscenes  # noqa: E402
import cutscene  # noqa: E402
from script_text import rollover_text  # noqa: E402  (MMIXSCRIPTTEXT.csv)

PROPS = PROJECT / "props.json"

# --- Events, timers, cogs, groups ------------------------------------------------------------------------------------
EV_LOAD = 1
EV_SUPPORT = 200                                  # support k (DestructableBrush k): EV_SUPPORT + k
EV_SECRET, EV_TELEPORT = 210, 211
EV_CAGE = 220                                     # cage k (RotatingDoor61 + k): EV_CAGE + k
EV_KILLED, EV_DAMAGED = 240, 241                  # monster killed / damage hooks
T_POLL, T_FALL = 150, 151
COG_HINT = 450                                    # PerceptionBrush k: COG_HINT + k
GROUP_YANMIR, GROUP_GIANTS, GROUP_CHILDREN, GROUP_SPAWNED, GROUP_BUGS = 1, 2, 3, 4, 5

SUPPORTS = [f"DestructableBrush{k}" for k in range(6)]
# Each support's DeathTriggerTarget relay and the PerceptionBrush that relay turns off (Trigger0-5).
SUPPORT_HINT = {"DestructableBrush0": "PerceptionBrush2", "DestructableBrush1": "PerceptionBrush5",
                "DestructableBrush2": "PerceptionBrush3", "DestructableBrush3": "PerceptionBrush6",
                "DestructableBrush4": "PerceptionBrush4", "DestructableBrush5": "PerceptionBrush7"}
HINTS = [f"PerceptionBrush{k}" for k in range(8)]
HINT_EVENTS = {SUPPORT_HINT[name]: EV_SUPPORT + k for k, name in enumerate(SUPPORTS)}
HINT_EVENTS["PerceptionBrush0"] = EV_SECRET
CAGES = [f"RotatingDoor{61 + k}" for k in range(7)]
PERCEPTION_SKILL = 29                             # evt.CheckSkill's id: the party's best Perception value
PERCEPTION_OPACITY = 0.5                          # the brushes' Alpha
POOL_OPACITY = 0.7                                # BlueWater0 SurfaceAlpha
PORTAL_OPACITY = 0.85                             # the exit gates' Water115 sheets (WavySurface4/5, brush Alpha 1)
UNTOUCHABLE = 0x20000000
PARTY_REACH = 32                                  # native: MM9's touch fires on any part of the party

# YanmirKey.scr, Yanmir.scr / YanmirBase.scr :GiveEeps, YanmirChild.scr
KEY_CAGES, ITEM_KEY = 7001, 570
KEY_QUEST, KEY_QUEST_DONE, KEY_FREE = 68, 69, 173
EXP_TRAP, EXP_DEATH = 8000, 5000
CHILD_SIGHT = 600                                 # SightDistance (LT)
BUG_RESPAWN_MIN, BUG_RESPAWN_MAX = 600, 900       # YanmirFort_BugSpawn.scr MIN/MAX_SPAWN_TIME (s)
KICK_REACH = 700                                  # native: Yanmir's reach for a door kick (his radius 154 + a stride)
KICK_CHECK = 0.5                                  # s: the door kicks are checked every other poll (T_POLL, 0.25 s)
BUG_SIGHT = 2000                                  # native: "the player can't see this happen" (no LOS test here)

# MM9's bodies: the ABC's first AnimBinding extents (half sizes, LT) by MONSTERS.txt row name x Scale x 2.56.
CHILD_EXTENTS = (10.0, 26.0)                      # PeasantChildBoy.abc
CHILD_ROW = 367                                   # Peasant Human2 MaleA (as Drangheim's prisoners): a friendly body
CHILD_RUDE = 433                                  # the children's NPCNbr (433.0 as a float): RUDE 433 "Child"
                                                  # (432 is the Afterworld's Questioner)
SPAWNER_CLASS = {"Yeti": "Yeti", "Thrall": "Thrall"}
POOL_MODEL, POOL_TEXTURE, POOL_TILE = "BlueWater0", "water:pool", 64.0
# A party under the trap hall's floor level once the trap has fired (on the fallen floor, 399 LT down: the movers stop
# there to keep their baked light) has fallen through: MM9's EndOfWorldTrigger at the shaft's bottom sends it on.
FALL_BOX_LT = ((-32, -3584, -4240), (416, -300, -2560))


def as_float(value) -> float:
    """A DAT float stored in an int property (PerceptionValue 1092616192 = 10.0)."""
    if isinstance(value, int) and abs(value) > 1_000_000:
        return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]
    return float(value)


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


def surface(points_xz, y: float, texture: str, width: int, height: int, model: str, role: str) -> Polygon:
    """A horizontal face over a ring of (x, z) points, front upward, one texel per LT (Beethoven's)."""
    ring = np.array([[x, y, z] for x, z in points_xz], float)
    polygon = Polygon(ring, [tuple(np.round(p, 1)) for p in ring], texture,
                      (np.zeros(3), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])), 0x1088, model, role)
    if polygon.normal[1] < 0:
        polygon = Polygon(ring[::-1], [tuple(np.round(p, 1)) for p in ring[::-1]], texture, polygon.mapping, 0x1088,
                          model, role)
    polygon.notes.update(width=width, height=height)
    return polygon


def lua_string(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def lua_list(values) -> str:
    return "{" + ", ".join(str(v) for v in values) + "}"



def kick_open_key() -> float:
    """The OpenDoor model key of YANMIR.abc's KickDoor (s): YanmirBase.scr opens the kicked door there."""
    from convert_abc_model import read_abc
    model = read_abc(ROOT / "mm9/extracted/MODELS/MODELS/YANMIR.abc")
    clip = next(a for a in model.animations if a.name.lower() == "kickdoor")
    return next(k.time_ms for k in clip.keyframes if "opendoor" in (k.event or "").lower()) / 1000.0

class YanmirsFort(dungeon.Hooks):
    generator = "mm9r_yanmirsfort"
    mover_events = {"Secretdoor": (EV_SECRET, "click"), "DPortal37": (EV_TELEPORT, "click"),
                    **{name: (EV_CAGE + k, "click") for k, name in enumerate(CAGES)}}

    def destructible_events(self, build) -> dict:
        """The six supports (`motion: break`: scene destructibles, HitPoints 1): support k's death runs EV_SUPPORT + k
        (YanmirTrap.scr's SupportBroken count; the map Lua turns its hint off)."""
        return {name: (EV_SUPPORT + k, 0) for k, name in enumerate(SUPPORTS)}

    # --- geometry -----------------------------------------------------------------------------------------------
    def edit_polygons(self, build, polygons: list) -> list:
        """BlueWater0 (the pool in the west ice cave; ShowSurface, Water115.spr, SurfaceAlpha 0.7): its top as
        non-solid translucent faces cut to the cave on a 64 LT grid (Dook's Castle's lake), so the party wades to the
        bed under it (at most 62 LT deep) and sees it through the surface."""
        source = build.source
        points = np.array(source.models[POOL_MODEL].points, float)
        (x0, z0), (x1, z1) = points[:, [0, 2]].min(0), points[:, [0, 2]].max(0)
        alias = source.aliases[POOL_TEXTURE]
        self.pool_y = y = float(points[:, 1].max())
        for polygon in polygons:
            polygon.bounds = (polygon.points.min(0), polygon.points.max(0))
        out, self.pool_faces = list(polygons), 0
        for row in np.arange(z0, z1, POOL_TILE):
            run = None
            for column in np.arange(x0, x1 + POOL_TILE, POOL_TILE):
                wet = column < x1 and any(in_air(polygons, column + u * POOL_TILE, y + 1, row + v * POOL_TILE)
                                          for u in (0.02, 0.5, 0.98) for v in (0.02, 0.5, 0.98))
                if wet and run is None:
                    run = column
                elif not wet and run is not None:
                    top = min(row + POOL_TILE, z1)
                    out.append(surface([(run, row), (run, top), (column, top), (column, row)], y, POOL_TEXTURE,
                                       alias["width"], alias["height"], POOL_MODEL, "nonsolid"))
                    self.pool_faces += 1
                    run = None
        return out

    # --- population ---------------------------------------------------------------------------------------------
    def populate(self, build) -> None:
        content, source = build.content, build.source
        # Yanmir's key is a world item (dungeon/pickups.py: item 570, key 7001 on pickup)
        self.placed = set()
        if PROPS.exists():
            self.placed = {entry["source_name"] for entry in json.loads(PROPS.read_text())}
            content.props(PROPS)
        else:
            print("note: props.json is missing; no decorations or chests placed")
        if PROPS.exists() and "Yanmir'sKey" not in self.placed:
            print("note: Yanmir'sKey has no placement")
        self.scale_lights(build)
        self.place_perception_hints(build)
        names = ["SquishTrigger0", "SquishTrigger1", "Trigger6", "Trigger7", "Trigger8", "Trigger9", "Trigger10"]
        self.boxes = {name: self.box(build, name) for name in names}
        self.boxes["TriggerYanmirTrap"] = self.box(build, "TriggerYanmirTrap", reach=0)
        self.boxes["EndOfWorld"] = self.lt_box(build, *FALL_BOX_LT)
        self.spawners = {}
        for o in source.objects:
            if o["class"] == "Spawner":
                spawn = str(o["properties"].get("DefaultSpawn", "")).split()[0]
                self.spawners[o["name"]] = (spawn, build.project.native(o["properties"]["Pos"]).round().astype(int))
        self.respawns = {o["name"]: build.project.native(o["properties"]["Pos"]).round().astype(int)
                         for o in source.objects if "bugspawn" in str(o["properties"].get("ScriptName", "")).lower()}
        content.report["omitted"] += [
            {"anchor": "PlayerRanAway/PlayerRanAway0", "class": "Trigger",
             "reason": "send Yanmir back along his YanmirPathA markers: native actors have no marker paths"},
            {"anchor": "Givekey", "class": "ScriptObject", "reason": "Yanmir.scr: its Use and Trigger do nothing "
                                                                     "(GiveEeps is not wired); YanmirBase.scr gives the key"},
            {"anchor": "YanmirDust/FrostDust*/CaveInDust*", "class": "Fire", "reason": "dust effects of the scripts"},
            {"anchor": "DoorQuake0-9", "class": "EarthQuake", "reason": "camera quakes of Yanmir's door kicks"},
        ]

    def scale_lights(self, build) -> None:
        """MM9 weights each Light by its BrightScale (the blue fills 0.3-1.0 over 300-1 536 LT): the BLV lights carry
        colour x BrightScale (the Ruined Temple's lesson); the profile's direct_scale makes up the level."""
        scale = {light["name"]: light["bright_scale"] for light in build.lights}
        for record in build.package.metadata["lights"]:
            record["color"] = [int(round(c * scale.get(record["id"], 1.0))) for c in record["color"]]

    def lt_box(self, build, low, high) -> list:
        a, b = build.project.native(np.array(low, float)), build.project.native(np.array(high, float))
        return [np.minimum(a, b).round().astype(int).tolist(), np.maximum(a, b).round().astype(int).tolist()]

    def box(self, build, name, reach=PARTY_REACH) -> list:
        """A Trigger's box in native units (Pos +- Dims), widened by the party's reach in x and y."""
        p = build.source.properties(name)
        pos, dims = np.array(p["Pos"], float), np.array(p["Dims"], float)
        low, high = self.lt_box(build, pos - dims, pos + dims)
        return [[low[0] - reach, low[1] - reach, low[2]], [high[0] + reach, high[1] + reach, high[2]]]

    def place_perception_hints(self, build) -> None:
        """MM9's PerceptionBrushes: the secret wall (0), the trap hall's floor (1), the six supports (2-7): their
        Perception polygons as untouchable translucent faces with a cog. 0 and 1 show to a party with Perception 10;
        2-7 carry no PerceptionValue (0: always shown) until their support breaks."""
        package, source = build.package, build.source
        self.hints, self.hint_faces, self.hint_value = {}, 0, {}
        for k, name in enumerate(HINTS):
            self.hint_value[name] = int(round(as_float(source.properties(name).get("PerceptionValue", 0) or 0)))
            parts = [p for p in source.polygons(name) if "perception" in p.texture.lower()]
            for i, polygon in enumerate(parts):
                rooms = build.content.rooms
                room = room_id(_side_room(rooms, polygon, 1) or _side_room(rooms, polygon, -1)
                               or rooms.owner(polygon.points.mean(0)))
                node = f"TRIGGER_perception_{name}_{i}"
                package.add_polygon(node, polygon, build.stats)
                package.room_nodes[room].append(node)
                surface_record = {"id": node[8:], "source_node": node, "flags": ["untouchable"],
                                  "cog_number": COG_HINT + k}
                if name in HINT_EVENTS:     # a hint round a clickable thing takes its click
                    surface_record["trigger"] = {"event_id": HINT_EVENTS[name], "type": "click"}
                package.metadata["surfaces"].append(surface_record)
                self.hint_faces += 1
            self.hints[name] = COG_HINT + k
        self.perception_textures = sorted({p.texture.lower() for name in HINTS for p in source.polygons(name)
                                           if "perception" in p.texture.lower()})

    # --- actors -------------------------------------------------------------------------------------------------
    def actors(self, build, sector_of_room: dict) -> list[dict]:
        content, source = build.content, build.source
        bases = content.monster_bases()
        out, self.actor = [], {}
        self.trap_floor_y, self.moved, self.forced_floor = None, {}, {}
        self.monster_ids, self.children, self.giants = {}, [], []
        self.death_spawn, self.bug_respawn = {}, {}
        for o in source.objects:
            if o["class"] not in build.project.monster_classes:
                continue
            name, p, cls = o["name"], o["properties"], o["class"]
            scale = float(p.get("Scale", 1.0) or 1.0)
            child = cls.startswith("CommonerChild")
            if child:
                base = {"name": "Child", "attributes": 0, "hp": 6, "hostility_type": 0, "monster_info_id": CHILD_ROW,
                        "monster_id": CHILD_ROW, "radius": 0, "height": 0, "move_speed": 0}
                body = CHILD_EXTENTS
                content.report["omitted"] = [e for e in content.report["omitted"] if e["anchor"] != name]
            elif name in bases:
                base = bases[name]
                body = None
            else:
                continue
            changes = placed_body(base["monster_id"], p)        # MM9's body: the row's, or at the DAT's own Scale
            if body is not None:                                # a child (no MM9 row): its model's body x the DAT Scale
                changes = {"radius": int(round(body[0] * scale * SCALE)), "height": int(round(2 * body[1] * scale * SCALE))}
            script = str(p.get("ScriptName") or "").lower()
            group, hidden, friendly = 0, False, child
            if cls == "Yanmir":
                group = GROUP_YANMIR
            elif "yanmirhidden" in script:
                group, hidden = GROUP_GIANTS, True
            elif child:
                group = GROUP_CHILDREN
            o = self.on_floor(build, o)
            actor = content.actor(o, base, sector_of_room, group=group, hidden=hidden, friendly=friendly,
                                  floor_query_lt=o["properties"]["Pos"][1] + 24, **changes)
            if name in self.forced_floor:
                actor["position"]["z"] = int(round(self.forced_floor[name] * SCALE)) + 1
            if cls == "Yanmir":
                actor["dormant"] = True                   # YanmirBase.scr :Main DisableWandering until "Squish"
            if child:
                actor["immobile"] = True
                actor["mm9_rude_id"] = CHILD_RUDE
                actor["mm9_source_object_index"] = o["index"]
                self.children.append((name, o["index"], actor["actor_index"]))
            if hidden:
                self.giants.append(actor["actor_index"])
            target = str(p.get("DeathTriggerTarget") or "")
            if target.startswith("Spawner"):
                self.death_spawn[actor["actor_index"]] = target
            elif target.startswith("Respawn"):
                self.bug_respawn[actor["actor_index"]] = target
            if not child:
                self.monster_ids[cls] = base["monster_id"]
            self.actor[name] = actor["actor_index"]
            out.append(actor)
        self.placed_actors = len(out)
        return out

    def on_floor(self, build, o: dict) -> dict:
        """MM9 hangs some Ice Lobbercicles from the ceilings (MoveToFloor 0, Gravity 0); native actors stand on a
        floor: the floor under them, or the nearest one within 256 LT where none is under them (IceLobbercicle6/10
        over the east cave's broken floor). IceLobbercicle2 stands on the trap hall's floor, a mover the static floor
        query falls through: it is set on YanDstruct0's top."""
        content = build.content
        p = o["properties"]
        x, y, z = p["Pos"]
        if self.trap_floor_y is None:
            from dungeon.source import floor_below
            self.trap_polygons = [q for name in ("YanDstruct0", "FallingFloor0") for q in build.source.polygons(name)]
            self.trap_floor_y = floor_below(self.trap_polygons, (192, 50, -3200))
        floor = content.floor_at(x, z, y + 24)
        if floor is not None and floor < y - 400:
            from dungeon.source import floor_below
            trap = floor_below(self.trap_polygons, (x, y + 24, z))
            if trap is not None and trap > floor:
                self.moved[o["name"]] = f"on the trap hall's floor ({trap:.0f} LT), not the shaft's ({floor:.0f})"
                self.forced_floor[o["name"]] = trap
                return o
        if floor is not None:
            return o
        for radius in (32, 64, 96, 128, 192, 256):
            for angle in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                nx, nz = x + radius * np.cos(angle), z + radius * np.sin(angle)
                found = content.floor_at(nx, nz, y + 24)
                if found is not None and abs(found - y) < 600:
                    self.moved[o["name"]] = f"no floor under it; moved {radius} LT to the floor at {found:.0f}"
                    return dict(o, properties=dict(p, Pos=[nx, y, nz]))
        raise SystemExit(f"actor {o['name']}: no floor near it")

    # --- map script ---------------------------------------------------------------------------------------------
    def map_script(self, build) -> str:
        script = lua.Script(build, "Yanmir's Fort")
        self.support_ids = [build.source.by_name[name.lower()]["index"] for name in SUPPORTS]
        boxes = self.boxes
        yanmir = self.actor["Yanmir0"]
        bug = self.monster_ids["IceLobbercicle"]
        spawners = ", ".join(f"{name} = {{monster = {self.monster_ids[kind]}, p = {lua.point(pos)}}}"
                             for name, (kind, pos) in sorted(self.spawners.items()) if kind in self.monster_ids)
        respawns = ", ".join(f"{name} = {lua.point(pos)}" for name, pos in sorted(self.respawns.items()))
        death_spawn = ", ".join(f"[{i}] = \"{t}\"" for i, t in sorted(self.death_spawn.items()))
        bug_respawn = ", ".join(f"[{i}] = \"{t}\"" for i, t in sorted(self.bug_respawn.items()))
        shaft = build.project.native([192, -3500, -3200]).round().astype(int)
        hints = ", ".join(f"{name} = {cog}" for name, cog in self.hints.items())
        support_hint = ", ".join(f"\"{SUPPORT_HINT[name]}\"" for name in SUPPORTS)
        # YanmirBase.scr :BD_OnDoor / :KickDoor: Yanmir kicks any shut door in his way open (the doorway pairs).
        kick = []
        for group in sorted({m["group"] for m in build.movers if m["group"].startswith(("DPortal", "Portal"))}):
            if group == "DPortal37":
                continue                       # the teleporter doors: Locked
            models = [name for name, rule in build.plan["movers"].items() if rule.get("group") == group]
            pts = np.concatenate([p.points for name in models for p in build.source.polygons(name)])
            # the doorway's middle at its foot: Yanmir's feet stand level with it (the middle of his 1200-high doors
            # stood 609 over his floor, out of the 600 reach in height, so he never kicked them)
            low, high = pts.min(0), pts.max(0)
            c = build.project.native([(low[0] + high[0]) / 2, low[1], (low[2] + high[2]) / 2]).round().astype(int)
            kick.append(f"{{\"{group}\", {c[0]}, {c[1]}, {c[2]}}}")
        script.lines += [
            "local GROUPS = {" + ", ".join(f"[\"{g}\"] = {{{', '.join(map(str, ids))}}}"
                                           for g, ids in sorted(script.groups.items())) + "}",
            "local function openGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Open) end end",
            "local function closeGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Close) end end",
            "local function toggleGroup(name) for _, id in ipairs(GROUPS[name]) do evt.SetDoorState(id, DoorAction.Trigger) end end",
            "local function inBox(b, x, y, z) return x >= b[1][1] and x <= b[2][1] and y >= b[1][2] and y <= b[2][2] "
            "and z + 170 >= b[1][3] and z <= b[2][3] end",
            f"local BOX = {{{', '.join(f'{k} = {{{lua.point(v[0])}, {lua.point(v[1])}}}' for k, v in sorted(boxes.items()))}}}",
            f"local YANMIR = {yanmir}",
            f"local GIANTS = {lua_list(self.giants)}",
            f"local SUPPORT_HINT = {{{support_hint}}}",
            f"local HINTS = {{{hints}}}",
            f"local KICK_DOORS = {{{', '.join(kick)}}}",
            "",
        ]
        script.doors()
        script.chests()
        lines = [
            "",
            "-- PerceptionBrushes: the secret wall (0) and the trap hall's floor (1) show to a party with Perception "
            f"{self.hint_value['PerceptionBrush0']}; the six",
            "-- supports' (2-7) have no PerceptionValue and show until their support breaks (YanmirTrap.scr :Init).",
            f"local function perceptive() return evt.CheckSkill({PERCEPTION_SKILL}, 0, {self.hint_value['PerceptionBrush0']}) end",
            "local function hintGone(name)",
            "    if name == \"PerceptionBrush0\" then return var(\"SecretOpen\") == 1 end",
            "    if name == \"PerceptionBrush1\" then return var(\"TrapFired\") == 1 end",
            "    for k, hint in ipairs(SUPPORT_HINT) do",
            "        if hint == name then return var(\"Support\" .. (k - 1)) == 1 end",
            "    end",
            "    return false",
            "end",
            "function updateHints()",
            "    local sees = perceptive()",
            "    set(\"PerceptiveParty\", sees and 1 or 0)",
            "    for name, cog in pairs(HINTS) do",
            "        local needs = name == \"PerceptionBrush0\" or name == \"PerceptionBrush1\"",
            "        evt.SetFacetBit(cog, FacetBits.Invisible, (needs and not sees) or hintGone(name))",
            "    end",
            "end",
            "",
            "-- YanmirTrap.scr: each broken support (DestructableBrush0-5, HitPoints 1; DeathTrigger Trigger0-5: its",
            "-- PerceptionBrush off, \"SupportBroken\" to YanmirTrap) counts; at six TriggerYanmirTrap turns on. The supports",
            "-- are scene destructibles: a weapon hit (or a click: the shared killing blow) breaks one and runs its event;",
            "-- the event run any other way breaks it too.",
            f"local SUPPORT_ID = {lua_list(self.support_ids)}",
            "local function breakSupport(k)",
            "    if var(\"Support\" .. k) == 1 then return end",
            "    set(\"Support\" .. k, 1)",
            "    evt.DestroyDestructible(SUPPORT_ID[k + 1])",
            "    local broken = 0",
            "    for j = 0, 5 do broken = broken + var(\"Support\" .. j) end",
            "    if broken >= 6 then set(\"TrapArmed\", 1) end",
            "    updateHints()",
            "end",
        ]
        registrations = []
        for k in range(6):
            lines.append(f"handlers[{EV_SUPPORT + k}] = function() breakSupport({k}) end   -- {SUPPORTS[k]}")
            registrations.append((EV_SUPPORT + k, "Wooden support", None))
        lines += [
            "",
            "-- Yanmir (YanmirBase.scr). :Reset CanDamage FALSE: nothing hurts him (TELP 1.3). :GiveEeps: key 69 and the",
            f"-- experience on the quest (key {KEY_QUEST}), else key {KEY_FREE}; {EXP_TRAP} by the trap (:OnTimeToDie), "
            f"{EXP_DEATH} on any other death (:OnDeath).",
            "local function giveEeps(amount)",
            f"    if MM9.hasKey({KEY_QUEST_DONE}) == 0 and MM9.hasKey({KEY_QUEST}) == 1 then",
            f"        MM9.giveKey({KEY_QUEST_DONE}); MM9.giveExperience(amount); MM9.playSound(\"sounds/events/quest.wav\")",
            "        return",
            "    end",
            f"    if MM9.hasKey({KEY_FREE}) == 0 then",
            f"        MM9.giveKey({KEY_FREE}); MM9.giveExperience(amount); MM9.playSound(\"sounds/events/quest.wav\")",
            "    end",
            "end",
            "local function wakeYanmir()      -- SquishTrigger0/1: \"Squish\" -> :Begin (wandering, hunting bugs)",
            "    if var(\"YanmirAwake\") == 1 then return end",
            "    if not MM9.receives(\"yanmirsfort\", \"Yanmir0\", \"Squish\", YANMIR) then return end   -- dead: none",
            "    set(\"YanmirAwake\", 1)",
            "    evt.WakeActor(YANMIR)",
            "end",
        ]
        # TriggerYanmirTrap -> :OnTimeToDie: the cinematic yanmir_death (cutscene.py), its steps on a timer for a party
        # that watches from the hall
        lines += cutscene.trap_lua(cutscene.watch_boxes(build.project, build.source), shaft, T_FALL,
                                   balanced_experience(EXP_TRAP, KEY_QUEST_DONE))
        lines += [
            f"handlers[{EV_DAMAGED}] = function(context)",
            "    if context.actorIndex == YANMIR then evt.SetHookDamage(0) end",
            "end",
        ]
        registrations.append((T_FALL, "Yanmir falls", None, "timer"))
        lines += [
            "",
            "-- Monsters killed. YanmirBase.scr :OnDeath (any death but the trap): the key and 5 000. The Spawners (Spawner0-5",
            "-- DefaultSpawn \"Yeti ...\", Spawner6 \"Thrall ...\"): each Yeti with a DeathTriggerTarget sends one more from its",
            "-- spawner. YanmirFort_BugSpawn.scr: an Ice Lobbercicle of Respawn0-3 (and every one they send) comes back at",
            f"-- its Respawn point {BUG_RESPAWN_MIN}-{BUG_RESPAWN_MAX} s later (:OnRespawnMe), when the party is not near (:DoSpawn).",
            f"local SPAWNERS = {{{spawners}}}",
            f"local RESPAWNS = {{{respawns}}}",
            f"local DEATH_SPAWN = {{{death_spawn}}}",
            f"local BUG_RESPAWN = {{{bug_respawn}}}",
            f"local PLACED = {self.placed_actors}",
            "local function spawnFrom(name)",
            "    local s = SPAWNERS[name]",
            "    if s == nil then return end",
            f"    evt.SummonMonstersById({{monster = s.monster, x = s.p[1], y = s.p[2], z = s.p[3], radius = 32, "
            f"group = {GROUP_SPAWNED}, count = 1}})",
            "    set(\"Spawned\" .. name, var(\"Spawned\" .. name) + 1)",
            "end",
            "local function nearestRespawn(x, y)",
            "    local best, bestName = nil, nil",
            "    for name, p in pairs(RESPAWNS) do",
            "        local d = (p[1] - x) ^ 2 + (p[2] - y) ^ 2",
            "        if best == nil or d < best then best, bestName = d, name end",
            "    end",
            "    return bestName",
            "end",
            f"handlers[{EV_KILLED}] = function(context)",
            "    local index = context.actorIndex",
            "    if index == YANMIR then",
            "        set(\"YanmirGone\", 1)",
            f"        if var(\"TrapFired\") == 0 then giveEeps({balanced_experience(EXP_DEATH, KEY_QUEST_DONE)}) end",
            "        return",
            "    end",
            "    if DEATH_SPAWN[index] ~= nil then spawnFrom(DEATH_SPAWN[index]) end",
            "    local respawn = BUG_RESPAWN[index]",
            f"    if respawn == nil and index >= PLACED and context.monsterId == {bug} then",
            "        local x, y = evt.GetMapActorPosition(index)",
            "        if x ~= nil then respawn = nearestRespawn(x, y) end",
            "    end",
            "    if respawn ~= nil then",
            f"        set(\"BugDue\" .. respawn, MM9.random({BUG_RESPAWN_MIN}, {BUG_RESPAWN_MAX}))",
            "        set(\"BugsQueued\", var(\"BugsQueued\") + 1)",
            "    end",
            "end",
            "local function tickRespawns()       -- once a second",
            "    local x, y = evt.GetPartyPosition()",
            "    for name, p in pairs(RESPAWNS) do",
            "        local due = var(\"BugDue\" .. name)",
            "        if due > 1 then set(\"BugDue\" .. name, due - 1)",
            "        elseif due == 1 then",
            f"            if (p[1] - x) ^ 2 + (p[2] - y) ^ 2 > {BUG_SIGHT} ^ 2 then",
            "                set(\"BugDue\" .. name, 0)",
            f"                evt.SummonMonstersById({{monster = {bug}, x = p[1], y = p[2], z = p[3], radius = 16, "
            f"group = {GROUP_BUGS}, count = 1}})",
            "                set(\"BugsRespawned\", var(\"BugsRespawned\") + 1)",
            "            else",
            "                set(\"BugDue\" .. name, 5)     -- :DoSpawn waits while the player can see it",
            "            end",
            "        end",
            "    end",
            "end",
        ]
        registrations += [(EV_KILLED, "Monster killed", None, "hook_killed"), (EV_DAMAGED, "Yanmir", None, "hook_damage")]
        lines += self.script_objects()
        registrations += [(EV_SECRET, "Wall", "Wall"), (EV_TELEPORT, "Door", "Door")]
        registrations += [(EV_CAGE + k, "Cage", "Cage") for k in range(len(CAGES))]
        child_lines, child_registrations = self.script_children()
        lines += child_lines
        registrations += child_registrations
        lines += self.script_volumes()
        registrations.append((T_POLL, "Trigger volumes", None, "timer"))
        lines += [
            "",
            "handlers[1] = function()   -- map load: the scripts' OnPostStartWorld / OnPostMiniSaveLoad",
            "    if var(\"TrapFired\") == 1 then openGroup(\"TrapFloor\"); openGroup(\"TrapPlanks\") end",
            cutscene.load_lua(),
            "    if var(\"SecretOpen\") == 1 then openGroup(\"Secretdoor\") end",
            "    -- YanmirHidden.scr :InitYanmirHidden: Yanmir gone, the Forest Giants are there (visible, solid, titan.scr)",
            "    if var(\"YanmirGone\") == 1 then",
            "        MM9.removeActor(YANMIR)",
            "        if var(\"GiantsOut\") == 0 then",
            "            set(\"GiantsOut\", 1)",
            f"            evt.SetMonGroupBit({GROUP_GIANTS}, MonsterBits.Invisible, false)",
            "        end",
            "    end",
            "    if var(\"YanmirAwake\") == 1 and var(\"YanmirGone\") == 0 then",
            "        evt.SetActorImmobile(YANMIR, false)   -- a kick saved half way (kickDoors' hold is runtime only)",
            "        evt.WakeActor(YANMIR)",
            "    end",
            "    for name, _ in pairs(CHILD) do",
            "        if var(\"Escaped\" .. name) == 1 then MM9.removeActor(CHILD[name]) end",
            "    end",
            "    updateHints()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "end",
        ]
        script.add(lines, *registrations, (1, "Map load", None))
        script.hooks += [f"RegisterMonsterKilledHook({EV_KILLED}, \"Monster killed\", handlers[{EV_KILLED}])",
                         f"RegisterMonsterDamageHook({EV_DAMAGED}, \"Yanmir cannot be hurt\", handlers[{EV_DAMAGED}])"]
        script.registrations = [r for r in script.registrations if r[3] not in ("hook_killed", "hook_damage")]
        self.scenes = cutscene.scenes(yanmir)
        return script.finish(on_load=[1]) + cutscenes.lua_block(self.scenes)

    def script_objects(self) -> list[str]:
        cages = " ".join(f"evt.SetDoorState(DOORS.{name}, DoorAction.Open)" for name in CAGES)
        lines = [
            "",
            "-- The secret wall (Secretdoor: PushOpen, OpenTrigger \"lock\": it opens once and stays open).",
            f"handlers[{EV_SECRET}] = function()",
            "    if var(\"SecretOpen\") == 1 then return end",
            "    set(\"SecretOpen\", 1)",
            "    openGroup(\"Secretdoor\")",
            "    updateHints()",
            "end",
            "",
            f"-- Yanmir's key (YanmirKey.scr :GiveKeyToPlayer) is a world item ({ITEM_KEY}, dungeon/pickups.py) that gives key "
            f"{KEY_CAGES};",
            "-- :UnlockCages: with it the teleporter doors (DoorTeleportRight/Left) and the cages (RotatingDoor61-67) open.",
            "-- The teleporter doors and the cages are Locked until the key; then they open on a click.",
            f"handlers[{EV_TELEPORT}] = function()",
            f"    if MM9.hasKey({KEY_CAGES}) == 0 then evt.StatusText(\"The door is locked.\") return end",
            "    toggleGroup(\"DPortal37\")",
            "end",
        ]
        for k, name in enumerate(CAGES):
            lines += [f"handlers[{EV_CAGE + k}] = function()   -- {name}",
                      f"    if MM9.hasKey({KEY_CAGES}) == 0 then evt.StatusText(\"The cage is locked.\") return end",
                      f"    toggleGroup(\"{name}\")",
                      "end"]
        return lines

    def script_children(self) -> tuple[list[str], list]:
        child = ", ".join(f"{name} = {index}" for name, _, index in self.children)
        lines = [
            "",
            "-- The children (YanmirChild.scr, ScriptParams TPS2). :ShoutForHelp: the first child to see the party calls for",
            f"-- help once per visit (RolloverText 200, or 201 with key {KEY_CAGES}). :OnUse: with key {KEY_CAGES} the child",
            "-- follows the party to the teleporter and escapes through it (:EscapeLevel, RemoveObject); here a click with the",
            "-- key sends it to the teleporter at once (no followers: README).",
            f"local CHILD = {{{child}}}",
            "local shouted = false",
            "local function shoutForHelp()",
            "    if shouted then return end",
            "    for name, index in pairs(CHILD) do",
            "        -- OnFoundPlayer: a dead child's callbacks do not fire (MM9.actorAlive)",
            f"        if var(\"Escaped\" .. name) == 0 and MM9.actorAlive(index)",
            f"                and evt.IsMapActorWithinPartyDistance(index, {int(CHILD_SIGHT * SCALE)}) then",
            "            shouted = true",
            f"            if MM9.hasKey({KEY_CAGES}) == 1 then",
            f"                evt.StatusText({lua_string(rollover_text(201))})",
            "            else",
            f"                evt.StatusText({lua_string(rollover_text(200))})",
            "            end",
            "            set(\"ChildShouted\", 1)",
            "            return",
            "        end",
            "    end",
            "end",
            "local function rescue(name)",
            "    if not MM9.receives(\"yanmirsfort\", name, \"use\", CHILD[name]) then return end   -- a dead child: none",
            f"    if MM9.hasKey({KEY_CAGES}) == 0 then MM9.openRude({CHILD_RUDE}) return end   -- :OnUse Exit FALSE: DoRude",
            "    if var(\"Escaped\" .. name) == 1 then return end",
            "    set(\"Escaped\" .. name, 1)",
            "    set(\"Rescued\", var(\"Rescued\") + 1)",
            "    MM9.removeActor(CHILD[name])",
            "    evt.StatusText(\"Thank you! The child runs for the teleporter.\")",
            "end",
        ]
        registrations = []
        for name, index, _ in self.children:
            event = 53000 + index
            lines.append(f"handlers[{event}] = function() rescue(\"{name}\") end   -- {name}, YanmirChild.scr :OnUse")
            registrations.append((event, name, None))
        return lines, registrations

    def script_volumes(self) -> list[str]:
        city = self.city_arrival
        key = kick_open_key()
        if abs(key - KICK_CHECK) > 0.05:
            raise SystemExit(f"YANMIR.abc KickDoor's OpenDoor key at {key} s: the door kicks' check ({KICK_CHECK} s) "
                             "no longer meets it")
        return [
            "",
            "-- YanmirBase.scr :BD_OnDoor -> :KickDoor (PlayAnim KickDoor) -> its OpenDoor model key -> :OpenDoor",
            f"-- (stonedoorslam.wav, \"Use\" on the door): a shut door within {KICK_REACH} of Yanmir is kicked open "
            "(native monsters do",
            f"-- not open doors). He plays kick_door, and the next check, {KICK_CHECK:g} s later (the key is at "
            f"{key:.3f} s), opens the door",
            "-- (Kicked 1: kicked, 2: open). No door state reaches the Lua, so only a door's first kick plays the clip:",
            "-- one the party shut again opens as he passes. As MM9's KickDoor holds his path (SavePath), he stands",
            "-- facing the door through the clip and walks on at the check after the opening (the clip's end).",
            "local kickHold = 0",
            "local function kickDoors()",
            "    if kickHold > 0 then",
            "        kickHold = kickHold - 1",
            "        if kickHold == 0 then",
            "            evt.SetActorImmobile(YANMIR, false)",
            "            if var(\"TrapFired\") == 0 then evt.ClearActorPresentation(YANMIR) end",
            "        end",
            "    end",
            "    for _, d in ipairs(KICK_DOORS) do",
            "        if var(\"Kicked\" .. d[1]) == 1 then   -- kicked at the last check: the clip's OpenDoor key",
            "            set(\"Kicked\" .. d[1], 2)",
            "            evt.PlaySoundName(\"door/stonedoorslam.wav\", d[2], d[3], d[4])",
            "            openGroup(d[1])",
            "        end",
            "    end",
            "    if var(\"YanmirAwake\") == 0 or var(\"YanmirGone\") == 1 or not MM9.actorAlive(YANMIR) then return end",
            "    local yx, yy, yz = evt.GetMapActorPosition(YANMIR)",
            "    if yx == nil then return end",
            "    for _, d in ipairs(KICK_DOORS) do",
            f"        if (d[2] - yx) ^ 2 + (d[3] - yy) ^ 2 < {KICK_REACH} ^ 2 and math.abs(d[4] - yz) < 600 then",
            "            if var(\"Kicked\" .. d[1]) == 0 then",
            "                set(\"Kicks\", var(\"Kicks\") + 1)",
            "                set(\"Kicked\" .. d[1], 1)",
            "                evt.PlayActorClip(YANMIR, \"kick_door\")",
            "                evt.FaceActorTo(YANMIR, d[2], d[3], 0.15)",
            "                evt.SetActorImmobile(YANMIR, true)",
            "                kickHold = 2",
            "            else",
            "                openGroup(d[1])",
            "            end",
            "        end",
            "    end",
            "end",
            "",
            "-- MM9's Trigger volumes, polled four times a second: SquishTrigger0/1 wake Yanmir; Trigger6-10 send their",
            "-- spawner's monster once (MessageName1 \"off\"); TriggerYanmirTrap (AIOnly) fires on Yanmir once armed;",
            "-- EndOfWorldTrigger: a party that falls through the trap hall's floor goes to Frosgard City (PlayerExit,",
            "-- \"FallingStart\"); the fallen floor stops 399 LT down (README), MM9's shaft goes on to -3520.",
            "local VOLUMES = {",
            "    {name = \"SquishTrigger0\", run = wakeYanmir}, {name = \"SquishTrigger1\", run = wakeYanmir},",
            "    {name = \"Trigger6\", run = function() spawnFrom(\"Spawner0\") end},",
            "    {name = \"Trigger7\", run = function() spawnFrom(\"Spawner1\") end},",
            "    {name = \"Trigger8\", run = function() spawnFrom(\"Spawner2\") end},",
            "    {name = \"Trigger9\", run = function() spawnFrom(\"Spawner4\") end},",
            "    {name = \"Trigger10\", run = function() spawnFrom(\"Spawner6\") end},",
            "}",
            "local inside, polls = {}, 0",
            f"handlers[{T_POLL}] = function()",
            f"    evt.StartTimer({T_POLL}, seconds(0.25))",
            "    local x, y, z = evt.GetPartyPosition()",
            "    polls = polls + 1",
            "    for _, v in ipairs(VOLUMES) do",
            "        local now = inBox(BOX[v.name], x, y, z)",
            "        if now and not inside[v.name] and var(\"Done\" .. v.name) == 0 then",
            "            set(\"Done\" .. v.name, 1)",
            "            v.run()",
            "        end",
            "        inside[v.name] = now",
            "    end",
            "    -- \"TimeToDie\" from Yanmir's own touch: a dead or removed Yanmir takes none (MM9.actorAlive)",
            "    if var(\"TrapArmed\") == 1 and var(\"TrapFired\") == 0 and MM9.actorAlive(YANMIR) then",
            "        local yx, yy, yz = evt.GetMapActorPosition(YANMIR)",
            "        local b = BOX.TriggerYanmirTrap",
            "        if yx ~= nil and yx >= b[1][1] and yx <= b[2][1] and yy >= b[1][2] and yy <= b[2][2] then trapFires() end",
            "    end",
            "    if polls % 2 == 0 then kickDoors() end",
            "    if var(\"TrapFired\") == 1 and inBox(BOX.EndOfWorld, x, y, z) and var(\"FellToCity\") == 0 then",
            "        set(\"FellToCity\", 1)",
            f"        evt.MoveToMap({city[0]}, {city[1]}, {city[2]}, {city[3]}, 0, 0, 0, 0, \"frosgardcity.blv\")",
            "    end",
            "    shoutForHelp()",
            "    if polls % 4 == 0 then tickRespawns() end",
            "    if polls % 12 == 0 then updateHints() end",
            "end",
        ]

    @property
    def city_arrival(self):
        """map_transitions.txt row mm9:transition/yanmirsfort/612 (PlayerExit -> frosgardcity FallingStart). Frosgard
        City is a BLV since 2026-10-31 (level_generation/projects/mm9r_frosgardcity): FallingStart as built, on the
        harbour's ice under MM9's drop point (MM9 drops the party from 6 554 native; over the BLV's air that is
        outside every sector), facing 37 degrees (90 - ry) = 210 yaw units."""
        return (-11633, -9830, -327, 210)

    def scene(self, build, scene: dict) -> None:
        """The perception hints (translucent, two-sided), the pool's surface and the exit gates' sheets."""
        sys.path.insert(0, str(ROOT))
        from util.map_export import parse_blv_file
        blv = parse_blv_file(build.runtime / build.project.map)["payload"]
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in blv["vertices"]], float)

        def faces_of(alias: str) -> list[dict]:
            return [f for f in blv["faces"] if str(f.get("texture_name", "")).lower() == alias.lower()]

        hints = sorted({f["index"] for t in self.perception_textures
                        for f in faces_of(build.source.aliases[t]["alias"])})
        if len(hints) != self.hint_faces:
            raise SystemExit(f"{len(hints)} perception faces in the BLV, {self.hint_faces} polygons")
        scene.setdefault("translucent_faces", []).append(
            {"faces": hints, "opacity": PERCEPTION_OPACITY, "tint": [1.0, 1.0, 1.0], "two_sided": True})
        water = faces_of(build.source.aliases[POOL_TEXTURE]["alias"])
        pool, gates = [], []
        for f in water:
            points = vertices[f["vertex_indices"]]
            (pool if np.ptp(points[:, 2]) < 1 else gates).append(f["index"])
        if len(pool) < self.pool_faces:
            raise SystemExit(f"{len(pool)} pool faces in the BLV, {self.pool_faces} built")
        scene["translucent_faces"].append({"faces": sorted(pool), "opacity": POOL_OPACITY, "tint": [1.0, 1.0, 1.0],
                                           "two_sided": True})
        if gates:
            scene["translucent_faces"].append({"faces": sorted(gates), "opacity": PORTAL_OPACITY,
                                               "tint": [1.0, 1.0, 1.0], "two_sided": True})
        self.water_faces = {"pool": len(pool), "gates": len(gates)}
        liquids.apply(build, scene)     # MM9's water to the liquid shader (../mm9r_common/liquids.py)

    def grown(self, build, scene: dict, script: str, copies: list) -> str:
        """Pack growth's copies (dungeon/density.py) follow the placed actors: PLACED, the first index of an actor
        the map summons (a killed summoned Ice Lobbercicle comes back), moves past them."""
        old = f"local PLACED = {self.placed_actors}\n"
        if script.count(old) != 1:
            raise SystemExit("yanmirsfort: no PLACED line in the map Lua")
        return script.replace(old, f"local PLACED = {len(scene['initial_state']['actors'])}\n")

    def report(self, build) -> dict:
        return {"scripted": {"actors": self.actor, "boxes": self.boxes, "hints": self.hints,
                             "children": self.children, "giants": self.giants, "death_spawn": self.death_spawn,
                             "bug_respawn": self.bug_respawn, "moved_actors": self.moved, "pool_faces": self.pool_faces,
                             "water_faces": getattr(self, "water_faces", {})}}


if __name__ == "__main__":
    hooks = YanmirsFort()
    code = dungeon.main(PROJECT, hooks)
    if code == 0 and not {"--plan", "--scratch"} & set(sys.argv):
        # Yanmir's fall (cutscene.py): the engine loads it beside the map
        print(f"cinematics installed: {cutscenes.install(cutscene.STEM, hooks.scenes)} (yanmir_death)")
    sys.exit(code)
