#!/usr/bin/env python3
"""Hair-shell colour drift of a candidate (PeasantM5 crown-streak fix, 2026-11-05): every candidate hair-shell face (head prim
faces whose vertices all belong to the installed hair shell, part 4 of work/glb_sets_a.npz) sampled at 7 barycentric points in each
tier's head image, against the installed hair surface's colour at the closest point (closest installed hair face, barycentric UV).
Prints the worst faces (mean RGB difference, luminance sign, rest position); writes work/hair_drift_<tag>.npz (candidate face
centroids, drift) and work/keep_streak_<tag>.npy (installed GLB face mask: installed hair faces within R of a candidate face with
drift > THR, plus RING rings). Usage: hair_drift_m5.py <candidate.glb> <tag>   (env THR 12, R 0.015, RING 1)"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import glbio  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
THR = float(os.environ.get('THR', '12')); R = float(os.environ.get('R', '0.015')); RING = int(os.environ.get('RING', '1'))
_, _, _, A = glbio.load(HERE / 'before' / 'mm9_markel.glb', 'Markel'); _, _, _, B = glbio.load(sys.argv[1], 'Markel'); tag = sys.argv[2]
s = np.load(HERE / 'work' / 'glb_sets_a.npz'); nb = int((s['mat'] == 0).sum()); part = s['part'][nb:]
a, b = A['MarkelHead'], B['MarkelHead']
hairT = a['T'][part == 4]; hv = np.zeros(len(a['P']), bool); hv[hairT.ravel()] = True
key = lambda d, i: d['P'][i].tobytes() + d['UV'][i].tobytes()
ka = {key(a, i): i for i in range(len(a['P']))}
bmap = np.array([ka.get(key(b, i), -1) for i in range(len(b['P']))])
bh = np.array([(bmap[t] >= 0).all() and hv[bmap[t]].all() for t in b['T']])
BT = b['T'][bh]
imgs = [np.asarray(Image.open(HERE / 'work' / f'tex_PeasantM5Head_{t}.png').convert('RGB'), np.float32) for t in 'AB']
S = imgs[0].shape[0]
look = lambda im, uv: im[np.clip((uv[:, 1] * S).astype(int), 0, S - 1), np.clip((uv[:, 0] * S).astype(int), 0, S - 1)]
bary = np.array([[1, 1, 1], [4, 1, 1], [1, 4, 1], [1, 1, 4], [2, 2, 1], [1, 2, 2], [2, 1, 2]], float); bary /= bary.sum(1, keepdims=True)
pts = np.einsum('sk,fkc->fsc', bary, b['P'][BT]).reshape(-1, 3); uvb = np.einsum('sk,fkc->fsc', bary, b['UV'][BT]).reshape(-1, 2)
AP = a['P'][hairT]; cen = AP.mean(1); tr = cKDTree(cen)
_, cand = tr.query(pts, k=12)
best_d = np.full(len(pts), np.inf); best_uv = np.zeros((len(pts), 2))
for k in range(cand.shape[1]):
    f = cand[:, k]; tri = AP[f]
    q, w = closest_on_triangles(pts, tri[:, 0], tri[:, 1], tri[:, 2]) if False else (None, None)
    # barycentric of the closest point on each candidate triangle
    e0, e1 = tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]; v = pts - tri[:, 0]
    d00, d01, d11 = (e0 * e0).sum(1), (e0 * e1).sum(1), (e1 * e1).sum(1); d20, d21 = (v * e0).sum(1), (v * e1).sum(1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-18); bv = (d11 * d20 - d01 * d21) / den; bw = (d00 * d21 - d01 * d20) / den
    bv, bw = np.clip(bv, 0, 1), np.clip(bw, 0, 1); sm = bv + bw; bv, bw = np.where(sm > 1, bv / sm, bv), np.where(sm > 1, bw / sm, bw)
    qp = tri[:, 0] + bv[:, None] * e0 + bw[:, None] * e1; dd = np.linalg.norm(qp - pts, axis=1)
    U = a['UV'][hairT[f]]; quv = U[:, 0] * (1 - bv - bw)[:, None] + U[:, 1] * bv[:, None] + U[:, 2] * bw[:, None]
    m = dd < best_d; best_d[m] = dd[m]; best_uv[m] = quv[m]
drift = np.zeros(len(BT)); lum = np.zeros(len(BT))
for im in imgs:
    cb, ca = look(im, uvb), look(im, best_uv)
    df = np.abs(cb - ca).mean(1).reshape(len(BT), 7).mean(1); drift = np.maximum(drift, df)
    lum = np.where(df >= drift, (cb.mean(1) - ca.mean(1)).reshape(len(BT), 7).mean(1), lum)
C = b['P'][BT].mean(1)
o = np.argsort(-drift)
print('hair faces', len(BT), 'drift p50/p90/p99/max', np.percentile(drift, [50, 90, 99]).round(1), drift.max().round(1), '> THR', int((drift > THR).sum()))
for f in o[:15]:
    print(f'  drift {drift[f]:5.1f} lum {lum[f]:+6.1f} at x {C[f,0]:+.3f} y {C[f,1]:.3f} z {C[f,2]:+.3f}')
np.savez(HERE / 'work' / f'hair_drift_{tag}.npz', C=C, drift=drift, lum=lum)
hot = C[drift > THR]
keep = np.zeros(len(s['part']), bool)
if len(hot):
    d, _ = cKDTree(hot).query(a['P'][a['T']].reshape(-1, 3)); near = d.reshape(-1, 3).min(1) < R
    kh = near & (part == 4)
    _, w = np.unique(np.round(a['P'], 6), axis=0, return_inverse=True); w = w.ravel()
    for _ in range(RING):
        ev = np.zeros(w.max() + 1, bool); ev[w[a['T'][kh]].ravel()] = True; kh = (part == 4) & ev[w[a['T']]].any(1)
    keep[nb:] = kh
print('installed hair faces kept', int(keep.sum()))
np.save(HERE / 'work' / f'keep_streak_{tag}.npy', keep)
