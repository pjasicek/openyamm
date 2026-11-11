"""
Doors and movers: every DAT mover model (overrides.yml `models` rules with a group and a motion) as a native linear
mechanism. Motions: `dat` (MM9's own linear Door: MoveDir, MoveDist, Speed), `rise` (a rotating door leaf pair rises
into the wall above its doorway), `sink` (a breakable plug drops under the floor in front of it), `nudge` (a
rotating lever or switch moves `move_lt` instead of swinging), `slide` (a rotating door or panel slides `move_lt`),
`rotate` (MM9's own swing, a rotating mover: devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md, one mover per leaf; rotation.py). Rule keys: doorway (the
mover closes a portal), portal (its name), click (default true: a click event toggles the group), authored_open
(a linear leaf: MM9 authors the leaves open and its open shuts them; a `rotate` leaf: MM9 authors it in its open
pose, StartOpen, Drangheim Prison's Celldoor18; both are built shut and start open), start_open, locked_event (the
click runs the map's own handler instead of the plain toggle), owner_lt (a LithTech point in the room that owns the
mover, instead of the room nearest its centre), drives (other door groups the group's click toggles with it: a lever
and its gate, Sturmford's Portcullislever), shoot (its faces run the group's event when a missile strikes them,
TriggerByObject: Thjorad Mine's falling torches, MM9's OnDamage on a WorldObject). Click events: a doorway's group
(unless `click: false`), every group with Hooks.all_doors_click, and a free MM9 door (`free_door`: PushOpen, not
Locked, no object or script sends it a message, no map event; MM9's USE toggles it: Thronheim City's Secretdoor0, Thjorgard City's BembgateL/R). A mover's invisible faces become a second mechanism
`<node>_INV` with the same motion, flagged invisible (one door id each; the group's events move both); its glass
faces (overrides.yml `glass`) likewise a mechanism `<node>_GLASS<k>` per glass kind (rooms.Glass), whose faces the
scene draws translucent (devdocs/INDOOR_TRANSLUCENT_FACES.md).
See ../DUNGEON_PLAYBOOK.md.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import numpy as np

from .geometry import Polygon
from .package import room_id
from .rotation import authored_open_polygons, rotating_mover, swing_room
from .rooms import mover_groups
from .source import SCALE, floor_below, lt_vector_to_native

RISE_SPEED = 192            # native units per second for the converted MM9 swing doors
SINK_SPEED = 384            # breakable wall plugs (MM9 destroys them at once)
NUDGE_SPEED = 64            # levers and switches (MM9 swings them in about a second)
DOOR_EVENT_BASE = 100       # door group k's click event is DOOR_EVENT_BASE + k (k from 1)
# MM9's door sound properties -> the scene door's `sounds` keys (game/maps/MechanismAudioYml.h)
SOUND_FIELDS = (("open", "OpenSoundName"), ("close", "CloseSoundName"), ("open_start", "OpenStartSound"),
                ("open_busy", "OpenBusySound"), ("open_stop", "OpenStopSound"), ("close_start", "CloseStartSound"),
                ("close_busy", "CloseBusySound"), ("close_stop", "CloseStopSound"), ("jiggle", "JiggleSound"))


def door_sounds(properties: dict) -> dict:
    """The MM9 object's own door sounds as world sound names ("Sounds\\Door\\door01open.wav" -> "Door/door01open.wav",
    the old outdoor exporter's names). The engine plays them at the door (no position). An object that names none moves
    silently, as in MM9 (its 151 RotatingDoors and 144 Doors without sounds, levers and drawers among them; a script that
    wants a sound plays it): the empty block keeps MM6-MM8's environment door loop off it (the play-test of 2026-11-06,
    Drangheim City's BlacksmithDoor0/1)."""
    sounds = {}
    for key, name in SOUND_FIELDS:
        value = properties.get(name)
        if not isinstance(value, str) or not value.strip():
            continue
        value = value.strip().replace("\\", "/").lstrip("/")
        for prefix in ("sounds/", "source/sounds/"):
            if value.lower().startswith(prefix):
                value = value[len(prefix):]
        sounds[key] = world_sound(value)
    return sounds


def mover_sounds(name: str, rule: dict, properties: dict) -> dict:
    """A mover's sounds: its overrides.yml rule's `sounds` (keys of SOUND_FIELDS, world sound names such as
    "Door/doorslammetal02.wav") in place of its DAT object's, for a door MM9 leaves silent that should sound (1000
    Terrors' CoffinGate2, the play-test of 2026-11-10); otherwise the DAT object's own (door_sounds)."""
    chosen = rule.get("sounds")
    if chosen is None:
        return door_sounds(properties)
    keys = {key for key, _ in SOUND_FIELDS}
    unknown = sorted(set(chosen) - keys)
    if unknown:
        raise SystemExit(f"{name}: unknown sounds keys {unknown} in overrides.yml (known: {sorted(keys)})")
    return {key: world_sound(value) for key, value in chosen.items()}


_WORLD_SOUNDS: dict[str, list[str]] | None = None


def world_sound(name: str) -> str:
    """A door sound as the MM9 world's audio holds it: a name whose folder MM9 misspells (1000 Terrors' GearElevator:
    "Sounds\\Doors\\elestart.wav", the file is Door/elestart.wav) takes the one file of that name."""
    global _WORLD_SOUNDS
    if _WORLD_SOUNDS is None:
        audio = Path(__file__).resolve().parents[4] / "assets_dev/worlds/mm9/audio"
        _WORLD_SOUNDS = {}
        for path in audio.rglob("*.wav"):
            _WORLD_SOUNDS.setdefault(path.name.lower(), []).append(path.relative_to(audio).as_posix().lower())
    found = _WORLD_SOUNDS.get(name.rsplit("/", 1)[-1].lower(), [])
    if name.lower() in found or len(found) != 1:
        return name
    folder, base = found[0].rsplit("/", 1)
    return f"{folder.capitalize()}/{name.rsplit('/', 1)[-1]}"


def linear_mover(properties: dict) -> dict | None:
    """The scene `mover` block of an MM9 linear Door (no rotation): MM9 closes it CloseWaitTime seconds after it opened,
    unless it is Sticky (the rotating doors' rule, rotation.rotating_mover); a closing leaf reverses on a body with
    ReopenOnContact, else waits for it to leave."""
    wait = float(properties.get("CloseWaitTime", 0.0) or 0.0)
    if wait <= 0.0 or properties.get("Sticky"):
        return None
    return {"easing": "linear", "bodies": "reverse" if properties.get("ReopenOnContact") else "hold", "carry": False,
            "auto_close_seconds": wait}


def spin_block(properties: dict, pivot_native, vector_native) -> dict | None:
    """The scene `mover.spin` of an MM9 RotatingBrush (gears, saws, wheels; devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md
    "Continuous spinners"): about its Pos, one turn per <Axis>AxisRevTime seconds about the axis whose time is set,
    ramping over <Axis>AxisSpinUpTime / SpinDownTime, StartOn. LithTech turns right-handed in its own frame, which the
    native frame mirrors, so <Axis>RotateForward 1 is a negative native turn about the mapped axis. None without a
    revolution time."""
    for index, axis_name in enumerate("XYZ"):
        seconds = float(properties.get(f"{axis_name}AxisRevTime", 0.0) or 0.0)
        if seconds <= 0.0:
            continue
        axis = np.zeros(3)
        axis[index] = 1.0
        native_axis = np.asarray(vector_native(axis), float)
        if properties.get(f"{axis_name}RotateForward", 1):
            native_axis = -native_axis
        return {"pivot": [round(float(v), 3) for v in pivot_native(np.asarray(properties["Pos"], float))],
                "axis": [float(v) + 0.0 for v in native_axis],
                "degrees_per_second": round(360.0 / seconds, 3),
                "spin_up_seconds": round(float(properties.get(f"{axis_name}AxisSpinUpTime", 0.0) or 0.0), 3),
                "spin_down_seconds": round(float(properties.get(f"{axis_name}AxisSpinDownTime", 0.0) or 0.0), 3),
                "start_on": bool(properties.get("StartOn", 0))}
    return None


def start_open(rule: dict, properties: dict) -> bool:
    """Whether a mover starts open: its rule's `start_open`, else MM9's own StartOpen (BaseDoor.inc: a door with
    StartOpen 1 begins in its open pose; Ta'Sar Academy's wall switches Switch/Switch1, Wizard's Lab's closet leaves
    Closet2Door1/2)."""
    return bool(rule.get("start_open", bool(float(properties.get("StartOpen", 0) or 0))))


# The properties naming the objects an MM9 object sends messages to (TargetName<k>, Open/CloseTriggerTarget<k>,
# Death/DamageTriggerTarget, TriggerTarget) and the tokens of its ScriptParams
TARGET_WORD = "Target"


def message_targets(source) -> set:
    """Lower-case names of the objects some object or script of the map may send a message to: a `...Target...`
    property, a ScriptParams token, a word of a script an object runs (`GetObjectHandle Door3 hDoor`). Broad on purpose:
    a door named anywhere there is left to the map's own wiring."""
    from .objects import _script_text
    names, scripts = set(), set()
    for o in source.objects:
        for key, value in o["properties"].items():
            if not isinstance(value, str) or not value.strip():
                continue
            if TARGET_WORD in key or key == "ScriptParams":
                names |= {token.lower() for token in re.split(r"[\s,;]+", value) if token}
                names.add(value.strip().lower())
            elif key == "ScriptName":
                scripts.add(value)
    for name in scripts:
        names |= set(re.findall(r"[a-z0-9_]+", _script_text(name)))
    return names


def locks_itself(source, members: list) -> bool:
    """Whether a door group's own OpenTriggers lock it (`Lock` to a member or a member's DoubleDoorName, which passes
    the lock on). MM9 refuses to close a locked door (StartClosing, devdocs/mm9_rework/MM9_DOOR_OPEN_RE.md §3), so such
    a door never closes by its CloseWaitTime: it stays open until something unlocks and shuts it. Thousand Terrors'
    MiddleDoor4/5 lock themselves as they open and TrigSorcStatueOff3 unlocks and shuts them; with the auto-close the
    door shut and locked behind a party in the treasure room beyond, which had no other way out (2026-11-09)."""
    names = set()
    for name in members:
        names.add(name.lower())
        record = source.by_name.get(name.lower())
        if record is not None and str(record["properties"].get("DoubleDoorName") or "").strip():
            names.add(str(record["properties"]["DoubleDoorName"]).strip().lower())
    for name in members:
        record = source.by_name.get(name.lower())
        if record is None:
            continue
        properties = record["properties"]
        for key, value in properties.items():
            match = re.fullmatch(r"OpenTriggerTarget(\d+)", key)
            if (match and str(value).strip().lower() in names
                    and str(properties.get(f"OpenTrigger{match.group(1)}") or "").strip().lower() == "lock"):
                return True
    return False


def free_door(source, members: list, targets: set) -> bool:
    """An MM9 door the player works with USE and nothing else drives (MM9_DOOR_OPEN_RE.md: PushOpen doors toggle on
    USE; OPEN-wired gates are PushOpen 0): every member a Door or RotatingDoor with PushOpen, not Locked, and named by
    no message (message_targets)."""
    for name in members:
        record = source.by_name.get(name.lower())
        if record is None or record["class"] not in ("Door", "RotatingDoor"):
            return False
        properties = record["properties"]
        if not float(properties.get("PushOpen", 1) or 0) or float(properties.get("Locked", 0) or 0):
            return False
        if name.lower() in targets:
            return False
    return True


def with_spin(block: dict | None, spinning: dict | None) -> dict | None:
    """A mover block with the RotatingBrush's spin added (a plain one for a door that had none)."""
    if spinning is None:
        return block
    block = dict(block or {"easing": "linear", "bodies": "ignore", "carry": False})
    block["spin"] = spinning
    return block


FLAT_MOVER_RATIO = 0.5              # a flat mover: height at most half its smaller horizontal extent
FLAT_MOVER_MIN_LT = 32.0            # ... and at least this wide both ways (something a party can stand on)
FLAT_MOVER_REACH = (1.0, 1.5, 2.0)  # voxels over its top and under its underside where the rooms are read


def flat_mover_owner(points: np.ndarray, rooms) -> np.ndarray | None:
    """A point in the air over a flat mover's top (LT) when its top and underside face different rooms (a trap door,
    hatch or lid over a pit or shaft), else None. The rooms are the labelled air straight over the top's centre and
    under the underside's (the first labelled voxel of FLAT_MOVER_REACH, as rooms.air_over reads a floor's)."""
    low, high = points.min(0), points.max(0)
    spans = high - low
    across = min(spans[0], spans[2])
    if across < FLAT_MOVER_MIN_LT or spans[1] > FLAT_MOVER_RATIO * across:
        return None
    centre = (low + high) / 2

    def room_at(y_lt: float, sign: float) -> tuple[int, np.ndarray | None]:
        for reach in FLAT_MOVER_REACH:
            point = np.array([centre[0], y_lt + sign * reach * rooms.grid.size, centre[2]])
            cell = rooms.grid.index(point[None])[0]
            label = int(rooms.labels[cell[0], cell[1], cell[2]])
            if label:
                return label, point
        return 0, None

    above, over = room_at(high[1], 1.0)
    below, _ = room_at(low[1], -1.0)
    if not above or not below or above == below:
        return None
    return over


def sink_length(points: np.ndarray, floors: list) -> float:
    """How far a breakable plug (LT points) sinks, native units: until its top is 8 units under the floor in front of
    and behind it (the lower of the two, half a thickness and 16 LT off its thin side), or by its height + 8 where no
    floor is found. A plug set in a wall over the floor (Anskram's cage window CritterBreakOut1, 128 LT up) that sank
    only its height ended inside the wall under it, its faces in that wall's planes: z-fighting once open
    (2026-11-06)."""
    low, high = points.min(0), points.max(0)
    height = (high[1] - low[1]) * SCALE + 8
    centre = (low + high) / 2
    thin = 0 if high[0] - low[0] < high[2] - low[2] else 2
    found = []
    for sign in (1.0, -1.0):
        probe = centre.copy()
        probe[thin] += sign * ((high[thin] - low[thin]) / 2 + 16.0)
        probe[1] = low[1] + 1.0
        floor = floor_below(floors, probe)
        if floor is not None:
            found.append(floor)
    if not found:
        return height
    return max(height, (high[1] - min(found)) * SCALE + 8)


def build_movers(source, plan: dict, package, rooms, stats: Counter, mover_events: dict, glass=None,
                 present: set | None = None, all_doors_click: bool = False) -> list[dict]:
    """Native linear movers: one per rising leaf pair, one per MM9 linear Door model, sinking plug or nudged lever.
    Each door group gets one click event that triggers all its movers (DOOR_EVENT_BASE + k); groups in
    `mover_events` (group -> (event, trigger type)) get the map's own events instead."""
    movers, door_id = [], 0
    groups = mover_groups(plan)
    # Click events: doorways (and every group with all_doors_click: Hooks.all_doors_click, the outdoor BLVs) first, in
    # group order, then the free MM9 doors (free_door), so the doorways keep their event numbers
    event_for_group = {}
    targets = message_targets(source)
    for free_pass in (False, True):
        for group, members in groups.items():
            rule = plan["movers"][members[0]]
            if group in mover_events or rule["motion"] == "break" or not rule.get("click", True):
                continue
            wanted = (free_door(source, members, targets) if free_pass
                      else bool(rule.get("doorway") or all_doors_click))
            if wanted and group not in event_for_group:
                event_for_group[group] = DOOR_EVENT_BASE + len(event_for_group) + 1
                if free_pass:
                    stats["free_door_clicks"] += 1
    floors_cache = []

    def static_floors() -> list:
        if not floors_cache:
            floors_cache.append([p for name in plan["static"] for p in source.polygons(name)
                                 if p.role == "static" and p.normal[1] >= 0.7])
        return floors_cache[0]

    for group, members in groups.items():
        rule = plan["movers"][members[0]]
        motion = rule["motion"]
        if motion == "break":
            continue            # a breakable brush: static faces and a scene destructible (destructibles.build_breakables)
        nodes = [members] if motion == "rise" or rule.get("one_node") else [[m] for m in members]
        for node_members in nodes:
            door_id += 1
            node = "MECH_" + (group if (motion == "rise" or rule.get("one_node")) else node_members[0])
            polygons = [p for m in node_members for p in source.polygons(m)]
            properties = source.by_name[node_members[0].lower()]["properties"]
            # MM9's RotatingBrush spins (spin_block) on the motion of the mover it is attached to (AttachTo: a saw on its
            # rail, gears on a lift; rule `motion_from` names another), or alone (motion `spin`: no travel)
            spinning = None
            if source.object_class(node_members[0]) == "RotatingBrush" and rule.get("spin", True):
                spinning = spin_block(properties, source.project.native, lt_vector_to_native)
                parent = rule.get("motion_from", properties.get("AttachTo") or "")
                if parent and parent.lower() in source.by_name and motion != "spin":
                    properties = source.by_name[parent.lower()]["properties"]
            shut_pose = rule.get("authored_open", False)
            if shut_pose and motion == "rotate":
                # MM9 authors the leaf in its open pose (StartOpen): built swung back by its angle, starting open
                polygons = authored_open_polygons(polygons, properties)
            elif shut_pose:
                # MM9 authors these leaves apart and its "open" slides them shut. They are built in the shut pose
                # (the pose that must collide from both rooms) and start open, apart, as in MM9.
                shift = np.asarray(properties["MoveDir"], float)
                shift = shift / np.linalg.norm(shift) * float(properties["MoveDist"])
                polygons = [Polygon(p.points + shift, p.keys, p.texture, (p.mapping[0] + shift,) + tuple(p.mapping[1:]),
                                    p.flags, p.model, p.role, notes=dict(p.notes)) for p in polygons]
            points = np.concatenate([p.points for p in polygons])
            centre = (points.min(0) + points.max(0)) / 2
            # A mover standing in a portal's plane (a floor trap over its pit) belongs to the room its top faces: a
            # party on it is found in that room, and from the pit's room the portal looks away. overrides.yml
            # `owner_lt` names the point by hand. Without it, a flat mover whose top and underside face different rooms
            # takes the room over its top (flat_mover_owner; Chasm of the Dead's pit hatch TrapExitDoor1 put the
            # camera of a party standing on it in the pit, which drew nothing of the corridor, 2026-11-08).
            flat_owner = None if "owner_lt" in rule else flat_mover_owner(points, rooms)
            owner = room_id(rooms.owner(rule["owner_lt"] if "owner_lt" in rule
                                        else centre if flat_owner is None else flat_owner))
            below = room_id(rooms.owner(centre))
            if flat_owner is not None and owner != below:
                stats["flat_movers_owned_by_room_over_top"] += 1
            spin, linear, extra_rooms = None, None, []
            if motion == "rise":
                height = (points[:, 1].max() - points[:, 1].min()) * SCALE
                open_direction = np.array([0.0, 0.0, 1.0])
                length, open_speed, close_speed = int(round(height + 8)), RISE_SPEED, RISE_SPEED
            elif motion == "sink":
                height = (points[:, 1].max() - points[:, 1].min()) * SCALE
                open_direction = np.array([0.0, 0.0, -1.0])
                length = int(round(sink_length(points, static_floors())))
                open_speed, close_speed = SINK_SPEED, SINK_SPEED
            elif motion == "spin":
                if spinning is None:
                    raise SystemExit(f"{node_members[0]}: motion spin needs a RotatingBrush with a revolution time")
                open_direction = np.array([0.0, 0.0, 1.0])
                length, open_speed, close_speed = 0, 1, 1
            elif motion in ("nudge", "slide"):
                move = lt_vector_to_native(np.asarray(rule["move_lt"], float)) * SCALE
                open_direction = move / np.linalg.norm(move)
                speed = rule.get("speed", NUDGE_SPEED if motion == "nudge" else RISE_SPEED)
                length, open_speed, close_speed = int(round(np.linalg.norm(move))), speed, speed
            elif motion == "rotate":
                spin = rotating_mover(node_members[0], rule, properties, polygons, source.project.native,
                                      lt_vector_to_native)
                open_direction = np.zeros(3)
                length, open_speed, close_speed = spin["move_length"], spin["open_speed"], spin["close_speed"]
                extra = swing_room(polygons, properties, owner, lambda point: room_id(rooms.owner(point)))
                extra = extra or (below if below != owner else None)
                if extra is not None and (present is None or extra in present):
                    extra_rooms = [extra]
            else:
                direction = np.asarray(rule.get("move_dir_lt", properties["MoveDir"]), float)
                open_direction = lt_vector_to_native(direction / np.linalg.norm(direction))
                length = int(round(float(rule.get("move_dist_lt", properties["MoveDist"])) * SCALE))
                open_speed = int(round(float(properties.get("Speed", 50)) * SCALE))
                close_speed = int(round(float(properties.get("ClosingSpeed", properties.get("Speed", 50))) * SCALE))
                if shut_pose:
                    open_direction = -open_direction
                # a door that starts open (MM9 StartOpen, or authored apart) stays open until it is shut once
                linear = linear_mover(properties) if not (shut_pose or start_open(rule, properties)) else None
            if locks_itself(source, members):
                # it locks itself as it opens, and MM9 never closes a locked door: no auto-close (locks_itself)
                if spin is not None:
                    spin["mover"].pop("auto_close_seconds", None)
                linear = None
                stats["self_locking_no_auto_close"] += 1
            event, trigger_type = 0, "click"
            if group in mover_events:
                event, trigger_type = mover_events[group]
            elif group in event_for_group:
                event = event_for_group[group]
            initial = "open" if (shut_pose or start_open(rule, properties)) else "closed"
            # The mover's invisible faces (MM9 Invisible.dtx collision shells round glass and doors) are a second
            # mechanism with the same motion, flagged invisible: a mechanism's faces share one surface entry.
            solid = [p for p in polygons if p.role != "invisible"]
            # A mover's walkable glass (a floor grate the party stands on: Chasm of the Dead's Gratetrap0) stays in the
            # main part: the party rides the mechanism it stands on, and a separate glass part would push it as an
            # obstacle (the grate reversed under the party, 2026-11-07); it draws alpha-tested
            kinds = [glass.kind(p) if glass and p.normal[1] < 0.7 else None for p in solid]
            parts = [(node, [p for p, k in zip(solid, kinds) if k is None], [], None),
                     (node + "_INV", [p for p in polygons if p.role == "invisible"], ["invisible"], None)]
            parts += [(f"{node}_GLASS{k}", [p for p, kk in zip(solid, kinds) if kk == k], [], k)
                      for k in sorted({k for k in kinds if k is not None})]
            parts = [part for part in parts if part[1]]
            for index, (part_node, part_polygons, flags, glass_k) in enumerate(parts):
                if index:
                    door_id += 1
                for polygon in part_polygons:
                    package.add_polygon(part_node, polygon, stats)
                mechanism = {"id": part_node[5:], "kind": "rotating" if spin else "linear", "source_nodes": [part_node],
                             "door": {"door_id": door_id, "initial_state": initial,
                                      "source_pose": "closed",
                                      "direction": [round(-v, 6) for v in open_direction.tolist()],
                                      "move_length": length, "open_speed": open_speed, "close_speed": close_speed}}
                if extra_rooms:
                    mechanism["extra_rooms"] = extra_rooms
                package.metadata["mechanisms"].append(mechanism)
                if event or flags:
                    surface_flags = flags + (["trigger_object"] if event and rule.get("shoot") else [])
                    surface = {"id": part_node[5:], "source_node": part_node, "flags": surface_flags}
                    if event:
                        surface["trigger"] = {"event_id": event, "type": trigger_type}
                    package.metadata["surfaces"].append(surface)
                package.room_nodes[owner].append(part_node)
                movers.append({"node": part_node, "dat_models": node_members, "group": group, "door_id": door_id,
                               "event": event, "motion": motion, "room": owner, "move_length": length,
                               "drives": list(rule.get("drives") or []),
                               "initial_state": initial, "doorway": bool(rule.get("doorway")),
                               "open_direction": open_direction.tolist(), "open_speed": open_speed,
                               "mm9_class": source.object_class(node_members[0]), "invisible": bool(flags),
                               "glass": glass_k, "mover": with_spin(spin["mover"] if spin else linear, spinning),
                               "extra_rooms": extra_rooms,
                               # MM9 TouchToOpen: the party walking into it opens it (lua.Script.finish's touch poll)
                               "touch": bool(properties.get("TouchToOpen")) and index == 0 and initial == "closed",
                               "box": [np.round(np.min(source.project.native(points), 0)).astype(int).tolist(),
                                       np.round(np.max(source.project.native(points), 0)).astype(int).tolist()],
                               # the sounds once per mover: its invisible and glass parts move with it, silently (no
                               # environment loop under the MM9 sounds); a spinner keeps the environment's
                               "sounds": None if spinning is not None
                               else mover_sounds(node_members[0], plan["movers"][node_members[0]], properties)
                               if index == 0 else {},
                               "sounds_overridden": index == 0 and "sounds" in plan["movers"][node_members[0]]})
    return movers
