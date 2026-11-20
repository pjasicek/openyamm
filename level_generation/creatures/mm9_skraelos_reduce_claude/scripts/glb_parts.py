#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_skraelos.glb, node Scholar, prims Scholar_A then ScholarHead) from the
creature's last mesh before the GLB build (../mm9_skraelos_claude/work/uv_ln_tex.npz: 13,012 faces = the GLB's; comp per vertex:
0 robe (robe + tabard + sleeves), 1 hood, 2 hands (bone pieces), 3 cap, 4 head (the skull: cranium, jaw, teeth, ember eyes),
5 cowl (neck tube), 6 necklace, 7 staff, 8 heldskull, 9 pendant; no linings: 'inner' is all False).
Frames: GLB (x, y, z) = npz (+-x, z, -y) plus the mirror of build_runtime_sk.sh, so the rest centroids are compared after
aligning the two bounding-box minima. Each GLB face is matched within its material by UV centroid (dominant), rest centroid and
face normal (a lining twin has its outer face's UVs, sits 2 mm behind it and faces the other way).
Writes work/glb_parts.npz: mat, part, inner, sub (-1), hpiece (hand bone piece per face, -1 elsewhere), cen, joint, src, jnames,
names."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_skraelos.glb', 'Skraelos')
s = np.load(HERE.parent / 'mm9_skraelos_claude' / 'work' / 'uv_ln_tex.npz')
tri = s['tri']; fpart = s['comp'][tri[:, 0]]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[], src=[], hpiece=[])
PR = ['Skraelos', 'SkraelosHead']
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
    out['part'].append(fpart[nn]); out['hpiece'].append(np.where(fpart[nn] == 2, s['hand_piece'][tri[nn, 0]], -1)); out['inner'].append(s['inner'][nn]); out['src'].append(nn)
    J, W = D[name]['J'], D[name]['W']
    acc = np.zeros((nk, len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(nk), J[T[:, c], i]), W[T[:, c], i])
    out['joint'].append(acc.argmax(1))
res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
res['jnames'] = np.array(jn)
names = s['names']
res['sub'] = -np.ones(len(res['mat']), int)
for p in np.unique(res['part']):
    m = res['part'] == p
    print(f'part {p} {names[p]:9s} {m.sum():6d} mats {np.unique(res["mat"][m]).tolist()}')
np.savez(HERE / 'work' / 'glb_parts.npz', **res, names=names)
