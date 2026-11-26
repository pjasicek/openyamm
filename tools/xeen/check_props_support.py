#!/usr/bin/env python3
"""Props and chests of the Xeen maps: what they stand on, what they look like, what they stand in front of.

Families F3 and F6 of the user's play feedback (devdocs/xeen/reviews/USER_FEEDBACK_20261121.md), checked over the
installed (or built) maps as the game reads them:

  support.overhang   error    part of a floor prop's footprint has no ground or floor within 24 under its base
                              (a barrel half over a terrace's edge)
  support.edge       error    a drop of more than 64 within 48 of a container's or other prop's footprint (it stands
                              at an edge: a cliff, a terrace, a platform or a bridge side); a warning for set pieces
  support.floating   error    nothing within 24 under the prop's middle
  support.sunk       error    outdoors, a structure's top 8 to 160 over the prop's base covers its middle: the studio
                              stood it on the land under a slab, a paving or a deck (P5 F72, X2 p13's keg in the quay)
  chest.look         error    a chest that is not one of the shipped chests: MM7's or MM8's 19 faces (7gt002 or gt002
                              pieces), MM6's chest kinds (ch1 to ch5, ch001 to ch006), a crate, or a bookcase
  chest.entrance     error    a chest within 320 in front of (192 beside) a house door, an exit, a door, a teleport
                              or a cave mouth's dark door face
  chest.title        warning  a chest whose hover title names a place (a den, a cave, a mine), not what opens

Usage:
  tools/xeen/check_props_support.py [--assets ROOT] [--maps xeen_x1,xeen_dd01 | --all] [--cache DIR] [--json FILE]
  tools/xeen/check_props_support.py --file path/to/xeen_x1.odm [--scene path/to/xeen_x1.scene.yml]

Reads `oymap export` and `oymap things` of each map (the studio binary openyamm-studio/build-xeen/oymap). Exits 1
when any error is found.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OYMAP = ROOT / 'openyamm-studio' / 'build-xeen' / 'oymap'

STEP = 24.0          # what the party steps onto counts as under a base
OVERHANG = 24.0      # a footprint sample may sit this far over the ground (a gentle slope)
EDGE_REACH = 48.0    # how far beyond the footprint an edge counts
EDGE_DROP = 64.0     # a drop this deep there is an edge (a 45 degree slope over the reach is not)
FLOOR_NORMAL_Z = 0.6
FURNITURE = 128.0
SLOPE_OVERHANG = 48.0  # outdoors what a prop other than a container may hang over a hillside
SUNK = 8.0           # a structure's top this far over a prop's base covers it (the prop is sunk in it)
SUNK_REACH = 160.0   # higher than this over the base it is a roof over the prop
SLOPE_EDGE_DROP = 96.0  # and the drop beside it that still reads as a steep hillside, not an edge    # indoors a table or a shelf is no deeper than this

CONTAINER_WORDS = re.compile(r'barrel|barel|cask|keg|sack|\bbag|crate|\bbox|bucket|firewood|woodpile|log pile')
# Plants grow on slopes; natural rocks lie where the land puts them, half sunk or at a cliff's lip: not judged.
NATURAL_WORDS = re.compile(r'\brock|boulder|basalt|stalagmite|crag|plant|bush|flower|fern|shrub|grass|reed|mushroom'
                           r'|weed|cactus|vine|lily|stump|log\b')
SET_PIECE_WORDS = re.compile(r'\btree|statue|pillar|column|altar|hearth|fire(?!wood)|brazier|cauldron|\bvat|fountain'
                             r'|pedestal|shrine|obelisk|\bstall|\brock|boulder')
HANG_WORDS = ('chandelier', 'lantern', 'sconce', 'torch', 'flambeaux', 'cage', 'flag', 'noose', 'stalagtite',
              'stalactite', 'buoy', 'lily', 'seaweed', 'banner', 'hang')
# Titles that name a place rather than the box that opens.
PLACE_WORDS = re.compile(r"\b(den|cave|cavern|mine|adit|lair|hall|tower|house|camp|gate|grotto|hole|tunnel|"
                         r"passage|entrance|crypt|tomb|barrow|ruin|ruins|keep|fort|shrine|temple|well)\b", re.I)
CONTAINER_TITLE_WORDS = re.compile(r"chest|box|cache|crate|coffer|strongbox|hoard|loot|plunder|supplies|pack|"
                                   r"goods|offerings|bag|sack|purse|trunk|casket|cask|barrel|stash|kit|satchel|"
                                   r"case|haul|spoils|treasure|bundle|basket|urn|jar", re.I)

SHIPPED_CHEST_SETS = [
    # MM7's and MM8's chest model: 19 faces of the a, b, c, e and g pieces (some lids add gt003 bands).
    {'prefixes': ('7gt002', 'gt002', 'gt003'), 'needs': ('a', 'b', 'c', 'e', 'g'), 'min_faces': 18},
]
MM6_CHEST = re.compile(r'^ch[1-5](frle|frntb?|frre|side|top|tople|topre|topb|toplb|toprb|tpbv|tplev|tprev|topv|'
                       r'bkre|bkle)$|^ch00[1-6][a-h]$')
CRATE_TEXTURES = {'7gt001a', 'gt001a', 'cr64', 'crside'}
BOOKCASE = re.compile(r'books|cab')

THING_LINE = re.compile(r'^event (\d+) "((?:[^"\\]|\\.)*)" ([a-z_]+) in (.+?): (\d+) faces \(([^)]*)\) at '
                        r'\[(-?\d+), (-?\d+), (-?\d+)\]')
OPENING_KINDS = {'house', 'exit', 'door', 'teleport'}
MOUTH_TEXTURES = {'7solid01', 'solid01', 'blackwal'}


def read_table(path: Path) -> list[list[str]]:
    rows = []
    for line in path.read_text(encoding='utf-8', errors='replace').splitlines():
        rows.append(line.split('\t'))
    return rows


def decoration_kinds(assets: Path) -> tuple[dict, dict]:
    by_id: dict[int, dict] = {}
    by_name: dict[str, int] = {}
    tables = [assets / 'engine' / 'data_tables' / 'decoration_data.txt',
              assets / 'worlds' / 'xeen' / 'models' / 'decoration_data.txt']
    for table in tables:
        if not table.exists():
            continue
        for cells in read_table(table):
            if len(cells) < 12 or not cells[0].strip().isdigit():
                continue
            names = (cells[1] + ' ' + cells[2]).lower()
            hint = cells[2].strip()
            radius = float(cells[4] or 0)
            flags = cells[11]
            kind = {
                'name': cells[1].strip(),
                'hint': hint,
                'radius': radius,
                'height': float(cells[5] or 0),
                'blocks': radius > 0 and 'MoveThrough' not in flags and 'DontDraw' not in flags
                and not any(word in hint.lower() for word in HANG_WORDS) and 'party start' not in names,
                'set_piece': bool(SET_PIECE_WORDS.search(names)),
            }
            kind['container'] = not kind['set_piece'] and (bool(CONTAINER_WORDS.search(names))
                                                           or hint.lower() == 'wood')
            row = int(cells[0]) - 1
            by_id[row] = kind
            by_name.setdefault(cells[1].strip().lower(), row)
    return by_id, by_name


def run_oymap(args: list[str]) -> str:
    result = subprocess.run([str(OYMAP)] + args, capture_output=True, text=True, timeout=600)
    return result.stdout


def export_map(path: Path, assets: Path, cache: Path) -> dict:
    out = cache / (path.name + '.json')
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        run_oymap(['export', str(path), '--world', 'xeen', '--assets', str(assets), '--out', str(out)])
    return json.loads(out.read_text())


def things_of(path: Path, assets: Path, cache: Path) -> list[dict]:
    out = cache / (path.name + '.things.txt')
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        out.write_text(run_oymap(['things', str(path), '--world', 'xeen', '--assets', str(assets)]))
    things = []
    for line in out.read_text().splitlines():
        match = THING_LINE.match(line)
        if not match:
            continue
        textures = {}
        for part in match.group(6).split(', '):
            name, _, count = part.rpartition(' ')
            textures[name.lower()] = int(count)
        things.append({'event': int(match.group(1)), 'title': match.group(2), 'kind': match.group(3),
                       'group': match.group(4), 'faces': int(match.group(5)), 'textures': textures,
                       'at': (int(match.group(7)), int(match.group(8)), int(match.group(9))),
                       'sector': int(re.match(r'sector (\d+)', match.group(4)).group(1))
                       if re.match(r'sector \d+', match.group(4)) else -1})
    return things


class Faces:
    """Every face as (polygon in plan, plane, texture, event, group id, is floor), bucketed by 512 cells."""

    CELL = 512.0

    def __init__(self):
        self.faces = []
        self.grid = defaultdict(list)

    def add(self, points, normal, texture, event, group, portal=False):
        if len(points) < 3:
            return
        length = math.sqrt(sum(component * component for component in normal)) or 1.0
        nx, ny, nz = (component / length for component in normal)
        px, py, pz = points[0]
        face = {
            'points': points, 'n': (nx, ny, nz), 'd': -(nx * px + ny * py + nz * pz), 'texture': texture.lower(),
            'event': event, 'group': group, 'floor': nz >= FLOOR_NORMAL_Z and not portal, 'portal': portal,
            'min': [min(p[i] for p in points) for i in range(3)], 'max': [max(p[i] for p in points) for i in range(3)],
        }
        index = len(self.faces)
        self.faces.append(face)
        for gx in range(int(face['min'][0] // self.CELL), int(face['max'][0] // self.CELL) + 1):
            for gy in range(int(face['min'][1] // self.CELL), int(face['max'][1] // self.CELL) + 1):
                self.grid[(gx, gy)].append(index)

    def near(self, x, y):
        return self.grid.get((int(x // self.CELL), int(y // self.CELL)), ())

    def wall_between(self, a, b, z):
        """Whether a wall (an upright face, not a portal) standing over z + 16 crosses the plan segment a-b."""
        seen = set()
        for cell in {(int(a[0] // self.CELL), int(a[1] // self.CELL)), (int(b[0] // self.CELL), int(b[1] // self.CELL))}:
            for index in self.grid.get(cell, ()):
                if index in seen:
                    continue
                seen.add(index)
                face = self.faces[index]
                if face['portal'] or abs(face['n'][2]) >= 0.7 or not (face['min'][2] <= z + 16 <= face['max'][2]):
                    continue
                nx, ny = face['n'][0], face['n'][1]
                tx, ty = -ny, nx
                along = [p[0] * tx + p[1] * ty for p in face['points']]
                first = face['points'][along.index(min(along))]
                last = face['points'][along.index(max(along))]
                if segments_cross(a, b, first, last):
                    return True
        return False

    def floor_heights(self, x, y, skip_group=None):
        heights = []
        for index in self.near(x, y):
            face = self.faces[index]
            if not face['floor'] or (skip_group is not None and face['group'] == skip_group):
                continue
            if not (face['min'][0] - 0.5 <= x <= face['max'][0] + 0.5 and face['min'][1] - 0.5 <= y <= face['max'][1] + 0.5):
                continue
            if not inside(face['points'], x, y):
                continue
            nx, ny, nz = face['n']
            heights.append(-(nx * x + ny * y + face['d']) / nz)
        return heights


def segments_cross(a, b, c, d) -> bool:
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2 = side(c, d, a), side(c, d, b)
    d3, d4 = side(a, b, c), side(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def inside(points, x, y) -> bool:
    result = False
    count = len(points)
    for index in range(count):
        x1, y1 = points[index][0], points[index][1]
        x2, y2 = points[(index + 1) % count][0], points[(index + 1) % count][1]
        if (y1 > y) != (y2 > y):
            cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < cross:
                result = not result
    # On an edge counts as inside (a prop on a seam between two floor faces).
    if not result:
        for index in range(count):
            x1, y1 = points[index][0], points[index][1]
            x2, y2 = points[(index + 1) % count][0], points[(index + 1) % count][1]
            dx, dy = x2 - x1, y2 - y1
            length = dx * dx + dy * dy
            if length == 0:
                continue
            t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / length))
            if (x1 + t * dx - x) ** 2 + (y1 + t * dy - y) ** 2 < 1.0:
                return True
    return result


class Terrain:
    def __init__(self, terrain: dict):
        self.width = terrain['width']
        self.heights = terrain['height_map']
        self.scale = terrain['height_scale']
        self.tile = terrain['tile_size']

    def vertex(self, gx, gy):
        gx = max(0, min(self.width - 1, gx))
        gy = max(0, min(self.width - 1, gy))
        return self.heights[gy * self.width + gx] * self.scale

    def bilinear(self, x, y):
        """The studio's placement height (LoweredOutdoorMap::storedHeightAt, bilinear over the cell)."""
        grid_x = x / self.tile + self.width / 2
        grid_y = self.width / 2 - y / self.tile
        x0 = max(0, min(self.width - 2, int(math.floor(grid_x))))
        y0 = max(0, min(self.width - 2, int(math.floor(grid_y))))
        fx = max(0.0, min(1.0, grid_x - x0))
        fy = max(0.0, min(1.0, grid_y - y0))
        north = self.vertex(x0, y0) * (1 - fx) + self.vertex(x0 + 1, y0) * fx
        south = self.vertex(x0, y0 + 1) * (1 - fx) + self.vertex(x0 + 1, y0 + 1) * fx
        return north * (1 - fy) + south * fy

    def height(self, x, y):
        grid_x = x / self.tile + self.width / 2
        grid_y = self.width / 2 - y / self.tile
        x0 = max(0, min(self.width - 2, int(math.floor(grid_x))))
        y0 = max(0, min(self.width - 2, int(math.floor(grid_y))))
        fx = max(0.0, min(1.0, grid_x - x0))
        fy = max(0.0, min(1.0, grid_y - y0))
        h00, h10 = self.vertex(x0, y0), self.vertex(x0 + 1, y0)
        h01, h11 = self.vertex(x0, y0 + 1), self.vertex(x0 + 1, y0 + 1)
        # The native diagonal runs from the north-west to the south-east corner (core OutdoorGeometryUtils).
        if fx >= fy:
            return h00 + fx * (h10 - h00) + fy * (h11 - h10)
        return h00 + fy * (h01 - h00) + fx * (h11 - h01)


class World:
    def __init__(self, data: dict, outdoor: bool):
        self.outdoor = outdoor
        self.faces = Faces()
        self.terrain = Terrain(data['map']['terrain']) if outdoor else None
        self.groups = {}
        m = data['map']
        if outdoor:
            for index, bmodel in enumerate(m['bmodels']):
                vertices = bmodel['vertices']
                self.groups[index] = bmodel['name']
                for face in bmodel['faces']:
                    points = [tuple(vertices[i]) for i in face['vertices'] if i < len(vertices)]
                    self.faces.add(points, face['plane_normal'], face['texture'], face.get('cog_triggered', 0),
                                   ('bmodel', index))
        else:
            vertices = m['vertices']
            for index, face in enumerate(m['faces']):
                points = [tuple(vertices[i]) for i in face['vertices'] if i < len(vertices)]
                self.faces.add(points, face['plane_normal'], face['texture'], face.get('cog_triggered', 0),
                               ('event', face.get('cog_triggered', 0)) if face.get('cog_triggered', 0) else None,
                               portal=face.get('is_portal', False))

    def support(self, x, y, z, skip_group=None):
        """The highest ground or floor at (x, y) no more than a step over z; z itself when the ground there rises
        over that (the prop's side is sunk in a slope, which holds it); None when there is nothing under it."""
        best = None
        if self.terrain is not None:
            ground = self.terrain.height(x, y)
            best = ground if ground <= z + STEP else z
        for height in self.faces.floor_heights(x, y, skip_group):
            if height <= z + STEP and (best is None or height > best):
                best = height
        return best


def ring(x, y, radius, count=8):
    return [(x + radius * math.cos(2 * math.pi * i / count), y + radius * math.sin(2 * math.pi * i / count))
            for i in range(count)]


def box_points(lo, hi, grow):
    x0, y0, x1, y1 = lo[0] - grow, lo[1] - grow, hi[0] + grow, hi[1] + grow
    xs = [x0, (x0 + x1) / 2, x1]
    ys = [y0, (y0 + y1) / 2, y1]
    return [(a, b) for a in xs for b in ys if not (a == xs[1] and b == ys[1])]


def judge_footprint(world, base, footprint, margin, centre, skip_group=None):
    """(worst overhang below the base under the footprint, worst drop just beyond it). A point with no floor under
    it (indoors: in or behind a wall) or behind a wall from the prop's middle is no drop: the prop stands against
    that wall."""
    def gap(x, y):
        under = world.support(x, y, base, skip_group)
        if under is None or world.faces.wall_between(centre, (x, y), base):
            return 0.0
        return base - under

    overhang = max([gap(x, y) for x, y in footprint] or [0.0])
    drop = max([gap(x, y) for x, y in margin] or [0.0])
    return overhang, drop


def check_map(path: Path, scene: Path | None, assets: Path, cache: Path, kinds, regrounded=False) -> list[dict]:
    by_id, by_name = kinds
    outdoor = path.suffix == '.odm'
    data = export_map(path, assets, cache)
    world = World(data, outdoor)
    sectors = [] if outdoor else data['map'].get('sectors') or []
    things = things_of(path, assets, cache)
    findings = []
    stem = path.stem

    def add(level, check, where, text, **extra):
        findings.append({'map': stem, 'level': level, 'check': check, 'at': [round(v) for v in where],
                         'text': text, **extra})

    # Decorations: the scene's entities outdoors (the ODM keeps none), the BLV's own indoors.
    entities = []
    if outdoor:
        scene_path = scene or path.with_suffix('.scene.yml')
        if scene_path.exists():
            scene_data = yaml.load(scene_path.read_text(), Loader=getattr(yaml, 'CSafeLoader', yaml.SafeLoader))
            for entity in scene_data.get('entities') or []:
                p = entity['position']
                entities.append({'name': entity.get('name', ''), 'id': entity.get('decoration_list_id', -1),
                                 'at': (p['x'], p['y'], p['z']), 'event': entity.get('event_id_secondary', 0)
                                 or entity.get('event_id_primary', 0)})
    else:
        for entity in data['map'].get('entities') or []:
            p = entity['position']
            entities.append({'name': entity.get('name', ''), 'id': entity.get('decoration_list_id', -1),
                             'at': tuple(p), 'event': entity.get('event_id_secondary', 0)
                             or entity.get('event_id_primary', 0)})

    # Decorations the studio hung on purpose (a ceiling brazier, a chandelier): its sidecar lists their entity numbers.
    hanging = set()
    sidecar = path.with_suffix('.studio.yml')
    if sidecar.exists():
        for line in sidecar.read_text().splitlines():
            if line.startswith('hanging_decorations:'):
                hanging = {int(v) for v in re.findall(r'\d+', line.split(':', 1)[1])}

    for number, entity in enumerate(entities):
        if number in hanging:
            continue
        row = by_name.get(entity['name'].strip().lower(), entity['id'])
        kind = by_id.get(row) or by_id.get(entity['id'])
        if kind is None or not kind['blocks'] or kind['hint'].lower() in ('null', 'pending', ''):
            continue
        if any(word in entity['name'].lower() for word in HANG_WORDS):
            continue
        if kind['name'].lower().startswith(('7tree', 'tree')) or 'tree' in kind['hint'].lower() \
                or NATURAL_WORDS.search((kind['name'] + ' ' + kind['hint']).lower()):
            continue
        x, y, z = entity['at']
        radius = kind['radius']
        # --regrounded: as the studio will place it once it stands things on the game's terrain triangles (A1
        # request R2): a prop the studio stood on the land (at its bilinear height) goes to the triangle height.
        if regrounded and outdoor and abs(z - world.terrain.bilinear(x, y)) <= 2:
            z = world.terrain.height(x, y)
            entity = dict(entity, at=(x, y, z))
        middle = world.support(x, y, z)
        label = f"{entity['name']} ({kind['name']}, radius {radius:g})"
        if middle is None or z - middle > STEP:
            add('error', 'support.floating', entity['at'], f'{label} floats: nothing under its middle within '
                f'{STEP:g}' + ('' if middle is None else f' (ground {middle:.0f})'), prop=entity['name'])
            continue
        base = max(z, middle)
        set_piece = kind['set_piece'] or entity['event'] != 0
        # Sunk under a structure's top (P5 F72, X2 p13): the studio stands a decoration on the land, so one sketched
        # inside a quay slab, a paving or a deck stands under its top; a top up to SUNK_REACH over the base covering
        # the middle is no roof over the prop but the floor round it.
        if outdoor:
            over = [h - base for h in world.faces.floor_heights(x, y) if SUNK < h - base <= SUNK_REACH]
            if over:
                add('error', 'support.sunk', entity['at'], f'{label}: sunk {max(over):.0f} under a structure\'s top '
                    'that covers its middle (it stands on the land under it)', prop=entity['name'])
                continue
        overhang, drop = judge_footprint(world, base, ring(x, y, radius * 0.85), ring(x, y, radius + EDGE_REACH)
                                         + ring(x, y, radius + EDGE_REACH / 2), (x, y))
        cls = 'container' if kind['container'] else 'set piece' if set_piece else 'other'
        # Indoors small things stand on tables and shelves (a candle, a cup, a crystal ball): only a drop deeper than
        # furniture counts for them. Containers stand on the floor.
        if not outdoor and cls != 'container':
            overhang = overhang if overhang > FURNITURE else 0.0
            drop = drop if drop > FURNITURE else 0.0
        # Outdoors a bone pile or a skull pole may lie on a hillside: only a container must stand level.
        if outdoor and cls != 'container':
            overhang = overhang if overhang > SLOPE_OVERHANG else 0.0
            drop = drop if drop > SLOPE_EDGE_DROP else 0.0
        if overhang > OVERHANG:
            add('warning' if set_piece else 'error', 'support.overhang', entity['at'],
                f'{label}, a {cls}: part of its footprint is {min(overhang, 9999):.0f} over the ground or floor',
                prop=entity['name'], cls=cls)
        elif drop > EDGE_DROP:
            add('warning' if set_piece else 'error', 'support.edge', entity['at'],
                f'{label}, a {cls}: a drop of {min(drop, 9999):.0f} within {EDGE_REACH:g} of its footprint '
                '(it stands at an edge)', prop=entity['name'], cls=cls)

    # Chests.
    events_by_kind = defaultdict(set)
    for thing in things:
        events_by_kind[thing['kind']].add(thing['event'])
    def chest_pieces(textures):
        return sum(count for name, count in textures.items()
                   if name.startswith(('7gt002', 'gt002')) or MM6_CHEST.match(name))

    # A chest is a thing whose click opens one, or a clicked thing built mostly of chest pieces (a chest that asks a
    # question first is a panel).
    chest_things = [t for t in things if t['kind'] == 'chest'
                    or (t['faces'] >= 9 and chest_pieces(t['textures']) * 2 > t['faces'])]
    openings = [f for f in world.faces.faces if not f['floor'] and abs(f['n'][2]) < 0.5 and (
        (f['event'] and any(f['event'] in events_by_kind[k] for k in OPENING_KINDS))
        or f['texture'] in MOUTH_TEXTURES)]

    for thing in chest_things:
        textures = thing['textures']
        names = set(textures)
        title = thing['title']
        chest_faces = [f for f in world.faces.faces if f['event'] == thing['event']]
        if not chest_faces:
            continue
        lo = [min(f['min'][i] for f in chest_faces) for i in range(3)]
        hi = [max(f['max'][i] for f in chest_faces) for i in range(3)]
        middle = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2])
        label = f'chest "{title}" (event {thing["event"]}, {thing["group"]})'
        group = chest_faces[0]['group']

        shipped = False
        if thing['faces'] >= 18 and all(any(n == p + s for p in ('7gt002', 'gt002') for n in names)
                                        for s in ('a', 'b', 'c', 'e', 'g')):
            shipped = True
        elif all(MM6_CHEST.match(n) for n in names):
            shipped = True
        elif names <= CRATE_TEXTURES:
            shipped = True
        elif any(BOOKCASE.search(n) for n in names):
            shipped = True
        # Furniture that opens like a chest is not a chest: a sarcophagus, a coffin, a cabinet, a desk.
        if re.search(r'sarcophag|coffin|cabinet|bookcase|shelf|desk|wardrobe|cupboard|dresser', title, re.I):
            shipped = True
        if not shipped:
            add('error', 'chest.look', middle, f'{label}: {thing["faces"]} faces of '
                + ', '.join(f'{n} {c}' for n, c in sorted(textures.items()))
                + ': not a shipped chest (MM7/MM8 19 faces of 7gt002/gt002 pieces, MM6 ch1-ch5, a crate)',
                event=thing['event'], title=title)

        if PLACE_WORDS.search(title) and not CONTAINER_TITLE_WORDS.search(title):
            add('warning', 'chest.title', middle, f'{label}: its hover title names a place, not the chest',
                event=thing['event'], title=title)

        # In front of an opening: the chest's footprint against each opening face (outdoors 320 in front, 192 beside;
        # indoors the indoor dressing numbers: 192 from a door's plane).
        for face in openings:
            # A cave mouth's dark door face stands at the back of its arch (up to 256 deep): its opening reaches
            # that much further out.
            reach = (320.0 if outdoor else 192.0) + (256.0 if face['texture'] in MOUTH_TEXTURES and outdoor else 0.0)
            if face['event'] == thing['event']:
                continue
            if face['max'][2] < lo[2] - 64 or face['min'][2] > hi[2] + 64:
                continue
            nx, ny, _ = face['n']
            plan = math.hypot(nx, ny) or 1.0
            nx, ny = nx / plan, ny / plan
            fx0, fx1 = face['min'][0], face['max'][0]
            fy0, fy1 = face['min'][1], face['max'][1]
            cx, cy = (fx0 + fx1) / 2, (fy0 + fy1) / 2
            # A cupboard: the chest's sector is a dead end (one portal) too shallow for anything in it to stand
            # `reach` from this face (XD-04's cabinet behind its wainscot panel). The door is the cupboard's own.
            sector = sectors[thing['sector']] if 0 <= thing['sector'] < len(sectors) else None
            if sector is not None and len(sector.get('portal_faces') or []) == 1 and max(
                    abs((x - cx) * nx + (y - cy) * ny) for x in (sector['min'][0], sector['max'][0])
                    for y in (sector['min'][1], sector['max'][1])) <= reach + 64:
                continue
            tx, ty = -ny, nx
            half = max(abs((p[0] - cx) * tx + (p[1] - cy) * ty) for p in face['points'])
            worst = None
            for px, py in box_points(lo, hi, 0):
                ahead = (px - cx) * nx + (py - cy) * ny
                side = abs((px - cx) * tx + (py - cy) * ty)
                if abs(ahead) <= reach and side <= half + 64:
                    worst = ahead if worst is None or abs(ahead) < abs(worst) else worst
            if worst is not None:
                kind = next((k for k in OPENING_KINDS if face['event'] in events_by_kind[k]), 'cave mouth')
                other = next((t['title'] for t in things if t['event'] == face['event']), face['texture'])
                add('error', 'chest.entrance', middle, f'{label} stands {abs(worst):.0f} from the {kind} face of '
                    f'"{other}" (event {face["event"]}, {face["texture"]}), within its opening\'s width',
                    event=thing['event'], title=title, opening=face['event'])
                break

        base = lo[2]
        if regrounded and outdoor and abs(base - world.terrain.bilinear(*middle[:2])) <= 2:
            # R2: a chest or crate on the land stands at the lowest ground under its corners.
            base = min(world.terrain.height(px, py) for px, py in
                       [(lo[0], lo[1]), (hi[0], lo[1]), (lo[0], hi[1]), (hi[0], hi[1])])
        overhang, drop = judge_footprint(world, base, box_points(lo, hi, -4), box_points(lo, hi, EDGE_REACH),
                                         middle[:2], skip_group=group)
        if overhang > OVERHANG:
            add('error', 'support.overhang', middle, f'{label}: part of its footprint is {min(overhang, 9999):.0f} '
                'over the ground or floor', event=thing['event'], title=title, prop='chest')
        elif drop > EDGE_DROP:
            add('error', 'support.edge', middle, f'{label}: a drop of {min(drop, 9999):.0f} within {EDGE_REACH:g} '
                'of its footprint (it stands at an edge)', event=thing['event'], title=title, prop='chest')

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--assets', default=str(ROOT / 'assets_dev'))
    parser.add_argument('--maps', default='', help='comma-separated stems (default: every installed Xeen map)')
    parser.add_argument('--file', default='', help='one built map file (.odm/.blv) instead of installed stems')
    parser.add_argument('--scene', default='', help='its scene file (outdoors), when not beside it')
    parser.add_argument('--cache', default=str(ROOT / 'output' / 'xeen_fb' / 'support_cache'))
    parser.add_argument('--json', default='')
    parser.add_argument('--errors-only', action='store_true')
    parser.add_argument('--regrounded', action='store_true', help='judge outdoor props and chests as the studio will '
                        'stand them once A1 request R2 lands (game terrain triangles; chests at their lowest corner)')
    args = parser.parse_args()

    assets = Path(args.assets)
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    kinds = decoration_kinds(assets)
    maps_dir = assets / 'worlds' / 'xeen' / 'maps'
    if args.file:
        paths = [Path(args.file)]
    elif args.maps:
        paths = []
        for stem in args.maps.split(','):
            stem = stem.strip()
            for suffix in ('.odm', '.blv'):
                if (maps_dir / (stem + suffix)).exists():
                    paths.append(maps_dir / (stem + suffix))
    else:
        paths = sorted(list(maps_dir.glob('xeen_*.odm')) + list(maps_dir.glob('xeen_*.blv')))

    findings = []
    for path in paths:
        scene = Path(args.scene) if args.scene else None
        findings.extend(check_map(path, scene, assets, cache, kinds, args.regrounded))

    errors = 0
    for finding in findings:
        if finding['level'] == 'error':
            errors += 1
        elif args.errors_only:
            continue
        print(f"{finding['level']:7s} {finding['check']:17s} {finding['map']:12s} {finding['at']}  {finding['text']}")
    counts = defaultdict(int)
    for finding in findings:
        counts[(finding['level'], finding['check'])] += 1
    print(f'{len(paths)} maps: ' + ', '.join(f'{c} {k[1]} {k[0]}s' for k, c in sorted(counts.items())) or 'clean')
    if args.json:
        Path(args.json).write_text(json.dumps(findings, indent=1))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
