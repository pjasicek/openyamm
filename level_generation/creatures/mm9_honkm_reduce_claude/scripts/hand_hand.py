#!/usr/bin/env python3
"""Hand faces that touch the other hand (b55's arm/hand gate: Taunt L 0 -> 3.1 cm and ResurrectSpell L 3.4 were the left pinky
tip read 'behind' a merged right ring-finger tip; the hands meet fingertip to fingertip): every hand face of one side whose posed
centroid comes within R m of a vertex of the other hand in any sampled frame (every clip, HZ), both sides, kept exactly
(after mm9_nosferatu_reduce_claude's hand-to-hand keep). Usage: hand_hand.py <sets tag> <out name>  (env R 0.02, HZ 30)"""
import json, os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model  # noqa: E402
R = float(os.environ.get('R', '0.02')); HZ = float(os.environ.get('HZ', '30'))
tag, outn = sys.argv[1:3]
m = Model(Glb(str(HERE / 'before' / 'mm9_zombie.glb')))
s = np.load(HERE / 'work' / f'glb_sets_{tag}.npz'); CLS = json.load(open(HERE / 'work' / 'classes.json'))['names']
T = np.asarray(m.primitives[0]['triangles']).reshape(-1, 3)
hand = s['cls'][:len(T)] == CLS.index('hands')
rest = np.asarray(m.skinned_positions(m.world({}))[0][0])
left = rest[T].mean(1)[:, 0] > 0
LV = np.unique(T[hand & left]); RV = np.unique(T[hand & ~left])
hit = np.zeros(len(T), bool)
for clip in [a['name'] for a in m.glb.json['animations']]:
    t1 = m.clip_times(clip)[-1]
    for t in np.append(np.arange(0, t1, 1 / HZ), t1):
        X = np.asarray(m.skinned_positions(m.world(m.sample(clip, float(t))))[0][0]); c = X[T].mean(1)
        for own, other in ((hand & left, RV), (hand & ~left, LV)):
            d, _ = cKDTree(X[other]).query(c[own], distance_upper_bound=R); hit[np.flatnonzero(own)[d < R]] = True
out = np.zeros(len(s['cls']), bool); out[:len(T)] = hit
print('HANDHAND', int(hit.sum()), 'left', int((hit & left).sum()), 'right', int((hit & ~left).sum()))
np.save(HERE / 'work' / f'{outn}.npy', out)
