#!/usr/bin/env python3
"""Eyes for head 5 (user review 2026-10-20; see head5_fix.py): the head texture holds no painted eye under the removed
horns (a shadowed socket with an ivory spill), so each eye is a low-poly ellipsoid lens (8 segments x 5 rings,
semi-axes 2.4 cm along the head, 1.6 cm up, 1.1 cm deep), centred 4 mm under the skin at the removed right horn's root
and at its mirror image across the head on the left (that horn's root lies in a pocket behind a skin flap),
rigid on Head5. Its UVs are a flat projection in the lens frame into one cell of the free sixth tile of the head atlas
(tile u 2/3..1, v 0..0.5, no face uses it), shared by both eyes (the left eye mirrored).
Writes work/head5_eyes.npz (verts, faces, per-corner uv) and work/head5_eye_cell.json (the cell in UV and pixels).
Usage: head5_eyes.py   (reads work/mesh_r78.npz, the picked candidate's rest geometry)"""
import json
import numpy as np
from scipy.spatial import cKDTree

c = np.load('work/mesh_r78.npz'); v, f = c['verts'], c['faces']; mat = (c['wuv'].reshape(-1, 3, 2)[:, 0, 0] // 2).astype(int)
W = np.load('work/weights_r78.npz'); names = [str(x) for x in W['names']]; h5 = W['weights'][:, names.index('Head5')]
skin = np.where((mat == 1) & (h5[f] > .99).all(1))[0]          # head 5 faces (the horns are already gone in Blender)
# the removed horns' roots (head5_fix.py HORNS, root = the quarter of each horn's vertices nearest the skin)
ROOTS = {'right': (0.712, -1.186, 1.401), 'left': (0.874, -1.200, 1.412)}
A, B, D, SINK = .024, .016, .011, .004
CELL = (1088 / 1536, 1 - 896 / 1024, 1280 / 1536, 1 - 704 / 1024)   # u0, v0, u1, v1: 192 px square in the free tile


def _unused(p, a, b, c_):
    # Ericson, Real-Time Collision Detection 5.1.5
    ab, ac, ap = b - a, c_ - a, p - a
    d1, d2 = ab @ ap, ac @ ap
    if d1 <= 0 and d2 <= 0:
        return a
    bp = p - b; d3, d4 = ab @ bp, ac @ bp
    if d3 >= 0 and d4 <= d3:
        return b
    vc = d1 * d4 - d3 * d2
    if vc <= 0 and d1 >= 0 and d3 <= 0:
        return a + d1 / (d1 - d3) * ab
    cp = p - c_; d5, d6 = ab @ cp, ac @ cp
    if d6 >= 0 and d5 <= d6:
        return c_
    vb = d5 * d2 - d1 * d6
    if vb <= 0 and d2 >= 0 and d6 <= 0:
        return a + d2 / (d2 - d6) * ac
    va = d3 * d6 - d5 * d4
    if va <= 0 and d4 - d3 >= 0 and d5 - d6 >= 0:
        return b + (d4 - d3) / ((d4 - d3) + (d5 - d6)) * (c_ - b)
    den = 1 / (va + vb + vc)
    return a + ab * vb * den + ac * vc * den


tri = v[f[skin]]; cen = tri.mean(1); tree = cKDTree(cen)
fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); fn /= np.linalg.norm(fn, axis=1, keepdims=True)
SEG, RINGS = 8, 5
hv = v[np.unique(f[skin])]; snout = hv[hv[:, 1] < hv[:, 1].min() + .03].mean(0)
FWD = snout - hv.mean(0); FWD /= np.linalg.norm(FWD); LAT = np.cross(FWD, [0, 0, 1.]); LAT /= np.linalg.norm(LAT)
if LAT[0] < 0:
    LAT = -LAT                                   # +x: the hydra's left
UPH = np.cross(FWD, LAT)
MID = hv.mean(0)
print('HEAD5 frame fwd', np.round(FWD, 3).tolist(), 'lat', np.round(LAT, 3).tolist(), 'up', np.round(UPH, 3).tolist())
verts, faces, uvs = [], [], []
for side, root in ROOTS.items():
    p = np.array(root)
    if side == 'left':  # its horn root lies in a pocket behind a skin flap: mirror the right eye across the head instead
        p = RIGHT - 2 * ((RIGHT - MID) @ LAT) * LAT
    # lens axis from the head's own frame (the skin under the horns is a ragged socket whose normals point anywhere):
    # sideways, a little forward and up, as the master's eyes look; the lens sits where that axis, cast inward, meets
    # the skin
    n = (-LAT if side == 'right' else LAT) * .75 + FWD * .45 + UPH * .3; n /= np.linalg.norm(n)
    o, dvec, best = p + .05 * n, -n, None
    for i in tree.query_ball_point(p, .08):
        a0, e1, e2 = tri[i, 0], tri[i, 1] - tri[i, 0], tri[i, 2] - tri[i, 0]
        h = np.cross(dvec, e2); det = e1 @ h
        if abs(det) < 1e-12:
            continue
        sv_ = o - a0; uu = (sv_ @ h) / det; q = np.cross(sv_, e1); vv = (dvec @ q) / det; tt = (e2 @ q) / det
        if uu >= 0 and vv >= 0 and uu + vv <= 1 and tt > 0 and (best is None or tt < best):
            best = tt
    surf = o + best * dvec
    if side == 'right':
        RIGHT = surf
    hf = FWD * [1, 1, 0]; t = hf - (hf @ n) * n; t /= np.linalg.norm(t); up = np.cross(n, t)  # level: upright slit
    if up[2] < 0:
        up = -up
    centre = surf - SINK * n
    print('EYE', side, 'skin point', np.round(surf, 4).tolist(), 'normal', np.round(n, 3).tolist())
    base = len(verts)
    # rings from the outward pole (+n) to the inward pole (-n); local coords (x along t, y along up, z along n)
    loc = [(0, 0, 1)]
    for r in range(1, RINGS):
        th = np.pi * r / RINGS
        for s in range(SEG):
            ph = 2 * np.pi * s / SEG
            loc.append((np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)))
    loc.append((0, 0, -1))
    loc = np.array(loc)
    for x, y, z in loc:
        verts.append(centre + A * x * t + B * y * up + D * z * n)
    mirror = -1 if side == 'left' else 1        # both eyes look forward with the same painted iris
    uv_of = lambda i: ((CELL[0] + CELL[2]) / 2 + mirror * loc[i][0] * (CELL[2] - CELL[0]) / 2,
                       (CELL[1] + CELL[3]) / 2 + loc[i][1] * (CELL[3] - CELL[1]) / 2)
    idx = lambda r, s: 1 + (r - 1) * SEG + s % SEG
    quads = []
    for s in range(SEG):
        quads.append((0, idx(1, s), idx(1, s + 1)))
    for r in range(1, RINGS - 1):
        for s in range(SEG):
            a_, b_, c2, d_ = idx(r, s), idx(r + 1, s), idx(r + 1, s + 1), idx(r, s + 1)
            quads += [(a_, b_, c2), (a_, c2, d_)]
    last = len(loc) - 1
    for s in range(SEG):
        quads.append((idx(RINGS - 1, s), last, idx(RINGS - 1, s + 1)))
    for q in quads:
        pa, pb, pc = (verts[base + i] for i in q)
        # outward winding: the face normal must point away from the lens centre
        if np.cross(pb - pa, pc - pa) @ ((pa + pb + pc) / 3 - centre) < 0:
            q = (q[0], q[2], q[1])
        faces.append([base + i for i in q]); uvs += [uv_of(i) for i in q]
np.savez('work/head5_eyes.npz', verts=np.array(verts), faces=np.array(faces), uv=np.array(uvs))
cell_px = {'base_1536x1024': [1088, 704, 1280, 896], 'half_768x512': [544, 352, 640, 448]}
json.dump({'uv': CELL, 'px': cell_px, 'semi_axes_m': [A, B, D], 'sink_m': SINK}, open('work/head5_eye_cell.json', 'w'), indent=1)
print('EYES', len(faces), 'faces', len(verts), 'verts')
