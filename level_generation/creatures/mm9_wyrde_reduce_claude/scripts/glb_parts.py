#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_wyrde.glb) from the creature's last mesh before the GLB build
(../mm9_wyrde_claude/work/uv_tex4.npz: 14,932 faces = the GLB's; parts 0 head set (face, neck, hair, circlet, hood, eyes), 1 mantle,
2 dress (gown + sleeves + cuff caps), 3 jewel, 4 skirt (underskirt), 5 legs, 6 hands (MPFB, forearm stub); 'inner' = linings_wy.py
twin and rim faces). Frames: GLB (x, y, z) = npz (+-x, z, -y) (mirror_glb.py flips x; both signs tried). Each GLB face is matched
within its material by UV centroid (dominant), rest centroid and face normal (a lining twin has its outer face's UVs, sits 2 mm
behind it and faces the other way).
Head sub-labels (head set only) from seg_wy.py's labels (work/seg.npz: head = face skin/neck/ears, hair, hood; mirrored |x|,
assemble_wy.py's X0 0.008 / Z0 -0.9297 and nearest-vertex majority vote); small closed pieces of the head set (eyeballs) -> 'eye'.
Writes work/glb_parts.npz: mat, part, inner, sub (head: 0 face, 1 hair, 2 hood, 3 eye; -1 elsewhere), cen, joint, src, jnames, names."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_wyrde.glb', 'Wyrde')
s = np.load(HERE.parent / 'mm9_wyrde_claude' / 'work' / 'uv_tex4.npz')
tri = s['tri']; fpart = s['comp'][tri[:, 0]]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[], src=[])
PR = ['Wyrde_YOUNG', 'WyrdeHead']
mats = [str(x) for x in s['matnames']]; print('npz materials', mats, np.bincount(s['mat']))


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
# ---- head sub-labels from the segmentation
g = np.load(HERE.parent / 'mm9_wyrde_claude' / 'work' / 'seg.npz'); labels = [str(x) for x in g['labels']]
sco = g['co'] + [0.008, 0, -0.9297]; slab = g['comp']
if slab.min() >= 100:
    slab = slab - 100
pos = (sco[:, 0] >= -0.002) & (g['comp'] >= 100); tree = cKDTree(np.c_[sco[pos][:, 0], sco[pos][:, 1], sco[pos][:, 2]]); lab_src = slab[pos] - 100
Ph = D['WyrdeHead']['P']; Th = D['WyrdeHead']['T']
q = np.c_[np.abs(Ph[:, 0]), -Ph[:, 2], Ph[:, 1]]                       # GLB -> npz frame, mirrored half
dq, iq = tree.query(q); vl = lab_src[iq]
print('seg labels', labels, 'vertex query dist p50/p99/max', np.percentile(dq, [50, 99, 100]).round(4))
fv_ = vl[Th]; fl = np.where(fv_[:, 1] == fv_[:, 2], fv_[:, 1], fv_[:, 0])
SUBMAP = {labels.index('head'): 0, labels.index('hair'): 1, labels.index('hood'): 2}
sub_h = np.array([SUBMAP.get(int(x), 2) for x in fl])
# small closed pieces (eyeballs): connected by welded position
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
_, w = np.unique(np.round(Ph, 6), axis=0, return_inverse=True); w = w.ravel(); FT = w[Th]; n = w.max() + 1
r_ = np.r_[FT[:, 0], FT[:, 1], FT[:, 2]]; c_ = np.r_[FT[:, 1], FT[:, 2], FT[:, 0]]
_, lab = connected_components(coo_matrix((np.ones(len(r_)), (r_, c_)), shape=(n, n)), directed=False)
fl2 = lab[FT[:, 0]]; cnt = np.bincount(fl2)
print('head pieces', sorted(cnt.tolist(), reverse=True)[:12])
inner_h = res['inner'][res['mat'] == 1]
for c in np.unique(fl2):
    m = fl2 == c
    print('  head piece', c, int(m.sum()), 'inner', int(inner_h[m].sum()), 'labels', np.bincount(sub_h[m], minlength=4).tolist(),
          'centre', Ph[Th[m]].reshape(-1, 3).mean(0).round(3))
sub_h[(cnt[fl2] < 600) & (cnt[fl2] >= 200) & ~inner_h] = 3
nb = len(D['Wyrde_YOUNG']['T'])
res['sub'] = np.r_[-np.ones(nb, int), sub_h]
for p in np.unique(res['part']):
    m = res['part'] == p
    print(f'part {p} {names[p]:7s} {m.sum():6d} inner {int(res["inner"][m].sum()):5d} mats {np.unique(res["mat"][m]).tolist()}')
hm = res['mat'] == 1
for sname, sv in (('face', 0), ('hair', 1), ('hood', 2), ('eye', 3)):
    m = hm & (res['sub'] == sv)
    print(f'  head {sname:5s} {m.sum():5d} inner {int(res["inner"][m].sum()):4d}')
np.savez(HERE / 'work' / 'glb_parts.npz', **res, names=names)
