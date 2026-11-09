"""Tree for one species (work/<id>/tree.blend; settings in species/<id>.json, defaults = the approved 6tree01 v2):
objects Tree, Tree_LOD1, Tree_LOD2 (Bark + Leaves), each mesh with a
'Color' point colour attribute (linear) = canopy occlusion, exported as glTF COLOR_0 (multiplied into base colour).

- Skeleton: the v1 Sapling settings (trunk forking low into three limbs); bark per LOD as in v1 (thin splines dropped
  until the bark budget holds, parts outside the crown envelope cut).
- Crown from clumps: ~100 small clumps (0.4-0.7 m) on Sapling branch tips in the outer crown plus a few inner ones,
  never closer than 0.72 x the sum of their radii (overlapping a little, gaps between them), slightly
  irregular ellipsoids, each pulled inward until it
  fits the sprite's crown envelope (work/profile.json). Cards (0.36-0.46 m whorl cells: 5-7 cm leaves) fill each
  clump densest near its surface, facing outward with a random tilt;
  shading normals blend the clump-centre normal (70 %) with the crown-centre normal (30 %).
- Occlusion: per vertex, sky rays (uniform over the upper hemisphere); each leaf card hit blocks 55 % (a ray continues
  through gaps), so clump undersides, crevices and the crown interior darken. occ = 0.22 + 0.78 * visibility^1.4,
  times a clump-local term (0.28..1 by height on the ball: bright tops, shaded undersides; 0.6..1 toward its
  core), times a
  per-clump value/hue jitter (+-12 % value, +-10 % red/blue). Bark vertices get the same rays (limbs under the crown darken).
- LOD1 / LOD2: the same cards, a per-clump subset that keeps the most visible ones (spread by farthest-point
  sampling), enlarged at most 1.3x / 1.6x about their centres (LOD2 cards also turned toward the crown's outside); each keeps its LOD0 corner occlusion, scaled by TONE so the crown's mean tone matches LOD0. Bark per LOD gets
  its own rays against the LOD0 leaves, so every level carries the same darkening.
Usage: blender --background --python build_tree.py -- <id>"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
WORK = OUT = spec['work']
H = spec['height_m']
SAPLING = spec['sapling']
BARK, CROWN, LOD = spec['bark'], spec['crown'], spec['lod']
BRANCH_MIN = dict(enumerate(BARK['min_thickness']))
BRANCH_BUDGET = dict(enumerate(BARK['budget']))
TRI_BUDGET = dict(enumerate(LOD['triangles']))
GROW = dict(enumerate(LOD['grow']))
OUTWARD = dict(enumerate(LOD['outward']))
# coarse levels keep the brighter outer cards: scale their occlusion so the crown's tone matches LOD0 (lod_check.py)
TONE = dict(enumerate(LOD['tone']))
CLUMPS, INNER_CLUMPS = CROWN['clumps'], CROWN['inner_clumps']
OUTER_RADIUS, INNER_RADIUS = tuple(CROWN['outer_radius']), tuple(CROWN['inner_radius'])
CLUMP_GAP = CROWN['gap']                # minimum centre distance / (r1 + r2): clumps overlap a little, gaps stay
CARD = tuple(CROWN['card'])             # card edge (m): one whorl cell, leaves ~5-7 cm
COVERAGE = CROWN['coverage']            # blocking per card hit: atlas coverage ~0.45, cards overlap in clumps
TILE = BARK['tile']                     # bark texture repeat (m); bark_brown_01 covers ~1 m
ROOTS = BARK['roots']                   # root spurs at the trunk base (no rng: the clump layout is unchanged)
OCC = spec['occlusion']
# Optional species features (absent = the approved behaviour, bit-identical):
#  crown.tiers [[lo, hi], ...] (fractions of the height): clump centres only inside these bands (a tiered cypress);
#  crown.flatten: clump balls squashed vertically by this factor (flat tier discs);
#  crown.moss {strands, length [m, m], width m, seed}: strands hanging under the clumps, material Moss (alpha cards);
#  bark.aerial_roots {count, z [lo, hi], reach [lo, hi], radius [top, ground], seed}: prop roots arching from the
#  limbs down into the ground (banyan), part of the bark.
#  crown.radius_by_width [min]: clump radius scaled by the envelope's width at its height (small clumps near a spire);
#  crown.lobes {fraction, slack}: that fraction of clumps may reach slack x the envelope (ragged protruding lobes);
#  crown.card_up: card normals tilted toward +z by this weight (flat pads);
#  crown.spire [top fraction, stretch]: clumps in that top part of the crown stretched tall and narrow (a pointed top);
#  leaves.snow {cells, up, tilt, lift}: cards whose normal z exceeds `up` use the snowy atlas cells (turned `tilt`
#  further up, occlusion lifted by `lift` toward 1), the others the plain ones; bark.root_radius scales root spurs,
#  bark.root_rise (m, default 0.38) sets how high on the trunk they start (a buttressed base).
SNOW = spec['leaves'].get('snow')
# leaves.snow.material {emissive, translucency} (MM7 trees_a): snow cards get their own material LeavesSnow (same
# atlas) with a small emissive lift and more translucency, so shaded snow stays near-white in the engine.
SNOW_MATERIAL = SNOW.get('material') if SNOW else None
TIERS = CROWN.get('tiers')
RADIUS_BY_WIDTH = CROWN.get('radius_by_width')
LOBES = CROWN.get('lobes')
CARD_UP = CROWN.get('card_up', 0.0)
lobe_rng = np.random.default_rng(spec['seed'] + 5)
clump_slack = []
FLATTEN = CROWN.get('flatten', 1.0)
MOSS = CROWN.get('moss')
AERIAL = BARK.get('aerial_roots')
rng = np.random.default_rng(spec['seed'])
profile = np.array(json.load(open(os.path.join(WORK, 'profile.json')))['half_width_by_height'])


def R(z):
    return float(np.interp(z / H, profile[:, 0], profile[:, 1])) * H


CANOPY_LOW = CROWN['canopy_low'] * H
CENTRE = Vector((0, 0, CROWN['centre'] * H))


def crown_normal(p):
    o = p - CENTRE; o.z *= CROWN['crown_normal_z']
    return o.normalized()


# ---------------------------------------------------------------- skeleton and bark (as v1)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.curve.tree_add(do_update=True, bevel=True, showLeaves=False, useArm=False, prune=False, **SAPLING)
skel = bpy.data.objects['tree']; cu = skel.data
SKELETON = spec.get('skeleton')


def conifer_skeleton():
    """skeleton.kind 'conifer' (MM7 trees_a): Sapling's splines replaced by an explicit spruce skeleton fitted to the
    sprite: a straight tapering trunk to the top, whorls of near-horizontal limbs from crown.canopy_low up, each limb
    reaching `reach` x the envelope half-width at its height and drooping toward its tip; limb radius scales with
    its length. Keeps Sapling's curve settings (bevel), so the bark code is unchanged. Settings: whorls, per_whorl,
    reach [lo, hi], rise (initial upward slope), droop (tip drop / length), trunk_radius, limb_radius, top (fraction
    of H where the whorls stop), seed."""
    k = SKELETON
    r = np.random.default_rng(k.get('seed', 1))
    for sp in list(cu.splines):
        cu.splines.remove(sp)
    unit = cu.bevel_depth

    def spline(points, radii):
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(points) - 1)
        for bp, q, rad in zip(sp.bezier_points, points, radii):
            bp.co = q; bp.radius = rad / unit
            bp.handle_left_type = bp.handle_right_type = 'AUTO'
        return sp

    r0 = k['trunk_radius']
    n = 14
    # skeleton.wobble [amplitude m, turns] (MM7 trees_a): the bole below the crown bends in a slow spiral (zero at
    # the ground and at the lowest whorl, where the limbs start on the axis)
    wob = k.get('wobble', [0.0, 1.0]); zc = max(CROWN['canopy_low'] * H, 1e-3)
    def trunk_point(z):
        if z >= zc or not wob[0]:
            return (0, 0, z)
        a = wob[0] * math.sin(math.pi * z / zc); th = 2 * math.pi * wob[1] * z / zc
        return (a * math.cos(th), a * math.sin(th), z)
    spline([trunk_point(H * i / n) for i in range(n + 1)], [r0 * (1 - 0.92 * i / n) ** 1.1 for i in range(n + 1)])
    whorls = k['whorls']; lo = CROWN['canopy_low'] * H; top = k.get('top', 0.95) * H
    phase = r.uniform(0, 2 * math.pi)
    longest = max(R(z) for z in np.linspace(lo, top, 40))
    for w in range(whorls):
        f = w / max(whorls - 1, 1)
        z0 = lo + (top - lo) * (f ** k.get('spacing_power', 1.0)) + r.uniform(-0.25, 0.25) * (top - lo) / whorls
        z0 = min(max(z0, lo), top)
        phase += 2.4
        count = int(k['per_whorl']) if f < 0.8 else max(int(k['per_whorl']) - 1, 3)
        whorl_reach = r.uniform(*k.get('whorl_reach', [1.0, 1.0]))   # lobed crowns: whole whorls shorter or longer
        for j in range(count):
            az = phase + 2 * math.pi * j / count + r.uniform(-0.3, 0.3)
            d = Vector((math.cos(az), math.sin(az), 0))
            droop = k.get('droop', 0.15) * r.uniform(0.7, 1.3)
            rise = k.get('rise', 0.1)
            L = R(z0) * r.uniform(*k['reach'])
            for _ in range(3):            # the limb tip sits lower: reach the envelope there
                L = max(R(max(z0 + (rise - droop) * L, 0.0)) * r.uniform(*k['reach']), 0.12)
            L *= whorl_reach
            pts, radii = [], []
            for i in range(5):
                t = i / 4
                q = d * (L * t) + Vector((0, 0, z0 + L * (rise * t - droop * t * t)))
                pts.append(q); radii.append(k['limb_radius'] * (L / longest) ** 0.8 * (1 - 0.85 * t) + 0.002)
            pts[0] = Vector((0, 0, z0))
            spline(pts, radii)
    print('SKELETON conifer whorls', whorls, 'splines', len(cu.splines))


def forked_skeleton():
    """skeleton.kind 'forked' (MM7 trees_a): Sapling's splines replaced by a broadleaf skeleton fitted to the sprite:
    a trunk (gently bent) to `fork` x H that splits into `stems` stems curving up and out to `stem_top` x H at
    `spread` x the envelope half-width, each with `limbs` side limbs in the crown reaching toward the envelope.
    fork 0 gives a multi-stem tree from the ground. Settings: fork, stems, stem_top [lo, hi], spread [lo, hi],
    trunk_radius, stem_radius, limbs, limb_reach [lo, hi], limb_radius, bend, seed."""
    k = SKELETON
    r = np.random.default_rng(k.get('seed', 1))
    for sp in list(cu.splines):
        cu.splines.remove(sp)
    unit = cu.bevel_depth

    def spline(points, radii):
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(points) - 1)
        for bp, q, rad in zip(sp.bezier_points, points, radii):
            bp.co = q; bp.radius = rad / unit
            bp.handle_left_type = bp.handle_right_type = 'AUTO'

    fz = k['fork'] * H
    bend = k.get('bend', 0.0) * H
    ba = r.uniform(0, 2 * math.pi); bdir = Vector((math.cos(ba), math.sin(ba), 0))
    top = Vector((0, 0, fz)) + bdir * bend * 0.3
    if fz > 0.05:
        pts = [Vector((0, 0, 0)), bdir * bend * 0.6 + Vector((0, 0, fz * 0.33)),
               -bdir * bend * 0.3 + Vector((0, 0, fz * 0.66)), top]
        spline(pts, [k['trunk_radius'] * f for f in (1.0, 0.9, 0.82, 0.75)])
    phase = r.uniform(0, 2 * math.pi)
    for j in range(k['stems']):
        az = phase + 2 * math.pi * j / k['stems'] + r.uniform(-0.35, 0.35)
        d = Vector((math.cos(az), math.sin(az), 0))
        z1 = r.uniform(*k['stem_top']) * H
        end = d * R(z1) * r.uniform(*k['spread']) + Vector((0, 0, z1))
        start = top + d * k['stem_radius'] * 0.5
        mid = start.lerp(end, 0.45) + d * 0.12 * (end - start).length * r.uniform(0.5, 1.2)
        mid.x *= k.get('mid_spread', 1.0); mid.y *= k.get('mid_spread', 1.0)    # < 1: stems rise first, then fan out
        pts = [start, start.lerp(mid, 0.5), mid, mid.lerp(end, 0.5), end]
        r0 = k['stem_radius'] * r.uniform(0.85, 1.1)
        spline(pts, [r0 * (1 - 0.7 * i / 4) for i in range(5)])
        for i in range(k.get('limbs', 0)):
            t = r.uniform(0.35, 0.95)
            base = (mid.lerp(end, (t - 0.45) / 0.55) if t > 0.45 else start.lerp(mid, t / 0.45))
            if base.z < CROWN['canopy_low'] * H:
                continue
            la = az + r.uniform(-1.3, 1.3)
            ld = Vector((math.cos(la), math.sin(la), r.uniform(0.1, 0.7))).normalized()
            reach = max(R(min(base.z, H)) - math.hypot(base.x, base.y), 0.3) * r.uniform(*k['limb_reach'])
            tip = base + ld * reach
            spline([base, base.lerp(tip, 0.5) + Vector((0, 0, 0.05 * reach)), tip],
                   [k['limb_radius'], k['limb_radius'] * 0.6, k['limb_radius'] * 0.2])
    print('SKELETON forked stems', k['stems'], 'splines', len(cu.splines))


if SKELETON and SKELETON.get('kind') == 'conifer':
    conifer_skeleton()
if SKELETON and SKELETON.get('kind') == 'forked':
    forked_skeleton()
TRUNK = BARK.get('trunk')


def stretch_trunk():
    """bark.trunk {top, taper} (MM7 trees_a): Sapling's single trunk stretched so its top is at `top` x H, with a
    gentle taper (radius at the top = taper x the base radius); every other spline moves up with the trunk point it
    starts from, so the limbs keep their shapes and fork from a tall, thick bole as on the sprite."""
    trunk = max(cu.splines, key=lambda sp: max(p.radius for p in sp.bezier_points))
    pts = trunk.bezier_points
    z_top = max(p.co.z for p in pts)
    factor = TRUNK['top'] * H / max(z_top, 1e-3)
    r0 = pts[0].radius
    for i, p in enumerate(pts):
        t = i / max(len(pts) - 1, 1)
        for attr in ('co', 'handle_left', 'handle_right'):
            v = getattr(p, attr); v.z *= factor; setattr(p, attr, v)
        p.radius = r0 * (1 - (1 - TRUNK.get('taper', 0.5)) * t)
    for sp in cu.splines:
        if sp == trunk:
            continue
        dz = sp.bezier_points[0].co.z * (factor - 1)
        for p in sp.bezier_points:
            for attr in ('co', 'handle_left', 'handle_right'):
                v = getattr(p, attr); v.z += dz; setattr(p, attr, v)
    print('TRUNK stretched x', round(factor, 2), 'top', round(TRUNK['top'] * H, 2))


if TRUNK:
    stretch_trunk()


def bezier_length(s):
    pts = s.bezier_points
    return sum((pts[i + 1].co - pts[i].co).length for i in range(len(pts) - 1))


def add_roots(bm, lod):
    """Root spurs flaring from the trunk base into the ground, like the sprite's: tapered tubes from inside the trunk
    at ~0.35 m down and out to ~0.75 m from the centre, curving under the ground at their tips."""
    base = [v.co for v in bm.verts if v.co.z < 0.25]
    trunk = max((Vector((c.x, c.y)).length for c in base), default=0.25)
    uv = bm.loops.layers.uv.active
    sides, rings = (5, 4) if lod == 0 else (4, 3) if lod == 1 else (4, 2)
    for k in range(ROOTS):
        a = 2 * math.pi * k / ROOTS + 0.35 * math.sin(3.1 * k)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = d.cross(Vector((0, 0, 1)))
        reach = trunk + BARK['root_reach'] + 0.12 * math.sin(1.7 * k + 0.5)
        loops = []
        for i in range(rings):
            t = i / (rings - 1)
            rise = BARK['root_rise'] if 'root_rise' in BARK else 0.38      # how high the spur starts on the trunk
            centre = d * (trunk * 0.45 + (reach - trunk * 0.45) * t) + Vector((0, 0, rise * (1 - t) ** 1.6 - 0.03 * t))
            radius = (0.16 * (1 - t) + 0.025 * t) * (trunk / 0.25) ** 0.5
            if 'root_radius' in BARK:                 # thinner spurs (many buttress ridges)
                radius *= BARK['root_radius']
            axis_up = Vector((0, 0, 1)).lerp(d, 0.35).normalized()
            loops.append([bm.verts.new(centre + (side * math.cos(2 * math.pi * j / sides)
                                                 + axis_up * math.sin(2 * math.pi * j / sides)) * radius)
                          for j in range(sides)])
        length = (reach - trunk * 0.45) + (BARK['root_rise'] if 'root_rise' in BARK else 0.38)
        for i in range(rings - 1):
            for j in range(sides):
                j2 = (j + 1) % sides
                face = bm.faces.new((loops[i][j], loops[i][j2], loops[i + 1][j2], loops[i + 1][j]))
                face.smooth = True
                for loop, (u, v) in zip(face.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                    loop[uv].uv = (u / sides * 0.6, v / (rings - 1) * length / TILE)
        tip = bm.verts.new(loops[-1][0].co.lerp(loops[-1][sides // 2].co, 0.5) + d * 0.05)
        for j in range(sides):
            bm.faces.new((loops[-1][j], loops[-1][(j + 1) % sides], tip)).smooth = True


def add_aerial_roots(bm, lod):
    """Prop roots: from points on the thick limbs, a tube drops almost vertically and flares outward into the ground,
    thickening toward its foot."""
    r = np.random.default_rng(AERIAL.get('seed', 404))
    points = []
    for s in cu.splines:
        for p in s.bezier_points:
            thick = p.radius * cu.bevel_depth
            if thick > 0.035 and AERIAL['z'][0] * H < p.co.z < AERIAL['z'][1] * H \
                    and Vector((p.co.x, p.co.y)).length > 0.35:
                points.append(Vector(p.co))
    if not points:
        return
    uv = bm.loops.layers.uv.active
    sides, segments = ((6, 7), (5, 4), (4, 3))[lod]
    keep = (1.0, 0.75, 0.5)[lod]
    order = r.permutation(len(points))[:AERIAL['count']]
    for k, index in enumerate(order):
        reach = r.uniform(*AERIAL['reach'])
        if k >= AERIAL['count'] * keep:
            continue
        top = points[int(index)]
        out = Vector((top.x, top.y, 0)).normalized()
        foot = Vector((top.x, top.y, 0)) + out * reach + Vector((0, 0, -0.06))
        loops = []
        for i in range(segments + 1):
            t = i / segments
            centre = top.lerp(Vector((top.x, top.y, foot.z)), t)
            centre += out * reach * t ** 2.5 + Vector((0, 0, 0))
            radius = AERIAL['radius'][0] + (AERIAL['radius'][1] - AERIAL['radius'][0]) * t ** 3
            axis = (Vector((0, 0, -1)) + out * 2.5 * t ** 1.5).normalized()
            side = axis.cross(Vector((0, 0, 1)) if abs(axis.z) < 0.99 else Vector((1, 0, 0))).normalized()
            other = axis.cross(side)
            loops.append([bm.verts.new(centre + (side * math.cos(2 * math.pi * j / sides)
                                                 + other * math.sin(2 * math.pi * j / sides)) * radius)
                          for j in range(sides)])
        length = (top - foot).length
        for i in range(segments):
            for j in range(sides):
                j2 = (j + 1) % sides
                face = bm.faces.new((loops[i][j], loops[i][j2], loops[i + 1][j2], loops[i + 1][j]))
                face.smooth = True
                for loop, (u, v) in zip(face.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                    loop[uv].uv = (u / sides * 0.5, v / segments * length / TILE)


def branch_mesh(lod, minimum=None):
    minimum = minimum or BRANCH_MIN[lod]
    parts = []
    trunk_thick = max(max(p.radius for p in s.bezier_points) for s in cu.splines) * cu.bevel_depth
    for s in cu.splines:
        thick = max(p.radius for p in s.bezier_points) * cu.bevel_depth
        if thick < minimum:
            continue
        # bark.bare_below (MM7 trees_a): limbs starting below this fraction of the height are left out (a clean
        # trunk under the crown instead of a fan of thin limbs)
        if BARK.get('bare_below') and thick < trunk_thick * 0.999 and s.bezier_points[0].co.z < BARK['bare_below'] * H:
            continue
        c = cu.copy()
        for other in list(c.splines):
            c.splines.remove(other)
        ns = c.splines.new('BEZIER'); ns.bezier_points.add(len(s.bezier_points) - 1)
        for a, b in zip(s.bezier_points, ns.bezier_points):
            b.co = a.co; b.handle_left = a.handle_left; b.handle_right = a.handle_right; b.radius = a.radius
            b.handle_left_type = a.handle_left_type; b.handle_right_type = a.handle_right_type
        sides = (8 if thick > 0.08 else 6 if thick > 0.04 else 4) if lod == 0 else (6 if thick > 0.08 else 4)
        c.bevel_resolution = (sides - 4) // 2
        c.resolution_u = (3 if thick > 0.08 else 1) if lod == 0 else (2 if thick > 0.08 and lod == 1 else 1)
        # a finer Sapling trunk (more curve segments, for a split near the ground) keeps the same ring spacing
        c.resolution_u = max(1, round(c.resolution_u * 6 / SAPLING['curveRes'][0]))
        o = bpy.data.objects.new('b', c); bpy.context.scene.collection.objects.link(o)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        bpy.data.objects.remove(o, do_unlink=True); bpy.data.curves.remove(c)
        around = max(1, round(2 * math.pi * thick * 0.8 / TILE)); along = max(bezier_length(s) / TILE, 0.3)
        uv = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        lo, hi = uv.min(0), uv.max(0); span = np.maximum(hi - lo, 1e-6)
        # Blender's curve UVs run u along the curve and v around the bevel: swap them so the bark's u goes around
        # (`around` tiles) and v along (`along` tiles), the furrows following the branch (MM7 trees_a fix; the MM6
        # copy scaled them the other way, stretching the bark along every branch)
        uv = ((uv - lo) / span)[:, ::-1] * np.array([around, along])
        if BARK.get('twist') and thick >= trunk_thick * 0.999:
            uv[:, 0] += BARK['twist'] * uv[:, 1]       # bark.twist (MM7 trees_a): spiral grain on the trunk
        me.uv_layers[0].data.foreach_set('uv', uv.ravel())
        parts.append(me)
    bm = bmesh.new()
    for me in parts:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    out = [v for v in bm.verts if v.co.z > CANOPY_LOW and Vector((v.co.x, v.co.y)).length > R(v.co.z) * 0.97]
    if BARK.get('clip_below_crown'):
        # limbs below the crown stay inside its lower footprint instead of poking out sideways
        reach = 0.75 * R(CANOPY_LOW + 0.15 * H)
        out += [v for v in bm.verts if 0.4 < v.co.z <= CANOPY_LOW and Vector((v.co.x, v.co.y)).length > reach]
    bmesh.ops.delete(bm, geom=out, context='VERTS')
    add_roots(bm, lod)
    if AERIAL:
        add_aerial_roots(bm, lod)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'bark{lod}'); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(f'bark{lod}', me); bpy.context.scene.collection.objects.link(obj)
    if len(me.polygons) > BRANCH_BUDGET[lod]:
        bpy.data.objects.remove(obj, do_unlink=True); bpy.data.meshes.remove(me)
        return branch_mesh(lod, minimum * 1.12)
    for p in obj.data.polygons:
        p.use_smooth = True
    print('BARK lod', lod, 'splines', len(parts), 'min thickness', round(minimum, 3), 'tris', len(me.polygons))
    return obj


barks = {lod: branch_mesh(lod) for lod in (0, 1, 2)}
tips = []
for s in cu.splines:
    thick = max(p.radius for p in s.bezier_points) * cu.bevel_depth
    if thick < CROWN['tip_thickness']:                # branch and twig ends (not trunk or limb segments)
        end = s.bezier_points[-1].co
        tips.append(np.array([end.x, end.y, end.z]))
tips = np.array(tips)
# crown.along {spacing, start, min_thickness, max_thickness} (MM7 trees_a): clump centres along the limbs instead of
# only at branch tips, so foliage sprays follow each branch shelf and the limbs show between them (conifers).
ALONG = CROWN.get('along')
limb_points, limb_tangents, limb_thick = [], [], []
if ALONG:
    trunk_thick = max(max(p.radius for p in s.bezier_points) * cu.bevel_depth for s in cu.splines)
    for s in cu.splines:
        thick = max(p.radius for p in s.bezier_points) * cu.bevel_depth
        if thick >= trunk_thick * 0.999 or thick < ALONG.get('min_thickness', 0.0) \
                or thick > ALONG.get('max_thickness', 1e9):
            continue
        pts = [np.array(p.co) for p in s.bezier_points]
        seg = [np.linalg.norm(b - a) for a, b in zip(pts, pts[1:])]
        total = sum(seg)
        if total < 1e-3:
            continue
        d = total * ALONG.get('start', 0.2)
        while d <= total:
            acc = 0.0
            for a, b, l in zip(pts, pts[1:], seg):
                if acc + l >= d:
                    limb_points.append(a + (b - a) * ((d - acc) / max(l, 1e-6)))
                    limb_tangents.append((b - a) / max(l, 1e-6))
                    limb_thick.append(thick)
                    break
                acc += l
            d += ALONG['spacing']
    limb_points = np.array(limb_points); limb_tangents = np.array(limb_tangents)
    print('ALONG limb points', len(limb_points))
bpy.data.objects.remove(skel, do_unlink=True)
print('TIPS', len(tips))

# ---------------------------------------------------------------- clumps


def fit(c, r, slack=1.0):
    """Pull a clump centre toward the crown axis/down until its ball (0.85 r) fits the envelope."""
    c = c.copy()
    for _ in range(60):
        rad = math.hypot(c[0], c[1])
        if rad + 0.85 * r <= R(min(c[2], H)) * slack and c[2] + 0.85 * r <= H and c[2] - 0.6 * r >= CANOPY_LOW:
            return c
        if c[2] + 0.85 * r > H:
            c[2] -= 0.05
        if c[2] - 0.6 * r < CANOPY_LOW:
            c[2] += 0.05
        if rad > 1e-3:
            c[:2] *= max(rad - 0.05, 0.0) / rad
    return c


depth = np.array([math.hypot(t[0], t[1]) / max(R(t[2]), 0.05) if CANOPY_LOW < t[2] < H else 0 for t in tips])


def place(pool, count, radius, accepted):
    """Clumps on branch tips, never closer than CLUMP_GAP x the sum of radii (neighbours stay separate balls)."""
    order = rng.permutation(len(pool))
    placed = 0
    for k in order:
        if placed >= count:
            break
        r = rng.uniform(*radius)
        if RADIUS_BY_WIDTH:
            widest = float(profile[:, 1].max()) * H
            r *= min(max(R(min(pool[k][2], H)) / widest, RADIUS_BY_WIDTH), 1.0)
        slack = LOBES['slack'] if LOBES and lobe_rng.random() < LOBES['fraction'] else 1.0
        c = fit(pool[k], r, slack)
        if TIERS and not any(lo * H <= c[2] <= hi * H for lo, hi in TIERS):
            continue
        if all(np.linalg.norm(c - a[0]) >= CLUMP_GAP * (r + a[1]) for a in accepted):
            accepted.append((c, r, radius is INNER_RADIUS)); placed += 1
            clump_slack.append(slack)
    return placed


FRONDS = CROWN.get('fronds')
clumps = []
# branch tips first (clumps hang on the limbs), then points of the crown's outer shell to fill the envelope
outer = tips[(depth > 0.55) & (tips[:, 2] > CANOPY_LOW + 0.2)]
if FRONDS:
    CLUMPS = 0; INNER_CLUMPS = 0; CROWN['shell'] = False
if ALONG:
    outer = np.concatenate([outer, limb_points]) if len(outer) else limb_points
place(outer, CLUMPS, OUTER_RADIUS, clumps)
shell = []
while len(shell) < 4000:
    z = rng.uniform(CANOPY_LOW + 0.3, H - 0.3); th = rng.uniform(0, 2 * math.pi)
    rad = R(z) * rng.uniform(0.5, 0.97)
    shell.append(np.array([rad * math.cos(th), rad * math.sin(th), z]))
shell = np.array(shell)
inner = tips[(depth > 0.15) & (depth <= 0.55) & (tips[:, 2] > CANOPY_LOW + 0.4)]
from_tips = len(clumps)
n_outer = from_tips + (place(shell, CLUMPS - from_tips, OUTER_RADIUS, clumps) if CROWN.get('shell', True) else 0)
n_inner = place(inner, INNER_CLUMPS, INNER_RADIUS, clumps)
if clumps:
    print('CLUMPS outer', n_outer, 'on tips', from_tips, 'inner', n_inner, 'radius', round(min(c[1] for c in clumps), 2),
          '..', round(max(c[1] for c in clumps), 2))

shapes = [rng.uniform(0.8, 1.25, 3) for _ in clumps]     # each clump a slightly irregular ellipsoid
if FLATTEN != 1.0:
    shapes = [shape * np.array([1.0, 1.0, FLATTEN]) for shape in shapes]
SPIRE = CROWN.get('spire')                # [top fraction, stretch]: clumps in the top of the crown grow tall and narrow
if SPIRE:
    shapes = [shape * (np.array([1 / math.sqrt(SPIRE[1])] * 2 + [SPIRE[1]]) if clumps[i][0][2] > (1 - SPIRE[0]) * H
                       else 1.0) for i, shape in enumerate(shapes)]
# moss strands (own rng): sorted longest first, so coarser levels keep the most visible ones
moss_strands = []
if MOSS:
    mr = np.random.default_rng(MOSS.get('seed', 707))
    weights = np.array([c[1] ** 2 * (0.3 if c[2] else 1.0) for c in clumps])
    if MOSS.get('band'):                      # MM7 trees_a: strands only from clumps in this height band (fractions of H)
        weights *= np.array([1.0 if MOSS['band'][0] * H <= c[0][2] <= MOSS['band'][1] * H else 0.0 for c in clumps])
    if MOSS.get('side_power'):                # MM7 trees_a: strands mostly from the crown's outer clumps (weeping sides)
        weights *= np.array([min(math.hypot(c[0][0], c[0][1]) / max(R(min(c[0][2], H)), 0.05), 1.0)
                             ** MOSS['side_power'] for c in clumps])
    weights /= weights.sum()
    for _ in range(MOSS['strands']):
        ci = int(mr.choice(len(clumps), p=weights)); c, r, _inner = clumps[ci]
        d = Vector(mr.normal(0, 1, 3)); d.z = -abs(d.z) - 0.4; d.normalize()
        top = Vector(c) + Vector(np.array(d) * shapes[ci]) * r * mr.uniform(0.55, 0.85)
        yaw = mr.uniform(0, math.pi)
        if MOSS.get('drape'):
            # moss.drape (MM7 trees_a): strands hang over the crown's side from the upper outer face of their
            # clump, facing outward (a weeping curtain), instead of from the clump's underside
            out = Vector((c[0], c[1], 0.0))
            out = out.normalized() if out.length > 1e-3 else Vector((1.0, 0.0, 0.0))
            out = Matrix.Rotation(mr.uniform(-0.7, 0.7), 3, 'Z') @ out
            top = Vector(c) + out * r * mr.uniform(0.8, 1.05) + Vector((0, 0, r * mr.uniform(*MOSS['drape'])))
            yaw = math.atan2(out.y, out.x) - math.pi / 2
        moss_strands.append((top, mr.uniform(*MOSS['length']), MOSS['width'] * mr.uniform(0.8, 1.25), yaw, ci))
    moss_strands.sort(key=lambda m: -m[1])
MOSS_KEEP = {0: 1.0, 1: 0.6, 2: 0.35}
moss_tris = {lod: 2 * int(len(moss_strands) * MOSS_KEEP[lod]) for lod in (0, 1, 2)}
bark_tris = len(barks[0].data.polygons)
cards_total = (TRI_BUDGET[0] - bark_tris - moss_tris[0]) // 2 - 20
area = np.array([r * r * (0.5 if inner_ else 1.0) for _, r, inner_ in clumps]); share = area / area.sum()
cards = []                          # centre, normal, roll, size, cell, clump index
for ci, (c, r, inner_) in enumerate(clumps):
    want = int(round(share[ci] * cards_total))
    centre = Vector(c)
    made = 0
    while made < want:
        d = Vector(rng.normal(0, 1, 3)).normalized()
        if d.dot(crown_normal(centre)) < -0.3 and rng.random() < 0.75:   # fewer cards on the crown-facing side
            continue
        rho = r * rng.uniform(0.35, 1.0) ** 0.5             # a dense leafy ball, densest near its surface
        p = centre + Vector(np.array(d) * shapes[ci]) * rho * (1 + 0.15 * math.sin(3 * d.x + 2 * d.z + ci))
        rad = math.hypot(p.x, p.y)
        if p.z > H + 0.2 or p.z < CANOPY_LOW - 0.3 or rad > R(min(p.z, H)) * 1.08 * clump_slack[ci]:
            continue
        n = (d + Vector(rng.normal(0, 0.35, 3))).normalized()
        if CARD_UP:
            n = (n + Vector((0, 0, CARD_UP))).normalized()
        roll = rng.uniform(0, 2 * math.pi); size = rng.uniform(*CARD)     # in this order (unchanged rng sequence)
        if RADIUS_BY_WIDTH:                       # small clumps (a spire) get proportionally small cards
            size *= min(max(r / OUTER_RADIUS[1], 0.45), 1.0)
        cell = int(rng.integers(4))
        if SNOW:                                  # snow cells on upward-facing cards, the plain ones elsewhere
            pool = SNOW['cells'] if n.z > SNOW.get('up', 0.3) else [k for k in range(4) if k not in SNOW['cells']]
            cell = pool[cell % len(pool)]
            if cell in SNOW['cells'] and SNOW.get('tilt'):      # snow lies on the upper side: those cards turn up
                n = (n + Vector((0, 0, SNOW['tilt']))).normalized()
        cards.append((p, n, roll, size, cell, ci))
        made += 1


def frond_cards():
    """crown.fronds (MM7 trees_a) {size [m, m], roll deg, droop, snow_by_height [[z fraction, p], ...], up_bias}:
    every limb point (crown.along) carries frond cards: the card's u axis runs along the limb from the point outward
    (the atlas frond's spine), rolled about the limb by up to `roll` degrees from flat (shelves seen from the side
    still show), drooping toward the tip. Each limb point is one 'clump' (centre, radius = half the card) for the
    occlusion terms, the LOD subsets and the LOD2 clump cards."""
    fr = np.random.default_rng(spec['seed'] + 77)
    bark_tris_ = len(barks[0].data.polygons)
    total = (TRI_BUDGET[0] - bark_tris_) // 2 - 20
    keep = [i for i, q in enumerate(limb_points) if CANOPY_LOW <= q[2] <= H * 1.01
            and math.hypot(q[0], q[1]) <= R(min(q[2], H)) * 1.02]
    keep = list(fr.permutation(keep))
    per = FRONDS.get('per_point', 1)
    keep = keep[:max(total // per, 1)]
    points = [(Vector(limb_points[i]), Vector(limb_tangents[i])) for i in keep]
    leader = FRONDS.get('leader')            # {from: fraction of H, count}: steep fronds up the leader (the spire)
    if leader:
        for j in range(leader['count']):
            z = H * (leader['from'] + (0.97 - leader['from']) * j / max(leader['count'] - 1, 1))
            a = fr.uniform(0, 2 * math.pi)
            points.append((Vector((0, 0, z)), Vector((math.cos(a), math.sin(a), leader.get('steep', 2.5))).normalized()))
    out_cards = []
    for q, tan in points:
        for j in range(per):
            t = tan.copy()
            hang = FRONDS.get('hang')            # {fraction, out}: weeping branchlets hanging from the limb
            if hang and t.z < 0.9 and fr.random() < hang['fraction']:
                flat = Vector((t.x, t.y, 0)).normalized() if math.hypot(t.x, t.y) > 1e-3 else Vector((1, 0, 0))
                t = flat * hang.get('out', 0.35) * fr.uniform(0.6, 1.4) + Vector((0, 0, -1))
            elif t.z < 0.9:
                t.z -= FRONDS.get('droop', 0.15) * fr.uniform(0.5, 1.5)
            t.normalize()
            size = fr.uniform(*FRONDS['size'])
            if FRONDS.get('size_by_width'):       # smaller fronds where the envelope narrows (a pointed top)
                widest = float(profile[:, 1].max()) * H
                size *= min(max(R(min(q.z, H)) / widest, FRONDS['size_by_width']), 1.0)
            reach = R(min(q.z, H)) * 1.06 - math.hypot(q.x, q.y)
            # the far end stays inside the sprite's envelope (shorter fronds near the spire and the crown edge)
            horiz = max(math.hypot(t.x, t.y), 0.2)
            size = max(min(size, reach / horiz, (H * 1.01 - q.z) / max(t.z, 0.05) if t.z > 0.3 else 1e9),
                       FRONDS['size'][0] * 0.35)
            up = Vector((0, 0, 1)) - t * t.z; up.normalize()
            side = t.cross(up)
            alpha = math.radians(fr.uniform(-FRONDS.get('roll', 50), FRONDS.get('roll', 50)))
            n = (up * math.cos(alpha) + side * math.sin(alpha)).normalized()
            if n.z < 0:
                n = -n
            p = q + t * size * 0.5 + n * fr.uniform(-0.02, 0.02)
            z = float(q.z / H)
            p_snow = float(np.interp(z, *zip(*SNOW['by_height']))) if SNOW and 'by_height' in SNOW else 0.0
            if SNOW:
                pool = SNOW['cells'] if fr.random() < p_snow else [c for c in range(4) if c not in SNOW['cells']]
            else:
                pool = list(range(4))
            cell = int(pool[int(fr.integers(len(pool)))])
            t0 = n.orthogonal().normalized()
            roll = math.atan2(n.cross(t0).dot(t), t0.dot(t))
            out_cards.append((p, n, roll, size, cell, len(clumps)))
            clumps.append((np.array(p), size * 0.5, False))
            clump_slack.append(1.0)
    return out_cards


if FRONDS:
    cards = frond_cards()
    shapes = [np.ones(3) for _ in clumps]
print('CARDS', len(cards))
clump_cell = {c[5]: c[4] for c in cards}       # frond trees: each card is its own clump (kept through lod.thin0)


def card_corners(card, grow, outward=0.0):
    p, n, roll, size, cell, ci = card
    s = size * grow
    if outward:                                       # coarse levels: cards turn toward the viewer side of the crown
        n = (n + crown_normal(p) * outward).normalized()
    t = n.orthogonal().normalized(); b = n.cross(t)
    rot = Matrix.Rotation(roll, 3, n); t = rot @ t; b = rot @ b
    return [p + (-t - b) * s / 2, p + (t - b) * s / 2, p + (t + b) * s / 2, p + (-t + b) * s / 2]


def shading_normal(q, ci):
    c = Vector(clumps[ci][0])
    if FRONDS:
        # a frond's light comes from above: snowy fronds face the sky (snow lies on top), green ones half way
        up = FRONDS.get('snow_up', 1.2) if SNOW and clump_cell[ci] in SNOW['cells'] else FRONDS.get('green_up', 0.35)
        return (0.5 * (q - c).normalized() + 0.5 * crown_normal(q) + Vector((0, 0, up))).normalized()
    return (0.7 * (q - c).normalized() + 0.3 * crown_normal(q)).normalized()


# ---------------------------------------------------------------- occlusion rays against the LOD0 cards
tris_v, tris_i, tri_card = [], [], []
for k, card in enumerate(cards):
    cs = card_corners(card, 1.0); base = len(tris_v)
    tris_v += [tuple(q) for q in cs]; tris_i += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
bvh = BVHTree.FromPolygons(tris_v, tris_i)
RAYS = 32
# uniform over the sky hemisphere: side light reaches the lower crown, as on the sprite (only gaps go black)
dirs_sky = rng.normal(0, 1, (2048, 3)); dirs_sky /= np.linalg.norm(dirs_sky, axis=1, keepdims=True)
dirs_sky = dirs_sky[dirs_sky[:, 2] > 0.02][:512]


def visibility(point, normal, skip=None):
    """Sky visibility: cosine-weighted rays over the upper hemisphere (sky light), through the leaf cards."""
    hits = 0.0
    sel = rng.choice(len(dirs_sky), RAYS, replace=False)
    for d in dirs_sky[sel]:
        d = Vector(d)
        origin = point + d * 0.02
        transmit = 1.0
        for _ in range(12):
            loc, _, index, dist = bvh.ray_cast(origin, d, 12.0)
            if loc is None:
                break
            if skip is None or index // 2 != skip:
                transmit *= 1.0 - COVERAGE
                if transmit < 0.05:
                    break
            origin = loc + d * 0.01
        hits += transmit
    return hits / RAYS


clump_tint = [np.array([rng.uniform(0.9, 1.1), 1.0, rng.uniform(0.88, 1.08)]) * rng.uniform(0.88, 1.12)
              for _ in clumps]


def snow_lift(o):
    """Snow cards (leaves.snow.lift) keep more light: snow on the branch tops stays bright inside the crown."""
    return o + SNOW.get('lift', 0.0) * (1.0 - o)


def occlusion(vis):
    return OCC['floor'] + OCC['range'] * vis ** OCC['power']


def local_term(q, ci):
    """Clump-local shading: lit clump top, shaded underside, darker toward the clump core."""
    c = Vector(clumps[ci][0]); r = clumps[ci][1]
    return (0.28 + 0.72 * (0.5 + 0.5 * (q - c).normalized().z)) * (0.6 + 0.4 * min((q - c).length / r, 1.0))


card_occ = []                       # per card: four corner colours (linear rgb)
card_rank = []                      # per card: mean occlusion before any snow lift (LOD subsets rank by it)
card_sky = []                       # per card: mean sky occlusion (clump cards of LOD2 carry it per clump)
for k, card in enumerate(cards):
    corners = card_corners(card, 1.0); ci = card[5]
    sky = [occlusion(visibility(q, shading_normal(q, ci), skip=k)) for q in corners]
    card_sky.append(sum(sky) / 4)
    occ = [o * local_term(q, ci) for o, q in zip(sky, corners)]
    mean = sum(occ) / 4
    card_occ.append([clump_tint[ci] * (0.7 * o + 0.3 * mean) for o in occ])   # partly per card: less ray noise
    card_rank.append(np.mean([c.mean() for c in card_occ[-1]]))
    if SNOW and card[4] in SNOW['cells'] and SNOW.get('lift'):
        card_occ[-1] = [snow_lift(o) for o in card_occ[-1]]
vis_card = np.array(card_rank)
print('OCCLUSION cards min/mean/max', round(float(vis_card.min()), 2), round(float(vis_card.mean()), 2),
      round(float(vis_card.max()), 2))
THIN0 = LOD.get('thin0', 0.0)
if THIN0:
    # lod.thin0 (MM7 trees_a): drop that fraction of the LOD0 cards, the least sky-visible first (buried in the crown,
    # covered by the cards around them); the sky rays for the bark use the thinned crown.
    drop = set(np.argsort(vis_card)[:int(len(cards) * THIN0)].tolist())
    keep_idx = [k for k in range(len(cards)) if k not in drop]
    cards = [cards[k] for k in keep_idx]; card_occ = [card_occ[k] for k in keep_idx]
    card_rank = [card_rank[k] for k in keep_idx]; card_sky = [card_sky[k] for k in keep_idx]
    vis_card = vis_card[keep_idx]
    tris_v, tris_i = [], []
    for card in cards:
        cs = card_corners(card, 1.0); base = len(tris_v)
        tris_v += [tuple(q) for q in cs]; tris_i += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    bvh = BVHTree.FromPolygons(tris_v, tris_i)
    print('THIN0 dropped', len(drop), 'cards, kept', len(cards))


def set_colours(me, colours):
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    flat = np.concatenate([np.append(c, 1.0) for c in colours])
    attr.data.foreach_set('color', flat)
    me.color_attributes.active_color = attr


for lod, obj in barks.items():
    me = obj.data; me.calc_loop_triangles() if hasattr(me, 'calc_loop_triangles') else None
    colours = []
    for v in me.vertices:
        p = obj.matrix_world @ v.co
        # Bark keeps more light than the leaves: the sprite's trunk is side-lit, and the darkest crevices are already in
        # the bark texture (ambient occlusion baked in).
        o = BARK['occlusion_floor'] + (1.0 - BARK['occlusion_floor']) * visibility(p, v.normal)
        colours.append(np.array([o, o, o]))
    set_colours(me, colours)

# ---------------------------------------------------------------- leaf meshes per LOD


def subset(lod):
    if lod == 0:
        return list(range(len(cards)))
    want = (TRI_BUDGET[lod] - len(barks[lod].data.polygons) - moss_tris[lod]) // 2 - 10
    picked = []
    if FRONDS:                    # one card per clump: keep the most visible cards (with a little spread)
        jitter = np.random.default_rng(spec['seed'] + 91 + lod).uniform(0, 0.08, len(cards))
        return list(np.argsort(-(vis_card + jitter))[:want])
    for ci in range(len(clumps)):
        members = [k for k, c in enumerate(cards) if c[5] == ci]
        n = max(2, int(round(len(members) * want / len(cards))))
        # most visible half (LOD1) / third (LOD2) of the clump, spread by farthest-point sampling
        pool = sorted(members, key=lambda k: -vis_card[k])[:max(n, int(len(members) * LOD['keep'][lod]))]
        pts = np.array([cards[k][0] for k in pool]); sel = [0]
        dist = np.linalg.norm(pts - pts[0], axis=1)
        for _ in range(min(n, len(pool)) - 1):
            j = int(dist.argmax()); sel.append(j); dist = np.minimum(dist, np.linalg.norm(pts - pts[j], axis=1))
        picked += [pool[j] for j in sel]
    return picked[:want]


def leaf_mesh(lod):
    sel = subset(lod)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for k in sel:
        card = cards[k]; cs = card_corners(card, GROW[lod], OUTWARD[lod]); ci = card[5]
        vs = [bm.verts.new(q) for q in cs]
        f = bm.faces.new(vs)
        if SNOW_MATERIAL and card[4] in SNOW['cells']:
            f.material_index = 1                      # LeavesSnow
        row, col = divmod(card[4], 2)
        u0, v0 = 0.5 * col, 0.5 * (1 - row)          # Blender v up: image row 0 = v 0.5..1
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + 0.5 * du, v0 + 0.5 * dv)
        for q, occ in zip(cs, card_occ[k]):
            normals.append(shading_normal(q, ci)); colours.append(occ * TONE[lod])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'leaves{lod}'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'leaves{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('LEAVES lod', lod, 'cards', len(sel), 'tris', len(me.polygons), 'grow', GROW[lod])
    return obj


leaves = {lod: leaf_mesh(lod) for lod in (0, 1, 2)}
clump_sky = {}
for k, card in enumerate(cards):
    clump_sky.setdefault(card[5], []).append(card_sky[k])


def moss_mesh(lod):
    """Hanging strands: vertical cards (u across, v 1 at the top), COLOR_0 = the clump's sky occlusion x tint, a
    little darker toward the bottom."""
    keep = moss_strands[:int(len(moss_strands) * MOSS_KEEP[lod])]
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for top, length, width, yaw, ci in keep:
        t = Vector((math.cos(yaw), math.sin(yaw), 0)); n = Vector((-t.y, t.x, 0))
        corners = [top - t * width / 2 - Vector((0, 0, length)), top + t * width / 2 - Vector((0, 0, length)),
                   top + t * width / 2, top - t * width / 2]
        f = bm.faces.new([bm.verts.new(q) for q in corners])
        for loop, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = c
        # moss hangs in the open below the clump: lighter than the clump's own sky occlusion
        sky = 0.5 + 0.5 * float(np.mean(clump_sky.get(ci, [0.6])))
        for v in (0.75, 0.75, 1.0, 1.0):
            normals.append(n); colours.append(clump_tint[ci] * sky * v * np.asarray(TONE[lod], float))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'moss{lod}'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'moss{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('MOSS lod', lod, 'strands', len(keep), 'tris', len(me.polygons))
    return obj


mosses = {lod: moss_mesh(lod) for lod in (0, 1, 2)} if MOSS else {}


def image(name, colorspace):
    img = bpy.data.images.load(os.path.join(OUT if name.startswith('leaves') else WORK, name))
    img.colorspace_settings.name = colorspace
    return img


def material(name, base, normal, roughness, alpha=False, rough_map=None, normal_strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = image(base, 'sRGB')
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(normal, 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nm.inputs['Strength'].default_value = normal_strength     # exported as normalTexture.scale
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    if rough_map:
        # glTF metallic-roughness texture: the exporter packs the green channel into roughness.
        tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = image(rough_map, 'Non-Color')
        sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tr.outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
        nt.links.new(sep.outputs['Blue'], bsdf.inputs['Metallic'])
        bsdf.inputs['Roughness'].default_value = 1.0
    if alpha:
        m.use_backface_culling = False
        m.surface_render_method = 'DITHERED'
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tb.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
    return m


bark_mat = material('Bark', 'bark_basecolor.png', 'bark_normal.png', 0.9, rough_map='bark_mr.png', normal_strength=1.6)
leaf_mat = material('Leaves', 'leaves_basecolor.png', 'leaves_normal.png', 0.85, alpha=True)
bark_mat['openyamm_wind'] = 0.03
leaf_mat['openyamm_wind'] = 0.12
leaf_mat['openyamm_translucency'] = 0.35
if SNOW_MATERIAL:
    snow_mat = material('LeavesSnow', 'leaves_basecolor.png', 'leaves_normal.png', 0.85, alpha=True)
    snow_mat['openyamm_wind'] = 0.12
    snow_mat['openyamm_translucency'] = SNOW_MATERIAL.get('translucency', 0.35)
    sb = next(n for n in snow_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    sb.inputs['Emission Color'].default_value = (1, 1, 1, 1)
    sb.inputs['Emission Strength'].default_value = SNOW_MATERIAL.get('emissive', 0.0)
if MOSS:
    moss_mat = material('Moss', 'moss_basecolor.png', 'moss_normal.png', 0.95, alpha=True)
    moss_mat['openyamm_wind'] = 0.12
    moss_mat['openyamm_translucency'] = 0.2
names = {0: 'Tree', 1: 'Tree_LOD1', 2: 'Tree_LOD2'}
for lod in (0, 1, 2):
    b, l = barks[lod], leaves[lod]
    b.data.materials.append(bark_mat); l.data.materials.append(leaf_mat)
    if SNOW_MATERIAL:
        l.data.materials.append(snow_mat)
    parts = (b, l)
    if MOSS:
        mosses[lod].data.materials.append(moss_mat); parts = (b, l, mosses[lod])
    for x in bpy.data.objects:
        x.select_set(x in parts)
    bpy.context.view_layer.objects.active = b
    bpy.ops.object.join()
    b.name = names[lod]; b.data.name = names[lod]
    print('LOD', lod, names[lod], 'tris', len(b.data.polygons), 'colour attrs', list(b.data.color_attributes.keys()))
# per clump: centre, radius, inner flag, tint, mean sky occlusion, and its LOD0 cards (corners, local terms, cell,
# shading normals) for clump_cards.py
clump_data = []
by_clump = {}
for k, card in enumerate(cards):
    by_clump.setdefault(card[5], []).append(k)
for ci, (c, r, inner_) in enumerate(clumps):
    members = by_clump.get(ci, [])
    clump_data.append({'centre': list(map(float, c)), 'radius': float(r), 'inner': bool(inner_),
                       'tint': clump_tint[ci].round(4).tolist(),
                       'sky': float(np.mean([snow_lift(card_sky[k]) if SNOW and cards[k][4] in SNOW['cells']
                                             else card_sky[k] for k in members])) if members else 1.0,
                       'cards': [{'corners': [list(map(float, q)) for q in card_corners(cards[k], 1.0)],
                                  'local': [float(snow_lift(local_term(q, ci)) if SNOW and cards[k][4] in SNOW['cells']
                                                  else local_term(q, ci)) for q in card_corners(cards[k], 1.0)],
                                  'normals': [list(map(float, shading_normal(q, ci)))
                                              for q in card_corners(cards[k], 1.0)],
                                  'cell': int(cards[k][4])} for k in members]})
json.dump({'clumps': clump_data, 'tone': TONE}, open(os.path.join(OUT, 'clumps.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'tree.blend'))
