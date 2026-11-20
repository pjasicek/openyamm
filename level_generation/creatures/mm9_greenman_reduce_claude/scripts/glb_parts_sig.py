#!/usr/bin/env python3
"""Per-face labels of the installed LOD0 (before/mm9_sigmund.glb, node Sigmund; prims Sigmund (body), SigmundHead (head shell,
eyes, hair twin, MPFB hands)) from work/final_parts.npz (dump_master_parts.py), matched by rest centroid: Blender z-up -> glTF
y-up (x, z, -y), then mirror_glb.py's true handedness (x -> -x; picked by the fit), offset fitted on the minimum corner.
Lining pairs: every added face (rim_lining.py band lining 3 mm / inner-layer 0.5 mm, hair_lining.py hair twin 1.5 mm) is matched to
the outer face it was copied from (three corners within TOL of three distinct outer corners, normals opposite); added faces without
such an outer face are the rim strips (kept). Gives a twin GLB vertex per outer GLB vertex of every lined face.
Writes work/glb_parts.npz: mat, head, hand, added, lining (added and paired), rim (added, unpaired), cen, joint, jnames, lined,
twin (per GLB vertex, prims concatenated; prim-local lining vertex, -1 none), ambig, pair, unmatched (= rim), voff, foff."""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
doc, binary, nd, D = glbio.load(HERE / 'before' / 'mm9_greenman.glb', 'Sigmund')
PR = ['Sigmund', 'SigmundHead']
TOL = 0.0055
s = np.load(HERE / 'work' / 'final_parts.npz')
allP = np.concatenate([D[k]['P'] for k in PR])
best = None
for sx in (1, -1):
    bco = s['co'][:, [0, 2, 1]] * [sx, 1, -1]
    offset = allP.min(0) - bco.min(0)
    fc = s['cen'][:, [0, 2, 1]] * [sx, 1, -1] + offset
    gc = np.concatenate([D[k]['P'][D[k]['T']].mean(1) for k in PR])
    dd = cKDTree(fc).query(gc)[0]
    print('mirror', sx, 'offset', offset.round(6), 'max', dd.max())
    if best is None or dd.max() < best[0]:
        best = (dd.max(), fc)
fc = best[1]
skin = doc['skins'][nd['skin']]; jn = [doc['nodes'][j]['name'] for j in skin['joints']]
out = dict(mat=[], head=[], hand=[], added=[], cen=[], joint=[], lined=[], pair=[], unmatched=[], ambig=[], lining=[])
twins = []
for k, name in enumerate(PR):
    P, T, J, W = D[name]['P'], D[name]['T'], D[name]['J'], D[name]['W']; gc = P[T].mean(1)
    dist, nn = cKDTree(fc).query(gc)
    print(name, len(T), 'max dist', dist.max().round(7), 'dup', len(nn) - len(np.unique(nn)))
    lab = {key: s[key][nn] for key in ('head', 'hand', 'added')}
    fn = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); fn /= np.maximum(np.linalg.norm(fn, axis=1, keepdims=True), 1e-20)
    twin = -np.ones(len(P), np.int64); lined = np.zeros(len(T), bool); pair = -np.ones(len(T), np.int64)
    ambig = np.zeros(len(P), bool); unmatched = np.zeros(len(T), bool); lining = np.zeros(len(T), bool)
    outer = np.flatnonzero(~lab['added'].astype(bool))
    otree = cKDTree(gc[outer])
    lf = np.flatnonzero(lab['added'].astype(bool)); res = []; conf = 0
    if len(lf):
        _, cand = otree.query(gc[lf], 16)
        # closest-first so a face nearest its own source claims it
        order = []
        for f, cs in zip(lf, cand):
            bb = None
            for c in outer[cs]:
                if fn[f] @ fn[c] > -0.5: continue
                d = np.linalg.norm(P[T[f]][:, None] - P[T[c]][None], axis=-1)
                perm = d.argmin(1)
                if len(set(perm.tolist())) != 3: continue
                e = d[np.arange(3), perm].max()
                if e < TOL and (bb is None or e < bb[0]): bb = (e, c, perm)
            if bb is None: unmatched[f] = True
            else: order.append((bb[0], f, bb[1], bb[2]))
        for e, f, c, perm in sorted(order, key=lambda x: x[0]):
            if lined[c]: unmatched[f] = True; conf += 1; continue
            lined[c] = True; pair[c] = f; lining[f] = True; res.append(e)
            for i in range(3):
                o = T[c, perm[i]]; l_ = T[f, i]
                if twin[o] >= 0 and twin[o] != l_:
                    if np.linalg.norm(P[twin[o]] - P[l_]) > 1e-6 or np.abs(D[name]['UV'][twin[o]] - D[name]['UV'][l_]).max() > 1e-6:
                        ambig[o] = True
                twin[o] = l_
        print(f'  added {len(lf)}: paired {len(res)} (offset max {max(res) * 1000:.2f} mm, p50 {np.median(res) * 1000:.2f}), '
              f'rim/unpaired {int(unmatched.sum())} (taken-twice {conf}), ambiguous twin vertices {int(ambig.sum())}')
    # bands: rim_lining.py lines each band once with one dark texel, so where two bands meet an outer vertex has two twins (the
    # ambiguous vertices). Band = connected lining piece (by GLB lining vertex); twins per (band, outer vertex)
    band = -np.ones(len(T), np.int64); tb = []
    if lining.any():
        lw = np.arange(len(P))   # by GLB vertex: two bands meeting with coincident twins keep their own texels apart
        lfs = np.flatnonzero(lining); LT = lw[T[lfs]]
        rr = np.r_[LT[:, 0], LT[:, 1], LT[:, 2]]; cc = np.r_[LT[:, 1], LT[:, 2], LT[:, 0]]; nn_ = lw.max() + 1
        _, bl = connected_components(coo_matrix((np.ones(len(rr)), (rr, cc)), shape=(nn_, nn_)), directed=False)
        lband = -np.ones(len(T), np.int64); lband[lfs] = bl[LT[:, 0]]
        for c in np.flatnonzero(lined):
            f = pair[c]; band[c] = lband[f]
            d = np.linalg.norm(P[T[f]][:, None] - P[T[c]][None], axis=-1); perm = d.argmin(1)
            for i in range(3):
                tb.append((band[c], T[c, perm[i]], T[f, i]))
        tb = np.array(tb, np.int64)
        u = np.unique(tb[:, :2], axis=0)
        print(f'  bands {len(np.unique(bl[LT[:, 0]]))}, (band, vertex) twins {len(u)} of {len(tb)} entries, conflicts',
              len(np.unique(tb, axis=0)) - len(u))
    else:
        tb = np.zeros((0, 3), np.int64)
    out.setdefault('band', []).append(band); out.setdefault('twinb', []).append(tb + [0, 0, 0])
    out['mat'] += [k] * len(T); out['cen'].append(gc); out['lined'].append(lined); out['pair'].append(pair)
    out['unmatched'].append(unmatched); out['ambig'].append(ambig); out['lining'].append(lining)
    for key in ('head', 'hand', 'added'): out[key].append(lab[key])
    acc = np.zeros((len(T), len(jn)))
    for c in range(3):
        for i in range(4):
            np.add.at(acc, (np.arange(len(T)), J[T[:, c], i]), W[T[:, c], i])
    out['joint'].append(acc.argmax(1))
    twins.append(twin)
tbs = out.pop('twinb'); res = {k: (np.concatenate(v) if k != 'mat' else np.array(v)) for k, v in out.items()}
for k, t in enumerate(tbs):
    res[f'twinb{k}'] = t
res['jnames'] = np.array(jn); res['twin'] = np.concatenate(twins); res['rim'] = res['unmatched']
res['voff'] = np.cumsum([0] + [len(D[k]['P']) for k in PR]); res['foff'] = np.cumsum([0] + [len(D[k]['T']) for k in PR])
np.savez(HERE / 'work' / 'glb_parts.npz', **res)
