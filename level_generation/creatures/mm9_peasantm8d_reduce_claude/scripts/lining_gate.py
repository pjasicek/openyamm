#!/usr/bin/env python3
"""Linings through the outer cloth and hair (PeasantDM2 reduction check, 2026-11-04): the linings (linings_dboy.sh: hair twins
1.5 mm, rim and sleeve twins 0.5-3 mm inside) are re-emitted from the cut outer faces. Per primitive and clip at FPS: each
lining vertex's signed distance to the posed outer surface of its primitive (the non-lining faces; closest point on the 8
nearest faces by centroid, sign along that face's normal: at rest a lining lies inside). Reports per primitive and clip the
largest outward distance and the most lining vertices more than TOL outside (a dark lining speck through the cloth).
Lining vertices = vertices of the installed lining faces (work/twins.npz), found in the candidate by exact position.
Usage: lining_gate.py <glb> <out json> [fps] [tol m]"""
import json
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
glb, out = sys.argv[1:3]; FPS = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
TOL = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0005
# PeasantDM2: nearest outer faces by centroid (env LK; 8 missed the closest of the larger cut faces: 16 mm false outs at rest)
LK = int(__import__('os').environ.get('LK', '32'))
m = Model(Glb(glb)); src = Model(Glb(str(HERE / 'before' / 'mm9_peasantm8d.glb')))
tw = np.load(HERE / 'work' / 'twins.npz'); lin = tw['lining'] | (tw['lining2'] if 'lining2' in tw else False)   # PeasantDM2: + loose linings mapped by vertex
nf = [len(p['triangles']) for p in src.primitives[:2]]; offs = np.cumsum([0] + nf)
setup = []
for k in range(2):
    sp = src.primitives[k]; cp = m.primitives[k]
    lv_src = np.unique(sp['triangles'][lin[offs[k]:offs[k + 1]]].ravel())
    d, j = cKDTree(sp['positions'][lv_src]).query(cp['positions'])
    is_lin = d < 1e-7
    T = cp['triangles']; outer = T[~is_lin[T].any(1)]
    linv = np.flatnonzero(is_lin & np.isin(np.arange(len(is_lin)), T.ravel()))
    setup.append((outer, linv)); print('prim', k, 'outer faces', len(outer), 'lining verts', len(linv))


def signed(X, outer, linv):
    tr = X[outer]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    Q = X[linv]; _, ids = cKDTree(c).query(Q, k=LK); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
    for k in range(LK):
        i = ids[:, k]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
        best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
    return sd


rep = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; res = [[-1.0, 0, 0], [-1.0, 0, 0]]
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        Xs = m.skinned_positions(m.world(m.sample(clip, t)))
        for k in range(2):
            if not len(setup[k][1]):
                continue
            sd = signed(Xs[k][0], *setup[k]); r = res[k]
            r[0] = max(r[0], float(sd.max())); c = int((sd > TOL).sum()); r[1] = max(r[1], c); r[2] += c > 0
    rep[clip] = {f'prim{k}': dict(max_out_mm=round(res[k][0] * 1000, 2), max_verts_out=res[k][1], frames_out=res[k][2]) for k in range(2)}
    print(f'{clip:12s} ' + ' | '.join(f'prim{k}: max out {res[k][0] * 1000:6.2f} mm, most verts > {TOL * 1000:.1f} mm {res[k][1]:4d}, frames {res[k][2]:3d}'
                                     for k in range(2)), flush=True)
Path(out).write_text(json.dumps(rep, indent=1))
