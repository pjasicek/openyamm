#!/usr/bin/env python3
"""Contact keeps for the Honk female (after the Zombie's hand_hand.py / hand_contact.py): (1) hand faces of one side whose posed
centroid comes within RH m of a vertex of the other hand, (2) faces that are not hand/forearm faces whose posed centroid comes
within R m of a posed hand vertex, in any sampled frame (every clip, HZ); (2) mirrored in x at rest. The arm/hand gate measures
hands against everything else, and a cut surface under a resting hand changes its depth.
Usage: honk_contact.py <sets tag> <out name>  -> work/<out name>.npy per GLB face  (env R 0.03, RH 0.02, HZ 15)"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.03')); RH = float(os.environ.get('RH', '0.02')); HZ = float(os.environ.get('HZ', '15'))
tag, outn = sys.argv[1:3]
m = Model(Glb(str(HERE / 'before' / 'mm9_honkf.glb')))
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CLS = json.load(open(HERE / 'work' / 'classes.json'))['names']
Ts = [np.asarray(p['triangles']).reshape(-1, 3) for p in m.primitives[:2]]
offs = np.cumsum([0] + [len(t) for t in Ts])
cls = s['cls']; hand_f = cls[offs[1]:offs[2]] == CLS.index('hands')
rest = [np.asarray(p) for p, _ in m.skinned_positions(m.world({}))[:2]]
left = rest[1][Ts[1]].mean(1)[:, 0] > 0
LV = np.unique(Ts[1][hand_f & left]); RV = np.unique(Ts[1][hand_f & ~left]); HV = np.unique(Ts[1][hand_f])
target = ~np.isin(cls, [CLS.index(c) for c in ('hands', 'forearm')])
hit = np.zeros(len(cls), bool); hh = np.zeros(len(cls), bool)
for clip in [a['name'] for a in m.glb.json['animations']]:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        sk = [np.asarray(p) for p, _ in m.skinned_positions(m.world(m.sample(clip, float(t))))[:2]]
        tree = cKDTree(sk[1][HV])
        for k in range(2):
            c = sk[k][Ts[k]].mean(1); d, _ = tree.query(c, distance_upper_bound=R); hit[offs[k]:offs[k + 1]] |= d < R
        c = sk[1][Ts[1]].mean(1)
        for own, other in ((hand_f & left, RV), (hand_f & ~left, LV)):
            d, _ = cKDTree(sk[1][other]).query(c[own], distance_upper_bound=RH); hh[offs[1] + np.flatnonzero(own)[d < RH]] = True
hit &= target
cen = np.concatenate([P[T].mean(1) for P, T in zip(rest, Ts)])
hit |= target & (cKDTree(cen[hit] * [-1, 1, 1]).query(cen)[0] < 0.006)
out = hit; np.save(HERE / 'work' / f'{outn}_handhand.npy', hh)
print('CONTACT body', int(hit.sum()), {CLS[c]: int((hit & (cls == c)).sum()) for c in np.unique(cls[hit])}, 'hand-hand', int(hh.sum()))
np.save(HERE / 'work' / f'{outn}.npy', out)
