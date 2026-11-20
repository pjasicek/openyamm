#!/usr/bin/env python3
"""Faces the hands touch (PeasantDM2 reduction; after the Monk's hand_contact.py): c250 failed the arm and hand gate in Death
(L hand 3.7 cm inside the body for one 48 fps frame; installed 0) where the hand lies on the cut tunic/trousers. Every face of
the installed LOD0 (both primitives) that is not a hand/forearm face and whose posed centroid comes within R m of a posed
hand vertex (dominant Hand/finger joint) in any 1/FPS frame of the listed clips -> work/hand_contact.npy (bool per GLB face,
primitive order as in the file). Usage: hand_contact_dm2.py   (env R default 0.04, FPS 24, CLIPS default every clip)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.04')); FPS = float(os.environ.get('FPS', '24'))
m = Model(Glb(str(HERE / 'before' / 'mm9_peasantm7.glb')))
names = [n.get('name') for n in m.glb.json['nodes']]
jn = [names[j] for j in m.joints]
CLIPS = os.environ.get('CLIPS', ','.join(m.clips)).split(',')
P = m.primitives[:2]
HANDN = ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
tris, handv, armf = [], [], []
for pr in P:
    J = np.asarray(pr['joints']); W = np.asarray(pr['weights'])
    dom = np.array([jn[J[i][W[i].argmax()]] for i in range(len(J))])
    hv = np.array([any(h in d for h in HANDN) for d in dom])
    av = hv | np.array(['Forearm' in d for d in dom])
    T = np.asarray(pr['triangles']).reshape(-1, 3)
    tris.append(T); handv.append(hv); armf.append(av[T].all(1))
hit = [np.zeros(len(t), bool) for t in tris]
for clip in CLIPS:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / FPS), t1):
        X = [x for x, _ in m.skinned_positions(m.world(m.sample(clip, t)))[:2]]
        H = np.concatenate([X[k][handv[k]] for k in range(2)])
        tr = cKDTree(H)
        for k in range(2):
            c = X[k][tris[k]].mean(1)
            d, _ = tr.query(c)
            hit[k] |= (d < R) & ~armf[k]
out = np.concatenate(hit)
print('hand contact faces', [int(h.sum()) for h in hit], 'total', int(out.sum()))
np.save(HERE / 'work' / 'hand_contact.npy', out)
