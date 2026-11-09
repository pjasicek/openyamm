"""Sprite-guided clump builder (inside Blender): flower plants, leafy rosettes and shrubs.

The sprite gives a radius profile R(z) (half the opaque width per height band, treated as a volume of revolution, since
placements are turned at random) and the heights where flower pixels lie. A spec lists leaf groups, spray cards,
flower heads and stems; one seeded layout is drawn, and every LOD is built from it with a keep fraction, enlargement
and fewer segments per part (see LOD_PLAN)."""
import json, math, os
import numpy as np
from mathutils import Vector
import plant_lib as pl

UP = Vector((0, 0, 1))

LOD_PLAN = [
    {'leaf': (1.0, 1.0), 'segs': None, 'across': 2, 'head': (1.0, 1.0), 'hseg': 0, 'card': (1.0, 1.0), 'stem': True},
    {'leaf': (0.55, 1.18), 'segs': 2, 'across': 1, 'head': (0.75, 1.08), 'hseg': 1, 'card': (0.6, 1.18),
     'stem': True},
    {'leaf': (0.28, 1.45), 'segs': 1, 'across': 1, 'head': (0.5, 1.18), 'hseg': 2, 'card': (0.36, 1.4),
     'stem': False},
]


def plan(leaf1=0.55, leaf2=0.28, head1=0.75, head2=0.5, card1=0.6, card2=0.36):
    p = [dict(x) for x in LOD_PLAN]
    p[1]['leaf'] = (leaf1, 1 + (1 - leaf1) * 0.4); p[2]['leaf'] = (leaf2, 1 + (1 - leaf2) * 0.6)
    p[1]['head'] = (head1, 1 + (1 - head1) * 0.3); p[2]['head'] = (head2, 1 + (1 - head2) * 0.35)
    p[1]['card'] = (card1, 1 + (1 - card1) * 0.45); p[2]['card'] = (card2, 1 + (1 - card2) * 0.6)
    return p


class Sprite:
    def __init__(self, sid):
        with open(os.path.join(pl.WORK, sid, 'sprite.json')) as fh:
            self.d = json.load(fh)
        self.H, self.W = self.d['H'], self.d['W']
        rows = np.array(self.d['rows'])
        self.R = np.maximum((rows[:, 1] - rows[:, 0]) * 0.5, 0.0)

    def scale_radius(self, k):
        self.R = self.R * k
        fl = np.array(self.d['flower']); lf = np.array(self.d['leaf'])
        self.flower_rows = fl.sum(1); self.leaf_rows = lf.sum(1)
        self.flower = fl; self.leaf = lf

    def radius(self, z):
        x = min(max(z / self.H * 64 - 0.5, 0), 63)
        i = int(x); f = x - i
        return self.R[i] * (1 - f) + self.R[min(i + 1, 63)] * f

    def inside(self, p, margin=1.0):
        if p.z < -0.02 or p.z > self.H * 1.02:
            return False
        return math.hypot(p.x, p.y) <= self.radius(max(p.z, 0)) * margin + 1e-4

    def sample_z(self, rng, weights='flower', lo=0.0, hi=1.0):
        w = (self.flower_rows if weights == 'flower' else self.leaf_rows).copy()
        n = len(w)
        idx = np.arange(n)
        w[(idx + 0.5) / n < lo] = 0; w[(idx + 0.5) / n > hi] = 0
        if w.sum() <= 0:
            w = np.ones(n)
        r = rng.choice(n, p=w / w.sum())
        return (r + rng.uniform()) / n * self.H

    def sample_xz(self, rng, weights='flower'):
        """A sprite position (x across, z up) drawn by the flower or leaf pixel density."""
        g = self.flower if weights == 'flower' else self.leaf
        flat = g.ravel() + 1e-9
        k = rng.choice(len(flat), p=flat / flat.sum())
        r, c = divmod(k, g.shape[1])
        return ((c + rng.uniform()) / g.shape[1] - 0.5) * self.W, (r + rng.uniform()) / g.shape[0] * self.H


def fit_length(sp, base, direction, droop, max_len, margin=0.97):
    """Longest leaf (up to max_len) from base along direction with droop that stays inside the sprite volume."""
    lo, hi = 0.0, max_len
    for _ in range(14):
        mid = (lo + hi) / 2
        pts, _ = pl.spine_points(base, direction, mid, droop, 6)
        if all(sp.inside(p, margin) for p in pts[1:]) and min(p.z for p in pts) > -0.01:
            lo = mid
        else:
            hi = mid
    return lo


def direction(phi, elev):
    return Vector((math.cos(phi) * math.cos(elev), math.sin(phi) * math.cos(elev), math.sin(elev)))


def layout(spec, sp, rng):
    """-> list of parts (dicts with 'kind' and 'keep'), drawn once for all LODs."""
    parts = []
    H, W = sp.H, sp.W
    def make_leaf(grp, base, phi, elev, keep_bonus=0.0):
        d = direction(phi, elev)
        droop = rng.uniform(*grp.get('droop', (0.2, 0.6)))
        L = grp['len'][1] * H if grp.get('rel', True) else grp['len'][1]
        Lmin = grp['len'][0] * H if grp.get('rel', True) else grp['len'][0]
        if grp.get('fit', True):
            L = min(L, fit_length(sp, base, d, droop, L, grp.get('margin', 1.0)))
            if L < Lmin:
                return None
        else:
            L = rng.uniform(Lmin, L)
        L *= rng.uniform(0.85, 1.0)
        part = {'kind': 'leaf', 'cell': grp['cell'], 'base': base, 'dir': d, 'len': L, 'droop': droop,
                'roll': rng.normal(0, grp.get('roll', 0.35)), 'width': grp.get('width', 1.0) * rng.uniform(0.9, 1.1),
                'tint': [c * rng.uniform(0.9, 1.08) for c in grp['tint']], 'fold': grp.get('fold', 0.25),
                'segs': grp.get('segs', 3), 'keep': rng.uniform() + grp.get('priority', 0.0) + 0.3 * L / H +
                keep_bonus, 'shade': grp.get('shade', 1.0), 'curl': rng.normal(0, grp.get('curl', 0.0))}
        parts.append(part)
        return part

    for grp in spec.get('leaves', []):
        n = grp['n']
        mode = grp.get('from', 'base')
        for k in range(n):
            phi = 2 * math.pi * (k + rng.uniform(0, 0.8)) / n + rng.normal(0, 0.15)
            if mode == 'stalk':
                lo, hi = grp.get('z', (0.1, 0.9))
                z = (lo + (hi - lo) * (k + rng.uniform(0.2, 0.8)) / n) * H
                phi = k * (math.pi + 0.35) + rng.normal(0, 0.25)
                base = Vector((0, 0, z))
                make_leaf(grp, base, phi, math.radians(rng.uniform(*grp['elev'])), 0.5 * (1 - k / n))
                continue
            if mode == 'base':
                rr = grp.get('root_r', 0.06) * W * math.sqrt(rng.uniform())
                rphi = rng.uniform(0, 2 * math.pi)
                base = Vector((rr * math.cos(rphi), rr * math.sin(rphi), grp.get('root_z', 0.0) * H))
                if 'root_c' in grp:
                    cx, cy = grp['root_c'][k % len(grp['root_c'])]
                    base += Vector((cx * W, cy * W, 0))
            else:
                z = sp.sample_z(rng, 'leaf', *grp.get('z', (0.1, 0.9)))
                rr = sp.radius(z) * rng.uniform(*grp.get('depth', (0.2, 0.6)))
                base = Vector((rr * math.cos(phi), rr * math.sin(phi), z))
            if mode == 'whorl':
                # k leaves radiating from one point at the top of a stem (schefflera, plant16)
                kk = grp.get('k', 6)
                bonus = rng.uniform() * 0.6
                p0 = rng.uniform(0, 2 * math.pi)
                for j in range(kk):
                    make_leaf(grp, base, p0 + 2 * math.pi * (j + rng.uniform(-0.2, 0.2)) / kk,
                              math.radians(rng.uniform(*grp['elev'])), bonus)
                st = grp.get('stem')
                if st:
                    foot = Vector((base.x * st.get('in', 0.3), base.y * st.get('in', 0.3), base.z * st.get('from_z', 0.0)))
                    parts.append({'kind': 'stem', 'pts': [foot, (foot + base) * 0.5 + Vector((0, 0, 0.02 * H)),
                                  base], 'r': st['r'] * H, 'colour': st.get('colour', 'green'),
                                  'tint': st.get('tint', (1, 1, 1)), 'keep': bonus + 0.5})
            else:
                make_leaf(grp, base, phi, math.radians(rng.uniform(*grp['elev'])))
    for st in spec.get('stalks', []):
        pts = [Vector(p) * H for p in st['pts']]
        parts.append({'kind': 'stem', 'pts': pts, 'r': st['r'] * H, 'colour': st.get('colour', 'green'),
                      'tint': st.get('tint', (1, 1, 1)), 'keep': 99.0, 'sides': st.get('sides', 3)})
    for grp in spec.get('shell', []):
        # spray cards tangent to an inner shell of the sprite volume: the leafy mass the heads sit on
        for k in range(grp['n']):
            z = sp.sample_z(rng, grp.get('weights', 'leaf'), *grp.get('z', (0.05, 0.9)))
            phi = rng.uniform(0, 2 * math.pi)
            R = sp.radius(z)
            rr = R * rng.uniform(*grp.get('depth', (0.6, 0.85)))
            c = Vector((rr * math.cos(phi), rr * math.sin(phi), z))
            nz = (z / H - 0.45) * grp.get('up', 1.2)
            normal = Vector((math.cos(phi), math.sin(phi), nz)) + Vector(rng.normal(0, grp.get('tilt', 0.25), 3))
            normal.normalize()
            right = Vector((-normal.y, normal.x, 0))
            if right.length < 0.2:
                right = Vector((math.cos(phi + 1.6), math.sin(phi + 1.6), 0))
            right.normalize()
            up = normal.cross(right).normalized()
            if up.z < 0:
                up = -up
            size = grp['size'] * H * rng.uniform(0.8, 1.15)
            base = c - up * size * 0.5
            parts.append({'kind': 'card', 'cell': grp['cell'], 'base': base, 'right': right * size,
                          'up': up * size, 'tint': [x * rng.uniform(0.9, 1.08) for x in grp['tint']],
                          'keep': rng.uniform() + grp.get('priority', 0.0), 'shade': grp.get('shade', 1.0)})
    for grp in spec.get('cards', []):
        n = grp['n']
        for k in range(n):
            phi = 2 * math.pi * (k + rng.uniform(0, 0.7)) / n
            z0 = grp.get('z', 0.0) * H
            rr = grp.get('r', 0.25) * W * rng.uniform(0.6, 1.0)
            size = grp['size'] * H * rng.uniform(0.85, 1.1)
            base = Vector((rr * math.cos(phi), rr * math.sin(phi), z0))
            facing = Vector((math.cos(phi), math.sin(phi), 0))
            right = Vector((-facing.y, facing.x, 0)) * size * grp.get('aspect', 1.0)
            lean = math.radians(rng.uniform(*grp.get('lean', (0, 20))))
            up = (UP * math.cos(lean) + facing * math.sin(lean)) * size
            parts.append({'kind': 'card', 'cell': grp['cell'], 'base': base, 'right': right, 'up': up,
                          'tint': [c * rng.uniform(0.92, 1.06) for c in grp['tint']], 'keep': rng.uniform() +
                          grp.get('priority', 0.0), 'shade': grp.get('shade', 1.0)})
    for grp in spec.get('heads', []):
        placed = []
        n = grp['n']; tries = 0
        while len([p for p in placed]) < n and tries < n * 60:
            tries += 1
            if grp.get('place', 'surface') == 'surface':
                z = sp.sample_z(rng, 'flower', *grp.get('z', (0.0, 1.0)))
                phi = rng.uniform(0, 2 * math.pi)
                R = sp.radius(z)
                rr = R * rng.uniform(*grp.get('depth', (0.78, 0.98)))
            else:          # 'sprite': (x, z) from the sprite, depth from the volume
                x, z = sp.sample_xz(rng, 'flower')
                R = sp.radius(z)
                y = math.sqrt(max(R * R - x * x, 0)) * rng.uniform(-1, 1)
                rr = math.hypot(x, y); phi = math.atan2(y, x)
            rad = rng.uniform(*grp['r']) * H
            p = Vector((rr * math.cos(phi), rr * math.sin(phi), max(z, rad * 0.8)))
            if p.z > H - rad * grp.get('top_clear', 0.6):
                p.z = H - rad * grp.get('top_clear', 0.6)
            if any((p - q['centre']).length < (rad + q['radius']) * grp.get('spacing', 0.85) for q in placed):
                continue
            out = Vector((math.cos(phi), math.sin(phi), 0))
            rise = math.radians(rng.uniform(*grp.get('rise', (15, 60))))
            if rr < 0.25 * max(R, 1e-3):
                rise = math.radians(rng.uniform(55, 85))
            axis = (out * math.cos(rise) + UP * math.sin(rise) + Vector(rng.normal(0, 0.08, 3))).normalized()
            placed.append({'kind': 'head', 'cell': grp['cell'], 'centre': p, 'axis': axis, 'radius': rad,
                           'profile': grp.get('profile', 'dish'), 'tint': [c * rng.uniform(0.92, 1.06)
                                                                          for c in grp['tint']],
                           'keep': rng.uniform() + 0.6 * p.z / H + grp.get('priority', 0.0),
                           'segments': grp.get('segments', 8), 'turn': rng.uniform(0, 2 * math.pi),
                           'stem': grp.get('stem'), 'shade': grp.get('shade', 1.0)})
        parts += placed
    return parts


def build_lod(spec, parts, atlas, lod, clump, plan=None):
    plan = plan or spec.get('lod_plan', LOD_PLAN)[lod]
    g = pl.Geo()
    stems_cell = spec.get('stems_cell', 'stems')
    rect = atlas.rect(stems_cell) if stems_cell in atlas.cells else None
    if rect:
        half = (rect[0] + rect[2]) * 0.5
        stems = sorted([p for p in parts if p['kind'] == 'stem'], key=lambda p: -p['keep'])
        minor = [p for p in stems if p['keep'] < 99] if plan['stem'] else []
        stems = [p for p in stems if p['keep'] >= 99] + minor[:int(round(len(minor) * plan['leaf'][0] * 1.5 + 0.49))]
        for p in stems:
            uv = (rect[0], rect[1], half, rect[3]) if p['colour'] == 'green' else (half, rect[1], rect[2], rect[3])
            path = p['pts'] if lod == 0 else [p['pts'][0], p['pts'][-1]]
            radii = [p['r'] * (1 - 0.35 * i / max(len(path) - 1, 1)) for i in range(len(path))]
            pl.tube(g, path, radii, p.get('sides', 3) if lod == 0 else 3, clump, p['tint'], uv_rect=uv)
    for kind, key in (('card', 'card'), ('leaf', 'leaf'), ('head', 'head')):
        group = [p for p in parts if p['kind'] == kind]
        frac, grow = plan[key]
        keep = sorted(group, key=lambda p: -p['keep'])[:int(round(len(group) * frac))]
        for p in keep:
            if kind == 'leaf':
                segs = p['segs'] if plan['segs'] is None else min(plan['segs'], p['segs'])
                across = plan['across'] if segs > 1 else 1
                L = p['len'] * grow
                pl.leaf(g, atlas, p['cell'], p['base'], p['dir'], L, clump, p['tint'], droop=p['droop'],
                        roll=p['roll'], segs=segs, across=across, fold=p['fold'], width=p['width'] *
                        (1 + (grow - 1) * 0.5), shade=p['shade'], curl=p['curl'])
            elif kind == 'card':
                c = p['base']; up = p['up'] * grow; right = p['right'] * grow
                pl.card(g, atlas, p['cell'], c, right, up, clump, p['tint'], shade=p['shade'])
            else:
                segs = [p['segments'], max(5, p['segments'] - 2), 5][plan['hseg']]
                prof = pl.PROFILES[p['profile']]
                rings = None if plan['hseg'] == 0 else ([1] if plan['hseg'] == 1 and len(prof) > 3 else [])
                if p['profile'] == 'goblet' and plan['hseg'] == 1:
                    rings = [2, 3]
                if p['profile'] == 'goblet' and plan['hseg'] == 2:
                    rings = [2]
                pl.head(g, atlas, p['cell'], p['centre'], p['axis'], p['radius'] * grow, clump, p['tint'],
                        profile=prof, segments=segs, rings=rings, turn=p['turn'], shade=p['shade'])
                st = p.get('stem')
                if st and plan['stem']:
                    top = p['centre'] - p['axis'] * p['radius'] * 0.1
                    bottom = Vector((top.x * st.get('in', 0.5), top.y * st.get('in', 0.5),
                                     max(0.0, top.z - st.get('len', 0.3) * sp_h(spec))))
                    mid = (top + bottom) * 0.5 + Vector((0, 0, 0.0))
                    rect = atlas.rect(stems_cell)
                    half = (rect[0] + rect[2]) * 0.5
                    uv = (rect[0], rect[1], half, rect[3]) if st.get('colour', 'green') == 'green' else \
                        (half, rect[1], rect[2], rect[3])
                    path = [bottom, mid, top] if lod == 0 else [bottom, top]
                    pl.tube(g, path, [st['r'] * sp_h(spec)] * len(path), 3, clump, st.get('tint', (1, 1, 1)),
                            uv_rect=uv)
    return g


def sp_h(spec):
    return spec['_H']


def build(sid, spec, seed):
    sp = Sprite(sid)
    sp.scale_radius(spec.get('radius_scale', 1.0))
    spec['_H'] = sp.H
    rng = np.random.default_rng(seed)
    parts = layout(spec, sp, rng)
    atlas = pl.Atlas(spec['atlas'])
    cl = spec.get('clump', {})
    clump = pl.Clump((0, 0, sp.H * cl.get('cz', 0.45)), (sp.W * 0.5 * cl.get('rx', 1.0), sp.W * 0.5 *
                     cl.get('rx', 1.0), sp.H * cl.get('rz', 0.55)), floor=cl.get('floor', 0.35),
                     ground=cl.get('ground', 0.35), depth=cl.get('depth', 0.55), blend=cl.get('blend', 0.55),
                     height=sp.H)
    mat = pl.material('Foliage', spec['atlas'], cutout=True, roughness=0.7,
                      extras={'openyamm_wind': spec.get('wind', 0.02), 'openyamm_specular': 0.1,
                              'openyamm_translucency': 0.3})
    mats = [mat]
    woody = spec.get('trunk') or spec.get('branches')
    if woody:
        mats.append(pl.material('Bark', 'bark', cutout=False, roughness=0.9, extension='REPEAT',
                                extras={'openyamm_wind': spec.get('wind', 0.02), 'openyamm_specular': 0.05}))
        branches = branch_layout(spec, sp, np.random.default_rng(seed + 7)) if spec.get('branches') else []
    objects = []
    for lod, name in enumerate(('Plant', 'Plant_LOD1', 'Plant_LOD2')):
        g = build_lod(spec, parts, atlas, lod, clump)
        if spec.get('trunk'):
            trunk(g, sp, spec['trunk'], lod, clump, np.random.default_rng(seed + 3))
        for br in (branches if woody else []):
            if lod == 2 and br['keep'] < 0.5:
                continue
            path = br['pts'] if lod == 0 else br['pts'][::2] + ([br['pts'][-1]] if len(br['pts']) % 2 == 0 else [])
            radii = [br['r0'] + (br['r1'] - br['r0']) * i / (len(path) - 1) for i in range(len(path))]
            pl.tube(g, path, radii, [br['sides'], 4, 3][lod], clump, br['tint'], mat=1,
                    tile=(1.0, 0.5), occ_floor=0.25)
        objects.append(g.to_object(name, mats))
    return objects


def trunk(g, sp, t, lod, clump, rng):
    """Bark trunk following the sprite's radius profile up to t['top'] x H (it ends inside the crown), with root lobes
    flaring into the ground. Material 1 (Bark), tiling texture."""
    H = sp.H
    sides = [t.get('sides', 16), 10, 7][lod]
    rows = [t.get('rows', 8), 5, 3][lod]
    lobes = t.get('lobes', 6)
    la = np.sort(rng.uniform(0, 2 * math.pi, lobes)); lw = rng.uniform(0.25, 0.45, lobes)
    lumps = rng.normal(0, 1, 12); lp = rng.uniform(0, 6.3, 12)
    top = t['top'] * H
    zs = [-0.02 * H] + [top * (i / rows) ** 1.15 for i in range(1, rows + 1)]
    # above the narrowest point (the waist under the crown) the trunk only widens gently: the sprite's rows there
    # already include the crown
    probe = [0.15 * H + (top - 0.15 * H) * k / 20 for k in range(21)]
    waist = min(probe, key=lambda z: sp.radius(z))
    waist_r = sp.radius(waist)
    around = t.get('around', 2.0)
    ring_ids = []
    for i, z in enumerate(zs):
        zz = max(z, 0.0)
        if t.get('profile', True):
            prof_r = sp.radius(zz) if zz <= waist else waist_r * (1 + 0.25 * (zz - waist) / max(top - waist, 1e-6))
        else:
            prof_r = t['r'] * H
        base_r = prof_r * t.get('scale', 0.9)
        base_r = max(base_r, t.get('min_r', 0.05) * H)
        flare = max(0.0, 1 - zz / (t.get('flare', 0.3) * H)) ** 1.5
        ring = []
        for k in range(sides + 1):
            a = 2 * math.pi * k / sides
            lobe = sum(math.exp(-(math.remainder(a - c, 2 * math.pi) / w) ** 2) for c, w in zip(la, lw))
            r = base_r * (1 - 0.35 * flare + 0.55 * flare * min(lobe, 1.2))
            if lod == 0:
                r *= 1 + 0.04 * sum(lumps[j] * math.sin((j + 2) * a + lp[j] + 3 * zz / H) for j in range(6))
            p = Vector((math.cos(a) * r, math.sin(a) * r, z))
            o = max(0.3, clump.occ(p) if clump else 1.0) * t.get('shade', 1.0)
            o *= 1 - t.get('crown_shade', 0.35) * min(1.0, zz / max(top, 1e-6)) ** 2
            tint = t.get('tint', (1, 1, 1))
            vid = g.vert(p, (tint[0] * o, tint[1] * o, tint[2] * o)) if k < sides else None
            ring.append((vid, (around * k / sides, z / t.get('tile', 0.6))))
        ring[sides] = (ring[0][0], ring[sides][1])
        ring_ids.append(ring)
    for i in range(len(zs) - 1):
        A, B = ring_ids[i], ring_ids[i + 1]
        for k in range(sides):
            g.face([A[k][0], A[k + 1][0], B[k + 1][0], B[k][0]], [A[k][1], A[k + 1][1], B[k + 1][1], B[k][1]],
                   None, 1)


def branch_layout(spec, sp, rng):
    """Woody stems fanning from the base into the crown (multi-stem shrubs, plant42)."""
    b = spec['branches']
    H = sp.H
    out = []
    for k in range(b['n']):
        phi = 2 * math.pi * (k + rng.uniform(0, 0.6)) / b['n']
        z1 = rng.uniform(*b.get('z', (0.45, 0.8))) * H
        rr = sp.radius(z1) * rng.uniform(*b.get('depth', (0.3, 0.65)))
        foot = Vector((math.cos(phi) * b.get('foot', 0.04) * H, math.sin(phi) * b.get('foot', 0.04) * H, -0.01 * H))
        tip = Vector((math.cos(phi) * rr, math.sin(phi) * rr, z1))
        mid = foot.lerp(tip, 0.5) + Vector((rng.normal(0, 0.04), rng.normal(0, 0.04), 0)) * H
        pts = [foot.lerp(mid, t) if t <= 1 else mid.lerp(tip, t - 1) for t in (0, 0.5, 1.0, 1.5, 2.0)]
        r0 = b['r'] * H * rng.uniform(0.8, 1.2)
        out.append({'pts': pts, 'r0': r0, 'r1': r0 * 0.5, 'sides': b.get('sides', 6),
                    'tint': b.get('tint', (0.8, 0.7, 0.6)), 'keep': rng.uniform() + 0.5})
        # forks: child branches from the parent's upper part out to the crown surface (dry bush, plant48)
        for f in range(b.get('forks', 0)):
            start = pts[3] if f % 2 else pts[4]
            ph = phi + rng.normal(0, 0.6)
            zt = min(start.z + rng.uniform(0.25, 0.45) * H, 0.99 * H)
            rt = sp.radius(zt) * rng.uniform(0.75, 1.0)
            end = Vector((math.cos(ph) * rt, math.sin(ph) * rt, zt))
            midc = start.lerp(end, 0.5) + Vector((0, 0, rng.uniform(0, 0.05) * H))
            cp = [start, start.lerp(midc, 0.5), midc, midc.lerp(end, 0.5), end]
            out.append({'pts': cp, 'r0': r0 * 0.5, 'r1': r0 * 0.2, 'sides': max(3, b.get('sides', 6) - 1),
                        'tint': b.get('tint', (0.8, 0.7, 0.6)), 'keep': rng.uniform() * 0.6})
    return out
