#!/usr/bin/env python3
"""Skirt lining through the skirt (reduction check, 2026-11-04): F3's skirt lining (F1's, 4 mm inside, decimated to 60 % at the
build, so not a twin of the skirt) is kept exactly while the skirt is cut. Per clip at FPS: each lining vertex's signed distance to
the posed outer skirt (closest point on the 8 nearest skirt faces by centroid, sign along that face's outward normal: at rest
the lining lies about 4 mm inside). Reports per clip the largest outward distance and the number of lining vertices more than TOL
outside (the dark lining showing through the blue cloth). Parts from work/glb_parts.npz (installed face labels -> installed vertices -> the candidate's identical vertices).
Usage: lining_gate.py <glb> <out json> [fps] [tol m] [clips: prints the worst vertex per new maximum]"""
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
m = Model(Glb(glb)); body = m.primitives[0]
g = np.load(HERE / 'work' / 'glb_parts.npz'); bm = g['mat'] == 0; fpart = g['part'][bm]
# vertex labels from the installed body primitive (every candidate vertex is an installed vertex), face label by its first corner
src = Model(Glb(str(HERE / 'before' / 'mm9_peasantf6.glb'))).primitives[0]
vpart = np.full(len(src['positions']), -1); vpart[src['triangles'].ravel()] = np.repeat(fpart, 3)
P0, T0 = body['positions'], body['triangles']
d_, j_ = cKDTree(src['positions']).query(P0); assert d_.max() < 1e-6, d_.max()
part = vpart[j_][T0[:, 0]]
skirt = T0[part == 2]; linv = np.unique(T0[part == 8].ravel())
print('skirt faces', len(skirt), 'lining verts', len(linv))
rep = {}


def signed(X):
    tr = X[skirt]; c = tr.mean(1); n = np.cross(tr[:, 1] - tr[:, 0], tr[:, 2] - tr[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    Q = X[linv]; _, ids = cKDTree(c).query(Q, k=8); best = np.full(len(Q), 1e9); sd = np.zeros(len(Q))
    for k in range(8):
        i = ids[:, k]; q, _ = closest_on_triangles(Q, tr[i, 0], tr[i, 1], tr[i, 2]); d = np.linalg.norm(q - Q, axis=1); u = d < best
        best[u] = d[u]; sd[u] = ((Q - q) * n[i])[u].sum(1)
    return sd


rest = m.skinned_positions(m.world({}))[0][0]
s0 = signed(rest); sgn = -1.0 if np.median(s0) > 0 else 1.0
print('rest median signed mm', round(float(np.median(s0 * sgn)) * 1000, 2))
CL = sys.argv[5].split(',') if len(sys.argv) > 5 else m.clips
for clip in CL:
    t1 = m.clip_times(clip)[-1]; worst = -1.0; frames = 0; cnt = 0
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        X = m.skinned_positions(m.world(m.sample(clip, t)))[0][0]
        sd = signed(X) * sgn
        if sd.max() > worst and len(sys.argv) > 5:
            i = int(sd.argmax()); print(f'  {clip} t={t:.2f} worst {sd.max()*1000:.1f} mm at rest {P0[linv[i]].round(3).tolist()} posed {X[linv[i]].round(3).tolist()} n>5mm {int((sd>0.005).sum())}')
        worst = max(worst, float(sd.max())); k = int((sd > TOL).sum()); cnt = max(cnt, k); frames += k > 0
    rep[clip] = dict(max_out_mm=round(worst * 1000, 2), frames_out=frames, max_verts_out=cnt)
    print(f'{clip:9s} max outside {worst * 1000:6.2f} mm, frames with lining > {TOL * 1000:.1f} mm out {frames}, most verts {cnt}', flush=True)
Path(out).write_text(json.dumps(rep, indent=1))
