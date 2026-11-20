"""
Pack growth (devdocs/mm9_rework/BALANCE_PLAN.md 3.6): the balance session's density targets
(tools/mm9_import_discovery/mm9_density_targets.yml, frozen with the members as DAT object names in
../density_anchors.json) as copies of each pack's own monsters next to them. Every converted map runs it after its
actors, scene hook and Lua (build.py), on the compiled BLV:

- A pack with `add` > 0 gets `add` copies of its ordinary members in the pack's own mix: each copy is of the monster
  row furthest below its share of the pack (largest remainder over all members, scripted ones included), its least
  copied member first, so a pack of one Bone Thrasher and three Skeletons adds Skeletons, not the first member listed
  (the first version cycled members in order and grew chapter 1 toward its weakest monsters). A copy is the member's whole scene
  record (row, hp, attributes, hostility, group, dormant, mm9_ai with its path stops, civilian/guard flags, draw scale,
  body) without its name-bound identity (npc_id, mm9_rude_id, mm9_source_object_index, unique_name_index).
- Not copied (scripted_reason): members with an identity (npc id, RUDE id, unique name index), hidden at the start
  (a script shows them), `mm9_can_receive_damage: false` (a scripted invulnerable), passive scripted actors, bosses
  (mm9_ai `boss`, the unique boss rows), and, from the DAT placement (References): a ScriptName (MM9 runs a
  script on it: KingKong breakers, summoners, set-piece actors), ShouldRepopulate 0 (quest actors) and a unique
  name (no instance number, not its class, used once in the DAT: JK, IckyRecon, LichSummoner); members whose actor
  index the map's Lua names (lua_actor_indices: handlers, show, remove, wake, move, clip, position, MM9.receives,
  kill hooks' tables) or whose DAT name it quotes (a message target), whose group it addresses (lua_group_numbers:
  group bits, group kill checks, wakes), and whose index the map's cinematics name (actor, look_at_actor). A pack of
  only those places nothing and says so. A map's actor directory tables (Hooks.density_lua_directories: every monster by
  DAT name, 1000 Terrors' ACTOR) are not read as scripting and take the copies, nor are tables that only name every
  actor (Hooks.density_lua_name_tables, 1000 Terrors' KIND); Hooks.grown lets a map Lua that
  counts its placed actors follow them (Yanmir's Fort's PLACED).
- A copy stands 120-600 units from the member it copies, on the same floor (within FLOOR_STEP), in the member's
  sector, on a floor no steeper than the engine walks (WALKABLE_NORMAL_Z, under its whole footprint) with no floor's
  top over it (the first face over its feet faces down: not under the ground or in a solid; a member that is gets
  no copies) and, for a flyer keeping its member's height, that face over half its body (not in a ceiling),
  reached from it without crossing a wall or a pit, clear of walls, other actors, doors and movers (swept along
  their travel), ladders, event faces (pads, exits, traps) and water (liquid textures, fluid faces, the
  scene's water volumes). Candidates are tried nearest first at angles seeded by map stem, anchor and copy number,
  so a reconversion places them the same. Where the member has no room the pack's other members are tried; a copy
  that fits nowhere is a shortfall, never forced. A pack's shortfall (and the copies of a pack with only scripted
  members) then moves to the map's other growable packs, never past a pack's `capacity`: each moved copy keeps the
  monster row it stood for and goes to the roomiest pack with an ordinary member of that row, else the roomiest; what
  finds no room stays unplaced, with its reason (work/density.json: target_total, placed_total, wanted/placed/moved/
  unplaced adds).
- Copies go after every existing actor (Lua refers to actors by index); their anchors are `<member>_grow<k>`.
  The packs' room check (a third of the free space where the pack stands) is the targets' `capacity`, which caps
  `add` already.

- Forced arrivals (overrides.yml `map: {density_arrivals: [{name, at: [x, y, z], radius, copies}]}`): where a
  teleporter or trap puts the party (Dark Passageway's one-way teleporters, Wizard's Lab's stations) at most `copies`
  copies stand within `radius` (height counted double, as the packs' link), so a weak party is not dropped into a
  grown pack with no way back (user, 2026-11-09). A spot past an arrival's quota is refused like any other, and the
  pack's remaining copies move to the map's other packs.

- Pod launchers (Lobbers and Ice Lobbers, modifiers.yml `pod_launch`): a copy of one is refused where
  LAUNCHERS_PER_SPOT launchers, placed or copied, already stand within LAUNCHER_RADIUS (height counted double), since
  each throws a pod every 5-10 s. Beethoven's Lua-named Lobbers had moved eight copies onto three Lobbers, two of them
  in one room: nine launchers sent a swarm of pods at every visit (user, 2026-11-09). A refused launcher copy moves on
  like any other and, once every launcher pack is at its quota, becomes a copy of the receiving pack's own mix.

- A map's scale (overrides.yml `map: {density_scale: 0.8}`) shrinks every pack's `add` by that factor, the total
  rounded and handed out by largest remainder in pack order (scale_adds: at 0.8 a 3 becomes 2, part of the 2s become
  1 and the 1s stay), where a map's grown packs are too many to progress (Isle of Ashes, user 2026-11-09).

overrides.yml `map: {density: false}` turns growth off for a map; `convert.py --no-density` for one run.
"""

from __future__ import annotations

import copy as copying
import hashlib
import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from mm9_density_targets import wall_segments

ANCHORS = Path(__file__).resolve().parents[1] / "density_anchors.json"
MIN_DISTANCE, MAX_DISTANCE = 120.0, 600.0
MARGIN = 32.0              # clearance beyond the bodies: to walls, actors, doors, ladders, pads
FLOOR_STEP = 24.0          # the copy's floor within this of the member's; and along the way between them
PATH_STEP = 32.0
RINGS, ANGLES = 7, 12      # candidate distances (nearest first) and angles per distance
INVISIBLE_BIT = 0x00010000
FLUID, LAVA, UNTOUCHABLE = 0x10, 0x40000000, 0x20000000
TRIGGER_ATTRIBUTES = 0x04000000 | 0x00080000 | 0x08000000    # pressure plate, touch, monster trigger
FLOOR_TYPES = {3, 4}
WALKABLE_NORMAL_Z = 0.68664550781     # game/indoor/IndoorGeometryUtils.cpp WalkableSlopeNormalZ
GRID = 512.0
POD_LAUNCHERS = frozenset({9086, 9106})     # Lobber, Ice Lobber (modifiers.yml mm9_ai pod_launch)
LAUNCHERS_PER_SPOT = 3
LAUNCHER_RADIUS = 3072.0                    # the Lobbers' alert radius


# --- The map's Lua: which actor indices it names -------------------------------------------------------------------
ACTOR_CALL = re.compile(r"\b(removeActor|showActor|hideActor|WakeActor|SetMonsterBit|SetMapActorPosition|"
                        r"GetMapActorPosition|setActorPosition|IsMapActorWithinPartyDistance|IsMapActorHostile|"
                        r"KillMapActor|TriggerActor|TurnActor|ActorSeesParty|SetActorBehavior|MoveActorTo|"
                        r"StopActorMove|IsActorMoving|PlayActorClip|ClearActorPresentation|SetActorTarget|FaceActorTo|"
                        r"actorAlive|setCanDamage)\s*\(")
RECEIVES_CALL = re.compile(r"\bMM9\.receives\s*\(")     # MM9.receives(map, target, message, actorIndex)
GROUP_CALL = re.compile(r"\b(SetMonGroupBit|WakeGroup|ChangeGroupAlly)\s*\(")
STRING = re.compile(r"\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'")
KILL_CHECK = re.compile(r"\bCheckMonstersKilled\s*\(\s*ActorKillCheck\.(\w+)\s*,")
LOOP = re.compile(r"\bfor\s+([\w\s,]+?)\s+in\s+(?:i?pairs)\s*\(")
DEFINITION = re.compile(r"(?:^|[;\s])(?:local\s+)?([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*=(?!=)\s*", re.MULTILINE)
INDEX_VARIABLE = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*[A-Za-z_]\w*\.actorIndex\b")
IDENTIFIER = re.compile(r"(?<![\w.:])([A-Za-z_]\w*)")
INTEGER = re.compile(r"(?<![\w.])(\d+)(?![\w.])")
KEYWORDS = {"and", "break", "do", "else", "elseif", "end", "false", "for", "function", "goto", "if", "in", "local",
            "nil", "not", "or", "repeat", "return", "then", "true", "until", "while", "math", "string", "table",
            "evt", "MM9", "ipairs", "pairs", "tostring", "tonumber", "MonsterBits", "ActorKillCheck"}


def strip_lua(text: str) -> str:
    """Lua code without its comments and string contents (strings become "")."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if text.startswith("--", i):
            long = re.match(r"--\[(=*)\[", text[i:])
            if long:
                end = text.find("]" + long.group(1) + "]", i)
                i = n if end < 0 else end + len(long.group(1)) + 2
            else:
                end = text.find("\n", i)
                i = n if end < 0 else end
            continue
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            out.append('""')
            i = j + 1
            continue
        long = re.match(r"\[(=*)\[", text[i:]) if c == "[" else None
        if long:
            end = text.find("]" + long.group(1) + "]", i)
            out.append('""')
            i = n if end < 0 else end + len(long.group(1)) + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _balanced(code: str, start: int, opening: str = "(", closing: str = ")") -> str:
    """The text from start up to the bracket closing the one just before start."""
    depth, i = 1, start
    while i < len(code) and depth:
        if code[i] in "({[":
            depth += 1
        elif code[i] in ")}]":
            depth -= 1
        i += 1
    return code[start:i - 1]


def _first_argument(arguments: str) -> str:
    depth = 0
    for i, c in enumerate(arguments):
        if c in "({[":
            depth += 1
        elif c in ")}]":
            depth -= 1
        elif c == "," and depth == 0:
            return arguments[:i]
    return arguments


def _expression(code: str, start: int) -> str:
    """A definition's right-hand side: a table constructor with its braces, else the rest of the line."""
    if code[start:start + 1] == "{":
        return "{" + _balanced(code, start + 1) + "}"
    end = code.find("\n", start)
    return code[start:end if end >= 0 else len(code)]


def _argument(arguments: str, n: int) -> str:
    """The n-th (0-based) top-level argument of a call's argument text ("" when it has fewer)."""
    depth, start, k = 0, 0, 0
    for i, c in enumerate(arguments):
        if c in "({[":
            depth += 1
        elif c in ")}]":
            depth -= 1
        elif c == "," and depth == 0:
            if k == n:
                return arguments[start:i]
            k, start = k + 1, i + 1
    return arguments[start:] if k == n else ""


def lua_actor_indices(text: str, directories=()) -> set[int]:
    """The actor indices a map script names, conservatively: the literal or resolved first argument of the actor
    calls (ACTOR_CALL; CheckMonstersKilled by actor), the tables and constants a killed or damaged actor's index
    (context.actorIndex) is looked up in or compared with, followed through local constants, tables (every integer
    in them) and the tables a loop variable runs over. Scopes are not told apart (a name's every definition counts).
    directories: tables that list every placed actor by name for the map's messages (Hooks.density_lua_directories),
    not followed."""
    code = strip_lua(text)
    definitions, loops = _scopes(code)
    index_variables = set(INDEX_VARIABLE.findall(code))
    seeds = []
    for match in ACTOR_CALL.finditer(code):
        seeds.append(_first_argument(_balanced(code, match.end())))
    for match in RECEIVES_CALL.finditer(code):
        seeds.append(_argument(_balanced(code, match.end()), 3))
    for match in KILL_CHECK.finditer(code):
        if match.group(1) not in ("Group", "MonsterId"):
            seeds.append(_first_argument(_balanced(code, match.end())))
    lookups = index_variables | {r"\w+\.actorIndex"}
    for variable in lookups:
        name = variable if variable.startswith("\\") else re.escape(variable)
        seeds += re.findall(rf"([A-Za-z_]\w*)\s*\[\s*{name}\s*\]", code)
        seeds += re.findall(rf"(?<![\w.]){name}\s*[=~]=\s*([A-Za-z_]\w*|\d+)", code)
        seeds += re.findall(rf"([A-Za-z_]\w*|\d+)\s*[=~]=\s*{name}(?![\w.])", code)
    return _resolve(seeds, definitions, loops, set(directories))


def _scopes(code: str) -> tuple[dict, dict]:
    """Every name's definitions (right-hand sides) and the tables each loop variable runs over."""
    definitions: dict[str, list[str]] = {}
    for match in DEFINITION.finditer(code):
        names = [name.strip() for name in match.group(1).split(",")]
        if names[-1] in KEYWORDS:
            continue
        expression = _expression(code, match.end())
        for name in names:
            definitions.setdefault(name, []).append(expression)
    loops: dict[str, list[str]] = {}
    for match in LOOP.finditer(code):
        iterated = _balanced(code, match.end())
        for name in match.group(1).split(","):
            loops.setdefault(name.strip(), []).append(iterated)
    return definitions, loops


def _resolve(seeds: list[str], definitions: dict, loops: dict, visited: set[str]) -> set[int]:
    """The integers of the seed expressions, followed through definitions and loop tables (lua_actor_indices)."""
    found: set[int] = set()

    def resolve(expression: str) -> None:
        found.update(int(v) for v in INTEGER.findall(expression))
        for name in IDENTIFIER.findall(expression):
            if name in KEYWORDS or name in visited:
                continue
            visited.add(name)
            for iterated in loops.get(name, []):
                resolve(iterated)
            for value in definitions.get(name, []):
                if ".actorIndex" not in value and not value.lstrip().startswith("function"):
                    resolve(value)

    for seed in seeds:
        resolve(seed)
    return found


def lua_group_numbers(text: str) -> set[int]:
    """The actor groups a map script addresses (group bits, wakes, allies and group kill checks), resolved like
    lua_actor_indices: a placed member of one of them is part of a scripted group (Lich Lab's summoner, group 70)."""
    code = strip_lua(text)
    definitions, loops = _scopes(code)
    seeds = [_first_argument(_balanced(code, match.end())) for match in GROUP_CALL.finditer(code)]
    for match in KILL_CHECK.finditer(code):
        if match.group(1) == "Group":
            seeds.append(_first_argument(_balanced(code, match.end())))
    return _resolve(seeds, definitions, loops, set())


def lua_strings(text: str, directories=()) -> set[str]:
    """The lowercase string literals of a map script outside its comments and its one-line actor directories
    (Hooks.density_lua_directories): a DAT name among them is a message target or a scripted name."""
    for name in directories:
        text = re.sub(rf"^local {re.escape(name)} = \{{.*$", "", text, flags=re.MULTILINE)
    out: set[str] = set()
    i, n = 0, len(text)
    while i < n:                     # comments out, strings kept (strip_lua drops the strings)
        if text.startswith("--", i):
            long = re.match(r"--\[(=*)\[", text[i:])
            end = text.find("]" + long.group(1) + "]", i) if long else text.find("\n", i)
            i = n if end < 0 else end + 1
            continue
        match = STRING.match(text, i)
        if match:
            out.add((match.group(1) if match.group(1) is not None else match.group(2)).lower())
            i = match.end()
            continue
        i += 1
    return out


# --- Which members a pack may copy ---------------------------------------------------------------------------------
# The unique bosses' MM9 rows (tools/mm9_import_discovery/mm9_monster_families.yml, its single-picture "bosses and
# unique actors": Yanmir, the Dragon King, Njam the Meddler, Ebora) as engine monster ids (9000 + row). Not the Lich
# King (209): the Lich Lab places its lich kings and lich scientists on that row as an ordinary pack monster.
BOSS_MONSTER_IDS = frozenset(9000 + row for row in (206, 212, 261, 301))
INSTANCE_NUMBER = re.compile(r"\d+$")


@dataclass
class References:
    """What marks a member as scripted beyond its scene record: its DAT placement (anchor -> (class, properties)),
    how often each DAT name is used, and what the map's Lua and cinematics name (scripted_reason)."""
    dat: dict = field(default_factory=dict)
    name_uses: Counter = field(default_factory=Counter)
    lua_groups: set = field(default_factory=set)
    lua_names: set = field(default_factory=set)
    scene_indices: set = field(default_factory=set)

    @classmethod
    def of(cls, source, script: str, directories=(), cinematics: dict | None = None) -> "References":
        """From the build's DAT world (dungeon.source.Source), the map Lua and the map's cinematics (parsed YAML)."""
        dat = {o["name"].lower(): (o["class"], o["properties"]) for o in source.objects if o["name"]}
        return cls(dat=dat, name_uses=Counter(o["name"].lower() for o in source.objects if o["name"]),
                   lua_groups=lua_group_numbers(script), lua_names=lua_strings(script, directories),
                   scene_indices=cinematic_actors(cinematics))

    def reason(self, anchor: str | None) -> str | None:
        if anchor is None:
            return None
        key = anchor.lower()
        if key in self.lua_names:
            return "named by the map Lua"
        if key not in self.dat:
            return None
        cls, properties = self.dat[key]
        if str(properties.get("ScriptName") or "").strip():
            return "script"
        if properties.get("ShouldRepopulate", 1) == 0:
            return "quest actor"
        if (not INSTANCE_NUMBER.search(anchor) and key != cls.lower() and self.name_uses[key] == 1):
            return "unique name"
        return None


def cinematic_actors(cinematics) -> set[int]:
    """The actor indices a map's cinematics name (any `actor` or `look_at_actor` value, at any depth)."""
    found: set[int] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("actor", "look_at_actor") and isinstance(value, int) and not isinstance(value, bool):
                    found.add(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(cinematics or {})
    return found


def scripted_reason(actor: dict, lua_indices: set[int], references: References | None = None,
                    anchor: str | None = None) -> str | None:
    """Why a pack member is not copied (None: an ordinary member)."""
    if actor.get("npc_id") or actor.get("mm9_rude_id") or actor.get("unique_name_index"):
        return "identity"
    if int(actor.get("attributes", 0)) & INVISIBLE_BIT:
        return "hidden"
    if actor.get("mm9_can_receive_damage") is False:
        return "scripted damage"
    if actor.get("respawns_on_refill") is False:
        return "quest actor"
    ai = actor.get("mm9_ai") or {}
    if (ai.get("profile") or {}).get("passive"):
        return "passive"
    if ai.get("boss") or actor.get("monster_id") in BOSS_MONSTER_IDS:
        return "boss"
    if actor["actor_index"] in lua_indices:
        return "named by the map Lua"
    references = references or References()
    if actor.get("group") and actor["group"] in references.lua_groups:
        return "group named by the map Lua"
    if actor["actor_index"] in references.scene_indices:
        return "named by the map's cinematics"
    return references.reason(anchor)


def copy_record(member: dict, index: int, position: tuple) -> dict:
    """A copy of a member's scene record at a new place, without its name-bound identity."""
    out = copying.deepcopy(member)
    for key in ("mm9_rude_id", "mm9_source_object_index"):
        out.pop(key, None)
    out.update(actor_index=index, npc_id=0, unique_name_index=0,
               position={"x": int(round(position[0])), "y": int(round(position[1])), "z": int(round(position[2]))})
    return out


# --- Where a copy may stand: the compiled BLV with the scene's doors, ladders and water -------------------------------
def _inside(x: float, y: float, ring: np.ndarray) -> bool:
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


class World:
    """The walkable floors (with their sector and what lies on them), walls and no-go boxes of a compiled BLV."""

    def __init__(self, blv: dict, scene: dict, liquid_textures: set[str]):
        vertices = np.array([(v["x"], v["y"], v["z"]) for v in blv["vertices"]], float)
        state = scene.get("initial_state") or {}
        doors = state.get("doors") or []
        door_faces = {f for door in doors for f in door.get("face_ids", [])}
        barriers = set((scene.get("actor_barriers") or {}).get("faces", []))
        textures = {o["face_index"]: str(o["texture_name"]).lower()
                    for o in state.get("face_attribute_overrides") or [] if o.get("texture_name")}
        self.floors, self.cells = [], {}
        self.covers = {}          # every solid face but the walls by plan cell: (ring, unit normal, point, low, high)
        self.zones = []           # (x0, y0, x1, y1, z0, z1, kind): no copy's body may overlap one
        for face in blv["faces"]:
            if face["is_portal"] or face["index"] in barriers:
                continue
            points = vertices[face["vertex_indices"]]
            self._add_cover(points, int(face["attributes"]))
            attributes = int(face["attributes"])
            event = int((face.get("face_param") or {}).get("cog_triggered", 0)) or attributes & TRIGGER_ATTRIBUTES
            if face["index"] in door_faces:
                self.zones.append(self._swept_box(points, doors, face["index"]) + ("door",))
            elif event:
                low, high = points.min(0), points.max(0)
                self.zones.append((low[0], low[1], high[0], high[1], low[2], high[2], "event"))
            if face["facet_type"] not in FLOOR_TYPES or attributes & UNTOUCHABLE:
                continue
            normal = np.zeros(3)
            for k in range(1, len(points) - 1):
                normal += np.cross(points[k] - points[0], points[k + 1] - points[0])
            if normal[2] <= 1e-6 * max(1.0, np.linalg.norm(normal)):
                continue
            texture = textures.get(face["index"], str(face["texture_name"]).lower())
            water = bool(attributes & (FLUID | LAVA)) or texture in liquid_textures
            kind = "door" if face["index"] in door_faces else "event" if event else "water" if water else None
            record = {"ring": points[:, :2], "normal": normal, "point": points[0], "sector": face["room_number"],
                      "kind": kind, "low": points[:, :2].min(0), "high": points[:, :2].max(0),
                      "walkable": normal[2] >= WALKABLE_NORMAL_Z * np.linalg.norm(normal)}
            self.floors.append(record)
            for cx in range(int(record["low"][0] // GRID), int(record["high"][0] // GRID) + 1):
                for cy in range(int(record["low"][1] // GRID), int(record["high"][1] // GRID) + 1):
                    self.cells.setdefault((cx, cy), []).append(record)
        for ladder in scene.get("ladders") or []:
            reach = float(ladder.get("width", 96)) / 2 + float(ladder.get("reach", 48))
            for key in ("bottom", "top", "top_exit"):
                if key in ladder:
                    x, y, z = ladder[key]
                    self.zones.append((x - reach, y - reach, x + reach, y + reach, z - 64, z + 256, "ladder"))
        self.water = [(np.array(piece["polygon"], float), float(piece["bottom"]), float(piece["top"]))
                      for volume in scene.get("water_volumes") or [] for piece in volume.get("pieces", [])]
        walls = wall_segments(blv)
        self.walls = walls if walls.size else np.zeros((6, 0))

    def _add_cover(self, points: np.ndarray, attributes: int) -> None:
        if attributes & UNTOUCHABLE:
            return
        normal = np.zeros(3)
        for k in range(1, len(points) - 1):
            normal += np.cross(points[k] - points[0], points[k + 1] - points[0])
        length = np.linalg.norm(normal)
        if length < 1e-6 or abs(normal[2]) < 0.02 * length:
            return
        record = (points[:, :2], normal / length, points[0], points[:, :2].min(0), points[:, :2].max(0))
        for cx in range(int(record[3][0] // GRID), int(record[4][0] // GRID) + 1):
            for cy in range(int(record[3][1] // GRID), int(record[4][1] // GRID) + 1):
                self.covers.setdefault((cx, cy), []).append(record)

    def under_cover(self, x: float, y: float, z: float) -> bool:
        """Whether the first face over feet at z is a floor's top: under the ground or in a solid (the Isle of Ashes'
        invisible terrain skins lie 20-60 over the ground under them)."""
        return self.first_over(x, y, z)[1]

    def first_over(self, x: float, y: float, z: float) -> tuple:
        """(height, faces up) of the first face over z at (x, y); (None, False) when there is none."""
        first, facing_up = None, False
        for ring, normal, point, low, high in self.covers.get((int(x // GRID), int(y // GRID)), []):
            if not (low[0] <= x <= high[0] and low[1] <= y <= high[1]) or not _inside(x, y, ring):
                continue
            h = point[2] - (normal[0] * (x - point[0]) + normal[1] * (y - point[1])) / normal[2]
            if h > z + 1 and (first is None or h < first):
                first, facing_up = h, normal[2] > 0
        return first, facing_up

    @staticmethod
    def _swept_box(points: np.ndarray, doors: list, face: int) -> tuple:
        """A door face's box over its whole travel (the stored pose and the pose move_length along its direction)."""
        low, high = points.min(0), points.max(0)
        for door in doors:
            if face in door.get("face_ids", []):
                travel = np.array(door.get("direction", [0, 0, 0]), float) / 65536.0 * float(door.get("move_length", 0))
                low, high = np.minimum(low, low + travel), np.maximum(high, high + travel)
                low, high = np.minimum(low, low - travel), np.maximum(high, high - travel)
        return (low[0], low[1], high[0], high[1], low[2], high[2])

    def floor(self, x: float, y: float, z_from: float):
        """The highest floor at (x, y) at or under z_from: (z, floor record), or (None, None)."""
        best, found = None, None
        for record in self.cells.get((int(x // GRID), int(y // GRID)), []):
            if not (record["low"][0] <= x <= record["high"][0] and record["low"][1] <= y <= record["high"][1]):
                continue
            if not _inside(x, y, record["ring"]):
                continue
            n, p = record["normal"], record["point"]
            z = p[2] - (n[0] * (x - p[0]) + n[1] * (y - p[1])) / n[2]
            if z <= z_from + 0.5 and (best is None or z > best):
                best, found = z, record
        return best, found

    def wall_distance(self, x: float, y: float, z_low: float, z_high: float, reach: float) -> float:
        """The plan distance to the nearest wall whose height range overlaps [z_low, z_high], at most reach."""
        if not self.walls.shape[1]:
            return reach
        x1, y1, x2, y2, zmin, zmax = self.walls
        keep = ((zmin <= z_high) & (zmax >= z_low) & (np.minimum(x1, x2) < x + reach) & (np.maximum(x1, x2) > x - reach)
                & (np.minimum(y1, y2) < y + reach) & (np.maximum(y1, y2) > y - reach))
        if not keep.any():
            return reach
        ax, ay, bx, by = x1[keep], y1[keep], x2[keep], y2[keep]
        dx, dy = bx - ax, by - ay
        t = np.clip(((x - ax) * dx + (y - ay) * dy) / np.maximum(dx * dx + dy * dy, 1e-9), 0, 1)
        return float(min(reach, np.hypot(ax + t * dx - x, ay + t * dy - y).min()))

    def crosses_wall(self, a, b, z_low: float, z_high: float) -> bool:
        if not self.walls.shape[1]:
            return False
        x1, y1, x2, y2, zmin, zmax = self.walls
        keep = ((zmin <= z_high) & (zmax >= z_low) & (np.maximum(x1, x2) >= min(a[0], b[0]))
                & (np.minimum(x1, x2) <= max(a[0], b[0])) & (np.maximum(y1, y2) >= min(a[1], b[1]))
                & (np.minimum(y1, y2) <= max(a[1], b[1])))
        if not keep.any():
            return False
        px, py, ex, ey = x1[keep], y1[keep], x2[keep] - x1[keep], y2[keep] - y1[keep]
        dx, dy = b[0] - a[0], b[1] - a[1]
        den = dx * ey - dy * ex
        ok = np.abs(den) > 1e-9
        safe = np.where(ok, den, 1.0)
        t = ((px - a[0]) * ey - (py - a[1]) * ex) / safe
        u = ((px - a[0]) * dy - (py - a[1]) * dx) / safe
        return bool(np.any(ok & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)))

    def in_zone(self, x: float, y: float, z_low: float, z_high: float, clearance: float) -> str | None:
        for x0, y0, x1, y1, z0, z1, kind in self.zones:
            if (x0 - clearance <= x <= x1 + clearance and y0 - clearance <= y <= y1 + clearance
                    and z0 <= z_high and z1 >= z_low):
                return kind
        return None

    def in_water(self, x: float, y: float, z: float) -> bool:
        return any(bottom - 8 <= z <= top and _inside(x, y, ring) for ring, bottom, top in self.water)

    def spot(self, member: dict, body: dict, x: float, y: float, actors: list) -> tuple | None:
        """The copy's feet at (x, y) next to member when every rule holds (module docstring), else None."""
        return self.check(member, body, x, y, actors)[0]

    def check(self, member: dict, body: dict, x: float, y: float, actors: list) -> tuple:
        """(the copy's feet at (x, y), "") when every rule holds, else (None, the first rule it breaks)."""
        mx, my, mz = (float(member["position"][k]) for k in ("x", "y", "z"))
        radius, height = float(body.get("radius") or 40), float(body.get("height") or 120)
        # the member's own floor: a flyer (Isle of Ashes' dragonflies) keeps its height over it in the copy
        home, _ = self.floor(mx, my, mz + 1)
        if home is None or self.under_cover(mx, my, home):
            return None, "member has no floor"
        lift = max(1.0, mz - home)
        z, record = self.floor(x, y, home + FLOOR_STEP)
        if record is None or abs(z - home) > FLOOR_STEP:
            return None, "other floor"
        if record["kind"]:
            return None, record["kind"]
        if not record["walkable"]:
            return None, "steep"
        cover, facing_up = self.first_over(x, y, z)
        if facing_up:
            return None, "under a floor"
        if lift > 1 and cover is not None and cover < z + lift + height / 2:
            return None, "in the ceiling"       # a flyer at its member's height over a lower room
        if record["sector"] != member.get("sector_id", record["sector"]):
            return None, "other room"
        for k in range(8):           # the body's footprint stands on the same floor, nothing under it
            angle = k * math.pi / 4
            fz, frecord = self.floor(x + radius * math.cos(angle), y + radius * math.sin(angle), z + FLOOR_STEP)
            if frecord is None or abs(fz - z) > FLOOR_STEP:
                return None, "footprint off the floor"
            if frecord["kind"]:
                return None, frecord["kind"]
            if not frecord["walkable"]:
                return None, "steep"
        steps = max(1, int(math.hypot(x - mx, y - my) // PATH_STEP))
        for k in range(1, steps):       # no pit or step on the way from the member
            px, py = mx + (x - mx) * k / steps, my + (y - my) * k / steps
            pz, precord = self.floor(px, py, home + FLOOR_STEP)
            if precord is None or abs(pz - home) > FLOOR_STEP:
                return None, "pit or step on the way"
        if self.crosses_wall((mx, my), (x, y), min(home, z) + 16, max(home, z) + 64):
            return None, "behind a wall"
        if self.wall_distance(x, y, z + 8, z + height, radius + MARGIN) < radius + MARGIN:
            return None, "against a wall"
        zone = self.in_zone(x, y, z - 8, z + height, radius + MARGIN)
        if zone:
            return None, zone
        if self.in_water(x, y, z):
            return None, "water"
        foot = math.floor(z) + round(lift)
        for other in actors:
            p = other["position"]
            if p["z"] > foot + height or p["z"] + float(other.get("height") or 120) < foot:
                continue
            if math.hypot(p["x"] - x, p["y"] - y) < radius + float(other.get("radius") or 40) + MARGIN:
                return None, "another actor"
        return (x, y, foot), ""


def candidates(member: dict, body: dict, seed: str):
    """Plan points round a member, nearest first, at angles seeded by `seed` (stable across reconversions)."""
    rng = random.Random(int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16))
    mx, my = float(member["position"]["x"]), float(member["position"]["y"])
    near = max(MIN_DISTANCE + 1, float(member.get("radius") or 40) + float(body.get("radius") or 40) + MARGIN)
    if near > MAX_DISTANCE:
        return
    offset = rng.random() * 2 * math.pi
    for ring in range(RINGS):
        distance = near + (MAX_DISTANCE - near) * ring / (RINGS - 1)
        jitter = rng.random() * 2 * math.pi / ANGLES
        for k in range(ANGLES):
            angle = offset + jitter + 2 * math.pi * k / ANGLES
            yield mx + distance * math.cos(angle), my + distance * math.sin(angle)


# --- Growth ---------------------------------------------------------------------------------------------------------
def map_packs(stem: str, anchors_path: Path = ANCHORS) -> list[dict]:
    """The map's packs with something to add (density_anchors.json)."""
    entry = json.loads(anchors_path.read_text())["maps"].get(stem) or {}
    return [pack for pack in entry.get("packs", []) if int(pack.get("add", 0)) > 0]


def scale_adds(packs: list[dict], scale: float) -> list[dict]:
    """The packs with each `add` scaled (module docstring): the scaled total rounded, its floors first, then one more
    to each pack by largest remainder (pack order breaks ties); packs left with nothing are dropped."""
    if scale == 1.0:
        return packs
    if not 0.0 <= scale <= 1.0:
        raise SystemExit(f"pack growth: density_scale {scale} must be between 0 and 1")
    exact = [int(pack["add"]) * scale for pack in packs]
    adds = [math.floor(value) for value in exact]
    rest = round(sum(exact)) - sum(adds)
    for i in sorted(range(len(packs)), key=lambda i: (adds[i] - exact[i], i))[:rest]:
        adds[i] += 1
    return [dict(pack, add=add) for pack, add in zip(packs, adds) if add > 0]


SCRIPTED_ONLY, NO_SPOT = "the pack's members are all scripted", "no free spot by the pack"
ARRIVAL_FULL = "a forced arrival's quota of copies"
LAUNCHERS_FULL = "the pod launchers' quota nearby"


def arrival_distance(arrival: dict, spot: tuple) -> float:
    """Distance from a forced arrival with height counted double (mm9_density_targets.packs_of's link)."""
    x, y, z = arrival["at"]
    return math.sqrt((spot[0] - x) ** 2 + (spot[1] - y) ** 2 + (2 * (spot[2] - z)) ** 2)


def grow(stem: str, actors: list[dict], anchors: dict[str, int], packs: list[dict], world: World,
         lua_indices: set[int], counted_today: int | None = None,
         references: References | None = None, arrivals=()) -> tuple[list[dict], dict]:
    """The copies for a map's packs (the caller appends them after `actors`) and the report. anchors: member anchor
    -> actor index of `actors`; counted_today: the map's counted monsters before growth (the targets' own count).

    First each pack places its own `add`. The copies a pack could not place (scripted members only, or no free spot)
    then go one at a time to the map's other growable packs (ordinary members, no spot refused yet), the one with the
    most room left first (capacity, the targets' room check, less its size after growth); what finds no room stays
    unplaced and is reported with its reason. arrivals: the map's forced arrivals (module docstring); a spot within
    one whose quota is spent is refused."""
    by_index = {a["actor_index"]: a for a in actors}
    placed_actors = list(actors)
    copies, states = [], []
    next_index = max((a["actor_index"] for a in actors), default=-1) + 1
    copies_of: dict[str, int] = {}
    near_arrival: Counter = Counter()

    def arrivals_at(spot: tuple) -> list[str]:
        return [a["name"] for a in arrivals if arrival_distance(a, spot) <= float(a["radius"])]

    def arrival_full(spot: tuple) -> bool:
        return any(near_arrival[a["name"]] >= int(a["copies"])
                   for a in arrivals if arrival_distance(a, spot) <= float(a["radius"]))

    def row_of(anchor: str) -> int:
        return int(by_index[anchors[anchor]].get("monster_info_id", 0))

    def launchers_full(member: dict, spot: tuple) -> bool:
        if int(member.get("monster_info_id", 0)) not in POD_LAUNCHERS:
            return False
        near = sum(1 for other in placed_actors if int(other.get("monster_info_id", 0)) in POD_LAUNCHERS
                   and arrival_distance({"at": tuple(other["position"][axis] for axis in "xyz")}, spot)
                   <= LAUNCHER_RADIUS)
        return near >= LAUNCHERS_PER_SPOT

    def next_row(rows: list[int], made: Counter) -> int:
        """The row furthest below its share of `rows` after one more copy (largest remainder; a tie goes to the larger
        share, then the first listed)."""
        share, total = Counter(rows), sum(made.values()) + 1
        return max(dict.fromkeys(rows), key=lambda row: (share[row] * total / len(rows) - made[row], share[row]))

    def copy_order(state: dict, row: int | None) -> list[str]:
        """The ordinary members to try, best first: those of the wanted row (the pack's most under-copied row, or a
        moved copy's own), the least copied first, then the others the same way."""
        ordinary = state["ordinary"]
        if row is None:
            row = next_row([row_of(anchor) for anchor in state["members"]], state["made"])
        rank = {anchor: position for position, anchor in enumerate(ordinary)}
        return sorted(ordinary, key=lambda anchor: (row_of(anchor) != row, copies_of.get(anchor, 0), rank[anchor]))

    def place(state: dict, moved: bool, row: int | None = None) -> bool:
        nonlocal next_index
        entry = state["entry"]
        state["tried"] += 1
        n = state["tried"] - 1
        order = copy_order(state, row)
        placed, why = None, Counter()
        for anchor in order:
            member = by_index[anchors[anchor]]
            for x, y in candidates(member, member, f"{stem}|{anchor}|{n}"):
                spot, reason = world.check(member, member, x, y, placed_actors)
                if spot is not None and arrival_full(spot):
                    spot, reason = None, ARRIVAL_FULL
                if spot is not None and launchers_full(member, spot):
                    spot, reason = None, LAUNCHERS_FULL
                if spot is not None:
                    placed = (anchor, member, spot)
                    break
                why[reason] += 1
            if placed:
                break
        if placed is None:
            entry["refused"] = dict(Counter(entry.get("refused", {})) + why)
            state["full"] = True
            return False
        anchor, member, spot = placed
        near_arrival.update(arrivals_at(spot))
        copies_of[anchor] = copies_of.get(anchor, 0) + 1
        state["made"][row_of(anchor)] += 1
        record = copy_record(member, next_index, spot)
        next_index += 1
        copies.append(record)
        placed_actors.append(record)
        entry["copies"].append({"anchor": f"{anchor}_grow{copies_of[anchor]}", "copy_of": anchor,
                                "actor_index": record["actor_index"], "position": list(map(int, spot)),
                                **({"moved": True} if moved else {})})
        return True

    pool = []                     # the copies a pack could not place: (reason, the monster row they stand for)
    for pack in packs:
        wanted = int(pack["add"])
        size = len(pack["members"])
        capacity = int(pack.get("capacity") or size + wanted)
        entry = {"members": pack["members"], "wanted": wanted, "placed": 0, "moved_in": 0, "capacity": capacity,
                 "skipped": {}, "copies": []}
        ordinary = []
        for anchor in pack["members"]:
            if anchor not in anchors:
                entry["skipped"][anchor] = "not placed"
                continue
            reason = scripted_reason(by_index[anchors[anchor]], lua_indices, references, anchor)
            if reason:
                entry["skipped"][anchor] = reason
            else:
                ordinary.append(anchor)
        members = [anchor for anchor in pack["members"] if anchor in anchors]
        state = {"entry": entry, "ordinary": ordinary, "members": members, "size": size, "tried": 0,
                 "full": not ordinary, "made": Counter()}
        states.append(state)

        def shortfall_rows(count: int) -> list[int]:
            # The rows the pack's missing copies stand for, continuing its own mix.
            made, rows = Counter(state["made"]), []
            for _ in range(count):
                row = next_row([row_of(anchor) for anchor in members], made) if members else 0
                made[row] += 1
                rows.append(row)
            return rows

        if not ordinary:
            entry["note"] = "only scripted or unplaced members: its copies go to the other packs"
            pool += [(SCRIPTED_ONLY, row) for row in shortfall_rows(wanted)]
            continue
        own = min(wanted, capacity - size)
        for _ in range(own):
            if not place(state, moved=False):
                break
        pool += [(NO_SPOT, row) for row in shortfall_rows(wanted - len(entry["copies"]))]

    def room(state: dict) -> int:
        return state["entry"]["capacity"] - state["size"] - len(state["entry"]["copies"])

    moved, unplaced = 0, Counter()
    while pool:
        open_states = [s for s in states if not s["full"] and room(s) > 0]
        if not open_states:
            break
        _, row = pool[0]
        # The roomiest pack with an ordinary member of the copy's row, else the roomiest; the first of them in pack order.
        same_row = [s for s in open_states if any(row_of(anchor) == row for anchor in s["ordinary"])]
        receiver = max(same_row or open_states, key=room)
        if place(receiver, moved=True, row=row if same_row else None):
            receiver["entry"]["moved_in"] += 1
            moved += 1
            pool.pop(0)
    unplaced.update(f"{reason}, and no other pack had room and a free spot" for reason, _ in pool)
    report_packs = []
    for state in states:
        entry = state["entry"]
        own = [c for c in entry["copies"] if not c.get("moved")]
        entry["placed"] = len(own)
        entry["room_left"] = room(state)
        if entry["placed"] < entry["wanted"]:
            entry["shortfall"] = entry["wanted"] - entry["placed"]
        report_packs.append(entry)
    wanted_adds, placed_adds = sum(p["wanted"] for p in report_packs), len(copies)
    summary = {"packs": len(report_packs), "wanted": wanted_adds, "placed": placed_adds,
               "packs_short": sum(1 for p in report_packs if p.get("shortfall")),
               "packs_scripted_only": sum(1 for p in report_packs if p.get("note")),
               "wanted_adds": wanted_adds, "placed_adds": placed_adds, "moved_adds": moved,
               "unplaced_adds": wanted_adds - placed_adds, "unplaced_reasons": dict(unplaced)}
    if arrivals:
        summary["arrivals"] = {a["name"]: {"copies": near_arrival[a["name"]], "quota": int(a["copies"])}
                               for a in arrivals}
    if counted_today is not None:
        summary.update(counted_today=counted_today, target_total=counted_today + wanted_adds,
                       placed_total=counted_today + placed_adds)
    return copies, {"map": stem, "summary": summary, "packs": report_packs}


def counted_today(stem: str) -> int | None:
    """The map's counted monsters before growth (mm9_density_targets.yml `counted_today`, read only)."""
    import yaml
    targets = Path(__file__).resolve().parents[4] / json.loads(ANCHORS.read_text())["targets"]
    entry = (yaml.load(targets.read_text(), Loader=yaml.CSafeLoader)["maps"].get(stem) or {})
    return entry.get("counted_today")


def installed_cinematics(stem: str) -> dict | None:
    """The map's cinematics in the review root (cinematics.py installs them before a conversion), parsed."""
    import yaml
    import review_root
    path = review_root.mirror_path(f"worlds/mm9/maps/{stem}.cinematics.yml")
    return yaml.load(path.read_text(), Loader=yaml.CSafeLoader) if path.is_file() else None


def liquid_textures() -> set[str]:
    """Every MM9 liquid's texture names (liquids.py), with the raw BLV names its surfaces retexture."""
    import liquids
    return liquids.mm9_liquid_textures() | set(liquids.SURFACES)


def lua_name_tables(hooks) -> tuple:
    """The map Lua's tables that list placed actors by name without scripting them, which the Lua scan skips: the
    directories that take the copies (Hooks.density_lua_directories) and the tables that only name them
    (Hooks.density_lua_name_tables)."""
    return tuple(getattr(hooks, "density_lua_directories", ())) + tuple(getattr(hooks, "density_lua_name_tables", ()))


def add_to_directories(script: str, directories, placed: list[dict]) -> str:
    """The map Lua with the placed copies (density.json `copies` entries) added to its actor directory tables
    (Hooks.density_lua_directories), each defined on one line as `local NAME = {...}`."""
    for name in directories:
        definition = re.search(rf"^local {re.escape(name)} = \{{.*$", script, re.MULTILINE)
        if definition is None:
            raise SystemExit(f"pack growth: the map Lua has no one-line `local {name} = {{...}}` directory")
        if placed:
            entries = ", ".join(f'["{c["anchor"]}"] = {c["actor_index"]}' for c in placed)
            line = f"for name, index in pairs({{{entries}}}) do {name}[name] = index end   -- pack growth (density.py)"
            script = script[:definition.end()] + "\n" + line + script[definition.end():]
    return script


def apply(build, scene: dict, script: str) -> str:
    """The build's pack growth (build.py, after the scene hook and the map Lua): appends the copies to the scene's
    actors and the content report, adds them to the script's actor directories, writes work/density.json (its summary
    in build.density) and returns the map Lua, which the map's `grown` hook may still change."""
    import sys
    from .source import ROOT
    project, hooks = build.project, build.hooks
    enabled = project.overrides["map"].get("density", True) and build.grow_packs
    packs = scale_adds(map_packs(project.stem), float(project.overrides["map"].get("density_scale", 1.0))) \
        if enabled else []
    work = project.work / "density.json"
    if not packs:
        _, result = grow(project.stem, scene["initial_state"]["actors"], {}, [], None, set(),
                         counted_today(project.stem))
        result["note"] = "growth off" if not enabled else "no packs to grow"
        work.write_text(json.dumps(result, indent=1) + "\n")
        build.density = result["summary"]
        return script
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(build.runtime / project.map)["payload"]
    actors = scene["initial_state"]["actors"]
    report_actors = build.content.report["actors"]
    anchors = {entry["anchor"]: entry["actor_index"] for entry in report_actors}
    directories = tuple(getattr(hooks, "density_lua_directories", ()))
    named = lua_name_tables(hooks)
    references = References.of(build.source, script, named, installed_cinematics(project.stem))
    copies, result = grow(project.stem, actors, anchors, packs, World(blv, scene, liquid_textures()),
                          lua_actor_indices(script, named), counted_today(project.stem), references,
                          project.overrides["map"].get("density_arrivals") or ())
    by_index = {entry["actor_index"]: entry for entry in report_actors}
    placed = [c for pack in result["packs"] for c in pack["copies"]]
    for entry in placed:
        source = {k: v for k, v in by_index[anchors[entry["copy_of"]]].items() if k != "note"}
        report_actors.append(dict(source, actor_index=entry["actor_index"], anchor=entry["anchor"], hidden=False,
                                  copy_of=entry["copy_of"]))
    actors += copies
    script = add_to_directories(script, directories, placed)
    work.write_text(json.dumps(result, indent=1) + "\n")
    build.density = result["summary"]
    summary = result["summary"]
    print(f"pack growth: {summary['placed_adds']} of {summary['wanted_adds']} copies placed ({summary['moved_adds']} "
          f"moved to other packs, {summary['unplaced_adds']} unplaced; work/density.json)")
    return hooks.grown(build, scene, script, copies)
