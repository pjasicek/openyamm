#!/usr/bin/env python3
"""T-junction cracks on the midline (dark dots on the nose, lips and chin): the mirror snapped near-midline vertices onto x = 0, which left
zero-area slivers whose middle vertex lies on the opposite edge; fix_needles_pg.py dropped the slivers, so that vertex sits on a neighbour's
edge without being one of its corners and the rasteriser opens a crack. Each such edge (p, q) with a midline vertex r strictly inside it is
split at r: the face (p, q, s) becomes (p, r', s) and (r', q, s), where r' is a new vertex at r's position with the UV interpolated on that
face's own chart (the paint stays valid: no existing UV moves) and r's original index for the weights. Repeated until none is left.
Args: <in uv npz> <out uv npz>. Project folder."""
import sys
import numpy as np
from scipy.spatial import cKDTree
D = dict(np.load(sys.argv[1])); co, tri, uv, orig, mat = D['co'], D['tri'].copy(), D['uv'], D['orig'], D['mat']
extra = {k: D[k] for k in ('comp',) if k in D}
co = list(co); uv = list(uv); orig = list(orig); comp = list(D['comp'])
tri = [list(t) for t in tri]; mat = list(mat); inner = list(D['inner']) if 'inner' in D else None
total = 0
for it in range(6):
    C = np.array(co); mid = np.where(np.abs(C[:, 0]) < 1e-5)[0]; kd = cKDTree(C[mid])
    splits = []
    for f, t in enumerate(tri):
        for k in range(3):
            p, q = t[k], t[(k + 1) % 3]; P, Q = C[p], C[q]
            if abs(P[0]) > 1e-5 or abs(Q[0]) > 1e-5: continue       # midline edges only
            L = np.linalg.norm(Q - P)
            if L < 1e-7: continue
            for j in kd.query_ball_point((P + Q) / 2, L / 2 + 1e-6):
                r = mid[j]; R = C[r]; s_ = (R - P) @ (Q - P) / L ** 2
                if 1e-3 < s_ < 1 - 1e-3 and np.linalg.norm(P + s_ * (Q - P) - R) < 1e-6:
                    splits.append((f, k, r, s_)); break
            else:
                continue
            break
    if not splits: break
    for f, k, r, s_ in splits:
        t = tri[f]; p, q, s = t[k], t[(k + 1) % 3], t[(k + 2) % 3]
        n = len(co); co.append(C[r]); uv.append(np.asarray(uv[p]) * (1 - s_) + np.asarray(uv[q]) * s_); orig.append(orig[r]); comp.append(comp[p])
        tri[f] = [p, n, s]; tri.append([n, q, s]); mat.append(mat[f])
        if inner is not None: inner.append(inner[f])
    total += len(splits); print('pass', it, 'split', len(splits))
D.update(co=np.array(co), tri=np.array(tri), uv=np.array(uv), orig=np.array(orig), mat=np.array(mat), comp=np.array(comp))
if inner is not None: D['inner'] = np.array(inner)
np.savez(sys.argv[2], **D); print('TJUNCTIONS split', total, 'faces', len(tri))
