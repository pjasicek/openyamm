#!/usr/bin/env python3
"""Town feel: the figures of devdocs/map_studio/TOWN_FEEL.md measured on any outdoor map, each printed against the
range of the shipped MM6-MM8 towns and flagged when outside it.

    town_feel.py <map.odm> --world <w> [--assets <root>] [--town <x0,y0,x1,y1>] [--json]

<map.odm> is a file name under <root>/worlds/<w>/maps/ or a path. The town footprint is found as the cluster of house
doors holding the most services (single link, 4000 units) unless --town gives it. Reads the map through
`oymap export` and `oymap things` (openyamm-studio/build/oymap), the placed actors from the map's scene file and the
house, decoration and map tables from <root>/engine/data_tables. How close the town is built (buildings per area,
gaps between them, street widths, the square, the services' spread: town_density, 2026-11-16) is measured here; tree
spacing, wild-land density and road ends at the map edge belong to OUTDOOR_REBUILD_PROCEDURE.md.

    town_feel.py --shipped [--json]     every shipped town of the rule set, one table
    --start                             judge a start or early map by the five shipped start maps' ranges
    --small                             judge a small town (9 services or fewer): its size figures by the thirteen
                                        towns and four small ones, no lower bound on spread or magic shop to alchemist
    town_feel.py --project <folder> [--assets <root>] [--report-json]
                                        a built outdoor project (its build/<stem>.odm and scene, from `oymap build`;
                                        the interactive things through oymap's private build of the project)
    --report-json                       the figures with every rule's range and verdict as JSON (the studio host's
                                        job: schema/rpc/jobs.rpc.json)

The oymap binary is $OYMAP when set (the studio host passes its own), else openyamm-studio/build/oymap.
"""

import argparse
import json
import math
import re
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
OYMAP = Path(os.environ.get("OYMAP") or REPO / "openyamm-studio/build/oymap")
CELL = 512
CELLS = 128
TOWN_REACH = 1536  # the town: land within this of a town house door
RING = 3072        # the land round the town: the next band out
TOWN_LINK = 1536   # town spread: buildings this close to a town door or to such a building belong to the town

# The shipped towns the ranges come from, and the footprint used where the automatic cluster is not the town.
SHIPPED = [
    ("mm6", "oute3.odm", "New Sorpigal", None),
    ("mm6", "outc2.odm", "Free Haven", None),
    ("mm6", "outd3.odm", "Castle Ironfist", None),
    ("mm6", "outd1.odm", "Silver Cove", None),
    ("mm7", "7out02.odm", "Harmondale", None),
    ("mm7", "7out03.odm", "Erathia (Steadwick)", None),
    ("mm7", "7out13.odm", "Tatalia (Tatalia town)", (-4500, -20500, 13500, -4000)),
    ("mm7", "7out04.odm", "Tularean Forest (Pierpont)", None),
    ("mm7", "7out06.odm", "Bracada (Celeste approach; not a town, left out of the ranges)", None),
    # Small towns, left out of the main ranges (decision D-20): only --small's size figures take them in.
    ("mm7", "7out05.odm", "Deyja (small town; --small only)", None),
    ("mm7", "out10.odm", "Mount Nighon (small town; --small only)", None),
    ("mm6", "outa2.odm", "Paradise Valley (small town; --small only)", None),
    ("mm6", "outb1.odm", "Kriegspire (small town; --small only)", None),
    ("mm8", "out02.odm", "Ravenshore", None),
    ("mm8", "out03.odm", "Alvar", None),
    ("mm8", "out06.odm", "Shadowspire", None),
    ("mm8", "out05.odm", "Garrote Gorge", None),
    ("mm8", "out01.odm", "Dagger Wound", None),
]

# Road tile sets per world: first row of each 36-tile set (openyamm-studio/core/OutdoorGround.cpp).
ROAD_ROWS = {"mm8": [414, 522, 774], "mm7": [414], "mm6": [414, 450, 486, 522, 558, 594, 630, 666, 702, 774, 810]}
TILE_TABLES = {"mm6": "terrain_tile_data_3.txt", "mm7": "terrain_tile_data_2.txt", "mm8": "terrain_tile_data.txt"}
DIRECT_TILE_BASES = [0, 450, 630]

SERVICE_GROUPS = {
    "weapon": ["Weapon Shop"], "armour": ["Armor Shop"], "magic": ["Magic Shop"], "alchemist": ["Alchemist"],
    "tavern": ["Tavern", "The Adventurer's Inn"], "temple": ["Temple"], "bank": ["Bank"], "town_hall": ["Town Hall"],
    "training": ["Training"], "stables": ["Stables"], "boats": ["Boats"],
}
THEMATIC = re.compile(r"wagon|cart|crate|create|barrel|keg|sign|well|fountain|statue|fence|gazebo|cannon|tent|"
                      r"dock|pier|bridge|fire pit|campfire|beacon|torch|flag|cauldron|trash|corn|hay|bench|lamp|"
                      r"pond|lighthouse|banner|post|trough|market|stall|wheel|boat|ship|skiff", re.I)
TREE = re.compile(r"tree|palm|pine|willow|cactus", re.I)
GREEN = re.compile(r"flower|plant|bush|shrub|fern|weed|grass|lily", re.I)
ROCK = re.compile(r"rock|boulder|stone|stalag", re.I)
BUFF = re.compile(r"Bonus|Base[A-Z]|Resistance|HP \+|SP \+|Gold \+|Luck|Might|Accuracy|Speed|Intellect|"
                  r"Personality|Endurance|ArmorClass", re.I)
SPECIAL_TITLE = re.compile(r"well|fountain|trough|pedestal|pedastal|shrine|altar|obelisk|drink", re.I)


# ---------------------------------------------------------------- reading

def read_json_bytes(data):
    return json.loads(data.decode("latin-1"))


def oymap(args):
    result = subprocess.run([str(OYMAP)] + args, capture_output=True)
    if result.returncode != 0:
        sys.exit(f"oymap {' '.join(args)} failed: {result.stderr.decode('latin-1')[:500]}")
    return read_json_bytes(result.stdout)


def table_rows(path):
    with open(path, encoding="latin-1") as handle:
        return [line.rstrip("\n").split("\t") for line in handle]


def world_table_rows(assets, world, name):
    """An engine table's rows, then the world's own rows of it (worlds/<world>/data_tables/<name>, the rows a world
    package adds: Xeen's houses, monsters and maps), as the game composes them."""
    rows = table_rows(assets / "engine/data_tables" / name)
    own = assets / "worlds" / (world or "") / "data_tables" / name
    return rows + table_rows(own) if world and own.is_file() else rows


def house_types(assets, world=None):
    types = {}
    for row in world_table_rows(assets, world, "house_data.txt")[2:]:
        if len(row) > 5 and row[0].strip().isdigit():
            types[int(row[0])] = (row[2].strip(), row[5].strip())
    return types


def decoration_hints(assets):
    hints = {}
    for row in table_rows(assets / "engine/data_tables/decoration_data.txt")[2:]:
        if len(row) > 2 and row[1]:
            hints.setdefault(row[1].lower(), row[2].lower())
    return hints


def monster_names(assets, world=None):
    names = {}
    for row in world_table_rows(assets, world, "monster_data.txt"):
        if len(row) > 2 and row[0].strip().isdigit():
            names[int(row[0])] = (row[1], row[2])
    return names


CIVILIAN = re.compile(r"peasant|villager|farmer|guard|defender|sergeant|merchant|noble|child|adventurer|"
                      r"apprentice|townsfolk|citizen|serf|elder", re.I)
AGGRESSOR_BIT = 0x00080000


def is_hostile(monster_id, monsters, attributes=0):
    """A civilian by name (peasants, guards, defenders, apprentices) is friendly unless authored as an aggressor; every
    other monster counts as a threat: spawned and placed monsters of other kinds attack once the party is near
    (their Hst range), whatever hostile.txt's party row says."""
    if attributes & AGGRESSOR_BIT:
        return True
    name = monsters.get(monster_id, ("", ""))[0]
    return not CIVILIAN.search(name)


def monster_by_picture(monsters, picture):
    picture = picture.strip().lower()
    for monster_id, (name, pic) in sorted(monsters.items()):
        if pic.lower().startswith(picture) or name.lower() == picture:
            return monster_id
    return None


def spawn_counts(assets, map_name, world=None):
    """Per map monster slot M1-M3: mean group size from map_stats ('#' dice such as ' 2-5') and its picture name."""
    for row in world_table_rows(assets, world, "map_stats.txt"):
        if len(row) > 28 and row[2].strip().lower() == map_name.lower():
            slots = []
            for column, name_column in ((19, 16), (23, 20), (27, 24)):
                match = re.match(r"\s*(\d+)\s*-\s*(\d+)", row[column])
                picture = row[name_column].strip()
                present = picture not in ("", "0")
                mean = ((int(match.group(1)) + int(match.group(2))) / 2.0) if match and present else 0.0
                slots.append((mean, picture if present else ""))
            return slots
    return [(0.0, ""), (0.0, ""), (0.0, "")]


def scene_actors(scene_path):
    """Placed actors of the scene's initial state: (monster_info_id, x, y, z, group). A line scan: the files are big."""
    actors = []
    if not scene_path.exists():
        return actors
    in_actors = False
    current = None
    axis = None
    with open(scene_path, encoding="latin-1") as handle:
        for line in handle:
            if line.startswith("  actors:"):
                in_actors = True
                continue
            if in_actors and re.match(r"^  [a-z_]+:", line):
                break
            if not in_actors:
                continue
            if line.startswith("    - "):
                if current:
                    actors.append(current)
                current = {}
            stripped = line.strip().lstrip("- ")
            key, _, value = stripped.partition(":")
            value = value.strip()
            if key == "monster_info_id":
                current["id"] = int(value)
            elif key == "attributes" and line.startswith("      attributes"):
                current["attributes"] = int(value)
            elif key == "hostility_type":
                current["hostility"] = int(value)
            elif key == "group" and line.startswith("      group"):
                current["group"] = int(value)
            elif key == "position":
                axis = "position"
            elif key in ("x", "y", "z") and axis == "position" and line.startswith("        "):
                current[key] = int(value)
            elif not line.startswith("        "):
                axis = None
    if current:
        actors.append(current)
    return [a for a in actors if "x" in a and "y" in a]


def scene_list(scene_path, section):
    """A top-level list of the scene file (entities, spawns) as dicts: scalar keys, and position as [x, y, z]."""
    items = []
    if not scene_path.exists():
        return None
    within = False
    current = None
    with open(scene_path, encoding="latin-1") as handle:
        for line in handle:
            if line.startswith(section + ":"):
                within = True
                continue
            if within and line[:1].strip():
                break
            if not within:
                continue
            if line.startswith("  - "):
                if current is not None:
                    items.append(current)
                current = {"position": [0, 0, 0], "name": ""}
            if current is None:
                continue
            key, _, value = line.strip().lstrip("- ").partition(":")
            value = value.strip().strip('"')
            if line.startswith("      ") and key in ("x", "y", "z"):
                current["position"]["xyz".index(key)] = int(value)
            elif value and not line.startswith("      "):
                current[key] = int(value) if re.fullmatch(r"-?\d+", value) else value
    if current is not None:
        items.append(current)
    return items if within else None


# ---------------------------------------------------------------- terrain

def cell_of(x, y):
    return int(math.floor((x + 32768) / CELL)), int(math.floor((32768 - y) / CELL))


def cell_centre(gx, gy):
    return (gx + 0.5) * CELL - 32768, 32768 - (gy + 0.5) * CELL


def ground_masks(world, terrain, tile_lookup, assets, scene_environment):
    """Per cell: a road-set tile (built roads), and worn ground (roads plus dirt tiles and their grass-dirt edges: the
    plazas and lanes of MM6 and MM7 towns are dirt, not road tiles)."""
    rows = ROAD_ROWS.get(world, ROAD_ROWS["mm7"])
    master = int(scene_environment.get("master_tile", terrain.get("master_tile", 0)) or 0)
    lookups = scene_environment.get("tile_set_lookup_indices") or tile_lookup
    table = table_rows(assets / "engine/data_tables" / TILE_TABLES.get(world, TILE_TABLES["mm7"]))[1:]
    tile_map = np.array(terrain["tile_map"]).reshape(CELLS, CELLS)
    road_of_raw = np.zeros(256, dtype=bool)
    worn_of_raw = np.zeros(256, dtype=bool)
    water_of_raw = np.zeros(256, dtype=bool)
    for raw in range(256):
        if raw >= 234:
            continue
        if raw < 90:
            index = raw + DIRECT_TILE_BASES[master] if world == "mm8" and raw != 0 and master < 3 else raw
        else:
            index = lookups[(raw - 90) // 36] + (raw - 90) % 36
        road_of_raw[raw] = any(row <= index < row + 36 for row in rows)
        name = table[index][1].lower() if index < len(table) and len(table[index]) > 1 else ""
        worn_of_raw[raw] = road_of_raw[raw] or bool(re.match(r"^[67]?(dirt|grdrt|grdr|drt)", name))
        water_of_raw[raw] = bool(re.match(r"^[67]?wtr", name)) or raw == 0
    return road_of_raw[tile_map], worn_of_raw[tile_map], water_of_raw[tile_map]


def thin(mask):
    """Zhang-Suen thinning of a boolean grid."""
    image = np.pad(mask.astype(np.uint8), 1)
    changed = True
    while changed:
        changed = False
        for step in (0, 1):
            p = image
            p2, p3, p4 = p[:-2, 1:-1], p[:-2, 2:], p[1:-1, 2:]
            p5, p6, p7 = p[2:, 2:], p[2:, 1:-1], p[2:, :-2]
            p8, p9 = p[1:-1, :-2], p[:-2, :-2]
            ring = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            neighbours = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
            transitions = sum(((ring[i] == 0) & (ring[i + 1] == 1)).astype(np.uint8) for i in range(8))
            centre = p[1:-1, 1:-1]
            if step == 0:
                cond = (p2 * p4 * p6 == 0) & (p4 * p6 * p8 == 0)
            else:
                cond = (p2 * p4 * p8 == 0) & (p2 * p6 * p8 == 0)
            remove = (centre == 1) & (neighbours >= 2) & (neighbours <= 6) & (transitions == 1) & cond
            if remove.any():
                changed = True
                image[1:-1, 1:-1][remove] = 0
    return image[1:-1, 1:-1].astype(bool)


NEIGHBOURS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]


def road_chains(skeleton):
    """Chains of skeleton cells between ends and junctions, as lists of (gx, gy)."""
    cells = set(zip(*np.nonzero(skeleton.T)))  # (gx, gy)

    def links(cell):
        """m-adjacency: a diagonal neighbour counts only when no shared side neighbour links the two."""
        found = []
        for dx, dy in NEIGHBOURS:
            other = (cell[0] + dx, cell[1] + dy)
            if other not in cells:
                continue
            if dx and dy and ((cell[0] + dx, cell[1]) in cells or (cell[0], cell[1] + dy) in cells):
                continue
            found.append(other)
        return found

    nodes = {cell for cell in cells if len(links(cell)) != 2}
    visited = set()
    chains = []
    for start in list(nodes) + list(cells):
        for first in links(start):
            if (start, first) in visited:
                continue
            chain = [start, first]
            visited.add((start, first))
            visited.add((first, start))
            previous, current = start, first
            while current not in nodes:
                following = [c for c in links(current) if c != previous and (current, c) not in visited]
                if not following:
                    break
                previous, current = current, following[0]
                visited.add((previous, current))
                visited.add((current, previous))
                chain.append(current)
                if current == start:
                    break
            chains.append(chain)
    return chains


def simplify(points, tolerance):
    if len(points) < 3:
        return points
    a, b = np.array(points[0], float), np.array(points[-1], float)
    direction = b - a
    length = np.hypot(*direction)
    worst, index = 0.0, 0
    for i in range(1, len(points) - 1):
        p = np.array(points[i], float)
        if length == 0:
            distance = np.hypot(*(p - a))
        else:
            distance = abs(direction[0] * (p - a)[1] - direction[1] * (p - a)[0]) / length
        if distance > worst:
            worst, index = distance, i
    if worst <= tolerance:
        return [points[0], points[-1]]
    return simplify(points[:index + 1], tolerance)[:-1] + simplify(points[index:], tolerance)


# ---------------------------------------------------------------- geometry helpers

def face_area_normal(vertices, face):
    points = np.array([vertices[i] for i in face["vertices"]], float)
    if len(points) < 3:
        return 0.0, (0.0, 0.0, 0.0)
    cross = np.zeros(3)
    for i in range(1, len(points) - 1):
        cross += np.cross(points[i] - points[0], points[i + 1] - points[0])
    area = np.linalg.norm(cross) / 2.0
    normal = np.array(face["plane_normal"], float) / 65536.0
    return area, tuple(normal)


def family(texture):
    """A texture's style family: MM8's numbered sets (t14a05 -> t14), else the first two letters of the name without
    a world prefix (MM7's Hhm1b3, Hhp1b and 7hhr1el3 -> hh: one human style in three grades; PXSTRRE -> px)."""
    name = texture.lower()
    match = re.match(r"t(\d\d)", name)
    if match:
        return "t" + match.group(1)
    letters = re.match(r"[67]?([a-z]+)", name)
    return letters.group(1)[:2] if letters else name


def cluster(points, link):
    """Single-link clusters of 2D points: a list of index lists."""
    n = len(points)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if math.dist(points[i], points[j]) <= link:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def inside(box, x, y, margin=0.0):
    return box[0] - margin <= x <= box[2] + margin and box[1] - margin <= y <= box[3] + margin


def median(values):
    return float(np.median(values)) if values else None


def share(flags):
    return (sum(1 for f in flags if f) / len(flags)) if flags else None


def angle_diff(a, b, period):
    d = (a - b) % period
    return min(d, period - d)


DENSITY_MERGE = 64     # parts of one building: house-sized model boxes this close or overlapping
DENSITY_YARD = 768     # the built footprint: land within this of a town building's box
STREET_REACH = 3072    # a street's width: the first building box either side of the road's middle, within this


def box_distance(boxes, x, y):
    """Distance from points (x, y arrays) to the nearest of the boxes [(x0, y0, x1, y1)] (0 inside one)."""
    best = np.full(np.shape(x), 1e9)
    for x0, y0, x1, y1 in boxes:
        dx = np.maximum(np.maximum(x0 - x, 0), x - x1)
        dy = np.maximum(np.maximum(y0 - y, 0), y - y1)
        best = np.minimum(best, np.hypot(dx, dy))
    return best


def convex_hull(points):
    points = sorted(set(points))
    if len(points) < 3:
        return points

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def town_density(bmodels, town_doors, roads, worn, water, town_cells):
    """How close the town is built (2026-11-16, after the user found X2's Rivercity "way too much stretched" next to
    Steadwick and Alvar): the town's buildings (house-sized model boxes, parts of one building merged), their number per
    100 cells of built footprint (land within DENSITY_YARD of a building), the gap between neighbours, the open width
    of the streets (building to building across a road's middle) and of the dirt lanes, the largest open circle among
    the buildings (the square), the town's extent for its number of buildings, and the farthest service from the
    town's middle."""
    parts = []
    for model in bmodels:
        if not model["vertices"] or re.search(r"wall|tower|twr|gate|bridge|dock|pier|fence|stall|crag|fall|statue|"
                                              r"well|fountain|shrine|obelisk|boat|ship|tent|cart|wagon|sign|step|"
                                              r"stair|ramp", model["name"], re.I):
            continue
        points = np.array(model["vertices"], float)
        low, high = points.min(axis=0), points.max(axis=0)
        span = high - low
        if min(span[0], span[1]) < 128 or span[2] < 300 or max(span[0], span[1]) > 6000:
            continue
        parts.append([float(low[0]), float(low[1]), float(high[0]), float(high[1])])
    # Merge the parts of one building (shipped houses are split into a few models; a studio plot is one).
    merged = True
    while merged:
        merged = False
        for i in range(len(parts)):
            for j in range(i + 1, len(parts)):
                a, b = parts[i], parts[j]
                gap = max(a[0] - b[2], b[0] - a[2], a[1] - b[3], b[1] - a[3])
                if gap <= DENSITY_MERGE:
                    parts[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    parts.pop(j)
                    merged = True
                    break
            if merged:
                break
    out = {}
    if not parts or not town_doors:
        return out
    # The town's buildings: within TOWN_LINK of a town house door, then of such a building (box to box).
    door_x = np.array([d["x"] for d in town_doors], float)
    door_y = np.array([d["y"] for d in town_doors], float)
    town = {i for i, b in enumerate(parts) if float(box_distance([b], door_x, door_y).min()) <= TOWN_LINK}
    grown = True
    while grown:
        grown = False
        for i, b in enumerate(parts):
            if i in town:
                continue
            for j in town:
                c = parts[j]
                if max(b[0] - c[2], c[0] - b[2], b[1] - c[3], c[1] - b[3]) <= TOWN_LINK:
                    town.add(i)
                    grown = True
                    break
    boxes = [parts[i] for i in sorted(town)]
    count = len(boxes)
    centres = np.array([((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in boxes])
    out["town_buildings"] = count
    # Built footprint on a 128 raster round the buildings.
    step = 128.0
    x0 = min(b[0] for b in boxes) - DENSITY_YARD - step
    y0 = min(b[1] for b in boxes) - DENSITY_YARD - step
    x1 = max(b[2] for b in boxes) + DENSITY_YARD + step
    y1 = max(b[3] for b in boxes) + DENSITY_YARD + step
    gx, gy = np.meshgrid(np.arange(x0, x1, step) + step / 2, np.arange(y0, y1, step) + step / 2)
    near = box_distance(boxes, gx, gy)
    footprint_cells = float((near <= DENSITY_YARD).sum()) * step * step / (CELL * CELL)
    out["town_footprint_cells"] = round(footprint_cells)
    out["town_buildings_per_100_cells"] = round(100.0 * count / footprint_cells, 1) if footprint_cells else None
    built = sum((b[2] - b[0]) * (b[3] - b[1]) for b in boxes) / (CELL * CELL)
    out["town_built_share"] = round(built / footprint_cells, 2) if footprint_cells else None
    # Nearest neighbour: box to box and middle to middle.
    if count >= 2:
        gaps, middles = [], []
        for i, a in enumerate(boxes):
            gaps.append(min(math.hypot(max(a[0] - b[2], b[0] - a[2], 0.0), max(a[1] - b[3], b[1] - a[3], 0.0))
                            for j, b in enumerate(boxes) if j != i))
            others = np.delete(centres, i, axis=0)
            middles.append(float(np.min(np.hypot(others[:, 0] - centres[i, 0], others[:, 1] - centres[i, 1]))))
        out["building_gap_median"] = round(median(gaps))
        out["building_gap_p90"] = round(float(np.percentile(gaps, 90)))
        out["building_nn_median"] = round(median(middles))
        out["building_nn_p90"] = round(float(np.percentile(middles, 90)))
    # Extent: the buildings' bounding box, its side per building and its long/short ratio.
    width = max(b[2] for b in boxes) - min(b[0] for b in boxes)
    height = max(b[3] for b in boxes) - min(b[1] for b in boxes)
    out["town_extent"] = [round(width), round(height)]
    out["town_extent_per_building"] = round(math.sqrt(width * height / count))
    out["town_aspect"] = round(max(width, height) / max(min(width, height), 1.0), 2)
    hull = convex_hull([(b[0], b[1]) for b in boxes] + [(b[2], b[1]) for b in boxes] +
                       [(b[0], b[3]) for b in boxes] + [(b[2], b[3]) for b in boxes])
    if len(hull) >= 3:
        area = 0.5 * abs(sum(hull[k][0] * hull[(k + 1) % len(hull)][1] - hull[(k + 1) % len(hull)][0] * hull[k][1]
                             for k in range(len(hull))))
        out["town_hull_cells_per_building"] = round(area / (CELL * CELL) / count, 2)
    # Streets and lanes: at each middle cell of a road (road tiles) or a dirt lane (worn, not road) in the town, the
    # open width from the first building box on one side to the first on the other, across the way's heading.
    def widths(mask):
        skeleton = thin(mask)
        cells = [(gx_, gy_) for gy_, gx_ in zip(*np.nonzero(skeleton & town_cells))]
        found = []
        middle_points = np.array([cell_centre(a, b) for a, b in zip(*np.nonzero(skeleton)[::-1])]) \
            if skeleton.any() else np.zeros((0, 2))
        ray = np.arange(32.0, STREET_REACH, 32.0)
        for cx_, cy_ in cells:
            px, py = cell_centre(cx_, cy_)
            close = middle_points[np.hypot(middle_points[:, 0] - px, middle_points[:, 1] - py) <= 2.5 * CELL]
            if len(close) < 3:
                continue
            centred = close - close.mean(axis=0)
            _, _, vt = np.linalg.svd(centred, full_matrices=False)
            nx, ny = -vt[0][1], vt[0][0]
            if box_distance(boxes, np.array([px]), np.array([py]))[0] <= 0:
                continue
            sides = []
            for sign in (1.0, -1.0):
                hits = box_distance(boxes, px + sign * nx * ray, py + sign * ny * ray) <= 0
                sides.append(float(ray[np.argmax(hits)]) if hits.any() else None)
            if sides[0] is not None and sides[1] is not None:
                found.append(sides[0] + sides[1])
        return found
    streets = widths(roads)
    lanes = widths(worn & ~roads)
    out["street_width_samples"] = len(streets)
    out["street_width_median"] = round(median(streets)) if streets else None
    out["street_width_p90"] = round(float(np.percentile(streets, 90))) if streets else None
    out["lane_width_samples"] = len(lanes)
    out["lane_width_median"] = round(median(lanes)) if lanes else None
    # The square: the largest circle inside the buildings' hull that holds no building and no water.
    if len(hull) >= 3:
        inside_hull = np.ones(gx.shape, dtype=bool)
        edge = np.full(gx.shape, 1e9)
        for k in range(len(hull)):
            ax, ay = hull[k]
            bx, by = hull[(k + 1) % len(hull)]
            inside_hull &= (bx - ax) * (gy - ay) - (by - ay) * (gx - ax) >= 0
            dx, dy = bx - ax, by - ay
            t = np.clip(((gx - ax) * dx + (gy - ay) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
            edge = np.minimum(edge, np.hypot(gx - ax - t * dx, gy - ay - t * dy))
        water_points = np.array([cell_centre(a, b) for b, a in zip(*np.nonzero(water))]) \
            if water.any() else np.zeros((0, 2))
        water_points = water_points[(water_points[:, 0] > x0 - CELL) & (water_points[:, 0] < x1 + CELL) &
                                    (water_points[:, 1] > y0 - CELL) & (water_points[:, 1] < y1 + CELL)] \
            if len(water_points) else water_points
        clear = np.minimum(near, edge)
        if len(water_points):
            half = CELL / 2
            clear = np.minimum(clear, box_distance([(wx - half, wy - half, wx + half, wy + half)
                                                    for wx, wy in water_points], gx, gy))
        clear[~inside_hull] = 0
        out["open_circle_diameter"] = round(2 * float(clear.max()))
    # The farthest service from the middle of the town's buildings, the services' spread (median distance between
    # two of them: the walk from shop to shop) and how far the middle of the town lies from its nearest building (an
    # empty middle: a river, a field).
    mx, my = centres.mean(axis=0)
    out["middle_to_building"] = round(float(box_distance(boxes, np.array([mx]), np.array([my]))[0]))
    services = [d for d in town_doors if d["kind"] != "House"]
    if services:
        out["farthest_service"] = round(max(math.dist((d["x"], d["y"]), (mx, my)) for d in services))
        out["farthest_service_per_extent"] = round(out["farthest_service"] / math.sqrt(width * height), 2)
    if len(services) >= 2:
        out["service_pair_median"] = round(median([math.dist((a["x"], a["y"]), (b["x"], b["y"]))
                                                   for k, a in enumerate(services) for b in services[k + 1:]]))
    return out


# ---------------------------------------------------------------- measuring

def resolve_map(map_arg, world, assets):
    path = Path(map_arg)
    if not path.exists():
        path = assets / "worlds" / world / "maps" / map_arg
    if not path.exists():
        sys.exit(f"no map {map_arg} (looked in {path})")
    return path


def measure(map_arg, world, assets, town_box=None, project=None):
    path = resolve_map(map_arg, world, assets)
    export = oymap(["export", str(path)])["map"]
    # A project's things come from oymap's private build of it (a built map's path would be read by its name from
    # the asset root, where a project's map is not installed).
    things_target = ([str(project)] if project else [str(path), "--world", world])
    things = oymap(["things"] + things_target + ["--assets", str(assets), "--json"])["things"]
    houses = house_types(assets, world)
    hints = decoration_hints(assets)
    monsters = monster_names(assets, world)
    scene_path = path.with_name(path.stem + ".scene.yml")
    environment = {}
    if scene_path.exists():
        text = scene_path.read_text(encoding="latin-1")[:4000]
        match = re.search(r"master_tile:\s*(\d+)", text)
        lookups = re.search(r"tile_set_lookup_indices:\s*\[([^\]]*)\]", text)
        if match:
            environment["master_tile"] = int(match.group(1))
        if lookups:
            environment["tile_set_lookup_indices"] = [int(v) for v in lookups.group(1).split(",")]
    terrain = export["terrain"]
    bmodels = export["bmodels"]
    # The scene file is what the game reads for decorations and spawn points (a studio build keeps them only there).
    for section in ("entities", "spawns"):
        listed = scene_list(scene_path, section)
        if listed is not None:
            export[section] = listed

    # Houses: every door that enters a house, with its type from house_data.
    doors = []
    for thing in things:
        effects = " ".join(thing["effects"])
        match = re.search(r"EnterHouse\((\d+)\)", effects)
        if thing["kind"] != "house" or not match:
            continue
        house_id = int(match.group(1))
        kind, name = houses.get(house_id, ("?", thing["title"]))
        normal_yaw = thing["yaw"] + math.pi  # thing yaw looks from the stand point at the door; the door faces back
        bmodel = thing["faces"][0] >> 16 if thing["faces"] else -1
        doors.append({"x": thing["middle"][0], "y": thing["middle"][1], "z": thing["middle"][2],
                      "stand": thing["stand"], "kind": kind, "name": name, "id": house_id, "bmodel": bmodel,
                      "yaw": normal_yaw, "door_textures": set(thing["textures"])})
    # One door per house id (a house can have two faces: door and sign).
    seen, unique = set(), []
    for door in doors:
        if door["id"] not in seen:
            seen.add(door["id"])
            unique.append(door)
    doors = unique

    # Town footprint.
    if town_box is None:
        groups = cluster([(d["x"], d["y"]) for d in doors], 4000)
        def weight(group):
            services = sum(1 for i in group if doors[i]["kind"] not in ("House", "Dungeon Ent", "?"))
            return (services, len(group))
        best = max(groups, key=weight) if groups else []
        xs = [doors[i]["x"] for i in best]
        ys = [doors[i]["y"] for i in best]
        town_box = (min(xs) - 1024, min(ys) - 1024, max(xs) + 1024, max(ys) + 1024) if best else (0, 0, 0, 0)
    town_doors = [d for d in doors if inside(town_box, d["x"], d["y"]) and d["kind"] != "Dungeon Ent"]
    # The town is the land within TOWN_REACH of a town house door (inside the box): a footprint that follows the
    # houses rather than the box round them, so the fields between two quarters are not counted as town.
    door_array = np.array([(d["x"], d["y"]) for d in town_doors], float) if town_doors else np.zeros((0, 2))

    def in_town(x, y):
        if not inside(town_box, x, y) or not len(door_array):
            return False
        return float(np.min(np.hypot(door_array[:, 0] - x, door_array[:, 1] - y))) <= TOWN_REACH

    def town_distance(x, y):
        return float(np.min(np.hypot(door_array[:, 0] - x, door_array[:, 1] - y))) if len(door_array) else 1e9

    town_cells = np.zeros((CELLS, CELLS), dtype=bool)
    ring_cells_mask = np.zeros((CELLS, CELLS), dtype=bool)
    for gy in range(CELLS):
        for gx in range(CELLS):
            x, y = cell_centre(gx, gy)
            if in_town(x, y):
                town_cells[gy, gx] = True
            elif town_distance(x, y) <= TOWN_REACH + RING:
                ring_cells_mask[gy, gx] = True
    cx, cy = (door_array.mean(axis=0) if len(door_array) else (0.0, 0.0))
    radius = math.sqrt(max(town_cells.sum(), 1) * CELL * CELL / math.pi)
    figures = {"town_box": [int(v) for v in town_box], "town_radius": round(radius), "centre": [round(cx), round(cy)],
               "town_cells": int(town_cells.sum()),
               "houses_in_town": len(town_doors)}

    # ---- style
    styles = Counter()
    style_of = {}
    for door in town_doors:
        if door["bmodel"] < 0 or door["bmodel"] in style_of:
            continue
        model = bmodels[door["bmodel"]]
        walls, roofs = Counter(), Counter()
        for face in model["faces"]:
            if face["texture"] in door["door_textures"]:
                continue
            area, normal = face_area_normal(model["vertices"], face)
            if abs(normal[2]) < 0.2:
                walls[family(face["texture"])] += area
            elif 0.2 <= normal[2] < 0.97:
                roofs[family(face["texture"])] += area
        wall = walls.most_common(1)[0][0] if walls else "-"
        roof = roofs.most_common(1)[0][0] if roofs else "flat"
        style_of[door["bmodel"]] = f"{wall}/{roof}"
        styles[f"{wall}/{roof}"] += 1
    total = sum(styles.values())
    figures["styles"] = dict(styles.most_common())
    figures["style_count_10pct"] = sum(1 for v in styles.values() if total and v / total >= 0.10)
    figures["main_style_share"] = round(styles.most_common(1)[0][1] / total, 2) if total else None
    # Shapes: one signature per house model (face count, footprint sides sorted, height, to 128 units), so the same
    # model turned or copied counts once.
    shapes = Counter()
    for index in style_of:
        model = bmodels[index]
        points = np.array(model["vertices"], float) if model["vertices"] else np.zeros((1, 3))
        span = points.max(axis=0) - points.min(axis=0)
        sides = sorted((int(span[0] // 128), int(span[1] // 128)))
        shapes[(len(model["faces"]), sides[0], sides[1], int(span[2] // 128))] += 1
    figures["house_shapes"] = len(shapes)
    figures["main_shape_share"] = round(shapes.most_common(1)[0][1] / total, 2) if total else None
    figures["shape_variety"] = round(len(shapes) / total, 2) if total else None
    wall_families = Counter(s.split("/")[0] for s in style_of.values())
    figures["main_wall_share"] = round(wall_families.most_common(1)[0][1] / total, 2) if total else None

    # ---- roads
    roads, worn, water = ground_masks(world, terrain, export.get("tile_set_lookup", []), assets, environment)
    skeleton = thin(roads)
    turns, runs, axis_length, total_length = [], [], 0.0, 0.0
    junction_angles = []
    town_chains = road_chains(skeleton & town_cells)
    branches = {}
    for chain in town_chains:
        if len(chain) >= 3:
            branches.setdefault(chain[0], []).append(chain[min(3, len(chain) - 1)])
            branches.setdefault(chain[-1], []).append(chain[max(len(chain) - 4, 0)])
    for node, ends in branches.items():
        if len(ends) < 3:
            continue
        headings = sorted(math.atan2(e[1] - node[1], e[0] - node[0]) for e in ends)
        for a, b in zip(headings, headings[1:] + [headings[0] + 2 * math.pi]):
            junction_angles.append(math.degrees(b - a))
    for chain in town_chains:
        simple = simplify(chain, 0.75)
        for a, b in zip(simple, simple[1:]):
            length = math.dist(a, b) * CELL
            runs.append(length)
            total_length += length
            heading = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
            if angle_diff(heading, 0, 90) <= 10:
                axis_length += length
        for a, b, c in zip(simple, simple[1:], simple[2:]):
            h1 = math.atan2(b[1] - a[1], b[0] - a[0])
            h2 = math.atan2(c[1] - b[1], c[0] - b[0])
            turns.append(math.degrees(angle_diff(h1, h2, 2 * math.pi)))
    figures["road_cells_in_town"] = int((roads & town_cells).sum())
    figures["road_share_town"] = round(float((roads & town_cells).sum() / max(town_cells.sum(), 1)), 2)
    figures["worn_share_town"] = round(float((worn & town_cells).sum() / max(town_cells.sum(), 1)), 2)
    figures["road_turns"] = len(turns)
    figures["road_turn_median_deg"] = round(median(turns), 1) if turns else None
    figures["road_turn_90_share"] = round(share([80 <= t <= 100 for t in turns]), 2) if turns else None
    figures["road_turn_45_share"] = round(share([35 <= t <= 55 for t in turns]), 2) if turns else None
    figures["junctions"] = sum(1 for ends in branches.values() if len(ends) >= 3)
    figures["junction_90_share"] = round(share([80 <= a <= 100 for a in junction_angles]), 2) \
        if junction_angles else None
    figures["road_run_median"] = round(median(runs)) if runs else None
    figures["road_run_max"] = round(max(runs)) if runs else None
    figures["road_axis_share"] = round(axis_length / total_length, 2) if total_length else None

    road_points = [cell_centre(gx, gy) for gy, gx in zip(*np.nonzero(worn))]
    road_array = np.array(road_points) if road_points else np.zeros((0, 2))
    skeleton_points = np.array([cell_centre(gx, gy) for gy, gx in zip(*np.nonzero(skeleton))]) \
        if skeleton.any() else np.zeros((0, 2))
    path_lengths, faces_road = [], []
    axis_doors = []
    for door in town_doors:
        axis_doors.append(math.degrees(angle_diff(door["yaw"], 0, math.pi / 2)) <= 5)
        if not len(road_array):
            continue
        sx, sy = door["stand"][0], door["stand"][1]
        distances = np.hypot(road_array[:, 0] - sx, road_array[:, 1] - sy)
        path_lengths.append(float(distances.min()))
        near = skeleton_points[np.hypot(skeleton_points[:, 0] - sx, skeleton_points[:, 1] - sy) < 4 * CELL] \
            if len(skeleton_points) else []
        if len(near) >= 3:
            centred = near - near.mean(axis=0)
            _, _, vt = np.linalg.svd(centred, full_matrices=False)
            road_heading = math.atan2(vt[0][1], vt[0][0])
            between = math.degrees(angle_diff(door["yaw"], road_heading, math.pi))
            faces_road.append(abs(90 - between))
    figures["door_axis_share"] = round(share(axis_doors), 2) if axis_doors else None
    figures["door_to_road_median"] = round(median(path_lengths)) if path_lengths else None
    figures["door_road_within_1024_share"] = round(share([d <= 1024 for d in path_lengths]), 2) \
        if path_lengths else None
    figures["door_vs_road_dev_median_deg"] = round(median(faces_road), 1) if faces_road else None
    figures["door_square_to_road_share"] = round(share([d <= 15 for d in faces_road]), 2) if faces_road else None

    # Mirror symmetry of the house doors about any axis through the town centre.
    points = np.array([(d["x"], d["y"]) for d in town_doors], float)
    best_mirror = 0.0
    if len(points) >= 4:
        centre = points.mean(axis=0)
        for degrees in range(0, 180, 5):
            theta = math.radians(degrees)
            axis = np.array([math.cos(theta), math.sin(theta)])
            rel = points - centre
            along = rel @ axis
            mirrored = centre + 2 * np.outer(along, axis) - rel
            matched = 0
            for i, m in enumerate(mirrored):
                distances = np.hypot(points[:, 0] - m[0], points[:, 1] - m[1])
                distances[i] = 1e9
                if distances.min() <= 512:
                    matched += 1
            best_mirror = max(best_mirror, matched / len(points))
    figures["mirror_share"] = round(best_mirror, 2)

    # ---- services
    kinds = Counter(d["kind"] for d in town_doors)
    figures["services"] = {k: v for k, v in kinds.items() if k != "House"}
    figures["service_count"] = sum(v for k, v in kinds.items() if k != "House")
    figures["residence_count"] = kinds.get("House", 0)

    def of(group):
        names = SERVICE_GROUPS[group]
        return [d for d in town_doors if d["kind"] in names]

    def nearest_pair(a_list, b_list):
        pairs = [math.dist((a["x"], a["y"]), (b["x"], b["y"])) for a in a_list for b in b_list if a is not b]
        return round(min(pairs)) if pairs else None

    figures["weapon_armour_dist"] = nearest_pair(of("weapon"), of("armour"))
    figures["magic_alchemist_dist"] = nearest_pair(of("magic"), of("alchemist"))
    guilds = [d for d in town_doors if "guild" in d["kind"].lower() and "thieves" not in d["kind"].lower()]
    if len(guilds) >= 2:
        nearest = [min(math.dist((g["x"], g["y"]), (h["x"], h["y"])) for h in guilds if h is not g) for g in guilds]
        figures["guild_nearest_median"] = round(median(nearest))
    else:
        figures["guild_nearest_median"] = None
    all_points = [(d["x"], d["y"]) for d in town_doors]

    def nearest_other_service(door):
        others = [math.dist((door["x"], door["y"]), (o["x"], o["y"])) for o in town_doors
                  if o is not door and o["kind"] != "House"]
        return min(others) if others else None

    # Arrival: party start markers (where the party enters the map) and the coach and boat houses.
    starts = [(e["position"][0], e["position"][1]) for e in export["entities"] if "start" in e["name"].lower()]
    arrivals = starts + [(d["x"], d["y"]) for d in town_doors if d["kind"] in ("Stables", "Boats")]

    def edge_rank(door):
        """0 at the town centre, 1 at its furthest house: the door's rank among all houses by distance from centre."""
        mine = math.dist((door["x"], door["y"]), (cx, cy))
        return sum(1 for p in all_points if math.dist(p, (cx, cy)) < mine) / max(len(all_points) - 1, 1)

    def arrival_rank(door):
        if not arrivals:
            return None
        def to_arrival(p):
            return min(math.dist(p, a) for a in arrivals if math.dist(a, (door["x"], door["y"])) > 64 or True)
        mine = to_arrival((door["x"], door["y"]))
        return sum(1 for p in all_points if to_arrival(p) < mine) / max(len(all_points) - 1, 1)

    for group in ("tavern", "stables", "boats", "temple", "training", "bank", "town_hall"):
        members = of(group)
        figures[f"{group}_edge_rank"] = round(min(edge_rank(d) for d in members), 2) if members else None
    taverns = of("tavern")
    figures["tavern_arrival_rank"] = round(min(arrival_rank(d) for d in taverns), 2) \
        if taverns and starts else None
    shops = [d for d in town_doors if d["kind"] not in ("House",)]
    figures["service_nearest_median"] = round(median([v for v in (nearest_other_service(d) for d in shops)
                                                      if v is not None])) if len(shops) >= 2 else None

    # ---- monsters
    actors = scene_actors(scene_path)
    hostile = [a for a in actors if is_hostile(a.get("id", 0), monsters, a.get("attributes", 0))]
    friendly = len(actors) - len(hostile)
    groups = []
    for members in cluster([(a["x"], a["y"]) for a in hostile], 768):
        xs = [hostile[i]["x"] for i in members]
        ys = [hostile[i]["y"] for i in members]
        groups.append({"x": sum(xs) / len(xs), "y": sum(ys) / len(ys), "size": len(members), "kind": "actors"})
    slots = spawn_counts(assets, path.name, world)
    slot_hostile = []
    for mean, picture in slots:
        monster_id = monster_by_picture(monsters, picture) if picture else None
        slot_hostile.append(bool(picture) and (monster_id is None or is_hostile(monster_id, monsters)))
    for spawn in export["spawns"]:
        if spawn["type_id"] != 3:
            continue
        index = spawn["index"]
        # As the game reads it (game/SpawnPreview.cpp): 1-3 a group of M1-M3 by the map_stats dice, 4-12 one
        # monster of M1-M3 at a fixed tier A-C; other indices spawn nothing.
        if 1 <= index <= 3:
            slot = index - 1
            size = slots[slot][0]
        elif 4 <= index <= 12:
            slot = (index - 4) % 3
            size = 1.0 if slots[slot][1] else 0.0
        else:
            continue
        if not slot_hostile[slot] or size <= 0:
            continue
        groups.append({"x": spawn["position"][0], "y": spawn["position"][1], "size": size, "kind": "spawn"})
    chests = [(t["middle"][0], t["middle"][1]) for t in things if t["kind"] == "chest"]
    entrances = [(t["middle"][0], t["middle"][1]) for t in things
                 if t["kind"] == "exit" and re.search(r"\.blv", " ".join(t["effects"]), re.I)]
    entrances += [(d["x"], d["y"]) for d in doors if d["kind"] == "Dungeon Ent"]
    bridges = [((b["min"][0] + b["max"][0]) / 2, (b["min"][1] + b["max"][1]) / 2) for b in bmodels
               if "bridge" in b["name"].lower()]
    # bmodel min/max of the export are not reliable boxes; use vertex means for bridges
    bridges = [tuple(np.array(b["vertices"])[:, :2].mean(axis=0)) for b in bmodels
               if "bridge" in b["name"].lower() and b["vertices"]]
    camps = [(e["position"][0], e["position"][1]) for e in export["entities"]
             if re.search(r"campfire|fire|tent", hints.get(e["name"].lower(), ""))]
    camps += [tuple(np.array(b["vertices"])[:, :2].mean(axis=0)) for b in bmodels
              if re.search(r"tent|fire pit|camp", b["name"].lower()) and b["vertices"]]
    guard_points = chests + entrances + bridges + camps

    def nearest(point, targets):
        return min(math.dist(point, t) for t in targets) if targets else None

    wild = [g for g in groups if not in_town(g["x"], g["y"])]
    figures["hostile_actors"] = len(hostile)
    figures["friendly_actors"] = friendly
    figures["spawn_markers"] = sum(1 for g in groups if g["kind"] == "spawn")
    figures["monster_groups"] = len(groups)
    figures["group_size_median"] = round(median([g["size"] for g in groups]), 1) if groups else None
    figures["group_size_max"] = round(max(g["size"] for g in groups), 1) if groups else None
    figures["monsters_total_est"] = round(sum(g["size"] for g in groups))
    figures["groups_on_guard_share"] = round(share([nearest((g["x"], g["y"]), guard_points) is not None and
                                                    nearest((g["x"], g["y"]), guard_points) <= 2000
                                                    for g in wild]), 2) if wild and guard_points else None
    figures["group_to_chest_median"] = round(median([nearest((g["x"], g["y"]), chests) for g in wild])) \
        if wild and chests else None
    figures["group_to_entrance_median"] = round(median([nearest((g["x"], g["y"]), entrances) for g in wild])) \
        if wild and entrances else None
    wild_chests = [c for c in chests if not in_town(c[0], c[1])]
    figures["groups_per_wild_chest_median"] = median([sum(1 for g in groups if math.dist(c, (g["x"], g["y"])) <=
                                                         2500) for c in wild_chests]) if wild_chests else None
    figures["groups_in_town"] = sum(1 for g in groups if in_town(g["x"], g["y"]))
    clear = sorted(town_distance(g["x"], g["y"]) for g in groups)
    figures["group_to_house_min"] = round(clear[0]) if clear else None
    figures["group_to_house_p10"] = round(clear[len(clear) // 10]) if clear else None
    # Spacing between monster groups in the wild (nearest neighbour).
    if len(wild) >= 2:
        spacing = [min(math.dist((g["x"], g["y"]), (h["x"], h["y"])) for h in wild if h is not g) for g in wild]
        figures["group_spacing_median"] = round(median(spacing))
        figures["group_spacing_cv"] = round(float(np.std(spacing) / np.mean(spacing)), 2)
    else:
        figures["group_spacing_median"] = figures["group_spacing_cv"] = None
    # How many the party meets: per land cell (not water) and, travelling, within 1500 of a road outside the town
    # per 1000 units of road (the road-tile skeleton outside the town).
    land_cells = max(int((~water).sum()), 1)
    figures["land_cells"] = land_cells
    figures["monsters_per_100_land_cells"] = round(100.0 * figures["monsters_total_est"] / land_cells, 2)
    wild_road = skeleton & ~town_cells
    road_cells_wild = [cell_centre(gx, gy) for gy, gx in zip(*np.nonzero(roads & ~town_cells))]
    road_wild_array = np.array(road_cells_wild) if road_cells_wild else np.zeros((0, 2))
    near_road = 0.0
    for g in wild:
        if len(road_wild_array) and float(np.min(np.hypot(road_wild_array[:, 0] - g["x"],
                                                          road_wild_array[:, 1] - g["y"]))) <= 1500:
            near_road += g["size"]
    road_length = int(wild_road.sum()) * CELL
    figures["wild_road_length"] = road_length
    figures["monsters_near_road"] = round(near_road)
    # Island maps with a road stub (Dagger Wound, Emerald Island: under 30,000 of road) say nothing about travel.
    figures["monsters_per_1000_road"] = round(1000.0 * near_road / road_length, 2) if road_length >= 30000 else None
    sizes = [g["size"] for g in groups]
    figures["group_1_share"] = round(share([s < 1.5 for s in sizes]), 2) if sizes else None
    figures["group_2_3_share"] = round(share([1.5 <= s < 3.5 for s in sizes]), 2) if sizes else None
    figures["group_4plus_share"] = round(share([s >= 3.5 for s in sizes]), 2) if sizes else None
    figures["largest_groups"] = sorted((round(s, 1) for s in sizes), reverse=True)[:5]

    # ---- town spread: the built footprint of the town (house-sized models, which shipped maps split into parts: each
    # weighted by its footprint): the models within TOWN_LINK of a town house door, then any within TOWN_LINK of
    # those (unenterable homes on the fringe), measured from the services' centroid. Core radius = the
    # footprint-weighted median distance; the fringe = its 90th percentile.
    buildings = []
    for model in bmodels:
        if not model["vertices"] or re.search(r"wall|tower|twr|gate|bridge|dock|pier|fence|stall|crag|fall|statue|"
                                              r"well|fountain|shrine|obelisk|boat|ship|tent|cart|wagon|sign|step|"
                                              r"stair|ramp", model["name"], re.I):
            continue
        points = np.array(model["vertices"], float)
        span = points.max(axis=0) - points.min(axis=0)
        if min(span[0], span[1]) < 256 or span[2] < 300 or max(span[0], span[1]) > 6000:
            continue
        buildings.append((tuple(points[:, :2].mean(axis=0)), float(span[0] * span[1])))
    service_points = [(d["x"], d["y"]) for d in town_doors if d["kind"] != "House"] or \
        [(d["x"], d["y"]) for d in town_doors]
    if buildings and service_points:
        town_cluster = {i for i, (c, _) in enumerate(buildings)
                        if any(math.dist(c, (d["x"], d["y"])) <= TOWN_LINK for d in town_doors)}
        grown = True
        while grown:
            grown = False
            for i, (c, _) in enumerate(buildings):
                if i not in town_cluster and any(math.dist(c, buildings[j][0]) <= TOWN_LINK for j in town_cluster):
                    town_cluster.add(i)
                    grown = True
        sx, sy = np.mean(service_points, axis=0)
        pairs = sorted((math.dist(buildings[i][0], (sx, sy)), buildings[i][1]) for i in town_cluster)
    else:
        pairs = []
    # A town of stalls (D3's Crossroads: a ring of market stalls, no house-sized model near its doors) has no spread.
    if pairs:
        weights = np.cumsum([w for _, w in pairs]) / sum(w for _, w in pairs)

        def at(q):
            return pairs[int(np.searchsorted(weights, q))][0]
        core = at(0.5)
        figures["town_built_area"] = round(sum(w for _, w in pairs) / (CELL * CELL), 1)
        figures["town_core_radius"] = round(core)
        figures["town_spread_p90"] = round(at(0.9))
        figures["town_farthest_house"] = round(pairs[-1][0])
        figures["town_fringe_ratio"] = round(at(0.9) / core, 2) if core else None
        figures["town_farthest_ratio"] = round(pairs[-1][0] / core, 2) if core else None
        figures["town_outer_share"] = round(sum(w for d, w in pairs if d > 1.5 * core) /
                                            sum(w for _, w in pairs), 2)

    figures.update(town_density(bmodels, town_doors, roads, worn, water, town_cells))

    # ---- props
    area_cells = max(int(town_cells.sum()), 1)
    ring_cells = max(int(ring_cells_mask.sum()), 1)
    counts = {"in": Counter(), "ring": Counter()}
    for entity in export["entities"]:
        x, y = entity["position"][0], entity["position"][1]
        gx, gy = cell_of(x, y)
        if not (0 <= gx < CELLS and 0 <= gy < CELLS):
            continue
        where = "in" if town_cells[gy, gx] else ("ring" if ring_cells_mask[gy, gx] else None)
        if where is None:
            continue
        hint = hints.get(entity["name"].lower(), entity["name"].lower())
        if "start" in entity["name"].lower() or hint in ("null", "test", "?", "") or entity["name"].startswith("snd"):
            continue
        if TREE.search(hint):
            counts[where]["tree"] += 1
        elif GREEN.search(hint):
            counts[where]["green"] += 1
        elif ROCK.search(hint):
            counts[where]["rock"] += 1
        elif THEMATIC.search(hint):
            counts[where]["thematic"] += 1
        else:
            counts[where]["other"] += 1
    thematic_models = Counter()
    for model in bmodels:
        if not model["vertices"]:
            continue
        x, y = np.array(model["vertices"])[:, :2].mean(axis=0)
        if in_town(x, y) and THEMATIC.search(model["name"]) and \
                not re.search(r"house|guild|tavern|temple|shop|bank|stable|hall", model["name"], re.I):
            thematic_models[re.sub(r"[_\d ]+[nsewa-c]?$", "", model["name"].lower())] += 1
    for key in ("tree", "green", "rock", "thematic"):
        figures[f"{key}_per_cell_town"] = round(counts["in"][key] / area_cells, 3)
        figures[f"{key}_per_cell_ring"] = round(counts["ring"][key] / ring_cells, 3)
    figures["thematic_models_town"] = sum(thematic_models.values())
    figures["thematic_kinds_town"] = len(thematic_models) + len([k for k in ("thematic",) if counts["in"][k]])
    figures["thematic_model_names"] = dict(thematic_models.most_common(12))

    # ---- specials: wells, fountains, shrines, altars, obelisks, pedestals
    specials = []
    for thing in things:
        title = thing["title"] or ""
        textures = " ".join(thing["textures"])
        if not (SPECIAL_TITLE.search(title) or re.search(r"ped\d|pedast", textures, re.I)):
            continue
        effects = " ".join(thing["effects"])
        kind = "obelisk" if "obelisk" in title.lower() else \
            "shrine" if re.search(r"shrine|altar", title, re.I) else \
            "pedestal" if re.search(r"pedestal|pedastal|ped\d", title + textures, re.I) else "well/fountain"
        if "OpenDimensionDoor" in effects:
            continue
        buff = bool(BUFF.search(effects))
        x, y = thing["middle"][0], thing["middle"][1]
        specials.append({"kind": kind, "buff": buff, "in_town": in_town(x, y),
                         "rank": round(math.dist((x, y), (cx, cy)) / radius, 2), "title": title})
    figures["wells_fountains"] = sum(1 for s in specials if s["kind"] == "well/fountain")
    figures["wells_fountains_in_town"] = sum(1 for s in specials if s["kind"] == "well/fountain" and s["in_town"])
    figures["buff_specials"] = sum(1 for s in specials if s["buff"])
    figures["buff_specials_in_town"] = sum(1 for s in specials if s["buff"] and s["in_town"])
    figures["shrines_altars"] = sum(1 for s in specials if s["kind"] == "shrine")
    figures["obelisks"] = sum(1 for s in specials if s["kind"] == "obelisk")

    # ---- terrain in the footprint
    heights = np.array(terrain["height_map"], float).reshape(CELLS, CELLS) * terrain.get("height_scale", 32)
    if town_cells.any():
        patch = heights[town_cells]
        figures["height_range"] = int(np.percentile(patch, 95) - np.percentile(patch, 5))
        rise_y = np.abs(np.diff(heights, axis=0))[town_cells[:-1, :] & town_cells[1:, :]]
        rise_x = np.abs(np.diff(heights, axis=1))[town_cells[:, :-1] & town_cells[:, 1:]]
        slopes = np.concatenate([rise_x, rise_y]) / CELL
        figures["slope_p90"] = round(float(np.percentile(slopes, 90)), 3)
        figures["flat_share"] = round(float((slopes <= 0.02).mean()), 2)
        base = [d["stand"][2] for d in town_doors]
        figures["door_level_range"] = int(np.percentile(base, 90) - np.percentile(base, 10)) if base else None
    return figures


# ---------------------------------------------------------------- rules

def load_rules(start=False, small=False):
    ranges = dict(SHIPPED_RANGES, **(START_RANGES if start else {}), **(SMALL_RANGES if small else {}))
    return [(key, label, ranges[key][0], ranges[key][1]) for key, label in RULE_LABELS if key in ranges]


RULE_LABELS = [
    ("main_wall_share", "share of houses in the main wall family"),
    ("style_count_10pct", "house styles (wall/roof) with 10% or more of the houses"),
    ("main_style_share", "share of houses in the main style"),
    ("main_shape_share", "share of houses that are the most common model shape"),
    ("shape_variety", "distinct house shapes per house"),
    ("door_axis_share", "doors facing a compass axis (within 5 deg)"),
    ("mirror_share", "houses with a mirror partner (best axis)"),
    ("door_road_within_1024_share", "doors with a road or dirt lane within 1024"),
    ("door_to_road_median", "door to nearest road or dirt lane, median"),
    ("worn_share_town", "town cells of road or dirt (lanes, plazas)"),
    ("road_axis_share", "road length on compass axes (+-10 deg)"),
    ("road_turn_90_share", "road turns of 80-100 deg"),
    ("road_turn_median_deg", "road turn, median deg"),
    ("junction_90_share", "junction branch angles of 80-100 deg"),
    ("road_run_median", "straight road run, median"),
    ("road_run_max", "straight road run, longest"),
    ("service_count", "services in town"),
    ("residence_count", "enterable residences in town"),
    ("weapon_armour_dist", "weapon shop to armour shop"),
    ("magic_alchemist_dist", "magic shop to alchemist"),
    ("guild_nearest_median", "guild to nearest guild, median"),
    ("service_nearest_median", "service to nearest service, median"),
    ("tavern_edge_rank", "tavern rank from centre (0 centre, 1 edge)"),
    ("tavern_arrival_rank", "tavern rank by distance to arrival (0 nearest)"),
    ("stables_edge_rank", "stables rank from centre"),
    ("boats_edge_rank", "boats rank from centre"),
    ("temple_edge_rank", "temple rank from centre"),
    ("groups_in_town", "monster groups inside the town"),
    ("group_to_house_min", "nearest monster group to a town house door"),
    ("group_to_house_p10", "monster group to town house, 10th percentile"),
    ("group_size_median", "monster group size, median"),
    ("group_size_max", "monster group size, largest"),
    ("monster_groups", "monster groups on the map"),
    ("monsters_total_est", "monsters on the map (est.)"),
    ("monsters_per_100_land_cells", "monsters per 100 land cells (not water)"),
    ("monsters_per_1000_road", "monsters within 1500 of a wild road per 1000 of road"),
    ("group_1_share", "monster groups of one"),
    ("group_4plus_share", "monster groups of four or more"),
    ("groups_on_guard_share", "wild groups within 2000 of a chest/entrance/bridge/camp"),
    ("group_to_chest_median", "wild group to nearest chest, median"),
    ("group_to_entrance_median", "wild group to nearest dungeon entrance, median"),
    ("groups_per_wild_chest_median", "groups within 2500 of a wild chest, median"),
    ("group_spacing_median", "wild group to nearest group, median"),
    ("group_spacing_cv", "wild group spacing variation (std/mean)"),
    ("tree_per_cell_town", "trees per cell in town"),
    ("green_per_cell_town", "flowers/plants/bushes per cell in town"),
    ("rock_per_cell_town", "rocks per cell in town"),
    ("thematic_per_cell_town", "thematic sprites per cell in town"),
    ("thematic_models_town", "thematic models in town (wells, carts, signs, docks...)"),
    ("tree_per_cell_ring", "trees per cell around the town (3072 ring)"),
    ("green_per_cell_ring", "flowers/plants per cell around the town"),
    ("rock_per_cell_ring", "rocks per cell around the town"),
    ("wells_fountains", "wells and fountains on the map"),
    ("wells_fountains_in_town", "wells and fountains in town"),
    ("buff_specials", "buff/stat wells, fountains, altars on the map"),
    ("buff_specials_in_town", "buff/stat specials in town"),
    ("obelisks", "obelisks on the map"),
    ("height_range", "terrain height range in town (p5-p95)"),
    ("slope_p90", "terrain slope p90 in town (rise/run)"),
    ("flat_share", "flat terrain share in town (slope <= 0.02)"),
    ("door_level_range", "door level range p10-p90"),
    ("town_spread_p90", "town spread: built footprint's 90th pct distance from the services"),
    ("town_farthest_house", "town spread: farthest building from the services"),
    ("town_fringe_ratio", "town fringe / core (p90 / median distance)"),
    ("town_farthest_ratio", "town farthest / core (farthest / median distance)"),
    ("town_outer_share", "town footprint beyond 1.5 x the core radius"),
    # 2026-11-16 (town_density): how close the town is built
    ("town_buildings_per_100_cells", "buildings per 100 cells of built footprint (768 round each)"),
    ("town_built_share", "built footprint covered by buildings"),
    ("building_gap_median", "building to nearest building, wall to wall, median"),
    ("building_gap_p90", "building to nearest building, wall to wall, 90th percentile"),
    ("building_nn_median", "building to nearest building, middle to middle, median"),
    ("building_nn_p90", "building to nearest building, middle to middle, 90th pct"),
    ("town_extent_per_building", "town extent per building (sqrt of box area / buildings)"),
    ("street_width_median", "street width, house to house across the road, median"),
    ("open_circle_diameter", "largest open circle among the buildings (the square)"),
    ("farthest_service", "farthest service from the middle of the buildings"),
    ("service_pair_median", "service to service, median of every pair"),
    ("town_core_radius", "town core radius (footprint-weighted median from services)"),
]

# Min and max over the thirteen shipped towns of SHIPPED (Bracada's Celeste approach left out: three houses round a
# stable, no town; the four small towns too, SMALL_RANGES), from `town_feel.py --shipped --json` on 2026-11-13; the monster figures and the town spread
# again on 2026-11-14 (spawn indices read as the game reads them). Regenerate after a change to the measures.
SHIPPED_RANGES = {
    "main_wall_share": (0.39, 1.0),
    "style_count_10pct": (1, 4),
    "main_style_share": (0.19, 1.0),
    "main_shape_share": (0.06, 0.41),
    "shape_variety": (0.42, 0.96),
    "door_axis_share": (0.77, 1.0),
    "mirror_share": (0.19, 0.61),
    "door_road_within_1024_share": (0.81, 1.0),
    "door_to_road_median": (147, 381),
    "worn_share_town": (0.37, 0.98),
    "road_axis_share": (0.66, 1.0),
    "road_turn_90_share": (0.36, 1.0),
    "road_turn_median_deg": (45.0, 90.0),
    "junction_90_share": (0.17, 0.6),
    "road_run_median": (1024, 3072),
    "road_run_max": (3072, 5655),
    "service_count": (6, 25),
    "residence_count": (8, 56),
    "weapon_armour_dist": (384, 5830),
    "magic_alchemist_dist": (1147, 5677),
    "guild_nearest_median": (512, 10156),
    "service_nearest_median": (1012, 2424),
    "tavern_edge_rank": (0.09, 0.86),
    "tavern_arrival_rank": (0.05, 0.95),
    "stables_edge_rank": (0.0, 0.81),
    "boats_edge_rank": (0.68, 1.0),
    "temple_edge_rank": (0.0, 1.0),
    "groups_in_town": (0, 7),
    "group_to_house_min": (171, 6796),
    "group_to_house_p10": (1096, 13090),
    "group_size_median": (1.0, 4.5),
    "group_size_max": (1.0, 16),
    "monster_groups": (18, 88),
    "monsters_total_est": (47, 377),
    "monsters_per_100_land_cells": (0.47, 4.26),
    "monsters_per_1000_road": (0.03, 0.58),
    "group_1_share": (0.0, 1.0),
    "group_4plus_share": (0.0, 1.0),
    "groups_on_guard_share": (0.0, 0.79),
    "group_to_chest_median": (1436, 25928),
    "group_to_entrance_median": (7438, 23867),
    "groups_per_wild_chest_median": (0.0, 7.0),
    "group_spacing_median": (403, 2433),
    "group_spacing_cv": (0.46, 2.08),
    "tree_per_cell_town": (0.008, 0.13),
    "green_per_cell_town": (0.0, 0.244),
    "rock_per_cell_town": (0.0, 0.072),
    "thematic_per_cell_town": (0.0, 0.056),
    "thematic_models_town": (1, 31),
    "tree_per_cell_ring": (0.011, 0.186),
    "green_per_cell_ring": (0.0, 0.096),
    "rock_per_cell_ring": (0.0, 0.039),
    "wells_fountains": (3, 8),
    "wells_fountains_in_town": (0, 5),
    "buff_specials": (0, 7),
    "buff_specials_in_town": (0, 3),
    "obelisks": (1, 1),
    "height_range": (0, 2080),
    "slope_p90": (0.0, 0.481),
    "flat_share": (0.73, 0.97),
    "door_level_range": (0, 680),
    "town_spread_p90": (4358, 13228),
    "town_farthest_house": (4711, 17027),
    "town_fringe_ratio": (1.29, 3.79),
    "town_farthest_ratio": (1.43, 5.06),
    "town_outer_share": (0.0, 0.38),
    # town_density (2026-11-16, `--shipped --json`, the same thirteen towns): Steadwick 6.3 / 0.22 / 398 / 1274 /
    # 1178 / 2328 / 2285 / 2464 / 2851 / 8539 / 6595 / 3540; Alvar 6.0 / 0.26 / 530 / 754 / 1449 / 2023 / 2772 / 992 /
    # 5100 / 12196 / 4574 / 4803. Printed but not judged: lane_width_median (dirt lanes, 1472-2912: in shipped towns
    # the worn ground round the houses), middle_to_building (0-767: a river town's middle is its river),
    # town_aspect (1.0-2.18), town_hull_cells_per_building (6.76-30.93).
    "town_buildings_per_100_cells": (3.6, 11.2),
    "town_built_share": (0.21, 0.37),
    "building_gap_median": (162, 744),
    "building_gap_p90": (411, 1358),
    "building_nn_median": (913, 2233),
    "building_nn_p90": (1265, 2850),
    "town_extent_per_building": (1413, 3576),
    "street_width_median": (512, 3168),
    "open_circle_diameter": (1802, 5602),
    "farthest_service": (3918, 16598),
    "service_pair_median": (2909, 8789),
    "town_core_radius": (2626, 6552),
}

# --start: a start or early map is judged by the five that open the shipped games (Emerald Island 7out01,
# Harmondale 7out02, Dagger Wound out01, Ravenshore out02, New Sorpigal oute3), 2026-11-14: their monsters are denser
# than the later towns' maps (Tularean Forest 0.47 a hundred land cells, Erathia's groups of 1-2). The road figure from
# the three with more than 30,000 of road. Their towns sprawl less than Garrote Gorge (fringe 3.79, a town strung
# along a gorge) and Tatalia (0.38 of the footprint beyond 1.5 x the core).
START_RANGES = {
    "monsters_per_100_land_cells": (1.55, 3.36),
    "monsters_per_1000_road": (0.18, 0.32),
    "group_1_share": (0.01, 0.33),
    "group_4plus_share": (0.13, 0.85),
    "group_size_max": (3.5, 16),
    "town_fringe_ratio": (1.29, 2.18),
    "town_farthest_ratio": (1.59, 2.81),
    "town_outer_share": (0.03, 0.29),
}

# --small (decision D-20, 2026-11-20): a town of nine services or fewer (Xeen's Nightshadow) is judged on its size
# figures by the thirteen towns and the four small towns the main ranges leave out (Deyja 7out05, Mount Nighon out10,
# Paradise Valley outa2, Kriegspire outb1; measured 2026-11-20: services 5-7, residences 6-16, nearest service
# 854-1891, tavern rank 0-0.94, built share 0.15-0.32, farthest service 3203-5585, service pairs 1526-5169, core
# radius 2360-4141), and the spread and magic shop to alchemist have no lower bound.
SMALL_RANGES = {
    "service_count": (5, 25),
    "residence_count": (6, 56),
    "service_nearest_median": (854, 2424),
    "tavern_edge_rank": (0.0, 0.94),
    "town_built_share": (0.15, 0.37),
    "farthest_service": (3203, 16598),
    "service_pair_median": (1526, 8789),
    "town_core_radius": (2360, 6552),
    "town_spread_p90": (None, 13228),
    "town_farthest_house": (None, 17027),
    "magic_alchemist_dist": (None, 5677),
}


def report(name, figures, rules):
    print(f"== {name}")
    print(f"   town box {figures['town_box']} radius {figures['town_radius']}, houses {figures['houses_in_town']}")
    print(f"   styles {figures['styles']}")
    print(f"   services {figures['services']}")
    print(f"   thematic models {figures['thematic_model_names']}")
    outside = 0
    for key, label, low, high in rules:
        value = figures.get(key)
        if value is None:
            mark = "  n/a"
        elif (low is not None and value < low) or (high is not None and value > high):
            mark = "  OUT"
            outside += 1
        else:
            mark = "   ok"
        span = f"{low if low is not None else '-'} .. {high if high is not None else '-'}"
        print(f"{mark} {label:58s} {str(value):>8s}   shipped {span}")
    print(f"   {outside} figure(s) outside the shipped ranges")
    return outside


def report_json(name, figures, rules, start, small=False):
    """The figures with each rule's range and verdict, as the studio's town feel job reports them."""
    checked = []
    outside = 0
    for key, label, low, high in rules:
        value = figures.get(key)
        out = value is not None and ((low is not None and value < low) or (high is not None and value > high))
        outside += 1 if out else 0
        checked.append({"key": key, "label": label, "low": low, "high": high,
                        "value": value if isinstance(value, (int, float)) else None,
                        "verdict": "n/a" if value is None else "out" if out else "ok"})
    return {"map": name, "start": start, "small": small, "town_box": [round(v) for v in figures.get("town_box") or []],
            "houses_in_town": figures.get("houses_in_town"), "rules": checked, "outside": outside,
            "figures": json.loads(json.dumps(figures, default=str))}


def project_map(project):
    """A built outdoor project's map: <project>/build/<id>.odm and its world, from project.yml."""
    card = (project / "project.yml").read_text(encoding="utf-8")
    stem = re.search(r"^id:\s*\"?([A-Za-z0-9_]+)", card, re.M)
    world = re.search(r"^world:\s*\"?([a-z0-9_]+)", card, re.M)
    if not stem or not world:
        sys.exit(f"{project}: project.yml names no id or world")
    path = project / "build" / f"{stem.group(1)}.odm"
    if not path.is_file():
        sys.exit(f"{path}: not built (oymap build {project})")
    return path, world.group(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("map", nargs="?")
    parser.add_argument("--world")
    parser.add_argument("--assets", default=str(REPO / "assets_dev"))
    parser.add_argument("--town", help="x0,y0,x1,y1 footprint")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shipped", action="store_true", help="measure every shipped town")
    parser.add_argument("--start", action="store_true", help="a start or early map: the start maps' ranges")
    parser.add_argument("--small", action="store_true", help="a small town: the small towns' size ranges")
    parser.add_argument("--project", help="a built outdoor project folder instead of a map")
    parser.add_argument("--report-json", action="store_true", help="figures, ranges and verdicts as JSON")
    args = parser.parse_args()
    assets = Path(args.assets).resolve()
    rules = load_rules(args.start, args.small)
    if args.shipped:
        results = {}
        for world, map_name, title, box in SHIPPED:
            results[map_name] = measure(map_name, world, assets, box)
            results[map_name]["title"] = title
        if args.json:
            print(json.dumps(results, indent=1, default=str))
        else:
            for map_name, figures in results.items():
                report(f"{figures['title']} ({map_name})", figures, rules)
        return
    project = Path(args.project).resolve() if args.project else None
    if project:
        built, world = project_map(project)
        args.map, args.world = str(built), args.world or world
    if not args.map or not args.world:
        parser.error("a map and --world are needed")
    box = tuple(float(v) for v in args.town.split(",")) if args.town else None
    figures = measure(args.map, args.world, assets, box, project)
    if args.report_json:
        print(json.dumps(report_json(Path(args.map).name, figures, rules, args.start, args.small), indent=1))
    elif args.json:
        print(json.dumps(figures, indent=1, default=str))
    else:
        report(args.map, figures, rules)


if __name__ == "__main__":
    main()
