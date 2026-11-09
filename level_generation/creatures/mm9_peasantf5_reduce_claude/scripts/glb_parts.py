#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_peasantf5.glb) from PeasantF5's last mesh before the GLB build
(../mm9_peasantf5_claude/work/uv_tex2.npz, 12,992 faces: parts head, coif, dress, skirt, legs, arms, hands, bracelets,
ornaments, buckle, lining; 'inner' = lining faces), matched by rest centroid (npz z-up rig frame -> glTF y-up; the GLB is
mirrored in x by mirror_glb.py as the last build step, so both x signs are tried and the closer kept per primitive).
Primitive order PeasantF5_B (body), PeasantF5Head. Also: per face dominant joint (hand vs forearm faces of the MPFB hands).
Writes work/glb_parts.npz: mat (prim index), part, inner, cen (glTF), joint (dominant joint index per face), jnames."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantf5.glb', 'PeasantF5')
s = np.load(HERE.parent / 'mm9_peasantf5_claude' / 'work' / 'uv_tex2.npz')
tri = s['tri']; fpart = s['comp'][tri[:, 0]]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[])
PR = ['PeasantF5_B', 'PeasantF5Head']
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']; gc = P[T].mean(1)
    msel = np.flatnonzero(s['mat'] == k)
    best = None
    for sx in (1, -1):
        co = s['co'][:, [0, 2, 1]] * [sx, 1, -1]; fc = co[tri].mean(1)
        dist, nn = cKDTree(fc[msel]).query(gc)
        if best is None or dist.max() < best[0].max():
            best = (dist, msel[nn], sx)
    dist, nn, sx = best
    print(name, len(T), 'npz faces', len(msel), 'x sign', sx, 'max dist', dist.max(), 'p99', np.percentile(dist, 99),
          'dup', len(nn) - len(np.unique(nn)))
    out['mat'] += [k] * len(T); out['cen'].append(gc)
    out['part'].append(fpart[nn].copy()); out['inner'].append(s['inner'][nn].copy())
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
    u, c = np.unique(res['joint'][m], return_counts=True); top = sorted(zip(c, u), reverse=True)[:6]
    print(f'part {p} {names[p]:9s} {m.sum():6d} inner {int(res["inner"][m].sum()):5d} mats {np.unique(res["mat"][m]).tolist()}',
          {jn[b]: int(a) for a, b in top})
np.savez(HERE / 'work' / 'glb_parts.npz', **res, names=names)
