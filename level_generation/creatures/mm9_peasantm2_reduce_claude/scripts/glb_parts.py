#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_peasantm2.glb, node PeasantM2; prims PeasantM2 (limbs), Pm2Torso_A,
Pm2Head) from work/final_parts.npz (dump_final_parts.py on the creature's final_v1.blend), matched by rest centroid
(Blender z-up -> glTF y-up (x, z, -y), offset fitted). Also the dominant joint per face and lining pairs: every lining face
(lining 1/3/4) is matched to the outer face it was duplicated from (reversed copy, offset 3 mm / 2 mm / 3 mm along the
vertex normals), giving a twin GLB vertex per outer GLB vertex of every lined face.
Writes work/glb_parts.npz: mat (prim index), part, lining, hand, ear, cen, joint, jnames, lined (outer face has a lining twin
face), twin (per GLB vertex, prims concatenated (voff): the prim-local index of its lining twin vertex, -1 none), ambig (vertex whose
twin is not unique), pair (outer lined face -> prim-local lining face), unmatched (lining face without an outer face), voff, foff."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_peasantm2.glb', 'PeasantM2')
PR = ['PeasantM2', 'Pm2Torso_A', 'Pm2Head']
s = np.load(HERE / 'work' / 'final_parts.npz')
fc = s['cen'][:, [0, 2, 1]] * [1, 1, -1]
allP = np.concatenate([D[k]['P'] for k in PR]); bco = s['co'][:, [0, 2, 1]] * [1, 1, -1]
offset = allP.min(0) - bco.min(0); print('OFFSET', offset.round(6)); fc = fc + offset
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], part=[], lining=[], hand=[], ear=[], cen=[], joint=[], lined=[])
twins = []; voff = 0
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']; gc = P[T].mean(1)
    dist, nn = cKDTree(fc).query(gc)
    print(name, len(T), 'max dist', dist.max().round(7), 'p99', np.percentile(dist, 99).round(7), 'dup', len(nn) - len(np.unique(nn)))
    lab = {key: (s[key] if key in s.files else np.zeros(len(s['cen']), np.int32))[nn] for key in ('part', 'lining', 'hand', 'ear')}  # PeasantM2: no ear attribute
    # lining pairs: lining 1/3/4 faces -> the outer face they copy
    twin = -np.ones(len(P), np.int64); lined = np.zeros(len(T), bool); pair = -np.ones(len(T), np.int64)
    ambig = np.zeros(len(P), bool); unmatched = np.zeros(len(T), bool)
    outer = np.flatnonzero(lab['lining'] == 0)
    otree = cKDTree(gc[outer])
    for lv, offm in ((1, 0.003), (3, 0.002), (4, 0.003)):
        lf = np.flatnonzero(lab['lining'] == lv)
        if not len(lf): continue
        bad = 0; res = []
        _, cand = otree.query(gc[lf], 12)
        for f, cs in zip(lf, cand):
            best = None
            for c in outer[cs]:
                d = np.linalg.norm(P[T[f]][:, None] - P[T[c]][None], axis=-1)       # lining corner x outer corner
                perm = d.argmin(1)
                if len(set(perm.tolist())) != 3: continue
                e = d[np.arange(3), perm]
                if best is None or e.max() < best[0]: best = (e.max(), c, perm)
            if best is None or best[0] > offm * 1.8 or lined[best[1]]:
                bad += 1; unmatched[f] = True; continue
            c, perm = best[1], best[2]; lined[c] = True; pair[c] = f; res.append(best[0])
            for i in range(3):
                o = T[c, perm[i]]; l_ = T[f, i]
                if twin[o] >= 0 and twin[o] != l_:
                    if np.linalg.norm(P[twin[o]] - P[l_]) > 1e-6 or np.abs(D[name]['UV'][twin[o]] - D[name]['UV'][l_]).max() > 1e-6:
                        bad += 1000; ambig[o] = True
                twin[o] = l_
        print(f'  lining {lv}: {len(lf)} faces, matched {len(res)}, unmatched/conflicts {bad}, offset max {max(res) * 1000:.2f} mm' if res else f'  lining {lv}: none')
    print(f'  {name}: ambiguous twin vertices {int(ambig.sum())}, unmatched lining faces {int(unmatched.sum())}')
    out['mat'] += [k] * len(T); out['cen'].append(gc); out['lined'].append(lined)
    out.setdefault('pair', []).append(pair); out.setdefault('unmatched', []).append(unmatched)
    out.setdefault('ambig', []).append(ambig)
    for key in ('part', 'lining', 'hand', 'ear'): out[key].append(lab[key])
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    out['joint'].append(acc.argmax(1))
    twins.append(twin); voff += len(P)
res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
res['jnames'] = np.array(jn); res['twin'] = np.concatenate(twins)
res['voff'] = np.cumsum([0] + [len(D[k]['P']) for k in PR]); res['foff'] = np.cumsum([0] + [len(D[k]['T']) for k in PR])
for p in np.unique(res['part']):
    m = res['part'] == p
    print(f'part {p:2d} {m.sum():6d} lining {dict(zip(*[x.tolist() for x in np.unique(res["lining"][m], return_counts=True)]))} '
          f'lined {int(res["lined"][m].sum())} mats {np.unique(res["mat"][m]).tolist()} hand {int(res["hand"][m].sum())} ear {int((res["ear"][m] > 0).sum())}')
for p in (0, 4):
    m = res['part'] == p; u, c = np.unique(res['joint'][m], return_counts=True)
    print('part', p, 'by joint', {jn[a]: int(b) for a, b in zip(u, c)})
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
