"""Blender: build one MM8 palm -> work/<id>/plant.blend with objects Plant, Plant_LOD1, Plant_LOD2 (materials Bark:
opaque, Leaves: alpha-tested tropical atlas). Adapted from the MM6 desert palm builder
(../../mm6_new_sorpigal_3d/desert/scripts/build_plant.py).

The layout is drawn once from the species seed (palm_common.SPECIES); every LOD is built from it with fewer rows
across and along each frond and fewer trunk sides. Fronds spring from the crown heart on a golden-angle spiral, the
youngest upright at the top and the oldest low and hanging; each frond is a petiole (tube) and a rachis arching down
under its own weight (bending more toward the tip), with leaflets hanging from it in a curved inverted V
(palm_lib.frond). Crownshaft species (bundle) grow long petioles from the trunk top up to the crown.
COLOR_0 = per-part tint x proxy-volume sky occlusion. Finally every LOD is scaled by the one factor that makes
LOD0 exactly the binding height. Usage: -- <id>"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as pc
import palm_lib as pl
from palm_lib import BARK, LEAVES, UP, DOWN

SID = sys.argv[sys.argv.index('--') + 1]
S = dict(pc.SPECIES[SID])
_args = sys.argv[sys.argv.index('--') + 2:]
if _args and _args[0].startswith('{'):
    S.update(json.loads(_args[0]))            # trial settings (crown_profile.py)
H = pc.height_m(SID)
K = H / 12.0                 # metre lengths in the species table are for a 12 m palm
NAMES = ['Plant', 'Plant_LOD1', 'Plant_LOD2']
LEAF_FLOOR = 0.2     # darkest leaf vertex colour relative to its tint (linear luminance)
_tints = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leaf_tint.json')
LEAF_TINT = json.load(open(_tints)) if os.path.exists(_tints) else {}     # calibrate_tint.py: matches the sprite
_contrast = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'leaf_contrast.json')
CONTRAST = json.load(open(_contrast)).get(SID, 1.8) if os.path.exists(_contrast) else 1.8   # calibrate_contrast.py
PLAN = [dict(rows=S.get('rows', 12), across=5, pet_sides=(4 if S['bundle'] else 3), pet_segs=(4 if S['bundle'] else 2),
             trunk_sides=12, trunk_rings=12, dead=1.0, grow=1.0),
        dict(rows=7, across=3, pet_sides=3, pet_segs=(2 if S['bundle'] else 1), trunk_sides=8, trunk_rings=7, dead=1.0,
             grow=1.0),
        dict(rows=4, across=3, pet_sides=3, pet_segs=(1 if S['bundle'] else 0), trunk_sides=6, trunk_rings=4, dead=0.5,
             grow=1.05 + 0.4 * S.get('lod2_drop', 0.0), drop=S.get('lod2_drop', 0.0), pet_every=2)]
# lod2_drop: LOD2 leaves out that fraction of the fronds, the least exposed ones (lowest sky visibility of their
# rachis: inner fronds hidden near the crown heart), against the stacked alpha-tested layers there; pet_every keeps
# every n-th petiole of a crownshaft bundle


def lerp(a, b, t):
    return a + (b - a) * t


def catmull(points, n):
    """smooth curve through points (Vector list), n samples evenly in parameter"""
    P = [points[0] * 2 - points[1]] + list(points) + [points[-1] * 2 - points[-2]]
    out = []
    segs = len(points) - 1
    for k in range(n):
        u = k / (n - 1) * segs; i = min(int(u), segs - 1); f = u - i
        p0, p1, p2, p3 = P[i], P[i + 1], P[i + 2], P[i + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3))
    return out


def layout(fit=1.0):
    """fit scales the frond lengths (main() solves it so the crown reaches the binding height)"""
    rng = np.random.default_rng(S['seed'])
    L = {}
    ctrl = [Vector((x * H, rng.normal(0, 0.006) * H * (0 < k < len(S['trunk']) - 1), z * H))
            for k, (x, z) in enumerate(S['trunk'])]
    L['trunk'] = catmull(ctrl, 60)
    zt = [p.z for p in L['trunk']]
    dz = [d[0] * H for d in S['diameter']]; dd = [d[1] * H / 2 for d in S['diameter']]
    L['radius'] = lambda z: float(np.interp(z, dz, dd))
    top = L['trunk'][-1]; r_top = L['radius'](top.z)
    heart = Vector((S['heart'][0] * H, top.y, S['heart'][1] * H))
    L['top'], L['r_top'], L['heart'] = top, r_top, heart
    sweep = Vector(S['sweep']) if S['sweep'] else None
    # fronds
    n = S['fronds']
    ga = math.pi * (3 - math.sqrt(5))
    cells = list(S['cells']); weights = np.array([S['cells'][c] for c in cells]); weights /= weights.sum()
    phase = rng.uniform(0, 2 * math.pi)
    fronds = []
    lens = []
    for i in range(n):
        age = i / max(n - 1, 1)
        a = phase + i * ga + rng.normal(0, 0.12)
        az = Vector((math.cos(a), math.sin(a), 0))
        if sweep is not None:
            az = (az + Vector((sweep.x, sweep.y, 0)) * 0.85).normalized()
        e = math.radians(lerp(S['elev'][0], S['elev'][1], age ** S.get('elev_pow', 0.9)) + rng.normal(0, 5))
        if sweep is not None:
            e += math.radians(18) * max(az.dot(Vector((sweep.x, sweep.y, 0)).normalized()), 0) * sweep.z / 0.25
        droop = math.radians(lerp(S['droop'][0], S['droop'][1], age ** S.get('droop_pow', 1.0)) + rng.normal(0, 8))
        if sweep is not None:              # fronds blown downwind stand stiffer (less droop)
            droop *= 1.0 - 0.45 * max(az.dot(Vector((sweep.x, sweep.y, 0)).normalized()), 0)
        length = fit * rng.uniform(*S['length']) * K * lerp(0.8, 1.0, min(age / 0.2, 1.0)) * lerp(*S.get('length_age', (1.0, 1.0)), age) * lerp(1.0, 1.12, max(age - 0.6, 0) / 0.4)
        lens.append(length)
        side = Vector((-az.y, az.x, 0))           # T x side points up for every frond
        if S['bundle']:
            base = top + az * r_top * 0.55 + Vector((0, 0, 0.05 * K))
            pe = math.radians(lerp(86, 66, age) + rng.normal(0, 3))
            plen = S['petiole'] * K * rng.uniform(0.9, 1.1) * lerp(1.0, 0.85, age)
        else:
            base = heart + az * r_top * 0.5 * S['heart_bulge'] - Vector((0, 0, lerp(-0.1, 0.35, age) * K))
            pe = e + math.radians(10)
            plen = S['petiole'] * K * rng.uniform(0.85, 1.15)
        d0 = (az * math.cos(pe) + UP * math.sin(pe)).normalized()
        dr = (az * math.cos(e) + UP * math.sin(e)).normalized()
        # petiole: bends from d0 toward the rachis start direction
        pet = [base]; d = d0.copy(); steps = 8
        turn = d0.angle(dr)
        for k in range(steps):
            pet.append(pet[-1] + d * plen / steps)
            d = pl.rotate_toward(d, dr, turn / steps * 1.2)
        # rachis: arches down under its weight, bending more toward the tip
        rates = np.array([0.35 + 1.3 * (k + 0.5) / 48 for k in range(48)]); rates *= droop / rates.sum()
        rach = [pet[-1]]; d = d.copy()
        for k in range(48):
            rach.append(rach[-1] + d * length / 48)
            d = pl.rotate_toward(d, DOWN, rates[k])
        cell = cells[int(rng.choice(len(cells), p=weights))]
        hy, ho = S['hang']
        fronds.append({'petiole': pet, 'rachis': rach, 'side': side, 'cell': cell, 'age': age,
                       'width': S['width'] * K * rng.uniform(0.9, 1.08) * lerp(0.85, 1.0, min(age / 0.2, 1.0)),
                       'hang_in': math.radians(lerp(hy[0], hy[1], age) + rng.normal(0, 4)),
                       'hang_out': math.radians(lerp(ho[0], ho[1], age) + rng.normal(0, 5)),
                       'roll': math.radians(S['roll']) * rng.normal(0, 1),
                       'value': rng.uniform(*S['value']), 'pet_r': S.get('pet_radius', 0.075 if S['bundle'] else 0.06) * K})
    # dead fronds hanging under the crown
    dead = []
    for j in range(S['dead']):
        a = rng.uniform(0, 2 * math.pi); az = Vector((math.cos(a), math.sin(a), 0))
        base = heart + az * r_top * 0.8 - Vector((0, 0, 0.45 * K))
        e = math.radians(rng.uniform(-75, -55))
        d = (az * math.cos(e) + UP * math.sin(e)).normalized()
        length = rng.uniform(*S['length']) * K * 0.7
        rach = [base]
        for k in range(24):
            rach.append(rach[-1] + d * length / 24)
            d = pl.rotate_toward(d, DOWN, math.radians(20) / 24)
        dead.append({'rachis': rach, 'side': Vector((-az.y, az.x, 0)), 'width': S['width'] * K * 0.75,
                     'value': rng.uniform(0.75, 1.0), 'roll': math.radians(rng.normal(0, 20))})
    L['fronds'], L['dead'] = fronds, dead
    Lm = float(np.mean(lens))
    density = S.get('crown_density', 0.45)
    L['spheres'] = [(heart + Vector((0, 0, 0.1 * Lm)), 0.62 * Lm, density), (heart, 0.22 * Lm, 2.2)]
    L['crown_centre'] = heart + Vector((0, 0, 0.1 * Lm))
    for f in fronds:            # exposure: mean sky visibility along the rachis (for the LOD2 frond thinning)
        samples = [tuple(f['rachis'][k]) for k in (6, 14, 22, 30, 38, 46)]
        f['exposure'] = float(pl.proxy_occlusion(samples, [(0, 0, 1)] * len(samples), L['spheres']).mean())
    return L


def build(L, lod):
    plan = PLAN[lod]
    mb = pl.MeshBuilder()
    C = L['crown_centre']
    crown_out = lambda p: (p - C).normalized() if (p - C).length > 1e-4 else UP
    # trunk: rings denser at the flared foot
    top, r_top = L['top'], L['r_top']
    nr = plan['trunk_rings']
    us = sorted(set([0.0, 0.015, 0.05] + list(np.linspace(0.12, 1.0, nr - 3)))) if lod == 0 else \
        sorted(set([0.0, 0.04] + list(np.linspace(0.15, 1.0, nr - 2)))) if lod == 1 else list(np.linspace(0.0, 1.0, nr))
    idx = [min(int(round(u * (len(L['trunk']) - 1))), len(L['trunk']) - 1) for u in us]
    pts = [L['trunk'][i] for i in idx]
    radii = [L['radius'](p.z) for p in pts]
    # crown heart (coconut types): fibrous bulge of leaf bases up to the heart, capped; crownshaft types: a cap
    hb = S['heart_bulge']
    if hb > 1.0:
        h = L['heart']
        pts += [top.lerp(h, 0.45), h + Vector((0, 0, 0.1 * K)), h + Vector((0, 0, 0.45 * K))]
        radii += [r_top * hb, r_top * hb * 0.8, r_top * 0.35]          # a cone of leaf bases, not a flat cap
    bt = np.asarray(S['bark_tint'])
    foot = lambda k: tuple(bt * lerp(0.75, 1.0, min(pts[k].z / (0.06 * H), 1.0)))
    pl.tube(mb, pts, radii, plan['trunk_sides'], foot, u_repeat=1.0, v_per_m=1.0 / pc.BARK_TILE_M, cap=True)
    leaf_tint = np.asarray(S['leaf_tint']) * np.asarray(LEAF_TINT.get(SID, [1.0, 1.0, 1.0]))
    ws = Vector((0, 0, 0))
    fronds = L['fronds']
    if plan.get('drop', 0.0) > 0:
        hidden = sorted(fronds, key=lambda f: f['exposure'])[:int(round(len(fronds) * plan['drop']))]
        fronds = [f for f in fronds if f not in hidden]
    for i, f in enumerate(fronds):
        tint = tuple(leaf_tint * f['value'])
        mb.current_base = tint
        rach = pl.resample(f['rachis'], plan['rows'])
        age = f['age']
        hang_in = lambda t, f=f: min(f['hang_in'] * (0.7 + 0.6 * t), math.radians(80))
        hang_out = lambda t, f=f: min(f['hang_out'] * (0.75 + 0.5 * t), math.radians(88))
        roll = lambda t, f=f: f['roll'] * t
        pl.frond(mb, rach, f['side'], f['width'], f['cell'], tint, hang_in, hang_out, roll=roll, across=plan['across'],
                 outward=crown_out, own_weight=0.65, grow=plan['grow'], edge_shade=S['edge_shade'], sun=S['sun'])
        if plan['pet_segs'] > 0 and i % plan.get('pet_every', 1) == 0:
            pet = pl.resample(f['petiole'] + [f['rachis'][2]], plan['pet_segs'] + 1)
            r = f['pet_r']
            radii_p = [r * lerp(1.0, 0.45, k / plan['pet_segs']) for k in range(plan['pet_segs'] + 1)]
            pl.tube(mb, pet, radii_p, plan['pet_sides'], tint, mat=LEAVES, uv_cell=pc.ATLAS[S['petiole_cell']])
    mb.current_base = None
    dead = L['dead'][:int(math.ceil(len(L['dead']) * plan['dead']))]
    for f in dead:
        tint = tuple(np.asarray(S['dead_tint']) * f['value'])
        rach = pl.resample(f['rachis'], max(plan['rows'] // 2, 3))
        pl.frond(mb, rach, f['side'], f['width'], 'frondB', tint, lambda t: math.radians(55), lambda t: math.radians(80),
                 roll=lambda t, f=f: f['roll'] * t, across=plan['across'], outward=crown_out, own_weight=0.6,
                 grow=plan['grow'])
    return mb


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # frond length fit: the trunk keeps the sprite's proportions, the crown grows until LOD0 reaches the height
    fit = 1.0
    for it in range(4 if S.get('fit') else 0):
        L = layout(fit)
        top0 = max(z for _, _, z in build(L, 0).co)
        hz = L['heart'].z
        fit = min(max(fit * (H - hz) / max(top0 - hz, 0.1), 0.9), 1.1)   # small corrections only (crown width)
    L = layout(fit)
    mats = pl.materials(SID, pc.WIND * K)
    builders = [build(L, lod) for lod in range(3)]
    top0 = max(z for _, _, z in builders[0].co)
    scale = H / top0
    print('SCALE', SID, round(scale, 3), 'frond fit', round(fit, 3), 'raw top', round(top0, 2), 'target', round(H, 2))
    occ = S['occlusion']
    for lod, (name, mb) in enumerate(zip(NAMES, builders)):
        mb.co = [(x * scale, y * scale, max(z * scale, 0.0)) for x, y, z in mb.co]
        top = max(z for _, _, z in mb.co)
        if top > H + 1e-4:
            z0 = 0.75 * H
            mb.co = [(x, y, z if z <= z0 else z0 + (z - z0) * (H - z0) / (top - z0)) for x, y, z in mb.co]
        spheres = [(c * scale, r * scale, d / scale) for c, r, d in L['spheres']]
        vis = pl.proxy_occlusion(mb.co, mb.nrm, spheres, ground=0.45)     # undersides get some ground bounce
        o = occ['floor'] + (1 - occ['floor']) * vis ** occ['gamma']
        # sunlit upper and outer fronds (high sky visibility): a yellow-green lift of the leaf tint
        leaf = np.zeros(len(mb.co), bool)
        for face, m in zip(mb.faces, mb.mats):
            if m == LEAVES:
                leaf[list(face)] = True
        w = np.clip((vis - 0.45) / 0.4, 0, 1) ** 1.5 * leaf
        lift = 1 + w[:, None] * (np.asarray(S['highlight']) - 1)
        # inner crown: darker with depth inside the crown proxy (on top of the sky visibility)
        cc, cr = spheres[0][0], spheres[0][1]
        depth = np.linalg.norm(np.asarray(mb.co) - np.asarray(cc), axis=1) / cr
        inner = np.where(leaf, S.get('inner_floor', 0.55) + (1 - S.get('inner_floor', 0.55)) * np.clip((depth - 0.15) / 0.6, 0, 1) ** 1.2, 1.0)
        col = np.asarray(mb.tint) * lift * (o * inner)[:, None]
        # value spread: leaf luminance raised to the contrast exponent about the LOD0 leaf mean (the same reference
        # for every LOD), brightened values shifted toward yellow (the sprites' sunlit tops, near-black gaps)
        Y = np.array([0.2126, 0.7152, 0.0722])
        lum = col @ Y
        if lod == 0:
            ref = float(lum[leaf].mean())
        f = np.where(leaf, (np.maximum(lum, 1e-4) / ref) ** (CONTRAST - 1), 1.0)
        col = col * f[:, None]
        bright = np.clip(lum * f / ref - 1, 0, 1) * leaf
        col = col * (1 + bright[:, None] * np.array([0.06, 0.0, -0.3]))
        # floor: no leaf vertex darker than LEAF_FLOOR of its own undarkened tint (luminance), softly (the crown heart
        # seen from below must stay deep green: the dark gaps live in the texture's under-leaflet layer)
        base = np.asarray(mb.base)
        g = (col @ Y) / np.maximum(base @ Y, 1e-6)
        g2 = g + LEAF_FLOOR * np.exp(-(g / LEAF_FLOOR) ** 2)
        lifted = np.where((g > 1e-3)[:, None], col * (g2 / np.maximum(g, 1e-3))[:, None], base * g2[:, None])
        col = np.where(leaf[:, None], lifted, col)
        mb.tint = [tuple(c) for c in col]
        mb.to_object(name, mats, np.ones(len(mb.co)))
        print('LOD', name, 'triangles', mb.triangles())
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(pc.work(SID), 'plant.blend'))


if __name__ == '__main__':
    main()
