#!/usr/bin/env python3
"""Wing knuckles (Winged Mutant lesson: a cut through the joint rings flattened the wrist knuckle; here set b's wing bones at
0.5 moved the Xwing knuckle by 64 mm in Spawn): wing-bone faces with a vertex within R m of a wing joint (bind position of
every Xwing*/Xwarm* joint, from the inverse bind matrices) are kept exactly. Writes work/keep_extra_knuckle.npy.
Usage: knuckle_keep.py [R]"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import bglbio as gb  # noqa: E402
R = float(sys.argv[1]) if len(sys.argv) > 1 else 0.07
doc, b = gb.read(HERE / 'before' / 'mm9_greaterdemon.glb')
node = next(n for n in doc['nodes'] if n.get('name') == 'GreaterDemon' and 'mesh' in n)
skin = doc['skins'][node['skin']]
names = [doc['nodes'][j]['name'] for j in skin['joints']]
ibm = gb.acc(doc, b, skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
jp = np.array([np.linalg.inv(m)[:3, 3] for m in ibm])
wj = [i for i, n in enumerate(names) if n.startswith(('Xwing', 'Xwarm'))]
print('wing joints', [names[i] for i in wj])
pr = gb.prims(doc, b, node['mesh'])
sets = np.load(HERE / 'work' / 'glb_sets_a.npz')
nB, nW, nH = (len(p['T']) for p in pr)
P = pr[0]['POSITION'].astype(float); T = pr[0]['T']
d = cKDTree(jp[wj]).query(P)[0]
keep = sets['wingbone'][:nB] & (d[T] < R).any(1)
print(f'knuckle faces kept {int(keep.sum())} of {int(sets["wingbone"][:nB].sum())} wing-bone faces')
np.save(HERE / 'work' / 'keep_extra_knuckle.npy', np.r_[keep, np.zeros(nW + nH, bool)])
