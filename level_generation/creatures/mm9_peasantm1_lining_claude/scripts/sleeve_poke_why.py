#!/usr/bin/env python3
"""Why sleeve_poke_gate.py (PeasantM2d) reads a larger poke on the lined GLB: the gate copied with the hit test split into the
installed sleeve faces and the new lining faces, for one clip/frame/side; prints the candidates whose poke rises, with the
installed hit (NaN = the ray misses the installed sleeve: the hand past the cuff) and the lining hit.
Usage: sleeve_poke_why.py <glb> <n installed body tris> <clip> <frame48> <L|R>"""
import sys
from pathlib import Path
import numpy as np
C = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(C / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
glb, nt0, clip, f48, tok = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), sys.argv[5]
g = Glb(Path(glb)); m = Model(g); doc = g.json; names = [n.get('name') for n in doc['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; node0 = P[0]['node']; mesh = doc['meshes'][doc['nodes'][node0]['mesh']]
USE = [k for k, pr in enumerate(P) if pr['node'] == node0 and pr['skinned']]
mats = [doc['materials'][mesh['primitives'][i]['material']]['name'] for i in range(len(USE))]
off, tri_all, dom, cloth, new = 0, [], [], [], []
for k, mn in zip(USE, mats):
    pr = P[k]; tri_all.append(pr['triangles'] + off); off += len(pr['positions'])
    dom += [jn[pr['joints'][v][np.argmax(pr['weights'][v])]] for v in range(len(pr['positions']))]
    cloth.append(np.full(len(pr['triangles']), mn == 'PeasantM1_A')); new.append(np.arange(len(pr['triangles'])) >= (nt0 if mn == 'PeasantM1_A' else 1 << 30))
tris = np.concatenate(tri_all); dom = np.array(dom); cloth = np.concatenate(cloth); new = np.concatenate(new)
ishead = np.concatenate([np.full(len(P[k]['positions']), mn == 'PeasantM1Head') for k, mn in zip(USE, mats)])
idx = {n: i for i, n in enumerate(names)}
arm = [j for j in jn if f' {tok} ' in j and any(k in j for k in ('UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky'))]
onarm = np.isin(dom, arm); sleeve_f = np.where(cloth & (onarm[tris].sum(1) >= 2))[0]
rw = m.world({}); rest = np.concatenate([m.skinned_positions(rw)[k][0] for k in USE])
fa, hd = idx[f'Bip01 {tok} Forearm'], idx[f'Bip01 {tok} Hand']
a0, a1 = rw[fa][:3, 3], rw[hd][:3, 3]; axis = (a1 - a0) / np.linalg.norm(a1 - a0); t = (rest - a0) @ axis
cand = np.where(ishead & onarm & (t < np.linalg.norm(a1 - a0) + 0.03) & (t > 0.05) & (np.linalg.norm(np.cross(rest - a0, axis), axis=1) < 0.12))[0]
W = m.world(m.sample(clip, f48 / 48)); X = np.concatenate([m.skinned_positions(W)[k][0] for k in USE])
a0, a1 = W[fa][:3, 3], W[hd][:3, 3]; ax = (a1 - a0) / np.linalg.norm(a1 - a0)
v = X[cand]; p0 = a0 + ((v - a0) @ ax)[:, None] * ax; r = v - p0; rv = np.linalg.norm(r, axis=1); rd = r / rv[:, None]


def hits(fs, i):
    T = X[tris[fs]]; A, B, Cc = T[:, 0], T[:, 1], T[:, 2]; e1, e2 = B - A, Cc - A
    pv = np.cross(rd[i], e2); det = np.einsum('ij,ij->i', e1, pv); ok = np.abs(det) > 1e-12; inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    tv = p0[i] - A; uu = np.einsum('ij,ij->i', tv, pv) * inv; qv = np.cross(tv, e1); vv = (qv @ rd[i]) * inv
    dist = np.einsum('ij,ij->i', e2, qv) * inv; h = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1) & (dist > 0) & (dist < 0.10)
    return (dist[h].max(), fs[h][dist[h].argmax()]) if h.any() else (np.nan, -1)


old = sleeve_f[~new[sleeve_f]]; lin = sleeve_f[new[sleeve_f]]
print(clip, f48, tok, 'sleeve faces', len(old), '+ lining', len(lin))
for i in range(len(v)):
    ho, _ = hits(old, i); hl, fl = hits(lin, i)
    po = rv[i] - ho if np.isfinite(ho) else np.nan; pl = rv[i] - max(ho if np.isfinite(ho) else -1, hl) if np.isfinite(hl) else po
    if np.isfinite(pl) and pl > 0.0005 and not (np.isfinite(po) and abs(pl - po) < 1e-6):
        print(f'  cand {cand[i]} r {rv[i] * 1000:.1f} mm: installed hit {ho * 1000:.1f} (poke {po * 1000:.1f}), lining hit {hl * 1000:.1f} face {fl} -> poke {pl * 1000:.1f} mm')
