#!/usr/bin/env python3
"""Bembridge Scholar (SCHOLAR.abc Bip01; from Igrid / the Wyrde, from PF1's fit_rig_pf.py, no scarf: Ponytail stays MM9's). Rig on the assembled mesh (Blender frame, MM9's origin). MM9's joints stay where they are (spine, neck, head, clavicles, skirt chains, legs,
xpony), except: arms (on the sleeve axis that assemble_pf.py turned onto MM9's arm direction, MM9's lengths), fingers (the MPFB hand), the
Ponytail chain (the scarf's hanging back, moved onto our scarf). Writes work/rig.json {joints: changed joints, fingers, mm9: all MM9 joints}.
Raw ABC space: 'L' is at -x. Args: <asm npz> <mm9 glb> <out json>"""
import sys, json, os
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
print('MM9 arm', round(ua, 3), round(fa, 3), 'ours to wrist', round(float(np.linalg.norm(wr - sh)), 3))
EL = np.array([float(x) for x in os.environ.get('ELBOW_OFF', '0,0,0').split(',')])
shp = sh + np.array([0, 0, float(os.environ.get('SHUP', '0.0'))])
elbow = sh + ax * ua + EL; wrist = sh + ax * (ua + fa)
# raw ABC: the R joints sit at +x
J['Bip01 R UpperArm'] = shp.tolist(); J['Bip01 R Forearm'] = elbow.tolist(); J['Bip01 R Hand'] = wrist.tolist()
for b in ('UpperArm', 'Forearm', 'Hand'):
    q = J[f'Bip01 R {b}']; J[f'Bip01 L {b}'] = [-q[0], q[1], q[2]]
# Ponytail chain: MM9's own joints (the Wyrde mantle hangs on the skirt's back chains, as MM9 weights it)
# head pivot at the skull base (ear height), not MM9's jaw-level Head joint: a bow then turns the face over the collar instead of driving the
# chin into the bodice (Fidget, Hit). Rotations are MM9's; only the pivot moves.
HP = os.environ.get('HEAD_POS', '0,-0.02,0.62')
if HP != 'mm9': J['Bip01 Head'] = [float(x) for x in HP.split(',')]
print('HEAD pivot', J.get('Bip01 Head'), 'MM9', MJ['Bip01 Head'].round(3))
F = {}
for nm, k in zip(('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'), range(1, 6)):
    F[nm] = [hj[f'finger{k}-1'], hj[f'finger{k}-2'], hj[f'finger{k}-3'], hj[f'finger{k}-3_tip']]
palm = np.cross(np.array(hj['finger1-1']) - wrist, np.array(hj['finger3-1']) - wrist); palm /= np.linalg.norm(palm)
json.dump(dict(joints=J, fingers=F, palm=palm.tolist(), mm9={k: v.tolist() for k, v in MJ.items()}, axis=ax.tolist()), open(out, 'w'), indent=0)
print('RIG', {k: np.round(v, 3).tolist() for k, v in J.items() if ' R ' in k})
