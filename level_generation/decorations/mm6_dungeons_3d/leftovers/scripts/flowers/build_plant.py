"""Blender: work/<id>/atlas_* -> work/<id>/plant_export.glb (+ plant.blend) with meshes Plant, Plant_LOD1, Plant_LOD2:
one MASK material 'Plant', double-sided, extras openyamm_wind 0.02, openyamm_specular 0.1, openyamm_translucency 0.3.
  6flower02 (gazania, ~0.29 m tall, ~0.42 m wide): foliage cards (atlas cells 0/1) leaning out from a low base form a
    dome; daisy heads are shallow cups (cell 2 mapped from above) on the dome's surface facing out and up, a few raised
    on thin stems (cell 3 strip).
  6flower07 (crocus, ~0.21 m tall, ~0.26 m wide): grass-leaf cards round the base; blooms are lathed goblets wrapped in
    the cell 2 petal strip, a stamen disc inside the opening (cell 3 centre) and a short pale stem (cell 3 strip).
  6flower06 (rose bush, ~1.6 m) and 6flower08 (sunflower clump, ~1.1 m): cards tangent to a shell (lobed and widened
    at the base for the rose, a low leaf skirt for the sunflowers), heads as flat cones over the surface; see README.
Shading normals: cards blend their own normal with one from the clump's centre (one volume); cups and goblets use
their surface normal. COLOR_0 ('Color') darkens toward the ground and inside. LOD1/LOD2 keep a seeded subset of the
cards (enlarged to hold the coverage) and the same flowers with fewer segments. Usage: -- <id>"""
import bpy, bmesh, math, os, sys
import numpy as np
from mathutils import Vector
SID = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # the leftovers batch folder
WORK = os.path.join(HERE, 'work', 'plants', SID)
bpy.ops.wm.read_factory_settings(use_empty=True)
rng = np.random.default_rng({'6flower02': 77, '6flower07': 78, '6flower06': 79, '6flower08': 80, '6flower11': 81,
                            '6flower01': 82}[SID])
GAZANIA = SID == '6flower02'
# Leftovers additions: 6flower11 (small low rose bush, ~0.43 m, big pale roses) reuses the rose bush scaled by
# ROSE_SCALE with fewer, larger roses; 6flower01 (AGAVE: a rosette of arching sword leaves round a short stalk with an
# orange bract spike, ~0.40 m) has leaves as folded ribbons (atlas cell 0 along each leaf) and the spike as three
# crossed cards (cell 2) on a stalk strip (cell 3).
ROSE = SID in ('6flower06', '6flower11')   # rose bush: dense dark leaf mound studded with roses
SMALL_ROSE = SID == '6flower11'
ROSE_SCALE = 0.27 if SMALL_ROSE else 1.0
AGAVE = SID == '6flower01'
SUN = SID == '6flower08'           # sunflower clump, ~1.1 m tall, ~1.6 m wide: a leaf skirt under many heads
HEADS = GAZANIA or ROSE or SUN     # flower heads are cups mapped with atlas cell 2
H = {'6flower02': 0.29, '6flower07': 0.21, '6flower06': 1.6, '6flower08': 1.08, '6flower11': 0.43,
     '6flower01': 0.40}[SID]
CENTRE = Vector((0, 0, {'6flower02': 0.07, '6flower07': 0.05, '6flower06': 0.70, '6flower08': 0.42, '6flower11': 0.19,
                        '6flower01': 0.08}[SID]))


def frame(axis):
    axis = Vector(axis).normalized()
    helper = Vector((0, 0, 1)) if abs(axis.z) < 0.95 else Vector((1, 0, 0))
    a = helper.cross(axis).normalized()
    return a, axis.cross(a), axis


class Mesh:
    def __init__(self):
        self.bm = bmesh.new(); self.uv = self.bm.loops.layers.uv.new('UVMap'); self.normals = []; self.colours = []

    def face(self, points, uvs, normals, occlusion):
        verts = [self.bm.verts.new(p) for p in points]
        f = self.bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, uvs):
            loop[self.uv].uv = (u, 1.0 - v)          # atlas coordinates are image space (v down)
        self.normals += [n.normalized() for n in normals]
        self.colours += [(o, o, o, 1.0) for o in occlusion]


def foliage_card(mesh, card, grow):
    base, right, up, cell = card['base'], card['right'] * grow, card['up'] * grow, card['cell']
    u0, v0 = (cell % 2) * 0.5, (cell // 2) * 0.5
    pts = [base - right * 0.5, base + right * 0.5, base + right * 0.5 + up, base - right * 0.5 + up]
    uvs = [(u0, v0 + 0.5), (u0 + 0.5, v0 + 0.5), (u0 + 0.5, v0), (u0, v0)]
    own = right.cross(up).normalized()
    normals, occ = [], []
    for p in pts:
        outward = (p - CENTRE).normalized()
        n = own if own.dot(outward) >= 0 else -own
        normals.append(n * 0.45 + outward * 0.55)
        height = max(p.z, 0.0) / H; radial = min(Vector((p.x, p.y)).length / (H * 0.8), 1.0)
        occ.append((0.30 + 0.70 * min(height * 1.6, 1.0) ** 0.9 * (0.75 + 0.25 * radial)) * card.get('shade', 1.0))
    mesh.face(pts, uvs, normals, occ)


def strip(mesh, bottom, top, width, crossed):
    """Thin stem: one or two crossed quads over the cell 3 strip (u 0.02-0.08 of that cell)."""
    axis = (top - bottom).normalized()
    a, b, _ = frame(axis)
    for side in ((a,) if not crossed else (a, b)):
        pts = [bottom - side * width, bottom + side * width, top + side * width, top - side * width]
        uvs = [(0.51, 1.0), (0.54, 1.0), (0.54, 0.5), (0.51, 0.5)]
        mesh.face(pts, uvs, [side.cross(axis)] * 4, [0.45, 0.45, 0.75, 0.75])


def cup(mesh, centre, axis, radius, segments, rings):
    """Gazania head: shallow cup round `axis`, cell 2 mapped from above (rim = petal tips)."""
    a, b, n = frame(axis)
    profile = [(0.0, -0.22), (0.42, -0.10), (1.0, 0.0)] if rings == 3 else [(0.0, -0.2), (1.0, 0.0)]
    cu, cv, scale = 0.25, 0.75, 0.235           # cell 2 centre in the atlas, rim radius in atlas units
    turn = rng.uniform(0, 2 * math.pi)

    def point(ring, k):
        r, depth = profile[ring]
        t = turn + 2 * math.pi * k / segments
        local = (a * math.cos(t) + b * math.sin(t)) * r * radius
        return centre + local + n * depth * radius, (cu + math.cos(t) * r * scale, cv + math.sin(t) * r * scale), \
            (n + (a * math.cos(t) + b * math.sin(t)) * r * 0.35)
    for ring in range(len(profile) - 1):
        for k in range(segments):
            quad = [point(ring, k), point(ring, k + 1), point(ring + 1, k + 1), point(ring + 1, k)]
            if ring == 0:
                quad = quad[1:]                     # centre: triangles
            mesh.face([q[0] for q in quad], [q[1] for q in quad], [q[2] for q in quad], [0.95] * len(quad))


def goblet(mesh, base, axis, height, radius, segments, rings, centre_disc):
    """Crocus bloom: lathe wrapped in the cell 2 petal strip (u round, v up), optional stamen disc inside the top."""
    a, b, n = frame(axis)
    profile = {4: [(0.0, 0.42), (0.25, 0.92), (0.62, 1.0), (1.0, 0.72)],
               3: [(0.0, 0.42), (0.5, 1.0), (1.0, 0.72)], 2: [(0.0, 0.6), (1.0, 0.98)]}[rings]
    turn = rng.uniform(0, 2 * math.pi)
    for ring in range(len(profile) - 1):
        for k in range(segments):
            pts, uvs, nrm, occ = [], [], [], []
            for rr, kk in ((ring, k), (ring, k + 1), (ring + 1, k + 1), (ring + 1, k)):
                t, r = profile[rr]
                angle = turn + 2 * math.pi * kk / segments
                radial = a * math.cos(angle) + b * math.sin(angle)
                pts.append(base + n * t * height + radial * r * radius)
                uvs.append((kk / segments * 0.5, 1.0 - t * 0.5))
                nrm.append(radial + n * 0.25)
                occ.append(0.55 + 0.45 * t)
            mesh.face(pts, uvs, nrm, occ)
    if centre_disc:
        top = base + n * height * 0.86; r = radius * 0.62
        for k in range(6):
            pts, uvs = [top], [(0.75, 0.75)]
            for kk in (k, k + 1):
                angle = turn + 2 * math.pi * kk / 6
                pts.append(top + (a * math.cos(angle) + b * math.sin(angle)) * r)
                uvs.append((0.75 + math.cos(angle) * 0.15, 0.75 + math.sin(angle) * 0.15))
            mesh.face(pts, uvs, [n] * 3, [0.8] * 3)


def upright(base, yaw, tilt, size, cell, keep):
    right = Vector((math.cos(yaw), math.sin(yaw), 0.0)); facing = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    up = (Vector((0, 0, 1)) * math.cos(tilt) + facing * math.sin(tilt)).normalized()
    return {'base': Vector(base), 'right': right * size, 'up': up * size, 'cell': cell, 'keep': keep}


def tangent_card(centre, normal, size, cell, keep, shade=1.0, ground=None):
    """Foliage card centred on `centre`, facing along `normal`, its up axis turned upward."""
    right = Vector((-normal.y, normal.x, 0.0))
    if right.length < 0.25:
        angle = rng.uniform(0, 2 * math.pi); right = Vector((math.cos(angle), math.sin(angle), 0.0))
    right.normalize()
    up = normal.cross(right).normalized()
    if up.z < 0:
        up = -up
    base = centre - up * size * 0.5
    ground = 0.08 * H / 1.6 if ground is None and ROSE else (0.08 if ground is None else ground)
    if base.z < ground:
        base.z = 0.0                         # the lowest cards stand on the ground
    return {'base': base, 'right': right * size, 'up': up * size, 'cell': cell, 'keep': keep, 'shade': shade}


def direction(lowest, highest=1.0):
    while True:
        d = Vector(rng.normal(0, 1, 3)).normalized()
        if lowest < d.z <= highest:
            return d


cards, flowers = [], []
if ROSE:
    # A loose, irregular mound, wider at the base: a shell with soft random lobes and dents, an outer layer of small
    # leaf cards with gaps over a dark inner layer, crossed sprigs sticking out of the silhouette, and small roses over
    # the whole surface down to the ground.
    S = ROSE_SCALE
    radius, height_radius = (0.19, 0.2) if SMALL_ROSE else (0.80, 0.95)
    counts = (110, 26, 7, 16) if SMALL_ROSE else (124, 36, 18, 124)   # outer, inner, sprigs, roses
    head_scale = 4.0 if SMALL_ROSE else 1.0                        # the small bush's roses are large and few
    S_CARD = 0.36 if SMALL_ROSE else 1.0                           # denser leaf cover on the small bush
    lobes = [(Vector(rng.normal(0, 1, 3)).normalized(), rng.uniform(-0.10, 0.16)) for _ in range(18)]

    def widen(d):
        return 1.2 - 0.4 * d.z

    def surface(d, scale=1.0):
        bump = 1.0 + sum(a * math.exp((d.dot(c) - 1.0) / 0.16) for c, a in lobes)
        return CENTRE + Vector((d.x * radius * widen(d), d.y * radius * widen(d), d.z * height_radius)) * scale * bump

    def shell_normal(d):
        return Vector((d.x / (radius * widen(d)), d.y / (radius * widen(d)), d.z / height_radius)).normalized()
    # Many mid-sized cards rather than a few large ones, each turned off the shell tangent by a random tilt (and never
    # facing far downward), so no card spans a large single plane that reads as a shell when seen edge-on.
    def tilted(d):
        normal = (shell_normal(d) + Vector(rng.normal(0, 0.28, 3))).normalized()
        if normal.z < -0.2:
            normal.z = -0.2; normal.normalize()
        return normal
    outer = []
    for k in range(counts[0]):               # outer layer
        d = direction(-0.55)
        outer.append(tangent_card(surface(d, rng.uniform(0.88, 1.0)), tilted(d), rng.uniform(0.38, 0.5) * S_CARD,
                                  int(rng.integers(0, 2)), 2.0 + rng.uniform()))
    cards += outer
    for k in range(counts[1]):               # dark interior seen through the gaps
        d = direction(-0.5)
        cards.append(tangent_card(surface(d, rng.uniform(0.6, 0.78)), tilted(d), rng.uniform(0.45, 0.6) * S_CARD,
                                  int(rng.integers(0, 2)), 1.0 + rng.uniform(), shade=0.4))
    for k in range(counts[2]):               # sprigs poking out: three cards in a star, a rose near the tip
        d = direction(-0.2)
        outward = (d + Vector((0, 0, 0.3)) + Vector(rng.normal(0, 0.2, 3))).normalized()
        size = rng.uniform(0.28, 0.38) * S_CARD
        first, second, _ = frame(outward)
        base = surface(d, 0.92)
        keep = 1.5 + rng.uniform()
        for turn in (0.0, math.pi / 3, 2 * math.pi / 3):
            side = first * math.cos(turn) + second * math.sin(turn)
            cards.append({'base': base, 'right': side * size, 'up': outward * size,
                          'cell': int(rng.integers(0, 2)), 'keep': keep, 'shade': 1.0})
        flowers.append({'centre': base + outward * size * 0.72, 'axis': outward + Vector((0, 0, 0.3)),
                        'radius': rng.uniform(0.045, 0.06) * S * head_scale, 'raised': False,
                        'keep': rng.uniform()})
    for k in range(counts[3]):               # small roses on the outer leaves, over the sides and top
        card = outer[int(rng.integers(0, len(outer)))]
        normal = card['right'].cross(card['up']).normalized()
        position = card['base'] + card['right'] * rng.uniform(-0.3, 0.3) + card['up'] * rng.uniform(0.25, 0.8)
        if normal.dot(position - CENTRE) < 0:
            normal = -normal
        head = rng.uniform(0.045, 0.07) * S * head_scale
        position += normal * (0.02 if SMALL_ROSE else 0.03)
        position.z = max(position.z, head * 1.2)
        axis = normal + Vector(rng.normal(0, 0.2, 3))
        if SMALL_ROSE:
            # the few large roses sit on the shell and face outward and a little up (never edge-on from the side)
            d = direction(-0.35, 0.8)
            position = surface(d, 1.0) + shell_normal(d) * 0.03
            outward = Vector((d.x, d.y, 0.0)).normalized()
            rise = math.radians(rng.uniform(10, 45))
            axis = outward * math.cos(rise) + Vector((0, 0, math.sin(rise))) + Vector(rng.normal(0, 0.1, 3))
        flowers.append({'centre': position, 'axis': axis, 'radius': head, 'raised': False, 'keep': rng.uniform()})
elif AGAVE:
    # Rosette: sword leaves from the centre, the inner ones steep, the outer ones flatter, all arching over and down
    # (curvature rising toward the tip); a short stalk off-centre carrying the orange bract spike above the leaves.
    leaves = []
    for k in range(13):
        yaw = 2 * math.pi * k / 13 + rng.normal(0, 0.15)
        steep = rng.uniform()
        leaves.append({'yaw': yaw, 'rise': math.radians(28 + 58 * steep), 'droop': math.radians(rng.uniform(45, 95)),
                       'length': rng.uniform(0.21, 0.29) * (1.0 - 0.2 * steep), 'width': rng.uniform(0.05, 0.064),
                       'twist': rng.normal(0, 0.25), 'keep': rng.uniform() + (1 - steep) * 0.5,
                       'shade': 0.7 + 0.3 * steep})
    flowers.append({'base': Vector((0.02, -0.01, 0.0)), 'top': Vector((0.035, -0.02, 0.29)), 'spike': 0.115,
                    'width': 0.15, 'keep': 9.0})
elif SUN:
    # Heads cover the whole visible hemisphere down to the ground on short stems; the leaves form a low skirt between
    # and below them. Every head faces outward and 10-40 degrees up, so none is seen edge-on from the side.
    leaf_centre, leaf_radius, leaf_height = Vector((0, 0, 0.22)), 0.80, 0.38
    for k in range(60):
        d = direction(-0.65)
        normal = Vector((d.x / leaf_radius, d.y / leaf_radius, d.z / leaf_height)).normalized()
        centre = leaf_centre + Vector((d.x * leaf_radius, d.y * leaf_radius, d.z * leaf_height)) * rng.uniform(0.75, 1.0)
        cards.append(tangent_card(centre, normal, rng.uniform(0.5, 0.68), int(rng.integers(0, 2)),
                                  rng.uniform() + (centre - leaf_centre).length))
    head_centre, head_radius, head_height = Vector((0, 0, 0.30)), 0.80, 0.52
    for k in range(78):
        d = direction(-0.45)
        position = head_centre + Vector((d.x * head_radius, d.y * head_radius, d.z * head_height)) * rng.uniform(0.95, 1.06)
        outward = Vector((d.x, d.y, 0.0))
        if outward.length < 0.2:
            angle = rng.uniform(0, 2 * math.pi); outward = Vector((math.cos(angle), math.sin(angle), 0.0))
        outward.normalize()
        rise = math.radians(rng.uniform(10, 40))
        axis = outward * math.cos(rise) + Vector((0, 0, math.sin(rise))) + Vector(rng.normal(0, 0.08, 3))
        head = rng.uniform(0.13, 0.22)
        position.z = max(position.z, head * 1.1)
        stem = Vector((position.x * 0.7, position.y * 0.7, max(position.z - 0.32, 0.04)))
        flowers.append({'centre': position, 'axis': axis, 'radius': head, 'raised': True, 'stem_base': stem,
                        'keep': rng.uniform() + head * 3})
elif GAZANIA:
    for k in range(20):
        phi = rng.uniform(0, 2 * math.pi); r = 0.10 * math.sqrt(rng.uniform())
        lean = rng.uniform(0.15, 0.5) * (1 if rng.uniform() < 0.5 else -1)
        cards.append(upright((r * math.cos(phi), r * math.sin(phi), 0.0), phi + math.pi / 2 + rng.normal(0, 0.5), lean,
                             rng.uniform(0.25, 0.30), int(rng.integers(0, 2)), rng.uniform() + r * 4))
    for k in range(17):
        phi = rng.uniform(0, 2 * math.pi); r = 0.18 * math.sqrt(rng.uniform())
        surface = 0.16 * (1 - (r / 0.24) ** 2)
        raised = k < 5
        z = surface + (rng.uniform(0.07, 0.11) if raised else rng.uniform(0.03, 0.06))
        outward = Vector((math.cos(phi), math.sin(phi), 0.0))
        # faces turned out toward the side, so they read from eye level
        axis = Vector((0, 0, 1)) * rng.uniform(0.5, 0.9) + outward * (0.7 + 1.2 * r / 0.18) + Vector(rng.normal(0, 0.15, 3))
        flowers.append({'centre': Vector((r * math.cos(phi), r * math.sin(phi), z)), 'axis': axis,
                        'radius': rng.uniform(0.055, 0.07), 'raised': raised, 'keep': rng.uniform() + (0.6 if raised else 0)})
else:
    for k in range(14):
        phi = rng.uniform(0, 2 * math.pi); r = 0.05 * math.sqrt(rng.uniform())
        cards.append(upright((r * math.cos(phi), r * math.sin(phi), 0.0), rng.uniform(0, math.pi), rng.uniform(-0.3, 0.3),
                             rng.uniform(0.15, 0.20), int(rng.integers(0, 2)), rng.uniform() + r * 8))
    for k in range(12):
        phi = rng.uniform(0, 2 * math.pi); r = 0.07 * math.sqrt(rng.uniform())
        lean = Vector((math.cos(phi), math.sin(phi), 0.0)) * rng.uniform(0.1, 0.5)
        flowers.append({'base': Vector((r * math.cos(phi), r * math.sin(phi), 0.0)), 'axis': Vector((0, 0, 1)) + lean,
                        'stem': rng.uniform(0.03, 0.06), 'height': rng.uniform(0.072, 0.088),
                        'radius': rng.uniform(0.025, 0.030), 'keep': rng.uniform()})

PLAN = [{'cards': (1.0, 1.0), 'flowers': 1.0, 'segments': 10 if GAZANIA else 8, 'rings': 3 if GAZANIA else 4, 'detail': True},
        {'cards': (0.62, 1.12), 'flowers': 1.0, 'segments': 6, 'rings': 2 if GAZANIA else 3, 'detail': True},
        {'cards': (0.45, 1.18) if GAZANIA else (0.38, 1.22), 'flowers': 1.0, 'segments': 5, 'rings': 2, 'detail': False}]
if ROSE or SUN:
    # Many heads as flat cones (one triangle per segment); the coarser levels keep a seeded subset of the heads and
    # fewer segments (a four-sided rose at LOD2).
    rose_or_sun = (lambda rose, sun: rose if ROSE else sun)
    if SMALL_ROSE:
        # few large roses: keep most of them (the bush's main feature) and drop cards instead
        rose_or_sun = (lambda rose, sun, small=None: small if small is not None else rose)
    PLAN = [{'cards': (1.0, 1.0), 'flowers': 1.0, 'segments': rose_or_sun(8, 10), 'rings': 2, 'detail': True},
            {'cards': rose_or_sun((0.5, 1.2), (0.55, 1.14)), 'flowers': rose_or_sun(0.45, 0.65, 0.85),
             'segments': rose_or_sun(6, 8), 'rings': 2, 'detail': True},
            {'cards': rose_or_sun((0.28, 1.5), (0.38, 1.3), (0.4, 1.3)), 'flowers': rose_or_sun(0.18, 0.55, 0.5),
             'segments': 4,
             'rings': 2, 'detail': False}]

if AGAVE:
    PLAN = [{'segments': 7, 'fold': True, 'leaves': 1.0, 'crossed': 3},
            {'segments': 4, 'fold': True, 'leaves': 0.8, 'crossed': 2},
            {'segments': 3, 'fold': False, 'leaves': 0.6, 'crossed': 2}]


def agave_leaf(mesh, leaf, segments, fold, grow):
    """One sword leaf: a ribbon along an arching curve (cell 0: u across the leaf, v base -> tip), its width tapering
    to the tip; folded along the midrib (two halves tilted up) at the finer levels."""
    yaw, rise, droop, length = leaf['yaw'], leaf['rise'], leaf['droop'], leaf['length']
    out = Vector((math.cos(yaw), math.sin(yaw), 0.0)); side0 = Vector((-math.sin(yaw), math.cos(yaw), 0.0))
    points, p = [], Vector((out.x * 0.012, out.y * 0.012, 0.01))
    for i in range(segments + 1):
        t = i / segments
        a = rise - droop * t ** 1.6
        direction = out * math.cos(a) + Vector((0, 0, math.sin(a)))
        points.append((p.copy(), direction, t))
        p += direction * length / segments
        if p.z < 0.004:
            p.z = 0.004
    halves = ((-1.0, 0.0), (0.0, 1.0)) if fold else ((-1.0, 1.0),)
    for i in range(segments):
        for lo, hi in halves:
            pts, uvs, nrm, occ = [], [], [], []
            for (q, direction, t), across in ((points[i], lo), (points[i], hi), (points[i + 1], hi),
                                              (points[i + 1], lo)):
                side = (side0 * math.cos(leaf['twist'] * t) + direction.cross(side0) * math.sin(leaf['twist'] * t))
                w = leaf['width'] * grow * (0.55 + 0.45 * math.sin(math.pi * min(0.35 + t, 1.0))) * (1 - 0.92 * t ** 2)
                lift = direction.cross(side).normalized()
                if lift.z < 0:
                    lift = -lift
                pos = q + side * across * w * 0.5 + lift * (0.0 if across == 0.0 else -abs(across) * w * 0.18
                                                                 if fold else 0.0)
                pts.append(pos); uvs.append((0.25 + across * 0.24, 0.5 - t * 0.49))
                nrm.append((lift + side * across * 0.35).normalized())
                occ.append((0.45 + 0.55 * min(max(pos.z, 0) / (H * 0.5), 1.0) ** 0.7
                            * (0.6 + 0.4 * min((pos - Vector((0, 0, pos.z))).length / 0.2, 1.0))) * leaf['shade'])
            mesh.face(pts, uvs, nrm, occ)


def agave_spike(mesh, f, crossed, detail):
    """Stalk strip (cell 3) up to the spike's foot, then `crossed` vertical cards of the bract spike (cell 2)."""
    foot = f['top'] - Vector((0, 0, f['spike']))
    if detail:
        strip(mesh, f['base'], foot + Vector((0, 0, 0.02)), 0.006, True)
    for k in range(crossed):
        a = math.pi * k / crossed + 0.4
        side = Vector((math.cos(a), math.sin(a), 0.0)) * f['width'] * 0.5
        pts = [foot - side, foot + side, f['top'] + side, f['top'] - side]
        uvs = [(0.0, 1.0), (0.5, 1.0), (0.5, 0.5), (0.0, 0.5)]
        n = Vector((0, 0, 1)).cross(side).normalized()
        mesh.face(pts, uvs, [n * 0.5 + Vector((0, 0, 0.5))] * 4, [0.75, 0.75, 1.0, 1.0])


def build(lod, name):
    plan = PLAN[lod]; mesh = Mesh()
    if AGAVE:
        kept = sorted(leaves, key=lambda l: -l['keep'])[:int(round(len(leaves) * plan['leaves']))]
        grow = 1.0 / math.sqrt(plan['leaves'])
        for leaf in kept:
            agave_leaf(mesh, leaf, plan['segments'], plan['fold'], grow)
        for f in flowers:
            agave_spike(mesh, f, plan['crossed'], lod < 2)
        return finish_mesh(mesh, name)
    fraction, grow = plan['cards']
    for card in sorted(cards, key=lambda c: -c['keep'])[:int(round(len(cards) * fraction))]:
        foliage_card(mesh, card, grow)
    keep = sorted(flowers, key=lambda f: -f['keep'])[:int(round(len(flowers) * plan['flowers']))]
    for f in keep:
        if HEADS:
            grow_head = 1.0 if lod == 0 else (1.04 if lod == 1 else 1.08)
            cup(mesh, f['centre'], f['axis'], f['radius'] * grow_head, plan['segments'], plan['rings'])
            if f['raised'] and lod < 2:
                bottom = f.get('stem_base', Vector((f['centre'].x * 0.6, f['centre'].y * 0.6, 0.06)))
                strip(mesh, bottom, f['centre'], 0.004 if GAZANIA else 0.011, lod == 0)
        else:
            axis = f['axis'].normalized()
            top = f['base'] + axis * f['stem']
            if plan['detail']:
                strip(mesh, f['base'], top, 0.004, lod == 0)
            goblet(mesh, top, axis, f['height'], f['radius'] * (1.0, 1.04, 1.1)[lod], plan['segments'], plan['rings'],
                   plan['detail'])
    return finish_mesh(mesh, name)


def finish_mesh(mesh, name):
    me = bpy.data.meshes.new(name); mesh.bm.to_mesh(me); mesh.bm.free()
    me.normals_split_custom_set_from_vertices(mesh.normals)
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', [x for c in mesh.colours for x in c]); me.color_attributes.active_color = attr
    obj = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(obj)
    return obj


mat = bpy.data.materials.new('Plant'); mat.use_nodes = True; nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = bpy.data.images.load(os.path.join(WORK, 'atlas_basecolor.png'))
nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color']); nt.links.new(tb.outputs['Alpha'], bsdf.inputs['Alpha'])
tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(os.path.join(WORK, 'atlas_normal.png'))
tn.image.colorspace_settings.name = 'Non-Color'
nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
bsdf.inputs['Roughness'].default_value = 0.85; bsdf.inputs['Metallic'].default_value = 0.0
mat.use_backface_culling = False; mat.surface_render_method = 'DITHERED'
mat['openyamm_wind'] = 0.02; mat['openyamm_specular'] = 0.1; mat['openyamm_translucency'] = 0.3
objects = []
for lod, name in enumerate(('Plant', 'Plant_LOD1', 'Plant_LOD2')):
    o = build(lod, name); o.data.materials.append(mat); objects.append(o)
    print('LOD', name, 'triangles', sum(len(p.vertices) - 2 for p in o.data.polygons))
for o in bpy.data.objects:
    o.select_set(o in objects)
bpy.context.view_layer.objects.active = objects[0]
out = os.path.join(WORK, 'plant_export.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_extras=True, export_normals=True, export_vertex_color='ACTIVE', export_tangents=False,
                          export_animations=False, export_skins=False, export_morph=False, export_image_format='AUTO')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'plant.blend'))
print('EXPORTED', out)
