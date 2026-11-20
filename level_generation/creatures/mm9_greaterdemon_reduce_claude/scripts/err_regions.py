#!/usr/bin/env python3
"""Where the ladder error sits: for a mpqem step (work/mp_<tag>.npz, index arrays into the installed LOD0 vertices), the
distance of every removed source vertex to the candidate surface over every clip (HZ samples), split by region: body skin
(group 0), wing bones (group 2), membrane, and per clip. Point-to-triangle distance against the 24 nearest candidate faces
(by centroid) of all primitives. Usage: err_regions.py <mp npz> [sets tag] [hz]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor')); sys.path.insert(0, str(HERE / 'scripts'))
from glb_pose import Glb, Model  # noqa: E402
import bglbio as gb  # noqa: E402


def pt_tri(p, a, b, c):
    """distance from points p (n,3) to triangles (n,k,3 each) -> (n,k), Ericson's closest point"""
    p = p[:, None]
    ab, ac, ap = b - a, c - a, p - a
    d1 = (ab * ap).sum(-1); d2 = (ac * ap).sum(-1)
    bp = p - b; d3 = (ab * bp).sum(-1); d4 = (ac * bp).sum(-1)
    cp = p - c; d5 = (ab * cp).sum(-1); d6 = (ac * cp).sum(-1)
    va = d3 * d6 - d5 * d4; vb = d5 * d2 - d1 * d6; vc = d1 * d4 - d3 * d2
    den = np.where(np.abs(va + vb + vc) < 1e-30, 1e-30, va + vb + vc)
    v = vb / den; w = vc / den
    q = a + ab * v[..., None] + ac * w[..., None]
    # edges/vertices fall back by clamping: evaluate the three edges and take the min with the interior where outside
    def seg(x, y):
        t = np.clip(((p - x) * (y - x)).sum(-1) / np.maximum(((y - x) ** 2).sum(-1), 1e-30), 0, 1)
        return np.linalg.norm(p - (x + (y - x) * t[..., None]), axis=-1)
    inside = (va >= 0) & (vb >= 0) & (vc >= 0)
    dint = np.linalg.norm(p - q, axis=-1)
    de = np.minimum(np.minimum(seg(a, b), seg(b, c)), seg(c, a))
    return np.where(inside, np.minimum(dint, de), de)


mp = np.load(sys.argv[1]); tag = sys.argv[2] if len(sys.argv) > 2 else 'a'; HZ = float(sys.argv[3]) if len(sys.argv) > 3 else 5
sets = np.load(HERE / 'work' / f'glb_sets_{tag}.npz')
src = HERE / 'before' / 'mm9_greaterdemon.glb'
doc, b = gb.read(src)
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
prims = gb.prims(doc, b, node['mesh']); names = [p['material'] for p in prims]
nf = [len(p['T']) for p in prims]; off = np.cumsum([0] + nf)
voff = np.cumsum([0] + [len(p['POSITION']) for p in prims])
# region per source GLB vertex: from the faces using it (prim, group)
reg = {}
labels = []
for k, p in enumerate(prims):
    g = sets['group'][off[k]:off[k + 1]]; T = p['T']
    lab = np.full(len(p['POSITION']), -1)
    name = {0: 'skin', 2: 'wingbone', 3: 'membrane'}
    for f in range(len(T)):
        lab[T[f]] = max(lab[T[f]].max(), g[f]) if k != 1 else 3
    labels.append(lab)
lab = np.concatenate(labels)
srcV = np.concatenate([np.unique(p['T']) + voff[k] for k, p in enumerate(prims)])
candT = np.concatenate([mp[n].astype(np.int64) + voff[k] for k, n in enumerate(names)])
used = np.zeros(voff[-1], bool); used[candT.ravel()] = True
removed = srcV[~used[srcV]]
print('removed vertices', len(removed), {n: int((lab[removed] == g).sum()) for n, g in (('skin', 0), ('wingbone', 2), ('membrane', 3))})
m = Model(Glb(str(src)))
res = {}
for clip in m.clips:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        X = np.concatenate([pz for pz, _ in m.skinned_positions(m.world(m.sample(clip, t)))])
        C = X[candT].mean(1); tree = cKDTree(C)
        _, nn = tree.query(X[removed], 24)
        tri = X[candT[nn]]
        d = pt_tri(X[removed], tri[..., 0, :], tri[..., 1, :], tri[..., 2, :]).min(1)
        res.setdefault(clip, []).append(d)
allD = np.stack([np.stack(v) for v in res.values()][0])
for g, n in ((0, 'skin'), (2, 'wingbone'), (3, 'membrane')):
    sel = lab[removed] == g
    vals = np.concatenate([np.stack(v)[:, sel].ravel() for v in res.values()])
    print(f'{n:9s} removed {int(sel.sum()):5d}  p50 {np.percentile(vals, 50) * 1000:6.2f}  p90 {np.percentile(vals, 90) * 1000:6.2f}  p99 {np.percentile(vals, 99) * 1000:6.2f}  max {vals.max() * 1000:6.1f} mm')
for clip, v in res.items():
    v = np.stack(v); worst = np.unravel_index(v.argmax(), v.shape)
    r = removed[worst[1]]
    print(f'  {clip:12s} p99 {np.percentile(v, 99) * 1000:6.2f}  max {v.max() * 1000:6.1f} mm at vertex {r} ({["skin", "?", "wingbone", "membrane"][lab[r]] if lab[r] >= 0 else "?"})')
# worst vertices overall
mx = np.max(np.concatenate([np.stack(v) for v in res.values()]), 0)
o = np.argsort(-mx)[:15]
P = np.concatenate([p['POSITION'] for p in prims])
for i in o:
    print('  worst', removed[i], lab[removed[i]], round(float(mx[i]) * 1000, 1), 'mm rest', P[removed[i]].round(3))
np.savez(HERE / 'work' / f'err_{Path(sys.argv[1]).stem}.npz', removed=removed, maxd=mx, lab=lab[removed])
