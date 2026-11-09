#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_peasantf3.glb) from PeasantF3's last mesh before the GLB build
(../mm9_peasantf3_claude/work/uv_tex2_chin.npz: parts head, scarf (hood), dress, skirt, legs, hands (MPFB arms), lining
(skirt lining), veil, braids; 'inner' = lining faces incl. the veil lining), matched by rest centroid (npz z-up rig frame ->
glTF y-up, no offset: both have the pelvis at the origin). Primitive order PeasantF3_B (body), PeasantF3Head.
Also: per face dominant joint name (sub-labels for the MPFB arms: upper-arm stub inside the sleeve, forearm, hand, fingers).
Writes work/glb_parts.npz: mat (prim index), part, inner, cen (glTF), joint (dominant joint index per face), jnames."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf3.glb', 'PeasantF3')
s = np.load(HERE.parent / 'mm9_peasantf3_claude' / 'work' / 'uv_tex2_chin.npz')
co = s['co'][:, [0, 2, 1]] * [1, 1, -1]
tri = s['tri']; fc = co[tri].mean(1); fpart = s['comp'][tri[:, 0]]
tree = cKDTree(fc)
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[])
PR = ['PeasantF3_B', 'PeasantF3Head']
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']; gc = P[T].mean(1)
    msel = np.flatnonzero(s['mat'] == k)
    dist, nn = cKDTree(fc[msel]).query(gc); nn = msel[nn]
    print(name, len(T), 'max dist', dist.max(), 'p99', np.percentile(dist, 99), 'dup', len(nn) - len(np.unique(nn)))
    part = fpart[nn].copy(); inner = s['inner'][nn].copy()
    if name == 'PeasantF3Head':
        # the veil and braid vertices moved after uv_tex2_chin.npz (up to 3 cm); label the head prim by welded connected
        # component instead: the head+hood shell (labels 0/1 by nearest face), the veil, two braids, eyes and teeth (head)
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        _, w = np.unique(np.round(P, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[T]; n = w.max() + 1
        r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
        _, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
        fl = lab[FT[:, 0]]
        for cmp in np.unique(fl):
            m = fl == cmp; u, cnt = np.unique(part[m], return_counts=True); maj = u[cnt.argmax()]
            if maj in (7, 8):
                part[m] = maj
                if maj == 8:
                    inner[m] = False
            elif not np.isin(part[m], (0, 1)).all():
                part[m & ~np.isin(part, (0, 1))] = 0
            print('  component', cmp, int(m.sum()), 'label', int(maj))
        vm = part == 7
        vsel = np.flatnonzero(fpart == 7)
        _, vn = cKDTree(fc[vsel]).query(gc[vm]); inner[vm] = s['inner'][vsel[vn]]
    out['mat'] += [k] * len(T); out['cen'].append(gc)
    out['part'].append(part); out['inner'].append(inner)
    # dominant joint per face: summed weights of the three corners
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
    print(f'part {p} {names[p]:7s} {m.sum():6d} inner {int(res["inner"][m].sum()):5d} mats {np.unique(res["mat"][m]).tolist()}')
m = res['part'] == 5
u, c = np.unique(res['joint'][m], return_counts=True)
print('hands by joint', {jn[a]: int(b) for a, b in zip(u, c)})
np.savez(HERE / 'work' / 'glb_parts.npz', **res, names=names)
