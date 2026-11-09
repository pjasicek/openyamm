#!/usr/bin/env python3
"""Read-only audit of where monsters can walk in the built Hesper BLVs.

Monsters climb at most 50 per move and plan paths in 40-unit steps over rises of at most 40, dropping at most 100
(game/indoor/IndoorMovementController.cpp `MaximumRise`; IndoorWorldRuntime.cpp `stepHeight`, `dropHeight`).
DUNGEON_PLAYBOOK's rule: a riser where monsters move is at most 32, an edge meant to be out of reach at least 128, no
trench deeper than 32 without a walkable way out, and movers end flush. Every built map (`<map>.blv` and its
`<map>.scene.yml`) is checked for:

- step: an edge between two floors (faces sharing an edge, or a floor's boundary above another floor within REACH)
  that rises 33-127 and no wall closes, where monsters walk below it and the party can climb it (50 at most) or
  reach its top another way (the sheer side of a stair-served dais); the top of an obstacle nobody can climb onto
  is an unreachable region when a monster fits on it and is ignored when none does (a plinth, a pump's flange);
- flight: a climb of more than 40 within one 40-unit path step (treads too short for their risers: the planner's
  steps skip a tread);
- unreachable: a walkable region of at least a monster's footprint beside the open floor (the region of the party
  start, every region where placed monsters that move stand, and every region monsters can walk to from these and back) that
  monsters cannot climb onto; and a region where placed monsters stand that they cannot walk from to the party
  start (analysed as open floor too);
- pit: a region of at least a monster's footprint beside the open floor that monsters fall or step into and cannot
  leave;
- mover: a door, lift or lowering block whose top, at either end of its travel, sits below the floor around it (a
  recess) or 33-127 above it (a lip);
- actor: a placed actor not standing on a floor or overhanging an edge of more than two risers (unless it flies), or
  with a wall within its radius or a ceiling lower than its height.

Floors are rastered on a GRID; doors count as open (walls of movers never block) and movers' floors stand at both
ends of their travel. Deliberate unreachable regions and pits are listed per map in walkability_allow.yml with the
reason. Print per map the findings; exit 1 when a map named by --gate (default: every map) has any. Hold the shared
stage lock while reading.
"""
import argparse
import fcntl
import json
import math
import os
from collections import defaultdict, deque
from pathlib import Path
import sys

import numpy as np

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
STAGE = ROOT / 'output/hesper_stage'
ASSETS = STAGE / 'assets_editor_dev'
ALLOW = PROJECT / 'walkability_allow.yml'
MONSTER_TABLES = [ASSETS / 'worlds/hesper/data_tables/monster_data.txt', ASSETS / 'engine/data_tables/monster_data.txt']

GRID = 16            # the floor raster's cell
SHIFT = 0.37         # the raster's origin: off every authored (whole or half) coordinate, so no wall runs through a
                     # cell's centre
STEP_OK = 32         # the most a riser may rise where monsters move
MONSTER_STEP = 40    # the path planner's step height and step length
MONSTER_DROP = 100   # IndoorActorMaxDropHeight
PARTY_STEP = 50      # the most the party (and a monster's single move) climbs: MaximumRise
WALL = 128           # an edge at least this high is out of reach, not a step
REACH = 40           # a floor this far past another's edge is its neighbour (about a party radius)
BODY = 24            # a wall blocks a move when it stands this far above the higher floor
HEAD = 160           # a floor with less room above it is inside a solid (under a box) or too low to stand in
CORE = 3             # a region counts when it holds a square of 2 * CORE + 1 cells (about a monster's footprint)
FLOOR_NZ = 0.68664550781   # WalkableSlopeNormalZ
UNTOUCHABLE = 0x20000000
KINDS = ('step', 'flight', 'unreachable', 'pit', 'mover', 'actor')


class Face:
    """A polygon: points (n x 3), its unit normal (Newell's, from the winding, unless given), kind ('floor', 'wall' or
    'ceiling'), sector, and the door id of its mover (None when static) with the end of its travel (0 or 1)."""
    def __init__(self, points, normal=None, sector=0, door=None, pose=0):
        self.points = np.asarray(points, float)
        if normal is None:
            normal = np.zeros(3)
            for a, b in zip(self.points, np.roll(self.points, -1, axis=0)):
                normal += [(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]),
                           (a[0] - b[0]) * (a[1] + b[1])]
        normal = np.asarray(normal, float)
        self.normal = normal / (np.linalg.norm(normal) or 1)
        self.sector, self.door, self.pose = sector, door, pose
        nz = float(self.normal[2])
        self.kind = 'floor' if nz > FLOOR_NZ else 'ceiling' if nz < -FLOOR_NZ else 'wall'
        self.lo, self.hi = self.points.min(axis=0), self.points.max(axis=0)
        self.plan = [(float(x), float(y)) for x, y in self.points[:, :2]]
        if abs(nz) > 1e-6:
            nx, ny = float(self.normal[0]), float(self.normal[1])
            p = self.points[0]
            self.slope = (-nx / nz, -ny / nz, float(p[2]) + (nx * float(p[0]) + ny * float(p[1])) / nz)

    def z_at(self, x, y):
        a, b, c = self.slope
        return a * x + b * y + c

    def contains(self, x, y):
        inside = False
        pts = self.plan
        ax, ay = pts[-1]
        for bx, by in pts:
            if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                inside = not inside
            ax, ay = bx, by
        return inside

    def raster(self):
        """The cells whose centres the face covers in plan: (i, j, z at the centre)."""
        (i0, j0), (i1, j1) = cell_of(self.lo[0], self.lo[1]), cell_of(self.hi[0], self.hi[1])
        ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing='ij')
        xs, ys = (ii + 0.5) * GRID + SHIFT, (jj + 0.5) * GRID + SHIFT
        inside = np.zeros(xs.shape, bool)
        pts = self.points[:, :2]
        for (ax, ay), (bx, by) in zip(np.roll(pts, 1, axis=0), pts):
            if ay == by:
                continue
            inside ^= ((ay > ys) != (by > ys)) & (xs < ax + (ys - ay) * (bx - ax) / (by - ay))
        a, b, c = self.slope
        return [(int(i), int(j), float(a * x + b * y + c))
                for i, j, x, y in zip(ii[inside], jj[inside], xs[inside], ys[inside])]


class Level:
    """One map: static faces, movers (door id -> its faces at each end of the travel), party start, placed actors
    and sector names. Floors and ceilings are rastered per cell; walls are plan segments indexed by cell."""
    def __init__(self, name, faces, start, actors=(), movers=None, rooms=None):
        self.name, self.start, self.actors, self.rooms = name, start, list(actors), rooms or {}
        self.movers = movers or {}
        self.surfaces = defaultdict(list)        # cell -> (z, kind, face), static floors and ceilings
        self.walls, self.wall_cells = [], defaultdict(list)
        for face in faces:
            if face.kind == 'wall':
                self._add_wall(face)
            else:
                for i, j, z in face.raster():
                    self.surfaces[(i, j)].append((z, face.kind, face))
        self.cells = defaultdict(list)           # cell -> (z, face), floors with room above them, and movers'
        for cell, entries in self.surfaces.items():
            entries.sort(key=lambda e: e[0])
            for z, kind, face in entries:
                if kind == 'floor' and self._room(entries, z) >= HEAD:
                    self.cells[cell].append((z, face))
        for poses in self.movers.values():
            for pose in poses:
                for face in pose:
                    if face.kind == 'floor':
                        for i, j, z in face.raster():
                            self.cells[(i, j)].append((z, face))

    def room(self, sector):
        return self.rooms.get(sector, f'sector {sector}')

    def _add_wall(self, face):
        """A wall's plan segment (its two extreme points along the plane), its z range and the cells it crosses."""
        horizontal = np.cross(face.normal, (0, 0, 1))
        length = np.linalg.norm(horizontal)
        if length < 1e-6:
            return
        along = face.points @ (horizontal / length)
        a, b = face.points[along.argmin()], face.points[along.argmax()]
        wid = len(self.walls)
        self.walls.append((float(a[0]), float(a[1]), float(b[0]), float(b[1]), float(face.lo[2]), float(face.hi[2])))
        for cell in cells_along(a[0], a[1], b[0], b[1]):
            self.wall_cells[cell].append(wid)

    def blocked(self, ax, ay, bx, by, height):
        """Whether a wall standing through `height` crosses the move from (ax, ay) to (bx, by)."""
        seen = set()
        for cell in cells_along(ax, ay, bx, by):
            for wid in self.wall_cells.get(cell, ()):
                if wid in seen:
                    continue
                seen.add(wid)
                x0, y0, x1, y1, z0, z1 = self.walls[wid]
                if z0 < height < z1 and segments_cross(ax, ay, bx, by, x0, y0, x1, y1):
                    return True
        return False

    @staticmethod
    def _room(entries, z):
        room = math.inf
        for ze, kind, _ in entries:
            if kind == 'floor' and ze > z + 1 or kind == 'ceiling' and ze > z - 1:
                room = min(room, max(ze - z, 0))
        return room

    def headroom(self, x, y, z):
        """The room above a floor at (x, y, z) to the next static floor or ceiling over that cell."""
        return self._room(self.surfaces.get(cell_of(x, y), ()), z)

    def floors_at(self, x, y):
        """(z at (x, y), face) of every floor over the cell of (x, y) with room above it, movers' at both ends."""
        return [(face.z_at(x, y), face) for _, face in self.cells.get(cell_of(x, y), ())]

    def floors_exact(self, x, y):
        """(z, face) of every floor with room above it whose polygon holds (x, y), from its cell and the next."""
        i, j = cell_of(x, y)
        faces = {id(f): f for di in (-1, 0, 1) for dj in (-1, 0, 1) for _, f in self.cells.get((i + di, j + dj), ())}
        return [(f.z_at(x, y), f) for f in faces.values() if f.contains(x, y)]


def cells_along(ax, ay, bx, by):
    span = math.hypot(bx - ax, by - ay)
    count = max(2, int(span / 4) + 2)
    return {cell_of(ax + (bx - ax) * k / (count - 1), ay + (by - ay) * k / (count - 1)) for k in range(count)}


def cell_of(x, y):
    return math.floor((x - SHIFT) / GRID), math.floor((y - SHIFT) / GRID)


def centre_of(cell):
    return (cell[0] + 0.5) * GRID + SHIFT, (cell[1] + 0.5) * GRID + SHIFT


def segments_cross(ax, ay, bx, by, cx, cy, dx, dy, eps=1e-6):
    rx, ry, sx, sy = bx - ax, by - ay, dx - cx, dy - cy
    denominator = rx * sy - ry * sx
    if abs(denominator) < eps:
        return False
    t = ((cx - ax) * sy - (cy - ay) * sx) / denominator
    u = ((cx - ax) * ry - (cy - ay) * rx) / denominator
    return -eps <= t <= 1 + eps and -0.01 <= u <= 1.01


# --- The floor graph ----------------------------------------------------------------------------------------------
class Graph:
    """A node per floor per cell, joined to the four neighbouring cells' nodes: both ways within MONSTER_STEP (one
    region), down only within MONSTER_DROP (a drop between regions); no wall may stand between them."""
    def __init__(self, level):
        self.level = level
        self.nodes = {}                          # cell -> node ids
        self.z, self.face, self.cell = [], [], []
        for cell, entries in level.cells.items():
            ids = []
            for z, face in sorted(entries, key=lambda e: e[0]):
                if ids and abs(self.z[ids[-1]] - z) < 1:
                    continue
                ids.append(len(self.z))
                self.z.append(z)
                self.face.append(face)
                self.cell.append(cell)
            self.nodes[cell] = ids
        self.parent = list(range(len(self.z)))
        drops = []
        for (i, j), ids in self.nodes.items():
            for other in ((i + 1, j), (i, j + 1)):
                for m in self.nodes.get(other, ()):
                    for n in ids:
                        dz = self.z[m] - self.z[n]
                        if abs(dz) > MONSTER_DROP:
                            continue
                        if (i, j) in level.wall_cells or other in level.wall_cells:
                            if level.blocked(*centre_of((i, j)), *centre_of(other), max(self.z[n], self.z[m]) + BODY):
                                continue
                        if abs(dz) <= MONSTER_STEP:
                            a, b = self.find(n), self.find(m)
                            if a != b:
                                self.parent[a] = b
                        else:
                            drops.append((m, n) if dz > 0 else (n, m))
        # A lift: a mover whose floor lies flush with static floors at both ends of its travel joins them.
        ends = defaultdict(lambda: defaultdict(set))
        for n, face in enumerate(self.face):
            if face.door is not None:
                ends[face.door][face.pose].add(self.find(n))
        static = {self.find(n) for n, face in enumerate(self.face) if face.door is None}
        for poses in ends.values():
            landings = [r for regions in poses.values() for r in regions if r in static]
            if len({p for p, regions in poses.items() if regions & static}) == 2:
                for r in landings[1:]:
                    self.parent[self.find(r)] = self.find(landings[0])
        self.region = [self.find(n) for n in range(len(self.z))]
        self.members = defaultdict(list)
        for n, r in enumerate(self.region):
            self.members[r].append(n)
        self.down = defaultdict(set)
        for a, b in drops:
            if self.region[a] != self.region[b]:
                self.down[self.region[a]].add(self.region[b])

    def find(self, n):
        while self.parent[n] != n:
            self.parent[n] = self.parent[self.parent[n]]
            n = self.parent[n]
        return n

    def node_near(self, x, y, z, tolerance=24):
        """The node nearest (x, y), a cell either way, on a floor within `tolerance` of z."""
        ci, cj = cell_of(x, y)
        best = None
        for i in (ci - 1, ci, ci + 1):
            for j in (cj - 1, cj, cj + 1):
                for n in self.nodes.get((i, j), ()):
                    if abs(self.z[n] - z) > tolerance:
                        continue
                    cx, cy = centre_of((i, j))
                    d = math.hypot(cx - x, cy - y) + abs(self.z[n] - z) / 8
                    if best is None or d < best[0]:
                        best = (d, n)
        return None if best is None else best[1]

    def reachable(self, start, forward=True):
        graph = self.down
        if not forward:
            graph = defaultdict(set)
            for a, targets in self.down.items():
                for b in targets:
                    graph[b].add(a)
        seen, queue = {start}, deque([start])
        while queue:
            for nxt in graph.get(queue.popleft(), ()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    def footprint(self, region, core=CORE):
        """Whether the region holds a monster's footprint: a node whose (2 core + 1)-cell square is all region (core 1:
        room for the party to stand, not the top of a rail)."""
        cells = {self.cell[n] for n in self.members[region]}
        span = range(-core, core + 1)
        return any(all((i + di, j + dj) in cells for di in span for dj in span) for i, j in cells)

    def centre(self, region):
        """A point of the region near its middle (an L or a ring has its mean off the region)."""
        members = self.members[region]
        mx = sum(self.cell[n][0] for n in members) / len(members)
        my = sum(self.cell[n][1] for n in members) / len(members)
        n = min(members, key=lambda m: (self.cell[m][0] - mx) ** 2 + (self.cell[m][1] - my) ** 2)
        x, y = centre_of(self.cell[n])
        return round(x), round(y), round(self.z[n])

    def area(self, region):
        return len(self.members[region]) * GRID * GRID


# --- Edges between floors -----------------------------------------------------------------------------------------
def edge_samples(level, faces):
    """Every 16 units of every floor's boundary: the floor (other than the face itself and its own mover) nearest in
    height found up to REACH outward with no wall between. Yields (face, (x, y, z) just inside, outward unit vector,
    (z, neighbouring face), distance)."""
    for face in faces:
        pts = face.plan
        area = sum(ax * by - bx * ay for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]))
        if abs(area) < 1:
            continue
        sign = 1 if area > 0 else -1
        for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy)
            if length < 8:
                continue
            ox, oy = dy / length * sign, -dx / length * sign
            for s in range(8, int(length), 16):
                sx, sy = ax + dx * s / length, ay + dy * s / length
                ix, iy = sx - ox * 2, sy - oy * 2
                if not face.contains(ix, iy):
                    continue
                iz = face.z_at(ix, iy)
                if face.door is None and level.headroom(ix, iy, iz) < HEAD:
                    continue
                for d in (4, 20, REACH):
                    px, py = sx + ox * d, sy + oy * d
                    candidates = [(z, f) for z, f in level.floors_exact(px, py)
                                  if f is not face and (f.door is None or f.door != face.door)]
                    candidates = [(z, f) for z, f in sorted(candidates, key=lambda c: abs(c[0] - iz))
                                  if not level.blocked(ix, iy, px, py, max(z, iz) + BODY)][:1]
                    if candidates:
                        yield face, (ix, iy, iz), (ox, oy), candidates[0], d
                        break


def climb_within_step(level, x, y, z, out, rise):
    """The floor height one 40-unit path step past a riser's foot, when it climbs further than a step allows."""
    px, py = x + out[0] * MONSTER_STEP, y + out[1] * MONSTER_STEP
    heights = [zz for zz, f in level.floors_exact(px, py) if z + rise - 1 <= zz <= z + WALL]
    if heights and min(heights) - z > MONSTER_STEP:
        return min(heights)
    return None


def runs(samples):
    """Group samples (key, x, y) into runs of samples with the same key no more than 40 apart."""
    groups = defaultdict(list)
    for key, x, y in samples:
        groups[key].append((x, y))
    result = []
    for key, items in groups.items():
        pending = sorted(items)
        while pending:
            run, frontier = [], [pending.pop(0)]
            while frontier:
                item = frontier.pop()
                run.append(item)
                near = [p for p in pending if abs(p[0] - item[0]) <= 40 and abs(p[1] - item[1]) <= 40]
                for p in near:
                    pending.remove(p)
                frontier += near
            result.append((key, run))
    return result


# --- The audit ----------------------------------------------------------------------------------------------------
def analyse(level, allow=()):
    """The level's findings: dicts with a kind, a place (`at`), the numbers and a text; a finding an allow entry
    ({'kind', 'at', 'reason'}) names carries 'allowed'. Returns (findings, graph)."""
    graph = Graph(level)
    findings = []
    sx, sy, sz = level.start
    start = graph.node_near(sx, sy, sz, tolerance=48)
    if start is None:
        return [dict(kind='start', at=[round(sx), round(sy), round(sz)], text='the party start is on no floor')], graph
    main = graph.region[start]
    actors_in = defaultdict(list)
    for actor in level.actors:
        n = graph.node_near(actor['x'], actor['y'], actor['z'])
        if n is not None and not actor.get('flies') and not actor.get('immobile'):
            actors_in[graph.region[n]].append(actor['index'])
    to_start = graph.reachable(main, forward=False)
    from_main, open_ground, cut_off = set(), set(), []
    # Open floor: the start's region and every region placed monsters stand on, with where they walk and come back.
    for anchor in [main] + sorted(actors_in, key=graph.area, reverse=True):
        if anchor in open_ground:
            continue
        if anchor not in to_start and graph.footprint(anchor):
            cut_off.append(anchor)
        reach = graph.reachable(anchor)
        from_main |= reach
        open_ground |= reach & graph.reachable(anchor, forward=False)

    step_samples, flight_samples, borders = [], [], defaultdict(list)
    for face, (x, y, z), out, (nz, other), d in edge_samples(level, unique_static_floors(level)):
        rise = nz - z
        if abs(rise) <= 1:
            continue
        a = graph.node_near(x, y, z)
        b = graph.node_near(x + out[0] * d, y + out[1] * d, nz)
        if a is None or b is None:
            continue
        ra, rb = graph.region[a], graph.region[b]
        if ra != rb:
            borders[(ra, rb)].append(rise)
        lower, upper = (ra, rb) if rise > 0 else (rb, ra)
        if (STEP_OK < abs(rise) < WALL and other.door is None and lower in from_main
                and (upper in from_main or abs(rise) <= PARTY_STEP and graph.footprint(upper, core=1))):
            low, high = sorted((z, nz))
            step_samples.append(((round(low), round(high), face.sector), x, y))
        if 0 < rise <= MONSTER_STEP and ra in from_main:
            top = climb_within_step(level, x, y, z, out, rise)
            if top is not None:
                n = graph.node_near(x + out[0] * MONSTER_STEP, y + out[1] * MONSTER_STEP, top, tolerance=4)
                if n is None or not graph.footprint(graph.region[n], core=1):
                    continue
                flight_samples.append(((round(z), round(top), face.sector), x, y))
    for (low, high, sector), run in runs(step_samples):
        x, y = round(np.mean([r[0] for r in run])), round(np.mean([r[1] for r in run]))
        findings.append(dict(kind='step', at=[x, y, low], rise=high - low, length=len(run) * 8, room=level.room(sector),
                             text=f'{level.room(sector)} ({x}, {y}): a {high - low} edge ({low} to {high}), '
                                  f'{len(run) * 8} long'))
    for (low, high, sector), run in runs(flight_samples):
        x, y = round(np.mean([r[0] for r in run])), round(np.mean([r[1] for r in run]))
        findings.append(dict(kind='flight', at=[x, y, low], rise=high - low, length=len(run) * 16,
                             room=level.room(sector),
                             text=f'{level.room(sector)} ({x}, {y}): climbs {high - low} within one 40-unit path '
                                  f'step from {low}, {len(run) * 16} wide'))

    for region in cut_off:
        x, y, z = graph.centre(region)
        room = level.room(graph.face[graph.members[region][0]].sector)
        findings.append(dict(kind='unreachable', at=[x, y, z], area=graph.area(region), region=region, room=room,
                             rise=None, actors=actors_in[region],
                             text=f'{room} ({x}, {y}, {z}): {graph.area(region) / 1e6:.2f}M units² whose monsters '
                                  f'{actors_in[region]} cannot walk to the party start'))
    reported = set(cut_off)
    for (ra, rb), rises in sorted(borders.items()):
        # Seen from ra: rb lies `rise` higher. The region off the open ground is the one at fault.
        for region, ground, rise_to_ground in ((ra, rb, max(rises)), (rb, ra, -min(rises))):
            if region in open_ground or ground not in open_ground or region in reported:
                continue
            if region not in from_main and STEP_OK < -rise_to_ground < WALL:
                kind = 'unreachable'      # a platform above the open ground that monsters cannot climb onto
            elif rise_to_ground > 0 and (region in from_main or STEP_OK < rise_to_ground < WALL):
                kind = 'pit'              # monsters walk or drop in, or are pushed in, and cannot climb out
            else:
                continue
            if not graph.footprint(region):
                continue
            reported.add(region)
            x, y, z = graph.centre(region)
            exits = [r for (a, b), rs in borders.items() if a == region and b in open_ground for r in rs]
            room = level.room(graph.face[graph.members[region][0]].sector)
            finding = dict(kind=kind, at=[x, y, z], area=graph.area(region), region=region, room=room,
                           actors=actors_in.get(region, []))
            if kind == 'pit':
                finding['exit_rise'] = round(min((r for r in exits if r > 0), default=0))
                finding['text'] = (f'{room} ({x}, {y}, {z}): {finding["area"] / 1e6:.2f}M units² that monsters '
                                   f'cannot leave (the lowest way out rises {finding["exit_rise"]})')
            else:
                finding['rise'] = round(min((-r for r in exits if r < 0), default=0))
                finding['text'] = (f'{room} ({x}, {y}, {z}): {finding["area"] / 1e6:.2f}M units² {finding["rise"]} '
                                   'above the open floor with no way up for monsters')
            if finding['actors']:
                finding['text'] += f'; actors {finding["actors"]} stand on it'
            findings.append(finding)

    findings += mover_findings(level)
    findings += actor_findings(level)
    for finding in findings:
        for entry in allow:
            if entry['kind'] == finding['kind'] and 'region' in finding:
                n = graph.node_near(*entry['at'], tolerance=32)
                if n is not None and graph.region[n] == finding['region']:
                    finding['allowed'] = entry['reason']
                    entry['used'] = True
    return findings, graph


def unique_static_floors(level):
    seen, floors = set(), []
    for entries in level.surfaces.values():
        for _, kind, face in entries:
            if kind == 'floor' and id(face) not in seen:
                seen.add(id(face))
                floors.append(face)
    return floors


def mover_findings(level):
    """Each mover's floors at each end of its travel against the static floors around them."""
    findings = []
    for door, poses in level.movers.items():
        for pose, faces in zip(('open', 'closed'), poses):
            worst = {}
            floors = [f for f in faces if f.kind == 'floor']
            for face, (x, y, z), out, (nz, other), d in edge_samples(level, floors):
                px, py = x + out[0] * (d + 2), y + out[1] * (d + 2)
                # Internal triangle edges still have the mover underfoot, even over lower static treads.
                if any(f.contains(px, py) and abs(f.z_at(px, py) - face.z_at(px, py)) < 1 for f in floors):
                    continue
                rise = nz - z
                if other.door is not None:
                    continue
                kind = 'recess' if 1 < rise < WALL else 'lip' if STEP_OK < -rise < WALL else None
                if kind and (kind not in worst or abs(rise) > abs(worst[kind][0])):
                    worst[kind] = (rise, x, y, z, face.sector)
            for kind, (rise, x, y, z, sector) in worst.items():
                depth = round(abs(rise))
                findings.append(dict(kind='mover', door=door, pose=pose, at=[round(x), round(y), round(z)],
                                     rise=depth, room=level.room(sector),
                                     text=f'door {door} {pose}: its top at ({round(x)}, {round(y)}, {round(z)}) is a '
                                          f'{depth} {kind}, {"below" if kind == "recess" else "above"} the floor '
                                          'around it'))
    return findings


def actor_findings(level):
    findings = []
    for actor in level.actors:
        x, y, z, r, h = (actor[k] for k in ('x', 'y', 'z', 'radius', 'height'))
        label = f'actor #{actor["index"]} {actor["name"]!r} ({round(x)}, {round(y)}, {round(z)})'
        floors = [fz for fz, f in level.floors_at(x, y) if -24 <= z - fz <= 8]
        problem = None
        if actor.get('flies'):
            fz = z
            for k in range(8):
                px, py = x + r * math.cos(k * math.pi / 4), y + r * math.sin(k * math.pi / 4)
                if any(level.blocked(x, y, px, py, z + above) for above in (8, h / 2, h - 8)):
                    problem = f'has a wall within its radius {r} (toward ({round(px)}, {round(py)}))'
                    break
        elif not floors:
            below = max((fz for fz, f in level.floors_at(x, y) if fz <= z + 8), default=None)
            problem = 'stands on no floor' + (f' (the floor below is at {round(below)})' if below is not None else '')
        else:
            fz = max(floors)
            for k in range(12):
                reach, angle = (r, k * math.pi / 4) if k < 8 else (r / 2, (k - 8) * math.pi / 2 + math.pi / 4)
                px, py = x + reach * math.cos(angle), y + reach * math.sin(angle)
                if not any(abs(zz - fz) <= 2 * STEP_OK for zz, f in level.floors_at(px, py)):
                    problem = f'overhangs an edge within its radius {r} (at ({round(px)}, {round(py)}))'
                    break
                if any(level.blocked(x, y, px, py, fz + above) for above in (STEP_OK + 8, h / 2, h - 8)):
                    problem = f'has a wall within its radius {r} (toward ({round(px)}, {round(py)}))'
                    break
        if problem is None and level.headroom(x, y, fz) < h:
            problem = f'stands under a ceiling {round(level.headroom(x, y, fz))} above it, lower than its height {h}'
        if problem:
            findings.append(dict(kind='actor', at=[round(x), round(y), round(z)], actor=actor['index'],
                                 text=f'{label} {problem}'))
    return findings


# --- Loading ------------------------------------------------------------------------------------------------------
def load(blv_path):
    """A built map as a Level: its BLV faces, its scene's doors (as movers), party start and actors, and the sector
    names from its project's semantic record."""
    sys.path.insert(0, str(ROOT / 'util'))
    from map_export import parse_blv_file
    payload = parse_blv_file(Path(blv_path))['payload']
    scene = json.loads(Path(blv_path).with_suffix('.scene.yml').read_text())
    vertices = np.array([[v['x'], v['y'], v['z']] for v in payload['vertices']], float)
    doors = scene['initial_state'].get('doors', [])
    moving = {fid for d in doors for fid in d['face_ids']}

    def make(record, points, door=None, pose=0):
        if record['is_portal'] or len(record['vertex_indices']) < 3 or record['attributes'] & UNTOUCHABLE:
            return None
        face = Face(points, sector=record['room_number'], door=door, pose=pose)
        return face if np.linalg.norm(face.hi - face.lo) > 0.5 else None
    faces = [f for r in payload['faces'] if r['index'] not in moving
             and (f := make(r, vertices[r['vertex_indices']])) is not None]
    by_index = {r['index']: r for r in payload['faces']}
    movers = {}
    for d in doors:
        direction = np.array(d['direction'], float) / 65536
        poses = []
        for pose, distance in enumerate((0, d['move_length'])):
            moved = vertices.copy()
            for vid, x, y, z in zip(d['vertex_ids'], d['x_offsets'], d['y_offsets'], d['z_offsets']):
                moved[vid] = np.array([x, y, z]) + direction * distance
            poses.append([f for fid in d['face_ids']
                          if (f := make(by_index[fid], moved[by_index[fid]['vertex_indices']], d['door_id'], pose))])
        movers[d['door_id']] = poses
    start = scene['party_start_points'][0]['position']
    flying = flyers()
    actors = [dict(index=a['actor_index'], name=a['name'], x=a['position']['x'], y=a['position']['y'],
                   z=a['position']['z'], radius=a['radius'], height=a['height'],
                   flies=a['monster_info_id'] in flying, immobile=bool(a.get('immobile')))
              for a in scene['initial_state'].get('actors', [])]
    stem = Path(blv_path).stem
    semantic = ROOT / f'level_generation/projects/{stem.replace("hes_", "hesper_")}/source/{stem}.semantic.json'
    rooms = {}
    if semantic.exists():
        rooms = {i + 1: s.removeprefix('room_') for i, s in enumerate(sorted(json.loads(semantic.read_text())['sectors']))}
    return Level(stem, faces, start, actors, movers, rooms)


def flyers():
    """The monster ids whose Fly column says Y (the hesper world's table first, then the engine's)."""
    flying, seen = set(), set()
    for table in MONSTER_TABLES:
        if not table.exists():
            continue
        for line in table.read_text(encoding='utf-8', errors='replace').splitlines():
            fields = line.split('\t')
            if len(fields) > 9 and fields[0].strip().isdigit() and int(fields[0]) not in seen:
                seen.add(int(fields[0]))
                if fields[9].strip().upper().startswith('Y'):
                    flying.add(int(fields[0]))
    return flying


def audit_map(path, allow):
    level = load(path)
    entries = [dict(e) for e in allow.get(level.name, [])]
    findings, _ = analyse(level, entries)
    return level.name, findings, entries


def audit(maps, gate, json_path=None, workers=8):
    import yaml
    allow = (yaml.safe_load(ALLOW.read_text()) if ALLOW.exists() else None) or {}
    jobs = [(path, allow) for path in maps]
    if workers <= 1:                      # OPENYAMM_WALKABILITY_WORKERS=1: sandboxes that refuse multiprocessing
        results = [audit_map(*job) for job in jobs]
    else:
        from multiprocessing import Pool
        with Pool(min(workers, len(maps))) as pool:
            results = pool.starmap(audit_map, jobs)
    failed = False
    report, totals = {}, defaultdict(int)
    for name, findings, entries in results:
        live = [f for f in findings if 'allowed' not in f]
        counts, bands = defaultdict(int), defaultdict(int)
        for f in live:
            counts[f['kind']] += 1
            totals[f['kind']] += 1
            if f['kind'] == 'step':
                bands['33-40' if f['rise'] <= 40 else '41-64' if f['rise'] <= 64 else '65-127'] += 1
        allowed = len(findings) - len(live)
        print(f'{name}: ' + ', '.join(f'{k}={counts[k]}' for k in KINDS)
              + (f' (steps {", ".join(f"{k}: {v}" for k, v in sorted(bands.items()))})' if bands else '')
              + (f', allowed={allowed}' if allowed else ''))
        for f in sorted(findings, key=lambda f: (KINDS.index(f['kind']) if f['kind'] in KINDS else -1, f['at'])):
            print(f'  {"allowed " if "allowed" in f else ""}{f["kind"].upper()} {f["text"]}'
                  + (f': {f["allowed"]}' if 'allowed' in f else ''))
        for e in entries:
            if not e.get('used'):
                print(f'  STALE ALLOW {e["kind"]} at {e["at"]}: no such finding ({e["reason"]})')
        failed |= bool(live) and (gate is None or name in gate)
        report[name] = dict(counts=dict(counts), step_bands=dict(bands), allowed=allowed,
                            findings=[{k: v for k, v in f.items() if k != 'region'} for f in findings])
    print(f'TOTAL: maps={len(maps)}, ' + ', '.join(f'{k}={totals[k]}' for k in KINDS))
    if json_path:
        Path(json_path).write_text(json.dumps(report, indent=1) + '\n')
    return int(failed)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('maps', nargs='*', help='map names (hes_d08); default: every built BLV')
    parser.add_argument('--gate', help='comma-separated maps whose findings fail the audit (default: every map)')
    parser.add_argument('--json', help='also write the findings to this JSON file')
    args = parser.parse_args()
    folder = ASSETS / 'worlds/hesper/maps'
    with (STAGE / 'locks/stage.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        maps = [folder / f'{m}.blv' for m in args.maps] or sorted(folder.glob('*.blv'))
        if not maps:
            raise ValueError('no built Hesper BLVs in the stage')
        gate = None if args.gate is None else set(filter(None, args.gate.split(',')))
        return audit(maps, gate, args.json, int(os.environ.get('OPENYAMM_WALKABILITY_WORKERS', '8')))


if __name__ == '__main__':
    raise SystemExit(main())
