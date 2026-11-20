"""Cacti (inside Blender): ribbed sweeps after the MM6 succulents' `ribbed()` (`succ_lib.py`), rebuilt on this batch's
Geo. A body is a polyline with ring radii; each ring has `ribs` x vpr vertices (vpr 2: valley, crest; 1: crest
only, a smooth polygon), valleys creased. u repeats once per rib (valley at whole u, crest at u + 0.5), v follows the
surface length. Bodies close in a rounded cap with an apex vertex.
  plant50/51: a short trunk splitting into four elongated ribbed segments (51 adds orange-red fruit);
  plant52/53: saguaro column with three curved arms (53 adds pale pink flowers);
  plant54:    four olive-yellow columns of different heights, densely spined.
Materials: Body (tiling skin, opaque), Foliage (flowers atlas: fruit as closed goblets, flowers as stars)."""
import math
import numpy as np
from mathutils import Vector
import plant_lib as pl
import clump as cl

UP = Vector((0, 0, 1))


def frames(pts):
    n = len(pts)
    tang = []
    for i in range(n):
        d = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
        tang.append(d.normalized() if d.length > 1e-9 else UP.copy())
    side, _, _ = pl.frame(tang[0])
    out = []
    for i, t in enumerate(tang):
        if i:
            q = tang[i - 1].rotation_difference(t); side = q @ side
            side = (side - t * side.dot(t)).normalized()
        out.append((t, side, t.cross(side)))
    return out


def ribbed(g, pts, radii, ribs, depth, vpr, v_tile, tint, occ, phase=0.0, mat=0, apex=True):
    pts = [Vector(p) for p in pts]
    fr = frames(pts)
    prof = [1.0] if vpr == 1 else [1.0 - depth, 1.0]
    ustep = [0.5] if vpr == 1 else [0.0, 0.5]
    N = ribs * vpr
    rings, vco = [], []
    length = 0.0
    for i, (p, r) in enumerate(zip(pts, radii)):
        if i:
            length += math.hypot((p - pts[i - 1]).length, r - radii[i - 1])
        vco.append(length / v_tile)
        t, a, b = fr[i]
        ring = []
        for k in range(ribs):
            for j in range(vpr):
                ang = phase + 2 * math.pi * (k + ustep[j]) / ribs
                d = a * math.cos(ang) + b * math.sin(ang)
                q = p + d * r * prof[j]
                o = occ(q, d)
                ring.append(g.vert(q, (tint[0] * o, tint[1] * o, tint[2] * o)))
        rings.append(ring)
    uvals = [k + ustep[j] for k in range(ribs) for j in range(vpr)]
    valley = [vpr > 1 and j == 0 for k in range(ribs) for j in range(vpr)]
    for i in range(len(pts) - 1):
        for s in range(N):
            s2 = (s + 1) % N
            u0, u1 = uvals[s], (uvals[s2] if s2 else ribs)
            g.face([rings[i][s], rings[i][s2], rings[i + 1][s2], rings[i + 1][s]],
                   [(u0, vco[i]), (u1, vco[i]), (u1, vco[i + 1]), (u0, vco[i + 1])],
                   ['flat' if valley[x] else None for x in (s, s2, s2, s)], mat)
    if apex:
        tip_p = pts[-1] + fr[-1][0] * radii[-1] * 0.45
        o = occ(tip_p, fr[-1][0])
        tip = g.vert(tip_p, (tint[0] * o, tint[1] * o, tint[2] * o))
        vt = vco[-1] + radii[-1] * 0.6 / v_tile
        for s in range(N):
            s2 = (s + 1) % N
            u0, u1 = uvals[s], (uvals[s2] if s2 else ribs)
            g.face([rings[-1][s], rings[-1][s2], tip], [(u0, vco[-1]), (u1, vco[-1]), ((u0 + u1) / 2, vt)],
                   ['flat' if valley[s] else None, 'flat' if valley[s2] else None, fr[-1][0]], mat)


def segment_path(start, end, R, rings, bend=0.0, pinch=0.55, power=0.55):
    """Elongated pad-like segment: pinched joint at start, widest past the middle, rounded end."""
    start, end = Vector(start), Vector(end)
    axis = end - start
    side = axis.cross(UP)
    side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
    bow = axis.cross(side).normalized()
    pts, radii = [], []
    for i in range(rings + 1):
        t = i / rings
        pts.append(start + axis * t + bow * (bend * axis.length * math.sin(math.pi * t)))
        s = math.sin(math.pi * (0.12 + 0.8 * t)) ** power
        radii.append(R * max(s, pinch if t < 0.3 else 0.0) * (pinch + (1 - pinch) * min(1, t / 0.3)) ** 0.5)
    radii[-1] = max(radii[-1], R * 0.35)
    return pts, radii


def column_path(base, top_z, R, rings, lean=Vector((0, 0, 0)), cap=0.6):
    """Straight column with a rounded top (the last rings close toward the apex)."""
    base = Vector(base)
    pts, radii = [], []
    body = top_z - R * cap
    for i in range(rings + 1):
        t = i / rings
        z = base.z + (body - base.z) * t
        pts.append(Vector((base.x, base.y, z)) + lean * (z - base.z))
        radii.append(R * (1.0 + 0.06 * (1 - t)))
    for t in (0.5, 0.85):
        z = body + R * cap * t
        pts.append(Vector((base.x, base.y, z)) + lean * (z - base.z))
        radii.append(R * math.cos(t * math.pi / 2) ** 0.6)
    return pts, radii


def arm_path(origin, out_dir, out_len, up_len, R, rings):
    """Saguaro arm: leaves the trunk sideways, bends and rises."""
    origin = Vector(origin); out_dir = Vector(out_dir).normalized()
    elbow = origin + out_dir * out_len
    pts, radii = [], []
    for i in range(rings + 1):
        t = i / rings
        a = t * math.pi / 2
        p = origin + out_dir * out_len * math.sin(a) + UP * (out_len * 0.6 * (1 - math.cos(a)))
        pts.append(p)
    top = pts[-1]
    for i in range(1, rings + 1):
        pts.append(top + UP * up_len * i / rings)
    radii = [R * (0.75 + 0.25 * min(1, i / 2)) for i in range(len(pts))]
    for t in (0.5, 0.85):
        pts.append(pts[-1] + UP * R * 0.35)
        radii.append(R * math.cos(t * math.pi / 2) ** 0.6)
    return pts, radii


def make_occ(H, inner=None):
    def occ(p, n):
        o = 0.5 + 0.5 * min(1.0, max(p.z, 0) / (0.3 * H)) ** 0.8
        o *= 0.78 + 0.22 * max(n.z, -0.5) + 0.0
        if inner is not None:
            o *= 0.85 + 0.15 * min(1.0, (Vector((p.x, p.y, 0)) - inner).length / (0.15 * H))
        return min(o, 1.0)
    return occ


LOD = [{'ribs': 1, 'vpr': 2, 'rings': 1.0, 'heads': 1.0, 'seg': 8},
       {'ribs': 1, 'vpr': 1, 'rings': 0.6, 'heads': 0.7, 'seg': 6},
       {'ribs': 0.7, 'vpr': 1, 'rings': 0.35, 'heads': 0.45, 'seg': 5}]


def build(sid):
    sp = cl.Sprite(sid)
    H = sp.H
    rng = np.random.default_rng({'plant50': 50, 'plant51': 50, 'plant52': 52, 'plant53': 52, 'plant54': 54}[sid])
    skin = {'plant50': 'cactus_green', 'plant51': 'cactus_green', 'plant52': 'cactus_saguaro',
            'plant53': 'cactus_saguaro', 'plant54': 'cactus_yellow'}[sid]
    body = pl.material('Body', skin, cutout=False, roughness=0.55, extension='REPEAT',
                       extras={'openyamm_specular': 0.2})
    extras = [body]
    flowers = sid in ('plant51', 'plant53')
    if flowers:
        extras.append(pl.material('Foliage', 'flowers', cutout=True, roughness=0.6,
                                  extras={'openyamm_specular': 0.1, 'openyamm_translucency': 0.2}))
    atlas = pl.Atlas('flowers')
    occ = make_occ(H)
    bodies = []          # (kind, args, ribs, depth, v_tile, tint)
    adorn = []           # heads: (cell, centre, axis, radius, profile, tint)
    if sid in ('plant50', 'plant51'):
        tint = (0.6, 0.66, 0.28)
        segs = [((-0.08, 0.0, -0.02), (-0.08, 0.0, 0.3), 0.12, 0.0),
                ((-0.15, 0.03, 0.2), (-0.45, 0.08, 0.96), 0.14, 0.06),
                ((-0.05, -0.02, 0.24), (-0.03, -0.05, 0.98), 0.14, -0.05),
                ((0.0, -0.08, 0.2), (0.16, -0.22, 0.64), 0.13, 0.08),
                ((0.05, 0.05, 0.36), (0.6, 0.14, 0.58), 0.13, 0.1)]
        for s, e, R, bend in segs:
            bodies.append(('segment', (Vector(s) * H, Vector(e) * H, R * H, bend), 6, 0.1, 0.35, tint))
            if sid == 'plant51' and e[2] > 0.4:
                d = (Vector(e) - Vector(s)).normalized()
                for f in range(int(rng.integers(2, 4))):
                    side = d.cross(UP); side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
                    off = side * rng.uniform(-0.6, 0.6) * R * H + d * R * H * rng.uniform(0.15, 0.45)
                    c = Vector(e) * H + off
                    ax = (d + side * rng.normal(0, 0.4) + UP * 0.3).normalized()
                    adorn.append(('h_tulip', c, ax, 0.035 * H, 'goblet', (1.0, 0.6, 0.45)))
    elif sid in ('plant52', 'plant53'):
        tint = (0.9, 0.95, 0.85)
        bodies.append(('column', (Vector((0, 0, -0.02 * H)), 0.99 * H, 0.06 * H), 10, 0.14, 0.18, tint))
        arms = [((-1, 0.15, 0), 0.47, 0.13, 0.25, 0.042), ((1, -0.2, 0), 0.52, 0.12, 0.18, 0.042),
                ((-0.4, -1, 0), 0.58, 0.08, 0.22, 0.036)]
        for d, z, out, up, R in arms:
            bodies.append(('arm', (Vector((0, 0, z * H)), Vector(d), out * H, up * H, R * H), 8, 0.14, 0.18, tint))
        if sid == 'plant53':
            for k in range(9):
                z = rng.uniform(0.35, 0.95)
                a = rng.uniform(0, 2 * math.pi)
                c = Vector((math.cos(a) * 0.055 * H, math.sin(a) * 0.055 * H, z * H))
                ax = (Vector((math.cos(a), math.sin(a), 0)) + UP * 0.4).normalized()
                adorn.append(('h_star', c, ax, 0.034 * H, 'star', (1.0, 0.85, 0.95)))
            for k in range(5):
                a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.08, 0.14) * H
                c = Vector((math.cos(a) * r, math.sin(a) * r, 0.012 * H))
                adorn.append(('h_star', c, (UP + Vector(rng.normal(0, 0.3, 3))).normalized(), 0.03 * H, 'star',
                              (1.0, 0.85, 0.95)))
    else:
        tint = (0.82, 0.8, 0.72)
        cols = [((-0.08, 0.02), 1.0, 0.11), ((0.03, 0.07), 0.9, 0.09), ((0.1, -0.04), 0.55, 0.075),
                ((0.0, -0.1), 0.42, 0.068)]
        for (x, y), top, R in cols:
            bodies.append(('column', (Vector((x * H, y * H, -0.02 * H)), top * H, R * H), 12, 0.12, 0.2, tint))
    objects = []
    for lod, plan in enumerate(LOD):
        g = pl.Geo()
        for kind, args, ribs, depth, vt, t in bodies:
            nr = max(4, int(round(ribs * plan['ribs'])))
            if kind == 'segment':
                s, e, R, bend = args
                pts, radii = segment_path(s, e, R, max(3, int(round(9 * plan['rings']))), bend)
            elif kind == 'column':
                base, top, R = args
                pts, radii = column_path(base, top, R, max(1, int(round(6 * plan['rings']))))
            else:
                o, d, out, up, R = args
                pts, radii = arm_path(o, d, out, up, R, max(2, int(round(4 * plan['rings']))))
            ribbed(g, pts, radii, nr, depth, plan['vpr'], vt * H, t, occ, phase=0.3)
        keep = adorn[:int(round(len(adorn) * plan['heads']))]
        for cell, c, ax, r, prof, t in keep:
            rings = None if lod == 0 else ([2] if prof == 'goblet' else [])
            pl.head(g, atlas, cell, c, ax, r * (1 + 0.1 * lod), None, t, profile=prof, segments=plan['seg'],
                    rings=rings, mat=1, turn=rng.uniform(0, 6.3))
        objects.append(g.to_object(('Plant', 'Plant_LOD1', 'Plant_LOD2')[lod], extras))
    return objects
