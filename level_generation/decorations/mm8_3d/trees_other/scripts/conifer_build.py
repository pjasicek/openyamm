"""Conifer (kind 'conifer') for one species: work/<id>/tree.blend with Tree, Tree_LOD1, Tree_LOD2 (Bark + Leaves), each
mesh with a 'Color' point attribute (linear) = sky occlusion x local shade x species tint, exported as COLOR_0.

Construction (settings in species/<id>.json 'conifer'; envelope work/<id>/profile.json from prepare.py):
- Trunk: a tapered tube with a root flare from the ground to the leader, 8/6/5 sides by LOD.
- Whorls of branches from crown_low to the top, spacing shrinking toward the top; each branch leaves the trunk at an
  elevation angle and sags quadratically (droop), its tip lifting a little (tip_lift); its length is the sprite
  envelope's half-width at the tip's height (iterated), minus the trunk radius.
- Each branch carries two crossed spray cards along its curve (a frond cell of the shared needle atlas: stem at the
  card's centre line, base at the trunk), rolled +-roll degrees about the branch from the horizontal, so the crown has
  cover from every side; plus secondary sprays leaving the branch sideways and hanging down (smaller frond cards).
  The secondary count fills the LOD0 triangle budget, distributed by branch length squared.
- The leader: two crossed vertical frond cards at the top.
- Shading normals: outward from the trunk axis and up (a soft cone), so the crown lights as a mass.
- COLOR_0: sky visibility through the LOD0 cards (each hit blocks `coverage`), floor + range x vis^power, times a
  local term darker toward the trunk (inner sprays), times a per-branch value/hue jitter, times the species tint
  (common.tints). Bark gets the same rays.
- LOD1 / LOD2: main cards with fewer segments, secondary sprays kept by importance (length x visibility) within the
  budget, cards grown about their axis (lod.grow), tone per LOD (lod.tone).
Usage: blender --background --python conifer_build.py -- <id>"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

spec = common.load()
W = spec['work']
H = spec['height_m']
C = spec['conifer']
LOD = spec['lod']
BUDGET = LOD['triangles']
LEAF_TINT, BARK_TINT = common.tints(spec)
CELLS = spec['leaves']['cells']
OCC = spec['occlusion']
COVERAGE = C.get('coverage', 0.4)
rng = np.random.default_rng(spec['seed'])
profile = np.array(json.load(open(os.path.join(W, 'profile.json')))['half_width_by_height'])
# the sprite's outline is jagged (single sprays stick out): a running max over +-2 rows, then a light smoothing
_k = C.get('envelope_max', 5) // 2
_hw = profile[:, 1]
_mx = np.array([_hw[max(i - _k, 0):i + _k + 1].max() for i in range(len(_hw))])
profile[:, 1] = np.convolve(np.pad(_mx, 1, mode='edge'), np.ones(3) / 3, mode='valid')
print('TINT leaves', LEAF_TINT.round(3), 'bark', BARK_TINT.round(3))


SUN = spec['leaves'].get('sun')                    # sunlit leaves: value and saturation lift (where the sprite is brighter)


def sun(col, o):
    """col: linear COLOR_0 of a leaf vertex, o: its occlusion (0..1). Brightest vertices gain value and chroma."""
    if not SUN:
        return col
    t = min(max((o - SUN.get('lo', 0.45)) / max(SUN.get('hi', 0.85) - SUN.get('lo', 0.45), 1e-6), 0.0), 1.0)
    t = t * t * (3 - 2 * t)
    col = np.asarray(col, float) * (1 + SUN.get('value', 0.1) * t)
    grey = float(col @ np.array([0.2126, 0.7152, 0.0722]))
    return np.maximum(grey + (col - grey) * (1 + SUN.get('sat', 0.15) * t), 0.0)


def R(z):
    return float(np.interp(z / H, profile[:, 0], profile[:, 1])) * H


def lerp(a, b, t):
    return a + (b - a) * t


R0 = C['trunk_radius']
TOP = C.get('top', 0.985) * H


def trunk_radius(z):
    t = min(max(z / TOP, 0.0), 1.0)
    r = R0 * (1 - t) ** 0.85 + 0.02
    return r * (1 + C.get('flare', 0.6) * math.exp(-z / (0.06 * H)))


# ---------------------------------------------------------------- branches
branches = []          # dict: base, dir, L, elev, sag, lift, z0, t (height fraction)
z = C['crown_low'] * H
whorl = 0
while z < H * C.get('whorl_top', 0.93):
    t = (z - C['crown_low'] * H) / (H * C.get('whorl_top', 0.93) - C['crown_low'] * H)
    n = int(round(lerp(*C['branches_per_whorl'], t) + rng.uniform(-0.6, 0.6)))
    phase = whorl * 2.39996 + rng.uniform(-0.3, 0.3)
    for k in range(n):
        theta = phase + 2 * math.pi * k / n + rng.uniform(-0.25, 0.25)
        d = Vector((math.cos(theta), math.sin(theta), 0.0))
        z0 = z + rng.uniform(-0.3, 0.3) * lerp(*C['whorl_spacing'], t)
        elev = math.radians(lerp(*C['elevation'], t) + rng.uniform(-6, 6))
        sag = lerp(*C['droop'], t) * rng.uniform(0.75, 1.25)
        lift = C.get('tip_lift', 0.0) * rng.uniform(0.5, 1.5)
        L = max(R(z0) - trunk_radius(z0), 0.3)
        for _ in range(6):                               # the tip's height decides the envelope it must fill
            tip_z = z0 + L * (math.sin(elev) - sag + lift)
            L = max((R(max(tip_z, 0.0)) * C.get('reach', 1.0) * rng.uniform(0.86, 1.04) - trunk_radius(z0))
                    / max(math.cos(elev), 0.5), 0.3)
        base = d * trunk_radius(z0) * 0.6 + Vector((0, 0, z0))
        branches.append({'base': base, 'dir': d, 'L': L, 'elev': elev, 'sag': sag, 'lift': lift, 'z0': z0, 't': t,
                         'tint': np.array([rng.uniform(0.94, 1.06), 1.0, rng.uniform(0.9, 1.08)]) *
                         rng.uniform(0.9, 1.1)})
    z += lerp(*C['whorl_spacing'], t) * rng.uniform(0.85, 1.15)
    whorl += 1
print('BRANCHES', len(branches), 'whorls', whorl, 'longest', round(max(b['L'] for b in branches), 2))


def branch_point(b, u):
    L = b['L']; e = b['elev']
    horiz = L * u * math.cos(e)
    vert = L * (u * math.sin(e) - b['sag'] * u * u + b['lift'] * max(u - 0.7, 0) ** 2 / 0.09)
    return b['base'] + b['dir'] * horiz + Vector((0, 0, vert))


def branch_tangent(b, u):
    return (branch_point(b, min(u + 0.01, 1.2)) - branch_point(b, max(u - 0.01, 0.0))).normalized()


# ---------------------------------------------------------------- cards
# card: dict(path(u)->point callable via samples, roll, width, cell, branch index, u0, u1, kind)
cards = []
ASPECT = C.get('aspect', 0.5)
for bi, b in enumerate(branches):
    base_roll = rng.uniform(-0.3, 0.3)
    for s in (-1, 1):
        roll = base_roll + s * math.radians(C['roll'] + rng.uniform(-10, 10))
        pts = [branch_point(b, u) for u in np.linspace(0.0, 1.06, 13)]
        cards.append({'pts': pts, 'roll': roll, 'width': b['L'] * ASPECT * C.get('main_width', 1.0)
                      * rng.uniform(0.9, 1.1), 'cell': CELLS[int(rng.integers(len(CELLS)))], 'branch': bi,
                      'kind': 'main', 'u': np.linspace(0.0, 1.0, 13)})
main_count = len(cards)


def trunk_mesh(sides, ring_heights):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    rings = []
    for zr in ring_heights:
        r = trunk_radius(zr)
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / sides), r * math.sin(2 * math.pi * j / sides), zr))
                      for j in range(sides)])
    tile = spec['bark']['tile']
    around = max(1, round(2 * math.pi * R0 / tile))
    for i in range(len(rings) - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            f = bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
            f.smooth = True
            for loop, (uu, vv) in zip(f.loops, ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1))):
                loop[uvl].uv = (uu / sides * around, ring_heights[vv] / tile)
    tip = bm.verts.new((0, 0, H * 0.995))
    for j in range(sides):
        f = bm.faces.new((rings[-1][j], rings[-1][(j + 1) % sides], tip)); f.smooth = True
        for loop, (uu, vv) in zip(f.loops, ((j / sides * around, ring_heights[-1] / tile),
                                            ((j + 1) / sides * around, ring_heights[-1] / tile),
                                            ((j + 0.5) / sides * around, H / tile))):
            loop[uvl].uv = (uu, vv)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return bm


TRUNK_RINGS = {lod: [f * H for f in fr] for lod, fr in
               {0: [0.0, 0.01, 0.03, 0.065, 0.125, 0.21, 0.32, 0.44, 0.58, 0.73, 0.9],
                1: [0.0, 0.025, 0.1, 0.25, 0.46, 0.87],
                2: [0.0, 0.05, 0.25, 0.82]}.items()}
TRUNK_SIDES = {0: 8, 1: 6, 2: 5}
trunk_tris = {lod: len(trunk_mesh(TRUNK_SIDES[lod], [h for h in TRUNK_RINGS[lod] if h < TOP * 0.95]).faces)
              for lod in (0, 1, 2)}

# leader: two crossed vertical fronds at the top
leader_len = C.get('leader', 0.09) * H
for s in range(2):
    pts = [Vector((0, 0, H - leader_len * 1.15 + leader_len * 1.15 * u)) for u in np.linspace(0, 1, 13)]
    cards.append({'pts': pts, 'roll': s * math.pi / 2, 'width': leader_len * 0.55, 'cell': CELLS[s % len(CELLS)],
                  'branch': -1, 'kind': 'main', 'u': np.linspace(0, 1, 13), 'vertical': True})

SEG = {'main': C.get('seg_main', [3, 2, 1]), 'spray': C.get('seg_spray', [2, 1, 1])}
SHELL = C.get('shell')                  # {inset, dark, sides, rings}: opaque cone inside the needles
SHELL_SIDES = {0: 10, 1: 8, 2: 6}
SHELL_RINGS = {0: 8, 1: 5, 2: 3}
shell_tris = {lod: (SHELL_SIDES[lod] * 2 * (SHELL_RINGS[lod] - 1) + 2 * SHELL_SIDES[lod]) if SHELL else 0
              for lod in (0, 1, 2)}
main_tris0 = sum(2 * SEG['main'][0] for c in cards if c['kind'] == 'main')
spray_total = max((BUDGET[0] - trunk_tris[0] - main_tris0 - shell_tris[0] - 4) // (2 * SEG['spray'][0]), 0)
weights = np.array([b['L'] ** 2 for b in branches]); weights /= weights.sum()
alloc = np.floor(weights * spray_total + rng.uniform(0, 1, len(branches))).astype(int)
while alloc.sum() > spray_total:
    alloc[int(np.argmax(alloc))] -= 1
SPRAY = C.get('spray', {})
for bi, b in enumerate(branches):
    for j in range(alloc[bi]):
        u0 = rng.uniform(*SPRAY.get('u', [0.2, 0.85]))
        p0 = branch_point(b, u0); tng = branch_tangent(b, u0)
        side = 1 if j % 2 == 0 else -1
        yaw = side * math.radians(rng.uniform(*SPRAY.get('yaw', [35, 70])))
        d = Matrix.Rotation(yaw, 3, 'Z') @ tng
        pitch = math.radians(rng.uniform(*SPRAY.get('pitch', [10, 35])))
        horiz = Vector((d.x, d.y, 0)).normalized()
        d = (horiz * math.cos(pitch) + Vector((0, 0, -math.sin(pitch)))).normalized()
        length = b['L'] * rng.uniform(*SPRAY.get('length', [0.35, 0.55])) * (1 - 0.45 * u0) * SPRAY.get('scale', 1.0)
        sag = rng.uniform(0.1, 0.3)
        pts = [p0 + d * length * u + Vector((0, 0, -sag * length * u * u)) for u in np.linspace(0, 1, 13)]
        cards.append({'pts': pts, 'roll': rng.uniform(-1, 1) * math.radians(SPRAY.get('roll', 55)),
                      'width': length * ASPECT * rng.uniform(0.9, 1.1), 'cell': CELLS[int(rng.integers(len(CELLS)))],
                      'branch': bi, 'kind': 'spray', 'u': u0 + (1 - u0) * 0.5 * np.linspace(0, 1, 13)})
def shell_radius(z):
    return R(min(max(z, 0.0), H)) * SHELL['inset']


if SHELL:
    # sprays lying wholly inside the cone are never seen (the depth prepass rejects them): drop them
    before = len(cards)
    cards = [c for c in cards if c['kind'] != 'spray' or
             any(math.hypot(q.x, q.y) > shell_radius(q.z) * 0.98 or not (SHELL.get('z0', C['crown_low']) * H < q.z
                 < SHELL.get('z1', 0.95) * H) for q in c['pts'])]
    print('SHELL dropped hidden sprays', before - len(cards))
print('CARDS main', sum(c['kind'] == 'main' for c in cards), 'sprays', sum(c['kind'] == 'spray' for c in cards),
      'trunk tris', trunk_tris)


def card_frames(card, segments, grow=1.0):
    """Rows of (left, right, centre, v) along the card: the stem follows the sampled curve, the width axis is the
    curve's side vector rolled about the tangent."""
    pts = card['pts']; n = len(pts)
    idx = np.linspace(0, n - 1, segments + 1)
    # arc-length parameter for v
    seglen = [0.0] + [(pts[i + 1] - pts[i]).length for i in range(n - 1)]
    arc = np.cumsum(seglen); arc /= arc[-1]
    rows = []
    for f in idx:
        i0 = int(math.floor(f)); i1 = min(i0 + 1, n - 1); w = f - i0
        p = pts[i0].lerp(pts[i1], w)
        tg = (pts[min(i0 + 1, n - 1)] - pts[max(i0 - 1, 0)]).normalized()
        if card.get('vertical'):
            side = Vector((math.cos(card['roll']), math.sin(card['roll']), 0))
        else:
            side = tg.cross(Vector((0, 0, 1)))
            if side.length < 1e-4:
                side = Vector((1, 0, 0))
            side.normalize()
            side = Matrix.Rotation(card['roll'], 3, tg) @ side
        half = card['width'] * grow / 2
        v = arc[i0] + (arc[i1] - arc[i0]) * w
        # grow about the axis: lengthen beyond the tip a little too
        # nothing below the ground: the engine scales a model by its LOD0 bounds height (DecorationModelSet)
        floor = C.get('ground', 0.01) * H
        lift = lambda q: Vector((q.x, q.y, max(q.z, floor)))
        rows.append((lift(p - side * half), lift(p + side * half), lift(p), v,
                     card['u'][i0] + (card['u'][i1] - card['u'][i0]) * w))
    if grow != 1.0:                                        # extend the tip along the tangent
        tg = (pts[-1] - pts[-3]).normalized(); extra = (grow - 1.0) * 0.4 * (pts[-1] - pts[0]).length
        l, r, p, v, u = rows[-1]
        rows[-1] = (l + tg * extra, r + tg * extra, p + tg * extra, v, u)
    return rows


def crown_normal(q):
    radial = Vector((q.x, q.y, 0.0))
    radial = radial.normalized() if radial.length > 1e-4 else Vector((0, 0, 0))
    return (radial * 1.0 + Vector((0, 0, C.get('normal_up', 0.6)))).normalized()


# ---------------------------------------------------------------- occlusion BVH (LOD0 cards)
tv, ti = [], []
for card in cards:
    rows = card_frames(card, SEG[card['kind']][0])
    for a, b in zip(rows, rows[1:]):
        base = len(tv); tv += [tuple(a[0]), tuple(a[1]), tuple(b[1]), tuple(b[0])]
        ti += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
bvh = BVHTree.FromPolygons(tv, ti)
dirs = rng.normal(0, 1, (4096, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
dirs = dirs[dirs[:, 2] > 0.02][:1024]
RAYS = 32


def visibility(point, normal):
    hits = 0.0
    sel = rng.choice(len(dirs), RAYS, replace=False)
    for d in dirs[sel]:
        d = Vector(d)
        if d.dot(normal) < -0.2:                        # mostly the hemisphere around the shading normal
            d = (d - normal * 1.2 * d.dot(normal)).normalized() if d.z > 0 else d
        origin = point + d * 0.03; transmit = 1.0
        for _ in range(14):
            loc, _, _, _ = bvh.ray_cast(origin, d, 3 * H)
            if loc is None:
                break
            transmit *= 1.0 - COVERAGE
            if transmit < 0.04:
                break
            origin = loc + d * 0.01
        hits += transmit
    return hits / RAYS


def occ_value(vis):
    return OCC['floor'] + OCC['range'] * vis ** OCC['power']


CONE = C.get('cone_ao')                 # {floor, power, low}: needles deep in the cone and low on the tree darker


def cone_term(p):
    """Depth into the crown cone (radius from the trunk / envelope radius at that height) and height: the inner
    and lower cards darken, so the lit tier edges separate from the shadowed gaps between tiers (as on the sprite)."""
    if not CONE:
        return 1.0
    depth = min(math.hypot(p.x, p.y) / max(R(min(max(p.z, 0.0), H)), 0.3), 1.0)
    cone = CONE.get('floor', 0.45) + (1 - CONE.get('floor', 0.45)) * depth ** CONE.get('power', 1.5)
    low = CONE.get('low', 0.75) + (1 - CONE.get('low', 0.75)) * min(p.z / (0.5 * H), 1.0)
    return cone * low


def local_term(u):
    lo = C.get('inner_shade', 0.55)
    return lo + (1 - lo) * min(max(u, 0.0), 1.0) ** 0.7


# per card: occlusion at its LOD0 row centres (interpolated for the other levels)
card_vis = []
for ci, card in enumerate(cards):
    rows = card_frames(card, SEG[card['kind']][0])
    vals = [occ_value(visibility(r[2], crown_normal(r[2]))) for r in rows]
    card_vis.append((np.array([r[3] for r in rows]), np.array(vals)))
vis_mean = np.array([v[1].mean() for v in card_vis])
print('OCCLUSION card min/mean/max', round(float(vis_mean.min()), 3), round(float(vis_mean.mean()), 3),
      round(float(vis_mean.max()), 3))


def set_colours(me, colours):
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.concatenate([np.append(np.clip(c, 0, 1), 1.0) for c in colours]))
    me.color_attributes.active_color = attr


# ---------------------------------------------------------------- per-LOD selection
importance = np.array([((c['width'] * (c['pts'][-1] - c['pts'][0]).length) ** 0.5) * (0.4 + vis_mean[k])
                       for k, c in enumerate(cards)]) * rng.uniform(0.8, 1.2, len(cards))


def select(lod):
    mains = [k for k, c in enumerate(cards) if c['kind'] == 'main']
    tris = trunk_tris[lod] + shell_tris[lod] + sum(2 * SEG['main'][lod] for _ in mains)
    sprays = sorted([k for k, c in enumerate(cards) if c['kind'] == 'spray'], key=lambda k: -importance[k])
    keep = list(mains)
    if tris > BUDGET[lod]:                       # drop the weaker of each crossed pair on short branches
        pairs = sorted(mains, key=lambda k: importance[k])
        for k in pairs:
            if tris <= BUDGET[lod]:
                break
            if cards[k]['branch'] >= 0 and k % 2 == 1:
                keep.remove(k); tris -= 2 * SEG['main'][lod]
    for k in sprays:
        if tris + 2 * SEG['spray'][lod] > BUDGET[lod] - 2:
            break
        keep.append(k); tris += 2 * SEG['spray'][lod]
    return keep


def leaf_mesh(lod):
    keep = select(lod)
    grow_main, grow_spray = LOD['grow'][lod] if isinstance(LOD['grow'][lod], list) else [LOD['grow'][lod]] * 2
    tone = np.asarray(LOD['tone'][lod], float)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    meta = common.atlas(spec['atlas'])['cells']
    for k in keep:
        card = cards[k]
        rows = card_frames(card, SEG[card['kind']][lod], grow_main if card['kind'] == 'main' else grow_spray)
        u0, v0, du, dv = meta[card['cell']]['uv']
        vrow, vvals = card_vis[k]
        tint = LEAF_TINT * (branches[card['branch']]['tint'] if card['branch'] >= 0 else 1.0)
        verts = []
        for (l, r, p, v, u) in rows:
            o = max(float(np.interp(v, vrow, vvals)) * local_term(u) * cone_term(p),
                    spec['leaves'].get('floor', 0.0))       # no black needle cards
            col = sun(tint * o, float(np.interp(v, vrow, vvals))) * tone
            pair = [bm.verts.new(l), bm.verts.new(r)]
            verts.append((pair, v))
            for q in (l, r):
                normals.append(crown_normal(q)); colours.append(col)
        for (a, va), (b, vb) in zip(verts, verts[1:]):
            f = bm.faces.new((a[0], a[1], b[1], b[0]))
            for loop, (uu, vv) in zip(f.loops, ((0, va), (1, va), (1, vb), (0, vb))):
                loop[uvl].uv = (u0 + du * uu, v0 + dv * vv)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='FIXED')
    me = bpy.data.meshes.new(f'leaves{lod}'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'leaves{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('LEAVES lod', lod, 'cards', len(keep), 'tris', len(me.polygons))
    return obj


def bark_mesh(lod):
    bm = trunk_mesh(TRUNK_SIDES[lod], [h for h in TRUNK_RINGS[lod] if h < TOP * 0.95])
    me = bpy.data.meshes.new(f'bark{lod}'); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(f'bark{lod}', me); bpy.context.scene.collection.objects.link(obj)
    colours = []
    floor = spec['bark']['occlusion_floor']
    for v in me.vertices:
        n = Vector((v.co.x, v.co.y, 0.3)).normalized()
        o = floor + (1 - floor) * visibility(v.co, n)
        colours.append(BARK_TINT * o)
    set_colours(me, colours)
    print('BARK lod', lod, 'tris', len(me.polygons))
    return obj


def shell_mesh(lod):
    """Opaque cone inside the needles: rings from SHELL.z0 to z1 of the height at SHELL.inset of the smoothed
    envelope radius, closed by an apex and a bottom cap; dark blue-green (needle colour x SHELL.dark x sky
    visibility); normals outward and a little up."""
    sides, rings = SHELL_SIDES[lod], SHELL_RINGS[lod]
    z0 = SHELL.get('z0', C['crown_low']) * H; z1 = SHELL.get('z1', 0.95) * H
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours, uv_of = [], [], {}
    # the middle of a dense needle-pad cell (the frond cells' lower part is the dark stem and its dilated surround)
    u0, v0, su, sv = common.cell_uv(spec, SHELL.get('cell', 4))
    u0 += 0.25 * su; v0 += 0.25 * sv; su *= 0.5; sv *= 0.5

    def vert(q, n, uv):
        # shading normal = the cards' crown normal (outward and up): the core lights like the needles around it,
        # its underside and bottom cap never turn black away from the sun
        v = bm.verts.new(q); normals.append(crown_normal(q)); uv_of[v] = uv
        # needle texture x the needles' tint: deeper fir foliage, a little darker than the cards
        vis = visibility(q + n.normalized() * 0.03, n.normalized())
        colours.append(LEAF_TINT * SHELL.get('dark', 0.6) * (0.6 + 0.4 * vis))
        return v
    ring_v = []
    for k in range(rings):
        z = z0 + (z1 - z0) * (k / (rings - 1)) ** 0.9
        r = max(shell_radius(z), 0.05)
        ring_v.append([vert(Vector((r * math.cos(2 * math.pi * j / sides), r * math.sin(2 * math.pi * j / sides), z)),
                            Vector((math.cos(2 * math.pi * j / sides), math.sin(2 * math.pi * j / sides), 0.5)),
                            (u0 + su * (0.15 + 0.7 * j / sides), v0 + sv * (0.1 + 0.8 * k / (rings - 1))))
                       for j in range(sides)])
    for k in range(rings - 1):
        for j in range(sides):
            j2 = (j + 1) % sides
            bm.faces.new((ring_v[k][j], ring_v[k][j2], ring_v[k + 1][j2], ring_v[k + 1][j]))
    apex = vert(Vector((0, 0, z1 + 0.04 * H)), Vector((0, 0, 1)), (u0 + su * 0.5, v0 + sv * 0.92))
    for j in range(sides):
        bm.faces.new((ring_v[-1][j], ring_v[-1][(j + 1) % sides], apex))
    bottom = vert(Vector((0, 0, z0 - 0.01 * H)), Vector((0, 0, -1)), (u0 + su * 0.5, v0 + sv * 0.5))
    for j in range(sides):
        bm.faces.new((ring_v[0][(j + 1) % sides], ring_v[0][j], bottom))
    for f in bm.faces:
        for loop in f.loops:
            loop[uvl].uv = uv_of[loop.vert]
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.normal_update()
    for f in bm.faces:                                   # outward winding (back faces are culled)
        c = f.calc_center_median()
        if Vector((c.x, c.y, 0.0)).dot(f.normal) < 0 and abs(f.normal.z) < 0.9:
            f.normal_flip()
    me = bpy.data.meshes.new(f'shell{lod}'); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'shell{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('SHELL lod', lod, 'tris', len(me.polygons))
    return obj


def material(name, base, normal, roughness, alpha=False, rough_map=None, normal_strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = bpy.data.images.load(common.shared_path(base), check_existing=True)
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(common.shared_path(normal), check_existing=True)
    tn.image.colorspace_settings.name = 'Non-Color'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nm.inputs['Strength'].default_value = normal_strength
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    if rough_map:
        tr = nt.nodes.new('ShaderNodeTexImage'); tr.image = bpy.data.images.load(common.shared_path(rough_map), check_existing=True)
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


for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bark_mat = material('Bark', 'bark_basecolor.png', 'bark_normal.png', 0.9, rough_map='bark_mr.png', normal_strength=1.6)
leaf_mat = material('Leaves', f"{spec['atlas']}_basecolor.png", f"{spec['atlas']}_normal.png", 0.85, alpha=True)
bark_mat['openyamm_wind'] = spec['wind']['bark']
if SHELL:
    # white 8x8 base colour and a flat normal map (shared, byte-identical): the colour is all COLOR_0, and every
    # pipeline step (impostor bake, LOD2 clump renders, review) treats the shell like any other material
    shell_mat = material('Shell', f"{spec['atlas']}_shell.png", 'shell_normal.png', 0.9)     # flat normals: atlas normals in its dilated texels shade the core black
    shell_mat['openyamm_wind'] = spec['wind']['leaves']
    shell_mat['openyamm_specular'] = 0.05
leaf_mat['openyamm_wind'] = spec['wind']['leaves']
leaf_mat['openyamm_translucency'] = spec['translucency']
names = {0: 'Tree', 1: 'Tree_LOD1', 2: 'Tree_LOD2'}
for lod in (0, 1, 2):
    b = bark_mesh(lod); l = leaf_mesh(lod)
    b.data.materials.append(bark_mat); l.data.materials.append(leaf_mat)
    parts = [b, l]
    if SHELL:
        sh = shell_mesh(lod); sh.data.materials.append(shell_mat); parts.append(sh)
    for x in bpy.data.objects:
        x.select_set(x in parts)
    bpy.context.view_layer.objects.active = b
    bpy.ops.object.join()
    b.name = names[lod]; b.data.name = names[lod]
    print('LOD', lod, names[lod], 'tris', len(b.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'tree.blend'))
