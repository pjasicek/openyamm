#!/usr/bin/env python3
"""Per-face labels of the installed elf LOD0 (before/mm9_peasantgirl1e.glb, the family's superset: human head + elf ears) from
the creature's last mesh before the GLB build (../mm9_peasantgirl_claude/work/uv_tex2.npz: parts head, skirt, dress, hair,
buttons, legs, hands, ears, lining; mat 0 body, 1 head), matched by rest face centroid (npz z-up -> glTF y-up, x sign and
offset fitted: build_runtime mirrors and floor-fixes). Primitive order PeasantGirl_G1E (body), PeasantGirlHead.
Also the dominant joint per face. Writes work/glb_parts.npz: mat, part, inner, cen, joint, jnames, names."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantgirl1e.glb', 'PeasantGirl')
s = np.load(HERE.parent / 'mm9_peasantgirl_claude' / 'work' / 'uv_tex2.npz')
co0 = np.c_[s['co'][:, 0], s['co'][:, 2], -s['co'][:, 1]]
tri = s['tri']; fpart = s['comp'][tri[:, 0]]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
PR = ['PeasantGirl_G1E', 'PeasantGirlHead']
allP = np.concatenate([D[k]['P'] for k in PR])
best = None
for sx in (1, -1):
    co = co0 * [sx, 1, 1]; off = allP.min(0) - co.min(0); off[0] = 0
    fc = (co + off)[tri].mean(1)
    dd = []
    for k, name in enumerate(PR):
        P, T = D[name]['P'], D[name]['T']; msel = np.flatnonzero(s['mat'] == k)
        dd.append(cKDTree(fc[msel]).query(P[T].mean(1))[0].max())
    print('x sign', sx, 'offset', off.round(5), 'max centroid dist', [round(float(x), 6) for x in dd])
    if best is None or max(dd) < best[0]:
        best = (max(dd), fc)
fc = best[1]
out = dict(mat=[], part=[], inner=[], cen=[], joint=[])
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']; gc = P[T].mean(1)
    msel = np.flatnonzero(s['mat'] == k)
    dist, nn = cKDTree(fc[msel]).query(gc); nn = msel[nn]
    print(name, len(T), 'max dist', dist.max(), 'p99', np.percentile(dist, 99), 'dup', len(nn) - len(np.unique(nn)))
    out['mat'] += [k] * len(T); out['cen'].append(gc)
    out['part'].append(fpart[nn]); out['inner'].append(s['inner'][nn])
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
m = res['part'] == 6
u, c = np.unique(res['joint'][m], return_counts=True)
print('hands by joint', {jn[a]: int(b) for a, b in zip(u, c)})
np.savez(HERE / 'work' / 'glb_parts.npz', **res, names=names)
