#!/usr/bin/env python3
"""
Placed actors that do not stand on a floor they can stand on, in the installed MM9 maps: the scene's actors
(assets_dev/worlds/mm9/maps/<stem>.scene.yml, written by the map converters) and MAW's pack reserve
(assets_dev/engine/rulesets/maw/maps/<stem>_zz_maw.scene.yml, tools/maw/mm9_pack_reserve.py), against the compiled BLV.

Per actor, at its feet (x, y, z) with its body (radius, height):

- `void`: no floor under it at all;
- `under`: the first face over its feet is a floor's top (a terrain's or a slab's upper side): it stands under the
  ground or inside a solid, on whatever lies below (an outdoor region's sky plane at the bottom of its box);
- `sky floor`: the floor under it is a sky face (an outdoor region's box bottom);
- `steep`: the floor under it is steeper than the engine walks (IndoorGeometryUtils WalkableSlopeNormalZ);
- `floating`: its feet are more than FLOAT_TOLERANCE over the floor, and it neither flies (monster_data Fly) nor
  swims (in one of the scene's water volumes);
- `buried`: its feet are under the floor by more than BURY_TOLERANCE;
- `low ceiling`: less headroom over the floor than half its height;
- `in wall`: its centre is nearer a wall than half its radius, at its body's height.

    python3 level_generation/projects/mm9r_common/actor_floor_audit.py                 # every MM9 BLV map
    python3 level_generation/projects/mm9r_common/actor_floor_audit.py guberland lindisfarne
    python3 level_generation/projects/mm9r_common/actor_floor_audit.py --maps-dir <scratch>/runtime --no-reserve x
    python3 level_generation/projects/mm9r_common/actor_floor_audit.py --json /tmp/audit.json

Exit status 1 when an actor has one of the ERRORS (void, under, sky floor, steep, floating, buried). Some are only
warnings: a hidden actor floating (its script shows it where it belongs: Beethoven's coffin mummies lie in their
coffins), a townsperson under or in a surface by at most SEAT_DEPTH (seated on a bench, behind a counter's collision
box: rude_props.py seats them), a flyer over a steep face.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

COMMON = Path(__file__).resolve().parent
ROOT = COMMON.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
from util.map_export import parse_blv_file  # noqa: E402
from mm9_density_targets import wall_segments  # noqa: E402

MAPS = ROOT / "assets_dev/worlds/mm9/maps"
RESERVES = ROOT / "assets_dev/engine/rulesets/maw/maps"
MONSTER_DATA = ROOT / "assets_dev/worlds/mm9/data_tables/monster_data.txt"
WALKABLE_NORMAL_Z = 0.68664550781     # game/indoor/IndoorGeometryUtils.cpp WalkableSlopeNormalZ
STEP = 24.0                           # a floor this far over the feet still carries them
FLOAT_TOLERANCE = 32.0
BURY_TOLERANCE = 8.0
UNTOUCHABLE = 0x20000000
GRID = 512.0
SEAT_DEPTH = 96.0
ERRORS = ("void", "under", "sky floor", "steep", "floating", "buried")


def flyers() -> set[int]:
    out = set()
    for line in MONSTER_DATA.read_text(errors="replace").splitlines():
        fields = line.split("\t")
        if len(fields) > 9 and fields[0].isdigit() and fields[9].strip().upper().startswith("Y"):
            out.add(int(fields[0]))
    return out


def _inside(x: float, y: float, ring: np.ndarray) -> bool:
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


class Geometry:
    """The solid, non-vertical faces of a compiled BLV by plan cell, with the wall segments."""

    def __init__(self, blv: dict):
        vertices = np.array([(v["x"], v["y"], v["z"]) for v in blv["vertices"]], float)
        self.faces, self.cells = [], {}
        for face in blv["faces"]:
            if face["is_portal"] or int(face["attributes"]) & UNTOUCHABLE:
                continue
            points = vertices[face["vertex_indices"]]
            normal = np.zeros(3)
            for k in range(1, len(points) - 1):
                normal += np.cross(points[k] - points[0], points[k + 1] - points[0])
            length = np.linalg.norm(normal)
            if length < 1e-6 or abs(normal[2]) < 0.02 * length:
                continue
            record = {"index": face["index"], "ring": points[:, :2], "normal": normal / length, "point": points[0],
                      "texture": str(face["texture_name"]).lower(), "sector": face["room_number"],
                      "low": points[:, :2].min(0), "high": points[:, :2].max(0)}
            self.faces.append(record)
            for cx in range(int(record["low"][0] // GRID), int(record["high"][0] // GRID) + 1):
                for cy in range(int(record["low"][1] // GRID), int(record["high"][1] // GRID) + 1):
                    self.cells.setdefault((cx, cy), []).append(record)
        self.walls = wall_segments(blv)

    def column(self, x: float, y: float) -> list[tuple[float, dict]]:
        """Every face crossing the vertical line at (x, y): (its height there, its record), lowest first."""
        out = []
        for record in self.cells.get((int(x // GRID), int(y // GRID)), []):
            if not (record["low"][0] <= x <= record["high"][0] and record["low"][1] <= y <= record["high"][1]):
                continue
            if not _inside(x, y, record["ring"]):
                continue
            n, p = record["normal"], record["point"]
            out.append((p[2] - (n[0] * (x - p[0]) + n[1] * (y - p[1])) / n[2], record))
        return sorted(out, key=lambda entry: entry[0])

    def wall_distance(self, x: float, y: float, z_low: float, z_high: float, reach: float) -> float:
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


def in_water(scene: dict, x: float, y: float, z: float, height: float) -> bool:
    for volume in scene.get("water_volumes") or []:
        for piece in volume.get("pieces", []):
            ring = np.array(piece["polygon"], float)
            if float(piece["bottom"]) - 8 <= z + height and z <= float(piece["top"]) and _inside(x, y, ring):
                return True
    return False


def problems(geometry: Geometry, scene: dict, actor: dict, flying: set[int]) -> list[tuple[str, bool]]:
    """What is wrong with where the actor stands (module docstring), each with whether it is an error; empty when
    nothing is."""
    p = actor["position"]
    x, y, z = float(p["x"]), float(p["y"]), float(p["z"])
    radius, height = float(actor.get("radius") or 40), float(actor.get("height") or 120)
    hidden = bool(int(actor.get("attributes", 0)) & 0x10000)
    friendly = int(actor.get("hostility_type", 0)) == 0
    flies = int(actor.get("monster_id", 0)) in flying
    column = geometry.column(x, y)
    floors = [(h, r) for h, r in column if r["normal"][2] > 0 and h <= z + STEP]
    if not floors:
        return [("void", True)]
    floor, record = floors[-1]
    # the foot of a slope: a floor under the steep face's edge carries the feet
    walkable = [(h, r) for h, r in floors if r["normal"][2] >= WALKABLE_NORMAL_Z and h >= floor - BURY_TOLERANCE]
    if record["normal"][2] < WALKABLE_NORMAL_Z and walkable:
        floor, record = walkable[-1]
    out = []
    above = [(h, r) for h, r in column if h > max(z, floor) + STEP]
    if above and above[0][1]["normal"][2] > 0:
        depth = above[0][0] - z
        out.append((f"under (a floor's top {depth:.0f} over its feet, face {above[0][1]['index']})",
                    not friendly or depth > SEAT_DEPTH))
    if record["texture"].startswith("sky"):
        out.append((f"sky floor (face {record['index']} at {floor:.0f})", True))
    if record["normal"][2] < WALKABLE_NORMAL_Z:
        out.append((f"steep (face {record['index']}, {math.degrees(math.acos(record['normal'][2])):.0f} degrees)",
                    not flies))
    swims = in_water(scene, x, y, z, height)
    if z - floor > FLOAT_TOLERANCE and not flies and not swims:
        out.append((f"floating ({z - floor:.0f} over the floor at {floor:.0f})", not hidden))
    if floor - z > BURY_TOLERANCE:
        out.append((f"buried ({floor - z:.0f} under the floor)", not friendly or floor - z > SEAT_DEPTH))
    ceilings = [h for h, r in above if r["normal"][2] < 0]
    if ceilings and ceilings[0] - floor < height * 0.5:
        out.append((f"low ceiling ({ceilings[0] - floor:.0f} over the floor, height {height:.0f})", False))
    if geometry.wall_distance(x, y, floor + STEP, floor + height, radius) < radius * 0.5:
        out.append(("in wall", False))
    return out


def audit(stem: str, maps: Path, reserves: Path | None, flying: set[int]) -> list[dict]:
    scene = yaml.load((maps / f"{stem}.scene.yml").read_text(), Loader=yaml.CSafeLoader)
    geometry = Geometry(parse_blv_file(maps / f"{stem}.blv")["payload"])
    actors = [("scene", i, a) for i, a in enumerate((scene.get("initial_state") or {}).get("actors") or [])]
    reserve_path = reserves / f"{stem}_zz_maw.scene.yml" if reserves is not None else None
    if reserve_path is not None and reserve_path.is_file():
        reserve = yaml.load(reserve_path.read_text(), Loader=yaml.CSafeLoader)["initial_state"]["pack_reserve"]
        base = len(actors)
        actors += [("maw reserve", base + k, entry["actor"]) for k, entry in enumerate(reserve.get("actors") or [])]
    out = []
    for source, index, actor in actors:
        found = problems(geometry, scene, actor, flying)
        if found:
            out.append({"map": stem, "source": source, "index": index, "name": actor.get("name"),
                        "monster_id": actor.get("monster_id"), "position": actor["position"],
                        "sector": actor.get("sector_id"), "hidden": bool(int(actor.get("attributes", 0)) & 0x10000),
                        "friendly": int(actor.get("hostility_type", 0)) == 0,
                        "error": any(error for _, error in found), "problems": [text for text, _ in found]})
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stems", nargs="*", help="map stems (every BLV with a scene in --maps-dir when none)")
    parser.add_argument("--maps-dir", type=Path, default=MAPS)
    parser.add_argument("--no-reserve", action="store_true", help="the scene's actors only")
    parser.add_argument("--json", type=Path, help="write the findings here")
    arguments = parser.parse_args(argv)
    stems = arguments.stems or sorted(p.name[:-len(".scene.yml")] for p in arguments.maps_dir.glob("*.scene.yml")
                                      if (arguments.maps_dir / (p.name[:-len(".scene.yml")] + ".blv")).is_file())
    flying = flyers()
    findings, errors = [], 0
    for stem in stems:
        found = audit(stem, arguments.maps_dir, None if arguments.no_reserve else RESERVES, flying)
        findings += found
        for entry in found:
            serious = entry["error"]
            errors += serious
            p = entry["position"]
            print(f"{'ERROR' if serious else 'warn '} {stem:20} {entry['source']:11} [{entry['index']:3}] "
                  f"{entry['monster_id']} {entry['name']:<24} ({p['x']}, {p['y']}, {p['z']}) sector {entry['sector']}"
                  f"{' hidden' if entry['hidden'] else ''}{' friendly' if entry['friendly'] else ''}: "
                  f"{'; '.join(entry['problems'])}")
    print(f"{len(stems)} maps, {len(findings)} actors with findings, {errors} errors")
    if arguments.json:
        arguments.json.write_text(json.dumps(findings, indent=1) + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
