#!/usr/bin/env python3
"""Per lining vertex: the largest outward distance through the skirt over every clip at FPS (lining_gate.py's measure), for the
installed GLB and a candidate; lists the vertices the candidate pushes out more than MARGIN m beyond the installed and writes their
rest positions to work/lining_probe_<tag>.npy (for a keep set: the skirt faces round them). Usage: lining_probe.py <glb> <tag>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE.parent / 'claude_shared'))
from glb_pose import Glb, Model  # noqa: E402
from detached_parts_audit import closest_on_triangles  # noqa: E402
FPS = 10.0; MARGIN = 0.0015
g = np.load(HERE / 'work' / 'glb_parts.npz'); fpart = g['part'][g['mat'] == 0]


def per_vertex(path):
    m = Model(Glb(path)); body = m.primitives[0]
    src = Model(Glb(str(HERE / 'before' / 'mm9_peasantf5.glb'))).primitives[0]
    vpart = np.full(len(src['positions']), -1); vpart[src['triangles'].ravel()] = np.repeat(fpart, 3)
    P0, T0 = body['positions'], body['triangles']
    d_, j_ = cKDTree(src['positions']).query(P0); assert d_.max() < 1e-6
    part = vpart[j_][T0[:, 0]]; skirt = T0[part == 3]; linv = np.unique(T0[part == 10].ravel())

    def signed(X):
        tr = X[skirt]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        Q = X[linv]; _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
        for k in range(8):
            i = ids[:, k]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
            best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
        return sd
    rest = m.skinned_positions(m.world({}))[0][0]; s0 = signed(rest); sgn = -1.0 if np.median(s0) > 0 else 1.0
    worst = np.full(len(linv), -1.0); where = [''] * len(linv)
    for clip in m.clips:
        t1 = m.clip_times(clip)[-1]
        for t in np.append(np.arange(0, t1, 1 / FPS), t1):
            sd = signed(m.skinned_positions(m.world(m.sample(clip, t)))[0][0]) * sgn
            u = sd > worst; worst[u] = sd[u]
            for i in np.flatnonzero(u):
                where[i] = f'{clip}@{t:.1f}'
    return P0[linv], worst, where


Pi, wi, _ = per_vertex(str(HERE / 'before' / 'mm9_peasantf5.glb'))
Pc, wc, wh = per_vertex(sys.argv[1])
_, j = cKDTree(Pi).query(Pc); wi = wi[j]
bad = np.flatnonzero(wc > np.maximum(wi, 0) + MARGIN)
for i in bad[np.argsort(-wc[bad])][:20]:
    print(f'lining v {Pc[i].round(3)} installed {wi[i] * 1000:.2f} mm candidate {wc[i] * 1000:.2f} mm at {wh[i]}')
print('vertices pushed out more than', MARGIN * 1000, 'mm beyond installed:', len(bad))
np.save(HERE / 'work' / f'lining_probe_{sys.argv[2]}.npy', Pc[bad])
