#!/usr/bin/env python3
"""Grip contact of the right (sword) hand: limb-primitive faces weighted to the right hand or fingers whose centre comes
within CONTACT m (default 1.5 cm) of the sword surface (its vertices and face centres) at any of 6 times of every clip.
They stay exact when the rest of the hand is decimated (prio-1 relaxed keep set). Writes work/grip_contact.npy (per GLB face).
(from mm9_lizardorc_reduce_claude; the Half-Orc's hands are all in primitive 0, the sword is primitive 3)"""
import os, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model
C = float(os.environ.get('CONTACT', '0.015'))
m = Model(Glb(str(HERE / 'before' / 'mm9_dookmilitia.glb')))
nm = [n.get('name') for n in m.glb.json['nodes']]; jn = [nm[j] for j in m.joints]
rh = np.array([n.startswith('Bip01 R ') and any(s in n for s in ('Hand', 'Index', 'Middle', 'Ring', 'Pinky', 'Thumb')) for n in jn])
nf = [len(p['triangles']) for p in m.primitives]; off = np.cumsum([0] + nf)
p0 = m.primitives[0]
hw = (rh[p0['joints']] * p0['weights']).sum(1)[p0['triangles']].max(1)
cand = np.where(hw > 0.01)[0]; best = np.full(len(cand), 9.0)
for clip in m.clips:
    ts = m.clip_times(clip)
    for t in np.linspace(ts[0], ts[-1], 6):
        posed = m.skinned_positions(m.world(m.sample(clip, t)))
        wp, wt = posed[3]; tree = cKDTree(np.vstack([wp, wp[wt].mean(1)]))
        p, tr = posed[0]
        d, _ = tree.query(p[tr[cand]].mean(1)); best = np.minimum(best, d)
mask = np.zeros(off[-1], bool); mask[cand[best < C]] = True
print('right hand faces', len(cand), 'contact', int(mask.sum()))
np.save(HERE / 'work' / 'grip_contact.npy', mask)
