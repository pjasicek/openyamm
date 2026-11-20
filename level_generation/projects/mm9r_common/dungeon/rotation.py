"""
Rotating movers and ladders from MM9's data (devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md): the `mover` block of a
`RotatingDoor`/`Switch`, the rooms its swing enters, its direction checks, and the scene's `ladders`. LithTech's
rotation is the right-handed formula in its own (x, y up, z) coordinates; the native frame swaps y and z, a reflection,
so the axis maps like any vector and the angle changes sign. The Anskram traps and hatches prove it: MM9's angles tip the
trigger half down and swing the hatch up with exactly this formula. The old outdoor import keeps its own mapping.
"""

from __future__ import annotations

import math
from collections import Counter

import numpy as np

SPIN_STEP_DEGREES = 15.0        # poses sampled along a swing for the rooms it enters
DEFAULT_REACH = 48.0            # native units in front of a ladder's strip that a body may stand and grab it


def lt_rotation(properties: dict) -> tuple[np.ndarray, float]:
    """The LithTech unit axis and signed degrees of a RotatingDoor (one angle component is non-zero)."""
    angles = np.asarray(properties["RotationAngles"], float)
    index = np.flatnonzero(angles)
    if len(index) != 1:
        raise SystemExit(f"rotation about one axis expected: {angles}")
    axis = np.zeros(3)
    axis[index[0]] = 1.0
    return axis, float(angles[index[0]])


def rotate_lt(points: np.ndarray, pivot: np.ndarray, axis: np.ndarray, degrees: float) -> np.ndarray:
    """LithTech points turned about the pivot, right-handed in LithTech coordinates."""
    radians = math.radians(degrees)
    relative = points - pivot
    return (pivot + relative * math.cos(radians) + np.cross(axis, relative) * math.sin(radians)
            + np.outer(relative @ axis, axis) * (1.0 - math.cos(radians)))


def authored_open_points(points: np.ndarray, properties: dict) -> np.ndarray:
    """LithTech points of a leaf MM9 authors in its open pose (`authored_open` on a `rotate` rule: StartOpen,
    Drangheim Prison's Celldoor18 standing along its cell's wall), swung back by its angle into the shut pose."""
    axis, degrees = lt_rotation(properties)
    return rotate_lt(np.asarray(points, float), np.asarray(properties["RotationPoint"], float), axis, -degrees)


def authored_open_polygons(polygons: list, properties: dict) -> list:
    """The leaf's polygons in its shut pose (authored_open_points), their texture mapping turned with them."""
    from .geometry import Polygon
    axis, degrees = lt_rotation(properties)
    out = []
    for p in polygons:
        origin, axis_u, axis_v = (np.asarray(v, float) for v in p.mapping[:3])
        turned = [authored_open_points(origin[None], properties)[0],
                  rotate_lt(axis_u[None], np.zeros(3), axis, -degrees)[0],
                  rotate_lt(axis_v[None], np.zeros(3), axis, -degrees)[0]]
        out.append(Polygon(authored_open_points(p.points, properties), p.keys, p.texture,
                           tuple(turned) + tuple(p.mapping[3:]), p.flags, p.model, p.role, notes=dict(p.notes)))
    return out


def rotating_mover(name: str, rule: dict, properties: dict, polygons, pivot_native, vector_native) -> dict:
    """The door numbers and scene `mover` block of one rotating model. `pivot_native` maps a LithTech point to native
    units, `vector_native` a LithTech vector. Travel is in tenths of a degree (the door record's move_length). Rule
    keys: bodies (default: reverse with MM9 ReopenOnContact, else hold), carry, falls (the name of an object that must
    go down as the mover opens: a trap's trigger) with falls_point (its LithTech position), rises (the mover's centre
    must rise: a hatch)."""
    axis, degrees = lt_rotation(properties)
    pivot = np.asarray(properties["RotationPoint"], float)
    if "falls_point" in rule:
        point = np.asarray(rule["falls_point"], float)
        if rotate_lt(point[None], pivot, axis, degrees)[0][1] >= point[1]:
            raise SystemExit(f"{name}: its open swing lifts {rule.get('falls')}; the trap would not tip the party")
    if rule.get("rises"):
        centre = np.concatenate([p.points for p in polygons]).mean(0)
        if rotate_lt(centre[None], pivot, axis, degrees)[0][1] <= centre[1]:
            raise SystemExit(f"{name}: its open swing does not rise")
    speed = float(properties.get("Speed", 50.0))
    closing = float(properties.get("ClosingSpeed", speed)) or speed
    wait = float(properties.get("CloseWaitTime", 0.0) or 0.0)
    sticky = bool(properties.get("Sticky", 0))
    bodies = rule.get("bodies", "reverse" if properties.get("ReopenOnContact") else "hold")
    block = {"rotation": {"pivot": [round(float(v), 3) for v in pivot_native(pivot)],
                          "axis": [float(v) for v in vector_native(axis)],
                          "open_degrees": -degrees,
                          "open_away": bool(properties.get("OpenAway", 0))},
             "easing": "sine" if properties.get("Waveform") else "linear",
             "bodies": bodies,
             "carry": bool(rule.get("carry", False))}
    if wait > 0.0 and not sticky:
        block["auto_close_seconds"] = wait
    return {"move_length": int(round(abs(degrees) * 10.0)), "open_speed": int(round(speed * 10.0)),
            "close_speed": int(round(closing * 10.0)), "mover": block}


def swing_room(polygons, properties: dict, owner: str, room_at) -> str | None:
    """The other room a swing enters, the one most of its sampled poses reach (both ways for an OpenAway door).
    `room_at` maps a LithTech point to a room id."""
    axis, degrees = lt_rotation(properties)
    pivot = np.asarray(properties["RotationPoint"], float)
    centres = np.array([p.points.mean(0) for p in polygons] + [p for poly in polygons for p in poly.points])
    signs = (1.0, -1.0) if properties.get("OpenAway") else (1.0,)
    steps = max(1, int(abs(degrees) / SPIN_STEP_DEGREES))
    found = Counter()
    for sign in signs:
        for step in range(1, steps + 1):
            for point in rotate_lt(centres, pivot, axis, sign * degrees * step / steps):
                room = room_at(point)
                if room and room != owner:
                    found[room] += 1
    return found.most_common(1)[0][0] if found else None


def grabs_at_top(record: dict) -> bool:
    """Whether a scene ladder can be taken at its top (`grab_at_top`, MM9's ladders: a party at the top climbs down).
    The engine reads walking from the top exit to the top as climbing down only when that is not mostly toward the strip;
    with the exit on the climber's side (a hole climbed out of backwards) it would climb straight back out, so no."""
    facing = math.radians(record["facing_degrees"])
    dx = record["top_exit"][0] - record["top"][0]
    dy = record["top_exit"][1] - record["top"][1]
    distance = math.hypot(dx, dy)
    return distance >= 1.0 and dx * math.cos(facing) + dy * math.sin(facing) > -0.5 * distance


def ladder_records(rules: dict, models: dict, native, scale: float) -> list[dict]:
    """The scene's `ladders` from overrides.yml `ladders`: {<Ladder model>: {facing_lt: [x, z] toward the ladder, surface_lt:
    the coordinate along facing where a climber stops (a LadderBlocker's face), top_exit_lt: [x, y, z], optional
    grab_at_top: true/false (default `grabs_at_top`)}}."""
    records = []
    for name, rule in sorted((rules or {}).items()):
        points = np.array(models[name].points, float)
        low, high = points.min(0), points.max(0)
        facing = np.array([rule["facing_lt"][0], 0.0, rule["facing_lt"][1]], float)
        along = 0 if abs(facing[0]) > 0.5 else 2
        across = 2 - along
        bottom = (low + high) / 2
        bottom[along] = float(rule["surface_lt"])
        bottom[1] = low[1]
        top = bottom.copy()
        top[1] = high[1]
        facing_native = (facing[0], facing[2])
        records.append({"id": name, "bottom": [round(float(v), 2) for v in native(bottom)],
                        "top": [round(float(v), 2) for v in native(top)],
                        "facing_degrees": round(math.degrees(math.atan2(facing_native[1], facing_native[0])) % 360.0, 2),
                        "width": round(float(high[across] - low[across]) * scale, 2), "reach": DEFAULT_REACH,
                        "top_exit": [round(float(v), 2) for v in native(np.asarray(rule["top_exit_lt"], float))]})
        if rule.get("grab_at_top", grabs_at_top(records[-1])):
            records[-1]["grab_at_top"] = True
    return records


def rectangle_portals(rules: list, lt_points=None) -> list[dict]:
    """overrides.yml `rect_portals`: explicit portal rectangles (a trap's opening, a hatch's hole): {name, min_lt,
    max_lt}, thin along one axis of the box."""
    portals = []
    for rule in rules or []:
        low, high = np.asarray(rule["min_lt"], float), np.asarray(rule["max_lt"], float)
        thin = int(np.argmin(high - low))
        normal = np.zeros(3)
        normal[thin] = 1.0
        axes = [axis for axis in range(3) if axis != thin]
        axis_a, axis_b = np.zeros(3), np.zeros(3)
        axis_a[axes[0]], axis_b[axes[1]] = 1.0, 1.0
        portals.append({"name": rule["name"], "kind": "rectangle", "centre": (low + high) / 2, "normal": normal,
                        "axis_a": axis_a, "half_a": float(high[axes[0]] - low[axes[0]]) / 2,
                        "axis_b": axis_b, "half_b": float(high[axes[1]] - low[axes[1]]) / 2})
    return portals
