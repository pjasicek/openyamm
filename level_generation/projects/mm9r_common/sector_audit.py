#!/usr/bin/env python3
"""
Sector audit of built BLVs (2026-11-07: Ravensford's tavern shelf and the loaves on it vanished at a small camera turn).
The engine draws a face when its sector is drawn, and a decoration model when the sector of its position is drawn: the
sector of the floor face under the position (findIndoorSectorForPoint). A floor face given the room behind a wall
(the street behind a tavern's shelf board) takes the props on it into that room too, and both vanish whenever that
room's portals leave the view. Per map:

- `floors`: up-facing faces whose sector is not that of the ceiling straight over them (the room their air belongs
  to), unless that face names the floor's room as its room behind (a portal, or a face drawn for two rooms). Faces
  under open sky (no ceiling over them) are not judged.
- `props`: decorations whose sector (the engine's rule, EngineSectors: findIndoorSectorForPoint at PROBE_LIFT over
  the base, with its sector bounding-box test) is not the sector of the ceiling over them nor, in a converter's BLV,
  the room it listed them in (the BLV sector's decoration list: the room of the voxel air nearest to the decoration);
  and the corners of the model's box (`straddling`: a model reaching into a sector other than its own). The list is
  41-unit voxels, so two kinds are kept apart, not counted (2026-11-07, each checked from 16 poses around it:
  output/mm9_rework/sector_props_20261107/): `props_at_portal`, a portal between the two rooms within PORTAL_REACH
  (the base a voxel's width off the portal plane: Sturmford City's anvil, hammer and lantern over a door, Thronheim
  City's lamppost, Lich Lab's gate fire, Drangheim Prison's axe over a floor portal), and `props_under_listed_room`,
  no floor of the listed room under the point (Verhoffin's lantern down in a channel whose floor is the other room's).
  Before the bounding-box test was modelled, Drangheim Prison's tapestry (its base 80 under its floor) counted in a
  room 1 600 units under it, where the engine never looks; and the test showed Thjorgard City's sunk bookcases (107
  under their floors) in the roof room, whose roof was the only floor the engine found for them: never drawn in their
  houses. The engine now takes a complete list's room when the sector found has no floor under the point.

    python3 level_generation/projects/mm9r_common/sector_audit.py [blv ...]   # default: every MM9 map of the review
                                                                             # roots
writes output/mm9_rework/prop_culling_20261107/sector_audit.json and prints one line per map.
"""

from __future__ import annotations

import base64
import json
import struct
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import review_root                                              # noqa: E402
from dungeon import prop_pose                                   # noqa: E402
from util.map_export import parse_blv_file                      # noqa: E402

OUT = ROOT / "output/mm9_rework/prop_culling_20261107"
CELL = 256.0
UP = 0.7
PROBE_LIFT = 32.0       # MapAssetLoader's DecorationSectorProbeLift
PORTAL_REACH = 64.0     # a prop this close to a portal into its listed room is drawn whenever that side is in view


class Faces:
    def __init__(self, blv: dict):
        v = np.array([[p["x"], p["y"], p["z"]] for p in blv["vertices"]], float)
        self.rings, self.normals, self.rooms, self.behind, self.portal = [], [], [], [], []
        for f in blv["faces"]:
            ring = v[f["vertex_indices"][:f["vertex_per_face_count"]]]
            if len(ring) < 3:
                ring = np.zeros((3, 3))
            n = np.zeros(3)
            for a, b in zip(ring, np.roll(ring, -1, axis=0)):          # Newell
                n += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])]
            length = np.linalg.norm(n)
            self.rings.append(ring)
            self.normals.append(n / length if length > 1e-9 else n)
            self.rooms.append(int(f["room_number"]))
            self.behind.append(int(f["room_behind_number"]))
            self.portal.append(bool(f["is_portal"]))
        self.normals = np.array(self.normals)
        self.grid = defaultdict(list)
        for index, ring in enumerate(self.rings):
            if abs(self.normals[index][2]) < UP:
                continue
            lo, hi = np.floor(ring.min(0)[:2] / CELL).astype(int), np.floor(ring.max(0)[:2] / CELL).astype(int)
            if (hi - lo + 1).prod() > 20000:
                continue
            for x in range(lo[0], hi[0] + 1):
                for y in range(lo[1], hi[1] + 1):
                    self.grid[(x, y)].append(index)

    def height(self, index: int, x: float, y: float) -> float | None:
        """The face's plane height at (x, y) when the point is inside its outline in plan (even-odd: a merged face
        need not be convex), else None."""
        ring, n = self.rings[index], self.normals[index]
        inside = False
        for a, b in zip(ring, np.roll(ring, -1, axis=0)):
            if (a[1] > y) != (b[1] > y) and x < a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                inside = not inside
        if not inside or abs(n[2]) < 1e-6:
            return None
        return float(ring[0][2] - (n[0] * (x - ring[0][0]) + n[1] * (y - ring[0][1])) / n[2])

    def under_over(self, x: float, y: float, z: float):
        """(floor index under the point, the engine's floor rule; ceiling index straight over it) or None each."""
        best_below, best_above, ceiling = (None, np.inf), (None, np.inf), (None, np.inf)
        for index in self.grid.get((int(np.floor(x / CELL)), int(np.floor(y / CELL))), ()):
            h = self.height(index, x, y)
            if h is None:
                continue
            if self.normals[index][2] >= UP and not self.portal[index]:
                if z >= h and z - h < best_below[1]:
                    best_below = (index, z - h)
                elif z < h and h - z < best_above[1]:
                    best_above = (index, h - z)
            elif self.normals[index][2] <= -UP or self.portal[index]:
                if h > z and h - z < ceiling[1]:
                    ceiling = (index, h - z)
        floor = best_below[0] if best_below[0] is not None else best_above[0]
        return floor, ceiling[0]

    def agrees(self, room: int, ceiling: int) -> bool:
        """A portal names both its rooms; a face drawn for two rooms (its room behind, rooms.shared_rooms) both."""
        return room in (self.rooms[ceiling], self.behind[ceiling])


def sector_records(blv: dict) -> list[dict]:
    """Per sector, as IndoorMapData reads it: flags, bounding box (min, max), floor and portal face lists and the
    decoration list (the sector data order)."""
    v8 = blv["version"] >= 8
    offsets = dict(floor=0x08, wall=0x10, ceil=0x18, fluid=0x20, portal=0x28, face=0x30, cyl=0x38, cog=0x40,
                   deco=0x48, marker=0x50) if v8 else dict(floor=0x04, wall=0x0c, ceil=0x14, fluid=0x1c,
                   portal=0x24, face=0x2c, cyl=0x34, cog=0x3c, deco=0x44, marker=0x4c)
    box = 0x6c if v8 else 0x68
    data, cursor, records = blv["sector_data"], 0, []
    for sector in blv["sectors"]:
        raw = base64.b64decode(sector["raw_record_base64"])
        count = {k: struct.unpack_from("<H", raw, o)[0] for k, o in offsets.items()}
        count["portal"] = max(struct.unpack_from("<h", raw, offsets["portal"])[0], 0)
        lists = {}
        for key in ("floor", "wall", "ceil", "fluid", "portal", "face", "cyl", "cog", "deco", "marker"):
            lists[key] = [int(i) for i in data[cursor:cursor + count[key]]]
            cursor += count[key]
        bounds = struct.unpack_from("<6h", raw, box)
        records.append({"flags": struct.unpack_from("<i", raw, 0)[0], "floors": lists["floor"],
                        "portals": lists["portal"], "decorations": lists["deco"],
                        "min": np.array(bounds[0::2], float), "max": np.array(bounds[1::2], float)})
    return records


def sector_decorations(blv: dict) -> dict:
    """entity index -> the sector whose decoration list holds it."""
    listed = {}
    for index, record in enumerate(sector_records(blv)):
        for entity in record["decorations"]:
            listed.setdefault(entity, index)
    return listed


UNTOUCHABLE = 0x20000000
WALKABLE_NZ = 0.68664550781     # IndoorGeometryUtils WalkableSlopeNormalZ
STEEP_FLOOR_NZ = 0.1            # IndoorMinimumSteepFloorNormalZ
FLOOR_SLACK = 8.0


class EngineSectors:
    """findIndoorSectorForPoint (game/indoor/IndoorGeometryUtils.cpp) on a BLV: the sectors whose bounding box holds
    the point (5 units across, 64 up and down), the floors of their floor lists (and floor portals of a sector with
    flag 0x8) under or over it; one candidate, or one such sector, decides; else the nearest floor below, else the
    nearest above. None when no floor holds the point (the engine then keeps the sector's decoration list)."""

    def __init__(self, blv: dict, faces: Faces):
        self.faces, self.records = faces, sector_records(blv)
        self.floor_like = []
        for index, face in enumerate(blv["faces"]):
            nz, facet = faces.normals[index][2], int(face["facet_type"])
            if facet == 1:
                kind = "wall"
            elif facet == 3:
                kind = "floor"
            elif facet == 4:
                kind = "floor" if nz > WALKABLE_NZ else "wall"
            elif facet in (5, 6):
                kind = "other"
            else:
                kind = "floor" if nz > WALKABLE_NZ else "other"
            self.floor_like.append(not int(face["attributes"]) & UNTOUCHABLE
                                   and (kind == "floor" or (facet == 4 and nz >= STEEP_FLOOR_NZ)))

    def sector(self, x: float, y: float, z: float) -> int | None:
        candidates, single, single_ok = [], None, True
        point = np.array([x, y, z])
        for index in range(1 if len(self.records) > 1 else 0, len(self.records)):
            record = self.records[index]
            if ((point + [5, 5, 64]) < record["min"]).any() or ((point - [5, 5, 64]) > record["max"]).any():
                continue
            if not record["floors"] and not record["portals"]:
                continue
            if single is None:
                single = index
            elif single != index:
                single_ok = False
            ids = record["floors"] + (record["portals"] if record["flags"] & 0x8 else [])
            for face in ids:
                if not self.floor_like[face]:
                    continue
                ring = self.faces.rings[face]
                if (x < ring[:, 0].min() - FLOOR_SLACK or x > ring[:, 0].max() + FLOOR_SLACK
                        or y < ring[:, 1].min() - FLOOR_SLACK or y > ring[:, 1].max() + FLOOR_SLACK):
                    continue
                h = self.faces.height(face, x, y)
                if h is not None:
                    candidates.append((index, h))
        if len(candidates) == 1:
            return candidates[0][0]
        if single is not None and single_ok and candidates:
            return single
        best_below, best_above = (np.inf, None), (np.inf, None)
        for index, h in candidates:                   # the first of equals, as the engine's strict comparison
            if z >= h and z - h < best_below[0]:
                best_below = (z - h, index)
            elif z < h and h - z < best_above[0]:
                best_above = (h - z, index)
        return best_below[1] if best_below[1] is not None else best_above[1]

    def portal_near(self, a: int, b: int, point: np.ndarray, reach: float) -> bool:
        """Whether a portal between sectors a and b comes within reach of the point."""
        for index, ring in enumerate(self.faces.rings):
            if self.faces.portal[index] and {self.faces.rooms[index], self.faces.behind[index]} == {a, b}:
                gap = np.maximum(np.maximum(ring.min(0) - point, point - ring.max(0)), 0)
                if np.linalg.norm(gap) <= reach:
                    return True
        return False

    def floor_under(self, sector: int, x: float, y: float, z: float) -> bool:
        """Whether a floor of the sector's floor list lies at or under the point."""
        for face in self.records[sector]["floors"]:
            h = self.faces.height(face, x, y) if self.floor_like[face] else None
            if h is not None and h <= z:
                return True
        return False


def decoration_names(maps: Path) -> dict:
    world = yaml.safe_load((maps.parent / "world.yml").read_text())
    tables = [maps.parents[2] / "engine/data_tables/decoration_data.txt"] + [
        maps.parent / c["path"] for c in world.get("tableContributions", []) if c.get("table") == "decorations"]
    names = {}
    for table in tables:
        for cells in (line.split("\t") for line in table.read_text(encoding="latin-1").splitlines()):
            if len(cells) > 1 and cells[0].strip().isdigit():
                names[int(cells[0]) - 1] = cells[1].strip().lower()
    return names


def bindings(maps: Path) -> dict:
    found = {}
    for path in (maps.parent / "models/indoor_decorations.yml", maps.parents[2] / "engine/models/indoor_decorations.yml",
                 maps.parent / "models/decorations.yml"):
        if path.is_file():
            for b in yaml.safe_load(path.read_text()).get("decorations", []):
                found.setdefault(b["name"].lower(), b)
    return found


def audit(path: Path) -> dict:
    blv = parse_blv_file(path)["payload"]
    faces = Faces(blv)
    floors = []
    for index, ring in enumerate(faces.rings):
        if faces.portal[index] or faces.normals[index][2] < UP:
            continue
        centre = ring.mean(0)
        _, ceiling = faces.under_over(centre[0], centre[1], centre[2] + 2)
        if ceiling is not None and not faces.agrees(faces.rooms[index], ceiling):
            floors.append({"face": index, "room": faces.rooms[index], "ceiling_room": faces.rooms[ceiling],
                           "centre": centre.round().astype(int).tolist()})
    names, binds = decoration_names(path.parent), bindings(path.parent)
    listed = sector_decorations(blv)
    # a converter's BLV lists every decoration once; an original map's lists can be incomplete or all in one sector
    complete = len(listed) == len(blv["entities"]) and len(set(listed.values())) > 1
    engine = EngineSectors(blv, faces)
    props, straddling, at_portal, under_listed = [], [], [], []
    for entity in blv["entities"]:
        p = entity["position"]
        x, y, z = float(p["x"]), float(p["y"]), float(p["z"])
        _, ceiling = faces.under_over(x, y, z + PROBE_LIFT)
        # the engine's own rule, else its list; with complete lists, the list when the sector found has no floor under
        # the point (MapAssetLoader buildIndoorDecorationBillboardSet)
        room = engine.sector(x, y, z + PROBE_LIFT)
        own = listed.get(entity["index"])
        if room is None or (complete and own is not None and own != room
                            and not engine.floor_under(room, x, y, z + PROBE_LIFT)):
            room = own
        if room is None:
            continue
        row = {"name": entity["name"], "decoration": names.get(entity["decoration_list_id"], ""), "sector": room,
               "position": [int(x), int(y), int(z)]}
        expected = listed.get(entity["index"]) if complete else None
        under_own_ceiling = ceiling is None or faces.agrees(room, ceiling)
        probe = np.array([x, y, z + PROBE_LIFT])
        if expected is not None and expected != room and not under_own_ceiling:
            row = dict(row, listed_room=expected, ceiling_room=faces.rooms[ceiling])
            if engine.portal_near(room, expected, probe, PORTAL_REACH):
                at_portal.append(row)
            elif not engine.floor_under(expected, x, y, z + PROBE_LIFT):
                under_listed.append(row)
            else:
                props.append(row)
        elif expected is None and not under_own_ceiling:
            props.append(dict(row, ceiling_room=faces.rooms[ceiling]))
        binding = binds.get(row["decoration"])
        if binding is None or not binding.get("model"):
            continue
        try:
            points, _ = prop_pose.decoration_mesh(binding, float(entity["facing"]))
        except Exception:
            continue
        lo, hi = points.min(0) + [x, y, z], points.max(0) + [x, y, z]
        mid = (lo[2] + hi[2]) / 2
        others = set()
        for cx in (lo[0] + 1, hi[0] - 1):
            for cy in (lo[1] + 1, hi[1] - 1):
                f, c = faces.under_over(cx, cy, mid)
                if f is not None and faces.rooms[f] != room:
                    others.add(faces.rooms[f])
        if others:
            straddling.append(dict(row, other_sectors=sorted(others)))
    return {"faces": len(faces.rings), "entities": len(blv["entities"]), "floors": floors, "props": props,
            "props_at_portal": at_portal, "props_under_listed_room": under_listed, "straddling": straddling}


def mm9_maps() -> list[Path]:
    regions = review_root.REVIEW / "isleofashes_blv_root/worlds/mm9/maps"
    found = []
    for directory in sorted((ROOT / "level_generation/projects").glob("mm9r_*")):
        overrides = directory / "overrides.yml"
        if not overrides.is_file():
            continue
        stem = yaml.safe_load(overrides.read_text())["map"]["stem"]
        path = (regions if directory.name.endswith("_blv") else review_root.ASSETS / "worlds/mm9/maps") / f"{stem}.blv"
        if path.is_file():
            found.append(path)
    return found


def main(argv: list[str]) -> None:
    paths = [Path(a).resolve() for a in argv] or mm9_maps()
    results = {}
    for path in paths:
        result = audit(path)
        results[str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)] = result
        print(f"{path.stem}: {len(result['floors'])} floors under another sector's ceiling, {len(result['props'])} "
              f"props in another sector than their room's ({len(result['props_at_portal'])} more at a portal "
              f"into it, {len(result['props_under_listed_room'])} under its floors), {len(result['straddling'])} "
              f"props straddling sectors (of {result['entities']})")
    OUT.mkdir(parents=True, exist_ok=True)
    name = "sector_audit.json" if not argv else f"sector_audit_{'_'.join(p.stem for p in paths)[:80]}.json"
    (OUT / name).write_text(json.dumps(results, indent=1) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
