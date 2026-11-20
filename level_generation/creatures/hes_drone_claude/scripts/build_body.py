"""Hand-built drone body (v2, replaces the Meshy shell): work/body_v2.blend (object 'HDR') + work/clean_info.json.

Forward -Y, up +Z, the drone's left +X; metres; grounded so the tendon claws touch z 0. Built from surfaces of
revolution and swept tubes like the Hesper turrets (level_generation/props/hesper_decorations/scripts/
build_hard_surface.py), after the approved concept design/kreegan_world/concepts/monsters/fam_drones.png:
  casing     a rounded lozenge lathed about the long axis (32 sides, slightly narrower than tall), a pointed ceramic
             tail cap behind a gold band (not a copy of the lens)
  lens       gold front ring, dark segmented collar, gold rear ring, the orange dome (part 4, 24 sides)
  vents      a short drum under the belly: dark band with 12 glowing slots, a gold rim, a dark disc with a glowing
             nozzle
  overgrowth ONLY on the drone's right flank (-X) and the back: seven thick resin tubes swept over the casing, three
             chitin masses; the casing's texture there is resin skin (compose_v2.py)
  ribs       ONE row of seven curved bone spurs along the top centre line, curving back, largest in the middle
  hooks      two curved bone hooks under the tail, pointing back and down
  tendons    three short trailing cables (6 sides) from the rear underside, hanging back ~45-70 deg at rest and
             curving further back towards a small gold plug end (no claws: the drone flies, nothing stands)
Face attributes: 'part' (rig: 0 body, 1-3 tendon k, 4 lens dome) and 'mat' (texture class, MAT below). UV layers:
'TileUV' in metres (u around / across, v along), from which compose_v2.py samples the tiling Hesper materials, and
'UVMap' = TileUV packed into the atlas above the reserved strip v < 0.125 (lens dome planar in the strip's first
square; the tier gear's strip UVs are written by gear.py). Env SIDES (32 round the casing, collar and tail).
Shading (user turret review 2026-10-22): smooth normals over every curved piece (casing, collar rings, tail, vent drum,
plates, tubes, masses, ribs); hard edges (split vertices, so also UV island borders) only at real breaks: between
pieces, at a profile corner sharper than HARD_DEG or a material change (collar lips, the vent drum's rim steps,
a plate's gold border against its top)."""
import bpy, bmesh, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIDES = int(os.environ.get('SIDES', 32))        # round silhouette close up (user turret review 2026-10-22)
HARD_DEG = float(os.environ.get('HARD_DEG', 50.0))  # a profile corner sharper than this is a hard edge (split rings)
MAT = {'ceramic': 0, 'gold': 1, 'darkmetal': 2, 'lens': 3, 'ventband': 4, 'ventglow': 5, 'resin': 6, 'chitin': 7,
       'bone': 8, 'cable': 9}
SX = 0.94                         # casing width / height
rng = np.random.default_rng(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
bm = bmesh.new()
uv_atlas = bm.loops.layers.uv.new('UVMap')
uv_tile = bm.loops.layers.uv.new('TileUV')
L_PART = bm.faces.layers.int.new('part')
L_MAT = bm.faces.layers.int.new('mat')


HINT = [None]          # outward direction of the piece being built: a function of the face centre


def face(verts, uvs, mat, part=0, smooth=True, hint=None):
    """one face; its winding is turned so the normal points along the outward hint (HINT[0](centre) or `hint`)"""
    f = bm.faces.new(verts)
    f[L_PART] = part; f[L_MAT] = MAT[mat]; f.smooth = smooth
    for loop, uv in zip(f.loops, uvs):
        loop[uv_tile].uv = uv; loop[uv_atlas].uv = uv
    f.normal_update()
    h = hint if hint is not None else (HINT[0](f.calc_center_median()) if HINT[0] else None)
    if h is not None and f.normal.dot(h) < 0:
        f.normal_flip()
    return f


def tri_quad(a, b, c, d, ua, ub, uc, ud, mat, part=0, hint=None):
    """quad a-b-c-d as two triangles on the shorter diagonal"""
    if (a.co - c.co).length <= (b.co - d.co).length:
        face((a, b, c), (ua, ub, uc), mat, part, hint=hint); face((a, c, d), (ua, uc, ud), mat, part, hint=hint)
    else:
        face((a, b, d), (ua, ub, ud), mat, part, hint=hint); face((b, c, d), (ub, uc, ud), mat, part, hint=hint)


# ---------------------------------------------------------------- lathe about the Y axis
def ring_point(y, r, k, n=SIDES, sx=SX):
    a = 2 * math.pi * k / n           # angle from the top (+Z), positive toward the drone's right (-X)
    return Vector((-sx * r * math.sin(a), y, r * math.cos(a)))


def lathe(profile, mat_of_segment, n=SIDES, sx=SX, u_scale=None, close_front=False, close_back=False):
    """profile: [(y, r)] front to back. Each segment between consecutive points gets mat_of_segment[i]. TileUV: u =
    angle * u_scale (metres round a reference radius), v = arc length along the profile (metres)."""
    mk = lambda y, r: [bm.verts.new(ring_point(y, r, k, n, sx)) for k in range(n)] if r > 1e-6 else [bm.verts.new((0, y, 0))]
    rings = [mk(y, r) for y, r in profile]
    # hard edges at real breaks: a sharp profile corner gets a second ring, so its two segments share no vertices
    start = list(rings)
    for i in range(1, len(profile) - 1):
        d0 = np.subtract(profile[i], profile[i - 1]); d1 = np.subtract(profile[i + 1], profile[i])
        if np.linalg.norm(d0) < 1e-9 or np.linalg.norm(d1) < 1e-9:
            continue
        cosang = np.dot(d0, d1) / np.linalg.norm(d0) / np.linalg.norm(d1)
        sharp = math.degrees(math.acos(max(-1.0, min(1.0, cosang)))) > HARD_DEG
        if (sharp or mat_of_segment[i - 1] != mat_of_segment[i]) and profile[i][1] > 1e-6:
            start[i] = mk(*profile[i])
    rmax = max(r for _, r in profile)
    us = u_scale if u_scale is not None else 2 * math.pi * rmax
    arc = [0.0]
    for (y0, r0), (y1, r1) in zip(profile[:-1], profile[1:]):
        arc.append(arc[-1] + math.hypot(y1 - y0, r1 - r0))
    for i in range(len(profile) - 1):
        A, B = start[i], rings[i + 1]; m = mat_of_segment[i]
        va, vb = arc[i], arc[i + 1]
        dy, dr = profile[i + 1][0] - profile[i][0], profile[i + 1][1] - profile[i][1]
        if abs(dy) + abs(dr) < 1e-9:
            continue
        HINT[0] = lambda c, dy=dy, dr=dr: Vector((0, -dr, 0)) + Vector((c.x / sx, 0, c.z)).normalized() * dy
        for k in range(n):
            u0, u1 = us * k / n, us * (k + 1) / n
            if len(A) == 1:
                face((A[0], B[(k + 1) % n], B[k]), (((u0 + u1) / 2, va), (u1, vb), (u0, vb)), m)
            elif len(B) == 1:
                face((A[k], A[(k + 1) % n], B[0]), ((u0, va), (u1, va), ((u0 + u1) / 2, vb)), m)
            else:
                # outward winding: going +Y (back) along the profile, k toward the right
                tri_quad(A[k], A[(k + 1) % n], B[(k + 1) % n], B[k], (u0, va), (u1, va), (u1, vb), (u0, vb), m)
    HINT[0] = None
    return rings


# casing profile (y, r): front collar to the tail cap
COLLAR = [(-0.365, 0.088), (-0.371, 0.096), (-0.370, 0.106), (-0.362, 0.112), (-0.348, 0.112),   # rounded gold ring
          (-0.345, 0.118), (-0.318, 0.120),                                          # dark segmented collar
          (-0.316, 0.130), (-0.309, 0.138), (-0.295, 0.140), (-0.290, 0.150)]       # rounded gold rear ring
CASE = [(-0.290, 0.150), (-0.262, 0.170), (-0.215, 0.186), (-0.150, 0.196), (-0.040, 0.201),
        (0.070, 0.196), (0.160, 0.181), (0.220, 0.162), (0.268, 0.137), (0.300, 0.112)]
TAIL = [(0.300, 0.112), (0.304, 0.104), (0.315, 0.102), (0.320, 0.094),            # rounded gold tail band
        (0.345, 0.076), (0.366, 0.050), (0.380, 0.024), (0.386, 0.0)]                  # pointed ceramic cap
lathe(COLLAR, ['gold'] * 4 + ['darkmetal'] * 2 + ['gold'] * 4, u_scale=2 * math.pi * 0.13)
lathe(CASE, ['ceramic'] * (len(CASE) - 1), u_scale=2 * math.pi * 0.2)
lathe(TAIL, ['ceramic'] * 7, u_scale=2 * math.pi * 0.1)
case_y = np.array([p[0] for p in CASE]); case_r = np.array([p[1] for p in CASE])


def radius(y):
    return float(np.interp(y, case_y, case_r))


def surface(y, a, lift=0.0):
    """point on the casing at length y and angle a (0 top, + toward the right flank), lifted along the normal"""
    r = radius(y)
    n = Vector((-math.sin(a) / SX, 0.0, math.cos(a))).normalized()
    return Vector((-SX * r * math.sin(a), y, r * math.cos(a))) + n * lift, n


# ---------------------------------------------------------------- lens dome (part 4)
R, YB, DEPTH = 0.090, -0.360, 0.042
LN = 24
lens_rings = []
for rr in (1.0, 0.86, 0.62, 0.36):
    yy = YB - DEPTH * math.sqrt(max(0.0, 1 - rr * rr))
    lens_rings.append([bm.verts.new((-R * rr * math.sin(2 * math.pi * k / LN), yy, R * rr * math.cos(2 * math.pi * k / LN)))
                       for k in range(LN)])
inner = [bm.verts.new((-0.14 * R * math.sin(2 * math.pi * (k + 0.5) / (LN // 2)), YB - DEPTH * 0.99,
                       0.14 * R * math.cos(2 * math.pi * (k + 0.5) / (LN // 2)))) for k in range(LN // 2)]
apex = bm.verts.new((0, YB - DEPTH, 0))
puv = lambda v: (v.co.x, v.co.z)                                                    # planar front TileUV
HINT[0] = lambda c: c - Vector((0, YB + 0.06, 0))
for A, B in zip(lens_rings[:-1], lens_rings[1:]):
    for k in range(LN):
        a, b, c, d = A[k], B[k], B[(k + 1) % LN], A[(k + 1) % LN]
        tri_quad(a, b, c, d, puv(a), puv(b), puv(c), puv(d), 'lens', 4)
o = lens_rings[-1]; H2 = LN // 2
for k in range(H2):
    face((o[2 * k], inner[k], o[2 * k + 1]), (puv(o[2 * k]), puv(inner[k]), puv(o[2 * k + 1])), 'lens', 4)
    tri_quad(o[2 * k + 1], inner[k], inner[(k + 1) % H2], o[(2 * k + 2) % LN],
             puv(o[2 * k + 1]), puv(inner[k]), puv(inner[(k + 1) % H2]), puv(o[(2 * k + 2) % LN]), 'lens', 4)
    face((inner[k], apex, inner[(k + 1) % H2]), (puv(inner[k]), puv(apex), puv(inner[(k + 1) % H2])), 'lens', 4)
HINT[0] = None
# lens rim fill: from the dome's rim to the gold front ring's inner edge (r 0.088 at y -0.365 is in front of the
# dome's base at y -0.36, so the gold ring overlaps the rim: no gap)


# ---------------------------------------------------------------- vent drum under the belly (axis Z)
YV = -0.03
ZB = -radius(YV)
VR, VN = 0.094, 24


def drum_ring(r, z, n=VN):
    return [bm.verts.new((r * math.cos(2 * math.pi * k / n), YV + r * math.sin(2 * math.pi * k / n), z)) for k in range(n)]


def strip_rings(rings, mats, u_scale, inward=False):
    """rings of the drum, consecutive strips smooth unless their (radius, z) directions meet sharper than HARD_DEG"""
    arc = [0.0]
    for A, B in zip(rings[:-1], rings[1:]):
        arc.append(arc[-1] + (A[0].co - B[0].co).length)
    rz = [(math.hypot(R_[0].co.x, R_[0].co.y - YV), R_[0].co.z) for R_ in rings]
    dirs = [np.subtract(rz[i + 1], rz[i]) for i in range(len(rings) - 1)]
    start = list(rings)
    for i in range(1, len(rings) - 1):
        c = np.dot(dirs[i - 1], dirs[i]) / np.linalg.norm(dirs[i - 1]) / np.linalg.norm(dirs[i])
        if math.degrees(math.acos(max(-1.0, min(1.0, c)))) > HARD_DEG:
            start[i] = [bm.verts.new(v.co) for v in rings[i]]
    for i, (A, B) in enumerate(zip(start[:-1], rings[1:])):
        ra = math.hypot(A[0].co.x, A[0].co.y - YV); rb = math.hypot(B[0].co.x, B[0].co.y - YV)
        dr, dz = rb - ra, B[0].co.z - A[0].co.z
        HINT[0] = lambda c, dr=dr, dz=dz: Vector((c.x, c.y - YV, 0)).normalized() * (-dz) + Vector((0, 0, dr))
        for k in range(VN):
            u0, u1 = u_scale * k / VN, u_scale * (k + 1) / VN
            a, b, c, d = A[k], A[(k + 1) % VN], B[(k + 1) % VN], B[k]
            if inward:
                tri_quad(a, d, c, b, (u0, arc[i]), (u0, arc[i + 1]), (u1, arc[i + 1]), (u1, arc[i]), mats[i])
            else:
                tri_quad(a, b, c, d, (u0, arc[i]), (u1, arc[i]), (u1, arc[i + 1]), (u0, arc[i + 1]), mats[i])
    HINT[0] = None


us = 2 * math.pi * VR
drum = [drum_ring(VR, ZB + 0.025), drum_ring(VR, ZB - 0.022), drum_ring(VR + 0.008, ZB - 0.024),
        drum_ring(VR + 0.008, ZB - 0.032), drum_ring(VR - 0.006, ZB - 0.034), drum_ring(0.052, ZB - 0.034),
        drum_ring(0.048, ZB - 0.028)]
strip_rings(drum, ['ventband', 'gold', 'gold', 'gold', 'ventband', 'ventband'], us, inward=True)
noz = [bm.verts.new((0.022 * math.cos(2 * math.pi * k / 8), YV + 0.022 * math.sin(2 * math.pi * k / 8), ZB - 0.026))
       for k in range(8)]
last = [bm.verts.new(v.co) for v in drum[-1]]          # the flat nozzle disc: hard against the drum's inner wall
HINT[0] = lambda c: Vector((0, 0, -1))
for k in range(8):   # nozzle disc (glow): 24 -> 8 transition, then an 8-fan
    for j in range(3):
        kk = 3 * k + j
        a, b = last[kk], last[(kk + 1) % VN]
        if j < 2:
            face((a, noz[k], b), ((a.co.x, a.co.y), (noz[k].co.x, noz[k].co.y), (b.co.x, b.co.y)), 'ventglow')
        else:
            tri_quad(a, noz[k], noz[(k + 1) % 8], b, (a.co.x, a.co.y), (noz[k].co.x, noz[k].co.y),
                     (noz[(k + 1) % 8].co.x, noz[(k + 1) % 8].co.y), (b.co.x, b.co.y), 'ventglow')
nc = bm.verts.new((0, YV, ZB - 0.025))
for k in range(8):
    face((noz[k], nc, noz[(k + 1) % 8]), ((noz[k].co.x, noz[k].co.y), (0, YV), (noz[(k + 1) % 8].co.x, noz[(k + 1) % 8].co.y)), 'ventglow')
# 12 glowing slots, 1.5 mm proud of the band
for s in range(12):
    a0, a1 = 2 * math.pi * (s + 0.2) / 12, 2 * math.pi * (s + 0.8) / 12
    rr = VR + 0.0015
    q = [bm.verts.new((rr * math.cos(a), YV + rr * math.sin(a), z)) for a, z in
         ((a0, ZB - 0.004), (a1, ZB - 0.004), (a1, ZB - 0.019), (a0, ZB - 0.019))]
    tri_quad(q[0], q[3], q[2], q[1], (0, 0.015), (0, 0), (0.03, 0), (0.03, 0.015), 'ventglow',
             hint=Vector((math.cos((a0 + a1) / 2), math.sin((a0 + a1) / 2), 0)))
HINT[0] = None


def _seg_dist(c, a, b):
    d = b - a; t = max(0.0, min(1.0, (c - a).dot(d) / max(d.dot(d), 1e-12)))
    return (c - (a + d * t)).length


# ---------------------------------------------------------------- swept tubes
def sweep(points, radii, mat, sides=6, part=0, cap_start=False, cap_end=False, u_scale=None, side_dir=None,
          aspect=1.0, keel=1.0):
    """tube along points with per-point radii; TileUV u = around (metres at the mean radius), v = arc length.
    side_dir fixes the section's side axis (else parallel transport); aspect scales the section along it; keel
    stretches the half of the section on the -up side (a rib's leading edge) and shrinks the other half"""
    pts = [Vector(p) for p in points]; n = len(pts)
    rings = []
    prev_side = None
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        if side_dir is not None:
            side = (Vector(side_dir) - d * Vector(side_dir).dot(d)).normalized()
        else:
            side = (prev_side - d * prev_side.dot(d)).normalized() if prev_side is not None else d.orthogonal().normalized()
        prev_side = side; up = d.cross(side)
        ring = []
        for k in range(sides):
            ca, sa = math.cos(2 * math.pi * k / sides), math.sin(2 * math.pi * k / sides)
            sa *= keel if sa < 0 else 1.0 / keel
            ring.append(bm.verts.new(p + (side * ca * aspect + up * sa) * radii[i]))
        rings.append(ring)
    arc = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        arc.append(arc[-1] + (b - a).length)
    usc = u_scale if u_scale is not None else 2 * math.pi * float(np.mean(radii))

    def radial(c):
        best = min(range(n - 1), key=lambda i: _seg_dist(c, pts[i], pts[i + 1]))
        a, b = pts[best], pts[best + 1]; d = b - a
        t = max(0.0, min(1.0, (c - a).dot(d) / max(d.dot(d), 1e-12)))
        return c - (a + d * t)
    HINT[0] = radial
    for i in range(n - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(sides):
            u0, u1 = usc * k / sides, usc * (k + 1) / sides
            tri_quad(A[k], A[(k + 1) % sides], B[(k + 1) % sides], B[k], (u0, arc[i]), (u1, arc[i]),
                     (u1, arc[i + 1]), (u0, arc[i + 1]), mat, part)
    HINT[0] = None
    if cap_end:
        tip = rings[-1]
        c = bm.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1] * 0.6)
        for k in range(sides):
            face((tip[k], tip[(k + 1) % sides], c), ((usc * k / sides, arc[-1]), (usc * (k + 1) / sides, arc[-1]),
                                                     (usc * (k + 0.5) / sides, arc[-1] + radii[-1])), mat, part,
                 hint=pts[-1] - pts[-2])
    if cap_start:
        top = rings[0]
        c = bm.verts.new(pts[0] - (pts[1] - pts[0]).normalized() * radii[0] * 0.5)
        for k in range(sides):
            face((top[(k + 1) % sides], top[k], c), ((usc * (k + 1) / sides, 0), (usc * k / sides, 0),
                                                     (usc * (k + 0.5) / sides, -radii[0])), mat, part,
                 hint=pts[0] - pts[1])
    return rings


WIGGLE = 0.12


def surf_curve(ctrl, rt, samples=10):
    """a tube lying on the casing: control (y, angle) pairs, interpolated; the ends dip into the casing"""
    cy = np.array([c[0] for c in ctrl]); ca = np.array([c[1] for c in ctrl])
    t = np.linspace(0, 1, samples); tc = np.linspace(0, 1, len(ctrl))
    ys = np.interp(t, tc, cy); as_ = np.interp(t, tc, ca) + WIGGLE * np.sin(t * math.pi * 3 + cy[0] * 30) * np.sin(t * math.pi)
    k = np.array([0.25, 0.5, 0.25])                       # smooth the polyline (keep the ends)
    for _ in range(3):
        ys[1:-1] = np.convolve(ys, k, 'same')[1:-1]; as_[1:-1] = np.convolve(as_, k, 'same')[1:-1]
    pts, rad = [], []
    for i, (y, a) in enumerate(zip(ys, as_)):
        end = min(i, samples - 1 - i)
        lift = rt * (0.55 if end >= 2 else (0.1 if end == 1 else -0.5))
        p, _ = surface(float(y), float(a), lift)
        pts.append(p); rad.append(rt * (0.75 + 0.25 * min(1.0, end / 2)))
    return pts, rad


# resin tubes: right flank (angle +0.5 .. +2.5) from mid-length back, and arcs over the back from the left flank
TUBES = [([(-0.21, 1.15), (-0.05, 0.95), (0.12, 0.7), (0.27, 0.45)], 0.030),
         ([(-0.17, 1.65), (0.0, 1.45), (0.16, 1.2), (0.29, 0.95)], 0.028),
         ([(-0.10, 2.15), (0.05, 1.95), (0.2, 1.75), (0.29, 1.6)], 0.026),
         ([(0.17, -1.45), (0.15, -0.6), (0.14, 0.25), (0.16, 1.0), (0.19, 1.9)], 0.030),
         ([(0.235, -1.7), (0.22, -0.8), (0.215, 0.1), (0.23, 0.9), (0.25, 2.1)], 0.026),
         ([(0.275, -1.3), (0.27, -0.4), (0.27, 0.5), (0.28, 1.4)], 0.022),
         ([(-0.02, 0.45), (0.09, 0.3), (0.2, 0.05), (0.27, -0.25)], 0.022)]
for ctrl, rt in TUBES:
    pts, rad = surf_curve(ctrl, rt)
    sweep(pts, rad, 'resin', sides=6)

# chitin masses: low ellipsoids half sunk into the casing (right flank and back)
MASSES = [(0.20, 1.25, (0.07, 0.085, 0.04)), (0.02, 1.75, (0.055, 0.07, 0.035)), (0.25, -0.55, (0.06, 0.06, 0.033))]
for y, a, (ra, rb, rc) in MASSES:
    c, n = surface(y, a, 0.0)
    ty = Vector((0, 1, 0)); ta = n.cross(ty).normalized()
    NU, NV = 8, 5
    grid = []
    for j in range(NV + 1):
        lat = -0.35 + (math.pi / 2 + 0.35) * j / NV                 # from inside the casing up to the top
        row = []
        for i in range(NU):
            lon = 2 * math.pi * i / NU
            wob = 1 + 0.12 * math.sin(3 * lon + 1.3 * j + y * 20)
            p = c + (ta * ra * math.cos(lon) * math.cos(lat) + ty * rb * math.sin(lon) * math.cos(lat)) * wob \
                + n * rc * math.sin(lat)
            row.append(p)
        grid.append(row)
    vs = [[bm.verts.new(p) for p in row] for row in grid[:-1]]
    HINT[0] = lambda q, c=c: q - c
    top = bm.verts.new(grid[-1][0])
    usc = 2 * math.pi * (ra + rb) / 2
    for j in range(NV - 1):
        for i in range(NU):
            u0, u1 = usc * i / NU, usc * (i + 1) / NU
            tri_quad(vs[j][i], vs[j][(i + 1) % NU], vs[j + 1][(i + 1) % NU], vs[j + 1][i],
                     (u0, j * 0.02), (u1, j * 0.02), (u1, (j + 1) * 0.02), (u0, (j + 1) * 0.02), 'chitin')
    for i in range(NU):
        face((vs[-1][i], vs[-1][(i + 1) % NU], top), ((usc * i / NU, 0.1), (usc * (i + 1) / NU, 0.1),
                                                       (usc * (i + 0.5) / NU, 0.12)), 'chitin')
    HINT[0] = None


# ---------------------------------------------------------------- raised ceramic plates (gold-edged) on the casing
def plate(y0, y1, a0, a1, lift=0.008, nu=6, nv=4):
    """a patch of the casing lifted along its normal, with a bevelled gold border down into the casing"""
    us_ = 2 * math.pi * 0.2
    grid = [[surface(y0 + (y1 - y0) * j / nv, a0 + (a1 - a0) * i / nu, lift)[0] for i in range(nu + 1)] for j in range(nv + 1)]
    vs = [[bm.verts.new(p) for p in row] for row in grid]
    tuv = lambda i, j: ((a0 + (a1 - a0) * i / nu) / (2 * math.pi) * us_, y0 + (y1 - y0) * j / nv)
    HINT[0] = lambda c: surface(c.y, -math.atan2(c.x / SX, c.z))[1]
    for j in range(nv):
        for i in range(nu):
            tri_quad(vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i], tuv(i, j), tuv(i + 1, j), tuv(i + 1, j + 1),
                     tuv(i, j + 1), 'ceramic')
    # border: the perimeter loop lowered into the casing, one gold band
    loop = [(i, 0) for i in range(nu)] + [(nu, j) for j in range(nv)] + [(i, nv) for i in range(nu, 0, -1)] + \
           [(0, j) for j in range(nv, 0, -1)]
    lower = {}
    for (i, j) in loop:
        y = y0 + (y1 - y0) * j / nv; a = a0 + (a1 - a0) * i / nu
        lower[(i, j)] = bm.verts.new(surface(y, a, -0.004)[0])
    c = sum((v.co for row in vs for v in row), Vector()) / ((nu + 1) * (nv + 1))
    s_acc = 0.0
    top = {(i, j): bm.verts.new(vs[j][i].co) for (i, j) in loop}       # the border's own top edge: a hard lip
    for q in range(len(loop)):
        p0, p1 = loop[q], loop[(q + 1) % len(loop)]
        a, b = top[p0], top[p1]
        la, lb = lower[p0], lower[p1]
        d = (b.co - a.co).length
        out = ((a.co + b.co) / 2 - c)
        tri_quad(la, lb, b, a, (s_acc, 0), (s_acc + d, 0), (s_acc + d, 0.012), (s_acc, 0.012), 'gold',
                 hint=out.normalized() + surface((a.co.y + b.co.y) / 2, -math.atan2(a.co.x / SX, a.co.z))[1] * 0.3)
        s_acc += d
    HINT[0] = None


PLATES = [(-0.262, 0.03, -1.95, -0.62), (-0.262, -0.15, -0.42, 0.42), (-0.10, 0.12, -2.75, -2.15),
          (-0.262, -0.14, 0.62, 1.7), (0.05, 0.25, -1.25, -0.45)]
for y0, y1, a0, a1 in PLATES:
    plate(y0, y1, a0, a1)


# ---------------------------------------------------------------- one row of bone ribs along the top
# each a curved blade: flared root sunk into the casing, flattened sideways (aspect), a keeled leading edge, the
# upper half hooking back harder than a cone
RIBS = [(-0.10, 0.070), (-0.045, 0.095), (0.015, 0.115), (0.075, 0.125), (0.135, 0.118), (0.195, 0.100), (0.250, 0.075)]
for y, h in RIBS:
    base, n = surface(y, 0.0, -0.012)
    pts, rad = [], []
    for t, r in ((0.0, 0.031), (0.16, 0.022), (0.45, 0.0155), (0.72, 0.0085), (0.92, 0.0035)):
        pts.append(base + Vector((0, 1.05 * h * t ** 2.1, h * t * (1 - 0.22 * t) + 0.012 * min(1.0, t / 0.16))))
        rad.append(r * (h / 0.11) ** 0.35)
    sweep(pts, rad, 'bone', sides=6, cap_end=True, side_dir=(1, 0, 0), aspect=0.6, keel=1.25)
# two hooks under the tail, pointing back and down
for side in (1, -1):
    base, n = surface(0.275, side * 2.55, -0.01)
    pts, rad = [], []
    for t in (0.0, 0.35, 0.65, 0.9):
        pts.append(base + Vector((-side * 0.012 * t, 0.06 * t ** 0.8, -0.05 * t + 0.03 * t * t)))
        rad.append(0.017 * (1 - t) ** 0.8 + 0.002)
    sweep(pts, rad, 'bone', sides=5, cap_end=True)

bm.normal_update()
me = bpy.data.meshes.new('HDR'); bm.to_mesh(me); bm.free()
obj = bpy.data.objects.new('HDR', me); bpy.context.scene.collection.objects.link(obj)

# ---------------------------------------------------------------- trailing cables, part 1..3, mat cable/gold
# rooted on the rear underside behind the vent drum; each leaves the casing at ANG0 back from straight down and bends
# to ANG1 at its end, so at rest it trails behind and above the vent drum's bottom (the casing and vents stay the
# lowest solid point); a short gold plug closes the end
bvh = BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())
ROOTS = [(0.05, 0.185), (0.0, 0.205), (-0.05, 0.185)]
TENDON_LEN, R0, R1, TS, SEG = 0.10, 0.013, 0.008, 6, 0.0167
ANG0, ANG1 = math.radians(46), math.radians(72)
bm = bmesh.new(); bm.from_mesh(me)
uv_atlas = bm.loops.layers.uv['UVMap']; uv_tile = bm.loops.layers.uv['TileUV']
L_PART = bm.faces.layers.int['part']; L_MAT = bm.faces.layers.int['mat']
info = []
for k, (x, y) in enumerate(ROOTS, start=1):
    hit = bvh.ray_cast(Vector((x, y, 0.0)), Vector((0, 0, -1)))
    z0 = hit[0].z
    n = int(round(TENDON_LEN / SEG)); out = math.copysign(1.0, x) if abs(x) > 1e-6 else 0.0
    pts = [Vector((x, y, z0 + 0.012))]
    for i in range(n):
        a = ANG0 + (ANG1 - ANG0) * (i + 0.5) / n
        pts.append(pts[-1] + Vector((out * 0.12, math.sin(a), -math.cos(a))).normalized() * (TENDON_LEN / n))
    rad = [R0 + (R1 - R0) * i / n for i in range(n + 1)]
    d = (pts[-1] - pts[-2]).normalized()
    plug = [pts[-1] - d * 0.003, pts[-1] + d * 0.002, pts[-1] + d * 0.012, pts[-1] + d * 0.016]
    sweep(pts, rad, 'cable', sides=TS, part=k, cap_start=True)
    sweep(plug, [R1, R1 * 1.45, R1 * 1.45, R1 * 1.1], 'gold', sides=TS, part=k, cap_end=True)
    info.append({'tendon': k, 'root': [x, y, z0], 'points': [list(map(float, p)) for p in pts],
                 'claw': [list(map(float, c)) for c in plug[2:]]})     # 'claw': the chain's end (the plug)
bm.normal_update(); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = True
# consistent outward winding (the swept pieces are open or closed shells; recalc per connected piece)
bpy.context.view_layer.objects.active = obj; obj.select_set(True)
# ground: the tendon claws at z 0
zmin = min(v.co.z for v in me.vertices)
for v in me.vertices:
    v.co.z -= zmin
for t in info:
    t['root'][2] -= zmin
    for p in t['points'] + t['claw']:
        p[2] -= zmin

# ---------------------------------------------------------------- atlas UVs: pack TileUV islands above the strip
STRIP = 0.125
me.uv_layers.active = me.uv_layers['UVMap']
part = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', part)
bpy.ops.object.mode_set(mode='EDIT')
bmx = bmesh.from_edit_mesh(me); uva = bmx.loops.layers.uv['UVMap']
for f in bmx.faces:
    f.select = bool(part[f.index] != 4)
bmesh.update_edit_mesh(me)
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.pack_islands(margin=0.004, rotate=True, scale=True)
bmx = bmesh.from_edit_mesh(me); uva = bmx.loops.layers.uv['UVMap']
lens = np.array([[l.vert.co.x, l.vert.co.z] for f in bmx.faces if part[f.index] == 4 for l in f.loops])
lo, hi = lens.min(0), lens.max(0); span = (hi - lo).max()
for f in bmx.faces:
    for l in f.loops:
        if part[f.index] == 4:
            x, z = (l.vert.co.x - lo[0]) / span, (l.vert.co.z - lo[1]) / span
            l[uva].uv = (0.008 + (1 - x) * (STRIP - 0.016), 0.008 + z * (STRIP - 0.016))
        else:
            u, v = l[uva].uv
            l[uva].uv = (u, STRIP + v * (1 - STRIP))
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
co = np.array([tuple(v.co) for v in me.vertices])
json.dump({'scale': 1.0, 'zmin': zmin, 'tendons': info, 'bbox': [co.min(0).tolist(), co.max(0).tolist()],
           'vent': {'y': YV, 'z_bottom': ZB - 0.034 - zmin}},
          open(os.path.join(HERE, 'work', 'clean_info.json'), 'w'), indent=1)
mats = np.zeros(len(me.polygons), int); me.attributes['mat'].data.foreach_get('value', mats)
print('BODY tris', len(me.polygons), {k: int((mats == v).sum()) for k, v in MAT.items()},
      'bbox', co.min(0).round(3), co.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'body_v2.blend'))
print('SAVED body_v2.blend')
