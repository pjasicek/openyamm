"""Blender: build one succulent's LOD meshes and export work/<id>_export.glb (+ <id>.blend for the review renders).
Objects <Base>, <Base>_LOD1.. (linked later by finish.py). Usage: blender --background --python build_model.py -- <id>
  cac8      golden barrel: ribbed sphere (24 ribs) under painted spines, spine fringe cards on the crests
  cac5      candelabra cluster: four segmented wing-ribbed columns and a short side shoot
  cac16     columnar cactus: ribbed trunk forking into two tall arms and a short front arm
  cac7, cac10, cac15  prickly pears: pad trees of bulged double-sided pad cards, fruit / flowers
  cac27     silver desert sage on a stone slab, a dead branch
  snoweed1  dry russet weed clumps (cards)"""
import bpy, math, os, sys
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import succ_lib as sl

SID = sys.argv[sys.argv.index('--') + 1]
sl.reset()
BODY_EXTRAS = {'openyamm_specular': 0.2}
CARD_EXTRAS = {'openyamm_specular': 0.1}
FOLIAGE_EXTRAS = {'openyamm_wind': 0.02, 'openyamm_specular': 0.1, 'openyamm_translucency': 0.3}


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# =========================================================================== cac8 golden barrel
def build_barrel():
    """A squat flattened dome (body width 2.4 m, height 1.95 m): the widest ring at 0.35 of the height, the base
    curving in to 0.59 R on the ground and a flattened crown. 24 ribs (valley + crest per rib, creased valleys)
    under the painted spines of barrel_skin; a cut-out spine shell (barrel_spines) 7 cm above the crests at LOD0-2
    and long irregular spine fringes standing on the crests at LOD0-2, leaning at random so neighbours cross."""
    R, c, a_lo, a_hi = 1.20, 0.68, 0.75, 1.27
    H = c + a_hi
    rng = np.random.default_rng(8)

    def half(z):
        return a_lo if z < c else a_hi

    def profile(deg):
        t = math.radians(deg)
        return R * max(math.cos(t), 0.0) ** 0.62, c + (a_lo if t < 0 else a_hi) * math.sin(t)

    def dome_normal(p):
        a = half(p.z)
        return Vector((p.x / (R * R), p.y / (R * R), (p.z - c) / (a * a))).normalized()
    body = sl.material('Body', 'barrel_skin', roughness=0.55, extras=BODY_EXTRAS)
    spines = sl.material('Spines', 'barrel_spines', cutout=True, roughness=0.5, extras=CARD_EXTRAS)
    plans = [dict(angles=[-65, -45, -25, -6, 12, 28, 44, 58, 71, 83], ribs=24, vpr=2, u_rib=1, shell=8, fins=2),
             dict(angles=[-65, -38, -10, 18, 44, 66, 84], ribs=24, vpr=2, u_rib=1, shell=4, fins=3),
             dict(angles=[-65, -30, 4, 32, 58, 80], ribs=24, vpr=1, u_rib=1, shell=4, fins=5),
             dict(angles=[-65, -18, 30, 66, 86], ribs=10, vpr=1, u_rib=2.4, shell=4, shell_ribs=10, fins=0)]
    rib_v = [float(x) for x in np.random.default_rng(81).uniform(0, 1, 24)]
    objects = []
    for lod, plan in enumerate(plans):
        g = sl.Geo()

        def rings(angles, offset):
            centres, radii = [], []
            for d in angles:
                r, z = profile(d); centres.append(Vector((0, 0, z))); radii.append(r + offset)
            r_top, z_top = profile(90)
            centres.append(Vector((0, 0, z_top - 0.03 + offset * 0.8))); radii.append(0.0)
            return centres, radii

        def occ(p, i, valley):
            o = 0.5 + 0.5 * smooth(p.z / (H * 0.45))
            return o * (0.72 if valley else 1.0)
        centres, radii = rings(plan['angles'], 0.0)
        crest = sl.ribbed(g, centres, radii, plan['ribs'], 0.09, plan['vpr'], 1.0, mat=0, occ=occ,
                          u_rib=plan['u_rib'], rib_v=rib_v)
        g.occlusion(rays=32, distance=0.6, strength=0.5)
        if plan['shell']:
            angles = list(np.linspace(-38, 84, plan['shell']))
            centres, radii = rings(angles, 0.07)
            sl.ribbed(g, centres, radii, plan.get('shell_ribs', 24), 0.0, 1, 1.0, mat=1,
                      u_rib=24 / plan.get('shell_ribs', 24), solid=False,
                      occ=lambda p, i, v: 0.6 + 0.4 * smooth(p.z / (H * 0.45)), normal_fn=dome_normal)
        if plan['fins']:
            # Fringes along the crest lines: each maps a band of the spine tile transposed (v along the crest,
            # u from the crest at 0.5 out past the tile edge into the neighbour's spines), so the areoles' sideways
            # spines stand out of the surface. Few, long cards (every third band per rib, 0.22-0.36 m) leaning
            # at random up to 0.7 rad, so neighbouring fringes cross.
            vband = [0.0]
            for i in range(1, len(crest)):
                vband.append(vband[-1] + (crest[i][0][0] - crest[i - 1][0][0]).length)
            for k in range(plan['ribs']):
                for i in range(len(crest) - 1):
                    if (i + k) % plan['fins'] or not -45 <= plan['angles'][i] <= 76:
                        continue
                    (p0, _), (p1, _) = crest[i][k], crest[i + 1][k]
                    ns = [dome_normal(p0), dome_normal(p1)]
                    along = (p1 - p0).normalized()
                    tilt = rng.uniform(-0.7, 0.7)
                    length = rng.uniform(0.22, 0.36)
                    droop = Vector((0, 0, -0.25 if p0.z < c else 0.0))       # lower spines droop, as in the sprite
                    tops = []
                    for p, n in zip((p0, p1), ns):
                        side = along.cross(n)
                        tops.append(p + ((n * math.cos(tilt) + side * math.sin(tilt)) + droop).normalized() * length
                                    * rng.uniform(0.9, 1.1))
                    pts = [p0 - ns[0] * 0.01, p1 - ns[1] * 0.01, tops[1], tops[0]]
                    pts = [Vector((q.x, q.y, max(q.z, 0.01))) for q in pts]          # nothing below the ground
                    shift = rng.uniform(0, 1)
                    v0, v1 = vband[i] + shift, vband[i + 1] + shift
                    uvs = [(0.5, v0), (0.5, v1), (-0.15, v1), (-0.15, v0)]
                    shade = [0.6 + 0.4 * smooth(p.z / (H * 0.45)) for p in pts]
                    idx = [g.vert(p, o) for p, o in zip(pts, shade)]
                    nrm = [ns[0], ns[1], ns[1], ns[0]]
                    for x, n in zip(idx, nrm):
                        g.ao_normal[x] = n
                    face_n = (pts[1] - pts[0]).cross(pts[2] - pts[1])
                    if face_n.dot(ns[0]) < 0:
                        idx, uvs, nrm = idx[::-1], uvs[::-1], nrm[::-1]
                    g.face(idx, uvs, nrm, 1, solid=False)
        name = 'Cactus' if lod == 0 else f'Cactus_LOD{lod}'
        objects.append(g.to_object(name, [body, spines]))
        print('LOD', name, 'triangles', g.triangles())
    return objects


def column_rings(base, height, R, lean, seg_lengths, per_seg, pinch=0.72, cap=(0.86, 0.5), bend=0.0, side=None):
    """Ring centres/radii of a segmented column: each segment bulges from a pinched joint (pinch x R) to R and back;
    the top rounds over two cap rings to an apex. lean: horizontal offset of the top; bend: extra mid curvature."""
    base = Vector(base); lean = Vector(lean)
    total = sum(seg_lengths)
    scale = (height - R * 0.35) / total
    centres, radii = [], []
    z = 0.0
    for k, L in enumerate(seg_lengths):
        L *= scale
        for j in range(per_seg):
            t = j / per_seg if per_seg > 1 else 0.5
            r = R * (pinch + (1 - pinch) * math.sin(math.pi * t) ** 0.55) if k else R * (0.92 + 0.08 * math.sin(math.pi * t))
            if per_seg == 1:
                r = R * (0.5 + 0.5 * (pinch + 1) / 2)
            centres.append((z + L * t)); radii.append(r)
        z += L
    top = z
    centres += [top + R * 0.12, top + R * 0.28, top + R * 0.35]; radii += [R * cap[0], R * cap[1], 0.0]
    pts = []
    for zz in centres:
        f = zz / (top + R * 0.35)
        off = lean * f ** 1.5 + (side or Vector((0, 0, 0))) * bend * math.sin(math.pi * f)
        pts.append(base + Vector((off.x, off.y, zz)))
    return pts, radii


def build_organ():
    """cac5: four segmented candelabra columns (4 wing ribs, pinched joints) and a shorter one behind, from the
    sprite's column positions; organ_skin tile = one rib x 0.34 m."""
    rng = np.random.default_rng(5)
    body = sl.material('Body', 'organ_skin', roughness=0.5, extras=BODY_EXTRAS)
    H = 3.04
    cols = [  # x, y (depth, + away from the front view), top / H, radius, lean
        (-0.40, 0.06, 0.81, 0.21, (-0.04, 0.0)),
        (-0.06, 0.0, 1.00, 0.22, (0.02, 0.02)),
        (0.20, -0.20, 0.66, 0.21, (0.03, -0.02)),
        (0.47, 0.06, 0.55, 0.20, (0.06, 0.0)),
        (0.10, 0.30, 0.62, 0.19, (0.0, 0.05)),
    ]
    segs = [[float(x) for x in rng.uniform(0.85, 1.15, max(2, round(c[2] * 6)))] for c in cols]
    phases = [float(x) for x in rng.uniform(0, math.pi / 2, len(cols))]
    plans = [dict(vpr=4, per_seg=3, ribs=4, u_rib=1), dict(vpr=2, per_seg=3, ribs=4, u_rib=1),
             dict(vpr=1, per_seg=2, ribs=6, u_rib=4 / 6), dict(vpr=1, per_seg=1, ribs=4, u_rib=1)]
    objects = []
    for lod, plan in enumerate(plans):
        g = sl.Geo()
        for ci, (x, y, top, R, lean) in enumerate(cols):
            pts, radii = column_rings((x, y, 0), top * H, R, Vector((lean[0], lean[1], 0)), segs[ci], plan['per_seg'],
                                      pinch=0.62)
            if lod == 3:                                          # one cap ring
                pts = pts[:-3] + pts[-2:]; radii = radii[:-3] + [radii[-3] * 0.7, 0.0]

            def occ(p, i, valley):
                # per-level gain evens out the mean colour between neighbouring levels (valley creases at LOD0/1)
                return (0.45 + 0.55 * smooth(p.z / 1.4)) * (0.6 if valley else 1.0) * (0.86, 1.0, 0.80, 0.80)[lod]
            sl.ribbed(g, pts, radii, plan['ribs'], 0.55, plan['vpr'], 1 / 0.34, mat=0, occ=occ,
                      u_rib=plan['u_rib'], phase=phases[ci] + (math.pi / 4 if lod == 3 else 0.0), crest_round=0.25)
        g.occlusion(rays=32, distance=0.7, strength=0.6)
        name = 'Cactus' if lod == 0 else f'Cactus_LOD{lod}'
        objects.append(g.to_object(name, [body]))
        print('LOD', name, 'triangles', g.triangles())
    return objects


def bezier(p0, p1, p2, n):
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    return [p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t for t in np.linspace(0, 1, n)]


def build_column():
    """cac16: 8-ribbed trunk forking at 0.6 H into a left arm (to 0.93 H) and a taller right arm (to the top), with a
    short rounded arm in front of the fork; saguaro_skin tile = one rib x 0.26 m."""
    H = 3.10
    body = sl.material('Body', 'saguaro_skin', roughness=0.55, extras=BODY_EXTRAS)
    # (bezier control points, base radius, tip radius, rings at LOD0, phase)
    limbs = [
        (((0.05, 0.0, 0.0), (0.05, 0.0, 0.9), (0.06, 0.0, 1.95)), 0.175, 0.165, 9, 0.0),          # trunk
        (((0.03, 0.02, 1.62), (-0.14, 0.02, 2.25), (-0.33, 0.05, 2.76)), 0.145, 0.135, 9, 0.2),     # left arm
        (((0.08, 0.0, 1.75), (0.22, -0.02, 2.40), (0.34, -0.02, 2.95)), 0.150, 0.140, 10, 0.4),     # right arm
        (((0.08, -0.07, 1.50), (0.18, -0.15, 1.85), (0.20, -0.17, 2.24)), 0.150, 0.150, 6, 0.1),    # front arm
    ]
    plans = [dict(vpr=2, ribs=8, u_rib=1, ring=1.0, gain=0.97), dict(vpr=2, ribs=8, u_rib=1, ring=0.55, gain=1.0),
             dict(vpr=1, ribs=8, u_rib=1, ring=0.4, gain=0.80), dict(vpr=1, ribs=5, u_rib=8 / 5, ring=0.3, gain=0.80)]
    objects = []
    for lod, plan in enumerate(plans):
        g = sl.Geo()
        for li, (ctrl, r0, r1, n, phase) in enumerate(limbs):
            count = max(2, int(round(n * plan['ring'])))
            pts = bezier(*ctrl, count + 1)
            # gentle swelling along each limb (fixed per limb, sampled the same at every level)
            radii = [(r0 + (r1 - r0) * i / count) * (1 + 0.07 * math.sin(2.3 * li + 7.0 * i / count)
                                                      + 0.04 * math.sin(1.1 * li + 15.0 * i / count))
                     for i in range(count + 1)]
            if li:                                                   # arms start inside the trunk
                pts = pts[:]
            tip = pts[-1]; d = (pts[-1] - pts[-2]).normalized()
            caps = [(0.13, 0.82), (0.24, 0.45)] if lod < 2 else [(0.18, 0.62)]
            for f, rf in caps:
                pts.append(tip + d * r1 * f * 1.4); radii.append(r1 * rf)
            pts.append(tip + d * r1 * 0.42); radii.append(0.0)

            def occ(p, i, valley):
                return (0.5 + 0.5 * smooth(p.z / 1.2)) * (0.7 if valley else 1.0) * plan['gain']
            sl.ribbed(g, pts, radii, plan['ribs'], 0.12, plan['vpr'], 1 / 0.26, mat=0, occ=occ, u_rib=plan['u_rib'],
                      phase=phase, rib_v=[0.5 * (k % 2) + 0.1 * li for k in range(plan['ribs'])])
        g.occlusion(rays=32, distance=0.5, strength=0.6)
        name = 'Cactus' if lod == 0 else f'Cactus_LOD{lod}'
        objects.append(g.to_object(name, [body]))
        print('LOD', name, 'triangles', g.triangles())
    return objects


# =========================================================================== prickly pears
PAD_STYLES = {
    # cac7: dense dome of long upright pads (ovals 2:1): many roots leaning out more toward the rim, short chains
    'cac7': dict(H=1.68, seed=7, texture='pads_cac7', ovals=[(0.21, 0.45), (0.22, 0.45), (0.24, 0.42)],
                 cells=[0.45, 0.35, 0.20], roots=50, foot=(0.64, 0.46), root_lean=(0.05, 0.45), size=(0.19, 0.44),
                 size_jitter=0.15, decay=0.86, children=[0.25, 0.60, 0.15], spread=0.30, twist=0.45, depth=3,
                 inner_depth=1, offset=0.45, fruits=6, fruit_cells=[0, 1], fruit_size=0.035, flowers=0, grid=3,
                 width_target=2.0, keep=[1.0, 1.0, 1.0, 0.62], grow=[1.0, 1.0, 1.0, 1.25]),
    # cac10: spreading mound of round pads branching outward and up, brown-red fruit on the top rims
    'cac10': dict(H=2.04, seed=10, texture='pads_cac10', ovals=[(0.36, 0.44), (0.37, 0.43), (0.34, 0.44)],
                  cells=[0.40, 0.35, 0.25], roots=16, foot=(0.58, 0.46), root_lean=(0.1, 0.7), size=(0.36, 0.42),
                  size_jitter=0.15, decay=0.84, children=[0.15, 0.50, 0.30, 0.05], spread=0.45, twist=0.5, depth=3,
                  inner_depth=1, offset=0.6, fruits=16, fruit_cells=[0, 1], fruit_size=0.045, flowers=0, grid=4,
                  width_target=3.05, keep=[1.0, 1.0, 1.0, 0.7], grow=[1.0, 1.0, 1.0, 1.25]),
    # cac15: low sprawling pads, a few corky purple-brown old pads in the middle, pink fruit and flowers on the rims
    'cac15': dict(H=1.70, seed=15, texture='pads_cac15', ovals=[(0.34, 0.43), (0.33, 0.43), (0.35, 0.42)],
                  cells=[0.45, 0.55, 0.0], roots=22, foot=(0.58, 0.40), root_lean=(0.1, 0.65), size=(0.22, 0.27),
                  size_jitter=0.18, decay=0.9, children=[0.10, 0.55, 0.35], spread=0.32, twist=0.6, depth=3,
                  inner_depth=1, offset=0.6, fruits=20, fruit_cells=[0, 1], fruit_size=0.04, flowers=7, grid=4,
                  width_target=2.8, dry_core=0.95, reach=1.0, keep=[1.0, 1.0, 1.0, 0.7], grow=[1.0, 1.0, 1.0, 1.25]),
}


def rotate(v, axis, angle):
    return Matrix.Rotation(angle, 3, Vector(axis).normalized()) @ Vector(v)


def grow_pads(st):
    """Pad trees: root pads round an elliptical footprint leaning outward, each pad carrying 0-3 children on its
    upper rim, turned in the parent's plane (toward the side they sit on) and twisted about their own long axis."""
    rng = np.random.default_rng(st['seed'])
    pads = []
    queue = []
    for r in range(st['roots']):
        ang = rng.uniform(0, 2 * math.pi); rad = math.sqrt(rng.uniform(0.05, 1.0))
        base = Vector((math.cos(ang) * st['foot'][0] * rad, math.sin(ang) * st['foot'][1] * rad, 0.0))
        out = Vector((math.cos(ang), math.sin(ang), 0)) if base.length > 1e-3 else Vector((1, 0, 0))
        lean = rng.uniform(*st['root_lean']) * (0.4 + 0.6 * rad)
        up = (Vector((0, 0, 1)) * math.cos(lean) + out * math.sin(lean)).normalized()
        # pad faces roughly tangent to the footprint (seen face-on from outside), with scatter
        normal = rotate(out, up, rng.normal(0, 0.6))
        queue.append((base, up, normal, 1.0, -st['inner_depth'] if rad < 0.55 else 0))
    while queue:
        attach, up, normal, scale, depth = queue.pop(0)
        w0, h0 = st['size']
        f = scale * (1 + rng.normal(0, st['size_jitter']))
        w, h = w0 * f, h0 * f
        normal = (normal - up * normal.dot(up)).normalized()
        cell = int(rng.choice(len(st['cells']), p=st['cells']))
        horizontal = math.hypot(attach.x / st['foot'][0], attach.y / st['foot'][1])
        if st.get('dry_core') and depth <= 0 and horizontal < st['dry_core'] and rng.uniform() < 0.85:
            cell = 2; w *= 1.3; h *= 1.1             # old corky pads: broad and low
        pads.append(dict(attach=attach, up=up, normal=normal, w=w, h=h, cell=cell, depth=depth))
        if depth + 1 >= st['depth'] or horizontal > st.get('reach', 9.0):
            continue
        n = int(rng.choice(len(st['children']), p=st['children']))
        right = up.cross(normal).normalized()
        for c in range(n):
            off = rng.uniform(-st['offset'], st['offset'])
            t = math.acos(max(min(off, 1), -1))                     # point on the upper rim
            rim = attach + up * (h * 0.5) + (right * math.cos(t) * w * 0.5 + up * math.sin(t) * h * 0.5) * 0.85
            cu = rotate(up, normal, -off * st['spread'] * 1.6 + rng.normal(0, st['spread'] * 0.4))
            if cu.z < 0.25:
                cu = (cu + Vector((0, 0, 0.6))).normalized()
            cn = rotate(normal, cu, rng.normal(0, st['twist']))
            queue.append((rim - cu * 0.03, cu, cn, scale * st['decay'], depth + 1))
    return pads


def build_pads():
    st = PAD_STYLES[SID]
    rng = np.random.default_rng(st['seed'] + 100)
    pads = grow_pads(st)
    # uniform scale so the highest pad top reaches H and the clump keeps the sprite's width / height ratio
    tops = [(p['attach'] + p['up'] * p['h']).z for p in pads]
    xs = [p['attach'].x + s * p['w'] * 0.5 for p in pads for s in (-1, 1)]
    k = st['H'] / max(tops)
    for p in pads:
        p['attach'] = p['attach'] * k; p['w'] *= k; p['h'] *= k
    width = (max(xs) - min(xs)) * k
    print('PADS', len(pads), 'width', round(width, 2), 'target', st['width_target'])
    # fruit / flowers on the upper rims of outer pads
    top_depth = max(p['depth'] for p in pads)
    leaves = [i for i, p in enumerate(pads) if p['depth'] >= top_depth - 1 and p['cell'] != 2] or list(range(len(pads)))
    fruits = []
    for f in range(st['fruits'] + st['flowers']):
        pi = int(rng.choice(leaves)); p = pads[pi]
        right = p['up'].cross(p['normal']).normalized()
        t = rng.uniform(0.35, 2.8)
        centre = p['attach'] + p['up'] * (p['h'] * 0.5)
        rim_dir = (right * math.cos(t) * p['w'] * 0.5 + p['up'] * math.sin(t) * p['h'] * 0.5)
        pos = centre + rim_dir * 0.97
        fruits.append(dict(pos=pos, axis=(rim_dir.normalized() + Vector((0, 0, 0.6))).normalized(),
                           cell=int(rng.choice(st['fruit_cells'])), flower=f >= st['fruits'], normal=p['normal'],
                           size=st['fruit_size'] * rng.uniform(0.8, 1.2), pad=pi))
    mat = sl.material('Pads', st['texture'], cutout=True, roughness=0.55, extension='EXTEND',
                      extras={'openyamm_specular': 0.15})
    grids = [st['grid'], 3 if st['grid'] == 4 else 2, 2, 2]
    objects = []
    order = sorted(range(len(pads)), key=lambda i: (pads[i]['depth'], -pads[i]['w']))
    for lod in range(4):
        g = sl.Geo()
        keep = order[:int(round(len(pads) * st['keep'][lod]))]
        grow = st['grow'][lod]

        def occ(q):
            return 0.5 + 0.5 * smooth(q.z / (st['H'] * 0.55))
        for i in keep:
            p = pads[i]
            sl.pad(g, p['attach'], p['up'], p['normal'], p['w'] * grow, p['h'] * grow, p['cell'],
                   st['ovals'][p['cell']], grids[lod], 0.10 * p['w'], occ_fn=occ)
        kept = set(keep)
        for f in fruits:
            if lod >= 2 and f['flower'] or f['pad'] not in kept:     # no fruit without its pad
                continue
            if f['flower']:
                a, b, n = sl.frame(f['axis'])
                size = f['size'] * 2.2
                sl.card(g, f['pos'] - b * size * 0.5, a * size, b * size, (0.75, 0.75, 1.0, 1.0),
                        lambda q, n=n: n, lambda q: 1.0)
                continue
            u0 = 0.5 + 0.125 * f['cell']
            segs, rings = [(5, 3), (5, 3), (4, 2), (4, 2)][lod]
            sl.ellipsoid(g, f['pos'] + f['axis'] * f['size'] * 0.9, f['axis'], f['size'] * 0.75, f['size'] * 1.1, segs, rings,
                         (u0 + 0.01, 0.51, u0 + 0.115, 0.615), occ_fn=lambda q: 0.85)
        for i, v in enumerate(g.v):                         # nothing below the ground
            if v.z < 0:
                g.v[i] = Vector((v.x, v.y, 0.0))
        g.occlusion(rays=32, distance=0.45, strength=0.65)
        name = 'Cactus' if lod == 0 else f'Cactus_LOD{lod}'
        objects.append(g.to_object(name, [mat]))
        print('LOD', name, 'triangles', g.triangles())
    return objects


# =========================================================================== shrubs (cards)
CELLS = [(0.0, 0.0, 0.5, 0.5), (0.5, 0.0, 1.0, 0.5), (0.0, 0.5, 0.5, 1.0), (0.5, 0.5, 1.0, 1.0)]


def clump_cards(rng, centre, radius, height, count, cells, size, inner=0, inner_cell=2, lean=0.5):
    """Fan cards of one shrub clump: bases scattered in the clump's footprint, leaning out from its centre (more at
    the rim), turned to face outward; inner cards are smaller, darker and upright."""
    cards = []
    for k in range(count + inner):
        is_inner = k >= count
        ang = rng.uniform(0, 2 * math.pi); rad = math.sqrt(rng.uniform()) * radius * (0.45 if is_inner else 0.8)
        base = centre + Vector((math.cos(ang) * rad, math.sin(ang) * rad, 0.0))
        out = Vector((math.cos(ang), math.sin(ang), 0.0))
        tilt = (rad / max(radius, 1e-6)) * lean + rng.normal(0, 0.12)
        face_yaw = ang + rng.normal(0, 0.5)
        facing = Vector((math.cos(face_yaw), math.sin(face_yaw), 0.0))
        right = Vector((0, 0, 1)).cross(facing).normalized()
        up = (Vector((0, 0, 1)) * math.cos(tilt) + out * math.sin(tilt)).normalized()
        sz = height * rng.uniform(*size) * (0.75 if is_inner else 1.0)
        cards.append(dict(base=base, right=right * sz * rng.uniform(1.0, 1.3), up=up * sz,
                          cell=inner_cell if is_inner else int(rng.choice(cells)), keep=rng.uniform() + (0 if is_inner else 0.6),
                          shade=0.45 if is_inner else 1.0, centre=centre, height=height, radius=radius))
    return cards


def emit_cards(g, cards, fraction, grow, mat):
    for c in sorted(cards, key=lambda c: -c['keep'])[:int(round(len(cards) * fraction))]:
        base, right, up = c['base'], c['right'] * grow, c['up'] * grow
        own = right.cross(up).normalized()
        centre = c['centre'] + Vector((0, 0, c['height'] * 0.35))

        def nfn(p, own=own, centre=centre):
            outward = (p - centre).normalized()
            n = own if own.dot(outward) >= 0 else -own
            return (n * 0.45 + outward * 0.55).normalized()

        def ofn(p, c=c):
            h = max(p.z - c['base'].z, 0.0) / (c['height'] * grow)
            r = min(Vector((p.x - c['centre'].x, p.y - c['centre'].y)).length / c['radius'], 1.0)
            return (0.32 + 0.68 * min(h * 1.5, 1.0) ** 0.9 * (0.8 + 0.2 * r)) * c['shade']
        sl.card(g, base, right, up, CELLS[c['cell']], nfn, ofn, mat=mat)


def shell_cards(rng, centre, radius, height, count, cells, size, core=3, core_cell=2):
    """Puff cards on a dome round one clump (facing outward, up axis vertical-ish, bases on the shell) and a few
    darker crossed cards in its core."""
    cards = []
    mid = centre + Vector((0, 0, height * 0.42))
    for k in range(count):
        while True:
            d = Vector(rng.normal(0, 1, 3)).normalized()
            if d.z > -0.15:
                break
        pos = mid + Vector((d.x * radius, d.y * radius, d.z * height * 0.55)) * rng.uniform(0.62, 0.85)
        normal = Vector((d.x / radius, d.y / radius, d.z / (height * 0.55))).normalized()
        right = Vector((0, 0, 1)).cross(normal)
        if right.length < 0.3:
            a = rng.uniform(0, 2 * math.pi); right = Vector((math.cos(a), math.sin(a), 0))
        right.normalize()
        up = normal.cross(right).normalized()
        if up.z < 0:
            up = -up
        up = (up + Vector((0, 0, 0.5))).normalized()
        sz = radius * rng.uniform(*size)
        base = pos - up * sz * 0.45
        base.z = max(base.z, centre.z)
        cards.append(dict(base=base, right=right * sz, up=up * sz, cell=int(rng.choice(cells)),
                          keep=rng.uniform() + 0.5, shade=1.0, centre=centre, height=height, radius=radius))
    for k in range(core):
        a = math.pi * k / core + rng.uniform(0, 0.3)
        right = Vector((math.cos(a), math.sin(a), 0))
        cards.append(dict(base=centre.copy(), right=right * radius * 1.5, up=Vector((0, 0, height * 0.95)),
                          cell=core_cell, keep=rng.uniform() * 0.6, shade=0.55, centre=centre, height=height,
                          radius=radius))
    return cards


def build_sage():
    """cac27: a layered stone slab (displaced ellipse, rock_cac27 tiled) under six silver sage clumps of fan cards
    (sage_cac27 cells 0/1, darker cell 2 inside), and a grey dead branch rising to the right (cell 3 strip)."""
    rng = np.random.default_rng(27)
    rock = sl.material('Rock', 'rock_cac27', roughness=0.85, extras={'openyamm_specular': 0.15})
    fol = sl.material('Foliage', 'sage_cac27', cutout=True, roughness=0.8, extras=FOLIAGE_EXTRAS)
    RX, RY, RH = 1.72, 0.95, 0.70
    bumps = [(rng.uniform(0, 2 * math.pi), rng.uniform(0.2, 1.0), rng.uniform(-0.12, 0.12)) for _ in range(9)]

    def rock_height(x, y):
        r = math.hypot(x / RX, y / RY)
        base = RH * (1 - 0.45 * r ** 8) * (0.72 + 0.32 * (-x / RX)) * (0.9 + 0.2 * (y / RY))
        for ang, rr, amp in bumps:
            bx, by = math.cos(ang) * rr * RX * 0.7, math.sin(ang) * rr * RY * 0.7
            base += amp * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / 0.18)
        return max(base, 0.04)
    rim_noise = [float(x) for x in rng.uniform(0.9, 1.08, 28)]
    clumps = [((-0.95, 0.05), 0.55, 1.05), ((-0.45, 0.20), 0.65, 1.30), ((0.05, 0.25), 0.60, 1.20),
              ((0.45, -0.05), 0.48, 0.80), ((0.90, 0.10), 0.42, 0.62), ((-0.30, -0.35), 0.45, 0.70),
              ((0.30, -0.40), 0.40, 0.55)]
    cards = []
    for (x, y), radius, height in clumps:
        z = rock_height(x, y) - 0.04
        cards += shell_cards(rng, Vector((x, y, z)), radius, height, 16, [0, 1], (0.9, 1.25))
    # dead branch: a bent tapering tube with a short fork
    branch = [Vector((0.10, 0.12, rock_height(0.1, 0.12) + 0.2)), Vector((0.45, 0.14, 0.95)), Vector((0.80, 0.16, 1.22)),
              Vector((1.08, 0.18, 1.40))]
    plans = [dict(rock=(28, [0, 0.35, 0.6, 0.8, 0.92, 0.98]), cards=(1.0, 1.0), branch=5),
             dict(rock=(18, [0, 0.5, 0.8, 0.97]), cards=(0.6, 1.12), branch=4),
             dict(rock=(12, [0, 0.6, 0.96]), cards=(0.36, 1.25), branch=3),
             dict(rock=(8, [0, 0.95]), cards=(0.2, 1.4), branch=0)]
    objects = []
    for lod, plan in enumerate(plans):
        g = sl.Geo()
        segs, radii = plan['rock']
        rings = len(radii)
        rows = []
        for i in range(rings + 1):
            t = radii[i] if i < rings else 1.03
            row = []
            for k in range(segs):
                a = 2 * math.pi * k / segs
                jitter = (1 + 0.07 * math.sin(a * 3 + 1.3) + 0.05 * math.sin(a * 7 + 0.4)) * rim_noise[k * 28 // segs]
                rr = t * jitter
                x, y = math.cos(a) * RX * rr, math.sin(a) * RY * rr
                z = 0.0 if i == rings else rock_height(x, y)
                row.append(g.vert((x, y, z), 0.55 + 0.45 * min(z / RH, 1.0) if i < rings else 0.5))
            rows.append(row)
        for i in range(rings):
            for k in range(segs):
                k2 = (k + 1) % segs
                idx = [rows[i][k], rows[i + 1][k], rows[i + 1][k2], rows[i][k2]]
                uvs = [(g.v[j].x * 1.4 + g.v[j].y * 0.4, -g.v[j].y * 1.2 - g.v[j].z * 2.2) for j in idx]
                if i == 0:                                   # faceted stone: flat shading
                    g.face(idx[1:], uvs[1:], ['flat'] * 3, 0)
                else:
                    g.face(idx, uvs, ['flat'] * 4, 0)
        rock_g = g
        if plan['branch']:
            sides = plan['branch']
            for (a, b, ra, rb) in ((branch[0], branch[1], 0.06, 0.045), (branch[1], branch[2], 0.045, 0.03),
                                   (branch[2], branch[3], 0.03, 0.012)):
                fa, fb, _ = sl.frame(b - a)
                ring_a, ring_b = [], []
                for k in range(sides):
                    ang = 2 * math.pi * k / sides
                    d = fa * math.cos(ang) + fb * math.sin(ang)
                    ring_a.append(g.vert(a + d * ra, 0.75)); ring_b.append(g.vert(b + d * rb, 0.9))
                for k in range(sides):
                    k2 = (k + 1) % sides
                    u0, u1 = 0.5 + 0.125 * k / sides, 0.5 + 0.125 * (k + 1) / sides
                    g.face([ring_a[k], ring_a[k2], ring_b[k2], ring_b[k]], [(u0, 0.98), (u1, 0.98), (u1, 0.52), (u0, 0.52)],
                           None, 1)
        g.occlusion(rays=32, distance=0.5, strength=0.6)
        bvh = g.bvh()
        h = sl.Geo()
        emit_cards(h, cards, *plan['cards'], mat=1)
        h.occlusion(rays=16, distance=0.4, strength=0.5, floor=True, extra_bvh=bvh)
        # one object: rock + branch faces, then the cards
        base = len(g.v)
        g.v += h.v; g.occ += h.occ
        for f, uv, nr, m, so in zip(h.faces, h.uvs, h.norms, h.mats, h.solid):
            g.faces.append(tuple(i + base for i in f)); g.uvs.append(uv); g.norms.append(nr); g.mats.append(m)
            g.solid.append(so)
        name = 'Shrub' if lod == 0 else f'Shrub_LOD{lod}'
        objects.append(g.to_object(name, [rock, fol]))
        print('LOD', name, 'triangles', g.triangles())
    return objects


def build_weeds():
    """snoweed1: dry russet weeds: a tall clump right of centre, a lower one left, low grass tufts at the right
    edge (weeds_snoweed1 cells 0-2 twig fans, cell 3 tufts)."""
    rng = np.random.default_rng(91)
    fol = sl.material('Foliage', 'weeds_snoweed1', cutout=True, roughness=0.85, extras=FOLIAGE_EXTRAS)
    clumps = [((0.35, 0.0), 0.40, 1.50, 16, [0, 1]), ((-0.70, 0.10), 0.36, 0.95, 12, [0, 1, 2]),
              ((-0.15, -0.20), 0.25, 0.65, 6, [2]), ((1.05, 0.05), 0.35, 0.42, 8, [3]),
              ((-1.15, -0.05), 0.25, 0.38, 5, [3])]
    cards = []
    for (x, y), radius, height, count, cells in clumps:
        cards += clump_cards(rng, Vector((x, y, 0.0)), radius, height, count, cells, (0.85, 1.0), inner=0, lean=0.5)
    plans = [(1.0, 1.0), (0.6, 1.06), (0.36, 1.15), (0.22, 1.25)]
    objects = []
    for lod, plan in enumerate(plans):
        g = sl.Geo()
        emit_cards(g, cards, *plan, mat=0)
        g.occlusion(rays=12, distance=0.3, strength=0.3)
        name = 'Shrub' if lod == 0 else f'Shrub_LOD{lod}'
        objects.append(g.to_object(name, [fol]))
        print('LOD', name, 'triangles', g.triangles())
    return objects


BUILDERS = {'cac27': build_sage, 'snoweed1': build_weeds, 'cac7': build_pads, 'cac10': build_pads, 'cac15': build_pads, 'cac16': build_column, 'cac8': build_barrel, 'cac5': build_organ}

objects = BUILDERS[SID]()
sl.export(objects, SID)
