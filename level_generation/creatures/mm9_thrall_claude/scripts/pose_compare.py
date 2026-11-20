#!/usr/bin/env python3
"""Hand position relative to the chest, ours vs MM9, per clip (m, worst over 12 times), and the bone-direction angle of upper arm and forearm."""
import sys
import numpy as np
sys.path.insert(0, '../claude_shared/floor')
from glb_pose import Glb, Model
a = Model(Glb('export/mm9_thrall.glb')); b = Model(Glb('source/true/thrall1_true.glb'))
na = [n.get('name') for n in a.glb.json['nodes']]; nb = [n.get('name') for n in b.glb.json['nodes']]
R = {'Walking': 'walk', 'Running': 'run', 'AttackMelee': 'hattack1', 'AttackMelee2': 'BigAttack', 'AttackRanged': 'Rattack1', 'Hit': 'wince1', 'Death': 'die1', 'Fidget': 'fidget1'}
def d(W, names, p, c):
    return W[names.index(c)][:3, 3] - W[names.index(p)][:3, 3]
for c, s in R.items():
    worst = 0; dur = max(a.clip_times(c))
    for t in np.linspace(0.15, dur - 0.1, 14):
        wa = a.world(a.sample(c, float(t))); wb = b.world(b.sample(s, float(t)))
        for p_, c_ in (('Bip01 R UpperArm', 'Bip01 R Forearm'), ('Bip01 R Forearm', 'Bip01 R Hand'), ('Bip01 L UpperArm', 'Bip01 L Forearm'), ('Bip01 L Forearm', 'Bip01 L Hand')):
            u = d(wa, na, p_, c_); v = d(wb, nb, p_, c_)
            ang = np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
            if ang > worst: worst = ang; wh = (round(float(t), 2), p_)
    print(c, 'worst bone dir difference deg', round(worst, 1), wh)
