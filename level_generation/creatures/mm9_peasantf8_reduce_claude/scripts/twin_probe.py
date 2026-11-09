#!/usr/bin/env python3
"""Probe the skirt -> lining twin relation in the installed LOD0 (assemble_pf.lining: lining vertex = skirt vertex - 4 mm
vertex normal, faces reversed, plus a hem rim). Prints residuals, how many original skirt faces have their reversed twin face in
the lining, and lining UV seams that the skirt does not have."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf8.glb', 'PeasantF8')
g = np.load(HERE / 'work' / 'glb_parts.npz'); part = g['part'][g['mat'] == 0]
P, T, U = D['PeasantF8_B']['P'], D['PeasantF8_B']['T'], D['PeasantF8_B']['UV']
sk = np.flatnonzero(part == 3); ln = np.flatnonzero(part == 6)
_, pk = np.unique(np.round(P, 5), axis=0, return_inverse=True); pk = pk.ravel()
for depth in (0.003, 0.004):
    for wmode in ('area', 'angle'):
        fn = np.cross(P[T[sk, 1]] - P[T[sk, 0]], P[T[sk, 2]] - P[T[sk, 0]])
        Ns = np.zeros((pk.max() + 1, 3))
        for c in range(3):
            if wmode == 'area':
                w = fn / 2
            else:
                a = P[T[sk, (c + 1) % 3]] - P[T[sk, c]]; b = P[T[sk, (c + 2) % 3]] - P[T[sk, c]]
                ang = np.arccos(np.clip((a * b).sum(1) / np.linalg.norm(a, axis=1) / np.linalg.norm(b, axis=1), -1, 1))
                w = np.nan_to_num(fn / np.linalg.norm(fn, axis=1, keepdims=True) * ang[:, None])
            np.add.at(Ns, pk[T[sk, c]], w)
        ov = np.unique(T[sk]); lv = np.unique(T[ln])
        n_ = Ns[pk[ov]]; n_ = np.nan_to_num(n_ / np.linalg.norm(n_, axis=1, keepdims=True))
        dd, q = cKDTree(P[lv]).query(P[ov] - depth * n_)
        print(f'depth {depth} {wmode}: residual max {dd.max()*1000:.3f} mm p99 {np.percentile(dd,99)*1000:.3f} p50 {np.median(dd)*1000:.4f}')
# twin by best mode: check faces
fn = np.cross(P[T[sk, 1]] - P[T[sk, 0]], P[T[sk, 2]] - P[T[sk, 0]])
Ns = np.zeros((pk.max() + 1, 3))
for c in range(3):
    a = P[T[sk, (c + 1) % 3]] - P[T[sk, c]]; b = P[T[sk, (c + 2) % 3]] - P[T[sk, c]]
    ang = np.arccos(np.clip((a * b).sum(1) / np.linalg.norm(a, axis=1) / np.linalg.norm(b, axis=1), -1, 1))
    np.add.at(Ns, pk[T[sk, c]], np.nan_to_num(fn / np.linalg.norm(fn, axis=1, keepdims=True) * ang[:, None]))
ov = np.unique(T[sk]); lv = np.unique(T[ln])
n_ = Ns[pk[ov]]; n_ = np.nan_to_num(n_ / np.linalg.norm(n_, axis=1, keepdims=True))
pred = P[ov] - 0.004 * n_
# candidate lining GLB vertices per outer vertex: all within 0.3 mm of the nearest
tree = cKDTree(P[lv]); dd, q = tree.query(pred)
cands = [lv[tree.query_ball_point(p_, d_ + 3e-4)] for p_, d_ in zip(pred, dd)]
multi = sum(len(set(map(tuple, np.round(P[c], 6)))) > 1 for c in cands)
uvmulti = sum(len(c) > 1 and len(np.unique(np.round(U[c], 5), axis=0)) > 1 for c in cands)
print('outer vertices', len(ov), 'candidates >1 position', multi, 'lining UV seam (several UVs at the twin)', uvmulti)
# outer topological seams
_, tk = np.unique(np.round(P[ov], 6), axis=0, return_inverse=True); tk = tk.ravel()
cnt = np.bincount(tk); print('skirt seam positions (several GLB vertices)', int((cnt > 1).sum()))
lin_seam = np.array([len(c) > 1 and len(np.unique(np.round(U[c], 5), axis=0)) > 1 for c in cands])
skirt_seam = cnt[tk] > 1
print('lining seam at a skirt non-seam vertex', int((lin_seam & ~skirt_seam).sum()), 'both', int((lin_seam & skirt_seam).sum()))
# face check: reversed twin faces
m = dict(zip(ov, cands))
lf = {tuple(sorted(t)) for t in T[ln].tolist()}
hit = 0
for f in T[sk]:
    import itertools
    ok = any(tuple(sorted(c)) in lf for c in itertools.product(*[m[v] for v in f]))
    hit += ok
print('skirt faces with a lining twin face', hit, 'of', len(sk), '; lining faces', len(ln), '(rim', len(ln) - len(sk), ')')
