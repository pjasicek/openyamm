#!/usr/bin/env python3
"""Props inside props or walls, and pick-ups hidden in them, on the Xeen indoor maps.

Family F40 of the player feedback (devdocs/xeen/reviews/PLAYER_FEEDBACK_20261124.md): a trash heap, a crate and a
barrel inside one another, an item the party cannot pick up under a trash heap, a bucket half inside the cave wall, a
spider stuck between a crystal and a stalagmite. Checked over the installed BLV maps as the game draws them:

  prop.overlap   error    two collidable floor props whose footprints overlap by more than 8 (one drawn inside the
                          other); a prop standing on another (its base at the other's top) is not one
  prop.wall      error    a floor prop whose footprint reaches more than 8 into a wall (a non-portal face that is not
                          a floor, a ceiling or a door leaf), or whose middle has no floor under it
  item.hidden    error    a ground item (a scene sprite object or a treasure spawn) inside a collidable prop's drawn
                          footprint (a sprite's: its collision circle), or more than 10 in a wall, or over no floor;
                          a warning within the prop's collision radius plus the item's pick size (20). The party
                          picks up by clicking within 512 (GameplayInteractionController), so only hiding matters
  prop.squeeze   warning  two collidable props, or a prop and a wall, leaving a gap of 1 to 96 that is open at both
                          ends (a slot a monster or the party tries and does not fit); the prop and wall pairs only
                          with `--wall-squeeze` (a prop a stride from a wall is the dressing rule, so they are many)

Classes: plants and trees are not judged (canopies and leaves). Loose heaps, bones, rubble, rocks, stalagmites and
crystals reaching into a wall are a warning (a cave wall swallows rubble), an error once more than half of their
footprint is in it; two natural formations (rocks, stalagmites, crystals, mushrooms) drawn into each other are a
warning. Containers, furniture, set pieces and everything else: an error past the tolerance. An item inside a model's
collision cylinder but outside its drawn footprint is a warning (visible, only the party cannot stand on it).

Footprints: a decoration drawn by a 3D model (engine/models/indoor_decorations.yml as extended by the Xeen world's)
has the convex hull of its model in plan, scaled and turned as the game places it (DecorationModelSet::placementFor:
scale = binding height / model height, yaw random from the position or the facing); a sprite has its collision circle
(decoration_data.txt radius). Two props are judged on their lower bodies (the hull of the model's points 12-40 % up
its height) and a wall on the lower body and the middle (45-75 %), so a heap's flat skirt is left out; an item against
the whole model. The game's collision is that radius in either case (IndoorWorldRuntime::
decorationMovementColliders: radius and height over 0, not MoveThrough or DontDraw). Hung and wall-mounted
decorations (the studio sidecar's hanging_decorations, `mount: wall` bindings, torches, lanterns, chandeliers) are
not floor props. Chests (BLV faces clicked to open) take part as boxes. Ids: an indoor entity's name is its L4
decoration id (`deco:<name>`); an item is named from the L4 objects.yml item or spawn at its position.

Usage:
  tools/xeen/check_prop_overlap.py [--assets ROOT] [--maps xeen_xd05,xeen_xd02 | --all] [--cache DIR] [--json FILE]
                                   [--errors-only] [--wall-squeeze]

Reads `oymap export` and `oymap things` of each map (cached like check_props_support.py). Exits 1 on any error.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_open_interiors import accessor, node_matrix, read_glb  # noqa: E402
from check_props_support import (HANG_WORDS, ROOT, Faces, decoration_kinds, export_map,  # noqa: E402
                                 things_of)

TOLERANCE = 8.0        # overlap or wall depth that still reads as touching
ITEM_PICK = 20.0       # an item's smallest pick half extent (game/items/WorldItemShape.cpp MinPickHalfExtent)
ITEM_WALL = 10.0       # an item this far in a wall is hidden
SQUEEZE = 96.0         # a gap narrower than this between two blockers, open at both ends, is a trap for walkers
WALL_SQUEEZE_MIN = 24.0  # a prop nearer a wall than this stands against it
STACK = 12.0           # a prop whose base is within this of another's top stands on it
STEP = 24.0
DIRECTIONS = 32
WALL_NZ = 0.7          # faces steeper than this (|nz| under it) are walls for the props

# Plan shapes of a model by height (fractions of its height): the whole model (what covers an item on the floor),
# its lower body (what two neighbours draw into each other: a heap's flat skirt left out) and its middle.
WHOLE = (0.0, 1.0)
LOWER = (0.12, 0.4)
MIDDLE = (0.45, 0.75)
BANDS = (WHOLE, LOWER, MIDDLE)

PLANT_WORDS = re.compile(r'tree|plant|bush|flower|fern|shrub|grass|reed|vine|lily|weed|cactus')
FORMATION_WORDS = re.compile(r'rock|boulder|stalag|stlmite|crystal|crys|geode|mushroom|mushrm')
LOOSE_WORDS = re.compile(r'heap|pile|bone|skull|skelet|dirt|straw|rubble|guano|muck|nest|ash|corpse|carcass|trash|'
                         r'debris|chaff|spoil|sklpl|dec05|dec29')

YAML_LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


# ------------------------------------------------------------------------------------------------ model footprints

def model_bindings(assets: Path, stem: str) -> dict:
    """decoration name -> its indoor binding (the Xeen world's entry replacing the engine's)."""
    result = {}
    for scope in ('engine', 'worlds/xeen'):
        path = assets / scope / 'models' / 'indoor_decorations.yml'
        if not path.exists():
            continue
        own = {}
        for entry in (yaml.load(path.read_text(), Loader=YAML_LOADER) or {}).get('decorations') or []:
            name = str(entry.get('name', '')).lower()
            maps = entry.get('maps')
            if maps and f'{stem}.blv' not in maps:
                continue
            own[name] = entry
        result.update(own)
    return result


_HULLS: dict = {}


def convex_hull(points):
    points = sorted(set(points))
    if len(points) <= 2:
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


def model_hull(assets: Path, model: str):
    """(plan hull in model units as OpenYAMM x/y before yaw, model height) of a GLB's LOD 0 meshes."""
    if model in _HULLS:
        return _HULLS[model]
    path = assets / model
    if not path.exists():
        _HULLS[model] = None
        return None
    document, binary = read_glb(path)
    nodes = document.get('nodes') or []
    points = []

    def walk(index, parent):
        node = nodes[index]
        matrix = parent @ node_matrix(node)
        if 'mesh' in node:
            mesh = document['meshes'][node['mesh']]
            if not re.search(r'_lod\d', str(mesh.get('name', '')).lower() + str(node.get('name', '')).lower()):
                for primitive in mesh.get('primitives') or []:
                    if 'POSITION' not in primitive.get('attributes', {}):
                        continue
                    local = accessor(document, binary, primitive['attributes']['POSITION'])
                    world = np.c_[local, np.ones(len(local))] @ matrix.T
                    points.append(world[:, :3])
        for child in node.get('children') or []:
            walk(child, matrix)

    scenes = document.get('scenes') or [{'nodes': list(range(len(nodes)))}]
    for root in scenes[document.get('scene', 0)].get('nodes') or []:
        walk(root, np.eye(4))
    if not points:
        _HULLS[model] = None
        return None
    allp = np.vstack(points)
    low, high = float(allp[:, 1].min()), float(allp[:, 1].max())
    height = high - low
    # glTF +Z is OpenYAMM +Y, glTF X is OpenYAMM -X (engine/models/ModelAsset.cpp gltfModelPlacement); heights 0..1.
    rows = np.unique(np.round(np.c_[-allp[:, 0], allp[:, 2], (allp[:, 1] - low) / max(height, 1e-6)], 2), axis=0)
    _HULLS[model] = (rows, height)
    return _HULLS[model]


_SLICES: dict = {}


def model_slice(model: str, rows, band):
    """The plan hull of a model's points between two heights (fractions of its height); the whole model's when
    the band holds too few."""
    key = (model, band)
    if key not in _SLICES:
        chosen = rows[(rows[:, 2] >= band[0]) & (rows[:, 2] <= band[1])]
        if len(chosen) < 3:
            chosen = rows
        _SLICES[key] = convex_hull([(float(a), float(b)) for a, b in chosen[:, :2].tolist()])
    return _SLICES[key]


def placement_random(x: int, y: int, salt: int) -> float:
    """game/maps/DecorationModelSet.cpp placementRandom."""
    mask = 0xffffffff
    h = ((x * 0x9e3779b1) & mask) ^ ((y * 0x85ebca77) & mask) ^ ((salt * 0xc2b2ae3d) & mask)
    h ^= h >> 15
    h = (h * 0x2c1b3c6d) & mask
    h ^= h >> 12
    h = (h * 0x297a2d39) & mask
    h ^= h >> 15
    return (h & 0xffffff) / float(0x1000000)


def circle(x, y, radius, count=16):
    return [(x + radius * math.cos(2 * math.pi * i / count), y + radius * math.sin(2 * math.pi * i / count))
            for i in range(count)]


# ------------------------------------------------------------------------------------------------ geometry

def sat_depth(a, b) -> float:
    """How far two convex plan polygons overlap (the least push that parts them); <= 0 when apart."""
    best = math.inf
    for poly in (a, b):
        for i in range(len(poly)):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % len(poly)]
            nx, ny = y2 - y1, x1 - x2
            length = math.hypot(nx, ny)
            if length < 1e-9:
                continue
            nx, ny = nx / length, ny / length
            pa = [px * nx + py * ny for px, py in a]
            pb = [px * nx + py * ny for px, py in b]
            overlap = min(max(pa), max(pb)) - max(min(pa), min(pb))
            if overlap <= 0:
                return overlap
            best = min(best, overlap)
    return best


def point_in(poly, x, y) -> bool:
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def extent(poly, cx, cy, dx, dy) -> float:
    return max((px - cx) * dx + (py - cy) * dy for px, py in poly)


class Walls:
    """The upright faces a prop may stand in: not portals, floors, ceilings or door leaves (nor chest faces)."""

    def __init__(self, faces: Faces, skip: set):
        self.faces = faces
        self.skip = skip

    def candidates(self, x, y, reach):
        cell = Faces.CELL
        seen = set()
        for gx in range(int((x - reach) // cell), int((x + reach) // cell) + 1):
            for gy in range(int((y - reach) // cell), int((y + reach) // cell) + 1):
                for index in self.faces.grid.get((gx, gy), ()):
                    if index in seen or index in self.skip:
                        continue
                    seen.add(index)
                    face = self.faces.faces[index]
                    if face['portal'] or abs(face['n'][2]) >= WALL_NZ:
                        continue
                    yield face

    def ray(self, faces, x, y, z, dx, dy, reach) -> float:
        """Distance along a level ray from (x, y, z) to the first wall it meets within reach (math.inf if none)."""
        best = math.inf
        for face in faces:
            if not (face['min'][2] <= z <= face['max'][2]):
                continue
            nx, ny, nz = face['n']
            denom = nx * dx + ny * dy
            if abs(denom) < 1e-6:
                continue
            t = -(nx * x + ny * y + nz * z + face['d']) / denom
            if t < -1e-3 or t > reach or t >= best:
                continue
            hx, hy = x + t * dx, y + t * dy
            # Inside the face: project away its dominant axis.
            ax = max(range(3), key=lambda i: abs(face['n'][i]))
            keep = [i for i in range(3) if i != ax]
            hit = (hx, hy, z)
            poly = [(p[keep[0]], p[keep[1]]) for p in face['points']]
            if point_in(poly, hit[keep[0]], hit[keep[1]]) or on_edge(poly, hit[keep[0]], hit[keep[1]]):
                best = max(t, 0.0)
        return best


def on_edge(poly, x, y, tol=0.5) -> bool:
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1
        length = dx * dx + dy * dy
        if length == 0:
            continue
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length))
        if (x1 + t * dx - x) ** 2 + (y1 + t * dy - y) ** 2 < tol * tol:
            return True
    return False


def wall_profile(walls: Walls, poly, cx, cy, heights, reach_extra=SQUEEZE + 8):
    """Per direction: (footprint extent, distance to the nearest wall) at the worst of the given heights."""
    reach = max(math.hypot(px - cx, py - cy) for px, py in poly) + reach_extra
    faces = list(walls.candidates(cx, cy, reach))
    rows = []
    for k in range(DIRECTIONS):
        angle = 2 * math.pi * k / DIRECTIONS
        dx, dy = math.cos(angle), math.sin(angle)
        e = extent(poly, cx, cy, dx, dy)
        hit = min(walls.ray(faces, cx, cy, z, dx, dy, e + reach_extra) for z in heights)
        rows.append((angle, e, hit))
    return rows


def floor_under(faces: Faces, x, y, z) -> bool:
    return any(h <= z + STEP and h >= z - 64 for h in faces.floor_heights(x, y))


def floor_height(faces: Faces, x, y, z):
    heights = [h for h in faces.floor_heights(x, y) if h <= z + STEP]
    return max(heights) if heights else None


# ------------------------------------------------------------------------------------------------ the map

def l4_names(stem: str) -> list:
    """(id, x, y) of the L4 brief's items and treasure spawns, to name a scene item by its position."""
    path = ROOT / 'devdocs' / 'xeen' / 'briefs' / stem.removeprefix('xeen_') / 'L4' / 'objects.yml'
    if not path.exists():
        return []
    data = yaml.load(path.read_text(), Loader=YAML_LOADER) or {}
    named = []
    for entry in (data.get('items') or []) + [s for s in data.get('spawns') or [] if s.get('kind') == 'item']:
        at = entry.get('at')
        if isinstance(at, list) and len(at) >= 2:
            named.append((entry.get('id', '?'), float(at[0]), float(at[1])))
    return named


def check_map(path: Path, assets: Path, cache: Path, kinds, wall_squeeze=False) -> list:
    by_id, by_name = kinds
    stem = path.stem
    data = export_map(path, assets, cache)
    things = things_of(path, assets, cache)
    m = data['map']
    vertices = m['vertices']
    faces = Faces()
    for index, face in enumerate(m['faces']):
        points = [tuple(vertices[i]) for i in face['vertices'] if i < len(vertices)]
        faces.add(points, face['plane_normal'], face['texture'], face.get('cog_triggered', 0),
                  face.get('cog_triggered', 0) or None, portal=face.get('is_portal', False))
    # Faces.add drops faces of fewer than three points: map the export's face numbers to its own.
    numbering, kept = {}, 0
    for index, face in enumerate(m['faces']):
        if len(face['vertices']) >= 3:
            numbering[index] = kept
            kept += 1
    door_faces = {numbering[f] for door in data.get('doors') or [] for f in door.get('faces') or [] if f in numbering}
    chest_events = {t['event'] for t in things if t['kind'] == 'chest'}
    chest_faces = {i for i, f in enumerate(faces.faces) if f['event'] and f['event'] in chest_events}
    walls = Walls(faces, door_faces | chest_faces)
    bindings = model_bindings(assets, stem)

    hanging = set()
    sidecar = path.with_suffix('.studio.yml')
    if sidecar.exists():
        for line in sidecar.read_text().splitlines():
            if line.startswith('hanging_decorations:'):
                hanging = {int(v) for v in re.findall(r'\d+', line.split(':', 1)[1])}

    findings = []

    def add(level, check, where, text, **extra):
        findings.append({'map': stem, 'level': level, 'check': check, 'at': [round(v) for v in where],
                         'text': text, **extra})

    # The floor props.
    props = []
    for number, entity in enumerate(m.get('entities') or []):
        if number in hanging:
            continue
        name = entity.get('name', '')
        row = by_name.get(name.strip().lower(), entity.get('decoration_list_id', -1))
        kind = by_id.get(row) or by_id.get(entity.get('decoration_list_id', -1))
        if kind is None or not kind['blocks'] or kind['height'] <= 0:
            continue
        if any(word in name.lower() for word in HANG_WORDS):
            continue
        binding = bindings.get(kind['name'].lower())
        if binding is not None and (binding.get('mount') == 'wall' or binding.get('swing')):
            continue
        words = f"{kind['name']} {kind['hint']} {Path(str((binding or {}).get('model') or '')).stem}".lower()
        if PLANT_WORDS.search(words):
            continue
        cls = 'formation' if FORMATION_WORDS.search(words) else 'loose' if LOOSE_WORDS.search(words) else 'solid'
        x, y, z = entity['position']
        height = kind['height']
        circ = circle(x, y, kind['radius'])
        shapes = {band: circ for band in BANDS}
        model = binding.get('model') if binding else None
        if model:
            hull = model_hull(assets, model)
            if hull is not None and hull[1] > 0:
                jitter = 1.0 + float(binding.get('height_jitter', 0.0)) * (2.0 * placement_random(int(x), int(y), 1)
                                                                           - 1.0)
                scale = float(binding['height']) / hull[1] * jitter
                if binding.get('yaw', 'random') == 'random':
                    yaw = placement_random(int(x), int(y), 2) * 2 * math.pi
                else:
                    yaw = float(entity.get('facing', 0)) * math.pi / 180.0
                yaw += float(binding.get('yaw_offset', 0.0))
                c, s = math.cos(yaw), math.sin(yaw)
                for band in BANDS:
                    shape = model_slice(model, hull[0], band)
                    if len(shape) >= 3:
                        shapes[band] = [(x + scale * (px * c - py * s), y + scale * (px * s + py * c))
                                        for px, py in shape]
                height = float(binding['height']) * jitter
                z = z + float(binding.get('z_offset', 0.0))
        props.append({'id': name or f"{kind['name']}@{x},{y}", 'deco': kind['name'], 'hint': kind['hint'],
                      'x': x, 'y': y, 'z': z, 'top': z + height, 'radius': kind['radius'], 'shapes': shapes,
                      'poly': shapes[WHOLE], 'model': model or '', 'chest': False, 'cls': cls})

    # Chests: the boxes of their clicked faces.
    for thing in things:
        if thing['kind'] != 'chest':
            continue
        own = [f for f in faces.faces if f['event'] == thing['event']]
        if not own:
            continue
        lo = [min(f['min'][i] for f in own) for i in range(3)]
        hi = [max(f['max'][i] for f in own) for i in range(3)]
        box = [(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])]
        props.append({'id': f'chest event {thing["event"]} "{thing["title"]}"', 'deco': 'chest', 'hint': 'chest',
                      'x': (lo[0] + hi[0]) / 2, 'y': (lo[1] + hi[1]) / 2, 'z': lo[2], 'top': hi[2],
                      'radius': 0.5 * max(hi[0] - lo[0], hi[1] - lo[1]),
                      'poly': box, 'shapes': {band: box for band in BANDS}, 'model': '', 'cls': 'solid',
                      'chest': True})

    def label(p):
        return f"{p['id']} ({p['deco']}{', ' + Path(p['model']).stem if p['model'] else ''}, radius {p['radius']:g})"

    # 1. Props inside props.
    cell = 384.0
    grid = defaultdict(list)
    for index, p in enumerate(props):
        grid[(int(p['x'] // cell), int(p['y'] // cell))].append(index)
    pairs = set()
    for index, p in enumerate(props):
        gx, gy = int(p['x'] // cell), int(p['y'] // cell)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for other in grid.get((gx + ox, gy + oy), ()):
                    if other > index:
                        pairs.add((index, other))
    for i, j in sorted(pairs):
        a, b = props[i], props[j]
        if a['chest'] and b['chest']:
            continue
        # Stacked: one stands on the other's top, or they do not share a height.
        if b['z'] >= a['top'] - STACK or a['z'] >= b['top'] - STACK:
            continue
        # A composite: two decorations at one spot drawn as one thing (a pot over its fire).
        distance = math.hypot(a['x'] - b['x'], a['y'] - b['y'])
        if distance < 2.0:
            continue
        depth = sat_depth(a['shapes'][LOWER], b['shapes'][LOWER])
        if depth > TOLERANCE:
            collide = a['radius'] + b['radius'] - distance
            natural = a['cls'] == 'formation' and b['cls'] == 'formation'
            middle = ((a['x'] + b['x']) / 2, (a['y'] + b['y']) / 2, min(a['z'], b['z']))
            add('warning' if natural else 'error', 'prop.overlap', middle,
                f"{label(a)} at {[round(v) for v in (a['x'], a['y'], a['z'])]} and {label(b)} at "
                f"{[round(v) for v in (b['x'], b['y'], b['z'])]}: drawn {depth:.0f} into each other, centres "
                f"{distance:.0f} apart" + (f', collision cylinders {collide:.0f} into each other' if collide > 0
                                           else ''),
                things=[a['id'], b['id']], depth=round(depth), distance=round(distance))
        elif not a['chest'] and not b['chest']:
            gap = distance - a['radius'] - b['radius']
            if 1.0 <= gap < SQUEEZE:
                # Open at both ends: across the gap's middle, sideways, floor at the same height and no wall.
                mx = a['x'] + (b['x'] - a['x']) * (a['radius'] + gap / 2) / distance
                my = a['y'] + (b['y'] - a['y']) * (a['radius'] + gap / 2) / distance
                base = max(a['z'], b['z'])
                ux, uy = -(b['y'] - a['y']) / distance, (b['x'] - a['x']) / distance
                reach = max(a['radius'], b['radius']) + 128
                open_ends = True
                for sign in (1, -1):
                    ex, ey = mx + sign * ux * reach, my + sign * uy * reach
                    ground = floor_height(faces, ex, ey, base)
                    if ground is None or abs(ground - base) > STEP or faces.wall_between((mx, my), (ex, ey), base) \
                            or any(point_in(q['poly'], ex, ey) for q in props if q is not a and q is not b):
                        open_ends = False
                        break
                if open_ends:
                    add('warning', 'prop.squeeze', (mx, my, base),
                        f"{label(a)} and {label(b)} leave a gap of {gap:.0f} between their collision cylinders, open "
                        f"at both ends", things=[a['id'], b['id']], gap=round(gap))

    # 2. Props in walls (and 4. against walls with a slot).
    for p in props:
        if p['chest']:
            continue
        base, top = p['z'], p['top']
        ground = floor_height(faces, p['x'], p['y'], base)
        if ground is None:
            add('error', 'prop.wall', (p['x'], p['y'], base), f"{label(p)} has no floor under its middle within "
                f"{STEP:g} (in the rock or over a hole)", things=[p['id']], depth=None)
            continue
        h = top - base
        rows = []
        for band in (LOWER, MIDDLE):
            rows += wall_profile(walls, p['shapes'][band], p['x'], p['y'], (base + max(8.0, h * sum(band) / 2),))
        worst = max(rows, key=lambda r: r[1] - r[2])
        depth = worst[1] - worst[2]
        if depth > TOLERANCE:
            loose = p['cls'] != 'solid' and depth <= 0.5 * worst[1]
            add('warning' if loose else 'error', 'prop.wall', (p['x'], p['y'], base),
                f"{label(p)} reaches {depth:.0f} into a wall (towards {math.degrees(worst[0]):.0f} degrees; its "
                f"footprint {worst[1]:.0f} from its middle, the wall {worst[2]:.0f})", things=[p['id']],
                depth=round(depth))
        elif wall_squeeze:
            # The collision cylinder against the nearest wall: a slot open along the wall at both ends.
            near = min(rows, key=lambda r: r[2] - p['radius'])
            gap = near[2] - p['radius']
            if WALL_SQUEEZE_MIN <= gap < SQUEEZE:
                angle = near[0]
                dx, dy = math.cos(angle), math.sin(angle)
                mx, my = p['x'] + dx * (p['radius'] + gap / 2), p['y'] + dy * (p['radius'] + gap / 2)
                open_ends = True
                for sign in (1, -1):
                    ex, ey = mx - sign * dy * (p['radius'] + 64), my + sign * dx * (p['radius'] + 64)
                    g2 = floor_height(faces, ex, ey, base)
                    if g2 is None or abs(g2 - base) > STEP or faces.wall_between((mx, my), (ex, ey), base) \
                            or any(point_in(q['poly'], ex, ey) for q in props if q is not p):
                        open_ends = False
                        break
                # The other side of the prop is open too (else it closes the way and nobody tries the slot).
                back = walls.ray(list(walls.candidates(p['x'], p['y'], p['radius'] + SQUEEZE + 8)), p['x'], p['y'],
                                 base + 16, -dx, -dy, p['radius'] + SQUEEZE + 8)
                if open_ends and back - p['radius'] >= SQUEEZE:
                    add('warning', 'prop.squeeze', (mx, my, base),
                        f"{label(p)} leaves a gap of {gap:.0f} to the wall (towards {math.degrees(angle):.0f} "
                        "degrees), open along the wall at both ends", things=[p['id']], gap=round(gap))

    # 3. Items: the scene's sprite objects and the map's treasure spawns.
    items = []
    scene = path.with_suffix('.scene.yml')
    if scene.exists():
        sdata = yaml.load(scene.read_text(), Loader=YAML_LOADER) or {}
        for obj in (sdata.get('initial_state') or {}).get('sprite_objects') or []:
            if obj.get('spell_id') or (obj.get('attributes') or 0) & 0x4:  # missiles are no pick-ups
                continue
            pos = obj['position']
            items.append({'what': f"sprite object {obj.get('sprite_object_index')} (object "
                          f"{obj.get('object_description_id')})", 'x': pos['x'], 'y': pos['y'], 'z': pos['z']})
    for index, spawn in enumerate(m.get('spawns') or []):
        if spawn.get('type_id') == 2:
            x, y, z = spawn['position']
            items.append({'what': f'treasure spawn {index} (level {spawn.get("index")})', 'x': x, 'y': y, 'z': z})
    named = l4_names(stem)
    for item in items:
        x, y, z = item['x'], item['y'], item['z']
        l4 = next((n for n, nx, ny in named if abs(nx - x) <= 2 and abs(ny - y) <= 2), None)
        what = (l4 + ' = ' if l4 else '') + item['what']
        ground = floor_height(faces, x, y, z + 8)
        lying = ground if ground is not None else z
        for p in props:
            if not (p['z'] - STEP <= lying < p['top'] - 4):
                continue
            distance = math.hypot(x - p['x'], y - p['y'])
            inside = point_in(p['poly'], x, y)
            if inside or distance < p['radius'] + ITEM_PICK:
                add('error' if inside else 'warning', 'item.hidden', (x, y, z),
                    f"{what} at {[round(v) for v in (x, y, z)]} lies "
                    + ('inside the drawn footprint of ' if inside else 'against the collision cylinder of ')
                    + f"{label(p)} at {[round(v) for v in (p['x'], p['y'], p['z'])]}: {distance:.0f} from its middle",
                    things=[l4 or item['what'], p['id']], distance=round(distance))
                break
        else:
            if ground is None:
                add('error', 'item.hidden', (x, y, z), f"{what} at {[round(v) for v in (x, y, z)]} has no floor "
                    'under it (in the rock)', things=[l4 or item['what']])
                continue
            rows = wall_profile(walls, circle(x, y, ITEM_PICK, 8), x, y, (lying + 12,), reach_extra=16)
            depth = max(r[1] - r[2] for r in rows)
            if depth > ITEM_WALL:
                add('error', 'item.hidden', (x, y, z), f"{what} at {[round(v) for v in (x, y, z)]} lies {depth:.0f} "
                    'into a wall', things=[l4 or item['what']], depth=round(depth))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--assets', default=str(ROOT / 'assets_dev'))
    parser.add_argument('--maps', default='', help='comma-separated stems (default: every installed Xeen BLV)')
    parser.add_argument('--all', action='store_true', help='every installed Xeen indoor map (the default)')
    parser.add_argument('--cache', default=str(ROOT / 'output' / 'xeen_fb' / 'support_cache'))
    parser.add_argument('--json', default='')
    parser.add_argument('--errors-only', action='store_true')
    parser.add_argument('--wall-squeeze', action='store_true', help='also report gaps between props and walls')
    args = parser.parse_args()

    assets = Path(args.assets)
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    kinds = decoration_kinds(assets)
    maps_dir = assets / 'worlds' / 'xeen' / 'maps'
    if args.maps and not args.all:
        paths = [maps_dir / (s.strip() + '.blv') for s in args.maps.split(',') if s.strip()]
        missing = [p.name for p in paths if not p.exists()]
        if missing:
            print('no such indoor map: ' + ', '.join(missing), file=sys.stderr)
            return 2
    else:
        paths = sorted(maps_dir.glob('xeen_*.blv'))

    findings = []
    for path in paths:
        findings.extend(check_map(path, assets, cache, kinds, args.wall_squeeze))

    errors = 0
    for finding in findings:
        if finding['level'] == 'error':
            errors += 1
        elif args.errors_only:
            continue
        print(f"{finding['level']:7s} {finding['check']:12s} {finding['map']:12s} {finding['at']}  {finding['text']}")
    counts = defaultdict(int)
    for finding in findings:
        counts[(finding['level'], finding['check'])] += 1
    print(f'{len(paths)} maps: ' + (', '.join(f'{c} {k[1]} {k[0]}s' for k, c in sorted(counts.items())) or 'clean'))
    if args.json:
        Path(args.json).write_text(json.dumps(findings, indent=1))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
