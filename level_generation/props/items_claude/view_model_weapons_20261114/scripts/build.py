"""Step 2 (README.md): the model of one weapon kind, built in Blender from parts (lathed shafts and fittings, lofted
diamond-section blades, bevelled plates and boxes), in the arms' Weapon-node frame: the palm at the origin, the head
along +Z (glTF +Y), the edge along X, the flat facing Y (glTF Z); Oblivion units (about 1.43 cm).

Usage: blender --background --python build.py -- <kind>
Writes work/<kind>/model.blend (one triangulated mesh, face attribute `region`) and work/<kind>/model_plain.glb
(grey, for a quick look in the arms).
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vmw  # noqa: E402

KIND = sys.argv[sys.argv.index('--') + 1]


def smooth_leaf(t, base, widest, peak_at):
    """Half width of a leaf blade: from `base` up to `widest` at t = peak_at, then a convex taper to the point."""
    if t <= peak_at:
        s = t / peak_at
        return base + (widest - base) * math.sin(s * math.pi / 2)
    s = (t - peak_at) / (1 - peak_at)
    return widest * (1 - s ** 1.35) ** 0.9


def shaft_profile(z0, z1, r0, r1, bands, wraps, step=12.0):
    """Lathe profile of a wooden shaft from z0 to z1 (radius r0 -> r1) with metal bands [(z, height)] and leather
    wraps [(z_lo, z_hi)] as raised sleeves. Returns (profile, regions per span)."""
    def radius(z):
        return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    events = []
    for z, h in bands:
        events.append((z - h / 2, z + h / 2, 'metal', 0.22))
    for lo, hi in wraps:
        events.append((lo, hi, 'leather', 0.12))
    events.sort()
    profile, regions = [(z0, radius(z0), True)], []
    z = z0
    for lo, hi, region, lift in events:
        # Plain wood up to the event, in steps (keeps the taper and the UV pieces short).
        n = max(1, int(math.ceil((lo - z) / step)))
        for k in range(1, n + 1):
            zz = z + (lo - z) * k / n
            profile.append((zz, radius(zz), k == n))
            regions.append('wood')
        # A raised sleeve with chamfered ends: up, along, down.
        c = min(0.25, (hi - lo) * 0.2)
        r = radius(lo)
        profile.append((lo + c * 0.2, r + lift, True)); regions.append(region)
        n = max(1, int(math.ceil((hi - lo - 2 * c) / step)))
        for k in range(1, n + 1):
            zz = lo + c + (hi - lo - 2 * c) * k / n
            profile.append((zz, radius(zz) + lift, k == n)); regions.append(region)
        profile.append((hi, radius(hi), True)); regions.append(region)
        z = hi
    n = max(1, int(math.ceil((z1 - z) / step)))
    for k in range(1, n + 1):
        zz = z + (z1 - z) * k / n
        profile.append((zz, radius(zz), k == n))
        regions.append('wood')
    return profile, regions


def fluted_sections(z0, length, half_width, ridge, rib, rows, edge=0.07, tip_rows=1, flute=0.55, curve=None):
    """Cross-sections of a leaf blade with a raised central rib and a shallow flute either side (the design masters'
    spear and trident points): per section 16 points, edge, bevel, flute, rib shoulder, rib crest on each face.
    half_width(t), ridge(t) (half thickness at the rib crest), rib(t) (the rib's half width) for t in 0..1; the last
    section is the point."""
    out = []
    for k in range(rows):
        t = k / (rows - 1)
        x0 = curve(t) if curve else 0.0
        if k == rows - 1:
            out.append([(x0, 0.0, z0 + length)])
            break
        w, T, r = half_width(t), ridge(t), min(rib(t), half_width(t) * 0.6)
        e = min(edge, T * 0.4)
        bx = max(0.8 * w, r + 0.05)
        b = max(e * 1.4, T * 0.32)
        fx = (bx + r) * 0.5
        f = b + (T * 0.62 - b) * 0.35 * flute
        s = T * 0.62
        z = z0 + length * t
        face = [(w, e), (bx, b), (fx, f), (r, s), (0.0, T), (-r, s), (-fx, f), (-bx, b)]
        # The front face from +x to -x, the far edge, the back face from -x to +x, the near edge: 18 points.
        pts = [(x, -y) for x, y in face] + [(-w, -e), (-w, e)] + [(x, y) for x, y in reversed(face[1:])] + [(w, e)]
        out.append([(x0 + x, y, z) for x, y in pts])
    return out


FLUTED_SHARP = (0, 1, 3, 4, 5, 7, 8, 9, 10, 12, 13, 14, 16, 17)
# The honed bevels and the thin edges of a fluted section (strip i joins columns i and i + 1).
FLUTED_EDGES = {i: 'edge' for i in (0, 7, 8, 9, 16, 17)}


def knob_bar(b, z, half_len, radius, region='metal', seg=10):
    """A horizontal bar along X through the socket with turned knob ends (the spear's lugs)."""
    before = set(b.bm.verts)
    r = radius
    profile = [(-half_len, 0.0, True), (-half_len + 0.7, r * 0.9, False), (-half_len + 1.25, r * 1.45, False),
               (-half_len + 1.9, r * 1.25, True), (-half_len + 2.25, r * 1.5, True), (-half_len + 2.6, r, True),
               (half_len - 2.6, r, True), (half_len - 2.25, r * 1.5, True), (half_len - 1.9, r * 1.25, True),
               (half_len - 1.25, r * 1.45, False), (half_len - 0.7, r * 0.9, False), (half_len, 0.0, True)]
    b.lathe(profile, seg, region, cap_start=False, cap_end=False)
    verts = [v for v in b.bm.verts if v not in before]
    bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    bmesh.ops.translate(b.bm, verts=verts, vec=(0, 0, z))


def build_spear(b):
    # The design master (work/spear/design): a fluted leaf point with a central rib, a collared steel socket with
    # knobbed lugs, triple brass rings, an ash shaft with a steel band, a spiral leather wrap between brass rings where
    # both hands hold it, a steel ferrule with a spike. The right palm at z = 0, the left hand about 12-15 below; butt
    # at -30, point at +110: 140 units (2.0 m).
    butt, top = -30.0, 110.0
    seg = 14
    # Butt: spike, ferrule with a ring.
    b.lathe([(butt, 0.0, True), (butt + 4.2, 0.85, True), (butt + 4.8, 1.30, True), (butt + 5.6, 1.48, True),
             (butt + 6.4, 1.48, True), (butt + 7.0, 1.30, True), (butt + 10.0, 1.30, True), (butt + 10.4, 1.42, True),
             (butt + 11.2, 1.42, True), (butt + 11.6, 1.24, True)], 10, 'metal', cap_start=False, cap_end=True,
            phase=0.5)
    # Shaft: ash, 2.5 units across at the hands (3.6 cm), slimmer under the head.
    shaft_lo, shaft_hi = butt + 11.3, 79.6
    profile, regions = shaft_profile(shaft_lo, shaft_hi, 1.25, 1.12, bands=[(-23.4, 0.9), (11.6, 0.9), (64.0, 1.6)],
                                     wraps=[(-23.0, 11.2)])
    b.lathe(profile, seg, regions, cap_start=True, cap_end=True)
    # Triple brass rings where the socket meets the wood.
    rings = []
    for k in range(3):
        z = 77.6 + k * 0.75
        rings += [(z, 1.18, True), (z + 0.12, 1.42, False), (z + 0.38, 1.46, False), (z + 0.62, 1.42, False),
                  (z + 0.74, 1.18, True)]
    b.lathe(rings, seg, 'brass', cap_start=True, cap_end=True)
    # Socket: a steel tube with the lug collar close above the rings, then two collar rings under the blade.
    b.lathe([(79.8, 1.30, True), (80.2, 1.34, True), (81.2, 1.22, False), (81.5, 1.42, True), (83.8, 1.42, True),
             (84.1, 1.12, True), (86.4, 1.02, False), (86.7, 1.26, True), (87.5, 1.26, True), (87.8, 0.98, True),
             (88.05, 1.16, True), (88.75, 1.16, True), (89.0, 0.72, True), (89.4, 0.44, True)],
            seg, 'metal', cap_start=True, cap_end=True)
    knob_bar(b, 82.65, 6.6, 0.44)
    # The point: 21.5 units (31 cm) of fluted leaf on a short stem, widest a third of the way up; the rib runs down
    # into the socket.
    z0, length = 88.5, top - 88.5

    def width(t):
        if t < 0.08:
            return 0.5 + (t / 0.08) * 0.45
        return smooth_leaf((t - 0.08) / 0.92, 0.95, 3.1, 0.3)
    sections = fluted_sections(z0, length, width, ridge=lambda t: 0.7 - 0.5 * t, rib=lambda t: 0.4 - 0.26 * t,
                               rows=19)
    b.loft(sections, 'blade', cap_start=True, cap_end=False, sharp_columns=FLUTED_SHARP, strip_regions=FLUTED_EDGES)


def bezier(p0, c, p1, n):
    """n points of a quadratic Bezier from p0 to p1 (p0 included, p1 excluded)."""
    out = []
    for k in range(n):
        t = k / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]))
    return out


def arc3(p0, pm, p1, n):
    """n points of the circle arc from p0 through pm to p1 (p0 included, p1 excluded)."""
    (ax, ay), (bx, by), (cx, cy) = p0, pm, p1
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in (p0, pm, p1))

    def between(a, s, e):
        return (a - s) % (2 * math.pi) <= (e - s) % (2 * math.pi)
    if between(am, a0, a1):
        span = (a1 - a0) % (2 * math.pi)
    else:
        span = -((a0 - a1) % (2 * math.pi))
    return [(ux + r * math.cos(a0 + span * k / n), uy + r * math.sin(a0 + span * k / n)) for k in range(n)]


def build_halberd(b):
    # The design master (work/halberd/design): a faceted top spike over two collar rings, a crescent axe blade (to -X)
    # and a down-hooked beak (to +X) on a steel socket with gilded side clamps, a studded langet down the front and
    # back, an ash shaft with bands, a leather wrap where both hands hold it, a rounded butt cap. Right palm at z = 0;
    # butt at -22, spike tip at +98: 120 units (1.7 m; the head drawn DROP lower than first built, so the two-handed
    # swings bring it into view: README.md "Held length").
    seg = 14
    b.lathe([(-22.0, 0.0, True), (-21.7, 0.8, False), (-21.2, 1.25, False), (-20.5, 1.42, True), (-18.6, 1.42, True),
             (-18.2, 1.22, True)], 12, 'metal', cap_start=False, cap_end=True)
    drop = 22.0
    profile, regions = shaft_profile(-18.4, 82.5 - drop, 1.25, 1.17, bands=[(-16.2, 0.9), (10.4, 0.9), (24.0, 0.8),
                                                                            (26.0, 0.8)], wraps=[(-15.6, 9.8)])
    b.lathe(profile, seg, regions, cap_start=True, cap_end=True)
    shaft_verts = set(b.bm.verts)
    # Socket and collars.
    b.lathe([(81.8, 1.30, True), (82.2, 1.42, True), (96.6, 1.36, True), (96.9, 1.10, True), (97.2, 1.32, True),
             (98.0, 1.32, True), (98.3, 1.04, True), (98.6, 1.26, True), (99.3, 1.26, True), (99.6, 0.9, True)],
            seg, 'metal', cap_start=True, cap_end=True)
    # Top spike: a flattened diamond, faceted.
    b.lathe([(99.4, 0.85, True), (101.6, 1.3, True), (103.2, 1.08, True), (120.0, 0.0, True)], 4, 'blade',
            cap_start=True, cap_end=False, scale_xy=(1.0, 0.62), facet=True)
    # Axe blade (CCW from the socket's top): upper edge, cutting edge (honed), lower edge, socket side.
    upper = bezier((-1.3, 95.2), (-7.5, 93.0), (-13.6, 103.5), 6)
    cut = arc3((-13.6, 103.5), (-18.6, 86.5), (-12.2, 69.0), 12)
    lower = bezier((-12.2, 69.0), (-6.0, 83.5), (-1.3, 85.0), 7)
    outline = upper + cut + lower
    inset = [0.5] * len(upper) + [0.55] + [1.7] * (len(cut) - 1) + [0.55] + [0.5] * (len(lower) - 1)
    inset[0] = 0.3
    inset[-1] = 0.3
    honed = list(range(len(upper), len(upper) + len(cut)))
    b.plate(outline, 0.95, 'blade', edge=0.06, bevel_in=inset, edge_segments=honed)
    # Beak (CCW from the socket's lower attachment): the honed lower edge to the hooked tip, the back up to the socket.
    lower = bezier((1.3, 89.6), (7.5, 92.0), (11.8, 84.0), 6)
    back = bezier((11.8, 84.0), (11.0, 96.5), (1.3, 94.4), 7)
    outline = lower + back
    inset = [0.3] + [0.6] * (len(lower) - 1) + [0.25] + [0.45] * (len(back) - 1)
    b.plate(outline, 0.9, 'blade', edge=0.06, bevel_in=inset, edge_segments=list(range(len(lower))))
    # Gilded clamps either side of the socket, each with a curled foot.
    for s in (-1, 1):
        b.box((s * 1.72, 0.0, 91.2), (0.7, 2.5, 9.6), 'brass', bevel=0.18)
        b.box((s * 1.95, 0.0, 86.0), (0.9, 1.7, 1.5), 'brass', bevel=0.25)
        b.box((s * 1.6, 0.0, 84.6), (0.6, 1.1, 1.6), 'brass', bevel=0.2)
    # Langets down the front and back with pyramid studs.
    for s in (-1, 1):
        b.box((0.0, s * 1.33, 78.0), (2.0, 0.36, 32.0), 'metal', bevel=0.1)
        for k in range(5):
            b.box((0.0, s * 1.68, 64.5 + k * 6.4), (0.75, 0.42, 0.75), 'brass', bevel=0.17)
    bmesh.ops.translate(b.bm, verts=[v for v in b.bm.verts if v not in shaft_verts], vec=(0.0, 0.0, -drop))


def sweep(b, path, half_width, half_thick, region, sides=8, sharp=(0, 4)):
    """A tube swept along a 2D path in the XZ plane [(x, z)], its section an ellipse of half_width(t) in the plane
    and half_thick(t) along Y (t: 0..1 along the path); a zero half width at an end is a point."""
    n = len(path)
    lengths = [0.0]
    for (x0, z0), (x1, z1) in zip(path[:-1], path[1:]):
        lengths.append(lengths[-1] + math.hypot(x1 - x0, z1 - z0))
    sections = []
    for i, (x, z) in enumerate(path):
        t = lengths[i] / lengths[-1]
        a, c = path[max(i - 1, 0)], path[min(i + 1, n - 1)]
        tx, tz = c[0] - a[0], c[1] - a[1]
        norm = math.hypot(tx, tz)
        nx, nz = -tz / norm, tx / norm
        w, th = half_width(t), half_thick(t)
        if w <= 1e-6:
            sections.append([(x, 0.0, z)])
            continue
        sections.append([(x + nx * w * math.cos(2 * math.pi * k / sides), th * math.sin(2 * math.pi * k / sides),
                          z + nz * w * math.cos(2 * math.pi * k / sides)) for k in range(sides)])
    b.loft(sections, region, cap_start=len(sections[0]) > 1, cap_end=len(sections[-1]) > 1, sharp_columns=sharp)
    return sections


def ring_at(b, centre, direction, radius, length, region='brass', seg=12):
    """A short collar ring around a prong at a point of the XZ plane, along a direction in that plane."""
    before = set(b.bm.verts)
    h = length / 2
    b.lathe([(-h, radius * 0.86, True), (-h + 0.18, radius, True), (h - 0.18, radius, True), (h, radius * 0.86, True)],
            seg, region, cap_start=True, cap_end=True)
    verts = [v for v in b.bm.verts if v not in before]
    angle = math.atan2(direction[0], direction[1])
    bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(angle, 3, 'Y'))
    bmesh.ops.translate(b.bm, verts=verts, vec=(centre[0], 0.0, centre[1]))


def build_trident(b):
    # The design master (work/trident/design): a long straight middle point, two side prongs rising from a curved
    # cross-piece and flaring out, barbed near the tips, a gilded boss with a set stone where they meet, gilded rings
    # at the cross-piece's ends, a socket with gilded collars, an ash shaft with bands and a leather wrap, a butt cap.
    # Right palm at z = 0; butt at -22, middle point at +96: 118 units (1.7 m; the head drawn DROP lower than first
    # built, README.md "Held length").
    seg = 14
    b.lathe([(-22.0, 0.0, True), (-21.5, 0.75, False), (-20.8, 1.2, False), (-20.0, 1.42, True), (-18.6, 1.42, True),
             (-18.2, 1.22, True)], 12, 'metal', cap_start=False, cap_end=True)
    drop = 24.0
    profile, regions = shaft_profile(-18.4, 76.4 - drop, 1.25, 1.17, bands=[(-16.2, 0.9), (10.4, 0.9), (28.0, 1.4),
                                                                            (42.0, 0.8)], wraps=[(-15.6, 9.8)])
    b.lathe(profile, seg, regions, cap_start=True, cap_end=True)
    shaft_verts = set(b.bm.verts)
    # Socket with gilded collars.
    b.lathe([(76.0, 1.28, True), (76.3, 1.40, True), (79.6, 1.36, True), (79.8, 1.62, True), (82.4, 1.62, True),
             (82.6, 1.34, True), (86.2, 1.30, True), (86.4, 1.55, True), (87.6, 1.55, True), (87.8, 1.2, True),
             (88.6, 1.0, True)], seg, 'metal', cap_start=True, cap_end=True)
    b.lathe([(79.75, 1.6, True), (79.9, 1.66, True), (82.3, 1.66, True), (82.45, 1.6, True)], seg, 'brass')
    b.lathe([(86.35, 1.53, True), (86.5, 1.6, True), (87.5, 1.6, True), (87.65, 1.53, True)], seg, 'brass')
    # The cross-piece and side prongs: one sweep from the left tip to the right tip.
    left = [(-10.6, 115.5), (-9.7, 111.6), (-9.1, 107.4), (-8.7, 103.0), (-8.0, 99.0), (-7.0, 95.5), (-5.6, 92.6),
            (-3.8, 90.6), (-1.9, 89.4), (0.0, 89.0)]
    path = left + [(-x, z) for x, z in reversed(left[:-1])]

    def hw(t):
        d = min(t, 1 - t)          # 0 at the tips, 0.5 at the middle
        if d < 0.16:
            return 0.95 * (d / 0.16) ** 0.8
        return 0.95 + 0.45 * min((d - 0.16) / 0.25, 1.0)

    def ht(t):
        d = min(t, 1 - t)
        return 0.62 if d > 0.16 else 0.62 * max(d / 0.16, 0.25)
    sweep(b, path, hw, ht, 'blade', sides=8)
    # Barbs on the inner side of the side prongs, pointing down and in.
    for s in (-1, 1):
        outline = [(-8.55, 108.9), (-7.1, 105.6), (-8.4, 107.1)]
        if s > 0:
            outline = [(-x, z) for x, z in reversed(outline)]
        b.plate(outline, 0.55, 'blade', edge=0.05, bevel_in=[0.12, 0.08, 0.12])
        ring_at(b, (s * 7.4, 96.6), (s * 0.35, 1.0), 1.25, 1.4)
    # Middle point: a long diamond blade rising out of the boss.
    sections = vmw.blade_sections(89.5, 30.5, half_width=lambda t: 1.25 + 0.5 * math.sin(min(t / 0.12, 1) * 1.57)
                                  if t < 0.12 else 1.75 * (1 - (t - 0.12) / 0.88) ** 0.8,
                                  ridge=lambda t: 0.78 - 0.5 * t, edge=0.06, bevel=0.78, rows=12)
    b.loft(sections, 'blade', cap_start=True, cap_end=False, sharp_columns=vmw.BLADE_SHARP,
           strip_regions={0: 'edge', 3: 'edge', 4: 'edge', 5: 'edge', 8: 'edge', 9: 'edge'})
    # The boss: a gilded disc across the cross-piece with a domed stone front and back.
    before = set(b.bm.verts)
    b.lathe([(-1.05, 1.7, True), (-0.95, 2.05, True), (0.95, 2.05, True), (1.05, 1.7, True)], 16, 'brass')
    b.lathe([(1.0, 1.15, True), (1.25, 1.05, False), (1.5, 0.75, False), (1.62, 0.0, False)], 16, 'gem', cap_start=True,
            cap_end=False)
    b.lathe([(-1.62, 0.0, False), (-1.5, 0.75, False), (-1.25, 1.05, False), (-1.0, 1.15, True)], 16, 'gem',
            cap_start=False, cap_end=True)
    verts = [v for v in b.bm.verts if v not in before]
    bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'X'))
    bmesh.ops.translate(b.bm, verts=verts, vec=(0.0, 0.0, 91.4))
    bmesh.ops.translate(b.bm, verts=[v for v in b.bm.verts if v not in shaft_verts], vec=(0.0, 0.0, -drop))


def build_wand(b):
    # The design master (work/wand/design): a faceted crystal held by four curved claws in a flared cup, a gilded ring,
    # a faceted collar, a slim rod with two rings, a leather grip and a turned pommel. 25 units (36 cm); the palm at
    # z = 0 a fifth of the way up.
    seg = 12
    # Pommel and grip.
    b.lathe([(-5.6, 0.0, True), (-5.45, 0.55, False), (-5.1, 0.95, False), (-4.6, 1.08, True), (-4.2, 0.92, True),
             (-3.9, 1.02, True), (-3.5, 1.02, True), (-3.3, 0.86, True)], seg, 'metal', cap_start=False)
    b.lathe([(-3.4, 0.86, True), (-3.3, 0.98, True), (2.3, 0.94, True), (2.4, 0.8, True)], seg, 'leather')
    b.lathe([(2.3, 0.86, True), (2.45, 1.0, True), (3.05, 1.0, True), (3.2, 0.74, True)], seg, 'metal')
    # Rod with two rings.
    b.lathe([(3.1, 0.72, True), (8.0, 0.66, False), (8.1, 0.66, True), (8.25, 0.8, True), (8.75, 0.8, True),
             (8.9, 0.64, True), (11.9, 0.6, True), (12.05, 0.76, True), (12.55, 0.76, True), (12.7, 0.6, True),
             (14.4, 0.6, True)], seg, ['wood', 'wood', 'metal', 'metal', 'metal', 'wood', 'metal', 'metal', 'metal',
                                       'wood'])
    # Faceted collar, gilded ring, flared cup.
    b.lathe([(14.2, 0.62, True), (14.4, 0.9, True), (16.2, 0.9, True), (16.35, 0.72, True)], 8, 'metal', facet=True)
    b.lathe([(16.3, 0.8, True), (16.45, 1.02, True), (17.05, 1.02, True), (17.2, 0.82, True)], seg, 'brass')
    b.lathe([(17.1, 0.74, True), (17.6, 0.82, False), (18.2, 1.1, False), (18.5, 1.28, True), (18.75, 1.2, True),
             (18.75, 0.9, True)], seg, 'metal', cap_end=True)
    # Crystal: a long hexagonal point.
    b.lathe([(17.6, 0.0, True), (18.6, 0.92, True), (22.4, 1.02, True), (25.0, 0.0, True)], 6, 'gem', cap_start=False,
            cap_end=False, facet=True)
    # Four claws from the cup's rim up around the crystal.
    for k in range(4):
        before = set(b.bm.verts)
        path = [(1.0, 18.4), (1.5, 19.0), (1.78, 20.0), (1.72, 21.1), (1.42, 22.1), (1.02, 22.9), (0.86, 23.3)]
        sweep(b, path, lambda t: 0.5 * (1 - t) + 0.08, lambda t: 0.26 * (1 - 0.6 * t), 'metal', sides=6, sharp=(0, 3))
        verts = [v for v in b.bm.verts if v not in before]
        bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 4 + k * math.pi / 2, 3,
                                                                                    'Z'))


def lathe_x(b, profile, seg, region, x0, z0, direction=-1.0, y0=0.0, **kw):
    """A lathe along X from x0 (toward -X with direction -1) at height z0: profile [(s, r, sharp)] with s the distance
    from x0."""
    before = set(b.bm.verts)
    b.lathe(profile, seg, region, **kw)
    verts = [v for v in b.bm.verts if v not in before]
    bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.pi / 2 * (1 if direction > 0 else -1), 3, 'Y'))
    bmesh.ops.translate(b.bm, verts=verts, vec=(x0, y0, z0))


def cylinder_between(b, p0, p1, radius, region, seg=6):
    """A thin round rod from p0 to p1 (a cord)."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    before = set(b.bm.verts)
    b.lathe([(0.0, radius, True), (d.length, radius, True)], seg, region)
    verts = [v for v in b.bm.verts if v not in before]
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix()
    bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=rot)
    bmesh.ops.translate(b.bm, verts=verts, vec=p0)


def build_blaster(b):
    # The design master (work/blaster/design): an Ancients' ray pistol, 30 cm: a body with an energy-cell window under
    # a top bar, a domed back with a set stone, a sight rail, a ribbed barrel between copper rings ending in a flared
    # emitter and a copper tip, a spur under the barrel, a hooked trigger guard, a raked grip with a pommel cap.
    # Built in the arms' Gun frame (game/render/HeldWeapons.h): the palm at the origin, the muzzle along -X, the grip
    # down (-Z here, glTF -Y), the width along Y.
    # Grip and pommel.
    grip = [(0.45, 1.5), (0.2, 0.0), (0.45, -2.0), (1.05, -4.0), (1.7, -5.6), (2.0, -6.3)]
    sweep(b, grip, lambda t: 1.42, lambda t: 1.06, 'wood', sides=12, sharp=())
    b.box((2.15, 0.0, -6.55), (3.4, 2.5, 0.8), 'metal', bevel=0.3, matrix=Matrix.Rotation(-0.36, 4, 'Y'))
    # Body: lower block, the cell's frame (top bar, front and back posts), the cell.
    b.box((-0.5, 0.0, 2.3), (9.5, 2.5, 2.2), 'metal', bevel=0.3)
    b.box((-0.5, 0.0, 5.55), (9.5, 2.3, 0.75), 'metal', bevel=0.22)
    b.box((-4.65, 0.0, 4.4), (1.2, 2.5, 2.4), 'metal', bevel=0.25)
    b.box((3.65, 0.0, 4.4), (1.2, 2.5, 2.4), 'metal', bevel=0.25)
    lathe_x(b, [(0.0, 0.88, True), (6.2, 0.88, True)], 14, 'glow', 2.6, 4.4, direction=-1.0)
    for x in (-2.4, 0.4):
        b.box((x, 0.0, 4.4), (0.45, 2.0, 2.0), 'brass', bevel=0.12)
    # Domed back with a set stone, the sight rail.
    lathe_x(b, [(0.0, 1.55, True), (0.5, 1.6, True), (1.0, 1.45, False), (1.5, 1.0, False), (1.8, 0.0, False)], 14,
            'metal', 4.25, 3.8, direction=1.0, cap_start=True, cap_end=False)
    before = set(b.bm.verts)
    b.lathe([(0.0, 0.52, True), (0.2, 0.5, False), (0.45, 0.3, False), (0.55, 0.0, False)], 10, 'gem',
            cap_start=True, cap_end=False)
    bmesh.ops.translate(b.bm, verts=[v for v in b.bm.verts if v not in before], vec=(3.2, 0.0, 5.9))
    b.box((-0.6, 0.0, 6.75), (6.6, 0.55, 0.5), 'metal', bevel=0.12)
    for x in (-3.3, 2.1):
        b.box((x, 0.0, 6.2), (0.55, 0.55, 1.1), 'metal', bevel=0.12)
    # Barrel: copper rings, ribs, copper rings, a tube, the flared emitter and a copper tip.
    prof = [(0.0, 1.12, True), (0.15, 1.3, True), (0.75, 1.3, True), (0.85, 1.12, True), (0.95, 1.3, True),
            (1.55, 1.3, True), (1.7, 0.95, True)]
    s0 = 1.9
    for k in range(9):
        a = s0 + k * 0.62
        prof += [(a, 0.86, True), (a + 0.08, 1.12, True), (a + 0.34, 1.12, True), (a + 0.42, 0.86, True)]
    a = s0 + 9 * 0.62 + 0.2
    prof += [(a, 0.95, True), (a + 0.1, 1.28, True), (a + 0.7, 1.28, True), (a + 0.8, 1.1, True), (a + 0.9, 1.28, True),
             (a + 1.5, 1.28, True), (a + 1.6, 0.86, True), (a + 3.0, 0.82, True), (a + 3.1, 0.95, True),
             (a + 4.9, 1.32, True), (a + 5.1, 1.1, True), (a + 5.3, 0.95, False), (a + 6.0, 0.7, False),
             (a + 6.4, 0.0, False)]
    lathe_x(b, prof, 14, 'metal', -5.2, 3.05, direction=-1.0, cap_start=True, cap_end=False)
    # The spur under the barrel, the trigger guard and the trigger.
    b.plate([(-5.3, 1.35), (-6.2, 1.9), (-9.6, 1.05), (-6.7, 0.55)], 0.55, 'metal', edge=0.08, bevel_in=0.18)
    sweep(b, [(-4.7, 1.25), (-5.0, 0.0), (-4.3, -1.25), (-2.7, -1.65), (-1.1, -1.25), (-0.5, -0.6)],
          lambda t: 0.3, lambda t: 0.36, 'metal', sides=6, sharp=(0, 3))
    sweep(b, [(-2.0, 1.25), (-2.45, 0.45), (-2.25, -0.35)], lambda t: 0.22 * (1 - 0.4 * t), lambda t: 0.2, 'metal',
          sides=6, sharp=(0, 3))


def build_crossbow(b):
    # The design master (work/crossbow/design 01_top, attempt1 side): a polished stock with a flared butt and a laced
    # leather grip, a steel prod with recurved tips bound across the front with steel bands, a cord drawn back to a
    # round nut, a bolt with fletching in its groove, a long trigger lever, a foot stirrup. Built in the left hand's
    # Torch frame at the bow set's full draw (README.md "Crossbow hold"): the bolt along +X (where the bow shoots),
    # up +Z here (glTF +Y), the prod across Y; the left fist closes on a short vertical foregrip at the origin.
    def section(x, w, h, zc, cheek=0.0):
        # 2026-11-14 rework (README.md "Crossbow tiller"): a shaped tiller instead of a box: squarer shoulders on top
        # (the groove), a rounder belly, 20 sides; on the butt a cheek piece swells out of the left side (+Y here, the
        # side the shooter's cheek rests on).
        n = 20
        pts = []
        for k in range(n):
            a = 2 * math.pi * k / n
            c, s_ = math.cos(a), math.sin(a)
            e = 0.55 if s_ > 0 else 0.85
            y = w * math.copysign(abs(c) ** e, c)
            if c > 0 and cheek > 0.0:
                # The pad: widest a little above the middle, fading to nothing at the comb and the belly.
                y += cheek * math.exp(-((a if a < math.pi else a - 2 * math.pi) - 0.3) ** 2 / 0.35)
            pts.append((x, y, zc + h * math.copysign(abs(s_) ** e, s_)))
        return pts
    # (x, half width, half height, centre height, cheek): a slim fore-end, the full depth at the lock, a narrower wrist
    # under the laced grip (the right fist's place: README.md "Crossbow hold"), then the butt deepening below a
    # straight comb into a tapered, slightly narrowing end with the cheek piece.
    stock = [(-34.0, 1.66, 3.25, 2.45, 0.0), (-32.6, 1.74, 3.3, 2.4, 0.3), (-29.0, 1.8, 3.2, 2.5, 0.5),
             (-25.5, 1.78, 2.95, 2.75, 0.55), (-22.0, 1.7, 2.55, 3.15, 0.4), (-19.0, 1.6, 2.1, 3.6, 0.12),
             (-16.5, 1.52, 1.82, 3.9, 0.0), (-13.0, 1.45, 1.72, 4.0, 0.0), (-9.5, 1.52, 1.75, 4.0, 0.0),
             (-6.5, 1.72, 1.85, 3.95, 0.0), (-3.0, 1.78, 1.85, 3.92, 0.0), (4.0, 1.72, 1.75, 4.0, 0.0),
             (12.0, 1.6, 1.55, 4.2, 0.0), (17.0, 1.45, 1.35, 4.4, 0.0), (20.0, 1.3, 1.15, 4.6, 0.0)]
    sections = [section(*station) for station in stock]
    b.loft(sections, 'wood', cap_start=True, cap_end=True)
    # Butt plate (gilt or iron by tier: 'brass'), the laced grip sleeve over the wrist.
    b.box((-34.25, 0.0, 2.45), (0.6, 3.5, 6.75), 'brass', bevel=0.2)
    before = set(b.bm.verts)
    lathe_x(b, [(0.0, 1.0, True), (6.0, 1.0, True)], 12, 'leather', -16.0, 4.15, direction=1.0, scale_xy=(1.0, 1.0))
    for v in [v for v in b.bm.verts if v not in before]:
        v.co.y *= 1.72
        v.co.z = 3.95 + (v.co.z - 4.15) * 1.95
    # Lock plates either side of the nut, each set with a stone (iron bosses on the low tier, rubies on the high one,
    # glowing on the legendary), and a stone in the nose.
    for side in (-1.0, 1.0):
        b.box((-3.6, side * 1.8, 4.25), (6.4, 0.16, 2.3), 'metal', bevel=0.06)
        before = set(b.bm.verts)
        b.lathe([(0.0, 0.62, True), (0.16, 0.6, False), (0.38, 0.4, False), (0.48, 0.0, False)], 10, 'gem',
                cap_start=True, cap_end=False)
        stone = [v for v in b.bm.verts if v not in before]
        bmesh.ops.rotate(b.bm, verts=stone, cent=(0, 0, 0), matrix=Matrix.Rotation(-side * math.pi / 2, 3, 'X'))
        bmesh.ops.translate(b.bm, verts=stone, vec=(-3.6, side * 1.86, 4.1))
    before = set(b.bm.verts)
    b.lathe([(0.0, 0.55, True), (0.14, 0.53, False), (0.34, 0.35, False), (0.42, 0.0, False)], 10, 'gem',
            cap_start=True, cap_end=False)
    stone = [v for v in b.bm.verts if v not in before]
    bmesh.ops.rotate(b.bm, verts=stone, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, 'Y'))
    bmesh.ops.translate(b.bm, verts=stone, vec=(20.02, 0.0, 4.55))
    # Groove rails on top, the nut, the bolt with its head and fletching.
    for y in (-0.55, 0.55):
        b.box((3.0, y, 5.82), (32.0, 0.4, 0.35), 'wood', bevel=0.1)
    b.lathe([(5.4, 0.0, True), (5.45, 1.0, True), (6.5, 1.0, True), (6.6, 0.75, True)], 12, 'metal', center=(-5.0, 0.0),
            cap_start=False, cap_end=True)
    lathe_x(b, [(0.0, 0.3, True), (21.5, 0.3, True), (21.7, 0.5, True), (23.6, 0.0, True)], 8,
            ['wood', 'metal', 'metal'], -4.5, 6.2, direction=1.0)
    for a in (0.0, 2.094, 4.189):
        before = set(b.bm.verts)
        b.plate([(0.0, 0.25), (3.2, 0.25), (2.4, 1.15), (0.6, 0.95)], 0.12, 'string', edge=0.04, bevel_in=0.08)
        verts = [v for v in b.bm.verts if v not in before]
        bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(a + 0.6, 3, 'X'))
        bmesh.ops.translate(b.bm, verts=verts, vec=(-3.6, 0.0, 6.2))
    # Prod: a steel bar across Y, its middle forward at x 17, the tips recurved back to x 12; bound by two bands.
    half = [(17.0, 0.0), (16.7, 2.6), (15.7, 6.5), (14.0, 11.0), (12.2, 15.0), (11.3, 18.0), (11.4, 19.6), (12.0, 20.6)]
    path = [(-a, f) for f, a in reversed(half[1:])] + [(0.0, 17.0)] + [(a, f) for f, a in half[1:]]
    before = set(b.bm.verts)

    def pw(t):
        d = min(t, 1 - t)
        return 0.3 + 0.55 * min(d / 0.5, 1.0)
    sweep(b, path, lambda t: 0.3 + 0.12 * (1 - abs(2 * t - 1)), pw, 'metal', sides=8, sharp=(0, 4))
    # The sweep lies in XZ (x across, z forward, y its thickness): across -> Y, forward -> X, thickness -> up.
    for v in [v for v in b.bm.verts if v not in before]:
        x, y, z = v.co
        v.co = Vector((z, x, 4.6 + y))
    for x in (15.6, 18.4):
        b.box((x, 0.0, 4.2), (0.7, 3.6, 4.0), 'brass', bevel=0.15)
    # Cord from the tips to the nut.
    for side in (-1, 1):
        cylinder_between(b, (12.0, side * 20.4, 4.6), (-5.0, side * 0.3, 6.0), 0.13, 'string')
    # Stirrup at the front, the trigger lever under the rear stock, the foregrip in the left fist.
    b.box((24.4, -2.4, 4.3), (8.0, 0.5, 0.55), 'metal', bevel=0.12)
    b.box((24.4, 2.4, 4.3), (8.0, 0.5, 0.55), 'metal', bevel=0.12)
    b.box((28.0, 0.0, 4.3), (0.55, 5.3, 0.55), 'metal', bevel=0.12)
    # The lever hugs the tiller's belly (the rework deepened the butt below it).
    sweep(b, [(-8.5, 2.75), (-11.5, 1.85), (-16.0, 1.6), (-19.5, 1.05), (-22.5, 0.2)], lambda t: 0.32,
          lambda t: 0.3, 'metal', sides=6, sharp=(0, 3))
    b.lathe([(-4.4, 0.0, True), (-4.2, 1.2, True), (-3.6, 1.42, True), (-2.6, 1.3, True), (2.4, 1.32, True),
             (3.0, 1.15, True)], 12, 'wood', cap_start=False, cap_end=True)
    # The rear stock shortened (x < -6 to 0.79): at full draw a full-length butt sat a hand's width in front of the
    # eye and filled the lower right of the screen (README.md "Crossbow hold").
    for v in b.bm.verts:
        if v.co.x < -6.0:
            v.co.x = -6.0 + (v.co.x + 6.0) * 0.79


def catmull_rom(points, z):
    """Radius at z on a Catmull-Rom curve through [(z, r)] (z ascending; clamped at the ends)."""
    zs = [p[0] for p in points]
    if z <= zs[0]:
        return points[0][1]
    if z >= zs[-1]:
        return points[-1][1]
    i = max(k for k in range(len(zs) - 1) if zs[k] <= z)
    p0, p1, p2, p3 = (points[max(i - 1, 0)], points[i], points[i + 1], points[min(i + 2, len(points) - 1)])
    t = (z - p1[0]) / (p2[0] - p1[0])
    m1 = (p2[1] - p0[1]) / (p2[0] - p0[0]) * (p2[0] - p1[0])
    m2 = (p3[1] - p1[1]) / (p3[0] - p1[0]) * (p2[0] - p1[0])
    return ((2 * t ** 3 - 3 * t ** 2 + 1) * p1[1] + (t ** 3 - 2 * t ** 2 + t) * m1
            + (-2 * t ** 3 + 3 * t ** 2) * p2[1] + (t ** 3 - t ** 2) * m2)


def build_club(b):
    # The design master (work/club/design, from the item077/club1/7item058/club2 icons): one piece of gnarled hardwood,
    # a knotted shaft swelling into an egg-shaped knob, a riveted iron band at the knob's neck and another near its top,
    # pyramid iron studs over the knob (three above the top band), a criss-cross rawhide wrap over the handle, a thin
    # band and a rounded knob at the butt. Held like the mace (the one-handed set's Weapon node): the palm at z = 0,
    # butt at -10.5, top at +44.85: 55 units (79 cm, make_held_table.py's club length). The handle 2.6 across under the
    # wrap, 2.88 over it (the fist closes on radius 1.38).
    seg = 18
    core = [(-7.5, 1.3), (6.6, 1.33), (12.0, 1.45), (18.0, 1.6), (24.0, 1.8), (27.0, 1.95), (28.4, 2.02),
            (29.6, 2.45), (31.5, 3.4), (33.5, 4.1), (36.0, 4.45), (38.5, 4.4), (40.8, 4.05), (42.2, 3.6),
            (43.4, 2.9), (44.3, 2.0), (44.85, 0.9)]
    bands = [(27.4, 28.8), (40.8, 42.2)]
    wrap = (-8.4, 6.6)
    # Burls (angle, height, bump): two big knots on the shaft as on the design, lumps on the knob.
    knots = ((0.4, 13.0, 0.85), (3.7, 20.0, 0.8), (5.2, 16.4, 0.4), (2.4, 33.0, 0.55), (5.3, 36.6, 0.5), (0.6, 31.4, 0.42),
             (4.0, 38.8, 0.4), (1.5, 37.2, 0.38), (3.4, 43.4, 0.3))

    def gnarl(theta, z):
        """Radial displacement of the wood: lengthwise ridges growing toward the knob, the burls. Small on the wrap
        and the iron bands (they stay nearly round)."""
        grow = min(max((z - 6.6) / 22.0, 0.0), 1.0)
        amp = 0.08 + 0.3 * grow
        if any(lo - 0.3 <= z <= hi + 0.3 for lo, hi in bands) or wrap[0] <= z <= wrap[1]:
            amp *= 0.25
        d = amp * (0.5 * math.sin(3 * theta + 0.35 * z + 1.0) + 0.3 * math.sin(5 * theta - 0.6 * z + 2.0)
                   + 0.2 * math.sin(2 * theta + 0.17 * z) + 0.15 * math.sin(9 * theta + 0.05 * z))
        if not (wrap[0] <= z <= wrap[1]):
            for kt, kz, ka in knots:
                dt = math.atan2(math.sin(theta - kt), math.cos(theta - kt))
                d += ka * math.exp(-(dt / 0.5) ** 2 - ((z - kz) / 1.7) ** 2)
        return d

    def radius(z):
        return catmull_rom(core, z)

    def ring(z, sharp=False, lift=0.0):
        return (z, radius(z) + lift, sharp)

    # The profile: butt knob, butt band, wrap (a raised sleeve), the shaft's wood rings about 2 units apart (one at
    # the upload's cut, z 18), the neck band, the knob, the top band, the domed top.
    profile = [(-10.5, 0.55, True), (-10.25, 1.05, False), (-9.85, 1.5, False), (-9.3, 1.72, False),
               (-8.75, 1.6, False), (-8.45, 1.3, True)]
    regions = ['wood'] * 5
    profile += [(-8.35, 1.5, True), (-7.7, 1.5, True), (-7.6, 1.3, True)]
    regions += ['metal'] * 3
    profile += [(-7.5, 1.44, True), (-4.0, 1.44, False), (0.0, 1.44, False), (3.5, 1.44, False), (6.45, 1.46, True),
                (6.6, 1.33, True)]
    regions += ['leather'] * 6
    for z in (8.6, 10.6, 12.0, 13.0, 14.2, 16.2, 18.0, 19.0, 20.0, 21.2, 23.0, 25.2, 27.4):
        profile.append(ring(z, z == 27.4))
        regions.append('wood')
    profile += [ring(27.5, True, 0.22), ring(28.7, True, 0.22), ring(28.8, True)]
    regions += ['metal'] * 3
    for z in (29.8, 30.8, 31.8, 32.8, 33.8, 35.0, 36.2, 37.4, 38.6, 39.7, 40.8):
        profile.append(ring(z, z == 40.8))
        regions.append('wood')
    profile += [ring(40.9, True, 0.2), ring(42.1, True, 0.2), ring(42.2, True)]
    regions += ['metal'] * 3
    for z in (42.9, 43.5, 44.0, 44.4, 44.7, 44.85):
        profile.append(ring(z))
        regions.append('wood')
    before = set(b.bm.verts)
    b.lathe(profile, seg, regions, cap_start=True, cap_end=True, scale_xy=(1.0, 0.95))
    for v in b.bm.verts:
        if v in before:
            continue
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-6:
            continue
        theta = math.atan2(v.co.y, v.co.x)
        # Damped on the narrow domed top and the caps' inner rings (no folding).
        k = (r + gnarl(theta, v.co.z) * min(1.0, r / 2.5)) / r
        v.co.x *= k
        v.co.y *= k

    def surface(theta, z):
        r = radius(z) * (1.0 - 0.05 * math.sin(theta) ** 2)
        return r + gnarl(theta, z) * min(1.0, r / 2.5)

    def place(verts, theta, z, tilt, depth):
        """Turns a part built along +Z outward at angle theta, tilted up by `tilt` degrees, onto the surface."""
        bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90 - tilt), 3, 'Y'))
        bmesh.ops.rotate(b.bm, verts=verts, cent=(0, 0, 0), matrix=Matrix.Rotation(theta, 3, 'Z'))
        r = surface(theta, z) - depth
        bmesh.ops.translate(b.bm, verts=verts, vec=(r * math.cos(theta), r * math.sin(theta), z))

    # Twelve pyramid iron studs: four and five in two rows on the knob, three above the top band.
    studs = [(32.2, a, 8) for a in (30, 120, 210, 300)] + [(36.6, a, 10) for a in (0, 72, 144, 216, 288)] + \
            [(43.5, a, 42) for a in (60, 180, 300)]
    for z, deg, tilt in studs:
        before = set(b.bm.verts)
        size = 0.72 if z > 43 else 0.88
        b.lathe([(-0.6, size, True), (0.0, size, True), (1.55 * size / 0.88, 0.0, True)], 4, 'metal',
                cap_start=True, cap_end=False, facet=True)
        place([v for v in b.bm.verts if v not in before], math.radians(deg), z, tilt, 0.2)
    # Domed rivets on both bands, four each (the design's brass rivets).
    for (lo, hi), offset in zip(bands, (0, 45)):
        for k in range(4):
            before = set(b.bm.verts)
            b.lathe([(-0.3, 0.36, True), (0.1, 0.35, False), (0.28, 0.0, False)], 6, 'brass',
                    cap_start=True, cap_end=False)
            place([v for v in b.bm.verts if v not in before], math.radians(offset + 90 * k + 15), (lo + hi) / 2, 0,
                  -0.12)


BUILDERS = {'spear': build_spear, 'halberd': build_halberd, 'trident': build_trident,
            'wand': build_wand, 'blaster': build_blaster, 'crossbow': build_crossbow, 'club': build_club}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    b = vmw.Builder()
    BUILDERS[KIND](b)
    obj = b.finish(KIND)
    me = obj.data
    out = os.path.join(PROJECT, 'work', KIND)
    os.makedirs(out, exist_ok=True)
    region = me.attributes['region'].data
    counts = {}
    for p in me.polygons:
        counts[region[p.index].value] = counts.get(region[p.index].value, 0) + 1
    co = [v.co for v in me.vertices]
    lo = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
    hi = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
    print('BUILD', KIND, 'tris', len(me.polygons), 'verts', len(me.vertices), 'regions', counts,
          'bounds', tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi), flush=True)
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'model.blend'))
    mat = bpy.data.materials.new('plain')
    mat.use_nodes = True
    me.materials.append(mat)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, 'model_plain.glb'), use_selection=True, export_format='GLB',
                              export_yup=True, export_animations=False)


main()
