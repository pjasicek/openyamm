#!/usr/bin/env python3
"""robe_gate.py diagnostics (finishing round 2026-11-04): for one clip/time, the flagged leg vertices (bind and posed
height, signed distance) and, per flagged vertex, whether an outward ray (from the robe's vertical axis through the vertex)
still hits another robe face further out (= the vertex is under cloth, hidden) or nothing (= visible through the dress).
Args: <glb> <clip|all> [<time s>] (all: every clip at 24 fps, summary per clip)"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model
from detached_parts_audit import closest_on_triangles
glb, clip = sys.argv[1], sys.argv[2]; t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
m = Model(Glb(glb)); prims = [p for p in m.primitives if p['node'] == m.primitives[0]['node']]
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
J = np.vstack([p['joints'] for p in prims]); W = np.vstack([p['weights'] for p in prims])
sk = [i for i, n in enumerate(jn) if n.startswith('x') or n.startswith('XCOM')]
leg = [i for i, n in enumerate(jn) if 'Calf' in n or 'Foot' in n or 'Toe' in n]
sw = (np.isin(J, sk) * W).sum(1); lw = (np.isin(J, leg) * W).sum(1)
offs = np.cumsum([0] + [len(p['positions']) for p in prims])
tri = np.vstack([np.asarray(p['triangles']).reshape(-1, 3) + o for p, o in zip(prims, offs)])
n_p = len(prims)
def allpos(w): return np.concatenate([r[0] for r in m.skinned_positions(w)][:n_p])
R0 = allpos(m.world({})); c0 = R0[tri].mean(1)
n0 = np.cross(R0[tri[:, 1]] - R0[tri[:, 0]], R0[tri[:, 2]] - R0[tri[:, 0]]); rad = c0.copy(); rad[:, 1] = 0
rob = (sw[tri] > 0.3).all(1) & ((n0 * rad).sum(1) > 0); F = np.where(rob)[0]
anyskirt = (sw[tri] > 0.3).all(1); FA = np.where(anyskirt)[0]
hem_y = R0[np.unique(tri[rob])][:, 1].min(); fh = c0[:, 1] - hem_y
legv = np.where(lw > 0.5)[0]
def one(clip, t, verbose):
    P = allpos(m.world(m.sample(clip, t)))
    tr = P[tri[F]]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    Q = P[legv]; _, ids = cKDTree(c).query(Q, k=6); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q)); ff = np.zeros(len(Q), int)
    for k in range(6):
        i = ids[:, k]; q, _b = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
        best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1); ff[u] = i[u]
    # winding sign as robe_gate
    sgn = 1.0
    bad = (sgn * sd > 0.003) & (fh[F[ff]] > 0.14) & (best < 0.08)
    if verbose: print('flagged', bad.sum(), 'of', len(legv))
    # outward ray test against ALL skirt faces (any facing), Moller-Trumbore
    TA = P[tri[FA]]; e1 = TA[:, 1] - TA[:, 0]; e2 = TA[:, 2] - TA[:, 0]
    cen = P[legv].mean(0)
    vis = 0
    for v in np.where(bad)[0]:
        o = Q[v]; dvec = o - np.array([cen[0], o[1], cen[2]]); dvec[1] = 0; dvec /= max(np.linalg.norm(dvec), 1e-9)
        h = np.cross(dvec, e2); a = (e1 * h).sum(1); ok = np.abs(a) > 1e-12; f = np.zeros_like(a); f[ok] = 1 / a[ok]
        s = o - TA[:, 0]; u = f * (s * h).sum(1); qv = np.cross(s, e1); vv = f * (qv @ dvec); tt = f * (qv * e2).sum(1)
        hit = ok & (u >= 0) & (u <= 1) & (vv >= 0) & (u + vv <= 1) & (tt > 1e-4)
        if not hit.any(): vis += 1
        if verbose and (v == np.where(bad)[0][0] or not hit.any()):
            print(f'  v{legv[v]} bind y {R0[legv[v],1]:.3f} posed y {o[1]:.3f} sd {sd[v]*100:.1f} cm  hits further out {int(hit.sum())}')

    return int(bad.sum()), vis
clips = [a['name'] for a in m.glb.json['animations']] if clip == 'all' else [clip]
for c_ in clips:
    if clip == 'all':
        T = np.arange(0, m.clip_times(c_)[-1] + 1e-6, 1 / 24); fl = vf = 0; vmax = 0; tw = 0.0
        for t in T:
            b, v = one(c_, float(t), False); fl += b > 0; vf += v > 0
            if v > vmax: vmax, tw = v, t
        print(f'ROBE_DIAG {c_:12} frames flagged {fl}/{len(T)}  frames with visible leg vertices {vf}  max visible verts {vmax} at frame48 {round(tw * 48)}', flush=True)
    else:
        b, v = one(c_, t0, True); print('ROBE_DIAG flagged', b, 'visible (no cloth further out)', v)
