#!/usr/bin/env python3
"""Linings through their cloth (reduction check, Wyrde copy of PeasantF8's lining_gate.py): the Wyrdes' linings (linings_wy.py: twin
faces 2 mm behind the outer cloth, rim strips at the open edges) are re-emitted from the cut outer cloth. Per primitive and clip at
FPS: each lining vertex's signed distance to the posed outer cloth (closest point on the 8 nearest outer faces of the same part by
centroid, sign along that face's normal: at rest the lining lies 2 mm behind). Reports per clip the largest outward distance and the
number of lining vertices more than TOL outside (the lining's colour showing through the cloth). Labels from work/glb_parts.npz:
lining vertices = installed vertices used only by inner (twin or rim) faces; outer faces = faces without a lining vertex.
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
m = Model(Glb(glb)); S = Model(Glb(str(HERE / 'before' / 'mm9_scholar.glb')))
g = np.load(HERE / 'work' / 'glb_parts.npz')
node = m.primitives[0]['node']; PI = [k for k, p in enumerate(m.primitives) if p['node'] == node][:2]
setup = []
for k in PI:
    src = S.primitives[k]; cand = m.primitives[k]; sel = g['mat'] == k
    inner, fpart = g['inner'][sel], g['part'][sel]
    used_out = np.zeros(len(src['positions']), bool); used_out[src['triangles'][~inner].ravel()] = True
    used_in = np.zeros(len(src['positions']), bool); used_in[src['triangles'][inner].ravel()] = True
    linsrc = used_in & ~used_out
    vpart = np.full(len(src['positions']), -1); vpart[src['triangles'].ravel()] = np.repeat(fpart, 3)
    d_, j_ = cKDTree(src['positions']).query(cand['positions']); assert d_.max() < 1e-6, d_.max()
    lin = linsrc[j_]; vp = vpart[j_]; T = cand['triangles']
    outer = T[~lin[T].any(1)]; opart = vp[outer[:, 0]]
    linv = np.flatnonzero(lin & np.isin(np.arange(len(lin)), T.ravel())); lpart = vp[linv]
    print('prim', k, 'outer faces', len(outer), 'lining verts', len(linv), 'parts', np.unique(lpart).tolist())
    setup.append((k, outer, opart, linv, lpart))


def signed(X, outer, opart, linv, lpart):
    sd = np.zeros(len(linv))
    for p_ in np.unique(lpart):
        o = outer[opart == p_]; L = linv[lpart == p_]
        tr = X[o]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        Q = X[L]; _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9); s = np.zeros(len(Q))
        for kk in range(8):
            i = ids[:, kk]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
            best[u] = d[u]; s[u] = ((Q - q) * n[i])[u].sum(1)
        sd[lpart == p_] = s
    return sd


rest = m.skinned_positions(m.world({}))
sg = {}
for k, outer, opart, linv, lpart in setup:
    s0 = signed(rest[k][0], outer, opart, linv, lpart); sg[k] = -1.0 if np.median(s0) > 0 else 1.0
    print('prim', k, 'rest median signed mm', round(float(np.median(s0 * sg[k])) * 1000, 2), 'rest max', round(float((s0 * sg[k]).max()) * 1000, 2))
rep = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]; worst = {k: -1.0 for k in sg}; frames = {k: 0 for k in sg}; cnt = {k: 0 for k in sg}
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        pos = m.skinned_positions(m.world(m.sample(clip, t)))
        for k, outer, opart, linv, lpart in setup:
            sd = signed(pos[k][0], outer, opart, linv, lpart) * sg[k]
            worst[k] = max(worst[k], float(sd.max())); n_ = int((sd > TOL).sum()); cnt[k] = max(cnt[k], n_); frames[k] += n_ > 0
    rep[clip] = {str(k): dict(max_out_mm=round(worst[k] * 1000, 2), frames_out=frames[k], max_verts_out=cnt[k]) for k in sg}
    print(f'{clip:9s} ' + ' | '.join(f'prim {k}: max outside {worst[k] * 1000:6.2f} mm, frames {frames[k]}, most verts {cnt[k]}' for k in sg), flush=True)
Path(out).write_text(json.dumps(rep, indent=1))
