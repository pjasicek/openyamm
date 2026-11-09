"""
Polygon and voxel helpers for the Anskram Keep conversion (convert.py): the DAT polygon rings, coplanar merging,
plane clipping, the air voxel grid and its partition into rooms by portal rectangles, and a minimal GLB writer for
the indoor compiler. All geometry here is in LithTech units and axes (x, y up, z); convert.py maps it to the native
frame at the end.
"""

from __future__ import annotations

import json
import struct
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage


def poly_ring(poly) -> list[int]:
    """A v66 poly's vertex list holds its base ring followed by the same ring with the T-junction vertices added
    (the reader sums the two counts). Return the second ring when present: it is watertight against its neighbours."""
    indices = [vertex.vertex_index for vertex in poly.disk_verts]
    count = len(indices)
    for split in range(3, count - 2):
        if indices[split] == indices[0] and set(indices[split:]) >= set(indices[:split]):
            return indices[split:]
    return indices


def newell(points: np.ndarray) -> np.ndarray:
    """The area-weighted normal of a ring (right-handed in the given axes; a DAT ring gives its front this way)."""
    rolled = np.roll(points, -1, axis=0)
    return np.cross(points, rolled).sum(axis=0) / 2.0


@dataclass
class Polygon:
    """One convex polygon: a ring of points (LithTech units), its front normal, its surface mapping and content."""
    points: np.ndarray                      # (n, 3)
    keys: list                              # per-point identity, so shared vertices stay shared through merging
    texture: str                            # the MM9 source texture path
    mapping: tuple                          # (origin, axis_u, axis_v) in LithTech units
    flags: int
    model: str
    role: str                               # static, invisible, nonsolid
    label: int = -1
    notes: dict = field(default_factory=dict)

    @property
    def normal(self) -> np.ndarray:
        n = newell(self.points)
        length = np.linalg.norm(n)
        return n / length if length > 1e-9 else n

    @property
    def area(self) -> float:
        return float(np.linalg.norm(newell(self.points)))


# --- Coplanar merging -----------------------------------------------------------------------------------------------

def _convex(points: np.ndarray, normal: np.ndarray, tolerance: float = 1e-3) -> bool:
    count = len(points)
    for index in range(count):
        a, b, c = points[index - 1], points[index], points[(index + 1) % count]
        turn = np.cross(b - a, c - b) @ normal
        if turn < -tolerance * max(np.linalg.norm(b - a) * np.linalg.norm(c - b), 1e-9):
            return False
    return True


def _splice(a: Polygon, b: Polygon) -> Polygon | None:
    """The union of two rings that share one contiguous chain of edges (b runs the chain backwards), if convex."""
    ka, kb = a.keys, b.keys
    na, nb = len(ka), len(kb)
    edges_b = {(kb[i], kb[(i + 1) % nb]): i for i in range(nb)}
    shared = [i for i in range(na) if (ka[(i + 1) % na], ka[i]) in edges_b]
    if not shared or len(shared) >= na - 1:
        return None
    shared_set = set(shared)
    # The chain's first edge: shared, its predecessor not.
    starts = [i for i in shared if (i - 1) % na not in shared_set]
    if len(starts) != 1:
        return None
    start = starts[0]
    length = 1
    while (start + length) % na in shared_set:
        length += 1
    if length != len(shared):
        return None
    chain_first, chain_last = start, (start + length) % na          # vertex indices in a
    # In b the chain runs from a[chain_last] to a[chain_first].
    b_first = kb.index(ka[chain_last])
    b_last = kb.index(ka[chain_first])
    ring_keys, ring_points = [], []
    index = chain_last
    while True:
        ring_keys.append(ka[index])
        ring_points.append(a.points[index])
        if index == chain_first:
            break
        index = (index + 1) % na
    index = (b_last + 1) % nb
    while index != b_first:
        ring_keys.append(kb[index])
        ring_points.append(b.points[index])
        index = (index + 1) % nb
    if len(set(ring_keys)) != len(ring_keys):
        return None
    points = np.array(ring_points)
    normal = a.normal
    if not _convex(points, normal):
        return None
    return Polygon(points, ring_keys, a.texture, a.mapping, a.flags, a.model, a.role, notes=dict(a.notes))


def merge_coplanar(polygons: list[Polygon]) -> list[Polygon]:
    """Merge BSP fragments back into larger convex polygons: polygons of one model, texture, mapping, flags and plane
    that share a chain of edges, while the union stays convex."""
    groups = defaultdict(list)
    for polygon in polygons:
        normal = polygon.normal
        distance = normal @ polygon.points[0]
        origin, axis_u, axis_v = polygon.mapping
        key = (polygon.model, polygon.texture, polygon.flags, polygon.role,
               tuple(np.round(normal, 3)), round(distance, 1),
               tuple(np.round(axis_u, 4)), tuple(np.round(axis_v, 4)),
               round(float(np.dot(origin, axis_u)) % polygon.notes.get("width", 1e9), 1),
               round(float(np.dot(origin, axis_v)) % polygon.notes.get("height", 1e9), 1))
        groups[key].append(polygon)
    result = []
    for members in groups.values():
        members = list(members)
        alive = [True] * len(members)

        def edges(polygon):
            count = len(polygon.keys)
            return [frozenset((polygon.keys[i], polygon.keys[(i + 1) % count])) for i in range(count)]

        by_edge = defaultdict(set)
        for index, polygon in enumerate(members):
            for edge in edges(polygon):
                by_edge[edge].add(index)
        changed = True
        while changed:
            changed = False
            for index in range(len(members)):
                if not alive[index]:
                    continue
                grew = True
                while grew:
                    grew = False
                    neighbours = set()
                    for edge in edges(members[index]):
                        neighbours |= by_edge[edge]
                    for other in sorted(neighbours - {index}):
                        if not alive[other]:
                            continue
                        union = _splice(members[index], members[other]) or _splice(members[other], members[index])
                        if union is None:
                            continue
                        alive[other] = False
                        members[index] = union
                        for edge in edges(union):
                            by_edge[edge].add(index)
                        grew = changed = True
                        break
        result.extend(polygon for polygon, keep in zip(members, alive) if keep)
    return result


def drop_unshared_collinear(polygons: list[Polygon], tolerance: float = 0.05) -> int:
    """Remove ring vertices that lie on a straight edge and belong to no other polygon (left over from merging)."""
    usage = defaultdict(int)
    for polygon in polygons:
        for key in polygon.keys:
            usage[key] += 1
    removed = 0
    for polygon in polygons:
        keep = []
        count = len(polygon.keys)
        for index in range(count):
            a, b, c = polygon.points[index - 1], polygon.points[index], polygon.points[(index + 1) % count]
            straight = np.linalg.norm(np.cross(b - a, c - b)) <= tolerance * max(np.linalg.norm(c - a), 1e-9)
            keep.append(not (straight and usage[polygon.keys[index]] <= 1))
        if not all(keep) and sum(keep) >= 3:
            polygon.points = polygon.points[np.array(keep)]
            polygon.keys = [key for key, kept in zip(polygon.keys, keep) if kept]
            removed += count - sum(keep)
    return removed


# --- Clipping -------------------------------------------------------------------------------------------------------

def clip(polygon: Polygon, normal: np.ndarray, distance: float, key_prefix: str) -> tuple[Polygon | None, Polygon | None]:
    """Split a convex polygon by the plane normal . p = distance into its front and back parts."""
    side = polygon.points @ normal - distance
    if (side >= -0.01).all() or (side <= 0.01).all():
        return (polygon, None) if side.sum() >= 0 else (None, polygon)
    front, back = ([], []), ([], [])
    count = len(polygon.points)
    for index in range(count):
        j = (index + 1) % count
        p, q, sp, sq = polygon.points[index], polygon.points[j], side[index], side[j]
        if sp >= -0.01:
            front[0].append(p); front[1].append(polygon.keys[index])
        if sp <= 0.01:
            back[0].append(p); back[1].append(polygon.keys[index])
        if (sp > 0.01 and sq < -0.01) or (sp < -0.01 and sq > 0.01):
            t = sp / (sp - sq)
            point = p + (q - p) * t
            key = (key_prefix, tuple(np.round(point, 2)))
            front[0].append(point); front[1].append(key)
            back[0].append(point); back[1].append(key)

    def make(part):
        if len(part[0]) < 3:
            return None
        made = Polygon(np.array(part[0]), part[1], polygon.texture, polygon.mapping, polygon.flags, polygon.model,
                       polygon.role, notes=dict(polygon.notes))
        return made if made.area > 1.0 else None
    return make(front), make(back)


# --- Voxels ---------------------------------------------------------------------------------------------------------

class VoxelGrid:
    def __init__(self, low, high, size):
        self.size = float(size)
        self.origin = np.floor(np.asarray(low, float) / size) * size - 2 * size
        self.shape = tuple(int(v) for v in np.ceil((np.asarray(high, float) - self.origin) / size) + 2)

    def index(self, points: np.ndarray) -> np.ndarray:
        cells = np.floor((points - self.origin) / self.size).astype(np.int64)
        return np.clip(cells, 0, np.array(self.shape) - 1)

    def centre(self, cells: np.ndarray) -> np.ndarray:
        return self.origin + (cells + 0.5) * self.size


def sample_polygon(points: np.ndarray, spacing: float) -> np.ndarray:
    """Points over a convex polygon (fan triangles sampled on a barycentric grid) at about `spacing`."""
    samples = []
    for index in range(1, len(points) - 1):
        a, b, c = points[0], points[index], points[index + 1]
        steps = max(1, int(np.ceil(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b))
                                   / spacing)))
        i, j = np.meshgrid(np.arange(steps + 1), np.arange(steps + 1), indexing="ij")
        mask = (i + j) <= steps
        u, v = i[mask] / steps, j[mask] / steps
        samples.append(a + np.outer(u, b - a) + np.outer(v, c - a))
    return np.concatenate(samples) if samples else np.zeros((0, 3))


def mark(grid: VoxelGrid, volume: np.ndarray, points: np.ndarray) -> None:
    cells = grid.index(points)
    volume[cells[:, 0], cells[:, 1], cells[:, 2]] = True


SIX = ndimage.generate_binary_structure(3, 1)


def air_regions(grid: VoxelGrid, solid: np.ndarray, seeds: np.ndarray) -> tuple[np.ndarray, dict]:
    """The air reachable from the seed points (6-connected empty voxels)."""
    labels, count = ndimage.label(~solid, structure=SIX)
    seed_cells = grid.index(seeds)
    seed_labels = set(int(v) for v in labels[seed_cells[:, 0], seed_cells[:, 1], seed_cells[:, 2]]) - {0}
    air = np.isin(labels, list(seed_labels))
    border = np.zeros_like(air)
    border[[0, -1], :, :] = border[:, [0, -1], :] = border[:, :, [0, -1]] = True
    leaked = bool((air & border).any())
    return air, {"air_components_seeded": len(seed_labels), "air_voxels": int(air.sum()), "leaked_to_border": leaked}


def rectangle_points(centre, axis_a, half_a, axis_b, half_b, spacing):
    a = np.linspace(-half_a, half_a, max(2, int(np.ceil(2 * half_a / spacing)) + 1))
    b = np.linspace(-half_b, half_b, max(2, int(np.ceil(2 * half_b / spacing)) + 1))
    aa, bb = np.meshgrid(a, b, indexing="ij")
    return np.asarray(centre) + np.outer(aa.ravel(), axis_a) + np.outer(bb.ravel(), axis_b)


# --- GLB ------------------------------------------------------------------------------------------------------------

def write_glb(path, nodes: list[dict]) -> None:
    """nodes: {'name', 'primitives': [{'material', 'positions' (n,3), 'uvs' (n,2), 'indices' (m,)}]}; positions are
    written as given (Z up, native units), one mesh per node, one primitive per material."""
    materials, material_index = [], {}
    binary = bytearray()
    buffer_views, accessors, meshes, gltf_nodes = [], [], [], []

    def add_view(data: bytes, target: int) -> int:
        while len(binary) % 4:
            binary.append(0)
        buffer_views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data), "target": target})
        binary.extend(data)
        return len(buffer_views) - 1

    for node in nodes:
        primitives = []
        for primitive in node["primitives"]:
            name = primitive["material"]
            if name not in material_index:
                material_index[name] = len(materials)
                materials.append({"name": name})
            positions = np.asarray(primitive["positions"], np.float32)
            uvs = np.asarray(primitive["uvs"], np.float32)
            indices = np.asarray(primitive["indices"], np.uint32)
            view = add_view(positions.tobytes(), 34962)
            accessors.append({"bufferView": view, "componentType": 5126, "count": len(positions), "type": "VEC3",
                              "min": positions.min(0).tolist(), "max": positions.max(0).tolist()})
            position_accessor = len(accessors) - 1
            view = add_view(uvs.tobytes(), 34962)
            accessors.append({"bufferView": view, "componentType": 5126, "count": len(uvs), "type": "VEC2"})
            uv_accessor = len(accessors) - 1
            view = add_view(indices.tobytes(), 34963)
            accessors.append({"bufferView": view, "componentType": 5125, "count": len(indices), "type": "SCALAR"})
            primitives.append({"attributes": {"POSITION": position_accessor, "TEXCOORD_0": uv_accessor},
                               "indices": len(accessors) - 1, "material": material_index[name],
                               "mode": primitive.get("mode", 4)})
        meshes.append({"name": node["name"], "primitives": primitives})
        gltf_nodes.append({"name": node["name"], "mesh": len(meshes) - 1})
    while len(binary) % 4:
        binary.append(0)
    document = {"asset": {"version": "2.0", "generator": "mm9r_anskramkeep"}, "scene": 0,
                "scenes": [{"nodes": list(range(len(gltf_nodes)))}], "nodes": gltf_nodes, "meshes": meshes,
                "materials": materials, "accessors": accessors, "bufferViews": buffer_views,
                "buffers": [{"byteLength": len(binary)}]}
    text = json.dumps(document, separators=(",", ":")).encode()
    while len(text) % 4:
        text += b" "
    total = 12 + 8 + len(text) + 8 + len(binary)
    with open(path, "wb") as stream:
        stream.write(struct.pack("<III", 0x46546C67, 2, total))
        stream.write(struct.pack("<II", len(text), 0x4E4F534A))
        stream.write(text)
        stream.write(struct.pack("<II", len(binary), 0x004E4942))
        stream.write(bytes(binary))
