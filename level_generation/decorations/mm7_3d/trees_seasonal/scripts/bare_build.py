"""Bare (winter) state of a seasonal family: the family's own Sapling skeleton (same settings and seed as its summer
species, so trunk, limbs, root spurs and height are identical) without leaves. work/<id>/tree.blend: objects Tree,
Tree_LOD1, Tree_LOD2 (materials Bark and Twigs), each with the 'Color' point attribute (COLOR_0).

- Tubes: every spline at least bare.min_thickness[lod] thick (raised 12 % at a time until bare.budget[lod] holds),
  bevelled as build_tree.py does (sides by thickness, the same bark UVs), without the summer crown-envelope cut; the
  summer root spurs (same code, so the same LOD0 lower bound).
- Twig cards (Twigs, the procedural atlas of bare_prepare.py): every thinner spline becomes one card along its chord,
  and each thin tube ends in a spray card along its end tangent (the fine twigs the sprites draw). Coarser levels keep
  the longest cards (bare.card_keep), grown (bare.card_grow). Card bases sit on their branch; shading normals point
  outward and up.
- Height: the engine scales a model so its LOD0 height is the binding height, and a family shares one binding, so the
  bare tree must reach exactly the summer model's LOD0 top (work/<family>/model.json, after the card cut). Cards stop
  just under it; a thin tapered leader tube grows from the highest branch tip to exactly that top.
- COLOR_0: sky visibility against the bare wood (16 rays; the ground blocks downward rays), floor bare.occlusion_floor,
  darker near the ground; twig cards take it at their centre x bare.twig_tone.
Usage: blender --background --python bare_build.py -- <id>"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
W = spec['work']; H = spec['height_m']; BARK = spec['bark']; BARE = spec['bare']; SAPLING = spec['sapling']
TILE = BARK['tile']
family = common.load(spec['family'])
TOP = json.load(open(os.path.join(family['work'], 'model.json')))['bounds_max'][1]   # glTF y = Blender z
rng = np.random.default_rng(BARE.get('seed', 1717))
LODS = (0, 1, 2)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.curve.tree_add(do_update=True, bevel=True, showLeaves=False, useArm=False, prune=False, **SAPLING)
skel = bpy.data.objects['tree']; cu = skel.data
GNARL = BARE.get('gnarl')
if GNARL:
    # Quality pass (2026-10-16): the winter crown closer to the native bare sprite. Below the fork (trunk, root flare)
    # nothing changes; above it, ramped in over GNARL['ramp'] m: limbs pulled in to the sprite's silhouette
    # (work/bare_profile.json from bare_prepare.py, scale per height clamped to GNARL['fit']), a smooth displacement
    # field of a few sines (GNARL['amp'] m, wavelength GNARL['wavelength'] m) for crooked, kinked limbs, and radii
    # thickened by GNARL['thick']. Every bezier point and both handles move by the same functions of position, so
    # child branches stay on their parents.
    fork = GNARL['fork'] * H
    ramp = GNARL.get('ramp', 1.0)

    def weight(z):
        t = min(max((z - fork) / ramp, 0.0), 1.0)
        return t * t * (3 - 2 * t)

    pts = [p for s in cu.splines for p in s.bezier_points]
    band = 0.25
    zs = np.array([p.co.z for p in pts]); rs = np.array([math.hypot(p.co.x, p.co.y) for p in pts])
    nb = int(TOP / band) + 2
    reach = np.zeros(nb)
    for z, r in zip(zs, rs):
        k = min(max(int(z / band), 0), nb - 1); reach[k] = max(reach[k], r)
    for k in range(1, nb):                       # bands without points take their neighbours' reach
        reach[k] = reach[k] if reach[k] > 0 else reach[k - 1]
    reach = np.convolve(np.pad(reach, 2, mode='edge'), np.ones(5) / 5, mode='valid')
    prof = np.array(json.load(open(os.path.join(W, 'bare_profile.json')))['half_width_m_by_z'])
    lo_fit, hi_fit = GNARL.get('fit', [0.55, 1.15])

    def xy_scale(z):
        k = min(max(int(z / band), 0), nb - 1)
        target = float(np.interp(z, prof[:, 0], prof[:, 1]))
        s_ = min(max(target / max(reach[k], 0.05), lo_fit), hi_fit) if GNARL.get('fit') else 1.0
        return 1.0 + (s_ - 1.0) * weight(z)

    grng = np.random.default_rng(GNARL.get('seed', 77))
    waves = [(Vector(grng.normal(0, 1, 3)).normalized() * (2 * math.pi / GNARL['wavelength'] * grng.uniform(0.7, 1.4)),
              grng.uniform(0, 2 * math.pi, 3)) for _ in range(3)]

    def displace(q):
        w = weight(q.z)
        if w <= 0:
            return q.copy()
        sc = xy_scale(q.z)
        out = Vector((q.x * sc, q.y * sc, q.z))
        d = Vector((0.0, 0.0, 0.0))
        for f, ph in waves:
            a = f.dot(q)
            d += Vector((math.sin(a + ph[0]), math.sin(a + ph[1]), 0.35 * math.sin(a + ph[2])))
        return out + d * (GNARL['amp'] * w / len(waves))

    for s in cu.splines:
        for p in s.bezier_points:
            co, hl, hr = p.co.copy(), p.handle_left.copy(), p.handle_right.copy()
            p.handle_left_type = p.handle_right_type = 'FREE'
            p.co = displace(co); p.handle_left = displace(hl); p.handle_right = displace(hr)
            p.radius *= 1.0 + (GNARL.get('thick', 1.0) - 1.0) * weight(co.z)
    print('BARE gnarl fork', round(fork, 2), 'amp', GNARL['amp'], 'thick', GNARL.get('thick', 1.0))


def thickness(s):
    return max(p.radius for p in s.bezier_points) * cu.bevel_depth


def bezier_length(s):
    pts = s.bezier_points
    return sum((pts[i + 1].co - pts[i].co).length for i in range(len(pts) - 1))


SPLINES = list(cu.splines)
THICK = [thickness(s) for s in SPLINES]


def tube(s, lod):
    """One spline bevelled as in build_tree.py branch_mesh (same sides, ring spacing and bark UVs)."""
    thick = thickness(s)
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
    c.resolution_u = max(1, round(c.resolution_u * 6 / SAPLING['curveRes'][0]))
    o = bpy.data.objects.new('b', c); bpy.context.scene.collection.objects.link(o)
    me = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(o, do_unlink=True); bpy.data.curves.remove(c)
    around = max(1, round(2 * math.pi * thick * 0.8 / TILE)); along = max(bezier_length(s) / TILE, 0.3)
    uv = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    lo, hi = uv.min(0), uv.max(0); span = np.maximum(hi - lo, 1e-6)
    # Blender's curve UVs run u along the curve and v around the bevel: swap them, so the bark's u goes around
    # (`around` tiles) and v along (`along` tiles). Until 2026-10-16 they were scaled the other way (bark stretched
    # along every branch); installed models were fixed in place by mm6_new_sorpigal_3d/trees/scripts/fix_bark_uv.py.
    uv = ((uv - lo) / span)[:, ::-1] * np.array([around, along]); me.uv_layers[0].data.foreach_set('uv', uv.ravel())
    return me


def add_roots(bm, lod):
    """build_tree.py's root spurs, unchanged (the family shares its LOD0 lower bound)."""
    base = [v.co for v in bm.verts if v.co.z < 0.25]
    trunk = max((Vector((c.x, c.y)).length for c in base), default=0.25)
    uv = bm.loops.layers.uv.active
    sides, rings = (5, 4) if lod == 0 else (4, 3) if lod == 1 else (4, 2)
    ROOTS = BARK['roots']
    for k in range(ROOTS):
        a = 2 * math.pi * k / ROOTS + 0.35 * math.sin(3.1 * k)
        d = Vector((math.cos(a), math.sin(a), 0.0))
        side = d.cross(Vector((0, 0, 1)))
        reach = trunk + BARK['root_reach'] + 0.12 * math.sin(1.7 * k + 0.5)
        loops = []
        rise = BARK['root_rise'] if 'root_rise' in BARK else 0.38
        for i in range(rings):
            t = i / (rings - 1)
            centre = d * (trunk * 0.45 + (reach - trunk * 0.45) * t) + Vector((0, 0, rise * (1 - t) ** 1.6 - 0.03 * t))
            radius = (0.16 * (1 - t) + 0.025 * t) * (trunk / 0.25) ** 0.5
            if 'root_radius' in BARK:
                radius *= BARK['root_radius']
            axis_up = Vector((0, 0, 1)).lerp(d, 0.35).normalized()
            loops.append([bm.verts.new(centre + (side * math.cos(2 * math.pi * j / sides)
                                                 + axis_up * math.sin(2 * math.pi * j / sides)) * radius)
                          for j in range(sides)])
        length = (reach - trunk * 0.45) + rise
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


def leader(bm, start, direction, radius, lod):
    """Thin tapered tube from the highest branch tip up to exactly TOP (its tip vertex)."""
    uv = bm.loops.layers.uv.active
    end = Vector((start.x + direction.x * 0.25 * (TOP - start.z), start.y + direction.y * 0.25 * (TOP - start.z), TOP))
    sides, segments = (5, 3) if lod == 0 else (4, 2)
    rings = []
    for i in range(segments):
        t = i / segments
        c = start.lerp(end, t)
        axis = (end - start).normalized()
        side = axis.cross(Vector((1, 0, 0))).normalized(); other = axis.cross(side)
        r = radius * (1 - t) + 0.004 * t
        rings.append([bm.verts.new(c + (side * math.cos(2 * math.pi * j / sides)
                                        + other * math.sin(2 * math.pi * j / sides)) * r) for j in range(sides)])
    tip = bm.verts.new(end)
    length = (end - start).length
    for i in range(segments - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            f = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j])); f.smooth = True
            for loop, (u, v) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                loop[uv].uv = (u / sides * 0.3, v / segments * length / TILE)
    for j in range(sides):
        f = bm.faces.new((rings[-1][j], rings[-1][(j + 1) % sides], tip)); f.smooth = True


# ---------------------------------------------------------------- tubes per LOD (budget by raising the minimum)
tube_cache = {}


def tube_tris(i, lod):
    if (i, lod) not in tube_cache:
        me = tube(SPLINES[i], lod)
        tube_cache[(i, lod)] = me
    me = tube_cache[(i, lod)]
    return sum(len(p.vertices) - 2 for p in me.polygons)


ROOT_TRIS = {0: BARK['roots'] * (5 * 3 * 2 + 5), 1: BARK['roots'] * (4 * 2 * 2 + 4), 2: BARK['roots'] * (4 * 2 + 4)}
tube_sets = {}
for lod in LODS:
    minimum = BARE['min_thickness'][lod]
    while True:
        chosen = [i for i, t in enumerate(THICK) if t >= minimum]
        if lod == 2:
            chosen = sorted(set(chosen) | {LEADER})            # the leader's branch stays at every level
        tris = sum(tube_tris(i, lod) for i in chosen) + ROOT_TRIS[lod]
        if tris <= BARE['budget'][lod]:
            break
        minimum *= 1.12
    tube_sets[lod] = chosen
    if lod == 1:
        # the leader grows from the highest branch end that LOD1 keeps (LOD2 keeps that branch too)
        LEADER = max(chosen, key=lambda i: SPLINES[i].bezier_points[-1].co.z)
    print('BARE tubes lod', lod, 'splines', len(chosen), 'of', len(SPLINES), 'min', round(minimum, 4), 'tris', tris)

# ---------------------------------------------------------------- twig cards
CHORD = 0.7          # the atlas twig spans ~70 % of its cell from the bottom-centre origin


def card_corners(base, direction, length, width, roll):
    d = direction.normalized()
    side = d.orthogonal().normalized()
    side = Matrix.Rotation(roll, 3, d) @ side
    return [base - side * width / 2, base + side * width / 2, base + side * width / 2 + d * length,
            base - side * width / 2 + d * length]


def end_tangent(s):
    pts = s.bezier_points
    return (pts[-1].co - pts[-2].co).normalized() if len(pts) > 1 else Vector((0, 0, 1))


chord_cards, tip_cards = [], []       # (base, direction, length, width, roll, cell, spline index, importance)
DROP = BARE.get('drop_below', 0.0)    # splines thinner than this get neither a tube nor a card
for i, s in enumerate(SPLINES):
    if THICK[i] < DROP:
        continue
    a, b = s.bezier_points[0].co.copy(), s.bezier_points[-1].co.copy()
    chord = (b - a).length
    if chord < 0.05:
        continue
    imp = chord * THICK[i]
    chord_cards.append((a, (b - a).normalized(), chord / CHORD, chord / CHORD * BARE.get('card_width', 0.8),
                        rng.uniform(0, math.pi), int(rng.integers(4)), i, imp))
    if THICK[i] < BARE['tip_max_thickness']:
        size = BARE['tip_card'] * rng.uniform(0.8, 1.2)
        for k in range(BARE.get('tip_cards', 1)):
            d = (end_tangent(s) + Vector(rng.normal(0, 0.25, 3))).normalized()
            tip_cards.append((b - end_tangent(s) * size * 0.15, d, size, size * BARE.get('card_width', 0.8),
                              rng.uniform(0, math.pi), int(rng.integers(4)), i, imp * 0.5))


def clamp_top(card):
    """Keep a card under the family top: shorten it about its base (drop it when the base is too high)."""
    base, d, length, width, roll, cell, i, imp = card
    corners = card_corners(base, d, length, width, roll)
    high = max(c.z for c in corners)
    limit = TOP - 0.02
    if high <= limit:
        return card
    if base.z >= limit - 0.05:
        return None
    s = (limit - base.z) / max(high - base.z, 1e-6)
    return (base, d, length * s, width * s, roll, cell, i, imp)


def cards_for(lod):
    """LOD0: chord cards for every spline that is not a tube, spray cards at thin tube ends. Coarser: chord cards for
    the splines that are not tubes at that level (the longest first, bare.card_keep of them) and fewer tip cards."""
    tubes = set(tube_sets[lod])
    keep, grow = BARE['card_keep'][lod], BARE['card_grow'][lod]
    pool = [c for c in chord_cards if c[6] not in tubes]
    pool.sort(key=lambda c: -c[7]); pool = pool[:int(math.ceil(len(pool) * keep))]
    tips = [c for c in tip_cards if c[6] in tubes]
    tips.sort(key=lambda c: -c[7]); tips = tips[:int(math.ceil(len(tips) * BARE['tip_keep'][lod]))]
    out = []
    for c in pool + tips:
        base, d, length, width, roll, cell, i, imp = c
        c = clamp_top((base, d, length * grow, width * grow, roll, cell, i, imp))
        if c:
            out.append(c)
    return out


# ---------------------------------------------------------------- meshes
def build_bark(lod):
    bm = bmesh.new()
    for i in tube_sets[lod]:
        bm.from_mesh(tube_cache[(i, lod)])
    add_roots(bm, lod)
    return bm


barks = {}
for lod in LODS:
    bm = build_bark(lod)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'bark{lod}'); bm.to_mesh(me); bm.free()
    barks[lod] = me

# the leader: from the highest tube tip (LOD0) to exactly TOP
cards0 = cards_for(0)
high_card = max((max(c.z for c in card_corners(*k[:5])) for k in cards0), default=0.0)
high_bark = max(v.co.z for v in barks[0].vertices)
ti = LEADER
s = SPLINES[ti]; P = s.bezier_points[-1].co.copy()
# start the leader a little back along the branch, inside its tube, so it grows from the tip without a seam
radius = max(s.bezier_points[-1].radius * cu.bevel_depth, BARE.get('leader_radius', 0.012))
if high_bark > TOP + 1e-4:
    raise SystemExit(f'BARE error: the skeleton ({high_bark:.3f} m) rises above the family top ({TOP:.3f} m); '
                     'lower the Sapling scale')
print('BARE top', round(TOP, 3), 'bark top', round(high_bark, 3), 'cards top', round(high_card, 3), 'leader from',
      round(P.z, 3), 'gap', round(TOP - P.z, 3))
for lod in LODS:
    bm = bmesh.new(); bm.from_mesh(barks[lod])
    if not bm.loops.layers.uv.active:
        bm.loops.layers.uv.new('UVMap')
    leader(bm, P - end_tangent(s) * 0.05, end_tangent(s), radius, lod)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(barks[lod]); bm.free()

# occlusion rays against the LOD0 wood
wood = bmesh.new(); wood.from_mesh(barks[0])
bvh = BVHTree.FromBMesh(wood)
dirs = rng.normal(0, 1, (1024, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
dirs = dirs[dirs[:, 2] > 0.05][:256]


def visibility(p, n):
    sel = rng.choice(len(dirs), 16, replace=False); hit = 0
    for d in dirs[sel]:
        d = Vector(d)
        if n is not None and d.dot(n) < -0.2:
            d = (d - n * 2 * d.dot(n)).normalized()
        loc, *_ = bvh.ray_cast(p + d * 0.03, d, 20.0)
        hit += loc is not None
    return 1 - hit / 16


FLOOR = BARE['occlusion_floor']


def ground(z):
    return 0.78 + 0.22 * min(z / 1.2, 1.0)


def set_colours(me, colours):
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.concatenate([np.append(c, 1.0) for c in colours]))
    me.color_attributes.active_color = attr


TONE = BARE['tone']
for lod in LODS:
    me = barks[lod]
    cols = []
    for v in me.vertices:
        o = (FLOOR + (1 - FLOOR) * visibility(v.co, v.normal)) * ground(v.co.z)
        cols.append(np.array([o, o, o]) * np.asarray(TONE[lod], float))
    set_colours(me, cols)
    for p in me.polygons:
        p.use_smooth = True


def twig_mesh(lod):
    cards = cards0 if lod == 0 else cards_for(lod)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for base, d, length, width, roll, cell, i, imp in cards:
        cs = card_corners(base, d, length, width, roll)
        f = bm.faces.new([bm.verts.new(q) for q in cs])
        row, col = divmod(cell, 2); u0, v0 = 0.5 * col, 0.5 * (1 - row)
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + 0.5 * du, v0 + 0.5 * dv)
        centre = sum(cs, Vector()) / 4
        o = (FLOOR + (1 - FLOOR) * visibility(centre, None)) * ground(centre.z) * BARE['twig_tone']
        out = Vector((centre.x, centre.y, 0)); out = out.normalized() if out.length > 1e-4 else Vector((1, 0, 0))
        n = (out * 0.6 + Vector((0, 0, 0.8))).normalized()
        for q in cs:
            normals.append(n); colours.append(np.array([o, o, o]) * np.asarray(TONE[lod], float))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'twigs{lod}'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    print('BARE twigs lod', lod, 'cards', len(cards), 'tris', len(me.polygons))
    return me


def material(name, base, normal, roughness, alpha=False, rough_map=None, normal_strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = bpy.data.images.load(os.path.join(W, base))
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(os.path.join(W, normal))
    tn.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nm.inputs['Strength'].default_value = normal_strength
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    if rough_map:
        tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = bpy.data.images.load(os.path.join(W, rough_map))
        tr.image.colorspace_settings.name = 'Non-Color'
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


bpy.data.objects.remove(skel, do_unlink=True)
bark_mat = material('Bark', 'bark_basecolor.png', 'bark_normal.png', 0.9, rough_map='bark_mr.png', normal_strength=1.6)
twig_mat = material('Twigs', 'twigs_basecolor.png', 'twigs_normal.png', 0.9, alpha=True)
bark_mat['openyamm_wind'] = 0.03
twig_mat['openyamm_wind'] = 0.03          # the same sway as the wood keeps every card on its branch
names = {0: 'Tree', 1: 'Tree_LOD1', 2: 'Tree_LOD2'}
for lod in LODS:
    b = bpy.data.objects.new(names[lod], barks[lod]); bpy.context.scene.collection.objects.link(b)
    t = bpy.data.objects.new(f't{lod}', twig_mesh(lod)); bpy.context.scene.collection.objects.link(t)
    b.data.materials.append(bark_mat); t.data.materials.append(twig_mat)
    for x in bpy.data.objects:
        x.select_set(x in (b, t))
    bpy.context.view_layer.objects.active = b
    bpy.ops.object.join()
    b.data.name = names[lod]
    zs = [v.co.z for v in b.data.vertices]
    print('LOD', lod, names[lod], 'tris', len(b.data.polygons), 'z', round(min(zs), 3), round(max(zs), 3))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'tree.blend'))
