#!/usr/bin/env python3
"""Linings through the outer cloth (reduction check; PeasantDM4 copy of PeasantF3's lining_gate.py). The linings are re-emitted
from the cut outer faces (mpqem.py, twins_dm4.py), so each lining vertex should stay behind its own outer surface in every pose.
Lining vertices: installed vertices used only by the installed paired lining faces (work/twins.npz); outer surface: every other
face of the same primitive except one-texel faces (rim strips). Per clip at FPS: each lining vertex's signed distance to the
posed outer surface (closest point on the 8 nearest outer faces by centroid, + along that face's normal = outside). Reports per
clip and primitive the largest outward distance, the frames with any lining vertex > TOL outside and the most such vertices.
Usage: lining_gate.py <glb> <out json> [fps 10] [tol m 0.0005]"""
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
m = Model(Glb(glb)); src = Model(Glb(str(HERE / 'before' / 'mm9_peasantm3.glb')))
tw = np.load(HERE / 'work' / 'twins.npz')
nf = [len(src.primitives[k]['triangles']) for k in range(2)]; off = np.cumsum([0] + nf)
sets = []
for k in range(2):
    s = src.primitives[k]; T = np.asarray(s['triangles']).reshape(-1, 3); lin = tw['lining'][off[k]:off[k + 1]]
    only = np.ones(len(s['positions']), bool); only[T[~lin].ravel()] = False
    used = np.zeros(len(s['positions']), bool); used[T[lin].ravel()] = True; lv_src = used & only
    c = m.primitives[k]; P0 = c['positions']; T0 = np.asarray(c['triangles']).reshape(-1, 3)
    d_, j_ = cKDTree(s['positions']).query(P0); assert d_.max() < 1e-6, d_.max()
    isl = lv_src[j_]                                       # candidate vertices are exact installed copies
    lin_f = isl[T0].all(1)
    outer = ~lin_f
    sets.append((k, T0[outer], np.unique(T0[lin_f].ravel())))       # one-texel faces (rim strips) dropped below
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, b = bglbio.read(glb); node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantM3' and 'mesh' in n)
cp = bglbio.prims(doc, b, node['mesh'])
for i, (k, To, lv) in enumerate(sets):
    U = cp[k]['TEXCOORD_0'].astype(float); spread = np.abs(U[To] - U[To][:, :1]).max((1, 2))
    sets[i] = (k, To[spread > 1e-7], lv)
    print('prim', k, 'outer faces', int((spread > 1e-7).sum()), 'lining verts', len(lv))
sets = [x for x in sets if len(x[2])]   # PeasantM3: the head set has no linings


def signed(X, To, lv):
    tr = X[To]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    Q = X[lv]; _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
    for kk in range(8):
        i = ids[:, kk]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
        best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
    return sd


rep = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; r = {}
    acc = {k: [-1.0, 0, 0] for k, _, _ in sets}
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        pz = m.skinned_positions(m.world(m.sample(clip, t)))
        for k, To, lv in sets:
            sd = signed(pz[k][0], To, lv); a = acc[k]
            a[0] = max(a[0], float(sd.max())); kk = int((sd > TOL).sum()); a[2] = max(a[2], kk); a[1] += kk > 0
    rep[clip] = {('body', 'head')[k]: dict(max_out_mm=round(a[0] * 1000, 2), frames_out=a[1], max_verts_out=a[2]) for k, a in acc.items()}
    print(f'{clip:12s} ' + '  '.join(f"{('body', 'head')[k]}: max out {a[0] * 1000:6.2f} mm, frames {a[1]:3d}, most verts {a[2]:3d}" for k, a in acc.items()), flush=True)
Path(out).write_text(json.dumps(rep, indent=1))
