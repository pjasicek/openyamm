#!/usr/bin/env python3
"""Rig on the assembled mesh (Blender frame, MM9's origin). MM9's joints stay where they are, except: arms (on the sleeve axis, MM9's lengths), fingers (the MPFB hand), Ponytail (along the hood's crest), the Y chains (on our cords).
Writes work/rig.json {joints: changed joints, fingers, palm}. Raw ABC space: 'R' is at +x. Args: <asm npz> <mm9 glb> <out json>"""
import sys, json
import numpy as np
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
npz, mm9, out = sys.argv[1:4]
D = np.load(npz); co, comp = D['co'], D['comp']; names = [str(x) for x in D['names']]; pid = {n: i for i, n in enumerate(names)}
sh, wr, ax = D['sh'], D['wr'], D['ax']; hj = {k: np.ravel(v).tolist() for k, v in json.loads(str(D['hj'])).items()}
m = Model(Glb(mm9)); nn = [n.get('name') for n in m.glb.json['nodes']]; w0 = m.world({})
MJ = {n: np.array([w0[i][0, 3], -w0[i][2, 3], w0[i][1, 3]]) for i, n in enumerate(nn)}
J = {}
ua = np.linalg.norm(MJ['Bip01 R Forearm'] - MJ['Bip01 R UpperArm']); fa = np.linalg.norm(MJ['Bip01 R Hand'] - MJ['Bip01 R Forearm'])
print('MM9 arm', ua, fa)
elbow = sh + ax * ua + np.array([0, -0.035, 0.02]); wrist = sh + ax * (ua + fa)       # the hinge toward the outside of the bend
J['Bip01 R UpperArm'] = (sh + np.array([0, 0, float(__import__('os').environ.get('SHUP', '-0.03'))])).tolist(); J['Bip01 R Forearm'] = elbow.tolist(); J['Bip01 R Hand'] = wrist.tolist()
for b in ('UpperArm', 'Forearm', 'Hand'):
    q = J[f'Bip01 R {b}']; J[f'Bip01 L {b}'] = [-q[0], q[1], q[2]]
# cords: +x cord centre line, top to knot end
c = co[np.isin(comp, [pid['cords']]) & (co[:, 0] > 0)]; kn = co[(comp == pid['knots']) & (co[:, 0] > 0)]
zs = np.linspace(c[:, 2].max(), c[:, 2].min(), 12); line = []
for z in zs:
    s = c[np.abs(c[:, 2] - z) < 0.02]
    if len(s): line.append(s.mean(0))
line = np.array(line); end = np.array([kn[:, 0].mean(), kn[:, 1].mean(), kn[:, 2].min()]); line = np.vstack([line, end])
print('cord', line[0].round(3), line[-1].round(3))
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(line, axis=0), axis=1))]
chain = ['Ytassbase01', 'Ytasspiv01', 'YtassA01', 'YtassB01', 'YtassC01', 'YtassD01']
pts = np.array([MJ[b] for b in chain]); ms = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
J['Ytassbase01'] = (line[0] + [0, 0.05, 0.01]).tolist()
for b, s in zip(chain[1:], ms[1:]):
    t = s / ms[-1] * seg[-1]; J[b] = [float(np.interp(t, seg, line[:, i])) for i in range(3)]
for b in chain:
    q = J[b]; J[b.replace('01', '')] = [-q[0], q[1], q[2]]
# hood crest: Ponytail chain on our hood (top, a third back, near the tip)
ro = co[comp == pid['robe']]; hood = ro[np.abs(ro[:, 0]) < 0.02]; hood = hood[hood[:, 2] > 0.70]
hh = ro[ro[:, 2] > 0.62]; tip = hh[hh[:, 1].argmax()]; print('hood tip', tip.round(3), 'MM9 ponytail', MJ['Bip01 Ponytail1'].round(3), MJ['Bip01 Ponytail12'].round(3))
yf, yt = 0.02, tip[1]
for b, u in (('Bip01 Ponytail1', 0.0), ('Bip01 Ponytail11', 0.42), ('Bip01 Ponytail12', 0.75)):
    y = yf + (yt - yf) * u; q = hood[np.abs(hood[:, 1] - y) < 0.035]
    J[b] = [0.0, float(y), float(0.5 * (q[:, 2].max() + q[:, 2].min()) if len(q) else tip[2] - 0.03)]
F = {}
for nm, k in zip(('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'), range(1, 6)):
    F[nm] = [hj[f'finger{k}-1'], hj[f'finger{k}-2'], hj[f'finger{k}-3'], hj[f'finger{k}-3_tip']]
palm = np.cross(np.array(hj['finger1-1']) - wrist, np.array(hj['finger3-1']) - wrist); palm /= np.linalg.norm(palm)
json.dump(dict(joints=J, fingers=F, palm=palm.tolist(), mm9={k: v.tolist() for k, v in MJ.items()}, axis=ax.tolist()), open(out, 'w'), indent=0)
print('RIG', {k: np.round(v, 3).tolist() for k, v in J.items() if 'Y' not in k[:1]})
