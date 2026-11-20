#!/usr/bin/env python3
"""What the collapse gate counts (diagnosis, run 2): per clip and region at its worst frame, the bad faces split by
material (primitive), lining (zero UV area), collapse vs flip, rest height band, and how many any camera can see.
Args: <glb> <clip:region,...> ...   e.g. Sleep:neck,head Death:neck"""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from glb_pose import Glb, Model
import importlib.util
src = (Path(__file__).resolve().parent / 'collapse_gate.py').read_text()
REGIONS = eval(src[src.index('REGIONS = ') + 10: src.index('\nm = Model')])
m = Model(Glb(sys.argv[1])); doc = m.glb.json
names = [doc['nodes'][j]['name'] for j in doc['skins'][0]['joints']]
PR = m.primitives
mats = []
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        mats.append(doc['materials'][p.get('material', 0)]['name'] if 'material' in p else '?')
OFF = np.cumsum([0] + [len(p['positions']) for p in PR])
T = np.vstack([np.asarray(x[1]).reshape(-1, 3) + o for x, o in zip(m.skinned_positions(m.world({})), OFF)])
primof = np.concatenate([np.full(len(np.asarray(x[1]).reshape(-1, 3)), i) for i, x in enumerate(m.skinned_positions(m.world({})))])
UV = np.vstack([np.asarray(m.glb.accessor(doc['meshes'][0]['primitives'][i]['attributes']['TEXCOORD_0'])) for i in range(len(PR))]) if len(doc['meshes'][0]['primitives']) >= len(PR) else None
J = np.vstack([p['joints'] for p in PR]); W = np.vstack([p['weights'] for p in PR])
fw = np.zeros((len(T), len(names)))
for k in range(J.shape[1]):
    for c in range(3):
        np.add.at(fw, (np.arange(len(T)), J[T[:, c], k]), W[T[:, c], k])
dom = fw.argmax(1)
label = np.array(['body'] * len(T), dtype=object)
for r, bones in REGIONS:
    label[np.isin(dom, [names.index(b) for b in bones if b in names])] = r
SK = lambda world: np.vstack([x[0] for x in m.skinned_positions(world)])
rest = SK(m.world({}))
def tri(P):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); return n, np.linalg.norm(n, axis=1) / 2
n0, a0 = tri(rest); ok = a0 > 1e-9
if UV is not None:
    u = UV[T]; uva = np.abs((u[:, 1, 0] - u[:, 0, 0]) * (u[:, 2, 1] - u[:, 0, 1]) - (u[:, 2, 0] - u[:, 0, 0]) * (u[:, 1, 1] - u[:, 0, 1]))
else:
    uva = np.ones(len(T))
cen = rest[T].mean(1)
for spec in sys.argv[2:]:
    clip, regs = spec.split(':'); regs = regs.split(',')
    Te = m.clip_times(clip)[-1]
    best = {r: (-1, 0.0, None) for r in regs}
    for t in np.arange(0, Te + 1e-6, 1 / 30):
        w = m.world(m.sample(clip, float(t))); P = SK(w); n, a = tri(P)
        pal = w[m.joints] @ m.inverse_binds
        nr = np.einsum('fij,fj->fi', np.einsum('fb,bij->fij', fw / 3, pal[:, :3, :3]), n0)
        d = (n * nr).sum(1) / np.maximum(np.linalg.norm(n, axis=1) * np.linalg.norm(nr, axis=1), 1e-12)
        col = ok & (a < 0.2 * a0); flp = ok & (d < 0)
        for r in regs:
            b = (col | flp) & (label == r)
            if b.sum() > best[r][0]: best[r] = (int(b.sum()), float(t), (col & (label == r), flp & (label == r)))
    for r in regs:
        cnt, t, (col, flp) = best[r]
        idx = np.where(col | flp)[0]
        print(f'{clip} {r}: {cnt} at {t:.2f}s  collapse {int(col.sum())} flip {int(flp.sum())}')
        if not len(idx): continue
        pm = {}
        for i in idx:
            k = (mats[primof[i]] if primof[i] < len(mats) else str(primof[i]), 'lining' if uva[i] < 1e-9 else 'painted')
            pm[k] = pm.get(k, 0) + 1
        print('   by material:', pm)
        z = cen[idx, 1]; x = np.abs(cen[idx, 0]); y = cen[idx, 2]
        print('   rest height m: min %.3f p50 %.3f max %.3f | |x| p50 %.3f | fwd(z) p50 %.3f' % (z.min(), np.median(z), z.max(), np.median(x), np.median(y)))
        print('   area ratio p50 %.2f, dominant bones:' % np.median((a0[idx] > 0) * 1), {names[b]: int((dom[idx] == b).sum()) for b in np.unique(dom[idx])})
