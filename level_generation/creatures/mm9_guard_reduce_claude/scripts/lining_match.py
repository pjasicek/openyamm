#!/usr/bin/env python3
"""Exact lining pairing on the installed GLB (per primitive): twin of each outer vertex = the lining vertex nearest its 3 mm
inward prediction (mpqem.py's rule); an outer face is lined when the reversed twin triple is a lining face. Prints lining faces
with no outer partner (they would be lost by the re-emission) and outer faces marked lined that have no lining face.
With --write <tag>: rewrites work/glb_sets_<tag>.npz with lined = the exact pairing and the unpaired lining faces kept as
ordinary kept faces (their outer neighbours' vertices locked through keep). Usage: lining_match.py <tag> [--write]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
tag = sys.argv[1]; S = dict(np.load(HERE / 'work' / f'glb_sets_{tag}.npz'))
doc, b = bglbio.read(HERE / 'before' / 'mm9_guard.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'Guard' and 'mesh' in n)
prims = bglbio.prims(doc, b, node['mesh']); off = np.cumsum([0] + [len(p['T']) for p in prims])
newl = S['lined'].copy(); orphan_all = np.zeros(len(newl), bool)
for pi, pr in enumerate(prims):
    sl = slice(off[pi], off[pi + 1]); T = pr['T']; P = pr['POSITION'].astype(np.float64)
    lining = S['lining'][sl]; outer = ~lining
    lf = np.flatnonzero(lining)
    if not len(lf): continue
    # outer faces that are candidates: those of the parts that have a lining; lined region by vertex normals over S['lined'] as mpqem
    of = np.flatnonzero(S['lined'][sl])
    lv = np.unique(T[lf])
    _, pk = np.unique(np.round(P, 5), axis=0, return_inverse=True); pk = pk.ravel()
    fn = np.cross(P[T[of, 1]] - P[T[of, 0]], P[T[of, 2]] - P[T[of, 0]]) / 2
    Ns = np.zeros((pk.max() + 1, 3))
    for c in range(3): np.add.at(Ns, pk[T[of, c]], fn)
    ov = np.unique(T[of]); n_ = Ns[pk[ov]]; n_ /= np.linalg.norm(n_, axis=1, keepdims=True)
    dd, q = cKDTree(P[lv]).query(P[ov] - 0.003 * n_)
    twin = -np.ones(len(P), np.int64); twin[ov] = lv[q]
    lset = {tuple(sorted(t)) for t in T[lf]}
    tw = twin[T[of]]
    paired = np.array([(t >= 0).all() and tuple(sorted(t)) in lset for t in tw])
    used = {tuple(sorted(t)) for t, ok in zip(tw, paired) if ok}
    orphan = np.array([tuple(sorted(t)) not in used for t in T[lf]])
    print(f"{pr['material']}: lining {len(lf)}, lined outer {len(of)}, paired {int(paired.sum())}, lined without lining {int((~paired).sum())}, "
          f"orphan lining {int(orphan.sum())}, twin residual max {dd.max()*1000:.2f} mm p99 {np.percentile(dd, 99)*1000:.2f}")
    bad = of[~paired]; newl[off[pi] + bad] = False
    orphan_all[off[pi] + lf[orphan]] = True
    if orphan.any():
        c = P[T[lf[orphan]]].mean(1); print('   orphan centroids (glTF)', np.round(c[:8], 3).tolist())
if '--write' in sys.argv:
    S['lined'] = newl; S['keep'] = S['keep'] | orphan_all; S['lining'] = S['lining'] & ~orphan_all
    np.savez(HERE / 'work' / f'glb_sets_{tag}.npz', **S); print('WROTE', tag, 'orphans kept', int(orphan_all.sum()), 'lined', int(newl.sum()))
