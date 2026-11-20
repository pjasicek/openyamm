#!/usr/bin/env python3
"""Skraelos rig on the assembled mesh (Blender frame, MM9's origin; after Igrid's fit_rig_wo.py). MM9's joints stay where they are (spine,
neck, clavicles, skirt chains, the thigh-less legs, Ponytail / xpony), except: arms (on the sleeve axis that assemble_sk.py turned onto MM9's arm
direction, MM9's lengths), the hand (at the bone palm's wrist end), the head pivot (the skull base) and the fingers (from the bone pieces:
per digit the chain of pieces base -> tip; the first piece of a finger is a metacarpal on the Hand; the rest split by length into the three
phalanges; a joint sits in the gap between two pieces). Writes work/rig.json {joints, fingers, groups (piece -> bone), palm, mm9}.
Raw ABC space: 'R' is at +x. Args: <asm npz> <mm9 glb> <out json>"""
import sys, json, os
import numpy as np
from pathlib import Path
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
npz, mm9, out = sys.argv[1:4]
D = np.load(npz); co, comp = D['co'], D['comp']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
hp = D['hand_piece']; chains = json.loads(str(D['chains'])); sh, wr, ax = D['sh'], D['wr'], D['ax']
m = Model(Glb(mm9)); nn = [n.get('name') for n in m.glb.json['nodes']]; w0 = m.world({})
MJ = {n: np.array([w0[i][0, 3], -w0[i][2, 3], w0[i][1, 3]]) for i, n in enumerate(nn) if n}
ua = np.linalg.norm(MJ['FHP R Forearm'] - MJ['FHP R UpperArm']); fa = np.linalg.norm(MJ['FHP R Hand'] - MJ['FHP R Forearm'])
J = {}
pc = {k: co[hp == k] for k in np.unique(hp[hp > -100000]) if k >= 0}
cen = {k: v.mean(0) for k, v in pc.items()}


def gap(a, b):
    """Midpoint of the closest vertex pair of two pieces."""
    d, i = cKDTree(pc[a]).query(pc[b]); j = int(np.argmin(d)); return 0.5 * (pc[a][i[j]] + pc[b][j])


# the wrist: the palm's end nearest the shoulder, on the arm axis
WBACK = float(os.environ.get('WRIST_BACK', '0.05'))
bases = [k for f, ch in chains.items() for k in ch[:1]]
tb = min(float(((pc[k] - sh) @ ax).min()) for k in bases if k in pc); wrist = sh + ax * (tb - WBACK)
J['FHP R UpperArm'] = sh.tolist(); J['FHP R Forearm'] = (sh + ax * ua * float(np.linalg.norm(wrist - sh)) / (ua + fa)).tolist(); J['FHP R Hand'] = wrist.tolist()
for b in ('UpperArm', 'Forearm', 'Hand'):
    q = J[f'FHP R {b}']; J[f'FHP L {b}'] = [-q[0], q[1], q[2]]
print('ARM', np.round(J['FHP R UpperArm'], 3), np.round(J['FHP R Forearm'], 3), np.round(J['FHP R Hand'], 3), 'MM9 hand', MJ['FHP R Hand'].round(3))
HP = os.environ.get('HEAD_POS', '0,-0.07,0.60')
J['FHP Head'] = [float(x) for x in HP.split(',')]
F = {}; groups = {}
SPLIT = (0.45, 0.30, 0.25)
for f, ch in chains.items():
    ch = [k for k in ch if k in pc]
    if f == 'Thumb': meta = []; rest = ch
    else: meta = ch[:1]; rest = ch[1:]
    for k in meta: groups[k] = 'Hand'
    L = [0.0]
    for a, b in zip(rest[:-1], rest[1:]): L.append(L[-1] + float(np.linalg.norm(cen[b] - cen[a])))
    L = np.array(L) / max(L[-1], 1e-9); cut = np.cumsum(SPLIT)[:2]
    grp = np.searchsorted(cut, L, side='right')
    for k, g_ in zip(rest, grp): groups[k] = f'{f}{int(g_) + 1}'
    joints = []
    first = rest[0]; prev = meta[-1] if meta else 7
    joints.append(gap(prev, first))
    for gi in (1, 2):
        idx = np.where(grp == gi)[0]
        if len(idx) == 0:
            joints.append(cen[rest[-1]]); continue
        i0 = idx[0]; joints.append(gap(rest[i0 - 1], rest[i0]) if i0 > 0 else cen[rest[i0]])
    tipp = pc[rest[-1]]; tip = tipp[np.argmax((tipp - cen[rest[-1]]) @ (cen[rest[-1]] - cen[rest[-2]]))]
    F[f] = [np.asarray(p).tolist() for p in joints] + [tip.tolist()]
    print('FINGER', f, [round(float(np.linalg.norm(np.array(F[f][i + 1]) - np.array(F[f][i]))), 3) for i in range(3)], 'groups', {k: groups[k] for k in rest})
for k in D['carpal']:
    groups[int(k)] = 'Hand'
palmv = np.cross(np.array(F['Index'][0]) - wrist, np.array(F['Ring'][0]) - wrist); palmv /= np.linalg.norm(palmv)
json.dump(dict(joints=J, fingers=F, groups={str(k): v for k, v in groups.items()}, palm=palmv.tolist(), mm9={k: v.tolist() for k, v in MJ.items()}, axis=ax.tolist()),
          open(out, 'w'), indent=0)
print('RIG head', J['FHP Head'])
