"""D7's sky-barges (one per element tint) and Lucio's celestial boat, hand-built (lane S, session 10; no Meshy).

A lofted hull (curved keel with rocker, a sheer that sweeps up into a raised prow and stern), a carved gilt frieze under
a fluted gilt rail, a low plank deck, gilt scroll posts at prow and stern, a mast with a yard and a bellied sail
carrying a glowing element sigil, a pennant, a glowing runner under the keel and glowing medallions along the hull.
The barges add a damask canopy on gilt posts over the gangway, a gangplank out of the port gangway and three crates.

Units: game units / 100 in Blender (the binding height sets the game size, scale 1). Origin: the deck's centre at deck
height. Prow toward Blender -Y (glTF +Z: the binding's yaw_offset -90 deg makes the map facing the way the prow points);
port (the gangway side) is Blender +X, so in the map the gangway is on the left of the facing.
Materials: skybarge_trim (shared 2K atlas), skybarge_cloth_<tint> and skybarge_glow_<tint> (one 1K image per tint,
the glow material emissive). Objects <name> and <name>_LOD1.._LOD3, linked afterwards by link_static_model_lods.py.
Usage: blender -b --factory-startup --python build.py -- <fire|air|earth|water|boat|all>"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
TEX = os.path.join(PROJECT, 'work', 'tex')
LAYOUT = json.load(open(os.path.join(TEX, 'layout.json')))
HULLS = json.load(open(os.path.join(HERE, 'hulls.json')))
U = 0.01
PX = 2.0                       # texels per game unit
TRIM_S, CLOTH_S = 2048, 1024
M_TRIM, M_CLOTH, M_GLOW = 0, 1, 2

DETAIL = [  # LOD0 .. LOD3
    dict(stations=31, girth=7, gangway=True, post=22, post_sides=6, rod=6, sail=(6, 4), medals=8, orb=(8, 5),
         strip=True, crates=True, valance=True, pennant=True, sigil=8),
    dict(stations=19, girth=4, gangway=True, post=13, post_sides=5, rod=5, sail=(4, 3), medals=6, orb=(6, 4),
         strip=True, crates=True, valance=False, pennant=True, sigil=6),
    dict(stations=11, girth=3, gangway=False, post=8, post_sides=4, rod=4, sail=(3, 2), medals=0, orb=(4, 3),
         strip=True, crates=False, valance=False, pennant=False, sigil=4),
    dict(stations=7, girth=2, gangway=False, post=5, post_sides=3, rod=3, sail=(2, 1), medals=0, orb=None,
         strip=False, crates=False, valance=False, pennant=False, sigil=0),
]

# per model: hull, rig and dressing (game units, origin at the deck's centre, prow at -Y)
SPEC = {
    'barge': dict(mast_y=-300, mast_h=500, yard_z=468, sail_w=300, sail_h=236, belly=40, sigil_r=46,
                  prow=dict(length=400, lean=0.1, turn=2.0, r0=21, r1=7),
                  stern=dict(length=360, lean=0.25, turn=-2.15, r0=20, r1=7),
                  medal_t=(-0.52, -0.2, 0.2, 0.52), canopy=dict(y0=-112, y1=232, half=152, eave=190, ridge=252,
                                                                  post_x=126, post_y=(-92, 212)),
                  gangplank=True, crates=((-120, -150, 56, 48), (-60, -160, 48, 40), (-110, -205, 44, 52))),
    'boat': dict(mast_y=-40, mast_h=400, yard_z=372, sail_w=230, sail_h=196, belly=34, sigil_r=36,
                 prow=dict(length=300, lean=0.1, turn=2.0, r0=16, r1=6),
                 stern=dict(length=270, lean=0.25, turn=-2.1, r0=15, r1=6),
                 medal_t=(-0.45, 0.0, 0.45), canopy=None, gangplank=False, crates=None,
                 thwarts=(-210, 170)),
}


def rpx(region, x, y, size):
    """Pixel (x right, y down) inside the atlas -> Blender UV."""
    return (x / size, 1.0 - y / size)


class Builder:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.part = self.bm.faces.layers.int.new('part')

    def v(self, p):
        return self.bm.verts.new(Vector(p) * U)

    def face(self, verts, uvs, mat, part=0):
        f = self.bm.faces.new(verts)
        f.material_index = mat
        f[self.part] = part
        f.smooth = True
        for loop, t in zip(f.loops, uvs):
            loop[self.uv].uv = t
        return f


# ------------------------------------------------------------------------------------------------ hull

def half_width(h, t):
    return max(h['tip'], h['beam'] / 2 * max(0.0, 1 - abs(t) ** h['pe']) ** h['pq'])


def keel_z(h, t):
    return h['keel_end'] + (h['keel'] - h['keel_end']) * max(0.0, 1 - abs(t) ** 2.2) ** 0.8


def sheer_z(h, t):
    return h['sheer_mid'] + (h['sheer_end'] - h['sheer_mid']) * abs(t) ** 3


def profile(w, zk, s, u):
    """Outer section point (x >= 0, z) at u in 0 (keel) .. 1 (sheer)."""
    return w * math.sin(u * math.pi / 2) ** 0.95, zk + (s - zk) * (1 - math.cos(u * math.pi / 2))


def solve_u(zk, s, z):
    z = min(max(z, zk), s)
    return 2 / math.pi * math.acos(max(-1.0, min(1.0, 1 - (z - zk) / (s - zk))))


def stations(h, det, gangway):
    n = det['stations']
    ts = []
    for i in range(n):
        q = -1 + 2 * i / (n - 1)
        ts.append(math.copysign(abs(q) ** 0.8, q))
    if gangway and det['gangway']:
        L = h['length'] / 2
        ts = [t for t in ts if abs(t * L) > 84] + [y / L for y in (-64, -48, 48, 64)]
    return sorted(ts)


def section(h, t, port_sheer, det):
    """The closed ring of one station: [(x, z, uvinfo)], the edge parts, and the per-point v data."""
    w, zk, s = half_width(h, t), keel_z(h, t), sheer_z(h, t)
    ng = det['girth']
    ring = [(0.0, zk, {'arc': {}})]
    sides = {}
    for sgn in (-1, 1):
        ss = s if sgn < 0 else port_sheer(t, s)
        zf = min(s - 56, ss - 2)
        uf = solve_u(zk, s, zf)
        utop = solve_u(zk, s, ss)
        lower = [profile(w, zk, s, uf * j / ng) for j in range(ng + 1)]
        arcs = [0.0]
        for a, b in zip(lower, lower[1:]):
            arcs.append(arcs[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        total = arcs[-1]
        top = profile(w, zk, s, utop)
        xt = top[0]
        T = min(14.0, 0.35 * xt)
        xd = profile(w, zk, s, solve_u(zk, s, 0.0))[0]
        xd = max(1.0, xd - min(10.0, 0.3 * xd))
        sides[sgn] = dict(lower=[(sgn * x, z, total - arcs[j]) for j, (x, z) in enumerate(lower)], top=(sgn * xt, ss),
                          rail=(sgn * (xt - T), ss), deck=(sgn * xd, 0.0), zf=zf)
    pts, parts = [], []
    # starboard: keel -> up the outer skin -> rail -> inside -> deck edge
    st, po = sides[-1], sides[1]
    pts.append(('hull', st['lower'][0]))
    for j in range(1, len(st['lower'])):
        pts.append(('hull', st['lower'][j]))
    pts += [('top', st['top']), ('rail', st['rail']), ('deck', st['deck']), ('centre', (0.0, 0.0)),
            ('deck', po['deck']), ('rail', po['rail']), ('top', po['top'])]
    for j in range(len(po['lower']) - 1, 0, -1):
        pts.append(('hull', po['lower'][j]))
    n = len(pts)
    names = []
    for i in range(n):
        a, b = pts[i][0], pts[(i + 1) % n][0]
        pair = {a, b}
        if pair <= {'hull'}:
            names.append('hull')
        elif pair == {'hull', 'top'}:
            names.append('frieze')
        elif pair == {'top', 'rail'}:
            names.append('railcap')
        elif pair == {'rail', 'deck'}:
            names.append('inner')
        else:
            names.append('deck')
    return pts, names, s


def region(name):
    return LAYOUT['trim'][name]


def hull_uv(name, kind, p, y, h, s_top):
    """UV of one ring point for a face of part `name`."""
    u = 8 + (y + h['length'] / 2) * PX * min(1.0, (TRIM_S - 16) / (h['length'] * PX))
    x0, y0, x1, y1 = region({'hull': 'hull', 'frieze': 'frieze', 'railcap': 'mould', 'inner': 'inner',
                             'deck': 'deck'}[name])
    if name == 'hull':
        v = y0 + 4 + min(p[2] if len(p) > 2 else 0.0, 345) * PX
    elif name == 'frieze':
        v = y0 + 6 if kind == 'top' else y1 - 6
    elif name == 'railcap':
        v = y0 + 18 if kind == 'top' else y0 + 46
    elif name == 'inner':
        v = y0 + 4 if kind == 'rail' else y1 - 4
    else:
        v = y0 + 4 + min(abs(p[0]) * PX, y1 - y0 - 8)
    return rpx(None, u, v, TRIM_S)


def build_hull(b, h, det, gangway):
    L = h['length'] / 2

    def port_sheer(t, s):
        if not (gangway and det['gangway']):
            return s
        y = abs(t * L)
        if y <= 48.5:
            return 4.0
        return s

    rings = []
    for t in stations(h, det, gangway):
        pts, names, s = section(h, t, port_sheer, det)
        y = t * L
        verts = [b.v((p[1][0], y, p[1][1])) for p in pts]
        rings.append((t, y, pts, names, verts, s))
    for (t0, y0, p0, n0, v0, s0), (t1, y1, p1, n1, v1, s1) in zip(rings, rings[1:]):
        n = len(p0)
        for i in range(n):
            j = (i + 1) % n
            name = n0[i]
            uvs = [hull_uv(name, p0[i][0], p0[i][1], y0, h, s0), hull_uv(name, p0[j][0], p0[j][1], y0, h, s0),
                   hull_uv(name, p1[j][0], p1[j][1], y1, h, s1), hull_uv(name, p1[i][0], p1[i][1], y1, h, s1)]
            # outward winding is fixed later by recalc; parts tag sharp edges
            b.face([v0[i], v0[j], v1[j], v1[i]], uvs, M_TRIM, part=['hull', 'frieze', 'railcap', 'inner',
                                                                   'deck'].index(name) + 1)
    x0, y0, x1, y1 = region('dark')
    for t, y, pts, names, verts, s in (rings[0], rings[-1]):
        uvs = [rpx(None, x0 + 200 + p[1][0] * PX, y0 + 300 - p[1][1] * PX * 0.8, TRIM_S) for p in pts]
        b.face(verts, uvs, M_TRIM, part=9)
    return rings


def outer_point(h, t, z, sgn):
    """A point on the outer skin and its outward normal (for the medallions)."""
    w, zk, s = half_width(h, t), keel_z(h, t), sheer_z(h, t)
    u = solve_u(zk, s, z)
    x, zz = profile(w, zk, s, u)
    xa, za = profile(w, zk, s, max(0.0, u - 0.01))
    xb, zb = profile(w, zk, s, min(1.0, u + 0.01))
    tx, tz = xb - xa, zb - za
    nl = math.hypot(tx, tz)
    return Vector((sgn * x, t * h['length'] / 2, zz)), Vector((sgn * tz / nl, 0.0, -tx / nl))


# ------------------------------------------------------------------------------------------------ parts

def prism(b, centre, axis_n, axis_u, radius, sides, depth_front, depth_back, mat, uv_centre, uv_radius, size,
          part=20):
    """A closed n-gon disc facing axis_n (front at +depth_front, back at -depth_back)."""
    axis_n, axis_u = axis_n.normalized(), axis_u.normalized()
    axis_w = axis_n.cross(axis_u).normalized()
    ring_f, ring_b, uvs = [], [], []
    for k in range(sides):
        a = 2 * math.pi * (k + 0.5) / sides
        off = (axis_u * math.cos(a) + axis_w * math.sin(a)) * radius
        ring_f.append(b.v(centre + axis_n * depth_front + off))
        ring_b.append(b.v(centre - axis_n * depth_back + off))
        uvs.append(rpx(None, uv_centre[0] + uv_radius * math.cos(a), uv_centre[1] - uv_radius * math.sin(a), size))
    b.face(ring_f, uvs, mat, part)
    b.face(list(reversed(ring_b)), list(reversed(uvs)), mat, part)
    edge = rpx(None, uv_centre[0] + uv_radius * 1.02, uv_centre[1], size)
    for k in range(sides):
        j = (k + 1) % sides
        b.face([ring_f[k], ring_b[k], ring_b[j], ring_f[j]], [edge] * 4, mat, part)


def tube(b, path, radii, sides, ref, mat, reg, size, part, u0=0.0, caps=True):
    """A tube along `path` (game units); `ref` a vector never parallel to the path (gives the section's frame).
    UV: u along the length (PX per unit), v round the section across the region's height."""
    x0, y0, x1, y1 = reg
    rings = []
    acc = 0.0
    lengths = [0.0]
    for a, c in zip(path, path[1:]):
        acc += (Vector(c) - Vector(a)).length
        lengths.append(acc)
    for i, p in enumerate(path):
        p = Vector(p)
        a = Vector(path[max(0, i - 1)])
        c = Vector(path[min(len(path) - 1, i + 1)])
        t = (c - a).normalized()
        n1 = ref.cross(t).normalized()
        n2 = t.cross(n1).normalized()
        rings.append([b.v(p + (n1 * math.cos(2 * math.pi * k / sides) + n2 * math.sin(2 * math.pi * k / sides))
                          * radii[i]) for k in range(sides)])
    squeeze = min(1.0, (x1 - x0 - 16) / max(1e-6, lengths[-1] * PX))
    for i in range(len(path) - 1):
        ua = x0 + 8 + lengths[i] * PX * squeeze
        ub = x0 + 8 + lengths[i + 1] * PX * squeeze
        for k in range(sides):
            j = (k + 1) % sides
            va = y0 + 6 + (y1 - y0 - 12) * k / sides
            vb = y0 + 6 + (y1 - y0 - 12) * (k + 1) / sides
            b.face([rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]],
                   [rpx(None, ua, va, size), rpx(None, ua, vb, size), rpx(None, ub, vb, size),
                    rpx(None, ub, va, size)], mat, part)
    if caps:
        cu = rpx(None, x0 + 12, (y0 + y1) / 2, size)
        b.face(list(reversed(rings[0])), [cu] * sides, mat, part)
        b.face(rings[-1], [cu] * sides, mat, part)


def scroll_path(base, out, lean, turn, length, n):
    """A scroll post in the y-z plane: from `base` leaning `lean` rad toward `out` (-1 prow, +1 stern), turning by
    `turn` x pi in all (positive curls outward, negative back over the deck) with curvature growing exponentially."""
    bexp = 3.4
    theta = turn * math.pi
    A = theta * bexp / (length * (math.exp(bexp) - 1))
    pts = [Vector(base)]
    phi = lean
    steps = 160
    ds = length / steps
    for i in range(steps):
        s = (i + 0.5) * ds
        phi += A * math.exp(bexp * s / length) * ds
        pts.append(pts[-1] + Vector((0.0, out * math.sin(phi) * ds, math.cos(phi) * ds)))
    # resample to n points, denser toward the curl (where the curvature lives)
    idx = sorted({round(steps * (1 - (1 - k / (n - 1)) ** 1.6)) for k in range(n)})
    return [tuple(pts[i]) for i in idx]


def sphere(b, centre, r, seg, rings_n, mat, uv, size, part=30):
    top = b.v(centre + Vector((0, 0, r)))
    bot = b.v(centre - Vector((0, 0, r)))
    rings = []
    for i in range(1, rings_n):
        a = math.pi * i / rings_n
        rings.append([b.v(centre + Vector((math.sin(a) * math.cos(2 * math.pi * k / seg),
                                           math.sin(a) * math.sin(2 * math.pi * k / seg), math.cos(a))) * r)
                      for k in range(seg)])
    c = rpx(None, uv[0], uv[1], size)
    for k in range(seg):
        j = (k + 1) % seg
        b.face([top, rings[0][k], rings[0][j]], [c] * 3, mat, part)
        b.face([bot, rings[-1][j], rings[-1][k]], [c] * 3, mat, part)
        for i in range(len(rings) - 1):
            b.face([rings[i][k], rings[i + 1][k], rings[i + 1][j], rings[i][j]], [c] * 4, mat, part)


def box(b, lo, hi, mat, reg, size, part=40, top_reg=None):
    lo, hi = Vector(lo), Vector(hi)
    c = [Vector((x, y, z)) for z in (lo.z, hi.z) for y in (lo.y, hi.y) for x in (lo.x, hi.x)]
    vs = [b.v(p) for p in c]
    faces = {'-z': (0, 2, 3, 1), '+z': (4, 5, 7, 6), '-y': (0, 1, 5, 4), '+y': (2, 6, 7, 3), '-x': (0, 4, 6, 2),
             '+x': (1, 3, 7, 5)}
    for key, idx in faces.items():
        x0, y0, x1, y1 = top_reg if (key == '+z' and top_reg) else reg
        axes = {'z': (0, 1), 'y': (0, 2), 'x': (1, 2)}[key[1]]
        pts = [c[i] for i in idx]
        a0 = [p[axes[0]] for p in pts]
        a1 = [p[axes[1]] for p in pts]
        uvs = []
        for p in pts:
            s = (p[axes[0]] - min(a0)) / max(max(a0) - min(a0), 1e-6)
            t = (p[axes[1]] - min(a1)) / max(max(a1) - min(a1), 1e-6)
            uvs.append(rpx(None, x0 + 6 + (x1 - x0 - 12) * s, y1 - 6 - (y1 - y0 - 12) * t, size))
        b.face([vs[i] for i in idx], uvs, mat, part)


def sail(b, sp, det, part=50):
    """The bellied sail under the yard (a closed slab 3 thick), the sigil disc through it."""
    nx, nz = det['sail']
    W, Hs = sp['sail_w'], sp['sail_h']
    ztop = sp['yard_z'] - 8
    ym = sp['mast_y'] - 12
    x0, y0, x1, y1 = LAYOUT['cloth']['weave']

    def point(i, k, back):
        x = -W / 2 + W * i / nx
        z = ztop - Hs * k / nz
        bell = sp['belly'] * (1 - (2 * x / W) ** 2) * math.sin(math.pi * (0.15 + 0.85 * k / nz) * 0.9)
        return (x, ym - bell + (3 if back else 0), z)

    def uv(i, k):
        return rpx(None, x0 + 8 + (W * i / nx) * PX, y0 + 8 + (Hs * k / nz) * PX, CLOTH_S)

    front = [[b.v(point(i, k, False)) for k in range(nz + 1)] for i in range(nx + 1)]
    back = [[b.v(point(i, k, True)) for k in range(nz + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for k in range(nz):
            b.face([front[i][k], front[i + 1][k], front[i + 1][k + 1], front[i][k + 1]],
                   [uv(i, k), uv(i + 1, k), uv(i + 1, k + 1), uv(i, k + 1)], M_CLOTH, part)
            b.face([back[i][k], back[i][k + 1], back[i + 1][k + 1], back[i + 1][k]],
                   [uv(i, k), uv(i, k + 1), uv(i + 1, k + 1), uv(i + 1, k)], M_CLOTH, part)
    rim = []
    rim += [(i, 0) for i in range(nx)] + [(nx, k) for k in range(nz)]
    rim += [(i, nz) for i in range(nx, 0, -1)] + [(0, k) for k in range(nz, 0, -1)]
    for (i, k), (i2, k2) in zip(rim, rim[1:] + rim[:1]):
        b.face([front[i][k], back[i][k], back[i2][k2], front[i2][k2]], [uv(i, k), uv(i, k), uv(i2, k2), uv(i2, k2)],
               M_CLOTH, part)
    if det['sigil']:
        zc = ztop - Hs * 0.48
        c = Vector((0.0, ym - sp['belly'] * math.sin(math.pi * (0.15 + 0.85 * 0.48) * 0.9), zc))
        mx0, my0, mx1, my1 = LAYOUT['cloth']['medal']
        prism(b, c + Vector((0, 1.5, 0)), Vector((0, -1, 0)), Vector((1, 0, 0)), sp['sigil_r'], det['sigil'], 6, 7,
              M_GLOW, ((mx0 + mx1) / 2, (my0 + my1) / 2), (mx1 - mx0) / 2 - 8, CLOTH_S, part=51)


def canopy(b, cp, det):
    x0, y0, x1, y1 = LAYOUT['cloth']['damask']
    half, eave, ridge = cp['half'], cp['eave'], cp['ridge']
    ya, yb = cp['y0'], cp['y1']
    p = {}
    for y in (ya, yb):
        p[(y, 'l')] = b.v((-half, y, eave))
        p[(y, 'r')] = b.v((half, y, eave))
        p[(y, 'c')] = b.v((0.0, y, ridge))
    slope = math.hypot(half, ridge - eave)

    def uvy(y, s):
        return rpx(None, x0 + 8 + (y - ya) * PX, y0 + 8 + s * PX, CLOTH_S)
    b.face([p[(ya, 'c')], p[(yb, 'c')], p[(yb, 'r')], p[(ya, 'r')]],
           [uvy(ya, 0), uvy(yb, 0), uvy(yb, slope), uvy(ya, slope)], M_CLOTH, 60)
    b.face([p[(ya, 'l')], p[(yb, 'l')], p[(yb, 'c')], p[(ya, 'c')]],
           [uvy(ya, slope), uvy(yb, slope), uvy(yb, 0), uvy(ya, 0)], M_CLOTH, 60)
    b.face([p[(ya, 'r')], p[(yb, 'r')], p[(yb, 'l')], p[(ya, 'l')]],
           [uvy(ya, 0), uvy(yb, 0), uvy(yb, 2 * half / 2), uvy(ya, 2 * half / 2)], M_CLOTH, 61)
    for y in (ya, yb):
        b.face([p[(y, 'l')], p[(y, 'c')], p[(y, 'r')]],
               [rpx(None, x0 + 8, y1 - 8, CLOTH_S), rpx(None, x0 + 8 + half * PX, y1 - 8 - (ridge - eave) * PX,
                                                          CLOTH_S), rpx(None, x0 + 8 + 2 * half * PX, y1 - 8,
                                                                         CLOTH_S)], M_CLOTH, 62)
    if det['valance']:
        dreg = (x0, y0, x1, y0 + 120)
        for sx in (-1, 1):
            box(b, (sx * half - 1.5, ya, eave - 26), (sx * half + 1.5, yb, eave), M_CLOTH, dreg, CLOTH_S, 63)
    g = region('gilt')
    for px in (-cp['post_x'], cp['post_x']):
        for py in cp['post_y']:
            tube(b, [(px, py, -4), (px, py, eave + 4)], [6, 6], 4, Vector((1, 0, 0)), M_TRIM, g, TRIM_S, 64)


def build_lod(name, kind, det):
    h = HULLS[kind]
    sp = SPEC[kind]
    b = Builder()
    L = h['length'] / 2
    build_hull(b, h, det, sp['gangplank'])
    mould = region('mould')
    # scroll posts
    for end, key, out in ((-1, 'prow', -1), (1, 'stern', 1)):
        ps = sp[key]
        base = (0.0, end * (L - 18), sheer_z(h, 1.0) - 46)
        path = scroll_path(base, out, ps['lean'], ps['turn'], ps['length'], det['post'])
        radii = [ps['r0'] + (ps['r1'] - ps['r0']) * (k / (len(path) - 1)) ** 0.8 for k in range(len(path))]
        tube(b, path, radii, det['post_sides'], Vector((1, 0, 0)), M_TRIM, mould, TRIM_S, 70)
    # mast, yard
    wood = region('wood')
    tube(b, [(0, sp['mast_y'], -30), (0, sp['mast_y'], sp['mast_h'])], [9, 6], det['rod'], Vector((1, 0, 0)),
         M_TRIM, wood, TRIM_S, 71)
    yw = sp['sail_w'] / 2 + 18
    tube(b, [(-yw, sp['mast_y'] - 8, sp['yard_z']), (yw, sp['mast_y'] - 8, sp['yard_z'])], [5, 5], det['rod'],
         Vector((0, 0, 1)), M_TRIM, wood, TRIM_S, 72)
    sail(b, sp, det)
    cl = LAYOUT['cloth']
    if det['pennant']:
        dx0, dy0, dx1, dy1 = cl['damask']
        z0 = sp['mast_h'] - 6
        tri = [(0, sp['mast_y'] + 6, z0), (0, sp['mast_y'] + 120, z0 - 22), (0, sp['mast_y'] + 6, z0 - 44)]
        f = [b.v((-1.5, y, z)) for _, y, z in tri]
        k = [b.v((1.5, y, z)) for _, y, z in tri]
        uv3 = [rpx(None, dx0 + 20, dy0 + 20, CLOTH_S), rpx(None, dx0 + 250, dy0 + 64, CLOTH_S),
               rpx(None, dx0 + 20, dy0 + 108, CLOTH_S)]
        b.face(f, uv3, M_CLOTH, 80)
        b.face(list(reversed(k)), list(reversed(uv3)), M_CLOTH, 80)
        for i in range(3):
            j = (i + 1) % 3
            b.face([f[i], f[j], k[j], k[i]], [uv3[i], uv3[j], uv3[j], uv3[i]], M_CLOTH, 80)
    medal = cl['medal']
    mc = ((medal[0] + medal[2]) / 2, (medal[1] + medal[3]) / 2)
    if det['orb']:
        sphere(b, Vector((0, sp['mast_y'], sp['mast_h'] + 12)), 13, det['orb'][0], det['orb'][1], M_GLOW, mc, CLOTH_S)
        if sp['canopy']:
            cp = sp['canopy']
            for y in (cp['y0'], cp['y1']):
                sphere(b, Vector((0, y, cp['ridge'] + 12)), 12, det['orb'][0], det['orb'][1], M_GLOW, mc, CLOTH_S)
    if det['medals']:
        for t in sp['medal_t']:
            for sgn in (-1, 1):
                zf = min(sheer_z(h, t) - 56, sheer_z(h, t) - 2)
                p, n = outer_point(h, t, zf - 34, sgn)
                prism(b, p, n, Vector((0, 1, 0)), 17 if kind == 'barge' else 14, det['medals'], 3, 6, M_GLOW, mc,
                      (medal[2] - medal[0]) / 2 - 8, CLOTH_S, part=90)
    if det['strip']:
        sx0, sy0, sx1, sy1 = cl['strip']
        ts = [t for t in stations(h, dict(det, gangway=False), False) if abs(t) <= 0.82]
        ts = ts[::2] if len(ts) > 6 else ts
        path = [(0.0, t * L, keel_z(h, t) - 3) for t in ts]
        tube(b, path, [10] * len(path), 4, Vector((1, 0, 0)), M_GLOW, (sx0, sy0 + 20, sx1, sy1 - 20), CLOTH_S, 91)
    if sp['canopy']:
        canopy(b, sp['canopy'], det)
    if sp['gangplank']:
        w = region('wood')
        box(b, (150, -36, -3), (L * 0 + h['beam'] / 2 + h['plank_reach'], 36, 4), M_TRIM, w, TRIM_S, 95)
    if det['crates'] and sp['crates']:
        for (cx, cy, s, hgt) in sp['crates']:
            box(b, (cx - s / 2, cy - s / 2, -2), (cx + s / 2, cy + s / 2, hgt), M_TRIM, region('panel'), TRIM_S, 96,
                top_reg=region('wood'))
    if sp.get('thwarts'):
        for ty in sp['thwarts']:
            t = ty / L
            w = profile(half_width(h, t), keel_z(h, t), sheer_z(h, t), solve_u(keel_z(h, t), sheer_z(h, t), 30))[0]
            box(b, (-w + 6, ty - 16, 22), (w - 6, ty + 16, 34), M_TRIM, region('wood'), TRIM_S, 97)
    bm = b.bm
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for e in bm.edges:
        parts = {f[b.part] for f in e.link_faces}
        if len(parts) > 1:
            e.smooth = False
        elif len(e.link_faces) == 2:
            n0, n1 = e.link_faces[0].normal, e.link_faces[1].normal
            if n0.dot(n1) < math.cos(math.radians(50)):
                e.smooth = False
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method='BEAUTY', ngon_method='BEAUTY')
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if 'part' in me.attributes:
        me.attributes.remove(me.attributes['part'])
    return me


def material(name, image, rough, glow=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = 0.0
    if glow:
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = 1.0
    return m


def build(model):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    kind = 'boat' if model == 'boat' else 'barge'
    tint = model
    name = 'xeen_deco_skyboat' if model == 'boat' else f'xeen_deco_skybarge_{model}'
    trim = bpy.data.images.load(os.path.join(TEX, 'skybarge_trim.png'))
    trim.name = 'skybarge_trim'
    cloth = bpy.data.images.load(os.path.join(TEX, f'skybarge_cloth_{tint}.png'))
    cloth.name = f'skybarge_cloth_{tint}'
    mats = [material('skybarge_trim', trim, 0.6), material(f'skybarge_cloth_{tint}', cloth, 0.85),
            material(f'skybarge_glow_{tint}', cloth, 0.5, glow=True)]
    objs, counts = [], []
    for level, det in enumerate(DETAIL):
        oname = name if level == 0 else f'{name}_LOD{level}'
        me = build_lod(oname, kind, det)
        for m in mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(oname, me)
        scene.collection.objects.link(ob)
        objs.append(ob)
        counts.append(sum(len(p.vertices) - 2 for p in me.polygons))
    co = [v.co for v in objs[0].data.vertices]
    lo = [min(c[i] for c in co) / U for i in range(3)]
    hi = [max(c[i] for c in co) / U for i in range(3)]
    info = {'name': name, 'tris': counts, 'min': [round(x, 1) for x in lo], 'max': [round(x, 1) for x in hi],
            'height': round(hi[2] - lo[2], 1)}
    print('MODEL', json.dumps(info))
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    out = os.path.join(PROJECT, 'work', f'{name}_raw.glb')
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_normals=True, export_animations=False, export_skins=False,
                              export_image_format='AUTO', export_apply=True, export_vertex_color='NONE')
    with open(os.path.join(PROJECT, 'work', f'{name}.json'), 'w') as f:
        json.dump(info, f)
    print('EXPORTED', out)


argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['all']
for m in (['fire', 'air', 'earth', 'water', 'boat'] if argv[0] == 'all' else argv):
    build(m)
