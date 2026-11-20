#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_peasantdm4.glb, node PeasantDM4; prims PeasantDM4 body, PeasantDM4Head
head + MPFB hands) from the creature's build blend (work/blend_parts.npz from dump_blend_parts.py on
../mm9_peasantdm4_claude/work/rigid_v3n.blend): head / hand / lined face attributes, matched by rest centroid. The export
mirrors x (mirror_glb.py) and lifts the mesh; the transform is solved here (axis signs tried, offset from medians).
Also per face: dominant joint, UV area (texels at 2K), welded connected component.
Writes work/glb_parts.npz: mat, head, hand, lined, cen (glTF), joint, jnames, uvarea, comp."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import bglbio  # noqa: E402
doc, b = bglbio.read(HERE / 'before' / 'mm9_peasantdm4.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'PeasantDM4' and 'mesh' in n)
prims = bglbio.prims(doc, b, node['mesh'])
s = np.load(HERE / 'work' / 'blend_parts.npz')
bc = s['cen']
jn = [doc['nodes'][j]['name'] for j in doc['skins'][node['skin']]['joints']]
gcs = [pr['POSITION'].astype(float)[pr['T']].mean(1) for pr in prims]
G = np.concatenate(gcs)
best = None
for sx in (1, -1):
    for sz in (1, -1):
        # glTF (x, y, z) <- blender (sx*X, Z, sz*Y) + offset
        t = np.c_[sx * bc[:, 0], bc[:, 2], sz * bc[:, 1]]
        off = np.median(G, 0) - np.median(t, 0)
        for _ in range(3):
            d, nn = cKDTree(t + off).query(G); off += np.median(G - (t[nn] + off), 0)
        d, nn = cKDTree(t + off).query(G)
        if best is None or np.percentile(d, 90) < best[0]:
            best = (np.percentile(d, 90), sx, sz, off, d, nn)
p90, sx, sz, off, dist, nn = best
print('MATCH sx', sx, 'sz', sz, 'offset', off.round(4), 'p50/p90/p99/max mm', *(np.percentile(dist, [50, 90, 99, 100]) * 1000).round(3))
out = dict(mat=[], joint=[], uvarea=[], comp=[])
for k, pr in enumerate(prims):
    T = pr['T']; P = pr['POSITION'].astype(float); UV = pr['TEXCOORD_0'].astype(float)
    J = pr['JOINTS_0'].astype(int); W = pr['WEIGHTS_0'].astype(float)
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    a = UV[T]; ar = np.abs((a[:, 1, 0] - a[:, 0, 0]) * (a[:, 2, 1] - a[:, 0, 1]) - (a[:, 2, 0] - a[:, 0, 0]) * (a[:, 1, 1] - a[:, 0, 1])) / 2 * 2048 ** 2
    _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
    r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
    _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
    out['mat'].append(np.full(len(T), k)); out['joint'].append(acc.argmax(1)); out['uvarea'].append(ar)
    out['comp'].append(lab[FT[:, 0]] + 100000 * k)
    print(pr['material'], len(T), 'components', len(np.unique(lab[FT[:, 0]])))
res = {k: np.concatenate(v) for k, v in out.items()}
for k in ('head', 'hand', 'lined'):
    res[k] = s[k][nn]
res['cen'] = G; res['jnames'] = np.array(jn); res['match_mm'] = dist * 1000
for k in range(len(prims)):
    m = res['mat'] == k
    print(prims[k]['material'], 'head', int(res['head'][m].sum()), 'hand', int(res['hand'][m].sum()), 'lined', int(res['lined'][m].sum()),
          'uvarea<0.5 texel', int((res['uvarea'][m] < 0.5).sum()), 'match>0.5mm', int((dist[m] > 5e-4).sum()))
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
