"""The great-tree crown (work/<id>/tree.blend; settings in species/<id>.json): objects Tree, Tree_LOD1, Tree_LOD2
(Bark + Leaves + Shell), each mesh with a 'Color' point colour attribute (linear), exported as glTF COLOR_0
(multiplied into base colour). Metres; the model origin is the centre of the bark stub's base.

Adapted from the MM8 broadleaf build (../../mm8_3d/trees_broadleaf/scripts/build_tree.py, copied, not edited):
- Skeleton: no Sapling. A 16-sided bark stub (A6's trunk is a 16-sided BModel) of `limbs.stub.radius` from z = 0 up
  to the fork, capped; `limbs.main` heavy limbs starting inside the stub (one upright leader, the others spreading:
  tilt from vertical growing from `tilt` to `tilt_end`), `limbs.sub` sub-limbs off each main limb and
  `limbs.branch` branches off each sub-limb, each a polyline with a geometric radius taper, a little random wander
  and an upward pull, cut where it leaves 0.92 x the crown envelope. Branch ends (and the outer parts of the
  sub-limbs) are the clump anchors.
- Bark: one tube per limb, sides by base radius (`limbs.sides`), rings per metre per level (`limbs.rings_per_m`,
  fewer on LOD1/LOD2), the tip closed by a short cone; limbs chosen thickest-first as the longest prefix that fits
  `bark.budget` per LOD. UVs in the trunk's xdbark tile (common.BARK_TILE_M: 1.57 m around x 3.13 m along), u
  proportional to each ring's circumference, the one seam along the limb's top side (seen least from the ground);
  the stub wraps exactly `around_tiles` tiles (no seam). COLOR_0 = the trunk's colour (1) x sky visibility through
  the leaves (floor `bark.occlusion_floor`), fading to 1 toward the stub's base (`bark.base_fade` [z0, z1] m) so the
  joint with the BModel trunk shows no step.
- Crown (as the MM8 batch): clumps on the branch ends in the outer crown plus points of the envelope's shell, inner
  clumps, an open lifted underside (`crown.underside`), leaf cards in each clump, sky-ray occlusion through the
  cards, opaque shell cores in the largest clumps, a view cull of the least visible cards, LOD1/LOD2 subsets.
  Clump placement is vectorised and the envelope fit steps scale with the crown (a 44 m crown, not 12 m).
Usage: blender --background --python build_tree.py -- <id>"""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
spec = common.load()
WORK = OUT = spec['work']
LEAF_TINT, BARK_TINT = common.tints(spec)
CELLS = spec['leaves']['cells']
print('TINT leaves', LEAF_TINT.round(3), 'bark', BARK_TINT.round(3))
H = spec['height_m']
LIMBS = spec['limbs']
BARK, CROWN, LOD = spec['bark'], spec['crown'], spec['lod']
BRANCH_BUDGET = dict(enumerate(BARK['budget']))
TRI_BUDGET = dict(enumerate(LOD['triangles']))
GROW = dict(enumerate(LOD['grow']))
OUTWARD = dict(enumerate(LOD['outward']))
TONE = dict(enumerate(LOD['tone']))
CLUMPS, INNER_CLUMPS = CROWN['clumps'], CROWN['inner_clumps']
OUTER_RADIUS, INNER_RADIUS = tuple(CROWN['outer_radius']), tuple(CROWN['inner_radius'])
CLUMP_GAP = CROWN['gap']
CARD = tuple(CROWN['card'])
COVERAGE = CROWN['coverage']
TILE_AROUND, TILE_ALONG = common.BARK_TILE_M
OCC = spec['occlusion']
HUE = np.array(OCC.get('hue', [1.0, 1.0, 1.0]))
LEAF_FLOOR = OCC.get('leaf_floor', 0.17)
RAYS = OCC.get('rays', 32)


def leaf_floor(c):
    lum = float(np.dot(c, [0.2126, 0.7152, 0.0722]))
    return c * (LEAF_FLOOR / lum) if 0 < lum < LEAF_FLOOR else c


CARD_UP = CROWN.get('card_up', 0.0)
LOW_KEEP = CROWN.get('low_keep', 1.0)
low_rng = np.random.default_rng(spec['seed'] + 9)
SHELL_RADIAL = CROWN.get('shell_radial')
FLATTEN = CROWN.get('flatten', 1.0)
SHELL = CROWN.get('shell')
rng = np.random.default_rng(spec['seed'])
profile = np.array(json.load(open(os.path.join(WORK, 'profile.json')))['half_width_by_height'])


LOBES_AZ = CROWN.get('lobes_az', [])          # [[amplitude, count around, phase], ...]: a lopsided, lobed crown


def R(z, x=None, y=None):
    """Envelope half-width at height z; with x, y, scaled by the azimuthal lobes (the revolved profile is otherwise
    the same from every side)."""
    r = float(np.interp(z / H, profile[:, 0], profile[:, 1])) * H
    if x is not None and LOBES_AZ:
        az = math.atan2(y, x)
        r *= 1.0 + sum(a * math.sin(k * az + ph + 0.15 * z) for a, k, ph in LOBES_AZ)
    return r


CANOPY_LOW = CROWN['canopy_low'] * H
CENTRE = Vector((0, 0, CROWN['centre'] * H))


def crown_normal(p):
    o = p - CENTRE; o.z *= CROWN['crown_normal_z']
    return o.normalized()


for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# ---------------------------------------------------------------- skeleton
lr = np.random.default_rng(LIMBS['seed'])
STEP = 1.0                                       # skeleton resolution (m); meshes resample it per LOD


def inside_envelope(p):
    return p.z < 0.93 * H and (p.z < CANOPY_LOW or math.hypot(p.x, p.y) < 0.92 * R(p.z, p.x, p.y))


def grow(start, heading, length, r0, r1, wander, up, tilt_to=None):
    """Polyline from `start` along `heading` (unit), radius r0 -> r1 (geometric), cut where it leaves the envelope.
    tilt_to: (tilt0, tilt1, azimuth) degrees: the heading's angle from vertical eases from tilt0 to tilt1."""
    n = max(2, int(math.ceil(length / STEP)))
    pts, d = [Vector(start)], Vector(heading).normalized()
    for i in range(n):
        t = (i + 1) / n
        if tilt_to:
            t0, t1, az = tilt_to
            tilt = math.radians(t0 + (t1 - t0) * t ** 0.8)
            base = Vector((math.sin(tilt) * math.cos(az), math.sin(tilt) * math.sin(az), math.cos(tilt)))
            d = (base + Vector(lr.normal(0, math.radians(wander), 3))).normalized()
        else:
            d = (d + Vector(lr.normal(0, math.radians(wander), 3)) + Vector((0, 0, up / n))).normalized()
        p = pts[-1] + d * (length / n)
        if not inside_envelope(p) and i > 0:
            break
        pts.append(p)
    m = len(pts) - 1
    full = n
    rads = [r0 * (r1 / r0) ** (min(k / full, 1.0)) for k in range(m + 1)]
    # a limb cut short by the envelope still ends thin
    if m < full:
        rads[-1] = max(r1, rads[-1] * 0.6)
    return pts, rads


def local(limb, t):
    """Point, radius and direction at fraction t of a limb's length."""
    pts, rads = limb['pts'], limb['rads']
    f = t * (len(pts) - 1); i = min(int(f), len(pts) - 2); w = f - i
    p = pts[i].lerp(pts[i + 1], w); r = rads[i] + (rads[i + 1] - rads[i]) * w
    return p, r, (pts[i + 1] - pts[i]).normalized()


def side_heading(d, spread, k):
    """Parent direction turned by `spread` degrees about a perpendicular axis that rotates per child (alternate
    sides), so children leave on all sides."""
    perp = d.orthogonal().normalized()
    perp = Matrix.Rotation(k * 2.4 + lr.uniform(-0.4, 0.4), 3, d) @ perp
    axis = d.cross(perp).normalized()
    return (Matrix.Rotation(math.radians(spread), 3, axis) @ d).normalized()


limbs = []                                       # {'pts', 'rads', 'level', 'parent'}
M, SUB, BR = LIMBS['main'], LIMBS['sub'], LIMBS['branch']
count = M['count']
phase = lr.uniform(0, 2 * math.pi)
for k in range(count):
    leader = k < M.get('leader', 0)
    az = phase + 2 * math.pi * k / max(count - M.get('leader', 0), 1) + lr.uniform(-0.25, 0.25)
    z0 = lr.uniform(*M['z']); r0 = lr.uniform(*M['radius'])
    off = 0.0 if leader else M['offset']
    start = Vector((off * math.cos(az), off * math.sin(az), z0))
    if leader:
        tilt = lr.uniform(*M['leader_tilt']); t_end = tilt + 6; length = M['leader_length']; r0 *= 0.85
    else:
        tilt = lr.uniform(*M['tilt']); t_end = lr.uniform(*M['tilt_end']); length = lr.uniform(*M['length'])
    pts, rads = grow(start, Vector((0, 0, 1)), length, r0, M['tip_radius'], M['wander'], 0,
                     tilt_to=(tilt, t_end, az))
    limbs.append({'pts': pts, 'rads': rads, 'level': 0, 'parent': -1})
for level, cfg in ((1, SUB), (2, BR)):
    parents = [i for i, l in enumerate(limbs) if l['level'] == level - 1]
    for pi in parents:
        parent = limbs[pi]
        n = int(lr.integers(cfg['count'][0], cfg['count'][1] + 1))
        for k in range(n):
            t = cfg['t'][0] + (cfg['t'][1] - cfg['t'][0]) * (k + lr.uniform(0.2, 0.8)) / n
            p, r, d = local(parent, min(t, 0.98))
            heading = side_heading(d, lr.uniform(*cfg['spread']), k)
            r0 = max(r * lr.uniform(*cfg['radius']), cfg['tip_radius'] * 1.2)
            length = lr.uniform(*cfg['length']) * (1.0 - 0.3 * t)
            pts, rads = grow(p, heading, length, r0, cfg['tip_radius'] * (0.6 if level == 2 else 1.0),
                             cfg['wander'], cfg['up'])
            if len(pts) >= 2:
                limbs.append({'pts': pts, 'rads': rads, 'level': level, 'parent': pi})
print('SKELETON limbs', {lv: sum(1 for l in limbs if l['level'] == lv) for lv in (0, 1, 2)})

# clump anchors: branch ends, sub-limb ends and the outer halves of the sub-limbs
tips = []
for l in limbs:
    if l['level'] == 2:
        tips.append(np.array(l['pts'][-1]))
        tips.append(np.array(l['pts'][len(l['pts']) // 2]))
    elif l['level'] == 1:
        for p in l['pts'][len(l['pts']) // 2:]:
            tips.append(np.array(p))
    else:
        tips.append(np.array(l['pts'][-1]))
tips = np.array(tips)
print('TIPS', len(tips))

# ---------------------------------------------------------------- bark meshes


def sides_for(r, lod):
    s = next(n for thr, n in LIMBS['sides'] if r > thr)
    if lod == 1:
        s = max(4, int(round(s * 0.67 / 2)) * 2)
    elif lod == 2:
        s = max(4, int(round(s * 0.5 / 2)) * 2)
    return s


def resample(pts, rads, segments):
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + (b - a).length)
    out_p, out_r = [], []
    for k in range(segments + 1):
        s = cum[-1] * k / segments
        i = max(0, min(np.searchsorted(cum, s) - 1, len(pts) - 2))
        w = (s - cum[i]) / max(cum[i + 1] - cum[i], 1e-6)
        out_p.append(pts[i].lerp(pts[i + 1], w)); out_r.append(rads[i] + (rads[i + 1] - rads[i]) * w)
    return out_p, out_r, cum[-1]


def tube(bm, uvl, pts, rads, sides, tip=True):
    """Rings along the polyline (frames: the side away from world up at u's centre; the seam on top), quads
    triangulated later, a cone at the tip. u = arc around / TILE_AROUND (per ring circumference), v = length along."""
    rings, prev_up = [], None
    length = 0.0
    for i, (p, r) in enumerate(zip(pts, rads)):
        if i == 0:
            t = (pts[1] - pts[0]).normalized()
        elif i == len(pts) - 1:
            t = (pts[-1] - pts[-2]).normalized()
        else:
            t = ((pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()).normalized()
            length += (pts[i] - pts[i - 1]).length
        if i == len(pts) - 1 and i > 0:
            length += (pts[i] - pts[i - 1]).length
        up = Vector((0, 0, 1)) - t * t.z
        if up.length < 0.15:
            up = (prev_up - t * prev_up.dot(t)) if prev_up is not None else t.orthogonal()
        up.normalize(); prev_up = up
        side = t.cross(up)
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides           # j = 0 on top (the seam), sides / 2 underneath
            ring.append(bm.verts.new(p + (up * math.cos(a) + side * math.sin(a)) * r))
        rings.append((ring, r, length))
    for (ra, r_a, la), (rb, r_b, lb) in zip(rings, rings[1:]):
        for j in range(sides):
            j2 = (j + 1) % sides
            f = bm.faces.new((ra[j], ra[j2], rb[j2], rb[j]))
            f.smooth = True
            uvs = []
            for (rr, ll), jj in (((r_a, la), j), ((r_a, la), j + 1), ((r_b, lb), j + 1), ((r_b, lb), j)):
                circ = 2 * math.pi * rr
                uvs.append(((jj / sides - 0.5) * circ / TILE_AROUND, ll / TILE_ALONG))
            for loop, uv in zip(f.loops, uvs):
                loop[uvl].uv = uv
    if tip:
        ring, r, ll = rings[-1]
        t = (pts[-1] - pts[-2]).normalized()
        apex = bm.verts.new(pts[-1] + t * max(r * 1.5, 0.15))
        for j in range(sides):
            j2 = (j + 1) % sides
            f = bm.faces.new((ring[j], ring[j2], apex)); f.smooth = True
            circ = 2 * math.pi * r
            for loop, uv in zip(f.loops, (((j / sides - 0.5) * circ / TILE_AROUND, ll / TILE_ALONG),
                                          (((j + 1) / sides - 0.5) * circ / TILE_AROUND, ll / TILE_ALONG),
                                          (0.0, (ll + r * 1.5) / TILE_ALONG))):
                loop[uvl].uv = uv


def stub(bm, uvl):
    """The stub: 16 sides (as A6's trunk), from z = 0 (inside the trunk, open) to the fork, a slight bulge, then a
    low cone cap under the limbs; wraps exactly `around_tiles` xdbark tiles."""
    S = LIMBS['stub']; n = S['sides']; tiles = S['around_tiles']
    levels = [(0.0, S['radius']), (S['top'] * 0.6, S['radius'] * 1.02), (S['top'], S['radius'] * 0.97)]
    rings = []
    for z, r in levels:
        rings.append([bm.verts.new((r * math.cos(2 * math.pi * j / n), r * math.sin(2 * math.pi * j / n), z))
                      for j in range(n)])
    for (ra, (za, _)), (rb, (zb, _)) in zip(zip(rings, levels), zip(rings[1:], levels[1:])):
        for j in range(n):
            j2 = (j + 1) % n
            f = bm.faces.new((ra[j], ra[j2], rb[j2], rb[j])); f.smooth = True
            for loop, (u, v) in zip(f.loops, ((j, za), (j + 1, za), (j + 1, zb), (j, zb))):
                loop[uvl].uv = (u / n * tiles, v / TILE_ALONG)
    inner = [bm.verts.new((S['radius'] * 0.45 * math.cos(2 * math.pi * j / n), S['radius'] * 0.45 * math.sin(2 * math.pi * j / n),
                           S['top'] + S['cap'] * 0.7)) for j in range(n)]
    apex = bm.verts.new((0, 0, S['top'] + S['cap']))
    for j in range(n):
        j2 = (j + 1) % n
        f = bm.faces.new((rings[-1][j], rings[-1][j2], inner[j2], inner[j])); f.smooth = True
        for loop, (u, v) in zip(f.loops, ((j, 0), (j + 1, 0), (j + 1, 1), (j, 1))):
            loop[uvl].uv = (u / n * tiles, (S['top'] + v * S['cap'] * 0.8) / TILE_ALONG)
        f = bm.faces.new((inner[j], inner[j2], apex)); f.smooth = True
        for loop, (u, v) in zip(f.loops, ((j, 1), (j + 1, 1), (j + 0.5, 2))):
            loop[uvl].uv = (u / n * tiles * 0.45, (S['top'] + v * S['cap'] * 0.5) / TILE_ALONG)


RPM = LIMBS['rings_per_m']
RING_SCALE = {0: 1.0, 1: 0.6, 2: 0.4}


def limb_parts(lod):
    parts = []
    for l in limbs:
        pts, rads = l['pts'], l['rads']
        seglen = sum((b - a).length for a, b in zip(pts, pts[1:]))
        segments = max(1, int(round(seglen * RPM[l['level']] * RING_SCALE[lod])))
        if l['level'] == 0:
            segments = max(segments, 3 if lod < 2 else 2)
        rp, rr, _ = resample(pts, rads, segments)
        sides = sides_for(rads[0], lod)
        tris = sides * segments * 2 + sides
        parts.append((rads[0], rp, rr, sides, tris))
    parts.sort(key=lambda p: -p[0])
    return parts


def bark_mesh(lod):
    parts = limb_parts(lod)
    total = 16 * 2 * 2 + 16 * 3                      # the stub
    n = 0
    for p in parts:
        if total + p[4] > BRANCH_BUDGET[lod]:
            break
        total += p[4]; n += 1
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    stub(bm, uvl)
    for _, rp, rr, sides, _ in parts[:n]:
        tube(bm, uvl, rp, rr, sides)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'bark{lod}'); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(f'bark{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('BARK lod', lod, 'limbs', n, 'of', len(parts), 'thinnest base radius', round(parts[n - 1][0], 3),
          'tris', len(me.polygons))
    return obj


barks = {lod: bark_mesh(lod) for lod in (0, 1, 2)}

# ---------------------------------------------------------------- clumps
UNDERSIDE = CROWN.get('underside')
WIDEST = float(profile[:, 1].max()) * H
FIT_STEP = 0.01 * H


def floor_at(rad):
    """Lowest clump bottom at this distance from the axis: canopy_low at the rim, rising to the underside."""
    if not UNDERSIDE:
        return CANOPY_LOW
    t = min(rad / max(WIDEST, 1e-3), 1.0)
    return UNDERSIDE * H + (CANOPY_LOW - UNDERSIDE * H) * t


def fit(c, r):
    """Pull a clump centre toward the crown axis/down (or up off the underside) until its ball fits the envelope."""
    c = c.copy()
    for _ in range(200):
        rad = math.hypot(c[0], c[1])
        low = floor_at(rad)
        if rad + 0.85 * r <= R(min(c[2], H), c[0], c[1]) and c[2] + 0.85 * r <= H and c[2] - 0.6 * r >= low:
            return c
        if c[2] + 0.85 * r > H:
            c[2] -= FIT_STEP
        if c[2] - 0.6 * r < low:
            c[2] += FIT_STEP
        if rad > 1e-3 and rad + 0.85 * r > R(min(c[2], H), c[0], c[1]):
            c[:2] *= max(rad - FIT_STEP, 0.0) / rad
    return c


depth = np.array([math.hypot(t[0], t[1]) / max(R(t[2], t[0], t[1]), 0.05) if CANOPY_LOW < t[2] < H else 0 for t in tips])
acc_c = np.zeros((0, 3)); acc_r = np.zeros(0)


# crown.gaps {count, radius [deg, deg], elevation [deg, deg], seed}: open windows in the outer crown (clumps whose
# direction from the crown centre falls inside one are skipped), so the limbs show through and the dome reads layered
GAPS = CROWN.get('gaps')
gap_dirs = []
if GAPS:
    gr = np.random.default_rng(GAPS.get('seed', 31))
    for k in range(GAPS['count']):
        az = 2 * math.pi * (k + gr.uniform(0.15, 0.85)) / GAPS['count']
        el = math.radians(gr.uniform(*GAPS['elevation']))
        gap_dirs.append((np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)]),
                         math.cos(math.radians(gr.uniform(*GAPS['radius'])))))


def in_gap(c):
    if not gap_dirs:
        return False
    v = np.asarray(c) - np.array(CENTRE); v = v / max(np.linalg.norm(v), 1e-6)
    return any(float(v @ d) > cos for d, cos in gap_dirs)


def place(pool, count, radius, accepted):
    """Clumps on anchor points, never closer than CLUMP_GAP x the sum of radii (vectorised)."""
    global acc_c, acc_r
    order = rng.permutation(len(pool))
    placed = 0
    for k in order:
        if placed >= count:
            break
        r = rng.uniform(*radius)
        c = fit(pool[k], r)
        if radius is OUTER_RADIUS and in_gap(c):
            continue
        if LOW_KEEP < 1.0 and c[2] < CROWN['centre'] * H and low_rng.random() > LOW_KEEP:
            continue
        if len(acc_r) and np.any(np.linalg.norm(acc_c - c, axis=1) < CLUMP_GAP * (acc_r + r)):
            continue
        accepted.append((c, r, radius is INNER_RADIUS)); placed += 1
        acc_c = np.vstack([acc_c, c]); acc_r = np.append(acc_r, r)
    return placed


clumps = []
outer = tips[(depth > 0.55) & (tips[:, 2] > CANOPY_LOW + 0.2)]
place(outer, CLUMPS, OUTER_RADIUS, clumps)
shell = []
while len(shell) < 30000:
    z = rng.uniform(CANOPY_LOW + 0.3, H - 0.3); th = rng.uniform(0, 2 * math.pi)
    lo = 0.5
    if SHELL_RADIAL and z < CROWN['centre'] * H:
        lo = SHELL_RADIAL
    rad = R(z, math.cos(th), math.sin(th)) * rng.uniform(lo, 0.97)
    shell.append(np.array([rad * math.cos(th), rad * math.sin(th), z]))
shell = np.array(shell)
inner = tips[(depth > 0.15) & (depth <= 0.55) & (tips[:, 2] > CANOPY_LOW + 0.4)]
from_tips = len(clumps)
n_outer = from_tips + place(shell, CLUMPS - from_tips, OUTER_RADIUS, clumps)
n_inner = place(inner, INNER_CLUMPS, INNER_RADIUS, clumps)
print('CLUMPS outer', n_outer, 'on tips', from_tips, 'inner', n_inner, 'radius', round(min(c[1] for c in clumps), 2), '..',
      round(max(c[1] for c in clumps), 2))

shapes = [rng.uniform(0.8, 1.25, 3) * np.array([1.0, 1.0, FLATTEN]) for _ in clumps]
cores_tris = {lod: 8 * SHELL['cores'][lod] for lod in (0, 1, 2)} if SHELL else {0: 0, 1: 0, 2: 0}
bark_tris = len(barks[0].data.polygons)
cards_total = (TRI_BUDGET[0] - bark_tris - cores_tris[0]) // 2 - 20
GEN_CARDS = CROWN.get('gen_cards')
keep_cards = cards_total
if CROWN.get('keep'):
    keep_cards = min(keep_cards, int(round((GEN_CARDS or cards_total) * CROWN['keep'])))
if GEN_CARDS:
    cards_total = GEN_CARDS
area = np.array([r * r * (0.5 if inner_ else 1.0) for _, r, inner_ in clumps]); share = area / area.sum()
cards = []                          # centre, normal, roll, size, cell, clump index
for ci, (c, r, inner_) in enumerate(clumps):
    want = int(round(share[ci] * cards_total))
    centre = Vector(c)
    made = 0
    tries = 0
    while made < want and tries < 50 * want:
        tries += 1
        d = Vector(rng.normal(0, 1, 3)).normalized()
        if d.dot(crown_normal(centre)) < -0.3 and rng.random() < 0.75:
            continue
        rho = r * rng.uniform(0.35, 1.0) ** 0.5
        p = centre + Vector(np.array(d) * shapes[ci]) * rho * (1 + 0.15 * math.sin(3 * d.x + 2 * d.z + ci))
        rad = math.hypot(p.x, p.y)
        if p.z > H + 0.2 or p.z < CANOPY_LOW - 0.3 or rad > R(min(p.z, H), p.x, p.y) * 1.08:
            continue
        n = (d + Vector(rng.normal(0, 0.35, 3))).normalized()
        if CARD_UP:
            n = (n + Vector((0, 0, CARD_UP))).normalized()
        roll = rng.uniform(0, 2 * math.pi); size = rng.uniform(*CARD)
        cell = CELLS[int(rng.integers(len(CELLS)))]
        cards.append((p, n, roll, size, cell, ci))
        made += 1
print('CARDS', len(cards), 'keep target', keep_cards)


def card_corners(card, grow, outward=0.0):
    p, n, roll, size, cell, ci = card
    s = size * grow
    if outward:
        n = (n + crown_normal(p) * outward).normalized()
    t = n.orthogonal().normalized(); b = n.cross(t)
    rot = Matrix.Rotation(roll, 3, n); t = rot @ t; b = rot @ b
    return [p + (-t - b) * s / 2, p + (t - b) * s / 2, p + (t + b) * s / 2, p + (-t + b) * s / 2]


def shading_normal(q, ci):
    c = Vector(clumps[ci][0])
    return (0.7 * (q - c).normalized() + 0.3 * crown_normal(q)).normalized()


# ---------------------------------------------------------------- occlusion rays against the generated cards
tris_v, tris_i = [], []
for k, card in enumerate(cards):
    cs = card_corners(card, 1.0); base = len(tris_v)
    tris_v += [tuple(q) for q in cs]; tris_i += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
bvh = BVHTree.FromPolygons(tris_v, tris_i)
shells = {}
shell_bvh = None


def core_mesh(count):
    """An octahedron (8 triangles) inside each of the `count` largest clumps, at shell.core x the clump's ellipsoid,
    sampling the leafy hub of one atlas cell (MM8 shell mode 'cores')."""
    order = sorted(range(len(clumps)), key=lambda i: -clumps[i][1] ** 2 * (0.6 if clumps[i][2] else 1.0))[:count]
    cr = np.random.default_rng(spec['seed'] + 77)
    yaws = cr.uniform(0, 2 * math.pi, len(clumps))
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    hub = {0: (0.75, 0.5), 1: (0.25, 0.5), 2: (0.5, 0.75), 3: (0.5, 0.25), 4: (0.5, 0.5), 5: (0.5, 0.5)}
    for k, i in enumerate(order):
        c, r, _ = clumps[i]; axes = r * SHELL['core'] * np.asarray(shapes[i])
        u0, v0, size = common.cell_uv(CELLS[k % len(CELLS)])
        ca, sa = math.cos(yaws[i]), math.sin(yaws[i])

        def put(x, y, z):
            return bm.verts.new((c[0] + (x * ca - y * sa) * axes[0], c[1] + (x * sa + y * ca) * axes[1], c[2] + z * axes[2]))
        px, nx, py, ny, pz, nz = put(1, 0, 0), put(-1, 0, 0), put(0, 1, 0), put(0, -1, 0), put(0, 0, 1), put(0, 0, -1)
        slot = {px: 0, nx: 1, py: 2, ny: 3, pz: 4, nz: 5}
        for a_, b_ in ((px, py), (py, nx), (nx, ny), (ny, px)):
            for f in (bm.faces.new((a_, b_, pz)), bm.faces.new((b_, a_, nz))):
                for loop in f.loops:
                    hu, hv = hub[slot[loop.vert]]
                    loop[uvl].uv = (u0 + size * hu, v0 + size * hv)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('shell'); bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    return me


if SHELL:
    for lod in (0, 1, 2):
        shells[lod] = core_mesh(SHELL['cores'][lod])
    shell_bvh = BVHTree.FromPolygons([tuple(v.co) for v in shells[0].vertices],
                                     [tuple(p.vertices) for p in shells[0].polygons])
    print('SHELL tris', [len(shells[l].polygons) for l in (0, 1, 2)])
dirs_sky = rng.normal(0, 1, (2048, 3)); dirs_sky /= np.linalg.norm(dirs_sky, axis=1, keepdims=True)
dirs_sky = dirs_sky[dirs_sky[:, 2] > 0.02][:512]
FAR = 3.0 * H


def visibility(point, normal, skip=None):
    """Sky visibility: rays over the upper hemisphere through the leaf cards (each hit blocks COVERAGE)."""
    hits = 0.0
    sel = rng.choice(len(dirs_sky), RAYS, replace=False)
    for d in dirs_sky[sel]:
        d = Vector(d)
        origin = point + d * 0.02
        transmit = 1.0
        for _ in range(12):
            loc, _, index, dist = bvh.ray_cast(origin, d, FAR)
            if loc is None:
                break
            if skip is None or index // 2 != skip:
                transmit *= 1.0 - COVERAGE
                if transmit < 0.05:
                    break
            origin = loc + d * 0.01
        hits += transmit
    return hits / RAYS


clump_tint = [np.array([rng.uniform(0.95, 1.05), 1.0, rng.uniform(0.94, 1.06)]) * rng.uniform(0.92, 1.08)
              for _ in clumps]


def occlusion(vis):
    return OCC['floor'] + OCC['range'] * vis ** OCC['power']


def local_term(q, ci):
    """Clump-local shading: lit clump top, shaded underside, darker toward the clump core."""
    c = Vector(clumps[ci][0]); r = clumps[ci][1]
    return (0.28 + 0.72 * (0.5 + 0.5 * (q - c).normalized().z)) * (0.6 + 0.4 * min((q - c).length / r, 1.0))


card_occ, card_rank, card_sky = [], [], []
for k, card in enumerate(cards):
    corners = card_corners(card, 1.0); ci = card[5]
    sky = [occlusion(visibility(q, shading_normal(q, ci), skip=k)) for q in corners]
    card_sky.append(sum(sky) / 4)
    occ = [o * local_term(q, ci) for o, q in zip(sky, corners)]
    mean = sum(occ) / 4
    card_occ.append([leaf_floor(LEAF_TINT * clump_tint[ci] * np.power(0.7 * o + 0.3 * mean, HUE)) for o in occ])
    card_rank.append(np.mean([c.mean() for c in card_occ[-1]]))
vis_card = np.array(card_rank)
card_view = np.ones(len(cards))
full = {'cards': list(cards), 'card_sky': list(card_sky)}
if len(cards) > keep_cards:
    # view visibility: 40 directions (8 azimuths x elevations -70/-25/0/25/50 degrees) from each card centre through
    # the cards (and the opaque cores); a card's score is its best direction
    view_dirs = []
    for el in (-70, -25, 0, 25, 50):
        for az in range(8):
            a = 2 * math.pi * (az + 0.5 * (el % 50 == 0)) / 8; e = math.radians(el)
            view_dirs.append(Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e))))

    def view_visibility(k):
        p = sum(card_corners(cards[k], 1.0), Vector()) / 4
        best = 0.0
        for d in view_dirs:
            origin = p + d * 0.02; transmit = 1.0
            if shell_bvh is not None and shell_bvh.ray_cast(origin, d, FAR)[0] is not None:
                continue
            for _ in range(10):
                loc, _, index, dist = bvh.ray_cast(origin, d, FAR)
                if loc is None:
                    break
                if index // 2 != k:
                    transmit *= 1.0 - COVERAGE
                    if transmit < 0.03:
                        break
                origin = loc + d * 0.01
            best = max(best, transmit)
            if best >= 0.99:
                break
        return best
    view = np.array([view_visibility(k) for k in range(len(cards))])
    order = np.lexsort((-vis_card, -view))
    keep = sorted(order[:keep_cards].tolist())
    card_view = view[keep]
    print('VIEW cull', len(cards), '->', len(keep), 'cards; dropped view score max', round(float(view[order[keep_cards:]].max()), 3),
          'mean', round(float(view[order[keep_cards:]].mean()), 3))
    cards = [cards[k] for k in keep]; card_occ = [card_occ[k] for k in keep]
    card_rank = [card_rank[k] for k in keep]; card_sky = [card_sky[k] for k in keep]
    vis_card = np.array(card_rank)
print('OCCLUSION cards min/mean/max', round(float(vis_card.min()), 3), round(float(vis_card.mean()), 3),
      round(float(vis_card.max()), 3))


def set_colours(me, colours):
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    flat = np.concatenate([np.append(c, 1.0) for c in colours])
    attr.data.foreach_set('color', flat)
    me.color_attributes.active_color = attr


z0, z1 = BARK['base_fade']
for lod, obj in barks.items():
    me = obj.data
    colours = []
    for v in me.vertices:
        p = obj.matrix_world @ v.co
        o = BARK['occlusion_floor'] + (1.0 - BARK['occlusion_floor']) * visibility(p, v.normal)
        w = min(max((p.z - z0) / (z1 - z0), 0.0), 1.0); w = w * w * (3 - 2 * w)
        colours.append(BARK_TINT * (1.0 * (1 - w) + o * w))
    set_colours(me, colours)

if SHELL:
    shell_base = LEAF_TINT / float(np.dot(LEAF_TINT, [0.2126, 0.7152, 0.0722])) * SHELL['lum']
    floor = SHELL.get('ao_floor', 0.45)
    for lod, me in shells.items():
        set_colours(me, [shell_base * np.power(floor + (1 - floor) * visibility(v.co, v.normal), HUE)
                         for v in me.vertices])

# ---------------------------------------------------------------- leaf meshes per LOD
members_of = {}
for k, c in enumerate(cards):
    members_of.setdefault(c[5], []).append(k)


def subset(lod):
    if lod == 0:
        return list(range(len(cards)))
    want = (TRI_BUDGET[lod] - len(barks[lod].data.polygons) - cores_tris[lod]) // 2 - 10
    want = int(want * LOD.get('card_frac', [1.0, 1.0, 1.0])[lod])
    picked = []
    for ci in range(len(clumps)):
        members = members_of.get(ci, [])
        if not members:
            continue
        n = max(1, int(round(len(members) * want / len(cards))))
        pool = sorted(members, key=lambda k: -(2 * card_view[k] + vis_card[k]))[:max(n, int(len(members) * LOD['keep'][lod]))]
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
        u0, v0, cs_ = common.cell_uv(card[4])
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + cs_ * du, v0 + cs_ * dv)
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


def image(name, colorspace):
    img = bpy.data.images.load(common.shared_path(name))
    img.colorspace_settings.name = colorspace
    return img


def material(name, base, normal, roughness, alpha=False, normal_strength=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = image(base, 'sRGB')
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(normal, 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nm.inputs['Strength'].default_value = normal_strength
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    if alpha:
        m.use_backface_culling = False
        m.surface_render_method = 'DITHERED'
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tb.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
    return m


bark_mat = material('Bark', 'bark_basecolor.png', 'bark_normal.png', 0.92, normal_strength=1.0)
leaf_mat = material('Leaves', 'leaves_basecolor.png', 'leaves_normal.png', 0.85, alpha=True)
bark_mat['openyamm_wind'] = BARK['wind']
leaf_mat['openyamm_wind'] = spec['leaves']['wind']
leaf_mat['openyamm_translucency'] = 0.35
if SHELL:
    shell_mat = bpy.data.materials.new('Shell'); shell_mat.use_nodes = True
    sb = next(n for n in shell_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    st = shell_mat.node_tree.nodes.new('ShaderNodeTexImage')
    st.image = next(n for n in leaf_mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image.name.startswith('leaves_base')).image
    st.image.alpha_mode = 'CHANNEL_PACKED'
    shell_mat.node_tree.links.new(st.outputs['Color'], sb.inputs['Base Color'])
    sb.inputs['Roughness'].default_value = 0.9
    sb.inputs['Metallic'].default_value = 0.0
    shell_mat['openyamm_wind'] = spec['leaves']['wind']; shell_mat['openyamm_specular'] = 0.1
names = {0: 'Tree', 1: 'Tree_LOD1', 2: 'Tree_LOD2'}
for lod in (0, 1, 2):
    b, l = barks[lod], leaves[lod]
    b.data.materials.append(bark_mat); l.data.materials.append(leaf_mat)
    parts = (b, l)
    if SHELL:
        so = bpy.data.objects.new(f'shell{lod}', shells[lod]); bpy.context.scene.collection.objects.link(so)
        so.data.materials.append(shell_mat); parts = parts + (so,)
    for x in bpy.data.objects:
        x.select_set(x in parts)
    bpy.context.view_layer.objects.active = b
    bpy.ops.object.join()
    b.name = names[lod]; b.data.name = names[lod]
    print('LOD', lod, names[lod], 'tris', len(b.data.polygons), 'colour attrs', list(b.data.color_attributes.keys()))
clump_data = []
cards, card_sky = full['cards'], full['card_sky']
all_members = {}
for k, card in enumerate(cards):
    all_members.setdefault(card[5], []).append(k)
for ci, (c, r, inner_) in enumerate(clumps):
    members = all_members.get(ci, [])
    clump_data.append({'centre': list(map(float, c)), 'radius': float(r), 'inner': bool(inner_),
                       'tint': (LEAF_TINT * clump_tint[ci]).round(5).tolist(),
                       'sky': float(np.mean([card_sky[k] for k in members])) if members else 1.0,
                       'cards': [{'corners': [list(map(float, q)) for q in card_corners(cards[k], 1.0)],
                                  'local': [float(local_term(q, ci)) for q in card_corners(cards[k], 1.0)],
                                  'normals': [list(map(float, shading_normal(q, ci)))
                                              for q in card_corners(cards[k], 1.0)],
                                  'cell': int(cards[k][4])} for k in members]})
json.dump({'clumps': clump_data, 'tone': TONE, 'hue': HUE.tolist()}, open(os.path.join(OUT, 'clumps.json'), 'w'))
json.dump({'limbs': [{'level': l['level'], 'pts': [list(map(float, p)) for p in l['pts']], 'rads': l['rads']}
                     for l in limbs]}, open(os.path.join(OUT, 'skeleton.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'tree.blend'))
