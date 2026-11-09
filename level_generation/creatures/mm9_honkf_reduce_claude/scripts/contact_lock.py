#!/usr/bin/env python3
"""Keeps for the arm/hand and jitter gates of a first build (after mm9_lesserdemon_reduce_claude/scripts/contact_lock.py):
(1) for every clip/side whose arm/hand gate got worse than the installed model (hand or forearm depth, or frames over 1 cm;
review/gates_before vs review/gates_<build>), every face that is not that side's own hand/forearm and whose posed centroid
comes within R m of that side's hand vertices in any frame of the clip at 48 fps (the other hand's reduced fingers, the sleeve
and robe under the hand); (2) the shoulder skin: every face with a vertex weighted mostly to a Clavicle or UpperArm (the jitter
gate's shoulder-skin set; its 95th percentile moved with fewer vertices, Death L 1.98 -> 2.15 mm/f2 on a60).
Usage: contact_lock.py <sets tag> <build tag> <out name>  (env R 0.03, ONLY clip:side,... to restrict (1))"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.03'))
tag, build, outn = sys.argv[1:4]
m = Model(Glb(str(HERE / 'before' / 'mm9_honkf.glb')))
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CLS = json.load(open(HERE / 'work' / 'classes.json'))['names']
Ts = [np.asarray(p['triangles']).reshape(-1, 3) for p in m.primitives[:2]]; offs = np.cumsum([0] + [len(t) for t in Ts])
cls = s['cls']; own = np.isin(cls, [CLS.index('hands'), CLS.index('forearm')])
rest = [np.asarray(p) for p, _ in m.skinned_positions(m.world({}))[:2]]
cen = np.concatenate([P[T].mean(1) for P, T in zip(rest, Ts)])
hand1 = cls[offs[1]:] == CLS.index('hands'); left1 = rest[1][Ts[1]].mean(1)[:, 0] > 0
a = json.load(open(HERE / 'review' / 'gates_before' / 'arm_hand.json'))['clips']
b = json.load(open(HERE / 'review' / f'gates_{build}' / 'arm_hand.json'))['clips']
worse = [(c, sd) for c in a for sd in a[c] if b[c][sd]['hand_in_body_cm'] > a[c][sd]['hand_in_body_cm']
         or b[c][sd]['forearm_in_body_cm'] > a[c][sd]['forearm_in_body_cm'] or b[c][sd]['frames_hand_over_1cm'] > a[c][sd]['frames_hand_over_1cm']]
ONLY = [x for x in os.environ.get('ONLY', '').split(',') if x]   # e.g. Death:R,PropFidget2:R
if ONLY:
    worse = [w for w in worse if f'{w[0]}:{w[1]}' in ONLY]
print('WORSE', worse)
hit = np.zeros(len(cls), bool)
for clip, sd in worse:
    hv = np.unique(Ts[1][hand1 & (left1 if sd == 'L' else ~left1)])
    sidef = np.zeros(len(cls), bool); sidef[offs[1]:] = (left1 if sd == 'L' else ~left1)
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / 48), t1):
        sk = [np.asarray(p) for p, _ in m.skinned_positions(m.world(m.sample(clip, float(t))))[:2]]
        tree = cKDTree(sk[1][hv])
        for k in range(2):
            d, _ = tree.query(sk[k][Ts[k]].mean(1), distance_upper_bound=R)
            sel = np.zeros(len(cls), bool); sel[offs[k]:offs[k + 1]] = d < R
            hit |= sel & ~(own & sidef)
names = [m.glb.json['nodes'][j]['name'] for j in m.glb.json['skins'][0]['joints']]
sh = np.array([n.endswith('Clavicle') or n.endswith('UpperArm') for n in names])
shoulder = np.zeros(len(cls), bool)
for k, p in enumerate(m.primitives[:2]):
    J = np.asarray(p['joints']); W = np.asarray(p['weights'])
    dom = sh[J[np.arange(len(J)), W.argmax(1)]]
    shoulder[offs[k]:offs[k + 1]] = dom[Ts[k]].any(1)
lining = s['lining']
print('CONTACTLOCK', int(hit.sum()), {CLS[c]: int((hit & (cls == c)).sum()) for c in np.unique(cls[hit])},
      'shoulder', int(shoulder.sum()), {CLS[c]: int((shoulder & (cls == c)).sum()) for c in np.unique(cls[shoulder])})
np.save(HERE / 'work' / f'{outn}.npy', (hit | shoulder) & ~lining)
