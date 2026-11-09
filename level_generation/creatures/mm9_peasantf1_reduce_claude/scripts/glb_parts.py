#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_peasantf1.glb) from PeasantF1's last mesh before the GLB build
(../mm9_peasantf1_claude/work/uv_tex2.npz: parts 0 head (face skin, neck, eyes, teeth), 1 scarf (hood), 2 dress (bodice,
sleeves, lacing), 3 skirt, 4 legs, 5 hands (MPFB arms), 6 lining (skirt lining + hem rim); 'inner' flag per face).
tweak_pf1.py moved positions after that file (mouth, nose, ears, eyes: up to a few cm) but never the UVs, so each GLB face is
matched within its material by its UV centroid together with its rest centroid (npz z-up rig frame -> glTF y-up; the GLB is
mirrored in x by mirror_glb.py, so both x signs are tried and the better one used).
Also: per face dominant joint index and the matched npz face (src). Writes work/glb_parts.npz: mat (prim index), part, inner, cen
(glTF), joint, src, jnames, names."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf1.glb', 'PeasantF1')
s = np.load(HERE.parent / 'mm9_peasantf1_claude' / 'work' / 'uv_tex2.npz')
tri = s['tri']; fpart = s['comp'][tri[:, 0]]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[], src=[])
PR = ['PeasantF1_B', 'PeasantF1Head']
for k, name in enumerate(PR):
    P, T, U = D[name]['P'], D[name]['T'], D[name]['UV']
    msel = np.flatnonzero(s['mat'] == k)
    res = []
    for sx in (1, -1):
        for fv in (False, True):
            co = s['co'][:, [0, 2, 1]] * [sx, 1, -1]
            un = s['uv'][tri[msel]].mean(1)
            ug = U[T].mean(1)
            if fv:
                ug = np.c_[ug[:, 0], 1 - ug[:, 1]]
            kn = np.c_[co[tri[msel]].mean(1), un * 2.0]      # 1 UV unit ~ 2 m: UV decides, position breaks mirrored ties
            kg = np.c_[P[T].mean(1), ug * 2.0]
            dist, nn = cKDTree(kn).query(kg)
            res.append((np.percentile(dist, 99), sx, fv, dist, msel[nn]))
    p99, sx, fv, dist, nn = min(res, key=lambda r: r[0])
    print(name, len(T), 'x sign', sx, 'v flip', fv, 'max dist', dist.max().round(5), 'p99', p99.round(5),
          'dup', len(nn) - len(np.unique(nn)))
    part = fpart[nn].copy(); inner = s['inner'][nn].copy()
    out['mat'] += [k] * len(T); out['cen'].append(P[T].mean(1))
    out['part'].append(part); out['inner'].append(inner); out['src'].append(nn)
    J, W = D[name]['J'], D[name]['W']
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
