"""Blender: build one desert plant -> work/<id>/plant.blend with objects Plant, Plant_LOD1, Plant_LOD2 (materials
Bark: opaque, Leaves: alpha-tested atlas). Each plant's layout is drawn once from its seed; every LOD is built
from the same layout with fewer/coarser parts (a seeded subset of the leaves, enlarged to keep the coverage).
COLOR_0 = per-part tint x proxy-volume sky occlusion (desert_lib.proxy_occlusion). Usage: -- <id>"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import desert_common as dc
import desert_lib as dl
from desert_lib import BARK, LEAVES, UP

SID = sys.argv[sys.argv.index('--') + 1]
H = dc.height_m(SID)
NAMES = ['Plant', 'Plant_LOD1', 'Plant_LOD2']


def lerp(a, b, t):
    return a + (b - a) * t


def golden_dirs(n, z_top, z_bottom, rng, jitter=0.05):
    """n directions spread evenly over the sphere band z in [z_bottom, z_top] (Fibonacci spiral)"""
    out = []
    ga = math.pi * (3 - math.sqrt(5))
    for i in range(n):
        z = lerp(z_top, z_bottom, (i + 0.5) / n) + rng.normal(0, jitter)
        z = max(min(z, 0.999), -0.999)
        a = i * ga + rng.normal(0, 0.15)
        r = math.sqrt(1 - z * z)
        out.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    return out


def radial_h(v):
    h = Vector((v.x, v.y, 0.0))
    return h.normalized() if h.length > 1e-4 else Vector((1, 0, 0))


def proj(v, n):
    return v - n * v.dot(n)


def tint_jitter(rng, base, amount=0.08, value=(0.85, 1.05)):
    return tuple(np.asarray(base) * np.exp(rng.normal(0, amount * 0.3, 3)) * rng.uniform(*value))


# ================================================================================================ 6tree21 fan palm
def layout_6tree21():
    rng = np.random.default_rng(2121)
    L = {}
    top = 2.75
    zs = [0.0, 0.07, 0.16, 0.3, 0.55, 0.9, 1.3, 1.7, 2.0, 2.3, 2.55, top]
    L['trunk'] = [Vector((0.07 * math.sin(z / top * math.pi * 0.9), 0.02 * math.sin(z / top * 2.0), z)) for z in zs]
    prof = [(0.0, 0.40), (0.07, 0.32), (0.16, 0.26), (0.3, 0.228), (0.55, 0.215), (1.3, 0.2), (2.1, 0.188), (top, 0.175)]
    L['radii'] = [float(np.interp(z, [p[0] for p in prof], [p[1] for p in prof])) for z in zs]
    C = L['trunk'][-1] + Vector((0, 0, 0.08)); L['C'] = C
    fans = []
    dirs = golden_dirs(25, 0.92, -0.5, rng)
    for i, d in enumerate(dirs):
        age = (0.92 - d.z) / 1.42                       # 0 top (young) .. 1 lowest (old)
        d = (d + Vector((0, 0, -0.25 * d.z * abs(d.z)))).normalized()     # more fans near the horizontal
        plen = lerp(0.7, 1.15, age) * rng.uniform(0.85, 1.15)
        start = C + d * 0.12
        pd = d.copy(); pts = [start]
        for k in range(3):
            pts.append(pts[-1] + pd * plen / 3)
            pd = dl.rotate_toward(pd, Vector((0, 0, -1)), lerp(0.03, 0.16, age))
        out = radial_h(d)
        n = (out * 0.6 + UP * lerp(1.0, 0.0, age) + Vector(rng.normal(0, 0.25, 3))).normalized()
        fwd = proj(pd + UP * lerp(1.3, -0.5, age), n)
        if fwd.length < 0.2:
            fwd = proj(UP, n)
        fans.append({'petiole': pts, 'centre': pts[-1], 'forward': fwd.normalized(), 'normal': n,
                     'radius': rng.uniform(0.9, 1.05) * lerp(0.95, 1.05, age), 'age': age,
                     'cell': 'fanC' if age > 0.82 and rng.uniform() < 0.7 else ('fanA' if rng.uniform() < 0.55 else 'fanB'),
                     'droop': lerp(0.04, 0.16, age) + rng.uniform(-0.03, 0.03), 'sag': lerp(0.03, 0.12, age),
                     'value': rng.uniform(0.7, 1.12), 'keep': rng.uniform() + (1 - abs(d.z)) * 0.6})
    L['fans'] = fans
    skirt = []
    for k in range(12):
        a = 2 * math.pi * k / 12 + rng.normal(0, 0.15)
        out = Vector((math.cos(a), math.sin(a), 0))
        z = top - 0.02 + rng.uniform(-0.06, 0.06)
        base = Vector((L['trunk'][-1].x, L['trunk'][-1].y, z)) + out * 0.2
        direction = (Vector((0, 0, -1)) + out * rng.uniform(0.12, 0.3)).normalized()
        skirt.append({'base': base, 'dir': direction, 'side': Vector((-out.y, out.x, 0)), 'length': rng.uniform(0.75, 1.0),
                      'width': rng.uniform(0.32, 0.42), 'out': out, 'keep': rng.uniform(), 'value': rng.uniform(0.7, 1.0)})
    L['skirt'] = skirt
    L['spheres'] = [(C + Vector((0, 0, 0.25)), 1.5, 0.6), (C, 0.6, 2.5)]
    return L


def build_6tree21(L, lod):
    mb = dl.MeshBuilder()
    leaf_tint = np.array([1.0, 0.8, 0.88]); dead_tint = np.array([0.95, 0.9, 0.8]); bark_tint = (0.86, 0.86, 0.72)
    C = L['C']
    crown_out = lambda p: (p - C).normalized() if (p - C).length > 1e-4 else UP
    trunk_out = lambda p: radial_h(p)
    # trunk
    idx = [range(len(L['trunk'])), [0, 1, 2, 3, 5, 7, 9, 11], [0, 2, 5, 8, 11]][lod]
    sides = [14, 8, 6][lod]
    zs = [L['trunk'][i].z for i in idx]
    base_shade = lambda k: tuple(np.asarray(bark_tint) * lerp(0.55, 1.0, min(zs[k] / 0.3, 1.0)))  # dark fibrous foot
    dl.tube(mb, [L['trunk'][i] for i in idx], [L['radii'][i] for i in idx], sides, base_shade, u_repeat=1.0,
            v_per_m=0.8, cap=True)
    # fans and petioles
    fans = sorted(L['fans'], key=lambda f: -f['keep'])[:[25, 25, 20][lod]]
    grow = [1.0, 1.03, 1.12][lod]
    rays = [21, 11, 7][lod]; rings = [[0, 0.3, 0.6, 0.82, 1.0], [0, 0.5, 1.0], [0, 1.0]][lod]
    for f in fans:
        t = tuple((leaf_tint if f['cell'] != 'fanC' else dead_tint) * f['value'])
        cell = dc.ATLAS['palm'][f['cell']]
        dl.fan(mb, f['centre'], f['forward'], f['normal'], f['radius'] * grow, rays, rings, cell, t,
               droop=f['droop'], sag=f['sag'], outward=crown_out, own_weight=0.75)
        if lod < 2:
            pts = f['petiole'] if lod == 0 else [f['petiole'][0], f['petiole'][2], f['petiole'][3]]
            dl.tube(mb, pts, [0.03, 0.024, 0.02, 0.016][:len(pts)], 3, t, mat=LEAVES,
                    uv_cell=dc.ATLAS['palm']['stalk'])
        else:
            p = f['petiole']
            dl.card(mb, p[0], (p[-1] - p[0]).normalized(), f['normal'].cross(f['forward']), 0.05, (p[-1] - p[0]).length,
                    dc.ATLAS['palm']['stalk'], 1, 0.0, t, outward=crown_out)
    # dead-leaf skirt under the crown
    skirt = sorted(L['skirt'], key=lambda s: -s['keep'])[:[12, 9, 6][lod]]
    for s in skirt:
        w = s['width'] * [1.0, 1.1, 1.25][lod]
        dl.card(mb, s['base'], s['dir'], s['side'], w, s['length'], dc.ATLAS['palm']['skirt'], [2, 1, 1][lod], 0.0,
                tuple(dead_tint * s['value'] * np.array([0.8, 0.75, 0.7])), outward=lambda p, o=s['out']: o,
                hanging=True)
    return mb


# ================================================================================================ bananas
def spine_curve(start, direction, length, droop, steps=32, gravity=Vector((0, 0, -1))):
    """fine spine from start along direction, bending toward gravity by droop radians in total"""
    pts = [Vector(start)]; d = Vector(direction).normalized()
    for k in range(steps):
        pts.append(pts[-1] + d * length / steps)
        d = dl.rotate_toward(d, gravity, droop / steps)
    return pts


def resample(pts, n):
    """n points evenly spaced by arc length along the polyline pts"""
    seg = [(b - a).length for a, b in zip(pts, pts[1:])]
    cum = np.concatenate([[0], np.cumsum(seg)]); total = cum[-1]
    out = []
    for k in range(n):
        s = total * k / (n - 1)
        i = min(int(np.searchsorted(cum, s, side='right')) - 1, len(seg) - 1)
        f = (s - cum[i]) / max(seg[i], 1e-9)
        out.append(pts[i].lerp(pts[i + 1], min(max(f, 0.0), 1.0)))
    return out


def banana_width(t):
    return min(1.0, (t / 0.1) ** 0.5) * min(1.0, ((1.0 - t) / 0.16) ** 0.65) if 0 < t < 1 else 0.0


def blade_ups(spine, out, roll):
    ups = []
    for i in range(len(spine)):
        t = (spine[min(i + 1, len(spine) - 1)] - spine[max(i - 1, 0)]).normalized()
        u = proj(UP, t)
        if u.length < 0.35:
            u = proj(out, t) * (1 - u.length / 0.35) + u
        u = u.normalized()
        ups.append(Matrix.Rotation(roll, 3, t) @ u)
    return ups


def banana_leaf_layout(rng, base, out, elev, lam, wmax, plen, droop, cell, keep, value):
    d = (out * math.cos(elev) + UP * math.sin(elev)).normalized()
    pet = spine_curve(base, d, plen, droop * 0.1, steps=4)
    d2 = (pet[-1] - pet[-2]).normalized()
    lamina = spine_curve(pet[-1], d2, lam, droop)
    return {'petiole': pet, 'lamina': lamina, 'w': wmax, 'out': out, 'roll': rng.normal(0, 0.3), 'cell': cell,
            'keep': keep, 'value': value}


def banana_stem_layout(rng, base, top, r0, r1, nleaves, lam, wmax, ndead, bunch=False, phase=0.0, elev_top=1.25,
                       elev_low=-0.15, droop=(0.35, 1.6), bias=0.0):
    st = {'pts': [Vector(base).lerp(Vector(top), f) + Vector((0, 0, 0)) for f in np.linspace(0, 1, 7)],
          'radii': [r0 * 1.3, r0 * 1.05, r0, lerp(r0, r1, 0.5), lerp(r0, r1, 0.75), r1, r1 * 0.9]}
    for i, f in enumerate(np.linspace(0, 1, 7)):
        st['pts'][i] += Vector((rng.normal(0, 0.01), rng.normal(0, 0.01), 0)) * (1 if 0 < i < 6 else 0)
    leaves, dead = [], []
    ga = math.pi * (3 - math.sqrt(5))
    top = Vector(top)
    for k in range(nleaves):
        age = k / max(nleaves - 1, 1)                     # 0 youngest (upright) .. 1 oldest (drooping)
        a = phase + k * ga
        out = Vector((math.cos(a), math.sin(a), 0))
        radial = Vector((top.x, top.y, 0))
        if bias and radial.length > 0.05:
            out = (out + radial.normalized() * bias).normalized()
        base_k = top - Vector((0, 0, 0.03 + 0.1 * age)) + out * r1 * 0.6
        elev = lerp(elev_top, elev_low, age) + rng.normal(0, 0.12)
        L = lam * rng.uniform(0.85, 1.1) * lerp(0.8, 1.0, min(age * 2, 1))
        cell = ['leafA', 'leafB', 'leafC'][int(rng.integers(0, 3))] if age > 0.2 else 'leafA'
        leaves.append(banana_leaf_layout(rng, base_k, out, elev, L, wmax * rng.uniform(0.9, 1.1),
                                         rng.uniform(0.12, 0.25) * lam, lerp(droop[0], droop[1], age) + rng.uniform(-0.15, 0.15),
                                         cell, 2 - age + rng.uniform(0, 0.4), rng.uniform(0.85, 1.05)))
    for k in range(ndead):
        a = phase + rng.uniform(0, 2 * math.pi)
        out = Vector((math.cos(a), math.sin(a), 0))
        b = top.lerp(Vector(base), rng.uniform(0.1, 0.35)) + out * r0
        d = (Vector((0, 0, -1)) + out * rng.uniform(0.15, 0.35)).normalized()
        dead.append({'lamina': spine_curve(b, d, lam * rng.uniform(0.45, 0.6), 0.15), 'w': wmax * 0.6, 'out': out,
                     'roll': rng.normal(0, 0.3), 'cell': 'dead', 'keep': rng.uniform(), 'value': rng.uniform(0.7, 1.0)})
    st['leaves'] = leaves; st['dead'] = dead
    st['bunch'] = None
    if bunch:
        a = phase + rng.uniform(0, 2 * math.pi); out = Vector((math.cos(a), math.sin(a), 0))
        stalk = spine_curve(top - Vector((0, 0, 0.05)), (out + UP * 0.2).normalized(), 0.45 * lam, 2.2, steps=8)
        st['bunch'] = {'stalk': stalk, 'axis': (stalk[-1] - stalk[-2]).normalized(), 'length': 0.32 * lam / 1.4,
                       'radius': 0.12 * lam / 1.4}
    return st


def layout_banana(seed, stems_spec, wind, density=0.55, lod2_leaves=0.8):
    rng = np.random.default_rng(seed)
    L = {'stems': [], 'wind': wind, 'spheres': [], 'density': density, 'lod2_leaves': lod2_leaves}
    for spec in stems_spec:
        st = banana_stem_layout(rng, **spec)
        L['stems'].append(st)
        top = st['pts'][-1]
        lam = spec['lam']
        L['spheres'].append((top + Vector((0, 0, 0.25 * lam)), 0.75 * lam, L.get('density', 0.55)))
    return L


def layout_cac19():
    stem = dict(base=(0.10, 0.0, 0.0), top=(-0.06, 0.02, 1.12), r0=0.055, r1=0.04, nleaves=15, lam=0.8, wmax=0.13,
                ndead=4, phase=0.4, elev_top=1.35, elev_low=-0.2, droop=(0.3, 1.7))
    return layout_banana(1919, [stem], 0.05, lod2_leaves=1.0)


def layout_cac18():
    rng = np.random.default_rng(1818)
    stems = []
    spots = [(0.0, 0.0, 1.95), (0.32, 0.12, 1.55), (-0.30, 0.15, 1.65), (0.12, -0.32, 1.35), (-0.18, -0.28, 1.25),
             (0.36, -0.15, 1.05), (-0.38, -0.05, 1.0), (0.05, 0.36, 1.2)]
    for k, (x, y, h) in enumerate(spots):
        out = Vector((x, y, 0)); lean = out.normalized() * 0.3 * h if out.length > 0.01 else Vector()
        stems.append(dict(base=(x, y, 0.0), top=(x + lean.x, y + lean.y, h), r0=0.11 if h > 1.3 else 0.09,
                          r1=0.07 if h > 1.3 else 0.06, nleaves=int(round(lerp(5, 8, (h - 1.0) / 0.95))),
                          lam=lerp(1.2, 1.55, (h - 1.0) / 0.95), wmax=0.2, ndead=2, bunch=k in (1, 2, 5),
                          phase=rng.uniform(0, 6.28), elev_top=1.15, elev_low=-0.05, droop=(0.25, 1.2), bias=0.9))
    return layout_banana(1818, stems, 0.06, density=0.35)


def build_banana(L, lod, leaf_tint, dead_tint, bark_tint):
    mb = dl.MeshBuilder()
    plan = [dict(across=5, segs=7, pet=(3, 2), sides=10, rings=[0, 1, 2, 3, 4, 5, 6], leaves=1.0, dead=1.0, grow=1.0,
                 bunch=(8, 5)),
            dict(across=3, segs=5, pet=(3, 1), sides=7, rings=[0, 2, 4, 6], leaves=1.0, dead=0.6, grow=1.03,
                 bunch=(6, 3)),
            dict(across=2, segs=3, pet=None, sides=5, rings=[0, 3, 6], leaves=L.get('lod2_leaves', 0.8), dead=0.35,
                 grow=1.3, bunch=(4, 2))][lod]
    centres = [s[0] for s in L['spheres']]

    def outward(p):
        c = min(centres, key=lambda c: (c - p).length)
        v = p - c
        return v.normalized() if v.length > 1e-4 else UP
    allleaves = [lf for st in L['stems'] for lf in st['leaves']]
    keep_leaves = set(id(lf) for lf in sorted(allleaves, key=lambda f: -f['keep'])[:int(round(len(allleaves) * plan['leaves']))])
    alldead = [lf for st in L['stems'] for lf in st['dead']]
    keep_dead = set(id(lf) for lf in sorted(alldead, key=lambda f: -f['keep'])[:int(round(len(alldead) * plan['dead']))])
    for st in L['stems']:
        pts = [st['pts'][i] for i in plan['rings']]; radii = [st['radii'][i] for i in plan['rings']]
        dl.tube(mb, pts, radii, plan['sides'], bark_tint, u_repeat=1.0, v_per_m=1.2, cap=True)
        for lf in st['leaves'] + st['dead']:
            if id(lf) not in keep_leaves and id(lf) not in keep_dead:
                continue
            dead = lf['cell'] == 'dead'
            t = tuple((dead_tint if dead else leaf_tint) * lf['value'])
            n = plan['segs'] + 1
            spine = resample(lf['lamina'], n)
            ts = np.linspace(0, 1, n)
            widths = [lf['w'] * plan['grow'] * banana_width(x) for x in ts]
            widths[0] = lf['w'] * plan['grow'] * 0.25
            if not dead and plan['pet'] is None:
                spine = [lf['petiole'][0]] + spine; widths = [0.02] + widths
            dl.blade(mb, spine, widths, blade_ups(spine, lf['out'], lf['roll']), dc.ATLAS['banana'][lf['cell']], t,
                     fold=0.25, across=min(plan['across'], 3) if dead else plan['across'], outward=outward,
                     own_weight=0.65)
            if not dead and plan['pet'] is not None:
                sides, segs = plan['pet']
                p = resample(lf['petiole'], segs + 1)
                dl.tube(mb, p, [0.022 * lf['w'] / 0.15 * (1 - 0.3 * k / segs) for k in range(segs + 1)], sides, t,
                        mat=LEAVES, uv_cell=dc.ATLAS['banana']['stalk'])
        if st['bunch']:
            b = st['bunch']; sides, rings = plan['bunch']
            stalk = resample(b['stalk'], 4 if lod == 0 else 3)
            dl.tube(mb, stalk, [0.018] * len(stalk), 3 if lod < 2 else 3, leaf_tint * 0.8, mat=LEAVES,
                    uv_cell=dc.ATLAS['banana']['stalk'])
            prof = [0.35, 0.9, 1.0, 0.85, 0.55, 0.2]
            zs = np.linspace(0, 1, rings + 1)
            pts = [stalk[-1] + b['axis'] * b['length'] * z for z in zs]
            radii = [b['radius'] * float(np.interp(z, np.linspace(0, 1, len(prof)), prof)) for z in zs]
            dl.tube(mb, pts, radii, sides, tuple(np.array([0.95, 1.0, 0.9])), mat=LEAVES,
                    uv_cell=dc.ATLAS['banana']['bunch'], cap=True)
    return mb


# ================================================================================================ rosettes
def rosette_layout(rng, centre, radius, count, zmin, cells, aspect=1.0, droop=(0.1, 0.6), dead=None, value=(0.8, 1.05)):
    """spray cards radiating from centre over the sphere band z >= zmin (more of them upward); dead: (count, length,
    drop) hanging cards below the centre"""
    sprays = []
    for d in golden_dirs(count, 0.98, zmin, rng, jitter=0.04):
        side = Vector(rng.normal(0, 1, 3)); side = proj(side, d)
        if side.length < 0.1:
            side = proj(Vector((1, 0, 0)), d)
        low = (0.98 - d.z) / (0.98 - zmin)
        sprays.append({'dir': d, 'side': side.normalized(), 'length': radius * rng.uniform(0.8, 1.05),
                       'cell': cells[int(rng.integers(0, len(cells)))], 'droop': lerp(droop[0], droop[1], low),
                       'keep': rng.uniform() + (1 - abs(d.z)) * 0.5, 'value': rng.uniform(*value)})
    hanging = []
    if dead:
        n, length, drop = dead
        for k in range(n):
            a = 2 * math.pi * k / n + rng.normal(0, 0.3)
            out = Vector((math.cos(a), math.sin(a), 0))
            base = Vector(centre) - Vector((0, 0, drop)) + out * radius * rng.uniform(0.08, 0.2)
            d = (Vector((0, 0, -1)) + out * rng.uniform(0.2, 0.5)).normalized()
            hanging.append({'base': base, 'dir': d, 'side': Vector((-out.y, out.x, 0)), 'out': out,
                            'length': length * rng.uniform(0.75, 1.1), 'keep': rng.uniform(), 'value': rng.uniform(0.7, 1.05)})
    return {'centre': Vector(centre), 'radius': radius, 'sprays': sprays, 'dead': hanging, 'aspect': aspect}


def build_rosette(mb, R, plan, tint, dead_tint, atlas='yucca'):
    c = R['centre']
    out = lambda p: (p - c).normalized() if (p - c).length > 1e-4 else UP
    keep = sorted(R['sprays'], key=lambda s: -s['keep'])[:max(3, int(round(len(R['sprays']) * plan['sprays'])))]
    for sp in keep:
        L = sp['length'] * plan['grow']
        dl.card(mb, c + sp['dir'] * R['radius'] * 0.05, sp['dir'], sp['side'], L * R['aspect'], L,
                dc.ATLAS[atlas][sp['cell']], plan['segs'], sp['droop'], tuple(np.asarray(tint) * sp['value']),
                outward=out, own_weight=0.4)
    for h in sorted(R['dead'], key=lambda s: -s['keep'])[:int(round(len(R['dead']) * plan['dead']))]:
        L = h['length'] * plan['grow']
        dl.card(mb, h['base'], h['dir'], h['side'], L * R.get('dead_width', 0.5) * plan['grow'], L, dc.ATLAS[atlas]['dead'],
                max(1, plan['segs'] - 1), 0.0, tuple(np.asarray(dead_tint) * h['value']),
                outward=lambda p, o=h['out']: o, hanging=True, own_weight=0.4)


ROSETTE_PLAN = [dict(sprays=1.0, grow=1.0, segs=2, dead=1.0), dict(sprays=0.55, grow=1.14, segs=1, dead=0.6),
                dict(sprays=0.2, grow=1.35, segs=1, dead=0.3)]


def branch_tubes(mb, branches, lod, tint, v_per_m=1.0):
    sides = [10, 6, 4]
    for b in branches:
        pts, radii = b['pts'], b['radii']
        if lod == 2 and len(pts) > 3:
            keep = sorted(set([0, len(pts) // 2, len(pts) - 1])); pts = [pts[i] for i in keep]; radii = [radii[i] for i in keep]
        elif lod == 1 and len(pts) > 4:
            keep = sorted(set(list(range(0, len(pts), 2)) + [len(pts) - 1])); pts = [pts[i] for i in keep]; radii = [radii[i] for i in keep]
        s = max(3, int(round(sides[lod] * b.get('sides', 1.0))))
        dl.tube(mb, pts, radii, s, tint, u_repeat=1.0, v_per_m=v_per_m, cap=lod < 2)


def smooth_branch(points, radii, n=None):
    """Catmull-Rom through points (and linear radii) -> densified polyline"""
    P = [Vector(p) for p in points]
    n = n or 3
    out, rr = [], []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        for k in range(n):
            t = k / n
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
            out.append(q); rr.append(lerp(radii[i], radii[i + 1], t))
    out.append(P[-1]); rr.append(radii[-1])
    return out, rr


# ---------------------------------------------------------------------------------------------- cac24 dragon tree
def layout_cac24():
    rng = np.random.default_rng(2424)
    m = 2.4 / 392                                     # sprite pixel -> metre (base of the trunk at px x 145)
    P = lambda x, y, d=0.0: Vector(((x - 145) * m, d, (392 - y) * m))
    trunk, tr = smooth_branch([P(145, 392), P(138, 340), P(134, 290), P(130, 225), P(126, 172)],
                              [0.16, 0.09, 0.08, 0.072, 0.066], 2)
    left, lr = smooth_branch([P(126, 172), P(102, 132, 0.02), P(78, 106, 0.04)], [0.066, 0.058, 0.05], 3)
    l1, l1r = smooth_branch([P(78, 104, 0.04), P(60, 98, 0.08), P(46, 92, 0.1)], [0.05, 0.042, 0.036], 2)
    l2, l2r = smooth_branch([P(78, 104, 0.04), P(82, 88, -0.05), P(86, 74, -0.12)], [0.05, 0.043, 0.038], 2)
    right, rr = smooth_branch([P(126, 172), P(140, 130, 0.0), P(148, 96, 0.03), P(154, 62, 0.05)],
                              [0.07, 0.06, 0.052, 0.045], 2)
    mid, mr = smooth_branch([P(138, 128, 0.0), P(128, 118, -0.1), P(120, 112, -0.18)], [0.045, 0.04, 0.035], 2)
    L = {'branches': [{'pts': trunk, 'radii': tr}, {'pts': left, 'radii': lr}, {'pts': l1, 'radii': l1r, 'sides': 0.8},
                      {'pts': l2, 'radii': l2r, 'sides': 0.8}, {'pts': right, 'radii': rr},
                      {'pts': mid, 'radii': mr, 'sides': 0.8}], 'wind': 0.03}
    tips = [(P(46, 90, 0.1), 0.33), (P(86, 72, -0.12), 0.34), (P(154, 58, 0.05), 0.4), (P(122, 110, -0.18), 0.3)]
    L['rosettes'] = [rosette_layout(rng, c, r, 64, -0.6, ['sprayA', 'sprayB'], droop=(0.05, 0.5),
                                    dead=(5, r * 0.5, r * 0.15)) for c, r in tips]
    L['spheres'] = [(R['centre'], R['radius'] * 0.95, 4.0) for R in L['rosettes']]
    return L


def build_cac24(L, lod):
    mb = dl.MeshBuilder()
    branch_tubes(mb, L['branches'], lod, (0.85, 0.8, 0.7), v_per_m=2.2)
    for R in L['rosettes']:
        build_rosette(mb, R, ROSETTE_PLAN[lod], (0.62, 0.72, 0.8), (0.75, 0.7, 0.6))
    return mb


# ---------------------------------------------------------------------------------------------- cac17 yucca clump
def sprite_mask(sid):
    img = bpy.data.images.load(os.path.join(dc.SPRITES, dc.MODELS_SPEC[sid][1]))
    w, h = img.size
    a = np.array(img.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, 3]   # rows from the top
    return a > 0.5, w, h


def layout_cac17():
    rng = np.random.default_rng(1717)
    mask, w, h = sprite_mask('cac17')
    H = dc.height_m('cac17'); m = H / h
    rosettes, branches = [], []
    tries = 0
    for k in range(7):                                # low rosettes round the base, on the ground
        a = 2 * math.pi * k / 7 + rng.normal(0, 0.25); rr = rng.uniform(0.45, 0.85)
        r = rng.uniform(0.36, 0.46)
        c = Vector((math.cos(a) * rr * 1.2, math.sin(a) * rr * 0.8, rng.uniform(0.3, 0.55)))
        rosettes.append(rosette_layout(rng, c, r, 26, -0.45, ['sprayA', 'sprayB'], droop=(0.05, 0.5), dead=(2, r * 0.5, r * 0.2),
                                       value=(0.7, 1.0)))
    while len(rosettes) < 36 and tries < 60000:
        tries += 1
        x, y = rng.uniform(0, w), rng.uniform(0, h * 0.92)
        r = rng.uniform(0.36, 0.48); rp = r / m * 0.6
        pts = [(x, y), (x - rp, y), (x + rp, y), (x, y - rp), (x, min(y + rp, h - 1))]
        if not all(0 <= px < w and 0 <= py < h and mask[int(py), int(px)] for px, py in pts):
            continue
        cx, cz = (x - w / 2) * m, (h - y) * m
        half = max((w / 2) * m * math.sqrt(max(1 - (cx / (w / 2 * m)) ** 2, 0.05)), 0.2)
        cy = rng.uniform(-0.42, 0.42) * half
        c = Vector((cx, cy, max(cz, r * 0.75)))
        if any((c - R['centre']).length < (r + R['radius']) * 0.45 for R in rosettes):
            continue
        hi = c.z > 1.0
        rosettes.append(rosette_layout(rng, c, r, 21, -0.6, ['sprayA', 'sprayB'], droop=(0.05, 0.6),
                                       dead=(4 if hi else 0, r * 1.0, r * 0.2), value=(0.7, 1.05)))
    roots = [Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 0)) for _ in range(5)]
    for R in rosettes:
        c = R['centre']
        if c.z < 0.55:
            continue
        b = min(roots, key=lambda q: (q - Vector((c.x, c.y, 0))).length)
        mid = b.lerp(c, 0.5) + Vector((0, 0, 0)) + (Vector((c.x, c.y, 0)) - b) * 0.15
        pts, rad = smooth_branch([b, b.lerp(c, 0.12) + Vector((0, 0, 0.0)), mid, c - Vector((0, 0, R['radius'] * 0.3))],
                                 [0.045, 0.038, 0.032, 0.027], 2)
        branches.append({'pts': pts, 'radii': rad, 'sides': 0.45})
    for R in rosettes:
        R['dead_width'] = 0.75
    L = {'branches': branches, 'rosettes': rosettes, 'wind': 0.04}
    L['spheres'] = [(R['centre'], R['radius'] * 1.0, 1.3) for R in rosettes]
    print('cac17 rosettes', len(rosettes), 'stems', len(branches))
    return L


def build_cac17(L, lod):
    mb = dl.MeshBuilder()
    plan = dict(ROSETTE_PLAN[lod])
    if lod == 2:
        plan.update(sprays=0.22, grow=1.4)
    branch_tubes(mb, L['branches'], lod, (0.62, 0.55, 0.48), v_per_m=1.5)
    for R in L['rosettes']:
        build_rosette(mb, R, plan, (0.62, 0.68, 0.74), (0.78, 0.66, 0.52))
    return mb


# ---------------------------------------------------------------------------------------------- cac23 tall yucca clump
def layout_cac23():
    rng = np.random.default_rng(2323)
    tops = [(-0.55, 0.25, 1.95, 0.85), (-0.22, -0.2, 2.35, 0.9), (0.22, 0.15, 2.5, 0.95), (0.52, -0.1, 2.0, 0.85),
            (0.06, -0.38, 1.75, 0.8), (0.32, 0.4, 1.6, 0.78)]
    branches, rosettes = [], []
    for k, (x, y, z, r) in enumerate(tops):
        b = Vector((rng.uniform(-0.1, 0.1), rng.uniform(-0.1, 0.1), 0))
        c = Vector((x, y, z))
        bow = Vector((rng.normal(0, 0.05), rng.normal(0, 0.05), 0))
        pts, rad = smooth_branch([b, b.lerp(c, 0.33) + bow, b.lerp(c, 0.66) + bow * 0.6, c],
                                 [0.075, 0.058, 0.052, 0.045], 3)
        branches.append({'pts': pts, 'radii': rad, 'sides': 0.8})
        rosettes.append(rosette_layout(rng, c + Vector((0, 0, 0.05)), r, 46, -0.75, ['strands', 'strandsB'], aspect=0.5,
                                       droop=(0.15, 1.5), dead=(8, 0.55, 0.12), value=(0.75, 1.05)))
    L = {'branches': branches, 'rosettes': rosettes, 'wind': 0.06}
    L['spheres'] = [(R['centre'] + Vector((0, 0, 0.1)), R['radius'] * 0.8, 0.9) for R in rosettes]
    return L


def build_cac23(L, lod):
    mb = dl.MeshBuilder()
    branch_tubes(mb, L['branches'], lod, (0.95, 0.88, 0.78), v_per_m=1.2)
    plan = dict(ROSETTE_PLAN[lod]); plan['segs'] = [3, 2, 1][lod]
    plan['sprays'] = [1.0, 0.5, 0.28][lod]; plan['grow'] = [1.0, 1.14, 1.5][lod]
    for R in L['rosettes']:
        build_rosette(mb, R, plan, (1.0, 0.92, 0.68), (0.85, 0.75, 0.6))
    return mb


# ---------------------------------------------------------------------------------------------- cac3 agave / yucca
def layout_cac3():
    rng = np.random.default_rng(303)
    H = dc.height_m('cac3'); zc = 0.33 * H
    leaves = []
    for d in golden_dirs(230, 0.995, -0.62, rng, jitter=0.03):
        d = Vector((d.x, d.y, d.z * 0.78)).normalized()            # a wider, lower rosette
        Lmax = rng.uniform(0.95, 1.25) * (1.0 + 0.04 * d.z)
        if d.z < 0:
            Lmax = min(Lmax, (zc - 0.03) / -d.z)
        spine = spine_curve(Vector((0, 0, zc)) + d * 0.05, d, Lmax, rng.uniform(0.05, 0.25) * (1 - abs(d.z)), steps=12)
        leaves.append({'spine': spine, 'w': rng.uniform(0.055, 0.07), 'roll': rng.normal(0, 0.35), 'out': radial_h(d),
                       'cell': 'bladeA' if rng.uniform() < 0.6 else 'bladeB', 'keep': rng.uniform(),
                       'value': rng.uniform(0.75, 1.08)})
    C = Vector((0, 0, zc))
    return {'leaves': leaves, 'wind': 0.02, 'C': C,
            'spheres': [(C, 0.38, 6.0), (C + Vector((0, 0, 0.1)), 0.9, 0.9)]}


def build_cac3(L, lod):
    mb = dl.MeshBuilder()
    plan = [dict(n=230, pts=3, across=3, grow=1.0), dict(n=150, pts=3, across=2, grow=1.45),
            dict(n=70, pts=3, across=2, grow=2.3)][lod]
    C = L['C']
    out = lambda p: (p - C).normalized() if (p - C).length > 1e-4 else UP
    for lf in sorted(L['leaves'], key=lambda f: -f['keep'])[:plan['n']]:
        spine = resample(lf['spine'], plan['pts'])
        ts = np.linspace(0, 1, plan['pts'])
        widths = [lf['w'] * plan['grow'] * min(1.0, (t / 0.12) ** 0.5 if t > 0 else 0.35) * (1 - t) ** 0.8 for t in ts]
        widths[0] = lf['w'] * plan['grow'] * 0.5
        dl.blade(mb, spine, widths, blade_ups(spine, lf['out'], lf['roll']), dc.ATLAS['yucca'][lf['cell']],
                 tuple(np.array([0.85, 0.82, 0.62]) * lf['value'] * [1.0, 0.94, 0.97][lod]), fold=-0.4, across=plan['across'], outward=out,
                 own_weight=0.7)
    return mb


# ================================================================================================ registry
PLANTS = {
    '6tree21': (layout_6tree21, build_6tree21, {'floor': 0.26, 'gamma': 1.3}),
    'cac19': (layout_cac19, lambda L, lod: build_banana(L, lod, np.array([1.0, 0.85, 1.0]), np.array([0.9, 0.75, 0.6]),
                                                         (1.0, 0.78, 0.6)), {'floor': 0.35, 'gamma': 1.2}),
    'cac18': (layout_cac18, lambda L, lod: build_banana(L, lod, np.array([1.0, 0.85, 0.9]), np.array([0.95, 0.8, 0.6]),
                                                         (1.0, 0.9, 0.72)), {'floor': 0.55, 'gamma': 1.0}),
    'cac24': (layout_cac24, build_cac24, {'floor': 0.3, 'gamma': 1.2}),
    'cac17': (layout_cac17, build_cac17, {'floor': 0.3, 'gamma': 1.2}),
    'cac23': (layout_cac23, build_cac23, {'floor': 0.4, 'gamma': 1.1}),
    'cac3': (layout_cac3, build_cac3, {'floor': 0.15, 'gamma': 1.3}),
}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    layout, build, occ = PLANTS[SID]
    L = layout()
    mats = dl.materials(SID, L.get('wind', dc.WIND))
    objects = []
    for lod, name in enumerate(NAMES):
        mb = build(L, lod)
        mb.co = [(x, y, max(z, 0.0)) for x, y, z in mb.co]       # nothing below the ground (tilted base rings)
        top = max(z for _, _, z in mb.co)
        if lod == 0:
            top0 = top
        elif top > top0:
            # enlarged cards must not rise above LOD0 (whose bounds scale the placement): squash the top quarter
            z0 = 0.75 * top0
            mb.co = [(x, y, z if z <= z0 else z0 + (z - z0) * (top0 - z0) / (top - z0)) for x, y, z in mb.co]
        vis = dl.proxy_occlusion(mb.co, mb.nrm, L['spheres'])
        o = occ['floor'] + (1 - occ['floor']) * vis ** occ['gamma']
        obj = mb.to_object(name, mats, o)
        objects.append(obj)
        print('LOD', name, 'triangles', mb.triangles())
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(dc.work(SID), 'plant.blend'))


main()
