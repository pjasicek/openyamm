#!/usr/bin/env python3
"""Staff clearance gate (2026-11-01): per clip at 15 fps, the staff (Bone01 vertices of LichKingStaff and the staff skull) against the body and
head skin (without the right hand and forearm, which hold it) and the floor (GLB y = 0). Behind = within 1.5 cm of a skin vertex and on the
inner side of its posed normal (the depth is not measured: on the open coat a vertex normal's side is only a hint; compare runs by counts).
Reports frames with any staff vertex behind the skin, the most such vertices in a frame and the skin part they meet, the least clearance
of the others, and the staff's lowest point. Args: <glb> [json]"""
import sys, json
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
NEAR = 0.015
m = Model(Glb(sys.argv[1])); doc = m.glb.json; nn = [n['name'] for n in doc['nodes']]; jn = [nn[j] for j in m.joints]
mats = [doc['materials'][p['material']]['name'] for p in doc['meshes'][0]['primitives']]
bone01 = jn.index('Bone01')
staff = [(i, np.where((m.primitives[i]['joints'][:, 0] == bone01) & (m.primitives[i]['weights'][:, 0] > 0.99))[0])
         for i, n in enumerate(mats) if n.startswith('LichKingStaff')]
HOLD = {'Bip01 R Hand', 'Bip01 R Forearm', 'Bip01 R XhalfForearm', 'Bone01'} | {f'Bip01 R {f}{k}' for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for k in (1, 2, 3)}
body = []; DOM = {}
for i, n in enumerate(mats):
    if n.startswith('LichKingStaff'): continue
    p = m.primitives[i]; dom = np.array([jn[j] for j in p['joints'][np.arange(len(p['positions'])), np.argmax(p['weights'], 1)]])
    body.append((i, np.where(~np.isin(dom, list(HOLD)))[0])); DOM[i] = dom
rep = {}
for clip in [a['name'] for a in doc['animations']]:
    T = m.clip_times(clip)[-1]; nmax = 0; frames = 0; nf = 0; clear = 9.0; low = 9.0; worst_t = 0.0; part = ''
    for t in np.arange(0, T + 1e-6, 1 / 15):
        SP = m.skinned_positions(m.world(m.sample(clip, float(t))))
        S = np.vstack([SP[i][0][v] for i, v in staff]); low = min(low, float(S[:, 1].min()))
        Bv, Bn, Bd = [], [], []
        for i, keep in body:
            P, T_ = SP[i]; fn = np.cross(P[T_[:, 1]] - P[T_[:, 0]], P[T_[:, 2]] - P[T_[:, 0]]); N = np.zeros_like(P)
            for c in range(3): np.add.at(N, T_[:, c], fn)
            N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12); Bv.append(P[keep]); Bn.append(N[keep]); Bd.append(DOM[i][keep])
        Bv = np.vstack(Bv); Bn = np.vstack(Bn); Bd = np.concatenate(Bd); d, k = cKDTree(Bv).query(S); nf += 1
        sd = np.einsum('ij,ij->i', S - Bv[k], Bn[k]); ins = (d < NEAR) & (sd < 0)
        frames += int(ins.any())
        if ins.sum() > nmax: nmax = int(ins.sum()); worst_t = float(t); part = ','.join(sorted(set(Bd[k[ins]])))
        out = ~ins
        if out.any(): clear = min(clear, float(d[out].min()))
    rep[clip] = dict(frames_behind=[frames, nf], most_behind=nmax, at_s=round(worst_t, 2), parts=part, clearance_cm=round(clear * 100, 2),
                     lowest_cm=round(low * 100, 2))
    print(f'{clip:15} behind skin {frames:3d}/{nf:3d} frames, most {nmax:3d} vertices (t {worst_t:4.2f}: {part})  least clearance '
          f'{clear*100:5.2f} cm  lowest {low*100:6.2f} cm')
if len(sys.argv) > 2: json.dump(rep, open(sys.argv[2], 'w'), indent=1)
