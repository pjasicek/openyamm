"""Blender (headless): build one MM7 flower clump with three LODs from its atlas and export work/<id>/plant_export.glb
(+ plant.blend). Meshes Plant, Plant_LOD1, Plant_LOD2; one MASK material 'Plant' (double-sided) with extras
openyamm_wind 0.02, openyamm_specular 0.1, openyamm_translucency 0.3; COLOR_0 = occlusion x per-part tint.

Parts (see README "Construction"):
  blade   grass/sword leaf as a curved strip (3 segments at LOD0, 2 at LOD1) over a blade strip region (B0/B1)
  head    flat or cupped cone mapped from above with a face-on painted flower (S slots); optional stem strip
  bloom   double flower (rose, cabbage rose, peony): lathed ball wrapped in a petal band (R0) and a rosette cap
  lily    two stacked cones (outer and inner petal stars)
  iris    three standards and three falls as bent two-segment petals on a stalk
  spike   foxglove: tapered lathe wrapped in bells (T0) plus two crossed silhouette cards (T1), tinted by COLOR_0
  leaf    broad leaf as a card folded along its midrib (two cards, 4 triangles), optional curl row (8 triangles)
  card    foliage card tangent to a shell (leaf and moss mounds)
  star    three crossed upright cards (tuft cards for the far levels and fill)
LOD1/LOD2 keep a seeded subset of each kind (enlarged to hold coverage) with fewer segments.
Usage: blender --background --python build_plant.py -- <id>"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import atlas_of, dims, region_uv, seed, work

SID = sys.argv[sys.argv.index('--') + 1]
AID = atlas_of(SID)
WORK = work(SID)
ATLAS_DIR = work(AID)
W, H = dims(SID)
RW = W / 2
rng = np.random.default_rng(seed(SID, 3))
bpy.ops.wm.read_factory_settings(use_empty=True)
UP = Vector((0, 0, 1))
CENTRE = Vector((0, 0, H * 0.35))
PAINT_R = 0.40          # painted head radius in slot units (paint.R)


def frame(axis):
    axis = Vector(axis).normalized()
    helper = UP if abs(axis.z) < 0.95 else Vector((1, 0, 0))
    a = helper.cross(axis).normalized()
    return a, axis.cross(a), axis


def ruv(region, s, t):
    u0, v0, u1, v1 = region_uv(region)
    return (u0 + s * (u1 - u0), v0 + t * (v1 - v0))


def occlusion(p, floor=0.32):
    height = max(p.z, 0.0) / H
    radial = min(Vector((p.x, p.y)).length / RW, 1.0)
    return floor + (1 - floor) * min(height * 1.5 + 0.25 * radial, 1.0) ** 0.85


class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.normals, self.colours = [], []

    def face(self, points, uvs, normals, colours):
        verts = [self.bm.verts.new(p) for p in points]
        f = self.bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, uvs):
            loop[self.uv].uv = (u, 1.0 - v)          # atlas coordinates are image space (v down)
        self.normals += [Vector(n).normalized() for n in normals]
        self.colours += [tuple(c) + (1.0,) if len(c) == 3 else tuple(c) for c in colours]

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)


def shade(p, tint, floor=0.32, extra=1.0):
    o = occlusion(p, floor) * extra
    return [min(o * t, 1.0) for t in tint]


def soft_normal(own, p, weight=0.5, centre=None):
    outward = (p - (CENTRE if centre is None else centre))
    outward = outward.normalized() if outward.length > 1e-6 else UP
    if own.dot(outward) < 0:
        own = -own
    return own * (1 - weight) + outward * weight


# --- part emitters ---------------------------------------------------------------------------------------------------

def emit_blade(mesh, b, segs, grow):
    if b['length'] < 0.45 * max(H, 0.8) and segs > 2:
        segs -= 1                       # short blades need one segment less for the same curvature
    base, az = b['base'], b['azimuth']
    horiz = Vector((math.cos(az), math.sin(az), 0))
    side0 = Vector((-math.sin(az), math.cos(az), 0))
    pts, tangents = [base.copy()], []
    for i in range(segs):
        t = (i + 0.5) / segs
        e = b['e0'] + (b['e1'] - b['e0']) * t ** b.get('curve', 1.0)
        d = horiz * math.cos(e) + UP * math.sin(e)
        tangents.append(d)
        pts.append(pts[-1] + d * b['length'] / segs)
    tangents.append(tangents[-1])
    width = b['width'] * grow
    rows = []
    for i, p in enumerate(pts):
        d = tangents[max(i - 1, 0)] if i == len(pts) - 1 else tangents[i]
        side = side0 * math.cos(b['twist']) + d.cross(side0).normalized() * math.sin(b['twist'])
        w = width * (0.75 if i == 0 else (0.55 if i == len(pts) - 1 else 1.0))
        rows.append((p - side * w * 0.5, p + side * w * 0.5, side, d))
    for i in range(segs):
        (l0, r0, s0, d0), (l1, r1, s1, d1) = rows[i], rows[i + 1]
        t0, t1 = 1.0 - i / segs, 1.0 - (i + 1) / segs
        n0, n1 = d0.cross(s0), d1.cross(s1)
        quad = [l0, r0, r1, l1]
        mesh.face(quad, [ruv(b['region'], 0, t0), ruv(b['region'], 1, t0), ruv(b['region'], 1, t1),
                         ruv(b['region'], 0, t1)],
                  [soft_normal(n, q, 0.45) for n, q in zip((n0, n0, n1, n1), quad)],
                  [shade(q, b.get('tint', (1, 1, 1)), extra=b.get('dark', 1.0)) for q in quad])


def emit_head(mesh, h, segs, grow, rings=1):
    a, bb, n = frame(h['axis'])
    k = max(segs, 5)
    r = h['radius'] * grow / math.cos(math.pi / k)
    ur = PAINT_R / math.cos(math.pi / k)
    turn = h['turn']
    cup = h.get('cup', 0.12)
    centre = h['centre'] - n * cup * h['radius']
    if rings == 1:
        profile = [(0.0, 0.0), (1.0, 1.0)]
    elif h.get('profile') == 'rim':      # lily pad: nearly flat, the outer quarter turned up
        profile = [(0.0, 0.0), (0.72, 0.15), (1.0, 1.0)]
    else:
        profile = [(0.0, 0.0), (0.45, 0.62), (1.0, 1.0)]

    def point(ring, j):
        f, lift = profile[ring]
        ang = turn + 2 * math.pi * j / k
        radial = a * math.cos(ang) + bb * math.sin(ang)
        p = centre + radial * r * f + n * cup * h['radius'] * lift
        uv = ruv(h['region'], 0.5 + math.cos(ang) * ur * f, 0.5 + math.sin(ang) * ur * f)
        return p, uv, n + radial * f * 0.35
    tint = h.get('tint', (1, 1, 1))
    for ring in range(len(profile) - 1):
        for j in range(k):
            quad = [point(ring, j), point(ring, j + 1), point(ring + 1, j + 1), point(ring + 1, j)]
            if ring == 0:
                quad = quad[1:]
            mesh.face([q[0] for q in quad], [q[1] for q in quad], [q[2] for q in quad],
                      [shade(q[0], tint, floor=0.6) for q in quad])


def emit_stem(mesh, bottom, top, width, crossed, tint=(1, 1, 1)):
    axis = (top - bottom).normalized()
    a, b, _ = frame(axis)
    for side in ((a,) if not crossed else (a, b)):
        pts = [bottom - side * width, bottom + side * width, top + side * width, top - side * width]
        uvs = [ruv('R1', 0.03, 1.0), ruv('R1', 0.09, 1.0), ruv('R1', 0.09, 0.0), ruv('R1', 0.03, 0.0)]
        mesh.face(pts, uvs, [soft_normal(side.cross(axis), p) for p in pts], [shade(p, tint) for p in pts])


def lathe(mesh, base, axis, profile, segs, uvf, tint, turn, floor=0.5):
    """profile: list of (height, radius) bottom to top; uvf(ring, j) -> uv."""
    a, b, n = frame(axis)
    ring_pts = []
    for hgt, rad in profile:
        row = []
        for j in range(segs + 1):
            ang = turn + 2 * math.pi * j / segs
            radial = a * math.cos(ang) + b * math.sin(ang)
            row.append((base + n * hgt + radial * rad, radial))
        ring_pts.append(row)
    for i in range(len(profile) - 1):
        for j in range(segs):
            idx = [(i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)]
            pts = [ring_pts[r][c][0] for r, c in idx]
            if profile[i + 1][1] < 1e-6:
                idx, pts = idx[:3], pts[:3]
            mesh.face(pts, [uvf(r, c) for r, c in idx], [ring_pts[r][c][1] + n * 0.3 for r, c in idx],
                      [shade(p, tint, floor=floor) for p in pts])


def emit_bloom(mesh, bl, segs, grow):
    r = bl['radius'] * grow
    side = [(0.0, 0.45 * r), (0.45 * r, 0.95 * r), (0.95 * r, 1.0 * r)]     # side band, bottom to top
    tint = bl.get('tint', (1, 1, 1))
    lathe(mesh, bl['base'], bl['axis'], side, segs,
          lambda ring, j: ruv('R0', j / segs, 1.0 - ring / (len(side) - 1) * 0.92), tint, bl['turn'])
    k = segs
    ur = PAINT_R / math.cos(math.pi / k)
    cap = [(0.85 * r, 1.04 * r / math.cos(math.pi / k)), (1.22 * r, 0.62 * r / math.cos(math.pi / k)),
           (1.36 * r, 0.0)]
    frac = [1.0, 0.6, 0.0]
    a, b, n = frame(bl['axis'])
    region = bl['cap']
    for i in range(len(cap) - 1):
        for j in range(k):
            pts, uvs, nrm = [], [], []
            for rr, jj in ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)):
                ang = bl['turn'] + 2 * math.pi * jj / k
                radial = a * math.cos(ang) + b * math.sin(ang)
                pts.append(bl['base'] + n * cap[rr][0] + radial * cap[rr][1])
                uvs.append(ruv(region, 0.5 + math.cos(ang) * ur * frac[rr], 0.5 + math.sin(ang) * ur * frac[rr]))
                nrm.append(n + radial * frac[rr] * 0.8)
            if i == len(cap) - 2:
                pts, uvs, nrm = pts[:3], uvs[:3], nrm[:3]
            mesh.face(pts, uvs, nrm, [shade(p, tint, floor=0.6) for p in pts])


def emit_lily(mesh, ly, segs, grow):
    r = ly['radius'] * grow
    a, b, n = frame(ly['axis'])
    k = max(segs, 5)
    c = 1 / math.cos(math.pi / k)
    for region, rim_r, rim_h, mid_h in (('S0', 1.0, 0.16, 0.02), ('S1', 0.62, 0.55, 0.10)):
        centre = ly['centre'] + n * mid_h * r
        turn = ly['turn'] + (0.5 if region == 'S1' else 0.0)
        for j in range(k):
            pts, uvs, nrm = [centre], [ruv(region, 0.5, 0.5)], [n]
            for jj in (j, j + 1):
                ang = turn + 2 * math.pi * jj / k
                radial = a * math.cos(ang) + b * math.sin(ang)
                pts.append(ly['centre'] + radial * rim_r * r * c + n * rim_h * r)
                uvs.append(ruv(region, 0.5 + math.cos(ang) * PAINT_R * c, 0.5 + math.sin(ang) * PAINT_R * c))
                nrm.append(n + radial * 0.5)
            mesh.face(pts, uvs, nrm, [shade(p, (1, 1, 1), floor=0.7) for p in pts])


def bent_petal(mesh, root, path, widths, side, region, tint):
    """Two-segment petal along `path` (3 points from the root), widths at each point, `side` the width direction."""
    rows = [(p - side * w * 0.5, p + side * w * 0.5) for p, w in zip(path, widths)]
    for i in range(len(rows) - 1):
        t0, t1 = 1.0 - i / (len(rows) - 1), 1.0 - (i + 1) / (len(rows) - 1)
        d = (path[i + 1] - path[i]).normalized()
        nrm = d.cross(side)
        pts = [rows[i][0], rows[i][1], rows[i + 1][1], rows[i + 1][0]]
        mesh.face(pts, [ruv(region, 0, t0), ruv(region, 1, t0), ruv(region, 1, t1), ruv(region, 0, t1)],
                  [soft_normal(nrm, p, 0.3) for p in pts], [shade(p, tint, floor=0.6) for p in pts])


def emit_iris(mesh, ir, grow, lod):
    P, L = ir['centre'], ir['size'] * grow
    count = 3
    for k in range(count):
        ang = ir['turn'] + 2 * math.pi * k / count
        out = Vector((math.cos(ang), math.sin(ang), 0))
        side = Vector((-math.sin(ang), math.cos(ang), 0))
        if lod < 2:      # standards: up and curling back in
            path = [P, P + UP * 0.5 * L + out * 0.28 * L, P + UP * 0.95 * L + out * 0.08 * L]
            bent_petal(mesh, P, path, [0.25 * L, 0.62 * L, 0.5 * L], side, 'S0', (1, 1, 1))
        ang2 = ang + math.pi / count
        out2 = Vector((math.cos(ang2), math.sin(ang2), 0))
        side2 = Vector((-math.sin(ang2), math.cos(ang2), 0))
        path = [P, P + out2 * 0.5 * L + UP * 0.18 * L, P + out2 * 0.85 * L - UP * 0.35 * L]
        bent_petal(mesh, P, path, [0.25 * L, 0.7 * L, 0.6 * L], side2, 'S1', (1, 1, 1))
    if lod == 2:         # one crossed pair standing in for the standards
        for k in range(2):
            ang = ir['turn'] + math.pi / 2 * k
            side = Vector((-math.sin(ang), math.cos(ang), 0))
            pts = [P - side * 0.35 * L, P + side * 0.35 * L, P + side * 0.35 * L + UP * L, P - side * 0.35 * L + UP * L]
            mesh.face(pts, [ruv('S3', 0, 1), ruv('S3', 1, 1), ruv('S3', 1, 0), ruv('S3', 0, 0)],
                      [soft_normal(side.cross(UP), p) for p in pts], [shade(p, (1, 1, 1), floor=0.6) for p in pts])


def emit_spike(mesh, sp, segs, grow, lod):
    """Foxglove: a thin lathed core (bells facing out, T0) inside crossed silhouette cards (T1), tinted per spike."""
    z0, length, r0 = sp['z0'], sp['length'], sp['radius'] * grow
    base = sp['base'] + UP * z0
    rings = 3 if lod == 0 else 2
    core = 0.5 * r0
    profile = [(t / rings * length * 0.95, max(core * (1 - t / rings) ** 0.8, 0.004)) for t in range(rings + 1)]
    tint = sp['tint']
    if lod < 2:
        lathe(mesh, base, UP, profile, segs, lambda ring, j: ruv('T0', j / segs, 1.0 - profile[ring][0] / length),
              tint, sp['turn'], floor=0.45)
    if lod == 0:                           # rows of single bell cards round the core, buds crossed at the tip
        rows = 9
        for i in range(rows):
            t = i / (rows - 1)
            z = length * (0.04 + 0.8 * t)
            s = r0 * (1.4 - 0.75 * t)
            count = 5 if t < 0.6 else (4 if t < 0.85 else 3)
            for j in range(count):
                ang = sp['turn'] + 2 * math.pi * j / count + i * 0.7
                out = Vector((math.cos(ang), math.sin(ang), 0))
                right = Vector((-math.sin(ang), math.cos(ang), 0))
                down = (-UP * math.cos(math.radians(30)) + out * math.sin(math.radians(30))).normalized()
                top = base + UP * (z + s * 0.25) + out * s * 0.3
                w, hgt = s * 0.95, s * 1.15
                pts = [top + down * hgt - right * w * 0.5, top + down * hgt + right * w * 0.5, top + right * w * 0.5,
                       top - right * w * 0.5]
                region = ('S0', 'S1')[(i + j) % 2]
                nrm = right.cross(down).normalized()
                mesh.face(pts, [ruv(region, 0, 1), ruv(region, 1, 1), ruv(region, 1, 0), ruv(region, 0, 0)],
                          [soft_normal(nrm, p, 0.4, base + UP * length * 0.5) for p in pts],
                          [shade(p, tint, floor=0.5) for p in pts])
        tip = base + UP * length * 0.78
        for k in range(2):
            ang = sp['turn'] + math.pi / 2 * k
            side = Vector((math.cos(ang), math.sin(ang), 0)) * r0 * 0.45
            pts = [tip - side, tip + side, tip + side + UP * length * 0.24, tip - side + UP * length * 0.24]
            mesh.face(pts, [ruv('S3', 0, 1), ruv('S3', 1, 1), ruv('S3', 1, 0), ruv('S3', 0, 0)],
                      [soft_normal(side.cross(UP).normalized(), p, 0.6) for p in pts],
                      [shade(p, (1, 1, 1)) for p in pts])
        emit_stem(mesh, sp['base'], base + UP * 0.05, 0.008 * W, True)
        return
    cards = 3 if lod < 2 else 2
    for k in range(cards):
        ang = sp['turn'] + math.pi * k / cards
        side = Vector((math.cos(ang), math.sin(ang), 0))
        wd = r0 * 2.6
        pts = [base - side * wd * 0.5, base + side * wd * 0.5, base + side * wd * 0.5 + UP * length,
               base - side * wd * 0.5 + UP * length]
        mesh.face(pts, [ruv('T1', 0, 1), ruv('T1', 1, 1), ruv('T1', 1, 0), ruv('T1', 0, 0)],
                  [soft_normal(side.cross(UP), p, 0.6) for p in pts], [shade(p, tint, floor=0.5) for p in pts])
    emit_stem(mesh, sp['base'], base + UP * 0.05, 0.008 * W, lod == 0)


def emit_leaf(mesh, lf, grow, fold=True):
    B, A, N = lf['base'], lf['axis'].normalized(), lf['normal']
    N = (N - A * N.dot(A)).normalized()
    S = A.cross(N).normalized()
    L, w = lf['length'] * grow, lf['width'] * grow
    f = lf.get('fold', 0.18) if fold else 0.0
    curl = lf.get('curl', 0.0)
    rows = [(0.0, 0.0), (1.0, 0.0)] if not curl else [(0.0, 0.0), (0.55, curl * 0.35), (1.0, curl)]
    region, tint = lf['region'], lf.get('tint', (1, 1, 1))
    grid = []
    for t, c in rows:
        centre = B + A * L * t - N * c * L
        grid.append([centre - S * w * 0.5 - N * f * w, centre, centre + S * w * 0.5 - N * f * w])
    for i in range(len(rows) - 1):
        t0, t1 = 1.0 - rows[i][0], 1.0 - rows[i + 1][0]
        cols = ((0, 1, 0.0, 0.5), (1, 2, 0.5, 1.0)) if fold else ((0, 2, 0.0, 1.0),)
        for c0, c1, s0, s1 in cols:
            pts = [grid[i][c0], grid[i][c1], grid[i + 1][c1], grid[i + 1][c0]]
            own = (pts[1] - pts[0]).cross(pts[3] - pts[0]).normalized()
            if own.dot(N) < 0:
                own = -own
            mesh.face(pts, [ruv(region, s0, t0), ruv(region, s1, t0), ruv(region, s1, t1), ruv(region, s0, t1)],
                      [soft_normal(own, p, 0.4, lf.get('centre')) for p in pts],
                      [shade(p, tint, extra=lf.get('dark', 1.0)) for p in pts])


def emit_card(mesh, cd, grow):
    base, right, up = cd['base'], cd['right'] * grow, cd['up'] * grow
    pts = [base - right * 0.5, base + right * 0.5, base + right * 0.5 + up, base - right * 0.5 + up]
    region = cd['region']
    own = right.cross(up).normalized()
    mesh.face(pts, [ruv(region, 0, 1), ruv(region, 1, 1), ruv(region, 1, 0), ruv(region, 0, 0)],
              [soft_normal(own, p, 0.55) for p in pts],
              [shade(p, cd.get('tint', (1, 1, 1)), extra=cd.get('dark', 1.0)) for p in pts])


def emit_star(mesh, st, grow):
    for k in range(st.get('cards', 3)):
        ang = st['turn'] + math.pi * k / st.get('cards', 3)
        right = Vector((math.cos(ang), math.sin(ang), 0)) * st['width'] * grow
        lean = Vector((-math.sin(ang), math.cos(ang), 0)) * st.get('lean', 0.0)
        up = (UP + lean).normalized() * st['height'] * grow
        emit_card(mesh, {'base': st['base'], 'right': right, 'up': up, 'region': st['regions'][k % 2],
                         'tint': st.get('tint', (1, 1, 1)), 'dark': st.get('dark', 1.0)}, 1.0)


# --- layout helpers --------------------------------------------------------------------------------------------------

def disc_point(radius):
    a = rng.uniform(0, 2 * math.pi)
    r = radius * math.sqrt(rng.uniform())
    return Vector((math.cos(a) * r, math.sin(a) * r, 0.0))


def grass(parts, tufts, per_tuft, radius, length, elev0=(62, 86), elev1=(-5, 40), width=(0.05, 0.075),
          regions=('B0', 'B1'), centre_boost=1.3, outward=0.9, keep_bias=0.0, ring=None, curve=1.0, centre_lift=30):
    """Tufts scattered in a disc; their blades fan out, longer near the centre (mound)."""
    for t in range(tufts):
        if ring is None:
            p = disc_point(radius)
        else:
            a = 2 * math.pi * (t + rng.uniform(-0.3, 0.3)) / tufts
            r = rng.uniform(*ring)
            p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        rel = p.length / max(radius if ring is None else ring[1], 1e-6)
        out_az = math.atan2(p.y, p.x) if p.length > 0.05 * W else rng.uniform(0, 2 * math.pi)
        for k in range(per_tuft):
            az = out_az + rng.normal(0, outward) if rel > 0.2 else rng.uniform(0, 2 * math.pi)
            ln = rng.uniform(*length) * (1 + (centre_boost - 1) * (1 - rel))
            parts.append({'kind': 'blade', 'base': p + Vector(rng.normal(0, 0.025 * W, 3)) * Vector((1, 1, 0)),
                          'azimuth': az, 'e0': math.radians(rng.uniform(*elev0)),
                          'e1': math.radians(rng.uniform(*elev1) + centre_lift * (1 - rel)), 'length': ln,
                          'width': rng.uniform(*width),
                          'twist': rng.normal(0, 0.35), 'region': regions[int(rng.integers(0, len(regions)))],
                          'keep': rng.uniform() + keep_bias + 0.3 * (ln / length[1]), 'curve': curve})


def stars(parts, count, radius, height, width, regions=('T0', 'T1'), lods=(2,), centre_first=True, **kw):
    for k in range(count):
        if centre_first and k == 0:
            p = Vector((0, 0, 0))
        else:
            a = 2 * math.pi * k / max(count - 1, 1) + rng.uniform(-0.3, 0.3)
            p = Vector((math.cos(a), math.sin(a), 0)) * radius * rng.uniform(0.75, 1.05)
        parts.append(dict({'kind': 'star', 'base': p, 'turn': rng.uniform(0, math.pi), 'width': width,
                           'height': height * (1.12 if k == 0 and centre_first else rng.uniform(0.8, 0.95)),
                           'regions': regions, 'lods': set(lods), 'keep': 2.0 - k * 0.01,
                           'lean': 0.12}, **kw))


def heads(parts, positions, regions, axis_up=0.75, stem=True, cup=0.15, stem_width=0.006, tint=(1, 1, 1),
          rings=1, keep_bias=0.0):
    for p, radius in positions:
        out = Vector((p.x, p.y, 0))
        out = out.normalized() if out.length > 1e-3 else Vector((math.cos(rng.uniform(0, 6.3)),
                                                                 math.sin(rng.uniform(0, 6.3)), 0))
        axis = out * (1 - axis_up) + UP * axis_up + Vector(rng.normal(0, 0.12, 3))
        parts.append({'kind': 'head', 'centre': p, 'axis': axis, 'radius': radius,
                      'region': regions[int(rng.integers(0, len(regions)))], 'turn': rng.uniform(0, 6.3),
                      'cup': cup, 'tint': tint, 'rings': rings, 'keep': 1.0 + radius + keep_bias + rng.uniform() * 0.2})
        if stem:
            bottom = Vector((p.x * 0.55, p.y * 0.55, 0.0))
            parts.append({'kind': 'stem', 'bottom': bottom, 'top': p - axis.normalized() * radius * 0.1,
                          'width': stem_width * W / 1.5, 'keep': 1.0 + radius + keep_bias})


def shell_point(d, centre, rx, rz):
    return centre + Vector((d.x * rx, d.y * rx, d.z * rz))


def dome_point(d, centre, rx, rz, n=2.6):
    """Point of a superquadric mound (|h/rx|^n + |z/rz|^n = 1, n > 2: a flatter top and steeper sides than an
    ellipsoid, like the sprites' wide mounds) in direction d."""
    h = math.hypot(d.x, d.y)
    k = (h ** n + abs(d.z) ** n) ** (-1.0 / n)
    return centre + Vector((d.x * k * rx, d.y * k * rx, d.z * k * rz))


def dome_normal(d, rx, rz, n=2.6):
    h = max(math.hypot(d.x, d.y), 1e-6)
    k = (h ** n + abs(d.z) ** n) ** (-1.0 / n)
    gh = (h * k) ** (n - 1) / rx
    gz = math.copysign(abs(d.z * k) ** (n - 1), d.z) / rz
    return Vector((d.x / h * gh, d.y / h * gh, gz)).normalized()


def direction(lowest, highest=1.0):
    while True:
        d = Vector(rng.normal(0, 1, 3)).normalized()
        if lowest < d.z <= highest:
            return d


def tangent_card(centre, normal, size, region, keep, dark=1.0, ground=0.03):
    right = Vector((-normal.y, normal.x, 0.0))
    if right.length < 0.25:
        ang = rng.uniform(0, 2 * math.pi)
        right = Vector((math.cos(ang), math.sin(ang), 0.0))
    right.normalize()
    up = normal.cross(right).normalized()
    if up.z < 0:
        up = -up
    base = centre - up * size * 0.5
    if base.z < ground:
        base.z = 0.0
    return {'kind': 'card', 'base': base, 'right': right * size, 'up': up * size, 'region': region, 'keep': keep,
            'dark': dark}


def leaves_around(parts, centre, count, length, width, region, droop=(-0.1, 0.35), curl=0.0, keep=0.5, tint=(1, 1, 1),
                  fold=0.18, regions=None):
    """Broad leaves radiating from below a bloom (rose leaves, peony cups)."""
    turn = rng.uniform(0, 6.3)
    for k in range(count):
        ang = turn + 2 * math.pi * k / count + rng.normal(0, 0.2)
        out = Vector((math.cos(ang), math.sin(ang), 0))
        rise = rng.uniform(*droop)
        axis = out * math.cos(rise) + UP * math.sin(rise)
        normal = UP - axis * UP.dot(axis)
        parts.append({'kind': 'leaf', 'base': centre + out * length * 0.08, 'axis': axis, 'normal': normal,
                      'length': length * rng.uniform(0.85, 1.1), 'width': width * rng.uniform(0.85, 1.1),
                      'region': regions[k % len(regions)] if regions else region, 'curl': curl, 'fold': fold,
                      'centre': centre - UP * length * 0.5,
                      'keep': keep + rng.uniform() * 0.5, 'tint': tint})


# --- species layouts (metres; W, H from the sprite) -----------------------------------------------------------------

parts = []
PLAN = {   # kind: per LOD (fraction kept, grow, segments)
    'blade': [(1.0, 1.0, 4), (0.5, 1.35, 2), (0.0, 1.0, 1)],
    'head': [(1.0, 1.0, 10), (1.0, 1.04, 7), (1.0, 1.08, 5)],
    'stem': [(1.0, 1.0, 2), (1.0, 1.0, 1), (0.0, 1.0, 1)],
    'bloom': [(1.0, 1.0, 8), (1.0, 1.03, 6), (1.0, 1.06, 5)],
    'lily': [(1.0, 1.0, 10), (1.0, 1.04, 7), (1.0, 1.08, 5)],
    'iris': [(1.0, 1.0, 0), (1.0, 1.04, 0), (1.0, 1.1, 0)],
    'spike': [(1.0, 1.0, 6), (1.0, 1.04, 5), (1.0, 1.08, 4)],
    'leaf': [(1.0, 1.0, 1), (0.7, 1.15, 1), (0.4, 1.35, 0)],
    'card': [(1.0, 1.0, 0), (0.6, 1.18, 0), (0.35, 1.4, 0)],
    'star': [(1.0, 1.0, 0), (1.0, 1.0, 0), (1.0, 1.0, 0)],
}

MEADOW = dict(width=(0.065, 0.09), elev0=(62, 87), elev1=(-45, 5), centre_boost=1.35, curve=1.3, centre_lift=45)


def ring_positions(count, r_range, z_range, size_range, centre=None):
    pos = [] if centre is None else [centre]
    for k in range(count):
        a = 2 * math.pi * k / count + rng.uniform(-0.3, 0.3)
        r = rng.uniform(*r_range) * W
        pos.append((Vector((math.cos(a) * r, math.sin(a) * r, rng.uniform(*z_range) * H)), rng.uniform(*size_range)))
    return pos


def bloom_group(parts, c, radius, cap, leaves, leaf_len, leaf_w, regions, droop, curl, fold=0.18, lean=0.5,
                stem_w=0.012):
    out = Vector((c.x, c.y, 0))
    out = out.normalized() if out.length > 1e-3 else Vector((1, 0, 0))
    axis = (out * lean + UP).normalized()
    parts.append({'kind': 'bloom', 'base': c, 'axis': axis, 'radius': radius, 'cap': cap, 'turn': rng.uniform(0, 6),
                  'keep': 3.0})
    leaves_around(parts, c + axis * radius * 0.15, leaves, leaf_len, leaf_w, None, regions=regions, droop=droop,
                  curl=curl, keep=1.2, fold=fold)
    parts.append({'kind': 'stem', 'bottom': Vector((c.x * 0.5, c.y * 0.5, 0)), 'top': c, 'width': stem_w,
                  'keep': 3.0})


if SID == 'flower01':
    grass(parts, 22, 6, 0.28 * W, (0.78, 1.12), **MEADOW)
    pos = ring_positions(6, (0.2, 0.34), (0.55, 0.8), (0.17, 0.23), (Vector((0.0, 0.0, 0.92 * H)), 0.31))
    heads(parts, pos, ('S0', 'S1', 'S2'), axis_up=0.4, cup=0.18, rings=2)
    stars(parts, 7, 0.28 * W, 0.85 * H, 0.36 * W, lods=(2,))
elif SID == 'flower02':
    grass(parts, 22, 6, 0.28 * W, (0.75, 1.05), **dict(MEADOW, elev0=(66, 88), elev1=(-35, 15)))
    pos = ring_positions(6, (0.14, 0.32), (0.5, 0.8), (0.2, 0.25), (Vector((0.03 * W, 0.0, 0.9 * H)), 0.27))
    heads(parts, pos, ('S0', 'S1', 'S2'), axis_up=0.45, cup=0.3, rings=2)
    stars(parts, 7, 0.28 * W, 0.85 * H, 0.36 * W, lods=(2,))
elif SID == 'flower03':
    grass(parts, 22, 6, 0.26 * W, (0.7, 1.0), **dict(MEADOW, width=(0.075, 0.1)))
    for k in range(3):
        a = 2 * math.pi * k / 3 + rng.uniform(-0.2, 0.2)
        c = Vector((math.cos(a) * 0.27 * W, math.sin(a) * 0.27 * W, 0.64 * H))
        bloom_group(parts, c, 0.19, 'S0', 5, 0.42, 0.30, ('S1', 'S2'), (0.0, 0.8), 0.3)
    stars(parts, 7, 0.28 * W, 0.85 * H, 0.36 * W, lods=(2,))
elif SID == 'flower04':
    grass(parts, 20, 6, 0.32 * W, (0.5, 0.78), **dict(MEADOW, elev1=(-40, 10), centre_lift=20))
    spots = [(0.02, 0.80, 0.27), (0.27, 0.60, 0.25), (0.30, 0.52, 0.24), (0.26, 0.66, 0.25), (0.20, 0.40, 0.22)]
    for k, (r, z, s) in enumerate(spots):
        a = 2 * math.pi * k / 4 + rng.uniform(-0.25, 0.25)
        c = Vector((math.cos(a) * r * W, math.sin(a) * r * W, z * H))
        bloom_group(parts, c, s, ('S0', 'S1')[k % 2], 6, 0.5, 0.36, ('S2', 'S3'), (-0.1, 0.9), 0.35, stem_w=0.016)
    for k in range(10):    # low leaves filling the base
        a = rng.uniform(0, 6.3)
        p = Vector((math.cos(a), math.sin(a), 0)) * rng.uniform(0.05, 0.25) * W + UP * rng.uniform(0.15, 0.35) * H
        leaves_around(parts, p, 1, 0.5, 0.34, None, regions=('S2', 'S3'), droop=(-0.1, 0.5), curl=0.3, keep=0.6)
    stars(parts, 6, 0.26 * W, 0.6 * H, 0.42 * W, lods=(2,))
elif SID == 'flower05':
    spots = [(0.03, 0.80, 0.20), (0.25, 0.70, 0.19), (0.28, 0.60, 0.17), (0.22, 0.74, 0.18), (0.30, 0.52, 0.16),
             (0.15, 0.86, 0.16), (0.32, 0.45, 0.15)]
    first = len(parts)
    for k, (r, z, s) in enumerate(spots):   # a tight cluster of blooms on short stems, cupped in leaves
        a = 2 * math.pi * k / 7 + rng.uniform(-0.25, 0.25)
        c = Vector((math.cos(a) * r * 0.85 * W, math.sin(a) * r * 0.85 * W, z * 0.76 * H))
        bloom_group(parts, c, s * 1.15, ('S0', 'S1')[k % 2], 5, 0.44, 0.36, ('S2', 'S3'), (0.25, 0.65), -0.2,
                    fold=0.3, lean=0.6 * r / 0.3)
    for p in parts[first:]:
        p['spread'] = False                  # the width comes from the leaves round the base, not the cluster
    for k in range(12):    # big olive leaves rising from the ground round the edge
        a = 2 * math.pi * k / 12 + rng.uniform(-0.2, 0.2)
        out = Vector((math.cos(a), math.sin(a), 0))
        parts.append({'kind': 'leaf', 'base': out * 0.2 * W, 'axis': out + UP * rng.uniform(0.35, 0.9),
                      'normal': UP, 'length': rng.uniform(0.5, 0.62), 'width': rng.uniform(0.4, 0.5),
                      'region': ('S2', 'S3')[k % 2], 'curl': 0.3, 'fold': 0.3, 'keep': 1.0 + rng.uniform(),
                      'centre': Vector((0, 0, -1.0))})
    stars(parts, 6, 0.16 * W, 0.52 * H, 0.32 * W, lods=(0, 1, 2), dark=0.8)
elif SID == 'flower06':
    grass(parts, 8, 7, 0.3 * W, (0.78, 1.0), width=(0.075, 0.1), elev0=(78, 89), elev1=(-5, 35), curve=1.5,
          centre_boost=1.0, ring=(0.15 * W, 0.24 * W), outward=0.55, centre_lift=0)
    grass(parts, 10, 3, 0.2 * W, (0.3, 0.5), width=(0.06, 0.08), elev0=(45, 70), elev1=(-20, 10), keep_bias=-0.3,
          centre_lift=0)
    for k in range(16):   # dark leaf mound under the flowers
        d = direction(-0.1, 0.9)
        cpt = shell_point(d, Vector((0, 0, 0.06 * H)), 0.22 * W, 0.28 * H)
        parts.append(tangent_card(cpt, Vector((d.x, d.y, d.z * 1.5)).normalized(), rng.uniform(0.45, 0.6), 'T1',
                                  1.0 + rng.uniform()))
    pos = ring_positions(9, (0.12, 0.27), (0.3, 0.46), (0.18, 0.24), (Vector((0.0, 0.0, 0.5 * H)), 0.23))
    heads(parts, pos, ('S0', 'S1'), axis_up=0.45, cup=0.1, stem=False)
    stars(parts, 8, 0.25 * W, 0.95 * H, 0.36 * W, regions=('T0', 'T0'), lods=(2,), centre_first=False)
elif SID == 'flower07':
    grass(parts, 12, 5, 0.30 * W, (0.42, 0.65), width=(0.07, 0.1), elev0=(55, 82), elev1=(-45, 0), centre_boost=0.9,
          curve=1.3, centre_lift=0)
    tints = [(1.0, 1.0, 1.0), (1.0, 0.36, 0.30), (0.92, 0.22, 0.40), (0.66, 0.48, 0.95)]
    for k, tint in enumerate(tints):
        a = 2 * math.pi * k / 4 + 0.4
        base = Vector((math.cos(a), math.sin(a), 0)) * 0.17 * W
        parts.append({'kind': 'spike', 'base': base, 'z0': 0.14 * H, 'length': rng.uniform(0.82, 0.86) * H,
                      'radius': 0.1 * W, 'tint': tint, 'turn': rng.uniform(0, 6), 'keep': 3.0})
    stars(parts, 5, 0.3 * W, 0.5 * H, 0.4 * W, regions=('S2', 'S2'), lods=(2,), centre_first=False)
elif SID == 'flower08':
    grass(parts, 16, 6, 0.26 * W, (0.6, 0.85), width=(0.045, 0.062), elev0=(74, 89), elev1=(10, 55), centre_boost=1.15,
          curve=1.3, centre_lift=15)
    for k in range(6):
        a = 2 * math.pi * k / 6 + rng.uniform(-0.25, 0.25)
        r = rng.uniform(0.18, 0.33) * W if k else 0.02 * W
        z = rng.uniform(0.55, 0.75) * H if k else 0.76 * H
        c = Vector((math.cos(a) * r, math.sin(a) * r, z))
        parts.append({'kind': 'iris', 'centre': c, 'size': rng.uniform(0.25, 0.29), 'turn': rng.uniform(0, 6),
                      'keep': 3.0})
        parts.append({'kind': 'stem', 'bottom': Vector((c.x * 0.4, c.y * 0.4, 0)), 'top': c, 'width': 0.009,
                      'keep': 3.0})
    stars(parts, 9, 0.22 * W, 0.62 * H, 0.36 * W, lods=(2,))
elif SID == 'flower09':
    grass(parts, 18, 6, 0.22 * W, (0.45, 0.72), **dict(MEADOW, width=(0.05, 0.07), centre_lift=40))
    first = len(parts)
    pos = ring_positions(6, (0.2, 0.31), (0.5, 0.68), (0.19, 0.23), (Vector((0.0, 0.0, 0.8 * H)), 0.25))
    heads(parts, pos, ('S0', 'S1'), axis_up=0.5, cup=0.2, rings=2)
    for p in parts[first:]:
        p['spread'] = False                  # the heads keep the sprite's spread; the fit narrows the grass
    stars(parts, 8, 0.24 * W, 0.68 * H, 0.42 * W, lods=(2,))
elif SID == 'flower10':
    shell_c, rx, rz = Vector((0, 0, 0.1 * H)), 0.46 * W, 0.62 * H
    for k in range(100):  # moss cards over the dome, a dark inner layer
        d = direction(-0.35)
        parts.append(tangent_card(dome_point(d, shell_c, rx, rz), dome_normal(d, rx, rz),
                                  rng.uniform(0.36, 0.44), ('T0', 'T1')[k % 2], 1.0 + rng.uniform()))
    for k in range(14):
        d = direction(-0.3)
        parts.append(tangent_card(dome_point(d, shell_c, rx * 0.72, rz * 0.72), dome_normal(d, rx, rz), 0.62,
                                  ('T0', 'T1')[k % 2],
                                  0.8 + rng.uniform(), dark=0.55))
    pos = []
    for k in range(46):
        d = direction(-0.25)
        p = dome_point(d, shell_c, rx * 1.12, rz * 1.1)
        p.z = max(p.z, 0.12)
        pos.append((p, rng.uniform(0.13, 0.165)))
    heads(parts, pos, ('S0', 'S1', 'S2'), axis_up=0.35, cup=0.12, stem=False)
    grass(parts, 3, 3, 0.3 * W, (0.4, 0.55), width=(0.04, 0.05), elev0=(65, 80), elev1=(20, 40), keep_bias=-0.5,
          centre_lift=0)
elif SID in ('flower11', 'flower12'):
    shell_c, rx, rz = Vector((0, 0, 0.05 * H)), 0.46 * W, 0.6 * H
    for k in range(92):
        d = direction(-0.35)
        parts.append(tangent_card(dome_point(d, shell_c, rx, rz), dome_normal(d, rx, rz),
                                  rng.uniform(0.38, 0.46), ('T0', 'T1')[k % 2], 1.0 + rng.uniform()))
    for k in range(6):    # the cap
        d = direction(0.75)
        parts.append(tangent_card(dome_point(d, shell_c, rx, rz), dome_normal(d, rx, rz),
                                  0.5, ('T0', 'T1')[k % 2], 1.5 + rng.uniform()))
    for k in range(10):
        d = direction(-0.3)
        parts.append(tangent_card(dome_point(d, shell_c, rx * 0.7, rz * 0.7), dome_normal(d, rx, rz), 0.55,
                                  ('T0', 'T1')[k % 2],
                                  0.8 + rng.uniform(), dark=0.55))
    for k in range(14):   # single leaves breaking the outline
        d = direction(0.0, 0.8)
        p = dome_point(d, shell_c, rx * 0.95, rz * 0.95)
        out = Vector((d.x, d.y, 0)).normalized()
        parts.append({'kind': 'leaf', 'base': p, 'axis': out + UP * rng.uniform(0.3, 1.0), 'normal': UP + out * 0.3,
                      'length': rng.uniform(0.22, 0.28), 'width': 0.12, 'region': 'S2', 'fold': 0.2,
                      'keep': 0.8 + rng.uniform()})
    pos = []
    for k in range(34):
        d = direction(-0.15)
        pos.append((dome_point(d, shell_c, rx * 1.18, rz * 1.16), rng.uniform(0.09, 0.12)))
    heads(parts, pos, ('S0', 'S1'), axis_up=0.4, cup=0.1, stem=False)
    if SID == 'flower11':
        grass(parts, 12, 4, 0.5 * W, (0.3, 0.42), width=(0.045, 0.06), elev0=(66, 86), elev1=(5, 45),
              ring=(0.27 * W, 0.35 * W), outward=0.5, centre_boost=1.0, curve=1.3, centre_lift=0)
        stars(parts, 5, 0.36 * W, 0.45 * H, 0.3 * W, regions=('S3', 'S3'), lods=(2,), centre_first=False)
elif SID in ('flower13', 'flower16'):
    low = SID == 'flower16'
    mound = 0.42 * H if low else 0.36 * H
    for k in range(26):
        d = direction(0.15)
        r = 0.36 * W * math.sqrt(1 - d.z ** 2) * rng.uniform(0.5, 1.0)
        a = math.atan2(d.y, d.x)
        p = Vector((math.cos(a) * r, math.sin(a) * r, mound * (1 - (r / (0.45 * W)) ** 2) + 0.02))
        tilt = Vector((math.cos(a), math.sin(a), 0)) * (r / (0.45 * W)) * 0.9
        parts.append({'kind': 'head', 'centre': p, 'axis': UP + tilt + Vector(rng.normal(0, 0.15, 3)),
                      'radius': rng.uniform(0.17, 0.22), 'region': ('S2', 'S3')[k % 2], 'turn': rng.uniform(0, 6.3),
                      'cup': 0.2, 'profile': 'rim', 'keep': 1.0 + rng.uniform(), 'rings': 2})
    for k, (r, s) in enumerate(((0.0, 0.2), (0.25, 0.17), (0.28, 0.15), (0.22, 0.16), (0.3, 0.12), (0.18, 0.13),
                                (0.32, 0.11))):
        a = 2 * math.pi * k / 6 + rng.uniform(-0.3, 0.3)
        rr = r * W
        z = mound * (1 - (rr / (0.45 * W)) ** 2) + 0.05
        parts.append({'kind': 'lily', 'centre': Vector((math.cos(a) * rr, math.sin(a) * rr, z)),
                      'axis': UP + Vector((math.cos(a), math.sin(a), 0)) * (0.45 + 1.5 * rr / W), 'radius': s * 1.25,
                      'turn': rng.uniform(0, 6), 'keep': 3.0})
    for k in range(3):   # buds
        a = rng.uniform(0, 6.3)
        rr = rng.uniform(0.1, 0.25) * W
        c = Vector((math.cos(a) * rr, math.sin(a) * rr, mound * (1 - (rr / (0.45 * W)) ** 2) + 0.03))
        parts.append({'kind': 'bud', 'base': c, 'radius': 0.035, 'keep': 1.5})
    if not low:
        grass(parts, 11, 7, 0.12 * W, (0.58, 0.78), width=(0.045, 0.06), elev0=(74, 89), elev1=(25, 62),
              centre_boost=1.2, curve=1.3, centre_lift=0)
        stars(parts, 3, 0.08 * W, 0.85 * H, 0.3 * W, regions=('T1', 'T1'), lods=(2,))
    parts.append({'kind': 'star', 'base': Vector((0, 0, 0)), 'turn': 0.3, 'width': 0.9 * W, 'height': 0.6 * H,
                  'regions': ('T0', 'T0'), 'lods': {2}, 'keep': 2.0, 'cards': 2})
else:
    raise SystemExit('no layout for ' + SID)

if SID in ('flower13', 'flower16'):
    PLAN['head'] = [(1.0, 1.0, 8), (0.7, 1.15, 7), (0.45, 1.35, 6)]
    PLAN['lily'] = [(1.0, 1.0, 9), (1.0, 1.04, 7), (1.0, 1.08, 5)]
if SID in ('flower10', 'flower11', 'flower12'):
    PLAN['head'] = [(1.0, 1.0, 7), (0.7, 1.12, 5), (0.4, 1.3, 5)]
if SID == 'flower05':
    PLAN['star'] = [(1.0, 1.0, 0), (0.6, 1.1, 0), (0.5, 1.15, 0)]
    PLAN['leaf'] = [(1.0, 1.0, 1), (0.7, 1.15, 1), (0.4, 1.35, 0)]
    PLAN['bloom'] = [(1.0, 1.0, 8), (1.0, 1.03, 6), (1.0, 1.08, 4)]


def emit_bud(mesh, bd, segs):
    r = bd['radius']
    profile = [(0.0, r * 0.7), (r * 1.2, r * 1.0), (r * 2.4, 0.0)]
    lathe(mesh, bd['base'], UP, profile, segs, lambda ring, j: ruv('R0', j / segs, 1.0 - ring / 2 * 0.9),
          (1, 1, 1), 0.0, floor=0.6)


def build_mesh(lod):
    mesh = Mesh()
    for kind in PLAN.keys() | {'bud'}:
        group = [p for p in parts if p['kind'] == kind and lod in p.get('lods', {0, 1, 2})]
        if not group:
            continue
        fraction, grow, segs = PLAN[kind][lod] if kind in PLAN else (1.0 if lod < 2 else 0.0, 1.0, 6)
        keep = sorted(group, key=lambda p: -p['keep'])[:int(round(len(group) * fraction))]
        for p in keep:
            if kind == 'blade':
                emit_blade(mesh, p, segs, grow)
            elif kind == 'head':
                emit_head(mesh, p, segs, grow, rings=p.get('rings', 1) if lod == 0 else 1)
            elif kind == 'stem':
                emit_stem(mesh, p['bottom'], p['top'], p['width'], lod == 0)
            elif kind == 'bloom':
                emit_bloom(mesh, p, segs, grow)
            elif kind == 'lily':
                emit_lily(mesh, p, segs, grow)
            elif kind == 'iris':
                emit_iris(mesh, p, grow, lod)
            elif kind == 'spike':
                emit_spike(mesh, p, segs, grow, lod)
            elif kind == 'leaf':
                emit_leaf(mesh, p, grow, fold=segs > 0)
            elif kind == 'card':
                emit_card(mesh, p, grow)
            elif kind == 'star':
                emit_star(mesh, p, grow)
            elif kind == 'bud':
                emit_bud(mesh, p, 5)
    return mesh


def spread(factor):
    """Move every part's anchor points horizontally (sizes unchanged), so the clump gets the sprite's width without
    squeezing its heads; parts marked spread=False (flower05's bloom cluster) stay."""
    for p in parts:
        if not p.get('spread', True):
            continue
        for key in ('base', 'centre', 'bottom', 'top', 'stem_base'):
            v = p.get(key)
            if isinstance(v, Vector):
                p[key] = Vector((v.x * factor, v.y * factor, v.z))


def fit_spread():
    total = 1.0
    for attempt in range(6):
        mesh = build_mesh(0)
        co = np.array([v.co[:] for v in mesh.bm.verts])
        mesh.bm.free()
        width = 0.5 * ((co[:, 0].max() - co[:, 0].min()) + (co[:, 1].max() - co[:, 1].min()))
        height = co[:, 2].max() - max(co[:, 2].min(), 0.0)    # as the final fit: below-ground parts are clamped
        correction = (W / H) / (width / height)
        if abs(correction - 1.0) < 0.012:
            break
        factor = min(max(correction ** 1.3, 0.75), 1.35)
        spread(factor)
        total *= factor
    print('SPREAD', SID, 'anchor scale', round(total, 3), 'after', attempt + 1, 'builds')


def build(lod, name):
    mesh = build_mesh(lod)
    me = bpy.data.meshes.new(name)
    mesh.bm.to_mesh(me)
    mesh.bm.free()
    me.normals_split_custom_set_from_vertices(mesh.normals)
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', [x for c in mesh.colours for x in c])
    me.color_attributes.active_color = attr
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


mat = bpy.data.materials.new('Plant')
mat.use_nodes = True
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tb = nt.nodes.new('ShaderNodeTexImage')
tb.image = bpy.data.images.load(os.path.join(ATLAS_DIR, 'atlas_basecolor.png'))
nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
nt.links.new(tb.outputs['Alpha'], bsdf.inputs['Alpha'])
tn = nt.nodes.new('ShaderNodeTexImage')
tn.image = bpy.data.images.load(os.path.join(ATLAS_DIR, 'atlas_normal.png'))
tn.image.colorspace_settings.name = 'Non-Color'
nm = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
bsdf.inputs['Roughness'].default_value = 0.85
bsdf.inputs['Metallic'].default_value = 0.0
mat.use_backface_culling = False
mat.surface_render_method = 'DITHERED'
mat['openyamm_wind'] = 0.02
mat['openyamm_specular'] = 0.1
mat['openyamm_translucency'] = 0.3

fit_spread()
objects = []
for lod, name in enumerate(('Plant', 'Plant_LOD1', 'Plant_LOD2')):
    o = build(lod, name)
    o.data.materials.append(mat)
    objects.append(o)

# Fit LOD0's bounds to the sprite: uniform scale to the art height, then a horizontal correction (clamped) to the art
# width, the same transform for every level.
co = np.array([v.co[:] for v in objects[0].data.vertices])
ground = co[:, 2].min()
if ground > 0.0:                   # the clump stands on the ground even when its lowest part was laid out above it
    for o in objects:
        for v in o.data.vertices:
            v.co.z = max(v.co.z - ground, 0.0)
    co[:, 2] -= ground
height = co[:, 2].max()
s = H / height
width = 0.5 * ((co[:, 0].max() - co[:, 0].min()) + (co[:, 1].max() - co[:, 1].min())) * s
sh = min(max(W / width, 0.97), 1.03)     # the residue after fit_spread()
print('FIT', SID, 'height', round(height, 3), 'scale', round(s, 3), 'horizontal', round(sh, 3),
      'width before', round(width, 3), 'target', round(W, 3))
for o in objects:
    for v in o.data.vertices:
        v.co = (v.co.x * s * sh, v.co.y * s * sh, max(v.co.z * s, 0.0))
top0 = max(v.co.z for v in objects[0].data.vertices)
for o in objects[1:]:
    top = max(v.co.z for v in o.data.vertices)
    if top > top0:
        for v in o.data.vertices:
            v.co.z *= top0 / top
for o in objects:
    print('LOD', o.name, 'triangles', sum(len(p.vertices) - 2 for p in o.data.polygons))
for o in bpy.data.objects:
    o.select_set(o in objects)
bpy.context.view_layer.objects.active = objects[0]
out = os.path.join(WORK, 'plant_export.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_extras=True, export_normals=True, export_vertex_color='ACTIVE', export_tangents=False,
                          export_animations=False, export_skins=False, export_morph=False, export_image_format='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'plant.blend'))
print('EXPORTED', out)
