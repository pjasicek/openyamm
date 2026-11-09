#!/usr/bin/env python3
"""Which faces the see-through gate's hole pixels land on (see_through_faces.npz of the patched gate), mapped to the GLB's LOD0
triangles by rest centre: per primitive and piece the hole pixels, and for the body's pieces how far (m) the hole-weighted
faces lie from each open loop of the piece (the band depth a lining needs). Writes <npz stem>_glbfaces.npz (holes per GLB
triangle, per primitive). Usage: hole_faces.py <glb> <see_through_faces.npz>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_common as C  # noqa: E402
glb, fz = sys.argv[1:3]
doc, binary, nd, prims, jn = C.load(glb)
z = np.load(fz); H = z['holes']; RC = z['rest_centre']; RCg = np.c_[RC[:, 0], RC[:, 2], -RC[:, 1]]
kd = cKDTree(RCg); out = {}
tot = H.sum(); print('hole pixels total', int(tot))
for name, d in prims.items():
    cen = d['P'][d['T']].mean(1); dist, idx = kd.query(cen)
    h = np.where(dist < 1e-4, H[idx], 0); out[name] = h
    print(f'== {name}: matched {(dist < 1e-4).sum()} / {len(cen)}, hole px {int(h.sum())}')
    inv = C.weld(d['P']); TT = inv[d['T']]; pc = C.pieces(TT, inv.max() + 1); fp = pc[TT[:, 0]]
    WP = np.zeros((inv.max() + 1, 3)); WP[inv] = d['P']
    loops, bnd, ec = C.boundary_loops(TT)
    dj = d['J'][np.arange(len(d['J'])), d['W'].argmax(1)]
    for p in sorted(set(fp), key=lambda p: -h[fp == p].sum()):
        m = fp == p; s = h[m].sum()
        if s < 20:
            continue
        top = np.argsort(-h * m)[:5]
        bones = {}
        for f in np.where(m & (h > 0))[0]:
            b = jn[dj[d['T'][f, 0]]]; bones[b] = bones.get(b, 0) + int(h[f])
        bl = sorted(bones.items(), key=lambda x: -x[1])[:4]
        print(f'  piece {p} ({m.sum()} tris): hole px {int(s)}, faces with holes {(h[m] > 0).sum()}, bones {bl}')
        for lp in loops:
            if pc[lp[0]] != p or len(lp) < 6:
                continue
            dd = cKDTree(WP[lp]).query(cen[m])[0]; w = h[m]
            if w.sum() == 0:
                continue
            q = [float(np.percentile(np.repeat(dd, w.astype(int)), x)) for x in (50, 90, 99)]
            print(f'     loop {len(lp)} v at {np.round(WP[lp].mean(0), 3)}: hole-weighted distance p50/p90/p99 '
                  f'{q[0]:.3f} / {q[1]:.3f} / {q[2]:.3f} m')
np.savez(str(Path(fz).with_suffix('')) + '_glbfaces.npz', **out)
