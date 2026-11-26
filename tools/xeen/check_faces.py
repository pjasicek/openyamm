#!/usr/bin/env python3
"""Faces that flicker or show their edges on Xeen's built maps (P2 feedback F30, F31; 2026-11-23).

The game draws every BModel face of an outdoor map and every face of an indoor map from both sides (no back-face
culling: game/outdoor/OutdoorRenderer.cpp and game/indoor/IndoorRenderer.cpp set no BGFX_STATE_CULL_* for them). So:

- `faces.back_to_back` (error): two drawn faces in one plane facing opposite ways whose polygons overlap. Both are drawn
  at the same depth from either side and each has its own lightmap, so they flicker (z-fighting): the Hunters' tent on
  X1 (the studio's tent lays its canvas once outward and once inward on the same points).
- `faces.coplanar` (error): two drawn faces in one plane facing the same way that overlap (the studio's build warns of
  these; a warning is easy to miss).
- `faces.on_land` (error, F58 2026-11-25): an upward model face lying on the land (within ON_LAND of the terrain as the
  game draws it) over ON_LAND_AREA square units: the face and the ground flicker (z-fighting). The ruins' sills where
  a wall is gone lay on the levelled land under the plot (X2 p11, X4 p2, X5 p5, X6 p2, p12). Decks, roads and slabs
  meant to cover the land stand over it; one that lies on it flickers just the same. Land as steep as ON_LAND_STEEP
  (0.35) or more crossing a level face is a seam, not a flicker (D-176: the band within ON_LAND is under a pixel wide),
  and is not counted. Each face is compared with its plane's own height at each sample (a sloping deck's mean height
  lay on the land somewhere along it).
- `faces.flipped` (error, F71 2026-11-26): a face of a rock shell (a `cave_mouth` or `hatch`) wound against its neighbours (every edge it shares with exactly
  one other face runs the same way in both, where a closed or open surface runs it once each way). The game draws the
  face, but the bake lights it from its back: it shows black (Sablewing's cave mouth on X7, p4/p5: the studio's cave
  shell chose each triangle's facing on its own and turned the ones a shake tilted down inward). Faces are flipped
  in turn until no face has more such edges than agreeing ones; what stays flipped is listed.
- `shell.open_edge` (error): a ruin's wall (a structure with `ruin:` in the map's sketch, or an indoor object with
  `ruin:`) must be a closed shell above the ground: every edge of its faces over the land is shared by another face.
  An open edge is a wall end or a corner seen as a paper-thin sheet (the Ruined watchtower on X1).

Two planes are one when their normals agree within about a twentieth of a degree (opposite for back to back) and every
point of each face lies within one unit of the other's plane; an overlap counts from 8 square units and 1.5 units wide
on average (as the studio's core/Coplanar.h). Portal and invisible faces are not drawn and not looked at.

  python3 tools/xeen/check_faces.py                       # every installed Xeen map (assets_dev)
  python3 tools/xeen/check_faces.py --maps xeen_x1,xeen_d1 [--assets ROOT] [--file built.odm] [--json out.json]
  python3 tools/xeen/check_faces.py --check               # exit 1 on any error not listed in check_faces.yml
  python3 tools/xeen/check_faces.py --self-test           # the plane test on known faces

Each map is exported once with `oymap export` into the cache (`output/xeen_fb/faces_cache/`, refreshed when the map
is newer). Known findings that a decision keeps are listed in `tools/xeen/check_faces.yml` with the reason.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OYMAP = ROOT / 'openyamm-studio' / 'build-xeen' / 'oymap'
PORTAL = 0x00000001
INVISIBLE = 0x00002000
NORMAL_COS = math.cos(math.radians(0.05))
PLANE_UNITS = 1.0
MIN_AREA = 8.0
MIN_WIDTH = 1.5
EDGE_OPEN = 8.0        # an edge is open when more than this much of it has no other face along it
OVER_LAND = 8.0        # an edge counts as over the land when one end stands this far over the terrain


def export_map(path: Path, assets: Path, cache: Path) -> dict:
    cache.mkdir(parents=True, exist_ok=True)
    out = cache / (path.name + '.json')
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        subprocess.run([str(OYMAP), 'export', str(path), '--world', 'xeen', '--assets', str(assets), '--out',
                        str(out)], capture_output=True, text=True, timeout=600, check=True)
    return json.loads(out.read_text())['map']


# ---- geometry ----

def unit(vector):
    length = math.sqrt(sum(component * component for component in vector)) or 1.0
    return tuple(component / length for component in vector)


def basis(normal):
    nx, ny, nz = normal
    helper = (0.0, 0.0, 1.0) if abs(nz) < 0.9 else (1.0, 0.0, 0.0)
    u = unit((helper[1] * nz - helper[2] * ny, helper[2] * nx - helper[0] * nz, helper[0] * ny - helper[1] * nx))
    v = (ny * u[2] - nz * u[1], nz * u[0] - nx * u[2], nx * u[1] - ny * u[0])
    return u, v


def area2(points):
    total = 0.0
    for index, (x1, y1) in enumerate(points):
        x2, y2 = points[(index + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return total * 0.5


def perimeter2(points):
    return sum(math.dist(points[index], points[(index + 1) % len(points)]) for index in range(len(points)))


def clip(subject, clipper):
    """Sutherland-Hodgman: subject clipped by a convex clipper (both counter-clockwise)."""
    output = subject
    for index in range(len(clipper)):
        if not output:
            break
        a = clipper[index]
        b = clipper[(index + 1) % len(clipper)]
        inputs = output
        output = []

        def inside(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= -1e-9

        def cross(p, q):
            dx1, dy1 = q[0] - p[0], q[1] - p[1]
            dx2, dy2 = b[0] - a[0], b[1] - a[1]
            denominator = dx1 * dy2 - dy1 * dx2
            if abs(denominator) < 1e-12:
                return q
            t = ((a[0] - p[0]) * dy2 - (a[1] - p[1]) * dx2) / denominator
            return (p[0] + dx1 * t, p[1] + dy1 * t)

        for position, current in enumerate(inputs):
            previous = inputs[position - 1]
            if inside(current):
                if not inside(previous):
                    output.append(cross(previous, current))
                output.append(current)
            elif inside(previous):
                output.append(cross(previous, current))
    return output


def triangles(points):
    """A fan: Xeen's faces are convex polygons."""
    return [[points[0], points[index], points[index + 1]] for index in range(1, len(points) - 1)]


def overlap(first, second):
    """The area two polygons of one plane share (each split into triangles, so concave faces count right), and its
    average width (twice the area over the perimeter of the shared parts)."""
    total = 0.0
    perimeter = 0.0
    for a in triangles(first):
        if area2(a) < 0:
            a = a[::-1]
        for b in triangles(second):
            if area2(b) < 0:
                b = b[::-1]
            shared = clip(a, b)
            if len(shared) >= 3:
                piece = abs(area2(shared))
                if piece > 1e-6:
                    total += piece
                    perimeter += perimeter2(shared)
    return total, (2.0 * total / perimeter if perimeter > 0 else 0.0)


# ---- faces of a map ----

class Face:
    __slots__ = ('index', 'model', 'texture', 'points', 'normal', 'd', 'event')

    def __init__(self, index, model, texture, points, normal, event):
        self.index = index
        self.model = model
        self.texture = texture
        self.points = points
        self.normal = normal
        self.d = -sum(normal[axis] * points[0][axis] for axis in range(3))
        self.event = event


def faces_of(data: dict) -> list[Face]:
    faces = []
    if data.get('kind') == 'outdoor' or 'bmodels' in data:
        for model in data['bmodels']:
            vertices = model['vertices']
            for face in model['faces']:
                if face['attributes'] & (PORTAL | INVISIBLE):
                    continue
                points = [tuple(float(c) for c in vertices[i]) for i in face['vertices']]
                if len(points) < 3:
                    continue
                normal = unit(face['plane_normal'])
                faces.append(Face(len(faces), model['name'], face['texture'].lower(), points, normal,
                                  face.get('cog_trigger') or face.get('cog_number') or 0))
    else:
        vertices = data['vertices']
        for number, face in enumerate(data['faces']):
            if face.get('is_portal') or face['attributes'] & (PORTAL | INVISIBLE):
                continue
            points = [tuple(float(c) for c in vertices[i]) for i in face['vertices']]
            if len(points) < 3:
                continue
            normal = unit(face['plane_normal'])
            faces.append(Face(len(faces), 'face %d (sector %d)' % (number, face.get('room', -1)),
                              face['texture'].lower(), points, normal, face.get('cog_number') or 0))
    return faces


def plane_pairs(faces: list[Face]):
    """Pairs of faces in one plane: (first, second, same way)."""
    buckets = defaultdict(list)
    for face in faces:
        # a plane's key with the normal folded to one side, so back-to-back faces share it
        n = face.normal
        sign = 1.0
        for component in n:
            if abs(component) > 1e-6:
                sign = 1.0 if component > 0 else -1.0
                break
        folded = (n[0] * sign, n[1] * sign, n[2] * sign)
        distance = face.d * sign
        # the distance coarse: two faces of one plane tilted by rounding differ in it by more than they lie apart
        key = (round(folded[0] * 200), round(folded[1] * 200), round(folded[2] * 200), round(distance / 32.0))
        buckets[key].append(face)
    seen = set()
    for key, members in buckets.items():
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for dd in (-1, 0, 1):
                        near.extend(buckets.get((key[0] + dx, key[1] + dy, key[2] + dz, key[3] + dd), ()))
        for first in members:
            for second in near:
                if second.index <= first.index or (first.index, second.index) in seen:
                    continue
                dot = sum(first.normal[axis] * second.normal[axis] for axis in range(3))
                if abs(dot) < NORMAL_COS:
                    continue
                same = dot > 0
                # One plane: every point of each face within a unit of the other's plane. Comparing the planes'
                # constants alone cannot tell faces 8 apart 20,000 units out once integer vertices tilt one of them
                # by a few hundredths of a degree (a fence rail's two sides on a slope, X5 palisade_1).
                if (max(abs(sum(first.normal[axis] * p[axis] for axis in range(3)) + first.d) for p in second.points)
                        > PLANE_UNITS
                        or max(abs(sum(second.normal[axis] * p[axis] for axis in range(3)) + second.d)
                               for p in first.points) > PLANE_UNITS):
                    continue
                if any(max(p[axis] for p in first.points) < min(p[axis] for p in second.points) - 0.5
                       or min(p[axis] for p in first.points) > max(p[axis] for p in second.points) + 0.5
                       for axis in range(3)):
                    continue
                seen.add((first.index, second.index))
                yield first, second, same


class Rays:
    """Where a point stands: in the open (a ray from it meets a face's front first, the land from above, or nothing)
    or shut inside a solid (its rays meet faces' backs). Faces face out of the solids they bound (BModels outdoors,
    the rooms' walls indoors), so two solids touching leave their touching faces back to back, unseen."""

    CELL = 512.0
    REACH = 8192.0
    DIRECTIONS = [(1, 0.013, 0.007), (-1, -0.011, 0.009), (0.012, 1, 0.006), (-0.008, -1, 0.011),
                  (0.009, 0.007, 1), (0.006, -0.012, -1)]

    def __init__(self, faces: list[Face], terrain: Terrain | None):
        self.terrain = terrain
        self.grid = defaultdict(list)
        self.flat = {}
        for face in faces:
            lo = [min(p[axis] for p in face.points) for axis in range(2)]
            hi = [max(p[axis] for p in face.points) for axis in range(2)]
            for gx in range(int(lo[0] // self.CELL), int(hi[0] // self.CELL) + 1):
                for gy in range(int(lo[1] // self.CELL), int(hi[1] // self.CELL) + 1):
                    self.grid[(gx, gy)].append(face)
            u, v = basis(face.normal)
            self.flat[face.index] = (u, v, [(sum(p[i] * u[i] for i in range(3)), sum(p[i] * v[i] for i in range(3)))
                                            for p in face.points])

    def hit(self, face: Face, origin, direction):
        denominator = sum(face.normal[axis] * direction[axis] for axis in range(3))
        if abs(denominator) < 1e-9:
            return None
        t = -(sum(face.normal[axis] * origin[axis] for axis in range(3)) + face.d) / denominator
        if t <= 0.5 or t > self.REACH:
            return None
        point = [origin[axis] + direction[axis] * t for axis in range(3)]
        u, v, polygon = self.flat[face.index]
        px = sum(point[i] * u[i] for i in range(3))
        py = sum(point[i] * v[i] for i in range(3))
        inside = False
        for index, (x1, y1) in enumerate(polygon):
            x2, y2 = polygon[index - 1]
            if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
                inside = not inside
        return (t, denominator < 0) if inside else None

    def ray_open(self, origin, direction, skip) -> bool:
        direction = unit(direction)
        cells = set()
        steps = int(self.REACH // 256) + 1
        for step in range(steps):
            x = origin[0] + direction[0] * step * 256
            y = origin[1] + direction[1] * step * 256
            cells.add((int(x // self.CELL), int(y // self.CELL)))
            if abs(direction[2]) > 0.99:
                break
        best = None
        for cell in cells:
            for face in self.grid.get(cell, ()):
                if face.index in skip:
                    continue
                found = self.hit(face, origin, direction)
                if found and (best is None or found[0] < best[0]):
                    best = found
        if self.terrain is not None and direction[2] < 0:
            reach = best[0] if best else self.REACH
            t = 16.0
            while t < reach:
                point = [origin[axis] + direction[axis] * t for axis in range(3)]
                if point[2] < self.terrain.height(point[0], point[1]):
                    return True
                t += 32.0
        if best is None:
            # outdoors a ray that meets nothing reaches the sky; indoors everything outside the rooms is rock
            return self.terrain is not None
        return best[1]

    def open_at(self, point, skip) -> bool:
        votes = sum(1 for direction in self.DIRECTIONS if self.ray_open(point, direction, skip))
        return votes >= 4


def coplanar_findings(faces: list[Face], terrain: Terrain | None = None) -> list[dict]:
    findings = []
    rays = None
    for first, second, same in plane_pairs(faces):
        u, v = basis(first.normal)
        flat_first = [(sum(p[i] * u[i] for i in range(3)), sum(p[i] * v[i] for i in range(3))) for p in first.points]
        flat_second = [(sum(p[i] * u[i] for i in range(3)), sum(p[i] * v[i] for i in range(3))) for p in second.points]
        area, width = overlap(flat_first, flat_second)
        if area < MIN_AREA or width < MIN_WIDTH:
            continue
        middle = [round(sum(p[axis] for p in first.points) / len(first.points)) for axis in range(3)]
        if not same:
            # back to back: seen only when one of its sides is open space (two solids touching hide both)
            if rays is None:
                rays = Rays(faces, terrain)
            skip = {first.index, second.index}
            centre = shared_centre(first, second, u, v, flat_first, flat_second)
            sides = [rays.open_at([centre[axis] + first.normal[axis] * way * 2.0 for axis in range(3)], skip)
                     for way in (1.0, -1.0)]
            if not any(sides):
                continue
        rule = 'faces.coplanar' if same else 'faces.back_to_back'
        findings.append({'rule': rule, 'severity': 'error', 'model': first.model, 'other': second.model,
                         'textures': [first.texture, second.texture], 'area': round(area), 'at': middle,
                         'text': '%s (%s) and %s (%s): one plane, %s, overlap %d sq units at %s' % (
                             first.model, first.texture, second.model, second.texture,
                             'facing the same way' if same else 'back to back', area, middle)})
    return findings


def shared_centre(first, second, u, v, flat_first, flat_second):
    """The middle of the two faces' shared part, back in 3D on the first face's plane."""
    best = None
    for a in triangles(flat_first):
        if area2(a) < 0:
            a = a[::-1]
        for b in triangles(flat_second):
            if area2(b) < 0:
                b = b[::-1]
            shared = clip(a, b)
            if len(shared) >= 3:
                piece = abs(area2(shared))
                if best is None or piece > best[0]:
                    best = (piece, (sum(p[0] for p in shared) / len(shared), sum(p[1] for p in shared) / len(shared)))
    cx, cy = best[1]
    n = first.normal
    w = -first.d
    return [u[axis] * cx + v[axis] * cy + n[axis] * w for axis in range(3)]


# ---- terrain ----

class Terrain:
    def __init__(self, data):
        terrain = data['terrain']
        self.width = terrain['width']
        self.scale = terrain['height_scale']
        self.heights = terrain['height_map']

    def node(self, x, y):
        x = min(max(x, 0), self.width - 1)
        y = min(max(y, 0), self.width - 1)
        return self.heights[y * self.width + x] * self.scale

    def height(self, wx, wy):
        gx = wx / 512.0 + 64.0
        gy = 64.0 - wy / 512.0
        x0 = int(math.floor(gx))
        y0 = int(math.floor(gy))
        fx = gx - x0
        fy = gy - y0
        z00, z10 = self.node(x0, y0), self.node(x0 + 1, y0)
        z01, z11 = self.node(x0, y0 + 1), self.node(x0 + 1, y0 + 1)
        # the game's split (OutdoorMovementController terrainSlopeTooHigh)
        if fx >= fy:
            return z00 + (z10 - z00) * fx + (z11 - z10) * fy
        return z00 + (z11 - z01) * fx + (z01 - z00) * fy


# ---- open edges of ruins ----

def ruin_ids(project: Path) -> set[str]:
    ids = set()
    for name in ('sketch.yml', 'objects.yml'):
        path = project / name
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text()) or {}
        for key in ('structures', 'objects'):
            for entry in data.get(key) or []:
                if not isinstance(entry, dict):
                    continue
                if entry.get('ruin') or any(isinstance(part, dict) and part.get('ruin')
                                            for part in entry.get('parts') or []):
                    ids.add(entry.get('id'))
    return ids


def open_edges(faces: list[Face], terrain: Terrain | None, floor_z=None) -> list[tuple]:
    """Edges of the faces (one model) not lying along another face's edge for more than EDGE_OPEN units."""
    lines = defaultdict(list)
    edges = []
    for face in faces:
        for index, a in enumerate(face.points):
            b = face.points[(index + 1) % len(face.points)]
            length = math.dist(a, b)
            if length < 1.0:
                continue
            direction = tuple((b[axis] - a[axis]) / length for axis in range(3))
            # fold the direction to one way round
            for component in direction:
                if abs(component) > 1e-6:
                    if component < 0:
                        direction = tuple(-c for c in direction)
                        a, b = b, a
                    break
            # the line's closest point to the origin
            t = -sum(a[axis] * direction[axis] for axis in range(3))
            foot = tuple(a[axis] + direction[axis] * t for axis in range(3))
            key = (round(direction[0] * 100), round(direction[1] * 100), round(direction[2] * 100),
                   round(foot[0] / 4), round(foot[1] / 4), round(foot[2] / 4))
            start = sum(a[axis] * direction[axis] for axis in range(3))
            end = sum(b[axis] * direction[axis] for axis in range(3))
            edge = (face.index, a, b, key, start, end)
            edges.append(edge)
            lines[key].append(edge)
    found = []
    for face_index, a, b, key, start, end in edges:
        if terrain is not None:
            over = max(a[2] - terrain.height(a[0], a[1]), b[2] - terrain.height(b[0], b[1]))
        else:
            over = max(a[2], b[2]) - (floor_z if floor_z is not None else -1e9)
        if over <= OVER_LAND:
            continue
        covers = []
        for dk0 in (-1, 0, 1):
            for dk3 in (-1, 0, 1):
                for dk4 in (-1, 0, 1):
                    for dk5 in (-1, 0, 1):
                        near = (key[0] + dk0 * 0, key[1], key[2], key[3] + dk3, key[4] + dk4, key[5] + dk5)
                        for other in lines.get(near, ()):
                            if other[0] == face_index:
                                continue
                            # the other edge must lie on this edge's line
                            if point_line_distance(other[1], a, b) > 1.0 or point_line_distance(other[2], a, b) > 1.0:
                                continue
                            covers.append((max(start, other[4]), min(end, other[5])))
        covers = sorted(c for c in covers if c[1] > c[0])
        covered = 0.0
        reach = start
        for low, high in covers:
            if high <= reach:
                continue
            covered += high - max(low, reach)
            reach = high
        if (end - start) - covered > EDGE_OPEN:
            found.append((a, b, (end - start) - covered))
    return found


def point_line_distance(point, a, b):
    ab = [b[axis] - a[axis] for axis in range(3)]
    ap = [point[axis] - a[axis] for axis in range(3)]
    length = math.sqrt(sum(c * c for c in ab)) or 1.0
    cross = (ab[1] * ap[2] - ab[2] * ap[1], ab[2] * ap[0] - ab[0] * ap[2], ab[0] * ap[1] - ab[1] * ap[0])
    return math.sqrt(sum(c * c for c in cross)) / length


def shell_findings(faces: list[Face], ruins: set[str], terrain: Terrain | None) -> list[dict]:
    findings = []
    by_model = defaultdict(list)
    for face in faces:
        base = face.model.split('#')[0]
        if base in ruins:
            by_model[face.model].append(face)
    for model, members in sorted(by_model.items()):
        edges = open_edges(members, terrain)
        if not edges:
            continue
        total = sum(length for _, _, length in edges)
        first = edges[0]
        findings.append({'rule': 'shell.open_edge', 'severity': 'error', 'model': model, 'other': '',
                         'textures': sorted({face.texture for face in members}), 'area': round(total),
                         'at': [round(c) for c in first[0]],
                         'text': '%s: a ruin with %d open edges over the land (%d units in all; first from %s to %s): '
                                 'wall ends or corners drawn as single sheets' % (
                                     model, len(edges), total, [round(c) for c in first[0]],
                                     [round(c) for c in first[1]])})
    return findings


# ---- the maps ----

ON_LAND = 2.0          # a face this near the land flickers with it
ON_LAND_AREA = 512.0   # ... over at least this much of it (square units; sampled every ON_LAND_STEP)
ON_LAND_STEP = 8.0
# D-176 (2026-11-25): land this steep (rise over run, central difference over ON_LAND_SLOPE_REACH each way) crosses a
# level face in a seam, not a flicker: the band where the two are within ON_LAND of each other is under a pixel wide
# (the cave crests on X1, X2, X5, X7 at 0.44-1.17, X1's culvert and shaft head, X7's XD-05 gate)
ON_LAND_STEEP = 0.35
ON_LAND_SLOPE_REACH = 4.0
WATER_WORDS = ('wtr', 'water', 'lava', 'swmp')


def on_land_findings(faces: list[Face], terrain: Terrain) -> list[dict]:
    """Upward faces lying on the land (faces.on_land)."""
    findings = []
    for face in faces:
        if face.normal[2] < 0.999 or any(word in face.texture for word in WATER_WORDS):
            continue      # a water face lies on the land the studio levels to its surface (a fall's pool): by design
        xs = [p[0] for p in face.points]
        ys = [p[1] for p in face.points]
        z = sum(p[2] for p in face.points) / len(face.points)
        flat = [(p[0], p[1]) for p in face.points]
        hits = []
        x = min(xs) + ON_LAND_STEP / 2
        while x < max(xs):
            y = min(ys) + ON_LAND_STEP / 2
            while y < max(ys):
                # the plane's own height at the point: a sloping deck's mean height lies on the land somewhere along
                # it while the deck stands well over it there (X3's causeway, D3's Wrath Bridge; 2026-11-25)
                if point_in(flat, x, y) and abs(terrain.height(x, y) + (face.normal[0] * x + face.normal[1] * y
                                                                        + face.d) / face.normal[2]) <= ON_LAND \
                        and land_slope(terrain, x, y) < ON_LAND_STEEP:
                    hits.append((x, y))
                y += ON_LAND_STEP
            x += ON_LAND_STEP
        area = len(hits) * ON_LAND_STEP * ON_LAND_STEP
        if area < ON_LAND_AREA:
            continue
        at = [round(sum(h[0] for h in hits) / len(hits)), round(sum(h[1] for h in hits) / len(hits)), round(z)]
        findings.append({'rule': 'faces.on_land', 'severity': 'error', 'model': face.model, 'other': 'terrain',
                         'textures': [face.texture], 'area': round(area), 'at': at,
                         'text': '%s (%s) lies on the land over %d sq units at %s: it flickers with the ground' % (
                             face.model, face.texture, area, at)})
    return findings


def land_slope(terrain, x, y) -> float:
    """The land's slope at a point (rise over run) as the game draws it, by central differences (D-176)."""
    r = ON_LAND_SLOPE_REACH
    dx = (terrain.height(x + r, y) - terrain.height(x - r, y)) / (2 * r)
    dy = (terrain.height(x, y + r) - terrain.height(x, y - r)) / (2 * r)
    return math.hypot(dx, dy)


def point_in(poly, x, y) -> bool:
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def project_of(stem: str) -> Path | None:
    key = stem.replace('xeen_', '')
    path = ROOT / 'devdocs' / 'xeen' / 'briefs' / key / 'L4'
    if path.exists():
        return path
    return None


SHELL_KINDS = ('cave_mouth', 'hatch')


def shell_ids(project: Path) -> set[str]:
    """The sketch's rock shells (cave mouths, hatches): one surface each, where faces.flipped is judged (a building's
    or a bridge's blocks meet other solids along shared edges, and their hidden butt faces run either way)."""
    path = project / 'sketch.yml'
    data = yaml.safe_load(path.read_text()) if path.exists() else {}
    return {entry.get('id') for entry in (data or {}).get('structures') or []
            if isinstance(entry, dict) and entry.get('kind') in SHELL_KINDS}


def flipped_findings(data: dict, shells: set[str]) -> list[dict]:
    """Shell faces wound against their neighbours (faces.flipped): the bake lights them from behind, black."""
    findings = []
    for model in data.get('bmodels') or []:
        if model['name'] not in shells:
            continue
        vertices = model['vertices']
        key = [tuple(round(float(c)) for c in v) for v in vertices]
        edges = defaultdict(list)
        drawn = [face for face in model['faces'] if not face['attributes'] & (PORTAL | INVISIBLE)]
        for number, face in enumerate(drawn):
            ring = [key[i] for i in face['vertices']]
            for a, b in zip(ring, ring[1:] + ring[:1]):
                if a != b:
                    edges[frozenset((a, b))].append((number, (a, b)))
        # one surface: the pairs of one texture (a gable's top edge meets the roof's underside, another solid's
        # surface, along the same line; X3's Camp Shrine)
        pairs = [(l[0], l[1]) for l in edges.values() if len(l) == 2 and l[0][0] != l[1][0]
                 and drawn[l[0][0]]['texture'].lower() == drawn[l[1][0]]['texture'].lower()]
        flip = set()
        for _ in range(32):
            good, bad = defaultdict(int), defaultdict(int)
            for (f1, d1), (f2, d2) in pairs:
                same = (d1 == d2) != ((f1 in flip) != (f2 in flip))
                for f in (f1, f2):
                    (bad if same else good)[f] += 1
            more = {f for f in bad if bad[f] > good[f]}
            if not more:
                break
            flip ^= more
        if not flip or len(flip) * 2 > len(drawn):
            continue      # the minority is the flipped side
        for number in sorted(flip):
            face = drawn[number]
            points = [vertices[i] for i in face['vertices']]
            at = [round(sum(float(p[axis]) for p in points) / len(points)) for axis in range(3)]
            findings.append({'rule': 'faces.flipped', 'severity': 'error', 'model': model['name'], 'other': '',
                             'textures': [face['texture'].lower()], 'at': at,
                             'text': '%s (%s) is wound against its neighbours at %s: the bake lights it from '
                                     'behind (black)' % (model['name'], face['texture'].lower(), at)})
    return findings


def check_map(path: Path, assets: Path, cache: Path) -> list[dict]:
    data = export_map(path, assets, cache)
    faces = faces_of(data)
    terrain = Terrain(data) if 'bmodels' in data else None
    findings = coplanar_findings(faces, terrain)
    if terrain is not None:
        findings += on_land_findings(faces, terrain)
    project = project_of(path.stem)
    if project is not None:
        ruins = ruin_ids(project)
        if ruins and terrain is not None:
            findings += shell_findings(faces, ruins, terrain)
        if terrain is not None:
            findings += flipped_findings(data, shell_ids(project))
    for finding in findings:
        finding['map'] = path.stem
    return findings


def kept(finding: dict, exceptions: list[dict]) -> str | None:
    for entry in exceptions:
        if entry.get('map') == finding['map'] and entry.get('rule') == finding['rule'] \
                and entry.get('model') in (finding['model'], finding['model'].split('#')[0]):
            return entry.get('reason', '')
    return None


def self_test() -> int:
    """The plane test on faces of a built map: X5's palisade rail, whose two sides 8 apart at x -17,600 the constants'
    comparison took for one plane (2026-11-24), and a sign laid on a board (one plane)."""
    def face(index, points, normal):
        return Face(index, 'test', 't', [tuple(float(c) for c in p) for p in points], unit(normal), 0)
    near = face(0, [(-17640, 15404, 1161), (-17471, 15419, 1164), (-17471, 15419, 1172), (-17640, 15404, 1169)],
                (5794, -65279, 0))
    far = face(1, [(-17471, 15427, 1164), (-17641, 15412, 1161), (-17641, 15412, 1169), (-17471, 15427, 1172)],
               (-5760, 65282, 0))
    board = face(2, [(20000, 20000, 0), (20100, 20000, 0), (20100, 20000, 100), (20000, 20000, 100)], (0, -1, 0))
    sign = face(3, [(20020, 20000, 20), (20080, 20000, 20), (20080, 20000, 80), (20020, 20000, 80)], (0, -1, 0))
    failures = []

    class Ramp:
        """Land rising `slope` along x through height 100 at x 0."""
        def __init__(self, slope):
            self.slope = slope

        def height(self, x, y):
            return 100.0 + self.slope * x
    level = face(4, [(-200, -100, 100), (200, -100, 100), (200, 100, 100), (-200, 100, 100)], (0, 0, 1))
    if on_land_findings([level], Ramp(0.44)):
        failures.append('a level face crossed by land at slope 0.44 counted as lying on it (D-176: a seam)')
    if not on_land_findings([level], Ramp(0.125)):
        failures.append('a level face on land at slope 0.125 not counted (a 32-wide band of 200)')
    if list(plane_pairs([near, far])):
        failures.append("a rail's two sides 8 apart are one plane")
    if len(list(plane_pairs([board, sign]))) != 1:
        failures.append('a sign on its board is not one plane')
    for failure in failures:
        print('self-test:', failure)
    print('self-test: %s' % ('FAIL' if failures else 'ok'))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--self-test', action='store_true', help='the plane test on known faces, then exit')
    parser.add_argument('--assets', default=str(ROOT / 'assets_dev'))
    parser.add_argument('--maps', help='comma-separated stems (xeen_x1,xeen_dd02); default every Xeen map')
    parser.add_argument('--file', help='a built .odm/.blv (with --maps naming its stem for the project)')
    parser.add_argument('--cache', default=str(ROOT / 'output' / 'xeen_fb' / 'faces_cache'))
    parser.add_argument('--json')
    parser.add_argument('--check', action='store_true', help='exit 1 on an error not kept in check_faces.yml')
    parser.add_argument('--quiet', action='store_true', help='per-map counts only')
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    assets = Path(args.assets)
    cache = Path(args.cache)
    maps_dir = assets / 'worlds' / 'xeen' / 'maps'
    if args.file:
        paths = [Path(args.file)]
    elif args.maps:
        paths = []
        for stem in args.maps.split(','):
            for suffix in ('.odm', '.blv'):
                if (maps_dir / (stem + suffix)).exists():
                    paths.append(maps_dir / (stem + suffix))
    else:
        paths = sorted(list(maps_dir.glob('xeen_*.odm')) + list(maps_dir.glob('xeen_*.blv')))
    exceptions_path = Path(__file__).with_name('check_faces.yml')
    exceptions = (yaml.safe_load(exceptions_path.read_text()) or {}).get('kept', []) if exceptions_path.exists() else []
    everything = []
    errors = 0
    for path in paths:
        findings = check_map(path, assets, cache)
        open_count = 0
        for finding in findings:
            reason = kept(finding, exceptions)
            finding['kept'] = reason
            if reason is None:
                open_count += 1
            if not args.quiet:
                print('%s %s %s: %s%s' % (finding['map'], 'kept' if reason is not None else finding['severity'],
                                          finding['rule'], finding['text'],
                                          (' (kept: %s)' % reason) if reason else ''))
        counts = defaultdict(int)
        for finding in findings:
            counts[finding['rule']] += 1
        print('%s: %s' % (path.stem, ', '.join('%s %d' % item for item in sorted(counts.items())) or 'clean'))
        errors += open_count
        everything += findings
    if args.json:
        Path(args.json).write_text(json.dumps(everything, indent=1))
    print('%d maps, %d findings, %d not kept' % (len(paths), len(everything), errors))
    return 1 if args.check and errors else 0


if __name__ == '__main__':
    sys.exit(main())
