#!/usr/bin/env python3
"""Markel: body faces the forearms and hands touch (arm_hand_gate --exact on b r60: Talk L hand 0 -> 5.2 cm, Fidget L 0 -> 3.1 cm,
Talk R forearm 2.0 -> 5.4 cm where the cut shirt lies under the hands that hand_rest.py cleared against the installed surface).
Every installed LOD0 face (both primitives, GLB face order) that is not on that side's arm and whose posed centroid comes within
R m of a posed forearm/hand/finger vertex of that side in any sampled frame (every clip, FPS) -> a face mask .npy for
make_sets_mk.py EXTRA. Usage: hand_contact_mk.py <out .npy>   (env R default 0.04, FPS default 16)"""
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.04')); FPS = float(os.environ.get('FPS', '16'))
m = Model(Glb(str(HERE / 'before' / 'mm9_bjarni.glb')))
names = [n.get('name') for n in m.glb.json['nodes']]; jn = [names[j] for j in m.joints]
P = m.primitives; USE = [k for k, pr in enumerate(P) if pr['node'] == P[0]['node'] and pr['skinned']]
assert USE == [0, 1], USE
Ts = [np.asarray(P[k]['triangles']).reshape(-1, 3) for k in USE]
nv = np.cumsum([0] + [len(P[k]['positions']) for k in USE])
T = np.concatenate([t + nv[i] for i, t in enumerate(Ts)])
dom = np.concatenate([np.array([jn[P[k]['joints'][v][np.argmax(P[k]['weights'][v])]] for v in range(len(P[k]['positions']))]) for k in USE])
ARM = ('Clavicle', 'UpperArm', 'Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Twist')
LOW = ('Forearm', 'Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky')
hit = np.zeros(len(T), bool)
for tok in (' L ', ' R '):
    onarm = np.array([tok in x and any(a in x for a in ARM) for x in dom])
    low = np.flatnonzero(np.array([tok in x and any(a in x for a in LOW) for x in dom]))
    target = ~onarm[T].any(1)
    for c in m.clips:
        t1 = m.clip_times(c)[-1]
        for t in np.append(np.arange(0, t1, 1 / FPS), t1):
            X = np.concatenate([sp[0] for k, sp in enumerate(m.skinned_positions(m.world(m.sample(c, t)))) if k in USE])
            d, _ = cKDTree(X[low]).query(X[T].mean(1), distance_upper_bound=R)
            hit |= target & (d < R)
    print('side', tok.strip(), 'contact faces so far', int(hit.sum()), flush=True)
nb = len(Ts[0]); print('HANDCONTACT body', int(hit[:nb].sum()), 'head prim', int(hit[nb:].sum()))
np.save(sys.argv[1], hit)
