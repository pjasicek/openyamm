#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_scholar.glb, node Scholar, prims Scholar_A then ScholarHead) from the
creature's last mesh before the GLB build (../mm9_scholar_claude/work/uv_tex.npz: 13,782 faces = the GLB's; comp per vertex:
0 robe (with the stole, sleeves), 1 head (face shell, eyes, neck), 2 hair (hair + beard shell), 3 cap, 4 jewel (chain beads,
medallion, buckle), 5 legs (low shoes + shin stub), 6 hands (MPFB, forearm stub); 'inner' = linings_wy.py twin and rim faces).
Frames: GLB (x, y, z) = npz (+-x, z, -y) plus the floor/mirror offsets of tail_sc.sh, so the rest centroids are compared after
aligning the two bounding-box minima. Each GLB face is matched within its material by UV centroid (dominant), rest centroid and
face normal (a lining twin has its outer face's UVs, sits 2 mm behind it and faces the other way).
Writes work/glb_parts.npz: mat, part, inner, sub (head pieces: 0 face shell, 3 eye = small closed head-part pieces), cen, joint,
src, jnames, names."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_scholar.glb', 'Scholar')
s = np.load(HERE.parent / 'mm9_scholar_claude' / 'work' / 'uv_tex.npz')
tri = s['tri']; fpart = s['comp'][tri[:, 0]]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[], src=[])
PR = ['Scholar_A', 'ScholarHead']
mats = [str(x) for x in s['matnames']]; print('npz materials', mats, np.bincount(s['mat']))
allP = np.concatenate([D[k]['P'] for k in PR])


def fnorm(X, T):
    n = np.cross(X[T[:, 1]] - X[T[:, 0]], X[T[:, 2]] - X[T[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-20)


for k, name in enumerate(PR):
    P, T, U = D[name]['P'], D[name]['T'], D[name]['UV']
    nk = len(T)
    cand = [m for m in range(len(mats)) if (s['mat'] == m).sum() == nk]
    msel = np.flatnonzero(s['mat'] == cand[0])
    res = []
    for sx in (1, -1):
        for fv in (False, True):
            co = s['co'][:, [0, 2, 1]] * [sx, 1, -1]
            co = co - co.min(0) + allP.min(0)
            Tn = tri[msel]
            if sx < 0:
                Tn = Tn[:, ::-1]                       # a mirror reverses the winding
            un = s['uv'][Tn].mean(1); ug = U[T].mean(1)
            if fv:
                ug = np.c_[ug[:, 0], 1 - ug[:, 1]]
            kn = np.c_[co[Tn].mean(1), un * 2.0, fnorm(co, Tn) * 0.004]
            kg = np.c_[P[T].mean(1), ug * 2.0, fnorm(P, T) * 0.004]
            dist, nn = cKDTree(kn).query(kg)
            res.append((np.percentile(dist, 99), sx, fv, dist, msel[nn]))
    p99, sx, fv, dist, nn = min(res, key=lambda r: r[0])
    print(name, nk, 'x sign', sx, 'v flip', fv, 'max dist', dist.max().round(5), 'p99', p99.round(5),
          'dup', len(nn) - len(np.unique(nn)))
    out['mat'] += [k] * nk; out['cen'].append(P[T].mean(1))
    out['part'].append(fpart[nn]); out['inner'].append(s['inner'][nn]); out['src'].append(nn)
    J, W = D[name]['J'], D[name]['W']
    acc = np.zeros((nk, len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(nk), J[T[:, c], i]), W[T[:, c], i])
    out['joint'].append(acc.argmax(1))
res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
res['jnames'] = np.array(jn)
names = s['names']
# head pieces: connected by welded position; small closed pieces of the head part (eyeballs) -> 'eye'
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
Ph = D['ScholarHead']['P']; Th = D['ScholarHead']['T']
_, w = np.unique(np.round(Ph, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[Th]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl2 = lab[FT[:, 0]]; cnt = np.bincount(fl2)
hm = res['mat'] == 1; ph = res['part'][hm]; inner_h = res['inner'][hm]
for c in np.unique(fl2):
    m = fl2 == c
    print('  head piece', c, int(m.sum()), 'inner', int(inner_h[m].sum()), 'parts', np.bincount(ph[m], minlength=7).tolist(),
          'centre', Ph[Th[m]].reshape(-1, 3).mean(0).round(3))
sub_h = np.where(ph == 1, 0, -1)
sub_h[(ph == 1) & (cnt[fl2] < 600)] = 3
nb = len(D['Scholar_A']['T'])
res['sub'] = np.r_[-np.ones(nb, int), sub_h]
for p in np.unique(res['part']):
    m = res['part'] == p
    print(f'part {p} {names[p]:7s} {m.sum():6d} inner {int(res["inner"][m].sum()):5d} mats {np.unique(res["mat"][m]).tolist()}')
np.savez(HERE / 'work' / 'glb_parts.npz', **res, names=names)
