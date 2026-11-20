"""The Hesper indoor (BLV) authoring kit, for Blender: faces with planar or fitted UVs, walls (on axis or any vertical
plane) with holes, recessed doors, plaques, boxes, bars, stair flights and ramps (along any direction, and concentric
tiers), polygon rooms (chamfered, n-gons, concave footprints in convex pieces), sloped ceilings (hipped, vaulted),
rooms with thick-wall reveals, portals, triggers, doors (linear movers), decorations, lights and spawns, written as the GLB and geometry metadata the indoor compiler reads
(mm9_compile_indoor_source; level_generation/projects/hesper_d00 is the first map built this way).

    import blv_kit
    b = blv_kit.Builder('hes_d01.blv', ROLE, OUTPUT)
    b.room('hall', bounds, ambient)
    b.rooms['hall'] += blv_kit.floor(...)
    ...
    b.export()

Rules it follows (design/kreegan_world/DUNGEON_PLAYBOOK.md): one texel per world unit unless a role is scaled;
rooms never share a wall plane (the indoor renderer draws both sides of a face, so two faces in one plane z-fight):
neighbours stand THICK apart and an opening's reveal belongs to one of them; a step is at most 32 (the party climbs
50), and the new flights and ramps refuse what monsters cannot climb: their path planner steps 40 and climbs at most
40 per step (check_walkability.py audits the built maps). Run inside Blender's Python.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'design/kreegan_world/art'
FOLDERS = [ART / 'textures_d0/blv', ART / 'textures_interiors/masters', ART / 'textures_out1/masters']
SCALE = 128
THICK = 64
MONSTER_STEP = 40          # a monster's path step: 40 along, at most 40 up
MAX_SLOPE = 45             # degrees: the steepest walkable floor (MaximumUphillSlopeNormalZ)


def texture_path(key):
    for folder in FOLDERS:
        if (folder / f'{key}.png').exists():
            return folder / f'{key}.png'
    raise FileNotFoundError(key)


class Fit:
    """A fitted texture: the picture spans one rectangle of a plane (origin, right and up in world units), so the
    pieces of a face cut round a door share it."""
    def __init__(self, origin, right, up, width, height):
        self.origin, self.right, self.up = Vector(origin), Vector(right), Vector(up)
        self.width, self.height = width, height


class Wall:
    """A vertical wall plane: x = plane (axis 'x') or y = plane (axis 'y'), facing `inward` into its room, or any
    vertical plane (`Wall.line`). Points are (along, z); `right` is the direction a viewer facing the wall sees as
    right."""
    def __init__(self, axis, plane, inward):
        self.axis, self.plane, self.inward = axis, plane, inward
        self.right = (-Vector(inward)).cross(Vector((0, 0, 1)))

    @classmethod
    def line(cls, start, end, inward=None):
        """A wall on the vertical plane through plan points `start` and `end`; `along` is the distance from `start`
        toward `end` (0 to `length`). It faces the left of start -> end (so a counter-clockwise footprint's walls face
        into the room) unless `inward` points the other way."""
        wall = cls.__new__(cls)
        x0, y0, x1, y1 = start[0], start[1], end[0], end[1]
        wall.length = math.hypot(x1 - x0, y1 - y0)
        wall.axis, wall.plane = 'line', None
        wall.origin = Vector((x0, y0, 0))
        wall.direction = Vector(((x1 - x0) / wall.length, (y1 - y0) / wall.length, 0))
        left = Vector((-wall.direction.y, wall.direction.x, 0))
        if inward is not None and left.dot(Vector(inward)) < 0:
            left = -left
        wall.inward = tuple(left)
        wall.right = (-left).cross(Vector((0, 0, 1)))
        return wall

    def axis_vector(self):
        if self.axis == 'line':
            return self.direction.copy()
        return Vector((0, 1, 0)) if self.axis == 'x' else Vector((1, 0, 0))

    def point(self, along, z, out=0.0):
        n = Vector(self.inward)
        if self.axis == 'line':
            return self.origin + self.direction * along + Vector((0, 0, z)) + n * out
        if self.axis == 'x':
            return Vector((self.plane, along, z)) + n * out
        return Vector((along, self.plane, z)) + n * out

    def offset(self, depth):
        """The parallel wall `depth` behind this one (away from its room), facing the same way, `along` unchanged."""
        if self.axis == 'line':
            back = self.origin - Vector(self.inward) * depth
            return Wall.line(back, back + self.direction * self.length, self.inward)
        return Wall(self.axis, self.plane - self.inward[0 if self.axis == 'x' else 1] * depth, self.inward)

    def quad(self, a0, a1, z0, z1, role, fit=None, out=0.0):
        if a1 - a0 < 0.5 or z1 - z0 < 0.5:
            return []
        coords = [self.point(a0, z0, out), self.point(a1, z0, out), self.point(a1, z1, out), self.point(a0, z1, out)]
        return [(coords, role, self.inward, fit)] if fit else [(coords, role, self.inward)]

    def fit(self, a0, a1, z0, z1, out=0.0):
        left = a0 if self.right.dot(self.axis_vector()) > 0 else a1
        return Fit(self.point(left, z0, out), self.right, (0, 0, 1), abs(a1 - a0), z1 - z0)


def rect_minus(a0, a1, z0, z1, holes):
    """The rectangle minus holes (a0, a1, z0, z1), as rectangles."""
    cuts = sorted({a0, a1} | {v for h in holes for v in (h[0], h[1]) if a0 < v < a1})
    pieces = []
    for s0, s1 in zip(cuts, cuts[1:]):
        covering = sorted((max(z0, h[2]), min(z1, h[3])) for h in holes
                          if h[0] < s1 - 0.1 and h[1] > s0 + 0.1 and h[2] < z1 and h[3] > z0)
        z = z0
        for c0, c1 in covering:
            if c0 > z:
                pieces.append((s0, s1, z, c0))
            z = max(z, c1)
        if z < z1:
            pieces.append((s0, s1, z, z1))
    return pieces


def banded(wall, a0, a1, bands, holes):
    """A wall in horizontal bands (z0, z1, role), minus holes."""
    panels = []
    for z0, z1, role in bands:
        for p in rect_minus(a0, a1, z0, z1, holes):
            panels += wall.quad(*p, role)
    return panels


def stretch(bands, height, thin=96):
    """Wall bands (z0, z1, role) drawn for one height, refitted to another: thin bands (trims, strips, hazard edges)
    keep their thickness and stay against the floor or ceiling they sat on, the wide ones share what is left."""
    total = bands[-1][1]
    if total == height:
        return bands
    wide = sum(z1 - z0 for z0, z1, _ in bands if z1 - z0 > thin)
    if wide == 0:
        raise ValueError(f'bands {bands} have no wide band to stretch to {height}')
    scale = (wide + height - total) / wide
    out, z = [], 0
    for z0, z1, role in bands:
        size = z1 - z0 if z1 - z0 <= thin else (z1 - z0) * scale
        out.append((round(z), round(z + size), role))
        z += size
    out[-1] = (out[-1][0], height, out[-1][2])
    return out


def floor(x0, y0, x1, y1, z, role):
    return [([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], role, (0, 0, 1))]


def ceiling(x0, y0, x1, y1, z, role):
    return [([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], role, (0, 0, -1))]


def prism(cx, cy, radius, z0, z1, side, top=None, bottom=None, sides=8, turn=math.pi / 8):
    """A vertical regular prism (a pump drum, a round pillar, a standing pipe), its sides facing out; top and bottom
    caps when given. turn: the first corner's angle (pi / sides puts a flat side to each axis)."""
    corners = [(cx + radius * math.cos(turn + k * 2 * math.pi / sides),
                cy + radius * math.sin(turn + k * 2 * math.pi / sides)) for k in range(sides)]
    panels = []
    for k in range(sides):
        (ax, ay), (bx, by) = corners[k], corners[(k + 1) % sides]
        mx, my = (ax + bx) / 2 - cx, (ay + by) / 2 - cy
        length = math.hypot(mx, my)
        panels.append(([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)], side, (mx / length, my / length, 0)))
    if top:
        panels.append(([(x, y, z1) for x, y in corners], top, (0, 0, 1)))
    if bottom:
        panels.append(([(x, y, z0) for x, y in reversed(corners)], bottom, (0, 0, -1)))
    return panels


def pipe(p0, p1, radius, role, sides=8, caps=()):
    """A straight horizontal pipe along x or y from p0 to p1 (same y or x, same z), its sides facing out; caps: the
    ends to close ('start', 'end'), leaving open the ones that meet a wall or another pipe."""
    (x0, y0, z), (x1, y1, _) = p0, p1
    along_x = abs(x1 - x0) >= abs(y1 - y0)
    panels = []
    ring = [(radius * math.cos(math.pi / sides + k * 2 * math.pi / sides),
             radius * math.sin(math.pi / sides + k * 2 * math.pi / sides)) for k in range(sides)]

    def point(end, u, v):
        x, y = end[0], end[1]
        return (x, y + u, z + v) if along_x else (x + u, y, z + v)
    for k in range(sides):
        (au, av), (bu, bv) = ring[k], ring[(k + 1) % sides]
        mu, mv = (au + bu) / 2, (av + bv) / 2
        length = math.hypot(mu, mv)
        normal = (0, mu / length, mv / length) if along_x else (mu / length, 0, mv / length)
        panels.append(([point(p0, au, av), point(p0, bu, bv), point(p1, bu, bv), point(p1, au, av)], role, normal))
    for end, name in ((p0, 'start'), (p1, 'end')):
        if name in caps:
            sign = (-1 if end is p0 else 1) * (1 if (x1 - x0 if along_x else y1 - y0) > 0 else -1)
            panels.append(([point(end, u, v) for u, v in ring], role, (sign, 0, 0) if along_x else (0, sign, 0)))
    return panels


def box(lo, hi, side, top=None, bottom=None, skip=()):
    """An axis box: sides `side`, top and bottom when given; `skip` names faces left out (south, north, west, east)."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    faces = {'south': ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
             'north': ([(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)], (0, 1, 0)),
             'west': ([(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], (-1, 0, 0)),
             'east': ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0))}
    panels = [(coords, side, n) for name, (coords, n) in faces.items() if name not in skip]
    if top:
        panels.append(([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top, (0, 0, 1)))
    if bottom:
        panels.append(([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], bottom, (0, 0, -1)))
    return panels


def beam(p0, p1, width, role):
    """A square bar between two points, open at its ends (they sit on a wall, a floor or a joint)."""
    a, b = Vector(p0), Vector(p1)
    axis = (b - a).normalized()
    u = axis.cross(Vector((0, 0, 1)) if abs(axis.z) < 0.9 else Vector((1, 0, 0))).normalized() * (width / 2)
    v = axis.cross(u).normalized() * (width / 2)
    corners = [u + v, -u + v, -u - v, u - v]
    panels = []
    for k in range(4):
        c0, c1 = corners[k], corners[(k + 1) % 4]
        panels.append(([a + c0, a + c1, b + c1, b + c0], role, tuple((c0 + c1).normalized())))
    return panels


def recessed_door(wall, a, z0, width, height, role, depth=16.0, trim='trim'):
    """The door face `depth` behind the wall plane at a (its centre), with jambs and a lintel; returns (door face,
    jambs). The door face is fitted to its texture."""
    a0, a1 = a - width / 2, a + width / 2
    door = wall.offset(depth)
    face = door.quad(a0, a1, z0, z0 + height, role, fit=door.fit(a0, a1, z0, z0 + height))
    jambs = []
    back = Vector(wall.inward) * -depth
    for edge, facing in ((a0, 1), (a1, -1)):
        p0, p1 = wall.point(edge, z0), wall.point(edge, z0 + height)
        jambs.append(([p0, p0 + back, p1 + back, p1], trim, tuple(wall.axis_vector() * facing)))
    top = [wall.point(a0, z0 + height), wall.point(a1, z0 + height), wall.point(a1, z0 + height) + back,
           wall.point(a0, z0 + height) + back]
    jambs.append((top, trim, (0, 0, -1)))
    return face, jambs


def plaque(wall, a, z0, width, height, role, out=8.0, edge='trim'):
    """A face on a little box standing `out` from the wall, fitted to its texture (signs, consoles, panels)."""
    a0, a1 = a - width / 2, a + width / 2
    panels = wall.quad(a0, a1, z0, z0 + height, role, fit=wall.fit(a0, a1, z0, z0 + height, out), out=out)
    for e, facing in ((a0, -1), (a1, 1)):
        p0, p1 = wall.point(e, z0), wall.point(e, z0 + height)
        n = Vector(wall.inward) * out
        panels.append(([p0, p0 + n, p1 + n, p1], edge, tuple(wall.axis_vector() * facing)))
    for z, facing in ((z0, -1), (z0 + height, 1)):
        q = [wall.point(a0, z), wall.point(a1, z), wall.point(a1, z, out), wall.point(a0, z, out)]
        panels.append((q, edge, (0, 0, facing)))
    return panels


def flight(x0, y0, x1, y1, z0, steps, direction, tread='floor', riser='trim', rise=32.0):
    """A stair flight filling the rectangle, `steps` steps of `rise`, climbing toward `direction` ('north', 'south',
    'east' or 'west'): treads and risers only (the room supplies its walls)."""
    panels = []
    along_y = direction in ('north', 'south')
    length = (y1 - y0) if along_y else (x1 - x0)
    run = length / steps
    for k in range(steps):
        z = z0 + rise * (k + 1)
        if direction == 'north':
            a, b = y0 + run * k, y0 + run * (k + 1)
            panels += floor(x0, a, x1, b, z, tread)
            panels.append(([(x0, a, z - rise), (x1, a, z - rise), (x1, a, z), (x0, a, z)], riser, (0, -1, 0)))
        elif direction == 'south':
            a, b = y1 - run * (k + 1), y1 - run * k
            panels += floor(x0, a, x1, b, z, tread)
            panels.append(([(x0, b, z - rise), (x1, b, z - rise), (x1, b, z), (x0, b, z)], riser, (0, 1, 0)))
        elif direction == 'east':
            a, b = x0 + run * k, x0 + run * (k + 1)
            panels += floor(a, y0, b, y1, z, tread)
            panels.append(([(a, y0, z - rise), (a, y1, z - rise), (a, y1, z), (a, y0, z)], riser, (-1, 0, 0)))
        else:
            a, b = x1 - run * (k + 1), x1 - run * k
            panels += floor(a, y0, b, y1, z, tread)
            panels.append(([(b, y0, z - rise), (b, y1, z - rise), (b, y1, z), (b, y0, z)], riser, (1, 0, 0)))
    return panels


def ring_walls(cx, cy, radius, sides, z0, z1, bands, holes=(), phase=0.0):
    """The walls of a regular polygon room facing inward, in bands; `holes` are (side index, z0, z1) openings that
    take a whole side. Returns (panels, corner points)."""
    corners = [(cx + radius * math.cos(phase + 2 * math.pi * k / sides),
                cy + radius * math.sin(phase + 2 * math.pi * k / sides)) for k in range(sides)]
    panels = []
    for k in range(sides):
        (ax, ay), (bx, by) = corners[k], corners[(k + 1) % sides]
        inward = (cx - (ax + bx) / 2, cy - (ay + by) / 2, 0)
        cut = [h for h in holes if h[0] == k]
        for b0, b1, role in bands:
            ranges = [(b0, b1)]
            for _, h0, h1 in cut:
                ranges = [r for r0, r1 in ranges for r in ((r0, min(r1, h0)), (max(r0, h1), r1)) if r[1] - r[0] > 0.5]
            for r0, r1 in ranges:
                panels.append(([(ax, ay, z0 + r0), (bx, by, z0 + r0), (bx, by, z0 + r1), (ax, ay, z0 + r1)], role,
                               inward))
    return panels, corners


def monster_safe(rise, run):
    """Whether monsters' path steps (MONSTER_STEP along, at most MONSTER_STEP up) climb a flight of `rise` risers on
    `run`-deep treads: one step may cross ceil(40 / run) risers."""
    return rise * math.ceil(MONSTER_STEP / run - 1e-9) <= MONSTER_STEP


def _ccw(points):
    return sum(ax * by - bx * ay for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1])) > 0


def chamfer_rect(x0, y0, x1, y1, cut):
    """A rectangle's footprint with its corners cut at 45 degrees, counter-clockwise from the south-west; `cut` is
    one length or {'sw', 'se', 'ne', 'nw'} (a missing corner stays square)."""
    cuts = cut if isinstance(cut, dict) else dict(sw=cut, se=cut, ne=cut, nw=cut)
    points = []
    for (cx, cy), name, (ax, ay), (bx, by) in (((x0, y0), 'sw', (0, 1), (1, 0)), ((x1, y0), 'se', (-1, 0), (0, 1)),
                                               ((x1, y1), 'ne', (0, -1), (-1, 0)), ((x0, y1), 'nw', (1, 0), (0, -1))):
        c = cuts.get(name, 0)
        points += [(cx + ax * c, cy + ay * c), (cx + bx * c, cy + by * c)] if c else [(cx, cy)]
    return points


def ngon(cx, cy, radius, sides, phase=None):
    """A regular polygon's footprint, counter-clockwise; `radius` reaches its corners (the flat sides stand at
    radius * cos(pi / sides)). The default phase puts a flat side facing each axis when sides is a multiple of 4."""
    phase = math.pi / sides if phase is None else phase
    return [(cx + radius * math.cos(phase + 2 * math.pi * k / sides), cy + radius * math.sin(phase + 2 * math.pi * k / sides))
            for k in range(sides)]


def convex_pieces(points):
    """A simple polygon (plan points, either winding) as convex pieces, counter-clockwise: ear-clipped triangles
    merged back across their diagonals while the result stays convex (Hertel-Mehlhorn)."""
    points = [tuple(p) for p in points]
    if not _ccw(points):
        points.reverse()

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def convex(poly):
        n = len(poly)
        return all(cross(poly[k], poly[(k + 1) % n], poly[(k + 2) % n]) >= -1e-6 for k in range(n))
    if convex(points):
        return [points]
    index, triangles = list(range(len(points))), []
    while len(index) > 3:
        for k in range(len(index)):
            a, b, c = index[k - 1], index[k], index[(k + 1) % len(index)]
            if cross(points[a], points[b], points[c]) <= 1e-9:
                continue
            if any(cross(points[a], points[b], points[q]) >= 0 and cross(points[b], points[c], points[q]) >= 0
                   and cross(points[c], points[a], points[q]) >= 0 for q in index if q not in (a, b, c)):
                continue
            triangles.append([a, b, c])
            index.pop(k)
            break
        else:
            raise ValueError(f'cannot split polygon {points}')
    triangles.append(index)
    pieces = [list(t) for t in triangles]
    merged = True
    while merged:
        merged = False
        for i in range(len(pieces)):
            for j in range(i + 1, len(pieces)):
                a, b = pieces[i], pieces[j]
                for k in range(len(a)):
                    u, v = a[k], a[(k + 1) % len(a)]
                    if v in b and b[(b.index(v) + 1) % len(b)] == u:
                        # a from v round to u, then b's vertices strictly between u and v.
                        joined = a[k + 1:] + a[:k + 1] + (b[b.index(u):] + b[:b.index(u)])[1:-1]
                        if convex([points[q] for q in joined]):
                            pieces[i] = joined
                            pieces.pop(j)
                            merged = True
                        break
                if merged:
                    break
            if merged:
                break
    return [[points[q] for q in piece] for piece in pieces]


def polygon_floor(points, z, role):
    """A floor over any simple footprint, in convex pieces."""
    return [([(x, y, z) for x, y in piece], role, (0, 0, 1)) for piece in convex_pieces(points)]


def polygon_ceiling(points, z, role):
    return [([(x, y, z) for x, y in piece], role, (0, 0, -1)) for piece in convex_pieces(points)]


def _down(coords):
    """The normal of a planar polygon, turned to face down (a ceiling's face)."""
    a, b, c = (Vector(p) for p in coords[:3])
    n = (b - a).cross(c - a).normalized()
    return tuple(-n if n.z > 0 else n)


def hip_ceiling(points, z0, z1, role, top=0.5):
    """A hipped (tray) ceiling over a convex footprint: from every edge at z0 a slope up to the footprint scaled by
    `top` about its centre at z1, and that flat top; top=0 makes a pyramid (an n-gon's makes a faceted dome)."""
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    inner = [(cx + (x - cx) * top, cy + (y - cy) * top) for x, y in points]
    panels = []
    for k in range(len(points)):
        (ax, ay), (bx, by) = points[k], points[(k + 1) % len(points)]
        (qx, qy), (rx, ry) = inner[k], inner[(k + 1) % len(points)]
        coords = [(ax, ay, z0), (bx, by, z0), (rx, ry, z1), (qx, qy, z1)] if top else \
            [(ax, ay, z0), (bx, by, z0), (cx, cy, z1)]
        panels.append((coords, role, _down(coords)))
    if top:
        panels.append(([(x, y, z1) for x, y in inner], role, (0, 0, -1)))
    return panels


def vault(x0, y0, x1, y1, z, rise, axis, role, segments=8, ends=None):
    """A barrel vault over a rectangle springing at z, `rise` high at its crown, running along `axis` ('x' or 'y');
    `ends` closes its two end arches (lunettes) with that role."""
    a0, a1 = (y0, y1) if axis == 'x' else (x0, x1)
    centre, half = (a0 + a1) / 2, (a1 - a0) / 2
    arc = [(centre - half * math.cos(math.pi * k / segments), z + rise * math.sin(math.pi * k / segments))
           for k in range(segments + 1)]

    def at(along, across, height):
        return (along, across, height) if axis == 'x' else (across, along, height)
    s0, s1 = (x0, x1) if axis == 'x' else (y0, y1)
    panels = []
    for (u0, h0), (u1, h1) in zip(arc, arc[1:]):
        coords = [at(s0, u0, h0), at(s1, u0, h0), at(s1, u1, h1), at(s0, u1, h1)]
        mu, mh = (u0 + u1) / 2, (h0 + h1) / 2
        inward = at(0, centre - mu, z - mh)
        panels.append((coords, role, inward))
    if ends:
        for s, facing in ((s0, 1), (s1, -1)):
            panels.append(([at(s, u, h) for u, h in arc], ends, at(facing, 0, 0)))
    return panels


def ramp_along(start, end, width, z0, z1, top='floor', skirt=None, rail=0, rail_role=None):
    """A ramp `width` wide on the centre line from plan point `start` (at z0) to `end` (at z1), at most MAX_SLOPE;
    `skirt` closes its two sides down to z0; `rail` stands a balustrade that high on both sides, so their sheer edges
    are walls. Cut the room's floor away under it: at a ramp's foot monsters otherwise keep the floor as their support
    and walk in under the ramp."""
    (sx, sy), (ex, ey) = start[:2], end[:2]
    length = math.hypot(ex - sx, ey - sy)
    if math.degrees(math.atan2(abs(z1 - z0), length)) > MAX_SLOPE:
        raise ValueError(f'ramp from {start} to {end} is steeper than {MAX_SLOPE} degrees')
    dx, dy = (ex - sx) / length, (ey - sy) / length
    nx, ny = -dy * width / 2, dx * width / 2
    a, b = (sx - nx, sy - ny), (sx + nx, sy + ny)
    c, d = (ex + nx, ey + ny), (ex - nx, ey - ny)
    coords = [(a[0], a[1], z0), (d[0], d[1], z1), (c[0], c[1], z1), (b[0], b[1], z0)]
    panels = [(coords, top, (0, 0, 1))]
    if skirt and z1 != z0:
        low, high = min(z0, z1), max(z0, z1)
        for p, q, side in ((a, d, -1), (b, c, 1)):
            panels.append(([(p[0], p[1], low), (q[0], q[1], low), (q[0], q[1], z1), (p[0], p[1], z0)], skirt,
                           (side * nx, side * ny, 0)))
    if rail:
        for p, q, side in ((a, d, -1), (b, c, 1)):
            panels.append(([(p[0], p[1], z0), (q[0], q[1], z1), (q[0], q[1], z1 + rail), (p[0], p[1], z0 + rail)],
                           rail_role or skirt or top, (side * nx, side * ny, 0)))
    return panels


def ramp(x0, y0, x1, y1, z0, z1, direction, top='floor', skirt=None, rail=0, rail_role=None):
    """A ramp filling the rectangle, rising from z0 to z1 toward `direction` ('north', 'south', 'east', 'west')."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    start, end, width = {'north': ((cx, y0), (cx, y1), x1 - x0), 'south': ((cx, y1), (cx, y0), x1 - x0),
                         'east': ((x0, cy), (x1, cy), y1 - y0), 'west': ((x1, cy), (x0, cy), y1 - y0)}[direction]
    return ramp_along(start, end, width, z0, z1, top, skirt, rail, rail_role)


def flight_along(start, end, width, z0, steps, tread='floor', riser='trim', rise=24.0, sides=None, rail=0,
                 rail_role=None):
    """A stair flight `width` wide on the centre line from plan point `start` (its foot, at z0) to `end`, `steps`
    risers of `rise` (24 by default; 16 for long shallow flights). Refuses treads monsters' path steps would skip
    (see monster_safe). `sides` closes the void under its two sides; `rail` stands a balustrade that high on them, so
    their sheer edges are walls."""
    (sx, sy), (ex, ey) = start[:2], end[:2]
    length = math.hypot(ex - sx, ey - sy)
    run = length / steps
    if not monster_safe(abs(rise), run):
        raise ValueError(f'a flight of {rise} risers on {run:.0f} treads skips treads for monsters')
    dx, dy = (ex - sx) / length, (ey - sy) / length
    nx, ny = -dy * width / 2, dx * width / 2
    panels = []
    for k in range(steps):
        z = z0 + rise * (k + 1)
        ax, ay = sx + dx * run * k, sy + dy * run * k
        bx, by = ax + dx * run, ay + dy * run
        panels.append(([(ax - nx, ay - ny, z), (bx - nx, by - ny, z), (bx + nx, by + ny, z), (ax + nx, ay + ny, z)],
                       tread, (0, 0, 1)))
        panels.append(([(ax - nx, ay - ny, z - rise), (ax + nx, ay + ny, z - rise), (ax + nx, ay + ny, z),
                        (ax - nx, ay - ny, z)], riser, (-dx, -dy, 0)))
        for side in (-1, 1):
            p, q = (ax + side * nx, ay + side * ny), (bx + side * nx, by + side * ny)
            normal = (side * nx, side * ny, 0)
            if sides:
                panels.append(([(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z), (p[0], p[1], z)], sides, normal))
            if rail:
                panels.append(([(p[0], p[1], z), (q[0], q[1], z), (q[0], q[1], z + rail), (p[0], p[1], z + rail)],
                               rail_role or sides or riser, normal))
    return panels


def ring_flight(cx, cy, radii, z0, rise, sides=8, phase=None, tread='floor', riser='trim', cap=None):
    """Concentric tiers of a regular polygon (MM6's round temple, MM8's tiered d22): `radii` from the outermost
    (whose ring meets the floor at z0) inward; tier k lies between radii[k] and radii[k + 1] at z0 + rise * (k + 1),
    climbing inward (rise > 0, a dais) or descending (rise < 0, a pit), and `cap` floors the innermost polygon one
    tier further. Refuses tiers monsters' path steps would skip."""
    shrink = math.cos(math.pi / sides)
    for r0, r1 in zip(radii, radii[1:]):
        if not monster_safe(abs(rise), (r0 - r1) * shrink):
            raise ValueError(f'tiers of {rise} on {(r0 - r1) * shrink:.0f} treads skip treads for monsters')
    rings = [ngon(cx, cy, r, sides, phase) for r in radii]
    panels = []
    for k, ring in enumerate(rings):
        low, high = z0 + rise * k, z0 + rise * (k + 1)
        for j in range(sides):
            (ax, ay), (bx, by) = ring[j], ring[(j + 1) % sides]
            outward = ((ax + bx) / 2 - cx, (ay + by) / 2 - cy, 0)
            facing = outward if rise > 0 else tuple(-v for v in outward)
            panels.append(([(ax, ay, min(low, high)), (bx, by, min(low, high)), (bx, by, max(low, high)),
                            (ax, ay, max(low, high))], riser, facing))
        if k + 1 < len(rings):
            inner = rings[k + 1]
            for j in range(sides):
                panels.append(([(ring[j][0], ring[j][1], high), (ring[(j + 1) % sides][0], ring[(j + 1) % sides][1], high),
                                (inner[(j + 1) % sides][0], inner[(j + 1) % sides][1], high),
                                (inner[j][0], inner[j][1], high)], tread, (0, 0, 1)))
        elif cap:
            panels.append(([(x, y, high) for x, y in ring], cap, (0, 0, 1)))
    return panels


def clip_half(panel, point, normal):
    """The part of a panel on the side of the plane through `point` that `normal` points away from ((p - point) .
    normal <= 0), or None; its role, facing and fitted texture are kept."""
    q, n = Vector(point), Vector(normal)
    points = [Vector(p) for p in panel[0]]
    kept = []
    for a, c in zip(points, points[1:] + points[:1]):
        da, dc = (a - q).dot(n), (c - q).dot(n)
        if da <= 1e-6:
            kept.append(a)
        if (da < -1e-6 and dc > 1e-6) or (dc < -1e-6 and da > 1e-6):
            kept.append(a + (c - a) * (da / (da - dc)))
    kept = [p for k, p in enumerate(kept) if (p - kept[k - 1]).length > 0.01]
    return (kept, *panel[1:]) if len(kept) >= 3 else None


def clip_to(panels, footprint, below=None):
    """Panels cut to a convex footprint (counter-clockwise plan points) and, with `below` = (point, normal), under a
    sloped ceiling's plane: the walls of a chamfered room and the floors laid across it, or the walls under a stair's
    sloped ceiling."""
    planes = []
    if footprint:
        for (ax, ay), (bx, by) in zip(footprint, footprint[1:] + footprint[:1]):
            planes.append(((ax, ay, 0), (by - ay, ax - bx, 0)))       # the right of each edge is outside
    if below:
        planes.append(below)
    result = []
    for panel in panels:
        for point, normal in planes:
            panel = clip_half(panel, point, normal)
            if panel is None:
                break
        if panel is not None:
            result.append(panel)
    return result


def rect_walls(x0, y0, x1, y1, bands, holes=None, chamfer=None, open_sides=()):
    """The walls of a rectangle in bands of absolute heights, minus holes per side ({'south': [(a0, a1, z0, z1)]},
    absolute), with corners cut at 45 degrees (chamfer: one length or {'sw', 'se', 'ne', 'nw'}): the flat sides
    keep their axis walls and holes, each cut corner gets a diagonal wall."""
    cuts = chamfer if isinstance(chamfer, dict) else dict(sw=chamfer, se=chamfer, ne=chamfer, nw=chamfer)
    cuts = {k: v or 0 for k, v in cuts.items()}
    holes = holes or {}
    panels = []
    for side, wall, a0, a1 in (('south', Wall('y', y0, (0, 1, 0)), x0 + cuts.get('sw', 0), x1 - cuts.get('se', 0)),
                               ('north', Wall('y', y1, (0, -1, 0)), x0 + cuts.get('nw', 0), x1 - cuts.get('ne', 0)),
                               ('west', Wall('x', x0, (1, 0, 0)), y0 + cuts.get('sw', 0), y1 - cuts.get('nw', 0)),
                               ('east', Wall('x', x1, (-1, 0, 0)), y0 + cuts.get('se', 0), y1 - cuts.get('ne', 0))):
        if side not in open_sides:
            panels += banded(wall, a0, a1, bands, holes.get(side, []))
    for start, end, name in (((x0, y0 + cuts.get('sw', 0)), (x0 + cuts.get('sw', 0), y0), 'sw'),
                             ((x1 - cuts.get('se', 0), y0), (x1, y0 + cuts.get('se', 0)), 'se'),
                             ((x1, y1 - cuts.get('ne', 0)), (x1 - cuts.get('ne', 0), y1), 'ne'),
                             ((x0 + cuts.get('nw', 0), y1), (x0, y1 - cuts.get('nw', 0)), 'nw')):
        if cuts.get(name):
            wall = Wall.line(start, end)
            panels += banded(wall, 0, wall.length, bands, [])
    return panels


def _inside(points, x, y, pad=1.0):
    """Whether (x, y) lies in the polygon or within `pad` of its boundary."""
    inside = False
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            inside = not inside
        length = math.hypot(bx - ax, by - ay) or 1
        t = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / length ** 2))
        if math.hypot(ax + t * (bx - ax) - x, ay + t * (by - ay) - y) <= pad:
            return True
    return inside


class Builder:
    """One map's authoring state: materials, rooms (sector panels), portals, triggers, mechanisms, decorations,
    lights and spawns; `export` writes the GLB, the geometry metadata and the .blend."""
    def __init__(self, map_file, roles, output, role_scale=None, decoration_ids=None):
        self.map_file, self.roles, self.output = map_file, dict(roles), Path(output)
        self.output.mkdir(parents=True, exist_ok=True)
        self.role_scale = role_scale or {}
        self.decoration_ids = decoration_ids or json.loads(
            (ROOT / 'output/hesper_stage/decoration_ids.json').read_text())
        for scene_object in list(bpy.data.objects):
            bpy.data.objects.remove(scene_object, do_unlink=True)
        self.scene = bpy.context.scene
        stem = Path(map_file).stem
        self.stem = stem
        self.metadata = {'format_version': 2, 'kind': 'indoor_geometry', 'map_file': map_file,
                         'source': {'authoring_file': f'{stem}.blend', 'asset_path': f'{stem}.glb',
                                    'coordinate_system': 'blender_z_up', 'unit_scale': SCALE,
                                    'import': {'source_format': 'glb', 'reserve_sector_zero': True,
                                               'merge_coplanar_faces': False, 'generate_bsp': True,
                                               'generate_outlines': True}},
                         'materials': [], 'rooms': [], 'portals': [], 'surfaces': [], 'mechanisms': [],
                         'entities': [], 'lights': [], 'spawns': []}
        self.materials, self.dimensions, self.palette = {}, {}, []
        for key in sorted(set(self.roles.values())):
            self._material(key)
        self.rooms, self.bounds, self.ambient = {}, {}, {}
        self.footprints = {}
        self.portals, self.triggers, self.mechanisms = [], [], []
        self.decorations, self.lights, self.spawns = [], [], []
        self.events = {}

    def _material(self, key):
        image = bpy.data.images.load(str(texture_path(key)), check_existing=True)
        image.pack()
        material = bpy.data.materials.new(f'{self.stem}_{key}')
        material.use_nodes = True
        node = material.node_tree.nodes.new('ShaderNodeTexImage')
        node.image = image
        node.interpolation = 'Closest'
        material.node_tree.links.new(node.outputs['Color'],
                                     material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        native = (image.size[0] // 4, image.size[1] // 4)
        self.materials[key], self.dimensions[key] = material, native
        self.palette.append(key)
        self.metadata['materials'].append({'id': key, 'source_material': material.name, 'texture': key,
                                           'texture_width': native[0], 'texture_height': native[1]})

    # --- Faces -----------------------------------------------------------------------------------------------------
    def mesh(self, name, panels, kind, **properties):
        """panels: (coords, role, inward[, Fit]). UVs: one texel per world unit on the dominant plane, or fitted."""
        vertices, polygons, uvs, keys = [], [], [], []
        for panel in panels:
            coords, role, inward = panel[:3]
            fit = panel[3] if len(panel) > 3 else None
            key = self.roles[role]
            points = []
            for p in coords:                       # a corner given twice is one corner
                if not points or (Vector(p) - points[-1]).length > 0.5:
                    points.append(Vector(p))
            if len(points) > 1 and (points[0] - points[-1]).length <= 0.5:
                points.pop()
            if len(points) < 3:
                continue
            normal = (points[1] - points[0]).cross(points[2] - points[0])
            if normal.length < .001:
                continue
            if normal.dot(Vector(inward)) < 0:
                points.reverse()
            offset = len(vertices)
            vertices.extend(tuple(p / SCALE) for p in points)
            polygons.append(tuple(range(offset, len(vertices))))
            if fit:
                uvs.extend(((p - fit.origin).dot(fit.right) / fit.width, (p - fit.origin).dot(fit.up) / fit.height)
                           for p in points)
            else:
                drop = max(range(3), key=lambda i: abs(normal[i]))
                tangents = [i for i in range(3) if i != drop]
                width, height = (d * self.role_scale.get(role, 1.0) for d in self.dimensions[key])
                uvs.extend((p[tangents[0]] / width, p[tangents[1]] / height) for p in points)
            keys.append(key)
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices, [], polygons)
        data.update()
        obj = bpy.data.objects.new(name, data)
        self.scene.collection.objects.link(obj)
        obj['levelgen_kind'] = kind
        for key, value in properties.items():
            obj[key] = value
        for key in self.palette:
            data.materials.append(self.materials[key])
        for polygon, key in zip(data.polygons, keys):
            polygon.material_index = self.palette.index(key)
        layer = data.uv_layers.new()
        for loop, uv in zip(layer.data, uvs):
            loop.uv = uv
        return obj

    # --- Rooms -------------------------------------------------------------------------------------------------------
    def room(self, rid, bounds, ambient):
        """bounds: (x0, y0, x1, y1, z0, z1), used to find the room of a marker; ambient: 0 brightest, 31 black."""
        self.rooms[rid] = []
        self.bounds[rid] = bounds
        self.ambient[rid] = ambient
        return self.rooms[rid]

    def box_room(self, rid, x0, y0, x1, y1, z, height, bands, holes=None, floor_role='floor', ceiling_role='ceiling',
                 ambient=24, open_sides=(), chamfer=None):
        """A rectangular room: floor, ceiling and banded walls with holes per side ({'south': [(a0, a1, z0, z1)]},
        heights relative to z; 'south'/'north' run along x, 'west'/'east' along y). `chamfer` cuts its corners at
        45 degrees (rect_walls; the room is then found by its footprint); ceiling_role None leaves the ceiling to
        hip_ceiling or vault."""
        if chamfer:
            footprint = chamfer_rect(x0, y0, x1, y1, chamfer)
            panels = self.room(rid, (x0, y0, x1, y1, z - 1, z + height), ambient)
            self.footprints[rid] = footprint
            panels += polygon_floor(footprint, z, floor_role)
            if ceiling_role:
                panels += polygon_ceiling(footprint, z + height, ceiling_role)
            holes = {side: [(h[0], h[1], z + h[2], z + h[3]) for h in hs] for side, hs in (holes or {}).items()}
            panels += rect_walls(x0, y0, x1, y1, [(z + b0, z + b1, role) for b0, b1, role in stretch(bands, height)],
                                 holes, chamfer, open_sides)
            return panels
        panels = self.room(rid, (x0, y0, x1, y1, z - 1, z + height), ambient)
        panels += floor(x0, y0, x1, y1, z, floor_role)
        panels += ceiling(x0, y0, x1, y1, z + height, ceiling_role)
        holes = holes or {}
        for side, wall, a0, a1 in (('south', Wall('y', y0, (0, 1, 0)), x0, x1),
                                    ('north', Wall('y', y1, (0, -1, 0)), x0, x1),
                                    ('west', Wall('x', x0, (1, 0, 0)), y0, y1),
                                    ('east', Wall('x', x1, (-1, 0, 0)), y0, y1)):
            if side in open_sides:
                continue
            fitted = stretch(bands, height)
            panels += banded(wall, a0, a1, [(z + b0, z + b1, role) for b0, b1, role in fitted],
                             [(h[0], h[1], z + h[2], z + h[3]) for h in holes.get(side, [])])
        return panels

    def poly_room(self, rid, footprint, z, height, bands, holes=None, floor_role='floor', ceiling_role='ceiling',
                  ambient=24, open_edges=()):
        """A room on any simple footprint (counter-clockwise plan points: chamfer_rect, ngon or your own): floor and
        ceiling in convex pieces (ceiling_role None leaves the ceiling to hip_ceiling or vault), banded walls on every
        edge, edge k running from footprint[k] to footprint[k + 1], with holes per edge ({k: [(a0, a1, z0, z1)]},
        `along` from that edge's start, heights relative to z). room_at finds markers by the footprint."""
        footprint = [tuple(p[:2]) for p in footprint]
        if not _ccw(footprint):
            raise ValueError(f'room {rid}: the footprint must run counter-clockwise')
        xs, ys = [p[0] for p in footprint], [p[1] for p in footprint]
        panels = self.room(rid, (min(xs), min(ys), max(xs), max(ys), z - 1, z + height), ambient)
        self.footprints[rid] = footprint
        panels += polygon_floor(footprint, z, floor_role)
        if ceiling_role:
            panels += polygon_ceiling(footprint, z + height, ceiling_role)
        holes = holes or {}
        fitted = stretch(bands, height)
        for k, start in enumerate(footprint):
            if k in open_edges:
                continue
            wall = Wall.line(start, footprint[(k + 1) % len(footprint)])
            panels += banded(wall, 0, wall.length, [(z + b0, z + b1, role) for b0, b1, role in fitted],
                             [(h[0], h[1], z + h[2], z + h[3]) for h in holes.get(k, [])])
        return panels

    def edge_wall(self, rid, k):
        """Edge k of a poly_room's footprint as its Wall."""
        footprint = self.footprints[rid]
        return Wall.line(footprint[k], footprint[(k + 1) % len(footprint)])

    def opening_line(self, owner, other, wall, a0, a1, z0, z1, depth=THICK, floor_role='floor', ceiling_role='trim',
                     side_role='trim'):
        """An opening through a wall of any direction `depth` thick: the reveal (floor, soffit, jambs; owned by
        `owner`, whose room the wall faces) runs behind the wall, the portal to `other` stands at its far side."""
        far = wall.offset(depth)
        near = [wall.point(a0, 0), wall.point(a1, 0), far.point(a1, 0), far.point(a0, 0)]
        panels = self.rooms[owner]
        panels.append(([p + Vector((0, 0, z0)) for p in near], floor_role, (0, 0, 1)))
        panels.append(([p + Vector((0, 0, z1)) for p in near], ceiling_role, (0, 0, -1)))
        along = wall.axis_vector()
        for a, facing in ((a0, 1), (a1, -1)):
            panels.append(([wall.point(a, z0), far.point(a, z0), far.point(a, z1), wall.point(a, z1)], side_role,
                           tuple(along * facing)))
        self.portal(owner, other, [far.point(a0, z0), far.point(a1, z0), far.point(a1, z1), far.point(a0, z1)])
        return far

    def reveal(self, rid, x0, y0, x1, y1, z0, z1, along, floor_role='floor', ceiling_role='trim', side_role='trim'):
        """The floor, soffit and jambs of an opening through a thick wall; `along` is the axis the passage runs on."""
        panels = self.rooms[rid]
        panels += floor(x0, y0, x1, y1, z0, floor_role)
        panels += ceiling(x0, y0, x1, y1, z1, ceiling_role)
        if along == 'y':
            panels += Wall('x', x0, (1, 0, 0)).quad(y0, y1, z0, z1, side_role)
            panels += Wall('x', x1, (-1, 0, 0)).quad(y0, y1, z0, z1, side_role)
        else:
            panels += Wall('y', y0, (0, 1, 0)).quad(x0, x1, z0, z1, side_role)
            panels += Wall('y', y1, (0, -1, 0)).quad(x0, x1, z0, z1, side_role)

    def portal(self, front, back, coords):
        self.portals.append((front, back, [tuple(p) for p in coords]))

    def opening(self, owner, other, axis, plane, a0, a1, z0, z1, depth=THICK, toward=1, **reveal_roles):
        """An opening between `owner` and `other` through a wall `depth` thick: the reveal (owned by `owner`) runs
        from the owner's wall plane `plane` toward `toward` (+1 or -1 along the axis), the portal stands at its far
        end. axis 'y': the wall runs along x at y = plane; 'x': along y at x = plane."""
        far = plane + toward * depth
        if axis == 'y':
            self.reveal(owner, a0, min(plane, far), a1, max(plane, far), z0, z1, 'y', **reveal_roles)
            self.portal(owner, other, [(a0, far, z0), (a1, far, z0), (a1, far, z1), (a0, far, z1)])
        else:
            self.reveal(owner, min(plane, far), a0, max(plane, far), a1, z0, z1, 'x', **reveal_roles)
            self.portal(owner, other, [(far, a0, z0), (far, a1, z0), (far, a1, z1), (far, a0, z1)])
        return far

    # --- Gameplay --------------------------------------------------------------------------------------------------
    def trigger(self, name, rid, panels, event, kind='click', flags=(), cog=0):
        self.triggers.append((name, rid, panels, event, kind, list(flags), cog))
        if event:
            self.events.setdefault(event, name)

    def surface(self, name, rid, panels, flags=(), cog=0):
        """Faces with flags or a cog number but no event (water, a face SetTexture swaps)."""
        self.triggers.append((name, rid, panels, 0, None, list(flags), cog))

    def door(self, name, rid, panels, door_id, move_length, direction=(0, 0, 1), open_speed=256, close_speed=256,
             initial='closed', event=0, flags=()):
        """A linear mover: its faces move `move_length` along `direction` to open (from the closed pose authored);
        `event` and `flags` (secret, ...) go on its faces."""
        self.mechanisms.append((name, rid, panels, door_id, move_length, direction, open_speed, close_speed,
                                initial, event, list(flags)))
        if event:
            self.events.setdefault(event, name)

    def decoration(self, name, x, y, z, facing=0, event=0, cog=0):
        """event: what clicking it runs (the entity's secondary event); cog: its key for evt.SetSprite (the primary
        event; 0 keys it by its index), shared by every decoration a script swaps together."""
        self.decorations.append((name, x, y, z, int(round(facing)) % 360, event, cog))

    def light(self, lid, x, y, z, radius, colour, group=0):
        self.lights.append((lid, x, y, z, radius, colour, group))

    def plan_light(self, light, cog_base):
        """A plan light (make_dungeon_plans.py): a fixture becomes its decoration (its own light; in a light group it
        stands as its _off variant, cog cog_base + group, until evt.SetSprite lights it), any other a BLV light."""
        if light['fixture']:
            name = light['fixture'] + ('_off' if light['group'] else '')
            self.decoration(name, light['x'], light['y'], light['z'], light['facing'],
                            cog=cog_base + light['group'] if light['group'] else 0)
        else:
            self.light(light['id'], light['x'], light['y'], light['z'], light['radius'], light['colour'],
                       light['group'])

    def spawn(self, sid, x, y, z, type_id=1, index=0):
        self.spawns.append((sid, x, y, z, type_id, index))

    def room_at(self, x, y, z):
        """The smallest room holding the point: by its footprint for a poly_room, else by its bounds."""
        best = None
        for rid, (x0, y0, x1, y1, z0, z1) in self.bounds.items():
            if x0 - 1 <= x <= x1 + 1 and y0 - 1 <= y <= y1 + 1 and z0 - 2 <= z <= z1 + 2:
                if rid in self.footprints:
                    if not _inside(self.footprints[rid], x, y):
                        continue
                    area = abs(sum(ax * by - bx * ay for (ax, ay), (bx, by)
                                   in zip(self.footprints[rid], self.footprints[rid][1:] + self.footprints[rid][:1]))) / 2
                else:
                    area = (x1 - x0) * (y1 - y0)
                if best is None or area < best[0]:
                    best = (area, rid)
        if best is None:
            raise ValueError((x, y, z))
        return best[1]

    # --- Export ----------------------------------------------------------------------------------------------------
    def _own(self, rid, obj):
        next(r for r in self.metadata['rooms'] if r['id'] == 'room_' + rid)['source_nodes'].append(obj.name)

    def _marker(self, name, x, y, z, kind, **properties):
        return self.mesh(name, [([(x - 1, y - 1, z), (x + 1, y - 1, z), (x + 1, y + 1, z), (x - 1, y + 1, z)],
                                 'marker', (0, 0, 1))], kind, **properties)

    def export(self, semantic=None):
        md = self.metadata
        for rid, panels in self.rooms.items():
            obj = self.mesh('ROOM_' + rid, panels, 'room', semantic_id=rid)
            obj['min_ambient_light_level'] = self.ambient[rid]
            md['rooms'].append({'id': 'room_' + rid, 'source_nodes': [obj.name],
                                'min_ambient_light_level': self.ambient[rid]})
        for index, (front, back, coords) in enumerate(self.portals):
            name = f'PORTAL_{front}_{back}_{index}'
            b = self.bounds[front]
            centre = Vector(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, (b[4] + b[5]) / 2))
            points = [Vector(p) for p in coords]
            normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
            facing = tuple(normal if normal.dot(centre - points[0]) > 0 else -normal)
            self.mesh(name, [(coords, 'marker', facing)], 'portal')
            md['portals'].append({'id': name[7:], 'source_node': name, 'front_room': 'room_' + front,
                                  'back_room': 'room_' + back})
        for name, rid, panels, event, kind, flags, cog in self.triggers:
            obj = self.mesh('TRIGGER_' + name, panels, 'trigger', event_id=event)
            self._own(rid, obj)
            record = {'id': name, 'source_node': obj.name, 'flags': flags}
            if event:
                record['trigger'] = {'event_id': event, 'type': kind}
            if cog:
                record['cog_number'] = cog
            md['surfaces'].append(record)
        for (name, rid, panels, door_id, length, direction, open_speed, close_speed, initial, event,
             flags) in self.mechanisms:
            obj = self.mesh('MECH_' + name, panels, 'mechanism', semantic_id=name, door_id=door_id)
            self._own(rid, obj)
            if event or flags:
                record = {'id': name, 'source_node': obj.name, 'flags': flags}
                if event:
                    record['trigger'] = {'event_id': event, 'type': 'click'}
                md['surfaces'].append(record)
            md['mechanisms'].append({'id': name, 'kind': 'linear', 'source_nodes': [obj.name],
                                     'door': {'door_id': door_id, 'initial_state': initial, 'source_pose': 'closed',
                                              'direction': [-v for v in direction], 'move_length': length,
                                              'open_speed': open_speed, 'close_speed': close_speed}})
        for index, (name, x, y, z, facing, event, cog) in enumerate(self.decorations):
            node = f'DECOR_{name}_{index}'
            obj = self._marker(node, x, y, z, 'decoration')
            self._own(self.room_at(x, y, z), obj)
            record = {'id': f'{name}_{index}', 'kind': 'decoration', 'source_node': node,
                      'decoration_list_id': self.decoration_ids[name] - 1, 'event_id_primary': cog,
                      'event_id_secondary': event}
            if facing:
                record['facing'] = facing
            md['entities'].append(record)
        for lid, x, y, z, radius, colour, group in self.lights:
            obj = self._marker('LIGHT_' + lid, x, y, z, 'light_marker', radius=radius, brightness=31)
            self._own(self.room_at(x, y, z), obj)
            record = {'id': lid, 'source_node': obj.name, 'color': list(colour), 'radius': radius, 'brightness': 31,
                      'type': 'point'}
            if group:
                record['group'] = group
            md['lights'].append(record)
        for sid, x, y, z, type_id, index in self.spawns:
            obj = self._marker('SPAWN_' + sid, x, y, z, 'spawn')
            self._own(self.room_at(x, y, z), obj)
            md['spawns'].append({'id': sid, 'source_node': obj.name, 'type_id': type_id, 'index': index,
                                 'radius': 256, 'group': 0})
        bpy.ops.export_scene.gltf(filepath=str(self.output / f'{self.stem}.glb'), export_format='GLB',
                                  use_active_scene=True, export_yup=False, export_cameras=False, export_lights=False,
                                  export_apply=True, export_extras=True)
        (self.output / f'{self.stem}.geometry.yml').write_text(json.dumps(md, indent=2) + '\n')
        semantic = dict(semantic or {})
        semantic.update({'map': self.map_file, 'events': self.events, 'decorations': len(self.decorations),
                         'sectors': [r['id'] for r in md['rooms']],
                         'doors': {m[0]: m[3] for m in self.mechanisms}})
        (self.output / f'{self.stem}.semantic.json').write_text(json.dumps(semantic, indent=2) + '\n')
        bpy.ops.wm.save_as_mainfile(filepath=str(self.output / f'{self.stem}.blend'), compress=True)
        print(json.dumps({'objects': len(self.scene.objects), 'sectors': len(md['rooms']) + 1,
                          'portals': len(md['portals']), 'triggers': len(md['surfaces']),
                          'mechanisms': len(md['mechanisms']), 'decorations': len(self.decorations),
                          'lights': len(md['lights']), 'spawns': len(md['spawns'])}))
