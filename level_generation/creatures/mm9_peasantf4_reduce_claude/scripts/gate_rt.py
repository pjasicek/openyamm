#!/usr/bin/env python3
"""PeasantF4's gate_pf4.py (hood vs body, arm vs sleeve tube, F1's hidden old hood vs the new hood) on a runtime GLB (the installed
file or a reduced candidate, LOD0), so before/after are measured the same way. Vertex labels (asm part, lining twin, sleeve
coordinate) come from work/glb_labels.npz through the installed vertices (a candidate's vertices are installed ones: matched by
position + UV). Hood: outer hood vertices of the cape and front edges (rest height below HOODY, the asm's 1.53 m line) behind the
nearest dress/head vertex's surface within 3 cm, minus the rest reading; sleeve: arm vertices under the tube (f <= 0.80) in front of
the nearest tube vertex's surface; old hood: above the new hood. Every clip at its keys and 30 fps.
Usage: gate_rt.py <glb> <out json>"""
import sys, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
import bglbio as g  # noqa: E402
GLB, OUT = sys.argv[1:3]
L = np.load(HERE / 'work' / 'glb_labels.npz'); names = [str(x) for x in L['names']]; K = names.index
d0, b0 = g.read(HERE / 'before' / 'mm9_peasantf4.glb'); P0 = g.prims(d0, b0, 0)
d1, b1 = g.read(GLB); n1 = next(n for n in d1['nodes'] if n.get('name') == 'PeasantF4' and 'mesh' in n); P1 = g.prims(d1, b1, n1['mesh'])
M = Model(Glb(GLB))
voff = np.cumsum([0] + [len(p['POSITION']) for p in P0])
rows = []; T0 = []; off = 0
for k, (a, c) in enumerate(zip(P0, P1)):
    dd, j = cKDTree(np.c_[a['POSITION'], a['TEXCOORD_0'] * 0.01]).query(np.c_[c['POSITION'], c['TEXCOORD_0'] * 0.01])
    assert dd.max() < 1e-6, dd.max()
    rows.append(j + voff[k]); T0.append(M.primitives[k]['triangles'] + off); off += len(c['POSITION'])
rows = np.concatenate(rows); T0 = np.vstack(T0)
cp = L['vcomp'][rows]; PR = L['vparam'][rows]; TW = L['vtwin'][rows]
def allpos(posed): return np.vstack([p_ for p_, _ in posed])
rest = allpos(M.skinned_positions(M.world({})))
HOODY = 1.53                                  # gate_pf4.py's line (skinned rest stands on y = 0 in half.glb and the runtime)
hood_out = np.where((cp == K('hood4')) & (TW < 0) & (rest[:, 1] < HOODY))[0]
body = np.where(np.isin(cp, [K('dress'), K('head')]))[0]
arm = np.where(cp == K('hands'))[0]
sl_out = np.where((cp == K('sleeve4')) & (TW < 0) & (PR[:, 0] > -1))[0]
d_, j_ = cKDTree(rest[sl_out]).query(rest[arm]); f_arm = PR[sl_out][j_, 0]
arm_in = arm[(d_ < 0.03) & (f_arm <= 0.80)]
hood_all = np.where((cp == K('hood4')) & (TW < 0))[0]
old = np.where(cp == K('scarf'))[0]
print('PARTS hood', len(hood_out), 'arm under tube', len(arm_in), 'old hood', len(old), 'rest y', rest[:, 1].min().round(3), rest[:, 1].max().round(3))
def normals(pts):
    fn = np.cross(pts[T0[:, 1]] - pts[T0[:, 0]], pts[T0[:, 2]] - pts[T0[:, 0]]); vn = np.zeros_like(pts)
    for c in range(3): np.add.at(vn, T0[:, c], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
def measure(pts):
    vn = normals(pts)
    kb = cKDTree(pts[body]); d, j = kb.query(pts[hood_out]); q = pts[hood_out] - pts[body][j]
    hd = -np.einsum('ij,ij->i', q, vn[body][j]); hd[(d >= 0.03) | (hd < 0)] = 0
    ks = cKDTree(pts[sl_out]); d2, j2 = ks.query(pts[arm_in]); q2 = pts[arm_in] - pts[sl_out][j2]
    sd = np.einsum('ij,ij->i', q2, vn[sl_out][j2]); sd[(d2 >= 0.03) | (sd < 0)] = 0
    ko = cKDTree(pts[hood_all]); d3, j3 = ko.query(pts[old]); q3 = pts[old] - pts[hood_all][j3]
    od = np.einsum('ij,ij->i', q3, vn[hood_all][j3]); od[(d3 >= 0.03)] = -1
    return hd, sd, od
RH, RS, RO = measure(rest)
print('REST max cm hood', round(float(RH.max()) * 100, 2), 'sleeve', round(float(RS.max()) * 100, 2), 'old hood above the new hood (mm)', round(float(RO.max()) * 1000, 2))
res = {}
for clip in M.clips:
    times = M.clip_times(clip); ts = np.unique(np.r_[times, np.arange(0, times[-1] + 1e-6, 1 / 30)])
    w = {'hood': [0.0, None, 0], 'sleeve': [0.0, None, 0], 'oldhood_out': [0.0, None, 0]}
    for t in ts:
        pts = allpos(M.skinned_positions(M.world(M.sample(clip, t))))
        hd, sd, od = measure(pts)
        for k, v in (('hood', float((hd - RH).max())), ('sleeve', float((sd - RS).max())), ('oldhood_out', float(od.max()))):
            if v > w[k][0]: w[k][0], w[k][1] = v, round(float(t), 3)
            if v > (0.0 if k == 'oldhood_out' else 0.01): w[k][2] += 1
    res[clip] = {k: {'max_cm': round(v[0] * 100, 2), 'at_s': v[1], 'frames_over_1cm': v[2], 'frames': int(len(ts))} for k, v in w.items()}
    print(f'{clip:10s}', '  '.join(f"{k}: {v['max_cm']:4.1f} cm @{v['at_s']} ({v['frames_over_1cm']}/{v['frames']} > 1 cm)" for k, v in res[clip].items()))
json.dump(res, open(OUT, 'w'), indent=1)
