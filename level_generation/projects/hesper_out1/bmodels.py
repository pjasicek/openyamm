"""The BModel kit of Starport Reach: buildings as faces (polygons of world points, each with a texture), written as
OBJ in the editor's convention (level_generation/projects/brackenford_greywatch: 1 OBJ unit = 128 world units,
z up, faces wound counter-clockwise seen from outside, UV 1.0 = the texture's native size, v up).

The game draws BModel faces without back-face culling but lights each by its normal, so a shell the party sees
from both sides (the hangar vaults, awnings) is made two sided by `both`: a reversed copy BACK_OFFSET units behind
the front, as two faces in one plane fight in the depth buffer. A building returns its faces and the indices of its
event faces (doors, hatches); `invisible` faces (FaceAttribute::Invisible) are not drawn but still block movement,
the collision of the 3D-model buildings.
"""
import math

import numpy as np

OBJ_SCALE = 128.0
BACK_OFFSET = 4.0


class Model:
    def __init__(self, name):
        self.name = name
        self.faces = []                 # (points [(x, y, z)], texture, fit)
        self.events = {}                # event id -> [face index]
        self.invisible = []             # face indices

    def face(self, points, texture, event=None, fit=False):
        """fit: the texture fills the face once (a single-face texture: a door, a hatch), instead of repeating at
        one native texel per world unit."""
        points = [tuple(float(c) for c in p) for p in points]
        if event is not None:
            self.events.setdefault(event, []).append(len(self.faces))
        self.faces.append((points, texture, fit))

    def facing(self, points, texture, direction, event=None, fit=False):
        """A face wound so its normal points along direction."""
        self.face(points if np.dot(normal(points), direction) >= 0 else list(reversed(points)), texture, event, fit)

    def both(self, points, texture):
        self.face(points, texture)
        back = normal(points) * BACK_OFFSET
        self.face([tuple(np.array(p) - back) for p in reversed(points)], texture)

    def collider(self, centre, size, yaw=0.0, texture='hoplate'):
        """An invisible box: blocks movement, not drawn."""
        first = len(self.faces)
        self.box(centre, size, texture, yaw=yaw)
        self.invisible += list(range(first, len(self.faces)))

    def box(self, centre, size, texture, yaw=0.0, top=None, bottom=False, sides=None, skip=()):
        """An axis box (size x, y, z) standing on centre's z, turned by yaw radians about its centre."""
        cx, cy, cz = centre
        hx, hy, h = size[0] / 2, size[1] / 2, size[2]
        corners = [rotate((-hx, -hy), yaw), rotate((hx, -hy), yaw), rotate((hx, hy), yaw), rotate((-hx, hy), yaw)]
        low = [(cx + x, cy + y, cz) for x, y in corners]
        high = [(cx + x, cy + y, cz + h) for x, y in corners]
        names = ['south', 'east', 'north', 'west']
        for i in range(4):
            if names[i] in skip:
                continue
            j = (i + 1) % 4
            texture_i = (sides or {}).get(names[i], texture)
            self.face([low[i], low[j], high[j], high[i]], texture_i)
        self.face(high, top or texture)
        if bottom:
            self.face(list(reversed(low)), texture)

    def prism(self, centre, radius, height, sides, texture, top=None, z0=0.0, phase=0.0):
        """A regular prism (round towers), standing on centre's z + z0."""
        cx, cy, cz = centre
        ring = [(cx + radius * math.cos(phase + 2 * math.pi * i / sides),
                 cy + radius * math.sin(phase + 2 * math.pi * i / sides)) for i in range(sides)]
        for i in range(sides):
            a, b = ring[i], ring[(i + 1) % sides]
            self.face([(a[0], a[1], cz + z0), (b[0], b[1], cz + z0), (b[0], b[1], cz + z0 + height),
                       (a[0], a[1], cz + z0 + height)], texture)
        if top:
            self.face([(x, y, cz + z0 + height) for x, y in ring], top)
        return ring

    def dome(self, centre, radius, rise, sides, rings, texture, z0=0.0, from_ring=0):
        """A dome of quads and a top cap, its base ring at centre's z + z0."""
        cx, cy, cz = centre

        def ring(k):
            angle = math.pi / 2 * k / rings
            r = radius * math.cos(angle)
            z = cz + z0 + rise * math.sin(angle)
            return [(cx + r * math.cos(2 * math.pi * i / sides), cy + r * math.sin(2 * math.pi * i / sides), z)
                    for i in range(sides)]
        for k in range(from_ring, rings - 1):
            a, b = ring(k), ring(k + 1)
            for i in range(sides):
                j = (i + 1) % sides
                self.face([a[i], a[j], b[j], b[i]], texture)
        top = ring(rings - 1)
        self.face(top, texture)

    def tube(self, start, end, radius, texture, sides=8, caps=True):
        """A pipe between two points."""
        a, b = np.array(start, dtype=np.float64), np.array(end, dtype=np.float64)
        axis = (b - a) / np.linalg.norm(b - a)
        helper = np.array([0, 0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(axis, helper)
        u /= np.linalg.norm(u)
        v = np.cross(axis, u)
        ring = [u * math.cos(2 * math.pi * i / sides) + v * math.sin(2 * math.pi * i / sides) for i in range(sides)]
        for i in range(sides):
            j = (i + 1) % sides
            self.face([a + ring[i] * radius, a + ring[j] * radius, b + ring[j] * radius, b + ring[i] * radius], texture)
        if caps:
            self.face([b + r * radius for r in ring], texture)
            self.face([a + r * radius for r in reversed(ring)], texture)

    def disc(self, centre, radius, front, texture, sides=16, event=None, rim=0.0, rim_depth=0.0, rim_texture=None):
        """A round face standing upright, facing the horizontal direction front, its texture fitted to it; with an
        optional rim ring standing out of the wall by rim_depth."""
        c = np.array(centre, dtype=np.float64)
        n = np.array([front[0], front[1], 0.0])
        n /= np.linalg.norm(n)
        right = np.array([-n[1], n[0], 0.0])          # to the right of a viewer in front, looking back along -front
        up = np.array([0, 0, 1.0])

        def point(angle, r, out=0.0):                # angles counter-clockwise as the viewer sees them
            return c + n * out + (right * math.cos(angle) + up * math.sin(angle)) * r
        angles = [2 * math.pi * i / sides for i in range(sides)]
        self.face([point(a, radius, rim_depth * 0.5) for a in angles], texture, event=event, fit=True)
        if rim > 0:
            for i in range(sides):
                a0, a1 = angles[i], angles[(i + 1) % sides]
                self.face([point(a0, radius, rim_depth), point(a0, radius + rim, rim_depth),
                           point(a1, radius + rim, rim_depth), point(a1, radius, rim_depth)], rim_texture)
                self.both([point(a0, radius + rim, 0), point(a1, radius + rim, 0),
                           point(a1, radius + rim, rim_depth), point(a0, radius + rim, rim_depth)], rim_texture)


def rotate(point, yaw):
    c, s = math.cos(yaw), math.sin(yaw)
    return (point[0] * c - point[1] * s, point[0] * s + point[1] * c)


def normal(points):
    p = np.array(points, dtype=np.float64)
    n = np.zeros(3)
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
    length = np.linalg.norm(n)
    return n / length if length > 0 else n


def uv(points, size, fit=False):
    """Planar UVs at one native texel per world unit: walls and sloped roofs take the horizontal direction in their
    plane as u and the direction up the face as v (a roof's corrugation runs down its slope), floors and flat roofs
    world x and y."""
    n = normal(points)
    p = np.array(points, dtype=np.float64)
    if abs(n[2]) > 0.98:
        u_axis, v_axis = np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
    else:
        u_axis = np.array([-n[1], n[0], 0.0])
        u_axis /= np.linalg.norm(u_axis)
        v_axis = np.cross(n, u_axis)
        v_axis /= np.linalg.norm(v_axis)
    origin = p[0]
    us = (p - origin) @ u_axis / size[0]
    vs = (p - origin) @ v_axis / size[1]
    if fit:
        us = (us - us.min()) / (us.max() - us.min())
        vs = (vs - vs.min()) / (vs.max() - vs.min())
        return list(zip(us, vs))
    # Keep the texture's bottom on the face's lowest edge for walls, so trim and bands line up.
    if abs(n[2]) <= 0.98:
        vs -= vs.min()
    return list(zip(us, vs))


def write_obj(model, path, sizes):
    lines = [f'o BMODEL_{model.name}']
    vertex = 1
    face_lines = []
    for points, texture, fit in model.faces:
        indices = []
        for (x, y, z), (u, v) in zip(points, uv(points, sizes[texture], fit)):
            lines.append(f'v {x / OBJ_SCALE:.5f} {y / OBJ_SCALE:.5f} {z / OBJ_SCALE:.5f}')
            lines.append(f'vt {u:.5f} {v:.5f}')
            indices.append(vertex)
            vertex += 1
        face_lines.append(f'usemtl {texture}')
        face_lines.append('f ' + ' '.join(f'{i}/{i}' for i in indices))
    path.write_text('\n'.join(lines + face_lines) + '\n')
