"""
The indoor source package the compiler (build/tools/mm9_compile_indoor_source) reads: GLB nodes (rooms, movers,
portals, trigger faces, light and entity markers) and the geometry metadata (materials, rooms, portals, surfaces,
mechanisms, entities, lights). Faces are written in native integer coordinates with MM9's texel mapping.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from .geometry import Polygon, write_glb
from .source import lt_vector_to_native


def room_id(label: int) -> str:
    return f"room_r{label:02d}"


def planar(points: np.ndarray) -> bool:
    """The compiler's derived-geometry rule: every vertex within 0.01 of the plane of the Newell normal."""
    normal = np.cross(points, np.roll(points, -1, axis=0)).sum(axis=0)
    length = np.linalg.norm(normal)
    if length < 1e-6:
        return False
    normal /= length
    return bool(np.abs((points - points[0]) @ normal).max() <= 0.005)


def face_rings(project, points_lt: np.ndarray, front_lt: np.ndarray, uv_px: np.ndarray, stats: Counter) -> list:
    """Native faces for one convex polygon: integer vertices (consecutive duplicates removed), wound so the native
    normal is the polygon's front, as one polygon when quantization keeps it planar, else as triangles. Each face
    starts at its sharpest corner, since the compiler's facet type reads the first three vertices."""
    points = np.round(project.native(points_lt)).astype(np.int64)
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


T_JUNCTION_REACH = 0.75     # native units: a vertex this close to another face's edge (not its end) sits on it
T_JUNCTION_CELL = 64


def repair_t_junctions(faces: list, stats: Counter) -> list:
    """Close the cracks at T-junctions. Where a vertex of one drawn face lies on the interior of another face's edge
    (a coplanar neighbour cut alone at a wall or a portal plane; a wall whose pieces stand on one long floor edge:
    MM9 cuts and merges its polygons independently), the two faces do not share that seam, and rounding to native
    units moves the vertex up to 0.71 units off the edge: the renderer leaves a crack along it, which shows the sky or
    the clear colour (on the line, the odd sparkling pixel). The vertex is inserted into the edge, its texel coordinate
    interpolated along it, when it lies in the face's plane. faces: [(points (n, 3) integer native, uvs (n, 2) texels,
    material)]. Returns, for each face, the faces replacing it: itself with the vertices inserted, or, where the
    insertions would make it non-planar (`planar`: a vertex rounds up to a unit off its plane), triangles over its new
    ring (`triangles_over_ring`)."""
    normals, offsets = [], []
    grid = defaultdict(set)
    owners = defaultdict(set)
    for index, (points, _, _) in enumerate(faces):
        normal = np.cross(points, np.roll(points, -1, axis=0)).sum(axis=0).astype(float)
        length = np.linalg.norm(normal)
        normal = normal / length if length > 0 else normal
        normals.append(normal)
        offsets.append(float(normal @ points[0]))
        for point in points:
            key = tuple(int(v) for v in point)
            owners[key].add(index)
            grid[tuple(v // T_JUNCTION_CELL for v in key)].add(key)
    inserted = 0
    result = [[face] for face in faces]
    for index, (points, uvs, material) in enumerate(faces):
        normal = normals[index]
        own = {tuple(int(v) for v in point) for point in points}
        additions = defaultdict(list)       # edge -> [(t, point, uv)]
        for edge in range(len(points)):
            a, b = points[edge].astype(float), points[(edge + 1) % len(points)].astype(float)
            length = np.linalg.norm(b - a)
            if length < 1.0:
                continue
            direction = (b - a) / length
            low = np.floor((np.minimum(a, b) - T_JUNCTION_REACH) / T_JUNCTION_CELL).astype(int)
            high = np.floor((np.maximum(a, b) + T_JUNCTION_REACH) / T_JUNCTION_CELL).astype(int)
            for cx in range(low[0], high[0] + 1):
                for cy in range(low[1], high[1] + 1):
                    for cz in range(low[2], high[2] + 1):
                        for key in grid.get((cx, cy, cz), ()):
                            if key in own:
                                continue
                            relative = np.array(key, float) - a
                            t = float(relative @ direction)
                            if t <= 0.5 or t >= length - 0.5:
                                continue
                            if np.linalg.norm(relative - t * direction) > T_JUNCTION_REACH:
                                continue
                            # the vertex must be in this face's plane (within a unit), or inserting it would bend
                            # the face (the planarity check below catches the rest): a coplanar neighbour across the
                            # edge, or a face of another plane meeting it there (a wall standing on a floor's edge)
                            if abs(float(normal @ np.array(key, float)) - offsets[index]) > 1.0:
                                continue
                            share = t / length
                            uv = uvs[edge] + (uvs[(edge + 1) % len(points)] - uvs[edge]) * share
                            additions[edge].append((share, key, uv))
        if not additions:
            continue
        new_points, new_uvs = [], []
        for edge in range(len(points)):
            new_points.append(points[edge])
            new_uvs.append(uvs[edge])
            for share, key, uv in sorted(additions.get(edge, []), key=lambda item: item[0]):
                new_points.append(np.array(key, np.int64))
                new_uvs.append(uv)
        candidate = np.array(new_points, np.int64)
        count = sum(len(v) for v in additions.values())
        inserted += count
        if len(candidate) > 128 or not planar(candidate.astype(float)):
            # The vertex rounds up to a unit off the face's plane (or the ring grows too long): the face becomes
            # triangles over the new ring, each flat, which keep every ring vertex on their edges.
            result[index] = triangles_over_ring(points, uvs, candidate, np.array(new_uvs, float), material)
            stats["t_junction_faces_split"] += 1
            continue
        # Start again at the sharpest corner (face_rings): the compiler reads a face's type from its first three
        # vertices, which an inserted vertex right after the first would make collinear.
        total = len(candidate)
        sharp = max(range(total), key=lambda i: np.linalg.norm(np.cross(
            candidate[(i + 1) % total] - candidate[i], candidate[(i + 2) % total] - candidate[i])))
        order = [(sharp + k) % total for k in range(total)]
        result[index] = [(candidate[order], np.array(new_uvs, float)[order], material)]
    stats["t_junction_vertices_inserted"] += inserted
    return result


def triangles_over_ring(points: np.ndarray, uvs: np.ndarray, ring: np.ndarray, ring_uvs: np.ndarray,
                        material) -> list:
    """Triangles covering a convex face whose ring (`ring`, with T-junction vertices inserted into its edges) is no
    longer planar, each ring edge an edge of a triangle (a T-junction vertex must stay a vertex): a fan from a corner
    whose two edges gained no vertex (n - 2 triangles), else a fan from the face's middle (n triangles)."""
    count = len(ring)
    original = {tuple(int(v) for v in point) for point in points}
    corners = [i for i in range(count) if tuple(int(v) for v in ring[i]) in original]
    for origin in corners:
        before, after = ring[origin - 1], ring[(origin + 1) % count]
        if tuple(int(v) for v in before) not in original or tuple(int(v) for v in after) not in original:
            continue
        order = [(origin + k) % count for k in range(count)]
        fan = [[order[0], order[k], order[k + 1]] for k in range(1, count - 1)]
        if all(np.linalg.norm(np.cross(ring[b] - ring[a], ring[c] - ring[a])) >= 1.0 for a, b, c in fan):
            return [(ring[t], ring_uvs[t], material) for t in fan]
    # the middle, at a whole unit, its texel coordinate from the face's (affine) mapping
    middle = np.round(points.mean(0)).astype(np.int64)
    design = np.hstack([points.astype(float), np.ones((len(points), 1))])
    mapping, *_ = np.linalg.lstsq(design, uvs, rcond=None)
    middle_uv = np.append(middle.astype(float), 1.0) @ mapping
    triangles = []
    for i in range(count):
        j = (i + 1) % count
        corners3 = np.array([middle, ring[i], ring[j]])
        if np.linalg.norm(np.cross(corners3[1] - corners3[0], corners3[2] - corners3[0])) < 1.0:
            continue
        triangles.append((corners3, np.array([middle_uv, ring_uvs[i], ring_uvs[j]]), material))
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
    def __init__(self, source, generator: str = "mm9r_dungeon"):
        self.source = source
        self.project = source.project
        self.generator = generator
        self.nodes = defaultdict(list)          # node name -> [(points, uvs (texels), material)]
        self.materials = {}
        self.room_nodes = defaultdict(list)     # room id -> owned nodes
        self.metadata = {"format_version": 2, "kind": "indoor_geometry", "map_file": self.project.map,
                         "source": {"authoring_file": "convert.py", "asset_path": f"{self.project.stem}.glb",
                                    "coordinate_system": "blender_z_up", "unit_scale": 1.0,
                                    "import": {"source_format": "glb", "reserve_sector_zero": True,
                                               "merge_coplanar_faces": False, "triangulate_ngons": False,
                                               "generate_bsp": True, "generate_outlines": True}},
                         "materials": [], "rooms": [], "portals": [], "surfaces": [], "mechanisms": [],
                         "entities": [], "lights": [], "spawns": []}
        if self.project.overrides["map"].get("generate_bsp") is False:
            # The game draws, collides and paths without the BSP (only the BLV format carries it). Choosing a split
            # tests every face of a sector against every other: a region's open air in one sector (an MM9 outdoor
            # map, 25 000 faces) did not finish in half an hour (outdoor_blv.py).
            self.metadata["source"]["import"]["generate_bsp"] = False
        if self.project.overrides["map"].get("painted_minimap"):
            # Painted map only (the MM9 cities and regions, ../CITY_PLAYBOOK.md): the compiler makes no outlines, so
            # the save format's 7 000-outline bitset does not limit the map, and the Map style setting cannot pick a
            # line map. Every map has its painted map (tables.catalog_text); the dungeons keep their outlines.
            self.metadata["source"]["import"]["generate_outlines"] = False

    def material(self, texture: str) -> tuple[str, int, int]:
        alias = self.source.aliases[texture.lower()]
        key = alias["alias"]
        if key not in self.materials:
            self.materials[key] = (alias["width"], alias["height"])
            self.metadata["materials"].append({"id": key, "source_material": key, "texture": key,
                                               "texture_width": alias["width"], "texture_height": alias["height"]})
        return key, alias["width"], alias["height"]

    def marker_material(self) -> str:
        """The material of marker and portal faces (the first material; markers are not drawn)."""
        return next(iter(self.materials))

    def add_polygon(self, node: str, polygon: Polygon, stats: Counter) -> int:
        key, _, _ = self.material(polygon.texture)
        rings = face_rings(self.project, polygon.points, polygon.normal, polygon_uvs(polygon), stats)
        for points, uvs in rings:
            self.nodes[node].append((points, uvs, key))
        return len(rings)

    def add_raw(self, node: str, points_native: np.ndarray, material: str):
        self.nodes[node].append((points_native, np.zeros((len(points_native), 2)), material))

    def marker(self, node: str, position_native: np.ndarray, material: str):
        x, y, z = position_native
        self.add_raw(node, np.array([[x - 1, y - 1, z], [x + 1, y - 1, z], [x + 1, y + 1, z], [x - 1, y + 1, z]]),
                     material)

    def repair_t_junctions(self, stats: Counter) -> None:
        """T-junction repair (`repair_t_junctions`) over the drawn static faces: the rooms' and the glass nodes'."""
        drawn = [name for name in self.nodes if name.startswith(("ROOM_", "STATIC_", "TRIGGER_shared_", "TRIGGER_opaque_"))]
        faces = [face for name in drawn for face in self.nodes[name]]
        replacements = iter(repair_t_junctions(faces, stats))
        for name in drawn:
            self.nodes[name] = [new for _ in range(len(self.nodes[name])) for new in next(replacements)]

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
        write_glb(glb_path, nodes, self.generator)
        metadata_path.write_text(json.dumps(self.metadata, indent=1) + "\n")
