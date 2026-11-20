#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_peasantf6.glb) from PeasantF6's last mesh before the GLB build
(../mm9_peasantf6_claude/work/uv_lined.npz, 14,620 faces = LOD0: parts 0 head (F5's head: face skin, neck, scalp, eyes,
teeth, mouth backing), 1 dress, 2 skirt, 3 legs, 4 arms, 5 hands (MPFB), 6 bracelets, 7 buckle, 8 lining, 9 hair (bob shell +
rim strip), 10 ears, 11 braid; 'inner' = lining/rim faces), matched by rest centroid (npz z-up rig frame -> glTF y-up).
Primitive order PeasantF6_A (body), PeasantF6Head. Also: per face dominant joint index.
Writes work/glb_parts.npz: mat (prim index), part, inner, cen (glTF), joint, jnames, names."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf6.glb', 'PeasantF6')
s = np.load(HERE.parent / 'mm9_peasantf6_claude' / 'work' / 'uv_lined.npz')
co = s['co'][:, [0, 2, 1]] * [1, 1, -1]
tri = s['tri']; fc = co[tri].mean(1); fpart = s['comp'][tri[:, 0]]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[])
PR = ['PeasantF6_A', 'PeasantF6Head']
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']; gc = P[T].mean(1)
    msel = np.flatnonzero(s['mat'] == k)
    dist, nn = cKDTree(fc[msel]).query(gc); nn = msel[nn]
    print(name, len(T), 'max dist', dist.max(), 'p99', np.percentile(dist, 99), 'dup', len(nn) - len(np.unique(nn)))
    part = fpart[nn].copy(); inner = s['inner'][nn].copy()
    if name == 'PeasantF6Head':
        # the braid moved after uv_lined.npz (up to 9 mm); label each welded connected component of the head prim by its
        # majority (skull+face, eyes, mouth backing = head; hair shell; braid; two ears)
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
        r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
        _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
        fl = lab[FT[:, 0]]
        for cmp in np.unique(fl):
            m = fl == cmp; u, cnt = np.unique(part[m], return_counts=True); part[m] = u[cnt.argmax()]
    out['mat'] += [k] * len(T); out['cen'].append(gc)
    out['part'].append(part); out['inner'].append(inner)
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    out['joint'].append(acc.argmax(1))
res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
res['jnames'] = np.array(jn)
names = s['names']
for p in np.unique(res['part']):
    m = res['part'] == p
    print(f'part {p} {names[p]:9s} {m.sum():6d} inner {int(res["inner"][m].sum()):5d} mats {np.unique(res["mat"][m]).tolist()}')
for p in (4, 5):
    m = res['part'] == p
    u, c = np.unique(res['joint'][m], return_counts=True)
    print(names[p], 'by joint', {jn[a]: int(b) for a, b in zip(u, c)})
np.savez(HERE / 'work' / 'glb_parts.npz', **res, names=names)
