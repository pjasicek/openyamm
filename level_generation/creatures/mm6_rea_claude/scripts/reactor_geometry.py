"""Procedural geometry, UVs and rigid bone assignment of the MM6 Reactor (plain Python, no bpy).

build() returns {'meshes': {node: Mesh}, 'bones': [(name, head, parent)], 'sockets': {name: (bone, position)}}.
Every vertex belongs to exactly one bone (rigid parts). Triangles are emitted directly (shorter diagonal of each quad),
with outward winding checked against the profile normal. Hard edges are vertex splits between profile sections and
coincide with UV gaps (GAME_ASSET_MODELLING_GUIDELINES.md, section 3).
"""
import math
import random

import reactor_layout as L

TAU = 2.0 * math.pi
GAP = 8  # texels between UV islands / sections
# Authored LODs (GAME_ASSET_MODELLING_GUIDELINES.md section 7): the same parts with fewer segments around, so every
# silhouette ring, UV and bone is kept and the triangle count roughly halves per level.
LOD_FACTORS = (1.0, 0.7, 0.5, 0.33)
_lod_f = 1.0


def S(n, lo=3):
    """Segment count n at the current LOD, at least lo."""
    return max(lo, int(round(n * _lod_f)))


class Mesh:
    def __init__(self, materials, atlas_sizes):
        self.materials = materials          # names, index = material slot
        self.sizes = atlas_sizes            # texel size of each slot's atlas
        self.verts = []                     # (x, y, z)
        self.bone = []                      # bone name per vertex
        self.tris = []                      # (a, b, c)
        self.uvs = []                       # ((u, v) * 3) per triangle, Blender UV space (origin bottom-left)
        self.mat = []                       # slot per triangle

    def vert(self, p, bone):
        self.verts.append(tuple(p)); self.bone.append(bone)
        return len(self.verts) - 1

    def tri(self, idx, uvs, slot):
        self.tris.append(tuple(idx)); self.uvs.append(tuple(uvs)); self.mat.append(slot)


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def norm(a):
    n = length(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 0.0, 0.0)


def rect_uv(rects, size, name, u, v):
    """u, v in 0..1 inside the named rectangle (v = 0 at the rectangle's top row) -> Blender UV."""
    x, y, w, h = rects[name]
    return ((x + u * w) / size, 1.0 - (y + v * h) / size)


def emit_quad(m, a, b, c, d, ua, ub, uc, ud, slot, expected=None):
    """Quad a-b-c-d (any winding); split on the shorter diagonal; orient each triangle along `expected`
    (a callable giving the outward normal at a point) when given."""
    P = m.verts
    if length(sub(P[a], P[c])) <= length(sub(P[b], P[d])):
        tris = [((a, b, c), (ua, ub, uc)), ((a, c, d), (ua, uc, ud))]
    else:
        tris = [((a, b, d), (ua, ub, ud)), ((b, c, d), (ub, uc, ud))]
    for idx, uv in tris:
        p0, p1, p2 = (P[i] for i in idx)
        n = cross(sub(p1, p0), sub(p2, p0))
        if length(n) < 1e-12:
            continue
        if expected is not None:
            centre = mul(add(add(p0, p1), p2), 1.0 / 3.0)
            if dot(n, expected(centre)) < 0:
                idx = (idx[0], idx[2], idx[1]); uv = (uv[0], uv[2], uv[1])
        m.tri(idx, uv, slot)


def lathe(m, profile, bone, slot, rects, rect, seg, mirrored=True, centre=(0.0, 0.0, 0.0), v_span=(0.0, 1.0),
          zfn=None, rfn=None, theta_range=None, scale_r=1.0, offset_n=0.0):
    """Surface of revolution about the vertical axis through `centre`. Sections are smooth inside and split from
    each other (hard edges, UV gap). v_span: the part of the rectangle (top = 0) this profile occupies, so split
    pieces of one shell share one continuous texture. offset_n pushes the surface along its profile normal."""
    size = m.sizes[slot]
    marks, total = L.profile_lengths(profile)
    rh = rects[rect][3]
    gaps = GAP * (len(profile) - 1) / max(rh, 1)
    span = v_span[1] - v_span[0]
    t0, t1 = theta_range if theta_range else (-math.pi, math.pi)
    for si, section in enumerate(profile):
        # Profile normals in (r, z) per point: average of adjacent segment normals (dz, -dr).
        pts = [(r * scale_r, z) for r, z in section]
        normals = []
        for i in range(len(pts)):
            segs = []
            if i > 0: segs.append((pts[i - 1], pts[i]))
            if i < len(pts) - 1: segs.append((pts[i], pts[i + 1]))
            nr = sum(b[1] - a[1] for a, b in segs); nz = sum(-(b[0] - a[0]) for a, b in segs)
            n = math.hypot(nr, nz) or 1.0
            normals.append((nr / n, nz / n))
        pts = [(r + offset_n * nr, z + offset_n * nz) for (r, z), (nr, nz) in zip(pts, normals)]
        acc = [0.0]
        for (r0, z0), (r1, z1) in zip(section, section[1:]):
            acc.append(acc[-1] + math.hypot(r1 - r0, z1 - z0))
        rings = []
        for i, (r, z) in enumerate(pts):
            t = (marks[si] + acc[i]) / total if total else 0.0
            tv = (t * (1.0 - gaps) + gaps * si / max(len(profile) - 1, 1)) if len(profile) > 1 else t
            # v from the top row: the profile end (top of the part) at v_span[0].
            v = v_span[0] + span * (1.0 - tv)
            ring = []
            for j in range(seg + 1):
                th = t0 + (t1 - t0) * j / seg
                rr = r + (rfn(r, z, th) if rfn else 0.0)
                zz = z + (zfn(r, z, th) if zfn else 0.0)
                p = (centre[0] + rr * math.sin(th), centre[1] - rr * math.cos(th), centre[2] + zz)
                u = abs(th) / math.pi if mirrored else (th - t0) / (t1 - t0)
                ring.append((m.vert(p, bone), rect_uv(rects, size, rect, u, v), r))
            rings.append(ring)
        for i in range(len(rings) - 1):
            (r0, z0), (r1, z1) = pts[i], pts[i + 1]
            nr, nz = z1 - z0, -(r1 - r0)
            def expected(p, nr=nr, nz=nz):
                dx, dy = p[0] - centre[0], p[1] - centre[1]
                rad = math.hypot(dx, dy) or 1.0
                return (nr * dx / rad, nr * dy / rad, nz)
            for j in range(seg):
                a, b = rings[i][j], rings[i][j + 1]
                c, d = rings[i + 1][j + 1], rings[i + 1][j]
                emit_quad(m, a[0], b[0], c[0], d[0], a[1], b[1], c[1], d[1], slot, expected)
    return marks, total


def cap(m, r, z, bone, slot, rects, rect, seg, up=True, centre=(0.0, 0.0, 0.0), zfn=None, planar=True):
    """Close a ring of radius r at height z with a strip-triangulated polygon (no centre vertex, no valence fan)."""
    size = m.sizes[slot]
    ring = []
    for j in range(seg):
        th = -math.pi + TAU * j / seg
        x, y = r * math.sin(th), -r * math.cos(th)
        zz = z + (zfn(r, z, th) if zfn else 0.0)
        uv = rect_uv(rects, size, rect, 0.5 + 0.5 * x / r, 0.5 + 0.5 * y / r) if planar else \
            rect_uv(rects, size, rect, abs(th) / math.pi, 0.5)
        ring.append((m.vert((centre[0] + x, centre[1] + y, centre[2] + zz), bone), uv))
    lo, hi = 0, seg - 1
    order = []
    while lo < hi:
        order.append(lo); order.append(hi); lo += 1; hi -= 1
    if lo == hi: order.append(lo)
    for k in range(len(order) - 2):
        idx = [ring[order[k]], ring[order[k + 1]], ring[order[k + 2]]]
        p = [m.verts[i[0]] for i in idx]
        n = cross(sub(p[1], p[0]), sub(p[2], p[0]))
        if (n[2] < 0) == up:
            idx = [idx[0], idx[2], idx[1]]
        if length(n) > 1e-12:
            m.tri([i[0] for i in idx], [i[1] for i in idx], slot)


def frame(direction):
    d = norm(direction)
    helper = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
    a = norm(cross(d, helper)); b = cross(d, a)
    return d, a, b


def tube(m, points, radius, bone, slot, rects, rect, seg, radii=None, close_ends=False):
    """Tube along a polyline (rods, arcs, goo); u around, v along."""
    size = m.sizes[slot]
    n = len(points)
    rings = []
    lengths = [0.0]
    for p, q in zip(points, points[1:]):
        lengths.append(lengths[-1] + length(sub(q, p)))
    total = lengths[-1] or 1.0
    for i, p in enumerate(points):
        tangent = sub(points[min(i + 1, n - 1)], points[max(i - 1, 0)])
        d, a, b = frame(tangent)
        r = radii[i] if radii else radius
        ring = []
        for j in range(seg + 1):
            th = TAU * j / seg
            off = add(mul(a, math.cos(th) * r), mul(b, math.sin(th) * r))
            ring.append((m.vert(add(p, off), bone), rect_uv(rects, size, rect, j / seg, 1.0 - lengths[i] / total)))
        rings.append(ring)
    for i in range(n - 1):
        axis_a, axis_b = points[i], points[i + 1]
        def expected(p, axis_a=axis_a, axis_b=axis_b):
            d = norm(sub(axis_b, axis_a)); w = sub(p, axis_a)
            return sub(w, mul(d, dot(w, d)))
        for j in range(seg):
            a, b = rings[i][j], rings[i][j + 1]
            c, d = rings[i + 1][j + 1], rings[i + 1][j]
            emit_quad(m, a[0], b[0], c[0], d[0], a[1], b[1], c[1], d[1], slot, expected)
    if close_ends:
        for ring, sign in ((rings[0], -1.0), (rings[-1], 1.0)):
            centre_p = m.verts[ring[0][0]]
            pts = [r[0] for r in ring[:-1]]
            k = len(pts)
            lo, hi, order = 0, k - 1, []
            while lo < hi:
                order.append(lo); order.append(hi); lo += 1; hi -= 1
            if lo == hi: order.append(lo)
            axis = norm(sub(points[-1], points[0]))
            # planar UVs on the disc: the rectangle's centre at the axis, its edge at the rim
            ring_uv = [rect_uv(rects, size, rect, 0.5 + 0.5 * math.cos(TAU * q / k), 0.5 + 0.5 * math.sin(TAU * q / k))
                       for q in range(k)]
            cap_ids = [m.vert(m.verts[i], bone) for i in pts]
            for q in range(len(order) - 2):
                sel = [order[q], order[q + 1], order[q + 2]]
                idx = [cap_ids[i] for i in sel]; uvs = [ring_uv[i] for i in sel]
                p = [m.verts[i] for i in idx]
                nn = cross(sub(p[1], p[0]), sub(p[2], p[0]))
                if dot(nn, axis) * sign < 0:
                    idx = [idx[0], idx[2], idx[1]]; uvs = [uvs[0], uvs[2], uvs[1]]
                if length(nn) > 1e-12:
                    m.tri(idx, uvs, slot)


def sphere(m, centre, radius, bone, slot, rects, rect, seg=8, rings=5, stretch=1.0):
    """Lat-long sphere as a lathe of a semicircle; pole valence = seg (<= 10, guidelines section 1)."""
    prof = [[(radius * math.sin(math.pi * k / rings), centre[2] + stretch * radius * -math.cos(math.pi * k / rings))
             for k in range(rings + 1)]]
    lathe(m, prof, bone, slot, rects, rect, seg, mirrored=False, centre=(centre[0], centre[1], 0.0))


def box(m, centre, axes, half, bone, slot, rects, front_rect, side_rect):
    """Box with local axes (x, y, z) and half sizes; the +z face takes front_rect, the others side_rect."""
    size = m.sizes[slot]
    corners = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                corners[(sx, sy, sz)] = add(centre, add(add(mul(axes[0], sx * half[0]), mul(axes[1], sy * half[1])),
                                                        mul(axes[2], sz * half[2])))
    faces = [((0, 0, 1), [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]),
             ((0, 0, -1), [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)]),
             ((1, 0, 0), [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)]),
             ((-1, 0, 0), [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)]),
             ((0, 1, 0), [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)]),
             ((0, -1, 0), [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)])]
    for normal_local, quad in faces:
        normal = add(add(mul(axes[0], normal_local[0]), mul(axes[1], normal_local[1])), mul(axes[2], normal_local[2]))
        rect = front_rect if normal_local == (0, 0, 1) else side_rect
        uvq = [(0, 1), (1, 1), (1, 0), (0, 0)]
        idx = [m.vert(corners[c], bone) for c in quad]
        uv = [rect_uv(rects, size, rect, u, v) for u, v in uvq]
        emit_quad(m, *idx, *uv, slot, lambda p, n=normal: n)


def patch(m, radius, half_angle, z0, z1, bone, slot, rects, rect, cols, cone=None):
    """Curved screen patch on a cylinder (or on a cone: cone = (r_at_z0, r_at_z1)) facing the front."""
    size = m.sizes[slot]
    rows = []
    for zi, z in enumerate((z0, z1)):
        r = radius if cone is None else cone[zi]
        row = []
        for j in range(cols + 1):
            th = -half_angle + 2 * half_angle * j / cols
            row.append((m.vert((r * math.sin(th), -r * math.cos(th), z), bone),
                        rect_uv(rects, size, rect, j / cols, 1.0 - zi)))
        rows.append(row)
    for j in range(cols):
        a, b, c, d = rows[0][j], rows[0][j + 1], rows[1][j + 1], rows[1][j]
        emit_quad(m, a[0], b[0], c[0], d[0], a[1], b[1], c[1], d[1], slot,
                  lambda p: (p[0], p[1], 0.0))


def polygon_piece(m, outline, thickness_dir, bone, slot, rects, rect, double=True):
    """Flat irregular piece (glass shard) from an outline; emitted on both sides as duplicated, flipped triangles."""
    size = m.sizes[slot]
    c = mul(outline[0], 0.0)
    for p in outline: c = add(c, p)
    c = mul(c, 1.0 / len(outline))
    for sign in ((1, -1) if double else (1,)):
        ids = [m.vert(p, bone) for p in outline]
        uv = [rect_uv(rects, size, rect, 0.2 + 0.6 * (k / len(outline)), 0.3 + 0.4 * (k % 2)) for k in range(len(ids))]
        for k in range(1, len(ids) - 1):
            tri = [ids[0], ids[k], ids[k + 1]]; tuv = [uv[0], uv[k], uv[k + 1]]
            p = [m.verts[i] for i in tri]
            n = cross(sub(p[1], p[0]), sub(p[2], p[0]))
            if dot(n, thickness_dir) * sign < 0:
                tri = [tri[0], tri[2], tri[1]]; tuv = [tuv[0], tuv[2], tuv[1]]
            m.tri(tri, tuv, slot)


def chunk(m, centre, size, bone, slot, rects, rect, rng):
    """Irregular debris lump: a jittered box."""
    axes = [norm((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) for _ in range(1)]
    a0 = axes[0]; _, a1, a2 = frame(a0)
    half = (size * rng.uniform(0.5, 1.0), size * rng.uniform(0.35, 0.8), size * rng.uniform(0.2, 0.5))
    box(m, centre, (a0, a1, a2), half, bone, slot, rects, rect, rect)


# ------------------------------------------------------------------------------------------------ arm kinematics
def arm_joints(shoulder, lengths, angles_deg):
    """Joint positions in the XZ plane (y = 0) from absolute segment angles (degrees from +X toward +Z)."""
    pts = [shoulder]
    x, z = shoulder
    for ln, ang in zip(lengths, angles_deg):
        a = math.radians(ang)
        x, z = x + ln * math.cos(a), z + ln * math.sin(a)
        pts.append((x, z))
    return pts


# Choreography poses, absolute segment angles (deg): image-left (-X) arm and image-right (+X) arm.
# Measured from the native frames (reaat05 converged, reaat09 spread); see README "Arms".
POSES = {
    'lower_converged': ([120.8, 42.8, 37.0], [59.2, 137.2, 143.0]),
    'lower_wide':      ([130.0, 161.0, 83.0], [45.0, 56.0, -73.0]),
    'lower_fold':      ([150.0, 250.0, 120.0], [30.0, -70.0, 60.0]),
    'upper_converged': ([-98.0, -40.0, -20.0], [-82.0, -140.0, -160.0]),
    'upper_wide':      ([-115.0, -98.5, -93.0], [-72.7, -71.0, 21.5]),
    'upper_fold':      ([-100.0, -60.0, -30.0], [-80.0, -120.0, -150.0]),
}


def rest_arm(side, upper):
    """Rest geometry: straight along -X (left) or +X (right) from the shoulder."""
    sx, sz = L.UPPER_SHOULDER if upper else L.LOWER_SHOULDER
    lengths = L.UPPER_LENGTHS if upper else L.LOWER_LENGTHS
    sign = -1.0 if side == 'L' else 1.0
    sx = abs(sx) * sign
    return arm_joints((sx, sz), lengths, [180.0 if side == 'L' else 0.0] * 3)


# ------------------------------------------------------------------------------------------------ build
def build(seed=6, lod=0):
    global _lod_f
    _lod_f = LOD_FACTORS[lod]
    rng = random.Random(seed)
    MR, GR = L.METAL_RECTS, L.GLOW_RECTS
    body = Mesh(['Reactor_Metal', 'Reactor_Glow'], [L.METAL_SIZE, L.GLOW_SIZE])
    glass = Mesh(['Reactor_Glass', 'Reactor_Flash', 'Reactor_Halo'], [L.GLASS_SIZE, L.GLOW_SIZE, L.GLOW_SIZE])
    METAL, GLOW = 0, 1
    bones = []
    def bone(name, head, parent):
        bones.append((name, tuple(head), parent)); return name

    bone('Root', (0, 0, 0), None)
    bone('Base', (0, 0, 0), 'Root')
    bone('Body', (0, 0, 0.215), 'Base')
    bone('DomeTop', (0, 0, 1.07), 'Body')
    bone('CapGlow', (0, 0, 1.20), 'Body')
    bone('Spire', (0, 0, 1.40), 'Body')
    bone('Crown', (0, 0, 1.05), 'Body')
    bone('GooBlob', (0, 0, 1.06), 'Body')
    bone('Chamber', L.CHAMBER_PIVOT, 'Root')
    for name in ('Glass', 'GlassBroken', 'Flash'):
        bone(name, (0, 0, 3.55), 'Chamber')
    for name in L.LIQUID_LEVELS:
        bone(name, (0, 0, L.LIQUID_BASE), 'Chamber')
    bone('BowlLower', (0, 0, 2.93), 'Chamber')
    bone('BowlGlow', (0, 0, 3.0), 'Chamber')
    bone('BowlTorn', (0, 0, 2.95), 'Chamber')
    bone('Nozzle', (0, 0, 2.70), 'Chamber')
    bone('GooStream', (0, 0, 2.86), 'Chamber')

    # ---- base and body shells (mirrored UVs, front = u 0)
    lathe(body, L.SKIRT, 'Base', METAL, MR, 'skirt', S(L.SEG, 8))
    lathe(body, L.BAND, 'Body', METAL, MR, 'band', S(L.SEG, 8))
    dome_len = L.profile_lengths(L.DOME)[1]; top_len = L.profile_lengths(L.DOME_TOP)[1]
    split = top_len / (dome_len + top_len)
    lathe(body, L.DOME, 'Body', METAL, MR, 'dome', S(L.SEG, 8), v_span=(split, 1.0))
    lathe(body, L.DOME_TOP, 'DomeTop', METAL, MR, 'dome', S(L.SEG, 8), v_span=(0.0, split))
    lathe(body, L.CAP, 'DomeTop', METAL, MR, 'cap', S(L.SEG_MID, 6))
    lathe(body, L.CAP, 'CapGlow', GLOW, GR, 'cap_glow', S(L.SEG_MID, 6), offset_n=0.012)
    lathe(body, L.SPIRE, 'Spire', METAL, MR, 'spire', S(L.SEG_SMALL, 4))
    tube(body, list(L.SPIRE_ROD[:2]), L.SPIRE_ROD[2], 'Spire', METAL, MR, 'rod', S(L.SEG_ROD, 3))
    sphere(body, L.LOWER_BALL[0], L.LOWER_BALL[1], 'Spire', METAL, MR, 'bulb', seg=S(12, 6), rings=S(7, 4))

    # ---- band screen (dark window + three waveform overlays) and the control plate with lamps
    r, half, z0, z1 = L.BAND_SCREEN
    patch(body, r, half, z0, z1, 'Body', METAL, MR, 'screen', 10)
    for k in (1, 2, 3):
        name = bone(f'BandWave{k}', (0, -r, (z0 + z1) / 2), 'Body')
        patch(body, r + 0.008, half * 0.96, z0 + 0.008, z1 - 0.008, name, GLOW, GR, f'band_wave{k}', 10)
    r, half, z0, z1 = L.LID_SCREEN
    patch(body, r, half, z0, z1, 'Chamber', METAL, MR, 'screen', 10)
    for k in (1, 2, 3):
        name = bone(f'LidWave{k}', (0, -r, (z0 + z1) / 2), 'Chamber')
        patch(body, r + 0.008, half * 0.96, z0 + 0.006, z1 - 0.006, name, GLOW, GR, f'lid_wave{k}', 10)

    px, pz, pw, ph = L.PLATE
    # Dome surface at the plate centre and its outward normal / upward tangent in the (y, z) plane.
    pts = L.DOME[0]
    for (r0, za), (r1, zb) in zip(pts, pts[1:]):
        if za <= pz <= zb:
            rr = r0 + (r1 - r0) * (pz - za) / (zb - za); slope = (r1 - r0) / (zb - za); break
    nrm = norm((0.0, -1.0, -slope))          # outward: -Y and up by the dome slope
    up = norm(cross((1.0, 0.0, 0.0), nrm))   # tangent toward the top
    if up[2] < 0: up = mul(up, -1.0)
    centre = (px, -math.sqrt(max(rr * rr - px * px, 0.0)), pz)
    plate_centre = add(centre, mul(nrm, 0.012))
    box(body, plate_centre, ((1.0, 0.0, 0.0), up, nrm), (pw / 2, ph / 2, 0.03), 'Body', METAL, MR, 'plate', 'plain')
    face = add(plate_centre, mul(nrm, 0.031))
    for name, kind, lx, ly, s in L.LAMPS:
        c = add(add(face, (lx, 0.0, 0.0)), mul(up, ly))
        bone(name, c, 'Body')
        rect = 'lamp_red' if kind == 'red' else 'lamp_green'
        if kind == 'red':      # round lens: a short capped tube along the plate normal
            tube(body, [c, add(c, mul(nrm, 0.006))], s, name, GLOW, GR, rect, S(8, 4), close_ends=True)
        else:                  # square lens
            box(body, add(c, mul(nrm, 0.003)), ((1.0, 0.0, 0.0), up, nrm), (s / 2, s / 2, 0.003), name, GLOW, GR,
                rect, rect)

    # ---- chamber: lid, glass frame, struts, bowl, nozzle, upper electrode
    lathe(body, L.LID, 'Chamber', METAL, MR, 'lid', S(L.SEG, 8))
    cap(body, 0.32, L.LID_CAP_Z, 'Chamber', METAL, MR, 'lidtop', S(16, 6), up=True)
    lathe(body, L.BOWL_RING, 'Chamber', METAL, MR, 'ring', S(L.SEG, 8))
    bl = L.profile_lengths(L.BOWL)[1]; bll = L.profile_lengths(L.BOWL_LOWER)[1]
    bsplit = bl / (bl + bll)
    lathe(body, L.BOWL, 'Chamber', METAL, MR, 'bowl', S(L.SEG_MID, 6), v_span=(0.0, bsplit))
    lathe(body, L.BOWL_LOWER, 'BowlLower', METAL, MR, 'bowl', S(L.SEG_MID, 6), v_span=(bsplit, 1.0))
    # Glow only on the lower bowl (native: chrome bowl with a blue-white core at the bottom).
    lathe(body, L.BOWL_LOWER, 'BowlGlow', GLOW, GR, 'bowl_glow', S(L.SEG_MID, 6), offset_n=0.012)
    lathe(body, L.NOZZLE, 'Nozzle', METAL, MR, 'nozzle', S(L.SEG_SMALL, 4))
    tube(body, list(L.NOZZLE_ROD[:2]), L.NOZZLE_ROD[2], 'Nozzle', METAL, MR, 'rod', S(L.SEG_ROD, 3))
    sphere(body, L.UPPER_BALL[0], L.UPPER_BALL[1], 'Nozzle', METAL, MR, 'bulb', seg=S(12, 6), rings=S(7, 4))
    # Struts: front, sides, back, outside the glass.
    for k in range(4):
        th = k * math.pi / 2
        prof = L.GLASS if _lod_f > 0.5 else L.GLASS[::2] + ([L.GLASS[-1]] if len(L.GLASS) % 2 == 0 else [])
        rows = []
        for (rg, z) in prof:
            ring = []
            for (dr, dt) in ((0.004, -0.022), (0.022, -0.017), (0.022, 0.017), (0.004, 0.022)):
                rr, tt = rg + dr, th + dt / rg
                ring.append((rr * math.sin(tt), -rr * math.cos(tt), z))
            rows.append(ring)
        size = body.sizes[METAL]
        for i in range(len(rows) - 1):
            for j in range(3):
                ids = [body.vert(p, 'Chamber') for p in (rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j])]
                uv = [rect_uv(MR, size, 'strut', (j + a) / 3, 1.0 - (i + b) / (len(rows) - 1))
                      for a, b in ((0, 0), (1, 0), (1, 1), (0, 1))]
                axis_th = th
                emit_quad(body, *ids, *uv, METAL,
                          lambda p, t=axis_th: (math.sin(t), -math.cos(t), 0.0))
    # Inner liner (dark, seen from inside once the glass breaks): lid underside, wall, floor.
    liner = [[(0.0 + 0.10, 3.852), (0.70, 3.852)],
             [(0.70, 3.852), (L.glass_radius(3.6) - 0.07, 3.60), (L.glass_radius(3.3) - 0.07, 3.30),
              (L.glass_radius(3.22) - 0.07, 3.225)],
             [(L.glass_radius(3.22) - 0.07, 3.225), (0.10, 3.225)]]
    lathe(body, liner, 'Chamber', METAL, MR, 'inner', 16)
    cap(body, 0.10, 3.852, 'Chamber', METAL, MR, 'inner', S(8, 4), up=False)
    cap(body, 0.10, 3.225, 'Chamber', METAL, MR, 'inner', S(8, 4), up=True)

    # ---- liquid levels (unlit green): wall just inside the glass and a lumpy top
    def lumps(r, z, th):
        return 0.03 * math.sin(3 * th + 1.3) * math.sin(r * 9.0) + 0.02 * math.cos(5 * th - r * 14.0)
    for name, top in L.LIQUID_LEVELS.items():
        # Behind the glass and struts the wall has no silhouette of its own: 24 segments, two bands.
        zs = [L.LIQUID_BASE, (L.LIQUID_BASE + top) / 2, top]
        wall = [[(L.glass_radius(z) - 0.03, z) for z in zs]]
        re = L.glass_radius(top) - 0.03
        # A lumpy mound (the native liquid rises toward the middle and shows its lumps through the front glass).
        top_prof = [[(re, top), (re * 0.6, top + 0.055), (re * 0.25, top + 0.08)]]
        lathe(body, wall, name, GLOW, GR, 'liquid_side', S(L.SEG_MID, 6))
        lathe(body, top_prof, name, GLOW, GR, 'liquid_top', S(L.SEG_MID, 6),
              zfn=lambda r, z, th, re=re: lumps(r, z, th) * min(1.0, (re - r) / 0.05))
        cap(body, re * 0.25, top + 0.08, name, GLOW, GR, 'liquid_top', S(8, 4), up=True, zfn=lumps)

    # ---- glass, flash shell, broken glass, shards
    glass_prof = [list(L.GLASS)]
    lathe(glass, glass_prof, 'Glass', 0, {'glass': (0, 0, L.GLASS_SIZE, L.GLASS_SIZE)}, 'glass', S(L.SEG, 8), mirrored=False)
    lathe(glass, [[(r - 0.012, z) for r, z in L.GLASS]], 'Flash', 1, GR, 'arc', S(L.SEG_MID, 6))
    # Broken glass: denser shell with holes; faces kept by a smooth noise field, rim rows intact.
    zs = [L.GLASS[0][1] + (L.GLASS[-1][1] - L.GLASS[0][1]) * k / 10 for k in range(11)]
    seg_b = 32
    grid = []
    for i, z in enumerate(zs):
        row = []
        for j in range(seg_b + 1):
            th = -math.pi + TAU * j / seg_b
            rg = L.glass_radius(z) + 0.002
            jitter = 0.0 if i in (0, len(zs) - 1) else rng.uniform(-0.012, 0.012)
            row.append((glass.vert((rg * math.sin(th), -rg * math.cos(th), z + jitter), 'GlassBroken'),
                        ((th + math.pi) / TAU, (z - zs[0]) / (zs[-1] - zs[0]))))
        grid.append(row)
    holes = [(-0.30, 3.50, 0.34), (0.55, 3.70, 0.20), (-1.45, 3.36, 0.17), (2.6, 3.55, 0.28), (1.4, 3.30, 0.14)]
    def broken(p):
        th = math.atan2(p[0], -p[1]); z = p[2]
        if z < zs[0] + 0.04 or z > zs[-1] - 0.04:
            return False                       # the rims stay in their frames
        rg = L.glass_radius(z)
        for ht, hz, hr in holes:
            dth = (th - ht + math.pi) % TAU - math.pi
            d = math.hypot(dth * rg, z - hz)
            ragged = 0.35 * hr * math.sin(9 * math.atan2(z - hz, dth * rg) + 3 * ht)
            if d < hr + ragged:
                return True
        return False
    for i in range(len(zs) - 1):
        for j in range(seg_b):
            a, b, c, d = grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]
            for tri in ((a, b, c), (a, c, d)):
                centre = mul(add(add(glass.verts[tri[0][0]], glass.verts[tri[1][0]]), glass.verts[tri[2][0]]), 1 / 3)
                if broken(centre):
                    continue
                idx = [t[0] for t in tri]; uv = [t[1] for t in tri]
                pp = [glass.verts[k] for k in idx]
                if dot(cross(sub(pp[1], pp[0]), sub(pp[2], pp[0])), (centre[0], centre[1], 0.0)) < 0:
                    idx = [idx[0], idx[2], idx[1]]; uv = [uv[0], uv[2], uv[1]]
                glass.tri(idx, uv, 0)
    shard_bones = []
    for k in range(8):
        th = rng.uniform(-1.2, 1.2); z = rng.uniform(3.30, 3.78)
        rg = L.glass_radius(z)
        c = (rg * math.sin(th), -rg * math.cos(th), z)
        name = bone(f'Shard{k + 1}', c, 'Chamber'); shard_bones.append(name)
        tang = (math.cos(th), math.sin(th), 0.0); outward = (math.sin(th), -math.cos(th), 0.0)
        s = rng.uniform(0.05, 0.10)
        outline = [add(c, add(mul(tang, s * math.cos(a)), (0, 0, s * 1.4 * math.sin(a)))) for a in
                   (0.2 + rng.uniform(-0.3, 0.3), 2.2 + rng.uniform(-0.3, 0.3), 4.2 + rng.uniform(-0.3, 0.3))]
        polygon_piece(glass, outline, outward, name, 0, {'glass': (0, 0, L.GLASS_SIZE, L.GLASS_SIZE)}, 'glass')

    # ---- arcs (unlit tubes): four idle variants between the electrode balls, three charge stars
    def zigzag(p0, p1, n, amp):
        pts = [p0]
        for k in range(1, n):
            t = k / n
            base = add(p0, mul(sub(p1, p0), t))
            pts.append(add(base, (rng.uniform(-amp, amp), rng.uniform(-amp, amp), rng.uniform(-amp, amp) * 0.3)))
        pts.append(p1)
        return pts
    bottom, top = (0, 0, L.ARC_BOTTOM), (0, 0, L.ARC_TOP)
    for k in range(1, 5):
        name = bone(f'Arc{k}', L.ARC_CENTRE, 'Root')
        path = zigzag(bottom, top, S(9, 4), 0.05)
        tube(body, path, 0.02, name, GLOW, GR, 'arc', S(4, 3))
        # soft glow around the bolt (blended, on the glass node so it draws after the opaque parts)
        tube(glass, path, 0.05, name, 2, GR, 'arc', 6)
        if k % 2 == 0 and _lod_f > 0.5:   # a thinner side branch on every other variant (LOD0-1)
            mid = rng.randrange(3, 6)
            branch = zigzag((0, 0, L.ARC_BOTTOM + 0.04 * mid), (rng.uniform(-0.07, 0.07), rng.uniform(-0.05, 0.05),
                            L.ARC_BOTTOM + 0.04 * mid + 0.09), 4, 0.015)
            tube(body, branch, 0.006, name, GLOW, GR, 'arc', 3)
    # Charge star: from the centre to the four converged tool tips and both electrodes.
    tips = []
    for upper, key in ((False, 'lower_converged'), (True, 'upper_converged')):
        sh = L.UPPER_SHOULDER if upper else L.LOWER_SHOULDER
        ln = L.UPPER_LENGTHS if upper else L.LOWER_LENGTHS
        left, right = POSES[key]
        jl = arm_joints(sh, ln, left)
        jr = arm_joints((-sh[0], sh[1]), ln, right)
        tips += [(jl[-1][0], 0.0, jl[-1][1]), (jr[-1][0], 0.0, jr[-1][1])]
    for k in range(1, 4):
        name = bone(f'ArcBig{k}', L.ARC_CENTRE, 'Root')
        for target in tips + [bottom, top]:
            path = zigzag(L.ARC_CENTRE, target, S(4, 2), 0.035)
            tube(body, path, 0.02, name, GLOW, GR, 'arc', S(4, 3))
            tube(glass, path, 0.055, name, 2, GR, 'arc', 6)
        for _ in range(2 if _lod_f > 0.5 else 0):
            d = norm((rng.uniform(-1, 1), rng.uniform(-0.6, 0.6), rng.uniform(-1, 1)))
            tube(body, zigzag(L.ARC_CENTRE, add(L.ARC_CENTRE, mul(d, rng.uniform(0.12, 0.2))), 3, 0.025), 0.008,
                 name, GLOW, GR, 'arc', 3)

    # ---- arms: rest geometry straight out along -X / +X; one bone per segment
    for upper in (False, True):
        prefix = 'UArm' if upper else 'LArm'
        for side in ('L', 'R'):
            j = rest_arm(side, upper)
            parent = 'Chamber' if upper else 'Body'
            up_b = bone(f'{prefix}{side}_Up', (j[0][0], 0, j[0][1]), parent)
            fo_b = bone(f'{prefix}{side}_Fore', (j[1][0], 0, j[1][1]), up_b)
            to_b = bone(f'{prefix}{side}_Tool', (j[2][0], 0, j[2][1]), fo_b)
            P = [(x, 0.0, z) for x, z in j]
            rod = 0.024 if upper else 0.032   # native arms read about 3-4 cm thick
            sphere(body, P[0], rod * 2.4, up_b, METAL, MR, 'bulb', seg=S(12, 6), rings=S(6, 3))
            tube(body, [P[0], P[1]], rod, up_b, METAL, MR, 'rod', S(L.SEG_ROD, 3))
            hub = 'hub_white' if (side == 'R' and not upper) else 'hub_black'
            if upper:
                sphere(body, P[1], rod * 2.2, fo_b, METAL, MR, hub, seg=S(12, 6), rings=S(6, 3))
            else:   # elbow disc, axis along Y (faces the front)
                tube(body, [add(P[1], (0, -0.035, 0)), add(P[1], (0, 0.035, 0))], 0.095, fo_b, METAL, MR, hub, S(20, 8),
                     close_ends=True)
            tube(body, [P[1], P[2]], rod * 0.85, fo_b, METAL, MR, 'rod', S(L.SEG_ROD, 3))
            d = norm(sub(P[3], P[2]))
            sphere(body, P[2], rod * 2.0, to_b, METAL, MR, 'bulb', seg=S(12, 6), rings=S(6, 3))
            tl = length(sub(P[3], P[2]))
            neck = add(P[2], mul(d, tl * 0.62))
            tube(body, [P[2], neck], rod * 0.7, to_b, METAL, MR, 'rod', S(L.SEG_ROD, 3))
            tube(body, [neck, add(neck, mul(d, tl * 0.08)), P[3]], 0.0, to_b, METAL, MR, 'tip', 5,
                 radii=[rod * 1.5, rod * 1.5, 0.0])

    # ---- wreck: torn crown on the dome, torn bowl petals, debris, goo
    def torn_ring(m, base_r, base_z, n, tip_fn, bone_name, rect, both=True):
        size = m.sizes[METAL]
        for j in range(n):
            th0, th1 = -math.pi + TAU * j / n, -math.pi + TAU * (j + 1) / n
            thm = (th0 + th1) / 2
            tr, tz = tip_fn(thm)
            pa = (base_r * math.sin(th0), -base_r * math.cos(th0), base_z)
            pb = (base_r * math.sin(th1), -base_r * math.cos(th1), base_z)
            pt = (tr * math.sin(thm), -tr * math.cos(thm), tz)
            for sign in ((1, -1) if both else (1,)):
                ids = [m.vert(p, bone_name) for p in (pa, pb, pt)]
                uv = [rect_uv(L.METAL_RECTS, size, rect, u, v) for u, v in
                      ((abs(th0) / math.pi, 0.95), (abs(th1) / math.pi, 0.95), (abs(thm) / math.pi, 0.05))]
                p = [m.verts[i] for i in ids]
                n_ = cross(sub(p[1], p[0]), sub(p[2], p[0]))
                out = (math.sin(thm), -math.cos(thm), 0.0)
                if dot(n_, out) * sign < 0:
                    ids = [ids[0], ids[2], ids[1]]; uv = [uv[0], uv[2], uv[1]]
                m.tri(ids, uv, METAL)
    crown_tips = [(rng.uniform(0.40, 0.62), rng.uniform(1.08, 1.24)) for _ in range(18)]
    torn_ring(body, 0.54, 1.025, 18, lambda th: crown_tips[int((th + math.pi) / TAU * 18) % 18], 'Crown', 'debris')
    cap(body, 0.50, 1.045, 'Crown', METAL, MR, 'hole', S(12, 5), up=True)
    petal = [(rng.uniform(0.44, 0.63), rng.uniform(2.70, 2.90)) for _ in range(16)]
    torn_ring(body, 0.57, 3.00, 16, lambda th: petal[int((th + math.pi) / TAU * 16) % 16], 'BowlTorn', 'debris')
    for k in range(8):
        if k < 5:
            a = rng.uniform(-math.pi, math.pi); r = rng.uniform(0.1, 0.4)
            c = (r * math.sin(a), -r * math.cos(a), rng.uniform(1.10, 1.22))
        else:
            a = rng.uniform(-math.pi, math.pi); r = rng.uniform(0.2, 0.45)
            c = (r * math.sin(a), -r * math.cos(a), rng.uniform(2.82, 2.95))
        name = bone(f'Debris{k + 1}', c, 'Root')
        chunk(body, c, rng.uniform(0.06, 0.12), name, METAL, MR, 'debris', rng)
    stream = []
    for k in range(12):
        z = 2.86 - (2.86 - 1.10) * k / 11
        stream.append((0.02 * math.sin(k * 1.7), 0.015 * math.cos(k * 2.3), z))
    radii = [0.07 - 0.02 * min(k, 6) / 6 + (0.05 if k == 11 else 0.0) for k in range(12)]
    tube(body, stream, 0.0, 'GooStream', GLOW, GR, 'goo', S(8, 4), radii=radii)
    blob = [[(0.34, 1.045), (0.30, 1.10), (0.22, 1.16), (0.12, 1.21)]]
    lathe(body, blob, 'GooBlob', GLOW, GR, 'goo', S(16, 6),
          rfn=lambda r, z, th: 0.035 * math.sin(4 * th + z * 20) * (1.2 - z + 0.1))
    cap(body, 0.12, 1.21, 'GooBlob', GLOW, GR, 'goo', S(8, 4), up=True)

    # tools/build_actor_lods.py welds coincident vertices before decimating; parts on different bones that share a
    # position (arc variant ends, dome/crown and bowl splits) would then blend their weights in LODs 1-3. A distinct
    # micro-offset per bone (multiples of 0.01 mm, at most 0.64 mm) keeps every part on its own bone.
    order = {name: k for k, (name, _, _) in enumerate(bones)}
    for m in (body, glass):
        m.verts = [(x, y, z + 1e-5 * order[b]) for (x, y, z), b in zip(m.verts, m.bone)]

    sockets = {'Socket_Arc': ('Root', L.ARC_CENTRE)}
    return {'meshes': {'Reactor': body, 'ReactorGlass': glass}, 'bones': bones, 'sockets': sockets}


def report(result):
    out = {}
    for name, m in result['meshes'].items():
        per_bone = {}
        for t in m.tris:
            b = m.bone[t[0]]
            per_bone[b] = per_bone.get(b, 0) + 1
        out[name] = {'triangles': len(m.tris), 'vertices': len(m.verts), 'per_bone': per_bone}
    return out


if __name__ == '__main__':
    import json
    print(json.dumps(report(build()), indent=1))
