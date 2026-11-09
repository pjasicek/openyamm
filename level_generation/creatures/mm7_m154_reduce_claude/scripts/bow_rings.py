#!/usr/bin/env python3
"""Bow LODs by ring removal (the m154 bow is a stack of 62 octagon rings along +Y, make_bow.py: one ring per 24
reference rows, planar UVs per ring, an octagon cap at each tip). A quadric collapse kinks such limbs below ~50 %;
dropping whole rings keeps the round section exactly. Each level greedily drops the ring whose vertices lie closest
to the straight bridge between its kept neighbours, until the level's ring budget or its REA_BOW_TOL (metres per level, default 3 / 8 / 15 / 30 mm) is reached.
Fixed at LOD0: the fist band (rings within 2 cm of the right-hand y range from grip_gate_bow.py, so every grip face stays the source
face) and the three rings at each tip (string ends). Kept segments copy the source triangles; bridges use the same
quad split. LOD2/LOD3 use the inscribed diamond (octagon vertices 0, 2, 4, 6) of each kept ring, which stays inside
the octagon and so inside the fist. Vertices keep their source positions, normals and UVs.
Usage: bow_rings.py <grip json> <rings LOD0,LOD1,LOD2,LOD3> -> work/bow_lod<N>.npz, prints tris and max bridge error"""
import json, os, sys
import numpy as np
d = np.load('work/bow.npz'); V, N, UV, F = d['verts'], d['normals'], d['uv'], d['faces']
grip = json.load(open(sys.argv[1]))['right_band_y']; budgets = [int(x) for x in sys.argv[2].split(',')]
ys = np.unique(np.round(V[:, 1], 5)); ring = np.searchsorted(ys, np.round(V[:, 1], 5)); R = len(ys)
# per ring: its 8 vertices ordered by angle about the ring centre in the (x, z) section
order = []
for i in range(R):
    ids = np.flatnonzero(ring == i); c = V[ids].mean(0); s = V[ids] - c
    ang = np.arctan2(s[:, 2] / (np.abs(s[:, 2]).max() + 1e-9), s[:, 0] / (np.abs(s[:, 0]).max() + 1e-9))
    ang = np.where(ang < -np.pi + 1e-3, np.pi, ang)  # the k=4 vertex sits at +-pi (z ~ -0): one side, or rings rotate
    order.append(ids[np.argsort(ang)])
order = np.array(order)                                                     # (R, 8)
fr = ring[F]; cap = (fr[:, 0] == fr[:, 1]) & (fr[:, 1] == fr[:, 2])
lo, hi = min(grip[0], grip[2]) - 0.02, max(grip[1], grip[3]) + 0.02
band = [i for i in range(R) if lo <= ys[i] <= hi]
# LOD0 keeps the whole fist band and three rings at each tip; LOD1 the band and the tip rings; LOD2/3 only the band's
# end rings and the tip rings (their hands are decimated too)
FIXED = [{0, 1, 2, R - 3, R - 2, R - 1} | set(band), {0, R - 1} | set(band), {0, R - 1, band[0], band[-1]},
         {0, R - 1, band[0], band[-1]}]
TOL = [float(x) for x in os.environ.get('REA_BOW_TOL', '0.003,0.008,0.015,0.03').split(',')]
cen = np.array([V[order[i]].mean(0) for i in range(R)])


def bridge_err(i, a, b):
    """max distance of ring i's vertices from the straight bridge between rings a and b (same angle index)"""
    t = (ys[i] - ys[a]) / (ys[b] - ys[a])
    return float(np.linalg.norm(V[order[i]] - ((1 - t) * V[order[a]] + t * V[order[b]]), axis=1).max())


def select(budget, keep, fixed, level=0):
    keep = sorted(keep); worst = 0.0
    while len(keep) > budget:
        best = None
        for j in range(1, len(keep) - 1):
            i = keep[j]
            if i in fixed:
                continue
            e = max(bridge_err(k, keep[j - 1], keep[j + 1]) for k in range(keep[j - 1] + 1, keep[j + 1]))
            if best is None or e < best[0]:
                best = (e, j)
        if best is None or best[0] > TOL[level]:
            break
        worst = max(worst, best[0]); keep.pop(best[1])
    return keep, worst


src_span = {}
for t in np.flatnonzero(~cap):
    src_span.setdefault(int(fr[t].min()), []).append(F[t])
caps = {int(fr[t, 0]): [] for t in np.flatnonzero(cap)}
for t in np.flatnonzero(cap):
    caps[int(fr[t, 0])].append(F[t])
prev = list(range(R)); stats = []
for level, budget in enumerate(budgets):
    fixed = FIXED[level]; keep, err = select(budget, prev, fixed, level); prev = keep
    sides = [0, 1, 2, 3, 4, 5, 6, 7] if level < 2 else [0, 2, 4, 6]
    tris = []
    for a, b in zip(keep, keep[1:]):
        if b == a + 1 and level < 2:
            tris += [list(t) for t in src_span[a]]                            # source segment, exact
            continue
        oa, ob = order[a][sides], order[b][sides]; n = len(sides)
        for k in range(n):
            j = (k + 1) % n
            for t in ((oa[k], oa[j], ob[j]), (oa[k], ob[j], ob[k])):
                p = V[list(t)]; nrm = np.cross(p[1] - p[0], p[2] - p[0])
                out = p.mean(0) - (cen[a] + cen[b]) / 2
                tris.append(list(t) if nrm @ out > 0 else [t[0], t[2], t[1]])
    for end in (keep[0], keep[-1]):
        if level < 2:
            tris += [list(t) for t in caps[end]]
        else:
            o = order[end][sides]; t = (o[0], o[1], o[2]); u = (o[0], o[2], o[3])
            axis = cen[keep[1]] - cen[keep[0]] if end == keep[0] else cen[keep[-1]] - cen[keep[-2]]
            sgn = -1 if end == keep[0] else 1
            for tt in (t, u):
                p = V[list(tt)]; nrm = np.cross(p[1] - p[0], p[2] - p[0])
                tris.append(list(tt) if (nrm @ axis) * sgn > 0 else [tt[0], tt[2], tt[1]])
    tris = np.array(tris); used = np.unique(tris); remap = -np.ones(len(V), int); remap[used] = np.arange(len(used))
    np.savez(f'work/bow_lod{level}.npz', verts=V[used], normals=N[used], uv=UV[used], faces=remap[tris], src=used)
    stats.append((level, len(keep), len(tris), round(err * 1000, 2)))
    print(f'BOW LOD{level}: {len(keep)} rings ({len(fixed)} fixed), {len(tris)} tris, max bridge error {err * 1000:.2f} mm')
