#!/usr/bin/env python3
"""Open tube ends inside the body, every pose: the open rims of the upper-arm tubes (both ends), the trousers (waist and cuffs) and the
gauntlets' wrist rims must stay covered (by the torso shell / pauldrons, the bracers, the boots). Per rim vertex, per frame at 30 fps, a ray
outward from the limb's axis (the bone the rim rides) must meet a covering part within 6 cm; a rim vertex that meets nothing shows.
Runs on work/rig_out.glb (raw, its vertex order = the uv npz's per material). Prints per clip: worst visible rim vertices per rim.
Args: <rig_out glb> <uv npz> <out json> [clips]"""
import json, sys
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
G_, U_, O_ = sys.argv[1:4]; want = sys.argv[4].split(',') if len(sys.argv) > 4 else None
m = Model(Glb(G_)); doc = m.glb.json; nn = [n['name'] for n in doc['nodes']]
D = np.load(U_); tri, mat, comp, co = D['tri'], D['mat'], D['comp'], D['co']; names = [str(x) for x in D['names']]
keep = mat != 9; tri, mat = tri[keep], mat[keep]
order = []; 
for k in range(int(mat.max()) + 1):
    order.append(np.unique(tri[mat == k]))
gidx = np.concatenate(order)                     # glb vertex i (concatenated primitives) -> uv-npz vertex
gcomp = comp[gidx]; inv = -np.ones(len(co), int); inv[gidx] = np.arange(len(gidx))
T = inv[tri]
def part(n): return names.index(n)
def rims(pn):
    t = tri[comp[tri[:, 0]] == part(pn)]
    pos = co[t.ravel()].round(5); _, key = np.unique(pos, axis=0, return_inverse=True); key = key.reshape(-1, 3)
    e = np.sort(np.vstack([key[:, [0, 1]], key[:, [1, 2]], key[:, [2, 0]]]), 1); u, c = np.unique(e, axis=0, return_counts=True)
    bk = np.unique(u[c == 1]); flat = t.ravel(); kv = key.ravel()
    return np.unique(inv[flat[np.isin(kv, bk)]])
covers = {'uarms': ('torso', 'bracers', 'wings', 'collar'), 'pants': ('torso', 'boots', 'buckle', 'tabard'), 'hands': ('bracers',)}
bones = {'uarms': 'UpperArm', 'pants': 'Thigh', 'hands': 'Forearm'}
R = {k: rims(k) for k in covers}
print('rim vertices', {k: len(v) for k, v in R.items()})
def skin(w): return np.vstack([r[0] for r in m.skinned_positions(w)])
def hit(O, Dv, P, Tr, maxd=0.06):
    A, B, C = P[Tr[:, 0]], P[Tr[:, 1]], P[Tr[:, 2]]; e1, e2 = B - A, C - A; out = np.zeros(len(O), bool)
    for s in range(0, len(O), 128):
        o, d = O[s:s + 128, None], Dv[s:s + 128, None]
        h = np.cross(d, e2[None]); det = (e1[None] * h).sum(-1); iv = 1 / np.where(np.abs(det) < 1e-12, 1e-12, det)
        sv = o - A[None]; u = (sv * h).sum(-1) * iv; q = np.cross(sv, e1[None]); v = (d * q).sum(-1) * iv; t = (e2[None] * q).sum(-1) * iv
        out[s:s + 128] = ((u >= 0) & (v >= 0) & (u + v <= 1) & (t > 1e-4) & (t < maxd) & (np.abs(det) > 1e-12)).any(1)
    return out
CT = {k: T[np.isin(comp[tri[:, 0]], [part(c) for c in cs])] for k, cs in covers.items()}
def visible(w):
    P = skin(w); r = {}
    for k, rv in R.items():
        side = np.sign(P[rv][:, 0] * 0 + co[gidx[rv], 0])
        res = []
        for s, sgn in (('L', -1), ('R', 1)):
            sel = rv[side == sgn]
            a = w[nn.index(f'Bip01 {s} {bones[k]}')][:3, 3]; b = w[[c for c in range(len(nn)) if m.parent[c] == nn.index(f'Bip01 {s} {bones[k]}') and 'Bip01' in nn[c] and 'Xhalf' not in nn[c]][0]][:3, 3]
            ax = (b - a) / np.linalg.norm(b - a); d = P[sel] - a; d -= np.outer(d @ ax, ax); d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
            res.append(sel[~hit(P[sel], d, P, CT[k])])
        r[k] = np.concatenate(res)
    return r
B = visible(m.world({})); print('bind visible', {k: len(v) for k, v in B.items()})
rep = {}
for clip in [a['name'] for a in doc['animations'] if not want or a['name'] in want]:
    Te = m.clip_times(clip)[-1]; worst = {k: 0 for k in R}
    for t in np.arange(0, Te + 1e-6, 1 / 30):
        v = visible(m.world(m.sample(clip, float(t))))
        for k in R: worst[k] = max(worst[k], len(np.setdiff1d(v[k], B[k])))
    rep[clip] = worst; print(f'{clip:15}', worst, flush=True)
json.dump(dict(bind=dict((k, int(len(v))) for k, v in B.items()), clips=rep), open(O_, 'w'), indent=1)
