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
LEAF_TINT, BARK_TINT = common.tints(spec)      # shared textures: the species colour goes into COLOR_0
CELLS = spec['leaves']['cells']                 # the species' cells of the shared leaf atlas
print('TINT leaves', LEAF_TINT.round(3), 'bark', BARK_TINT.round(3))
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
_prof = json.load(open(os.path.join(WORK, 'profile.json')))
profile = np.array(_prof['half_width_by_height'])
# MM8 option crown.follow_centre: the whole skeleton is sheared sideways (x) to follow the sprite's centre line per
# height (leaning, curving trunks), smoothed; radial tests measure from that line (radial()).
FOLLOW = CROWN.get('follow_centre', 0.0)
_centre = np.array(_prof['centre_by_height'])
if FOLLOW:
    _c = _centre[:, 1].copy()
    for _ in range(CROWN.get('centre_smooth', 3)):
        _c = np.convolve(np.pad(_c, 1, mode='edge'), [0.25, 0.5, 0.25], 'valid')
    _centre[:, 1] = _c * FOLLOW
    _centre[:, 1] -= _centre[0, 1]                 # the trunk foot stays at the origin


def Cx(z):
    return float(np.interp(z / H, _centre[:, 0], _centre[:, 1])) * H if FOLLOW else 0.0


# crown.centre_line [[z, x], ...] (fractions of the height): the skeleton's shear (the trunk's path) when it differs
# from the crown's centre per row (a trunk curving up into a crown carried off to one side, tree19)
_line = np.array(CROWN['centre_line']) if CROWN.get('centre_line') else None


def shear_x(z):
    if CROWN.get('shear', True) is False:          # MM8 option: an upright skeleton under an offset envelope
        return 0.0
    if _line is not None:
        return float(np.interp(z / H, _line[:, 0], _line[:, 1])) * H
    return Cx(z)


def radial(x, y, z):
    return math.hypot(x - Cx(z), y)


def R(z):
    return float(np.interp(z / H, profile[:, 0], profile[:, 1])) * H


CANOPY_LOW = CROWN['canopy_low'] * H
CENTRE = Vector((0, 0, CROWN['centre'] * H))


def crown_normal(p):
    o = p - CENTRE; o.x -= Cx(CENTRE.z); o.z *= CROWN['crown_normal_z']
    return o.normalized()


# ---------------------------------------------------------------- skeleton and bark (as v1)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.curve.tree_add(do_update=True, bevel=True, showLeaves=False, useArm=False, prune=False, **SAPLING)
skel = bpy.data.objects['tree']; cu = skel.data
if FOLLOW or _line is not None:
    for s_ in cu.splines:
        for bp in s_.bezier_points:
            for attr in ('co', 'handle_left', 'handle_right'):
                v = getattr(bp, attr).copy(); v.x += shear_x(max(v.z, 0.0)); setattr(bp, attr, v)


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
    for s in cu.splines:
        thick = max(p.radius for p in s.bezier_points) * cu.bevel_depth
        if thick < minimum:
            continue
        c = cu.copy()
        for other in list(c.splines):
            c.splines.remove(other)
        points = list(s.bezier_points)
        if BARK.get('truncate'):
            # MM8 option: end a branch at its first point outside the envelope (vertex clipping alone can leave a
            # detached upper piece floating when a branch leaves the envelope and re-enters it)
            clip_z = max(CANOPY_LOW, BARK.get('clip_from', CROWN['canopy_low']) * H)
            for k, p in enumerate(points):
                q = p.co
                if q.z > clip_z and radial(q.x, q.y, q.z) > R(q.z) and math.hypot(q.x - shear_x(q.z), q.y) \
                        >= BARK.get('clip_keep', 0.08) * H:
                    points = points[:k]
                    break
            if len(points) < 2:
                bpy.data.curves.remove(c)
                continue
        truncated = len(points) < len(s.bezier_points)
        ns = c.splines.new('BEZIER'); ns.bezier_points.add(len(points) - 1)
        for a, b in zip(points, ns.bezier_points):
            b.co = a.co; b.handle_left = a.handle_left; b.handle_right = a.handle_right; b.radius = a.radius
            b.handle_left_type = a.handle_left_type; b.handle_right_type = a.handle_right_type
        if truncated:                                   # a truncated branch tapers to a point (no open pipe end)
            ns.bezier_points[-1].radius *= 0.12
            if len(ns.bezier_points) > 2:
                ns.bezier_points[-2].radius *= 0.6
        big, mid = BARK.get('sides', [0.08, 0.04])     # MM8 trees are ~12 m: thresholds per species (m)
        sides = (8 if thick > big else 6 if thick > mid else 4) if lod == 0 else (6 if thick > big else 4)
        c.bevel_resolution = (sides - 4) // 2
        c.resolution_u = (3 if thick > big else 1) if lod == 0 else (2 if thick > big and lod == 1 else 1)
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
        # (`around` tiles) and v along (`along` tiles), the furrows following the branch (fix from the MM7 trees_a
        # copy; the MM6 original scaled them the other way, stretching the bark along every branch)
        uv = ((uv - lo) / span)[:, ::-1] * np.array([around, along]); me.uv_layers[0].data.foreach_set('uv', uv.ravel())
        parts.append(me)
    bm = bmesh.new()
    for me in parts:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    # the envelope is measured from each sprite row's centre; on lopsided crowns that lies far from the trunk, so
    # nothing near the trunk line is clipped (it would leave cut, box-like stubs)
    near_trunk = lambda v: math.hypot(v.co.x - shear_x(v.co.z), v.co.y) < BARK.get('clip_keep', 0.08) * H
    clip_from = BARK.get('clip_from', CROWN['canopy_low']) * H      # MM8 option: clip only above this height
    out = [v for v in bm.verts if v.co.z > max(CANOPY_LOW, clip_from)
           and radial(v.co.x, v.co.y, v.co.z) > R(v.co.z) * 0.97 and not near_trunk(v)]
    if BARK.get('clip_below_crown'):
        # limbs below the crown stay inside its lower footprint instead of poking out sideways
        reach = 0.75 * R(CANOPY_LOW + 0.15 * H)
        out += [v for v in bm.verts if 0.4 < v.co.z <= CANOPY_LOW and radial(v.co.x, v.co.y, v.co.z) > reach]
    bmesh.ops.delete(bm, geom=out, context='VERTS')
    if BARK.get('truncate'):
        # small islands the vertex clip cut off a branch (not attached to anything) are dropped
        seen, islands = set(), []
        for v in bm.verts:
            if v in seen:
                continue
            stack, island = [v], []
            seen.add(v)
            while stack:
                x = stack.pop(); island.append(x)
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if y not in seen:
                        seen.add(y); stack.append(y)
            islands.append(island)
        floating = [x for isl in islands if min(x.co.z for x in isl) > 0.08 * H and len(isl) < 40
                    and min(math.hypot(x.co.x - shear_x(x.co.z), x.co.y) for x in isl) > 0.15 * H for x in isl]
        bmesh.ops.delete(bm, geom=floating, context='VERTS')
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
bpy.data.objects.remove(skel, do_unlink=True)
print('TIPS', len(tips))

# ---------------------------------------------------------------- clumps


def fit(c, r, slack=1.0):
    """Pull a clump centre toward the crown axis/down until its ball (0.85 r) fits the envelope."""
    c = c.copy()
    for _ in range(60):
        rad = radial(c[0], c[1], c[2])
        if rad + 0.85 * r <= R(min(c[2], H)) * slack and c[2] + 0.85 * r <= H and c[2] - 0.6 * r >= CANOPY_LOW:
            return c
        if c[2] + 0.85 * r > H:
            c[2] -= 0.05
        if c[2] - 0.6 * r < CANOPY_LOW:
            c[2] += 0.05
        if rad > 1e-3:
            cx = Cx(c[2])
            c[0] = cx + (c[0] - cx) * max(rad - 0.05, 0.0) / rad; c[1] *= max(rad - 0.05, 0.0) / rad
    return c


depth = np.array([radial(t[0], t[1], t[2]) / max(R(t[2]), 0.05) if CANOPY_LOW < t[2] < H else 0 for t in tips])


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
        # MM8 option crown.exclude [[x0, x1, z0, z1], ...] (fractions of the height, x from the trunk foot in the
        # sprite's view): no foliage there, so the limbs inside stay bare (tree20's dead branch)
        if any(x0 * H <= c[0] <= x1 * H and z0 * H <= c[2] <= z1 * H for x0, x1, z0, z1 in CROWN.get('exclude', [])):
            continue
        if all(np.linalg.norm(c - a[0]) >= CLUMP_GAP * (r + a[1]) for a in accepted):
            accepted.append((c, r, radius is INNER_RADIUS)); placed += 1
            clump_slack.append(slack)
    return placed


clumps = []
# branch tips first (clumps hang on the limbs), then points of the crown's outer shell to fill the envelope
outer = tips[(depth > 0.55) & (tips[:, 2] > CANOPY_LOW + 0.2)]
place(outer, CLUMPS, OUTER_RADIUS, clumps)
shell = []
while len(shell) < 4000:
    z = rng.uniform(CANOPY_LOW + 0.3, H - 0.3); th = rng.uniform(0, 2 * math.pi)
    rad = R(z) * rng.uniform(0.5, 0.97)
    shell.append(np.array([Cx(z) + rad * math.cos(th), rad * math.sin(th), z]))
shell = np.array(shell)
inner = tips[(depth > 0.15) & (depth <= 0.55) & (tips[:, 2] > CANOPY_LOW + 0.4)]
from_tips = len(clumps)
n_outer = from_tips + place(shell, CLUMPS - from_tips, OUTER_RADIUS, clumps)
n_inner = place(inner, INNER_CLUMPS, INNER_RADIUS, clumps)
print('CLUMPS outer', n_outer, 'on tips', from_tips, 'inner', n_inner, 'radius', round(min(c[1] for c in clumps), 2), '..',
      round(max(c[1] for c in clumps), 2))

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
    weights = np.array([c[1] ** 2 * (0.3 if c[2] else 1.0) for c in clumps]); weights /= weights.sum()
    for _ in range(MOSS['strands']):
        ci = int(mr.choice(len(clumps), p=weights)); c, r, _inner = clumps[ci]
        d = Vector(mr.normal(0, 1, 3)); d.z = -abs(d.z) - 0.4; d.normalize()
        top = Vector(c) + Vector(np.array(d) * shapes[ci]) * r * mr.uniform(0.55, 0.85)
        yaw = mr.uniform(0, math.pi)
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
        rad = radial(p.x, p.y, p.z)
        if p.z > H + 0.2 or p.z < CANOPY_LOW - 0.3 or rad > R(min(p.z, H)) * 1.08 * clump_slack[ci]:
            continue
        n = (d + Vector(rng.normal(0, 0.35, 3))).normalized()
        if CARD_UP:
            n = (n + Vector((0, 0, CARD_UP))).normalized()
        roll = rng.uniform(0, 2 * math.pi); size = rng.uniform(*CARD)     # in this order (unchanged rng sequence)
        if RADIUS_BY_WIDTH:                       # small clumps (a spire) get proportionally small cards
            size *= min(max(r / OUTER_RADIUS[1], 0.45), 1.0)
        cell = CELLS[int(rng.integers(len(CELLS)))]
        if SNOW:                                  # snow cells on upward-facing cards, the plain ones elsewhere
            pool = SNOW['cells'] if n.z > SNOW.get('up', 0.3) else [k for k in range(4) if k not in SNOW['cells']]
            cell = pool[cell % len(pool)]
            if cell in SNOW['cells'] and SNOW.get('tilt'):      # snow lies on the upper side: those cards turn up
                n = (n + Vector((0, 0, SNOW['tilt']))).normalized()
        cards.append((p, n, roll, size, cell, ci))
        made += 1
print('CARDS', len(cards))


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
            loc, _, index, dist = bvh.ray_cast(origin, d, max(12.0, 1.6 * H))
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
    lo, core = CROWN.get('local', [0.28, 0.6])     # MM8 option: softer per-clump shading (less 'ball' look)
    return (lo + (1 - lo) * (0.5 + 0.5 * (q - c).normalized().z)) * (core + (1 - core) * min((q - c).length / r, 1.0))


card_occ = []                       # per card: four corner colours (linear rgb)
card_rank = []                      # per card: mean occlusion before any snow lift (LOD subsets rank by it)
card_sky = []                       # per card: mean sky occlusion (clump cards of LOD2 carry it per clump)
for k, card in enumerate(cards):
    corners = card_corners(card, 1.0); ci = card[5]
    sky = [occlusion(visibility(q, shading_normal(q, ci), skip=k)) for q in corners]
    card_sky.append(sum(sky) / 4)
    occ = [o * local_term(q, ci) for o, q in zip(sky, corners)]
    mean = sum(occ) / 4
    card_occ.append([LEAF_TINT * clump_tint[ci] * (0.7 * o + 0.3 * mean) for o in occ])   # partly per card: less ray noise
    card_rank.append(np.mean([c.mean() for c in card_occ[-1]]))
    if SNOW and card[4] in SNOW['cells'] and SNOW.get('lift'):
        card_occ[-1] = [snow_lift(o) for o in card_occ[-1]]
vis_card = np.array(card_rank)
print('OCCLUSION cards min/mean/max', round(float(vis_card.min()), 2), round(float(vis_card.mean()), 2),
      round(float(vis_card.max()), 2))


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
        colours.append(BARK_TINT * o)
    set_colours(me, colours)

# ---------------------------------------------------------------- leaf meshes per LOD


def subset(lod):
    if lod == 0:
        return list(range(len(cards)))
    want = (TRI_BUDGET[lod] - len(barks[lod].data.polygons) - moss_tris[lod]) // 2 - 10
    picked = []
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
        u0, v0, su, sv = common.cell_uv(spec, card[4])
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + su * du, v0 + sv * dv)
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
    img = bpy.data.images.load(common.shared_path(name) if os.path.exists(common.shared_path(name))
                               else os.path.join(WORK, name))
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
leaf_mat = material('Leaves', f"{spec['atlas']}_basecolor.png", f"{spec['atlas']}_normal.png", 0.85, alpha=True)
bark_mat['openyamm_wind'] = spec['wind']['bark']
leaf_mat['openyamm_wind'] = spec['wind']['leaves']
leaf_mat['openyamm_translucency'] = spec['translucency']
if MOSS:
    moss_mat = material('Moss', 'moss_basecolor.png', 'moss_normal.png', 0.95, alpha=True)
    moss_mat['openyamm_wind'] = 0.12
    moss_mat['openyamm_translucency'] = 0.2
names = {0: 'Tree', 1: 'Tree_LOD1', 2: 'Tree_LOD2'}
for lod in (0, 1, 2):
    b, l = barks[lod], leaves[lod]
    b.data.materials.append(bark_mat); l.data.materials.append(leaf_mat)
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
for ci, (c, r, inner_) in enumerate(clumps):
    members = [k for k, card in enumerate(cards) if card[5] == ci]
    clump_data.append({'centre': list(map(float, c)), 'radius': float(r), 'inner': bool(inner_),
                       'tint': (LEAF_TINT * clump_tint[ci]).round(5).tolist(),
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
