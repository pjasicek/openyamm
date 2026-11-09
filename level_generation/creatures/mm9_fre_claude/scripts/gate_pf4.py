#!/usr/bin/env python3
"""PF4 geometry gate (2026-11-02) on the rigged clips GLB before texturing (work/half.glb, one primitive built from the asm):
- hood: hood4 outer vertices below 1.53 m at rest (the cape and the front edges) inside the body (dress, head shell, neck), as
  headwear_gate_pf3.py (F3): inside = behind the nearest body vertex's surface within 3 cm, minus the bind pose's own reading;
- sleeve: arm (MPFB) vertices under the sleeve tube (f between the tube's start and 0.80 of the forearm) outside the tube: in front of the
  nearest tube vertex's surface within 3 cm, minus the bind pose's reading (the sleeve poke).
Every clip at its keys and 30 fps. Args: <glb (built from the uv npz)> <asm npz> <out json> [uv npz: work/uv_tex2.npz]"""
import sys, json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
M = Model(Glb(sys.argv[1])); A = np.load(sys.argv[2]); OUT = sys.argv[3]
names = [str(x) for x in A['names']]; comp = A['comp']; tri = A['tri']; par = A['f4_param']; twin = A['f4_twin_v']
U = np.load(sys.argv[4] if len(sys.argv) > 4 else 'work/uv_tex2.npz'); ut, um, uo = U['tri'], U['mat'], U['orig']
rows = []; T0 = []; off = 0
for m in range(len(M.primitives)):
    used = np.unique(ut[um == m]); assert len(used) == len(M.primitives[m]['positions'])
    rows.append(uo[used]); T0.append(M.primitives[m]['triangles'] + off); off += len(used)
rows = np.concatenate(rows); T0 = np.vstack(T0)
cp = comp[rows]; P = par[rows]; TW = twin[rows]
def allpos(posed): return np.vstack([p_ for p_, _ in posed])
rest = allpos(M.skinned_positions(M.world({})))
K = lambda n: names.index(n)
hood_out = np.where((cp == K('hood4')) & (TW < 0) & (rest[:, 1] < 1.53))[0]
body = np.where(np.isin(cp, [K('dress'), K('head')]))[0]
arm = np.where(cp == K('hands'))[0]
sl_out = np.where((cp == K('sleeve4')) & (TW < 0) & (P[:, 0] > -1))[0]
# arm coordinate per arm vertex: nearest sleeve outer vertex's f, only where the tube covers (f <= 0.80)
d_, j_ = cKDTree(rest[sl_out]).query(rest[arm]); f_arm = P[sl_out][j_, 0]
arm_in = arm[(d_ < 0.03) & (f_arm <= 0.80)]
hood_all = np.where((cp == K('hood4')) & (TW < 0))[0]
old = np.where(cp == K('scarf'))[0]
print('PARTS hood', len(hood_out), 'arm under tube', len(arm_in), 'old hood', len(old))
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
