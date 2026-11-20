"""Sculpted tree (kind 'sculpt': the desert and gorge trees tree14/15/16/19/20/21): work/<id>/tree.blend with Tree,
Tree_LOD1, Tree_LOD2 (Bark + Leaves), each mesh with a 'Color' point attribute (linear, exported as COLOR_0).

The skeleton is hand-authored per species from its sprite (species/<id>.json 'sculpt', traced on
review/trace/<id>_grid.png): every limb is a polyline of [x, z] points in fractions of the tree height (x from the trunk
foot, + to the right in the sprite's view = model +x; the front camera looks along +y), radii per point (fractions of
H), and a depth `depth` (y of its tip relative to its start, fraction of H; the sprite gives no depth). A limb starts
at the y of the nearest point of the limbs before it.
- Limbs: Catmull-Rom through the points, sampled every ring step; tubes with parallel-transport frames. The cross
  section carries `ridges` lobes that spiral along the limb (`twist` rad/m: the twisted, sculpted trunks), knots
  (bumps at random places), and the trunk a lobed root flare (`flare`). u wraps the bark texture a whole number of
  times round the limb plus the same twist, so the bark fibres spiral with the ridges; v follows the arc length.
  Every vertex has its analytic normal (no shading seam at the u seam). Tips end in a short cone; limb starts sit
  inside their parent.
- Foliage pads ('pads': [x, z, r] or [x, y, z, r], fractions of H) are compact card clusters at the limb tips:
  cards (`card` m, from the species' atlas cells) on a flattened ellipsoid (`pad_flat`) facing outward and up.
  A pad with no limb tip inside it gets a thin stem from the nearest skeleton point, so no pad floats.
- COLOR_0: pads: sky visibility through all cards (each hit blocks `coverage`), floor + range x vis^power, x a
  pad-local term (lit top, shaded underside and core), x per-pad jitter, x the species leaf tint. Bark: the same rays
  x a crevice term from the ridges (darker valleys: the sprites' high-contrast trunks) x the bark tint (x `tone` per
  limb, e.g. tree20's pale dead limb).
- LOD1 / LOD2: rings and sides coarsen with the radius; pad cards keep the most visible fraction (spread by
  farthest-point sampling) grown about their centres; tone per LOD (lod.tone).
Usage: blender --background --python sculpt_build.py -- <id>"""
import bpy, bmesh, os, sys, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

spec = common.load()
W = spec['work']
H = spec['height_m']
SC = spec['sculpt']
LOD = spec['lod']
BUDGET = LOD['triangles']
LEAF_TINT, BARK_TINT = common.tints(spec)
CELLS = spec['leaves']['cells']
OCC = spec['occlusion']
COVERAGE = SC.get('coverage', 0.3)
TILE = spec['bark'].get('tile', 0.8)
rng = np.random.default_rng(spec['seed'])
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


def catmull(points, step):
    """Centripetal-ish Catmull-Rom through the points (ends duplicated), sampled about every `step` metres."""
    P = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        n = max(int(math.ceil((p2 - p1).length / step)), 1)
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(points[-1])
    return out


for o in list(bpy.data.objects):                   # the default scene (cube, camera, light) goes
    bpy.data.objects.remove(o, do_unlink=True)
DEPTH = SC.get('depth_scale', 1.8)                  # authored depths are guesses: spread the crown in depth

# ---------------------------------------------------------------- skeleton
limbs = []
for li, L in enumerate(SC['limbs']):
    pts2 = [np.array(p, float) for p in L['pts']]
    radii = L['r']
    if len(radii) == 2 and len(pts2) != 2:
        radii = list(np.linspace(radii[0], radii[1], len(pts2)))
    # start depth: the nearest earlier skeleton sample (in the sprite plane)
    y0 = 0.0
    if limbs:
        best = 1e9
        for prev in limbs:
            for q in prev['dense']:
                d = math.hypot(q.x - pts2[0][0] * H, q.z - pts2[0][1] * H)
                if d < best:
                    best, y0 = d, q.y
    n = len(pts2)
    pts = [Vector((p[0] * H, y0 + L.get('depth', 0.0) * DEPTH * H * (k / max(n - 1, 1)) ** 1.2, p[1] * H))
           for k, p in enumerate(pts2)]
    dense = catmull(pts, 0.004 * H)
    # radius along the arc length (linear between the authored points)
    seg = [0.0]
    for a, b in zip(pts, pts[1:]):
        seg.append(seg[-1] + (b - a).length)
    limbs.append({'pts': pts, 'radii': [r * H for r in radii], 'arc': seg, 'dense': dense,
                  'trunk': li == 0, 'tone': L.get('tone', 1.0), 'tip': L.get('tip', True), 'dead': L.get('dead', False)})
print('LIMBS', len(limbs))

# pads, and stems to the pads no limb reaches
pads = []
for pd in SC['pads']:
    if len(pd) == 3:
        x, z, r = pd; y = None
    else:
        x, y, z, r = pd
    c = Vector((x * H, 0.0, max(z * H, r * H * SC.get('pad_flat', 0.7) + 0.02 * H)))
    # depth: from the nearest skeleton sample, jittered
    best, qy = 1e9, 0.0
    for L in limbs:
        for q in L['dense']:
            d = math.hypot(q.x - c.x, q.z - c.z)
            if d < best:
                best, qy = d, q.y
    c.y = (y * H) if y is not None else qy + rng.uniform(-1.0, 1.0) * r * H
    lobes = [Vector(rng.normal(0, 1, 3)).normalized() for _ in range(SC.get('pad_lobes', 5))]
    pads.append({'lobes': lobes, 'scale': rng.uniform(0.8, 1.2, 3), 'c': c, 'r': r * H, 'tint': np.array([rng.uniform(0.93, 1.07), 1.0, rng.uniform(0.9, 1.08)])
                 * rng.uniform(0.9, 1.1)})
stems = 0
for pd in pads:
    tips = [L['pts'][-1] for L in limbs if L['tip']]
    if any((t - pd['c']).length < pd['r'] * 0.9 for t in tips):
        continue
    best, bq, br = 1e9, None, 0.0
    for L in limbs:
        if L.get('dead'):                               # no pad grows from a dead limb
            continue
        for k, q in enumerate(L['dense']):
            d = (q - pd['c']).length
            if d < best:
                best, bq = d, q
                f = k / max(len(L['dense']) - 1, 1)
                br = float(np.interp(f * L['arc'][-1], L['arc'], L['radii']))
    if bq is None:
        continue
    end = pd['c'] - (pd['c'] - bq).normalized() * pd['r'] * 0.25
    mid = bq.lerp(end, 0.5) + Vector((0, 0, 0.12 * (end - bq).length))
    r0 = min(max(br * 0.55, 0.006 * H), SC.get('stem_radius', 0.014) * H)
    pts = [bq, mid, end]
    seg = [0.0, (mid - bq).length, (mid - bq).length + (end - mid).length]
    limbs.append({'pts': pts, 'radii': [r0, r0 * 0.7, r0 * 0.35], 'arc': seg, 'dense': catmull(pts, 0.004 * H),
                  'trunk': False, 'tone': 1.0, 'tip': True, 'stem': True})
    stems += 1
print('PADS', len(pads), 'stems added', stems)

knot_rng = np.random.default_rng(spec['seed'] + 7)
for L in limbs:
    length = L['arc'][-1]
    L['knots'] = [(knot_rng.uniform(0.1, 0.9) * length, knot_rng.uniform(0, 2 * math.pi),
                   knot_rng.uniform(0.6, 1.0)) for _ in range(int(SC.get('knots', 1.2) * length / (0.1 * H)))]
    L['phase'] = knot_rng.uniform(0, 2 * math.pi)


def radius_at(L, s):
    return float(np.interp(s, L['arc'], L['radii']))


def frames(P):
    T = [(P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized() for i in range(len(P))]
    up = Vector((0, 0, 1)) if abs(T[0].z) < 0.95 else Vector((1, 0, 0))
    N = [(up - T[0] * up.dot(T[0])).normalized()]
    for i in range(1, len(P)):
        n = N[-1] - T[i] * N[-1].dot(T[i])
        N.append(n.normalized() if n.length > 1e-6 else N[-1])
    return T, N


SIDES_STEP = {0: 0.03, 1: 0.05, 2: 0.08}
SIDES_RANGE = {0: (5, 12), 1: (4, 7), 2: (3, 5)}
RING = {0: (1.4, 0.022, 0.06), 1: (2.8, 0.05, 0.12), 2: (4.5, 0.09, 0.2)}     # x radius, min, max (fractions of H)


def tube(bm, uvl, L, lod, normals, shades):
    """One limb as a ridged, twisted, knotted tube; appends per-vertex normals and crevice shades."""
    dense = L['dense']
    # arc length of the dense samples
    acc = [0.0]
    for a, b in zip(dense, dense[1:]):
        acc.append(acc[-1] + (b - a).length)
    total = acc[-1]
    rmax = max(L['radii'])
    sides = int(np.clip(round(2 * math.pi * rmax / (H * SIDES_STEP[lod])), *SIDES_RANGE[lod]))
    if L.get('stem') and lod > 0:
        sides = 3
    k_r, s_min, s_max = RING[lod]
    # ring positions: spacing follows the radius, tighter where the limb bends
    ss = [0.0]
    while ss[-1] < total:
        r = radius_at(L, ss[-1] * L['arc'][-1] / max(total, 1e-6))
        ss.append(min(ss[-1] + float(np.clip(k_r * r, s_min * H, s_max * H)), total))
        if total - ss[-1] < 1e-6:
            break
    ss = np.array(ss)
    P = [Vector(np.array([np.interp(s, acc, [q[c] for q in dense]) for c in range(3)])) for s in ss]
    T, N = frames(P)
    ridges = SC.get('ridges', 0) if (L['trunk'] or rmax > 0.035 * H) else 0
    ridge_amp = SC.get('ridge_amp', 0.0)
    twist = SC.get('twist', 0.0)                          # rad per metre
    around = max(1, round(2 * math.pi * rmax * 0.8 / TILE))
    rings = []
    tip = L['tip']
    last = len(P) - 1 if tip else len(P)
    for i in range(last):
        s = ss[i] * L['arc'][-1] / max(total, 1e-6)
        r = radius_at(L, s)
        if L['trunk']:                                    # lobed root flare
            fz = math.exp(-max(P[i].z, 0.0) / (SC.get('flare_height', 0.06) * H))
            r *= 1.0 + SC.get('flare', 0.0) * fz
        B = T[i].cross(N[i])
        ring = []
        for j in range(sides + 1):                         # j == sides duplicates j == 0 (u seam)
            th = 2 * math.pi * (j % sides) / sides
            ang = th + twist * s
            bump = 0.0
            if ridges:
                bump += ridge_amp * math.sin(ridges * th + twist * s + L['phase'])
            if L['trunk'] and SC.get('flare_lobes'):
                bump += SC.get('flare', 0.0) * 0.5 * fz * math.sin(SC['flare_lobes'] * th + L['phase'])
            for ks, ka, kamp in L['knots']:
                da = math.remainder(th - ka, 2 * math.pi)
                bump += SC.get('knot_amp', 0.15) * kamp * math.exp(-((s - ks) / (2.2 * r + 1e-6)) ** 2 - (da / 0.7) ** 2)
            radial = N[i] * math.cos(th) + B * math.sin(th)
            v = bm.verts.new(P[i] + radial * r * (1.0 + bump))
            ring.append((v, (j / sides * around + twist * s / (2 * math.pi) * around, s / TILE)))
            normals.append(radial)
            # crevices: the ridge valleys and the underside of knots read darker
            crev = 0.5 + 0.5 * math.sin(ridges * th + twist * s + L['phase']) if ridges else 0.7
            shades.append((SC.get('crevice', 0.3) * (crev - 1.0) + 1.0) * L['tone'])
        rings.append(ring)
    for i in range(len(rings) - 1):
        for j in range(sides):
            a, b = rings[i][j], rings[i][j + 1]
            c, d = rings[i + 1][j + 1], rings[i + 1][j]
            f = bm.faces.new((a[0], b[0], c[0], d[0]))
            for loop, (_, uv) in zip(f.loops, (a, b, c, d)):
                loop[uvl].uv = uv
    if tip:                                               # short cone at the tip
        apex = bm.verts.new(P[-1])
        normals.append(T[-1]); shades.append(L['tone'])
        i = len(rings) - 1
        for j in range(sides):
            a, b = rings[i][j], rings[i][j + 1]
            f = bm.faces.new((a[0], b[0], apex))
            for loop, uv in zip(f.loops, (a[1], b[1], (a[1][0], ss[-1] / TILE))):
                loop[uvl].uv = uv


def bark_mesh(lod):
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, shades = [], []
    for L in limbs:
        if lod == 2 and max(L['radii']) < SC.get('lod2_min_radius', 0.009) * H:
            continue                  # sub-pixel twigs and pad stems at the far level
        tube(bm, uvl, L, lod, normals, shades)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method='FIXED')
    # coarse rings can fold at sharp bends: a face whose winding disagrees with its outward normals is flipped, so the
    # engine (back faces culled on single-sided bark) never drops it
    bm.verts.index_update(); bm.normal_update()
    flipped = 0
    for f in bm.faces:
        avg = sum((normals[v.index] for v in f.verts), Vector((0, 0, 0)))
        if f.normal.dot(avg) < 0:
            f.normal_flip(); flipped += 1
    if flipped:
        print('BARK lod', lod, 'faces flipped outward', flipped)
    me = bpy.data.meshes.new(f'bark{lod}'); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set_from_vertices(normals)
    obj = bpy.data.objects.new(f'bark{lod}', me); bpy.context.scene.collection.objects.link(obj)
    return obj, shades


# ---------------------------------------------------------------- pad cards
CARD = SC.get('card', [0.7, 0.85])
FLAT = SC.get('pad_flat', 0.7)
CARD_UP = SC.get('card_up', 0.35)
bark0, _ = bark_mesh(0)
bark_tris0 = len(bark0.data.polygons)
cards_total = max((BUDGET[0] - bark_tris0) // 2 - 4, len(pads) * 4)
area = np.array([p['r'] ** 2 for p in pads]); share = area / area.sum()
cards = []                                   # (centre, normal, roll, size, cell, pad)
SHELL = SC.get('shell')                     # {inset, dark}: an opaque core per pad (depth prepass occludes cards)
LAYERS = SC.get('layers_target')            # mean card layers wanted over a pad's projected area
CELL_COV = float(np.mean([common.atlas(spec['atlas'])['cells'][c]['coverage'] for c in CELLS]))
if SHELL:
    cards_total -= len(pads) * 10                   # the shells' 20 triangles per pad come out of the card budget
if LAYERS:
    # both hemispheres of a pad carry cards; the far one is behind the shell (or the near one) and is rejected by the
    # depth prepass, so the near one sets the visible layers
    s_mean = 0.5 * (CARD[0] + CARD[1])
    wants = [max(int(round(2 * LAYERS * math.pi * (pd['r'] * 1.15) ** 2 / (CELL_COV * s_mean ** 2))), 6) for pd in pads]
    fit = min(1.0, cards_total / max(sum(wants), 1))
    wants = [max(int(w * fit), 6) for w in wants]
    print('LAYERS target', LAYERS, 'cards', sum(wants), 'budget fit', round(fit, 2))
for pi, pd in enumerate(pads):
    want = wants[pi] if LAYERS else max(int(round(share[pi] * cards_total)), 4)
    made = 0
    while made < want:
        d = Vector(rng.normal(0, 1, 3)).normalized()
        if d.z < -0.4 and rng.random() < 0.6:            # fewer cards on the pad's underside
            continue
        rho = rng.uniform(SC.get('pad_inner', 0.3), 1.0) ** 0.5      # no deep interior cards (never seen)
        # irregular pads: a few lobes push the surface out, axes scaled a little per pad
        rho *= 0.8 + SC.get('lobe_amp', 0.45) * max(max(d.dot(lb), 0.0) ** 2 for lb in pd['lobes'])
        sprig = rng.random() < SC.get('sprigs', 0.0)      # stray sprigs past the pad's outline (ragged edges)
        if sprig:
            rho = rng.uniform(1.15, 1.5)
        sc = pd['scale']
        q = pd['c'] + Vector((d.x * sc[0], d.y * sc[1], d.z * FLAT * sc[2])) * pd['r'] * rho
        if q.z < 0.02 * H:
            continue
        n = (d + Vector(rng.normal(0, 0.35, 3)) + Vector((0, 0, CARD_UP))).normalized()
        roll = rng.uniform(0, 2 * math.pi); size = rng.uniform(*CARD) * (0.6 if sprig else 1.0)
        cards.append((q, n, roll, size, CELLS[int(rng.integers(len(CELLS)))], pi))
        made += 1
print('CARDS', len(cards), 'bark tris LOD0', bark_tris0)


def corners(card, grow=1.0):
    p, n, roll, size, cell, pi = card
    s = size * grow
    t = n.orthogonal().normalized(); b = n.cross(t)
    rot = Matrix.Rotation(roll, 3, n); t = rot @ t; b = rot @ b
    return [p + (-t - b) * s / 2, p + (t - b) * s / 2, p + (t + b) * s / 2, p + (-t + b) * s / 2]


def shading_normal(q, pi):
    c = pads[pi]['c']
    o = q - c; o.z /= max(FLAT, 0.3)
    return (0.75 * o.normalized() + 0.25 * Vector((0, 0, 1))).normalized()


tv, ti = [], []
for card in cards:
    cs = corners(card); base = len(tv)
    tv += [tuple(q) for q in cs]; ti += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
bvh = BVHTree.FromPolygons(tv, ti)
dirs = rng.normal(0, 1, (4096, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
dirs = dirs[dirs[:, 2] > 0.02][:1024]
RAYS = 28


def visibility(point, normal):
    hits = 0.0
    for d in dirs[rng.choice(len(dirs), RAYS, replace=False)]:
        d = Vector(d)
        if d.dot(normal) < -0.3:
            d = (d - normal * 1.3 * d.dot(normal)).normalized() if d.z > 0 else d
        origin = point + d * 0.02; transmit = 1.0
        for _ in range(12):
            loc, *_ = bvh.ray_cast(origin, d, 3 * H)
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


LOCAL = SC.get('local', [0.5, 0.75])
LEAF_FLOOR = spec['leaves'].get('floor', 0.0)      # leaf vertex darkening never below this (no black cards)


def local_term(q, pi):
    c = pads[pi]['c']; r = pads[pi]['r']
    o = (q - c)
    return (LOCAL[0] + (1 - LOCAL[0]) * (0.5 + 0.5 * o.normalized().z)) * \
        (LOCAL[1] + (1 - LOCAL[1]) * min(o.length / r, 1.0))


card_col, card_vis = [], []
for k, card in enumerate(cards):
    cs = corners(card); pi = card[5]
    sky = [occ_value(visibility(q, shading_normal(q, pi))) for q in cs]
    occ = [max(o * local_term(q, pi), LEAF_FLOOR) for o, q in zip(sky, cs)]
    mean = sum(occ) / 4
    card_col.append([sun(LEAF_TINT * pads[pi]['tint'] * (0.7 * o + 0.3 * mean), 0.7 * o + 0.3 * mean) for o in occ])
    card_vis.append(mean)
card_vis = np.array(card_vis)
print('OCCLUSION cards min/mean/max', round(float(card_vis.min()), 2), round(float(card_vis.mean()), 2),
      round(float(card_vis.max()), 2))


def set_colours(me, colours):
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.concatenate([np.append(np.clip(c, 0, 1), 1.0) for c in colours]))
    me.color_attributes.active_color = attr


def subset(lod, budget_cards):
    if lod == 0:
        return list(range(len(cards)))
    picked = []
    frac = budget_cards / len(cards)
    for pi in range(len(pads)):
        members = [k for k, c in enumerate(cards) if c[5] == pi]
        n = max(2, int(round(len(members) * frac)))
        pool = sorted(members, key=lambda k: -card_vis[k])[:max(n, int(len(members) * LOD['keep'][lod]))]
        pts = np.array([cards[k][0] for k in pool]); sel = [0]
        dist = np.linalg.norm(pts - pts[0], axis=1)
        for _ in range(min(n, len(pool)) - 1):
            j = int(dist.argmax()); sel.append(j); dist = np.minimum(dist, np.linalg.norm(pts - pts[j], axis=1))
        picked += [pool[j] for j in sel]
    return picked[:budget_cards]


def leaf_mesh(lod, budget_cards):
    sel = subset(lod, budget_cards)
    grow = LOD['grow'][lod]; tone = np.asarray(LOD['tone'][lod], float)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for k in sel:
        card = cards[k]; cs = corners(card, grow); pi = card[5]
        f = bm.faces.new([bm.verts.new(q) for q in cs])
        u0, v0, su, sv = common.cell_uv(spec, card[4])
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + su * du, v0 + sv * dv)
        for q, col in zip(cs, card_col[k]):
            normals.append(shading_normal(q, pi)); colours.append(col * tone)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'leaves{lod}'); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'leaves{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('LEAVES lod', lod, 'cards', len(sel), 'tris', len(me.polygons))
    return obj


ICO_V = [(-1, 1.618, 0), (1, 1.618, 0), (-1, -1.618, 0), (1, -1.618, 0), (0, -1, 1.618), (0, 1, 1.618),
         (0, -1, -1.618), (0, 1, -1.618), (1.618, 0, -1), (1.618, 0, 1), (-1.618, 0, -1), (-1.618, 0, 1)]
ICO_F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
OCT_V = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
OCT_F = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]


def shell_mesh(lod):
    """Opaque core per pad: an icosahedron (octahedron at LOD2) inside the cards (SHELL.inset of the pad's lobed,
    flattened ellipsoid), dark interior green (species leaf colour x SHELL.dark x sky visibility), normals radial."""
    verts_src, faces_src = (ICO_V, ICO_F) if lod < 2 else (OCT_V, OCT_F)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals, colours = [], []
    for pi, pd in enumerate(pads):
        sc = pd['scale']; vs = []; uvs = []
        u0, v0, su, sv = common.cell_uv(spec, CELLS[pi % len(CELLS)])
        for v in verts_src:
            d = Vector(v).normalized()
            lobe = 0.8 + SC.get('lobe_amp', 0.45) * max(max(d.dot(lb), 0.0) ** 2 for lb in pd['lobes'])
            q = pd['c'] + Vector((d.x * sc[0], d.y * sc[1], d.z * FLAT * sc[2])) * pd['r'] * SHELL['inset'] * lobe
            q.z = max(q.z, 0.02 * H)
            vs.append(bm.verts.new(q))
            n = (q - pd['c']).normalized()
            normals.append(shading_normal(q, pi))      # as the pad's cards: outward and a little up
            vis = visibility(q + n * 0.02, n)
            # leaf texture (opaque: the atlas colour is dilated into its cut-out texels) x the leaves' tint: the core
            # reads as deeper foliage, a little darker than the inner cards, never as a hole
            colours.append(LEAF_TINT * pd['tint'] * SHELL.get('dark', 0.75) * (0.6 + 0.4 * vis))
            uvs.append((u0 + su * (0.5 + 0.22 * d.x), v0 + sv * (0.5 + 0.22 * d.z)))   # the spray, not the corners
        for f in faces_src:
            face = bm.faces.new([vs[i] for i in f])
            if face.calc_center_median().__sub__(pd['c']).dot(face.normal) < 0:
                face.normal_flip()
            for loop in face.loops:
                loop[uvl].uv = uvs[vs.index(loop.vert)]
    me = bpy.data.meshes.new(f'shell{lod}'); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.normals_split_custom_set_from_vertices(normals)
    set_colours(me, colours)
    obj = bpy.data.objects.new(f'shell{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('SHELL lod', lod, 'tris', len(me.polygons))
    return obj


def colour_bark(obj, shades, lod):
    me = obj.data
    floor = spec['bark']['occlusion_floor']
    tone = np.asarray(LOD['tone'][lod], float) if SC.get('tone_bark', False) else 1.0
    cols = []
    for v, sh in zip(me.vertices, shades):
        n = Vector(v.normal)
        o = floor + (1 - floor) * visibility(v.co + n * 0.01, n)
        cols.append(BARK_TINT * o * sh * tone)
    set_colours(me, cols)


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


bset = spec.get('bark_set', 'bark')
bark_mat = material('Bark', f'{bset}_basecolor.png', f'{bset}_normal.png', 0.9, rough_map=f'{bset}_mr.png',
                    normal_strength=1.6)
leaf_mat = material('Leaves', f"{spec['atlas']}_basecolor.png", f"{spec['atlas']}_normal.png", 0.85, alpha=True)
bark_mat['openyamm_wind'] = spec['wind']['bark']
if SHELL:
    # white 8x8 base colour and a flat normal map (shared, byte-identical): the colour is all COLOR_0, and every
    # pipeline step (impostor bake, LOD2 clump renders, review) treats the shell like any other material
    shell_mat = material('Shell', f"{spec['atlas']}_shell.png", 'shell_normal.png', 0.9)     # flat normals: atlas normals in its dilated texels shade the core black
    shell_mat['openyamm_wind'] = spec['wind']['leaves']        # moves with the cards around it
    shell_mat['openyamm_specular'] = 0.05
leaf_mat['openyamm_wind'] = spec['wind']['leaves']
leaf_mat['openyamm_translucency'] = spec['translucency']
names = {0: 'Tree', 1: 'Tree_LOD1', 2: 'Tree_LOD2'}
for lod in (0, 1, 2):
    if lod == 0:
        bpy.data.objects.remove(bark0, do_unlink=True)
    b, shades = bark_mesh(lod)
    colour_bark(b, shades, lod)
    bark_tris = len(b.data.polygons)
    shell_tris = len(pads) * (20 if lod < 2 else 8) if SHELL else 0
    budget_cards = (BUDGET[lod] - bark_tris - shell_tris) // 2 - 2
    if lod == 0:
        budget_cards = len(cards)
    l = leaf_mesh(lod, max(budget_cards, len(pads) * 2))
    print('BARK lod', lod, 'tris', bark_tris)
    b.data.materials.append(bark_mat); l.data.materials.append(leaf_mat)
    parts = [b, l]
    if SHELL and lod < 3:
        sh = shell_mesh(lod); sh.data.materials.append(shell_mat); parts.append(sh)
    for x in bpy.data.objects:
        x.select_set(x in parts)
    bpy.context.view_layer.objects.active = b
    bpy.ops.object.join()
    b.name = names[lod]; b.data.name = names[lod]
    print('LOD', lod, names[lod], 'tris', len(b.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(W, 'tree.blend'))
