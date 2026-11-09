#!/usr/bin/env python3
"""
Isle of Ashes, MM9 rework: convert the original DAT world into a native OpenYAMM ODM in the review root.

This first stage converts the terrain only: heights resampled from MM9's terrain world models onto the 128x128 grid,
one native tile per cell from the MM9 terrain texture that covers it, the sea as water and shore tiles, the ground
material weights, and a report of where the coarse grid changes what the party can walk on. The seabed below sea level is kept in work/ for a later
diving decision. Writes the editor source package to source/, builds the ODM with the editor and installs the map
into output/mm9_rework/assets_dev (see ../mm9r_common/review_root.py); assets_dev itself is never written.

    python3 level_generation/projects/mm9r_isleofashes/convert.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, deque
from pathlib import Path

import numpy as np
import yaml
from PIL import Image
from scipy import ndimage

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
sys.path.insert(0, str(ROOT / "tools/mm9_import_discovery"))
sys.path.insert(0, str(PROJECT.parent / "mm9r_common"))
sys.path.insert(0, str(ROOT))
import review_root  # noqa: E402
import story as isle_story  # noqa: E402
from dungeon.tables import locked  # noqa: E402
from mm9_units import MM9_TO_OPENYAMM_COORDINATE_SCALE as SCALE  # noqa: E402
from transcode_mm9_dat_to_odm import read_dat_world  # noqa: E402
from util.map_export import parse_odm_file  # noqa: E402

MAP = "isleofashes.odm"
STEM = "isleofashes"
DAT = ROOT / "mm9/extracted/WORLDS/WORLDS/ISLEOFASHES.dat"
SOURCE = PROJECT / "source"
WORK = PROJECT / "work"
MAP_STATS_ID = 9021

GRID = 128
CELL = 512
HEIGHT_STEP = 32
FINE = 64                       # fine raster step; 8 x 8 samples per cell
FINE_PER_CELL = CELL // FINE
HALF = GRID * CELL // 2         # the grid spans [-HALF, HALF)
PARTY_BOUND = 22528             # OutdoorWorldRuntime's party bounds
LAND_ABOVE_SEA = 16             # a sample counts as land this far above the sea
NODE_REACH = 128                # a node is dry when land lies within this distance of it
ROUTE_FIX_PASSES = 6
ROUTE_SPREAD = 480              # a softened route cell's corner spread (cells slide above 512)
PATH_SHARE = 0.2                # a cell is on an MM9 route when this share of it is MM9-walkable (a 128-wide path)

WATER_MODEL_PREFIXES = ("bluewater", "clearwater", "ocean", "water")
HELPER_MODELS = {"visbsp", "physicsbsp"}

# The MM8 tile table (the world's terrain_tile_data.txt): four tilesets through the lookups, raw id 90 + 36 * set +
# offset, offset 0 the base tile and 12-23 the ground-over-dirt transitions (the water set's are its shore tiles);
# dirt is direct id 1. Set 3 (volcanic) is unused here.
LOOKUPS = [90, 342, 198, 126]   # grass, rock, volcanic, water
TILE = {"grass": 90, "rock": 126, "dirt": 1, "water": 198}
SHORE_EDGE = {"S": 216, "N": 217, "W": 214, "E": 215}      # wtrdr*: water on that side of the land cell
SHORE_INNER = {"SW": 218, "NW": 219, "SE": 220, "NE": 221}
SHORE_OUTER = {"SW": 210, "NW": 211, "SE": 212, "NE": 213}

# MM9 terrain textures to native grounds. The isle's "ash" set is tan rock, green scrub and grass, not black ash.
GROUND = {
    "ashcliff": "rock", "ashrock2": "rock", "nwrock": "rock",
    "ashrock": "grass", "maingrass": "grass",
    "ashdirt3": "dirt",
}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


# --- Source geometry ------------------------------------------------------------------------------------------------

def load_terrain():
    world = read_dat_world(DAT)
    triangles, textures, names = [], [], []
    sea_level = None
    for model in world.world_models:
        name = model.name.lower()
        if name.startswith(WATER_MODEL_PREFIXES):
            sea_level = model.max_box[1] if sea_level is None else min(sea_level, model.max_box[1])
            continue
        if name in HELPER_MODELS:
            continue
        for poly in model.polies:
            texture = model.textures[model.surfaces[poly.surface_index].texture_index].replace("\\", "/").lower()
            if "/terrain/" not in texture:
                continue
            stem = texture.rsplit("/", 1)[-1].rsplit(".", 1)[0]
            if stem not in names:
                names.append(stem)
            points = [model.points[vertex.vertex_index] for vertex in poly.disk_verts]
            for index in range(1, len(points) - 1):
                triangles.append((points[0], points[index], points[index + 1]))
                textures.append(names.index(stem))
    triangles = np.array(triangles, dtype=np.float64)
    x = triangles[:, :, 0] * SCALE
    y = triangles[:, :, 2] * SCALE
    z = (triangles[:, :, 1] - sea_level) * SCALE
    # Centre the terrain on the grid, on a cell boundary so the conversion stays aligned with the cells.
    offset_x = round((x.min() + x.max()) / 2 / CELL) * CELL
    offset_y = round((y.min() + y.max()) / 2 / CELL) * CELL
    transform = {"scale": SCALE, "sea_level_lt": sea_level, "offset_x": offset_x, "offset_y": offset_y,
                 "note": "x = LT.x * scale - offset_x, y = LT.z * scale - offset_y, z = (LT.y - sea_level) * scale"}
    return x - offset_x, y - offset_y, z, np.array(textures), names, transform


def rasterize(x, y, z, texture, origin_x, origin_y, step, size):
    """Top surface over a size x size grid of points (origin_x + step * column, origin_y - step * row): height,
    texture index and the count and lowest height of all surfaces at each point."""
    top = np.full((size, size), -1e9)
    low = np.full((size, size), 1e9)
    count = np.zeros((size, size), np.int16)
    top_texture = np.full((size, size), -1, np.int16)
    for tx, ty, tz, tex in zip(x, y, z, texture):
        denominator = (ty[1] - ty[2]) * (tx[0] - tx[2]) + (tx[2] - tx[1]) * (ty[0] - ty[2])
        if abs(denominator) < 1e-6:
            continue
        c0 = max(int(np.floor((tx.min() - origin_x) / step)), 0)
        c1 = min(int(np.ceil((tx.max() - origin_x) / step)), size - 1)
        r0 = max(int(np.floor((origin_y - ty.max()) / step)), 0)
        r1 = min(int(np.ceil((origin_y - ty.min()) / step)), size - 1)
        if c0 > c1 or r0 > r1:
            continue
        gx, gy = np.meshgrid(origin_x + step * np.arange(c0, c1 + 1), origin_y - step * np.arange(r0, r1 + 1))
        a = ((ty[1] - ty[2]) * (gx - tx[2]) + (tx[2] - tx[1]) * (gy - ty[2])) / denominator
        b = ((ty[2] - ty[0]) * (gx - tx[2]) + (tx[0] - tx[2]) * (gy - ty[2])) / denominator
        c = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if not inside.any():
            continue
        height = a * tz[0] + b * tz[1] + c * tz[2]
        window = (slice(r0, r1 + 1), slice(c0, c1 + 1))
        higher = inside & (height > top[window])
        top[window] = np.where(higher, height, top[window])
        top_texture[window] = np.where(higher, tex, top_texture[window])
        low[window] = np.where(inside, np.minimum(low[window], height), low[window])
        count[window] += inside
    return top, top_texture, low, count


# --- Water and shores -----------------------------------------------------------------------------------------------

def coast(dry):
    """Water and shore tiles from which nodes are dry (rows run north to south; a cell's corners are NW (r, c),
    NE (r, c + 1), SW (r + 1, c), SE (r + 1, c + 1)). The native shore tiles say where in a cell the water lies:
    four wet corners are water, two adjacent ones an edge (wtrdrN: water to the south), three an inner corner (water
    on two sides), one an outer corner. Two wet corners on a diagonal have no tile: the wet node with the most dry
    neighbours becomes dry, repeated until none is left. Returns the adjusted dry nodes, the water cells and the
    shore tiles (0 elsewhere)."""
    dry = dry.copy()
    while True:
        nw, ne, sw, se = ~dry[:-1, :-1], ~dry[:-1, 1:], ~dry[1:, :-1], ~dry[1:, 1:]       # wet corners per cell
        diagonal = ((nw & se & ~ne & ~sw) | (ne & sw & ~nw & ~se))
        if not diagonal.any():
            break
        neighbours = ndimage.convolve(dry.astype(int), np.ones((3, 3), int), mode="constant") - dry
        candidates = np.zeros(dry.shape, bool)
        for r, c in zip(*np.nonzero(diagonal)):
            corners = [(r + dr, c + dc) for dr in (0, 1) for dc in (0, 1) if not dry[r + dr, c + dc]]
            best = max(corners, key=lambda node: neighbours[node])
            candidates[best] = True
        dry |= candidates
    nw, ne, sw, se = ~dry[:-1, :-1], ~dry[:-1, 1:], ~dry[1:, :-1], ~dry[1:, 1:]
    wet_count = nw.astype(int) + ne + sw + se
    water = np.zeros((GRID, GRID), bool)
    water[:-1, :-1] = wet_count == 4
    shore = np.zeros((GRID, GRID), np.uint8)
    cells = shore[:-1, :-1]
    for side, (a, b) in {"S": (sw, se), "N": (nw, ne), "W": (nw, sw), "E": (ne, se)}.items():
        cells[(wet_count == 2) & a & b] = SHORE_EDGE[side]
    for corner, land in {"SW": ne, "SE": nw, "NW": se, "NE": sw}.items():     # three wet: the dry corner opposite
        cells[(wet_count == 3) & ~land] = SHORE_INNER[corner]
    for corner, wet in {"SW": sw, "NW": nw, "SE": se, "NE": ne}.items():
        cells[(wet_count == 1) & wet] = SHORE_OUTER[corner]
    water[-1, :] = water[:, -1] = True                     # the last row and column have no cell of their own
    return dry, water, shore


# --- Gating ---------------------------------------------------------------------------------------------------------

def gating_report(fine_top, fine_land, heights, water):
    """Compare what the party can walk on in MM9 (slope under 50 degrees at a 128-unit scale; MM9's navigation limit
    is 49.5) with the native grid (a cell slides when its corners differ by more than 512), inside the party bounds."""
    size = fine_top.shape[0]
    centres = -HALF + FINE / 2 + FINE * np.arange(size)
    inside = (np.abs(centres)[None, :] <= PARTY_BOUND) & (np.abs(centres)[:, None] <= PARTY_BOUND)
    land = fine_land & inside
    smooth = ndimage.uniform_filter(np.where(fine_land, fine_top, 0.0), 2)
    gradient_r, gradient_c = np.gradient(smooth, FINE)
    slope = np.degrees(np.arctan(np.hypot(gradient_r, gradient_c)))
    mm9_walk = ndimage.binary_opening(land & (slope < 50), iterations=1)
    corners = np.stack([heights[:-1, :-1], heights[1:, :-1], heights[:-1, 1:], heights[1:, 1:]])
    cell_walk = ((corners.max(0) - corners.min(0)) <= CELL) & ~water[:-1, :-1]
    cell_walk = np.pad(cell_walk, ((0, 1), (0, 1)))
    native_walk = np.kron(cell_walk, np.ones((FINE_PER_CELL, FINE_PER_CELL), bool))[:size, :size] & land
    opened = land & ~mm9_walk & native_walk
    closed = mm9_walk & ~native_walk

    def spots(mask, minimum):
        labels, count = ndimage.label(mask, structure=np.ones((3, 3)))
        found = []
        for index, (sl, size_px) in enumerate(zip(ndimage.find_objects(labels),
                                                  ndimage.sum(mask, labels, range(1, count + 1))), start=1):
            if size_px * FINE * FINE < minimum:
                continue
            rows, columns = np.nonzero(labels[sl] == index)
            found.append({"x": int(centres[int(columns.mean()) + sl[1].start]),
                          "y": int(-centres[int(rows.mean()) + sl[0].start]),
                          "area": int(size_px * FINE * FINE)})
        return sorted(found, key=lambda spot: -spot["area"])

    # Closed spots matter when they cut through MM9 walkable ground: report those with MM9 walkable ground on two
    # sides, i.e. at least a cell's worth.
    report = {"mm9_blocked_share": float((land & ~mm9_walk).sum() / max(land.sum(), 1)),
              "opened_share_of_blocked": float(opened.sum() / max((land & ~mm9_walk).sum(), 1)),
              "opened": spots(opened, CELL * CELL), "closed": spots(closed, CELL * CELL)}
    # Routes, per cell: a closed spot matters where it splits one MM9 walkable area into separate native parts (the
    # cells to fix are the slide cells touching two parts), an opened one where a native walkable area joins two MM9
    # areas (the cells are the ones that are steep in MM9 and touch both). Terrain only: bridges, stairs and floors of
    # the structures are not counted, so each entry is a candidate to check, not a defect.
    def cell_of(mask, share=0.5):
        return mask[:GRID * FINE_PER_CELL, :GRID * FINE_PER_CELL].reshape(
            GRID, FINE_PER_CELL, GRID, FINE_PER_CELL).mean(axis=(1, 3)) >= share

    # Each MM9 walkable component on its own (8-connected at the fine step): a cell belongs to it when PATH_SHARE of
    # the cell is that component, so narrow paths (switchbacks, ledges up a slope) count, and a cell holding a hill
    # path above a valley floor belongs to both, each with its own heights.
    fine_labels, fine_count = ndimage.label(mm9_walk, structure=np.ones((3, 3)))
    mm9_cells = np.zeros((GRID, GRID), bool)
    native_cells = cell_walk[:GRID, :GRID] & cell_of(land | native_walk)
    spread = np.pad(corners.max(0) - corners.min(0), ((0, 1), (0, 1)))
    neighbours = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def touching(labels, row, column):
        return {labels[row + dr, column + dc] for dr, dc in neighbours
                if 0 <= row + dr < GRID and 0 <= column + dc < GRID and labels[row + dr, column + dc]}

    def where(row, column):
        return {"x": int(column * CELL - HALF + CELL / 2), "y": int(HALF - row * CELL - CELL / 2)}

    cuts, cut_cells = [], set()
    for component, box in enumerate(ndimage.find_objects(fine_labels), start=1):
        cells = cell_of(np.pad(fine_labels[box] == component,
                               ((box[0].start, size - box[0].stop), (box[1].start, size - box[1].stop))), PATH_SHARE)
        mm9_cells |= cells
        if cells.sum() < 4:
            continue
        parts, count = ndimage.label(native_cells & cells)
        if count < 2:
            continue
        # Each smaller part joins the largest by the shortest chain of the component's cells; the slide cells on
        # that chain are the cut (a break can be several cells long: a path up a slope to a plateau).
        sizes = ndimage.sum(np.ones_like(parts), parts, range(1, count + 1))
        main = int(np.argmax(sizes)) + 1
        parent = {(int(r), int(c)): None for r, c in zip(*np.nonzero(parts == main))}
        queue = deque(parent)
        while queue:
            row, column = queue.popleft()
            for dr, dc in neighbours:
                step = (row + dr, column + dc)
                if 0 <= step[0] < GRID and 0 <= step[1] < GRID and cells[step] and step not in parent:
                    parent[step] = (row, column)
                    queue.append(step)
        for part in range(1, count + 1):
            if part == main or sizes[part - 1] < 2:
                continue
            reached = [(int(r), int(c)) for r, c in zip(*np.nonzero(parts == part)) if (r, c) in parent]
            node = reached[0] if reached else None
            while node is not None:
                if not native_cells[node] and node not in cut_cells:
                    cut_cells.add(node)
                    cuts.append({**where(*node), "corner_spread": int(spread[node]), "component": component})
                node = parent[node]
    mm9_labels, mm9_count = ndimage.label(mm9_cells)
    native_labels, native_count = ndimage.label(native_cells)
    joins = []
    for row, column in zip(*np.nonzero(native_cells & ~mm9_cells)):
        areas = {area for area in touching(mm9_labels, row, column) if (mm9_labels == area).sum() >= 4}
        if len(areas) >= 2:
            joins.append(where(row, column))
    report["route_cuts"] = cuts
    report["route_joins"] = joins

    image = np.zeros(land.shape + (3,), np.uint8)
    image[:] = (20, 40, 90)
    image[fine_land] = (70, 70, 70)
    image[mm9_walk] = (60, 140, 60)
    image[opened] = (230, 40, 40)
    image[closed] = (250, 170, 30)
    for marks, colour in ((cuts, (255, 0, 255)), (joins, (0, 255, 255))):
        for mark in marks:
            row = int((HALF - mark["y"]) // CELL) * FINE_PER_CELL
            column = int((mark["x"] + HALF) // CELL) * FINE_PER_CELL
            image[row:row + FINE_PER_CELL, column:column + FINE_PER_CELL] = colour
    return report, image, fine_labels


PAINTED_MAP = ROOT / "assets_dev/worlds/mm9/ui/maps/isleofashes.pcx"
MAP_CATALOG = ROOT / "assets_dev/worlds/mm9/ui/maps/catalog.yml"
TRAIL_VALUE = 180               # painted map pixels this bright (any channel) are trails or open ground; rock is darker


def painted_trails(transform):
    """MM9's painted map (the minimap art, with its world bounds in the old map's frame) resampled onto the fine
    samples: True where the art is pale (paths, beaches, plazas). About 120 units per art pixel, so it marks the
    trail's neighbourhood; the walkable samples inside it find the trail itself."""
    entry = next(e for e in yaml.safe_load(MAP_CATALOG.read_text())["maps"] if e["map"] == STEM)
    bounds = entry["world_bounds"]
    art = np.asarray(Image.open(PAINTED_MAP).convert("RGB"))
    height, width = art.shape[:2]
    shift = frame_shift(transform)
    x = -HALF + FINE / 2 + FINE * np.arange(GRID * FINE_PER_CELL) + shift[0]
    y = HALF - FINE / 2 - FINE * np.arange(GRID * FINE_PER_CELL) + shift[1]
    u = (x - bounds["min_x"]) / (bounds["max_x"] - bounds["min_x"])
    v = (y - bounds["min_y"]) / (bounds["max_y"] - bounds["min_y"])
    u = 1 - u if entry.get("flip_u") else u
    v = 1 - v if entry.get("flip_v") else v
    columns = np.clip((u * width).astype(int), 0, width - 1)
    rows = np.clip((v * height).astype(int), 0, height - 1)
    return art.max(axis=2)[rows[:, None], columns[None, :]] >= TRAIL_VALUE


def route_cell_targets(row, column, fine_top, path):
    """The corner heights (2 x 2) that carry an MM9 path across a cell: the cell's path samples (a fine mask: one
    walkable component, or the painted trail) give the path's direction (principal axis) and its rise along it; the
    corners take the path's height there, level across the path, so the cell becomes a ramp and its neighbours take
    the hillside. None when too few samples."""
    r, c = row * FINE_PER_CELL, column * FINE_PER_CELL
    walk = path[r:r + FINE_PER_CELL, c:c + FINE_PER_CELL]
    rows, columns = np.nonzero(walk)
    if rows.size < 3:
        return None
    xs = (c + columns) * FINE - HALF + FINE / 2
    ys = HALF - FINE / 2 - (r + rows) * FINE
    zs = fine_top[r:r + FINE_PER_CELL, c:c + FINE_PER_CELL][walk]
    centre = np.array([xs.mean(), ys.mean()])
    offsets = np.stack([xs, ys], 1) - centre
    axis = np.linalg.eigh(offsets.T @ offsets)[1][:, -1]
    along = offsets @ axis
    rise = np.polyfit(along, zs, 1)[0] if np.ptp(along) > FINE else 0.0
    corner_x = np.array([[0, CELL], [0, CELL]]) + column * CELL - HALF
    corner_y = HALF - np.array([[0, 0], [CELL, CELL]]) - row * CELL
    return zs.mean() + rise * ((corner_x - centre[0]) * axis[0] + (corner_y - centre[1]) * axis[1])


def grade_routes(base, routes, pinned):
    """Node heights with every route cell walkable, solved together so neighbouring route cells do not undo each
    other: route nodes start at the mean of their cells' path targets, then each route cell's corners are pulled into
    a ROUTE_SPREAD window around their mean (pinned nodes, which carry structure floors and foundations, stay put and
    the window moves to include them), repeated until it settles. routes maps (row, column) to its 2 x 2 targets."""
    heights = base.copy()
    total = np.zeros_like(base)
    count = np.zeros_like(base)
    for (row, column), target in routes.items():
        total[row:row + 2, column:column + 2] += target
        count[row:row + 2, column:column + 2] += 1
    free = (count > 0) & ~pinned
    heights[free] = total[free] / count[free]
    for _ in range(200):
        moved = 0.0
        for row, column in routes:
            block = heights[row:row + 2, column:column + 2]
            fixed = pinned[row:row + 2, column:column + 2]
            if block.max() - block.min() <= ROUTE_SPREAD:
                continue
            low = block.mean() - ROUTE_SPREAD / 2
            if fixed.any():
                low = np.clip(low, block[fixed].max() - ROUTE_SPREAD, block[fixed].min())
            clipped = np.where(fixed, block, np.clip(block, low, low + ROUTE_SPREAD))
            moved = max(moved, float(np.abs(clipped - block).max()))
            block[:] = clipped
        if moved < 1:
            break
    return np.clip(heights, LAND_ABOVE_SEA * 2, 255 * HEIGHT_STEP)


# --- Structures -----------------------------------------------------------------------------------------------------

# The current imported map (generated by transcode_mm9_dat_to_odm.py) holds every DAT world model as a BModel with
# 10-character texture aliases and texel UVs; the structures are taken from it and moved into this map's frame.
OLD_MAP = ROOT / "assets_editor_dev/worlds/mm9/maps/isleofashes.odm"
ALIASES = ROOT / "assets_editor_dev/worlds/mm9/maps/isleofashes.material_aliases.yml"
TEXTURES = ROOT / "assets_editor_dev/worlds/mm9/textures"
# World models that are structures: all their faces count (invisible ones become collision). The world models the
# story scripts move or destroy (story.SCRIPTED_MODELS: the bunker doors, the hut door, the fort walls) are BModels of
# their own instead (scripted_models()).
STRUCTURE_PREFIXES = ("physicsbsp", "fortwall", "worldobject")
# Terrain world models also carry walls (Terrain3's fort wall); their non-terrain faces are structure.
TERRAIN_PREFIXES = ("terrain", "earthquake")
FACE_INVISIBLE = 0x2000
INVISIBLE_TEXTURE = "ASHRPOKF0H"   # any loaded texture: the collision faces are drawn nowhere (FaceAttribute::Invisible)
OBJ_SCALE = 128.0
VERTEX_TOLERANCE = 8            # faces with vertices this close belong to one BModel
FOUNDATION_BAND = 48            # a structure's vertices this close to its lowest point form its foundation
FLOOR_NORMAL = 0.7              # an upward face this level is a floor
FLOOR_CLEARANCE = 8             # our terrain stays this far under a floor MM9 shows


def texture_sizes() -> dict[str, tuple[int, int]]:
    sizes = {}
    for path in TEXTURES.glob("*.bmp"):
        header = path.read_bytes()[:26]
        sizes[path.stem.upper()] = (int.from_bytes(header[18:22], "little", signed=True),
                                    abs(int.from_bytes(header[22:26], "little", signed=True)))
    return sizes


def structure_faces(transform):
    """The structure faces of the old map in this map's frame: (points, uvs, texture, invisible, source model)."""
    aliases = yaml.load(ALIASES.read_text(), Loader=yaml.CSafeLoader)["textures"]
    terrain_alias = {entry["alias"] for entry in aliases
                     if "/terrain/" in entry["source_texture"].replace("\\", "/").lower()}
    sizes = texture_sizes()
    shift = np.array([transform["offset_x"], transform["offset_y"], transform["sea_level_lt"] * transform["scale"]])
    faces = []
    skipped = Counter()
    for bmodel in parse_odm_file(OLD_MAP)["payload"]["bmodels"]:
        name = bmodel["name"].lower()
        if bmodel["name"] in isle_story.SCRIPTED_MODELS:
            continue
        structure = name.startswith(STRUCTURE_PREFIXES)
        if not structure and not name.startswith(TERRAIN_PREFIXES):
            continue
        vertices = np.array([[v["x"], v["y"], v["z"]] for v in bmodel["vertices"]], dtype=np.float64) - shift
        for face in bmodel["faces"]:
            texture = face["texture_name"].upper()
            invisible = bool(face["attributes"] & FACE_INVISIBLE)
            if not structure and (invisible or texture in terrain_alias):
                continue                                    # the terrain itself: in the height map
            points = vertices[face["vertex_indices"][:face["vertex_count"]]]
            if invisible or not texture:
                faces.append((points, None, "", True, bmodel["name"]))
                continue
            if texture not in sizes:
                skipped[texture] += 1
                continue
            width, height = sizes[texture]
            us = (np.array(face["texture_us"][:face["vertex_count"]]) + face["texture_delta_u"]) / width
            vs = 1.0 - (np.array(face["texture_vs"][:face["vertex_count"]]) + face["texture_delta_v"]) / height
            faces.append((points, list(zip(us, vs)), texture, False, bmodel["name"]))
    if skipped:
        raise SystemExit(f"structure textures without a bitmap: {dict(skipped)}")
    return faces


def cluster_faces(faces):
    """Group visible faces into buildings: faces with a vertex within VERTEX_TOLERANCE of another's join. A group
    larger than the map (MM9's sea floor plane under the whole archipelago) is left out: under water it belongs to
    the diving decision. Invisible faces form one collision model."""
    visible = [index for index, face in enumerate(faces) if not face[3]]
    parent = list(range(len(faces)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    owner = {}
    for index in visible:
        for point in faces[index][0]:
            key = tuple(np.round(point / VERTEX_TOLERANCE).astype(int))
            if key in owner:
                parent[find(index)] = find(owner[key])
            else:
                owner[key] = index
    groups = {}
    for index in visible:
        groups.setdefault(find(index), []).append(index)
    kept, dropped = [], []
    for group in groups.values():
        points = np.concatenate([faces[i][0] for i in group])
        (kept if np.ptp(points[:, :2], axis=0).max() < 2 * PARTY_BOUND else dropped).append(group)
    kept.sort(key=lambda g: -len(g))
    colliders = [index for index, face in enumerate(faces) if face[3]]
    return kept, colliders, dropped


def fit_foundations(heights, dry, faces, groups, fine_top) -> int:
    targets: dict[tuple[int, int], list[float]] = {}
    for group in groups:
        points = np.concatenate([faces[index][0] for index in group])
        foundation = points[points[:, 2] <= points[:, 2].min() + FOUNDATION_BAND]
        for x, y, z in np.unique(np.round(foundation), axis=0):
            row = int(np.clip((HALF - FINE / 2 - y) / FINE, 0, fine_top.shape[0] - 1))
            column = int(np.clip((x + HALF - FINE / 2) / FINE, 0, fine_top.shape[1] - 1))
            ground = fine_top[row, column]
            if ground < -1e8 or abs(z - ground) > FOUNDATION_BAND or z <= LAND_ABOVE_SEA:
                continue                        # not standing on MM9's ground above the sea
            cell_row, cell_column = int((HALF - y) // CELL), int((x + HALF) // CELL)
            for node in ((cell_row, cell_column), (cell_row + 1, cell_column), (cell_row, cell_column + 1),
                         (cell_row + 1, cell_column + 1)):
                targets.setdefault(node, []).append(z)
    for node, values in targets.items():
        if dry[node]:
            heights[node] = np.mean(values)
    return sum(1 for node in targets if dry[node])


def fill_cutouts(fine_top, faces, groups):
    """Openings in MM9's terrain enclosed by terrain (not reaching the grid's edge) where a structure stands instead:
    each sample takes the lowest upward structure face over it, FLOOR_CLEARANCE under it; samples no floor covers are
    filled from the surrounding ground (harmonic fill). fine_top is updated in place; returns the cut-out mask."""
    size = fine_top.shape[0]
    labels, _ = ndimage.label(fine_top < -1e8)
    outside = np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))
    cutout = (labels > 0) & ~np.isin(labels, outside)
    if not cutout.any():
        return cutout
    lowest = np.full(fine_top.shape, np.inf)
    for group in groups:
        for index in group:
            points = faces[index][0]
            normal = np.cross(points[1] - points[0], points[2] - points[0])
            length = np.linalg.norm(normal)
            if length < 1e-6 or normal[2] / length < FLOOR_NORMAL:
                continue
            c0 = max(int((points[:, 0].min() + HALF - FINE / 2) // FINE), 0)
            c1 = min(int((points[:, 0].max() + HALF - FINE / 2) // FINE) + 1, size - 1)
            r0 = max(int((HALF - FINE / 2 - points[:, 1].max()) // FINE), 0)
            r1 = min(int((HALF - FINE / 2 - points[:, 1].min()) // FINE) + 1, size - 1)
            if not cutout[r0:r1 + 1, c0:c1 + 1].any():
                continue
            for r, c in zip(*np.nonzero(cutout[r0:r1 + 1, c0:c1 + 1])):
                r, c = r + r0, c + c0
                x, y = c * FINE - HALF + FINE / 2, HALF - FINE / 2 - r * FINE
                if point_in_polygon(points[:, :2], x, y):
                    lowest[r, c] = min(lowest[r, c], plane_height(points, normal, x, y))
    floored = cutout & np.isfinite(lowest)
    fine_top[floored] = lowest[floored] - FLOOR_CLEARANCE
    open_samples = cutout & ~floored
    if open_samples.any():
        known = ~open_samples & (fine_top > -1e8)
        values = np.where(known, fine_top, 0.0)
        for _ in range(200):
            total = ndimage.uniform_filter(np.where(known | open_samples, values, 0.0), 3)
            weight = ndimage.uniform_filter((known | open_samples).astype(float), 3)
            values = np.where(open_samples, total / np.maximum(weight, 1e-6), values)
        fine_top[open_samples] = values[open_samples]
    return cutout


def clamp_under_floors(heights, dry, faces, groups, fine_top) -> int:
    """Our terrain stays under every structure floor MM9 shows: an upward face (normal z over FLOOR_NORMAL) lying on
    or above MM9's terrain. Each dry node within a cell of such a floor is lowered to FLOOR_CLEARANCE under the lowest
    one; floors MM9 itself buries are left alone, so no terrain is carved down to hidden geometry."""
    size = fine_top.shape[0]
    lowest = np.full(fine_top.shape, np.inf)
    for group in groups:
        for index in group:
            points = faces[index][0]
            normal = np.cross(points[1] - points[0], points[2] - points[0])
            length = np.linalg.norm(normal)
            if length < 1e-6 or abs(normal[2]) / length < FLOOR_NORMAL:
                continue
            c0 = max(int((points[:, 0].min() + HALF - FINE / 2) // FINE), 0)
            c1 = min(int((points[:, 0].max() + HALF - FINE / 2) // FINE) + 1, size - 1)
            r0 = max(int((HALF - FINE / 2 - points[:, 1].max()) // FINE), 0)
            r1 = min(int((HALF - FINE / 2 - points[:, 1].min()) // FINE) + 1, size - 1)
            for r in range(r0, r1 + 1):
                for c in range(c0, c1 + 1):
                    x, y = c * FINE - HALF + FINE / 2, HALF - FINE / 2 - r * FINE
                    if not point_in_polygon(points[:, :2], x, y):
                        continue
                    z = plane_height(points, normal, x, y)
                    ground = fine_top[r, c]
                    if ground < -1e8 or z >= ground - FLOOR_CLEARANCE:
                        lowest[r, c] = min(lowest[r, c], z)
    lowered = 0
    reach = CELL // FINE
    for row in range(GRID):
        for column in range(GRID):
            if not dry[row, column]:
                continue
            r, c = row * FINE_PER_CELL, column * FINE_PER_CELL
            floor = lowest[max(r - reach, 0):r + reach, max(c - reach, 0):c + reach]
            if np.isfinite(floor).any() and heights[row, column] > floor.min() - FLOOR_CLEARANCE:
                heights[row, column] = max(floor.min() - FLOOR_CLEARANCE, 0.0)
                lowered += 1
    return lowered


def floor_at(heights, faces, groups, x, y, z_limit) -> float:
    """The highest floor at a point up to z_limit: an upward structure face over it, or our terrain."""
    best = ground_at(heights, x, y)
    for group in groups:
        for index in group:
            points = faces[index][0]
            if not (points[:, 0].min() <= x <= points[:, 0].max() and points[:, 1].min() <= y <= points[:, 1].max()):
                continue
            normal = np.cross(points[1] - points[0], points[2] - points[0])
            length = np.linalg.norm(normal)
            if length < 1e-6 or normal[2] / length < FLOOR_NORMAL or not point_in_polygon(points[:, :2], x, y):
                continue
            z = plane_height(points, normal, x, y)
            if best < z <= z_limit:
                best = z
    return best


def point_in_polygon(polygon, x, y) -> bool:
    inside = False
    for (x0, y0), (x1, y1) in zip(polygon, np.roll(polygon, -1, axis=0)):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def plane_height(points, normal, x, y) -> float:
    return float(points[0][2] - (normal[0] * (x - points[0][0]) + normal[1] * (y - points[0][1])) / normal[2])


def write_obj(path: Path, name: str, faces, indices, invisible: bool) -> None:
    """Faces share their positions (so the editor can merge coplanar neighbours); UVs stay per corner."""
    positions, position_ids, uv_lines, face_lines = [], {}, [], []
    for index in indices:
        points, uvs, texture, _, _ = faces[index]
        uvs = uvs if uvs is not None else [(0.0, 0.0)] * len(points)
        corners = []
        for point, (u, v) in zip(points, uvs):
            key = tuple(np.round(point).astype(int))
            if key not in position_ids:
                position_ids[key] = len(positions) + 1
                positions.append(f"v {key[0] / OBJ_SCALE:.5f} {key[1] / OBJ_SCALE:.5f} {key[2] / OBJ_SCALE:.5f}")
            uv_lines.append(f"vt {u:.6f} {v:.6f}")
            corners.append(f"{position_ids[key]}/{len(uv_lines)}")
        face_lines.append(f"usemtl {texture if not invisible else INVISIBLE_TEXTURE}")
        face_lines.append("f " + " ".join(corners))
    path.write_text("\n".join([f"o BMODEL_{name}"] + positions + uv_lines + face_lines) + "\n")


# --- Chests ---------------------------------------------------------------------------------------------------------

OLD_SCENE = ROOT / "assets_editor_dev/worlds/mm9/maps/isleofashes.scene.yml"
CHEST_EVENT = 40                        # chest k opens with map event CHEST_EVENT + k
FACE_CLICKABLE = 0x2000000


def old_bmodel_faces(bmodel, shift, sizes):
    """An old-map BModel's faces moved into this frame, every face kept (no merging: face indices stay stable)."""
    vertices = np.array([[v["x"], v["y"], v["z"]] for v in bmodel["vertices"]], dtype=np.float64) - shift
    faces = []
    for face in bmodel["faces"]:
        texture = face["texture_name"].upper()
        width, height = sizes[texture]
        count = face["vertex_count"]
        us = (np.array(face["texture_us"][:count]) + face["texture_delta_u"]) / width
        vs = 1.0 - (np.array(face["texture_vs"][:count]) + face["texture_delta_v"]) / height
        faces.append((vertices[face["vertex_indices"][:count]], list(zip(us, vs)), texture, False, bmodel["name"]))
    return faces


def frame_shift(transform):
    return np.array([transform["offset_x"], transform["offset_y"], transform["sea_level_lt"] * transform["scale"]])


def scripted_models(transform):
    """The world models the story scripts move or destroy (story.SCRIPTED_MODELS), by their old-map BModel names:
    [(name, faces)] in this frame."""
    shift, sizes = frame_shift(transform), texture_sizes()
    models = {b["name"]: b for b in parse_odm_file(OLD_MAP)["payload"]["bmodels"]}
    return [(name, old_bmodel_faces(models[name], shift, sizes)) for name in isle_story.SCRIPTED_MODELS]


def chests(transform):
    """MM9's chests: their baked BModels from the old map (MM9_chest_<object>_TreasureChest) as clickable models, and
    their loot records from the old scene, moved into this frame. Returns [(name, faces, loot record)]."""
    shift, sizes = frame_shift(transform), texture_sizes()
    loot = {entry["source_object_index"]: entry
            for entry in yaml.load(OLD_SCENE.read_text(), Loader=yaml.CSafeLoader)["loot_containers"]}
    found = []
    for bmodel in parse_odm_file(OLD_MAP)["payload"]["bmodels"]:
        if not bmodel["name"].startswith("MM9_chest_"):
            continue
        source = int(bmodel["name"].split("_")[2])
        faces = old_bmodel_faces(bmodel, shift, sizes)
        record = dict(loot[source])
        record.pop("world_visual", None)
        position = np.array([record["position"][k] for k in ("x", "y", "z")], dtype=np.float64) - shift
        record["position"] = {k: int(round(v)) for k, v in zip(("x", "y", "z"), position)}
        found.append((f"chest_{source}", faces, record))
    for number, (_, _, record) in enumerate(found):
        record["container_id"] = number
    return found


# --- Exits ----------------------------------------------------------------------------------------------------------

TRANSITIONS = Path("worlds/mm9/data_tables/map_transitions.txt")


def install_transitions(transform) -> int:
    """The review root's MM9 transition table with the isle's rows in this map's frame: exit volumes on the isle and
    arrivals onto it, computed from the assets_dev originals (so a rerun changes nothing). Other maps' rows are kept
    as the review root has them (other conversions shift their own). Read and written under the review tables lock
    the dungeon and city conversions use (../mm9r_common/dungeon/tables.py)."""
    with locked("review_tables.lock"):
        return install_transitions_locked(transform)


def install_transitions_locked(transform) -> int:
    shift = (transform["offset_x"], transform["offset_y"], transform["sea_level_lt"] * transform["scale"])
    raw = (ROOT / "assets_dev" / TRANSITIONS).read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    original = raw.decode("latin-1").splitlines()
    current = review_root.mirror_path(TRANSITIONS).read_text(encoding="latin-1").splitlines()
    header = original[0].split("\t")
    column = {name: header.index(name) for name in header}
    by_id = {line.split("\t")[0]: line for line in current[1:] if line.strip()}
    changed = 0
    for line in original[1:]:
        source = line.split("\t")
        if len(source) < len(header):
            continue
        # Only the isle's side moves; the rest of the row stays as the review root has it (another conversion may
        # have changed the other side, e.g. Verhoffin Ruins became verhoffinruins.blv).
        row = by_id[source[0]].split("\t") if source[0] in by_id else list(source)
        moved = False
        for side, prefix in (("SourceMapFile", "Center"), ("DestinationMapFile", "Arrival")):
            if source[column[side]].lower() != MAP:
                continue
            for axis, delta in zip("XYZ", shift):
                value = float(source[column[prefix + axis]])
                row[column[prefix + axis]] = str(round(value - delta))
            moved = True
        if moved:
            by_id[row[0]] = "\t".join(row)
            changed += 1
    lines = [current[0]] + [by_id[line.split("\t")[0]] for line in current[1:] if line.strip()]
    review_root.install(TRANSITIONS, (newline.join(lines) + newline).encode("latin-1"))
    return changed


# --- Props ----------------------------------------------------------------------------------------------------------

PROPS = PROJECT / "props.json"          # level_generation/props/mm9_isleofashes_claude: decorations and placements


def ground_at(heights, x, y) -> float:
    """The native terrain height at a point (the two triangles of the cell, as OutdoorGeometryUtils)."""
    column, row = (x + HALF) / CELL, (HALF - y) / CELL
    c, r = int(np.clip(np.floor(column), 0, GRID - 2)), int(np.clip(np.floor(row), 0, GRID - 2))
    fx, fy = column - c, row - r
    h00, h10, h01, h11 = heights[r, c], heights[r, c + 1], heights[r + 1, c], heights[r + 1, c + 1]
    if fx + fy <= 1:
        return float(h00 + (h10 - h00) * fx + (h01 - h00) * fy)
    return float(h11 + (h01 - h11) * (1 - fx) + (h10 - h11) * (1 - fy))


def prop_entities(heights, events):
    """Decoration entities from props.json: the list id by name (row number minus 1) from the review root's decoration
    table as the engine merges it (the engine's rows, then the MM9 world's own: world.yml tableContributions table
    decorations; game/content/WorldDecorations.cpp), props that stand on the ground set on ours, the others at MM9's
    height."""
    world = yaml.safe_load(review_root.mirror_path("worlds/mm9/world.yml").read_text())
    tables = ["engine/data_tables/decoration_data.txt"] + [
        "worlds/mm9/" + c["path"] for c in world.get("tableContributions", []) if c.get("table") == "decorations"]
    ids = {}
    for table in tables:
        for cells in (line.split("\t") for line in review_root.mirror_path(table).read_text(encoding="latin-1")
                      .splitlines()):
            if len(cells) > 1 and cells[0].strip().isdigit():
                ids[cells[1].strip().lower()] = int(cells[0]) - 1
    entities = []
    for prop in json.loads(PROPS.read_text()):
        name = prop["decoration"].lower()
        if name not in ids:
            raise SystemExit(f"decoration {name} has no row in the review root's decoration table")
        z = ground_at(heights, prop["x"], prop["y"]) if prop["snap_to_ground"] else prop["z"]
        entity = {"entity_index": len(entities), "name": name, "decoration_list_id": ids[name],
                  "ai_attributes": 0,
                  "position": {"x": int(round(prop["x"])), "y": int(round(prop["y"])), "z": int(round(z))},
                  "facing": int(round(prop["yaw_degrees"])) % 360, "event_id_primary": 0,
                  "event_id_secondary": 0, "variable_primary": 0, "variable_secondary": 0,
                  "special_trigger": 0, "initial_decoration_flag": 0}
        entity.update(events.get(prop["source_object"], {}))       # the story's props (story.prop_events())
        entities.append(entity)
    return entities


# --- Build ----------------------------------------------------------------------------------------------------------

def main() -> int:
    # Superseded by ../mm9r_isleofashes_blv/ (README.md): story.py writes no map Lua since the BLV's hand port
    # (regionlua.py, 2026-11-06), so this pilot stops here rather than install a map without its story.
    sys.exit("mm9r_isleofashes (the ODM pilot) no longer builds: superseded by mm9r_isleofashes_blv (README.md)")
    review_root.create(fresh=False)
    WORK.mkdir(exist_ok=True)
    x, y, z, texture, names, transform = load_terrain()
    print(f"{len(x)} terrain triangles, textures {names}, sea level LT {transform['sea_level_lt']:.0f}")

    # Heights at the nodes (row 0 = north, y = HALF - CELL * row; x = CELL * column - HALF).
    node_top, _, _, _ = rasterize(x, y, z, texture, -HALF, HALF, CELL, GRID)
    covered_nodes = node_top > -1e8
    seabed = np.where(covered_nodes, node_top, 0.0)
    np.save(WORK / "seabed_heights.npy", seabed)                 # below zero: under the sea (kept for diving)

    # Fine samples at cell sub-centres, for the land share, the ground per cell and the gating report.
    fine_size = GRID * FINE_PER_CELL
    fine_top, fine_texture, _, _ = rasterize(x, y, z, texture, -HALF + FINE / 2, HALF - FINE / 2, FINE, fine_size)
    fine_land = fine_top > LAND_ABOVE_SEA
    blocks = fine_land.reshape(GRID, FINE_PER_CELL, GRID, FINE_PER_CELL)

    # Cut-outs: MM9 removes its terrain under some structures (the castle on the middle island stands in a 2 000-unit
    # opening, its floors are the ground). An opening enclosed by terrain is land, not sea: our ground lies just under
    # the structure's lowest floor there (or follows the rim where no floor covers it).
    faces = structure_faces(transform)
    groups, colliders, dropped = cluster_faces(faces)
    cutout = fill_cutouts(fine_top, faces, groups)
    fine_land = fine_top > LAND_ABOVE_SEA
    blocks = fine_land.reshape(GRID, FINE_PER_CELL, GRID, FINE_PER_CELL)
    for row, column in zip(*np.nonzero(~covered_nodes)):
        r, c = row * FINE_PER_CELL, column * FINE_PER_CELL
        window = (slice(max(r - 1, 0), r + 1), slice(max(c - 1, 0), c + 1))
        if cutout[window].any():
            node_top[row, column] = fine_top[window][cutout[window]].min()
            covered_nodes[row, column] = True
    print(f"cut-outs: {int(cutout.sum())} fine samples filled under structures")

    # Dry nodes: land within NODE_REACH of the node (so spits and ridges narrower than a cell survive). A dry node
    # whose own sample is at the sea takes the mean height of the land around it; wet nodes lie at the sea.
    reach = NODE_REACH // FINE
    padded_land = np.pad(fine_land, reach)
    padded_top = np.pad(np.where(fine_land, fine_top, 0.0), reach)
    around_land = np.zeros((GRID, GRID), int)
    around_height = np.zeros((GRID, GRID))
    for dr in range(-reach, reach):
        for dc in range(-reach, reach):
            rows = slice(reach + dr, reach + dr + GRID * FINE_PER_CELL, FINE_PER_CELL)
            columns = slice(reach + dc, reach + dc + GRID * FINE_PER_CELL, FINE_PER_CELL)
            around_land += padded_land[rows, columns]
            around_height += padded_top[rows, columns]
    dry, water, shore = coast(around_land > 0)
    own = covered_nodes & (node_top > LAND_ABOVE_SEA)
    heights = np.where(own, node_top, around_height / np.maximum(around_land, 1))
    heights = np.where(dry, np.clip(np.maximum(heights, LAND_ABOVE_SEA * 2), 0, 255 * HEIGHT_STEP), 0.0)

    # Foundations: where a structure's lowest vertices met MM9's ground, our ground meets them too (the grid fills
    # sunken paths and smooths the ledges they stand on). The corners of the cell under each such vertex take the
    # mean foundation height of the vertices over them; sea nodes stay at the sea.
    unfitted = heights.copy()
    fitted = fit_foundations(heights, dry, faces, groups, fine_top)
    lowered = clamp_under_floors(heights, dry, faces, groups, fine_top)
    structure_nodes = heights != unfitted
    print(f"foundations: {fitted} nodes fitted to structures, {lowered} lowered under floors")
    height_bytes = np.clip(np.round(heights / HEIGHT_STEP), 0, 255).astype(np.uint8)
    heights = height_bytes.astype(np.float64) * HEIGHT_STEP

    # One ground per land cell: the MM9 terrain texture covering most of its land samples.
    tiles = np.full((GRID, GRID), TILE["water"], np.uint8)
    cell_textures = fine_texture.reshape(GRID, FINE_PER_CELL, GRID, FINE_PER_CELL).transpose(0, 2, 1, 3)
    cell_land = blocks.transpose(0, 2, 1, 3)
    unmapped = Counter()
    for row in range(GRID):
        for column in range(GRID):
            if water[row, column]:
                continue
            values = cell_textures[row, column][cell_land[row, column]]
            if values.size == 0:
                values = cell_textures[row, column][cell_textures[row, column] >= 0]
            name = names[Counter(values.tolist()).most_common(1)[0][0]] if values.size else "ashdirt3"
            if name not in GROUND:
                unmapped[name] += 1
                name = "ashdirt3"
            tiles[row, column] = TILE[GROUND[name]]
    if unmapped:
        raise SystemExit(f"unmapped MM9 terrain textures: {dict(unmapped)}")
    tiles[shore > 0] = shore[shore > 0]

    # Route cuts: an MM9 walkable component that the grid splits into separate walkable parts. The cut cells are
    # graded to the path crossing them (route_cell_targets), all together (grade_routes), then checked again: grading
    # can cut a neighbouring cell, which joins the set. Cells beside the sea keep the sea level; nodes the structures
    # set (foundations, floors) stay. Every graded cell is logged in work/route_fixes.json.
    base = heights.copy()
    routes, fixes = {}, []
    # Trails first: MM9's painted map draws its paths and open ground pale (painted_trails); a trail cell the grid
    # makes a slide is graded to the trail's own walkable samples (its largest walkable component in the cell).
    _, _, fine_labels = gating_report(fine_top, fine_land, heights, water)
    trail = painted_trails(transform) & (fine_labels > 0)
    corners = np.stack([heights[:-1, :-1], heights[1:, :-1], heights[:-1, 1:], heights[1:, 1:]])
    slide = np.pad(corners.max(0) - corners.min(0) > CELL, ((0, 1), (0, 1)))
    share = trail.reshape(GRID, FINE_PER_CELL, GRID, FINE_PER_CELL).mean(axis=(1, 3))
    for row, column in zip(*np.nonzero(slide & (share >= PATH_SHARE))):
        if water[max(row - 1, 0):row + 2, max(column - 1, 0):column + 2].any():
            continue
        r, c = row * FINE_PER_CELL, column * FINE_PER_CELL
        labels = fine_labels[r:r + FINE_PER_CELL, c:c + FINE_PER_CELL][trail[r:r + FINE_PER_CELL, c:c + FINE_PER_CELL]]
        component = Counter(labels.tolist()).most_common(1)[0][0]
        target = route_cell_targets(row, column, fine_top, trail & (fine_labels == component))
        if target is not None:
            routes[(int(row), int(column))] = target
            fixes.append({"x": int(column * CELL - HALF + CELL / 2), "y": int(HALF - row * CELL - CELL / 2),
                          "trail": True, "component": int(component)})
    if routes:
        heights = np.round(grade_routes(base, routes, structure_nodes) / HEIGHT_STEP) * HEIGHT_STEP
    for _ in range(ROUTE_FIX_PASSES):
        report, overlay, fine_labels = gating_report(fine_top, fine_land, heights, water)
        added = 0
        for cut in report["route_cuts"]:
            row, column = int((HALF - cut["y"]) // CELL), int((cut["x"] + HALF) // CELL)
            if (row, column) in routes or water[max(row - 1, 0):row + 2, max(column - 1, 0):column + 2].any():
                continue
            target = route_cell_targets(row, column, fine_top, fine_labels == cut["component"])
            routes[(row, column)] = target if target is not None else heights[row:row + 2, column:column + 2].copy()
            fixes.append(cut)
            added += 1
        if not added:
            break
        heights = np.round(grade_routes(base, routes, structure_nodes) / HEIGHT_STEP) * HEIGHT_STEP
    for fix in fixes:
        row, column = int((HALF - fix["y"]) // CELL), int((fix["x"] + HALF) // CELL)
        fix["corners_before"] = base[row:row + 2, column:column + 2].astype(int).tolist()
        fix["corners_after"] = heights[row:row + 2, column:column + 2].astype(int).tolist()
    height_bytes = np.clip(np.round(heights / HEIGHT_STEP), 0, 255).astype(np.uint8)
    heights = height_bytes.astype(np.float64) * HEIGHT_STEP
    (WORK / "route_fixes.json").write_text(json.dumps(fixes, indent=1) + "\n")
    print(f"route fixes: {len(fixes)} cells softened")
    report, overlay, _ = gating_report(fine_top, fine_land, heights, water)
    Image.fromarray(overlay).save(WORK / "gating.png")
    (WORK / "gating.json").write_text(json.dumps(report, indent=1) + "\n")
    (WORK / "transform.json").write_text(json.dumps(transform, indent=1) + "\n")
    ground_counts = Counter(tiles.flatten().tolist())
    print(f"cells: water {int(water.sum())}, shore {int((shore > 0).sum())}, "
          + ", ".join(f"{g} {ground_counts[t]}" for g, t in TILE.items() if g != "water"))
    print(f"gating: MM9 blocked {100 * report['mm9_blocked_share']:.0f} % of land, "
          f"{100 * report['opened_share_of_blocked']:.0f} % of that walkable natively; "
          f"{len(report['opened'])} opened and {len(report['closed'])} closed spots of a cell or more; "
          f"route candidates: {len(report['route_cuts'])} cut cells, {len(report['route_joins'])} join cells")

    # Editor source package.
    if SOURCE.exists():
        shutil.rmtree(SOURCE)
    SOURCE.mkdir()
    write(SOURCE / f"{STEM}.terrain.yml", json.dumps({
        "version": 1, "map_file": MAP, "height_map_hex": height_bytes.tobytes().hex().upper(),
        "tile_map_hex": tiles.tobytes().hex().upper(), "attribute_map_hex": bytes(GRID * GRID).hex().upper()}) + "\n")
    if dropped:
        print(f"  left out (larger than the map): {[len(group) for group in dropped]} faces")
    (SOURCE / "models").mkdir()
    bmodels, interactive = [], []
    models = [(f"structure{number:02d}", group, False) for number, group in enumerate(groups)]
    if colliders:
        models.append(("colliders", colliders, True))
    story = isle_story.Story(transform)
    actors = story.build_actors(lambda x, y: ground_at(heights, x, y),
                                lambda x, y, z: floor_at(heights, faces, groups, x, y, z))
    scripted = scripted_models(transform)
    for name, model_faces in scripted:
        models.append((name, list(range(len(faces), len(faces) + len(model_faces))), False))
        faces.extend(model_faces)
    chest_list = chests(transform)
    for name, chest_faces, _ in chest_list:
        models.append((name, list(range(len(faces), len(faces) + len(chest_faces))), False))
        faces.extend(chest_faces)
    for index, (name, indices, invisible) in enumerate(models):
        path = SOURCE / "models" / f"{name}.obj"
        write_obj(path, name, faces, indices, invisible)
        textures = sorted({faces[i][2] for i in indices if faces[i][2]}) or [INVISIBLE_TEXTURE]
        bmodels.append({"geometry_id": f"mm9r_isleofashes:{name}", "runtime_bmodel_index": index,
                        "source": {"asset_path": str(path), "scale": OBJ_SCALE,
                                   "merge_coplanar_faces": not invisible and name.startswith("structure"),
                                   "preserve_source_winding": True},
                        "materials": {"default_texture": textures[0], "remaps": {t: t for t in textures}}})
        if invisible:
            interactive += [{"bmodel_index": index, "face_index": face, "legacy_attributes": FACE_INVISIBLE,
                             "cog_number": 0, "cog_triggered_number": 0, "cog_trigger": 0}
                            for face in range(len(indices))]
        if name in isle_story.SCRIPTED_MODELS:
            # Doors: clickable, their Use event on the faces; fort walls: only the cog (story.lua removes them).
            event = story.model_event(name)
            interactive += [{"bmodel_index": index, "face_index": face,
                             "legacy_attributes": FACE_CLICKABLE if event else 0,
                             "cog_number": story.scripted_model_cogs()[name], "cog_triggered_number": event,
                             "cog_trigger": 0} for face in range(len(indices))]
        if name.startswith("chest_"):
            event = CHEST_EVENT + [chest[0] for chest in chest_list].index(name)
            interactive += [{"bmodel_index": index, "face_index": face, "legacy_attributes": FACE_CLICKABLE,
                             "cog_number": 0, "cog_triggered_number": event, "cog_trigger": 0}
                            for face in range(len(indices))]
        sources = Counter(faces[i][4] for i in indices)
        print(f"  {name}: {len(indices)} faces from {dict(sources.most_common(3))}")
    write(SOURCE / f"{STEM}.geometry.yml", json.dumps({"version": 1, "map_file": MAP, "bmodels": bmodels},
                                                       indent=1) + "\n")
    environment = yaml.safe_load((ROOT / "assets_dev/worlds/mm8/maps/out01.scene.yml").read_text())["environment"]
    environment["tile_set_lookup_indices"] = LOOKUPS
    environment["master_tile"] = 0
    scene = {"format_version": 1, "kind": "outdoor_scene", "source": {"geometry_file": MAP},
             "environment": environment, "terrain": {"attribute_overrides": [], "footstep_sound_overrides": []},
             "bmodel_faces": {"interactive_faces": interactive},
             "mechanisms": story.mechanisms({name: index for index, (name, _, _) in enumerate(models)}),
             "mm9_npc_greetings": story.greetings(),
             "entities": prop_entities(heights, story.prop_events()), "spawns": [],
             "initial_state": {"location": {"respawn_count": 0, "last_respawn_day": 0, "reputation": 0,
                                            "alert_status": 0},
                               "face_attribute_overrides": [], "actors": actors, "sprite_objects": [], "chests": [],
                               "variables": {"map": [0] * 75, "decor": [0] * 125}},
             "loot_containers": [record for _, _, record in chest_list], "world_items": []}
    write(SOURCE / f"{STEM}.scene.yml", json.dumps(scene, indent=1) + "\n")
    package = {"format_version": 1, "kind": "outdoor_map_package", "package_id": "mm9:isleofashes",
               "display_name": "Isle of Ashes", "map_file": MAP, "scene_file": f"{STEM}.scene.yml",
               "geometry_metadata_file": f"{STEM}.geometry.yml", "terrain_metadata_file": f"{STEM}.terrain.yml",
               "script_module": f"maps/{STEM}.lua", "map_stats_id": MAP_STATS_ID, "redbook_track": 0,
               "environment_name": "grassland", "is_top_level_area": True,
               "outdoor_bounds": {"enabled": True, "min_x": -PARTY_BOUND, "max_x": PARTY_BOUND,
                                  "min_y": -PARTY_BOUND, "max_y": PARTY_BOUND}}
    write(SOURCE / f"{STEM}.map.yml", json.dumps(package, indent=1) + "\n")

    with tempfile.TemporaryDirectory(prefix="mm9r-isle-") as directory:
        temp = Path(directory)
        for name in (f"{STEM}.map.yml", f"{STEM}.scene.yml", f"{STEM}.geometry.yml", f"{STEM}.terrain.yml"):
            shutil.copy2(SOURCE / name, temp / name)
        with (WORK / "build.log").open("w") as log:
            subprocess.run([str(ROOT / "build/editor/openyamm-editor"), "--asset-root", str(review_root.ASSETS),
                            "--headless-build-map", str(temp / f"{STEM}.map.yml")],
                           check=True, stdout=log, stderr=subprocess.STDOUT)
        built = (temp / MAP).read_bytes()

    # Install into the review root: the new map, its scene and script; the bmodel_world sidecars go.
    maps = Path("worlds/mm9/maps")
    for suffix in (".render", ".render.yml", ".nav", ".nav.yml", ".lighting", ".mm9.yml", ".model_assets.yml"):
        review_root.remove(maps / f"{STEM}{suffix}")
    review_root.install(maps / MAP, built)
    review_root.install_file(maps / f"{STEM}.scene.yml", SOURCE / f"{STEM}.scene.yml")

    native = parse_odm_file(review_root.mirror_path(maps / MAP))["payload"]
    assert bytes(native["height_map"]) == height_bytes.tobytes()
    assert bytes(native["tile_map"]) == tiles.tobytes()
    print(f"installed {review_root.mirror_path(maps / MAP)}; {install_transitions(transform)} transition rows moved")

    # The map script: the chests, then the story (story.py: generated data and dialogue callbacks, story.lua).
    opened = ", ".join(f"[{CHEST_EVENT + k}] = {{{k}}}" for k in range(len(chest_list)))
    lua = ["-- Isle of Ashes, MM9 rework: written by level_generation/projects/mm9r_isleofashes/convert.py",
           f"SetMapMetadata({{openedChestIds = {{{opened}}}}})"]
    lua += [f'RegisterEvent({CHEST_EVENT + k}, "Chest", function() evt.OpenChest({k}) end, "Chest")'
            for k in range(len(chest_list))]
    rows = review_root.mirror_path(TRANSITIONS).read_text(encoding="latin-1").splitlines()
    header = rows[0].split("\t")
    transitions = [dict(zip(header, row.split("\t"))) for row in rows[1:] if row.strip()]
    write(SOURCE / f"{STEM}.lua", "\n".join(lua) + "\n" + story.lua_text(transitions, story.scripted_model_cogs()))
    review_root.install_file(Path("worlds/mm9/events/maps") / f"{STEM}.lua", SOURCE / f"{STEM}.lua")
    print(f"story: {len(actors)} actors, {len(scripted)} scripted models; sounds installed: "
          f"{story.install_sounds(review_root) or 'none'}")

    # The world's terrain material file, then this map's weights.
    review_root.install_file("worlds/mm9/terrain_materials/world.yml",
                             PROJECT.parent / "mm9r_common/terrain_materials_world.yml")
    subprocess.run([sys.executable, str(ROOT / "tools/terrain_materials.py"), "weights", "--world", "mm9", "--map", MAP,
                    "--assets", str(review_root.ASSETS)], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
