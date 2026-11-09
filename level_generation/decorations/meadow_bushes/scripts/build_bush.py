"""Build one meadow bush (settings in bushes.py) -> work/<id>.blend and work/<id>_export.glb with objects <id>,
<id>_LOD1 and <id>_LOD2, each one mesh with two materials: Bark (stems, opaque) and Leaves (alpha-cut cards).

- Stems: tapered tubes (4-5 sides, parallel-transport rings), u around the stem and v along it, both in units of the
  bark tile (bushes.TILE), so the bark grain runs along the stem. Shading normals are radial (no seam shading).
- Leaf clumps: 'mound' bushes spread clumps over an ellipsoid envelope (a few inside it); a 'sapling' grows three
  leaning stems with side branches and puts clumps at their tips and along their upper part; bush04's arching canes
  carry clumps too. Cards fill each clump densest near its surface, facing outward with a random tilt plus card_up;
  the top clumps face the sky, so the bush covers its top in flying views.
- Shading normals: 60 % from the clump centre, 40 % from the bush centre (one soft mass rather than flat cards).
- COLOR_0 ('Color', linear) = occlusion: sky rays through the LOD0 cards (each card hit passes 45 %), a clump-local
  term (lit tops, shaded undersides), darkening toward the ground and a small per-clump tint. Stems get the rays too.
- LOD1 / LOD2: the most sky-visible cards of every clump (farthest-point spread), grown about their centres, toned so
  the bush's mean colour matches LOD0; LOD1 stems with fewer rings, LOD2 keeps only the visible sapling trunks.
- The whole bush is scaled so LOD0's top is exactly the target height.
Usage: blender --background --python build_bush.py -- <id>"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'scripts'))
from bushes import BUSHES, TILE   # noqa: E402

BID = sys.argv[sys.argv.index('--') + 1]
S = BUSHES[BID]
H = S['height']
WORK = os.path.join(HERE, 'work')
TEX = os.path.join(HERE, 'textures')
rng = np.random.default_rng(S['seed'])
UP = Vector((0, 0, 1))
TONE = S.get('tone', [1.0, 0.94, 0.9])

bpy.ops.wm.read_factory_settings(use_empty=True)


def rand_unit(min_z=-1.0):
    while True:
        d = Vector(rng.normal(0, 1, 3))
        if d.length > 1e-6:
            d.normalize()
            if d.z >= min_z:
                return d


# ---------------------------------------------------------------- stems (centre-lines; meshed per LOD)
stems = []          # dict(points, radii, sides, lods: {lod: (sides, ring_step)}, tip)


def bezier(p0, p1, p2, n):
    return [p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t for t in np.linspace(0, 1, n + 1)]


clumps = []         # (centre, radius, inner, cell weights)
CELLS = S['cells']

if S['kind'] == 'mound':
    rx, ry, rz, cz = S['envelope']
    C = Vector((0, 0, cz))

    def envelope_distance(d):
        return 1.0 / math.sqrt((d.x / rx) ** 2 + (d.y / ry) ** 2 + (d.z / rz) ** 2)

    tries = 0
    while len(clumps) < S['clumps'] and tries < 20000:
        tries += 1
        d = rand_unit(S.get('under', -0.45))
        r = float(rng.uniform(*S['clump_radius']))
        c = C + d * (envelope_distance(d) - 0.55 * r) * float(rng.uniform(0.9, 1.04))
        c.z = max(c.z, 0.8 * r)
        if all((c - o[0]).length > 0.78 * (r + o[1]) for o in clumps):
            clumps.append((c, r, False))
    for _ in range(S.get('inner_clumps', 0)):
        c = C + Vector((rng.uniform(-0.4, 0.4) * rx, rng.uniform(-0.4, 0.4) * ry, rng.uniform(-0.25, 0.3) * rz))
        clumps.append((c, float(rng.uniform(*S['clump_radius'])), True))
    st = S['stems']
    targets = sorted(clumps, key=lambda o: abs(o[0].z - cz))[:st['count'] * 2]
    for k in range(st['count']):
        a = 2 * math.pi * k / st['count'] + rng.uniform(-0.4, 0.4)
        base = Vector((math.cos(a), math.sin(a), 0)) * st['spread'] * rng.uniform(0.3, 1.0) + Vector((0, 0, -0.03))
        tgt = targets[k % len(targets)][0]
        tip = base.lerp(tgt, 0.85)
        mid = (base + tip) / 2 + Vector((0, 0, 0.12 * H)) - Vector((tip.x, tip.y, 0)) * 0.25
        pts = bezier(base, mid, tip, st['segments'])
        r0 = st['radius'] * rng.uniform(0.85, 1.15)
        stems.append({'points': pts, 'radii': [r0 * (1 - 0.6 * i / st['segments']) for i in range(len(pts))],
                      'lods': {0: (st['sides'], 1), 1: (4, max(st['segments'] - 1, 1))}, 'tip': False})
    for k in range(S.get('canes', {}).get('count', 0)):
        cn = S['canes']
        a = 2 * math.pi * (k + 0.5) / cn['count'] + rng.uniform(-0.35, 0.35)
        d = Vector((math.cos(a), math.sin(a), 0))
        reach = rng.uniform(*cn['reach']); rise = rng.uniform(*cn['rise']) * H
        p0 = d * 0.05; p1 = d * reach * 0.45 + Vector((0, 0, rise * 1.35)); p2 = d * reach + Vector((0, 0, 0.3 * H))
        pts = bezier(p0, p1, p2, 5)
        stems.append({'points': pts, 'radii': [cn['radius'] * (1 - 0.65 * i / 5) for i in range(6)],
                      'lods': {0: (4, 1), 1: (4, 2)}, 'tip': True})
        for t in (0.6, 0.97)[:cn['clumps']]:
            c = p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t
            clumps.append((c + Vector((0, 0, 0.04)), float(rng.uniform(0.18, 0.22)), False))
    CROWN_C = C
    CROWN_Z = 1.15
else:
    # sapling: leaning trunks from one root, side branches; clumps on the tips and along the upper trunks
    n = S['trunks']
    az0 = rng.uniform(0, 2 * math.pi)
    for k in range(n):
        az = az0 + 2 * math.pi * k / n + rng.uniform(-0.3, 0.3)
        lean = math.radians(rng.uniform(*S['lean']) * (0.6 if k == 0 else 1.0))
        d = Vector((math.cos(az) * math.sin(lean), math.sin(az) * math.sin(lean), math.cos(lean)))
        L = H * (0.86 if k == 0 else rng.uniform(0.66, 0.8))
        base = Vector((math.cos(az), math.sin(az), 0)) * 0.03 + Vector((0, 0, -0.03))
        side = d.cross(UP).normalized() if abs(d.z) < 0.999 else Vector((1, 0, 0))
        bend = rng.uniform(-0.05, 0.05)
        pts = [base + d * L * t + side * bend * math.sin(math.pi * t) for t in np.linspace(0, 1, 7)]
        r0 = S['trunk_radius'] * (1.0 if k == 0 else 0.8)
        stems.append({'points': pts, 'radii': [r0 * (1 - 0.75 * i / 6) for i in range(7)],
                      'lods': {0: (5, 1), 1: (4, 2), 2: (4, 3)}, 'tip': True})
        top = pts[-1]
        clumps.append((top + d * 0.06, float(rng.uniform(0.19, 0.23)), False))
        for t in rng.uniform(0.6, 0.85, 1):                       # a clump hugging the upper trunk
            p = base + d * L * t
            off = Vector((math.cos(az + rng.uniform(-1.5, 1.5)), math.sin(az + rng.uniform(-1.5, 1.5)), 0)) * 0.1
            clumps.append((p + off, float(rng.uniform(0.17, 0.21)), False))
        for b in range(int(rng.integers(S['branches'][0], S['branches'][1] + 1))):
            t = rng.uniform(0.42, 0.8)
            p = base + d * L * t + side * bend * math.sin(math.pi * t)
            baz = az + rng.uniform(-1.3, 1.3)
            el = math.radians(rng.uniform(30, 55))
            bd = Vector((math.cos(baz) * math.cos(el), math.sin(baz) * math.cos(el), math.sin(el)))
            bl = rng.uniform(*S.get('branch_length', [0.28, 0.45])) * (1.1 - 0.4 * t)
            bpts = [p + bd * bl * s + Vector((0, 0, -0.04 * math.sin(math.pi * s))) for s in np.linspace(0, 1, 3)]
            stems.append({'points': bpts, 'radii': [0.011, 0.007, 0.004], 'lods': {0: (4, 1)}, 'tip': True})
            clumps.append((bpts[-1] + bd * 0.05, float(rng.uniform(*S['clump_radius'])), False))
    CROWN_C = Vector((0, 0, 0.72 * H))
    CROWN_Z = 1.3


def crown_normal(p):
    o = p - CROWN_C
    o.z *= CROWN_Z
    return o.normalized() if o.length > 1e-6 else UP.copy()


# ---------------------------------------------------------------- cards
cards = []          # centre, normal, roll, size, cell, clump index
area = np.array([o[1] ** 2 * (0.5 if o[2] else 1.0) for o in clumps])
per = np.maximum(np.round(area / area.sum() * S['cards']).astype(int), 3)
cells, weights = list(CELLS.keys()), np.array(list(CELLS.values()), float)
weights /= weights.sum()
for ci, (c, r, inner) in enumerate(clumps):
    for _ in range(int(per[ci])):
        for _attempt in range(8):
            u = rand_unit()
            if u.dot(crown_normal(c)) > -0.3 or rng.random() > 0.75:     # fewer cards on the bush-facing side
                break
        q = c + u * r * float(0.35 + 0.65 * math.sqrt(rng.random()))
        n = (u + Vector(rng.normal(0, 0.35, 3))).normalized()
        n = (n + UP * S['card_up']).normalized()
        size = float(rng.uniform(*S['card']))
        q.z = max(q.z, 0.3 * size)
        cards.append((q, n, float(rng.uniform(0, 2 * math.pi)), size, int(rng.choice(cells, p=weights)), ci))


def card_corners(card, grow=1.0):
    p, n, roll, size, _, _ = card
    s = size * grow
    t = n.orthogonal().normalized(); b = n.cross(t)
    rot = Matrix.Rotation(roll, 3, n); t = rot @ t; b = rot @ b
    cs = [p + (-t - b) * s / 2, p + (t - b) * s / 2, p + (t + b) * s / 2, p + (-t + b) * s / 2]
    low = min(q.z for q in cs)
    if low < 0.01:                                  # never into the ground
        cs = [q + Vector((0, 0, 0.01 - low)) for q in cs]
    return cs


def shading_normal(q, ci):
    c = clumps[ci][0]
    return (0.6 * (q - c).normalized() + 0.4 * crown_normal(q)).normalized()


# ---------------------------------------------------------------- occlusion
tris_v, tris_i = [], []
for card in cards:
    cs = card_corners(card); base = len(tris_v)
    tris_v += [tuple(q) for q in cs]; tris_i += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
bvh = BVHTree.FromPolygons(tris_v, tris_i)
dirs = rng.normal(0, 1, (4096, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
dirs = dirs[dirs[:, 2] > 0.05][:1024]
RAYS = 48
PASS = 0.45


def visibility(point, normal, skip=None):
    total = 0.0; weight = 0.0
    for d in dirs[rng.choice(len(dirs), RAYS, replace=False)]:
        d = Vector(d)
        w = 0.35 + 0.65 * max(d.dot(normal), 0.0)              # softly cosine-weighted toward the shading normal
        origin = point + d * 0.01
        transmit = 1.0
        for _ in range(16):
            loc, _, index, _ = bvh.ray_cast(origin, d, 4.0)
            if loc is None:
                break
            if skip is None or index // 2 != skip:
                transmit *= PASS
                if transmit < 0.03:
                    break
            origin = loc + d * 0.005
        total += w * transmit; weight += w
    return total / weight


def ground(z):
    t = min(max(z / (0.45 * H), 0.0), 1.0)
    return 0.72 + 0.28 * t * t * (3 - 2 * t)


def local(q, ci):
    c, r, _ = clumps[ci]
    return (0.55 + 0.45 * (0.5 + 0.5 * (q - c).normalized().z)) * (0.7 + 0.3 * min((q - c).length / r, 1.0))


tint = [np.array([rng.uniform(0.94, 1.06), 1.0, rng.uniform(0.92, 1.06)]) * rng.uniform(0.93, 1.07) for _ in clumps]
card_occ, card_rank = [], []
for k, card in enumerate(cards):
    ci = card[5]
    cs = card_corners(card)
    vis = [visibility(q, shading_normal(q, ci), skip=k) for q in cs]
    occ = [(0.3 + 0.7 * v ** 1.1) * local(q, ci) * ground(q.z) for v, q in zip(vis, cs)]
    m = sum(occ) / 4
    card_occ.append([tint[ci] * (0.7 * o + 0.3 * m) for o in occ])
    card_rank.append(sum(vis) / 4)
card_rank = np.array(card_rank)
print('OCCLUSION cards', len(cards), 'vis min/mean/max', round(float(card_rank.min()), 2),
      round(float(card_rank.mean()), 2), round(float(card_rank.max()), 2))


def subset(lod):
    if lod == 0:
        return list(range(len(cards)))
    keep = S['keep'][lod]
    picked = []
    for ci in range(len(clumps)):
        members = [k for k, c in enumerate(cards) if c[5] == ci]
        n = max(1, int(round(len(members) * keep)))
        pool = sorted(members, key=lambda k: -card_rank[k])[:max(n, int(len(members) * min(1.0, keep * 1.8)))]
        pts = np.array([tuple(cards[k][0]) for k in pool]); sel = [0]
        dist = np.linalg.norm(pts - pts[0], axis=1)
        for _ in range(min(n, len(pool)) - 1):
            j = int(dist.argmax()); sel.append(j); dist = np.minimum(dist, np.linalg.norm(pts - pts[j], axis=1))
        picked += [pool[j] for j in sel]
    return picked


# ---------------------------------------------------------------- meshes
def set_colours(me, colours):
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.concatenate([np.append(c, 1.0) for c in colours]).astype(np.float32))
    me.color_attributes.active_color = attr


def tube(bm, uvl, pts, radii, sides, tip, vnormals):
    """Rings along pts (parallel transport), quads between them, an apex at the end when tip is set. vnormals gets
    each new vertex's shading normal, in creation (index) order."""
    tangents = []
    for i in range(len(pts)):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tangents.append((b - a).normalized())
    ref = tangents[0].orthogonal().normalized()
    frames = []
    for t in tangents:
        ref = (ref - t * ref.dot(t)).normalized()
        frames.append((ref.copy(), t.cross(ref).normalized()))
    circumference = 2 * math.pi * max(radii[0], 0.006)
    rings, v_along = [], 0.0
    last = len(pts) - 1 if tip else len(pts)
    for i in range(last):
        if i:
            v_along += (pts[i] - pts[i - 1]).length
        x, y = frames[i]
        ring = []
        for j in range(sides + 1):
            a = 2 * math.pi * j / sides
            radial = x * math.cos(a) + y * math.sin(a)
            v = bm.verts.new(pts[i] + radial * radii[i]); vnormals.append(radial)
            ring.append((v, radial, (circumference * j / sides / TILE, v_along / TILE)))
        rings.append(ring)
    faces = []
    for i in range(len(rings) - 1):
        for j in range(sides):
            quad = [rings[i][j], rings[i][j + 1], rings[i + 1][j + 1], rings[i + 1][j]]
            f = bm.faces.new([q[0] for q in quad])
            faces.append((f, quad))
    if tip:
        v_end = v_along + (pts[-1] - pts[-2]).length
        apex = bm.verts.new(pts[-1]); vnormals.append(tangents[-1])
        for j in range(sides):
            a, b = rings[-1][j], rings[-1][j + 1]
            tri = [a, b, (apex, tangents[-1], ((a[2][0] + b[2][0]) / 2, v_end / TILE))]
            f = bm.faces.new([q[0] for q in tri])
            faces.append((f, tri))
    for f, items in faces:
        for loop, item in zip(f.loops, items):
            loop[uvl].uv = item[2]
    return faces


def bark_mesh(lod):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    vnormals = []
    count = 0
    for s in stems:
        if lod not in s['lods']:
            continue
        sides, step = s['lods'][lod]
        idx = list(range(0, len(s['points']), step))
        if idx[-1] != len(s['points']) - 1:
            idx.append(len(s['points']) - 1)
        pts = [s['points'][i] for i in idx]; radii = [s['radii'][i] for i in idx]
        tube(bm, uvl, pts, radii, sides, s['tip'], vnormals)
        count += 1
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='SHORT_EDGE')
    me = bpy.data.meshes.new(f'bark{lod}')
    bm.to_mesh(me); bm.free()
    assert len(me.vertices) == len(vnormals)
    normals = [n.normalized() for n in vnormals]
    colours = []
    for v, n in zip(me.vertices, normals):
        o = 0.45 + 0.55 * visibility(v.co, n)
        colours.append(np.array([o, o, o]) * ground(v.co.z))
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'bark{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('BARK lod', lod, 'stems', count, 'tris', len(me.polygons))
    return obj


def leaf_mesh(lod):
    sel = subset(lod)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for k in sel:
        card = cards[k]; ci = card[5]
        cs = card_corners(card, S['grow'][lod])
        f = bm.faces.new([bm.verts.new(q) for q in cs])
        row, col = divmod(card[4], 2)
        u0, v0 = 0.5 * col, 0.5 * (1 - row)
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + 0.5 * du, v0 + 0.5 * dv)
        for q, occ in zip(cs, card_occ[k]):
            normals.append(shading_normal(q, ci)); colours.append(occ * TONE[lod])
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='FIXED')
    me = bpy.data.meshes.new(f'leaves{lod}'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'leaves{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('LEAVES lod', lod, 'cards', len(sel), 'tris', len(me.polygons))
    return obj


def image(name, colorspace):
    img = bpy.data.images.load(os.path.join(TEX, name))
    img.colorspace_settings.name = colorspace
    return img


def material(name, base, normal, roughness, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = image(base, 'sRGB')
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(normal, 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    if alpha:
        m.use_backface_culling = False
        m.surface_render_method = 'DITHERED'
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tb.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
    else:
        m.use_backface_culling = True
    return m


bark_mat = material('Bark', 'bark_basecolor.png', 'bark_normal.png', 0.9)
leaf_mat = material('Leaves', 'leaves_basecolor.png', 'leaves_normal.png', 0.85, alpha=True)
bark_mat['openyamm_wind'] = round(S['wind'] * 0.25, 4)
bark_mat['openyamm_specular'] = 0.1
leaf_mat['openyamm_wind'] = S['wind']
leaf_mat['openyamm_translucency'] = 0.35
leaf_mat['openyamm_specular'] = 0.1

names = {0: BID, 1: f'{BID}_LOD1', 2: f'{BID}_LOD2'}
objects = {}
for lod in (0, 1, 2):
    leaves = leaf_mesh(lod)
    parts = [leaves]
    if any(lod in s['lods'] for s in stems):
        bark = bark_mesh(lod); bark.data.materials.append(bark_mat); leaves.data.materials.append(leaf_mat)
        parts = [bark, leaves]
        # join keeps each part's material slots: bark slot 0, leaves slot 1
        for x in bpy.data.objects:
            x.select_set(x in parts)
        bpy.context.view_layer.objects.active = bark
        bpy.ops.object.join()
        obj = bark
    else:
        leaves.data.materials.append(leaf_mat)
        obj = leaves
    obj.name = names[lod]; obj.data.name = names[lod]
    objects[lod] = obj

# scale to the exact target height (LOD0 top); coarser levels never rise above it
top0 = max(v.co.z for v in objects[0].data.vertices)
scale = H / top0
for lod, obj in objects.items():
    obj.data.transform(Matrix.Scale(scale, 4))
    obj.data.update()
for lod in (1, 2):
    me = objects[lod].data
    over = max(v.co.z for v in me.vertices) - H
    if over > 0:
        # push the poking cards down (only leaf vertices above the top)
        for v in me.vertices:
            if v.co.z > H:
                v.co.z = H
stats = {}
for lod, obj in objects.items():
    me = obj.data
    co = np.array([tuple(v.co) for v in me.vertices])
    stats[lod] = {'tris': len(me.polygons), 'min': co.min(0).round(3).tolist(), 'max': co.max(0).round(3).tolist()}
    print(f'LOD{lod}', obj.name, 'tris', len(me.polygons), 'bounds', stats[lod]['min'], stats[lod]['max'],
          'materials', [m.name for m in me.materials])
    assert len(me.polygons) <= S['budget'][lod], (lod, len(me.polygons), S['budget'][lod])
json.dump({'id': BID, 'scale': scale, 'clumps': len(clumps), 'cards': len(cards), 'lods': stats},
          open(os.path.join(WORK, f'{BID}_build.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{BID}.blend'))
for o in bpy.data.objects:
    o.select_set(o.name in names.values())
bpy.context.view_layer.objects.active = objects[0]
out = os.path.join(WORK, f'{BID}_export.glb')
bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                          export_extras=True, export_normals=True, export_vertex_color='ACTIVE',
                          export_tangents=False, export_animations=False, export_skins=False, export_morph=False,
                          export_image_format='AUTO', export_apply=True)
print('EXPORTED', out)
