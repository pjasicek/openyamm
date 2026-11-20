"""Blender: build one MM7 plant's three LOD meshes and export work/<id>_export.glb (+ work/<id>.blend for the review).
Objects <Base>, <Base>_LOD1, <Base>_LOD2 (linked by finish.py). Heights in metres = binding height / 81.7.
  bush03     fern clump: arching frond cards
  bush10     small saguaro: ribbed trunk, two arms           bush11  tall pale column with spine fringe cards
  bush13     candelabra: ribbed trunk, three arms             bush16  prickly-pear clump (pad lenses)
  bush12     Joshua tree: forked trunk, spiky rosettes of crossed star cards
  bush02     broad-leaved plant (dieffenbachia): stems, petioles, folded leaf blades
  plant01a/01b/07b/04b   amphorae (one lathe family with handles) with sprays, dry fronds, dry grass, wilting leaves
  plant11a/02a           terracotta pots on saucers with a small tree / palm fronds
  plant03b               square marble planter with hanging dry fronds
Usage: blender --background --python build_model.py -- <id>"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plants_lib as pl
import common
from common import CELLS

SID = sys.argv[sys.argv.index('--') + 1]
pl.sl.reset()
H = common.height_m(SID)
BODY = {'openyamm_specular': 0.2}


def foliage_extras(wind):
    return {'openyamm_wind': wind, 'openyamm_specular': 0.1, 'openyamm_translucency': 0.3}


def lod_objects(build, plans, base='Plant', occlusion=None):
    objects = []
    top0 = 0.0
    for lod, plan in enumerate(plans):
        g = pl.Geo()
        build(g, lod, plan)
        for i, v in enumerate(g.v):                 # nothing below the ground
            if v.z < 0:
                g.v[i] = Vector((v.x, v.y, 0.0))
        top = max(v.z for v in g.v)
        if lod == 0:
            top0 = top
        elif top > top0:                             # the engine scales by LOD0's height: no level may rise above it
            for i, v in enumerate(g.v):
                g.v[i] = Vector((v.x, v.y, v.z * top0 / top))
        if occlusion:
            g.occlusion(**occlusion)
        name = base if lod == 0 else f'{base}_LOD{lod}'
        objects.append(g.to_object(name, MATERIALS))
        print('LOD', name, 'triangles', g.triangles())
    return objects


def subset(n, fraction, rng_seed):
    """A seeded subset of range(n) (the same order at every level, so coarser levels keep a prefix)."""
    order = list(np.random.default_rng(rng_seed).permutation(n))
    return sorted(order[:max(1, int(round(n * fraction)))])


# =========================================================================== bush03 fern
def build_fern():
    """bush03 (revision 2): a rounded mound of arching fronds. Every frond is a quadratic Bézier from a small ring at
    the base to a tip on a dome shell (horizontal radius 0.52 H, height H, the sprite's w/h 1.04), its control point
    raised above the chord so the frond arches and arrives moving outward and a little down: the outline is a dome of
    frond backs rather than a crown of upright tips. Frond cards are 1:3 of the `fern_a` strip, facing outward."""
    global MATERIALS
    MATERIALS = [pl.material('Fronds', 'fronds', cutout=True, roughness=0.7, extras=foliage_extras(0.03),
                             extension='EXTEND')]
    rng = np.random.default_rng(304)
    fronds = []
    N = 64
    for i in range(N):
        az = i * 2.39996 + rng.normal(0, 0.12)
        out = Vector((math.cos(az), math.sin(az), 0))
        phi = math.radians(10 + 86 * ((i + 0.5) / N) ** 0.6 + rng.normal(0, 4))     # 0 = up .. 96 deg = on the ground
        tip = out * (0.52 * H * max(math.sin(phi), 0.38)) + Vector((0, 0, max(0.97 * H * math.cos(phi) + 0.04 * H,
                                                                             0.03 * H)))
        tip = tip * rng.uniform(0.9, 1.0)
        start = out * 0.12 * H + Vector((0, 0, 0.004))
        chord = tip - start
        # control point: above the chord's middle and pulled toward the axis, so the frond rises, then arches out
        ctrl = start + chord * 0.45 + Vector((0, 0, chord.length * rng.uniform(0.22, 0.32))) - out * 0.05 * H * math.cos(phi)
        side = Vector((0, 0, 1)).cross(out).normalized()
        L = sum(((b - a).length for a, b in zip(pl.bezier([start, ctrl, tip], 8), pl.bezier([start, ctrl, tip], 8)[1:])))
        fronds.append(dict(ctrl=[start, ctrl, tip], L=L, side=side, roll=rng.normal(0, 0.3),
                           shade=0.8 + 0.2 * math.sin(phi)))
    centre = Vector((0, 0, H * 0.3))

    def normal_fn(q, cn):
        radial = (q - centre).normalized()
        return (radial * 0.7 + cn * 0.3 + Vector((0, 0, 0.25))).normalized()

    def build(g, lod, plan):
        frac, segs, grow = plan
        for i in subset(N, frac, 3041):
            f = fronds[i]
            pts = pl.bezier(f['ctrl'], segs)
            pl.strip(g, pts, f['side'], f['L'] * 0.33 * grow, CELLS['fern_a'], 0,
                     occ_fn=lambda q, t, f=f: min(1.0, (0.42 + 0.58 * pl.smooth(q.z / (H * 0.65))) * (0.75 + 0.25 * t)
                                                  * (1.0, 1.1, 1.1)[lod]),
                     normal_fn=normal_fn, roll=f['roll'])
    return lod_objects(build, [(1.0, 3, 1.0), (0.62, 2, 1.18), (0.38, 2, 1.36)])


# =========================================================================== ribbed cacti
def ribbed_limb(g, ctrl, r0, r1, rings, plan, phase, occ, vscale, swell=0.06, cap=True, li=0, rib_v=None,
                depth=0.12, crest_round=0.35, dome=0.8):
    """One ribbed limb along a Bézier with a rounded cap (succ_lib.ribbed)."""
    pts = pl.bezier(ctrl, rings)
    radii = [(r0 + (r1 - r0) * i / rings) * (1 + swell * math.sin(2.3 * li + 7.0 * i / rings)) for i in range(rings + 1)]
    if cap:
        tip = pts[-1]; d = (pts[-1] - pts[-2]).normalized()
        # a rounded dome of height dome x r1
        angles = (35, 62, 80) if plan['caps'] == 2 else (50, 75)
        for a in angles:
            a = math.radians(a)
            pts.append(tip + d * r1 * dome * math.sin(a)); radii.append(r1 * math.cos(a))
        pts.append(tip + d * r1 * dome); radii.append(0.0)
    return pl.ribbed(g, pts, radii, plan['ribs'], depth, plan['vpr'], vscale, mat=0, occ=occ, u_rib=plan['u_rib'],
                     phase=phase, rib_v=rib_v, crest_round=crest_round)


def spine_fringe(g, crest, tile, length, mat, occ_fn, keep=1.0, seed=0, z_range=(0.0, 1e9)):
    """Spine cards along each rib crest (crest data from succ_lib.ribbed: per ring, per rib (point, outward)): the
    crest polyline is resampled every `tile` metres and each piece gets one card in the plane of the crest and its
    outward direction, u = 0 on the crest (the ring spacing does not stretch the spines)."""
    rng = np.random.default_rng(seed)
    ribs = len(crest[0])
    for k in range(ribs):
        pts = [ring[k] for ring in crest if len(ring) == ribs]
        lengths = [0.0]
        for a, b in zip(pts, pts[1:]):
            lengths.append(lengths[-1] + (b[0] - a[0]).length)

        def at(s):
            i = max(0, min(len(pts) - 2, next((j for j in range(len(lengths) - 1) if lengths[j + 1] >= s),
                                              len(pts) - 2)))
            f = (s - lengths[i]) / max(lengths[i + 1] - lengths[i], 1e-9)
            return pts[i][0].lerp(pts[i + 1][0], f), pts[i][1].lerp(pts[i + 1][1], f).normalized()
        s0 = rng.uniform(0, tile * 0.5)
        while s0 + tile <= lengths[-1]:
            (p0, d0), (p1, d1) = at(s0), at(s0 + tile)
            s0 += tile
            if not (z_range[0] <= p0.z <= z_range[1]) or rng.uniform() > keep:
                continue
            out = (d0 + d1).normalized()
            L = length * rng.uniform(0.8, 1.2)
            q0, q1 = p0 + out * (L * 0.5 - 0.004), p1 + out * (L * 0.5 - 0.004)
            pl.strip(g, [q0, q1], out, L, (0.0, 0.0, 1.0, 1.0), mat, occ_fn=occ_fn,
                     normal_fn=lambda q, cn, out=out: (out + cn * 0.3).normalized())


def build_bush10():
    """bush10: squat saguaro: a fat 12-rib trunk (radius 0.175 H) with a domed top, a thin left arm from 0.58 H to
    0.81 H and a thicker right arm from 0.36 H to 0.61 H (bush10_skin tile = one rib x 0.24 m). Revision 2 adds a
    sparse rim of black spine cards (bush10_spines, one per 0.24 m of crest) on LOD0 and, every second one, LOD1."""
    global MATERIALS
    MATERIALS = [pl.material('Body', 'bush10_skin', roughness=0.5, extras=BODY),
                 pl.material('Spines', 'bush10_spines', cutout=True, roughness=0.6,
                             extras={'openyamm_specular': 0.1}, extension='EXTEND')]
    R = 0.175 * H
    limbs = [  # control points (fractions of H), base radius, tip radius, rings, ribs
        (((0, 0, 0), (0, 0, 0.5), (0, 0, 1.0 - 0.165 * 0.75)), R * 0.97, R * 1.02, 5, 12, 0.0),
        (((-0.08, 0.02, 0.58), (-0.28, 0.03, 0.56), (-0.26, 0.04, 0.81 - 0.045)), 0.06 * H, 0.058 * H, 5, 8, 0.2),
        (((0.10, -0.02, 0.36), (0.33, -0.04, 0.36), (0.31, -0.05, 0.61 - 0.06)), 0.072 * H, 0.07 * H, 5, 8, 0.5),
    ]
    plans = [dict(vpr=2, ring=1.0, caps=2, ribs=1.0, u_rib=1, gain=0.95, spines=1.0),
             dict(vpr=1, ring=0.6, caps=1, ribs=1.0, u_rib=1, gain=0.85, spines=0.5),
             dict(vpr=1, ring=0.4, caps=1, ribs=0.6, u_rib=1 / 0.6, gain=0.82, spines=0.0)]

    def build(g, lod, plan):
        for li, (ctrl, r0, r1, n, ribs, phase) in enumerate(limbs):
            ctrl = [Vector(c) * H for c in ctrl]
            p = dict(plan, ribs=max(5, int(round(ribs * plan['ribs']))))
            p['u_rib'] = ribs / p['ribs']

            def occ(q, i, valley):
                return (0.5 + 0.5 * pl.smooth(q.z / (0.6 * H))) * (0.7 if valley else 1.0) * plan['gain']
            crest = ribbed_limb(g, ctrl, r0, r1, max(2, int(round(n * plan['ring']))), p, phase, occ, 1 / 0.24,
                                li=li, rib_v=[0.5 * (k % 2) for k in range(p['ribs'])], depth=0.10)
            if plan['spines']:
                spine_fringe(g, crest, 0.24, 0.05 * H * (1.25 if lod else 1.0), 1,
                             lambda q, t: 0.6 + 0.4 * pl.smooth(q.z / (0.6 * H)), keep=plan['spines'] * 0.8,
                             seed=1001 + li, z_range=(0.08 * H, 0.98 * H))
    return lod_objects(build, plans, 'Cactus', occlusion=dict(rays=24, distance=0.5, strength=0.5))


def build_bush11():
    """bush11: one tall pale column (16 shallow ribs, radius 0.135 H, narrower foot, slight lean) under a fringe of
    long spine cards on every crest (one bush11_spines tile = 0.24 m per card)."""
    global MATERIALS
    MATERIALS = [pl.material('Body', 'bush11_skin', roughness=0.55, extras=BODY),
                 pl.material('Spines', 'bush11_spines', cutout=True, roughness=0.6,
                             extras={'openyamm_specular': 0.1}, extension='EXTEND')]
    R = 0.142 * H
    rng = np.random.default_rng(1101)
    plans = [dict(vpr=2, rings=7, ribs=16, fringe=1.0, caps=2), dict(vpr=1, rings=6, ribs=12, fringe=0.5, caps=1),
             dict(vpr=1, rings=4, ribs=8, fringe=0.0, caps=1)]
    tile = 0.24
    fringe_cards = []
    for k in range(16):
        for j in range(int((0.86 * H) / tile)):
            fringe_cards.append((k, 0.10 * H + j * tile + rng.uniform(-0.03, 0.03), rng.uniform(0.85, 1.15)))

    def build(g, lod, plan):
        top = 0.86 * H
        zs = [top * i / plan['rings'] for i in range(plan['rings'] + 1)]
        centres = [Vector((0.02 * H * (z / top) ** 2, 0, z)) for z in zs]
        radii = [R * (0.72 + 0.28 * pl.smooth(z / (0.45 * H))) * (1 - 0.06 * pl.smooth((z - 0.55 * H) / (0.3 * H)))
                 for z in zs]
        caps = [(0.06, 0.92), (0.11, 0.62)] if plan['caps'] == 2 else [(0.09, 0.78)]
        tip = centres[-1]
        for f, rf in caps:
            centres.append(tip + Vector((0, 0, f * H))); radii.append(R * rf)
        centres.append(tip + Vector((0.01 * H, 0, 0.14 * H))); radii.append(0.0)
        u_rib = 16 / plan['ribs']

        def occ(q, i, valley):
            return (0.55 + 0.45 * pl.smooth(q.z / (0.5 * H))) * (0.75 if valley else 1.0) * (0.95, 0.88, 0.86)[lod]
        pl.ribbed(g, centres, radii, plan['ribs'], 0.08, plan['vpr'], 1 / 0.24, mat=0, occ=occ, u_rib=u_rib,
                  phase=0.0, rib_v=[0.5 * (k % 2) for k in range(plan['ribs'])])
        # spine fringes: a card per crest per tile, outward from the crest, its plane through the column axis
        keep = subset(len(fringe_cards), plan['fringe'], 1102) if plan['fringe'] else []
        for ci in keep:
            k, z, s = fringe_cards[ci]
            ang = 2 * math.pi * (k + 0.5) / 16
            out = Vector((math.cos(ang), math.sin(ang), 0))
            rz = R * (0.72 + 0.28 * pl.smooth(z / (0.45 * H))) * (1 - 0.06 * pl.smooth((z - 0.55 * H) / (0.3 * H)))
            base = Vector((0.02 * H * (z / top) ** 2, 0, z)) + out * (rz * 0.97)
            L = 0.09 * H * s * (1.4 if lod else 1.0)
            pts = [base, base + Vector((0, 0, tile))]
            # card: u = 0 on the crest -> 1 outward; v along the crest. Built as a strip whose spine runs along the
            # crest and whose width runs outward (u across), so the texture's crest edge sits on the body
            q0 = base + out * (L * 0.5)
            pl.strip(g, [q0, q0 + Vector((0, 0, tile))], out, L, (0.0, 0.0, 1.0, 1.0), 1,
                     occ_fn=lambda q, t: 0.6 + 0.4 * pl.smooth(q.z / (0.5 * H)),
                     normal_fn=lambda q, cn, out=out: (out + cn * 0.3).normalized())
    return lod_objects(build, plans, 'Cactus', occlusion=dict(rays=24, distance=0.4, strength=0.4))


def build_bush13():
    """bush13: candelabra: a 7-rib trunk (radius 0.085 H, deep ribs, pale crests) to the top, a short left arm,
    a front arm and a right arm rising from 0.42-0.5 H to 0.66-0.74 H."""
    global MATERIALS
    MATERIALS = [pl.material('Body', 'bush13_skin', roughness=0.45, extras=BODY)]
    R = 0.085 * H
    limbs = [
        (((0, 0, 0), (0.005, 0, 0.5), (0, 0, 1.0 - 0.06)), R * 1.0, R * 0.92, 8, 7, 0.0, 0.03),
        (((-0.04, 0.02, 0.50), (-0.15, 0.03, 0.50), (-0.145, 0.03, 0.66 - 0.03)), 0.042 * H, 0.04 * H, 5, 6, 0.3, 0.05),
        (((0.02, -0.05, 0.42), (0.06, -0.13, 0.43), (0.055, -0.12, 0.72 - 0.035)), 0.048 * H, 0.046 * H, 6, 6, 0.6, 0.05),
        (((0.05, 0.01, 0.50), (0.16, 0.0, 0.50), (0.155, 0.0, 0.74 - 0.03)), 0.04 * H, 0.038 * H, 5, 6, 0.1, 0.05),
    ]
    plans = [dict(vpr=2, ring=1.0, caps=2, rf=1.0, gain=0.95), dict(vpr=2, ring=0.55, caps=1, rf=1.0, gain=0.95),
             dict(vpr=1, ring=0.35, caps=1, rf=1.0, gain=0.8)]

    def build(g, lod, plan):
        for li, (ctrl, r0, r1, n, ribs, phase, sw) in enumerate(limbs):
            ctrl = [Vector(c) * H for c in ctrl]
            p = dict(plan, ribs=ribs, u_rib=1)

            def occ(q, i, valley):
                return (0.5 + 0.5 * pl.smooth(q.z / (0.5 * H))) * (0.55 if valley else 1.0) * plan['gain']
            ribbed_limb(g, ctrl, r0, r1, max(2, int(round(n * plan['ring']))), p, phase, occ, 1 / 0.32, swell=sw,
                        li=li, depth=0.30, crest_round=0.3)
    return lod_objects(build, plans, 'Cactus', occlusion=dict(rays=24, distance=0.6, strength=0.5))


# =========================================================================== bush16 prickly pear
def grow_pads(st, rng):
    """Pad chains (as the MM6 succulents' grow_pads): roots round an elliptical footprint, each pad carrying 0-2
    children on its upper rim, mostly upright, turned in the parent's plane and twisted about their long axis."""
    pads, queue = [], []
    for r in range(st['roots']):
        ang = rng.uniform(0, 2 * math.pi); rad = math.sqrt(rng.uniform(0.05, 1.0))
        base = Vector((math.cos(ang) * st['foot'][0] * rad + st['shift'], math.sin(ang) * st['foot'][1] * rad, 0.0))
        out = Vector((math.cos(ang), math.sin(ang), 0))
        lean = rng.uniform(*st['root_lean']) * (0.4 + 0.6 * rad)
        up = (Vector((0, 0, 1)) * math.cos(lean) + out * math.sin(lean)).normalized()
        normal = pl.rotate(out, up, rng.normal(0, 0.7))
        queue.append((base, up, normal, 1.0, 0))
    while queue:
        attach, up, normal, scale, depth = queue.pop(0)
        f = scale * (1 + rng.normal(0, st['size_jitter']))
        w, h = st['size'][0] * f, st['size'][1] * f
        normal = (normal - up * normal.dot(up)).normalized()
        pads.append(dict(attach=attach, up=up, normal=normal, w=w, h=h, cell=int(rng.integers(4)), depth=depth))
        if depth + 1 >= st['depth']:
            continue
        n = int(rng.choice(len(st['children']), p=st['children']))
        right = up.cross(normal).normalized()
        for c in range(n):
            off = rng.uniform(-st['offset'], st['offset'])
            t = math.acos(max(min(off, 1), -1))
            rim = attach + up * (h * 0.5) + (right * math.cos(t) * w * 0.5 + up * math.sin(t) * h * 0.5) * 0.85
            cu = pl.rotate(up, normal, -off * st['spread'] * 1.6 + rng.normal(0, st['spread'] * 0.4))
            if cu.z < 0.5:
                cu = (cu + Vector((0, 0, 0.8))).normalized()
            cn = pl.rotate(normal, cu, rng.normal(0, st['twist']))
            queue.append((rim - cu * 0.02, cu, cn, scale * st['decay'], depth + 1))
    return pads


def build_bush16():
    """bush16: an upright prickly-pear clump: a tall left mass and a right column of stacked pads (w/h 0.81)."""
    global MATERIALS
    MATERIALS = [pl.material('Pads', 'pads_bush16', cutout=True, roughness=0.45, extension='EXTEND',
                             extras={'openyamm_specular': 0.2})]
    st = dict(roots=9, foot=(0.34, 0.2), shift=-0.02, root_lean=(0.0, 0.25), size=(0.20, 0.30), size_jitter=0.12,
              decay=0.93, children=[0.15, 0.6, 0.25], spread=0.30, twist=0.9, depth=5, offset=0.55)
    rng = np.random.default_rng(1616)
    pads = grow_pads(st, rng)
    tops = [(p['attach'] + p['up'] * p['h']).z for p in pads]
    k = H / max(tops)
    for p in pads:
        p['attach'] = p['attach'] * k; p['w'] *= k; p['h'] *= k
    xs = [p['attach'].x + s * p['w'] * 0.5 for p in pads for s in (-1, 1)]
    print('PADS', len(pads), 'w/h', round((max(xs) - min(xs)) / H, 2), 'sprite 0.81')
    order = sorted(range(len(pads)), key=lambda i: (pads[i]['depth'], -pads[i]['w']))
    ovals = [(0.33, 0.45), (0.36, 0.44), (0.30, 0.45), (0.35, 0.43)]
    plans = [(3, 1.0, 1.0), (3, 0.82, 1.07), (2, 0.8, 1.1)]

    # revision 2: every pad bends (cupped along its length) and twists a little, and its width/height ratio varies,
    # so the pads read as fleshy, uneven pads rather than identical lenses
    prng = np.random.default_rng(1617)
    for p in pads:
        p['bend'] = prng.uniform(-0.3, 0.3); p['twist'] = prng.uniform(-0.2, 0.2)
        p['w'] *= prng.uniform(0.85, 1.15)

    def build(g, lod, plan):
        grid, keep, grow = plan
        for i in order[:int(round(len(pads) * keep))]:
            p = pads[i]
            first = len(g.v)
            w, h = p['w'] * grow, p['h'] * grow
            centre, right = pl.pad(g, p['attach'], p['up'], p['normal'], w, h, p['cell'], ovals[p['cell']],
                                   grid, 0.065 * p['w'], occ_fn=lambda q: 0.5 + 0.5 * pl.smooth(q.z / (H * 0.55)))
            up = p['up'].normalized(); nrm = right.cross(up).normalized()
            if grid > 2:
                for vi in range(first, len(g.v)):
                    q = g.v[vi] - centre
                    ly, lx = q.dot(up) / (h * 0.5), q.dot(right) / (w * 0.5)
                    g.v[vi] = g.v[vi] + nrm * (p['bend'] * h * 0.5 * ly * ly + p['twist'] * w * 0.5 * lx * ly)
    return lod_objects(build, plans, 'Cactus', occlusion=dict(rays=24, distance=0.35, strength=0.55))


# =========================================================================== bush12 Joshua tree
def build_bush12():
    """bush12: a Joshua tree traced from the sprite (512 px = H): a shaggy trunk forking at 0.4 H into a left
    branch (two rosettes), a front branch, a middle branch and a right branch, each ending in a spiky rosette of
    crossed star cards ('burst'; a few upward half-stars below)."""
    global MATERIALS
    wind = 0.03
    MATERIALS = [pl.material('Bark', 'joshbark', roughness=0.85, extras={'openyamm_wind': wind,
                                                                         'openyamm_specular': 0.1}),
                 pl.material('Leaves', 'joshua', cutout=True, roughness=0.6, extension='EXTEND',
                             extras=foliage_extras(wind))]

    def P(px, py, y=0.0):
        return Vector(((px - 255) / 512 * H, y * H, (512 - py) / 512 * H))
    # branches: control points (sprite px, depth fraction), base radius, tip radius (fractions of H)
    branches = [
        ([P(255, 512), P(258, 420), P(262, 300)], 0.062, 0.048),                                  # trunk
        ([P(255, 320), P(230, 200, 0.02), P(140, 95, 0.06)], 0.042, 0.030),                       # left up
        ([P(205, 190, 0.03), P(130, 180, 0.08), P(75, 215, 0.10)], 0.026, 0.020),                 # left low
        ([P(250, 330), P(225, 290, -0.10), P(180, 230, -0.16)], 0.030, 0.024),                    # front
        ([P(268, 310), P(285, 220, 0.12), P(295, 135, 0.16)], 0.034, 0.026),                      # middle
        ([P(266, 300), P(300, 180, -0.02), P(405, 150, -0.04)], 0.040, 0.030),                    # right
    ]
    rosettes = [(P(132, 78, 0.06), 190), (P(68, 215, 0.10), 170), (P(178, 228, -0.16), 190),
                (P(296, 118, 0.16), 145), (P(425, 138, -0.04), 170)]
    rng = np.random.default_rng(1212)
    plans = [dict(sides=8, rings=6, cards=12, halves=4), dict(sides=6, rings=3, cards=7, halves=2),
             dict(sides=4, rings=2, cards=4, halves=0)]

    def build(g, lod, plan):
        r2 = np.random.default_rng(1213)
        for bi, (ctrl, r0, r1) in enumerate(branches):
            n = plan['rings'] + (2 if bi == 0 else 0)
            pts = pl.bezier(ctrl, n)
            radii = [(r0 + (r1 - r0) * i / n) * H * (1.25 if bi == 0 and i == 0 else 1.0) for i in range(n + 1)]
            pl.tube(g, pts, radii, plan['sides'], mat=0, tile=(1.0, 1.0), cap=bi > 0,
                    occ_fn=lambda q: 0.55 + 0.45 * pl.smooth(q.z / (0.6 * H)), phase=0.3 * bi)
        for ri, (c, px) in enumerate(rosettes):
            size = px / 512 * H * 1.12 * (1 + 0.12 * lod)
            pl.crossed(g, c, size, CELLS['burst'], plan['cards'], r2, mat=1,
                       occ_fn=lambda q, c=c: 0.62 + 0.38 * max(0.0, min(1.0, 0.5 + (q - c).z / (0.6 * size))))
            for k in range(plan['halves']):
                a = 2 * math.pi * k / max(plan['halves'], 1) + ri
                out = Vector((math.cos(a), math.sin(a), 0))
                side = Vector((0, 0, 1)).cross(out).normalized()
                pl.card(g, c - Vector((0, 0, size * 0.42)) + out * size * 0.05, side * size * 0.8,
                        (Vector((0, 0, 1)) * 0.7 + out * 0.3).normalized() * size * 0.55,
                        CELLS['half'], lambda q, out=out: (out + Vector((0, 0, 0.3))).normalized(),
                        lambda q: 0.6, mat=1)
    return lod_objects(build, plans, 'Plant', occlusion=dict(rays=20, distance=0.6, strength=0.45))


# =========================================================================== bush02 broad-leaved plant
def leaf_blade(g, start, direction, length, width, droop, cell, segs, across, mat, occ_fn, centre, roll=0.0,
               fold=0.18):
    pts = pl.bent_spine(start, direction, length, segs, droop)
    d = Vector(direction).normalized()
    side = Vector((0, 0, 1)).cross(d)
    side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))

    def normal_fn(q, cn):
        return (cn * 0.6 + (q - centre).normalized() * 0.4).normalized()
    pl.strip(g, pts, side, width, CELLS[cell], mat, occ_fn=occ_fn, normal_fn=normal_fn, across=across,
             fold=fold if across == 2 else 0.0, roll=roll)


def build_bush02():
    """bush02: dieffenbachia: a short central stalk (to 0.3 H) with ~24 large leaves on petioles: pale variegated
    leaves spreading and drooping low and in the middle, dark leaves raised at the top (w/h 1.07)."""
    global MATERIALS
    wind = 0.03
    MATERIALS = [pl.material('Leaves', 'leaves', cutout=True, roughness=0.55, extension='EXTEND',
                             extras=foliage_extras(wind))]
    rng = np.random.default_rng(202)
    stem = [Vector((0.0, 0, 0)), Vector((0.01, 0, 0.18 * H)), Vector((0.02, 0.01, 0.36 * H))]
    sp = pl.bezier(stem, 10)
    leaves = []
    N = 24
    for i in range(N):
        t = i / (N - 1)                                   # 0 low .. 1 top
        a = sp[min(10, int(4 + t * 6))]
        az = i * 2.39996 + rng.normal(0, 0.2)
        dark = t > 0.55 and rng.uniform() < 0.8 or rng.uniform() < 0.1
        el = math.radians((35 + 35 * t if dark else -5 + 45 * t) + rng.normal(0, 8))
        d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        L = H * rng.uniform(0.36, 0.45) * (1.05 if dark else 1.0)
        leaves.append(dict(a=a, d=d, L=L, W=L * 0.36, droop=(0.9 - 0.7 * t) * rng.uniform(0.7, 1.2),
                           cell='leaf_dark' if dark else 'leaf_var', pet=H * rng.uniform(0.06, 0.14),
                           roll=rng.normal(0, 0.25)))
    centre = Vector((0, 0, 0.45 * H))
    plans = [(1.0, 4, 2, 4), (0.8, 2, 2, 3), (0.6, 2, 2, 3)]

    def build(g, lod, plan):
        frac, segs, across, sides = plan
        pts = pl.bezier(stem, 3 if lod == 0 else 2)
        pl.tube(g, pts, [0.022 * H * (1 - 0.4 * i / (len(pts) - 1)) for i in range(len(pts))], sides, mat=0,
                rect=CELLS['stem_green'], occ_fn=lambda q: 0.5, solid=False)
        grow = 1.0 / frac ** 0.5
        for i in subset(N, frac, 2021):
            f = leaves[i]
            pet_end = f['a'] + f['d'] * f['pet']
            if lod < 2:
                pl.tube(g, [f['a'], pet_end], [0.008 * H, 0.006 * H], 3, mat=0, rect=CELLS['stem_green'],
                        occ_fn=lambda q: 0.6, solid=False)
            leaf_blade(g, pet_end, f['d'], f['L'] * grow ** 0.5, f['W'] * grow, f['droop'],
                       f['cell'], segs, across, 0,
                       lambda q, t: (0.45 + 0.55 * pl.smooth(q.z / (0.8 * H))) * (0.85 + 0.15 * t), centre,
                       roll=f['roll'])
    return lod_objects(build, plans, 'Plant')


# =========================================================================== pots
def amphora_profile(h, base, belly, belly_z, neck, neck_z, lip, lip_h=0.05, wall=0.04, soil=0.9, n=6):
    """Outside from the foot up over the lip and down the inner wall to the soil disc (r 0 at soil x h). The
    rounded belly is sampled with n points below and n above its widest ring (fewer on coarse levels)."""
    pr = [(base * 0.92, 0.0), (base, 0.02)]
    for i in range(1, n + 1):                                # foot -> belly: a rounded bottom
        t = i / n
        pr.append((base + (belly - base) * math.sin(math.pi / 2 * t) ** 0.55, 0.02 + (belly_z - 0.02) * t))
    for i in range(1, n + 1):                                # belly -> neck: shoulder easing into the neck
        t = i / n
        pr.append((neck + (belly - neck) * math.cos(math.pi / 2 * t) ** 1.1, belly_z + (neck_z - belly_z) * t))
    pr += [(neck * 1.02, neck_z + (1 - lip_h - neck_z) * 0.6), (lip, 1 - lip_h), (lip * 1.02, 1 - lip_h * 0.4),
           (lip * 0.97, 1.0), (lip - wall * 1.5, 1.0), (lip - wall * 2.2, soil + 0.02), (0.0, soil)]
    return [(r * h, z * h) for r, z in pr]


def pot_vcoords(profile, v_top=0.08):
    """v per profile point: 0.08 (below the soil swatch) at the lip, growing down the outside by profile length."""
    lengths = [0.0]
    for a, b in zip(profile, profile[1:]):
        lengths.append(lengths[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    lip = max(range(len(profile)), key=lambda k: profile[k][1] - 1e-3 * k)
    lip_len = lengths[lip]
    out = []
    for k, L in enumerate(lengths):
        out.append(v_top + (lip_len - L) / max(lengths[lip], 1e-6) * 0.9)
    out[-1] = 0.03                                         # the soil disc centre samples the soil swatch
    out[-2] = min(out[-2], 0.05) if profile[-1][0] < 1e-6 else out[-2]
    return out


def handle(g, h, z0, z1, r_attach0, r_attach1, reach, thick, side, lod_sides, rings, mat, occ, lift=0.0):
    """A loop handle in the x-z plane on side +1/-1: from the shoulder (z0, radius r_attach0) out to `reach` and
    up to under the lip (z1, r_attach1)."""
    a = Vector((side * r_attach0 * 0.92, 0, z0 * h))
    b = Vector((side * reach * h, 0, (z0 + (z1 - z0) * 0.55) * h))
    c = Vector((side * reach * h * 1.02, 0, (z1 + lift) * h))
    d = Vector((side * r_attach1 * 0.92, 0, z1 * h))
    pts = pl.bezier([a, b, c, d], rings)
    pl.tube(g, pts, [thick * h] * len(pts), lod_sides, mat=mat, tile=(1.0, 0.6), occ_fn=occ)


POTS = {
    # amphora: (pot height / H, profile args, texture, u repeats, handles (z0, z1, reach, thickness, lift), spout)
    'plant01a': dict(kind='amphora', hf=0.37, args=dict(base=0.27, belly=0.46, belly_z=0.36, neck=0.27, neck_z=0.76,
                                                       lip=0.37, lip_h=0.06), tex='pot_gold', spec=0.45,
                     handles=(0.64, 0.92, 0.56, 0.035, 0.06), spout=False),
    'plant01b': dict(kind='amphora', hf=0.62, args=dict(base=0.25, belly=0.47, belly_z=0.33, neck=0.31, neck_z=0.80,
                                                       lip=0.34, lip_h=0.05), tex='pot_brass', spec=0.35,
                     handles=(0.62, 0.93, 0.56, 0.035, 0.03), spout=True),
    'plant07b': dict(kind='amphora', hf=0.58, args=dict(base=0.26, belly=0.50, belly_z=0.36, neck=0.33, neck_z=0.82,
                                                       lip=0.40, lip_h=0.05), tex='pot_patina', spec=0.25,
                     handles=(0.62, 0.95, 0.56, 0.03, 0.05), spout=False),
    'plant04b': dict(kind='amphora', hf=0.55, args=dict(base=0.24, belly=0.50, belly_z=0.38, neck=0.30, neck_z=0.84,
                                                       lip=0.34, lip_h=0.05), tex='pot_stone', spec=0.15,
                     handles=(0.70, 0.98, 0.52, 0.03, 0.12), spout=False),
    'plant11a': dict(kind='clay', hf=0.39, tex='pot_clay', spec=0.15),
    'plant02a': dict(kind='clay', hf=0.39, tex='pot_clay', spec=0.15),
    'plant03b': dict(kind='planter', hf=0.62, tex='pot_marble', spec=0.25),
}


def clay_profile(h):
    """Terracotta flower pot with a thick rolled rim on a separate saucer (fractions of the pot height)."""
    pr = [(0.33, 0.0), (0.35, 0.02), (0.35, 0.22), (0.33, 0.27), (0.30, 0.30), (0.29, 0.31), (0.31, 0.33),
          (0.42, 0.76), (0.43, 0.77), (0.56, 0.78), (0.58, 0.80), (0.58, 0.97), (0.56, 1.0), (0.49, 1.0),
          (0.47, 0.96), (0.0, 0.93)]
    return [(r * h, z * h) for r, z in pr]


def planter_profile(h):
    """Square planter (4 segments): plinth, a body widening upward, a lipped top slab (r = half the diagonal)."""
    k = math.sqrt(2)
    pr = [(0.33, 0.0), (0.33, 0.10), (0.27, 0.10), (0.27, 0.12), (0.40, 0.84), (0.47, 0.85), (0.47, 1.0),
          (0.40, 1.0), (0.0, 0.97)]
    return [(r * k * h, z * h) for r, z in pr]


def build_pot(g, lod, pot, h, mat, occ):
    # revision 2 reduction: 16 segments where the pot is under half the model's height (plant01a, 11a, 02a); the
    # big amphorae (01b, 07b, 04b) keep 20, since 16 showed in the surface-distance check
    big = pot['hf'] > 0.5
    segs = ([20, 12, 8] if big else [16, 12, 8])[lod] if pot['kind'] != 'planter' else 4
    if pot['kind'] == 'amphora':
        prof = amphora_profile(h, n=((5, 3, 2) if big else (4, 3, 2))[lod], **pot['args'])
        crease = {len(prof) - 4, len(prof) - 2}
    elif pot['kind'] == 'clay':
        prof = clay_profile(h)
        if lod == 2:
            prof = [p for i, p in enumerate(prof) if i not in (1, 4, 6, 9, 11)]
        crease = {2, 5, 8} if lod < 2 else set()
    else:
        prof = planter_profile(h)
        crease = set()
    pl.lathe(g, prof, segs, mat=mat, u_repeat=2.0 if segs > 4 else 1.0, vcoords=pot_vcoords(prof), occ_fn=occ,
             crease=crease, flat=pot['kind'] == 'planter', phase=math.pi / 4 if pot['kind'] == 'planter' else 0.0)
    if pot['kind'] == 'amphora':
        z0, z1, reach, thick, lift = pot['handles']
        args = pot['args']
        r_at = lambda z: next(r for r, zz in prof if zz >= z * h - 1e-6) if True else 0
        for side in (-1, 1):
            handle(g, h, z0, z1, r_at(z0), r_at(z1), reach, thick, side, ([6, 5, 4] if big else [5, 4, 4])[lod],
                   ([8, 5, 3] if big else [6, 4, 3])[lod], mat, occ, lift)
        if pot['spout'] and lod < 2:
            a = Vector((0, -args['belly'] * 0.9 * h, 0.55 * h))
            pl.tube(g, [a, a + Vector((0, -0.12 * h, 0.12 * h)), a + Vector((0, -0.2 * h, 0.26 * h))],
                    [0.06 * h, 0.045 * h, 0.035 * h], [6, 4][lod], mat=mat, tile=(1.0, 0.6), occ_fn=occ)
    return prof


def build_potted():
    global MATERIALS
    pot = POTS[SID]
    wind = 0.02
    MATERIALS = [pl.material('Pot', pot['tex'], roughness=0.45 if pot['spec'] > 0.3 else 0.75,
                             extras={'openyamm_specular': pot['spec'], 'openyamm_wind': wind}),
                 pl.material('Leaves', 'fronds' if SID in ('plant01a', 'plant02a', 'plant01b', 'plant03b') else 'leaves',
                             cutout=True, roughness=0.65, extension='EXTEND', extras=foliage_extras(wind))]
    h = pot['hf'] * H
    rim_z = h * (0.97 if pot['kind'] != 'clay' else 0.93)
    rim_r = {'amphora': pot.get('args', {}).get('lip', 0.3) * h * 0.85, 'clay': 0.47 * h,
             'planter': 0.40 * h}[pot['kind']]
    rng = np.random.default_rng(sum(map(ord, SID)))
    prof = {'amphora': lambda: amphora_profile(h, **pot['args']), 'clay': lambda: clay_profile(h),
            'planter': lambda: planter_profile(h)}[pot['kind']]()
    pot_r = max(r for r, z in prof) * (0.75 if pot['kind'] == 'planter' else 1.0)
    plant = PLANTS[SID](rng, h, rim_z, rim_r, pot_r)
    plans = [0, 1, 2]

    def occ_pot(q):
        return 0.55 + 0.45 * pl.smooth(q.z / (0.6 * h))

    def build(g, lod, _):
        build_pot(g, lod, pot, h, 0, occ_pot)
        plant(g, lod)
    return lod_objects(build, plans, 'Plant', occlusion=dict(rays=24, distance=0.4 * h, strength=0.55))


def frond_spray(rng, rim_z, rim_r, count, cell, length, el_range, droop, width_f=0.25, spread=1.0, min_len=0.4):
    """Frond cards from the soil: each rising at an elevation in el_range, arching by droop."""
    fronds = []
    for i in range(count):
        az = i * 2.39996 + rng.normal(0, 0.2)
        el = math.radians(rng.uniform(*el_range))
        d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))).normalized()
        start = Vector((math.cos(az) * rim_r * 0.4 * spread, math.sin(az) * rim_r * 0.4 * spread, rim_z - 0.01))
        L = length * rng.uniform(min_len, 1.0)
        fronds.append(dict(start=start, d=d, L=L, W=L * width_f, droop=droop * rng.uniform(0.7, 1.3), cell=cell,
                           side=Vector((0, 0, 1)).cross(d).normalized(), roll=rng.normal(0, 0.3), gp=1.6))
    return fronds


def emit_fronds(g, fronds, lod, mat, z_ref, seed, keep=(1.0, 0.65, 0.4), segs=(4, 2, 2)):
    frac = keep[lod]; grow = 1.0 / math.sqrt(frac) ** 0.6
    centre = Vector((0, 0, z_ref))
    for i in subset(len(fronds), frac, seed):
        f = fronds[i]
        pts = pl.bent_spine(f['start'], f['d'], f['L'], segs[lod], f['droop'], gravity_power=f['gp'])
        pl.strip(g, pts, f['side'], f['W'] * grow, CELLS[f['cell']], mat,
                 occ_fn=lambda q, t: 0.6 + 0.4 * t,
                 normal_fn=lambda q, cn: ((q - centre).normalized() * 0.5 + cn * 0.5 + Vector((0, 0, 0.3))).normalized(),
                 roll=f['roll'])


def plant_01a(rng, h, rim_z, rim_r, pot_r):
    """Two tall leafy sprays to the top (the 'spray' strip), shorter sprays and palm fronds round them."""
    tall = H - rim_z
    fronds = frond_spray(rng, rim_z, rim_r, 9, 'spray', tall * 0.7, (55, 80), 0.3, width_f=0.26, min_len=0.5)
    for f in fronds[4:]:
        f['cell'] = 'palm'
    for f, d, L in ((fronds[0], (-0.28, 0.05, 1), 1.0), (fronds[1], (0.32, -0.05, 1), 0.97)):
        f['L'] = tall * L; f['d'] = Vector(d).normalized(); f['W'] = f['L'] * 0.24; f['droop'] = 0.12
        f['side'] = Vector((1, 0, 0)); f['roll'] = 0.3
    return lambda g, lod: emit_fronds(g, fronds, lod, 1, rim_z + tall * 0.4, 101, keep=(1.0, 0.7, 0.45))


def plant_02a(rng, h, rim_z, rim_r, pot_r):
    """A fan of upright palm fronds."""
    tall = H - rim_z
    fronds = frond_spray(rng, rim_z, rim_r, 12, 'palm', tall * 1.0, (66, 88), 0.25, width_f=0.28, min_len=0.55)
    fronds[0]['L'] = tall * 1.0; fronds[0]['d'] = Vector((0.1, 0, 1)).normalized(); fronds[0]['droop'] = 0.1
    return lambda g, lod: emit_fronds(g, fronds, lod, 1, rim_z + tall * 0.4, 102)


def plant_dry_fronds(rng, rim_z, rim_r, pot_r, count, rise, hang, front=0.0):
    """Withered fronds rising out of the mouth, turning over the rim and hanging down outside the pot (a cubic
    Bézier from the soil over a peak just outside the rim to a tip `hang` below the rim, clear of the belly
    `pot_r`). front biases them toward -y (the sprite's front). The card faces outward."""
    fronds = []
    for i in range(count):
        az = i * 2.39996 + rng.normal(0, 0.25)
        out = Vector((math.cos(az), math.sin(az) - front, 0)).normalized()
        r = rise * rng.uniform(0.7, 1.0)
        down = hang * rng.uniform(0.55, 1.0)
        a = out * rim_r * 0.3 + Vector((0, 0, rim_z - 0.02))
        ctrl = [a, a + Vector((0, 0, r * 0.9)) + out * rim_r * 0.3,
                out * (rim_r + 0.25 * r) + Vector((0, 0, rim_z + r * 0.6)),
                out * (pot_r * 1.12) + Vector((0, 0, rim_z - down))]
        L = sum((b - c).length for b, c in zip(pl.bezier(ctrl, 8), pl.bezier(ctrl, 8)[1:]))
        fronds.append(dict(ctrl=ctrl, W=min(L * 0.17, 0.7 * r), cell='dry', side=Vector((0, 0, 1)).cross(out),
                           roll=rng.normal(0, 0.25)))
    return fronds


def emit_hanging(g, fronds, lod, mat, centre, seed, keep=(1.0, 0.72, 0.58), segs=(6, 4, 3)):
    frac = keep[lod]; grow = 1.0 / math.sqrt(frac) ** 0.6
    for i in subset(len(fronds), frac, seed):
        f = fronds[i]
        pl.strip(g, pl.bezier(f['ctrl'], segs[lod]), f['side'], f['W'] * grow, CELLS[f['cell']], mat,
                 occ_fn=lambda q, t: 0.55 + 0.45 * (1 - t) ** 0.5,
                 normal_fn=lambda q, cn: ((q - centre).normalized() * 0.6 + cn * 0.4).normalized(), roll=f['roll'])


def plant_01b(rng, h, rim_z, rim_r, pot_r):
    tall = H - rim_z
    fronds = plant_dry_fronds(rng, rim_z, rim_r, pot_r, 7, tall * 1.4, h * 0.75, front=0.2)
    return lambda g, lod: emit_hanging(g, fronds, lod, 1, Vector((0, 0, rim_z)), 103)


def plant_03b(rng, h, rim_z, rim_r, pot_r):
    tall = H - rim_z
    fronds = plant_dry_fronds(rng, rim_z, rim_r, pot_r, 7, tall * 1.4, h * 0.95, front=0.7)
    return lambda g, lod: emit_hanging(g, fronds, lod, 1, Vector((0, 0, rim_z)), 104)


def plant_07b(rng, h, rim_z, rim_r, pot_r):
    """Dry grass tuft: grass-fan cards round the mouth, tilted outward so the strands fall over the rim."""
    tall = H - rim_z
    cards = []
    for i in range(8):
        az = 2 * math.pi * i / 8 + rng.normal(0, 0.15)
        cards.append((az, rng.uniform(0.25, 0.5), rng.uniform(0.85, 1.0)))

    def emit(g, lod):
        n = [8, 5, 3][lod]
        for az, tilt, s in cards[:n]:
            out = Vector((math.cos(az), math.sin(az), 0))
            right = Vector((0, 0, 1)).cross(out)
            up = (Vector((0, 0, 1)) + out * tilt).normalized()
            w = tall * 1.5 * s * (1 + 0.1 * lod)
            pl.card(g, out * rim_r * 0.2 + Vector((0, 0, rim_z - 0.03)), right * w, up * tall * s,
                    CELLS['grass'], lambda q, out=out: (out + Vector((0, 0, 0.8))),
                    lambda q: 0.55 + 0.45 * pl.smooth((q.z - rim_z) / tall), mat=1)
    return emit


def plant_04b(rng, h, rim_z, rim_r, pot_r):
    """Wilting plant: green petioles arching up and out of the mouth, each with a hanging green or brown leaf."""
    tall = H - rim_z
    stems = []
    for i in range(14):
        az = i * 2.39996 + rng.normal(0, 0.2)
        out = Vector((math.cos(az), math.sin(az), 0))
        a = out * rim_r * 0.25 + Vector((0, 0, rim_z - 0.02))
        top = a + out * tall * rng.uniform(0.15, 0.4) + Vector((0, 0, tall * rng.uniform(0.6, 0.98)))
        tip = top + out * tall * rng.uniform(0.1, 0.2) - Vector((0, 0, tall * rng.uniform(0.05, 0.2)))
        brown = rng.uniform() < 0.5
        stems.append(dict(ctrl=[a, a + (top - a) * 0.5 + Vector((0, 0, tall * 0.2)), top, tip], out=out,
                          cell='leaf_wilt' if brown else 'leaf_green', L=tall * rng.uniform(0.45, 0.62),
                          roll=rng.normal(0, 0.3)))

    def emit(g, lod):
        keep = subset(len(stems), (1.0, 0.7, 0.5)[lod], 105)
        for i in keep:
            s = stems[i]
            pts = pl.bezier(s['ctrl'], (4, 3, 2)[lod])
            pl.tube(g, pts, [0.011 * H] * len(pts), (3, 3, 2)[lod], mat=1, rect=CELLS['stem_green'],
                    occ_fn=lambda q: 0.7, solid=False)
            d = (s['out'] * 0.35 + Vector((0, 0, -1))).normalized()
            leaf_blade(g, pts[-1], d, s['L'], s['L'] * 0.30 * (1 + 0.15 * lod), -0.4, s['cell'], (4, 2, 1)[lod],
                       2 if lod < 2 else 1, 1, lambda q, t: 0.6 + 0.4 * pl.smooth((q.z - rim_z) / tall),
                       Vector((0, 0, rim_z)), roll=s['roll'])
    return emit


def plant_11a(rng, h, rim_z, rim_r, pot_r):
    """A small airy tree: a thin woody stem with a side stem; the crown is a few large crossed cards of the
    'clump' cell (itself a little tree with twigs from its bottom centre) rotated round the stem, plus smaller
    clump cards for volume in the middle and at the top."""
    tall = H - rim_z
    trunks = [[Vector((0, 0, rim_z - 0.05)), Vector((0.03, 0, rim_z + tall * 0.35)), Vector((-0.02, 0.0, rim_z + tall * 0.6))],
              [Vector((0.02, 0.01, rim_z + tall * 0.2)), Vector((0.08, 0.03, rim_z + tall * 0.3)),
               Vector((0.15 * tall, 0.02, rim_z + tall * 0.5))]]
    big = [(math.radians(a), rng.uniform(0.95, 1.0)) for a in (0, 60, 120)]
    small = []
    for i in range(8):
        u = rng.uniform(0.35, 0.85)
        th = rng.uniform(0, 2 * math.pi)
        r = tall * 0.16 * (1.1 - u)
        small.append((Vector((math.cos(th) * r, math.sin(th) * r, rim_z + tall * u)), tall * rng.uniform(0.3, 0.4),
                      rng.uniform(0, math.pi)))
    centre = Vector((0, 0, rim_z + tall * 0.55))
    occ = lambda q: 0.42 + 0.4 * pl.smooth((q.z - rim_z) / tall)
    nrm = lambda q: ((q - centre).normalized() + Vector((0, 0, 0.4)))

    def emit(g, lod):
        for t in trunks[:(2, 2, 1)[lod]]:
            pts = pl.bezier(t, (4, 3, 2)[lod])
            pl.tube(g, pts, [0.013 * H * (1 - 0.5 * i / (len(pts) - 1)) for i in range(len(pts))], (4, 3, 2)[lod],
                    mat=1, rect=CELLS['stem_wood'], occ_fn=lambda q: 0.6, solid=False)
        for ang, s in big[:(3, 3, 2)[lod]]:
            right = Vector((math.cos(ang), math.sin(ang), 0))
            pl.card(g, Vector((0, 0, rim_z + tall * 0.02)), right * tall * 0.78, Vector((0, 0, tall * s)),
                    CELLS['clump'], nrm, occ, mat=1)
        for c, s, a in small[:(8, 4, 2)[lod]]:
            right = Vector((math.cos(a), math.sin(a), 0))
            pl.card(g, c - Vector((0, 0, s * 0.5)), right * s, Vector((0, 0, s)), CELLS['clump'], nrm, occ, mat=1)
    return emit


PLANTS = {'plant01a': plant_01a, 'plant02a': plant_02a, 'plant01b': plant_01b, 'plant03b': plant_03b,
          'plant07b': plant_07b, 'plant04b': plant_04b, 'plant11a': plant_11a}

BUILDERS = {'bush03': build_fern, 'bush10': build_bush10, 'bush11': build_bush11, 'bush13': build_bush13,
            'bush16': build_bush16, 'bush12': build_bush12, 'bush02': build_bush02}
MATERIALS = []
objects = BUILDERS.get(SID, build_potted)()
pl.export(objects, SID)
