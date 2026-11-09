#!/usr/bin/env python3
"""
Anskram Keep, MM9 rework: convert the original DAT world into a native OpenYAMM indoor map (BLV: sectors, portals,
linear movers, lights, exits) in the review root.

    python3 level_generation/projects/mm9r_anskramkeep/convert.py            # full build and install
    python3 level_generation/projects/mm9r_anskramkeep/convert.py --plan     # analysis and plans only

Geometry is MM9's PhysicsBSP (the lightmapped static world) and its static world models, merged back from BSP
fragments into convex polygons. Rooms are the air of the keep divided at its doorways (MM9's UserPortals and door
leaves) and at the archways listed in overrides.yml; every face goes to the room in front of it and is split where it
crosses a portal. The source package (GLB + geometry metadata) is written to source/, compiled with
build/tools/mm9_compile_indoor_source, and installed with its scene, Lua and the map's table rows into
output/mm9_rework/assets_dev (see ../mm9r_common/review_root.py). assets_dev is never written. See README.md.
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageDraw
from scipy import ndimage

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(ROOT / "util"))
sys.path.insert(0, str(PROJECT))
import review_root  # noqa: E402
from geometry import (SIX, Polygon, VoxelGrid, air_regions, clip, drop_unshared_collinear, mark,  # noqa: E402
                      merge_coplanar, poly_ring, rectangle_points, sample_polygon, write_glb)
from dungeon.rotation import ladder_records, rectangle_portals, rotating_mover, swing_room  # noqa: E402
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE  # noqa: E402
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402

MAP = "anskramkeep.blv"
STEM = "anskramkeep"
DAT = ROOT / "mm9/extracted/WORLDS/WORLDS/ANSKRAMKEEP.dat"
ALIASES = ROOT / "assets_editor_dev/worlds/mm9/maps/anskramkeep.material_aliases.yml"
SOURCE = PROJECT / "source"
WORK = PROJECT / "work"
OVERRIDES = PROJECT / "overrides.yml"
COMPILER = ROOT / "build/tools/mm9_compile_indoor_source"
OFFSET = (0, 0, 0)              # native = (LT.x, LT.z, LT.y) * 2.56 - OFFSET: the old map's frame (int16 fits)
VOXEL = 16                      # LithTech units (41 native)

LT_SOLID, LT_INVISIBLE = 0x1, 0x4
MONSTER_CLASSES = {"Imply", "Imp", "ImpElder", "NagateHatchling", "NagateElder", "AirBorneIcky", "GuardSegeant"}
SKIPPED_MODELS = ("AITrk", "VisBSP", "PerceptionBrush", "Ladder")      # LadderBlocker is kept (prefix checked below)


def native(points) -> np.ndarray:
    """LithTech (x, y up, z) to native (x, y, z up), scaled, in floats."""
    points = np.asarray(points, float)
    return np.stack([points[..., 0] * SCALE - OFFSET[0], points[..., 2] * SCALE - OFFSET[1],
                     points[..., 1] * SCALE - OFFSET[2]], axis=-1)


def lt_vector_to_native(vector) -> np.ndarray:
    return np.array([vector[0], vector[2], vector[1]], float)


# --- Source -----------------------------------------------------------------------------------------------------------

class Source:
    def __init__(self):
        self.world = read_dat_world(DAT)
        self.models = {model.name: model for model in self.world.world_models}
        self.objects = []
        for index, world_object in enumerate(self.world.objects):
            properties = {p.name: p.value for p in world_object.properties}
            self.objects.append({"index": index, "class": world_object.name, "name": str(properties.get("Name", "")),
                                 "properties": properties})
        self.by_name = {o["name"].lower(): o for o in self.objects}
        aliases = yaml.safe_load(ALIASES.read_text())["textures"]
        self.aliases = {entry["source_texture"].lower(): entry for entry in aliases}

    def polygons(self, model_name: str) -> list[Polygon]:
        model = self.models[model_name]
        result = []
        for poly in model.polies:
            ring = poly_ring(poly)
            if len(ring) < 3:
                continue
            surface = model.surfaces[poly.surface_index]
            texture = model.textures[surface.texture_index]
            points = np.array([model.points[i] for i in ring], float)
            invisible = bool(surface.flags & LT_INVISIBLE) or Path(texture.replace("\\", "/")).stem.lower() == "invisible"
            solid = bool(surface.flags & LT_SOLID)
            if invisible and not solid:
                continue
            role = "invisible" if invisible else ("static" if solid else "nonsolid")
            polygon = Polygon(points, [tuple(np.round(p, 1)) for p in points], texture,
                              (np.array(surface.uv_origin), np.array(surface.uv_u), np.array(surface.uv_v)),
                              surface.flags, model_name, role)
            alias = self.aliases[texture.lower()]
            polygon.notes.update(width=alias["width"], height=alias["height"])
            if polygon.area > 0.5:
                result.append(polygon)
        return result

    def object_class(self, name: str) -> str | None:
        found = self.by_name.get(name.lower())
        return found["class"] if found else None


# --- Content classification -----------------------------------------------------------------------------------------

def classify_models(source: Source, overrides: dict) -> dict:
    """Every world model: static geometry, a mover (its group and motion) or skipped, with the reason."""
    plan = {"static": [], "movers": {}, "skipped": {}}
    for model in source.world.world_models:
        name = model.name
        cls = source.object_class(name)
        if name in ("PhysicsBSP",):
            plan["static"].append(name)
            continue
        if name.startswith(SKIPPED_MODELS) and not name.startswith("LadderBlocker"):
            plan["skipped"][name] = cls or "helper"
            continue
        rule = overrides["models"].get(name)
        if rule is None:
            for pattern, value in overrides["model_patterns"].items():
                if name.startswith(pattern):
                    rule = value
                    break
        if rule is None:
            raise SystemExit(f"world model {name} ({cls}) has no rule in overrides.yml")
        if rule == "static":
            plan["static"].append(name)
        elif rule == "skip":
            plan["skipped"][name] = cls
        else:
            plan["movers"][name] = rule
    return plan


# --- Rooms ----------------------------------------------------------------------------------------------------------

def leaf_rectangle(points: np.ndarray):
    """The doorway rectangle of a door leaf set (closed pose): its mid-plane, a vertical and a horizontal axis."""
    centre = (points.min(0) + points.max(0)) / 2
    flat = points - points.mean(0)
    horizontal = flat[:, [0, 2]]
    _, _, vt = np.linalg.svd(horizontal - horizontal.mean(0), full_matrices=False)
    along = np.array([vt[0][0], 0.0, vt[0][1]])
    normal = np.array([vt[1][0], 0.0, vt[1][1]])
    up = np.array([0.0, 1.0, 0.0])
    a = flat @ along
    centre = points.mean(0) + along * (a.max() + a.min()) / 2
    y = points[:, 1]
    centre[1] = (y.max() + y.min()) / 2
    plane = normal @ points.mean(0)
    centre = centre - normal * (normal @ centre - plane)
    return {"centre": centre, "normal": normal, "axis_a": along, "half_a": (a.max() - a.min()) / 2,
            "axis_b": up, "half_b": (y.max() - y.min()) / 2}


def door_portals(source: Source, plan: dict) -> list[dict]:
    """One portal per doorway: MM9's UserPortals, and the leaves' rectangle for doors without one."""
    portals = []
    for user_portal in source.models["VisBSP"].user_portals:
        centre, dims = np.array(user_portal.center), np.array(user_portal.dims)
        thin = int(np.argmin(dims))
        normal = np.zeros(3); normal[thin] = 1.0
        if dims[0] > 1 and dims[2] > 1:                    # a diagonal doorway: take the plane from its door leaves
            continue
        in_plane = [axis for axis in (0, 2) if axis != thin]
        axis_a = np.zeros(3); axis_a[in_plane[0]] = 1.0
        portals.append({"name": user_portal.name, "kind": "user_portal", "centre": centre, "normal": normal,
                        "axis_a": axis_a, "half_a": float(dims[in_plane[0]]), "axis_b": np.array([0.0, 1.0, 0.0]),
                        "half_b": float(dims[1])})
    named = {p["name"].lower() for p in portals}
    for group, members in mover_groups(plan).items():
        rule = plan["movers"][members[0]]
        if not rule.get("doorway"):
            continue
        portal_name = rule.get("portal") or group
        if portal_name.lower() in named:
            continue
        points = np.concatenate([np.array(source.models[m].points) for m in members])
        rectangle = leaf_rectangle(points)
        rectangle.update({"name": portal_name, "kind": "door_leaves"})
        portals.append(rectangle)
        named.add(portal_name.lower())
    # Each doorway portal moves from the middle of its leaves to their face on its normal's negative side, so the
    # leaves stand wholly in the room on the other side. The engine collides a party with door faces of the next
    # room only once its sphere reaches the portal: with the portal through the middle of thick leaves (the gates:
    # 82 units) the party got half way into a closed leaf from the other room before meeting it.
    leaves = {}
    for group, members in mover_groups(plan).items():
        rule = plan["movers"][members[0]]
        if rule.get("doorway"):
            leaves[(rule.get("portal") or group).lower()] = np.concatenate(
                [np.array(source.models[m].points) for m in members])
    for portal in portals:
        points = leaves.get(portal["name"].lower())
        if points is None:
            continue
        normal = portal["normal"]
        face = float((points @ normal).min()) - 0.5
        portal["centre"] = portal["centre"] + normal * (face - float(normal @ portal["centre"]))
        portal["shifted_to_leaf_face"] = True
    return portals


def mover_groups(plan: dict) -> dict:
    groups = defaultdict(list)
    for name, rule in plan["movers"].items():
        groups[rule["group"]].append(name)
    return dict(sorted(groups.items()))


def build_voxels(polygons: list[Polygon], source: Source):
    points = np.concatenate([p.points for p in polygons])
    grid = VoxelGrid(points.min(0), points.max(0), VOXEL)
    solid = np.zeros(grid.shape, bool)
    for polygon in polygons:
        if polygon.role == "static":
            mark(grid, solid, sample_polygon(polygon.points, VOXEL / 4))
    seeds = []
    for o in source.objects:
        if o["class"] in {"StartPoint", "Light", "TreasureChest", "Trigger"} | MONSTER_CLASSES:
            seeds.append(o["properties"]["Pos"])
    air, stats = air_regions(grid, solid, np.array(seeds, float))
    return grid, solid, air, stats


def portal_barrier(grid: VoxelGrid, portal: dict) -> np.ndarray:
    points = rectangle_points(portal["centre"], portal["axis_a"], portal["half_a"] + VOXEL, portal["axis_b"],
                              portal["half_b"] + VOXEL, VOXEL / 4)
    return grid.index(points)


def label_rooms(grid: VoxelGrid, air: np.ndarray, portals: list[dict]):
    barrier = np.zeros(grid.shape, bool)
    for portal in portals:
        cells = portal["cells"] if "cells" in portal else portal_barrier(grid, portal)
        barrier[cells[:, 0], cells[:, 1], cells[:, 2]] = True
    labels, count = ndimage.label(air & ~barrier, structure=SIX)
    # Pockets smaller than a cube of 4 voxels join the neighbour they touch most.
    sizes = ndimage.sum(np.ones_like(labels), labels, range(count + 1))
    small = [index for index in range(1, count + 1) if sizes[index] < 64]
    for index in small:
        region = labels == index
        ring = ndimage.binary_dilation(region, structure=SIX) & ~region
        neighbours = Counter(int(v) for v in labels[ring] if v and v != index and sizes[v] >= 64)
        if neighbours:
            labels[region] = neighbours.most_common(1)[0][0]
    # Barrier voxels in the air take the label of a neighbour (so faces in a doorway find a room).
    for _ in range(3):
        missing = air & (labels == 0)
        if not missing.any():
            break
        grown = ndimage.grey_dilation(labels, footprint=SIX)
        labels[missing] = grown[missing]
    # Renumber densely, ordered by position (south to north, west to east).
    present = sorted(set(np.unique(labels)) - {0})
    centres = ndimage.center_of_mass(np.ones_like(labels), labels, present)
    order = sorted(range(len(present)), key=lambda i: (round(centres[i][2] / 8), centres[i][0]))
    remap = np.zeros(labels.max() + 1, np.int32)
    for new, i in enumerate(order, start=1):
        remap[present[i]] = new
    return remap[labels], len(present)


def portal_sides(grid: VoxelGrid, labels: np.ndarray, portal: dict) -> tuple[int, int]:
    """The rooms on the two sides of a portal: the most common label over its rectangle, one voxel and a half off."""
    points = rectangle_points(portal["centre"], portal["axis_a"], portal["half_a"] * 0.8, portal["axis_b"],
                              portal["half_b"] * 0.8, VOXEL / 2)
    sides = []
    for sign in (1, -1):
        cells = grid.index(points + portal["normal"] * sign * VOXEL * 1.5)
        found = Counter(int(v) for v in labels[cells[:, 0], cells[:, 1], cells[:, 2]] if v)
        sides.append(found.most_common(1)[0][0] if found else 0)
    return tuple(sides)


class NearestRoom:
    """For every voxel, the nearest voxel of labelled air (the voxels a surface touches are not air)."""
    def __init__(self, grid: VoxelGrid, labels: np.ndarray):
        self.grid, self.labels = grid, labels
        self.distance, self.nearest = ndimage.distance_transform_edt(labels == 0, return_indices=True)

    def front(self, polygon: Polygon, spacing: float = 24.0, with_samples: bool = False):
        """The room in front of each sample of the polygon (0: none; air behind the face does not count)."""
        samples = sample_polygon(polygon.points, spacing)
        if len(samples) > 400:
            samples = samples[np.linspace(0, len(samples) - 1, 400).astype(int)]
        normal = polygon.normal
        points = samples + normal * 6.0
        cells = self.grid.index(points)
        i, j, k = cells[:, 0], cells[:, 1], cells[:, 2]
        near = np.stack([self.nearest[axis][i, j, k] for axis in range(3)], axis=1)
        offset = self.grid.centre(near) - points
        length = np.linalg.norm(offset, axis=1)
        facing = (offset @ normal) >= -0.25 * np.maximum(length, 1e-6)
        found = self.labels[near[:, 0], near[:, 1], near[:, 2]]
        distance = self.distance[i, j, k]
        found[(distance > 2.5) | ~facing] = 0
        # Samples right at open air decide which rooms a face sees; those under a wall standing on it go either way.
        confident = found.copy()
        confident[distance > 1.5] = 0
        if confident.any():
            found = confident
        return (found, samples) if with_samples else found


MIXED: list[dict] = []            # faces left over several rooms
DROPPED: list[dict] = []          # faces with no room in front of them (hidden between brushes or facing out)


SPLIT_AXES = [np.array(a, float) / np.linalg.norm(a) for a in ((1, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, -1), (0, 1, 0))]


def separating_plane(samples: np.ndarray, found: np.ndarray, counts: Counter, corners: np.ndarray):
    """A plane (normal, distance) that puts one room's samples on one side and the other rooms' on the other, for at
    least 88 % of the samples (samples under a wall that stands on the face go either way), at the middle of the gap between them (the widest gap over rooms and axes); None if no
    axis separates any room from the rest."""
    valid = found > 0
    points = samples[valid]
    best = None
    for main in counts:
        inside = found[valid] == main
        total_main, total = int(inside.sum()), len(inside)
        for axis in SPLIT_AXES:
            values = points @ axis
            order = np.argsort(values, kind="stable")
            sorted_inside = inside[order]
            main_below = np.concatenate([[0], np.cumsum(sorted_inside)])
            others_below = np.arange(total + 1) - main_below
            correct_low = main_below + (total - total_main - others_below)        # the room below the split
            correct_high = others_below + (total_main - main_below)               # the room above it
            for correct in (correct_low, correct_high):
                k = int(np.argmax(correct))
                if 0 < k < total and correct[k] >= 0.88 * total:
                    gap = values[order[k]] - values[order[k - 1]]
                    split = (values[order[k]] + values[order[k - 1]]) / 2
                    extent = corners @ axis
                    if min(split - extent.min(), extent.max() - split) < 12.0:      # no slivers
                        continue
                    if best is None or gap > best[0]:
                        best = (gap, axis, split, main)
    if best is None:
        return None
    # Only a split that leaves the separated room's part seeing (nearly) only that room; noise along a doorway edge
    # is no reason. The other part may see several rooms and is split again.
    side = points @ best[1] > best[2]
    for part in (side, ~side):
        labels_part = found[valid][part]
        if len(labels_part) and (labels_part == best[3]).mean() >= 0.5 and (labels_part == best[3]).mean() < 0.9:
            return None
    return best[1], float(best[2])


def assign_faces(rooms: NearestRoom, polygons: list[Polygon], portals: list[dict], stats: Counter) -> list[Polygon]:
    """Each polygon goes to the room in front of it; one that sees two rooms is split by the portal planes between
    them until each part sees one."""
    result = []
    queue = [(p, 0) for p in polygons]
    while queue:
        polygon, depth = queue.pop()
        found, samples = rooms.front(polygon, with_samples=True)
        counts = Counter(int(v) for v in found if v)
        if not counts:
            stats["faces_without_air_dropped"] += 1
            DROPPED.append({"model": polygon.model, "texture": polygon.texture.split("\\")[-1],
                            "centre_lt": polygon.points.mean(0).round(1).tolist(),
                            "normal_lt": polygon.normal.round(2).tolist(), "area_lt": round(polygon.area)})
            continue
        second = counts.most_common(2)[1][1] if len(counts) > 1 else 0
        if len(counts) == 1 or depth >= 10 or second < max(3, 0.15 * sum(counts.values())):
            polygon.label = counts.most_common(1)[0][0]
            if len(counts) > 1 and depth >= 10:
                stats["faces_mixed_after_splitting"] += 1
            result.append(polygon)
            continue
        low, high = polygon.points.min(0) - 2 * VOXEL, polygon.points.max(0) + 2 * VOXEL
        candidates = []
        for portal in portals:
            corners = rectangle_points(portal["centre"], portal["axis_a"], portal["half_a"] + VOXEL,
                                       portal["axis_b"], portal["half_b"] + VOXEL, 1e9)
            if (corners.max(0) < low).any() or (corners.min(0) > high).any():
                continue
            side = polygon.points @ portal["normal"] - portal["normal"] @ portal["centre"]
            if side.min() < -0.5 and side.max() > 0.5:
                candidates.append(portal)
        if not candidates:
            # A face over several rooms without a portal between them (a ceiling or floor brush running over the
            # walls between rooms): split it where the rooms' samples separate along a horizontal axis.
            plane = separating_plane(samples, found, counts, polygon.points)
            if plane is None:
                polygon.label = counts.most_common(1)[0][0]
                stats["faces_mixed_without_portal"] += 1
                if counts.most_common(1)[0][1] < 0.8 * sum(counts.values()):
                    stats["faces_mixed_without_portal_minority_over_20pct"] += 1
                    MIXED.append({"texture": polygon.texture.split("\\")[-1], "centre_lt": polygon.points.mean(0).round().tolist(),
                                  "normal_lt": polygon.normal.round(2).tolist(), "area_lt": round(polygon.area),
                                  "rooms": dict(counts)})
                result.append(polygon)
                continue
            front, back = clip(polygon, plane[0], plane[1], f"wall{depth}")
            stats["face_splits_at_walls"] += 1
            for part in (front, back):
                if part is not None:
                    queue.append((part, depth + 1))
            continue
        portal = candidates[0]
        front, back = clip(polygon, portal["normal"], float(portal["normal"] @ portal["centre"]), portal["name"])
        stats["face_splits"] += 1
        for part in (front, back):
            if part is not None:
                queue.append((part, depth + 1))
    return result


# --- Plans ------------------------------------------------------------------------------------------------------------

def room_colour(label: int) -> tuple:
    import colorsys
    r, g, b = colorsys.hsv_to_rgb((label * 0.618034) % 1.0, 0.55 + 0.35 * (label % 3) / 2, 0.95)
    return int(r * 255), int(g * 255), int(b * 255)


def draw_plan(path: Path, polygons: list[Polygon], portals: list[dict], source: Source, title: str, scale=0.2):
    points = np.concatenate([p.points for p in polygons])
    x0, z1 = points[:, 0].min() - 60, points[:, 2].max() + 60
    width = int((points[:, 0].max() + 60 - x0) * scale)
    height = int((z1 - points[:, 2].min() + 60) * scale)
    image = Image.new("RGB", (width, height), (18, 18, 26))
    draw = ImageDraw.Draw(image)
    to = lambda x, z: ((x - x0) * scale, (z1 - z) * scale)      # noqa: E731
    floors = [p for p in polygons if p.normal[1] > 0.7]
    for polygon in sorted(floors, key=lambda p: p.points[:, 1].mean()):
        colour = room_colour(polygon.label) if polygon.label > 0 else (90, 90, 90)
        shade = 0.55 + 0.45 * np.clip((polygon.points[:, 1].mean() + 450) / 700, 0, 1)
        draw.polygon([to(p[0], p[2]) for p in polygon.points], fill=tuple(int(c * shade) for c in colour))
    for polygon in polygons:
        if abs(polygon.normal[1]) < 0.3:
            xy = [to(p[0], p[2]) for p in polygon.points]
            draw.line(xy + [xy[0]], fill=(10, 10, 10), width=1)
    for portal in portals:
        a = portal["centre"] - portal["axis_a"] * portal["half_a"]
        b = portal["centre"] + portal["axis_a"] * portal["half_a"]
        draw.line([to(a[0], a[2]), to(b[0], b[2])], fill=(255, 255, 255), width=3)
    labels = defaultdict(list)
    for polygon in floors:
        if polygon.label > 0:
            labels[polygon.label].append(polygon.points.mean(0))
    for label, centres in labels.items():
        centre = np.mean(centres, axis=0)
        draw.text(to(centre[0], centre[2]), str(label), fill=(255, 255, 255))
    for gx in range(-2560, 2817, 256):
        draw.line([to(gx, z1), to(gx, z1 - height / scale)], fill=(70, 70, 90) if gx % 1024 else (140, 140, 170))
        draw.text(to(gx + 4, z1 - 20), str(gx), fill=(150, 150, 180))
    for gz in range(-256, 6400, 256):
        draw.line([to(x0, gz), to(x0 + width / scale, gz)], fill=(70, 70, 90) if gz % 1024 else (140, 140, 170))
        draw.text(to(x0 + 4, gz + 30), str(gz), fill=(150, 150, 180))
    draw.text((6, 6), title, fill=(255, 255, 255))
    image.save(path)


# --- Native faces -----------------------------------------------------------------------------------------------------

def planar(points: np.ndarray) -> bool:
    """The compiler's derived-geometry rule: every vertex within 0.01 of the plane of the Newell normal."""
    normal = np.cross(points, np.roll(points, -1, axis=0)).sum(axis=0)
    length = np.linalg.norm(normal)
    if length < 1e-6:
        return False
    normal /= length
    return bool(np.abs((points - points[0]) @ normal).max() <= 0.005)


def face_rings(points_lt: np.ndarray, front_lt: np.ndarray, uv_px: np.ndarray, stats: Counter) -> list:
    """Native faces for one convex polygon: integer vertices (consecutive duplicates removed), wound so the native
    normal is the polygon's front, as one polygon when quantization keeps it planar, else as triangles. Each face
    starts at its sharpest corner, since the compiler's facet type reads the first three vertices."""
    points = np.round(native(points_lt)).astype(np.int64)
    keep = [i for i in range(len(points)) if not np.array_equal(points[i], points[i - 1])]
    points, uv_px = points[keep], uv_px[keep]
    if len(points) < 3:
        stats["faces_collapsed_by_rounding"] += 1
        return []
    front = lt_vector_to_native(front_lt)
    normal = np.cross(points, np.roll(points, -1, axis=0)).sum(axis=0).astype(float)
    if np.linalg.norm(normal) < 1.0:
        stats["faces_collapsed_by_rounding"] += 1
        return []
    if normal @ front < 0:
        points, uv_px = points[::-1], uv_px[::-1]
    if len(points) <= 128 and planar(points.astype(float)):
        count = len(points)
        sharp = max(range(count), key=lambda i: np.linalg.norm(np.cross(points[(i + 1) % count] - points[i],
                                                                         points[(i + 2) % count] - points[i])))
        order = [(sharp + k) % count for k in range(count)]
        stats["native_polygons"] += 1
        return [(points[order], uv_px[order])]
    stats["triangulated_polygons"] += 1
    triangles = []
    for i in range(1, len(points) - 1):
        triangle = points[[0, i, i + 1]]
        if np.linalg.norm(np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])) < 1.0:
            continue
        triangles.append((triangle, uv_px[[0, i, i + 1]]))
    return triangles


def polygon_uvs(polygon: Polygon) -> np.ndarray:
    """MM9's surface mapping in texels, shifted by whole repeats so the numbers stay small."""
    origin, axis_u, axis_v = polygon.mapping
    relative = polygon.points - origin
    uv = np.stack([relative @ axis_u, relative @ axis_v], axis=1)
    size = np.array([polygon.notes["width"], polygon.notes["height"]], float)
    return uv - np.floor(uv.min(0) / size) * size


class SourcePackage:
    """The GLB nodes and the geometry metadata the indoor compiler reads."""
    def __init__(self, source: Source):
        self.source = source
        self.nodes = defaultdict(list)          # node name -> [(points, uvs (texels), material)]
        self.materials = {}
        self.room_nodes = defaultdict(list)     # room id -> owned nodes
        self.metadata = {"format_version": 2, "kind": "indoor_geometry", "map_file": MAP,
                         "source": {"authoring_file": "convert.py", "asset_path": f"{STEM}.glb",
                                    "coordinate_system": "blender_z_up", "unit_scale": 1.0,
                                    "import": {"source_format": "glb", "reserve_sector_zero": True,
                                               "merge_coplanar_faces": False, "triangulate_ngons": False,
                                               "generate_bsp": True, "generate_outlines": True}},
                         "materials": [], "rooms": [], "portals": [], "surfaces": [], "mechanisms": [],
                         "entities": [], "lights": [], "spawns": []}

    def material(self, texture: str) -> tuple[str, int, int]:
        alias = self.source.aliases[texture.lower()]
        key = alias["alias"]
        if key not in self.materials:
            self.materials[key] = (alias["width"], alias["height"])
            self.metadata["materials"].append({"id": key, "source_material": key, "texture": key,
                                               "texture_width": alias["width"], "texture_height": alias["height"]})
        return key, alias["width"], alias["height"]

    def add_polygon(self, node: str, polygon: Polygon, stats: Counter) -> int:
        key, _, _ = self.material(polygon.texture)
        rings = face_rings(polygon.points, polygon.normal, polygon_uvs(polygon), stats)
        for points, uvs in rings:
            self.nodes[node].append((points, uvs, key))
        return len(rings)

    def add_raw(self, node: str, points_native: np.ndarray, material: str):
        self.nodes[node].append((points_native, np.zeros((len(points_native), 2)), material))

    def marker(self, node: str, position_native: np.ndarray, material: str):
        x, y, z = position_native
        self.add_raw(node, np.array([[x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y + 1, z], [x - 1, y + 1, z]]),
                     material)

    def write(self, glb_path: Path, metadata_path: Path):
        nodes = []
        for name, faces in self.nodes.items():
            primitives = []
            for points, uvs, key in faces:
                width, height = self.materials.get(key, (64, 64))
                primitives.append({"material": key, "positions": np.asarray(points, float),
                                   "uvs": np.asarray(uvs, float) / np.array([width, height]),
                                   "indices": np.arange(len(points)), "mode": 6})
            nodes.append({"name": name, "primitives": primitives})
        write_glb(glb_path, nodes)
        metadata_path.write_text(json.dumps(self.metadata, indent=1) + "\n")


def room_id(label: int) -> str:
    return f"room_r{label:02d}"


# --- Movers ---------------------------------------------------------------------------------------------------------

RISE_SPEED = 192            # native units per second for the converted MM9 swing doors
SINK_SPEED = 384            # the cages' wall plugs (MM9 destroys them at once)
NUDGE_SPEED = 64            # the levers and switches (MM9 swings them in about a second)


def build_movers(source: Source, plan: dict, package: SourcePackage, rooms: NearestRoom, grid: VoxelGrid,
                 stats: Counter, present: set) -> list[dict]:
    """Native movers: one per MM9 linear Door model, sinking cage plug or swinging leaf, lever, hatch and trap
    (`rotate`: a rotating mover, devdocs/INDOOR_ROTATING_MOVERS_AND_LADDERS.md). Each door group gets one click event
    that triggers all its movers; plates, panels, levers and switches get content.MOVER_EVENTS (pressure plates or
    clicks), handled by content.map_script."""
    import content
    movers, door_id = [], 0
    groups = mover_groups(plan)
    event_for_group = {}
    for group, members in groups.items():
        rule = plan["movers"][members[0]]
        motion = rule["motion"]
        nodes = [members] if motion == "rise" else [[m] for m in members]
        for node_members in nodes:
            door_id += 1
            node = "MECH_" + (group if motion == "rise" else node_members[0])
            polygons = [p for m in node_members for p in source.polygons(m)]
            properties = source.by_name[node_members[0].lower()]["properties"]
            shut_pose = rule.get("authored_open", False)
            if shut_pose:
                # MM9 authors these leaves apart and its "open" slides them shut. They are built in the shut pose
                # (the pose that must collide from both rooms) and start open, apart, as in MM9.
                shift = np.asarray(properties["MoveDir"], float)
                shift = shift / np.linalg.norm(shift) * float(properties["MoveDist"])
                polygons = [Polygon(p.points + shift, p.keys, p.texture, (p.mapping[0] + shift,) + tuple(p.mapping[1:]),
                                    p.flags, p.model, p.role, notes=dict(p.notes)) for p in polygons]
            points = np.concatenate([p.points for p in polygons])
            centre = (points.min(0) + points.max(0)) / 2
            owner = owner_room(rooms, grid, centre)
            for polygon in polygons:
                package.add_polygon(node, polygon, stats)
            spin, extra_rooms = None, []
            if motion == "rotate":
                spin = rotating_mover(node_members[0], rule, properties, polygons, native, lt_vector_to_native)
                open_direction = np.zeros(3)
                length, open_speed, close_speed = spin["move_length"], spin["open_speed"], spin["close_speed"]
                extra = swing_room(polygons, properties, owner, lambda point: owner_room(rooms, grid, point))
                if extra in present:
                    extra_rooms = [extra]
            elif motion == "rise":
                height = (points[:, 1].max() - points[:, 1].min()) * SCALE
                open_direction = np.array([0.0, 0.0, 1.0])
                length, open_speed, close_speed = int(round(height + 8)), RISE_SPEED, RISE_SPEED
            elif motion == "sink":
                height = (points[:, 1].max() - points[:, 1].min()) * SCALE
                open_direction = np.array([0.0, 0.0, -1.0])
                length, open_speed, close_speed = int(round(height + 8)), SINK_SPEED, SINK_SPEED
            elif motion == "nudge":
                move = lt_vector_to_native(np.asarray(rule["move_lt"], float)) * SCALE
                open_direction = move / np.linalg.norm(move)
                length, open_speed, close_speed = int(round(np.linalg.norm(move))), NUDGE_SPEED, NUDGE_SPEED
            else:
                direction = np.asarray(properties["MoveDir"], float)
                open_direction = lt_vector_to_native(direction / np.linalg.norm(direction))
                length = int(round(float(properties["MoveDist"]) * SCALE))
                open_speed = int(round(float(properties.get("Speed", 50)) * SCALE))
                close_speed = int(round(float(properties.get("ClosingSpeed", properties.get("Speed", 50))) * SCALE))
                if shut_pose:
                    open_direction = -open_direction
            event, trigger_type = 0, "click"
            if group in content.MOVER_EVENTS:
                event, trigger_type = content.MOVER_EVENTS[group]
            elif rule.get("doorway") and rule.get("click", True):
                event = event_for_group.setdefault(group, 100 + len(event_for_group) + 1)
            mechanism = {"id": node[5:], "kind": "rotating" if spin else "linear", "source_nodes": [node],
                         "door": {"door_id": door_id, "initial_state": "open" if shut_pose else "closed",
                                  "source_pose": "closed",
                                  "direction": [round(-v, 6) for v in open_direction.tolist()],
                                  "move_length": length, "open_speed": open_speed, "close_speed": close_speed}}
            if extra_rooms:
                mechanism["extra_rooms"] = extra_rooms
            package.metadata["mechanisms"].append(mechanism)
            if event:
                package.metadata["surfaces"].append({"id": node[5:], "source_node": node, "flags": [],
                                                     "trigger": {"event_id": event, "type": trigger_type}})
            package.room_nodes[owner].append(node)
            movers.append({"node": node, "dat_models": node_members, "group": group, "door_id": door_id,
                           "event": event, "motion": motion, "room": owner, "move_length": length,
                           "initial_state": "open" if shut_pose else "closed",
                           "open_direction": open_direction.tolist(), "open_speed": open_speed,
                           "mm9_class": source.object_class(node_members[0]),
                           "mover": spin["mover"] if spin else None, "extra_rooms": extra_rooms})
    return movers


def owner_room(rooms: NearestRoom, grid: VoxelGrid, point_lt: np.ndarray) -> str:
    cell = grid.index(np.asarray(point_lt, float)[None])[0]
    near = [rooms.nearest[axis][cell[0], cell[1], cell[2]] for axis in range(3)]
    return room_id(int(rooms.labels[near[0], near[1], near[2]]))


# --- Lights -----------------------------------------------------------------------------------------------------------

MAX_LIGHTS_PER_POINT = 4


def build_lights(source: Source, polygons: list[Polygon], package: SourcePackage, rooms: NearestRoom,
                 grid: VoxelGrid) -> list[dict]:
    """MM9's point lights (class Light; the 408 DirLights only fed MM9's lightmap bake) as native lights, kept in
    order of their reach (torch lights first) while no floor point is under more than four."""
    floor_samples = np.concatenate([sample_polygon(p.points, 96) for p in polygons if p.normal[1] > 0.7])
    floor_native = native(floor_samples) + np.array([0, 0, 64])
    candidates = []
    for o in source.objects:
        if o["class"] != "Light":
            continue
        p = o["properties"]
        radius = float(p.get("LightRadius", 300)) * SCALE
        colour = [int(round(c)) for c in p.get("LightColor", [255, 255, 255])]
        candidates.append({"name": o["name"], "position_lt": p["Pos"], "position": native(p["Pos"]).round().tolist(),
                           "radius": int(round(radius)), "colour": colour,
                           "bright_scale": float(p.get("BrightScale", 1.0))})
    coverage = np.zeros(len(floor_native), np.int32)
    lights = []
    for light in sorted(candidates, key=lambda l: (l["radius"], l["name"])):
        reach = np.linalg.norm(floor_native - np.array(light["position"]), axis=1) <= light["radius"]
        if (coverage[reach] >= MAX_LIGHTS_PER_POINT).any():
            light["kept"] = False
            light["reason"] = "a floor point already under four lights"
            lights.append(light)
            continue
        coverage[reach] += 1
        light["kept"] = True
        light["room"] = owner_room(rooms, grid, np.array(light["position_lt"], float))
        node = "LIGHT_" + light["name"]
        package.marker(node, np.array(light["position"], float), next(iter(package.materials)))
        package.room_nodes[light["room"]].append(node)
        package.metadata["lights"].append({"id": light["name"], "source_node": node, "color": light["colour"],
                                           "radius": light["radius"], "brightness": 31, "type": "point"})
        lights.append(light)
    return lights


# --- Party, exits, population -----------------------------------------------------------------------------------------

def floor_below(polygons: list[Polygon], point_lt) -> float | None:
    """The highest floor under a point (LithTech y), for snapping starts and arrivals."""
    x, y, z = point_lt
    best = None
    for polygon in polygons:
        if polygon.normal[1] < 0.7 or polygon.role != "static":
            continue
        pts = polygon.points
        if not (pts[:, 0].min() <= x <= pts[:, 0].max() and pts[:, 2].min() <= z <= pts[:, 2].max()):
            continue
        inside = False
        count = len(pts)
        for i in range(count):
            x1, z1, x2, z2 = pts[i, 0], pts[i, 2], pts[(i + 1) % count, 0], pts[(i + 1) % count, 2]
            if (z1 > z) != (z2 > z) and x < x1 + (z - z1) / (z2 - z1) * (x2 - x1):
                inside = not inside
        if not inside:
            continue
        n = polygon.normal
        height = (n @ pts[0] - n[0] * x - n[2] * z) / n[1]
        if height <= y + 1 and (best is None or height > best):
            best = height
    return best


def population(source: Source, polygons: list[Polygon]) -> dict:
    """Where MM9 placed its monsters and chests (DAT records; content.py places them)."""
    from transcode_mm9_dat_to_odm import lt_rotation_to_openyamm_yaw_degrees
    monsters, chests = [], []
    for o in source.objects:
        p = o["properties"]
        if o["class"] not in MONSTER_CLASSES | {"TreasureChest"}:
            continue
        floor = floor_below(polygons, p["Pos"])
        record = {"dat_object_index": o["index"], "name": o["name"], "class": o["class"],
                  "position_lt": [round(v, 1) for v in p["Pos"]],
                  "position": native(p["Pos"]).round().astype(int).tolist(),
                  "floor_z": None if floor is None else int(round(floor * SCALE)),
                  "facing_degrees": round(lt_rotation_to_openyamm_yaw_degrees(p.get("Rotation", [0, 0, 0, 0])), 1)}
        keys = (("Locked", "TreasureLevel", "TrapLevel", "TreasureType0_7", "Gold", "GoldOnly", "Random", "AIDrop",
                 "Item1", "Item2", "Item3", "Item4", "Item5", "TriggerTarget", "Filename", "Scale")
                if o["class"] == "TreasureChest" else
                ("ScriptName", "WanderPathName", "Filename", "Scale", "ShouldRepopulate", "GiveTreasure", "SightDistance"))
        for key in keys:
            value = p.get(key)
            if value in ("", None):
                continue
            if isinstance(value, int) and abs(value) > 1_000_000:         # a float stored in an int property
                value = round(struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0], 3)
            record[key] = value
        (chests if o["class"] == "TreasureChest" else monsters).append(record)
    counts = Counter(m["class"] for m in monsters)
    return {"note": "DAT placements in the native frame (work/transform.json); content.py places them (work/content.json)",
            "monster_counts": dict(sorted(counts.items())), "monsters": monsters, "chests": chests}


# --- Scene, script, tables, install ---------------------------------------------------------------------------------

AMBIENT = 20                    # sector minimum light level (0 brightest, 31 black); MM9 lights its rooms


def scene_file(starts: list[dict], doors: list) -> dict:
    template = ROOT / "level_generation/projects/brackenford_greywatch/calibration/calibration.scene.yml"
    scene = json.loads(template.read_text())
    scene["source"]["geometry_file"] = MAP
    scene["environment"]["ceiling"] = 1024
    scene["party_start_points"] = [{"start_index": i, "source_name": "StartPoint0" if i == 0 else s["name"],
                                    "position": s["position"], "direction_degrees": s["direction_degrees"]}
                                   for i, s in enumerate(starts)]
    scene["initial_state"]["doors"] = doors
    scene["initial_state"]["actors"] = []
    scene["loot_containers"] = []
    return scene


def read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    lines = path.read_text().split("\n")
    return lines, [line.split("\t") for line in lines]


EXIT_BOTTOMS: dict = {}            # overrides.yml exits: DAT exit name -> lowest LithTech y of its volume


def table_rows(polygons: list[Polygon], source: Source) -> dict:
    """The review root's copies of map_stats.txt and map_transitions.txt with this map's rows changed (computed from the
    assets_dev originals, merged into the review root's current copies so other maps' changes stay). Files are read
    with newline="" so every line keeps its own ending (map_stats mixes CRLF and LF rows)."""
    results = {}
    # map_stats: the row of anskramkeep.odm names the BLV.
    original = ROOT / "assets_dev/engine/data_tables/map_stats.txt"
    current = review_root.mirror_path("engine/data_tables/map_stats.txt")
    replacements = {}
    for line in original.read_text(newline="").split("\n"):
        cells = line.split("\t")
        if len(cells) > 2 and cells[2] == "anskramkeep.odm":
            cells[2] = MAP
            replacements[cells[0]] = "\t".join(cells)
    out = []
    for line in current.read_text(newline="").split("\n"):
        cells = line.split("\t")
        out.append(replacements.get(cells[0], line) if len(cells) > 2 and cells[1] == "Anskram Keep" else line)
    results["engine/data_tables/map_stats.txt"] = "\n".join(out)
    # map_transitions: exits from the keep and arrivals into it; the frame is unchanged, arrivals land on the floor.
    original = ROOT / "assets_dev/worlds/mm9/data_tables/map_transitions.txt"
    current = review_root.mirror_path("worlds/mm9/data_tables/map_transitions.txt")
    header = original.read_text(newline="").split("\n")[0].split("\t")
    column = {name: i for i, name in enumerate(header)}
    replacements, changes = {}, []
    for line in original.read_text(newline="").split("\n")[1:]:
        cells = line.split("\t")
        if len(cells) < len(header):
            continue
        changed = False
        if cells[column["SourceMapFile"]] == "anskramkeep.odm":
            cells[column["SourceMapFile"]] = MAP
            bottom = EXIT_BOTTOMS.get(cells[column["SourceName"]])
            if bottom is not None:              # the volume reaches down to the floor the party stands on
                top = float(cells[column["CenterZ"]]) + float(cells[column["HalfExtentZ"]])
                low = bottom * SCALE
                cells[column["CenterZ"]] = str(int(round((top + low) / 2)))
                cells[column["HalfExtentZ"]] = str(int(round((top - low) / 2)))
            changed = True
        if cells[column["DestinationMapFile"]] == "anskramkeep.odm":
            cells[column["DestinationMapFile"]] = MAP
            point = (float(cells[column["ArrivalX"]]) / SCALE, float(cells[column["ArrivalZ"]]) / SCALE,
                     float(cells[column["ArrivalY"]]) / SCALE)
            floor = floor_below(polygons, point)
            if floor is not None:
                cells[column["ArrivalZ"]] = str(int(round(floor * SCALE)) + 1)
            changed = True
        if changed:
            replacements[cells[0]] = "\t".join(cells)
            changes.append({"id": cells[0], "source": cells[column["SourceMapFile"]], "name": cells[column["SourceName"]],
                            "destination": cells[column["DestinationMapFile"]],
                            "arrival": [cells[column["ArrivalX"]], cells[column["ArrivalY"]], cells[column["ArrivalZ"]]]})
    out = [replacements.get(line.split("\t")[0], line) for line in current.read_text(newline="").split("\n")]
    results["worlds/mm9/data_tables/map_transitions.txt"] = "\n".join(out)
    return results, changes


OLD_SIDECARS = (".odm", ".render", ".render.yml", ".nav", ".nav.yml", ".lighting", ".mm9.yml", ".model_assets.yml",
                ".raw_objects.yml", ".material_aliases.yml", ".events.yml")


def install(runtime: Path, tables: dict) -> None:
    maps = Path("worlds/mm9/maps")
    for suffix in OLD_SIDECARS:
        # The BLV's own baked lighting (bake_lighting.py, an indoor OYILIT1 file) shares the old map's .lighting name:
        # keep it (the game ignores it once this rebuild changes the BLV; bake_lighting.py makes a matching one).
        target = review_root.mirror_path(maps / f"{STEM}{suffix}")
        if suffix == ".lighting" and target.is_file() and target.read_bytes()[:8] == b"OYILIT1\0":
            continue
        review_root.remove(maps / f"{STEM}{suffix}")
    review_root.remove(Path("worlds/mm9/events/maps") / f"{STEM}.script_ir.yml")
    review_root.install_file(maps / MAP, runtime / MAP)
    review_root.install_file(maps / f"{STEM}.scene.yml", runtime / f"{STEM}.scene.yml")
    review_root.install_file(Path("worlds/mm9/events/maps") / f"{STEM}.lua", runtime / f"{STEM}.lua")
    for relative, text in tables.items():
        review_root.install(relative, text.encode())


def install_original_comparison() -> None:
    """The original map forbids saving, which the isolated launcher needs: the second mirror
    (output/mm9_rework/assets_original) gets a copy of the old scene that allows it (temporary file, then rename)."""
    import os
    import tempfile
    mirror = ROOT / "output/mm9_rework/assets_original"
    target = mirror / f"worlds/mm9/maps/{STEM}.scene.yml"
    if not mirror.exists():
        print(f"note: {mirror} is missing; the comparison tour cannot run")
        return
    text = (ROOT / f"assets_editor_dev/worlds/mm9/maps/{STEM}.scene.yml").read_text()
    text = text.replace("  allow_save_game: false", "  allow_save_game: true", 1)
    if target.exists() and target.read_text() == text:
        return
    handle, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
    with os.fdopen(handle, "w") as stream:
        stream.write(text)
    os.chmod(temporary, 0o644)
    os.replace(temporary, target)


# --- Main -------------------------------------------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", action="store_true", help="analysis and plan images only")
    arguments = parser.parse_args()
    WORK.mkdir(exist_ok=True)
    overrides = yaml.safe_load(OVERRIDES.read_text())
    EXIT_BOTTOMS.update({name: rule["bottom_lt"] for name, rule in (overrides.get("exits") or {}).items()})
    source = Source()
    plan = classify_models(source, overrides)
    stats = Counter()

    polygons = []
    for name in plan["static"]:
        polygons += source.polygons(name)
    stats["source_polygons"] = len(polygons)
    polygons = merge_coplanar(polygons)
    stats["merged_polygons"] = len(polygons)
    stats["collinear_vertices_removed"] = drop_unshared_collinear(polygons)

    portals = door_portals(source, plan)
    grid, solid, air, air_stats = build_voxels(polygons, source)
    stats.update(air_stats)
    for extra in overrides.get("portals", []):
        portals.extend(archway_portals(grid, air, extra))
    portals.extend(rectangle_portals(overrides.get("rect_portals")))
    labels, room_count = label_rooms(grid, air, portals)
    stats["rooms"] = room_count
    for portal in portals:
        portal["rooms"] = portal_sides(grid, labels, portal)
    leaky = [p["name"] for p in portals if len(set(p["rooms"])) < 2 or 0 in p["rooms"]]
    stats["portals_without_two_rooms"] = len(leaky)
    if leaky:
        print("portals without two rooms:", leaky, [p["rooms"] for p in portals if p["name"] in leaky])
    rooms = NearestRoom(grid, labels)
    polygons = assign_faces(rooms, polygons, portals, stats)
    stats["faces"] = len(polygons)
    draw_plan(WORK / "rooms.png", polygons, portals, source, f"{room_count} rooms, {len(portals)} portals")
    draw_plan(WORK / "rooms_large.png", polygons, portals, source, "rooms", scale=0.4)
    if arguments.plan:
        (WORK / "dropped_faces.json").write_text(json.dumps(DROPPED, indent=0) + "\n")
        (WORK / "mixed_faces.json").write_text(json.dumps(MIXED, indent=0) + "\n")
        print(json.dumps(stats, indent=1))
        return 0

    # Source package: rooms, their invisible and non-solid faces, portals, movers, lights.
    review_root.create(fresh=False)
    package = SourcePackage(source)
    by_room = defaultdict(list)
    for polygon in polygons:
        by_room[polygon.label].append(polygon)
    room_faces = {}
    for label in sorted(by_room):
        rid = room_id(label)
        for polygon in by_room[label]:
            node = {"static": "ROOM_", "invisible": "TRIGGER_invisible_", "nonsolid": "TRIGGER_nonsolid_"}[
                polygon.role] + rid[5:]
            package.add_polygon(node, polygon, stats)
            if node.startswith("TRIGGER_") and node not in package.room_nodes[rid]:
                package.room_nodes[rid].append(node)
                package.metadata["surfaces"].append({"id": node[8:], "source_node": node, "flags": [
                    "invisible" if polygon.role == "invisible" else "untouchable"]})
        room_faces[rid] = sum(len(package.nodes[n]) for n in [f"ROOM_{rid[5:]}"] + package.room_nodes[rid])
    present = {room_id(label) for label in by_room if package.nodes.get(f"ROOM_{room_id(label)[5:]}")}
    portal_report = []
    for portal in portals:
        front, back = (room_id(v) for v in portal["rooms"])
        if front == back or front not in present or back not in present:
            portal_report.append({"name": portal["name"], "kind": portal["kind"], "skipped": True,
                                  "rooms": [front, back]})
            continue
        corners = [portal["centre"] + sa * portal["axis_a"] * portal["half_a"] + sb * portal["axis_b"] * portal["half_b"]
                   for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        node = "PORTAL_" + portal["name"]
        material = package.material(next(iter(source.aliases.values()))["source_texture"])[0]
        rings = face_rings(np.array(corners), portal["normal"], np.zeros((4, 2)), Counter())
        for points, _ in rings:
            package.add_raw(node, points, material)
        package.metadata["portals"].append({"id": portal["name"], "source_node": node, "front_room": front,
                                            "back_room": back})
        portal_report.append({"name": portal["name"], "kind": portal["kind"], "rooms": [front, back],
                              "centre_native": native(portal["centre"]).round().astype(int).tolist(),
                              "width": round(2 * portal["half_a"] * SCALE), "height": round(2 * portal["half_b"] * SCALE),
                              "faces": len(rings)})
    movers = build_movers(source, plan, package, rooms, grid, stats, present)
    lights = build_lights(source, polygons, package, rooms, grid)
    import content as content_module
    population_content = content_module.Content(source, polygons, package, rooms, grid)
    loot = population_content.loot()
    population_content.decorations(loot)
    population_content.pads()
    sector_of_room = {rid: index + 1 for index, rid in enumerate(sorted(present))}
    for rid in sorted(present):
        package.metadata["rooms"].append({"id": rid, "source_nodes": [f"ROOM_{rid[5:]}"] + package.room_nodes[rid],
                                          "min_ambient_light_level": AMBIENT})
    SOURCE.mkdir(exist_ok=True)
    package.write(SOURCE / f"{STEM}.glb", SOURCE / f"{STEM}.geometry.yml")

    # Compile.
    runtime = WORK / "runtime"
    runtime.mkdir(exist_ok=True)
    result = subprocess.run([str(COMPILER), str(SOURCE / f"{STEM}.glb"), str(SOURCE / f"{STEM}.geometry.yml"),
                             str(runtime / MAP), str(runtime / f"{STEM}.doors.yml"), str(runtime / f"{STEM}.faces.yml")],
                            capture_output=True, text=True)
    (WORK / "build.log").write_text(result.stdout + result.stderr)
    if result.returncode != 0:
        raise SystemExit("compile failed:\n" + result.stdout[-3000:] + result.stderr[-3000:])
    print(result.stdout.strip().split("\n")[0])
    doors = yaml.safe_load((runtime / f"{STEM}.doors.yml").read_text()) or []

    # Starts, scene, script, tables.
    from transcode_mm9_dat_to_odm import lt_rotation_to_openyamm_yaw_degrees
    starts = []
    for name in ("Anskramkeepback", "Anskramkeepfront"):
        p = source.by_name[name.lower()]["properties"]
        floor = floor_below(polygons, p["Pos"])
        position = native(p["Pos"]).round().astype(int).tolist()
        position[2] = int(round(floor * SCALE)) + 1
        starts.append({"name": name, "position": position,
                       "direction_degrees": int(round(lt_rotation_to_openyamm_yaw_degrees(p["Rotation"]))) % 360})
    mover_blocks = {mover["door_id"]: mover["mover"] for mover in movers if mover["mover"]}
    for door in doors:
        if door["door_id"] in mover_blocks:
            door["mover"] = mover_blocks[door["door_id"]]
    scene = scene_file(starts, doors)
    scene["ladders"] = ladder_records(overrides.get("ladders"), source.models, native, SCALE)
    scene["initial_state"]["actors"] = population_content.actors(sector_of_room)
    scene["loot_containers"] = loot
    (runtime / f"{STEM}.scene.yml").write_text(json.dumps(scene, indent=1) + "\n")
    (runtime / f"{STEM}.lua").write_text(content_module.map_script(movers, population_content, source))
    tables, transition_changes = table_rows(polygons, source)
    install(runtime, tables)
    install_original_comparison()

    # Reports.
    sys.path.insert(0, str(ROOT))
    from util.map_export import parse_blv_file
    blv = parse_blv_file(review_root.mirror_path(f"worlds/mm9/maps/{MAP}"))["payload"]
    sector_faces = list(Counter(f["room_number"] for f in blv["faces"] if not f["is_portal"]).values())
    report = {"map": MAP, "stats": dict(stats), "native": {
        "faces": len(blv["faces"]), "vertices": len(blv["vertices"]), "sectors": len(blv["sectors"]),
        "portal_faces": sum(1 for f in blv["faces"] if f["is_portal"]), "doors": len(doors), "lights": len(blv["lights"]),
        "faces_per_sector_max": max(sector_faces), "faces_per_sector_median": int(np.median(sector_faces))},
        "portals": portal_report, "transitions": transition_changes, "starts": starts}
    (WORK / "build_report.json").write_text(json.dumps(report, indent=1) + "\n")
    (WORK / "doors.json").write_text(json.dumps(movers, indent=1) + "\n")
    (WORK / "dropped_faces.json").write_text(json.dumps(DROPPED, indent=0) + "\n")
    (WORK / "lights.json").write_text(json.dumps(lights, indent=1) + "\n")
    population_content.report["light_coverage"] = light_coverage(polygons, lights, population_content)
    population_content.report["decorations_per_room_max"] = max(Counter(
        d["room"] for d in population_content.report["decorations"]).values())
    (WORK / "content.json").write_text(json.dumps(population_content.report, indent=1) + "\n")
    (WORK / "population.json").write_text(json.dumps(population(source, polygons), indent=1) + "\n")
    (WORK / "models.json").write_text(json.dumps({"static": plan["static"], "skipped": plan["skipped"],
                                                  "movers": sorted(plan["movers"])}, indent=1) + "\n")
    (WORK / "transform.json").write_text(json.dumps({
        "scale": SCALE, "offset": OFFSET, "voxel_lt": VOXEL,
        "note": "native x = LT.x * scale - offset[0], y = LT.z * scale - offset[1], z = LT.y * scale - offset[2] "
                "(the frame of the old bmodel_world map, so its transitions and minimap bounds stay valid)"},
        indent=1) + "\n")
    print(json.dumps(report["native"], indent=1))
    return 0


def light_coverage(polygons: list[Polygon], lights: list[dict], population_content) -> dict:
    """Floor points under more than four lights, counting the kept BLV lights and the decorations that carry a light
    (the Imp gate fires; the wall torches carry none: the BLV light beside each is theirs)."""
    floor_samples = np.concatenate([sample_polygon(p.points, 96) for p in polygons if p.normal[1] > 0.7])
    floor_native = native(floor_samples) + np.array([0, 0, 64])
    sources = [(np.array(l["position"], float), l["radius"]) for l in lights if l["kept"]]
    sources += [(np.array(d["position"], float), 205) for d in population_content.report["decorations"]
                if d["decoration"] == "mm9_gatefire"]
    coverage = np.zeros(len(floor_native), np.int32)
    for position, radius in sources:
        coverage += np.linalg.norm(floor_native - position, axis=1) <= radius
    return {"lights": len(sources), "max_per_floor_point": int(coverage.max()),
            "points_over_four": int((coverage > MAX_LIGHTS_PER_POINT).sum())}


def archway_portals(grid: VoxelGrid, air: np.ndarray, extra: dict) -> list[dict]:
    """An archway cut: the air of the voxel slice perpendicular to `axis` (x or z) through `point` (or each of
    `points`, for a cut across several openings in one plane), as far as it connects to the point within that slice
    and within `span` of it along the cut, is the barrier; each opening's bounding rectangle is a portal (one per
    opening, since each joins its own pair of rooms)."""
    axis = {"x": 0, "z": 2}[extra["axis"]]
    others = [a for a in range(3) if a != axis]
    horizontal = others[1] if others[1] != 1 else others[0]
    h, v = others.index(horizontal), others.index(1)
    seeds = [np.array(p, float) for p in extra.get("points", [extra.get("point")])]
    plane_cell = grid.index(seeds[0][None])[0][axis]
    slice_air = np.take(air, plane_cell, axis=axis)                     # 2D over the two other axes in order
    span_cells = int(np.ceil(extra.get("span", 256) / grid.size))
    openings = []
    for point in seeds:
        cell = grid.index(point[None])[0]
        seed = (cell[others[0]], cell[others[1]])
        if not slice_air[seed]:
            near = np.argwhere(slice_air)
            seed = tuple(near[np.argmin(np.abs(near - np.array(seed)).sum(1))])
        window = np.zeros_like(slice_air)
        index = [slice(None), slice(None)]
        index[h] = slice(max(seed[h] - span_cells, 0), seed[h] + span_cells + 1)
        window[tuple(index)] = True
        windowed, _ = ndimage.label(slice_air & window)
        component = windowed == windowed[seed]
        if not any((component & other).any() for other in openings):
            openings.append(component)
    plane = grid.origin[axis] + (plane_cell + 0.5) * grid.size
    portals = []
    for number, component in enumerate(openings):
        cells2 = np.argwhere(component)
        cells = np.zeros((len(cells2), 3), np.int64)
        cells[:, axis] = plane_cell
        cells[:, others[0]], cells[:, others[1]] = cells2[:, 0], cells2[:, 1]
        low = grid.origin[others] + cells2.min(0) * grid.size
        high = grid.origin[others] + (cells2.max(0) + 1) * grid.size
        centre = np.zeros(3)
        centre[axis] = plane
        centre[others] = (low + high) / 2
        normal = np.zeros(3); normal[axis] = 1.0
        axis_a = np.zeros(3); axis_a[horizontal] = 1.0
        name = extra["name"] if len(openings) == 1 else f"{extra['name']}_{number + 1}"
        portals.append({"name": name, "kind": "archway", "centre": centre, "normal": normal, "axis_a": axis_a,
                        "half_a": (high[h] - low[h]) / 2, "axis_b": np.array([0.0, 1.0, 0.0]),
                        "half_b": (high[v] - low[v]) / 2, "cells": cells})
    return portals


if __name__ == "__main__":
    sys.exit(main())
